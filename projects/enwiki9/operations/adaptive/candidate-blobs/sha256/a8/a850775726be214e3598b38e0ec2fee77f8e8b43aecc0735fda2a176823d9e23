#include <array>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace {

constexpr std::size_t kFeatures = 6144;
constexpr std::size_t kStreams = 32;
constexpr std::size_t kStates = 64;
constexpr std::size_t kElements = kFeatures * kStreams * kStates;

float decode_bf16(std::uint16_t word) {
    const std::uint32_t bits = static_cast<std::uint32_t>(word) << 16U;
    float value;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

std::uint16_t encode_bf16(float value) {
    std::uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    const std::uint32_t rounding = 0x7fffU + ((bits >> 16U) & 1U);
    return static_cast<std::uint16_t>((bits + rounding) >> 16U);
}

std::vector<std::uint16_t> read_payload(const fs::path & path) {
    if (!fs::is_regular_file(path) ||
        fs::file_size(path) != kElements * sizeof(std::uint16_t)) {
        throw std::runtime_error("FF1-output residual geometry differs");
    }
    std::vector<std::uint16_t> payload(kElements);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char *>(payload.data()),
               static_cast<std::streamsize>(fs::file_size(path)));
    if (!input) throw std::runtime_error("cannot read FF1-output residual");
    return payload;
}

void write_payload(const fs::path & path,
                   const std::vector<std::uint16_t> & payload) {
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(payload.data()),
                 static_cast<std::streamsize>(
                     payload.size() * sizeof(payload[0])));
    if (!output) throw std::runtime_error("cannot write FF1 bias gradient");
}

std::vector<std::uint16_t> state_reduce(
    const std::vector<std::uint16_t> & payload,
    bool reverse_states,
    bool negate
) {
    std::vector<std::uint16_t> gradient(kFeatures, 0);
    for (std::size_t step = 0; step < kStates; ++step) {
        const std::size_t state = reverse_states ? kStates - 1 - step : step;
        for (std::size_t feature = 0; feature < kFeatures; ++feature) {
            float total = decode_bf16(gradient[feature]);
            for (std::size_t stream = 0; stream < kStreams; ++stream) {
                const std::size_t index =
                    ((state * kStreams + stream) * kFeatures) + feature;
                std::uint16_t word = payload[index];
                if (negate) word ^= UINT16_C(0x8000);
                total += decode_bf16(word);
            }
            gradient[feature] = encode_bf16(total);
        }
    }
    return gradient;
}

std::vector<std::uint16_t> flat_reduce(
    const std::vector<std::uint16_t> & payload
) {
    std::vector<std::uint16_t> gradient(kFeatures);
    for (std::size_t feature = 0; feature < kFeatures; ++feature) {
        float total = 0.0F;
        for (std::size_t sample = 0; sample < kStates * kStreams; ++sample) {
            total += decode_bf16(payload[sample * kFeatures + feature]);
        }
        gradient[feature] = encode_bf16(total);
    }
    return gradient;
}

}  // namespace

int main(int argc, char ** argv) {
    try {
        if (argc != 6) {
            throw std::runtime_error(
                "usage: ff1_bias_state_reduce INPUT TREATMENT FLAT REVERSE NEGATED");
        }
        const std::vector<std::uint16_t> payload = read_payload(argv[1]);
        write_payload(argv[2], state_reduce(payload, false, false));
        write_payload(argv[3], flat_reduce(payload));
        write_payload(argv[4], state_reduce(payload, true, false));
        write_payload(argv[5], state_reduce(payload, false, true));
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "open FF1 bias reduction failed: %s\n", error.what());
        return 1;
    }
}
