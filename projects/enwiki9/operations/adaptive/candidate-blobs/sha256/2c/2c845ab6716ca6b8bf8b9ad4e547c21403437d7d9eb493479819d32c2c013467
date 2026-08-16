#include <algorithm>
#include <cstdio>
#include <cstdint>
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
constexpr std::size_t kWidth = 1024;
constexpr std::size_t kInner = 3072;
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

std::vector<float> read_bf16(const fs::path &path, std::size_t count) {
    const std::uintmax_t expected = count * sizeof(std::uint16_t);
    if (!fs::is_regular_file(path) || fs::file_size(path) != expected)
        throw std::runtime_error("BF16 input geometry differs: " + path.string());
    std::vector<std::uint16_t> words(count);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char *>(words.data()),
               static_cast<std::streamsize>(expected));
    if (!input)
        throw std::runtime_error("truncated BF16 input");
    std::vector<float> values(count);
    std::transform(words.begin(), words.end(), values.begin(), bf16_to_float);
    return values;
}

std::vector<float> pack_weights(const std::vector<float> &weights) {
    if (weights.size() != kInner * kWidth)
        throw std::runtime_error("FF2 weight geometry differs");
    std::vector<float> packed(weights.size());
    for (std::size_t output = 0; output < kWidth; ++output) {
        for (std::size_t inner = 0; inner < kInner; ++inner)
            packed[output * kInner + inner] =
                weights[inner * kWidth + output];
    }
    return packed;
}

void write_bf16(const fs::path &path, const std::vector<float> &values) {
    std::vector<std::uint16_t> words(values.size());
    std::transform(values.begin(), values.end(), words.begin(), bf16);
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(words.data()),
                 static_cast<std::streamsize>(
                     words.size() * sizeof(words.front())));
    if (!output)
        throw std::runtime_error("cannot write BF16 transpose adjoint");
}

std::vector<float> block128_transpose(
    const std::vector<float> &packed,
    const std::vector<float> &incoming
) {
    if (packed.size() != kWidth * kInner ||
        incoming.size() != kSamples * kWidth)
        throw std::runtime_error("FF2 transpose geometry differs");
    std::vector<float> result(kSamples * kInner);
    std::vector<std::thread> workers;
    for (std::size_t worker = 0; worker < kThreads; ++worker) {
        workers.emplace_back([&, worker] {
            for (std::size_t sample = worker; sample < kSamples;
                 sample += kThreads) {
                const float *gradient = incoming.data() + sample * kWidth;
                float *destination = result.data() + sample * kInner;
                for (std::size_t inner = 0; inner < kInner;
                     inner += kLaneWidth) {
                    __m256 total = _mm256_setzero_ps();
                    for (std::size_t panel = 0; panel < kWidth;
                         panel += kReductionPanel) {
                        __m256 partial = _mm256_setzero_ps();
                        for (std::size_t output = panel;
                             output < panel + kReductionPanel; ++output) {
                            partial = _mm256_fmadd_ps(
                                _mm256_set1_ps(gradient[output]),
                                _mm256_loadu_ps(
                                    packed.data() + output * kInner + inner),
                                partial);
                        }
                        total = _mm256_add_ps(total, partial);
                    }
                    _mm256_storeu_ps(destination + inner, total);
                }
            }
        });
    }
    for (std::thread &worker : workers)
        worker.join();
    return result;
}

}  // namespace

int main(int argc, char **argv) {
    try {
        if (argc != 4)
            throw std::runtime_error(
                "usage: ff2_transpose_block128 WEIGHTS INCOMING OUTPUT");
        const std::vector<float> weights = read_bf16(
            argv[1], kInner * kWidth);
        const std::vector<float> incoming = read_bf16(
            argv[2], kSamples * kWidth);
        write_bf16(
            argv[3], block128_transpose(pack_weights(weights), incoming));
        return 0;
    } catch (const std::exception &error) {
        std::fprintf(stderr, "FF2 transpose 128-panel probe failed: %s\n",
                     error.what());
        return 1;
    }
}
