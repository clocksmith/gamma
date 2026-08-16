#include <immintrin.h>
#include <sys/mman.h>
#include <sys/stat.h>

#include <algorithm>
#include <array>
#include <cerrno>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <fcntl.h>
#include <unistd.h>

namespace fs = std::filesystem;

namespace {

constexpr std::uint32_t kFileMagic = 0x23f4aefbU;
constexpr std::uint32_t kTensorMagic = 0x23f4aefaU;
constexpr std::uint32_t kF32 = 0U;
constexpr std::uint32_t kBf16 = 1U;
constexpr std::uint64_t kExpectedParameters = 246U;
constexpr std::uint64_t kBf16Bias = 0x8000U;
constexpr float kBeta2 = 0.9999F;
constexpr float kEpsilon = 1.0e-8F;
constexpr float kGradientClip = 0.05F;
constexpr float kLearningRate = 0x1.4f7e76p-13F;
constexpr std::uint64_t kUpdateExponent = 5U;

class Mapping {
  public:
    explicit Mapping(const fs::path &path) : path_(path) {
        fd_ = open(path.c_str(), O_RDONLY | O_CLOEXEC);
        if (fd_ < 0) {
            throw std::runtime_error("cannot open " + path.string() + ": " +
                                     std::strerror(errno));
        }
        struct stat status {};
        if (fstat(fd_, &status) != 0 || status.st_size <= 0) {
            close(fd_);
            throw std::runtime_error("cannot stat nonempty file " + path.string());
        }
        size_ = static_cast<std::size_t>(status.st_size);
        void *mapped = mmap(nullptr, size_, PROT_READ, MAP_PRIVATE, fd_, 0);
        if (mapped == MAP_FAILED) {
            close(fd_);
            throw std::runtime_error("cannot map " + path.string() + ": " +
                                     std::strerror(errno));
        }
        data_ = static_cast<const std::uint8_t *>(mapped);
    }

    Mapping(const Mapping &) = delete;
    Mapping &operator=(const Mapping &) = delete;

    ~Mapping() {
        if (data_ != nullptr) {
            munmap(const_cast<std::uint8_t *>(data_), size_);
        }
        if (fd_ >= 0) {
            close(fd_);
        }
    }

    const std::uint8_t *data() const { return data_; }
    std::size_t size() const { return size_; }
    const fs::path &path() const { return path_; }

  private:
    fs::path path_;
    int fd_ = -1;
    const std::uint8_t *data_ = nullptr;
    std::size_t size_ = 0;
};

std::uint32_t read_u32(const Mapping &mapping, std::size_t &offset) {
    if (offset > mapping.size() || mapping.size() - offset < sizeof(std::uint32_t)) {
        throw std::runtime_error("truncated u32 in " + mapping.path().string());
    }
    std::uint32_t value;
    std::memcpy(&value, mapping.data() + offset, sizeof(value));
    offset += sizeof(value);
    return value;
}

std::size_t type_size(std::uint32_t type) {
    switch (type) {
    case kF32:
        return 4;
    case kBf16:
        return 2;
    case 2:
        return 2;
    case 3:
        return 1;
    case 4:
        return 2;
    case 5:
        return 4;
    case 6:
        return 1;
    case 7:
        return 2;
    case 8:
        return 4;
    default:
        throw std::runtime_error("unsupported tensor type " + std::to_string(type));
    }
}

struct Record {
    std::uint32_t type;
    std::vector<std::uint32_t> dimensions;
    std::uint64_t count;
    const std::uint8_t *payload;
};

class Container {
  public:
    explicit Container(const fs::path &path) : mapping_(path) {
        std::size_t offset = 0;
        if (read_u32(mapping_, offset) != kFileMagic) {
            throw std::runtime_error("container magic differs: " + path.string());
        }
        const std::uint32_t configuration_size = read_u32(mapping_, offset);
        if (offset > mapping_.size() || mapping_.size() - offset < configuration_size) {
            throw std::runtime_error("truncated container configuration: " + path.string());
        }
        configuration_.assign(
            reinterpret_cast<const char *>(mapping_.data() + offset),
            configuration_size);
        offset += configuration_size;
        while (offset < mapping_.size()) {
            if (read_u32(mapping_, offset) != kTensorMagic) {
                throw std::runtime_error("tensor marker differs: " + path.string());
            }
            Record record {};
            record.type = read_u32(mapping_, offset);
            const std::uint32_t rank = read_u32(mapping_, offset);
            const std::uint32_t name_size = read_u32(mapping_, offset);
            if (rank == 0 || rank > 8 || name_size == 0 || name_size > 4096) {
                throw std::runtime_error("invalid tensor header: " + path.string());
            }
            record.count = 1;
            for (std::uint32_t axis = 0; axis < rank; ++axis) {
                const std::uint32_t dimension = read_u32(mapping_, offset);
                if (dimension == 0 ||
                    record.count > std::numeric_limits<std::uint64_t>::max() / dimension) {
                    throw std::runtime_error("invalid tensor dimensions: " + path.string());
                }
                record.dimensions.push_back(dimension);
                record.count *= dimension;
            }
            if (offset > mapping_.size() || mapping_.size() - offset < name_size) {
                throw std::runtime_error("truncated tensor name: " + path.string());
            }
            std::string name(
                reinterpret_cast<const char *>(mapping_.data() + offset), name_size);
            offset += name_size;
            const std::uint64_t payload_size = record.count * type_size(record.type);
            if (payload_size > mapping_.size() - offset) {
                throw std::runtime_error("truncated tensor payload for " + name);
            }
            record.payload = mapping_.data() + offset;
            offset += static_cast<std::size_t>(payload_size);
            if (!records_.emplace(name, std::move(record)).second) {
                throw std::runtime_error("duplicate tensor name " + name);
            }
            order_.push_back(std::move(name));
        }
        if (offset != mapping_.size()) {
            throw std::runtime_error("container has trailing bytes: " + path.string());
        }
    }

    const Record &at(const std::string &name) const {
        const auto iterator = records_.find(name);
        if (iterator == records_.end()) {
            throw std::runtime_error("missing tensor " + name + " in " +
                                     mapping_.path().string());
        }
        return iterator->second;
    }

    const std::vector<std::string> &order() const { return order_; }
    std::size_t size() const { return records_.size(); }

  private:
    Mapping mapping_;
    std::string configuration_;
    std::map<std::string, Record> records_;
    std::vector<std::string> order_;
};

struct Gradient {
    fs::path payload;
    std::uint32_t type;
    std::vector<std::uint32_t> dimensions;
};

std::vector<std::uint32_t> parse_dimensions(const std::string &text) {
    std::vector<std::uint32_t> dimensions;
    std::size_t begin = 0;
    while (begin < text.size()) {
        const std::size_t end = text.find(',', begin);
        const std::string token = text.substr(begin, end - begin);
        std::size_t consumed = 0;
        const unsigned long value = std::stoul(token, &consumed, 10);
        if (consumed != token.size() || value == 0 ||
            value > std::numeric_limits<std::uint32_t>::max()) {
            throw std::runtime_error("invalid gradient dimension " + token);
        }
        dimensions.push_back(static_cast<std::uint32_t>(value));
        if (end == std::string::npos) {
            break;
        }
        begin = end + 1;
    }
    return dimensions;
}

std::map<std::string, Gradient> load_gradients(const fs::path &directory) {
    std::vector<fs::path> metadata;
    for (const fs::directory_entry &entry : fs::directory_iterator(directory)) {
        if (entry.is_regular_file() && entry.path().extension() == ".meta") {
            metadata.push_back(entry.path());
        }
    }
    std::sort(metadata.begin(), metadata.end());
    std::map<std::string, Gradient> gradients;
    for (const fs::path &path : metadata) {
        std::ifstream input(path);
        if (!input) {
            throw std::runtime_error("cannot read " + path.string());
        }
        std::map<std::string, std::string> fields;
        std::string line;
        while (std::getline(input, line)) {
            const std::size_t delimiter = line.find('=');
            if (delimiter == std::string::npos) {
                throw std::runtime_error("malformed gradient metadata: " + path.string());
            }
            fields.emplace(line.substr(0, delimiter), line.substr(delimiter + 1));
        }
        const std::string name = fields.at("name");
        Gradient gradient {
            path.parent_path() / path.stem().replace_extension(".bin"),
            static_cast<std::uint32_t>(std::stoul(fields.at("item_type"))),
            parse_dimensions(fields.at("dims")),
        };
        if (!fs::is_regular_file(gradient.payload)) {
            throw std::runtime_error("missing gradient payload for " + name);
        }
        if (!gradients.emplace(name, std::move(gradient)).second) {
            throw std::runtime_error("duplicate gradient name " + name);
        }
    }
    return gradients;
}

float libnc_sum64(const __m256 (&x)[8]) {
    const __m256 u23 = _mm256_unpacklo_ps(x[2], x[3]);
    const __m256 u67 = _mm256_unpacklo_ps(x[6], x[7]);
    const __m256 u01 = _mm256_unpacklo_ps(x[0], x[1]);
    const __m256 h23 = _mm256_unpackhi_ps(x[2], x[3]);
    const __m256 h01 = _mm256_unpackhi_ps(x[0], x[1]);
    const __m256 u45 = _mm256_unpacklo_ps(x[4], x[5]);
    const __m256 h45 = _mm256_unpackhi_ps(x[4], x[5]);
    const __m256 h67 = _mm256_unpackhi_ps(x[6], x[7]);
    const __m256 a = _mm256_shuffle_ps(u01, u23, 0x44);
    const __m256 b = _mm256_shuffle_ps(h01, h23, 0x44);
    const __m256 c = _mm256_shuffle_ps(u01, u23, 0xee);
    const __m256 d = _mm256_shuffle_ps(h01, h23, 0xee);
    const __m256 e = _mm256_shuffle_ps(u45, u67, 0x44);
    const __m256 f = _mm256_shuffle_ps(h45, h67, 0x44);
    const __m256 g = _mm256_shuffle_ps(u45, u67, 0xee);
    const __m256 h = _mm256_shuffle_ps(h45, h67, 0xee);
    __m256 left_low = _mm256_insertf128_ps(a, _mm256_castps256_ps128(e), 1);
    __m256 left_high = _mm256_insertf128_ps(c, _mm256_castps256_ps128(g), 1);
    __m256 right_low = _mm256_insertf128_ps(b, _mm256_castps256_ps128(f), 1);
    __m256 right_high = _mm256_insertf128_ps(d, _mm256_castps256_ps128(h), 1);
    const __m256 left_low_high = _mm256_permute2f128_ps(a, e, 0x31);
    left_high = _mm256_add_ps(left_high, left_low);
    const __m256 left_high_high = _mm256_permute2f128_ps(c, g, 0x31);
    const __m256 right_low_high = _mm256_permute2f128_ps(b, f, 0x31);
    const __m256 right_high_high = _mm256_permute2f128_ps(d, h, 0x31);
    const __m256 left_tail = _mm256_add_ps(left_low_high, left_high_high);
    right_high = _mm256_add_ps(right_high, right_low);
    const __m256 right_tail = _mm256_add_ps(right_low_high, right_high_high);
    right_high = _mm256_add_ps(left_high, right_high);
    __m256 total = _mm256_add_ps(left_tail, right_tail);
    total = _mm256_add_ps(right_high, total);
    total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0xb1));
    total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0x4e));
    total = _mm256_add_ps(total, _mm256_permute2f128_ps(total, total, 0x01));
    return _mm_cvtss_f32(_mm256_castps256_ps128(total));
}

__m256 load_bf16(const std::uint16_t *source) {
    const __m128i packed = _mm_loadu_si128(reinterpret_cast<const __m128i *>(source));
    return _mm256_castsi256_ps(_mm256_slli_epi32(_mm256_cvtepu16_epi32(packed), 16));
}

float gradient_sum_squares(const Mapping &gradient, std::uint32_t type,
                           std::uint64_t count) {
    if (count % 8 != 0 || gradient.size() != count * type_size(type)) {
        throw std::runtime_error("gradient geometry or byte count differs: " +
                                 gradient.path().string());
    }
    std::array<float, 64> tail {};
    std::array<float, 32> partials {};
    std::uint64_t blocks = 0;
    std::uint64_t index = 0;
    while (index < count) {
        const std::uint64_t available = std::min<std::uint64_t>(64, count - index);
        __m256 squares[8] {};
        if (available == 64) {
            for (std::uint64_t lane = 0; lane < 8; ++lane) {
                __m256 value;
                if (type == kBf16) {
                    const auto *source = reinterpret_cast<const std::uint16_t *>(
                        gradient.data()) + index + lane * 8;
                    value = load_bf16(source);
                } else if (type == kF32) {
                    const auto *source = reinterpret_cast<const float *>(gradient.data()) +
                                         index + lane * 8;
                    value = _mm256_loadu_ps(source);
                } else {
                    throw std::runtime_error("gradient type is not F32 or BF16");
                }
                squares[lane] = _mm256_mul_ps(value, value);
            }
        } else {
            std::fill(tail.begin(), tail.end(), 0.0F);
            for (std::uint64_t item = 0; item < available; ++item) {
                float value;
                if (type == kBf16) {
                    std::uint32_t bits = static_cast<const std::uint16_t *>(
                                             static_cast<const void *>(gradient.data()))[index + item]
                                         << 16;
                    std::memcpy(&value, &bits, sizeof(value));
                } else if (type == kF32) {
                    value = reinterpret_cast<const float *>(gradient.data())[index + item];
                } else {
                    throw std::runtime_error("gradient type is not F32 or BF16");
                }
                tail[item] = value * value;
            }
            for (std::uint64_t lane = 0; lane < 8; ++lane) {
                squares[lane] = _mm256_load_ps(tail.data() + lane * 8);
            }
        }
        float block_sum = libnc_sum64(squares);
        std::uint32_t slot = 0;
        while ((blocks & (std::uint64_t {1} << slot)) != 0) {
            block_sum += partials[slot];
            partials[slot++] = 0.0F;
        }
        partials[slot] = block_sum;
        ++blocks;
        index += available;
    }
    float total = 0.0F;
    std::uint32_t slots = 0;
    for (std::uint64_t remaining = blocks; remaining != 0; remaining >>= 1) {
        ++slots;
    }
    for (std::uint32_t slot = 0; slot < slots; ++slot) {
        total += partials[slot];
    }
    return total;
}

__m256 fast_rsqrt(__m256 value) {
    const __m256 half = _mm256_mul_ps(value, _mm256_set1_ps(0.5F));
    const __m256i shifted = _mm256_srli_epi32(_mm256_castps_si256(value), 1);
    const __m256 estimate = _mm256_castsi256_ps(
        _mm256_sub_epi32(_mm256_set1_epi32(0x5f3759df), shifted));
    const __m256 half_estimate = _mm256_mul_ps(half, estimate);
    const __m256 correction = _mm256_fnmadd_ps(
        estimate, half_estimate, _mm256_set1_ps(1.5F));
    return _mm256_mul_ps(correction, estimate);
}

float power_f32(float base, std::uint64_t exponent) {
    if (exponent == 0) {
        return 1.0F;
    }
    std::uint32_t highest = 63U - static_cast<std::uint32_t>(__builtin_clzll(exponent));
    float result = base;
    while (highest-- != 0) {
        result *= result;
        if ((exponent & (std::uint64_t {1} << highest)) != 0) {
            result *= base;
        }
    }
    return result;
}

std::uint32_t float_bits(float value) {
    std::uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}

std::string hex_word(std::uint32_t value, unsigned width = 8) {
    std::ostringstream output;
    output << "0x" << std::hex << std::setfill('0') << std::setw(width) << value;
    return output.str();
}

struct FirstMismatch {
    bool present = false;
    std::string tensor;
    std::string stream;
    std::uint64_t index = 0;
    std::uint32_t expected = 0;
    std::uint32_t actual = 0;
    unsigned width = 8;
};

struct TensorResult {
    std::string name;
    std::uint32_t type;
    std::uint64_t count;
    std::uint32_t norm_bits;
    std::uint32_t scale_bits;
    std::uint64_t parameter_high_mismatches = 0;
    std::uint64_t parameter_low_mismatches = 0;
    std::uint64_t variance_mismatches = 0;
};

struct Totals {
    std::uint64_t parameter_words = 0;
    std::uint64_t parameter_high_mismatches = 0;
    std::uint64_t parameter_low_mismatches = 0;
    std::uint64_t variance_mismatches = 0;
    std::uint64_t clipped_tensors = 0;
    std::uint64_t bf16_tensors = 0;
    std::uint64_t f32_tensors = 0;
};

void note_mismatch(FirstMismatch &first, const std::string &tensor,
                   const std::string &stream, std::uint64_t index,
                   std::uint32_t expected, std::uint32_t actual, unsigned width) {
    if (!first.present) {
        first = {true, tensor, stream, index, expected, actual, width};
    }
}

void require_same_geometry(const Record &left, const Record &right,
                           const std::string &label) {
    if (left.type != right.type || left.dimensions != right.dimensions ||
        left.count != right.count) {
        throw std::runtime_error("tensor geometry differs for " + label);
    }
}

TensorResult replay_bf16(
    const std::string &name, const Record &parameter_initial,
    const Record &parameter_final, const Record &low_initial,
    const Record &low_final, const Record &variance_initial,
    const Record &variance_final, const Mapping &gradient, float gradient_scale,
    float gradient_norm, float alpha, float epsilon_squared, FirstMismatch &first) {
    const std::uint64_t count = parameter_initial.count;
    if (count % 8 != 0) {
        throw std::runtime_error("BF16 tensor width is not divisible by eight: " + name);
    }
    const auto *parameter_in = reinterpret_cast<const std::uint16_t *>(
        parameter_initial.payload);
    const auto *parameter_out = reinterpret_cast<const std::uint16_t *>(
        parameter_final.payload);
    const auto *low_in = reinterpret_cast<const std::uint16_t *>(low_initial.payload);
    const auto *low_out = reinterpret_cast<const std::uint16_t *>(low_final.payload);
    const auto *variance_in = reinterpret_cast<const std::uint16_t *>(
        variance_initial.payload);
    const auto *variance_out = reinterpret_cast<const std::uint16_t *>(
        variance_final.payload);
    const auto *gradient_in = reinterpret_cast<const std::uint16_t *>(gradient.data());

    TensorResult result {
        name, kBf16, count, float_bits(gradient_norm), float_bits(gradient_scale)};
    const __m256 scale = _mm256_set1_ps(gradient_scale);
    const __m256 beta2 = _mm256_set1_ps(kBeta2);
    const __m256 one_minus_beta2 = _mm256_set1_ps(1.0F - kBeta2);
    const __m256 alpha_vector = _mm256_set1_ps(alpha);
    const __m256 epsilon_vector = _mm256_set1_ps(epsilon_squared);
    const __m256 decay = _mm256_set1_ps(1.0F);
    const __m256i bias = _mm256_set1_epi32(static_cast<int>(kBf16Bias));
    const __m256i inverse_bias = _mm256_set1_epi32(-static_cast<int>(kBf16Bias));
    const __m256i round_bias = _mm256_set1_epi32(0x7fff);
    const __m256i one = _mm256_set1_epi32(1);
    alignas(32) std::array<std::uint32_t, 8> predicted_parameter {};
    alignas(32) std::array<std::uint32_t, 8> predicted_variance {};

    for (std::uint64_t index = 0; index < count; index += 8) {
        const __m256 gradient_value = _mm256_mul_ps(load_bf16(gradient_in + index), scale);
        const __m256 old_variance = load_bf16(variance_in + index);
        const __m256 gradient_square = _mm256_mul_ps(gradient_value, gradient_value);
        const __m256 weighted_square = _mm256_mul_ps(gradient_square, one_minus_beta2);
        const __m256 new_variance = _mm256_fmadd_ps(old_variance, beta2, weighted_square);

        __m256i variance_bits = _mm256_castps_si256(new_variance);
        const __m256i variance_lsb = _mm256_and_si256(
            _mm256_srli_epi32(variance_bits, 16), one);
        variance_bits = _mm256_add_epi32(
            _mm256_add_epi32(variance_bits, round_bias), variance_lsb);
        const __m256i variance_high = _mm256_srli_epi32(variance_bits, 16);
        _mm256_store_si256(
            reinterpret_cast<__m256i *>(predicted_variance.data()), variance_high);

        const __m256 scaled_update = _mm256_mul_ps(gradient_value, alpha_vector);
        const __m256 update = _mm256_mul_ps(
            fast_rsqrt(_mm256_add_ps(new_variance, epsilon_vector)), scaled_update);
        const __m256i parameter_high = _mm256_slli_epi32(
            _mm256_cvtepu16_epi32(_mm_loadu_si128(
                reinterpret_cast<const __m128i *>(parameter_in + index))),
            16);
        const __m256i parameter_low = _mm256_cvtepu16_epi32(_mm_loadu_si128(
            reinterpret_cast<const __m128i *>(low_in + index)));
        const __m256 parameter = _mm256_castsi256_ps(_mm256_add_epi32(
            _mm256_or_si256(parameter_high, parameter_low), inverse_bias));
        const __m256 new_parameter = _mm256_fmsub_ps(parameter, decay, update);
        const __m256i biased_parameter = _mm256_add_epi32(
            _mm256_castps_si256(new_parameter), bias);
        _mm256_store_si256(
            reinterpret_cast<__m256i *>(predicted_parameter.data()), biased_parameter);

        for (std::uint64_t lane = 0; lane < 8; ++lane) {
            const std::uint64_t item = index + lane;
            const std::uint16_t predicted_high = static_cast<std::uint16_t>(
                predicted_parameter[lane] >> 16);
            const std::uint16_t predicted_low = static_cast<std::uint16_t>(
                predicted_parameter[lane] & 0xffffU);
            const std::uint16_t predicted_v = static_cast<std::uint16_t>(
                predicted_variance[lane]);
            if (predicted_high != parameter_out[item]) {
                ++result.parameter_high_mismatches;
                note_mismatch(first, name, "parameter-high", item,
                              parameter_out[item], predicted_high, 4);
            }
            if (predicted_low != low_out[item]) {
                ++result.parameter_low_mismatches;
                note_mismatch(first, name, "parameter-low", item,
                              low_out[item], predicted_low, 4);
            }
            if (predicted_v != variance_out[item]) {
                ++result.variance_mismatches;
                note_mismatch(first, name, "variance", item,
                              variance_out[item], predicted_v, 4);
            }
        }
    }
    return result;
}

TensorResult replay_f32(
    const std::string &name, const Record &parameter_initial,
    const Record &parameter_final, const Record &variance_initial,
    const Record &variance_final, const Mapping &gradient, float gradient_scale,
    float gradient_norm, float alpha, float epsilon_squared, FirstMismatch &first) {
    const std::uint64_t count = parameter_initial.count;
    if (count % 8 != 0) {
        throw std::runtime_error("F32 tensor width is not divisible by eight: " + name);
    }
    const auto *parameter_in = reinterpret_cast<const float *>(parameter_initial.payload);
    const auto *parameter_out = reinterpret_cast<const std::uint32_t *>(
        parameter_final.payload);
    const auto *variance_in = reinterpret_cast<const float *>(variance_initial.payload);
    const auto *variance_out = reinterpret_cast<const std::uint32_t *>(
        variance_final.payload);
    const auto *gradient_in = reinterpret_cast<const float *>(gradient.data());
    TensorResult result {
        name, kF32, count, float_bits(gradient_norm), float_bits(gradient_scale)};
    const __m256 scale = _mm256_set1_ps(gradient_scale);
    const __m256 beta2 = _mm256_set1_ps(kBeta2);
    const __m256 one_minus_beta2 = _mm256_set1_ps(1.0F - kBeta2);
    const __m256 alpha_vector = _mm256_set1_ps(alpha);
    const __m256 epsilon_vector = _mm256_set1_ps(epsilon_squared);
    const __m256 decay = _mm256_set1_ps(1.0F);
    alignas(32) std::array<std::uint32_t, 8> predicted_parameter {};
    alignas(32) std::array<std::uint32_t, 8> predicted_variance {};
    for (std::uint64_t index = 0; index < count; index += 8) {
        const __m256 gradient_value = _mm256_mul_ps(
            _mm256_loadu_ps(gradient_in + index), scale);
        const __m256 old_variance = _mm256_loadu_ps(variance_in + index);
        const __m256 weighted_square = _mm256_mul_ps(
            _mm256_mul_ps(gradient_value, gradient_value), one_minus_beta2);
        const __m256 new_variance = _mm256_fmadd_ps(old_variance, beta2, weighted_square);
        const __m256 scaled_update = _mm256_mul_ps(gradient_value, alpha_vector);
        const __m256 update = _mm256_mul_ps(
            fast_rsqrt(_mm256_add_ps(new_variance, epsilon_vector)), scaled_update);
        const __m256 new_parameter = _mm256_fmsub_ps(
            _mm256_loadu_ps(parameter_in + index), decay, update);
        _mm256_store_si256(reinterpret_cast<__m256i *>(predicted_parameter.data()),
                           _mm256_castps_si256(new_parameter));
        _mm256_store_si256(reinterpret_cast<__m256i *>(predicted_variance.data()),
                           _mm256_castps_si256(new_variance));
        for (std::uint64_t lane = 0; lane < 8; ++lane) {
            const std::uint64_t item = index + lane;
            if (predicted_parameter[lane] != parameter_out[item]) {
                ++result.parameter_high_mismatches;
                note_mismatch(first, name, "parameter-f32", item,
                              parameter_out[item], predicted_parameter[lane], 8);
            }
            if (predicted_variance[lane] != variance_out[item]) {
                ++result.variance_mismatches;
                note_mismatch(first, name, "variance-f32", item,
                              variance_out[item], predicted_variance[lane], 8);
            }
        }
    }
    return result;
}

std::string json_escape(std::string_view input) {
    std::ostringstream output;
    for (const unsigned char value : input) {
        switch (value) {
        case '\\':
            output << "\\\\";
            break;
        case '"':
            output << "\\\"";
            break;
        case '\n':
            output << "\\n";
            break;
        case '\r':
            output << "\\r";
            break;
        case '\t':
            output << "\\t";
            break;
        default:
            if (value < 0x20) {
                output << "\\u" << std::hex << std::setw(4) << std::setfill('0')
                       << static_cast<unsigned>(value) << std::dec;
            } else {
                output << static_cast<char>(value);
            }
        }
    }
    return output.str();
}

void write_report(const fs::path &path, const std::vector<TensorResult> &tensors,
                  const Totals &totals, const FirstMismatch &first,
                  float beta2_power, float bias_correction, float epsilon_squared) {
    std::ofstream output(path);
    if (!output) {
        throw std::runtime_error("cannot create report " + path.string());
    }
    const bool exact = totals.parameter_high_mismatches == 0 &&
                       totals.parameter_low_mismatches == 0 &&
                       totals.variance_mismatches == 0;
    output << "{\n"
           << "  \"schema\": \"gamma.nncp.open-profile-adam-replay.q0.v1\",\n"
           << "  \"exact\": " << (exact ? "true" : "false") << ",\n"
           << "  \"constants\": {\n"
           << "    \"beta2Bits\": \"" << hex_word(float_bits(kBeta2)) << "\",\n"
           << "    \"beta2PowerBits\": \"" << hex_word(float_bits(beta2_power))
           << "\",\n"
           << "    \"biasCorrectionBits\": \""
           << hex_word(float_bits(bias_correction)) << "\",\n"
           << "    \"epsilonSquaredBits\": \""
           << hex_word(float_bits(epsilon_squared)) << "\",\n"
           << "    \"gradientClipBits\": \""
           << hex_word(float_bits(kGradientClip)) << "\",\n"
           << "    \"learningRateBits\": \""
           << hex_word(float_bits(kLearningRate)) << "\",\n"
           << "    \"updateExponent\": " << kUpdateExponent << "\n"
           << "  },\n"
           << "  \"totals\": {\n"
           << "    \"tensorCount\": " << tensors.size() << ",\n"
           << "    \"bf16TensorCount\": " << totals.bf16_tensors << ",\n"
           << "    \"f32TensorCount\": " << totals.f32_tensors << ",\n"
           << "    \"clippedTensorCount\": " << totals.clipped_tensors << ",\n"
           << "    \"parameterWordCount\": " << totals.parameter_words << ",\n"
           << "    \"parameterHighMismatchCount\": "
           << totals.parameter_high_mismatches << ",\n"
           << "    \"parameterLowMismatchCount\": "
           << totals.parameter_low_mismatches << ",\n"
           << "    \"varianceMismatchCount\": " << totals.variance_mismatches
           << "\n  },\n"
           << "  \"firstMismatch\": ";
    if (!first.present) {
        output << "null,\n";
    } else {
        output << "{\"tensor\": \"" << json_escape(first.tensor)
               << "\", \"stream\": \"" << json_escape(first.stream)
               << "\", \"index\": " << first.index << ", \"expected\": \""
               << hex_word(first.expected, first.width) << "\", \"actual\": \""
               << hex_word(first.actual, first.width) << "\"},\n";
    }
    output << "  \"tensors\": [\n";
    for (std::size_t index = 0; index < tensors.size(); ++index) {
        const TensorResult &tensor = tensors[index];
        output << "    {\"name\": \"" << json_escape(tensor.name)
               << "\", \"type\": \"" << (tensor.type == kBf16 ? "BF16" : "F32")
               << "\", \"count\": " << tensor.count
               << ", \"normBits\": \"" << hex_word(tensor.norm_bits)
               << "\", \"scaleBits\": \"" << hex_word(tensor.scale_bits)
               << "\", \"parameterHighMismatches\": "
               << tensor.parameter_high_mismatches
               << ", \"parameterLowMismatches\": "
               << tensor.parameter_low_mismatches
               << ", \"varianceMismatches\": " << tensor.variance_mismatches
               << "}" << (index + 1 == tensors.size() ? "\n" : ",\n");
    }
    output << "  ]\n}\n";
}

} // namespace

int main(int argc, char **argv) {
    try {
        if (argc != 3) {
            throw std::runtime_error("usage: adam_replay FIXTURE REPORT");
        }
        const fs::path fixture = fs::canonical(argv[1]);
        const fs::path report = fs::absolute(argv[2]);
        Container parameters_initial(fixture / "parameters_initial.coefs");
        Container parameters_final(fixture / "parameters_final.coefs");
        Container optimizer_initial(fixture / "optimizer_initial.params");
        Container optimizer_final(fixture / "optimizer_final.params");
        const auto gradients = load_gradients(fixture / "gradients");
        if (parameters_initial.size() != kExpectedParameters ||
            parameters_final.size() != kExpectedParameters ||
            gradients.size() != kExpectedParameters) {
            throw std::runtime_error("parameter or gradient population differs from 246");
        }

        volatile float beta2_source = kBeta2;
        const float beta2_power = power_f32(beta2_source, kUpdateExponent);
        const float bias_correction = std::sqrt(1.0F - beta2_power);
        const float alpha = kLearningRate * bias_correction;
        float epsilon_squared = kEpsilon * bias_correction;
        epsilon_squared *= epsilon_squared;

        std::vector<TensorResult> tensors;
        tensors.reserve(kExpectedParameters);
        Totals totals {};
        FirstMismatch first {};
        for (const std::string &name : parameters_initial.order()) {
            const Record &parameter_initial = parameters_initial.at(name);
            const Record &parameter_final = parameters_final.at(name);
            require_same_geometry(parameter_initial, parameter_final, name);
            const auto gradient_iterator = gradients.find(name);
            if (gradient_iterator == gradients.end()) {
                throw std::runtime_error("missing gradient " + name);
            }
            const Gradient &gradient_metadata = gradient_iterator->second;
            if (gradient_metadata.type != parameter_initial.type ||
                gradient_metadata.dimensions != parameter_initial.dimensions) {
                throw std::runtime_error("gradient geometry differs for " + name);
            }
            Mapping gradient(gradient_metadata.payload);
            const float sum_squares = gradient_sum_squares(
                gradient, gradient_metadata.type, parameter_initial.count);
            const float norm = std::sqrt(sum_squares);
            const float scale = norm > kGradientClip ? kGradientClip / norm : 1.0F;
            totals.clipped_tensors += scale != 1.0F;

            const Record &variance_initial = optimizer_initial.at(name + ".grad_v");
            const Record &variance_final = optimizer_final.at(name + ".grad_v");
            require_same_geometry(parameter_initial, variance_initial,
                                  name + ".grad_v-initial");
            require_same_geometry(parameter_initial, variance_final,
                                  name + ".grad_v-final");
            TensorResult result;
            if (parameter_initial.type == kBf16) {
                const Record &low_initial = optimizer_initial.at(name + ".low");
                const Record &low_final = optimizer_final.at(name + ".low");
                if (low_initial.type != 7 || low_final.type != 7 ||
                    low_initial.dimensions != parameter_initial.dimensions ||
                    low_final.dimensions != parameter_initial.dimensions) {
                    throw std::runtime_error("BF16 low-word geometry differs for " + name);
                }
                result = replay_bf16(
                    name, parameter_initial, parameter_final, low_initial, low_final,
                    variance_initial, variance_final, gradient, scale, norm, alpha,
                    epsilon_squared, first);
                ++totals.bf16_tensors;
            } else if (parameter_initial.type == kF32) {
                result = replay_f32(
                    name, parameter_initial, parameter_final, variance_initial,
                    variance_final, gradient, scale, norm, alpha, epsilon_squared,
                    first);
                ++totals.f32_tensors;
            } else {
                throw std::runtime_error("parameter type is not F32 or BF16: " + name);
            }
            totals.parameter_words += result.count;
            totals.parameter_high_mismatches += result.parameter_high_mismatches;
            totals.parameter_low_mismatches += result.parameter_low_mismatches;
            totals.variance_mismatches += result.variance_mismatches;
            tensors.push_back(std::move(result));
        }
        if (optimizer_initial.size() != 491 || optimizer_final.size() != 491) {
            throw std::runtime_error("optimizer population differs from 491");
        }
        write_report(report, tensors, totals, first, beta2_power, bias_correction,
                     epsilon_squared);
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
