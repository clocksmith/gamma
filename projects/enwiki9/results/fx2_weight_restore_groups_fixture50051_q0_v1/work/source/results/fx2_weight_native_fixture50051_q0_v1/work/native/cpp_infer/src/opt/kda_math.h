// KDA-specific vector math on top of the canonical shared library
// (vec_math.h): naive-order reductions and a full-range exp for the
// per-channel decay.
//
// Accuracy is validated in test_kda (1e7 random points per real input range;
// see the tables it prints):
//   exp_full8  : bit-identical to fx2::exp256_ps for every normal result
//                (same constants/poly; the 2^n scale is applied as two exact
//                power-of-two multiplies), but keeps going below -87.34:
//                results underflow gracefully through subnormals to 0 at
//                x <= ~-104, like libm expf. Needed by decay = exp(a_neg*sp)
//                whose argument reaches -96.5 on the real g_raw range
//                (exp256_ps would clamp; absolute error would still be
//                < 1.2e-38 but the subnormal tail costs nothing).
//   sum_squares64 / hsum256v : bit-identical reduction order to
//                src/kernels.cpp sum_squares/hsum256 (one accumulator, 8
//                sequential fmas, the same shuffle tree), so l2norm and
//                gated-norm statistics match the naive path bit-for-bit.
#pragma once

#include <immintrin.h>

#include "vec_math.h"

namespace fx2 {
namespace opt {

// ---------- exact copy of src/kernels.cpp hsum256 reduction order ----------
static inline float hsum256v(__m256 v) {
  __m128 lo = _mm256_castps256_ps128(v);
  __m128 hi = _mm256_extractf128_ps(v, 1);
  lo = _mm_add_ps(lo, hi);
  lo = _mm_add_ps(lo, _mm_movehl_ps(lo, lo));
  lo = _mm_add_ss(lo, _mm_movehdup_ps(lo));
  return _mm_cvtss_f32(lo);
}

// sum of squares of 64 floats, bit-identical to src/kernels.cpp
// sum_squares(x, 64).
static inline float sum_squares64(const float* x) {
  __m256 acc = _mm256_setzero_ps();
  for (int i = 0; i < 64; i += 8) {
    __m256 v = _mm256_loadu_ps(x + i);
    acc = _mm256_fmadd_ps(v, v, acc);
  }
  return hsum256v(acc);
}

// Full-range exp: exp256_ps's reduction + Estrin polynomial (mirrors the
// final canonical vec_math.h body) with the 2^n scale split into two exact
// power-of-two factors (n = n1+n2), extending the domain to [-110, 88.0]
// with graceful subnormal underflow (exp(-110) -> exactly 0, like libm expf
// which underflows below ~-103.97). Bit-identical to fx2::exp256_ps
// wherever the result is a normal float (the power-of-two multiplies are
// exact there).
static inline __m256 exp_full8(__m256 x) {
  const __m256 hi = _mm256_set1_ps(88.0f);
  const __m256 lo = _mm256_set1_ps(-110.0f);
  const __m256 LOG2EF = _mm256_set1_ps(1.44269504088896341f);
  const __m256 C1 = _mm256_set1_ps(0.693359375f);
  const __m256 C2 = _mm256_set1_ps(-2.12194440e-4f);
  const __m256 half = _mm256_set1_ps(0.5f);
  const __m256 one = _mm256_set1_ps(1.0f);
  const __m256 p0 = _mm256_set1_ps(1.9875691500E-4f);
  const __m256 p1 = _mm256_set1_ps(1.3981999507E-3f);
  const __m256 p2 = _mm256_set1_ps(8.3334519073E-3f);
  const __m256 p3 = _mm256_set1_ps(4.1665795894E-2f);
  const __m256 p4 = _mm256_set1_ps(1.6666665459E-1f);
  const __m256 p5 = _mm256_set1_ps(5.0000001201E-1f);
  x = _mm256_min_ps(x, hi);
  x = _mm256_max_ps(x, lo);
  __m256 fx = _mm256_fmadd_ps(x, LOG2EF, half);
  fx = _mm256_floor_ps(fx);
  x = _mm256_fnmadd_ps(fx, C1, x);
  x = _mm256_fnmadd_ps(fx, C2, x);
  __m256 z = _mm256_mul_ps(x, x);
  __m256 z2 = _mm256_mul_ps(z, z);
  __m256 pa = _mm256_fmadd_ps(p4, x, p5);
  __m256 pb = _mm256_fmadd_ps(p2, x, p3);
  __m256 pc = _mm256_fmadd_ps(p0, x, p1);
  __m256 y = _mm256_fmadd_ps(z, pb, pa);
  y = _mm256_fmadd_ps(z2, pc, y);
  y = _mm256_fmadd_ps(y, z, x);
  y = _mm256_add_ps(y, one);
  __m256i n = _mm256_cvtps_epi32(fx);
  __m256i n1 = _mm256_srai_epi32(n, 1);  // floor(n/2)
  __m256i n2 = _mm256_sub_epi32(n, n1);
  const __m256i bias = _mm256_set1_epi32(127);
  __m256 s1 =
      _mm256_castsi256_ps(_mm256_slli_epi32(_mm256_add_epi32(n1, bias), 23));
  __m256 s2 =
      _mm256_castsi256_ps(_mm256_slli_epi32(_mm256_add_epi32(n2, bias), 23));
  return _mm256_mul_ps(_mm256_mul_ps(y, s1), s2);
}

}  // namespace opt
}  // namespace fx2
