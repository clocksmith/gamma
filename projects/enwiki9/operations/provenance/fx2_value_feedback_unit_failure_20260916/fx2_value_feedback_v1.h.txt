#pragma once
// Authored reference kernel. No corpus compression or native-model claim.
// First-order error feedback is established sigma-delta quantization.
#include <cmath>
#include <cstdint>

namespace gamma_value_feedback_v1 {
constexpr int32_t Q = 65536;
constexpr int32_t HALF = Q / 2;
constexpr int32_t MINIMUM = -128 * Q;
constexpr int32_t MAXIMUM = 127 * Q;

struct Result {
  bool valid;
  int32_t value;
  int32_t residual;
};

inline int32_t round_q16(int32_t value) {
  const int64_t magnitude = value < 0 ? -int64_t(value) : value;
  int32_t whole = magnitude / Q;
  const int32_t remainder = magnitude % Q;
  if (remainder > HALF || (remainder == HALF && (whole & 1))) ++whole;
  return value < 0 ? -whole : whole;
}

// Input is the parent's already-computed normalized FP32 value. Clipping and
// Q16 conversion are explicit; no host rounding-mode dependent integer cast.
inline bool normalized_q16(float value, int32_t& result) {
  if (!std::isfinite(value)) return false;
  if (value < -128.0f) value = -128.0f;
  if (value > 127.0f) value = 127.0f;
  const double scaled = static_cast<double>(value) * Q;
  const double below = std::floor(scaled);
  int32_t whole = static_cast<int32_t>(below);
  const double fraction = scaled - below;
  if (fraction > 0.5 || (fraction == 0.5 && whole % 2 != 0)) ++whole;
  result = whole;
  return true;
}

inline Result step(int32_t input, int32_t previous) {
  if (input < MINIMUM || input > MAXIMUM ||
      previous < -HALF || previous > HALF) return {false, 0, 0};
  const int32_t total = input + previous;
  int32_t value = round_q16(total);
  if (value < -128) value = -128;
  if (value > 127) value = 127;
  const int32_t residual = total - value * Q;
  return {true, value, residual};
}
}  // namespace gamma_value_feedback_v1
