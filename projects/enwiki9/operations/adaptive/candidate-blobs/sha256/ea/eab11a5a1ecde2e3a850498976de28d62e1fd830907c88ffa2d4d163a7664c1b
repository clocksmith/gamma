#include <algorithm>
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

constexpr std::size_t kSliceOutputs = 128;
constexpr std::size_t kFullOutputs = 1024;
constexpr std::size_t kInputs = 1024;
constexpr std::size_t kStreams = 32;
constexpr std::size_t kStates = 64;
constexpr std::size_t kSamples = kStreams * kStates;
constexpr std::size_t kLanes = 8;

enum class Mode {
    post_add,
    prior_fma,
    prior_nonfused,
};

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
            throw std::runtime_error("non-finite w_o weight-gradient lane");
        }
        destination[lane] = bf16(lanes[lane]);
    }
}

std::vector<std::uint16_t> project(
    const std::vector<std::uint16_t> & inputs,
    const std::vector<std::uint16_t> & residuals,
    Mode mode,
    bool reverse_states,
    bool negate
) {
    if (inputs.size() != kSamples * kInputs ||
        residuals.size() != kSamples * kFullOutputs) {
        throw std::runtime_error("w_o weight-slice operand geometry differs");
    }
    std::vector<std::uint16_t> gradient(kInputs * kSliceOutputs, 0);
    for (std::size_t step = 0; step < kStates; ++step) {
        const std::size_t state = reverse_states ? kStates - 1 - step : step;
        for (std::size_t input = 0; input < kInputs; ++input) {
            for (std::size_t output = 0; output < kSliceOutputs;
                 output += kLanes) {
                std::uint16_t * prior_words =
                    gradient.data() + input * kSliceOutputs + output;
                const __m256 prior = load_bf16_8(prior_words);
                __m256 accumulated = mode == Mode::post_add
                    ? _mm256_setzero_ps() : prior;
                for (std::size_t stream = 0; stream < kStreams; ++stream) {
                    const std::size_t sample = state * kStreams + stream;
                    const float input_value = bf16_to_float(
                        inputs[sample * kInputs + input]);
                    __m256 residual = load_bf16_8(
                        residuals.data() + sample * kFullOutputs + output);
                    if (negate) {
                        residual = _mm256_xor_ps(
                            residual,
                            _mm256_castsi256_ps(_mm256_set1_epi32(
                                static_cast<int>(UINT32_C(0x80000000)))));
                    }
                    if (mode == Mode::prior_nonfused) {
                        accumulated = _mm256_add_ps(
                            accumulated,
                            _mm256_mul_ps(
                                _mm256_set1_ps(input_value), residual));
                    } else {
                        accumulated = _mm256_fmadd_ps(
                            _mm256_set1_ps(input_value), residual, accumulated);
                    }
                }
                if (mode == Mode::post_add) {
                    accumulated = _mm256_add_ps(accumulated, prior);
                }
                store_bf16_8(prior_words, accumulated);
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
    if (!output) throw std::runtime_error("cannot write w_o weight-slice output");
}

}  // namespace

int main(int argc, char ** argv) {
    try {
        if (argc != 8) {
            throw std::runtime_error(
                "usage: w_o_weight_slice_post_add INPUT RESIDUAL "
                "TREATMENT PRIOR NONFUSED REVERSE NEGATED");
        }
        const std::vector<std::uint16_t> inputs = read_words(
            argv[1], kSamples * kInputs);
        const std::vector<std::uint16_t> residuals = read_words(
            argv[2], kSamples * kFullOutputs);
        write_words(argv[3], project(
            inputs, residuals, Mode::post_add, false, false));
        write_words(argv[4], project(
            inputs, residuals, Mode::prior_fma, false, false));
        write_words(argv[5], project(
            inputs, residuals, Mode::prior_nonfused, false, false));
        write_words(argv[6], project(
            inputs, residuals, Mode::post_add, true, false));
        write_words(argv[7], project(
            inputs, residuals, Mode::post_add, false, true));
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "open w_o weight-slice failed: %s\n", error.what());
        return 1;
    }
}
