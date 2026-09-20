// Optimized vanilla attention kernels — see attn.h for the layout/numerics
// contract. Hot structure per head:
//   1. q int8 -> int16 pair table (8 vector ops).
//   2. QK scan over the K blocks in slot/memory order: 32 positions per
//      iteration, 4 int32 accumulators, vpbroadcastd(q pair) x
//      vpmaddwd(k pair row) -> exact int32 dots vertically; scores =
//      cvtepi32_ps * coef stored to a scratch buffer with a fused vector max.
//      prefetcht0 ~2KB ahead (MACHINE.md section 2).
//   3. exp pass over 8-score groups: d = s - max; kept mask = d >= -thr;
//      whole groups with no kept lane are skipped BEFORE any exp math;
//      exp256_ps on kept groups, masked into the denominator; kept group
//      ids+masks recorded for PV.
//   4. PV over kept rows only: int8 V row -> vpmovsxbd + vcvtdq2ps + fmadd
//      into 8 fp32 accumulators; (sv/den) folded into one final multiply.
#include "attn.h"

#include <immintrin.h>

#include <cmath>
#include <cstring>

#include "vec_math.h"

namespace fx2 {
namespace opt {

// phase tick counters (rdtsc ticks), only accumulated in -DATTN_PROFILE
// builds: [0]=qk, [1]=exp, [2]=pv, [3]=whole-step calls
uint64_t g_attn_prof[4];

namespace {

#ifdef ATTN_PROFILE
inline uint64_t prof_rd() {
  unsigned lo, hi;
  asm volatile("lfence\n\trdtsc" : "=a"(lo), "=d"(hi)::"memory");
  return (static_cast<uint64_t>(hi) << 32) | lo;
}
#define PROF_T(v) const uint64_t v = prof_rd()
#define PROF_ADD(i, a, b) g_attn_prof[i] += (b) - (a)
#else
#define PROF_T(v) (void)0
#define PROF_ADD(i, a, b) (void)0
#endif

// scratch (single-threaded; see attn.h)
alignas(64) float g_sc[ATTN_WIN + 32];  // scores, padded with -inf
alignas(64) float g_eb[ATTN_WIN + 32];  // exp values (+0.0 = excluded lane)

inline float hsum8(__m256 v) {
  __m128 lo = _mm_add_ps(_mm256_castps256_ps128(v), _mm256_extractf128_ps(v, 1));
  lo = _mm_add_ps(lo, _mm_movehl_ps(lo, lo));
  lo = _mm_add_ss(lo, _mm_movehdup_ps(lo));
  return _mm_cvtss_f32(lo);
}

inline float hmax8(__m256 v) {
  __m128 lo = _mm_max_ps(_mm256_castps256_ps128(v), _mm256_extractf128_ps(v, 1));
  lo = _mm_max_ps(lo, _mm_movehl_ps(lo, lo));
  lo = _mm_max_ss(lo, _mm_movehdup_ps(lo));
  return _mm_cvtss_f32(lo);
}

// ---------------------------------------------------------------------------
// K row loading: one pair-row half (8 positions x int16 pair) per ymm.
// int8 layout: vpmovsxbw with a memory operand. (An in-lane
// vpcmpgtb+vpunpck variant with a compensating permuted insert was tried and
// MEASURED SLOWER: the extra live temporaries caused register spills in the
// 2x-unrolled scan and the insert path slowed 292 -> 480 cyc; reverted.)
// ---------------------------------------------------------------------------
struct KH {
  __m256i lo, hi;  // 2 x (8 positions x int16 pair)
};
inline KH ldk2(const int8_t* row) {
  return {_mm256_cvtepi8_epi16(
              _mm_load_si128(reinterpret_cast<const __m128i*>(row))),
          _mm256_cvtepi8_epi16(
              _mm_load_si128(reinterpret_cast<const __m128i*>(row + 16)))};
}
inline KH ldk2(const int16_t* row) {
  return {_mm256_load_si256(reinterpret_cast<const __m256i*>(row)),
          _mm256_load_si256(reinterpret_cast<const __m256i*>(row + 16))};
}

// ---------------------------------------------------------------------------
// QK scan: scores for slots [0, n) of head kh, fused running max over the
// full 32-position blocks; tail (var kernel only) computed per 16-block, then
// the buffer is padded to a 32 boundary with -inf and the tail is max-folded.
// FIXED specializes every loop count to the 1024-slot shape.
// ---------------------------------------------------------------------------
template <bool FIXED, typename T>
inline float qk_scan(const T* kh, const int32_t* qp32, float coef, int n,
                     float* sc) {
  const __m256 vcoef = _mm256_set1_ps(coef);
  __m256 vmax = _mm256_set1_ps(-INFINITY);
  const int nDB = FIXED ? (ATTN_WIN / 32) : (n >> 5);
  const T* kb = kh;
  float* scp = sc;
  for (int bb = 0; bb < nDB; bb++, kb += 2048, scp += 32) {
    __m256i a0 = _mm256_setzero_si256(), a1 = a0, a2 = a0, a3 = a0;
    for (int i = 0; i < 32; i += 2) {
      // prefetch the next double block (~2KB ahead), covering all its lines
      _mm_prefetch(reinterpret_cast<const char*>(kb + 2048 + i * 64),
                   _MM_HINT_T0);
      _mm_prefetch(reinterpret_cast<const char*>(kb + 2048 + i * 64 + 32),
                   _MM_HINT_T0);
      const __m256i qb = _mm256_set1_epi32(qp32[i]);
      const KH h0 = ldk2(kb + i * 32);
      const KH h1 = ldk2(kb + 1024 + i * 32);
      a0 = _mm256_add_epi32(a0, _mm256_madd_epi16(qb, h0.lo));
      a1 = _mm256_add_epi32(a1, _mm256_madd_epi16(qb, h0.hi));
      a2 = _mm256_add_epi32(a2, _mm256_madd_epi16(qb, h1.lo));
      a3 = _mm256_add_epi32(a3, _mm256_madd_epi16(qb, h1.hi));
      const __m256i qc = _mm256_set1_epi32(qp32[i + 1]);
      const KH h2 = ldk2(kb + (i + 1) * 32);
      const KH h3 = ldk2(kb + 1024 + (i + 1) * 32);
      a0 = _mm256_add_epi32(a0, _mm256_madd_epi16(qc, h2.lo));
      a1 = _mm256_add_epi32(a1, _mm256_madd_epi16(qc, h2.hi));
      a2 = _mm256_add_epi32(a2, _mm256_madd_epi16(qc, h3.lo));
      a3 = _mm256_add_epi32(a3, _mm256_madd_epi16(qc, h3.hi));
    }
    const __m256 s0 = _mm256_mul_ps(_mm256_cvtepi32_ps(a0), vcoef);
    const __m256 s1 = _mm256_mul_ps(_mm256_cvtepi32_ps(a1), vcoef);
    const __m256 s2 = _mm256_mul_ps(_mm256_cvtepi32_ps(a2), vcoef);
    const __m256 s3 = _mm256_mul_ps(_mm256_cvtepi32_ps(a3), vcoef);
    _mm256_store_ps(scp + 0, s0);
    _mm256_store_ps(scp + 8, s1);
    _mm256_store_ps(scp + 16, s2);
    _mm256_store_ps(scp + 24, s3);
    vmax = _mm256_max_ps(vmax, _mm256_max_ps(_mm256_max_ps(s0, s1),
                                             _mm256_max_ps(s2, s3)));
  }
  if (!FIXED) {
    const int rem = n - (nDB << 5);
    if (rem) {
      const int nblk = (rem + 15) >> 4;  // 1 or 2 single 16-blocks
      for (int b = 0; b < nblk; b++) {
        const T* k1 = kb + static_cast<size_t>(b) * 1024;
        __m256i a0 = _mm256_setzero_si256(), a1 = a0;
        for (int i = 0; i < 32; i++) {
          const __m256i qb = _mm256_set1_epi32(qp32[i]);
          const KH h = ldk2(k1 + i * 32);
          a0 = _mm256_add_epi32(a0, _mm256_madd_epi16(qb, h.lo));
          a1 = _mm256_add_epi32(a1, _mm256_madd_epi16(qb, h.hi));
        }
        _mm256_store_ps(scp + b * 16,
                        _mm256_mul_ps(_mm256_cvtepi32_ps(a0), vcoef));
        _mm256_store_ps(scp + b * 16 + 8,
                        _mm256_mul_ps(_mm256_cvtepi32_ps(a1), vcoef));
      }
      // pad [n, next 32 boundary) with -inf, then fold the tail into the max
      const int pad_end = (n + 31) & ~31;
      for (int j = n; j < pad_end; j++) sc[j] = -INFINITY;
      for (int j = nDB << 5; j < pad_end; j += 8)
        vmax = _mm256_max_ps(vmax, _mm256_load_ps(sc + j));
    }
  }
  return hmax8(vmax);
}

// ---------------------------------------------------------------------------
// exp pass: branchless dense sweep. e = exp256(d) & (d >= -thr) is stored for
// EVERY group; masked-out lanes become +0.0f, and exp256 never returns 0 for
// a finite input, so eb[j] == 0 <=> position j is excluded — that IS the kept
// set, so no list needs building here (the sparse PV path reconstructs group
// masks from eb). The kept predicate runs on exactly the naive kernel's
// d = score - max values -> identical kept set. unroll 4: exp256's ~35-cycle
// dependency chain needs ~4 groups in flight to reach the 2 fp-ops/cycle
// throughput ceiling. noinline: keeps the exp256 constants from colliding
// with other phases' registers (inlining caused spill storms).
// ---------------------------------------------------------------------------
template <bool FIXED>
__attribute__((noinline)) float exp_pass(const float* sc, int n, float m,
                                         float thr, float* eb, int& kept_out) {
  const __m256 vm = _mm256_set1_ps(m);
  const __m256 vthr = _mm256_set1_ps(-thr);
  __m256 vden0 = _mm256_setzero_ps(), vden1 = _mm256_setzero_ps();
  // AND of all kept-masks over the FULL groups; all-ones at the end
  // <=> every full-group lane kept (the dominant case: at the SPEC threshold
  // nothing is ever excluded on real data) -> kept = n with no per-group
  // scalar popcount work in the hot loop.
  __m256 vall = _mm256_castsi256_ps(_mm256_set1_epi32(-1));
  const int G = FIXED ? (ATTN_WIN / 8) : ((n + 7) >> 3);
  const int Gfull = FIXED ? (ATTN_WIN / 8) : (n >> 3);  // full 8-lane groups
  int g = 0;
  for (; g + 4 <= Gfull; g += 4) {
    const __m256 d0 = _mm256_sub_ps(_mm256_load_ps(sc + 8 * g), vm);
    const __m256 d1 = _mm256_sub_ps(_mm256_load_ps(sc + 8 * g + 8), vm);
    const __m256 d2 = _mm256_sub_ps(_mm256_load_ps(sc + 8 * g + 16), vm);
    const __m256 d3 = _mm256_sub_ps(_mm256_load_ps(sc + 8 * g + 24), vm);
    const __m256 k0 = _mm256_cmp_ps(d0, vthr, _CMP_GE_OQ);
    const __m256 k1 = _mm256_cmp_ps(d1, vthr, _CMP_GE_OQ);
    const __m256 k2 = _mm256_cmp_ps(d2, vthr, _CMP_GE_OQ);
    const __m256 k3 = _mm256_cmp_ps(d3, vthr, _CMP_GE_OQ);
    const __m256 e0 = _mm256_and_ps(exp256_ps(d0), k0);
    const __m256 e1 = _mm256_and_ps(exp256_ps(d1), k1);
    const __m256 e2 = _mm256_and_ps(exp256_ps(d2), k2);
    const __m256 e3 = _mm256_and_ps(exp256_ps(d3), k3);
    _mm256_store_ps(eb + 8 * g, e0);
    _mm256_store_ps(eb + 8 * g + 8, e1);
    _mm256_store_ps(eb + 8 * g + 16, e2);
    _mm256_store_ps(eb + 8 * g + 24, e3);
    vden0 = _mm256_add_ps(vden0, _mm256_add_ps(e0, e1));
    vden1 = _mm256_add_ps(vden1, _mm256_add_ps(e2, e3));
    vall = _mm256_and_ps(vall, _mm256_and_ps(_mm256_and_ps(k0, k1),
                                             _mm256_and_ps(k2, k3)));
  }
  for (; g < G; g++) {
    const __m256 d = _mm256_sub_ps(_mm256_load_ps(sc + 8 * g), vm);
    const __m256 k = _mm256_cmp_ps(d, vthr, _CMP_GE_OQ);
    const __m256 e = _mm256_and_ps(exp256_ps(d), k);
    _mm256_store_ps(eb + 8 * g, e);
    vden0 = _mm256_add_ps(vden0, e);
    if (g < Gfull) vall = _mm256_and_ps(vall, k);
  }
  if (_mm256_movemask_ps(vall) == 0xFF) {
    // all full groups fully kept; count the <=7 tail lanes only
    int kept = Gfull * 8;
    for (int j = Gfull * 8; j < n; j++) kept += (eb[j] != 0.0f);
    kept_out = kept;
  } else {  // genuinely pruning threshold: recount from eb (e==0 <=> excluded)
    const __m256 vz = _mm256_setzero_ps();
    __m256i vc = _mm256_setzero_si256();
    for (int gg = 0; gg < G; gg++)  // lanes >= n hold e == 0 -> not counted
      vc = _mm256_sub_epi32(
          vc, _mm256_castps_si256(
                  _mm256_cmp_ps(_mm256_load_ps(eb + 8 * gg), vz, _CMP_NEQ_OQ)));
    __m128i lo = _mm_add_epi32(_mm256_castsi256_si128(vc),
                               _mm256_extracti128_si256(vc, 1));
    lo = _mm_add_epi32(lo, _mm_shuffle_epi32(lo, _MM_SHUFFLE(1, 0, 3, 2)));
    lo = _mm_add_epi32(lo, _mm_shuffle_epi32(lo, _MM_SHUFFLE(2, 3, 0, 1)));
    kept_out = _mm_cvtsi128_si32(lo);
  }
  return hsum8(_mm256_add_ps(vden0, vden1));
}

// ---------------------------------------------------------------------------
// PV: accumulate e_j * v_row(j) into 8 fp32 accumulators, final multiply by
// rfac = sv/den. Two paths:
//  * dense (kept >= ~3/4 of n, i.e. always at the SPEC threshold 21 on real
//    data): branchless sweep over ALL rows [0, n) — excluded rows have
//    e == +0.0 and fmadd(0, v, acc) == acc bit-exactly, so no masking is
//    needed; V streams sequentially (prefetched). The int8 loop is inline
//    asm: clang rotates the accumulators through registers (fmadd213 forms)
//    and spills one per iteration; pinning accs in ymm0-7 with fmadd231
//    keeps the loop at its pipe floor. Bitwise-identical op order.
//  * sparse (a genuinely pruning threshold): group masks reconstructed from
//    eb (e != 0 <=> kept), V rows of skipped positions are never touched.
// ---------------------------------------------------------------------------
inline void pv_row(const int8_t* vrow, __m256 ve, __m256* acc) {
  for (int t = 0; t < 8; t++) {
    const __m256i vi = _mm256_cvtepi8_epi32(
        _mm_loadl_epi64(reinterpret_cast<const __m128i*>(vrow + t * 8)));
    acc[t] = _mm256_fmadd_ps(ve, _mm256_cvtepi32_ps(vi), acc[t]);
  }
}
inline void pv_row(const float* vrow, __m256 ve, __m256* acc) {
  for (int t = 0; t < 8; t++)
    acc[t] = _mm256_fmadd_ps(ve, _mm256_load_ps(vrow + t * 8), acc[t]);
}

// dense int8 sweep, accumulators pinned in ymm0-7 (clang's version rotated
// them through fmadd213 destinations and spilled one per iteration), 2 rows
// per loop iteration with alternating temporaries. An in-lane
// vpcmpgt/vpunpck variant was tried and measured slower (front-end bound at
// 41 uops/row); the memory-operand vpmovsxbd triple is the sweet spot:
// ~8 cvtdq2ps (1/cyc) + ~8 lane-crossing unpacks per row are the pipe floor.
#define PV_ROW(OFF, E, T0, T1)                              \
  "vpmovsxbd " #OFF "+0(%[v]), %%ymm" #T0 "\n\t"            \
  "vcvtdq2ps %%ymm" #T0 ", %%ymm" #T0 "\n\t"                \
  "vfmadd231ps %%ymm" #T0 ", %%ymm" #E ", %%ymm0\n\t"       \
  "vpmovsxbd " #OFF "+8(%[v]), %%ymm" #T1 "\n\t"            \
  "vcvtdq2ps %%ymm" #T1 ", %%ymm" #T1 "\n\t"                \
  "vfmadd231ps %%ymm" #T1 ", %%ymm" #E ", %%ymm1\n\t"       \
  "vpmovsxbd " #OFF "+16(%[v]), %%ymm" #T0 "\n\t"           \
  "vcvtdq2ps %%ymm" #T0 ", %%ymm" #T0 "\n\t"                \
  "vfmadd231ps %%ymm" #T0 ", %%ymm" #E ", %%ymm2\n\t"       \
  "vpmovsxbd " #OFF "+24(%[v]), %%ymm" #T1 "\n\t"           \
  "vcvtdq2ps %%ymm" #T1 ", %%ymm" #T1 "\n\t"                \
  "vfmadd231ps %%ymm" #T1 ", %%ymm" #E ", %%ymm3\n\t"       \
  "vpmovsxbd " #OFF "+32(%[v]), %%ymm" #T0 "\n\t"           \
  "vcvtdq2ps %%ymm" #T0 ", %%ymm" #T0 "\n\t"                \
  "vfmadd231ps %%ymm" #T0 ", %%ymm" #E ", %%ymm4\n\t"       \
  "vpmovsxbd " #OFF "+40(%[v]), %%ymm" #T1 "\n\t"           \
  "vcvtdq2ps %%ymm" #T1 ", %%ymm" #T1 "\n\t"                \
  "vfmadd231ps %%ymm" #T1 ", %%ymm" #E ", %%ymm5\n\t"       \
  "vpmovsxbd " #OFF "+48(%[v]), %%ymm" #T0 "\n\t"           \
  "vcvtdq2ps %%ymm" #T0 ", %%ymm" #T0 "\n\t"                \
  "vfmadd231ps %%ymm" #T0 ", %%ymm" #E ", %%ymm6\n\t"       \
  "vpmovsxbd " #OFF "+56(%[v]), %%ymm" #T1 "\n\t"           \
  "vcvtdq2ps %%ymm" #T1 ", %%ymm" #T1 "\n\t"                \
  "vfmadd231ps %%ymm" #T1 ", %%ymm" #E ", %%ymm7\n\t"

__attribute__((noinline)) void pv_dense_i8(const int8_t* v, const float* eb,
                                           int n, float rfac, float* out64) {
  int n2 = n >> 1;
  const int odd = n & 1;
  asm volatile(
      "vxorps %%xmm0,%%xmm0,%%xmm0\n\t"
      "vxorps %%xmm1,%%xmm1,%%xmm1\n\t"
      "vxorps %%xmm2,%%xmm2,%%xmm2\n\t"
      "vxorps %%xmm3,%%xmm3,%%xmm3\n\t"
      "vxorps %%xmm4,%%xmm4,%%xmm4\n\t"
      "vxorps %%xmm5,%%xmm5,%%xmm5\n\t"
      "vxorps %%xmm6,%%xmm6,%%xmm6\n\t"
      "vxorps %%xmm7,%%xmm7,%%xmm7\n\t"
      "testl %[n2], %[n2]\n\t"
      "jz 2f\n\t"
      ".p2align 4\n\t"
      "1:\n\t"
      "vbroadcastss (%[eb]), %%ymm12\n\t"
      "vbroadcastss 4(%[eb]), %%ymm13\n\t"
      "prefetcht0 1024(%[v])\n\t"
      "prefetcht0 1088(%[v])\n\t"
      PV_ROW(0, 12, 8, 9)
      PV_ROW(64, 13, 10, 11)
      "addq $128, %[v]\n\t"
      "addq $8, %[eb]\n\t"
      "decl %[n2]\n\t"
      "jnz 1b\n\t"
      "2:\n\t"
      "testl %[odd], %[odd]\n\t"
      "jz 3f\n\t"
      "vbroadcastss (%[eb]), %%ymm12\n\t"
      PV_ROW(0, 12, 8, 9)
      "3:\n\t"
      "vbroadcastss %[rf], %%ymm13\n\t"
      "vmulps %%ymm13, %%ymm0, %%ymm0\n\t"
      "vmulps %%ymm13, %%ymm1, %%ymm1\n\t"
      "vmulps %%ymm13, %%ymm2, %%ymm2\n\t"
      "vmulps %%ymm13, %%ymm3, %%ymm3\n\t"
      "vmulps %%ymm13, %%ymm4, %%ymm4\n\t"
      "vmulps %%ymm13, %%ymm5, %%ymm5\n\t"
      "vmulps %%ymm13, %%ymm6, %%ymm6\n\t"
      "vmulps %%ymm13, %%ymm7, %%ymm7\n\t"
      "vmovaps %%ymm0, (%[out])\n\t"
      "vmovaps %%ymm1, 32(%[out])\n\t"
      "vmovaps %%ymm2, 64(%[out])\n\t"
      "vmovaps %%ymm3, 96(%[out])\n\t"
      "vmovaps %%ymm4, 128(%[out])\n\t"
      "vmovaps %%ymm5, 160(%[out])\n\t"
      "vmovaps %%ymm6, 192(%[out])\n\t"
      "vmovaps %%ymm7, 224(%[out])\n\t"
      : [v] "+r"(v), [eb] "+r"(eb), [n2] "+r"(n2)
      : [rf] "x"(rfac), [out] "r"(out64), [odd] "r"(odd)
      : "ymm0", "ymm1", "ymm2", "ymm3", "ymm4", "ymm5", "ymm6", "ymm7",
        "ymm8", "ymm9", "ymm10", "ymm11", "ymm12", "ymm13", "cc", "memory");
}

// dense fp32-mirror sweep (measurement variant)
__attribute__((noinline)) void pv_dense_f32(const float* v, const float* eb,
                                            int n, float rfac, float* out64) {
  __m256 a0 = _mm256_setzero_ps(), a1 = a0, a2 = a0, a3 = a0, a4 = a0,
         a5 = a0, a6 = a0, a7 = a0;
  for (int j = 0; j < n; j++) {
    const float* r = v + size_t(j) * ATTN_DH;
    _mm_prefetch(reinterpret_cast<const char*>(r + 16 * ATTN_DH), _MM_HINT_T0);
    const __m256 ve = _mm256_broadcast_ss(eb + j);
    a0 = _mm256_fmadd_ps(ve, _mm256_load_ps(r + 0), a0);
    a1 = _mm256_fmadd_ps(ve, _mm256_load_ps(r + 8), a1);
    a2 = _mm256_fmadd_ps(ve, _mm256_load_ps(r + 16), a2);
    a3 = _mm256_fmadd_ps(ve, _mm256_load_ps(r + 24), a3);
    a4 = _mm256_fmadd_ps(ve, _mm256_load_ps(r + 32), a4);
    a5 = _mm256_fmadd_ps(ve, _mm256_load_ps(r + 40), a5);
    a6 = _mm256_fmadd_ps(ve, _mm256_load_ps(r + 48), a6);
    a7 = _mm256_fmadd_ps(ve, _mm256_load_ps(r + 56), a7);
  }
  const __m256 vf = _mm256_set1_ps(rfac);
  _mm256_store_ps(out64 + 0, _mm256_mul_ps(a0, vf));
  _mm256_store_ps(out64 + 8, _mm256_mul_ps(a1, vf));
  _mm256_store_ps(out64 + 16, _mm256_mul_ps(a2, vf));
  _mm256_store_ps(out64 + 24, _mm256_mul_ps(a3, vf));
  _mm256_store_ps(out64 + 32, _mm256_mul_ps(a4, vf));
  _mm256_store_ps(out64 + 40, _mm256_mul_ps(a5, vf));
  _mm256_store_ps(out64 + 48, _mm256_mul_ps(a6, vf));
  _mm256_store_ps(out64 + 56, _mm256_mul_ps(a7, vf));
}

inline void pv_dense(const int8_t* v, const float* eb, int n, float rfac,
                     float* out64) {
  pv_dense_i8(v, eb, n, rfac, out64);
}
inline void pv_dense(const float* v, const float* eb, int n, float rfac,
                     float* out64) {
  pv_dense_f32(v, eb, n, rfac, out64);
}

template <typename VT>
__attribute__((noinline)) void pv_sparse(const VT* vh, const float* eb, int n,
                                         float rfac, float* out64) {
  __m256 acc[8];
  for (int t = 0; t < 8; t++) acc[t] = _mm256_setzero_ps();
  const __m256 vzero = _mm256_setzero_ps();
  const int G = (n + 7) >> 3;
  for (int g = 0; g < G; g++) {
    const __m256 e = _mm256_load_ps(eb + 8 * g);
    unsigned bits = unsigned(
        _mm256_movemask_ps(_mm256_cmp_ps(e, vzero, _CMP_NEQ_OQ)));
    if (!bits) continue;
    const VT* base = vh + static_cast<size_t>(g) * 8 * ATTN_DH;
    const float* ebg = eb + 8 * g;
    while (bits) {
      const int l = __builtin_ctz(bits);
      bits &= bits - 1;
      _mm_prefetch(reinterpret_cast<const char*>(
                       base + (l + 8) * ATTN_DH),  // likely-next row
                   _MM_HINT_T0);
      pv_row(base + l * ATTN_DH, _mm256_broadcast_ss(ebg + l), acc);
    }
  }
  const __m256 vf = _mm256_set1_ps(rfac);
  for (int t = 0; t < 8; t++)
    _mm256_store_ps(out64 + t * 8, _mm256_mul_ps(acc[t], vf));
}

template <typename VT>
inline void pv_pass(const VT* vh, const float* eb, int n, int kept, float rfac,
                    float* out64) {
  if (kept * 4 >= n * 3)
    pv_dense(vh, eb, n, rfac, out64);
  else
    pv_sparse(vh, eb, n, rfac, out64);
}

// ---------------------------------------------------------------------------
// full step
// ---------------------------------------------------------------------------
template <typename KV, bool FIXED>
inline void attn_impl(const KV& kv, const int8_t* q192, const float* coef3,
                      const float* sv3, int n, float* out192, float thr_in,
                      int* kept3) {
  // thr <= 0 -> exact: the compare keeps every valid lane (finite scores are
  // always >= max - 1e30) and rejects the -inf padding lanes.
  const float thr = thr_in > 0.0f ? thr_in : 1e30f;
  for (int h = 0; h < ATTN_NH; h++) {
    alignas(32) int32_t qp32[32];  // q int16 pairs, one per 32-bit broadcast
    const int8_t* qh = q192 + h * ATTN_DH;
    for (int c = 0; c < 4; c++)
      _mm256_store_si256(
          reinterpret_cast<__m256i*>(qp32 + c * 8),
          _mm256_cvtepi8_epi16(_mm_loadu_si128(
              reinterpret_cast<const __m128i*>(qh + c * 16))));

    PROF_T(p0);
    const float m = qk_scan<FIXED>(&kv.k[h][0][0][0], qp32, coef3[h], n, g_sc);
    PROF_T(p1);
    int kept;
    const float den = exp_pass<FIXED>(g_sc, n, m, thr, g_eb, kept);
    if (kept3) kept3[h] = kept;
    PROF_T(p2);
    pv_pass(&kv.v[h][0][0], g_eb, n, kept, sv3[h] / den,
            out192 + h * ATTN_DH);
    PROF_T(p3);
    PROF_ADD(0, p0, p1);
    PROF_ADD(1, p1, p2);
    PROF_ADD(2, p2, p3);
    PROF_ADD(3, 0, 1);
  }
}

// K scatter of one head row (64 int8) into the transposed pair rows
inline void kt_insert_head(int8_t* dst_pair0, const int8_t* k64) {
  for (int i = 0; i < 32; i++)
    std::memcpy(dst_pair0 + 32 * i, k64 + 2 * i, 2);
}
inline void kt_insert_head(int16_t* dst_pair0, const int8_t* k64) {
  alignas(32) int16_t tmp[64];
  for (int c = 0; c < 4; c++)
    _mm256_store_si256(
        reinterpret_cast<__m256i*>(tmp + c * 16),
        _mm256_cvtepi8_epi16(_mm_loadu_si128(
            reinterpret_cast<const __m128i*>(k64 + c * 16))));
  for (int i = 0; i < 32; i++)
    std::memcpy(dst_pair0 + 32 * i, tmp + 2 * i, 4);
}

}  // namespace

// ---------------------------------------------------------------------------
// public entry points
// ---------------------------------------------------------------------------
void attn_kv_insert(AttnKV& kv, int slot, const int8_t* k192,
                    const int8_t* v192) {
  const int b = slot >> 4, l = slot & 15;
  for (int h = 0; h < ATTN_NH; h++) {
    kt_insert_head(&kv.k[h][b][0][2 * l], k192 + h * ATTN_DH);
    std::memcpy(&kv.v[h][slot][0], v192 + h * ATTN_DH, ATTN_DH);
  }
}

void attn_kv_insert(AttnKV16& kv, int slot, const int8_t* k192,
                    const int8_t* v192) {
  const int b = slot >> 4, l = slot & 15;
  for (int h = 0; h < ATTN_NH; h++) {
    kt_insert_head(&kv.k[h][b][0][2 * l], k192 + h * ATTN_DH);
    std::memcpy(&kv.v[h][slot][0], v192 + h * ATTN_DH, ATTN_DH);
  }
}

void attn_kv_insert(AttnKVF32& kv, int slot, const int8_t* k192,
                    const int8_t* v192) {
  const int b = slot >> 4, l = slot & 15;
  for (int h = 0; h < ATTN_NH; h++) {
    kt_insert_head(&kv.k[h][b][0][2 * l], k192 + h * ATTN_DH);
    const int8_t* s = v192 + h * ATTN_DH;
    float* d = &kv.v[h][slot][0];
    for (int c = 0; c < 8; c++) {
      const __m256i vi = _mm256_cvtepi8_epi32(
          _mm_loadl_epi64(reinterpret_cast<const __m128i*>(s + c * 8)));
      _mm256_store_ps(d + c * 8, _mm256_cvtepi32_ps(vi));
    }
  }
}

void attn_step_var(const AttnKV& kv, const int8_t* q192, const float* coef3,
                   const float* sv3, int n, float* out192, float skip_threshold,
                   int* kept3) {
  attn_impl<AttnKV, false>(kv, q192, coef3, sv3, n, out192, skip_threshold,
                           kept3);
}
void attn_step_var(const AttnKV16& kv, const int8_t* q192, const float* coef3,
                   const float* sv3, int n, float* out192, float skip_threshold,
                   int* kept3) {
  attn_impl<AttnKV16, false>(kv, q192, coef3, sv3, n, out192, skip_threshold,
                             kept3);
}
void attn_step_var(const AttnKVF32& kv, const int8_t* q192, const float* coef3,
                   const float* sv3, int n, float* out192, float skip_threshold,
                   int* kept3) {
  attn_impl<AttnKVF32, false>(kv, q192, coef3, sv3, n, out192, skip_threshold,
                              kept3);
}

void attn_step_fixed(const AttnKV& kv, const int8_t* q192, const float* coef3,
                     const float* sv3, float* out192, float skip_threshold,
                     int* kept3) {
  attn_impl<AttnKV, true>(kv, q192, coef3, sv3, ATTN_WIN, out192,
                          skip_threshold, kept3);
}
void attn_step_fixed(const AttnKV16& kv, const int8_t* q192,
                     const float* coef3, const float* sv3, float* out192,
                     float skip_threshold, int* kept3) {
  attn_impl<AttnKV16, true>(kv, q192, coef3, sv3, ATTN_WIN, out192,
                            skip_threshold, kept3);
}
void attn_step_fixed(const AttnKVF32& kv, const int8_t* q192,
                     const float* coef3, const float* sv3, float* out192,
                     float skip_threshold, int* kept3) {
  attn_impl<AttnKVF32, true>(kv, q192, coef3, sv3, ATTN_WIN, out192,
                             skip_threshold, kept3);
}

}  // namespace opt
}  // namespace fx2
