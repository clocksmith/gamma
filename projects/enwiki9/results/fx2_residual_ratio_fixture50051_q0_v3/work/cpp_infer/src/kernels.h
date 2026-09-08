// Free-function kernels for the fx2 transformer (correctness-first AVX2/scalar).
// Numerical contracts follow cpp_infer/SPEC.md and cpp_infer/KIMI_SEMANTICS.md.
#pragma once

#include <cmath>
#include <cstdint>

namespace fx2 {

// torch rms_norm default eps for fp32 = FLT_EPSILON
constexpr float RMS_EPS = 1.1920928955078125e-07f;

// ---------- basic fp32 ----------
float sum_squares(const float* x, int n);
// y[i] = x[i] / sqrt(mean_j(x[j]^2) + RMS_EPS); y may alias x
void rms_norm_vec(const float* x, float* y, int n);
float dot_f32(const float* a, const float* b, int n);

// ---------- activation quantization (SPEC section 2) ----------
// q[i] = clamp(round_half_even(x[i] / scale), -128, 127), IEEE fp32 division;
// q[n..n_pad) is zero-filled (padding for the int matmul row stride)
void quantize_i8(const float* x, int n, int n_pad, float scale, int8_t* q);

// ---------- integer matmul ----------
// exact int32 dot product of two int8 vectors; n must be a multiple of 16
int32_t dot_i8(const int8_t* a, const int8_t* b, int n);
// y[o] = fold[o] * float(dot_i8(qx, w + o*stride, stride)), o in [0, d_out)
void qmatvec(const int8_t* w, int stride, const float* fold, int d_out,
             const int8_t* qx, float* y);

// ---------- scalar nonlinearities (libm accuracy; no fast-math) ----------
inline float sigmoid1f(float z) { return 1.0f / (1.0f + std::exp(-z)); }
inline float siluf(float z) { return z / (1.0f + std::exp(-z)); }
// softplus with threshold exactly 20 (KIMI_SEMANTICS section 4)
inline float softplus20f(float x) {
  return (x > 20.0f) ? x : std::log1p(std::exp(x));
}

// ---------- kimi causal conv (k=4) + SiLU (KIMI_SEMANTICS section 3) ----------
// wt is tap-major [4][d] (wt[j][c] multiplies x[t-3+j][c]; wt[3] = newest);
// h0 = x[t-3], h1 = x[t-2], h2 = x[t-1], xc = x[t]; y[c] = silu(sum of taps)
void conv4_silu(const float* wt, const float* h0, const float* h1,
                const float* h2, const float* xc, float* y, int d);

// ---------- KDA per-head recurrence (KIMI_SEMANTICS section 1) ----------
// S: fp32 [64][64] row-major, row index = k dim; updated in place.
// a_neg = -exp(A_log[head]); beta already sigmoided. o[64] output.
void kda_head_step(float* S, const float* q, const float* k, const float* v,
                   const float* g_raw, const float* dt_bias, float a_neg,
                   float beta, float* o);

// FusedRMSNormGated, d=64 (KIMI_SEMANTICS section 2):
// y = o / sqrt(mean(o^2) + 1e-5) * w * sigmoid(og)
void gated_rms_norm64(const float* o, const float* og, const float* w,
                      float* y);

// ---------- RoPE (SPEC section 3.6), interleaved pairs ----------
// h192 = 3 heads x 64, in place; sin32/cos32 = the 32 fp32 table entries
void rope_apply(float* h192, const float* sin32, const float* cos32);

// ---------- vanilla sliding-window attention (SPEC section 3.5) ----------
// Ring layout: kring/vring hold int8 rows of 192 (3 heads x 64) per slot.
// coef3[h] = 0.125*sq[h]*sk[h]; sv3[h] = per-head value scale.
// out192[h*64 + i] = attention output (fp32), pre output-projection.
// skip_threshold: 0 = exact (default); > 0 enables skipping positions with
// (max_score - score) > skip_threshold (excluded from softmax denominator).
//
// variable-length kernel: valid slots are exactly [0, n), n = t+1 < 1024
void attention_step_var(const int8_t* q192, const int8_t* kring,
                        const int8_t* vring, const float* coef3,
                        const float* sv3, int n, float* out192,
                        float skip_threshold);
// fixed-length kernel: all 1024 ring slots valid (t+1 >= 1024)
void attention_step_fixed(const int8_t* q192, const int8_t* kring,
                          const int8_t* vring, const float* coef3,
                          const float* sv3, float* out192,
                          float skip_threshold);

// ---------- misc ----------
// exact widening conversion of n IEEE half-precision values
void f16_to_f32(const uint16_t* h, float* out, int n);

}  // namespace fx2
