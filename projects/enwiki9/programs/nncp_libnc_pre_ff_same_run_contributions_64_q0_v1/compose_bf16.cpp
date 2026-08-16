#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <vector>

namespace fs = std::filesystem;

namespace {

constexpr std::size_t kElements = 2'097'152;

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

std::vector<std::uint16_t> read_words(const fs::path & path) {
    if (!fs::is_regular_file(path) ||
        fs::file_size(path) != kElements * sizeof(std::uint16_t)) {
        throw std::runtime_error("same-run contribution geometry differs");
    }
    std::vector<std::uint16_t> words(kElements);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char *>(words.data()),
               static_cast<std::streamsize>(fs::file_size(path)));
    if (!input) throw std::runtime_error("truncated same-run contribution");
    return words;
}

void write_words(const fs::path & path,
                 const std::vector<std::uint16_t> & words) {
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(words.data()),
                 static_cast<std::streamsize>(
                     words.size() * sizeof(words[0])));
    if (!output) throw std::runtime_error("cannot write same-run composition");
}

}  // namespace

int main(int argc, char ** argv) {
    if (argc != 5) {
        throw std::runtime_error(
            "usage: compose_bf16 BRANCH DIRECT TOTAL NEGATED");
    }
    const std::vector<std::uint16_t> branch = read_words(argv[1]);
    const std::vector<std::uint16_t> direct = read_words(argv[2]);
    std::vector<std::uint16_t> total(kElements);
    std::vector<std::uint16_t> negated(kElements);
    for (std::size_t index = 0; index < kElements; ++index) {
        const float branch_value = bf16_to_float(branch[index]);
        const float direct_value = bf16_to_float(direct[index]);
        total[index] = bf16(branch_value + direct_value);
        negated[index] = bf16(direct_value - branch_value);
    }
    write_words(argv[3], total);
    write_words(argv[4], negated);
    return 0;
}
