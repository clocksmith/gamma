// Microbenchmark of the qmat kernel suite under REALISTIC cache conditions:
// the FULL per-token weight working set (all 110 quantized matmuls of the
// model, ~6 MB unpacked) is laid out in consumption order and cycled token by
// token, so every arena is L3-resident but evicted from L1/L2 between uses —
// exactly like real inference. Never benchmarks a single hot matmul in L1.
//
// Configs: naive (src/kernels.cpp qmatvec), dense-unpacked (production
// epilogues, chained mlp.up relu2q -> mlp.down), dense all-(a) unpacked vs
// packed-int4 (format comparison), sparse (mlp.down + prior via column
// kernels at real densities, real ppmd prior rows), density sweeps.
#include "../../bench/bench_common.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>

#include "../kernels.h"
#include "qmat_dense.h"
#include "qmat_sparse.h"

using namespace fx2::opt;

// ---------------------------------------------------------------------------
static uint64_t g_rng = 0x9E3779B97F4A7C15ull;
static inline uint64_t rnd64() {
  g_rng ^= g_rng << 13;
  g_rng ^= g_rng >> 7;
  g_rng ^= g_rng << 17;
  return g_rng;
}
static inline int rndi(int lo, int hi) {
  return lo + (int)(rnd64() % (uint64_t)(hi - lo + 1));
}
static inline float rndf01() { return (float)(rnd64() >> 40) / (float)(1 << 24); }

// ---------------------------------------------------------------------------
enum Epi { EA, EB, EC, ED };
enum Cls { C_P192A, C_P192B, C_UP, C_GUP, C_GDN, C_DOWN, C_PRIOR, C_UNEMB, NCLS };
static const char* CLS_NAME[NCLS] = {"qkv192_a", "oproj192_b", "mlp_up_c",
                                     "gate_up_d", "gate_dn_a", "mlp_down",
                                     "prior", "unembed"};
static const bool KIMI[12] = {true, true, true,  false, true, true,
                              true, false, true, true,  true, false};
constexpr int NVAR = 16;   // act variants for chained sites
constexpr int NPRIOR = 512;

struct Site {
  int cls;
  Epi epi;
  int d_out, d_in;
  bool biased;
  int layer;        // -1 for prior/unembed
  QDense qd;        // unpacked dense arena
  QPacked qp;       // packed arena
  QSparse qs;       // int8 column arena (down/prior only)
  QSparse4 qs4;     // int4 column arena (down/prior only)
  const int8_t* nw; // naive weights (stride-padded)
  const float* nfold;
  int nstride;
  uint8_t* act;     // u8 acts; up sites: NVAR variants of stride bytes
  int8_t* act_s8;   // signed acts for naive/packed (same ints)
  int32_t corr7[NVAR]; // per-variant packed correction
  float* out;       // f32 out / residual (rows_padded)
  float s_next;     // (c)/(d)
  uint8_t* q_out;   // (c)/(d) output vector (u8)
  uint16_t* idx_out;
  int nnz;          // last (c) nnz
};

static std::vector<Site> g_sites;
static std::vector<int8_t> g_qw_scratch;

// per-layer real mlp nonzero fractions (1 - zero_frac from dumps/stats.json)
static const float REAL_DENS[12] = {0.437f, 0.159f, 0.112f, 0.142f,
                                    0.190f, 0.223f, 0.175f, 0.185f,
                                    0.166f, 0.152f, 0.149f, 0.204f};

// prior rows (real if data file present)
static uint8_t* g_prior_q8[NPRIOR];    // 224 padded, raw u8
static uint16_t* g_prior_idx[NPRIOR];  // built per token in sparse config
static int g_prior_nnz[NPRIOR];
static double g_prior_mean_nnz = 0;

// sweep pattern storage: per down-site, NVAR synthetic (q8, idx, nnz)
struct Pattern {
  uint8_t* q8;
  uint16_t* idx;
  int nnz;
};
static std::vector<Pattern> g_pat;  // [12 * NVAR] active sweep patterns

// bump allocator over one hugepage-backed pool (arenas + acts contiguous,
// like real inference; avoids one 2 MB mapping per buffer)
static uint8_t* g_pool = nullptr;
static size_t g_pool_off = 0, g_pool_cap = 0;
static uint8_t* balloc(size_t n) {  // 64B-aligned, +tail slack readable, zeroed
  n = (n + 63) & ~size_t(63);
  if (!g_pool) {
    g_pool_cap = size_t(96) << 20;
    g_pool = (uint8_t*)alloc_buf(g_pool_cap);
    memset(g_pool, 0, g_pool_cap);
  }
  if (g_pool_off + n + QMAT_TAIL_SLACK > g_pool_cap) {
    fprintf(stderr, "bench pool exhausted\n");
    exit(1);
  }
  uint8_t* p = g_pool + g_pool_off;
  g_pool_off += n;
  return p;
}

// ---------------------------------------------------------------------------
// model stream construction
// ---------------------------------------------------------------------------
static void add_site(int cls, Epi epi, int d_out, int d_in, bool biased,
                     int layer) {
  Site s;
  memset(&s, 0, sizeof(s));
  s.cls = cls;
  s.epi = epi;
  s.d_out = d_out;
  s.d_in = d_in;
  s.biased = biased;
  s.layer = layer;
  g_sites.push_back(s);
}

static void build_stream_defs() {
  add_site(C_PRIOR, EA, 192, 205, false, -1);
  for (int l = 0; l < 12; l++) {
    if (KIMI[l]) {
      add_site(C_P192A, EA, 192, 192, true, l);  // q
      add_site(C_P192A, EA, 192, 192, true, l);  // k
      add_site(C_P192A, EA, 192, 192, true, l);  // v
      add_site(C_GUP, ED, 64, 192, true, l);     // forget up
      add_site(C_GDN, EA, 192, 64, true, l);     // forget down
      add_site(C_GUP, ED, 64, 192, true, l);     // outgate up
      add_site(C_GDN, EA, 192, 64, true, l);     // outgate down
      add_site(C_P192B, EB, 192, 192, true, l);  // out proj
    } else {
      add_site(C_P192A, EA, 192, 192, true, l);
      add_site(C_P192A, EA, 192, 192, true, l);
      add_site(C_P192A, EA, 192, 192, true, l);
      add_site(C_P192B, EB, 192, 192, true, l);
    }
    add_site(C_UP, EC, 768, 192, true, l);
    add_site(C_DOWN, EB, 192, 768, false, l);
  }
  add_site(C_UNEMB, EA, 205, 192, true, -1);
}

static void load_priors() {
  FILE* f = fopen("../../data/test_priors.f16", "rb");
  const float scale = 0.0027618408203125f;  // bf16(prior act scale)
  std::vector<uint16_t> row16(205);
  std::vector<float> rowf(224, 0.0f);
  std::vector<int8_t> q(224);
  long long nz_sum = 0;
  for (int r = 0; r < NPRIOR; r++) {
    g_prior_q8[r] = balloc(224);
    g_prior_idx[r] = (uint16_t*)balloc(2 * (224 + 16));
    bool ok = f && fseek(f, (long)( (100000ll + r * 37) % 2000000 ) * 410, SEEK_SET) == 0 &&
              fread(row16.data(), 2, 205, f) == 205;
    if (ok) {
      fx2::f16_to_f32(row16.data(), rowf.data(), 205);
    } else {  // synthetic fallback: ~25 spiky nonzeros
      for (int i = 0; i < 205; i++) rowf[i] = 0.0f;
      int k = 5 + rndi(0, 40);
      for (int i = 0; i < k; i++) rowf[rndi(0, 204)] = rndf01() * 0.4f;
    }
    fx2::quantize_i8(rowf.data(), 205, 224, scale, q.data());
    for (int i = 0; i < 224; i++) g_prior_q8[r][i] = (uint8_t)q[i];
    int nnz = qsparse_make_idx(g_prior_q8[r], 205, g_prior_idx[r]);
    for (int k2 = nnz; k2 < nnz + 8; k2++)
      g_prior_idx[r][k2] = nnz ? g_prior_idx[r][nnz - 1] : 0;
    g_prior_nnz[r] = nnz;
    nz_sum += nnz;
  }
  if (f) fclose(f);
  g_prior_mean_nnz = (double)nz_sum / NPRIOR;
  printf("# priors: %s, mean nnz %.1f / 205\n", f ? "REAL rows" : "synthetic",
         g_prior_mean_nnz);
}

// build all arenas + acts; returns footprints
static void build_all() {
  build_stream_defs();
  // contiguous unpacked / packed / naive / sparse blocks in stream order
  size_t tot_u = 0, tot_p = 0, tot_n = 0, tot_s = 0;
  for (auto& s : g_sites) {
    tot_u += (qdense_bytes(s.d_out, s.d_in) + 63) & ~size_t(63);
    tot_p += (qpacked_bytes(s.d_out, s.d_in) + 63) & ~size_t(63);
    tot_n += (size_t)s.d_out * ((s.d_in + 15) & ~15) + 64;
    if (s.cls == C_DOWN || s.cls == C_PRIOR)
      tot_s += ((qsparse_bytes(s.d_in) + 63) & ~size_t(63)) +
               ((qsparse4_bytes(s.d_in) + 63) & ~size_t(63)) + 2048;
  }
  uint8_t* ub = balloc(tot_u);
  uint8_t* pb = balloc(tot_p);
  uint8_t* nb = balloc(tot_n);
  uint8_t* sb = balloc(tot_s + g_sites.size() * 1024);  // + fold arrays
  printf("# arenas: unpacked %.2f MB, packed %.2f MB, naive %.2f MB, "
         "sparse-cols %.2f MB\n",
         tot_u / 1048576.0, tot_p / 1048576.0, tot_n / 1048576.0,
         tot_s / 1048576.0);
  size_t ou = 0, op = 0, on = 0, os = 0;

  for (auto& s : g_sites) {
    const int stride = (s.d_in + 15) & ~15;
    // random weights/scales
    g_qw_scratch.assign((size_t)s.d_out * s.d_in, 0);
    std::vector<float> fold(s.d_out);
    for (auto& w : g_qw_scratch) w = (int8_t)rndi(-7, 7);
    for (auto& fv : fold) {
      fv = std::exp2f(-11.0f + 6.0f * rndf01());
      if (rnd64() & 1) fv = -fv;
    }
    // fold magnitudes tuned so (c) h values are sane; see calibration below
    s.qd = qdense_build(ub + ou, g_qw_scratch.data(), fold.data(), s.d_out,
                        s.d_in, s.biased);
    ou += (qdense_bytes(s.d_out, s.d_in) + 63) & ~size_t(63);
    s.qp = qpacked_build(pb + op, g_qw_scratch.data(), fold.data(), s.d_out,
                         s.d_in);
    op += (qpacked_bytes(s.d_out, s.d_in) + 63) & ~size_t(63);
    // naive layout
    int8_t* nw = (int8_t*)(nb + on);
    for (int o = 0; o < s.d_out; o++) {
      memcpy(nw + (size_t)o * stride, &g_qw_scratch[(size_t)o * s.d_in],
             s.d_in);
      memset(nw + (size_t)o * stride + s.d_in, 0, stride - s.d_in);
    }
    s.nw = nw;
    s.nstride = stride;
    on += (size_t)s.d_out * stride;
    float* nf = (float*)(nb + ((on + 63) & ~size_t(63)));
    memcpy(nf, fold.data(), sizeof(float) * s.d_out);
    s.nfold = nf;
    on = ((on + 63) & ~size_t(63)) + sizeof(float) * s.d_out;
    on = (on + 63) & ~size_t(63);
    // sparse columns for down/prior (int8 and int4 variants)
    if (s.cls == C_DOWN || s.cls == C_PRIOR) {
      float* sf = (float*)(sb + os);
      os += 1024;
      s.qs = qsparse_build((int8_t*)(sb + os), sf, g_qw_scratch.data(),
                           fold.data(), 192, s.d_in);
      os += (qsparse_bytes(s.d_in) + 63) & ~size_t(63);
      float* sf4 = (float*)(sb + os);
      os += 1024;
      s.qs4 = qsparse4_build(sb + os, sf4, g_qw_scratch.data(), fold.data(),
                             192, s.d_in);
      os += (qsparse4_bytes(s.d_in) + 63) & ~size_t(63);
    }
    // activations
    const int nv = (s.cls == C_UP) ? NVAR : 1;
    s.act = balloc((size_t)nv * s.qd.stride);
    s.act_s8 = (int8_t*)balloc((size_t)nv * ((s.qp.stride4 > s.qd.stride)
                                                 ? s.qp.stride4
                                                 : s.qd.stride));
    for (int v = 0; v < nv; v++) {
      int32_t sum = 0;
      for (int i = 0; i < s.d_in; i++) {
        int qa = s.biased ? rndi(-128, 127) : rndi(0, 127);
        s.act[v * s.qd.stride + i] = (uint8_t)(s.biased ? qa + 128 : qa);
        s.act_s8[v * s.qd.stride + i] = (int8_t)qa;
        sum += qa;
      }
      s.corr7[v] = 7 * sum;
    }
    s.out = (float*)balloc(sizeof(float) * (s.qd.rows_padded + 8));
    s.q_out = balloc(s.qd.rows_padded + 32);
    s.idx_out = (uint16_t*)balloc(2 * (s.qd.rows_padded + 16));
    s.nnz = 0;
    s.s_next = 0.02f;
  }

  // calibrate mlp.up s_next per layer so relu2q hits the real densities,
  // then wire mlp.down inputs to the chained up outputs
  Site* up[12];
  Site* down[12];
  {
    int ui = 0, di = 0;
    for (auto& s : g_sites) {
      if (s.cls == C_UP) up[ui++] = &s;
      if (s.cls == C_DOWN) down[di++] = &s;
    }
  }
  for (int l = 0; l < 12; l++) {
    Site* u = up[l];
    std::vector<float> h;
    h.reserve(NVAR * 768);
    std::vector<float> y(u->qd.rows_padded);
    for (int v = 0; v < NVAR; v++) {
      qgemv_f32(u->qd, u->act + v * u->qd.stride, y.data());
      for (int o = 0; o < 768; o++) {
        float t = y[o] > 0 ? y[o] * y[o] : 0.0f;
        h.push_back(t);
      }
    }
    std::sort(h.begin(), h.end());
    float target = REAL_DENS[l];
    float hq = h[(size_t)((1.0f - target) * (h.size() - 1))];
    u->s_next = hq > 0 ? 2.0f * hq : 1.0f;
    // achieved density check
    long long nz = 0;
    for (int v = 0; v < NVAR; v++)
      nz += qgemv_relu2q(u->qd, u->act + v * u->qd.stride, u->s_next,
                         u->q_out, u->idx_out);
    printf("# layer %2d: target dens %.3f achieved %.3f (s_next=%g)\n", l,
           target, (double)nz / (NVAR * 768.0), u->s_next);
    (void)down;
  }

  load_priors();

  // sweep patterns (initially unused)
  g_pat.assign(12 * NVAR, Pattern{nullptr, nullptr, 0});
  for (auto& pt : g_pat) {
    pt.q8 = balloc(768);
    pt.idx = (uint16_t*)balloc(2 * (768 + 16));
  }
}

// fill sweep patterns at a given density; clustered = markov runs (mean ~4)
static void make_patterns(float dens, bool clustered) {
  for (int k = 0; k < 12 * NVAR; k++) {
    Pattern& pt = g_pat[k];
    memset(pt.q8, 0, 768);
    int nnz = 0;
    if (!clustered) {
      for (int i = 0; i < 768; i++)
        if (rndf01() < dens) {
          pt.q8[i] = (uint8_t)rndi(1, 127);
          pt.idx[nnz++] = (uint16_t)i;
        }
    } else {
      const float a = 0.75f;  // P(nz|prev nz): mean run 4
      float b = dens * (1 - a) / (1 - dens);
      if (b > 1) b = 1;
      bool prev = false;
      for (int i = 0; i < 768; i++) {
        bool nz = rndf01() < (prev ? a : b);
        if (nz) {
          pt.q8[i] = (uint8_t)rndi(1, 127);
          pt.idx[nnz++] = (uint16_t)i;
        }
        prev = nz;
      }
    }
    for (int j = nnz; j < nnz + 8; j++) pt.idx[j] = nnz ? pt.idx[nnz - 1] : 0;
    pt.nnz = nnz;
  }
}

// ---------------------------------------------------------------------------
// stream runners
// ---------------------------------------------------------------------------
enum Mode {
  M_NAIVE,
  M_DENSE,       // production epilogues, dense down (G4 row-major) + dense prior
  M_DENSE_ALLA,  // every site epilogue (a), unpacked
  M_DENSE_ALLA_NOPF,
  M_PACKED_ALLA, // every site epilogue (a), packed int4
  M_SPARSE,      // sparse down (chained idx) + sparse prior (real rows+make_idx)
  M_SPARSE_NODOWN,  // sparse config with mlp.down calls REMOVED entirely:
                    // (sparse - nodown)/12 = true marginal cost of a chained
                    // sparse down incl. all overlap effects (no lfence bias)
  M_SWEEP_SPARSE,   // downs from g_pat via int8 sparse kernel
  M_SWEEP_SPARSE4,  // downs from g_pat via int4 sparse kernel
  M_SWEEP_COLDENSE, // downs from g_pat via int8 column-dense fallback
  M_SWEEP_COLDENSE4,// downs from g_pat via int4 column-dense fallback
};

static int32_t g_dummy_i32;
static volatile float g_sink;

// one token pass; tok selects act variants / prior rows / patterns
template <Mode MODE>
static inline void run_token(int tok) {
  const int pv = tok % NPRIOR;
  int downs_seen = 0;
  for (auto& s : g_sites) {
    const int v = (s.cls == C_UP) ? (tok & (NVAR - 1)) : 0;
    const uint8_t* act = s.act + v * s.qd.stride;
    const int8_t* act8 = s.act_s8 + v * s.qd.stride;
    if (MODE == M_NAIVE) {
      if (s.cls == C_PRIOR)
        fx2::qmatvec(s.nw, s.nstride, s.nfold, s.d_out,
                     (const int8_t*)g_prior_q8[pv], s.out);
      else
        fx2::qmatvec(s.nw, s.nstride, s.nfold, s.d_out, act8, s.out);
      continue;
    }
    if (MODE == M_DENSE_ALLA) {
      qgemv_f32(s.qd, s.cls == C_PRIOR ? g_prior_q8[pv] : act, s.out);
      continue;
    }
    if (MODE == M_DENSE_ALLA_NOPF) {
      qgemv_f32_nopf(s.qd, s.cls == C_PRIOR ? g_prior_q8[pv] : act, s.out);
      continue;
    }
    if (MODE == M_PACKED_ALLA) {
      if (s.cls == C_PRIOR) {
        int32_t sum = 0;  // act sum for the global correction 7*sum(q)
        const uint8_t* q = g_prior_q8[pv];
        for (int i = 0; i < 205; i++) sum += q[i];
        qgemv_packed_f32(s.qp, (const int8_t*)q, 7 * sum, s.out);
      } else {
        qgemv_packed_f32(s.qp, act8, s.corr7[v], s.out);
      }
      continue;
    }
    // production modes
    switch (s.cls) {
      case C_PRIOR:
        if (MODE == M_DENSE) {
          qgemv_f32(s.qd, g_prior_q8[pv], s.out);
        } else {  // sparse prior: build the index list, then column kernel
          int nnz = qsparse_make_idx(g_prior_q8[pv], 205, s.idx_out);
          for (int k = nnz; k < nnz + 8; k++)
            s.idx_out[k] = nnz ? s.idx_out[nnz - 1] : 0;
          qsparse4_f32(s.qs4, g_prior_q8[pv], s.idx_out, nnz, s.out);
        }
        break;
      case C_UP:
        s.nnz = qgemv_relu2q(s.qd, act, s.s_next, s.q_out, s.idx_out);
        break;
      case C_DOWN: {
        if (MODE == M_SPARSE_NODOWN) {
          downs_seen++;
          break;
        }
        if (MODE == M_DENSE) {
          // dense row-major G4 arena on the chained q8 (raw u8)
          const Site* u = &s - 1;  // up site precedes its down site
          qgemv_add(s.qd, u->q_out, s.out);
        } else if (MODE == M_SPARSE) {
          const Site* u = &s - 1;
          if (u->nnz > (int)(QMAT_SPARSE_DENSITY_THRESHOLD * 768))
            qsparse4_dense_add(s.qs4, u->q_out, s.out);
          else
            qsparse4_add(s.qs4, u->q_out, u->idx_out, u->nnz, s.out);
        } else {
          const Pattern& pt =
              g_pat[downs_seen * NVAR + (tok & (NVAR - 1))];
          if (MODE == M_SWEEP_COLDENSE)
            qsparse_dense_add(s.qs, pt.q8, s.out);
          else if (MODE == M_SWEEP_COLDENSE4)
            qsparse4_dense_add(s.qs4, pt.q8, s.out);
          else if (MODE == M_SWEEP_SPARSE4)
            qsparse4_add(s.qs4, pt.q8, pt.idx, pt.nnz, s.out);
          else
            qsparse_add(s.qs, pt.q8, pt.idx, pt.nnz, s.out);
        }
        downs_seen++;
        break;
      }
      case C_GUP:
        qgemv_quant_bias(s.qd, act, s.s_next, s.q_out);
        break;
      case C_GDN: {
        // chained: consume the preceding gate-up's biased u8 output
        const Site* gu = &s - 1;
        qgemv_f32(s.qd, gu->q_out, s.out);
        break;
      }
      case C_P192B:
        qgemv_add(s.qd, act, s.out);
        break;
      default:
        qgemv_f32(s.qd, act, s.out);
    }
  }
}

template <Mode MODE>
static double time_stream(int tokens, int reps, double* spread = nullptr) {
  auto one = [&]() -> double {
    uint64_t t0 = rdtsc_ser();
    for (int t = 0; t < tokens; t++) run_token<MODE>(t);
    return ticks_to_cycles((double)(rdtsc_ser() - t0)) / tokens;
  };
  one();  // warm (page in arenas, settle L3)
  Stats s = repeat_stat(one, reps, 1);
  if (spread) *spread = (s.mx - s.mn) / s.med;
  g_sink = g_sites[5].out[0];
  return s.med;
}

// instrumented per-class pass (lfence;rdtsc boundaries between sites)
static double g_stamp_cost = 66.8;
static void measure_stamp_cost() {
  const int N = 4001;
  std::vector<uint64_t> t(N);
  for (int i = 0; i < N; i++) t[i] = rdtsc_ser();
  std::vector<double> d(N - 1);
  for (int i = 0; i + 1 < N; i++) d[i] = (double)(t[i + 1] - t[i]);
  std::sort(d.begin(), d.end());
  g_stamp_cost = ticks_to_cycles(d[d.size() / 2]);
  printf("# stamp cost %.1f core cyc\n", g_stamp_cost);
}

template <Mode MODE>
static void per_class(int tokens, double macs[NCLS], double cyc[NCLS],
                      double* down_per_matmul) {
  static std::vector<uint64_t> stamps;
  stamps.assign(g_sites.size() + 1, 0);
  double acc[NCLS] = {0};
  long long cnt[NCLS] = {0};
  double mc[NCLS] = {0};
  for (int t = 0; t < tokens; t++) {
    int i = 0;
    // (loop split so each site is individually stamped)
    stamps[0] = rdtsc_ser();
    const int pv = t % NPRIOR;
    int downs_seen = 0;
    for (auto& s : g_sites) {
      // reuse run_token's per-site body by calling it for a single site is
      // awkward; duplicate the minimal dispatch here:
      const int v = (s.cls == C_UP) ? (t & (NVAR - 1)) : 0;
      const uint8_t* act = s.act + v * s.qd.stride;
      const int8_t* act8 = s.act_s8 + v * s.qd.stride;
      switch (MODE) {
        case M_NAIVE:
          fx2::qmatvec(s.nw, s.nstride, s.nfold, s.d_out,
                       s.cls == C_PRIOR ? (const int8_t*)g_prior_q8[pv] : act8,
                       s.out);
          break;
        default:
          switch (s.cls) {
            case C_PRIOR:
              if (MODE == M_DENSE) {
                qgemv_f32(s.qd, g_prior_q8[pv], s.out);
              } else {
                int nnz = qsparse_make_idx(g_prior_q8[pv], 205, s.idx_out);
                for (int k = nnz; k < nnz + 8; k++)
                  s.idx_out[k] = nnz ? s.idx_out[nnz - 1] : 0;
                qsparse4_f32(s.qs4, g_prior_q8[pv], s.idx_out, nnz, s.out);
              }
              break;
            case C_UP:
              s.nnz = qgemv_relu2q(s.qd, act, s.s_next, s.q_out, s.idx_out);
              break;
            case C_DOWN: {
              const Site* u = &s - 1;
              if (MODE == M_DENSE) {
                qgemv_add(s.qd, u->q_out, s.out);
              } else if (MODE == M_SPARSE) {
                if (u->nnz > (int)(QMAT_SPARSE_DENSITY_THRESHOLD * 768))
                  qsparse4_dense_add(s.qs4, u->q_out, s.out);
                else
                  qsparse4_add(s.qs4, u->q_out, u->idx_out, u->nnz, s.out);
              } else {
                const Pattern& pt = g_pat[downs_seen * NVAR + (t & (NVAR - 1))];
                if (MODE == M_SWEEP_COLDENSE)
                  qsparse_dense_add(s.qs, pt.q8, s.out);
                else if (MODE == M_SWEEP_COLDENSE4)
                  qsparse4_dense_add(s.qs4, pt.q8, s.out);
                else if (MODE == M_SWEEP_SPARSE4)
                  qsparse4_add(s.qs4, pt.q8, pt.idx, pt.nnz, s.out);
                else
                  qsparse_add(s.qs, pt.q8, pt.idx, pt.nnz, s.out);
              }
              downs_seen++;
              break;
            }
            case C_GUP:
              qgemv_quant_bias(s.qd, act, s.s_next, s.q_out);
              break;
            case C_GDN:
              qgemv_f32(s.qd, (&s - 1)->q_out, s.out);
              break;
            case C_P192B:
              qgemv_add(s.qd, act, s.out);
              break;
            default:
              qgemv_f32(s.qd, act, s.out);
          }
      }
      i++;
      stamps[i] = rdtsc_ser();
    }
    // accumulate (effective MACs: sparse counts nnz*192, dense d_in*d_out)
    downs_seen = 0;
    for (size_t k = 0; k < g_sites.size(); k++) {
      Site& s = g_sites[k];
      double c = ticks_to_cycles((double)(stamps[k + 1] - stamps[k])) -
                 g_stamp_cost;
      acc[s.cls] += c;
      cnt[s.cls]++;
      double m = (double)s.d_out * s.d_in;
      if (s.cls == C_DOWN && (MODE == M_SPARSE || MODE == M_SWEEP_SPARSE ||
                              MODE == M_SWEEP_SPARSE4)) {
        const Site* u = &s - 1;
        m = 192.0 * (MODE == M_SPARSE
                         ? (&s - 1)->nnz
                         : g_pat[downs_seen * NVAR + (t & (NVAR - 1))].nnz);
        (void)u;
        downs_seen++;
      } else if (s.cls == C_PRIOR && MODE != M_NAIVE && MODE != M_DENSE) {
        m = 192.0 * g_prior_nnz[pv];
      }
      mc[s.cls] += m;
    }
  }
  for (int c = 0; c < NCLS; c++) {
    macs[c] = mc[c] / tokens;
    cyc[c] = acc[c] / tokens;
  }
  if (down_per_matmul) *down_per_matmul = acc[C_DOWN] / (12.0 * tokens);
}

template <Mode MODE>
static void report_stream(const char* name, int tokens, int reps) {
  double spread = 0;
  double cyc = time_stream<MODE>(tokens, reps, &spread);
  printf("STREAM %-18s %9.0f cyc/token  (5.83M dense-MAC => %5.2f MAC/cyc)  "
         "spread %.1f%%\n",
         name, cyc, 5829504.0 / cyc, 100 * spread);
  fflush(stdout);
}

template <Mode MODE>
static void report_classes(const char* name, int tokens) {
  double macs[NCLS], cyc[NCLS], dpm;
  per_class<MODE>(tokens, macs, cyc, &dpm);
  double tot = 0;
  for (int c = 0; c < NCLS; c++) tot += cyc[c];
  printf("CLASSES %s (instrumented; per-token):\n", name);
  for (int c = 0; c < NCLS; c++)
    printf("  %-11s %8.0f cyc  %9.0f MAC  %6.2f MAC/cyc%s\n", CLS_NAME[c],
           cyc[c], macs[c], macs[c] / cyc[c],
           c == C_DOWN ? "  (effective)" : "");
  printf("  %-11s %8.0f cyc (sum; clean stream is lower)\n", "TOTAL", tot);
  fflush(stdout);
}

int main(int argc, char** argv) {
  int tokens = argc > 1 ? atoi(argv[1]) : 1500;
  const char* mode = argc > 2 ? argv[2] : "all";
  const bool all = !strcmp(mode, "all");
  const bool only_sparse = !strcmp(mode, "sparse");
  pin_from_env();
  Calib c = calibrate();
  print_calib("bench_qmat", c);
  measure_stamp_cost();

  build_all();

  // ---- headline streams (clean timing) ----
  if (all) {
    report_stream<M_NAIVE>("naive", tokens / 4, 5);
    report_stream<M_DENSE>("dense_prod", tokens, 5);
    report_stream<M_DENSE_ALLA>("dense_allA", tokens, 5);
    report_stream<M_DENSE_ALLA_NOPF>("dense_allA_nopf", tokens, 5);
    report_stream<M_PACKED_ALLA>("packed_allA", tokens, 5);
  }
  report_stream<M_SPARSE>("sparse_prod", tokens, 5);
  {
    double c_sp = time_stream<M_SPARSE>(tokens, 5);
    double c_nd = time_stream<M_SPARSE_NODOWN>(tokens, 5);
    printf("MARGINAL sparse mlp.down (clean-stream diff/12): %.0f cyc/matmul "
           "(stream %.0f vs nodown %.0f)\n",
           (c_sp - c_nd) / 12.0, c_sp, c_nd);
    fflush(stdout);
  }
  if (all) report_stream<M_DENSE>("dense_prod2", tokens, 5);

  // ---- per-class instrumented ----
  if (all) {
    report_classes<M_NAIVE>("naive", tokens / 8);
    report_classes<M_DENSE_ALLA>("dense_allA", tokens / 2);
    report_classes<M_DENSE>("dense_prod", tokens / 2);
  }
  report_classes<M_SPARSE>("sparse_prod", tokens / 2);

  // ---- density sweep for the sparse down kernel ----
  printf("SWEEP mlp.down (per-matmul cyc, 147456 dense-MAC; row-dense G4 for "
         "reference comes from dense_prod class above)\n");
  for (int cl = 0; cl <= 1; cl++) {
    for (float d : {0.05f, 0.11f, 0.15f, 0.22f, 0.33f, 0.44f, 0.55f, 0.66f,
                    0.77f, 0.88f, 1.0f}) {
      if (only_sparse && cl == 0 && d != 0.11f && d != 0.15f && d != 0.22f &&
          d != 0.44f)
        continue;
      if (only_sparse && cl == 1) continue;
      make_patterns(d, cl == 1);
      double macs[NCLS], cyc[NCLS], dpm_s8, dpm_s4, dpm_cd8, dpm_cd4;
      per_class<M_SWEEP_SPARSE>(tokens / 4, macs, cyc, &dpm_s8);
      per_class<M_SWEEP_SPARSE4>(tokens / 4, macs, cyc, &dpm_s4);
      double eff4 = macs[C_DOWN] / cyc[C_DOWN];
      per_class<M_SWEEP_COLDENSE>(tokens / 4, macs, cyc, &dpm_cd8);
      per_class<M_SWEEP_COLDENSE4>(tokens / 4, macs, cyc, &dpm_cd4);
      printf("  dens %.2f %-9s sp8 %6.0f  sp4 %6.0f cyc (%5.2f eff-MAC/cyc)  "
             "cd8 %6.0f  cd4 %6.0f cyc\n",
             d, cl ? "clustered" : "iid", dpm_s8, dpm_s4, eff4, dpm_cd8,
             dpm_cd4);
      fflush(stdout);
    }
  }

  // theoretical floors for context
  printf("# floors: ALU 32 MAC/cyc => 182.2 Kcyc; L3 ~23 B/cyc on 6.15 MB "
         "stream => ~265 Kcyc (dense)\n");
  g_dummy_i32 = (int32_t)g_sink;
  return 0;
}
