// EXACT sparse GEMV kernels over the qmat.h column-major arenas.
// Skipping q==0 input channels changes nothing mathematically; the int32
// accumulators equal the full dense dot bit-for-bit.
//
// Inputs: dense u8 activation vector q8 (values [0,127], raw/unbiased) plus a
// u16 ascending index list of the nonzero positions. The index buffer must
// have >= 8 readable entries past nnz containing in-range values (the
// qgemv_relu2q / qsparse_make_idx producers guarantee this) — the kernel's
// column prefetch reads ahead of the current pair.
//
// Column pairs are interleaved on the fly (vpunpcklbw/hbw) and consumed by
// vpmaddubsw(act_pair_u8, interleaved_s8): 384 MACs per 12 madd-pipe ops.
// 16-bit accumulators (12 ymm = 192 rows) are widened into an int32[192]
// buffer every 18 pairs (18 * 2 * 127 * 7 = 32004 < 32767: no saturation).
#pragma once

#include "qmat.h"

namespace fx2 {
namespace opt {

// out[r] = fold[r] * float(dot[r])
void qsparse_f32(const QSparse& m, const uint8_t* q8, const uint16_t* idx,
                 int nnz, float* out);
// out[r] = out[r] + fold[r] * float(dot[r])   (mul rounded, then add)
void qsparse_add(const QSparse& m, const uint8_t* q8, const uint16_t* idx,
                 int nnz, float* out);
// test/debug: raw int32 dots
void qsparse_i32(const QSparse& m, const uint8_t* q8, const uint16_t* idx,
                 int nnz, int32_t* out);

// benchmark ablation variant with column prefetch disabled
void qsparse_f32_nopf(const QSparse& m, const uint8_t* q8,
                      const uint16_t* idx, int nnz, float* out);

// dense fallback over the SAME column-major arena (iterates every column;
// use when nnz/d_in > QMAT_SPARSE_DENSITY_THRESHOLD). Bit-identical results.
void qsparse_dense_f32(const QSparse& m, const uint8_t* q8, float* out);
void qsparse_dense_add(const QSparse& m, const uint8_t* q8, float* out);
void qsparse_dense_i32(const QSparse& m, const uint8_t* q8, int32_t* out);

// ---- int4-packed column kernels (see qmat.h QSparse4; bit-exact vs the
// int8 column kernels and the scalar reference; corr = 0) ----
void qsparse4_f32(const QSparse4& m, const uint8_t* q8, const uint16_t* idx,
                  int nnz, float* out);
void qsparse4_add(const QSparse4& m, const uint8_t* q8, const uint16_t* idx,
                  int nnz, float* out);
void qsparse4_i32(const QSparse4& m, const uint8_t* q8, const uint16_t* idx,
                  int nnz, int32_t* out);
void qsparse4_dense_f32(const QSparse4& m, const uint8_t* q8, float* out);
void qsparse4_dense_add(const QSparse4& m, const uint8_t* q8, float* out);
void qsparse4_dense_i32(const QSparse4& m, const uint8_t* q8, int32_t* out);

// Build the nonzero index list of q8[0..n) (e.g. the quantized prior).
// Writes in 16 B blocks: idx must have n + 8 entries of room; slack entries
// receive in-range values. q8 must be zero-padded to a multiple of 32 bytes.
// Returns nnz.
int qsparse_make_idx(const uint8_t* q8, int n, uint16_t* idx);

}  // namespace opt
}  // namespace fx2
