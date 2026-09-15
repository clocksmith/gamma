// glue.h — optimized "everything else" ops for the fx2 transformer:
// fused rms-norm + activation quantization, residual/coefficient passes,
// embedding + prior input path, and the softcap+softmax head.
//
// NUMERICAL CONTRACT: every function here is BIT-EXACT vs the naive
// reference (src/kernels.cpp + the inline loops of src/model.cpp as compiled
// by clang++-17 -O3 -march=znver2), EXCEPT where exp256/tanh256 replace libm
// (head_softcap_softmax) — those divergences are <= ~1.5 ulp per element and
// are documented at the function. Verified by src/opt/test_glue.cpp.
//
// Conventions:
// - "biased u8" = quantized int8 value + 128 (i.e. int8 XOR 0x80), the layout
//   the vpmaddubsw weight-matmul kernels consume. Padding lanes hold 128
//   (= quantized 0).
// - Activation scales are the fp32 values AFTER bf16 decode (QLinear::s_act),
//   always > 0.
// - Buffers marked "cap 208" must have capacity for 208 floats (205 rounded
//   up); the pad elements are owned/overwritten by the callee.
// - All pointers should be 32B-aligned (loads are issued unaligned, so this
//   is a performance, not correctness, requirement).
#pragma once

#include <cstdint>

#include "sparse_acts.h"

namespace fx2 {
namespace opt {

// ---------- rms-norm (+ fused activation quantization) ----------
// Naive semantics (kernels.cpp): ss = serial 8-wide fmadd sum of squares;
// ms = ss/n; denom = sqrt(ms + FLT_EPSILON); xn[i] = x[i]/denom (IEEE div);
// q[i] = clamp(round_half_even(xn[i]/s), -128, 127)  (IEEE div), stored +128.

// plain norms (bit-exact = fx2::rms_norm_vec)
void rms_norm192(const float* x, float* xn);
void rms_norm64(const float* x, float* xn);   // vanilla per-head q/k norm
float rms_denom192(const float* x);           // the sqrt(mean+eps) scalar

// fused norm + m quantized outputs from ONE xn pass. xn (192 fp32) is always
// emitted (beta-projection and captures need it). Outputs are biased u8,
// out k at q + k*192. m <= 8.
void rms_norm_quant192_multi(const float* x, float* xn, const float* s, int m,
                             uint8_t* q);
// single-output variant (mlp up, unembed input = final norm)
void rms_norm_quant192(const float* x, float* xn, float s, uint8_t* q);
// q/k/v triple (vanilla + kimi projections)
void rms_norm_quant192_x3(const float* x, float* xn, const float s[3],
                          uint8_t* q0, uint8_t* q1, uint8_t* q2);

// plain quantize passes (no norm), biased u8 out
void quant192_u8(const float* x, float s, uint8_t* q);  // attn out -> o-proj
void quant64_u8(const float* x, float s, uint8_t* q);   // low-rank down input
// plain int8 (UNbiased) variant: the vanilla-attention per-head post-rope
// q/k/v quantization — attn.h kernels and the KV ring take signed int8
void quant64_i8(const float* x, float s, int8_t* q);
// mlp activation: y = relu(h)^2 then quantize. h >= 0 after relu so the
// output int8 is in [0,127] and is stored UNBIASED (plain u8) for the
// unsigned x signed vpmaddubsw mlp-down kernel. NOTE: the qmat workstream's
// qgemv_relu2q fuses this into the mlp-up epilogue (bit-identical semantics);
// this standalone remains for non-fused composition.
void relu2_quant768(const float* h, float s, uint8_t* q);

// ---------- residual / coefficient single-pass ops (192) ----------
void axpby_tok192(float a, float* x, float b, const float* tok);  // x = a*x + b*tok
void add192(float* x, const float* y);                            // x += y
void add_scaled192(float* x, float w, const float* s);            // x += w*s

// ---------- embedding + prior input path ----------
// load-time helper: normed token-embedding table (205x192) from the int8
// embedding rows and their fp32(bf16) per-row scales; row = rms_norm(q*s).
// Bit-exact vs the naive loader (model.cpp).
void build_normed_embedding_table(const int8_t* emb_q, const float* row_scale,
                                  float* table);
// f16 -> fp32 prior row (F16C, exact), pads [205..208) zeroed.
void prior_f16_to_f32(const uint16_t* h205, float* out /*cap 208*/);
// prior quantization, RECONCILED with the qmat workstream's sparse-prior
// contract (src/opt/qmat_sparse.h): the prior ints are >= 0, so the dense
// vector is emitted as RAW/unbiased u8 in [0,127] (pads = 0) — exactly what
// qsparse_f32 / the u8 dense prior kernel consume; build the index list with
// their qsparse_make_idx(q8, 205, idx) (idx needs 205+8 entries of room).
void prior_quant_raw(const float* p /*cap 208, pads 0*/, float s,
                     uint8_t* q8 /*cap 208, raw*/);
// self-contained variant predating the qmat contract: biased-u8 dense (pads
// = 128) + embedded SparseActs list. Kept for compositions that do not link
// qmat_sparse; the integration path should prefer prior_quant_raw above.
// The sparse list is filled only when the nonzero count is <= sparse_cap,
// otherwise sp->n = -1 ("row is dense — use the dense matmul path").
void prior_quant(const float* p /*cap 208, pads 0*/, float s,
                 uint8_t* qb /*cap 208*/, SparseActs* sp,
                 int sparse_cap = 205);
// x0 = tok_row + rms_norm(prior_y): the block-0 input, fused single pass
// (bit-exact vs naive rms_norm_vec + add).
void embed_combine192(const float* tok_row, const float* prior_y, float* x0);

// ---------- RoPE building block (vanilla attention) ----------
// One 64-dim head, interleaved pairs (x[2i], x[2i+1]), table row pointers
// sin/cos = &rope_sin[pos*32]. Bit-exact vs clang-compiled fx2::rope_apply:
// y0 = fma(x0,c, x1*s); y1 = fmsub(x1,c, x0*s).
void rope_apply_64(float* head, const float* sin32, const float* cos32);
void rope_apply_192(float* h192, const float* sin32, const float* cos32);

// ---------- head: softcap + softmax (after the unembed matmul) ----------
// l (in-out, cap 208): on entry raw logits [0..205); on exit the softcapped
// logits l = 15*tanh(l/15) (pads set to -15). probs (out, cap 208): fp32
// softmax exp(l-max)/sum over the 205 real elements (pads = 0).
// Same op structure as naive (l/15 by IEEE division; max; e = exp(l-max)
// stored; den accumulated; p = e/den with IEEE division by den) but tanh/exp
// are tanh256/exp256 (<= 2 ulp each; whole-chain capped logits <= 3.9 ulp vs
// double — naive libm measures 3.5 on the same metric) and den is summed
// 2-accumulator 8-lane + lane-tree hsum instead of scalar-serial (order-only
// difference, <= ~1 ulp on den). Measured 1480 cycles/call (naive: ~14.6K);
// max |delta(-log p[target])| vs double reference: 2.3e-6 nats.
void head_softcap_softmax(float* l, float* probs);
// f16 emit of the 205 probabilities (vcvtps2ph round-nearest-even)
void probs_to_f16(const float* probs205, uint16_t* out205);
// e2e-test helper, matches test_e2e's sanity loss term
double neg_log_prob(const float* probs, int target);

}  // namespace opt
}  // namespace fx2
