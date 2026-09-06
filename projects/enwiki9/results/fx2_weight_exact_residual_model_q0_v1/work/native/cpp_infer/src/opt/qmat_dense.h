// Dense GEMV kernels over the qmat.h row-major arenas (AVX2, Zen 2 tuned).
// All kernels produce int32 dots that are bit-identical to the naive scalar
// reference (kernels.cpp dot_i8 on the signed ints); the fp32 epilogues use
// exactly the single-rounding formulas documented per function.
//
// Shapes supported (d_out x d_in): any d_out; d_in in {64, 192, 224, 768}.
// Activations: u8, 32B-aligned, zero-padded to m.stride (biased qa+128 or raw
// [0,127] depending on the arena's corr convention — see qmat.h).
#pragma once

#include "qmat.h"

namespace fx2 {
namespace opt {

// (a) out[r] = float(dot[r]) * scale[r]      for r in [0, rows_padded)
void qgemv_f32(const QDense& m, const uint8_t* act, float* out);

// (b) out[r] = out[r] + float(dot[r]) * scale[r]
//     (multiply rounded first, then the add — matches "residual += y" of the
//      naive model exactly; do NOT fuse into an FMA)
void qgemv_add(const QDense& m, const uint8_t* act, float* out);

// (c) mlp.up fused relu^2 + activation-quantize epilogue (d_in must be 192):
//       y = float(dot[r]) * scale[r]
//       y = max(y, 0);  h = y * y                       (fp32)
//       t = h / s_next  (IEEE div);  t = min(t, 127.0f)
//       q = cvt round-half-even(t)                      (in [0,127])
//     q_out[r] = q (u8, raw); idx_out receives the indices r with q != 0
//     (ascending); returns nnz. idx_out needs rows_padded + 8 entries of
//     room (written in 16 B blocks; slack entries are in-range indices).
//     Bit-identical to the naive path: qmatvec -> h=(y>0?y*y:0) ->
//     quantize_i8(h, s_next) reinterpreted as u8.
int qgemv_relu2q(const QDense& m, const uint8_t* act, float s_next,
                 uint8_t* q_out, uint16_t* idx_out);

// (d) low-rank gate chain epilogue (d_in must be 192; d_out 64):
//       y = float(dot[r]) * scale[r]
//       t = y / s_next;  t = clamp(t, -128.0f, 127.0f)
//       q = cvt round-half-even(t);  q_out[r] = u8(q + 128)   (BIASED u8)
//     Bit-identical to naive quantize_i8(y, s_next) + 128.
void qgemv_quant_bias(const QDense& m, const uint8_t* act, float s_next,
                      uint8_t* q_out);

// test/debug epilogue: the exact int32 dots (correction already subtracted)
void qgemv_i32(const QDense& m, const uint8_t* act, int32_t* out);

// benchmark ablation variant of (a) with software prefetch disabled
void qgemv_f32_nopf(const QDense& m, const uint8_t* act, float* out);

// -------- packed int4 alternative (epilogue (a) + test i32 only) --------
// act is SIGNED int8, zero-padded to m.stride4; corr7 = 7 * sum_i qa[i].
void qgemv_packed_f32(const QPacked& m, const int8_t* act, int32_t corr7,
                      float* out);
void qgemv_packed_i32(const QPacked& m, const int8_t* act, int32_t corr7,
                      int32_t* out);

}  // namespace opt
}  // namespace fx2
