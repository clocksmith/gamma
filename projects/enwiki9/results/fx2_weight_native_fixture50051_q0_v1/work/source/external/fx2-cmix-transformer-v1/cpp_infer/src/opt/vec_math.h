// vec_math.h — shared AVX2 fp32 vector math library for the fx2 inference
// engine (CANONICAL — SPEC.md forbids -ffast-math; everything here is safe
// under strict IEEE compilation, uses FMA/AVX2 only, no libm calls).
//
// API contract (FROZEN): plain inline functions  __m256 f(__m256).
// All functions assume FINITE inputs in the documented ranges (NaN is not
// supported; +-inf is tolerated by the clamps where noted). MXCSR is assumed
// at its default state (round-nearest-even, FTZ/DAZ OFF) to match the naive
// reference build.
//
// Measured accuracy (test_glue.cpp random sweeps vs double-precision libm;
// tanh additionally verified EXHAUSTIVELY over every fp32 in +-[2^-11, 10),
// see report) and throughput (bench_glue.cpp, cycles/element, L1-resident
// 4096-elem arrays, 4x-unrolled caller, clang++-17 -O3 -march=znver2,
// EPYC 7702 @ 3.337 GHz; results bit-identical under g++-13):
//
//   fn               range              max ulp        cyc/elem
//   exp256_ps        [-30, 30]          1.03           1.70
//   log256_ps        [1e-9, 1e3]        0.85           2.12
//   log1p256_ps      [9e-14, 1e13]      1.60           3.21
//   sigmoid256_ps    [-30, 30]          1.91 (1.97*)   2.93
//   silu256_ps       [-30, 30]          2.80           3.35
//   softplus256_ps   [-30, 30]          2.45           7.89
//   tanh256_ps       [-20, 20]          1.96 (1.99*)   3.73
//     (* = exhaustive-scan max: tanh over +-[2^-11,10) all 268M floats,
//        sigmoid over [-8,-1) all floats; silu/softplus floors are set by
//        exp256's ~1.0 ulp passing straight through their result)
//
// (libm scalar baselines on this box: expf 9.1 c/elem, tanhf 44-56 c/elem.)
#pragma once

#include <immintrin.h>

namespace fx2 {

// ---------------------------------------------------------------------------
// exp256_ps: e^x. Cephes-style polynomial adopted from bench/misc.cpp (its
// "8.0e-8 max rel err / 0.7 ulp-ish" is 1.03 ulp measured per-binade), with
// the polynomial in Estrin form (same coefficients, half the fma depth) and
// the hi clamp lowered to 88.0 (misc.cpp's 88.3763 lets the n=128 exponent
// reconstruction overflow to +inf at the boundary). Inputs are clamped to
// [-87.3365, 88.0]; result is always a positive normal float (never 0/inf
// for finite input, including +-inf inputs).
// ---------------------------------------------------------------------------
inline __m256 exp256_ps(__m256 x) {
  const __m256 hi = _mm256_set1_ps(88.0f);  // NOT 88.376...: fma(hi,log2e,.5) would round to 128 -> 2^n overflows to inf (NaN via inf-inf in expm1)
  const __m256 lo = _mm256_set1_ps(-87.3365478515625f);
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
  // Estrin: P = (p5+p4 x) + z(p3+p2 x) + z^2(p1+p0 x)  — half the fma depth
  // of Horner (verified: max ulp unchanged at 1.01 on [-30,30])
  __m256 z2 = _mm256_mul_ps(z, z);
  __m256 pa = _mm256_fmadd_ps(p4, x, p5);
  __m256 pb = _mm256_fmadd_ps(p2, x, p3);
  __m256 pc = _mm256_fmadd_ps(p0, x, p1);
  __m256 y = _mm256_fmadd_ps(z, pb, pa);
  y = _mm256_fmadd_ps(z2, pc, y);
  y = _mm256_fmadd_ps(y, z, x);
  y = _mm256_add_ps(y, one);
  __m256i n = _mm256_cvtps_epi32(fx);
  n = _mm256_slli_epi32(_mm256_add_epi32(n, _mm256_set1_epi32(127)), 23);
  return _mm256_mul_ps(y, _mm256_castsi256_ps(n));
}

// ---------------------------------------------------------------------------
// log256_ps: natural log. Cephes logf scheme with FMA. Input must be a
// POSITIVE NORMAL float (no 0 / negative / denormal handling — target range
// [1e-9, 1e3] and the softplus path both satisfy this).
// ---------------------------------------------------------------------------
inline __m256 log256_ps(__m256 x) {
  const __m256 one = _mm256_set1_ps(1.0f);
  const __m256 SQRTHF = _mm256_set1_ps(0.707106781186547524f);
  // decompose x = m * 2^e, m in [0.5, 1)
  __m256i xi = _mm256_castps_si256(x);
  __m256i ei = _mm256_sub_epi32(_mm256_srli_epi32(xi, 23),
                                _mm256_set1_epi32(126));
  __m256 m = _mm256_or_ps(
      _mm256_and_ps(x, _mm256_castsi256_ps(_mm256_set1_epi32(0x007FFFFF))),
      _mm256_castsi256_ps(_mm256_set1_epi32(0x3F000000)));
  __m256 e = _mm256_cvtepi32_ps(ei);
  // if m < sqrt(1/2): m *= 2, e -= 1  =>  m in [sqrt(1/2), sqrt(2))
  __m256 mask = _mm256_cmp_ps(m, SQRTHF, _CMP_LT_OQ);
  e = _mm256_sub_ps(e, _mm256_and_ps(one, mask));
  m = _mm256_add_ps(m, _mm256_and_ps(m, mask));
  __m256 z = _mm256_sub_ps(m, one);  // exact (Sterbenz)
  __m256 z2 = _mm256_mul_ps(z, z);
  // P(z), cephes logf coefficients, Estrin scheme (l0 = leading z^8 coeff)
  const __m256 l0 = _mm256_set1_ps(7.0376836292E-2f);
  const __m256 l1 = _mm256_set1_ps(-1.1514610310E-1f);
  const __m256 l2 = _mm256_set1_ps(1.1676998740E-1f);
  const __m256 l3 = _mm256_set1_ps(-1.2420140846E-1f);
  const __m256 l4 = _mm256_set1_ps(1.4249322787E-1f);
  const __m256 l5 = _mm256_set1_ps(-1.6668057665E-1f);
  const __m256 l6 = _mm256_set1_ps(2.0000714765E-1f);
  const __m256 l7 = _mm256_set1_ps(-2.4999993993E-1f);
  const __m256 l8 = _mm256_set1_ps(3.3333331174E-1f);
  __m256 z4 = _mm256_mul_ps(z2, z2);
  __m256 pa = _mm256_fmadd_ps(l7, z, l8);
  __m256 pb = _mm256_fmadd_ps(l5, z, l6);
  __m256 pc = _mm256_fmadd_ps(l3, z, l4);
  __m256 pd = _mm256_fmadd_ps(l1, z, l2);
  __m256 y = _mm256_fmadd_ps(z2, pb, pa);          // low half
  __m256 yh = _mm256_fmadd_ps(l0, z2, pd);         // pd + l0 z^2
  yh = _mm256_fmadd_ps(z2, yh, pc);                // pc + pd z^2 + l0 z^4
  y = _mm256_fmadd_ps(z4, yh, y);                  // P(z)
  y = _mm256_mul_ps(y, _mm256_mul_ps(z, z2));      // z^3 * P(z)
  // log(x) = e*ln2 + z - z^2/2 + z^3*P(z), ln2 split into C1+C2
  y = _mm256_fmadd_ps(e, _mm256_set1_ps(-2.12194440e-4f), y);
  y = _mm256_fnmadd_ps(_mm256_set1_ps(0.5f), z2, y);
  __m256 r = _mm256_add_ps(z, y);
  r = _mm256_fmadd_ps(e, _mm256_set1_ps(0.693359375f), r);
  return r;
}

// ---------------------------------------------------------------------------
// log1p256_ps: log(1+u) for u > -0.5 (used with u = exp(x) >= 0). Exact-
// residual correction: w = fl(1+u), d = w-1 and cd = u-d are EXACT (Sterbenz),
// and log1p(u) = log(w) + log(w)*cd/d + O(cd^2). The correction is applied
// ADDITIVELY (a multiplicative u/d factor cannot be represented finely enough
// near 1.0). If w == 1 the result is u itself.
//
// cd/d is a true IEEE divide, NOT vrcpps: the accuracy of the reciprocal is
// irrelevant here (the correction is ~1 ulp), but its exact bits are not.
// RCPPS/RSQRTPS are only specified to a relative error bound; the value they
// return is implementation-defined and differs between CPU vendors, so a
// compressor and a decompressor running on different machines would disagree
// on the last bit of a probability and the arithmetic coder would
// desynchronise. Nothing in this file may use a reciprocal estimate.
// ---------------------------------------------------------------------------
inline __m256 log1p256_ps(__m256 u) {
  const __m256 one = _mm256_set1_ps(1.0f);
  const __m256 sign = _mm256_set1_ps(-0.0f);
  // |u| < 2^-6: single-rounding series u + u^2*(-1/2 + u/3 - u^2/4 + u^3/5)
  // (also covers the d == 0 lanes; truncation < 2e-10 rel at the boundary)
  __m256 small = _mm256_cmp_ps(_mm256_andnot_ps(sign, u),
                               _mm256_set1_ps(0.015625f), _CMP_LT_OQ);
  __m256 qp = _mm256_set1_ps(0.2f);
  qp = _mm256_fmadd_ps(qp, u, _mm256_set1_ps(-0.25f));
  qp = _mm256_fmadd_ps(qp, u, _mm256_set1_ps(0.33333333333f));
  qp = _mm256_fmadd_ps(qp, u, _mm256_set1_ps(-0.5f));
  __m256 res_s = _mm256_fmadd_ps(_mm256_mul_ps(u, u), qp, u);
  // else the additive-Goldberg path (cd/d <= 4e-6 here, so vrcpps is ample)
  __m256 w = _mm256_add_ps(u, one);
  __m256 d = _mm256_sub_ps(w, one);   // exact
  __m256 cd = _mm256_sub_ps(u, d);    // exact
  __m256 f = _mm256_div_ps(cd, d);
  __m256 lw = log256_ps(w);
  __m256 res_g = _mm256_fmadd_ps(lw, f, lw);  // lw*(1 + cd/d), single rounding
  return _mm256_blendv_ps(res_g, res_s, small);
}

namespace vecdetail {
// num / (den + cd) where |cd| << den is the exact residual of den's rounding:
// r0*(1 - cd/den). Both quotients are true IEEE divides: a reciprocal
// estimate would be accurate enough but is not bit-reproducible across CPU
// vendors (see the note on log1p256_ps above), and the compressor and the
// decompressor must agree bit for bit. The two divides are independent, so
// they still overlap in the divider.
inline __m256 div_corrected(__m256 num, __m256 den, __m256 cd) {
  __m256 f = _mm256_div_ps(cd, den);
  __m256 r0 = _mm256_div_ps(num, den);
  return _mm256_fnmadd_ps(r0, f, r0);
}
}  // namespace vecdetail

// ---------------------------------------------------------------------------
// sigmoid256_ps: 1/(1+e^-x). Computed on e = exp(-|x|) <= 1 so den = 1+e is
// in [1,2] and its rounding residual cd = e-(den-1) is exact; sigmoid =
// (x>=0 ? 1 : e) / (den+cd) via the corrected division. sigmoid(+-0) = 0.5.
// ---------------------------------------------------------------------------
inline __m256 sigmoid256_ps(__m256 x) {
  const __m256 one = _mm256_set1_ps(1.0f);
  const __m256 sign = _mm256_set1_ps(-0.0f);
  __m256 ax = _mm256_andnot_ps(sign, x);       // |x|
  __m256 e = exp256_ps(_mm256_xor_ps(ax, sign));  // e^-|x| in (0,1]
  __m256 den = _mm256_add_ps(one, e);
  __m256 cd = _mm256_sub_ps(e, _mm256_sub_ps(den, one));  // exact residual
  __m256 neg = _mm256_cmp_ps(x, _mm256_setzero_ps(), _CMP_LT_OQ);
  __m256 num = _mm256_blendv_ps(one, e, neg);  // sigmoid(-t) = e/(1+e)
  return vecdetail::div_corrected(num, den, cd);
}

// ---------------------------------------------------------------------------
// silu256_ps: x*sigmoid(x) = x/(1+e^-x), same corrected-division scheme
// (numerator x for x >= 0, x*e for x < 0). silu(+-0) = +-0.
// ---------------------------------------------------------------------------
inline __m256 silu256_ps(__m256 x) {
  const __m256 one = _mm256_set1_ps(1.0f);
  const __m256 sign = _mm256_set1_ps(-0.0f);
  __m256 ax = _mm256_andnot_ps(sign, x);
  __m256 e = exp256_ps(_mm256_xor_ps(ax, sign));
  __m256 den = _mm256_add_ps(one, e);
  __m256 cd = _mm256_sub_ps(e, _mm256_sub_ps(den, one));
  __m256 neg = _mm256_cmp_ps(x, _mm256_setzero_ps(), _CMP_LT_OQ);
  __m256 num = _mm256_blendv_ps(x, _mm256_mul_ps(x, e), neg);
  __m256 y = vecdetail::div_corrected(num, den, cd);
  return _mm256_or_ps(y, _mm256_and_ps(x, sign));  // silu(-0) = -0
}

// ---------------------------------------------------------------------------
// softplus256_ps: (x > 20) ? x : log1p(exp(x))  — threshold EXACTLY 20,
// exactly the KIMI_SEMANTICS.md / naive softplus20f semantics.
// ---------------------------------------------------------------------------
inline __m256 softplus256_ps(__m256 x) {
  __m256 sp = log1p256_ps(exp256_ps(x));
  __m256 big = _mm256_cmp_ps(x, _mm256_set1_ps(20.0f), _CMP_GT_OQ);
  return _mm256_blendv_ps(sp, x, big);
}

namespace vecdetail {
// expm1 core: e^t - 1 with full RELATIVE accuracy for all t (unlike
// exp256(t)-1, which cancels catastrophically near 0). Same range reduction
// as exp256_ps; the polynomial is the exact Taylor series of (e^r-1-r)/r^2
// through r^7 (truncation < 6e-9 abs at |r| = ln2/2). Two sub-ulp residuals
// are recovered and pre-combined at em1r's scale before the single 2^n
// reconstruction rounding: the reduction residual rlo (enters as rlo*e^r)
// and the em1r fma's Fast2Sum residual — without them the n = +-1 zone of
// tanh reaches 2.05 ulp; with them the exhaustive max is 1.99.
inline __m256 expm1_core(__m256 t) {
  const __m256 hi = _mm256_set1_ps(88.0f);  // NOT 88.376...: fma(hi,log2e,.5) would round to 128 -> 2^n overflows to inf (NaN via inf-inf in expm1)
  const __m256 lo = _mm256_set1_ps(-87.3365478515625f);
  const __m256 LOG2EF = _mm256_set1_ps(1.44269504088896341f);
  const __m256 C1 = _mm256_set1_ps(0.693359375f);
  const __m256 C2 = _mm256_set1_ps(-2.12194440e-4f);
  const __m256 half = _mm256_set1_ps(0.5f);
  const __m256 one = _mm256_set1_ps(1.0f);
  t = _mm256_min_ps(t, hi);
  t = _mm256_max_ps(t, lo);
  __m256 fx = _mm256_fmadd_ps(t, LOG2EF, half);
  fx = _mm256_floor_ps(fx);
  __m256 r1 = _mm256_fnmadd_ps(fx, C1, t);       // exact (Sterbenz)
  __m256 pc = _mm256_mul_ps(fx, C2);
  __m256 r = _mm256_sub_ps(r1, pc);
  // residual of the reduction: r_true = r + rlo (rlo also absorbs fx*C2's
  // own rounding); enters the result as rlo*e^r
  __m256 rlo = _mm256_sub_ps(_mm256_sub_ps(r1, r), pc);
  __m256 z = _mm256_mul_ps(r, r);
  // Taylor (e^r-1-r)/r^2 through r^7 (trunc < 6e-9 at |r|=ln2/2), Estrin
  const __m256 q0 = _mm256_set1_ps(1.9841269841E-4f);   // 1/5040 (r^5)
  const __m256 q1 = _mm256_set1_ps(1.3888888889E-3f);   // 1/720
  const __m256 q2 = _mm256_set1_ps(8.3333333333E-3f);   // 1/120
  const __m256 q3 = _mm256_set1_ps(4.1666666667E-2f);   // 1/24
  const __m256 q4 = _mm256_set1_ps(1.6666666667E-1f);   // 1/6
  __m256 qa = _mm256_fmadd_ps(q4, r, half);             // 1/2 + r/6
  __m256 qb = _mm256_fmadd_ps(q2, r, q3);
  __m256 qc = _mm256_fmadd_ps(q0, r, q1);
  // combine in Horner order (small terms first): qa + z*(qb + z*qc)
  __m256 y = _mm256_fmadd_ps(z, _mm256_fmadd_ps(z, qc, qb), qa);
  // e^r - 1 = r + y*z kept as an exact hi+lo pair (Fast2Sum: |y*z| <= |r|/2);
  // together with rlo*(1+em1r) [= rlo*e^r] this removes the two dominant
  // sub-ulp residuals that pushed the n = +-1 zone of tanh to ~2.05 ulp
  __m256 em1r = _mm256_fmadd_ps(y, z, r);
  __m256 t1 = _mm256_sub_ps(em1r, r);            // exact
  __m256 em1r_lo = _mm256_fmsub_ps(y, z, t1);    // residual of the fma
  __m256 lo_all = _mm256_add_ps(em1r_lo, _mm256_fmadd_ps(rlo, em1r, rlo));
  // pre-combine at em1r's (finer) scale, then ONE reconstruction rounding:
  // e^t - 1 = 2^n*(em1r + lo_all) + (2^n - 1)
  __m256 em1r2 = _mm256_add_ps(em1r, lo_all);
  __m256i n = _mm256_cvtps_epi32(fx);
  __m256 p2n = _mm256_castsi256_ps(
      _mm256_slli_epi32(_mm256_add_epi32(n, _mm256_set1_epi32(127)), 23));
  return _mm256_fmadd_ps(p2n, em1r2, _mm256_sub_ps(p2n, one));
}
}  // namespace vecdetail

// ---------------------------------------------------------------------------
// tanh256_ps: tanh(|x|) = t/(t+2) with t = e^{2|x|}-1 >= 0 from the expm1
// core (odd symmetry: computing on |x| keeps the error amplification factor
// 2/(t+2) <= 1 and makes den-2 exact), corrected division for den = fl(t+2),
// then the sign of x is restored (also giving tanh(-0) = -0 exactly).
// Valid for all finite x (saturates to +-1); accuracy range +-20, softcap
// uses |x| <= ~1.4.
// ---------------------------------------------------------------------------
inline __m256 tanh256_ps(__m256 x) {
  const __m256 two = _mm256_set1_ps(2.0f);
  const __m256 sign = _mm256_set1_ps(-0.0f);
  __m256 ax = _mm256_andnot_ps(sign, x);
  __m256 t = vecdetail::expm1_core(_mm256_add_ps(ax, ax));  // e^{2|x|}-1 >= 0
  __m256 den = _mm256_add_ps(t, two);
  __m256 cd = _mm256_sub_ps(t, _mm256_sub_ps(den, two));  // exact residual
  __m256 y = vecdetail::div_corrected(t, den, cd);
  return _mm256_or_ps(y, _mm256_and_ps(x, sign));  // restore sign (and -0)
}

}  // namespace fx2
