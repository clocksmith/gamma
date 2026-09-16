// Diagnostic-only full residual stream. Excluded from the delivered codec.
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace gamma_value_observer_v1 {
inline void fail() { std::_Exit(125); }
struct Sink {
  FILE* file = nullptr;
  uint64_t observations = 0;
  uint32_t resets = 0;
  int32_t state[3][192] = {}, old[3][192] = {};
  Sink() {
    const char* name = std::getenv("GAMMA_VALUE_FEEDBACK_TRACE");
    if (!name || !*name || !(file = std::fopen(name, "wbx"))) fail();
    if (std::fwrite("GVF1", 1, 4, file) != 4) fail();
  }
  void word(uint32_t v) {
    unsigned char bytes[4];
    for (unsigned i = 0; i < 4; ++i) bytes[i] = v >> (i * 8);
    if (std::fwrite(bytes, 1, 4, file) != 4) fail();
  }
  ~Sink() {
    if (observations % 576) fail();
    word(0x80000001u);
    word(uint32_t(observations)); word(uint32_t(observations >> 32));
    word(resets);
    if (std::fclose(file)) fail();
  }
};
inline Sink& sink() { static Sink s; return s; }
}  // namespace gamma_value_observer_v1

extern "C" inline void gamma_value_feedback_reset() {
  auto& s = gamma_value_observer_v1::sink();
  if (s.observations % 576) gamma_value_observer_v1::fail();
  std::memset(s.state, 0, sizeof(s.state));
  ++s.resets;
  s.word(0x80000000u);
}

extern "C" inline void gamma_value_feedback_observe(
    int layer, int coordinate, int32_t input, int32_t previous,
    int32_t value, int32_t residual) {
  using namespace gamma_value_observer_v1;
  auto& s = sink();
  const int expected_layer = (s.observations % 576) / 192;
  const int expected_coordinate = s.observations % 192;
  if (layer != expected_layer || coordinate != expected_coordinate ||
      value < -128 || value > 127 || residual < -32768 || residual > 32768 ||
      input + previous != value * 65536 + residual) fail();
  if (coordinate == 0) std::memcpy(s.old[layer], s.state[layer], sizeof(s.old[layer]));
  const int donor = coordinate / 64 * 64 +
      (GAMMA_VALUE_FEEDBACK_ARM == 3 ? (coordinate % 64 + 1) % 64 : coordinate % 64);
  if (previous != s.old[layer][donor]) fail();
  s.state[layer][coordinate] = residual;
  ++s.observations;
  s.word(uint32_t(residual));
}
