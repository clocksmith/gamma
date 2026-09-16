// Synthetic native-transformer probe: no corpus, arithmetic coder, or score.
#include "cpp_infer/src/opt/model_opt.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

static uint64_t observations = 0, changed = 0, resets = 0;
static int maximum = 0;
static int32_t last[3][192] = {};
static int expected_arm = 0;

extern "C" void gamma_value_feedback_reset() {
  ++resets;
  std::memset(last, 0, sizeof(last));
}

extern "C" void gamma_value_feedback_observe(
    int layer, int coordinate, int32_t input, int32_t previous,
    int32_t value, int32_t residual) {
  if (layer < 0 || layer >= 3 || coordinate < 0 || coordinate >= 192 ||
      value < -128 || value > 127 || std::abs(residual) > 32768 ||
      input + previous != value * 65536 + residual) std::abort();
  // Ordered callbacks let the observer retain both old and next residuals.
  static int32_t old[3][192] = {};
  if (coordinate == 0) std::memcpy(old[layer], last[layer], sizeof(old[layer]));
  const int donor = coordinate / 64 * 64 +
      (expected_arm == 3 ? (coordinate % 64 + 1) % 64 : coordinate % 64);
  if (previous != old[layer][donor]) std::abort();
  last[layer][coordinate] = residual;
  ++observations;
  changed += residual != 0;
  maximum = std::max(maximum, std::abs(residual));
}

int main(int argc, char** argv) {
  if (argc != 6) return 2;
  const int count = std::atoi(argv[3]);
  expected_arm = std::atoi(argv[4]);
  const int mode = std::atoi(argv[5]);
  if (count < 64 || count > 1088 || expected_arm < 0 || expected_arm > 3 ||
      mode < 0 || mode > 1) return 2;
  fx2::opt::TransformerOpt model(argv[1], fx2::opt::AttnKind::KVI8);
  model.begin_article();
  std::vector<float> output(size_t(count) * 205);
  float prior[205];
  std::fill(prior, prior + 205, 1.0f / 205.0f);
  auto token = [](int t) { return uint8_t((t * 17 + t / 7 + 31) % 205); };
  for (int t = 0; t < count; ++t) {
    float* row = output.data() + t * 205;
    model.step(token(t), prior, row);
    double sum = 0;
    for (int c = 0; c < 205; ++c) {
      if (!std::isfinite(row[c]) || row[c] < 0 || row[c] > 1) return 3;
      sum += row[c];
    }
    if (std::abs(sum - 1) > 1e-5) return 4;
  }
  // Reset an already-used object, including after crossing its 1024 KV window.
  model.begin_article();
  for (int t = 0; t < 64; ++t) {
    float row[205];
    model.step(token(t), prior, row);
    if (std::memcmp(row, output.data() + t * 205, sizeof(row)) != 0) return 5;
  }
  if (mode == 0) {
    FILE* out = std::fopen(argv[2], "wb");
    if (!out) return 6;
    const auto n = std::fwrite(output.data(), sizeof(float), output.size(), out);
    if (std::fclose(out) || n != output.size()) return 7;
  }
  const uint64_t expected = expected_arm ? uint64_t(count + 64) * 576 : 0;
  if (observations != expected || resets != uint64_t(expected_arm ? 2 : 0)) return 8;
  std::printf("{\"observations\":%llu,\"nonzero_residuals\":%llu,"
              "\"maximum_abs_residual\":%d,\"resets\":%llu,\"tokens\":%d}\n",
              (unsigned long long)observations, (unsigned long long)changed,
              maximum, (unsigned long long)resets, count);
}
