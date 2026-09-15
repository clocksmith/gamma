// qmat.h — quantized-matmul weight-arena format + descriptors (AVX2 / Zen 2).
//
// This file DEFINES the weight storage format the optimized kernels consume.
// At integration this becomes the model's in-memory format (the weights FILE
// stays as in SPEC section 4; the loader repacks into these arenas).
//
// =========================================================================
// 1. DENSE ROW-MAJOR ARENA (one per matmul, consumed strictly sequentially)
// =========================================================================
// Weights are UNPACKED int8 (one byte per weight, values in [-7,7], two's
// complement). Per MACHINE.md section 3 this beats packed int4 at the model's
// ~6 MB L3 footprint (20.4-21.4 vs 18.6-20.4 MAC/cyc).
//
// Geometry:
//   stride      = round_up(d_in, 32)          (in-dim padded, pad weights = 0)
//   group_rows  = 8  if d_in <= 256           (G8 kernels)
//                 4  if d_in == 768           (G4 kernel, register pressure)
//   rows_padded = round_up(d_out, group_rows) (pad rows: weights 0, scale 0,
//                                              corr 0 -> output rows = +0.0f)
//   nchunk      = stride / 32
//   ngroups     = rows_padded / group_rows
//
// Arena = ngroups consecutive GROUP BLOCKS, base 64B-aligned, no gaps:
//   group block (G8) = [ 8 x int32 corr | 8 x fp32 scale |  weights ]
//                          32 B              32 B          nchunk*8*32 B
//   group block (G4) = [ 4 x int32 corr | 4 x fp32 scale |  weights ]
//                          16 B              16 B          nchunk*4*32 B
//   weights are chunk-major: for c in [0,nchunk): for r in [0,group_rows):
//     the 32 bytes of row (group*group_rows + r), columns [32c, 32c+32).
//
// Metadata semantics (per row o):
//   scale[o] = fold = s_act * fp32(bf16(w_scale[o]))   (can be NEGATIVE)
//   corr[o]  = 128 * sum_i qw[o][i]   if the activation is BIASED u8
//                                     (qa + 128, qa in [-128,127])
//            = 0                      if the activation is RAW u8 in [0,127]
//                                     (relu^2 outputs, quantized priors)
// The kernel computes  dot[o] = sum_i act_u8[i]*qw[o][i] - corr[o]  which for
// the biased case equals the exact signed int32 dot sum_i qa[i]*qw[o][i]
// (16-bit intermediate accumulation is safe: <= 8 chunk maddubs results,
// 8*2*255*7 = 28560 < 32767). The bias convention is thus a property of the
// ARENA, not of the kernel.
//
// Group bytes: d_in=192: 1600, d_in=64: 576, d_in=224(prior): 1856 (all
// multiples of 64); d_in=768: 3104 (multiple of 32).
//
// The buffer holding an arena must have QMAT_TAIL_SLACK extra mapped bytes
// after the stream (software prefetch runs ~2 KB ahead).
//
// Activation vectors passed to the kernels must be 32B-aligned and padded
// with zeros to `stride` bytes (padding value is irrelevant for correctness
// when pad weights are 0, but 0 keeps sums reproducible).
//
// Output buffers must have room for `rows_padded` floats (only the unembedding
// 205->208 actually pads; pad entries are written/clobbered).
//
// =========================================================================
// 2. SPARSE COLUMN-MAJOR ARENA (192-out matmuls with sparse RAW-u8 inputs:
//    mlp.down 192x768, prior_embedding 192x205)
// =========================================================================
//   cols   : d_in consecutive columns; column c = 192 int8 (rows in natural
//            order, values [-7,7]) at byte offset c*192. Base 64B-aligned ->
//            every column is 64B-aligned (192 = 3 cache lines).
//   fold   : separate 64B-aligned fp32[192] of per-row folded scales.
// Input activations are RAW u8 in [0,127] (relu^2 / prior ints; zero skipping
// is exact because a q==0 column contributes nothing). The caller supplies the
// dense u8 vector plus a u16 index list of the nonzero positions (produced for
// free by the mlp.up relu^2 epilogue). corr is always 0 here.
// The index buffer must have >= 8 writable slack entries past nnz (the
// producers write in 16 B blocks; slack entries hold in-range values, which
// keeps the kernel's lookahead prefetch on mapped memory).
//
// =========================================================================
// 3. PACKED INT4 ARENA (compile-time ALTERNATIVE, for the packed-vs-unpacked
//    comparison; not the recommended production format)
// =========================================================================
// 4-row groups: [4 x fp32 scale, 16 B pad | nibbles]. Per 32-byte weight
// vector: row r columns [64p,64p+32) in the LOW nibbles and [64p+32,64p+64)
// in the HIGH nibbles, stored as unsigned qw+7 in [0,14]. Activations SIGNED
// int8 (unbiased; raw [0,127] values also work). The correction is the single
// scalar 7*sum_i qa[i], passed by the caller. stride4 = round_up(d_in, 64).
//
// =========================================================================
// All builders take the same inputs the model loader has: row-major int8
// weights in [-7,7] and the folded per-row fp32 scales.
#pragma once

#include <cstddef>
#include <cstdint>

namespace fx2 {
namespace opt {

// mapped slack required after every arena (prefetch overrun)
constexpr size_t QMAT_TAIL_SLACK = 4096;

constexpr int qmat_round_up(int x, int m) { return (x + m - 1) / m * m; }

constexpr int qmat_group_rows(int d_in) { return d_in <= 256 ? 8 : 4; }

// ---------------- dense row-major descriptor ----------------
struct QDense {
  const uint8_t* arena = nullptr;  // 64B-aligned group-block stream
  int d_out = 0, d_in = 0;
  int stride = 0;       // round_up(d_in, 32)
  int nchunk = 0;       // stride / 32
  int group_rows = 0;   // 8 or 4
  int ngroups = 0;      // rows_padded / group_rows
  int rows_padded = 0;  // round_up(d_out, group_rows)
  size_t bytes = 0;     // total stream bytes (multiple of the group size)
};

// arena size in bytes (excluding QMAT_TAIL_SLACK)
size_t qdense_bytes(int d_out, int d_in);

// Build a dense arena into dst (64B-aligned, qdense_bytes + QMAT_TAIL_SLACK
// mapped). qw is row-major [d_out][d_in] in [-7,7]; fold[d_out] the folded
// fp32 row scales. biased_input selects the corr convention (see above).
QDense qdense_build(uint8_t* dst, const int8_t* qw, const float* fold,
                    int d_out, int d_in, bool biased_input);

// ---------------- sparse column-major descriptor ----------------
struct QSparse {
  const int8_t* cols = nullptr;  // 64B-aligned, d_in * 192 bytes
  const float* fold = nullptr;   // 64B-aligned fp32[192]
  int d_in = 0;
  int d_out = 0;  // always 192
};

size_t qsparse_bytes(int d_in);  // = d_in * 192

// dst_cols 64B-aligned with qsparse_bytes + QMAT_TAIL_SLACK mapped;
// dst_fold 64B-aligned fp32[192]. d_out must be 192.
QSparse qsparse_build(int8_t* dst_cols, float* dst_fold, const int8_t* qw,
                      const float* fold, int d_out, int d_in);

// ---- int4-packed column variant (RECOMMENDED for the sparse matmuls) ----
// The index-driven gather is cache-LINE-fetch-bound under realistic full-
// stream conditions (measured ~17-22 cyc/col for 3-line int8 columns), so
// halving the column to 2 lines wins ~20-30% despite extra unpack ALU:
//   column c at byte offset c*128: 96 bytes of nibbles (byte b: LOW nibble =
//   row b + 7, HIGH nibble = row 96+b + 7, values [0,14]) + 32 pad bytes.
//   Base 64B-aligned -> every column is exactly 2 aligned cache lines.
// The kernel keeps the nibbles unsigned as the vpmaddubsw unsigned operand
// (activation pair as the signed one) and subtracts the exact global
// correction 7 * sum(processed act values) once in the int32 epilogue:
// results are bit-identical to the int8 column kernels. The one-sided s16
// bound (2*14*127 = 3556 per pair) means it widens every 9 pairs.
struct QSparse4 {
  const uint8_t* cols = nullptr;  // 64B-aligned, d_in * 128 bytes
  const float* fold = nullptr;    // 64B-aligned fp32[192]
  int d_in = 0;
  int d_out = 0;  // always 192
};

size_t qsparse4_bytes(int d_in);  // = d_in * 128
QSparse4 qsparse4_build(uint8_t* dst_cols, float* dst_fold, const int8_t* qw,
                        const float* fold, int d_out, int d_in);

// ---------------- packed int4 descriptor (comparison alternative) ---------
struct QPacked {
  const uint8_t* arena = nullptr;
  int d_out = 0, d_in = 0;
  int stride4 = 0;  // round_up(d_in, 64): logical cols per row
  int npair = 0;    // stride4 / 64: 32-byte weight vectors per row
  int ngroups = 0;  // rows_padded4 / 4
  int rows_padded = 0;
  size_t bytes = 0;
};

size_t qpacked_bytes(int d_out, int d_in);
QPacked qpacked_build(uint8_t* dst, const int8_t* qw, const float* fold,
                      int d_out, int d_in);

// Empirically determined density threshold (bench_qmat): above this nonzero
// fraction, switch from the index-driven sparse kernel to the column-dense
// fallback. Measured on the int4 column arenas the two are within noise of
// each other even at density 1.0 (the index-driven loop is the same pair
// loop and becomes sequential), so the fallback exists only to bound the
// worst case; with a row-major dense arena also resident one could switch to
// qgemv_add at ~0.65 instead (7.0 vs ~8.5 Kcyc at density 1), at +1.7 MB L3.
constexpr float QMAT_SPARSE_DENSITY_THRESHOLD = 0.95f;

}  // namespace opt
}  // namespace fx2
