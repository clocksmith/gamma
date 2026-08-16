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
constexpr std::size_t kVocabulary = 16392;
constexpr std::size_t kReductionChunk = 128;
constexpr std::size_t kControlFeatures = 8;
constexpr std::size_t kThreads = 4;
constexpr float kLossScale = 1.0F / static_cast<float>(kSamples);

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

std::vector<std::uint32_t> read_targets(const fs::path & path) {
    std::ifstream input(path, std::ios::binary);
    if (!input || read_u32(input) != kFileMagic) {
        throw std::runtime_error("invalid state container");
    }
    const std::uint32_t config_size = read_u32(input);
    input.seekg(config_size, std::ios::cur);
    while (input.peek() != std::ifstream::traits_type::eof()) {
        if (read_u32(input) != kTensorMagic) {
            throw std::runtime_error("invalid state tensor marker");
        }
        const std::uint32_t type = read_u32(input);
        const std::uint32_t rank = read_u32(input);
        const std::uint32_t name_size = read_u32(input);
        std::uint64_t count = 1;
        std::vector<std::uint32_t> dimensions;
        for (std::uint32_t axis = 0; axis < rank; ++axis) {
            const std::uint32_t dimension = read_u32(input);
            dimensions.push_back(dimension);
            count *= dimension;
        }
        std::string name(name_size, '\0');
        input.read(name.data(), name.size());
        if (!input) throw std::runtime_error("truncated state tensor name");
        if (name == "target_all_streams") {
            if (type != 5 || dimensions != std::vector<std::uint32_t>({32, 64})) {
                throw std::runtime_error("target tensor contract differs");
            }
            std::vector<std::uint32_t> targets(count);
            for (std::uint32_t & target : targets) target = read_u32(input);
            return targets;
        }
        const std::uint64_t bytes = count * type_size(type);
        if (bytes > static_cast<std::uint64_t>(
                std::numeric_limits<std::streamoff>::max())) {
            throw std::runtime_error("state tensor is too large to seek");
        }
        input.seekg(static_cast<std::streamoff>(bytes), std::ios::cur);
    }
    throw std::runtime_error("missing target_all_streams");
}

std::vector<float> read_f32(const fs::path & path, std::size_t count) {
    const std::uintmax_t expected = count * sizeof(float);
    if (!fs::is_regular_file(path) || fs::file_size(path) != expected) {
        throw std::runtime_error("open tensor geometry differs: " + path.string());
    }
    std::vector<float> values(count);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char *>(values.data()),
               static_cast<std::streamsize>(expected));
    if (!input || !std::all_of(values.begin(), values.end(),
            [](float value) { return std::isfinite(value); })) {
        throw std::runtime_error("open tensor is invalid: " + path.string());
    }
    return values;
}

std::uint16_t bf16(float value) {
    std::uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    const std::uint32_t rounding = 0x7fffU + ((bits >> 16U) & 1U);
    return static_cast<std::uint16_t>((bits + rounding) >> 16U);
}

float round_bf16(float value) {
    const std::uint32_t bits = static_cast<std::uint32_t>(bf16(value)) << 16U;
    float result;
    std::memcpy(&result, &bits, sizeof(result));
    return result;
}

void write_bf16(const fs::path & path, const std::vector<float> & values) {
    std::vector<std::uint16_t> output(values.size());
    std::transform(values.begin(), values.end(), output.begin(), bf16);
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    stream.write(reinterpret_cast<const char *>(output.data()),
                 static_cast<std::streamsize>(output.size() * sizeof(output[0])));
    if (!stream) throw std::runtime_error("cannot write BF16 gradient");
}

std::vector<float> matrix_gradient(
    const std::vector<float> & residuals,
    const std::vector<float> & hidden,
    std::size_t feature_count
) {
    if (residuals.size() != kSamples * kVocabulary ||
        hidden.size() != kSamples * kWidth || feature_count > kWidth) {
        throw std::runtime_error("matrix-gradient geometry differs");
    }
    std::vector<float> result(feature_count * kVocabulary);
    std::vector<std::thread> workers;
    workers.reserve(kThreads);
    for (std::size_t worker = 0; worker < kThreads; ++worker) {
        workers.emplace_back([&, worker] {
            for (std::size_t feature = worker; feature < feature_count;
                 feature += kThreads) {
                float * destination = result.data() + feature * kVocabulary;
                for (std::size_t symbol = 0; symbol < kVocabulary; symbol += 8) {
                    __m256 accumulated = _mm256_setzero_ps();
                    for (std::size_t chunk = 0; chunk < kSamples;
                         chunk += kReductionChunk) {
                        __m256 partial = _mm256_setzero_ps();
                        for (std::size_t sample = chunk;
                             sample < chunk + kReductionChunk; ++sample) {
                            const __m256 residual = _mm256_loadu_ps(
                                residuals.data() + sample * kVocabulary + symbol);
                            const __m256 activation = _mm256_set1_ps(
                                hidden[sample * kWidth + feature]);
                            partial = _mm256_fmadd_ps(activation, residual, partial);
                        }
                        accumulated = _mm256_add_ps(accumulated, partial);
                    }
                    _mm256_storeu_ps(destination + symbol, accumulated);
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
        if (argc != 6) {
            throw std::runtime_error(
                "usage: output_matrix_gradient STATE OPEN_ROOT OUT_BIAS "
                "OUT_MATRIX SHIFTED_CONTROL");
        }
        const std::vector<std::uint32_t> targets = read_targets(argv[1]);
        std::vector<float> residuals(kSamples * kVocabulary);
        std::vector<float> shifted_residuals(kSamples * kVocabulary);
        std::vector<float> hidden(kSamples * kWidth);
        for (std::size_t stream = 0; stream < kStreams; ++stream) {
            char name[32];
            std::snprintf(name, sizeof(name), "stream_%02zu", stream);
            const fs::path root = fs::path(argv[2]) / name;
            const std::vector<float> probabilities = read_f32(
                root / "output.f32", kStates * kVocabulary);
            const std::vector<float> current_hidden = read_f32(
                root / "final_hidden.f32", kStates * kWidth);
            for (std::size_t state = 0; state < kStates; ++state) {
                const std::size_t sample = stream + kStreams * state;
                const std::uint32_t target = targets[sample];
                if (target >= kVocabulary) {
                    throw std::runtime_error("target is outside the vocabulary");
                }
                const std::uint32_t shifted_target = (target + 1U) % kVocabulary;
                const float * probability =
                    probabilities.data() + state * kVocabulary;
                float * residual = residuals.data() + sample * kVocabulary;
                float * shifted = shifted_residuals.data() + sample * kVocabulary;
                for (std::size_t symbol = 0; symbol < kVocabulary; ++symbol) {
                    float value = probability[symbol] * kLossScale;
                    float shifted_value = value;
                    if (symbol == target) value -= kLossScale;
                    if (symbol == shifted_target) shifted_value -= kLossScale;
                    residual[symbol] = round_bf16(value);
                    shifted[symbol] = round_bf16(shifted_value);
                }
                std::copy_n(current_hidden.data() + state * kWidth, kWidth,
                            hidden.data() + sample * kWidth);
            }
        }
        std::vector<float> bias_gradient(kVocabulary, 0.0F);
        for (std::size_t sample = 0; sample < kSamples; ++sample) {
            const float * residual = residuals.data() + sample * kVocabulary;
            for (std::size_t symbol = 0; symbol < kVocabulary; ++symbol) {
                bias_gradient[symbol] += residual[symbol];
            }
        }
        write_bf16(argv[3], bias_gradient);
        write_bf16(argv[4], matrix_gradient(residuals, hidden, kWidth));
        write_bf16(
            argv[5], matrix_gradient(shifted_residuals, hidden, kControlFeatures));
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "output-matrix gradient failed: %s\n", error.what());
        return 1;
    }
}
