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
#include <thread>
#include <vector>

namespace fs = std::filesystem;

namespace {

constexpr std::uint32_t kFileMagic = 0x23f4aefbU;
constexpr std::uint32_t kTensorMagic = 0x23f4aefaU;
constexpr std::size_t kStreams = 32;
constexpr std::size_t kStates = 64;
constexpr std::size_t kSamples = kStreams * kStates;
constexpr std::size_t kWidth = 1024;
constexpr std::size_t kInner = 3072;
constexpr std::size_t kFf1Width = 2 * kInner;
constexpr std::size_t kLaneWidth = 8;
constexpr std::size_t kReductionPanel = 128;
constexpr std::size_t kThreads = 4;
constexpr float kGeluCubic = 0.044715F;
constexpr float kGeluScale = 0.7978845608028654F;

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

std::vector<float> read_ff2(const fs::path & path) {
    std::ifstream input(path, std::ios::binary);
    if (!input || read_u32(input) != kFileMagic) {
        throw std::runtime_error("invalid parameter container");
    }
    const std::uint32_t config_size = read_u32(input);
    input.seekg(config_size, std::ios::cur);
    while (input.peek() != std::ifstream::traits_type::eof()) {
        const TensorHeader header = read_header(input);
        if (header.name == "ff2_19") {
            if (header.type != 1 || header.dimensions !=
                std::vector<std::uint32_t>({kWidth, kInner})) {
                throw std::runtime_error("ff2_19 tensor contract differs");
            }
            std::vector<std::uint16_t> words(kWidth * kInner);
            input.read(reinterpret_cast<char *>(words.data()),
                       static_cast<std::streamsize>(
                           words.size() * sizeof(words[0])));
            if (!input) throw std::runtime_error("truncated ff2_19 tensor");
            std::vector<float> values(words.size());
            std::transform(words.begin(), words.end(), values.begin(),
                           bf16_to_float);
            return values;
        }
        skip_payload(input, header);
    }
    throw std::runtime_error("missing ff2_19 tensor");
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

std::vector<float> read_ff1_output(const fs::path & root) {
    std::vector<float> result(kSamples * kFf1Width);
    for (std::size_t stream = 0; stream < kStreams; ++stream) {
        char name[32];
        std::snprintf(name, sizeof(name), "stream_%02zu", stream);
        const std::vector<float> current = read_f32(
            root / name / "layer_19_ff1_output.f32", kStates * kFf1Width);
        for (std::size_t state = 0; state < kStates; ++state) {
            const std::size_t sample = stream + kStreams * state;
            std::copy_n(current.data() + state * kFf1Width, kFf1Width,
                        result.data() + sample * kFf1Width);
        }
    }
    for (float value : result) {
        std::uint32_t bits;
        std::memcpy(&bits, &value, sizeof(bits));
        if ((bits & 0xffffU) != 0) {
            throw std::runtime_error("layer-19 FF1 output is not BF16-exact");
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

std::vector<float> pack_ff2(const std::vector<float> & weights) {
    if (weights.size() != kInner * kWidth) {
        throw std::runtime_error("FF2 weight geometry differs");
    }
    std::vector<float> packed(weights.size());
    for (std::size_t output = 0; output < kWidth; ++output) {
        for (std::size_t inner = 0; inner < kInner; ++inner) {
            packed[output * kInner + inner] =
                weights[inner * kWidth + output];
        }
    }
    return packed;
}

float gelu(float value) {
    const float argument = kGeluScale *
        (value + kGeluCubic * value * value * value);
    const float tanh_value = argument >= 8.0F ? 1.0F : std::tanh(argument);
    return 0.5F * value * (1.0F + tanh_value);
}

float gelu_derivative(float value) {
    const float square = value * value;
    const float argument = kGeluScale *
        (value + kGeluCubic * value * square);
    const float tanh_value = argument >= 8.0F ? 1.0F : std::tanh(argument);
    const float argument_derivative = kGeluScale *
        (1.0F + 3.0F * kGeluCubic * square);
    return 0.5F * (1.0F + tanh_value) +
        0.5F * value * (1.0F - tanh_value * tanh_value) *
            argument_derivative;
}

struct BackwardResult {
    std::vector<float> ff2_input_residual;
    std::vector<float> ff1_output_residual;
    std::vector<float> bias_gradient;
};

BackwardResult backward(
    const std::vector<float> & packed_ff2,
    const std::vector<float> & ff1_output,
    const std::vector<float> & incoming,
    bool negate
) {
    if (packed_ff2.size() != kWidth * kInner ||
        ff1_output.size() != kSamples * kFf1Width ||
        incoming.size() != kSamples * kWidth) {
        throw std::runtime_error("top-FF1 backward geometry differs");
    }
    BackwardResult result {
        std::vector<float>(kSamples * kInner),
        std::vector<float>(kSamples * kFf1Width),
        std::vector<float>(kFf1Width, 0.0F),
    };
    std::vector<std::thread> workers;
    for (std::size_t worker = 0; worker < kThreads; ++worker) {
        workers.emplace_back([&, worker] {
            std::array<float, kWidth> current {};
            for (std::size_t sample = worker; sample < kSamples;
                 sample += kThreads) {
                const float * source = incoming.data() + sample * kWidth;
                for (std::size_t output = 0; output < kWidth; ++output) {
                    current[output] = negate ? -source[output] : source[output];
                }
                float * ff2_residual =
                    result.ff2_input_residual.data() + sample * kInner;
                float * ff1_residual =
                    result.ff1_output_residual.data() + sample * kFf1Width;
                const float * activation =
                    ff1_output.data() + sample * kFf1Width;
                for (std::size_t inner = 0; inner < kInner;
                     inner += kLaneWidth) {
                    __m256 total = _mm256_setzero_ps();
                    for (std::size_t panel = 0; panel < kWidth;
                         panel += kReductionPanel) {
                        __m256 partial = _mm256_setzero_ps();
                        for (std::size_t output = panel;
                             output < panel + kReductionPanel; ++output) {
                            partial = _mm256_fmadd_ps(
                                _mm256_set1_ps(current[output]),
                                _mm256_loadu_ps(
                                    packed_ff2.data() +
                                    output * kInner + inner),
                                partial);
                        }
                        total = _mm256_add_ps(total, partial);
                    }
                    _mm256_storeu_ps(ff2_residual + inner, total);
                }
                for (std::size_t inner = 0; inner < kInner; ++inner) {
                    const float upstream = round_bf16(ff2_residual[inner]);
                    ff2_residual[inner] = upstream;
                    const float gate = activation[inner];
                    const float value = activation[kInner + inner];
                    const float gate_upstream = round_bf16(upstream * value);
                    ff1_residual[inner] = round_bf16(
                        gate_upstream * gelu_derivative(gate));
                    ff1_residual[kInner + inner] = round_bf16(
                        upstream * round_bf16(gelu(gate)));
                }
            }
        });
    }
    for (std::thread & worker : workers) worker.join();
    for (std::size_t feature = 0; feature < kFf1Width; ++feature) {
        float total = 0.0F;
        for (std::size_t sample = 0; sample < kSamples; ++sample) {
            total += result.ff1_output_residual[sample * kFf1Width + feature];
        }
        result.bias_gradient[feature] = total;
    }
    return result;
}

}  // namespace

int main(int argc, char ** argv) {
    try {
        if (argc != 8) {
            throw std::runtime_error(
                "usage: top_ff1_bias_gradient PARAMETERS OPEN_ROOT INPUT_RESIDUAL "
                "OUT_FF2_RESIDUAL OUT_FF1_RESIDUAL OUT_BIAS CONTROL_BIAS");
        }
        const std::vector<float> ff2 = pack_ff2(read_ff2(argv[1]));
        const std::vector<float> ff1_output = read_ff1_output(argv[2]);
        const std::vector<float> incoming = read_bf16(
            argv[3], kSamples * kWidth);
        const BackwardResult observed = backward(ff2, ff1_output, incoming, false);
        const BackwardResult control = backward(ff2, ff1_output, incoming, true);
        write_bf16(argv[4], observed.ff2_input_residual);
        write_bf16(argv[5], observed.ff1_output_residual);
        write_bf16(argv[6], observed.bias_gradient);
        write_bf16(argv[7], control.bias_gradient);
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "top-FF1 bias backward failed: %s\n", error.what());
        return 1;
    }
}
