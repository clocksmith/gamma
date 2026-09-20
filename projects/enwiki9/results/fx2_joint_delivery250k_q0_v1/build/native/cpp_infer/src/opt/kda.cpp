// Fused KDA per-token per-layer step (see kda.h for the contract).
//
// Sweep structure ("1.5-pass", default):
//   pass 1 streams the 16 KB head state once: rowd = S[i][:]*decay[i] is
//   written back (rounded exactly like the naive path) while
//   r += kn[i]*rowd accumulates in 8 ymm registers.
//   pass 2 re-reads the (L1-resident) decayed state in two 32-column
//   halves, applying S[i][:] += kn[i]*u fused with o += (0.125qn)[i]*S[i][:],
//   with u and o halves held in registers. Measured at ~95% of its
//   512-cycle issue floor L1-hot.
// Whole-token state traffic: each 16 KB state is read from L3/L2 once and
// written back once; the pass-2 re-read hits L1. The states are pulled to
// L2 ahead of time by the scheduled front-end prefetch cursor (pf mode 5,
// see kda.h) — in-sweep prefetching measured strictly slower.
//
// The "2-pass" alternative (KdaSweep::TWOPASS) keeps pass 1 read-only using
// r += (kn[i]*decay[i])*S_old[i][:] and folds the decay multiply into
// pass 2 (mul + 2 fma per element there): same 4 FMA-pipe ops per element,
// half the stores, but a 768-cycle pass-2 issue floor vs 512+512 balanced.
// Measured slower; ONEFIVE is the default.
//
// Nonlinearity passes are STAGED through small L1 buffers (z / exp / div as
// separate tight loops): a single exp256 chain has ~50+ cycles of latency
// and ~16 fp ops, and mixed-chain loops choke the fp scheduler and spill
// (measured 37 cyc/vec for interleaved conv+silu vs 22 staged; 92 cyc/vec
// for softplus+exp decay vs 58 staged). Staging preserves the exact
// per-element operation sequence (bit-identical results).

#include "kda.h"

#include <cmath>
#include <cstring>

#include "kda_math.h"  // includes vec_math.h (canonical exp/silu/sigmoid/softplus)

namespace fx2 {
namespace opt {

namespace {

inline uint64_t rdt() {
  unsigned lo, hi;
  asm volatile("lfence\n\trdtsc" : "=a"(lo), "=d"(hi)::"memory");
  return (static_cast<uint64_t>(hi) << 32) | lo;
}

KdaSweep g_sweep = KdaSweep::ONEFIVE;
int g_pf_mode = 5;  // see kda.h; 5 = scheduled front-end prefetch (default)

// prefetch cursor helper: NPF lines per call, clamped to [begin, end).
// t1 = use _MM_HINT_T1 (keeps the 48 KB state batch out of the 32 KB L1
// while the host loops run; sweeps then read L2 hits). The branch is
// perfectly predicted (constant per run).
template <int NPF>
inline void pf_step(const char*& pf, const char* pf_end, bool t1) {
  if (NPF > 0 && pf < pf_end) {
    if (t1) {
      _mm_prefetch(pf, _MM_HINT_T1);
      if (NPF > 1) _mm_prefetch(pf + 64, _MM_HINT_T1);
      if (NPF > 2) _mm_prefetch(pf + 128, _MM_HINT_T1);
      if (NPF > 3) _mm_prefetch(pf + 192, _MM_HINT_T1);
    } else {
      _mm_prefetch(pf, _MM_HINT_T0);
      if (NPF > 1) _mm_prefetch(pf + 64, _MM_HINT_T0);
      if (NPF > 2) _mm_prefetch(pf + 128, _MM_HINT_T0);
      if (NPF > 3) _mm_prefetch(pf + 192, _MM_HINT_T0);
    }
    pf += 64 * NPF;
  }
}

// ---------------- sweep pass 1, 1.5-pass variant ----------------
// rowd = row*decay[i] (stored), r += kn[i]*rowd. r[8] stays in registers.
template <int PF>
inline void pass1_15(float* S, const float* decay, const float* kn,
                     const float* pfp, __m256 r[8]) {
  const char* pf = reinterpret_cast<const char*>(pfp);
  for (int jv = 0; jv < 8; jv++) r[jv] = _mm256_setzero_ps();
  for (int i = 0; i < 64; i++) {
    float* row = S + static_cast<size_t>(i) * 64;
    __m256 d = _mm256_broadcast_ss(decay + i);
    __m256 kb = _mm256_broadcast_ss(kn + i);
    if (PF == 1) {
      _mm_prefetch(pf + 0, _MM_HINT_T0);
      _mm_prefetch(pf + 64, _MM_HINT_T0);
      _mm_prefetch(pf + 128, _MM_HINT_T0);
      _mm_prefetch(pf + 192, _MM_HINT_T0);
      pf += 256;
    } else if (PF == 2) {
      _mm_prefetch(pf + 0, _MM_HINT_T1);
      _mm_prefetch(pf + 64, _MM_HINT_T1);
      _mm_prefetch(pf + 128, _MM_HINT_T1);
      _mm_prefetch(pf + 192, _MM_HINT_T1);
      pf += 256;
    } else if (PF == 3) {
      _mm_prefetch(pf + 0, _MM_HINT_T0);
      _mm_prefetch(pf + 64, _MM_HINT_T0);
      pf += 128;  // covers half the next state; HW prefetch rides the rest
    }
    for (int jv = 0; jv < 8; jv++) {
      __m256 a = _mm256_mul_ps(_mm256_load_ps(row + 8 * jv), d);
      _mm256_store_ps(row + 8 * jv, a);
      r[jv] = _mm256_fmadd_ps(kb, a, r[jv]);
    }
  }
}

// ---------------- sweep pass 1, 2-pass variant (read-only) ----------------
template <int PF>
inline void pass1_2p(const float* S, const float* kd, const float* pfp,
                     __m256 r[8]) {
  const char* pf = reinterpret_cast<const char*>(pfp);
  for (int jv = 0; jv < 8; jv++) r[jv] = _mm256_setzero_ps();
  for (int i = 0; i < 64; i++) {
    const float* row = S + static_cast<size_t>(i) * 64;
    __m256 kb = _mm256_broadcast_ss(kd + i);
    if (PF == 1) {
      _mm_prefetch(pf + 0, _MM_HINT_T0);
      _mm_prefetch(pf + 64, _MM_HINT_T0);
      _mm_prefetch(pf + 128, _MM_HINT_T0);
      _mm_prefetch(pf + 192, _MM_HINT_T0);
      pf += 256;
    } else if (PF == 2) {
      _mm_prefetch(pf + 0, _MM_HINT_T1);
      _mm_prefetch(pf + 64, _MM_HINT_T1);
      _mm_prefetch(pf + 128, _MM_HINT_T1);
      _mm_prefetch(pf + 192, _MM_HINT_T1);
      pf += 256;
    } else if (PF == 3) {
      _mm_prefetch(pf + 0, _MM_HINT_T0);
      _mm_prefetch(pf + 64, _MM_HINT_T0);
      pf += 128;
    }
    for (int jv = 0; jv < 8; jv++)
      r[jv] = _mm256_fmadd_ps(kb, _mm256_load_ps(row + 8 * jv), r[jv]);
  }
}

// ---------------- sweep pass 2, 1.5-pass variant ----------------
// State already decayed. Two 32-column halves; u/o halves in registers.
// PF2 != 0: prefetch the next head's state (2 lines per half-row = full
// 16 KB across the pass) — pass 2 runs on L1 hits, so it has AGU slack and
// its fills do not compete with pass 1's demand misses.
template <int PF2>
inline void pass2_15(float* S, const float* kn, const float* qs,
                     const float* u, float* o, const float* pfp) {
  const char* pf = reinterpret_cast<const char*>(pfp);
  for (int half = 0; half < 2; half++) {
    float* Sh = S + 32 * half;
    const float* uh = u + 32 * half;
    __m256 u0 = _mm256_load_ps(uh + 0);
    __m256 u1 = _mm256_load_ps(uh + 8);
    __m256 u2 = _mm256_load_ps(uh + 16);
    __m256 u3 = _mm256_load_ps(uh + 24);
    __m256 o0 = _mm256_setzero_ps(), o1 = _mm256_setzero_ps();
    __m256 o2 = _mm256_setzero_ps(), o3 = _mm256_setzero_ps();
    for (int i = 0; i < 64; i++) {
      float* row = Sh + static_cast<size_t>(i) * 64;
      __m256 kb = _mm256_broadcast_ss(kn + i);
      __m256 qb = _mm256_broadcast_ss(qs + i);
      if (PF2 != 0) {
        _mm_prefetch(pf + 0, _MM_HINT_T0);
        _mm_prefetch(pf + 64, _MM_HINT_T0);
        pf += 128;
      }
      __m256 a0 = _mm256_fmadd_ps(kb, u0, _mm256_load_ps(row + 0));
      _mm256_store_ps(row + 0, a0);
      o0 = _mm256_fmadd_ps(qb, a0, o0);
      __m256 a1 = _mm256_fmadd_ps(kb, u1, _mm256_load_ps(row + 8));
      _mm256_store_ps(row + 8, a1);
      o1 = _mm256_fmadd_ps(qb, a1, o1);
      __m256 a2 = _mm256_fmadd_ps(kb, u2, _mm256_load_ps(row + 16));
      _mm256_store_ps(row + 16, a2);
      o2 = _mm256_fmadd_ps(qb, a2, o2);
      __m256 a3 = _mm256_fmadd_ps(kb, u3, _mm256_load_ps(row + 24));
      _mm256_store_ps(row + 24, a3);
      o3 = _mm256_fmadd_ps(qb, a3, o3);
    }
    float* oh = o + 32 * half;
    _mm256_store_ps(oh + 0, o0);
    _mm256_store_ps(oh + 8, o1);
    _mm256_store_ps(oh + 16, o2);
    _mm256_store_ps(oh + 24, o3);
  }
}

// ---------------- sweep pass 2, 2-pass variant ----------------
// State NOT yet decayed: a = row*decay[i]; a = fma(kn[i], u, a); store;
// o += qs[i]*a.
inline void pass2_2p(float* S, const float* decay, const float* kn,
                     const float* qs, const float* u, float* o) {
  for (int half = 0; half < 2; half++) {
    float* Sh = S + 32 * half;
    const float* uh = u + 32 * half;
    __m256 u0 = _mm256_load_ps(uh + 0);
    __m256 u1 = _mm256_load_ps(uh + 8);
    __m256 u2 = _mm256_load_ps(uh + 16);
    __m256 u3 = _mm256_load_ps(uh + 24);
    __m256 o0 = _mm256_setzero_ps(), o1 = _mm256_setzero_ps();
    __m256 o2 = _mm256_setzero_ps(), o3 = _mm256_setzero_ps();
    for (int i = 0; i < 64; i++) {
      float* row = Sh + static_cast<size_t>(i) * 64;
      __m256 d = _mm256_broadcast_ss(decay + i);
      __m256 kb = _mm256_broadcast_ss(kn + i);
      __m256 qb = _mm256_broadcast_ss(qs + i);
      __m256 a0 = _mm256_mul_ps(_mm256_load_ps(row + 0), d);
      a0 = _mm256_fmadd_ps(kb, u0, a0);
      _mm256_store_ps(row + 0, a0);
      o0 = _mm256_fmadd_ps(qb, a0, o0);
      __m256 a1 = _mm256_mul_ps(_mm256_load_ps(row + 8), d);
      a1 = _mm256_fmadd_ps(kb, u1, a1);
      _mm256_store_ps(row + 8, a1);
      o1 = _mm256_fmadd_ps(qb, a1, o1);
      __m256 a2 = _mm256_mul_ps(_mm256_load_ps(row + 16), d);
      a2 = _mm256_fmadd_ps(kb, u2, a2);
      _mm256_store_ps(row + 16, a2);
      o2 = _mm256_fmadd_ps(qb, a2, o2);
      __m256 a3 = _mm256_mul_ps(_mm256_load_ps(row + 24), d);
      a3 = _mm256_fmadd_ps(kb, u3, a3);
      _mm256_store_ps(row + 24, a3);
      o3 = _mm256_fmadd_ps(qb, a3, o3);
    }
    float* oh = o + 32 * half;
    _mm256_store_ps(oh + 0, o0);
    _mm256_store_ps(oh + 8, o1);
    _mm256_store_ps(oh + 16, o2);
    _mm256_store_ps(oh + 24, o3);
  }
}

template <int PF, int PF2>
void sweep_head_t(float* S, const float* decay, const float* kn,
                  const float* v, float beta, const float* qs, float* o,
                  const float* pfp, KdaSweep variant) {
  alignas(32) float u[64];
  __m256 r[8];
  if (variant == KdaSweep::ONEFIVE) {
    pass1_15<PF>(S, decay, kn, pfp, r);
  } else {
    alignas(32) float kd[64];
    for (int c = 0; c < 64; c += 8)
      _mm256_store_ps(kd + c, _mm256_mul_ps(_mm256_load_ps(kn + c),
                                            _mm256_load_ps(decay + c)));
    pass1_2p<PF>(S, kd, pfp, r);
  }
  __m256 bb = _mm256_set1_ps(beta);
  for (int jv = 0; jv < 8; jv++) {
    __m256 uv =
        _mm256_mul_ps(bb, _mm256_sub_ps(_mm256_loadu_ps(v + 8 * jv), r[jv]));
    _mm256_store_ps(u + 8 * jv, uv);
  }
  if (variant == KdaSweep::ONEFIVE)
    pass2_15<PF2>(S, kn, qs, u, o, pfp);
  else
    pass2_2p(S, decay, kn, qs, u, o);
}

}  // namespace

void kda_set_sweep(KdaSweep v) { g_sweep = v; }
KdaSweep kda_get_sweep() { return g_sweep; }
void kda_set_pf_mode(int m) { g_pf_mode = m; }
int kda_get_pf_mode() { return g_pf_mode; }

void kda_layer_reset(KdaState& st) { std::memset(&st, 0, sizeof(st)); }

void kda_sweep_head(float* S, const float* decay, const float* kn,
                    const float* v, float beta, const float* qs, float* o,
                    const float* pf_next, KdaSweep variant) {
  const float* pfp = pf_next ? pf_next : S;
  switch (g_pf_mode) {
    case 1: sweep_head_t<1, 0>(S, decay, kn, v, beta, qs, o, pfp, variant); break;
    case 2: sweep_head_t<2, 0>(S, decay, kn, v, beta, qs, o, pfp, variant); break;
    case 3: sweep_head_t<3, 0>(S, decay, kn, v, beta, qs, o, pfp, variant); break;
    case 4: sweep_head_t<0, 1>(S, decay, kn, v, beta, qs, o, pfp, variant); break;
    default: sweep_head_t<0, 0>(S, decay, kn, v, beta, qs, o, pfp, variant); break;
  }
}

void kda_layer_step(const KdaWeights& w, KdaState& st, const float* q_in,
                    const float* k_in, const float* v_in, const float* g_raw,
                    const float* og, const float* beta_raw, float* out,
                    KdaDebug* dbg, KdaProfile* prof) {
  alignas(64) float cq[192], ck[192], cv[192];
  alignas(64) float decay[192], kn192[192], qs192[192], o192[192];
  alignas(64) float zb[576], eb[576];  // staging buffers (z / exp results)

  const __m256 one = _mm256_set1_ps(1.0f);
  const __m256 sign = _mm256_set1_ps(-0.0f);

  uint64_t t0 = prof ? rdt() : 0;

  // Scheduled state prefetch (pf mode 5, the default): one cursor walks all
  // 48 KB of this layer's head states under the front-end's compute-heavy
  // staged passes (~700 prefetcht0 metered at ~1 line / 7 cycles, ~9 B/c —
  // well under the 22.7 B/c L3 read budget), so every sweep pass runs on an
  // L1/L2-warm state. Sweep-side prefetching measured strictly worse (it
  // steals AGU slots and L1 fill ports from the store-saturated pass 1).
  const char* pfc = reinterpret_cast<const char*>(st.S[0]);
  const char* pfe =
      (g_pf_mode == 5 || g_pf_mode == 6) ? pfc + sizeof(st.S) : pfc;
  const bool pft1 = g_pf_mode == 6;

  // ---- conv (staged): tap-z pass (+ring update), one exp pass over all
  //      3*192 channels, then the silu division fused with the q/k
  //      l2norm sum-of-squares accumulation ----
  const uint32_t slot = st.pos & 3;
  __m256 aq[3], ak[3];  // l2norm sums (bit-identical order to naive)
  {
    const float* in3[3] = {q_in, k_in, v_in};
    for (int c3 = 0; c3 < 3; c3++) {
      float(*ring)[192] = st.ring[c3];
      const float* t0p = ring[(slot + 1) & 3];
      const float* t1p = ring[(slot + 2) & 3];
      const float* t2p = ring[(slot + 3) & 3];
      const float* x = in3[c3];
      float* slotp = ring[slot];
      const float* wt = w.conv_w[c3];
      float* z3 = zb + 192 * c3;
      for (int c = 0; c < 192; c += 8) {
        __m256 xv = _mm256_loadu_ps(x + c);
        _mm256_store_ps(slotp + c, xv);
        __m256 z = _mm256_mul_ps(_mm256_loadu_ps(wt + c),
                                 _mm256_load_ps(t0p + c));
        z = _mm256_fmadd_ps(_mm256_loadu_ps(wt + 192 + c),
                            _mm256_load_ps(t1p + c), z);
        z = _mm256_fmadd_ps(_mm256_loadu_ps(wt + 384 + c),
                            _mm256_load_ps(t2p + c), z);
        z = _mm256_fmadd_ps(_mm256_loadu_ps(wt + 576 + c), xv, z);
        _mm256_store_ps(z3 + c, z);
      }
    }
    for (int c = 0; c < 576; c += 8) {
      pf_step<4>(pfc, pfe, pft1);
      _mm256_store_ps(eb + c,
                      exp256_ps(_mm256_xor_ps(_mm256_load_ps(zb + c), sign)));
    }
    float* out3[3] = {cq, ck, cv};
    for (int h = 0; h < 3; h++) {
      aq[h] = _mm256_setzero_ps();
      ak[h] = _mm256_setzero_ps();
    }
    for (int c3 = 0; c3 < 3; c3++) {
      float* y = out3[c3];
      const float* z3 = zb + 192 * c3;
      const float* e3 = eb + 192 * c3;
      for (int c = 0; c < 192; c += 8) {
        pf_step<3>(pfc, pfe, pft1);
        __m256 r = _mm256_div_ps(_mm256_load_ps(z3 + c),
                                 _mm256_add_ps(one, _mm256_load_ps(e3 + c)));
        _mm256_store_ps(y + c, r);
        if (c3 == 0) aq[c >> 6] = _mm256_fmadd_ps(r, r, aq[c >> 6]);
        if (c3 == 1) ak[c >> 6] = _mm256_fmadd_ps(r, r, ak[c >> 6]);
      }
    }
  }

  uint64_t t1 = prof ? rdt() : 0;

  // ---- per-channel log-decay gate, staged:
  //      x = g_raw + dt_bias; u = exp256(x); sp = log1p(u) (blend x>20 -> x);
  //      arg = a_neg*sp; decay = exp_full(arg). Same op sequence as
  //      softplus256_ps + exp, staged through zb/eb. ----
  {
    for (int c = 0; c < 192; c += 8) {
      pf_step<4>(pfc, pfe, pft1);
      __m256 x = _mm256_add_ps(_mm256_loadu_ps(g_raw + c),
                               _mm256_loadu_ps(w.dt_bias + c));
      _mm256_store_ps(zb + c, x);
      _mm256_store_ps(eb + c, exp256_ps(x));
    }
    const __m256 twenty = _mm256_set1_ps(20.0f);
    for (int h = 0; h < 3; h++) {
      __m256 an = _mm256_set1_ps(w.a_neg[h]);
      for (int c = 64 * h; c < 64 * h + 64; c += 8) {
        pf_step<2>(pfc, pfe, pft1);
        __m256 x = _mm256_load_ps(zb + c);
        __m256 sp = log1p256_ps(_mm256_load_ps(eb + c));
        sp = _mm256_blendv_ps(sp, x, _mm256_cmp_ps(x, twenty, _CMP_GT_OQ));
        _mm256_store_ps(zb + c, _mm256_mul_ps(an, sp));
      }
    }
    for (int c = 0; c < 192; c += 8) {
      pf_step<4>(pfc, pfe, pft1);
      _mm256_store_ps(decay + c, exp_full8(_mm256_load_ps(zb + c)));
    }
  }

  // ---- beta sigmoid (3 logits) ----
  float beta[3];
  {
    alignas(32) float b8[8] = {beta_raw[0], beta_raw[1], beta_raw[2],
                               0, 0, 0, 0, 0};
    _mm256_store_ps(b8, sigmoid256_ps(_mm256_load_ps(b8)));
    beta[0] = b8[0];
    beta[1] = b8[1];
    beta[2] = b8[2];
  }

  // ---- q/k l2norm (eps 1e-6 on the raw sum) + 0.125 q-scale;
  //      sums were accumulated in the conv division pass ----
  {
    const __m256 eighth = _mm256_set1_ps(0.125f);
    for (int h = 0; h < 3; h++) {
      float dq = std::sqrt(hsum256v(aq[h]) + 1e-6f);
      float dk = std::sqrt(hsum256v(ak[h]) + 1e-6f);
      __m256 dqb = _mm256_set1_ps(dq);
      __m256 dkb = _mm256_set1_ps(dk);
      for (int c = 0; c < 64; c += 8) {
        pf_step<2>(pfc, pfe, pft1);
        __m256 qn = _mm256_div_ps(_mm256_load_ps(cq + 64 * h + c), dqb);
        _mm256_store_ps(qs192 + 64 * h + c, _mm256_mul_ps(eighth, qn));
        _mm256_store_ps(kn192 + 64 * h + c,
                        _mm256_div_ps(_mm256_load_ps(ck + 64 * h + c), dkb));
      }
    }
  }

  uint64_t t2 = prof ? rdt() : 0;

  // ---- the three head sweeps (next head's state prefetched in pass 1) ----
  for (int h = 0; h < 3; h++) {
    const float* pfn = st.S[h < 2 ? h + 1 : h];  // self-prefetch for the last
    kda_sweep_head(st.S[h], decay + 64 * h, kn192 + 64 * h, cv + 64 * h,
                   beta[h], qs192 + 64 * h, o192 + 64 * h, pfn, g_sweep);
  }

  uint64_t t3 = prof ? rdt() : 0;

  // ---- gated rms norm: rmsnorm64(o)*w*sigmoid(og), sigmoid staged ----
  {
    // three per-head sums interleaved (each keeps the naive serial order)
    __m256 ao[3];
    for (int h = 0; h < 3; h++) ao[h] = _mm256_setzero_ps();
    for (int c = 0; c < 64; c += 8)
      for (int h = 0; h < 3; h++) {
        __m256 vo = _mm256_load_ps(o192 + 64 * h + c);
        ao[h] = _mm256_fmadd_ps(vo, vo, ao[h]);
      }
    for (int c = 0; c < 192; c += 8)
      _mm256_store_ps(eb + c,
                      exp256_ps(_mm256_xor_ps(_mm256_loadu_ps(og + c), sign)));
    for (int h = 0; h < 3; h++) {
      float ss = hsum256v(ao[h]);
      float rstd = 1.0f / std::sqrt(ss / 64.0f + 1e-5f);
      __m256 rb = _mm256_set1_ps(rstd);
      for (int c = 0; c < 64; c += 8) {
        __m256 sg = _mm256_div_ps(one,
                                  _mm256_add_ps(one, _mm256_load_ps(eb + 64 * h + c)));
        __m256 t = _mm256_mul_ps(_mm256_load_ps(o192 + 64 * h + c), rb);
        t = _mm256_mul_ps(t, _mm256_loadu_ps(w.gn_w + c));
        _mm256_storeu_ps(out + 64 * h + c, _mm256_mul_ps(t, sg));
      }
    }
  }

  if (prof) {
    uint64_t t4 = rdt();
    prof->conv += t1 - t0;
    prof->gates += t2 - t1;
    prof->sweep += t3 - t2;
    prof->norm += t4 - t3;
  }

  if (dbg) {
    if (dbg->conv_q) std::memcpy(dbg->conv_q, cq, sizeof(cq));
    if (dbg->conv_k) std::memcpy(dbg->conv_k, ck, sizeof(ck));
    if (dbg->conv_v) std::memcpy(dbg->conv_v, cv, sizeof(cv));
    if (dbg->kda_out) std::memcpy(dbg->kda_out, o192, sizeof(o192));
  }

  st.pos++;
}

}  // namespace opt
}  // namespace fx2
