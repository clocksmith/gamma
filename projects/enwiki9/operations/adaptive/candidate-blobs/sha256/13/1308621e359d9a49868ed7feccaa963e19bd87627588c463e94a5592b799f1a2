#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <immintrin.h>
#include <stdexcept>
#include <thread>
#include <vector>

namespace fs = std::filesystem;

namespace {

constexpr std::size_t kStreams = 32;
constexpr std::size_t kStates = 64;
constexpr std::size_t kSamples = kStreams * kStates;
constexpr std::size_t kWidth = 1024;
constexpr std::size_t kInner = 3072;
constexpr std::size_t kReductionChunk = 128;
constexpr std::size_t kThreads = 4;

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

std::vector<float> read_geglu(const fs::path & root) {
    std::vector<float> result(kSamples * kInner);
    for (std::size_t stream = 0; stream < kStreams; ++stream) {
        char name[32];
        std::snprintf(name, sizeof(name), "stream_%02zu", stream);
        const std::vector<float> current = read_f32(
            root / name / "layer_19_geglu_output.f32", kStates * kInner);
        for (std::size_t state = 0; state < kStates; ++state) {
            const std::size_t sample = stream + kStreams * state;
            std::copy_n(current.data() + state * kInner, kInner,
                        result.data() + sample * kInner);
        }
    }
    for (float value : result) {
        std::uint32_t bits;
        std::memcpy(&bits, &value, sizeof(bits));
        if ((bits & 0xffffU) != 0) {
            throw std::runtime_error("layer-19 GEGLU output is not BF16-exact");
        }
    }
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
    const std::vector<float> & incoming,
    const std::vector<float> & geglu
) {
    if (incoming.size() != kSamples * kWidth ||
        geglu.size() != kSamples * kInner) {
        throw std::runtime_error("top FF2 gradient geometry differs");
    }
    std::vector<float> result(kInner * kWidth);
    std::vector<std::thread> workers;
    for (std::size_t worker = 0; worker < kThreads; ++worker) {
        workers.emplace_back([&, worker] {
            for (std::size_t inner = worker; inner < kInner;
                 inner += kThreads) {
                float * destination = result.data() + inner * kWidth;
                for (std::size_t output = 0; output < kWidth; output += 8) {
                    __m256 accumulated = _mm256_setzero_ps();
                    for (std::size_t chunk = 0; chunk < kSamples;
                         chunk += kReductionChunk) {
                        __m256 partial = _mm256_setzero_ps();
                        for (std::size_t sample = chunk;
                             sample < chunk + kReductionChunk; ++sample) {
                            partial = _mm256_fmadd_ps(
                                _mm256_set1_ps(geglu[sample * kInner + inner]),
                                _mm256_loadu_ps(
                                    incoming.data() + sample * kWidth + output),
                                partial);
                        }
                        accumulated = _mm256_add_ps(accumulated, partial);
                    }
                    _mm256_storeu_ps(destination + output, accumulated);
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
        if (argc != 5) {
            throw std::runtime_error(
                "usage: top_ff2_gradient OPEN_ROOT INPUT_RESIDUAL "
                "OUT_FF2 CONTROL_FF2");
        }
        const std::vector<float> geglu = read_geglu(argv[1]);
        const std::vector<float> incoming = read_bf16(
            argv[2], kSamples * kWidth);
        std::vector<float> negated(incoming.size());
        std::transform(incoming.begin(), incoming.end(), negated.begin(),
                       [](float value) { return -value; });
        write_bf16(argv[3], matrix_gradient(incoming, geglu));
        write_bf16(argv[4], matrix_gradient(negated, geglu));
        return 0;
    } catch (const std::exception & error) {
        std::fprintf(stderr, "top FF2 gradient failed: %s\n", error.what());
        return 1;
    }
}
