// Optimized fused KDA (Kimi linear attention) per-token per-layer step.
// Math follows cpp_infer/KIMI_SEMANTICS.md exactly (validated in test_kda):
//
//   per token, per layer (3 heads, d_head 64):
//     cq/ck/cv = silu(causal_conv4(q_in/k_in/v_in))        (per channel, 192)
//     beta[h]  = sigmoid(beta_raw[h])
//     per head h:
//       qn = l2norm(cq[h]) (eps 1e-6 on the raw sum, inside sqrt); kn likewise
//       decay[i] = exp(a_neg[h] * softplus20(g_raw[h][i] + dt_bias[h][i]))
//       S[i][:] *= decay[i]                    (decay k-rows FIRST)
//       r = S^T kn;  u = beta[h] * (v - r);  S += outer(kn, u)
//       o[h] = S^T (0.125 * qn)                (output AFTER the update)
//     out[h] = rmsnorm64(o[h], eps 1e-5 on the mean) * gn_w * sigmoid(og[h])
//
// Numerics: no -ffast-math; every operation is an explicit intrinsic.
// With the default sweep variant (ONEFIVE) the state recurrence performs
// bit-identically the naive arithmetic of src/kernels.cpp kda_head_step
// (mul-round decay, then fma updates, same per-lane accumulation order);
// the only divergence from the naive path is <= ~2 ulp per elementary
// exp/log-family call (see vmath.h and the accuracy tables in test_kda).
//
// State layout (owned here):
//   S[3][64*64] fp32, 48 KB/layer, contiguous, 64-byte aligned:
//     S[h][i*64 + j], i = k-dim row (decay dim), j = v-dim column.
//   ring[3][4][192] fp32: causal-conv input history for q/k/v.
//     Slot (pos & 3) holds x[t]; taps read slots (pos+1..3)&3 = x[t-3..t-1].
//   pos: steps since article start. kda_layer_reset zeroes everything
//   (article start: conv history and state are zero per cu_seqlens semantics).
#pragma once

#include <cstdint>

namespace fx2 {
namespace opt {

struct KdaWeights {
  // conv weights, tap-major [4][192]: conv_w[c][j*192 + ch] multiplies
  // x[t-3+j][ch] (j=3 newest) — same repacked layout as src/model.cpp.
  const float* conv_w[3] = {nullptr, nullptr, nullptr};  // q, k, v
  const float* dt_bias = nullptr;  // [192], head h owns [64h, 64h+64)
  const float* gn_w = nullptr;     // [64], shared across heads
  float a_neg[3] = {0, 0, 0};      // -exp(A_log[h])
};

struct alignas(64) KdaState {
  float S[3][64 * 64];    // 48 KB per layer
  float ring[3][4][192];  // conv input history ring (q, k, v)
  uint32_t pos = 0;       // steps since reset; ring slot = pos & 3
  uint32_t pad_[15];
};

// Optional diagnostics: any pointer may be null. conv_* are post conv+silu
// (192 each); kda_out is the raw pre-norm output o (192 = 3 heads x 64).
struct KdaDebug {
  float* conv_q = nullptr;
  float* conv_k = nullptr;
  float* conv_v = nullptr;
  float* kda_out = nullptr;
};

// Sweep structure selection (both are exact; see kda.cpp):
//  ONEFIVE (default): pass1 writes the decayed rows while accumulating
//    r = S^T kn; pass2 applies the rank-1 update fused with the output.
//    Bit-identical to the naive kda_head_step arithmetic.
//  TWOPASS: pass1 is read-only, r += (kn_i*decay_i) * S_old[i][:]
//    (the two scalar factors are pre-multiplied — a documented ~1 ulp
//    local rounding change vs naive); pass2 does decay+update+output.
enum class KdaSweep : int { ONEFIVE = 0, TWOPASS = 1 };
void kda_set_sweep(KdaSweep v);
KdaSweep kda_get_sweep();

// Software-prefetch scheme for the state streams (perf only, no numerical
// effect):
//   0 = none (hardware prefetch only)
//   1/2/3 = in-sweep prefetch of the next head during pass 1
//           (4x t0 / 4x t1 / 2x t0 per row) — measured net-negative: they
//           steal AGU slots and L1 fill ports from the store-saturated pass
//   4 = 2x t0 per half-row during pass 2 — also slower
//   5 = DEFAULT: scheduled front-end prefetch: one cursor walks all 48 KB
//       of the layer's head states under the staged nonlinearity passes
//       (~9 B/c metering), so every sweep runs on an L2-warm state
//   6 = like 5 with the t1 hint (measured equal to 5)
void kda_set_pf_mode(int m);
int kda_get_pf_mode();

// Per-phase tick accumulators (lfence;rdtsc ticks — convert with the
// caller's TSC->core-cycle ratio). Enabled only when a profile pointer is
// passed to kda_layer_step; adds ~5 serializing stamps per layer.
struct KdaProfile {
  uint64_t conv = 0;    // conv+silu q/k/v + ring update
  uint64_t gates = 0;   // decay (softplus/exp), beta sigmoid, q/k l2norm
  uint64_t sweep = 0;   // the 3 per-head state sweeps
  uint64_t norm = 0;    // gated rms norm (incl. sigmoid(og))
};

// Reset at article start: zeroes S, conv history and pos.
void kda_layer_reset(KdaState& st);

// The fused per-token step for one layer.
//   q_in/k_in/v_in: fp32[192] pre-conv projection outputs.
//   g_raw:          fp32[192] forget-gate low-rank output (pre dt_bias).
//   og:             fp32[192] output-gate pre-activation.
//   beta_raw:       fp32[3]   beta logits (pre-sigmoid; sigmoid applied here).
//   out:            fp32[192] post gated-norm, pre out-projection.
// Buffers need not be aligned and must not alias the state.
void kda_layer_step(const KdaWeights& w, KdaState& st, const float* q_in,
                    const float* k_in, const float* v_in, const float* g_raw,
                    const float* og, const float* beta_raw, float* out,
                    KdaDebug* dbg = nullptr, KdaProfile* prof = nullptr);

// Exposed for tests/benchmarks: one head's state sweep on precomputed
// inputs. decay/kn[64], v[64], qs[64] = 0.125*qn, beta already sigmoided,
// o[64] output. pf_next: state of the next head to software-prefetch
// during pass1 (may be null).
void kda_sweep_head(float* S, const float* decay, const float* kn,
                    const float* v, float beta, const float* qs, float* o,
                    const float* pf_next, KdaSweep variant);

}  // namespace opt
}  // namespace fx2
