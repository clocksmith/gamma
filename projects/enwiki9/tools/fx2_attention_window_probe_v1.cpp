// Synthetic kernel probe; excluded from the production source delivery.
#include "cpp_infer/src/opt/attn.h"
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <new>

struct Probe {
  fx2::opt::AttnKVF32 kv;
  uint64_t clock = 0;
  Probe() { std::memset(&kv, 0x55, sizeof(kv)); }
};

extern "C" {
unsigned window_size() { return fx2::opt::ATTN_WIN; }
void* window_new() { return new (std::nothrow) Probe; }
void window_delete(void* p) { delete static_cast<Probe*>(p); }
unsigned window_step(void* p, const int8_t* q, const int8_t* k,
                     const int8_t* v, const float* coef, const float* sv,
                     float* out) {
  auto& s = *static_cast<Probe*>(p);
  const unsigned w = fx2::opt::ATTN_WIN;
  fx2::opt::attn_kv_insert(s.kv, unsigned(s.clock % w), k, v);
  const unsigned n = unsigned(std::min<uint64_t>(++s.clock, w));
  // The native kernel uses aligned stores; foreign callers need not be aligned.
  alignas(32) float aligned[192];
  if (n < w) fx2::opt::attn_step_var(s.kv, q, coef, sv, n, aligned, 0.0f);
  else fx2::opt::attn_step_fixed(s.kv, q, coef, sv, aligned, 0.0f);
  std::memcpy(out, aligned, sizeof(aligned));
  return n;
}
}
