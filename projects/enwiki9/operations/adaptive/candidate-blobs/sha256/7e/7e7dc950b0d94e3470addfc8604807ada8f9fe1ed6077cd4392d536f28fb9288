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
constexpr std::size_t kFeatureBlock = 64;
constexpr std::size_t kFeatureVectors = kFeatureBlock / 8;
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

void open_container(std::ifstream & input, const fs::path & path) {
    input.open(path, std::ios::binary);
    if (!input || read_u32(input) != kFileMagic) {
        throw std::runtime_error("invalid tensor container: " + path.string());
    }
    const std::uint32_t config_size = read_u32(input);
    input.seekg(config_size, std::ios::cur);
}

void skip_payload(std::ifstream & input, const TensorHeader & header) {
    const std::uint64_t bytes = header.elements * type_size(header.type);
    if (bytes > static_cast<std::uint64_t>(
            std::numeric_limits<std::streamoff>::max())) {
        throw std::runtime_error("tensor is too large to seek");
    }
    input.seekg(static_cast<std::streamoff>(bytes), std::ios::cur);
}

std::vector<std::uint32_t> read_targets(const fs::path & path) {
    std::ifstream input;
    open_container(input, path);
    while (input.peek() != std::ifstream::traits_type::eof()) {
        const TensorHeader header = read_header(input);
        if (header.name == "target_all_streams") {
            if (header.type != 5 ||
                header.dimensions != std::vector<std::uint32_t>({32, 64})) {
                throw std::runtime_error("target tensor contract differs");
            }
            std::vector<std::uint32_t> targets(header.elements);
            for (std::uint32_t & target : targets) target = read_u32(input);
            return targets;
        }
        skip_payload(input, header);
    }
    throw std::runtime_error("missing target_all_streams");
}

float bf16_to_float(std::uint16_t value) {
    const std::uint32_t bits = static_cast<std::uint32_t>(value) << 16U;
    float result;
    std::memcpy(&result, &bits, sizeof(result));
    return result;
}

std::vector<float> read_output_matrix(const fs::path & path) {
    std::ifstream input;
    open_container(input, path);
    while (input.peek() != std::ifstream::traits_type::eof()) {
        const TensorHeader header = read_header(input);
        if (header.name == "embed_out") {
            if (header.type != 1 || header.dimensions !=
                    std::vector<std::uint32_t>({kVocabulary, kWidth})) {
                throw std::runtime_error("embed_out tensor contract differs");
            }
            std::vector<std::uint16_t> words(header.elements);
            input.read(reinterpret_cast<char *>(words.data()),
                       static_cast<std::streamsize>(
                           words.size() * sizeof(words[0])));
            if (!input) throw std::runtime_error("truncated embed_out tensor");
            std::vector<float> transposed(header.elements);
            for (std::size_t feature = 0; feature < kWidth; ++feature) {
                for (std::size_t symbol = 0; symbol < kVocabulary; ++symbol) {
                    transposed[symbol * kWidth + feature] = bf16_to_float(
                        words[feature * kVocabulary + symbol]);
                }
            }
            return transposed;
        }
        skip_payload(input, header);
    }
    throw std::runtime_error("missing embed_out tensor");
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
    return bf16_to_float(bf16(value));
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
    const std::vector<float> & hidden
) {
    if (residuals.size() != kSamples * kVocabulary ||
        hidden.size() != kSamples * kWidth) {
        throw std::runtime_error("matrix-gradient geometry differs");
    }
    std::vector<float> result(kWidth * kVocabulary);
    std::vector<std::thread> workers;
    for (std::size_t worker = 0; worker < kThreads; ++worker) {
        workers.emplace_back([&, worker] {
            for (std::size_t feature = worker; feature < kWidth;
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
                            partial = _mm256_fmadd_ps(
                                _mm256_set1_ps(hidden[sample * kWidth + feature]),
                                residual,
                                partial);
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

std::vector<float> activation_residual(
    const std::vector<float> & residuals,
    const std::vector<float> & transposed_weights
) {
    if (residuals.size() != kSamples * kVocabulary ||
        transposed_weights.size() != kVocabulary * kWidth) {
        throw std::runtime_error("activation-residual geometry differs");
    }
    std::vector<float> result(kSamples * kWidth);
    std::vector<std::thread> workers;
    for (std::size_t worker = 0; worker < kThreads; ++worker) {
        workers.emplace_back([&, worker] {
            for (std::size_t sample = worker; sample < kSamples;
                 sample += kThreads) {
                const float * source =
                    residuals.data() + sample * kVocabulary;
                float * destination = result.data() + sample * kWidth;
                for (std::size_t block = 0; block < kWidth;
                     block += kFeatureBlock) {
                    __m256 accumulated[kFeatureVectors];
                    for (__m256 & value : accumulated) value = _mm256_setzero_ps();
                    for (std::size_t chunk = 0; chunk < kVocabulary;
                         chunk += kReductionChunk) {
                        __m256 partial[kFeatureVectors];
                        for (__m256 & value : partial) value = _mm256_setzero_ps();
                        const std::size_t end = std::min(
                            chunk + kReductionChunk, kVocabulary);
                        for (std::size_t symbol = chunk; symbol < end; ++symbol) {
                            const __m256 residual = _mm256_set1_ps(source[symbol]);
                            const float * weights = transposed_weights.data() +
                                symbol * kWidth + block;
                            for (std::size_t lane = 0; lane < kFeatureVectors; ++lane) {
                                partial[lane] = _mm256_fmadd_ps(
                                    residual,
                                    _mm256_loadu_ps(weights + lane * 8),
                                    partial[lane]);
                            }
                        }
                        for (std::size_t lane = 0; lane < kFeatureVectors; ++lane) {
                            accumulated[lane] = _mm256_add_ps(
                                accumulated[lane], partial[lane]);
                        }
                    }
                    for (std::size_t lane = 0; lane < kFeatureVectors; ++lane) {
                        _mm256_storeu_ps(destination + block + lane * 8,
                                         accumulated[lane]);
                    }
                    for (std::size_t feature = block;
                         feature < block + kFeatureBlock; ++feature) {
                        destination[feature] = round_bf16(destination[feature]);
                    }
                }
            }
        });
    }
    for (std::thread & worker : workers) worker.join();
    return result;
}

std::vector<float> reduce_bias(const std::vector<float> & residuals) {
    if (residuals.size() % kSamples) {
        throw std::runtime_error("bias-reduction geometry differs");
    }
    const std::size_t width = residuals.size() / kSamples;
    std::vector<float> result(width, 0.0F);
    for (std::size_t sample = 0; sample < kSamples; ++sample) {
        const float * source = residuals.data() + sample * width;
        for (std::size_t index = 0; index < width; ++index) {
            result[index] += source[index];
        }
    }
    return result;
}

}  // namespace

int main(int argc, char ** argv) {
    try {
        if (argc != 9) {
            throw std::runtime_error(
                "usage: final_hidden_residual STATE PARAMETERS OPEN_ROOT "
                "OUT_BIAS OUT_MATRIX OUT_HIDDEN OUT_LN_B SHIFTED_LN_B");
        }
        const std::vector<std::uint32_t> targets = read_targets(argv[1]);
        const std::vector<float> transposed_weights = read_output_matrix(argv[2]);
        std::vector<float> residuals(kSamples * kVocabulary);
        std::vector<float> shifted_residuals(kSamples * kVocabulary);
        std::vector<float> hidden(kSamples * kWidth);
        for (std::size_t stream = 0; stream < kStreams; ++stream) {
            char name[32];
            std::snprintf(name, sizeof(name), "stream_%02zu", stream);
            const fs::path root = fs::path(argv[3]) / name;
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
                float * shifted =
                    shifted_residuals.data() + sample * kVocabulary;
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
        write_bf16(argv[4], reduce_bias(residuals));
        write_bf16(argv[5], matrix_gradient(residuals, hidden));
        const std::vector<float> final_hidden_residual = activation_residual(
            residuals, transposed_weights);
        const std::vector<float> shifted_final_hidden_residual =
            activation_residual(shifted_residuals, transposed_weights);
        write_bf16(argv[6], final_hidden_residual);
        write_bf16(argv[7], reduce_bias(final_hidden_residual));
        write_bf16(argv[8], reduce_bias(shifted_final_hidden_residual));
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "final-hidden residual failed: %s\n", error.what());
        return 1;
    }
}
