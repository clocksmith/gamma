#include "kernels.h"

#include <immintrin.h>

#include <cassert>
#include <cmath>

namespace fx2 {

namespace {

inline float hsum256(__m256 v) {
  __m128 lo = _mm256_castps256_ps128(v);
  __m128 hi = _mm256_extractf128_ps(v, 1);
  lo = _mm_add_ps(lo, hi);
  lo = _mm_add_ps(lo, _mm_movehl_ps(lo, lo));
  lo = _mm_add_ss(lo, _mm_movehdup_ps(lo));
  return _mm_cvtss_f32(lo);
}

inline int32_t hsum256_i32(__m256i v) {
  __m128i lo = _mm256_castsi256_si128(v);
  __m128i hi = _mm256_extracti128_si256(v, 1);
  lo = _mm_add_epi32(lo, hi);
  lo = _mm_add_epi32(lo, _mm_shuffle_epi32(lo, _MM_SHUFFLE(1, 0, 3, 2)));
  lo = _mm_add_epi32(lo, _mm_shuffle_epi32(lo, _MM_SHUFFLE(2, 3, 0, 1)));
  return _mm_cvtsi128_si32(lo);
}

}  // namespace

float sum_squares(const float* x, int n) {
  int i = 0;
  __m256 acc = _mm256_setzero_ps();
  for (; i + 8 <= n; i += 8) {
    __m256 v = _mm256_loadu_ps(x + i);
    acc = _mm256_fmadd_ps(v, v, acc);
  }
  float s = hsum256(acc);
  for (; i < n; i++) s += x[i] * x[i];
  return s;
}

void rms_norm_vec(const float* x, float* y, int n) {
  float ms = sum_squares(x, n) / static_cast<float>(n);
  float denom = std::sqrt(ms + RMS_EPS);
  __m256 vd = _mm256_set1_ps(denom);
  int i = 0;
  for (; i + 8 <= n; i += 8)
    _mm256_storeu_ps(y + i, _mm256_div_ps(_mm256_loadu_ps(x + i), vd));
  for (; i < n; i++) y[i] = x[i] / denom;
}

float dot_f32(const float* a, const float* b, int n) {
  int i = 0;
  __m256 acc = _mm256_setzero_ps();
  for (; i + 8 <= n; i += 8)
    acc = _mm256_fmadd_ps(_mm256_loadu_ps(a + i), _mm256_loadu_ps(b + i), acc);
  float s = hsum256(acc);
  for (; i < n; i++) s += a[i] * b[i];
  return s;
}

// clamp-to-[-128,127] in float BEFORE the nearest-even convert: identical
// results to round-then-int-clamp for every finite input (values outside
// [-128, 127] round/clamp to the boundary either way) and immune to
// int32-convert overflow sentinels.
void quantize_i8(const float* x, int n, int n_pad, float scale, int8_t* q) {
  const __m256 vs = _mm256_set1_ps(scale);
  const __m256 vlo = _mm256_set1_ps(-128.0f);
  const __m256 vhi = _mm256_set1_ps(127.0f);
  int i = 0;
  for (; i + 16 <= n; i += 16) {
    __m256 a = _mm256_div_ps(_mm256_loadu_ps(x + i), vs);
    __m256 b = _mm256_div_ps(_mm256_loadu_ps(x + i + 8), vs);
    a = _mm256_min_ps(_mm256_max_ps(a, vlo), vhi);
    b = _mm256_min_ps(_mm256_max_ps(b, vlo), vhi);
    __m256i ia = _mm256_cvtps_epi32(a);  // MXCSR default: round half to even
    __m256i ib = _mm256_cvtps_epi32(b);
    __m256i w16 = _mm256_packs_epi32(ia, ib);
    w16 = _mm256_permute4x64_epi64(w16, _MM_SHUFFLE(3, 1, 2, 0));
    __m128i w8 = _mm_packs_epi16(_mm256_castsi256_si128(w16),
                                 _mm256_extracti128_si256(w16, 1));
    _mm_storeu_si128(reinterpret_cast<__m128i*>(q + i), w8);
  }
  for (; i < n; i++) {
    float t = x[i] / scale;
    t = t < -128.0f ? -128.0f : (t > 127.0f ? 127.0f : t);
    q[i] = static_cast<int8_t>(_mm_cvtss_si32(_mm_set_ss(t)));  // nearest even
  }
  for (; i < n_pad; i++) q[i] = 0;
}

int32_t dot_i8(const int8_t* a, const int8_t* b, int n) {
  __m256i acc = _mm256_setzero_si256();
  for (int i = 0; i < n; i += 16) {
    __m256i va = _mm256_cvtepi8_epi16(
        _mm_loadu_si128(reinterpret_cast<const __m128i*>(a + i)));
    __m256i vb = _mm256_cvtepi8_epi16(
        _mm_loadu_si128(reinterpret_cast<const __m128i*>(b + i)));
    acc = _mm256_add_epi32(acc, _mm256_madd_epi16(va, vb));
  }
  return hsum256_i32(acc);
}

void qmatvec(const int8_t* w, int stride, const float* fold, int d_out,
             const int8_t* qx, float* y) {
  for (int o = 0; o < d_out; o++)
    y[o] = fold[o] * static_cast<float>(dot_i8(qx, w + size_t(o) * stride, stride));
}

void conv4_silu(const float* wt, const float* h0, const float* h1,
                const float* h2, const float* xc, float* y, int d) {
  const float* w0 = wt;
  const float* w1 = wt + d;
  const float* w2 = wt + 2 * d;
  const float* w3 = wt + 3 * d;
  // taps accumulated oldest-first, matching the reference kernel
  for (int c = 0; c < d; c++) {
    float z = w0[c] * h0[c];
    z += w1[c] * h1[c];
    z += w2[c] * h2[c];
    z += w3[c] * xc[c];
    y[c] = siluf(z);
  }
}

void kda_head_step(float* S, const float* q, const float* k, const float* v,
                   const float* g_raw, const float* dt_bias, float a_neg,
                   float beta, float* o) {
  float qn[64], kn[64], decay[64], r[64], u[64];

  // l2norm: eps 1e-6 added to the RAW sum of squares, inside sqrt
  float dq = std::sqrt(sum_squares(q, 64) + 1e-6f);
  float dk = std::sqrt(sum_squares(k, 64) + 1e-6f);
  for (int i = 0; i < 64; i++) qn[i] = q[i] / dq;
  for (int i = 0; i < 64; i++) kn[i] = k[i] / dk;

  // per-channel log-decay gate
  for (int i = 0; i < 64; i++) {
    float x = g_raw[i] + dt_bias[i];
    decay[i] = std::exp(a_neg * softplus20f(x));
  }

  // decay FIRST (per k-row), then r = S^T kn on the decayed state
  for (int j = 0; j < 64; j++) r[j] = 0.0f;
  for (int i = 0; i < 64; i++) {
    float* row = S + 64 * i;
    float d = decay[i];
    float kni = kn[i];
    for (int j = 0; j < 64; j++) {
      row[j] *= d;
      r[j] += kni * row[j];
    }
  }
  for (int j = 0; j < 64; j++) u[j] = beta * (v[j] - r[j]);
  // rank-1 delta update, then output on the UPDATED state (token sees itself)
  for (int j = 0; j < 64; j++) o[j] = 0.0f;
  for (int i = 0; i < 64; i++) {
    float* row = S + 64 * i;
    float kni = kn[i];
    float qi = 0.125f * qn[i];  // scale on the q side only
    for (int j = 0; j < 64; j++) {
      row[j] += kni * u[j];
      o[j] += qi * row[j];
    }
  }
}

void gated_rms_norm64(const float* o, const float* og, const float* w,
                      float* y) {
  float ms = sum_squares(o, 64) / 64.0f;  // eps added to the MEAN
  float rstd = 1.0f / std::sqrt(ms + 1e-5f);
  for (int j = 0; j < 64; j++) y[j] = o[j] * rstd * w[j] * sigmoid1f(og[j]);
}

void rope_apply(float* h192, const float* sin32, const float* cos32) {
  for (int h = 0; h < 3; h++) {
    float* p = h192 + h * 64;
    for (int i = 0; i < 32; i++) {
      float x0 = p[2 * i], x1 = p[2 * i + 1];
      float c = cos32[i], s = sin32[i];
      p[2 * i] = x0 * c + x1 * s;
      p[2 * i + 1] = x1 * c - x0 * s;
    }
  }
}

namespace {

// shared attention implementation; slots [0, n) of the ring are valid
// (softmax is order-independent up to fp rounding, so ring order is fine)
inline void attention_impl(const int8_t* q192, const int8_t* kring,
                           const int8_t* vring, const float* coef3,
                           const float* sv3, int n, float* out192,
                           float skip_threshold) {
  float scores[1024];
  for (int h = 0; h < 3; h++) {
    const int8_t* qh = q192 + h * 64;
    const float coef = coef3[h];
    float m = -INFINITY;
    for (int j = 0; j < n; j++) {
      float s = coef * static_cast<float>(dot_i8(qh, kring + size_t(j) * 192 + h * 64, 64));
      scores[j] = s;
      if (s > m) m = s;
    }
    __m256 acc[8];
    for (int t = 0; t < 8; t++) acc[t] = _mm256_setzero_ps();
    float denom = 0.0f;
    const float sv = sv3[h];
    const __m256 vsv = _mm256_set1_ps(sv);
    for (int j = 0; j < n; j++) {
      float d = scores[j] - m;
      if (skip_threshold > 0.0f && d < -skip_threshold) continue;
      float e = std::exp(d);
      denom += e;
      const int8_t* vh = vring + size_t(j) * 192 + h * 64;
      __m256 ve = _mm256_set1_ps(e);
      for (int t = 0; t < 8; t++) {
        __m128i b = _mm_loadl_epi64(
            reinterpret_cast<const __m128i*>(vh + t * 8));
        __m256 vf = _mm256_cvtepi32_ps(_mm256_cvtepi8_epi32(b));
        // PV in fp32 on dequantized v: e * (sv * int)
        acc[t] = _mm256_fmadd_ps(ve, _mm256_mul_ps(vsv, vf), acc[t]);
      }
    }
    __m256 vden = _mm256_set1_ps(denom);
    for (int t = 0; t < 8; t++)
      _mm256_storeu_ps(out192 + h * 64 + t * 8, _mm256_div_ps(acc[t], vden));
  }
}

}  // namespace

void attention_step_var(const int8_t* q192, const int8_t* kring,
                        const int8_t* vring, const float* coef3,
                        const float* sv3, int n, float* out192,
                        float skip_threshold) {
  assert(n >= 1 && n < 1024);
  attention_impl(q192, kring, vring, coef3, sv3, n, out192, skip_threshold);
}

void attention_step_fixed(const int8_t* q192, const int8_t* kring,
                          const int8_t* vring, const float* coef3,
                          const float* sv3, float* out192,
                          float skip_threshold) {
  attention_impl(q192, kring, vring, coef3, sv3, 1024, out192, skip_threshold);
}

void f16_to_f32(const uint16_t* h, float* out, int n) {
  int i = 0;
  for (; i + 8 <= n; i += 8) {
    __m128i v = _mm_loadu_si128(reinterpret_cast<const __m128i*>(h + i));
    _mm256_storeu_ps(out + i, _mm256_cvtph_ps(v));
  }
  for (; i < n; i++) {
    __m128i v = _mm_cvtsi32_si128(h[i]);
    out[i] = _mm_cvtss_f32(_mm_cvtph_ps(v));
  }
}

}  // namespace fx2
