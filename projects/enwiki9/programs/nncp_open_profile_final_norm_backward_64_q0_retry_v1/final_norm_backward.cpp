#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <immintrin.h>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace {

constexpr std::uint32_t kFileMagic = 0x23f4aefbU;
constexpr std::uint32_t kTensorMagic = 0x23f4aefaU;
constexpr std::size_t kStreams = 32;
constexpr std::size_t kStates = 64;
constexpr std::size_t kSamples = kStreams * kStates;
constexpr std::size_t kWidth = 1024;
constexpr std::size_t kReductionChunk = 128;
constexpr float kEpsilon = 1.0e-5F;

std::uint32_t read_u32(std::ifstream & input) {
    std::array<unsigned char, 4> bytes {};
    input.read(reinterpret_cast<char *>(bytes.data()), bytes.size());
    if (!input) throw std::runtime_error("truncated container u32");
    return static_cast<std::uint32_t>(bytes[0]) |
        (static_cast<std::uint32_t>(bytes[1]) << 8U) |
        (static_cast<std::uint32_t>(bytes[2]) << 16U) |
        (static_cast<std::uint32_t>(bytes[3]) << 24U);
}

std::size_t type_size(std::uint32_t type) {
    constexpr std::array<std::size_t, 9> sizes {4, 2, 2, 1, 2, 4, 1, 2, 4};
    if (type >= sizes.size()) throw std::runtime_error("unsupported container type");
    return sizes[type];
}

struct TensorHeader {
    std::uint32_t type;
    std::vector<std::uint32_t> dimensions;
    std::uint64_t elements;
    std::string name;
};

TensorHeader read_header(std::ifstream & input) {
    if (read_u32(input) != kTensorMagic) {
        throw std::runtime_error("invalid tensor marker");
    }
    TensorHeader header;
    header.type = read_u32(input);
    const std::uint32_t rank = read_u32(input);
    const std::uint32_t name_size = read_u32(input);
    header.elements = 1;
    for (std::uint32_t axis = 0; axis < rank; ++axis) {
        const std::uint32_t dimension = read_u32(input);
        header.dimensions.push_back(dimension);
        header.elements *= dimension;
    }
    header.name.resize(name_size);
    input.read(header.name.data(), header.name.size());
    if (!input) throw std::runtime_error("truncated tensor name");
    return header;
}

void skip_payload(std::ifstream & input, const TensorHeader & header) {
    const std::uint64_t bytes = header.elements * type_size(header.type);
    if (bytes > static_cast<std::uint64_t>(
            std::numeric_limits<std::streamoff>::max())) {
        throw std::runtime_error("tensor is too large to seek");
    }
    input.seekg(static_cast<std::streamoff>(bytes), std::ios::cur);
}

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

std::vector<float> read_gain(const fs::path & path) {
    std::ifstream input(path, std::ios::binary);
    if (!input || read_u32(input) != kFileMagic) {
        throw std::runtime_error("invalid parameter container");
    }
    const std::uint32_t config_size = read_u32(input);
    input.seekg(config_size, std::ios::cur);
    while (input.peek() != std::ifstream::traits_type::eof()) {
        const TensorHeader header = read_header(input);
        if (header.name == "ln_g_40") {
            if (header.type != 1 ||
                header.dimensions != std::vector<std::uint32_t>({kWidth})) {
                throw std::runtime_error("ln_g_40 tensor contract differs");
            }
            std::vector<std::uint16_t> words(kWidth);
            input.read(reinterpret_cast<char *>(words.data()),
                       static_cast<std::streamsize>(
                           words.size() * sizeof(words[0])));
            if (!input) throw std::runtime_error("truncated ln_g_40 tensor");
            std::vector<float> values(kWidth);
            std::transform(words.begin(), words.end(), values.begin(),
                           bf16_to_float);
            return values;
        }
        skip_payload(input, header);
    }
    throw std::runtime_error("missing ln_g_40 tensor");
}

std::vector<float> read_bf16(const fs::path & path, std::size_t count) {
    const std::uintmax_t expected = count * sizeof(std::uint16_t);
    if (!fs::is_regular_file(path) || fs::file_size(path) != expected) {
        throw std::runtime_error("BF16 tensor geometry differs: " + path.string());
    }
    std::vector<std::uint16_t> words(count);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char *>(words.data()),
               static_cast<std::streamsize>(expected));
    if (!input) throw std::runtime_error("truncated BF16 tensor");
    std::vector<float> values(count);
    std::transform(words.begin(), words.end(), values.begin(), bf16_to_float);
    return values;
}

std::vector<float> read_f32(const fs::path & path, std::size_t count) {
    const std::uintmax_t expected = count * sizeof(float);
    if (!fs::is_regular_file(path) || fs::file_size(path) != expected) {
        throw std::runtime_error("F32 tensor geometry differs: " + path.string());
    }
    std::vector<float> values(count);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char *>(values.data()),
               static_cast<std::streamsize>(expected));
    if (!input || !std::all_of(values.begin(), values.end(),
            [](float value) { return std::isfinite(value); })) {
        throw std::runtime_error("invalid F32 tensor: " + path.string());
    }
    return values;
}

std::vector<float> read_norm_inputs(const fs::path & root) {
    std::vector<float> result(kSamples * kWidth);
    for (std::size_t stream = 0; stream < kStreams; ++stream) {
        char name[32];
        std::snprintf(name, sizeof(name), "stream_%02zu", stream);
        const std::vector<float> current = read_f32(
            root / name / "final_norm_input.f32", kStates * kWidth);
        for (std::size_t state = 0; state < kStates; ++state) {
            const std::size_t sample = stream + kStreams * state;
            std::copy_n(current.data() + state * kWidth, kWidth,
                        result.data() + sample * kWidth);
        }
    }
    for (float value : result) {
        std::uint32_t bits;
        std::memcpy(&bits, &value, sizeof(bits));
        if ((bits & 0xffffU) != 0) {
            throw std::runtime_error("final RMSNorm input is not BF16-exact");
        }
    }
    return result;
}

void write_bf16(const fs::path & path, const std::vector<float> & values) {
    if (!std::all_of(values.begin(), values.end(),
            [](float value) { return std::isfinite(value); })) {
        throw std::runtime_error("non-finite backward output");
    }
    std::vector<std::uint16_t> output(values.size());
    std::transform(values.begin(), values.end(), output.begin(), bf16);
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    stream.write(reinterpret_cast<const char *>(output.data()),
                 static_cast<std::streamsize>(output.size() * sizeof(output[0])));
    if (!stream) throw std::runtime_error("cannot write BF16 gradient");
}

float reduce_products64(const float * left, const float * right) {
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
    total = _mm256_add_ps(total,
                          _mm256_permute2f128_ps(total, total, 0x01));
    return _mm_cvtss_f32(_mm256_castps256_ps128(total));
}

float reduce_products(const float * left, const float * right) {
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
    for (int count = blocks; count; count >>= 1) ++slots;
    for (int slot = 0; slot < slots; ++slot) total += partials[slot];
    return total;
}

struct BackwardResult {
    std::vector<float> gain_gradient;
    std::vector<float> bias_gradient;
    std::vector<float> input_residual;
    std::vector<float> input_bias_projection;
};

BackwardResult backward(
    const std::vector<float> & norm_input,
    const std::vector<float> & incoming,
    const std::vector<float> & gain
) {
    if (norm_input.size() != kSamples * kWidth ||
        incoming.size() != kSamples * kWidth || gain.size() != kWidth) {
        throw std::runtime_error("final RMSNorm backward geometry differs");
    }
    BackwardResult result {
        std::vector<float>(kWidth, 0.0F),
        std::vector<float>(kWidth, 0.0F),
        std::vector<float>(kSamples * kWidth),
        std::vector<float>(kWidth, 0.0F),
    };
    std::vector<float> unit(kWidth);
    std::vector<float> upstream(kWidth);
    std::vector<float> normalized(kSamples * kWidth);
    std::vector<float> ones(kWidth, 1.0F);
    for (std::size_t sample = 0; sample < kSamples; ++sample) {
        const float * source = norm_input.data() + sample * kWidth;
        const float * gradient = incoming.data() + sample * kWidth;
        const float sum_squares = reduce_products(source, source);
        const float inverse = 1.0F /
            std::sqrt(sum_squares / static_cast<float>(kWidth) + kEpsilon);
        for (std::size_t feature = 0; feature < kWidth; ++feature) {
            unit[feature] = round_bf16(source[feature] * inverse);
            normalized[sample * kWidth + feature] = unit[feature];
            upstream[feature] = gradient[feature] * gain[feature];
            result.bias_gradient[feature] += gradient[feature];
        }
        const float mean_upstream = reduce_products(
            upstream.data(), ones.data()) / static_cast<float>(kWidth);
        const float mean_product = reduce_products(
            upstream.data(), unit.data()) / static_cast<float>(kWidth);
        float * destination = result.input_residual.data() + sample * kWidth;
        for (std::size_t feature = 0; feature < kWidth; feature += 8) {
            const __m256 current = _mm256_loadu_ps(upstream.data() + feature);
            const __m256 normalized = _mm256_loadu_ps(unit.data() + feature);
            const __m256 mean_centered = _mm256_sub_ps(
                current, _mm256_set1_ps(mean_upstream));
            const __m256 centered = _mm256_fnmadd_ps(
                normalized, _mm256_set1_ps(mean_product), mean_centered);
            const __m256 values = _mm256_mul_ps(
                _mm256_set1_ps(inverse), centered);
            _mm256_storeu_ps(destination + feature, values);
        }
        for (std::size_t feature = 0; feature < kWidth; ++feature) {
            destination[feature] = round_bf16(destination[feature]);
            result.input_bias_projection[feature] += destination[feature];
        }
    }
    for (std::size_t feature = 0; feature < kWidth; ++feature) {
        float accumulated = 0.0F;
        for (std::size_t chunk = 0; chunk < kSamples;
             chunk += kReductionChunk) {
            float partial = 0.0F;
            for (std::size_t sample = chunk;
                 sample < chunk + kReductionChunk; ++sample) {
                partial = std::fma(
                    incoming[sample * kWidth + feature],
                    normalized[sample * kWidth + feature],
                    partial);
            }
            accumulated += partial;
        }
        result.gain_gradient[feature] = accumulated;
    }
    return result;
}

}  // namespace

int main(int argc, char ** argv) {
    try {
        if (argc != 9) {
            throw std::runtime_error(
                "usage: final_norm_backward PARAMETERS OPEN_ROOT HIDDEN_RESIDUAL "
                "OUT_LN_G OUT_LN_B OUT_INPUT_RESIDUAL OUT_FF_BIAS CONTROL_FF_BIAS");
        }
        const std::vector<float> gain = read_gain(argv[1]);
        const std::vector<float> norm_input = read_norm_inputs(argv[2]);
        const std::vector<float> incoming = read_bf16(
            argv[3], kSamples * kWidth);
        const BackwardResult observed = backward(norm_input, incoming, gain);
        std::vector<float> negated(incoming.size());
        std::transform(incoming.begin(), incoming.end(), negated.begin(),
                       [](float value) { return -value; });
        const BackwardResult control = backward(norm_input, negated, gain);
        write_bf16(argv[4], observed.gain_gradient);
        write_bf16(argv[5], observed.bias_gradient);
        write_bf16(argv[6], observed.input_residual);
        write_bf16(argv[7], observed.input_bias_projection);
        write_bf16(argv[8], control.input_bias_projection);
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "final RMSNorm backward failed: %s\n", error.what());
        return 1;
    }
}

