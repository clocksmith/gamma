// Optimized vanilla sliding-window attention (SPEC.md section 3.5) for the
// 3 vanilla layers (3/7/11): W=1024, 3 heads x d_head 64, int8 q/k/v with
// per-head static scales. Single-threaded; the score/exp scratch buffers are
// file-static (NOT reentrant).
//
// ---------------------------------------------------------------------------
// KV-cache layout (owned by this module)
// ---------------------------------------------------------------------------
// slot = position % 1024. The score index j IS the slot index: softmax is
// order-independent, so scores are produced and consumed in slot/memory order,
// never in temporal order.
//   * variable kernel (t+1 < 1024): slots [0, n) are valid and are exactly
//     positions 0..n-1 (no wraparound can have happened yet) -> validity is a
//     PREFIX of the arrays.
//   * fixed kernel (t+1 >= 1024): ALL 1024 slots are valid.
// Consequence: the K scan is always ONE contiguous ascending-address pass
// ([0,n) or [0,1024)); ring wraparound never splits the stream, so the
// hardware prefetcher (helped by prefetcht0 +2KB) sees pure sequential reads.
//
// K is stored TRANSPOSED and pair-interleaved for vpmaddwd batching over
// positions, per head (head-major so each head's scan is one sequential
// stream):
//   k[head][block][pair][2*lane + {0,1}], block = slot/16, lane = slot%16,
//   pair = dim/2. One 32-byte row holds dim-pair (2i, 2i+1) of 16 positions;
//   vpmovsxbw of each 16-byte half -> 8 positions x (int16 lo,hi) pairs, and
//   vpmaddwd against a vpbroadcastd'ed q int16-pair accumulates the exact
//   int32 dot of 8 positions VERTICALLY (no horizontal sums anywhere).
//   K bytes: 64 KB/head, 192 KB/layer (int8 variant; same total as a naive
//   row ring).
// V is stored per head, slot-major plain int8 rows:
//   v[head][slot][64]  (64 KB/head, 192 KB/layer). PV dequantizes on the fly
//   (vpmovsxbd + vcvtdq2ps); the value scale sv and the softmax denominator
//   are folded into ONE final multiply per output element.
//
// Layout variants and the MEASURED verdict (bench_attn, realistic cache =
// 5.9 MB weight-stream thrash between calls, real article22 data, cycles for
// the 3-layer attention component per token):
//   AttnKV    int8 K + int8 V   384 KB/layer (1.125 MB total)
//               146.6K @ n=863, 170.4K @ n=1024, insert 281 cyc
//   AttnKV16  int16 K + int8 V  576 KB/layer — SLOWER (153.8K @ 863): the
//               doubled K stream from L3 costs more than the saved
//               vpmovsxbw unpacks. Rejected.
//   AttnKVF32 int8 K + fp32 V   960 KB/layer — FASTEST (138.5K @ 863,
//               163.8K @ 1024, insert 360 cyc): PV becomes pure
//               load+fmadd (~29K/layer, L3-BW-bound) vs int8's
//               conversion-pipe-bound ~32K/layer. vcvtdq2ps and the
//               lane-crossing vpmovsxbd both run at ~1/cyc on Zen 2, putting
//               an ~8-9 cyc/row floor on any int-stored V.
// Recommendation: AttnKVF32 when the whole-model L3 budget allows the extra
// 1.7 MB (SPEC treats footprint as secondary), AttnKV otherwise; outputs are
// bitwise-identical between the variants (test_attn asserts it), so the
// choice is purely a footprint/speed knob at integration time. The naive
// reference lives in src/kernels.h.
//
// ---------------------------------------------------------------------------
// Numerics
// ---------------------------------------------------------------------------
// score[h][j] = coef3[h] * float(qq[h] . qk[h][j])  -- the int32 dot is exact
// and float() of it is exact (|dot| <= 2^20 < 2^24), so scores are
// BIT-IDENTICAL to the naive kernel, and so is the running max.
// softmax/PV are fp32 like the naive kernel but reassociated (vector partial
// sums; sv/den folded): with skip OFF the output matches the naive kernel to
// ~1e-7 relative (exp256_ps vs libm expf <= 1 ulp per term; see vec_math.h).
//
// skip_threshold semantics (matches naive attention_step_*): <= 0 -> exact,
// every valid position enters the softmax. > 0 -> positions with
// (score[j] - max) < -skip_threshold are skipped: excluded from the softmax
// denominator, their exp is never computed and their V row is never loaded.
// The kept SET is bit-identical to the naive kernel's (the compare runs on
// the same d = score - max values). The toggle is a runtime float; when off
// the only residual cost is the (always-vectorized) compare+movemask that
// also drives the group-skip fast path.
#pragma once

#include <cstdint>

namespace fx2 {
namespace opt {

// phase profile counters (rdtsc ticks; populated only when attn.cpp is
// compiled with -DATTN_PROFILE): [0]=qk scan, [1]=exp/denominator, [2]=pv,
// [3]=number of per-head iterations profiled
extern uint64_t g_attn_prof[4];

constexpr int ATTN_WIN = 1024;
constexpr int ATTN_NH = 3;
constexpr int ATTN_DH = 64;
constexpr int ATTN_BLK = 16;  // positions per K block
constexpr int ATTN_NBLK = ATTN_WIN / ATTN_BLK;

// production KV cache: int8 transposed K + int8 V (384 KB)
struct AttnKV {
  alignas(64) int8_t k[ATTN_NH][ATTN_NBLK][ATTN_DH / 2][2 * ATTN_BLK];
  alignas(64) int8_t v[ATTN_NH][ATTN_WIN][ATTN_DH];
};

// measurement variant: int16 K (skips vpmovsxbw, doubles K bytes; 576 KB)
struct AttnKV16 {
  alignas(64) int16_t k[ATTN_NH][ATTN_NBLK][ATTN_DH / 2][2 * ATTN_BLK];
  alignas(64) int8_t v[ATTN_NH][ATTN_WIN][ATTN_DH];
};

// measurement variant: fp32 V mirror (PV without int->float conversion,
// 4x the V bytes; 960 KB)
struct AttnKVF32 {
  alignas(64) int8_t k[ATTN_NH][ATTN_NBLK][ATTN_DH / 2][2 * ATTN_BLK];
  alignas(64) float v[ATTN_NH][ATTN_WIN][ATTN_DH];
};

// Shared insert path: scatter k192 (3 heads x 64, post-rope int8 ints) into
// the transposed pair rows of slot, copy v192 into the per-head V rows.
void attn_kv_insert(AttnKV& kv, int slot, const int8_t* k192,
                    const int8_t* v192);
void attn_kv_insert(AttnKV16& kv, int slot, const int8_t* k192,
                    const int8_t* v192);
void attn_kv_insert(AttnKVF32& kv, int slot, const int8_t* k192,
                    const int8_t* v192);

// Attention step kernels. q192 = 3 heads x 64 int8 ints; coef3[h] =
// 0.125*sq[h]*sk[h]; sv3[h] = per-head value scale; out192 = fp32 attention
// output (pre output-projection). kept3 (optional): number of positions that
// entered the softmax per head (for skip statistics).
//
// variable-shape kernel: n = t+1 in [1, 1024) valid slots (prefix of the ring)
void attn_step_var(const AttnKV& kv, const int8_t* q192, const float* coef3,
                   const float* sv3, int n, float* out192,
                   float skip_threshold, int* kept3 = nullptr);
void attn_step_var(const AttnKV16& kv, const int8_t* q192, const float* coef3,
                   const float* sv3, int n, float* out192,
                   float skip_threshold, int* kept3 = nullptr);
void attn_step_var(const AttnKVF32& kv, const int8_t* q192, const float* coef3,
                   const float* sv3, int n, float* out192,
                   float skip_threshold, int* kept3 = nullptr);

// fixed-shape kernel: exactly 1024 valid slots, fully specialized loops
void attn_step_fixed(const AttnKV& kv, const int8_t* q192, const float* coef3,
                     const float* sv3, float* out192, float skip_threshold,
                     int* kept3 = nullptr);
void attn_step_fixed(const AttnKV16& kv, const int8_t* q192,
                     const float* coef3, const float* sv3, float* out192,
                     float skip_threshold, int* kept3 = nullptr);
void attn_step_fixed(const AttnKVF32& kv, const int8_t* q192,
                     const float* coef3, const float* sv3, float* out192,
                     float skip_threshold, int* kept3 = nullptr);

}  // namespace opt
}  // namespace fx2
