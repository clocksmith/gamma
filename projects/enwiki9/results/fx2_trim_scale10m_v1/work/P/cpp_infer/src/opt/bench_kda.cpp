// bench_kda: realistic-cache benchmark of the fused KDA component.
//
// Reproduces the cache conditions of real inference: all NINE layers' states
// (9 x 48 KB S + conv rings = ~527 KB) live simultaneously, and BETWEEN the
// per-layer KDA steps a dummy weight stream of ~590 KB/layer (5.3 MB/token
// total, the real int8 weight traffic) is read at full speed, evicting L2 so
// the next layer's state must come from L3 — exactly as in production.
//
// Reported (all in core cycles, rdtsc x measured TSC->core ratio):
//   - whole loop cycles/token (KDA + weight streams)
//   - KDA cycles/token (per-layer rdtsc pairs; ~2% stamp overhead)
//   - stream cycles/token and achieved stream bandwidth
//   - phase breakdown (conv / gates / sweeps / gated norm) via KdaProfile
//   - FMA-pipe utilization vs the 16 fp32-FMA-lane/cycle peak (2 ymm
//     FMA-class ops/cycle), against exact op counts for the sweeps and
//     analytic counts for the rest
//   - L1-hot single-head sweep microbenchmark (issue-limit sanity)
//   - ONEFIVE vs TWOPASS sweep variants
//
// Pinning: BENCH_CPU env var, default cpu 105 (idle CCX 40-43/104-107).
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>

#include "bench_common.h"
#include "kda.h"

using fx2::opt::KdaProfile;
using fx2::opt::KdaState;
using fx2::opt::KdaSweep;
using fx2::opt::KdaWeights;

namespace {

constexpr int NL = 9;

struct TokenIn {
  alignas(64) float q[192], k[192], v[192], g[192], og[192];
  alignas(32) float braw[8];
};

struct LayerWStore {
  alignas(64) float conv[3][4 * 192];
  alignas(64) float dt_bias[192];
  alignas(64) float gn_w[64];
};

// ---- exact / analytic FMA-pipe vector-op counts (ops on the 2 FMA pipes:
// mul/fma/add/sub/min/max/cmp/blend/floor/cvt; IEEE divides counted apart) ----
// sweep (ONEFIVE), per head: pass1 64*(8 mul + 8 fma) + u 16 + pass2 64*16
constexpr double SWEEP_VOPS_LAYER = 3.0 * (1024 + 16 + 1024);
// conv: 72 groups * (4 conv + 17 silu(exp256=15,xor,add)) [+1 div]
constexpr double CONV_VOPS_LAYER = 72.0 * 21;
// decay: 24 groups * (1 add + 43 softplus + 1 mul + 17 exp_full) [+1 div]
constexpr double DECAY_VOPS_LAYER = 24.0 * 62;
// l2norm: 3 heads * (16 fma sums + 6 hsum + 8 qs-scale) [+16 div]
constexpr double L2_VOPS_LAYER = 3.0 * 30;
// gated norm: 3 heads * (8 sumsq + 3 hsum + 8*17 sigmoid + 24 mul) [+8 div]
constexpr double NORM_VOPS_LAYER = 3.0 * 171;
constexpr double BETA_VOPS_LAYER = 17.0;
constexpr double KDA_VOPS_LAYER = SWEEP_VOPS_LAYER + CONV_VOPS_LAYER +
                                  DECAY_VOPS_LAYER + L2_VOPS_LAYER +
                                  NORM_VOPS_LAYER + BETA_VOPS_LAYER;
constexpr double KDA_DIVS_LAYER = 72 + 24 + 48 + 24 + 1;

__attribute__((noinline)) uint64_t stream_read(const uint8_t* p, size_t bytes) {
  __m256i a0 = _mm256_setzero_si256(), a1 = _mm256_setzero_si256();
  for (size_t i = 0; i < bytes; i += 128) {
    _mm_prefetch(reinterpret_cast<const char*>(p + i + 2048), _MM_HINT_T0);
    a0 = _mm256_or_si256(a0, _mm256_load_si256(reinterpret_cast<const __m256i*>(p + i)));
    a1 = _mm256_or_si256(a1, _mm256_load_si256(reinterpret_cast<const __m256i*>(p + i + 32)));
    a0 = _mm256_or_si256(a0, _mm256_load_si256(reinterpret_cast<const __m256i*>(p + i + 64)));
    a1 = _mm256_or_si256(a1, _mm256_load_si256(reinterpret_cast<const __m256i*>(p + i + 96)));
  }
  a0 = _mm256_or_si256(a0, a1);
  return static_cast<uint64_t>(_mm256_extract_epi64(a0, 0)) ^
         static_cast<uint64_t>(_mm256_extract_epi64(a0, 3));
}

struct Bench {
  KdaState* st = nullptr;         // [NL]
  LayerWStore* ws = nullptr;      // [NL]
  KdaWeights w[NL];
  TokenIn* pool = nullptr;        // [8]
  uint8_t* stream = nullptr;      // NL segments
  size_t stream_bytes = 0;        // per segment
  long reset_every = 2048;
  uint64_t sink = 0;

  void init(size_t stream_kb) {
    st = static_cast<KdaState*>(alloc_buf(sizeof(KdaState) * NL));
    ws = static_cast<LayerWStore*>(alloc_buf(sizeof(LayerWStore) * NL));
    pool = static_cast<TokenIn*>(alloc_buf(sizeof(TokenIn) * 8));
    stream_bytes = stream_kb * 1024;
    stream = static_cast<uint8_t*>(alloc_buf(stream_bytes * NL + 4096));

    std::mt19937 rng(7);
    std::normal_distribution<float> N(0.0f, 1.0f);
    std::uniform_real_distribution<float> U(0.0f, 1.0f);
    const float rates[3] = {1.567f, 2.645f, 3.129f};
    for (int l = 0; l < NL; l++) {
      for (int c = 0; c < 3; c++)
        for (int i = 0; i < 4 * 192; i++) ws[l].conv[c][i] = 0.4f * N(rng);
      for (int i = 0; i < 192; i++) ws[l].dt_bias[i] = -3.26f + 4.1f * U(rng);
      for (int i = 0; i < 64; i++) ws[l].gn_w[i] = 0.5f + U(rng);
      for (int c = 0; c < 3; c++) w[l].conv_w[c] = ws[l].conv[c];
      w[l].dt_bias = ws[l].dt_bias;
      w[l].gn_w = ws[l].gn_w;
      for (int h = 0; h < 3; h++) w[l].a_neg[h] = -rates[h];
      fx2::opt::kda_layer_reset(st[l]);
    }
    for (int p = 0; p < 8; p++) {
      for (int i = 0; i < 192; i++) {
        pool[p].q[i] = N(rng);
        pool[p].k[i] = N(rng);
        pool[p].v[i] = N(rng);
        pool[p].g[i] = 1.4f * N(rng);
        pool[p].og[i] = 3.0f * N(rng);
      }
      for (int h = 0; h < 8; h++) pool[p].braw[h] = N(rng);
    }
    // the stream buffer content is irrelevant; alloc_buf memset it already
  }

  void reset_all() {
    for (int l = 0; l < NL; l++) fx2::opt::kda_layer_reset(st[l]);
  }

  // one full run; returns {total ticks, kda ticks, stream ticks}
  struct RunT {
    double total = 0, kda = 0, strm = 0;
  };
  RunT run(long tokens, bool instr, KdaProfile* prof) {
    alignas(64) float out[192];
    alignas(64) static TokenIn hot;  // stand-in for the projections' outputs:
    // in real inference q/k/v/g/og are written into hot stack buffers by the
    // int8 matmuls right before the KDA step, so the KDA step always reads
    // L1-hot inputs. The copy below models those writes (outside the KDA
    // timing but inside the loop, so it shares the cache like the real thing).
    RunT r;
    uint64_t t0 = rdtsc_ser();
    for (long t = 0; t < tokens; t++) {
      if (reset_every > 0 && t % reset_every == 0) reset_all();
      for (int l = 0; l < NL; l++) {
        std::memcpy(&hot, &pool[(t * NL + l) & 7], sizeof(TokenIn));
        if (instr) {
          uint64_t a = rdtsc_ser();
          fx2::opt::kda_layer_step(w[l], st[l], hot.q, hot.k, hot.v, hot.g,
                                   hot.og, hot.braw, out, nullptr, prof);
          uint64_t b = rdtsc_ser();
          sink += stream_read(stream + size_t(l) * stream_bytes, stream_bytes);
          uint64_t c = rdtsc_ser();
          r.kda += double(b - a);
          r.strm += double(c - b);
        } else {
          fx2::opt::kda_layer_step(w[l], st[l], hot.q, hot.k, hot.v, hot.g,
                                   hot.og, hot.braw, out, nullptr, nullptr);
          sink += stream_read(stream + size_t(l) * stream_bytes, stream_bytes);
        }
      }
      sink += static_cast<uint64_t>(out[0] != 0.0f);
    }
    r.total = double(rdtsc_ser() - t0);
    return r;
  }
};

void print_cyc(const char* name, double cyc_tok, double vops, double divs) {
  // utilization vs 2 FMA-class ymm ops/cycle; divs shown for context
  double util = vops > 0 ? (vops / 2.0) / cyc_tok : 0;
  if (vops > 0)
    std::printf("  %-28s %9.0f cyc/tok   fma-pipe util %5.1f%%  "
                "(%.0f vec-ops + %.0f div)\n",
                name, cyc_tok, 100.0 * util, vops, divs);
  else
    std::printf("  %-28s %9.0f cyc/tok\n", name, cyc_tok);
}

}  // namespace

int main(int argc, char** argv) {
  long tokens = 4000;
  size_t stream_kb = 590;
  long reset_every = 2048;
  int reps = 5;
  bool do_profile = true;
  for (int i = 1; i < argc; i++) {
    if (std::strcmp(argv[i], "--tokens") == 0 && i + 1 < argc)
      tokens = std::atol(argv[++i]);
    else if (std::strcmp(argv[i], "--stream-kb") == 0 && i + 1 < argc)
      stream_kb = std::strtoul(argv[++i], nullptr, 10);
    else if (std::strcmp(argv[i], "--reset-every") == 0 && i + 1 < argc)
      reset_every = std::atol(argv[++i]);
    else if (std::strcmp(argv[i], "--reps") == 0 && i + 1 < argc)
      reps = std::atoi(argv[++i]);
    else if (std::strcmp(argv[i], "--no-profile") == 0)
      do_profile = false;
    else if (std::strcmp(argv[i], "--pf") == 0 && i + 1 < argc)
      fx2::opt::kda_set_pf_mode(std::atoi(argv[++i]));
    else {
      std::fprintf(stderr,
                   "usage: %s [--tokens N] [--stream-kb K] [--reset-every N] "
                   "[--reps N] [--no-profile] [--pf 0|1|2|3]\n",
                   argv[0]);
      return 2;
    }
  }

  if (!getenv("BENCH_CPU")) setenv("BENCH_CPU", "105", 0);
  pin_from_env();
  Calib cal = calibrate();
  print_calib("bench_kda", cal);

  std::printf(
      "config: %d layers, %ld tokens/rep x %d reps, stream %zu KB/layer "
      "(%.2f MB/token), reset every %ld, sweep sizes: 9 x (3 x 16 KB state)\n",
      NL, tokens, reps, stream_kb, stream_kb * NL / 1024.0, reset_every);

  Bench B;
  B.init(stream_kb);
  B.reset_every = reset_every;

  // ---------------- L1-hot single-head sweep microbenchmark ----------------
  {
    alignas(64) static float S[4096];
    alignas(32) float decay[64], kn[64], v[64], qs[64], o[64];
    std::mt19937 rng(3);
    std::normal_distribution<float> N(0.0f, 1.0f);
    for (int i = 0; i < 4096; i++) S[i] = 0.1f * N(rng);
    for (int i = 0; i < 64; i++) {
      decay[i] = 0.5f + 0.5f * (float)(i & 1);
      kn[i] = 0.1f * N(rng);
      qs[i] = 0.01f * N(rng);
      v[i] = N(rng);
    }
    for (KdaSweep var : {KdaSweep::ONEFIVE, KdaSweep::TWOPASS}) {
      const long R = 30000;
      auto once = [&]() {
        uint64_t t0 = rdtsc_ser();
        for (long r = 0; r < R; r++)
          fx2::opt::kda_sweep_head(S, decay, kn, v, 0.5f, qs, o, S, var);
        return ticks_to_cycles(double(rdtsc_ser() - t0)) / double(R);
      };
      Stats s = repeat_stat(once, 5, 1);
      double vops = 1024 + 16 + 1024 + (var == KdaSweep::TWOPASS ? 8 + 512 : 0);
      std::printf(
          "  L1-hot sweep %-8s %7.1f cyc/head (min %.1f)  issue-floor %d, "
          "util %.1f%%\n",
          var == KdaSweep::ONEFIVE ? "ONEFIVE" : "TWOPASS", s.med, s.mn,
          (int)(vops / 2), 100.0 * (vops / 2) / s.med);
    }
  }

  // ---------------- realistic loop, both variants ----------------
  for (KdaSweep var : {KdaSweep::ONEFIVE, KdaSweep::TWOPASS}) {
    fx2::opt::kda_set_sweep(var);
    std::printf("\n=== variant %s ===\n",
                var == KdaSweep::ONEFIVE ? "ONEFIVE (1.5-pass)" : "TWOPASS");
    B.run(1000, false, nullptr);  // warm

    // clean total (no per-layer stamps)
    auto clean = [&]() { return B.run(tokens, false, nullptr).total; };
    Stats sc = repeat_stat(clean, reps, 1);
    double clean_tok = ticks_to_cycles(sc.med) / tokens;

    // instrumented split
    Bench::RunT acc;
    auto instr = [&]() {
      Bench::RunT r = B.run(tokens, true, nullptr);
      acc = r;
      return r.total;
    };
    Stats si = repeat_stat(instr, reps, 1);
    double kda_tok = ticks_to_cycles(acc.kda) / tokens;
    double strm_tok = ticks_to_cycles(acc.strm) / tokens;
    double instr_tok = ticks_to_cycles(si.med) / tokens;

    std::printf("  whole loop (clean)           %9.0f cyc/tok  "
                "(instrumented: %.0f, stamp overhead %.1f%%)\n",
                clean_tok, instr_tok, 100.0 * (instr_tok - clean_tok) / clean_tok);
    print_cyc("KDA total (9 layers)", kda_tok, KDA_VOPS_LAYER * NL,
              KDA_DIVS_LAYER * NL);
    double sb = double(B.stream_bytes) * NL / strm_tok;
    std::printf("  %-28s %9.0f cyc/tok   (%.1f B/cyc, %.1f GB/s @3.337GHz)\n",
                "weight stream (dummy)", strm_tok, sb, sb * 3.337);

    if (do_profile) {
      KdaProfile prof;
      B.run(tokens, true, &prof);
      double c = ticks_to_cycles(double(prof.conv)) / tokens;
      double g = ticks_to_cycles(double(prof.gates)) / tokens;
      double s = ticks_to_cycles(double(prof.sweep)) / tokens;
      double n = ticks_to_cycles(double(prof.norm)) / tokens;
      std::printf("  phase split (extra stamps; sums > clean):\n");
      print_cyc("  conv+silu+ring", c, CONV_VOPS_LAYER * NL, 72.0 * NL);
      print_cyc("  gates (decay,beta,l2norm)", g,
                (DECAY_VOPS_LAYER + L2_VOPS_LAYER + BETA_VOPS_LAYER) * NL,
                (24 + 48 + 1.0) * NL);
      print_cyc("  state sweeps (3 heads)", s, SWEEP_VOPS_LAYER * NL, 0);
      print_cyc("  gated norm", n, NORM_VOPS_LAYER * NL, 24.0 * NL);
    }
  }
  fx2::opt::kda_set_sweep(KdaSweep::ONEFIVE);

  // ---------------- no-stream contrast (states stay L2-resident) ----------
  {
    std::printf("\n=== no weight stream (states L2-resident; NOT the real "
                "regime) ===\n");
    Bench B2;
    B2.init(1);  // 1 KB dummy stream
    B2.reset_every = reset_every;
    B2.run(1000, false, nullptr);
    Bench::RunT acc;
    auto instr = [&]() {
      Bench::RunT r = B2.run(tokens, true, nullptr);
      acc = r;
      return r.total;
    };
    repeat_stat(instr, reps, 1);
    print_cyc("KDA total (9 layers)", ticks_to_cycles(acc.kda) / tokens,
              KDA_VOPS_LAYER * NL, KDA_DIVS_LAYER * NL);
  }

  std::printf("\nanalytic floors per token: sweeps %d cyc (exact op count), "
              "whole KDA %.0f cyc issue-bound; state traffic 864 KB/token "
              "r+w -> %.0f cyc at 43 B/c (overlapped)\n",
              (int)(SWEEP_VOPS_LAYER * NL / 2), KDA_VOPS_LAYER * NL / 2,
              864.0 * 1024 / 43);
  std::printf("(sink %llu)\n", (unsigned long long)B.sink);
  return 0;
}
