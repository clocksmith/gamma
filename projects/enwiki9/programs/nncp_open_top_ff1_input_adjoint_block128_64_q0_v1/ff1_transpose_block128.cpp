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
constexpr std::size_t kSamples = kStates * kStreams;
constexpr std::size_t kReduction = 6144;
constexpr std::size_t kDestination = 1024;
constexpr std::size_t kLaneWidth = 8;
constexpr std::size_t kReductionPanel = 128;
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

std::vector<float> pack_weights(const std::vector<float> & weights) {
    if (weights.size() != kReduction * kDestination) {
        throw std::runtime_error("FF1 weight geometry differs");
    }
    std::vector<float> packed(weights.size());
    for (std::size_t reduction = 0; reduction < kReduction; ++reduction) {
        for (std::size_t destination = 0; destination < kDestination;
             ++destination) {
            packed[reduction * kDestination + destination] =
                weights[destination * kReduction + reduction];
        }
    }
    return packed;
}

void write_bf16(const fs::path & path, const std::vector<float> & values) {
    std::vector<std::uint16_t> words(values.size());
    std::transform(values.begin(), values.end(), words.begin(), bf16);
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(words.data()),
                 static_cast<std::streamsize>(
                     words.size() * sizeof(words.front())));
    if (!output) throw std::runtime_error("cannot write BF16 FF1 adjoint");
}

std::vector<float> transpose(
    const std::vector<float> & packed,
    const std::vector<float> & incoming,
    std::size_t panel_width
) {
    if (packed.size() != kReduction * kDestination ||
        incoming.size() != kSamples * kReduction ||
        panel_width == 0 || kReduction % panel_width != 0) {
        throw std::runtime_error("FF1 transpose geometry differs");
    }
    std::vector<float> result(kSamples * kDestination);
    std::vector<std::thread> workers;
    for (std::size_t worker = 0; worker < kThreads; ++worker) {
        workers.emplace_back([&, worker] {
            for (std::size_t sample = worker; sample < kSamples;
                 sample += kThreads) {
                const float * gradient = incoming.data() + sample * kReduction;
                float * destination = result.data() + sample * kDestination;
                for (std::size_t feature = 0; feature < kDestination;
                     feature += kLaneWidth) {
                    __m256 total = _mm256_setzero_ps();
                    for (std::size_t panel = 0; panel < kReduction;
                         panel += panel_width) {
                        __m256 partial = _mm256_setzero_ps();
                        for (std::size_t reduction = panel;
                             reduction < panel + panel_width; ++reduction) {
                            partial = _mm256_fmadd_ps(
                                _mm256_set1_ps(gradient[reduction]),
                                _mm256_loadu_ps(
                                    packed.data()
                                    + reduction * kDestination + feature),
                                partial);
                        }
                        total = _mm256_add_ps(total, partial);
                    }
                    _mm256_storeu_ps(destination + feature, total);
                }
            }
        });
    }
    for (std::thread & worker : workers) worker.join();
    return result;
}

}  // namespace

int main(int argc, char ** argv) {
    try {
        if (argc != 5) {
            throw std::runtime_error(
                "usage: ff1_transpose_block128 WEIGHTS INCOMING BLOCK128 UNBLOCKED");
        }
        const std::vector<float> weights = read_bf16(
            argv[1], kReduction * kDestination);
        const std::vector<float> incoming = read_bf16(
            argv[2], kSamples * kReduction);
        const std::vector<float> packed = pack_weights(weights);
        write_bf16(argv[3], transpose(packed, incoming, kReductionPanel));
        write_bf16(argv[4], transpose(packed, incoming, kReduction));
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "FF1 transpose probe failed: %s\n", error.what());
        return 1;
    }
}
