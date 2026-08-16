#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
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
constexpr std::size_t kVocabulary = 16392;
constexpr float kLossScale = 1.0F / static_cast<float>(kStreams * kStates);

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

std::vector<float> read_probabilities(const fs::path & path) {
    const std::uintmax_t expected = kStates * kVocabulary * sizeof(float);
    if (!fs::is_regular_file(path) || fs::file_size(path) != expected) {
        throw std::runtime_error("open probability payload contract differs: " + path.string());
    }
    std::vector<float> values(kStates * kVocabulary);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char *>(values.data()),
               static_cast<std::streamsize>(expected));
    if (!input) throw std::runtime_error("cannot read open probabilities");
    if (!std::all_of(values.begin(), values.end(),
                     [](float value) { return std::isfinite(value) && value >= 0.0F; })) {
        throw std::runtime_error("open probabilities are invalid");
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

}  // namespace

int main(int argc, char ** argv) {
    try {
        if (argc != 5) {
            throw std::runtime_error(
                "usage: output_bias_gradient STATE_CONTAINER OPEN_ROOT OUTPUT SHIFTED_OUTPUT");
        }
        const std::vector<std::uint32_t> targets = read_targets(argv[1]);
        std::vector<std::vector<float>> probabilities;
        probabilities.reserve(kStreams);
        for (std::size_t stream = 0; stream < kStreams; ++stream) {
            char name[32];
            std::snprintf(name, sizeof(name), "stream_%02zu/output.f32", stream);
            probabilities.push_back(read_probabilities(fs::path(argv[2]) / name));
        }
        std::vector<float> gradient(kVocabulary, 0.0F);
        std::vector<float> shifted(kVocabulary, 0.0F);
        for (std::size_t state = 0; state < kStates; ++state) {
            for (std::size_t stream = 0; stream < kStreams; ++stream) {
                const float * row = probabilities[stream].data() + state * kVocabulary;
                const std::uint32_t target = targets[stream + kStreams * state];
                const std::uint32_t shifted_target = (target + 1U) % kVocabulary;
                if (target >= kVocabulary || shifted_target >= kVocabulary) {
                    throw std::runtime_error("target is outside the vocabulary");
                }
                for (std::size_t symbol = 0; symbol < kVocabulary; ++symbol) {
                    float residual = row[symbol] * kLossScale;
                    float shifted_residual = residual;
                    if (symbol == target) residual -= kLossScale;
                    if (symbol == shifted_target) shifted_residual -= kLossScale;
                    gradient[symbol] += round_bf16(residual);
                    shifted[symbol] += round_bf16(shifted_residual);
                }
            }
        }
        write_bf16(argv[3], gradient);
        write_bf16(argv[4], shifted);
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "output-bias gradient failed: %s\n", error.what());
        return 1;
    }
}
