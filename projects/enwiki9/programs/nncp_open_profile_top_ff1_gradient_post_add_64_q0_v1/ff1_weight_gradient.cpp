#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <immintrin.h>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace {

constexpr std::size_t kOutputs = 6144;
constexpr std::size_t kInputs = 1024;
constexpr std::size_t kStreams = 32;
constexpr std::size_t kStates = 64;
constexpr std::size_t kSamples = kStreams * kStates;
constexpr std::size_t kLanes = 8;

std::vector<std::uint16_t> read_words(const fs::path & path,
                                      std::size_t count) {
    if (!fs::is_regular_file(path) ||
        fs::file_size(path) != count * sizeof(std::uint16_t)) {
        throw std::runtime_error("BF16 input geometry differs: " + path.string());
    }
    std::vector<std::uint16_t> words(count);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char *>(words.data()),
               static_cast<std::streamsize>(words.size() * sizeof(words[0])));
    if (!input) throw std::runtime_error("truncated BF16 input");
    return words;
}

float bf16_to_float(std::uint16_t word) {
    const std::uint32_t bits = static_cast<std::uint32_t>(word) << 16U;
    float value;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

std::uint16_t bf16(float value) {
    std::uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    const std::uint32_t rounding = 0x7fffU + ((bits >> 16U) & 1U);
    return static_cast<std::uint16_t>((bits + rounding) >> 16U);
}

__m256 load_bf16_8(const std::uint16_t * words) {
    const __m128i packed = _mm_loadu_si128(
        reinterpret_cast<const __m128i *>(words));
    const __m256i expanded = _mm256_slli_epi32(
        _mm256_cvtepu16_epi32(packed), 16);
    return _mm256_castsi256_ps(expanded);
}

void store_bf16_8(std::uint16_t * destination, __m256 values) {
    alignas(32) std::array<float, kLanes> lanes {};
    _mm256_store_ps(lanes.data(), values);
    for (std::size_t lane = 0; lane < kLanes; ++lane) {
        if (!std::isfinite(lanes[lane])) {
            throw std::runtime_error("non-finite FF1 weight-gradient lane");
        }
        destination[lane] = bf16(lanes[lane]);
    }
}

std::vector<std::uint16_t> project(
    const std::vector<std::uint16_t> & inputs,
    const std::vector<std::uint16_t> & residuals
) {
    if (inputs.size() != kSamples * kInputs ||
        residuals.size() != kSamples * kOutputs) {
        throw std::runtime_error("FF1 weight-gradient operand geometry differs");
    }
    std::vector<std::uint16_t> gradient(kInputs * kOutputs, 0);
    for (std::size_t state = 0; state < kStates; ++state) {
        for (std::size_t input = 0; input < kInputs; ++input) {
            for (std::size_t output = 0; output < kOutputs;
                 output += kLanes) {
                std::uint16_t * prior_words =
                    gradient.data() + input * kOutputs + output;
                const __m256 prior = load_bf16_8(prior_words);
                __m256 dot = _mm256_setzero_ps();
                for (std::size_t stream = 0; stream < kStreams; ++stream) {
                    const std::size_t sample = state * kStreams + stream;
                    const float input_value = bf16_to_float(
                        inputs[sample * kInputs + input]);
                    const __m256 residual = load_bf16_8(
                        residuals.data() + sample * kOutputs + output);
                    dot = _mm256_fmadd_ps(
                        _mm256_set1_ps(input_value), residual, dot);
                }
                store_bf16_8(prior_words, _mm256_add_ps(dot, prior));
            }
        }
    }
    return gradient;
}

void write_words(const fs::path & path,
                 const std::vector<std::uint16_t> & words) {
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(words.data()),
                 static_cast<std::streamsize>(words.size() * sizeof(words[0])));
    if (!output) throw std::runtime_error("cannot write FF1 weight gradient");
}

}  // namespace

int main(int argc, char ** argv) {
    try {
        if (argc != 4) {
            throw std::runtime_error(
                "usage: ff1_weight_gradient INPUT RESIDUAL OUTPUT");
        }
        const std::vector<std::uint16_t> inputs = read_words(
            argv[1], kSamples * kInputs);
        const std::vector<std::uint16_t> residuals = read_words(
            argv[2], kSamples * kOutputs);
        write_words(argv[3], project(inputs, residuals));
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "open FF1 weight gradient failed: %s\n", error.what());
        return 1;
    }
}
