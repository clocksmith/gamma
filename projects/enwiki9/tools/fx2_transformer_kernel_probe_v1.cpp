// Diagnostic kernel measurement of the pinned public model, not a codec score.
// The runner authenticates source/weights and enforces the memory/scratch guard.
#include <sched.h>
#include <sys/resource.h>
#include <unistd.h>

#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <vector>

#include "opt/model_opt.h"

namespace {
constexpr int kVocabulary = 205;
constexpr int kWarmup = 1024;
constexpr int kMeasured = 512;
constexpr int kRepeats = 2;
constexpr uint64_t kOffset = UINT64_C(14695981039346656037);
constexpr uint64_t kPrime = UINT64_C(1099511628211);

uint64_t now_ns() {
  return std::chrono::duration_cast<std::chrono::nanoseconds>(
      std::chrono::steady_clock::now().time_since_epoch()).count();
}

bool cpu_two_only() {
  cpu_set_t cpus;
  CPU_ZERO(&cpus);
  return sched_getaffinity(0, sizeof(cpus), &cpus) == 0 &&
         CPU_COUNT(&cpus) == 1 && CPU_ISSET(2, &cpus) && sched_getcpu() == 2;
}

uint64_t digest(const std::vector<float>& probabilities) {
  uint64_t hash = kOffset;
  const auto* bytes = reinterpret_cast<const unsigned char*>(probabilities.data());
  for (size_t i = 0; i < probabilities.size() * sizeof(float); ++i)
    hash = (hash ^ bytes[i]) * kPrime;
  return hash;
}

struct Run {
  uint64_t load_ns = 0, warmup_ns = 0, measured_ns = 0, probability_digest = 0;
  double maximum_sum_error = 0;
};
}  // namespace

int main(int argc, char** argv) {
  if (argc != 3) {
    std::fprintf(stderr, "usage: %s PACKED_WEIGHTS OUTPUT_PROBABILITIES_F32LE\n", argv[0]);
    return 2;
  }
  // Scientific execution ceiling, independent of the runner's process guard.
  alarm(30);
  static_assert(sizeof(float) == 4 && std::numeric_limits<float>::is_iec559,
                "the retained probability stream requires IEEE float32");
  const uint32_t endian = 1;
  if (*reinterpret_cast<const unsigned char*>(&endian) != 1 || !cpu_two_only()) {
    std::fprintf(stderr, "requires little-endian IEEE float32 and exclusive CPU 2 affinity\n");
    return 2;
  }
  FILE* weights = std::fopen(argv[1], "rb");
  char magic[8] = {};
  bool packed = weights && std::fread(magic, 1, sizeof(magic), weights) == sizeof(magic) &&
                std::memcmp(magic, "FX2TFWC2", sizeof(magic)) == 0;
  if (weights) std::fclose(weights);
  if (!packed) {
    std::fprintf(stderr, "expected pinned FX2TFWC2 packed public weights\n");
    return 2;
  }
  FILE* output = std::fopen(argv[2], "wbx");
  if (!output) {
    std::perror("create probability output");
    return 2;
  }

  // Fixed synthetic inputs exercise the trained 205 x 192, 12-layer model.
  // Priors alternate uniform (nearest float16 to 1/205) and one-hot rows.
  // These inputs do not represent measured CMIX prior statistics or text loss.
  std::array<uint8_t, kWarmup + kMeasured> tokens{};
  std::array<std::array<uint16_t, kVocabulary>, kWarmup + kMeasured> priors{};
  for (int t = 0; t < kWarmup + kMeasured; ++t) {
    tokens[t] = static_cast<uint8_t>((73 * t + 19) % kVocabulary);
    priors[t].fill(t % 2 == 0 ? UINT16_C(0x1cff) : 0);
    if (t % 2 != 0) priors[t][tokens[t]] = UINT16_C(0x3c00);
  }
  std::array<Run, kRepeats> runs{};
  std::vector<float> first, probabilities(kMeasured * kVocabulary);
  std::array<float, kVocabulary> discarded{};
  bool identical = true;
  for (int r = 0; r < kRepeats; ++r) {
    uint64_t before = now_ns();
    // Match predictor.cpp: optimized inference with the int8-V attention cache.
    fx2::opt::TransformerOpt model(argv[1], fx2::opt::AttnKind::KVI8);
    model.begin_article(0);
    runs[r].load_ns = now_ns() - before;
    before = now_ns();
    for (int t = 0; t < kWarmup; ++t)
      model.step(tokens[t], priors[t].data(), discarded.data());
    runs[r].warmup_ns = now_ns() - before;
    before = now_ns();
    for (int t = 0; t < kMeasured; ++t)
      model.step(tokens[kWarmup + t], priors[kWarmup + t].data(),
                 probabilities.data() + t * kVocabulary);
    runs[r].measured_ns = now_ns() - before;
    for (int t = 0; t < kMeasured; ++t) {
      double sum = 0;
      for (int v = 0; v < kVocabulary; ++v) {
        float p = probabilities[t * kVocabulary + v];
        if (!std::isfinite(p) || p < 0 || p > 1) {
          std::fprintf(stderr, "invalid probability at repeat %d token %d index %d\n", r, t, v);
          std::fclose(output);
          return 1;
        }
        sum += p;
      }
      double error = std::fabs(sum - 1.0);
      if (error > runs[r].maximum_sum_error) runs[r].maximum_sum_error = error;
      if (error > 0.0005) {
        std::fprintf(stderr, "probability sum outside frozen tolerance\n");
        std::fclose(output);
        return 1;
      }
    }
    if (!cpu_two_only() || runs[r].measured_ns == 0) {
      std::fprintf(stderr, "CPU affinity or timing evidence failed\n");
      std::fclose(output);
      return 1;
    }
    runs[r].probability_digest = digest(probabilities);
    if (r == 0) first = probabilities;
    else identical = identical &&
        std::memcmp(first.data(), probabilities.data(), probabilities.size() * sizeof(float)) == 0;
    if (std::fwrite(probabilities.data(), sizeof(float), probabilities.size(), output) != probabilities.size()) {
      std::perror("write probability output");
      std::fclose(output);
      return 1;
    }
  }
  if (std::fclose(output) != 0) {
    std::perror("close probability output");
    return 1;
  }
  rusage usage{};
  bool rss_available = getrusage(RUSAGE_SELF, &usage) == 0;
  std::printf("{\"schema\":\"gamma.enwiki9.fx2-kernel-probe.v1\",\"cpu\":2,"
              "\"model\":\"TransformerOpt-KVI8\",\"vocabulary\":205,\"dimension\":192,"
              "\"layers\":12,\"attention_window\":1024,\"warmup_tokens_per_repeat\":1024,"
              "\"measured_tokens_per_repeat\":512,\"repeats\":2,\"total_steps\":3072,"
              "\"inputs\":\"synthetic-cyclic-tokens-alternating-uniform-onehot-f16-priors\","
              "\"probabilities_finite_and_normalized\":true,\"repeat_probabilities_identical\":%s,"
              "\"probability_output_bytes\":%zu,\"digest_kind\":\"fnv1a64-f32le-diagnostic\","
              "\"timing_authority\":\"shared-host-diagnostic\",\"objective_credit_bytes\":0,"
              "\"resource_evidence_complete\":false,\"process_lifetime_peak_rss_kib\":",
              identical ? "true" : "false", probabilities.size() * sizeof(float) * kRepeats);
  if (rss_available) std::printf("%ld", usage.ru_maxrss);
  else std::printf("null");
  std::printf(",\"runs\":[");
  for (int r = 0; r < kRepeats; ++r)
    std::printf("%s{\"repeat\":%d,\"load_ns\":%llu,\"warmup_ns\":%llu,"
                "\"measured_ns\":%llu,\"ns_per_token\":%.3f,\"probability_digest\":\"%016llx\","
                "\"maximum_probability_sum_error\":%.12g}",
                r ? "," : "", r, static_cast<unsigned long long>(runs[r].load_ns),
                static_cast<unsigned long long>(runs[r].warmup_ns),
                static_cast<unsigned long long>(runs[r].measured_ns),
                double(runs[r].measured_ns) / kMeasured,
                static_cast<unsigned long long>(runs[r].probability_digest), runs[r].maximum_sum_error);
  std::printf("]}\n");
  return identical ? 0 : 1;
}
