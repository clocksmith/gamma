#include "qmat_sparse.h"

#include <immintrin.h>

#include <algorithm>
#include <cstring>

namespace fx2 {
namespace opt {

namespace {

constexpr int FLUSH_PAIRS = 18;  // 18 * 2*127*7 = 32004 < 32767 (exact bound)
#ifndef QMAT_PF_PAIRS_AHEAD
#define QMAT_PF_PAIRS_AHEAD 4
#endif
constexpr int PF_PAIRS_AHEAD = QMAT_PF_PAIRS_AHEAD;

struct IdxLut8 {
  alignas(64) uint8_t t[256][8];
  IdxLut8() {
    for (int m = 0; m < 256; m++) {
      int k = 0;
      for (int b = 0; b < 8; b++)
        if (m & (1 << b)) t[m][k++] = static_cast<uint8_t>(b);
      for (; k < 8; k++) t[m][k] = 0;
    }
  }
};
const IdxLut8 g_lut;

// widen the 12 s16 accumulators into acc[192] (natural row order) and clear.
// a[4b+0] = rows 64b+{0..7 | 16..23}, a[4b+1] = 64b+{8..15 | 24..31},
// a[4b+2] = 64b+{32..39 | 48..55},   a[4b+3] = 64b+{40..47 | 56..63}.
#define QS_FLUSH1(A, base_lo, base_hi)                                       \
  {                                                                          \
    __m256i lo32 = _mm256_cvtepi16_epi32(_mm256_castsi256_si128(A));         \
    __m256i hi32 = _mm256_cvtepi16_epi32(_mm256_extracti128_si256(A, 1));    \
    _mm256_store_si256(                                                      \
        reinterpret_cast<__m256i*>(acc + (base_lo)),                         \
        _mm256_add_epi32(lo32, _mm256_load_si256(reinterpret_cast<          \
                                   const __m256i*>(acc + (base_lo)))));      \
    _mm256_store_si256(                                                      \
        reinterpret_cast<__m256i*>(acc + (base_hi)),                         \
        _mm256_add_epi32(hi32, _mm256_load_si256(reinterpret_cast<          \
                                   const __m256i*>(acc + (base_hi)))));      \
    A = _mm256_setzero_si256();                                              \
  }

#define QS_FLUSH_ALL()                                                       \
  {                                                                          \
    QS_FLUSH1(a0, 0, 16)                                                     \
    QS_FLUSH1(a1, 8, 24)                                                     \
    QS_FLUSH1(a2, 32, 48)                                                    \
    QS_FLUSH1(a3, 40, 56)                                                    \
    QS_FLUSH1(a4, 64, 80)                                                    \
    QS_FLUSH1(a5, 72, 88)                                                    \
    QS_FLUSH1(a6, 96, 112)                                                   \
    QS_FLUSH1(a7, 104, 120)                                                  \
    QS_FLUSH1(a8, 128, 144)                                                  \
    QS_FLUSH1(a9, 136, 152)                                                  \
    QS_FLUSH1(a10, 160, 176)                                                 \
    QS_FLUSH1(a11, 168, 184)                                                 \
  }

// one column pair into the 12 s16 accumulators
#define QS_BLOCK(b, A0, A1, A2, A3)                                          \
  {                                                                          \
    __m256i w = _mm256_load_si256(c0 + 2 * (b));                             \
    __m256i x = _mm256_load_si256(c1 + 2 * (b));                             \
    __m256i t = _mm256_unpacklo_epi8(w, x);                                  \
    A0 = _mm256_add_epi16(A0, _mm256_maddubs_epi16(av, t));                  \
    t = _mm256_unpackhi_epi8(w, x);                                          \
    A1 = _mm256_add_epi16(A1, _mm256_maddubs_epi16(av, t));                  \
    w = _mm256_load_si256(c0 + 2 * (b) + 1);                                 \
    x = _mm256_load_si256(c1 + 2 * (b) + 1);                                 \
    t = _mm256_unpacklo_epi8(w, x);                                          \
    A2 = _mm256_add_epi16(A2, _mm256_maddubs_epi16(av, t));                  \
    t = _mm256_unpackhi_epi8(w, x);                                          \
    A3 = _mm256_add_epi16(A3, _mm256_maddubs_epi16(av, t));                  \
  }

#define QS_PAIR()                                                            \
  {                                                                          \
    QS_BLOCK(0, a0, a1, a2, a3)                                              \
    QS_BLOCK(1, a4, a5, a6, a7)                                              \
    QS_BLOCK(2, a8, a9, a10, a11)                                            \
  }

// index-driven accumulation of nnz nonzero columns into acc[192] (zeroed here)
template <bool PF>
void sparse_accum(const int8_t* __restrict cols, const uint8_t* __restrict q8,
                  const uint16_t* __restrict idx, int nnz,
                  int32_t* __restrict acc) {
  std::memset(acc, 0, sizeof(int32_t) * 192);
  __m256i a0 = _mm256_setzero_si256(), a1 = a0, a2 = a0, a3 = a0, a4 = a0,
          a5 = a0, a6 = a0, a7 = a0, a8 = a0, a9 = a0, a10 = a0, a11 = a0;
  const int npairs = nnz / 2;
  int p = 0;
  while (p < npairs) {
    const int end = std::min(p + FLUSH_PAIRS, npairs);
    for (; p < end; p++) {
      const uint32_t i0 = idx[2 * p], i1 = idx[2 * p + 1];
      if (PF) {  // prefetch both columns of the pair PF_PAIRS_AHEAD ahead
        const char* f0 = reinterpret_cast<const char*>(cols) +
                         192u * idx[2 * (p + PF_PAIRS_AHEAD)];
        const char* f1 = reinterpret_cast<const char*>(cols) +
                         192u * idx[2 * (p + PF_PAIRS_AHEAD) + 1];
        _mm_prefetch(f0, _MM_HINT_T0);
        _mm_prefetch(f0 + 64, _MM_HINT_T0);
        _mm_prefetch(f0 + 128, _MM_HINT_T0);
        _mm_prefetch(f1, _MM_HINT_T0);
        _mm_prefetch(f1 + 64, _MM_HINT_T0);
        _mm_prefetch(f1 + 128, _MM_HINT_T0);
      }
      const __m256i* c0 =
          reinterpret_cast<const __m256i*>(cols + 192u * i0);
      const __m256i* c1 =
          reinterpret_cast<const __m256i*>(cols + 192u * i1);
      const __m256i av = _mm256_set1_epi16(
          static_cast<short>(q8[i0] | (q8[i1] << 8)));
      QS_PAIR()
    }
    QS_FLUSH_ALL()
  }
  if (nnz & 1) {  // tail column: pair it with itself, second act byte = 0
    const uint32_t i0 = idx[nnz - 1];
    const __m256i* c0 = reinterpret_cast<const __m256i*>(cols + 192u * i0);
    const __m256i* c1 = c0;
    const __m256i av = _mm256_set1_epi16(static_cast<short>(q8[i0]));
    QS_PAIR()
    QS_FLUSH_ALL()
  }
}

// dense fallback: every column, sequential stream over the same arena
void dense_accum(const int8_t* __restrict cols, const uint8_t* __restrict q8,
                 int d_in, int32_t* __restrict acc) {
  std::memset(acc, 0, sizeof(int32_t) * 192);
  __m256i a0 = _mm256_setzero_si256(), a1 = a0, a2 = a0, a3 = a0, a4 = a0,
          a5 = a0, a6 = a0, a7 = a0, a8 = a0, a9 = a0, a10 = a0, a11 = a0;
  const int npairs = d_in / 2;
  int p = 0;
  while (p < npairs) {
    const int end = std::min(p + FLUSH_PAIRS, npairs);
    for (; p < end; p++) {
      const uint32_t i0 = 2 * p, i1 = 2 * p + 1;
      const char* f = reinterpret_cast<const char*>(cols) + 192u * i0 + 2048;
      _mm_prefetch(f, _MM_HINT_T0);
      _mm_prefetch(f + 64, _MM_HINT_T0);
      _mm_prefetch(f + 128, _MM_HINT_T0);
      _mm_prefetch(f + 192, _MM_HINT_T0);
      _mm_prefetch(f + 256, _MM_HINT_T0);
      _mm_prefetch(f + 320, _MM_HINT_T0);
      const __m256i* c0 =
          reinterpret_cast<const __m256i*>(cols + 192u * i0);
      const __m256i* c1 =
          reinterpret_cast<const __m256i*>(cols + 192u * i1);
      const __m256i av = _mm256_set1_epi16(
          static_cast<short>(q8[i0] | (q8[i1] << 8)));
      QS_PAIR()
    }
    QS_FLUSH_ALL()
  }
  if (d_in & 1) {
    const uint32_t i0 = static_cast<uint32_t>(d_in - 1);
    const __m256i* c0 = reinterpret_cast<const __m256i*>(cols + 192u * i0);
    const __m256i* c1 = c0;
    const __m256i av = _mm256_set1_epi16(static_cast<short>(q8[i0]));
    QS_PAIR()
    QS_FLUSH_ALL()
  }
}

inline void epi_f32(const int32_t* acc, const float* fold, float* out) {
  for (int k = 0; k < 24; k++) {
    __m256 y = _mm256_mul_ps(
        _mm256_cvtepi32_ps(_mm256_load_si256(
            reinterpret_cast<const __m256i*>(acc + 8 * k))),
        _mm256_load_ps(fold + 8 * k));
    _mm256_storeu_ps(out + 8 * k, y);
  }
}

inline void epi_add(const int32_t* acc, const float* fold, float* out) {
  for (int k = 0; k < 24; k++) {
    __m256 y = _mm256_mul_ps(
        _mm256_cvtepi32_ps(_mm256_load_si256(
            reinterpret_cast<const __m256i*>(acc + 8 * k))),
        _mm256_load_ps(fold + 8 * k));
    _mm256_storeu_ps(out + 8 * k, _mm256_add_ps(_mm256_loadu_ps(out + 8 * k), y));
  }
}

// ---------------------------------------------------------------------------
// int4-packed columns (QSparse4): 128-B columns = 2 cache lines. Nibbles are
// qw+7 in [0,14]; byte b of a column = row b (low nibble) | row 96+b (high).
// maddubs(unsigned = interleaved nibbles, signed = act pair); the global
// correction 7*sum(acts) is subtracted exactly in the int32 epilogue.
// The per-pair contribution is one-sided in [0, 3556]; initializing the s16
// accumulators to -32768 uses the full 16-bit range (true sum x in
// [0, 65535], stored as x - 32768), recovered at flush by xor 0x8000 +
// zero-extend. 18 * 3556 = 64008 <= 65535 -> same flush cadence as int8.
// ---------------------------------------------------------------------------
constexpr int FLUSH_PAIRS4 = 18;

// block b covers rows [32b,32b+32) (low nibbles) and [96+32b,96+32b+32)
#define QS4_BLOCK(b, AL0, AL1, AH0, AH1)                                     \
  {                                                                          \
    __m256i w = _mm256_load_si256(c0 + (b));                                 \
    __m256i x = _mm256_load_si256(c1 + (b));                                 \
    __m256i wl = _mm256_and_si256(w, m0F);                                   \
    __m256i xl = _mm256_and_si256(x, m0F);                                   \
    __m256i t = _mm256_unpacklo_epi8(wl, xl);                                \
    AL0 = _mm256_add_epi16(AL0, _mm256_maddubs_epi16(t, av));                \
    t = _mm256_unpackhi_epi8(wl, xl);                                        \
    AL1 = _mm256_add_epi16(AL1, _mm256_maddubs_epi16(t, av));                \
    w = _mm256_and_si256(_mm256_srli_epi16(w, 4), m0F);                      \
    x = _mm256_and_si256(_mm256_srli_epi16(x, 4), m0F);                      \
    t = _mm256_unpacklo_epi8(w, x);                                          \
    AH0 = _mm256_add_epi16(AH0, _mm256_maddubs_epi16(t, av));                \
    t = _mm256_unpackhi_epi8(w, x);                                          \
    AH1 = _mm256_add_epi16(AH1, _mm256_maddubs_epi16(t, av));                \
  }

#define QS4_PAIR()                                                           \
  {                                                                          \
    QS4_BLOCK(0, a0, a1, a2, a3)                                             \
    QS4_BLOCK(1, a4, a5, a6, a7)                                             \
    QS4_BLOCK(2, a8, a9, a10, a11)                                           \
  }

// biased-s16 flush: true 16-bit sum bits = acc ^ 0x8000; zero-extend; reset
// the accumulator to the -32768 bias.
#define QS4_FLUSH1(A, base_lo, base_hi)                                      \
  {                                                                          \
    __m256i ux = _mm256_xor_si256(A, vbias);                                 \
    __m256i lo32 = _mm256_cvtepu16_epi32(_mm256_castsi256_si128(ux));        \
    __m256i hi32 = _mm256_cvtepu16_epi32(_mm256_extracti128_si256(ux, 1));   \
    _mm256_store_si256(                                                      \
        reinterpret_cast<__m256i*>(acc + (base_lo)),                         \
        _mm256_add_epi32(lo32, _mm256_load_si256(reinterpret_cast<          \
                                   const __m256i*>(acc + (base_lo)))));      \
    _mm256_store_si256(                                                      \
        reinterpret_cast<__m256i*>(acc + (base_hi)),                         \
        _mm256_add_epi32(hi32, _mm256_load_si256(reinterpret_cast<          \
                                   const __m256i*>(acc + (base_hi)))));      \
    A = vbias;                                                               \
  }

#define QS4_FLUSH_ALL()                                                      \
  {                                                                          \
    QS4_FLUSH1(a0, 0, 16)                                                    \
    QS4_FLUSH1(a1, 8, 24)                                                    \
    QS4_FLUSH1(a2, 96, 112)                                                  \
    QS4_FLUSH1(a3, 104, 120)                                                 \
    QS4_FLUSH1(a4, 32, 48)                                                   \
    QS4_FLUSH1(a5, 40, 56)                                                   \
    QS4_FLUSH1(a6, 128, 144)                                                 \
    QS4_FLUSH1(a7, 136, 152)                                                 \
    QS4_FLUSH1(a8, 64, 80)                                                   \
    QS4_FLUSH1(a9, 72, 88)                                                   \
    QS4_FLUSH1(a10, 160, 176)                                                \
    QS4_FLUSH1(a11, 168, 184)                                                \
  }

// returns 7 * sum(processed act values): the exact global int32 correction
template <bool PF>
int32_t sparse4_accum(const uint8_t* __restrict cols,
                      const uint8_t* __restrict q8,
                      const uint16_t* __restrict idx, int nnz,
                      int32_t* __restrict acc) {
  std::memset(acc, 0, sizeof(int32_t) * 192);
  const __m256i m0F = _mm256_set1_epi8(0x0F);
  const __m256i vbias = _mm256_set1_epi16(static_cast<short>(0x8000));
  __m256i a0 = vbias, a1 = vbias, a2 = vbias, a3 = vbias, a4 = vbias,
          a5 = vbias, a6 = vbias, a7 = vbias, a8 = vbias, a9 = vbias,
          a10 = vbias, a11 = vbias;
  uint32_t asum = 0;
  const int npairs = nnz / 2;
  int p = 0;
  while (p < npairs) {
    const int end = std::min(p + FLUSH_PAIRS4, npairs);
    for (; p < end; p++) {
      const uint32_t i0 = idx[2 * p], i1 = idx[2 * p + 1];
      if (PF) {
        const char* f0 = reinterpret_cast<const char*>(cols) +
                         128u * idx[2 * (p + PF_PAIRS_AHEAD)];
        const char* f1 = reinterpret_cast<const char*>(cols) +
                         128u * idx[2 * (p + PF_PAIRS_AHEAD) + 1];
        _mm_prefetch(f0, _MM_HINT_T0);
        _mm_prefetch(f0 + 64, _MM_HINT_T0);
        _mm_prefetch(f1, _MM_HINT_T0);
        _mm_prefetch(f1 + 64, _MM_HINT_T0);
      }
      const __m256i* c0 = reinterpret_cast<const __m256i*>(cols + 128u * i0);
      const __m256i* c1 = reinterpret_cast<const __m256i*>(cols + 128u * i1);
      const uint32_t v0 = q8[i0], v1 = q8[i1];
      asum += v0 + v1;
      const __m256i av = _mm256_set1_epi16(static_cast<short>(v0 | (v1 << 8)));
      QS4_PAIR()
    }
    QS4_FLUSH_ALL()
  }
  if (nnz & 1) {  // tail column paired with itself, second act byte = 0
    const uint32_t i0 = idx[nnz - 1];
    const __m256i* c0 = reinterpret_cast<const __m256i*>(cols + 128u * i0);
    const __m256i* c1 = c0;
    const uint32_t v0 = q8[i0];
    asum += v0;
    const __m256i av = _mm256_set1_epi16(static_cast<short>(v0));
    QS4_PAIR()
    QS4_FLUSH_ALL()
  }
  return static_cast<int32_t>(7u * asum);
}

int32_t dense4_accum(const uint8_t* __restrict cols,
                     const uint8_t* __restrict q8, int d_in,
                     int32_t* __restrict acc) {
  std::memset(acc, 0, sizeof(int32_t) * 192);
  const __m256i m0F = _mm256_set1_epi8(0x0F);
  const __m256i vbias = _mm256_set1_epi16(static_cast<short>(0x8000));
  __m256i a0 = vbias, a1 = vbias, a2 = vbias, a3 = vbias, a4 = vbias,
          a5 = vbias, a6 = vbias, a7 = vbias, a8 = vbias, a9 = vbias,
          a10 = vbias, a11 = vbias;
  uint32_t asum = 0;
  const int npairs = d_in / 2;
  int p = 0;
  while (p < npairs) {
    const int end = std::min(p + FLUSH_PAIRS4, npairs);
    for (; p < end; p++) {
      const uint32_t i0 = 2 * p, i1 = 2 * p + 1;
      const char* f = reinterpret_cast<const char*>(cols) + 128u * i0 + 2048;
      _mm_prefetch(f, _MM_HINT_T0);
      _mm_prefetch(f + 64, _MM_HINT_T0);
      _mm_prefetch(f + 128, _MM_HINT_T0);
      _mm_prefetch(f + 192, _MM_HINT_T0);
      const __m256i* c0 = reinterpret_cast<const __m256i*>(cols + 128u * i0);
      const __m256i* c1 = reinterpret_cast<const __m256i*>(cols + 128u * i1);
      const uint32_t v0 = q8[i0], v1 = q8[i1];
      asum += v0 + v1;
      const __m256i av = _mm256_set1_epi16(static_cast<short>(v0 | (v1 << 8)));
      QS4_PAIR()
    }
    QS4_FLUSH_ALL()
  }
  if (d_in & 1) {
    const uint32_t i0 = static_cast<uint32_t>(d_in - 1);
    const __m256i* c0 = reinterpret_cast<const __m256i*>(cols + 128u * i0);
    const __m256i* c1 = c0;
    const uint32_t v0 = q8[i0];
    asum += v0;
    const __m256i av = _mm256_set1_epi16(static_cast<short>(v0));
    QS4_PAIR()
    QS4_FLUSH_ALL()
  }
  return static_cast<int32_t>(7u * asum);
}

inline void epi4_f32(const int32_t* acc, int32_t corr, const float* fold,
                     float* out) {
  const __m256i vc = _mm256_set1_epi32(corr);
  for (int k = 0; k < 24; k++) {
    __m256i d = _mm256_sub_epi32(
        _mm256_load_si256(reinterpret_cast<const __m256i*>(acc + 8 * k)), vc);
    __m256 y = _mm256_mul_ps(_mm256_cvtepi32_ps(d), _mm256_load_ps(fold + 8 * k));
    _mm256_storeu_ps(out + 8 * k, y);
  }
}

inline void epi4_add(const int32_t* acc, int32_t corr, const float* fold,
                     float* out) {
  const __m256i vc = _mm256_set1_epi32(corr);
  for (int k = 0; k < 24; k++) {
    __m256i d = _mm256_sub_epi32(
        _mm256_load_si256(reinterpret_cast<const __m256i*>(acc + 8 * k)), vc);
    __m256 y = _mm256_mul_ps(_mm256_cvtepi32_ps(d), _mm256_load_ps(fold + 8 * k));
    _mm256_storeu_ps(out + 8 * k, _mm256_add_ps(_mm256_loadu_ps(out + 8 * k), y));
  }
}

// warm the epilogue inputs while the gather runs: fold[192] (12 lines) and,
// for the add variant, the residual (12 lines) are L3-cold in steady state;
// without this the tail chain (load->cvt->mul->add->store) eats their L3
// latency nearly serially (~+1.5 K cyc measured on the real stream).
inline void warm_epilogue(const float* fold, const float* out) {
  for (int k = 0; k < 12; k++)
    _mm_prefetch(reinterpret_cast<const char*>(fold) + 64 * k, _MM_HINT_T0);
  if (out)
    for (int k = 0; k < 12; k++)
      _mm_prefetch(reinterpret_cast<const char*>(out) + 64 * k, _MM_HINT_T0);
}

}  // namespace

void qsparse_f32(const QSparse& m, const uint8_t* q8, const uint16_t* idx,
                 int nnz, float* out) {
  alignas(64) int32_t acc[192];
  warm_epilogue(m.fold, nullptr);
  sparse_accum<true>(m.cols, q8, idx, nnz, acc);
  epi_f32(acc, m.fold, out);
}

void qsparse_f32_nopf(const QSparse& m, const uint8_t* q8,
                      const uint16_t* idx, int nnz, float* out) {
  alignas(64) int32_t acc[192];
  sparse_accum<false>(m.cols, q8, idx, nnz, acc);
  epi_f32(acc, m.fold, out);
}

void qsparse_add(const QSparse& m, const uint8_t* q8, const uint16_t* idx,
                 int nnz, float* out) {
  alignas(64) int32_t acc[192];
  warm_epilogue(m.fold, out);
  sparse_accum<true>(m.cols, q8, idx, nnz, acc);
  epi_add(acc, m.fold, out);
}

void qsparse_i32(const QSparse& m, const uint8_t* q8, const uint16_t* idx,
                 int nnz, int32_t* out) {
  alignas(64) int32_t acc[192];
  sparse_accum<true>(m.cols, q8, idx, nnz, acc);
  std::memcpy(out, acc, sizeof(acc));
}

void qsparse_dense_f32(const QSparse& m, const uint8_t* q8, float* out) {
  alignas(64) int32_t acc[192];
  warm_epilogue(m.fold, nullptr);
  dense_accum(m.cols, q8, m.d_in, acc);
  epi_f32(acc, m.fold, out);
}

void qsparse_dense_add(const QSparse& m, const uint8_t* q8, float* out) {
  alignas(64) int32_t acc[192];
  warm_epilogue(m.fold, out);
  dense_accum(m.cols, q8, m.d_in, acc);
  epi_add(acc, m.fold, out);
}

void qsparse_dense_i32(const QSparse& m, const uint8_t* q8, int32_t* out) {
  alignas(64) int32_t acc[192];
  dense_accum(m.cols, q8, m.d_in, acc);
  std::memcpy(out, acc, sizeof(acc));
}

void qsparse4_f32(const QSparse4& m, const uint8_t* q8, const uint16_t* idx,
                  int nnz, float* out) {
  alignas(64) int32_t acc[192];
  warm_epilogue(m.fold, nullptr);
  int32_t corr = sparse4_accum<true>(m.cols, q8, idx, nnz, acc);
  epi4_f32(acc, corr, m.fold, out);
}

void qsparse4_add(const QSparse4& m, const uint8_t* q8, const uint16_t* idx,
                  int nnz, float* out) {
  alignas(64) int32_t acc[192];
  warm_epilogue(m.fold, out);
  int32_t corr = sparse4_accum<true>(m.cols, q8, idx, nnz, acc);
  epi4_add(acc, corr, m.fold, out);
}

void qsparse4_i32(const QSparse4& m, const uint8_t* q8, const uint16_t* idx,
                  int nnz, int32_t* out) {
  alignas(64) int32_t acc[192];
  int32_t corr = sparse4_accum<true>(m.cols, q8, idx, nnz, acc);
  for (int r = 0; r < 192; r++) out[r] = acc[r] - corr;
}

void qsparse4_dense_f32(const QSparse4& m, const uint8_t* q8, float* out) {
  alignas(64) int32_t acc[192];
  warm_epilogue(m.fold, nullptr);
  int32_t corr = dense4_accum(m.cols, q8, m.d_in, acc);
  epi4_f32(acc, corr, m.fold, out);
}

void qsparse4_dense_add(const QSparse4& m, const uint8_t* q8, float* out) {
  alignas(64) int32_t acc[192];
  warm_epilogue(m.fold, out);
  int32_t corr = dense4_accum(m.cols, q8, m.d_in, acc);
  epi4_add(acc, corr, m.fold, out);
}

void qsparse4_dense_i32(const QSparse4& m, const uint8_t* q8, int32_t* out) {
  alignas(64) int32_t acc[192];
  int32_t corr = dense4_accum(m.cols, q8, m.d_in, acc);
  for (int r = 0; r < 192; r++) out[r] = acc[r] - corr;
}

int qsparse_make_idx(const uint8_t* q8, int n, uint16_t* idx) {
  int nnz = 0;
  const int nblk = (n + 31) / 32;
  for (int b = 0; b < nblk; b++) {
    __m256i v = _mm256_loadu_si256(
        reinterpret_cast<const __m256i*>(q8 + 32 * b));
    uint32_t zm = static_cast<uint32_t>(_mm256_movemask_epi8(
        _mm256_cmpeq_epi8(v, _mm256_setzero_si256())));
    uint32_t m = ~zm;
    if (b == nblk - 1 && (n & 31)) m &= (1u << (n & 31)) - 1;
    for (int k = 0; k < 4; k++) {
      const uint32_t m8 = (m >> (8 * k)) & 0xFF;
      __m128i lut = _mm_loadl_epi64(
          reinterpret_cast<const __m128i*>(g_lut.t[m8]));
      __m128i i16 = _mm_add_epi16(
          _mm_cvtepu8_epi16(lut),
          _mm_set1_epi16(static_cast<short>(32 * b + 8 * k)));
      _mm_storeu_si128(reinterpret_cast<__m128i*>(idx + nnz), i16);
      nnz += __builtin_popcount(m8);
    }
  }
  return nnz;
}

}  // namespace opt
}  // namespace fx2
