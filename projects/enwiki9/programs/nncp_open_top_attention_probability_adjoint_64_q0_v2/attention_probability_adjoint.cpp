#include <immintrin.h>

#include <array>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr std::size_t kStates = 64;
constexpr std::size_t kStreams = 32;
constexpr std::size_t kHeads = 8;
constexpr std::size_t kKeys = 320;
constexpr std::size_t kWidth = 128;
constexpr std::size_t kValueElements = kStreams * kHeads * kKeys * kWidth;
constexpr std::size_t kIncomingElements = kStates * kStreams * kHeads * kWidth;
constexpr std::size_t kOutputElements = kStates * kHeads * kStreams * kKeys;

float FromBf16(uint16_t value) {
  const uint32_t bits = static_cast<uint32_t>(value) << 16;
  float result = 0.0f;
  std::memcpy(&result, &bits, sizeof(result));
  return result;
}

uint16_t ToBf16(float value) {
  uint32_t bits = 0;
  std::memcpy(&bits, &value, sizeof(bits));
  if ((bits & 0x7f800000U) == 0x7f800000U && (bits & 0x007fffffU) != 0) {
    return static_cast<uint16_t>((bits >> 16) | 0x0040U);
  }
  const uint32_t rounding_bias = 0x00007fffU + ((bits >> 16) & 1U);
  return static_cast<uint16_t>((bits + rounding_bias) >> 16);
}

std::vector<uint16_t> ReadWords(const std::string& path, std::size_t count) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open input: " + path);
  std::vector<uint16_t> words(count);
  input.read(reinterpret_cast<char*>(words.data()),
             static_cast<std::streamsize>(count * sizeof(uint16_t)));
  if (input.gcount() != static_cast<std::streamsize>(count * sizeof(uint16_t))) {
    throw std::runtime_error("input size mismatch: " + path);
  }
  char extra = 0;
  if (input.read(&extra, 1)) throw std::runtime_error("input has trailing bytes: " + path);
  return words;
}

void WriteWords(const std::string& path, const std::vector<uint16_t>& words) {
  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  if (!output) throw std::runtime_error("cannot open output: " + path);
  output.write(reinterpret_cast<const char*>(words.data()),
               static_cast<std::streamsize>(words.size() * sizeof(uint16_t)));
  if (!output) throw std::runtime_error("output write failed: " + path);
}

std::size_t ValueIndex(std::size_t stream, std::size_t head,
                       std::size_t key, std::size_t feature) {
  return (((stream * kHeads + head) * kKeys + key) * kWidth + feature);
}

std::size_t IncomingIndex(std::size_t state, std::size_t stream,
                          std::size_t head, std::size_t feature) {
  return (((state * kStreams + stream) * kHeads + head) * kWidth + feature);
}

std::size_t SourceIndex(std::size_t state, std::size_t head,
                        std::size_t stream, std::size_t key) {
  return (((state * kHeads + head) * kStreams + stream) * kKeys + key);
}

std::size_t StreamMajorIndex(std::size_t state, std::size_t stream,
                             std::size_t head, std::size_t key) {
  return (((state * kStreams + stream) * kHeads + head) * kKeys + key);
}

std::vector<uint16_t> ScalarReference(const std::vector<uint16_t>& value,
                                      const std::vector<uint16_t>& incoming) {
  std::vector<uint16_t> output(kOutputElements);
  for (std::size_t state = 0; state < kStates; ++state) {
    for (std::size_t head = 0; head < kHeads; ++head) {
      for (std::size_t stream = 0; stream < kStreams; ++stream) {
        for (std::size_t key = 0; key < kKeys; ++key) {
          __m128 accumulator = _mm_set_ss(0.0f);
          for (std::size_t feature = 0; feature < kWidth; ++feature) {
            const __m128 left = _mm_set_ss(
                FromBf16(incoming[IncomingIndex(state, stream, head, feature)]));
            const __m128 right = _mm_set_ss(
                FromBf16(value[ValueIndex(stream, head, key, feature)]));
            accumulator = _mm_fmadd_ss(left, right, accumulator);
          }
          output[SourceIndex(state, head, stream, key)] =
              ToBf16(_mm_cvtss_f32(accumulator));
        }
      }
    }
  }
  return output;
}

std::vector<uint16_t> AvxTreatment(const std::vector<uint16_t>& value,
                                   const std::vector<uint16_t>& incoming,
                                   bool negate) {
  std::vector<uint16_t> output(kOutputElements);
  alignas(32) std::array<float, 8> lanes{};
  for (std::size_t state = 0; state < kStates; ++state) {
    for (std::size_t head = 0; head < kHeads; ++head) {
      for (std::size_t stream = 0; stream < kStreams; ++stream) {
        for (std::size_t key = 0; key < kKeys; key += 8) {
          __m256 accumulator = _mm256_setzero_ps();
          for (std::size_t feature = 0; feature < kWidth; ++feature) {
            float incoming_value = FromBf16(
                incoming[IncomingIndex(state, stream, head, feature)]);
            if (negate) incoming_value = -incoming_value;
            const __m256 left = _mm256_set1_ps(incoming_value);
            const __m256 right = _mm256_set_ps(
                FromBf16(value[ValueIndex(stream, head, key + 7, feature)]),
                FromBf16(value[ValueIndex(stream, head, key + 6, feature)]),
                FromBf16(value[ValueIndex(stream, head, key + 5, feature)]),
                FromBf16(value[ValueIndex(stream, head, key + 4, feature)]),
                FromBf16(value[ValueIndex(stream, head, key + 3, feature)]),
                FromBf16(value[ValueIndex(stream, head, key + 2, feature)]),
                FromBf16(value[ValueIndex(stream, head, key + 1, feature)]),
                FromBf16(value[ValueIndex(stream, head, key + 0, feature)]));
            accumulator = _mm256_fmadd_ps(left, right, accumulator);
          }
          _mm256_store_ps(lanes.data(), accumulator);
          for (std::size_t lane = 0; lane < 8; ++lane) {
            output[SourceIndex(state, head, stream, key + lane)] =
                ToBf16(lanes[lane]);
          }
        }
      }
    }
  }
  return output;
}

std::vector<uint16_t> WrongLayout(const std::vector<uint16_t>& source_order) {
  std::vector<uint16_t> output(kOutputElements);
  for (std::size_t state = 0; state < kStates; ++state) {
    for (std::size_t head = 0; head < kHeads; ++head) {
      for (std::size_t stream = 0; stream < kStreams; ++stream) {
        for (std::size_t key = 0; key < kKeys; ++key) {
          output[StreamMajorIndex(state, stream, head, key)] =
              source_order[SourceIndex(state, head, stream, key)];
        }
      }
    }
  }
  return output;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 7) {
      throw std::runtime_error(
          "usage: evaluator value.bf16 attended.bf16 scalar.bf16 avx.bf16 "
          "wrong-layout.bf16 negated.bf16");
    }
    const uint16_t endian_probe = 1;
    if (*reinterpret_cast<const unsigned char*>(&endian_probe) != 1) {
      throw std::runtime_error("little-endian host required");
    }
    const std::vector<uint16_t> value = ReadWords(argv[1], kValueElements);
    const std::vector<uint16_t> incoming = ReadWords(argv[2], kIncomingElements);
    const std::vector<uint16_t> scalar = ScalarReference(value, incoming);
    const std::vector<uint16_t> avx = AvxTreatment(value, incoming, false);
    const std::vector<uint16_t> wrong_layout = WrongLayout(avx);
    const std::vector<uint16_t> negated = AvxTreatment(value, incoming, true);
    WriteWords(argv[3], scalar);
    WriteWords(argv[4], avx);
    WriteWords(argv[5], wrong_layout);
    WriteWords(argv[6], negated);
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
