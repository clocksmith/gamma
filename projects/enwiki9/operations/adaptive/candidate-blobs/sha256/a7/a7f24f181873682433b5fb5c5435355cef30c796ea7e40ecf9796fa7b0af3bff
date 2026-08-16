#include <algorithm>
#include <array>
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
constexpr std::size_t kStates = 64;
constexpr std::size_t kStreams = 32;
constexpr std::size_t kSamples = kStates * kStreams;
constexpr std::size_t kWidth = 1024;
constexpr std::size_t kInner = 3072;
constexpr std::size_t kLaneWidth = 8;
constexpr std::size_t kThreads = 4;

std::uint32_t read_u32(std::ifstream &input) {
    std::array<unsigned char, 4> bytes {};
    input.read(reinterpret_cast<char *>(bytes.data()), bytes.size());
    if (!input)
        throw std::runtime_error("truncated container u32");
    return static_cast<std::uint32_t>(bytes[0]) |
           (static_cast<std::uint32_t>(bytes[1]) << 8U) |
           (static_cast<std::uint32_t>(bytes[2]) << 16U) |
           (static_cast<std::uint32_t>(bytes[3]) << 24U);
}

std::size_t type_size(std::uint32_t type) {
    constexpr std::array<std::size_t, 9> sizes {4, 2, 2, 1, 2, 4, 1, 2, 4};
    if (type >= sizes.size())
        throw std::runtime_error("unsupported container type");
    return sizes[type];
}

struct TensorHeader {
    std::uint32_t type;
    std::vector<std::uint32_t> dimensions;
    std::uint64_t elements;
    std::string name;
};

TensorHeader read_header(std::ifstream &input) {
    if (read_u32(input) != kTensorMagic)
        throw std::runtime_error("invalid tensor marker");
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
    if (!input)
        throw std::runtime_error("truncated tensor name");
    return header;
}

void skip_payload(std::ifstream &input, const TensorHeader &header) {
    const std::uint64_t bytes = header.elements * type_size(header.type);
    if (bytes > static_cast<std::uint64_t>(
                    std::numeric_limits<std::streamoff>::max()))
        throw std::runtime_error("tensor is too large to seek");
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

std::vector<float> read_ff2_packed(const fs::path &path) {
    std::ifstream input(path, std::ios::binary);
    if (!input || read_u32(input) != kFileMagic)
        throw std::runtime_error("invalid parameter container");
    const std::uint32_t config_size = read_u32(input);
    input.seekg(config_size, std::ios::cur);
    while (input.peek() != std::ifstream::traits_type::eof()) {
        const TensorHeader header = read_header(input);
        if (header.name != "ff2_19") {
            skip_payload(input, header);
            continue;
        }
        if (header.type != 1 || header.dimensions !=
                std::vector<std::uint32_t>({kWidth, kInner}))
            throw std::runtime_error("ff2_19 tensor contract differs");
        std::vector<std::uint16_t> words(kInner * kWidth);
        input.read(reinterpret_cast<char *>(words.data()),
                   static_cast<std::streamsize>(
                       words.size() * sizeof(words.front())));
        if (!input)
            throw std::runtime_error("truncated ff2_19 tensor");
        std::vector<float> packed(kWidth * kInner);
        for (std::size_t output = 0; output < kWidth; ++output) {
            for (std::size_t inner = 0; inner < kInner; ++inner) {
                packed[output * kInner + inner] =
                    bf16_to_float(words[inner * kWidth + output]);
            }
        }
        return packed;
    }
    throw std::runtime_error("missing ff2_19 tensor");
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

std::vector<float> lane_sequential_transpose(
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
                    for (std::size_t output = 0; output < kWidth; ++output) {
                        total = _mm256_fmadd_ps(
                            _mm256_set1_ps(gradient[output]),
                            _mm256_loadu_ps(
                                packed.data() + output * kInner + inner),
                            total);
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
                "usage: ff2_transpose_lane_order PARAMETERS INCOMING OUTPUT");
        const std::vector<float> packed = read_ff2_packed(argv[1]);
        const std::vector<float> incoming = read_bf16(
            argv[2], kSamples * kWidth);
        write_bf16(argv[3], lane_sequential_transpose(packed, incoming));
        return 0;
    } catch (const std::exception &error) {
        std::fprintf(stderr, "FF2 transpose lane-order probe failed: %s\n",
                     error.what());
        return 1;
    }
}
