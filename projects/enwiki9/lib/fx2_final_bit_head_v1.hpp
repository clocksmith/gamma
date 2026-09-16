// Causal correction of the final bit probability. No original model is updated.
#ifndef GAMMA_FX2_FINAL_BIT_HEAD_V1_HPP
#define GAMMA_FX2_FINAL_BIT_HEAD_V1_HPP
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <vector>

namespace gamma_final_bit_head {
#if defined(__GNUC__) && !defined(__clang__)
#pragma GCC push_options
#pragma GCC optimize ("fp-contract=off")
#endif
constexpr unsigned D = 192, ROWS = 255, Q = 65536;
inline void require(bool ok) { if (!ok) std::abort(); }

// Nearest integer count, upward ties, with the parent's legal endpoints.
inline uint32_t corrected_count(uint32_t parent, double correction) {
  require(parent > 0 && parent < Q && std::isfinite(correction));
  require(std::fabs(correction) <= 4.00001);
  if (correction == 0) return parent;
  const double a = double(parent) * std::exp(correction);
  const double q = a / (double(Q - parent) + a);
  const unsigned count = unsigned(std::floor(Q * q + 0.5));
  return count < 1 ? 1 : count >= Q ? Q - 1 : count;
}

class Model {
 public:
  char arm;
  std::array<double, ROWS * D> weights{};
  std::array<double, D> feature{};
  uint64_t position = 0, predictions = 0, updates = 0, resets = 0;
  unsigned prefix = 1, previous_byte = 0;
  bool previous_valid = false, feature_valid = false, pending = false;
  uint32_t parent_count = 32768, candidate_count = 32768;

  explicit Model(char a): arm(a) {
    require(a == 'P' || a == 'K' || a == 'D' || a == 'S');
  }

  void reset_article() {
    require(!pending && position % 8 == 0 && prefix == 1);
    weights.fill(0);
    feature.fill(0);
    feature_valid = false;
    previous_valid = false;
    previous_byte = 0;
    ++resets;
  }

  void invalidate_feature() {
    require(!pending && position % 8 == 0 && prefix == 1);
    feature.fill(0);
    feature_valid = false;
  }

  void capture(const float* hidden) {
    require(!pending && position % 8 == 0 && prefix == 1);
    double norm2 = 1;
    for (unsigned i = 0; i < D; ++i) {
      require(std::isfinite(hidden[i]));
      norm2 += double(hidden[i]) * hidden[i];
    }
    require(std::isfinite(norm2));
    const double inv = 1 / std::sqrt(norm2);
    for (unsigned i = 0; i < D; ++i) feature[i] = hidden[i] * inv;
    feature_valid = true;
  }

  uint32_t predict(uint32_t parent) {
    require(!pending && prefix > 0 && prefix < 256);
    require(parent > 0 && parent < Q);
    parent_count = parent;
    double correction = 0;
    if (feature_valid && arm != 'P') {
      const unsigned start = (prefix - 1) * D;
      for (unsigned i = 0; i < D; ++i)
        correction += weights[start + i] * feature[i];
    }
    candidate_count = corrected_count(parent, correction);
    pending = true;
    ++predictions;
    return arm == 'P' || arm == 'K' ? parent : candidate_count;
  }

  void observe(unsigned truth) {
    require(pending && truth < 2);
    if (feature_valid && previous_valid && arm != 'P') {
      const unsigned label = arm == 'S'
          ? (previous_byte >> (7 - position % 8)) & 1 : truth;
      const double residual = double(label) - double(candidate_count) / Q;
      const unsigned start = (prefix - 1) * D;
      double norm2 = 0;
      for (unsigned i = 0; i < D; ++i) {
        double& w = weights[start + i];
        w += 0.25 * residual * feature[i];
        norm2 += w * w;
      }
      require(std::isfinite(norm2));
      if (norm2 > 16) {
        const double scale = 3.999999999 / std::sqrt(norm2);
        for (unsigned i = 0; i < D; ++i) weights[start + i] *= scale;
      }
      ++updates;
    }
    prefix = prefix * 2 + truth;
    ++position;
    if (position % 8 == 0) {
      previous_byte = prefix - 256;
      previous_valid = true;
      prefix = 1;
    }
    pending = false;
  }

  // Full introduced state; arm is deliberately excluded for K/D comparisons.
  std::vector<uint8_t> state() const {
    require(!pending);
    std::vector<uint8_t> out;
    auto put = [&](uint64_t value, unsigned bytes) {
      for (unsigned i = 0; i < bytes; ++i) out.push_back(uint8_t(value >> (8*i)));
    };
    for (uint64_t x : {position, predictions, updates, resets}) put(x, 8);
    for (unsigned x : {prefix, previous_byte, parent_count, candidate_count}) put(x, 4);
    put(previous_valid, 1); put(feature_valid, 1); put(pending, 1);
    auto doubles = [&](const auto& array) {
      for (double x : array) { uint64_t bits; std::memcpy(&bits, &x, 8); put(bits, 8); }
    };
    doubles(feature); doubles(weights);
    return out;
  }
};
#if defined(__GNUC__) && !defined(__clang__)
#pragma GCC pop_options
#endif
}
#endif
