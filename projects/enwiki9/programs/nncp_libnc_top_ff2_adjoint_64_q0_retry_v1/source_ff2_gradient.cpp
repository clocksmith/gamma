#include <algorithm>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <immintrin.h>
#include <stdexcept>
#include <thread>
#include <vector>

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

std::vector<float> read_bf16(const char *path, std::size_t count) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    if (!input || static_cast<std::size_t>(input.tellg()) !=
            count * sizeof(std::uint16_t)) {
        throw std::runtime_error("source BF16 tensor geometry differs");
    }
    input.seekg(0);
    std::vector<std::uint16_t> words(count);
    input.read(reinterpret_cast<char *>(words.data()),
               static_cast<std::streamsize>(words.size() * sizeof(words[0])));
    if (!input) throw std::runtime_error("source BF16 tensor is truncated");
    std::vector<float> result(count);
    std::transform(words.begin(), words.end(), result.begin(), bf16_to_float);
    return result;
}

void write_bf16(const char *path, const std::vector<float> & values) {
    std::vector<std::uint16_t> output(values.size());
    std::transform(values.begin(), values.end(), output.begin(), bf16);
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    stream.write(reinterpret_cast<const char *>(output.data()),
                 static_cast<std::streamsize>(output.size() * sizeof(output[0])));
    if (!stream) throw std::runtime_error("cannot write source FF2 gradient");
}

std::vector<float> matrix_gradient(
    const std::vector<float> & incoming,
    const std::vector<float> & activated
) {
    if (incoming.size() != kSamples * kWidth ||
        activated.size() != kSamples * kInner) {
        throw std::runtime_error("source FF2 gradient geometry differs");
    }
    std::vector<float> result(kInner * kWidth);
    std::vector<std::thread> workers;
    for (std::size_t worker = 0; worker < kThreads; ++worker) {
        workers.emplace_back([&, worker] {
            for (std::size_t inner = worker; inner < kInner;
                 inner += kThreads) {
                float *destination = result.data() + inner * kWidth;
                for (std::size_t output = 0; output < kWidth; output += 8) {
                    __m256 accumulated = _mm256_setzero_ps();
                    for (std::size_t chunk = 0; chunk < kSamples;
                         chunk += kReductionChunk) {
                        __m256 partial = _mm256_setzero_ps();
                        for (std::size_t sample = chunk;
                             sample < chunk + kReductionChunk; ++sample) {
                            partial = _mm256_fmadd_ps(
                                _mm256_set1_ps(
                                    activated[sample * kInner + inner]),
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
    for (std::thread &worker : workers) worker.join();
    return result;
}

}  // namespace

int main(int argc, char **argv) {
    try {
        if (argc != 5) {
            throw std::runtime_error(
                "usage: source_ff2_gradient INPUT ADJOINT OUTPUT CONTROL");
        }
        const std::vector<float> input = read_bf16(argv[1], kSamples * kInner);
        const std::vector<float> adjoint = read_bf16(argv[2], kSamples * kWidth);
        std::vector<float> negated(adjoint.size());
        std::transform(adjoint.begin(), adjoint.end(), negated.begin(),
                       [](float value) { return -value; });
        write_bf16(argv[3], matrix_gradient(adjoint, input));
        write_bf16(argv[4], matrix_gradient(negated, input));
        return 0;
    } catch (const std::exception &error) {
        std::fprintf(stderr, "source FF2 reconstruction failed: %s\n", error.what());
        return 1;
    }
}
