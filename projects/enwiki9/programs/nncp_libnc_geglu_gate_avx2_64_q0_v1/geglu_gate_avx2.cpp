#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <immintrin.h>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace {

constexpr std::size_t kElements = 64 * 32 * 3072;
constexpr std::size_t kLanes = 8;

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

float round_bf16(float value) {
    return bf16_to_float(bf16(value));
}

std::vector<float> read_bf16(const fs::path & path) {
    const std::uintmax_t expected = kElements * sizeof(std::uint16_t);
    if (!fs::is_regular_file(path) || fs::file_size(path) != expected) {
        throw std::runtime_error("BF16 input geometry differs: " + path.string());
    }
    std::vector<std::uint16_t> words(kElements);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char *>(words.data()),
               static_cast<std::streamsize>(expected));
    if (!input) throw std::runtime_error("cannot read BF16 input");
    std::vector<float> values(kElements);
    std::transform(words.begin(), words.end(), values.begin(), bf16_to_float);
    return values;
}

void write_bf16(const fs::path & path, const std::vector<float> & values) {
    if (values.size() != kElements) {
        throw std::runtime_error("BF16 output geometry differs");
    }
    std::vector<std::uint16_t> words(values.size());
    std::transform(values.begin(), values.end(), words.begin(), bf16);
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(words.data()),
                 static_cast<std::streamsize>(words.size() * sizeof(words[0])));
    if (!output) throw std::runtime_error("cannot write BF16 output");
}

__m256 libnc_exp8(__m256 value) {
    const __m256 upper = _mm256_set1_ps(87.0F);
    const __m256 lower = _mm256_set1_ps(-88.0F);
    const __m256 log2e = _mm256_set1_ps(1.4426950216293335F);
    const __m256 minus_ln2_high = _mm256_set1_ps(-0.693359375F);
    const __m256 ln2_low = _mm256_set1_ps(0.00021219444170128554F);
    __m256 reduced = _mm256_min_ps(value, upper);
    reduced = _mm256_max_ps(reduced, lower);
    const __m256i exponent = _mm256_cvtps_epi32(
        _mm256_mul_ps(log2e, reduced));
    const __m256 exponent_float = _mm256_cvtepi32_ps(exponent);
    reduced = _mm256_fmadd_ps(minus_ln2_high, exponent_float, reduced);
    reduced = _mm256_fmadd_ps(ln2_low, exponent_float, reduced);
    __m256 polynomial = _mm256_set1_ps(0.00019841270113829523F);
    polynomial = _mm256_fmadd_ps(
        polynomial, reduced, _mm256_set1_ps(0.0013888889225199819F));
    polynomial = _mm256_fmadd_ps(
        polynomial, reduced, _mm256_set1_ps(0.008333333767950535F));
    polynomial = _mm256_fmadd_ps(
        polynomial, reduced, _mm256_set1_ps(0.0416666679084301F));
    polynomial = _mm256_fmadd_ps(
        polynomial, reduced, _mm256_set1_ps(0.1666666716337204F));
    polynomial = _mm256_fmadd_ps(
        polynomial, reduced, _mm256_set1_ps(0.5F));
    polynomial = _mm256_fmadd_ps(
        polynomial, _mm256_mul_ps(reduced, reduced), reduced);
    polynomial = _mm256_add_ps(polynomial, _mm256_set1_ps(1.0F));
    return _mm256_castsi256_ps(_mm256_add_epi32(
        _mm256_castps_si256(polynomial),
        _mm256_slli_epi32(exponent, 23)));
}

__m256 libnc_gelu_backward8(__m256 input, __m256 incoming) {
    const __m256 half = _mm256_set1_ps(0.5F);
    const __m256 one = _mm256_set1_ps(1.0F);
    const __m256 two = _mm256_set1_ps(2.0F);
    const __m256 minus_two = _mm256_set1_ps(-2.0F);
    const __m256 scale = _mm256_set1_ps(0.7978845834732056F);
    const __m256 cubic_scale = _mm256_set1_ps(0.035677406936883926F);
    const __m256 three_cubic_scale =
        _mm256_set1_ps(0.10703222453594208F);

    __m256 argument = _mm256_mul_ps(input, cubic_scale);
    argument = _mm256_fmadd_ps(argument, input, scale);
    argument = _mm256_mul_ps(argument, input);
    const __m256 exponential = libnc_exp8(
        _mm256_mul_ps(argument, minus_two));
    const __m256 tanh_value = _mm256_sub_ps(
        _mm256_div_ps(two, _mm256_add_ps(exponential, one)), one);
    __m256 argument_derivative = _mm256_mul_ps(
        input, three_cubic_scale);
    argument_derivative = _mm256_fmadd_ps(
        argument_derivative, input, scale);
    const __m256 one_plus_tanh = _mm256_add_ps(tanh_value, one);
    const __m256 one_minus_tanh_square = _mm256_fnmadd_ps(
        tanh_value, tanh_value, one);
    __m256 derivative = _mm256_mul_ps(input, one_minus_tanh_square);
    derivative = _mm256_fmadd_ps(
        derivative, argument_derivative, one_plus_tanh);
    derivative = _mm256_mul_ps(derivative, half);
    return _mm256_mul_ps(derivative, incoming);
}

float gelu(float value) {
    constexpr float cubic = 0.044715F;
    constexpr float scale = 0.7978845608028654F;
    const float argument = scale *
        (value + cubic * value * value * value);
    const float tanh_value = argument >= 8.0F ? 1.0F : std::tanh(argument);
    return 0.5F * value * (1.0F + tanh_value);
}

}  // namespace

int main(int argc, char ** argv) {
    try {
        if (argc != 6) {
            throw std::runtime_error(
                "usage: geglu_gate_avx2 GATE VALUE UPSTREAM GATE_OUT VALUE_OUT");
        }
        const std::vector<float> gate = read_bf16(argv[1]);
        const std::vector<float> value = read_bf16(argv[2]);
        const std::vector<float> upstream = read_bf16(argv[3]);
        std::vector<float> gate_upstream(kElements);
        std::vector<float> gate_output(kElements);
        std::vector<float> value_output(kElements);
        for (std::size_t index = 0; index < kElements; ++index) {
            gate_upstream[index] = round_bf16(upstream[index] * value[index]);
            value_output[index] = round_bf16(
                upstream[index] * round_bf16(gelu(gate[index])));
        }
        for (std::size_t index = 0; index < kElements; index += kLanes) {
            const __m256 result = libnc_gelu_backward8(
                _mm256_loadu_ps(gate.data() + index),
                _mm256_loadu_ps(gate_upstream.data() + index));
            _mm256_storeu_ps(gate_output.data() + index, result);
        }
        write_bf16(argv[4], gate_output);
        write_bf16(argv[5], value_output);
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "GEGLU gate attribution failed: %s\n", error.what());
        return 1;
    }
}
