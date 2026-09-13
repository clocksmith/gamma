// Fixed causal KDA memory carryover; independent of the trained weight format.
#pragma once
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace gamma_kda_carry {
inline void fail(const char* reason) {
  std::fprintf(stderr, "Gamma KDA carry: %s\n", reason);
  std::_Exit(125);
}
inline char arm() {
  const char* value = std::getenv("GAMMA_FX2_KDA_ARM");
  if (!value) return 'P';
  if (!value[0] || value[1] || !std::strchr("PKDS", value[0])) fail("invalid arm");
  return value[0];
}
template<class State> void reset(State& state, char selected) {
  if (selected == 'P') { std::memset(&state, 0, sizeof(state)); return; }
  float retained[3][4096];
  for (unsigned h=0; h<3; ++h)
    for (unsigned i=0; i<64; ++i)
      for (unsigned j=0; j<64; ++j) {
        const unsigned column = selected == 'S' ? (j+1)%64 : j;
        const float value = state.S[h][i*64+column] * 0.0625f;
        if (!std::isfinite(value)) fail("nonfinite retained state");
        retained[h][i*64+j] = value;
      }
  std::memset(&state, 0, sizeof(state));
  if (selected != 'K') std::memcpy(state.S, retained, sizeof(retained));
}
// At this declared boundary t=0 makes every KV cache entry unavailable.
// S, convolution history and pos are all live KDA state; padding is excluded.
template<class State> void audit(const State* states, long long t, long long rope) {
  const char* path = std::getenv("GAMMA_FX2_KDA_TRACE");
  if (!path) return;
  if (t != 0) fail("audit requires invalidated KV cache");
  FILE* file = std::fopen(path, "ab");
  if (!file) fail("audit open failed");
  auto write = [&](const void* data, size_t bytes) {
    if (std::fwrite(data, 1, bytes, file) != bytes) fail("audit write failed");
  };
  write("KDC1", 4); write(&t, 8); write(&rope, 8);
  for (unsigned i=0; i<9; ++i) {
    write(states[i].S, sizeof(states[i].S));
    write(states[i].ring, sizeof(states[i].ring));
    write(&states[i].pos, sizeof(states[i].pos));
  }
  if (std::fclose(file)) fail("audit close failed");
}
}
