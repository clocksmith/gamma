// sparse_acts.h — self-contained sparse view of a quantized activation
// vector (prior probabilities row).
//
// RECONCILED 2026-07-19: the qmat workstream's src/opt/qmat_sparse.h defines
// the OPERATIVE sparse-prior matmul contract — a dense RAW u8 vector in
// [0,127] plus a separate uint16 index list built by qsparse_make_idx (idx
// buffer needs nnz+8 entries of room). The integration path is
//   fx2::opt::prior_quant_raw(p, s, q8) + fx2::opt::qsparse_make_idx(q8,
//   205, idx) -> qsparse_f32/qsparse_add, falling back to the dense u8
//   kernel for dense rows.
// This struct (embedded signed values) remains for compositions that do not
// link qmat_sparse; both describe the same ascending nonzero index set.
#pragma once

#include <cstdint>

namespace fx2 {

// Sparse view of a quantized activation vector (prior probabilities row).
// - n       : number of nonzero quantized entries (0..205)
// - idx[i]  : ascending element indices of the nonzeros (0..204)
// - q[i]    : the SIGNED quantized value at idx[i], in [-128,127], nonzero.
//             (For the prior row the input is >= 0, so in practice q in
//             [1,127]; the clamp at 127 does saturate for peaked priors.)
// The corresponding dense biased-u8 vector (value+128, padded to 208 with
// bias 128 = q 0) is produced alongside by fx2::opt::prior_quant for kernels
// that prefer the dense vpmaddubsw path when the row is not sparse.
struct SparseActs {
  int n;
  uint16_t idx[205];
  int8_t q[205];
};

}  // namespace fx2
