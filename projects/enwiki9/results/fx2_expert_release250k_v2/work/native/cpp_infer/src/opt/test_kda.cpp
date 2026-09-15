// test_kda: correctness/accuracy validation of the optimized KDA path
// (src/opt/kda.cpp) against the naive reference (src/kernels.cpp) and the
// Python dumps.
//
// Sections (all run by default):
//   [math]  elementary-function accuracy tables, 1e7 random points per real
//           input range (g_raw in [-30,30] (+dt_bias -> [-34,31]),
//           og in [-20,20], conv pre-act in [-20,20]); max ulp vs
//           double-precision truth and vs the naive libm float path.
//   [sweep] bit-exactness of the AVX2 state sweep vs a pinned-rounding
//           scalar reference (mul-round + std::fmaf, the exact naive
//           arithmetic); ONEFIVE must be bit-identical, TWOPASS is allowed
//           its documented ~1 ulp r-path rounding change.
//   [drift] 10000-step random sequences through 9 layers (article resets
//           every ~700 steps): optimized fused layer vs the naive
//           conv4_silu + kda_head_step + gated_rms_norm64 composition;
//           gate: max rel divergence (over |ref| > 1e-2) <= 1e-4.
//   [dumps] article4 teacher-forced dump validation for all 9 kimi layers:
//           the projection front-end is replicated from weights.bin
//           (quantize_i8 + qmatvec), block inputs are the reference dump
//           rows; conv outs / g_raw / out_gate / beta_raw are gated at
//           clean-upstream level (smooth rel-RMS <= 1e-4, knife-edge flip
//           fraction <= 1e-3, like test_components); kda_out and
//           gated_norm_out carry the reference's own tf32 noise
//           (~2.3e-4 max abs per KIMI_SEMANTICS section 6) -> rel-RMS gate 3%.
//
// Compiled with -ffp-contract=off: scalar glue in THIS file has pinned
// rounding; intended fusions are written as std::fmaf.
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <random>
#include <string>
#include <vector>

#include "kda.h"
#include "kda_math.h"
#include "kernels.h"
#include "npy.h"
#include "testdata.h"
#include "weights_io.h"

using fx2::opt::KdaDebug;
using fx2::opt::KdaState;
using fx2::opt::KdaSweep;
using fx2::opt::KdaWeights;

namespace {

bool g_fail = false;
void gate(bool ok, const char* what, double val, double lim) {
  if (!ok) {
    std::printf("  ** GATE FAIL: %s = %.3e (limit %.3e)\n", what, val, lim);
    g_fail = true;
  }
}

// ---------------------------------------------------------------------------
// [math] elementary function accuracy
// ---------------------------------------------------------------------------

double ulp_dist(double a, double ref) {
  float rf = static_cast<float>(ref);
  float rfa = std::fabs(rf);
  double ulp = static_cast<double>(std::nextafterf(rfa, INFINITY)) -
               static_cast<double>(rfa);
  if (!(ulp > 0)) return 0.0;  // inf edge
  return std::fabs(a - ref) / ulp;
}

struct FnAcc {
  double max_ulp_d = 0, arg_ulp_d = 0;   // vs double truth
  double max_rel_d = 0;
  double max_ulp_f = 0, arg_ulp_f = 0;   // vs naive float path
  double max_abs_f = 0;
};

template <typename VF, typename RF, typename RD>
FnAcc measure_fn(double lo, double hi, long n, VF vecf, RF reff, RD refd,
                 uint32_t seed) {
  std::mt19937 rng(seed);
  std::uniform_real_distribution<double> U(lo, hi);
  FnAcc a;
  alignas(32) float in[8], out[8];
  for (long b = 0; b < n; b += 8) {
    for (int l = 0; l < 8; l++) in[l] = static_cast<float>(U(rng));
    _mm256_store_ps(out, vecf(_mm256_load_ps(in)));
    for (int l = 0; l < 8; l++) {
      double mine = out[l];
      double rd = refd(in[l]);
      double du = ulp_dist(mine, rd);
      if (du > a.max_ulp_d) {
        a.max_ulp_d = du;
        a.arg_ulp_d = in[l];
      }
      if (rd != 0.0) {
        double rel = std::fabs(mine - rd) / std::fabs(rd);
        if (rel > a.max_rel_d) a.max_rel_d = rel;
      }
      float rf = reff(in[l]);
      double fu = ulp_dist(mine, rf);
      if (fu > a.max_ulp_f) {
        a.max_ulp_f = fu;
        a.arg_ulp_f = in[l];
      }
      a.max_abs_f = std::max(a.max_abs_f, std::fabs(mine - double(rf)));
    }
  }
  return a;
}

void print_row(const char* name, const char* range, const FnAcc& a) {
  std::printf(
      "  %-22s %-12s ulp-vs-dbl %6.3f (@%+9.4f)  rel %.2e | ulp-vs-libm "
      "%6.3f  abs %.2e\n",
      name, range, a.max_ulp_d, a.arg_ulp_d, a.max_rel_d, a.max_ulp_f,
      a.max_abs_f);
}

double softplus20_d(double x) { return x > 20.0 ? x : std::log1p(std::exp(x)); }

void section_math(long npts) {
  std::printf("[math] accuracy on %ld random points per range "
              "(vec vs double truth / vs naive libm float path)\n", npts);

  auto acc_exp = measure_fn(
      -30.0, 30.0, npts, [](__m256 x) { return fx2::opt::exp_full8(x); },
      [](float x) { return std::exp(x); },
      [](double x) { return std::exp(x); }, 11);
  print_row("exp_full8", "[-30,30]", acc_exp);
  // canonical Estrin exp256 measures 1.03 ulp per-binade (vec_math.h)
  gate(acc_exp.max_ulp_d <= 1.1, "exp_full8 ulp", acc_exp.max_ulp_d, 1.1);

  // subnormal tail: naive expf underflows gradually; so do we
  {
    std::mt19937 rng(12);
    std::uniform_real_distribution<double> U(-104.0, -80.0);
    double max_absd = 0, max_q = 0;
    alignas(32) float in[8], out[8];
    for (long b = 0; b < npts / 8; b += 8) {
      for (int l = 0; l < 8; l++) in[l] = static_cast<float>(U(rng));
      _mm256_store_ps(out, fx2::opt::exp_full8(_mm256_load_ps(in)));
      for (int l = 0; l < 8; l++) {
        double rd = std::exp(static_cast<double>(in[l]));
        max_absd = std::max(max_absd, std::fabs(out[l] - rd));
        max_q = std::max(max_q, ulp_dist(out[l], rd));
      }
    }
    std::printf(
        "  %-22s %-12s max abs vs dbl %.3e, max subnormal-quanta %.1f\n",
        "exp_full8 (deep tail)", "[-104,-80]", max_absd, max_q);
    gate(max_absd <= 1.5e-38, "exp tail abs", max_absd, 1.5e-38);
  }

  auto acc_sp = measure_fn(
      -34.0, 31.0, npts, [](__m256 x) { return fx2::softplus256_ps(x); },
      [](float x) { return fx2::softplus20f(x); }, softplus20_d, 13);
  print_row("softplus256 (thr 20)", "[-34,31]", acc_sp);
  gate(acc_sp.max_ulp_d <= 3.0, "softplus ulp", acc_sp.max_ulp_d, 3.0);

  auto acc_sig = measure_fn(
      -20.0, 20.0, npts, [](__m256 x) { return fx2::sigmoid256_ps(x); },
      [](float x) { return fx2::sigmoid1f(x); },
      [](double x) { return 1.0 / (1.0 + std::exp(-x)); }, 14);
  print_row("sigmoid256", "[-20,20]", acc_sig);
  gate(acc_sig.max_ulp_d <= 2.5, "sigmoid ulp", acc_sig.max_ulp_d, 2.5);

  auto acc_silu = measure_fn(
      -20.0, 20.0, npts, [](__m256 x) { return fx2::silu256_ps(x); },
      [](float x) { return fx2::siluf(x); },
      [](double x) { return x / (1.0 + std::exp(-x)); }, 15);
  print_row("silu256", "[-20,20]", acc_silu);
  gate(acc_silu.max_ulp_d <= 3.0, "silu ulp", acc_silu.max_ulp_d, 3.0);

  // full decay chains for the three real per-head rates
  const float rates[3] = {1.567f, 2.645f, 3.129f};  // exp(A_log)
  for (int h = 0; h < 3; h++) {
    float an = -rates[h];
    auto acc_dec = measure_fn(
        -34.0, 31.0, npts / 2,
        [an](__m256 x) {
          return fx2::opt::exp_full8(_mm256_mul_ps(
              _mm256_set1_ps(an), fx2::softplus256_ps(x)));
        },
        [an](float x) { return std::exp(an * fx2::softplus20f(x)); },
        [an](double x) {
          return std::exp(static_cast<double>(an) * softplus20_d(x));
        },
        16 + h);
    char nm[32], rg[16];
    std::snprintf(nm, sizeof nm, "decay (a=-%.3f)", rates[h]);
    std::snprintf(rg, sizeof rg, "[-34,31]");
    print_row(nm, rg, acc_dec);
    // decay in (0,1]: gate on absolute agreement with the naive float chain
    // (ulp-vs-double blows up only where |result| < 1e-38, physically zero)
    gate(acc_dec.max_abs_f <= 3e-7, "decay abs vs naive", acc_dec.max_abs_f,
         3e-7);
  }
  std::printf("\n");
}

// ---------------------------------------------------------------------------
// [sweep] bit-exactness vs pinned-rounding scalar reference
// ---------------------------------------------------------------------------

// The exact naive arithmetic of src/kernels.cpp kda_head_step's state loops
// (as compiled: mul-round for the decay, fma for the accumulations), with
// every rounding pinned explicitly.
void ref_sweep(float* S, const float* decay, const float* kn, const float* v,
               float beta, const float* qs, float* o) {
  float r[64];
  for (int j = 0; j < 64; j++) r[j] = 0.0f;
  for (int i = 0; i < 64; i++) {
    float d = decay[i], kni = kn[i];
    float* row = S + 64 * i;
    for (int j = 0; j < 64; j++) {
      float a = row[j] * d;
      row[j] = a;
      r[j] = std::fmaf(kni, a, r[j]);
    }
  }
  float u[64];
  for (int j = 0; j < 64; j++) u[j] = beta * (v[j] - r[j]);
  for (int j = 0; j < 64; j++) o[j] = 0.0f;
  for (int i = 0; i < 64; i++) {
    float kni = kn[i], qi = qs[i];
    float* row = S + 64 * i;
    for (int j = 0; j < 64; j++) {
      float a = std::fmaf(kni, u[j], row[j]);
      row[j] = a;
      o[j] = std::fmaf(qi, a, o[j]);
    }
  }
}

void section_sweep() {
  std::printf("[sweep] AVX2 state sweep vs pinned-rounding scalar reference "
              "(1000 chained steps x 4 states)\n");
  std::mt19937 rng(77);
  std::normal_distribution<float> N(0.0f, 1.0f);
  std::uniform_real_distribution<float> U01(0.0f, 1.0f);

  alignas(64) static float Sa[4096], Sb[4096], Sc[4096];
  alignas(32) float decay[64], kn[64], v[64], qs[64], oa[64], ob[64], oc[64];

  long n15_bits = 0, n2p_bits = 0;
  double max2p_S = 0, max2p_o = 0, max2p_S_ulp = 0;
  for (int trial = 0; trial < 4; trial++) {
    for (int i = 0; i < 4096; i++) Sa[i] = 0.25f * N(rng);
    std::memcpy(Sb, Sa, sizeof(Sa));
    std::memcpy(Sc, Sa, sizeof(Sa));
    for (int step = 0; step < 1000; step++) {
      // realistic-ish sweeps: decays across the whole (0,1] range incl. tiny
      for (int i = 0; i < 64; i++) {
        float sp = std::log1p(std::exp(N(rng) * 1.4f + 0.5f));
        decay[i] = std::exp(-2.6f * sp);
        kn[i] = 0.125f * N(rng);
        qs[i] = 0.015625f * N(rng);
        v[i] = N(rng);
      }
      float beta = U01(rng);
      ref_sweep(Sa, decay, kn, v, beta, qs, oa);
      fx2::opt::kda_sweep_head(Sb, decay, kn, v, beta, qs, ob, nullptr,
                               KdaSweep::ONEFIVE);
      fx2::opt::kda_sweep_head(Sc, decay, kn, v, beta, qs, oc, nullptr,
                               KdaSweep::TWOPASS);
      n15_bits += std::memcmp(Sa, Sb, sizeof(Sa)) != 0 ||
                  std::memcmp(oa, ob, sizeof(oa)) != 0;
      if (std::memcmp(Sa, Sc, sizeof(Sa)) != 0 ||
          std::memcmp(oa, oc, sizeof(oa)) != 0)
        n2p_bits++;
      for (int i = 0; i < 4096; i++) {
        max2p_S = std::max(max2p_S, (double)std::fabs(Sc[i] - Sa[i]));
        max2p_S_ulp = std::max(max2p_S_ulp, ulp_dist(Sc[i], Sa[i]));
      }
      for (int j = 0; j < 64; j++)
        max2p_o = std::max(max2p_o, (double)std::fabs(oc[j] - oa[j]));
      // keep the TWOPASS state from drifting the comparison: resync
      std::memcpy(Sc, Sa, sizeof(Sa));
    }
  }
  std::printf("  ONEFIVE: %ld/4000 steps with any bit difference (must be 0)\n",
              n15_bits);
  gate(n15_bits == 0, "ONEFIVE bit-exact steps", (double)n15_bits, 0);
  std::printf("  TWOPASS: %ld/4000 steps differing; max |dS| %.3e "
              "(%.1f ulp), max |do| %.3e (documented r-path rounding)\n",
              n2p_bits, max2p_S, max2p_S_ulp, max2p_o);
  gate(max2p_S <= 1e-5, "TWOPASS state abs", max2p_S, 1e-5);
  std::printf("\n");
}

// ---------------------------------------------------------------------------
// [drift] naive full-layer path vs fused layer over long random sequences
// ---------------------------------------------------------------------------

struct NaiveState {
  alignas(64) float S[3][4096];
  alignas(64) float hist[3][3][192];
};

// exact composition of src/model.cpp kimi_attention from conv onward
void naive_layer_step(const KdaWeights& w, NaiveState& st, const float* bq,
                      const float* bk, const float* bv, const float* graw,
                      const float* og, const float* braw, float* out,
                      float* kda_out) {
  alignas(32) float cq[192], ck[192], cv[192], o192[192];
  fx2::conv4_silu(w.conv_w[0], st.hist[0][0], st.hist[0][1], st.hist[0][2],
                  bq, cq, 192);
  fx2::conv4_silu(w.conv_w[1], st.hist[1][0], st.hist[1][1], st.hist[1][2],
                  bk, ck, 192);
  fx2::conv4_silu(w.conv_w[2], st.hist[2][0], st.hist[2][1], st.hist[2][2],
                  bv, cv, 192);
  const float* newest[3] = {bq, bk, bv};
  for (int c = 0; c < 3; c++) {
    std::memmove(st.hist[c][0], st.hist[c][1], sizeof(float) * 2 * 192);
    std::memcpy(st.hist[c][2], newest[c], sizeof(float) * 192);
  }
  for (int h = 0; h < 3; h++)
    fx2::kda_head_step(st.S[h], cq + h * 64, ck + h * 64, cv + h * 64,
                       graw + h * 64, w.dt_bias + h * 64, w.a_neg[h],
                       fx2::sigmoid1f(braw[h]), o192 + h * 64);
  if (kda_out) std::memcpy(kda_out, o192, sizeof(o192));
  for (int h = 0; h < 3; h++)
    fx2::gated_rms_norm64(o192 + h * 64, og + h * 64, w.gn_w, out + h * 64);
}

struct DriftW {
  std::vector<float> conv[3], dt_bias, gn_w;
  KdaWeights kw;
};

void section_drift(long steps) {
  std::printf("[drift] fused layer vs naive path: 9 layers, %ld steps, "
              "article resets every ~700\n", steps);
  std::mt19937 rng(2024);
  std::normal_distribution<float> N(0.0f, 1.0f);
  std::uniform_real_distribution<float> U(0.0f, 1.0f);

  const float rates[3] = {1.567f, 2.645f, 3.129f};
  std::vector<DriftW> W(9);
  for (int l = 0; l < 9; l++) {
    for (int c = 0; c < 3; c++) {
      W[l].conv[c].resize(4 * 192);
      for (auto& x : W[l].conv[c]) x = 0.4f * N(rng);
    }
    W[l].dt_bias.resize(192);
    for (auto& x : W[l].dt_bias) x = -3.26f + 4.1f * U(rng);
    W[l].gn_w.resize(64);
    for (auto& x : W[l].gn_w) x = 0.5f + U(rng);
    for (int c = 0; c < 3; c++) W[l].kw.conv_w[c] = W[l].conv[c].data();
    W[l].kw.dt_bias = W[l].dt_bias.data();
    W[l].kw.gn_w = W[l].gn_w.data();
    for (int h = 0; h < 3; h++)
      W[l].kw.a_neg[h] = -rates[h] * (0.9f + 0.2f * U(rng));
  }

  std::vector<KdaState> ost(9);
  std::vector<NaiveState> nst(9);
  for (int l = 0; l < 9; l++) {
    fx2::opt::kda_layer_reset(ost[l]);
    std::memset(&nst[l], 0, sizeof(NaiveState));
  }

  alignas(32) float bq[192], bk[192], bv[192], graw[192], og[192], braw[3];
  alignas(32) float on[192], oo[192], kn_[192], ko[192];
  double omax_abs = 0, omax_rel2 = 0, omax_rel4 = 0, omax_rel1 = 0;
  double kmax_abs = 0, kmax_rel2 = 0;
  double smax_abs = 0, smax_rel2 = 0;
  long next_reset = 640 + (long)(rng() % 128), scmp = 0;

  for (long t = 0; t < steps; t++) {
    if (t == next_reset) {
      for (int l = 0; l < 9; l++) {
        fx2::opt::kda_layer_reset(ost[l]);
        std::memset(&nst[l], 0, sizeof(NaiveState));
      }
      next_reset += 640 + (long)(rng() % 128);
    }
    for (int l = 0; l < 9; l++) {
      for (int i = 0; i < 192; i++) {
        bq[i] = N(rng);
        bk[i] = N(rng);
        bv[i] = N(rng);
        graw[i] = 1.4f * N(rng);
        og[i] = 3.0f * N(rng);
      }
      for (int h = 0; h < 3; h++) braw[h] = N(rng);
      naive_layer_step(W[l].kw, nst[l], bq, bk, bv, graw, og, braw, on, kn_);
      KdaDebug dbg;
      dbg.kda_out = ko;
      fx2::opt::kda_layer_step(W[l].kw, ost[l], bq, bk, bv, graw, og, braw,
                               oo, &dbg);
      for (int i = 0; i < 192; i++) {
        double d = std::fabs((double)oo[i] - on[i]);
        omax_abs = std::max(omax_abs, d);
        if (std::fabs(on[i]) > 1e-1) omax_rel1 = std::max(omax_rel1, d / std::fabs(on[i]));
        if (std::fabs(on[i]) > 1e-2) omax_rel2 = std::max(omax_rel2, d / std::fabs(on[i]));
        if (std::fabs(on[i]) > 1e-4) omax_rel4 = std::max(omax_rel4, d / std::fabs(on[i]));
        double dk = std::fabs((double)ko[i] - kn_[i]);
        kmax_abs = std::max(kmax_abs, dk);
        if (std::fabs(kn_[i]) > 1e-2) kmax_rel2 = std::max(kmax_rel2, dk / std::fabs(kn_[i]));
      }
      if (t % 33 == 0 || t + 1 == next_reset) {
        scmp++;
        for (int h = 0; h < 3; h++)
          for (int i = 0; i < 4096; i++) {
            double d = std::fabs((double)ost[l].S[h][i] - nst[l].S[h][i]);
            smax_abs = std::max(smax_abs, d);
            if (std::fabs(nst[l].S[h][i]) > 1e-2)
              smax_rel2 = std::max(smax_rel2, d / std::fabs(nst[l].S[h][i]));
          }
      }
    }
  }
  std::printf("  out (post gated-norm): max abs %.3e, max rel %.3e (|ref|>1e-1), "
              "%.3e (|ref|>1e-2), %.3e (|ref|>1e-4)\n",
              omax_abs, omax_rel1, omax_rel2, omax_rel4);
  std::printf("  kda raw out:           max abs %.3e, max rel %.3e (|ref|>1e-2)\n",
              kmax_abs, kmax_rel2);
  std::printf("  state S (%ld checks):   max abs %.3e, max rel %.3e (|ref|>1e-2)\n",
              scmp, smax_abs, smax_rel2);
  // The recurrence itself (state, raw o) must hold 1e-4 at the KIMI-standard
  // |ref|>1e-2 depth (measured ~1e-6). Post-norm out multiplies o's absolute
  // noise by rstd (up to 1/sqrt(1e-5) ~ 316 on near-zero heads), pulling
  // pre-norm elements far below the threshold up across it, so its
  // |ref|>1e-2 rel is a small-element metric: gate 1e-3 there and 1e-4 at
  // the amplitude-equivalent |ref|>1e-1 depth (out rms ~10x the raw-o rms).
  gate(omax_rel1 <= 1e-4, "drift out rel (>1e-1)", omax_rel1, 1e-4);
  gate(omax_rel2 <= 1e-3, "drift out rel (>1e-2)", omax_rel2, 1e-3);
  gate(kmax_rel2 <= 1e-4, "drift kda_out rel", kmax_rel2, 1e-4);
  gate(smax_rel2 <= 1e-4, "drift state rel", smax_rel2, 1e-4);
  std::printf("\n");
}

// ---------------------------------------------------------------------------
// [dumps] article4 validation for all kimi layers, front-end from weights.bin
// ---------------------------------------------------------------------------

struct QLin {
  std::vector<int8_t> w;
  std::vector<float> fold;
  float s_act = 0;
  int d_out = 0, d_in = 0, stride = 0;
};

QLin load_ql(const fx2::WeightsFile& wf, const std::string& prefix, int d_out,
             int d_in) {
  const fx2::WTensor& wq =
      wf.get(prefix + ".weight.q", fx2::DT_I8,
             {static_cast<uint32_t>(d_out), static_cast<uint32_t>(d_in)});
  const fx2::WTensor& ws = wf.get(prefix + ".weight.scale", fx2::DT_BF16,
                                  {static_cast<uint32_t>(d_out)});
  const fx2::WTensor& sa =
      wf.get(prefix + ".quantize_activation.scale", fx2::DT_BF16, {1});
  QLin L;
  L.d_out = d_out;
  L.d_in = d_in;
  L.stride = (d_in + 15) & ~15;
  L.w.assign(static_cast<size_t>(d_out) * L.stride, 0);
  for (int o = 0; o < d_out; o++)
    std::memcpy(L.w.data() + static_cast<size_t>(o) * L.stride,
                wq.i8() + static_cast<size_t>(o) * d_in, d_in);
  L.s_act = fx2::bf16_to_f32(sa.bf16_bits()[0]);
  L.fold.resize(d_out);
  for (int o = 0; o < d_out; o++)
    L.fold[o] = L.s_act * fx2::bf16_to_f32(ws.bf16_bits()[o]);
  return L;
}

void ql_apply(const QLin& L, const float* x, float* y, int8_t* q8) {
  fx2::quantize_i8(x, L.d_in, L.stride, L.s_act, q8);
  fx2::qmatvec(L.w.data(), L.stride, L.fold.data(), L.d_out, q8, y);
}

struct Metric {
  double max_abs = 0, max_rel = 0, ssd = 0, ssr = 0, ssd_smooth = 0;
  long n = 0, n_flip = 0, at_t = -1;
  int at_i = -1;
  double at_ref = 0;
  void add(long t, int i, double mine, double ref) {
    double d = std::fabs(mine - ref);
    n++;
    ssd += d * d;
    ssr += ref * ref;
    if (d <= 1e-4) ssd_smooth += d * d;
    else n_flip++;
    if (d > max_abs) {
      max_abs = d;
      at_t = t;
      at_i = i;
      at_ref = ref;
    }
    if (std::fabs(ref) > 1e-2) max_rel = std::max(max_rel, d / std::fabs(ref));
  }
  double rel_rms() const { return ssr > 0 ? std::sqrt(ssd / ssr) : 0; }
  double smooth_rel_rms() const {
    return ssr > 0 ? std::sqrt(ssd_smooth / ssr) : 0;
  }
  double flip_frac() const { return n ? double(n_flip) / double(n) : 0; }
};

void cmp_rows(Metric& m, long t, const float* mine, const float* ref, int n) {
  for (int i = 0; i < n; i++) m.add(t, i, mine[i], ref[i]);
}

struct LayerW {
  QLin qp, kp, vp, fgu, fgd, ogu, ogd;
  std::vector<float> conv[3], beta_w, dt_bias, gn_w;
  float rsc = 0, tec = 0;
  float a_neg[3] = {0, 0, 0};
};

void section_dumps(const char* data_dir) {
  std::string dir = fx2::find_data_dir(data_dir);
  std::printf("[dumps] article4 teacher-forced validation, data dir %s\n",
              dir.c_str());
  fx2::WeightsFile wf = fx2::WeightsFile::load((dir + "/weights.bin").c_str());
  auto tokens = fx2::read_file<uint8_t>(dir + "/test_tokens.u8");
  auto bounds = fx2::read_file<int32_t>(dir + "/test_bounds.i32");
  const long g0 = bounds[4];
  std::string adir = dir + "/dumps/article4";
  long n_dump = fx2::meta_int(fx2::read_text_file(adir + "/meta.json"),
                              "dumped_positions");

  // normed token embedding table (exactly as model.cpp)
  std::vector<float> tok_table(205 * 192);
  {
    const fx2::WTensor& eq = wf.get("embedding.weight.q", fx2::DT_I8, {205, 192});
    const fx2::WTensor& es = wf.get("embedding.weight.scale", fx2::DT_BF16, {205});
    for (int c = 0; c < 205; c++) {
      float s = fx2::bf16_to_f32(es.bf16_bits()[c]);
      float* row = tok_table.data() + static_cast<size_t>(c) * 192;
      for (int i = 0; i < 192; i++)
        row[i] = static_cast<float>(eq.i8()[c * 192 + i]) * s;
      fx2::rms_norm_vec(row, row, 192);
    }
  }

  const int kimi_layers[9] = {0, 1, 2, 4, 5, 6, 8, 9, 10};
  const char* comp_names[8] = {"conv_q", "conv_k", "conv_v", "g_raw",
                               "out_gate", "beta_raw", "kda_out",
                               "gated_norm_out"};
  bool sec_fail = false;

  for (int li = 0; li < 9; li++) {
    int l = kimi_layers[li];
    std::string b = "blocks." + std::to_string(l) + ".";
    std::string a = b + "attention.";
    LayerW L;
    L.rsc = wf.get(b + "residual_stream_coefficient.value", fx2::DT_F32, {1}).f32()[0];
    L.tec = wf.get(b + "token_embedding_coefficient.value", fx2::DT_F32, {1}).f32()[0];
    L.qp = load_ql(wf, a + "query_projection", 192, 192);
    L.kp = load_ql(wf, a + "key_projection", 192, 192);
    L.vp = load_ql(wf, a + "value_projection", 192, 192);
    L.fgu = load_ql(wf, a + "forget_gate_projection.up", 64, 192);
    L.fgd = load_ql(wf, a + "forget_gate_projection.down", 192, 64);
    L.ogu = load_ql(wf, a + "output_gate_projection.up", 64, 192);
    L.ogd = load_ql(wf, a + "output_gate_projection.down", 192, 64);
    const char* convs[3] = {"query_convolution.weight", "key_convolution.weight",
                            "value_convolution.weight"};
    for (int c = 0; c < 3; c++) {
      const fx2::WTensor& cw = wf.get(a + convs[c], fx2::DT_F32, {192, 4});
      L.conv[c].resize(4 * 192);
      for (int j = 0; j < 4; j++)
        for (int ch = 0; ch < 192; ch++)
          L.conv[c][j * 192 + ch] = cw.f32()[ch * 4 + j];
    }
    {
      const fx2::WTensor& bw = wf.get(a + "beta_projection.weight", fx2::DT_F32, {3, 192});
      L.beta_w.assign(bw.f32(), bw.f32() + 3 * 192);
      const fx2::WTensor& dt = wf.get(a + "dt_bias", fx2::DT_F32, {192});
      L.dt_bias.assign(dt.f32(), dt.f32() + 192);
      const fx2::WTensor& gw = wf.get(a + "output_fused_norm_gate.weight", fx2::DT_F32, {64});
      L.gn_w.assign(gw.f32(), gw.f32() + 64);
      const fx2::WTensor& al = wf.get(a + "log_baseline_decay_rate", fx2::DT_F32, {3});
      for (int h = 0; h < 3; h++) L.a_neg[h] = -std::exp(al.f32()[h]);
    }
    KdaWeights kw;
    for (int c = 0; c < 3; c++) kw.conv_w[c] = L.conv[c].data();
    kw.dt_bias = L.dt_bias.data();
    kw.gn_w = L.gn_w.data();
    for (int h = 0; h < 3; h++) kw.a_neg[h] = L.a_neg[h];

    char nn[8];
    std::snprintf(nn, sizeof nn, "%02d_", l);
    auto ld = [&](const char* c) {
      return fx2::load_npy(adir + "/" + nn + std::string("kimi_") + c + ".npy");
    };
    fx2::Npy d_bi = fx2::load_npy(adir + "/" + nn + std::string("block_input.npy"));
    fx2::Npy d_cq = ld("conv_q"), d_ck = ld("conv_k"), d_cv = ld("conv_v");
    fx2::Npy d_gr = ld("g_raw"), d_og = ld("out_gate"), d_br = ld("beta_raw");
    fx2::Npy d_ko = ld("kda_out"), d_go = ld("gated_norm_out");

    static KdaState st;
    fx2::opt::kda_layer_reset(st);
    Metric M[8];
    alignas(32) float xw[192], xn[192], bq[192], bk[192], bv[192];
    alignas(32) float fu[64], graw[192], og[192], braw[3], out[192];
    alignas(32) float dcq[192], dck[192], dcv[192], dko[192];
    alignas(32) int8_t q8[192];
    for (long t = 0; t < n_dump; t++) {
      const float* x = d_bi.f32() + static_cast<size_t>(t) * 192;
      const float* tok = tok_table.data() + static_cast<size_t>(tokens[g0 + t]) * 192;
      for (int i = 0; i < 192; i++) {
        float t1 = L.rsc * x[i];
        float t2 = L.tec * tok[i];
        xw[i] = t1 + t2;
      }
      fx2::rms_norm_vec(xw, xn, 192);
      ql_apply(L.qp, xn, bq, q8);
      ql_apply(L.kp, xn, bk, q8);
      ql_apply(L.vp, xn, bv, q8);
      ql_apply(L.fgu, xn, fu, q8);
      ql_apply(L.fgd, fu, graw, q8);
      ql_apply(L.ogu, xn, fu, q8);
      ql_apply(L.ogd, fu, og, q8);
      for (int h = 0; h < 3; h++)
        braw[h] = fx2::dot_f32(xn, L.beta_w.data() + static_cast<size_t>(h) * 192, 192);

      KdaDebug dbg;
      dbg.conv_q = dcq;
      dbg.conv_k = dck;
      dbg.conv_v = dcv;
      dbg.kda_out = dko;
      fx2::opt::kda_layer_step(kw, st, bq, bk, bv, graw, og, braw, out, &dbg);

      cmp_rows(M[0], t, dcq, d_cq.f32() + t * 192, 192);
      cmp_rows(M[1], t, dck, d_ck.f32() + t * 192, 192);
      cmp_rows(M[2], t, dcv, d_cv.f32() + t * 192, 192);
      cmp_rows(M[3], t, graw, d_gr.f32() + t * 192, 192);
      cmp_rows(M[4], t, og, d_og.f32() + t * 192, 192);
      cmp_rows(M[5], t, braw, d_br.f32() + t * 3, 3);
      cmp_rows(M[6], t, dko, d_ko.f32() + t * 192, 192);
      cmp_rows(M[7], t, out, d_go.f32() + t * 192, 192);
    }

    std::printf("  layer %2d: %-14s %11s %11s %13s %11s %9s\n", l, "component",
                "max-abs", "max-rel", "rel-RMS", "smoothRMS", "flips");
    for (int c = 0; c < 8; c++) {
      std::printf("            %-14s %11.3e %11.3e %13.3e %11.3e %6ld/%ld\n",
                  comp_names[c], M[c].max_abs, M[c].max_rel, M[c].rel_rms(),
                  M[c].smooth_rel_rms(), M[c].n_flip, M[c].n);
      bool clean = c <= 5;  // front-end + conv: upstream of the state update
      if (clean) {
        if (M[c].smooth_rel_rms() > 1e-4 || M[c].flip_frac() > 1e-3) {
          sec_fail = true;
          std::printf("    ** clean gate fail (smooth %.3e / flips %.3e)\n",
                      M[c].smooth_rel_rms(), M[c].flip_frac());
        }
      } else if (M[c].rel_rms() > 0.03) {  // tf32-noise-limited components
        sec_fail = true;
        std::printf("    ** rel-RMS gate fail (%.3e > 3%%)\n", M[c].rel_rms());
      }
    }
  }
  if (sec_fail) g_fail = true;
  std::printf("  (kda_out / gated_norm_out compare against tf32-noised "
              "reference dumps: expect ~2.3e-4-level max-abs, per "
              "KIMI_SEMANTICS section 5/6)\n\n");
}

}  // namespace

int main(int argc, char** argv) {
  const char* data_dir = nullptr;
  long npts = 10 * 1000 * 1000, steps = 10000;
  bool do_math = true, do_sweep = true, do_drift = true, do_dumps = true;
  for (int i = 1; i < argc; i++) {
    if (std::strcmp(argv[i], "--data") == 0 && i + 1 < argc)
      data_dir = argv[++i];
    else if (std::strcmp(argv[i], "--quick") == 0) {
      npts = 1000 * 1000;
      steps = 2000;
    } else if (std::strcmp(argv[i], "--only") == 0 && i + 1 < argc) {
      std::string s = argv[++i];
      do_math = s == "math";
      do_sweep = s == "sweep";
      do_drift = s == "drift";
      do_dumps = s == "dumps";
    } else if (std::strcmp(argv[i], "--twopass") == 0) {
      fx2::opt::kda_set_sweep(KdaSweep::TWOPASS);
    } else {
      std::fprintf(stderr,
                   "usage: %s [--data DIR] [--quick] "
                   "[--only math|sweep|drift|dumps] [--twopass]\n",
                   argv[0]);
      return 2;
    }
  }
  std::printf("test_kda (sweep variant: %s)\n\n",
              fx2::opt::kda_get_sweep() == KdaSweep::ONEFIVE ? "ONEFIVE"
                                                             : "TWOPASS");
  if (do_math) section_math(npts);
  if (do_sweep) section_sweep();
  if (do_drift) section_drift(steps);
  if (do_dumps) section_dumps(data_dir);

  if (g_fail) {
    std::printf("FAIL\n");
    return 1;
  }
  std::printf("PASS\n");
  return 0;
}
