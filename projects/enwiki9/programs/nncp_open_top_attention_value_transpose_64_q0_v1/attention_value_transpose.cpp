#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <immintrin.h>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace fs = std::filesystem;

namespace {

constexpr std::size_t kStates = 64;
constexpr std::size_t kStreams = 32;
constexpr std::size_t kHeads = 8;
constexpr std::size_t kKeys = 320;
constexpr std::size_t kHeadWidth = 128;
constexpr std::size_t kLaneWidth = 8;
constexpr std::size_t kThreads = 4;

float bf16_to_float(std::uint16_t value) {
    const std::uint32_t bits = static_cast<std::uint32_t>(value) << 16U;
    float result;
    std::memcpy(&result, &bits, sizeof(result));
    return result;
}

std::uint16_t bf16(float value) {
    std::uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    const std::uint32_t rounding = 0x7fffU + ((bits >> 16U) & 1U);
    return static_cast<std::uint16_t>((bits + rounding) >> 16U);
}

std::vector<float> read_bf16(const fs::path & path, std::size_t count) {
    const std::uintmax_t expected = count * sizeof(std::uint16_t);
    if (!fs::is_regular_file(path) || fs::file_size(path) != expected) {
        throw std::runtime_error("BF16 input geometry differs: " + path.string());
    }
    std::vector<std::uint16_t> words(count);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char *>(words.data()),
               static_cast<std::streamsize>(expected));
    if (!input) throw std::runtime_error("truncated BF16 input");
    std::vector<float> values(count);
    std::transform(words.begin(), words.end(), values.begin(), bf16_to_float);
    return values;
}

void write_bf16(const fs::path & path, const std::vector<float> & values) {
    std::vector<std::uint16_t> words(values.size());
    std::transform(values.begin(), values.end(), words.begin(), bf16);
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(words.data()),
                 static_cast<std::streamsize>(
                     words.size() * sizeof(words.front())));
    if (!output) throw std::runtime_error("cannot write probability adjoint");
}

std::vector<float> pack_value(const std::vector<float> & value) {
    const std::size_t count = kStreams * kHeads * kKeys * kHeadWidth;
    if (value.size() != count) {
        throw std::runtime_error("value-state geometry differs");
    }
    std::vector<float> packed(count);
    for (std::size_t stream = 0; stream < kStreams; ++stream) {
        for (std::size_t head = 0; head < kHeads; ++head) {
            const std::size_t matrix = stream * kHeads + head;
            for (std::size_t feature = 0; feature < kHeadWidth; ++feature) {
                for (std::size_t key = 0; key < kKeys; ++key) {
                    packed[(matrix * kHeadWidth + feature) * kKeys + key] =
                        value[(matrix * kKeys + key) * kHeadWidth + feature];
                }
            }
        }
    }
    return packed;
}

std::vector<float> value_transpose(
    const std::vector<float> & packed,
    const std::vector<float> & incoming,
    bool negate
) {
    const std::size_t value_count = kStreams * kHeads * kHeadWidth * kKeys;
    const std::size_t incoming_count =
        kStates * kStreams * kHeads * kHeadWidth;
    if (packed.size() != value_count || incoming.size() != incoming_count) {
        throw std::runtime_error("value transpose geometry differs");
    }
    std::vector<float> result(kStates * kHeads * kStreams * kKeys);
    std::vector<std::thread> workers;
    for (std::size_t worker = 0; worker < kThreads; ++worker) {
        workers.emplace_back([&, worker] {
            for (std::size_t state = worker; state < kStates;
                 state += kThreads) {
                for (std::size_t head = 0; head < kHeads; ++head) {
                    for (std::size_t stream = 0; stream < kStreams; ++stream) {
                        const float * gradient = incoming.data()
                            + ((state * kStreams + stream) * kHeads + head)
                                * kHeadWidth;
                        const float * matrix = packed.data()
                            + (stream * kHeads + head) * kHeadWidth * kKeys;
                        float * destination = result.data()
                            + ((state * kHeads + head) * kStreams + stream)
                                * kKeys;
                        for (std::size_t key = 0; key < kKeys;
                             key += kLaneWidth) {
                            __m256 total = _mm256_setzero_ps();
                            for (std::size_t feature = 0;
                                 feature < kHeadWidth; ++feature) {
                                const float value = negate
                                    ? -gradient[feature] : gradient[feature];
                                total = _mm256_fmadd_ps(
                                    _mm256_set1_ps(value),
                                    _mm256_loadu_ps(
                                        matrix + feature * kKeys + key),
                                    total);
                            }
                            _mm256_storeu_ps(destination + key, total);
                        }
                    }
                }
            }
        });
    }
    for (std::thread & worker : workers) worker.join();
    return result;
}

std::vector<float> stream_major_control(const std::vector<float> & source) {
    std::vector<float> control(source.size());
    for (std::size_t state = 0; state < kStates; ++state) {
        for (std::size_t stream = 0; stream < kStreams; ++stream) {
            for (std::size_t head = 0; head < kHeads; ++head) {
                const float * input = source.data()
                    + ((state * kHeads + head) * kStreams + stream) * kKeys;
                float * output = control.data()
                    + ((state * kStreams + stream) * kHeads + head) * kKeys;
                std::copy(input, input + kKeys, output);
            }
        }
    }
    return control;
}

}  // namespace

int main(int argc, char ** argv) {
    try {
        if (argc != 6) {
            throw std::runtime_error(
                "usage: attention_value_transpose VALUE DATTENDED "
                "TREATMENT STREAM_MAJOR NEGATED");
        }
        const std::vector<float> value = read_bf16(
            argv[1], kStreams * kHeads * kKeys * kHeadWidth);
        const std::vector<float> incoming = read_bf16(
            argv[2], kStates * kStreams * kHeads * kHeadWidth);
        const std::vector<float> packed = pack_value(value);
        const std::vector<float> treatment = value_transpose(
            packed, incoming, false);
        write_bf16(argv[3], treatment);
        write_bf16(argv[4], stream_major_control(treatment));
        write_bf16(argv[5], value_transpose(packed, incoming, true));
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "open attention transpose failed: %s\n", error.what());
        return 1;
    }
}
