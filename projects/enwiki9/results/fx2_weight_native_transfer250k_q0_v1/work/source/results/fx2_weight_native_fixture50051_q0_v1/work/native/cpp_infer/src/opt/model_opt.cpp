// TransformerOpt implementation. Wiring order matches SPEC section 3.3 and
// the arena stream order of arena_build.cpp exactly.
//
// Profiling (-DFX2_PROF): raw rdtsc (no lfence/rdtscp — the ~67-cycle
// serialized stamp would distort short sections; raw back-to-back stamps
// measure ~10-20 core cycles) section accumulators, one per call site,
// aggregated into the four SPEC section-9 groups at print time and
// overhead-corrected by the measured empty-section delta.

#include "model_opt.h"

#include <immintrin.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>

#include "arena_build.h"
#include "attn.h"
#include "glue.h"
#include "kda.h"
#include "kda_math.h"
#include "qmat_dense.h"
#include "qmat_sparse.h"

// Debug-only component isolation for the naive-vs-opt cross-check (never
// defined in the production build targets): swap the fused KDA step and/or
// the attention kernel for the naive path (bit-exact vs src/model.cpp) to
// attribute divergence per component.
#if defined(FX2_XCHECK_NAIVE_KDA) || defined(FX2_XCHECK_NAIVE_ATTN)
#include "../kernels.h"
#endif

namespace fx2 {
namespace opt {

namespace {
constexpr int V = 205, D = 192, NL = 12, DH = 64, NH = 3, DMLP = 768;
constexpr int WIN = 1024, ROPE_LEN = 131072;
// density thresholds for the sparse column kernels (qmat.h)
constexpr int DOWN_DENSE_NNZ =
    static_cast<int>(QMAT_SPARSE_DENSITY_THRESHOLD * DMLP);  // 729
constexpr int PRIOR_DENSE_NNZ =
    static_cast<int>(QMAT_SPARSE_DENSITY_THRESHOLD * V);  // 194

// beta projection: 3x192 fp32 matvec on xn. Bit-identical to the naive
// fx2::dot_f32(xn, w, 192) (same 8-wide fmadd chain + hsum tree).
inline float dot192(const float* a, const float* b) {
  __m256 acc = _mm256_setzero_ps();
  for (int i = 0; i < 192; i += 8)
    acc = _mm256_fmadd_ps(_mm256_loadu_ps(a + i), _mm256_loadu_ps(b + i), acc);
  return hsum256v(acc);
}
}  // namespace

// ---------------------------------------------------------------------------
// profiling sites
// ---------------------------------------------------------------------------
namespace {

enum PSite : int {
  // group 0: int4 x int8 matmuls (ALL arenas)
  PS_MM_PRIOR = 0,
  PS_MM_KQKV,
  PS_MM_GUP,
  PS_MM_GDN,
  PS_MM_KOP,
  PS_MM_VQKV,
  PS_MM_VOP,
  PS_MM_MLP_UP,
  PS_MM_MLP_DOWN,
  PS_MM_UNEMB,
  // group 1: vanilla attention mechanism
  PS_AT_INSERT,
  PS_AT_STEP,
  // group 2: kimi linear attention mechanism
  PS_KD_BETA,
  PS_KD_STEP,
  // group 3: everything else
  PS_EL_PRIORQ,
  PS_EL_EMBED,
  PS_EL_RESID,
  PS_EL_NQ_KIMI,
  PS_EL_NQ_VAN,
  PS_EL_NQ_MLP,
  PS_EL_NQ_FIN,
  PS_EL_HEADPREP,
  PS_EL_OQ,
  PS_EL_HEAD,
  PS_N
};

#ifdef FX2_PROF
struct PSiteInfo {
  const char* name;
  int group;
};
const PSiteInfo kPSites[PS_N] = {
    {"prior spmv (int4 cols)", 0},
    {"kimi q/k/v proj (27)", 0},
    {"gate up (fg+og, 18)", 0},
    {"gate down (fg+og, 18)", 0},
    {"kimi out proj (9)", 0},
    {"van q/k/v proj (9)", 0},
    {"van out proj (3)", 0},
    {"mlp up + relu2q (12)", 0},
    {"mlp down spmv (12)", 0},
    {"unembed (1)", 0},
    {"kv insert (3)", 1},
    {"attn step qk+sm+pv (3)", 1},
    {"beta matvec (9)", 2},
    {"kda fused step (9)", 2},
    {"prior quant+idx", 3},
    {"embed combine", 3},
    {"resid/skip/tok ops", 3},
    {"norm+quant kimi (9)", 3},
    {"norm+quant van (3)", 3},
    {"norm+quant mlp (12)", 3},
    {"final norm+quant", 3},
    {"head-prep norm/rope/q (3)", 3},
    {"attnout quant (12)", 3},
    {"softcap+softmax head", 3},
};
const char* kGroups[4] = {"int4xint8 matmuls", "vanilla attention mechanism",
                          "kimi (KDA) mechanism", "everything else"};

inline uint64_t prof_rdtsc() {
  unsigned lo, hi;
  asm volatile("rdtsc" : "=a"(lo), "=d"(hi)::"memory");
  return (static_cast<uint64_t>(hi) << 32) | lo;
}
uint64_t g_pacc[PS_N] = {};
uint64_t g_pcalls[PS_N] = {};
struct PScope {
  int s;
  uint64_t t0;
  explicit PScope(int s_) : s(s_), t0(prof_rdtsc()) {}
  ~PScope() {
    g_pacc[s] += prof_rdtsc() - t0;
    g_pcalls[s]++;
  }
};
#define PSCOPE(site) PScope pscope_(site)
#else
#define PSCOPE(site) \
  do {               \
  } while (0)
#endif

}  // namespace

void prof_reset() {
#ifdef FX2_PROF
  std::memset(g_pacc, 0, sizeof(g_pacc));
  std::memset(g_pcalls, 0, sizeof(g_pcalls));
#endif
}

bool prof_enabled() {
#ifdef FX2_PROF
  return true;
#else
  return false;
#endif
}

void prof_print(double tsc_to_core, long tokens) {
#ifndef FX2_PROF
  (void)tsc_to_core;
  (void)tokens;
  std::printf("prof: not compiled in (build with -DFX2_PROF)\n");
#else
  // empty-section overhead: median back-to-back raw-rdtsc delta
  const int NS = 4001;
  std::vector<uint64_t> st(NS);
  for (int i = 0; i < NS; i++) st[i] = prof_rdtsc();
  std::vector<double> dd(NS - 1);
  for (int i = 0; i + 1 < NS; i++) dd[i] = double(st[i + 1] - st[i]);
  std::nth_element(dd.begin(), dd.begin() + (NS - 1) / 2, dd.end());
  const double stamp_ticks = dd[(NS - 1) / 2];
  std::printf("\n== per-part profile (raw rdtsc, overhead-corrected by %.1f "
              "ticks/section = %.1f core cyc) ==\n",
              stamp_ticks, stamp_ticks * tsc_to_core);
  double gcyc[4] = {}, gcalls[4] = {};
  double site_cyc[PS_N];
  double total = 0;
  for (int s = 0; s < PS_N; s++) {
    double ticks = double(g_pacc[s]) - double(g_pcalls[s]) * stamp_ticks;
    if (ticks < 0) ticks = 0;
    site_cyc[s] = ticks * tsc_to_core / double(tokens > 0 ? tokens : 1);
    gcyc[kPSites[s].group] += site_cyc[s];
    gcalls[kPSites[s].group] += double(g_pcalls[s]);
    total += site_cyc[s];
  }
  std::printf("%-34s %12s %6s %9s\n", "group", "cyc/token", "%", "calls/tok");
  for (int g = 0; g < 4; g++)
    std::printf("%-34s %12.0f %5.1f%% %9.1f\n", kGroups[g], gcyc[g],
                100.0 * gcyc[g] / total,
                gcalls[g] / double(tokens > 0 ? tokens : 1));
  std::printf("%-34s %12.0f %5.1f%%\n", "TOTAL (instrumented sections)", total,
              100.0);
  std::printf("\n%-34s %12s %6s %9s\n", "  site", "cyc/token", "%",
              "calls/tok");
  for (int g = 0; g < 4; g++) {
    std::printf("  -- %s --\n", kGroups[g]);
    for (int s = 0; s < PS_N; s++) {
      if (kPSites[s].group != g) continue;
      std::printf("  %-32s %12.0f %5.1f%% %9.1f\n", kPSites[s].name,
                  site_cyc[s], 100.0 * site_cyc[s] / total,
                  double(g_pcalls[s]) / double(tokens > 0 ? tokens : 1));
    }
  }
#endif
}

// ---------------------------------------------------------------------------
// the model
// ---------------------------------------------------------------------------
struct TransformerOptImpl {
  OptModel M;
  AttnKind kind;

  // streaming state (hugepage pool: KDA states, then KV caches)
  HugeBuf spool;
  KdaState* kst = nullptr;   // [9]
  AttnKVF32* kvf = nullptr;  // [3] iff kind == KVF32
  AttnKV* kvi = nullptr;     // [3] iff kind == KVI8
  int64_t t = 0;
  int64_t rope_off = 0;

#ifdef FX2_XCHECK_NAIVE_KDA
  struct NaiveKst {
    alignas(64) float S[NH][DH * DH];
    alignas(64) float hist[3][3][D];
  };
  std::vector<NaiveKst> nkst = std::vector<NaiveKst>(9);
#endif
#ifdef FX2_XCHECK_NAIVE_ATTN
  struct NaiveVst {
    alignas(64) int8_t kring[WIN][D];
    alignas(64) int8_t vring[WIN][D];
  };
  std::vector<NaiveVst> nvst = std::vector<NaiveVst>(3);
#endif

  // per-token skip stack (written by layers 0..5, read by 6..11 of the SAME
  // token) — transient within step
  alignas(64) float skip_store[6][D] = {};

  // scratch
  alignas(64) float x[D] = {}, xn[D] = {}, yb[D] = {};
  alignas(64) uint8_t q5[5 * D] = {};  // up to 5 biased-u8 copies of xn
  alignas(64) uint8_t q64b[DH] = {};
  alignas(64) float bq[D] = {}, bk[D] = {}, bv[D] = {};
  alignas(64) float graw[D] = {}, og192[D] = {}, gn[D] = {};
  alignas(32) float braw[8] = {};
  alignas(64) float qf[D] = {}, kf[D] = {}, vf[D] = {}, pre[D] = {};
  alignas(64) int8_t qq[D] = {}, kk[D] = {}, vv[D] = {};
  alignas(64) uint8_t q768[DMLP] = {};
  alignas(64) uint16_t idx768[DMLP + 16] = {};
  alignas(64) float prior_f32[208] = {};
  alignas(64) uint8_t q8p[224] = {};      // 224 = 205 rounded to 32
  alignas(64) uint16_t idxp[224 + 16] = {};
  alignas(64) float logits[208] = {};
  alignas(64) float probs208[208] = {};
  alignas(32) float sfall[32] = {}, cfall[32] = {};  // rope fallback row

  explicit TransformerOptImpl(const char* path, AttnKind k) : kind(k) {
    M.load(path);
    const size_t kda_sz = sizeof(KdaState) * 9;
    const size_t kv_sz =
        (kind == AttnKind::KVF32 ? sizeof(AttnKVF32) : sizeof(AttnKV)) * 3;
    spool.alloc(kda_sz + kv_sz);
    kst = reinterpret_cast<KdaState*>(spool.p);
    if (kind == AttnKind::KVF32)
      kvf = reinterpret_cast<AttnKVF32*>(spool.p + kda_sz);
    else
      kvi = reinterpret_cast<AttnKV*>(spool.p + kda_sz);
    for (int i = 0; i < 9; i++) kda_layer_reset(kst[i]);
  }

  void begin(int64_t rope_position_offset) {
    for (int i = 0; i < 9; i++) kda_layer_reset(kst[i]);
#ifdef FX2_XCHECK_NAIVE_KDA
    std::memset(nkst.data(), 0, sizeof(NaiveKst) * 9);
#endif
    t = 0;  // invalidates the KV rings (validity is [0, t] within an article)
    rope_off = rope_position_offset;
  }

  void kimi_layer(int ki) {
    KimiArenas& L = M.kimi[ki];
    {
      PSCOPE(PS_EL_NQ_KIMI);
      const float s5[5] = {L.qp.s_act, L.kp.s_act, L.vp.s_act, L.fg_up.s_act,
                           L.og_up.s_act};
      rms_norm_quant192_multi(x, xn, s5, 5, q5);
    }
    {
      PSCOPE(PS_MM_KQKV);
      qgemv_f32(L.qp.m, q5, bq);
      qgemv_f32(L.kp.m, q5 + D, bk);
      qgemv_f32(L.vp.m, q5 + 2 * D, bv);
    }
    {
      PSCOPE(PS_MM_GUP);
      qgemv_quant_bias(L.fg_up.m, q5 + 3 * D, L.fg_down.s_act, q64b);
    }
    {
      PSCOPE(PS_MM_GDN);
      qgemv_f32(L.fg_down.m, q64b, graw);
    }
    {
      PSCOPE(PS_MM_GUP);
      qgemv_quant_bias(L.og_up.m, q5 + 4 * D, L.og_down.s_act, q64b);
    }
    {
      PSCOPE(PS_MM_GDN);
      qgemv_f32(L.og_down.m, q64b, og192);
    }
    {
      PSCOPE(PS_KD_BETA);
      for (int h = 0; h < NH; h++)
        braw[h] = dot192(xn, L.beta_w + size_t(h) * D);
    }
    {
      PSCOPE(PS_KD_STEP);
#ifdef FX2_XCHECK_NAIVE_KDA
      // naive scalar kimi path (bit-exact vs src/model.cpp kimi_attention)
      NaiveKst& st = nkst[ki];
      alignas(32) float cq[D], ck[D], cv[D], o192[D];
      conv4_silu(L.kw.conv_w[0], st.hist[0][0], st.hist[0][1], st.hist[0][2],
                 bq, cq, D);
      conv4_silu(L.kw.conv_w[1], st.hist[1][0], st.hist[1][1], st.hist[1][2],
                 bk, ck, D);
      conv4_silu(L.kw.conv_w[2], st.hist[2][0], st.hist[2][1], st.hist[2][2],
                 bv, cv, D);
      const float* newest[3] = {bq, bk, bv};
      for (int c = 0; c < 3; c++) {
        std::memmove(st.hist[c][0], st.hist[c][1], sizeof(float) * 2 * D);
        std::memcpy(st.hist[c][2], newest[c], sizeof(float) * D);
      }
      for (int h = 0; h < NH; h++)
        kda_head_step(st.S[h], cq + h * DH, ck + h * DH, cv + h * DH,
                      graw + h * DH, L.kw.dt_bias + h * DH, L.kw.a_neg[h],
                      sigmoid1f(braw[h]), o192 + h * DH);
      for (int h = 0; h < NH; h++)
        gated_rms_norm64(o192 + h * DH, og192 + h * DH, L.kw.gn_w,
                         gn + h * DH);
#else
      kda_layer_step(L.kw, kst[ki], bq, bk, bv, graw, og192, braw, gn);
#endif
    }
    {
      PSCOPE(PS_EL_OQ);
      quant192_u8(gn, L.op.s_act, q5);
    }
    {
      PSCOPE(PS_MM_KOP);
      qgemv_add(L.op.m, q5, x);
    }
  }

  void van_layer(int vi) {
    VanArenas& L = M.van[vi];
    {
      PSCOPE(PS_EL_NQ_VAN);
      const float s3[3] = {L.qp.s_act, L.kp.s_act, L.vp.s_act};
      rms_norm_quant192_x3(x, xn, s3, q5, q5 + D, q5 + 2 * D);
    }
    {
      PSCOPE(PS_MM_VQKV);
      qgemv_f32(L.qp.m, q5, qf);
      qgemv_f32(L.kp.m, q5 + D, kf);
      qgemv_f32(L.vp.m, q5 + 2 * D, vf);
    }
    {
      PSCOPE(PS_EL_HEADPREP);
      for (int h = 0; h < NH; h++) rms_norm64(qf + h * DH, qf + h * DH);
      for (int h = 0; h < NH; h++) rms_norm64(kf + h * DH, kf + h * DH);
      const int64_t pos = rope_off + t;
      const float *sp, *cp;
      if (pos < ROPE_LEN) {
        sp = M.rope_sin.data() + size_t(pos) * 32;
        cp = M.rope_cos.data() + size_t(pos) * 32;
      } else {  // beyond the shipped table: libm fallback (same as naive)
        const float fpos = static_cast<float>(pos);
        for (int i = 0; i < 32; i++) {
          const float ang = fpos * M.inv_freq[i];
          sfall[i] = std::sin(ang);
          cfall[i] = std::cos(ang);
        }
        sp = sfall;
        cp = cfall;
      }
      rope_apply_192(qf, sp, cp);
      rope_apply_192(kf, sp, cp);
      for (int h = 0; h < NH; h++) {
        quant64_i8(qf + h * DH, L.sq[h], qq + h * DH);
        quant64_i8(kf + h * DH, L.sk[h], kk + h * DH);
        quant64_i8(vf + h * DH, L.sv[h], vv + h * DH);
      }
    }
    const int slot = static_cast<int>(t % WIN);
    const int64_t n = t + 1;
#ifdef FX2_EXP_KPF
    {  // experiment: warm the first 2KB of each head's K stream (the scan's
       // software prefetch runs +2KB ahead, so the first 2KB are cold-start
       // demand misses paced by the QK compute)
      const char* kb = kind == AttnKind::KVF32
                           ? reinterpret_cast<const char*>(kvf[vi].k)
                           : reinterpret_cast<const char*>(kvi[vi].k);
      for (int h = 0; h < 3; h++)
        for (int off = 0; off < 2048; off += 64)
          _mm_prefetch(kb + h * (ATTN_NBLK * 32 * ATTN_DH) + off, _MM_HINT_T0);
    }
#endif
#ifdef FX2_XCHECK_NAIVE_ATTN
    {
      NaiveVst& st = nvst[vi];
      std::memcpy(st.kring[slot], kk, D);
      std::memcpy(st.vring[slot], vv, D);
      if (n < WIN)
        fx2::attention_step_var(qq, st.kring[0], st.vring[0], L.coef, L.sv,
                                static_cast<int>(n), pre, 0.0f);
      else
        fx2::attention_step_fixed(qq, st.kring[0], st.vring[0], L.coef, L.sv,
                                  pre, 0.0f);
    }
#else
    if (kind == AttnKind::KVF32) {
      {
        PSCOPE(PS_AT_INSERT);
        attn_kv_insert(kvf[vi], slot, kk, vv);
      }
      {
        PSCOPE(PS_AT_STEP);
        if (n < WIN)
          attn_step_var(kvf[vi], qq, L.coef, L.sv, static_cast<int>(n), pre,
                        0.0f);
        else
          attn_step_fixed(kvf[vi], qq, L.coef, L.sv, pre, 0.0f);
      }
    } else {
      {
        PSCOPE(PS_AT_INSERT);
        attn_kv_insert(kvi[vi], slot, kk, vv);
      }
      {
        PSCOPE(PS_AT_STEP);
        if (n < WIN)
          attn_step_var(kvi[vi], qq, L.coef, L.sv, static_cast<int>(n), pre,
                        0.0f);
        else
          attn_step_fixed(kvi[vi], qq, L.coef, L.sv, pre, 0.0f);
      }
    }
#endif
    {
      PSCOPE(PS_EL_OQ);
      quant192_u8(pre, L.op.s_act, q5);
    }
    {
      PSCOPE(PS_MM_VOP);
      qgemv_add(L.op.m, q5, x);
    }
  }

  void mlp_block(int l) {
    MlpArenas& mm = M.mlp[l];
    {
      PSCOPE(PS_EL_NQ_MLP);
      rms_norm_quant192(x, xn, mm.up.s_act, q5);
    }
    int nnz;
    {
      PSCOPE(PS_MM_MLP_UP);
      nnz = qgemv_relu2q(mm.up.m, q5, mm.down_s_act, q768, idx768);
    }
    {
      PSCOPE(PS_MM_MLP_DOWN);
      if (nnz > DOWN_DENSE_NNZ)
        qsparse4_dense_add(mm.down, q768, x);
      else
        qsparse4_add(mm.down, q768, idx768, nnz, x);
    }
  }

  // prior must be the cap-208 internal buffer with pads [205..208) zeroed
  void step(uint8_t token, float* probs_out) {
    const float* tok = M.tok_table + size_t(token) * D;
    int nnzp;
    {
      PSCOPE(PS_EL_PRIORQ);
      prior_quant_raw(prior_f32, M.prior_s_act, q8p);  // raw u8; q8p[208..224)=0
      nnzp = qsparse_make_idx(q8p, V, idxp);
      const uint16_t fillv = nnzp ? idxp[nnzp - 1] : 0;
      for (int k = nnzp; k < nnzp + 8; k++) idxp[k] = fillv;
    }
    {
      PSCOPE(PS_MM_PRIOR);
      if (nnzp > PRIOR_DENSE_NNZ)
        qsparse4_dense_f32(M.prior, q8p, yb);
      else
        qsparse4_f32(M.prior, q8p, idxp, nnzp, yb);
    }
    {
      PSCOPE(PS_EL_EMBED);
      embed_combine192(tok, yb, x);  // x0 = tok_row + rms_norm(prior_y)
    }

    for (int l = 0; l < NL; l++) {
      {
        PSCOPE(PS_EL_RESID);
        // skip-add BEFORE the token connection (SPEC 3.3); pairing 11-l
        if (l >= 6) add_scaled192(x, M.skip_w[l - 6], skip_store[11 - l]);
        axpby_tok192(M.rsc[l], x, M.tec[l], tok);
      }
      if (OptModel::KIMI_L[l])
        kimi_layer(M.layer2kimi[l]);
      else
        van_layer(M.layer2van[l]);
      mlp_block(l);
      if (l < 6) {
        PSCOPE(PS_EL_RESID);
        std::memcpy(skip_store[l], x, sizeof(float) * D);  // push AFTER block
      }
    }

    {
      PSCOPE(PS_EL_NQ_FIN);
      rms_norm_quant192(x, xn, M.unembed.s_act, q5);
    }
    {
      PSCOPE(PS_MM_UNEMB);
      qgemv_f32(M.unembed.m, q5, logits);  // rows_padded 208
    }
    {
      PSCOPE(PS_EL_HEAD);
      head_softcap_softmax(logits, probs208);
      std::memcpy(probs_out, probs208, sizeof(float) * V);
    }
    t++;
  }
};

TransformerOpt::TransformerOpt(const char* weights_path, AttnKind attn)
    : impl(new TransformerOptImpl(weights_path, attn)) {}

TransformerOpt::~TransformerOpt() = default;

void TransformerOpt::begin_article(int64_t rope_position_offset) {
  impl->begin(rope_position_offset);
}

void TransformerOpt::step(uint8_t token, const uint16_t* prior_f16,
                          float* probs_out) {
  prior_f16_to_f32(prior_f16, impl->prior_f32);  // exact; pads zeroed
  impl->step(token, probs_out);
}

void TransformerOpt::step(uint8_t token, const float* prior205,
                          float* probs_out) {
  std::memcpy(impl->prior_f32, prior205, sizeof(float) * V);
  impl->prior_f32[205] = impl->prior_f32[206] = impl->prior_f32[207] = 0.0f;
  impl->step(token, probs_out);
}

const float* TransformerOpt::last_logits() const { return impl->logits; }

AttnKind TransformerOpt::attn_kind() const { return impl->kind; }

}  // namespace opt
}  // namespace fx2
