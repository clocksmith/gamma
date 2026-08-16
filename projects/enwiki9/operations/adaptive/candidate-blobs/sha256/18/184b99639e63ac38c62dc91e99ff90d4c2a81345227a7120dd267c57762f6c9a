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

constexpr std::size_t kStates = 64;
constexpr std::size_t kStreams = 32;
constexpr std::size_t kSamples = kStates * kStreams;
constexpr std::size_t kWidth = 1024;
constexpr float kEpsilon = 1.0e-5F;

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

std::vector<float> read_bf16(const fs::path &path, std::size_t count) {
    const std::uintmax_t expected = count * sizeof(std::uint16_t);
    if (!fs::is_regular_file(path) || fs::file_size(path) != expected)
        throw std::runtime_error("BF16 input geometry differs: " + path.string());
    std::vector<std::uint16_t> words(count);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char *>(words.data()),
               static_cast<std::streamsize>(expected));
    if (!input)
        throw std::runtime_error("truncated BF16 input: " + path.string());
    std::vector<float> values(words.size());
    for (std::size_t index = 0; index < words.size(); ++index)
        values[index] = bf16_to_float(words[index]);
    return values;
}

void write_bf16(const fs::path &path, const std::vector<float> &values) {
    std::vector<std::uint16_t> words(values.size());
    for (std::size_t index = 0; index < values.size(); ++index)
        words[index] = bf16(values[index]);
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(words.data()),
                 static_cast<std::streamsize>(
                     words.size() * sizeof(words.front())));
    if (!output)
        throw std::runtime_error("cannot write BF16 output: " + path.string());
}

float reduce_products64(const float *left, const float *right) {
    __m256 x[8];
    for (int index = 0; index < 8; ++index) {
        x[index] = _mm256_mul_ps(
            _mm256_loadu_ps(left + index * 8),
            _mm256_loadu_ps(right + index * 8));
    }
    const __m256 u01 = _mm256_unpacklo_ps(x[0], x[1]);
    const __m256 u23 = _mm256_unpacklo_ps(x[2], x[3]);
    const __m256 h01 = _mm256_unpackhi_ps(x[0], x[1]);
    const __m256 h23 = _mm256_unpackhi_ps(x[2], x[3]);
    const __m256 u45 = _mm256_unpacklo_ps(x[4], x[5]);
    const __m256 u67 = _mm256_unpacklo_ps(x[6], x[7]);
    const __m256 h45 = _mm256_unpackhi_ps(x[4], x[5]);
    const __m256 h67 = _mm256_unpackhi_ps(x[6], x[7]);
    const __m256 a = _mm256_shuffle_ps(u01, u23, 0xee);
    const __m256 b = _mm256_shuffle_ps(u45, u67, 0x44);
    const __m256 c = _mm256_shuffle_ps(u01, u23, 0x44);
    const __m256 d = _mm256_shuffle_ps(u45, u67, 0xee);
    const __m256 e = _mm256_shuffle_ps(h01, h23, 0x44);
    const __m256 f = _mm256_shuffle_ps(h45, h67, 0x44);
    const __m256 g = _mm256_shuffle_ps(h01, h23, 0xee);
    const __m256 h = _mm256_shuffle_ps(h45, h67, 0xee);
    const __m256 low_a = _mm256_insertf128_ps(
        a, _mm256_castps256_ps128(d), 1);
    const __m256 low_c = _mm256_insertf128_ps(
        c, _mm256_castps256_ps128(b), 1);
    const __m256 low_g = _mm256_insertf128_ps(
        g, _mm256_castps256_ps128(h), 1);
    const __m256 low_e = _mm256_insertf128_ps(
        e, _mm256_castps256_ps128(f), 1);
    const __m256 high_g = _mm256_permute2f128_ps(g, h, 0x31);
    const __m256 first = _mm256_add_ps(low_a, low_c);
    const __m256 second = _mm256_add_ps(low_g, low_e);
    const __m256 high_a = _mm256_permute2f128_ps(a, d, 0x31);
    const __m256 high_c = _mm256_permute2f128_ps(c, b, 0x31);
    const __m256 high_e = _mm256_permute2f128_ps(e, f, 0x31);
    const __m256 third = _mm256_add_ps(high_a, high_c);
    const __m256 fourth = _mm256_add_ps(high_g, high_e);
    __m256 total = _mm256_add_ps(third, fourth);
    total = _mm256_add_ps(_mm256_add_ps(first, second), total);
    total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0xb1));
    total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0x4e));
    total = _mm256_add_ps(
        total, _mm256_permute2f128_ps(total, total, 0x01));
    return _mm_cvtss_f32(_mm256_castps256_ps128(total));
}

float reduce_products(const float *left, const float *right) {
    std::array<float, 16> partials {};
    int blocks = 0;
    for (std::size_t index = 0; index < kWidth; index += 64, ++blocks) {
        float block_sum = reduce_products64(left + index, right + index);
        int slot = 0;
        while (blocks & (1 << slot)) {
            block_sum += partials[slot];
            partials[slot++] = 0.0F;
        }
        partials[slot] = block_sum;
    }
    float total = 0.0F;
    int slots = 0;
    for (int count = blocks; count; count >>= 1)
        ++slots;
    for (int slot = 0; slot < slots; ++slot)
        total += partials[slot];
    return total;
}

float reduce_streaming_products(const float *left, const float *right) {
    __m256 total = _mm256_setzero_ps();
    for (std::size_t index = 0; index < kWidth; index += 8) {
        total = _mm256_fmadd_ps(
            _mm256_loadu_ps(left + index),
            _mm256_loadu_ps(right + index), total);
    }
    total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0xb1));
    total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0x4e));
    total = _mm256_add_ps(
        total, _mm256_permute2f128_ps(total, total, 0x01));
    return _mm_cvtss_f32(_mm256_castps256_ps128(total));
}

enum class Variant {
    generic_dot_mean_scaled,
    stream_dot_mean_scaled,
    generic_dot_width_scaled,
    stream_dot_width_scaled,
};

bool uses_streaming_dot(Variant variant) {
    return variant == Variant::stream_dot_mean_scaled ||
           variant == Variant::stream_dot_width_scaled;
}

bool uses_width_scaling(Variant variant) {
    return variant == Variant::generic_dot_width_scaled ||
           variant == Variant::stream_dot_width_scaled;
}

std::vector<float> evaluate(const std::vector<float> &source,
                            const std::vector<float> &normalized,
                            const std::vector<float> &incoming,
                            Variant variant, bool negate) {
    std::vector<float> result(source.size());
    std::vector<float> current(kWidth);
    std::vector<float> ones(kWidth, 1.0F);
    for (std::size_t sample = 0; sample < kSamples; ++sample) {
        const float *x = source.data() + sample * kWidth;
        const float *unit = normalized.data() + sample * kWidth;
        const float *gradient = incoming.data() + sample * kWidth;
        for (std::size_t feature = 0; feature < kWidth; ++feature)
            current[feature] = negate ? -gradient[feature] : gradient[feature];
        const float inverse = 1.0F / std::sqrt(
            reduce_products(x, x) / static_cast<float>(kWidth) + kEpsilon);
        const float upstream_sum =
            reduce_products(current.data(), ones.data());
        const float product_sum = uses_streaming_dot(variant)
            ? reduce_streaming_products(current.data(), unit)
            : reduce_products(current.data(), unit);
        float *destination = result.data() + sample * kWidth;
        for (std::size_t feature = 0; feature < kWidth; feature += 8) {
            const __m256 upstream =
                _mm256_loadu_ps(current.data() + feature);
            const __m256 normalized_values =
                _mm256_loadu_ps(unit + feature);
            __m256 centered;
            __m256 scale;
            if (uses_width_scaling(variant)) {
                centered = _mm256_fmsub_ps(
                    upstream, _mm256_set1_ps(static_cast<float>(kWidth)),
                    _mm256_set1_ps(upstream_sum));
                centered = _mm256_fnmadd_ps(
                    normalized_values, _mm256_set1_ps(product_sum), centered);
                scale = _mm256_set1_ps(
                    inverse / static_cast<float>(kWidth));
            } else {
                const float mean_upstream =
                    upstream_sum / static_cast<float>(kWidth);
                const float mean_product =
                    product_sum / static_cast<float>(kWidth);
                centered = _mm256_fnmadd_ps(
                    normalized_values, _mm256_set1_ps(mean_product),
                    _mm256_sub_ps(
                        upstream, _mm256_set1_ps(mean_upstream)));
                scale = _mm256_set1_ps(inverse);
            }
            const __m256 values = _mm256_mul_ps(scale, centered);
            _mm256_storeu_ps(destination + feature, values);
        }
        for (std::size_t feature = 0; feature < kWidth; ++feature)
            destination[feature] = round_bf16(destination[feature]);
    }
    return result;
}

}  // namespace

int main(int argc, char **argv) {
    try {
        if (argc != 5)
            throw std::runtime_error(
                "usage: final_rmsnorm_order INPUT_BF16 NORMALIZED_BF16 "
                "INCOMING_BF16 OUTPUT_DIRECTORY");
        const std::vector<float> source = read_bf16(
            argv[1], kSamples * kWidth);
        const std::vector<float> normalized = read_bf16(
            argv[2], kSamples * kWidth);
        const std::vector<float> incoming = read_bf16(
            argv[3], kSamples * kWidth);
        const fs::path output = argv[4];
        if (!fs::is_directory(output))
            throw std::runtime_error("output directory is missing");
        const std::array<std::pair<const char *, Variant>, 4> variants {{
            {"generic_dot_mean_scaled", Variant::generic_dot_mean_scaled},
            {"stream_dot_mean_scaled", Variant::stream_dot_mean_scaled},
            {"generic_dot_width_scaled", Variant::generic_dot_width_scaled},
            {"stream_dot_width_scaled", Variant::stream_dot_width_scaled},
        }};
        for (const auto &[name, variant] : variants)
            write_bf16(output / (std::string(name) + ".bf16"),
                       evaluate(source, normalized, incoming, variant, false));
        write_bf16(output / "negated_control.bf16",
                   evaluate(source, normalized, incoming,
                            Variant::stream_dot_width_scaled, true));
        return 0;
    } catch (const std::exception &error) {
        std::fprintf(stderr, "final RMSNorm reduction-scale probe failed: %s\n",
                     error.what());
        return 1;
    }
}
