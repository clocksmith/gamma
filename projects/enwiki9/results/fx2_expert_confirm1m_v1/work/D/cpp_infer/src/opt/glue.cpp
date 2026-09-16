#include "glue.h"

#include <immintrin.h>

#include <cassert>
#include <cmath>

#include "vec_math.h"

namespace fx2 {
namespace opt {

namespace {

constexpr float RMS_EPS_ = 1.1920928955078125e-07f;  // FLT_EPSILON

// hsum in the exact naive kernels.cpp order:
// ((a0+a4)+(a2+a6)) + ((a1+a5)+(a3+a7))
inline float hsum256_naive(__m256 v) {
  __m128 lo = _mm256_castps256_ps128(v);
  __m128 hi = _mm256_extractf128_ps(v, 1);
  lo = _mm_add_ps(lo, hi);
  lo = _mm_add_ps(lo, _mm_movehl_ps(lo, lo));
  lo = _mm_add_ss(lo, _mm_movehdup_ps(lo));
  return _mm_cvtss_f32(lo);
}

// serial single-accumulator sum of squares — MUST keep the naive order
// (one fmadd chain), n a multiple of 8
inline float sumsq_naive(const float* x, int n) {
  __m256 acc = _mm256_setzero_ps();
  for (int i = 0; i + 8 <= n; i += 8) {
    __m256 v = _mm256_loadu_ps(x + i);
    acc = _mm256_fmadd_ps(v, v, acc);
  }
  return hsum256_naive(acc);
}

inline float rms_denom(const float* x, int n) {
  float ms = sumsq_naive(x, n) / static_cast<float>(n);
  return std::sqrt(ms + RMS_EPS_);
}

// the naive quantize_i8 16-lane pipeline: two fp32 octets (already divided
// by the scale) -> clamp in float -> cvt (nearest-even) -> pack to int8
inline __m128i pack16_i8(__m256 a, __m256 b, __m256 vlo, __m256 vhi) {
  a = _mm256_min_ps(_mm256_max_ps(a, vlo), vhi);
  b = _mm256_min_ps(_mm256_max_ps(b, vlo), vhi);
  __m256i ia = _mm256_cvtps_epi32(a);  // MXCSR default: round half to even
  __m256i ib = _mm256_cvtps_epi32(b);
  __m256i w16 = _mm256_packs_epi32(ia, ib);
  w16 = _mm256_permute4x64_epi64(w16, _MM_SHUFFLE(3, 1, 2, 0));
  return _mm_packs_epi16(_mm256_castsi256_si128(w16),
                         _mm256_extracti128_si256(w16, 1));
}

inline __m128i quant16_i8(__m256 a, __m256 b, __m256 vs, __m256 vlo,
                          __m256 vhi) {
  return pack16_i8(_mm256_div_ps(a, vs), _mm256_div_ps(b, vs), vlo, vhi);
}

const __m128i kBias128 = _mm_set1_epi8(static_cast<char>(0x80));

// generic fused rms-norm + M quantized biased-u8 outputs (n multiple of 16)
template <int M>
inline void rms_norm_quant_impl(const float* x, float* xn, const float* s,
                                uint8_t* q, int n) {
  const float denom = rms_denom(x, n);
  const __m256 vden = _mm256_set1_ps(denom);
  const __m256 vlo = _mm256_set1_ps(-128.0f);
  const __m256 vhi = _mm256_set1_ps(127.0f);
  __m256 vs[M > 0 ? M : 1];
  for (int k = 0; k < M; k++) vs[k] = _mm256_set1_ps(s[k]);
  for (int i = 0; i < n; i += 16) {
    __m256 a = _mm256_div_ps(_mm256_loadu_ps(x + i), vden);
    __m256 b = _mm256_div_ps(_mm256_loadu_ps(x + i + 8), vden);
    _mm256_storeu_ps(xn + i, a);
    _mm256_storeu_ps(xn + i + 8, b);
    for (int k = 0; k < M; k++) {
      __m128i w8 = quant16_i8(a, b, vs[k], vlo, vhi);
      _mm_storeu_si128(reinterpret_cast<__m128i*>(q + k * 192 + i),
                       _mm_xor_si128(w8, kBias128));
    }
  }
}

}  // namespace

void rms_norm192(const float* x, float* xn) {
  const float denom = rms_denom(x, 192);
  const __m256 vden = _mm256_set1_ps(denom);
  for (int i = 0; i < 192; i += 8)
    _mm256_storeu_ps(xn + i, _mm256_div_ps(_mm256_loadu_ps(x + i), vden));
}

void rms_norm64(const float* x, float* xn) {
  const float denom = rms_denom(x, 64);
  const __m256 vden = _mm256_set1_ps(denom);
  for (int i = 0; i < 64; i += 8)
    _mm256_storeu_ps(xn + i, _mm256_div_ps(_mm256_loadu_ps(x + i), vden));
}

float rms_denom192(const float* x) { return rms_denom(x, 192); }

void rms_norm_quant192_multi(const float* x, float* xn, const float* s, int m,
                             uint8_t* q) {
  switch (m) {
    case 1: rms_norm_quant_impl<1>(x, xn, s, q, 192); return;
    case 2: rms_norm_quant_impl<2>(x, xn, s, q, 192); return;
    case 3: rms_norm_quant_impl<3>(x, xn, s, q, 192); return;
    case 4: rms_norm_quant_impl<4>(x, xn, s, q, 192); return;
    case 5: rms_norm_quant_impl<5>(x, xn, s, q, 192); return;
    default: break;
  }
  assert(m > 0 && m <= 8);
  rms_norm192(x, xn);
  for (int k = 0; k < m; k++) quant192_u8(xn, s[k], q + k * 192);
}

void rms_norm_quant192(const float* x, float* xn, float s, uint8_t* q) {
  rms_norm_quant_impl<1>(x, xn, &s, q, 192);
}

void rms_norm_quant192_x3(const float* x, float* xn, const float s[3],
                          uint8_t* q0, uint8_t* q1, uint8_t* q2) {
  const float denom = rms_denom(x, 192);
  const __m256 vden = _mm256_set1_ps(denom);
  const __m256 vlo = _mm256_set1_ps(-128.0f);
  const __m256 vhi = _mm256_set1_ps(127.0f);
  const __m256 vs0 = _mm256_set1_ps(s[0]);
  const __m256 vs1 = _mm256_set1_ps(s[1]);
  const __m256 vs2 = _mm256_set1_ps(s[2]);
  for (int i = 0; i < 192; i += 16) {
    __m256 a = _mm256_div_ps(_mm256_loadu_ps(x + i), vden);
    __m256 b = _mm256_div_ps(_mm256_loadu_ps(x + i + 8), vden);
    _mm256_storeu_ps(xn + i, a);
    _mm256_storeu_ps(xn + i + 8, b);
    _mm_storeu_si128(reinterpret_cast<__m128i*>(q0 + i),
                     _mm_xor_si128(quant16_i8(a, b, vs0, vlo, vhi), kBias128));
    _mm_storeu_si128(reinterpret_cast<__m128i*>(q1 + i),
                     _mm_xor_si128(quant16_i8(a, b, vs1, vlo, vhi), kBias128));
    _mm_storeu_si128(reinterpret_cast<__m128i*>(q2 + i),
                     _mm_xor_si128(quant16_i8(a, b, vs2, vlo, vhi), kBias128));
  }
}

namespace {
inline void quant_u8_n(const float* x, float s, uint8_t* q, int n) {
  const __m256 vs = _mm256_set1_ps(s);
  const __m256 vlo = _mm256_set1_ps(-128.0f);
  const __m256 vhi = _mm256_set1_ps(127.0f);
  for (int i = 0; i < n; i += 16) {
    __m128i w8 = quant16_i8(_mm256_loadu_ps(x + i), _mm256_loadu_ps(x + i + 8),
                            vs, vlo, vhi);
    _mm_storeu_si128(reinterpret_cast<__m128i*>(q + i),
                     _mm_xor_si128(w8, kBias128));
  }
}
}  // namespace

void quant192_u8(const float* x, float s, uint8_t* q) { quant_u8_n(x, s, q, 192); }
void quant64_u8(const float* x, float s, uint8_t* q) { quant_u8_n(x, s, q, 64); }

void quant64_i8(const float* x, float s, int8_t* q) {
  const __m256 vs = _mm256_set1_ps(s);
  const __m256 vlo = _mm256_set1_ps(-128.0f);
  const __m256 vhi = _mm256_set1_ps(127.0f);
  for (int i = 0; i < 64; i += 16) {
    __m128i w8 = quant16_i8(_mm256_loadu_ps(x + i), _mm256_loadu_ps(x + i + 8),
                            vs, vlo, vhi);
    _mm_storeu_si128(reinterpret_cast<__m128i*>(q + i), w8);
  }
}

void relu2_quant768(const float* h, float s, uint8_t* q) {
  const __m256 vs = _mm256_set1_ps(s);
  const __m256 vlo = _mm256_set1_ps(-128.0f);
  const __m256 vhi = _mm256_set1_ps(127.0f);
  const __m256 vz = _mm256_setzero_ps();
  for (int i = 0; i < 768; i += 16) {
    __m256 a = _mm256_max_ps(_mm256_loadu_ps(h + i), vz);
    __m256 b = _mm256_max_ps(_mm256_loadu_ps(h + i + 8), vz);
    a = _mm256_mul_ps(a, a);  // relu(h)^2, bit-equal to (h>0 ? h*h : 0)
    b = _mm256_mul_ps(b, b);
    __m128i w8 = quant16_i8(a, b, vs, vlo, vhi);
    // values in [0,127]: unbiased u8 store for the unsigned mlp-down kernel
    _mm_storeu_si128(reinterpret_cast<__m128i*>(q + i), w8);
  }
}

// ---------- residual / coefficient ops ----------
// contraction shapes matched to clang-compiled model.cpp loops (verified by
// disassembly + test_glue): a*x + b*tok -> fma(a, x, mul(b, tok));
// x += w*s -> fma(w, s, x); x += y -> add.

void axpby_tok192(float a, float* x, float b, const float* tok) {
  const __m256 va = _mm256_set1_ps(a);
  const __m256 vb = _mm256_set1_ps(b);
  for (int i = 0; i < 192; i += 8) {
    __m256 t = _mm256_mul_ps(vb, _mm256_loadu_ps(tok + i));
    _mm256_storeu_ps(x + i, _mm256_fmadd_ps(va, _mm256_loadu_ps(x + i), t));
  }
}

void add192(float* x, const float* y) {
  for (int i = 0; i < 192; i += 8)
    _mm256_storeu_ps(
        x + i, _mm256_add_ps(_mm256_loadu_ps(x + i), _mm256_loadu_ps(y + i)));
}

void add_scaled192(float* x, float w, const float* s) {
  const __m256 vw = _mm256_set1_ps(w);
  for (int i = 0; i < 192; i += 8)
    _mm256_storeu_ps(x + i,
                     _mm256_fmadd_ps(vw, _mm256_loadu_ps(s + i),
                                     _mm256_loadu_ps(x + i)));
}

// ---------- embedding + prior path ----------

void build_normed_embedding_table(const int8_t* emb_q, const float* row_scale,
                                  float* table) {
  for (int c = 0; c < 205; c++) {
    float* row = table + static_cast<size_t>(c) * 192;
    const int8_t* src = emb_q + static_cast<size_t>(c) * 192;
    float sc = row_scale[c];
    for (int i = 0; i < 192; i++)
      row[i] = static_cast<float>(src[i]) * sc;
    rms_norm192(row, row);
  }
}

void prior_f16_to_f32(const uint16_t* h205, float* out) {
  for (int i = 0; i + 8 <= 205; i += 8) {
    __m128i v = _mm_loadu_si128(reinterpret_cast<const __m128i*>(h205 + i));
    _mm256_storeu_ps(out + i, _mm256_cvtph_ps(v));
  }
  {  // tail 197..204 via overlapping window (conversion is elementwise exact)
    __m128i v = _mm_loadu_si128(reinterpret_cast<const __m128i*>(h205 + 197));
    _mm256_storeu_ps(out + 197, _mm256_cvtph_ps(v));
  }
  out[205] = out[206] = out[207] = 0.0f;
}

void prior_quant_raw(const float* p, float s, uint8_t* q8) {
  const __m256 vs = _mm256_set1_ps(s);
  const __m256 vlo = _mm256_set1_ps(-128.0f);
  const __m256 vhi = _mm256_set1_ps(127.0f);
  for (int i = 0; i < 208; i += 16) {
    __m128i w8 = quant16_i8(_mm256_loadu_ps(p + i), _mm256_loadu_ps(p + i + 8),
                            vs, vlo, vhi);
    // prior >= 0 -> ints in [0,127]: raw store IS the unsigned activation
    _mm_storeu_si128(reinterpret_cast<__m128i*>(q8 + i), w8);
  }
}

void prior_quant(const float* p, float s, uint8_t* qb, SparseActs* sp,
                 int sparse_cap) {
  const __m256 vs = _mm256_set1_ps(s);
  const __m256 vlo = _mm256_set1_ps(-128.0f);
  const __m256 vhi = _mm256_set1_ps(127.0f);
  uint32_t masks[13];
  int total = 0;
  for (int b = 0; b < 13; b++) {
    int i = b * 16;
    __m128i w8 = quant16_i8(_mm256_loadu_ps(p + i), _mm256_loadu_ps(p + i + 8),
                            vs, vlo, vhi);
    _mm_storeu_si128(reinterpret_cast<__m128i*>(qb + i),
                     _mm_xor_si128(w8, kBias128));
    __m128i zero = _mm_cmpeq_epi8(w8, _mm_setzero_si128());
    uint32_t nz = ~static_cast<uint32_t>(_mm_movemask_epi8(zero)) & 0xFFFFu;
    masks[b] = nz;
    total += __builtin_popcount(nz);
  }
  if (total > sparse_cap) {  // dense row: signal caller to use the dense path
    sp->n = -1;
    return;
  }
  int n = 0;
  for (int b = 0; b < 13; b++) {
    uint32_t nz = masks[b];
    while (nz) {
      int j = __builtin_ctz(nz) + b * 16;
      nz &= nz - 1;
      sp->idx[n] = static_cast<uint16_t>(j);
      sp->q[n] = static_cast<int8_t>(qb[j] ^ 0x80u);
      n++;
    }
  }
  sp->n = n;  // pads quantize to 0 -> never listed
}

void embed_combine192(const float* tok_row, const float* prior_y, float* x0) {
  const float denom = rms_denom(prior_y, 192);
  const __m256 vden = _mm256_set1_ps(denom);
  for (int i = 0; i < 192; i += 8) {
    __m256 yn = _mm256_div_ps(_mm256_loadu_ps(prior_y + i), vden);
    _mm256_storeu_ps(x0 + i, _mm256_add_ps(_mm256_loadu_ps(tok_row + i), yn));
  }
}

// ---------- RoPE ----------
// pair deinterleave/reinterleave and fma shapes copied from the
// clang-17-compiled naive fx2::rope_apply (bit-exact; see glue.h).

void rope_apply_64(float* head, const float* sin32, const float* cos32) {
  for (int j = 0; j < 4; j++) {
    float* p = head + 16 * j;
    __m256 v0 = _mm256_loadu_ps(p);
    __m256 v1 = _mm256_loadu_ps(p + 8);
    __m256 x0 = _mm256_castpd_ps(_mm256_permute4x64_pd(
        _mm256_castps_pd(_mm256_shuffle_ps(v0, v1, 0x88)), 0xD8));
    __m256 x1 = _mm256_castpd_ps(_mm256_permute4x64_pd(
        _mm256_castps_pd(_mm256_shuffle_ps(v0, v1, 0xDD)), 0xD8));
    __m256 s = _mm256_loadu_ps(sin32 + 8 * j);
    __m256 c = _mm256_loadu_ps(cos32 + 8 * j);
    __m256 y0 = _mm256_fmadd_ps(x0, c, _mm256_mul_ps(x1, s));
    __m256 y1 = _mm256_fmsub_ps(x1, c, _mm256_mul_ps(x0, s));
    __m256 lo = _mm256_unpacklo_ps(y0, y1);
    __m256 hi = _mm256_unpackhi_ps(y0, y1);
    _mm256_storeu_ps(p, _mm256_permute2f128_ps(lo, hi, 0x20));
    _mm256_storeu_ps(p + 8, _mm256_permute2f128_ps(lo, hi, 0x31));
  }
}

void rope_apply_192(float* h192, const float* sin32, const float* cos32) {
  rope_apply_64(h192, sin32, cos32);
  rope_apply_64(h192 + 64, sin32, cos32);
  rope_apply_64(h192 + 128, sin32, cos32);
}

// ---------- head ----------

namespace {
inline float hmax256(__m256 v) {  // max is exact in any order
  __m128 lo = _mm256_castps256_ps128(v);
  __m128 hi = _mm256_extractf128_ps(v, 1);
  lo = _mm_max_ps(lo, hi);
  lo = _mm_max_ps(lo, _mm_movehl_ps(lo, lo));
  lo = _mm_max_ss(lo, _mm_movehdup_ps(lo));
  return _mm_cvtss_f32(lo);
}
}  // namespace

void head_softcap_softmax(float* l, float* probs) {
  l[205] = l[206] = l[207] = -INFINITY;  // pads cap to exactly -15
  const __m256 v15 = _mm256_set1_ps(15.0f);
  // pass 0: a = l/15 (IEEE div like naive) — hoisted so the divider work
  // pipelines independently instead of heading each tanh dependency chain
  alignas(32) float a[208];
  for (int i = 0; i < 208; i += 8)
    _mm256_store_ps(a + i, _mm256_div_ps(_mm256_loadu_ps(l + i), v15));
  __m256 vmax0 = _mm256_set1_ps(-INFINITY);
  __m256 vmax1 = vmax0;
  // 2x unrolled so two tanh dependency chains overlap (3x spills)
  for (int i = 0; i < 208; i += 16) {
    __m256 c0 = _mm256_mul_ps(v15, tanh256_ps(_mm256_load_ps(a + i)));
    __m256 c1 = _mm256_mul_ps(v15, tanh256_ps(_mm256_load_ps(a + i + 8)));
    _mm256_storeu_ps(l + i, c0);  // 15 * tanh(l/15)
    _mm256_storeu_ps(l + i + 8, c1);
    vmax0 = _mm256_max_ps(vmax0, c0);
    vmax1 = _mm256_max_ps(vmax1, c1);
  }
  const __m256 vm = _mm256_set1_ps(hmax256(_mm256_max_ps(vmax0, vmax1)));
  const __m256 tailmask = _mm256_castsi256_ps(
      _mm256_setr_epi32(-1, -1, -1, -1, -1, 0, 0, 0));  // keep 200..204
  __m256 acc0 = _mm256_setzero_ps();
  __m256 acc1 = _mm256_setzero_ps();
  for (int i = 0; i < 192; i += 16) {
    __m256 e0 = exp256_ps(_mm256_sub_ps(_mm256_loadu_ps(l + i), vm));
    __m256 e1 = exp256_ps(_mm256_sub_ps(_mm256_loadu_ps(l + i + 8), vm));
    _mm256_storeu_ps(probs + i, e0);
    _mm256_storeu_ps(probs + i + 8, e1);
    acc0 = _mm256_add_ps(acc0, e0);
    acc1 = _mm256_add_ps(acc1, e1);
  }
  {
    __m256 e0 = exp256_ps(_mm256_sub_ps(_mm256_loadu_ps(l + 192), vm));
    __m256 e1 = exp256_ps(_mm256_sub_ps(_mm256_loadu_ps(l + 200), vm));
    e1 = _mm256_and_ps(e1, tailmask);
    _mm256_storeu_ps(probs + 192, e0);
    _mm256_storeu_ps(probs + 200, e1);
    acc0 = _mm256_add_ps(acc0, e0);
    acc1 = _mm256_add_ps(acc1, e1);
  }
  // den = hsum(acc0 + acc1), 8-lane tree order (documented divergence from
  // the naive scalar-serial sum: <= ~1 ulp on den)
  const float den = hsum256_naive(_mm256_add_ps(acc0, acc1));
  const __m256 vden = _mm256_set1_ps(den);
  for (int i = 0; i < 208; i += 8)
    _mm256_storeu_ps(probs + i,
                     _mm256_div_ps(_mm256_loadu_ps(probs + i), vden));
}

void probs_to_f16(const float* probs205, uint16_t* out205) {
  for (int i = 0; i + 8 <= 205; i += 8) {
    __m128i h = _mm256_cvtps_ph(_mm256_loadu_ps(probs205 + i),
                                _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
    _mm_storeu_si128(reinterpret_cast<__m128i*>(out205 + i), h);
  }
  {  // tail via overlapping window
    __m128i h = _mm256_cvtps_ph(_mm256_loadu_ps(probs205 + 197),
                                _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
    _mm_storeu_si128(reinterpret_cast<__m128i*>(out205 + 197), h);
  }
}

double neg_log_prob(const float* probs, int target) {
  return -std::log(static_cast<double>(probs[target]));
}

}  // namespace opt
}  // namespace fx2
