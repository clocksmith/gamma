#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <immintrin.h>
#include <iostream>
#include <regex>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace contract {
constexpr int symbols = 64;
constexpr int vocabulary = 16392;
constexpr int probability_unit = 32768;
constexpr int branch_rows = 896;
}

struct BranchRow {
    uint32_t position;
    uint32_t symbol;
    uint32_t depth;
    uint32_t start;
    uint32_t range;
    uint32_t range0;
    uint32_t probability0;
    uint32_t bit;
};

static uint32_t read_u32(const unsigned char * source) {
    return static_cast<uint32_t>(source[0]) |
           (static_cast<uint32_t>(source[1]) << 8) |
           (static_cast<uint32_t>(source[2]) << 16) |
           (static_cast<uint32_t>(source[3]) << 24);
}

static std::vector<unsigned char> read_bytes(const fs::path & path) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    if (!input) throw std::runtime_error("cannot read " + path.string());
    const std::streamsize size = input.tellg();
    if (size < 0) throw std::runtime_error("cannot size " + path.string());
    std::vector<unsigned char> bytes(static_cast<size_t>(size));
    input.seekg(0);
    input.read(reinterpret_cast<char *>(bytes.data()), size);
    if (!input) throw std::runtime_error("truncated read " + path.string());
    return bytes;
}

static std::vector<float> read_probabilities(const fs::path & path) {
    const std::vector<unsigned char> bytes = read_bytes(path);
    if (bytes.size() != static_cast<size_t>(contract::vocabulary) * sizeof(float))
        throw std::runtime_error("probability tensor has the wrong extent: " + path.string());
    std::vector<float> values(contract::vocabulary);
    std::memcpy(values.data(), bytes.data(), bytes.size());
    return values;
}

static std::vector<BranchRow> read_tree(const fs::path & path) {
    const std::vector<unsigned char> bytes = read_bytes(path);
    constexpr size_t header_bytes = 16;
    constexpr size_t row_bytes = 32;
    if (bytes.size() != header_bytes + contract::branch_rows * row_bytes ||
        std::memcmp(bytes.data(), "NNPTREE1", 8) != 0 ||
        read_u32(bytes.data() + 8) != contract::symbols ||
        read_u32(bytes.data() + 12) != contract::vocabulary)
        throw std::runtime_error("branch oracle differs from the frozen population");
    std::vector<BranchRow> rows;
    rows.reserve(contract::branch_rows);
    for (size_t offset = header_bytes; offset < bytes.size(); offset += row_bytes) {
        const unsigned char * source = bytes.data() + offset;
        rows.push_back({read_u32(source), read_u32(source + 4),
                        read_u32(source + 8), read_u32(source + 12),
                        read_u32(source + 16), read_u32(source + 20),
                        read_u32(source + 24), read_u32(source + 28)});
    }
    return rows;
}

static float libnc_sum64(const std::array<__m256, 8> & x) {
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
    const __m256 g = _mm256_shuffle_ps(h45, h67, 0xee);
    const __m256 h = _mm256_shuffle_ps(u45, u67, 0xee);
    __m256 left_low = _mm256_insertf128_ps(a, _mm256_castps256_ps128(e), 1);
    __m256 left_high = _mm256_insertf128_ps(c, _mm256_castps256_ps128(h), 1);
    __m256 right_low = _mm256_insertf128_ps(b, _mm256_castps256_ps128(f), 1);
    __m256 right_high = _mm256_insertf128_ps(d, _mm256_castps256_ps128(g), 1);
    const __m256 left_low_high = _mm256_permute2f128_ps(a, e, 0x31);
    left_high = _mm256_add_ps(left_high, left_low);
    const __m256 left_high_high = _mm256_permute2f128_ps(c, h, 0x31);
    const __m256 right_low_high = _mm256_permute2f128_ps(b, f, 0x31);
    const __m256 right_high_high = _mm256_permute2f128_ps(d, g, 0x31);
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

static float libnc_sum_values(const float * source, int count) {
    if (count <= 0) throw std::runtime_error("invalid LibNC sum width");
    std::array<float, 16> partials{};
    int blocks = 0;
    int index = 0;
    for (; index + 64 <= count; index += 64, blocks++) {
        std::array<__m256, 8> values;
        for (int lane = 0; lane < 8; lane++)
            values[lane] = _mm256_loadu_ps(source + index + lane * 8);
        float block_sum = libnc_sum64(values);
        int slot = 0;
        while (blocks & (1 << slot)) {
            block_sum += partials[slot];
            partials[slot++] = 0.0f;
        }
        partials[slot] = block_sum;
    }
    if (index < count) {
        alignas(32) std::array<float, 64> tail{};
        std::copy_n(source + index, count - index, tail.data());
        std::array<__m256, 8> values;
        for (int lane = 0; lane < 8; lane++)
            values[lane] = _mm256_load_ps(tail.data() + lane * 8);
        float block_sum = libnc_sum64(values);
        int slot = 0;
        while (blocks & (1 << slot)) {
            block_sum += partials[slot];
            partials[slot++] = 0.0f;
        }
        partials[slot] = block_sum;
        blocks++;
    }
    float total = 0.0f;
    int slots = 0;
    for (int count_left = blocks; count_left; count_left >>= 1) slots++;
    for (int slot = 0; slot < slots; slot++) total += partials[slot];
    return total;
}

static float scalar_sum_values(const float * source, int count) {
    float total = 0.0f;
    for (int index = 0; index < count; index++) total += source[index];
    return total;
}

static int branch_probability(float part, float total) {
    int value = std::lrint(part * contract::probability_unit / total);
    return std::max(1, std::min(contract::probability_unit - 1, value));
}

struct Comparison {
    int mismatches = 0;
    int maximum_difference = 0;
};

using Reducer = float (*)(const float *, int);

static Comparison compare(const std::vector<std::vector<float>> & probabilities,
                          const std::vector<BranchRow> & rows, Reducer reduce) {
    Comparison result;
    std::array<float, contract::symbols> totals{};
    totals.fill(1.0f);
    for (const BranchRow & row : rows) {
        if (row.position >= probabilities.size() || row.range <= 1 ||
            row.range0 != row.range / 2 || row.start + row.range > contract::vocabulary ||
            row.bit > 1 || row.depth >= 15)
            throw std::runtime_error("invalid branch geometry");
        const float part = reduce(probabilities[row.position].data() + row.start,
                                  static_cast<int>(row.range0));
        const int observed = branch_probability(part, totals[row.position]);
        const int difference = std::abs(observed - static_cast<int>(row.probability0));
        result.mismatches += difference != 0;
        result.maximum_difference = std::max(result.maximum_difference, difference);
        totals[row.position] = row.bit ? totals[row.position] - part : part;
    }
    return result;
}

int main(int argc, char ** argv) {
    try {
        if (argc != 2) {
            std::cerr << "usage: " << argv[0] << " FIXTURE_DIR\n";
            return 2;
        }
        const fs::path fixture = argv[1];
        std::vector<fs::path> tensor_paths;
        const std::regex tensor_name("[0-9]{5}_output\\.f32");
        for (const fs::directory_entry & entry : fs::directory_iterator(fixture / "internal"))
            if (entry.is_regular_file() &&
                std::regex_match(entry.path().filename().string(), tensor_name))
                tensor_paths.push_back(entry.path());
        std::sort(tensor_paths.begin(), tensor_paths.end());
        if (tensor_paths.size() != contract::symbols)
            throw std::runtime_error("retained probability population is incomplete");
        std::vector<std::vector<float>> probabilities;
        probabilities.reserve(tensor_paths.size());
        for (const fs::path & path : tensor_paths)
            probabilities.push_back(read_probabilities(path));
        const std::vector<BranchRow> rows = read_tree(fixture / "tree_path.u32le");
        const Comparison scalar = compare(probabilities, rows, scalar_sum_values);
        const Comparison exact = compare(probabilities, rows, libnc_sum_values);
        std::cout << "{\n"
                  << "  \"branchRows\": " << rows.size() << ",\n"
                  << "  \"probabilityTensorCount\": " << probabilities.size() << ",\n"
                  << "  \"scalarMismatchCount\": " << scalar.mismatches << ",\n"
                  << "  \"scalarMaximumDifference\": " << scalar.maximum_difference << ",\n"
                  << "  \"exactMismatchCount\": " << exact.mismatches << ",\n"
                  << "  \"exactMaximumDifference\": " << exact.maximum_difference << "\n"
                  << "}\n";
        return 0;
    } catch (const std::exception & error) {
        std::cerr << error.what() << "\n";
        return 1;
    }
}

