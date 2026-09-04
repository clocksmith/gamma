#include "profile_population.hpp"

#include "profile_artifacts.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <initializer_list>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

namespace gamma_enwiki9::nncp {
namespace {

namespace fs = std::filesystem;

constexpr std::array<std::uint32_t, 64> kSha256RoundConstants{
    UINT32_C(0x428a2f98), UINT32_C(0x71374491), UINT32_C(0xb5c0fbcf),
    UINT32_C(0xe9b5dba5), UINT32_C(0x3956c25b), UINT32_C(0x59f111f1),
    UINT32_C(0x923f82a4), UINT32_C(0xab1c5ed5), UINT32_C(0xd807aa98),
    UINT32_C(0x12835b01), UINT32_C(0x243185be), UINT32_C(0x550c7dc3),
    UINT32_C(0x72be5d74), UINT32_C(0x80deb1fe), UINT32_C(0x9bdc06a7),
    UINT32_C(0xc19bf174), UINT32_C(0xe49b69c1), UINT32_C(0xefbe4786),
    UINT32_C(0x0fc19dc6), UINT32_C(0x240ca1cc), UINT32_C(0x2de92c6f),
    UINT32_C(0x4a7484aa), UINT32_C(0x5cb0a9dc), UINT32_C(0x76f988da),
    UINT32_C(0x983e5152), UINT32_C(0xa831c66d), UINT32_C(0xb00327c8),
    UINT32_C(0xbf597fc7), UINT32_C(0xc6e00bf3), UINT32_C(0xd5a79147),
    UINT32_C(0x06ca6351), UINT32_C(0x14292967), UINT32_C(0x27b70a85),
    UINT32_C(0x2e1b2138), UINT32_C(0x4d2c6dfc), UINT32_C(0x53380d13),
    UINT32_C(0x650a7354), UINT32_C(0x766a0abb), UINT32_C(0x81c2c92e),
    UINT32_C(0x92722c85), UINT32_C(0xa2bfe8a1), UINT32_C(0xa81a664b),
    UINT32_C(0xc24b8b70), UINT32_C(0xc76c51a3), UINT32_C(0xd192e819),
    UINT32_C(0xd6990624), UINT32_C(0xf40e3585), UINT32_C(0x106aa070),
    UINT32_C(0x19a4c116), UINT32_C(0x1e376c08), UINT32_C(0x2748774c),
    UINT32_C(0x34b0bcb5), UINT32_C(0x391c0cb3), UINT32_C(0x4ed8aa4a),
    UINT32_C(0x5b9cca4f), UINT32_C(0x682e6ff3), UINT32_C(0x748f82ee),
    UINT32_C(0x78a5636f), UINT32_C(0x84c87814), UINT32_C(0x8cc70208),
    UINT32_C(0x90befffa), UINT32_C(0xa4506ceb), UINT32_C(0xbef9a3f7),
    UINT32_C(0xc67178f2),
};

class Sha256 {
 public:
  void Update(const void* source, std::size_t bytes) {
    if (bytes > std::numeric_limits<std::uint64_t>::max() - total_bytes_) {
      throw std::overflow_error("SHA-256 input length overflows");
    }
    total_bytes_ += bytes;
    const auto* input = static_cast<const std::uint8_t*>(source);
    while (bytes != 0) {
      const std::size_t available = block_.size() - block_bytes_;
      const std::size_t copied = std::min(available, bytes);
      std::memcpy(block_.data() + block_bytes_, input, copied);
      block_bytes_ += copied;
      input += copied;
      bytes -= copied;
      if (block_bytes_ == block_.size()) {
        Transform(block_.data());
        block_bytes_ = 0;
      }
    }
  }

  std::array<std::uint8_t, 32> Finalize() {
    if (finalized_) throw std::logic_error("SHA-256 finalized twice");
    if (total_bytes_ > std::numeric_limits<std::uint64_t>::max() / 8) {
      throw std::overflow_error("SHA-256 bit length overflows");
    }
    const std::uint64_t bits = total_bytes_ * 8;
    block_[block_bytes_++] = 0x80;
    if (block_bytes_ > 56) {
      std::fill(block_.begin() + static_cast<std::ptrdiff_t>(block_bytes_),
                block_.end(), 0);
      Transform(block_.data());
      block_bytes_ = 0;
    }
    std::fill(
        block_.begin() + static_cast<std::ptrdiff_t>(block_bytes_),
        block_.begin() + 56,
        0);
    for (std::size_t index = 0; index < 8; ++index) {
      block_[63 - index] = static_cast<std::uint8_t>(bits >> (8U * index));
    }
    Transform(block_.data());
    std::array<std::uint8_t, 32> output{};
    for (std::size_t word = 0; word < state_.size(); ++word) {
      for (std::size_t byte = 0; byte < 4; ++byte) {
        output[word * 4 + byte] = static_cast<std::uint8_t>(
            state_[word] >> (24U - 8U * byte));
      }
    }
    finalized_ = true;
    return output;
  }

 private:
  static std::uint32_t Choose(
      std::uint32_t x,
      std::uint32_t y,
      std::uint32_t z) {
    return (x & y) ^ (~x & z);
  }

  static std::uint32_t Majority(
      std::uint32_t x,
      std::uint32_t y,
      std::uint32_t z) {
    return (x & y) ^ (x & z) ^ (y & z);
  }

  void Transform(const std::uint8_t* block) {
    std::array<std::uint32_t, 64> words{};
    for (std::size_t index = 0; index < 16; ++index) {
      words[index] =
          (static_cast<std::uint32_t>(block[index * 4]) << 24U) |
          (static_cast<std::uint32_t>(block[index * 4 + 1]) << 16U) |
          (static_cast<std::uint32_t>(block[index * 4 + 2]) << 8U) |
          static_cast<std::uint32_t>(block[index * 4 + 3]);
    }
    for (std::size_t index = 16; index < words.size(); ++index) {
      const std::uint32_t s0 = std::rotr(words[index - 15], 7) ^
          std::rotr(words[index - 15], 18) ^ (words[index - 15] >> 3U);
      const std::uint32_t s1 = std::rotr(words[index - 2], 17) ^
          std::rotr(words[index - 2], 19) ^ (words[index - 2] >> 10U);
      words[index] = words[index - 16] + s0 + words[index - 7] + s1;
    }
    std::uint32_t a = state_[0];
    std::uint32_t b = state_[1];
    std::uint32_t c = state_[2];
    std::uint32_t d = state_[3];
    std::uint32_t e = state_[4];
    std::uint32_t f = state_[5];
    std::uint32_t g = state_[6];
    std::uint32_t h = state_[7];
    for (std::size_t index = 0; index < words.size(); ++index) {
      const std::uint32_t upper =
          std::rotr(e, 6) ^ std::rotr(e, 11) ^ std::rotr(e, 25);
      const std::uint32_t lower =
          std::rotr(a, 2) ^ std::rotr(a, 13) ^ std::rotr(a, 22);
      const std::uint32_t first = h + upper + Choose(e, f, g) +
          kSha256RoundConstants[index] + words[index];
      const std::uint32_t second = lower + Majority(a, b, c);
      h = g;
      g = f;
      f = e;
      e = d + first;
      d = c;
      c = b;
      b = a;
      a = first + second;
    }
    state_[0] += a;
    state_[1] += b;
    state_[2] += c;
    state_[3] += d;
    state_[4] += e;
    state_[5] += f;
    state_[6] += g;
    state_[7] += h;
  }

  std::array<std::uint32_t, 8> state_{
      UINT32_C(0x6a09e667), UINT32_C(0xbb67ae85), UINT32_C(0x3c6ef372),
      UINT32_C(0xa54ff53a), UINT32_C(0x510e527f), UINT32_C(0x9b05688c),
      UINT32_C(0x1f83d9ab), UINT32_C(0x5be0cd19),
  };
  std::array<std::uint8_t, 64> block_{};
  std::uint64_t total_bytes_ = 0;
  std::size_t block_bytes_ = 0;
  bool finalized_ = false;
};

std::string Hex(const std::array<std::uint8_t, 32>& digest) {
  std::ostringstream output;
  output << std::hex << std::setfill('0');
  for (const std::uint8_t byte : digest) {
    output << std::setw(2) << static_cast<unsigned int>(byte);
  }
  return output.str();
}

class StateHasher {
 public:
  void Bytes(const void* source, std::size_t bytes) {
    hash_.Update(source, bytes);
  }

  void U64(std::uint64_t value) {
    std::array<std::uint8_t, 8> bytes{};
    for (std::size_t index = 0; index < bytes.size(); ++index) {
      bytes[index] = static_cast<std::uint8_t>(value >> (8U * index));
    }
    Bytes(bytes.data(), bytes.size());
  }

  void String(const std::string& value) {
    U64(value.size());
    Bytes(value.data(), value.size());
  }

  template <typename Value>
  void Vector(const std::vector<Value>& values) {
    static_assert(std::is_trivially_copyable_v<Value>);
    if (values.size() > std::numeric_limits<std::size_t>::max() / sizeof(Value)) {
      throw std::overflow_error("state witness byte count overflows");
    }
    U64(values.size());
    Bytes(values.data(), values.size() * sizeof(Value));
  }

  std::string FinalizeHex() { return Hex(hash_.Finalize()); }

 private:
  Sha256 hash_;
};

bool SameDescriptor(
    const GradientDescriptor& left,
    const GradientDescriptor& right) {
  return left.name == right.name && left.element_type == right.element_type &&
      left.dimensions == right.dimensions;
}

void HashDescriptor(StateHasher& hash, const GradientDescriptor& descriptor) {
  hash.String(descriptor.name);
  hash.U64(descriptor.element_type == GradientElementType::kBf16 ? 1 : 0);
  hash.U64(descriptor.dimensions.size());
  for (const std::size_t dimension : descriptor.dimensions) hash.U64(dimension);
}

std::size_t CheckedProduct(
    std::initializer_list<std::size_t> factors,
    const char* label) {
  std::size_t result = 1;
  for (const std::size_t factor : factors) {
    if (factor == 0 ||
        result > std::numeric_limits<std::size_t>::max() / factor) {
      throw std::invalid_argument(std::string(label) + " geometry is invalid");
    }
    result *= factor;
  }
  return result;
}

}  // namespace

std::vector<std::uint32_t> LoadBigEndianProfileSymbols(
    const fs::path& path,
    std::size_t expected_symbols,
    std::size_t vocabulary) {
  if (expected_symbols == 0 || vocabulary <= 1 ||
      vocabulary > std::numeric_limits<std::uint16_t>::max() ||
      expected_symbols > std::numeric_limits<std::size_t>::max() / 2) {
    throw std::invalid_argument("profile symbol geometry is invalid");
  }
  const fs::file_status status = fs::symlink_status(path);
  if (fs::is_symlink(status) || !fs::is_regular_file(status)) {
    throw std::runtime_error("profile symbol input is not a regular file");
  }
  const std::size_t expected_bytes = expected_symbols * 2;
  if (expected_bytes > static_cast<std::size_t>(
                           std::numeric_limits<std::streamsize>::max())) {
    throw std::invalid_argument("profile symbol input exceeds stream size");
  }
  if (fs::file_size(path) != expected_bytes) {
    throw std::runtime_error("profile symbol byte count differs");
  }
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open profile symbols");
  std::vector<std::uint8_t> bytes(expected_bytes);
  input.read(
      reinterpret_cast<char*>(bytes.data()),
      static_cast<std::streamsize>(bytes.size()));
  if (!input || input.peek() != std::char_traits<char>::eof()) {
    throw std::runtime_error("profile symbol input changed or truncated");
  }
  std::vector<std::uint32_t> symbols(expected_symbols);
  for (std::size_t index = 0; index < symbols.size(); ++index) {
    const std::uint32_t symbol =
        (static_cast<std::uint32_t>(bytes[index * 2]) << 8U) |
        static_cast<std::uint32_t>(bytes[index * 2 + 1]);
    if (symbol >= vocabulary) {
      throw std::runtime_error("profile symbol lies outside the vocabulary");
    }
    symbols[index] = symbol;
  }
  return symbols;
}

ProfilePopulationBatch BuildProfilePopulationBatch(
    std::span<const std::uint32_t> stream_major_symbols,
    std::size_t streams,
    std::size_t states,
    std::size_t model_batch_index,
    std::size_t vocabulary) {
  if (streams == 0 || states == 0 || vocabulary <= 1 ||
      stream_major_symbols.empty() ||
      stream_major_symbols.size() % streams != 0 ||
      states > std::numeric_limits<std::size_t>::max() / streams) {
    throw std::invalid_argument("profile population geometry is invalid");
  }
  const std::size_t stream_stride = stream_major_symbols.size() / streams;
  if (model_batch_index > std::numeric_limits<std::size_t>::max() / states) {
    throw std::invalid_argument("profile population model batch overflows");
  }
  const std::size_t batch_start = model_batch_index * states;
  if (batch_start > stream_stride || states > stream_stride - batch_start) {
    throw std::invalid_argument("profile population model batch is outside input");
  }
  const std::size_t samples = states * streams;
  ProfilePopulationBatch batch{
      .input_symbols = std::vector<std::uint32_t>(samples),
      .targets = std::vector<std::uint32_t>(samples),
      .original_coordinates = std::vector<std::uint64_t>(samples),
  };
  for (std::size_t state = 0; state < states; ++state) {
    const std::size_t position = batch_start + state;
    for (std::size_t stream = 0; stream < streams; ++stream) {
      const std::size_t original = stream * stream_stride + position;
      const std::size_t execution = state * streams + stream;
      const std::uint32_t target = stream_major_symbols[original];
      const std::uint32_t input = position == 0
          ? 0
          : stream_major_symbols[original - 1];
      if (input >= vocabulary || target >= vocabulary) {
        throw std::runtime_error("profile population symbol is out of range");
      }
      batch.input_symbols[execution] = input;
      batch.targets[execution] = target;
      batch.original_coordinates[execution] = original;
    }
  }
  return batch;
}

float FrozenProfileLearningRate(std::size_t parent_model_batch_index) {
  constexpr std::size_t kPopulationModelBatches = 32;
  if (parent_model_batch_index >= kPopulationModelBatches) {
    throw std::invalid_argument("profile learning-rate coordinate is outside population");
  }
  const float start = 1.6e-4F;
  const float end = 1.0e-4F;
  const float position = static_cast<float>(parent_model_batch_index);
  const float span = 10000.0F;
  const float fraction = position / span;
  const float difference = end - start;
  const float adjustment = fraction * difference;
  return start + adjustment;
}

std::string Sha256Hex(std::span<const std::uint8_t> bytes) {
  Sha256 hash;
  hash.Update(bytes.data(), bytes.size());
  return Hex(hash.Finalize());
}

std::string ProfileFutureStateSha256(
    const ProfileGeometry& geometry,
    ProfileWeights& weights,
    const ProfileAdamState& optimizer,
    const std::vector<Bf16Buffer>& memory) {
  if constexpr (std::endian::native != std::endian::little) {
    throw std::runtime_error("profile state witness requires little endian");
  }
  if (sizeof(float) != 4) {
    throw std::runtime_error("profile state witness requires binary32 float");
  }
  std::vector<ParameterArtifactView> parameters =
      CanonicalParameterArtifacts(geometry, weights);
  if (optimizer.next_update_exponent == 0 ||
      optimizer.tensors.size() != parameters.size() ||
      memory.size() != geometry.layers) {
    throw std::invalid_argument("profile future state population differs");
  }
  StateHasher hash;
  hash.String("gamma.enwiki9.nncp-profile-future-state.v1");
  hash.U64(geometry.transformer.states);
  hash.U64(geometry.transformer.streams);
  hash.U64(geometry.transformer.heads);
  hash.U64(geometry.transformer.head_width);
  hash.U64(geometry.transformer.memory);
  hash.U64(geometry.transformer.inner);
  hash.U64(geometry.layers);
  hash.U64(geometry.vocabulary);
  hash.U64(geometry.loss_start);
  hash.U64(geometry.loss_length);
  hash.U64(optimizer.next_update_exponent);
  hash.U64(parameters.size());
  for (std::size_t index = 0; index < parameters.size(); ++index) {
    const ParameterArtifactView& parameter = parameters[index];
    const AdamTensorState& adam = optimizer.tensors[index];
    if (!SameDescriptor(parameter.descriptor, adam.descriptor)) {
      throw std::invalid_argument("profile state descriptor differs");
    }
    hash.U64(index);
    HashDescriptor(hash, parameter.descriptor);
    if (parameter.descriptor.element_type == GradientElementType::kBf16) {
      if (parameter.bf16_values == nullptr || parameter.f32_values != nullptr ||
          adam.low_words.size() != parameter.bf16_values->size() ||
          adam.variance_bf16.size() != parameter.bf16_values->size() ||
          !adam.variance_f32.empty()) {
        throw std::invalid_argument("profile BF16 future state differs");
      }
      hash.Vector(*parameter.bf16_values);
      hash.Vector(adam.low_words);
      hash.Vector(adam.variance_bf16);
    } else {
      if (parameter.f32_values == nullptr || parameter.bf16_values != nullptr ||
          adam.variance_f32.size() != parameter.f32_values->size() ||
          !adam.low_words.empty() || !adam.variance_bf16.empty()) {
        throw std::invalid_argument("profile F32 future state differs");
      }
      hash.Vector(*parameter.f32_values);
      hash.Vector(adam.variance_f32);
    }
  }
  hash.U64(memory.size());
  const std::size_t model = CheckedProduct(
      {geometry.transformer.heads, geometry.transformer.head_width},
      "profile state model");
  const std::size_t expected_memory = CheckedProduct(
      {geometry.transformer.memory, geometry.transformer.streams, model},
      "profile state memory");
  for (std::size_t layer = 0; layer < memory.size(); ++layer) {
    if (memory[layer].size() != expected_memory) {
      throw std::invalid_argument("profile recurrent-memory geometry differs");
    }
    hash.U64(layer);
    hash.Vector(memory[layer]);
  }
  return hash.FinalizeHex();
}

}  // namespace gamma_enwiki9::nncp
