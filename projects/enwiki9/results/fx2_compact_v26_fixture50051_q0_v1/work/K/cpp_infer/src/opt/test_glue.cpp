// test_glue: exactness of src/opt vec_math.h + glue.{h,cpp}
// - vec math: max ulp vs double-precision libm over the contract ranges
// - glue ops: BIT-EXACT vs the naive reference (src/kernels.cpp + the
//   model.cpp loop shapes), 10k random vectors + edge cases
// - head: per-element divergence (tanh256/exp256 replace libm) + effect on
//   -log p[target]
#include <immintrin.h>

#include <cfloat>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <algorithm>

#include "../kernels.h"
#include "glue.h"
#include "vec_math.h"

static int g_fail = 0;
#define CHECK(cond, ...)                                  \
  do {                                                    \
    if (!(cond)) {                                        \
      std::printf("FAIL %s:%d: ", __FILE__, __LINE__);    \
      std::printf(__VA_ARGS__);                           \
      std::printf("\n");                                  \
      g_fail++;                                           \
    }                                                     \
  } while (0)

// ---------------- rng ----------------
static uint64_t g_rng = 0x9E3779B97F4A7C15ULL;
static uint64_t rnd64() {
  uint64_t x = g_rng;
  x ^= x << 13;
  x ^= x >> 7;
  x ^= x << 17;
  return g_rng = x;
}
static float rndu() {  // [0,1)
  return static_cast<float>((rnd64() >> 40) * (1.0 / 16777216.0));
}
static float rndrange(float lo, float hi) { return lo + (hi - lo) * rndu(); }
static float rnd_normal() {  // approx N(0,1)
  float s = 0;
  for (int i = 0; i < 12; i++) s += rndu();
  return s - 6.0f;
}

// ---------------- ulp ----------------
static double ulp_err(float res, double ref) {
  if (std::isnan(ref) || std::isnan(res)) return 1e18;
  if (ref == 0.0) return res == 0.0f ? 0.0 : 1e18;
  if (std::isinf(ref)) return std::isinf(res) && ((res > 0) == (ref > 0)) ? 0.0 : 1e18;
  int e = std::ilogb(std::fabs(ref));
  if (e < -126) e = -126;
  double u = std::ldexp(1.0, e - 23);
  return std::fabs(static_cast<double>(res) - ref) / u;
}

// ---------------- vec math sweeps ----------------
struct SweepResult {
  double maxulp = 0;
  float worst = 0;
};

template <typename VF, typename RF>
static void sweep_vals(VF vf, RF rf, const float* xs, int n, SweepResult* sr) {
  for (int i = 0; i + 8 <= n; i += 8) {
    __m256 v = _mm256_loadu_ps(xs + i);
    alignas(32) float out[8];
    _mm256_store_ps(out, vf(v));
    for (int j = 0; j < 8; j++) {
      double u = ulp_err(out[j], rf(static_cast<double>(xs[i + j])));
      if (u > sr->maxulp) {
        sr->maxulp = u;
        sr->worst = xs[i + j];
      }
    }
  }
}

template <typename VF, typename RF>
static SweepResult sweep_range(VF vf, RF rf, double lo, double hi, long n,
                               bool logspace) {
  SweepResult sr;
  const int B = 4096;
  float buf[B];
  long done = 0;
  while (done < n) {
    int m = static_cast<int>(std::min<long>(B, n - done));
    for (int i = 0; i < m; i++) {
      double t = (rnd64() >> 11) * 0x1p-53;
      double x;
      if (logspace) {
        x = lo * std::exp(t * std::log(hi / lo));
      } else {
        x = lo + t * (hi - lo);
      }
      buf[i] = static_cast<float>(x);
    }
    for (int i = m; i < ((m + 7) & ~7); i++) buf[i] = buf[0];
    sweep_vals(vf, rf, buf, (m + 7) & ~7, &sr);
    done += m;
  }
  return sr;
}

static double ref_sigmoid(double x) { return 1.0 / (1.0 + std::exp(-x)); }
static double ref_silu(double x) { return x / (1.0 + std::exp(-x)); }
// threshold semantics on the FLOAT input, exactly like naive softplus20f
static double ref_softplus(double x) {
  return (static_cast<float>(x) > 20.0f) ? x : std::log1p(std::exp(x));
}

static void vec_math_accuracy() {
  std::printf("== vec_math accuracy (max ulp vs double libm) ==\n");
  struct Row {
    const char* name;
    double budget;
    SweepResult sr;
  };

  auto vexp = [](__m256 v) { return fx2::exp256_ps(v); };
  auto vlog = [](__m256 v) { return fx2::log256_ps(v); };
  auto vl1p = [](__m256 v) { return fx2::log1p256_ps(v); };
  auto vsig = [](__m256 v) { return fx2::sigmoid256_ps(v); };
  auto vsil = [](__m256 v) { return fx2::silu256_ps(v); };
  auto vsp = [](__m256 v) { return fx2::softplus256_ps(v); };
  auto vth = [](__m256 v) { return fx2::tanh256_ps(v); };

  auto report = [](const char* name, const char* range, SweepResult sr,
                   double budget) {
    bool ok = sr.maxulp <= budget;
    std::printf("  %-13s %-14s max ulp %6.3f  at x=% .9g   budget %.1f  %s\n",
                name, range, sr.maxulp, sr.worst, budget, ok ? "ok" : "FAIL");
    if (!ok) g_fail++;
  };

  {
    SweepResult a = sweep_range(vexp, [](double x) { return std::exp(x); },
                                -30, 30, 8'000'000, false);
    // structural limit of the cephes scheme is ~1.0 ulp (8e-8 rel, the
    // "0.7-ulp-ish" of MACHINE.md measured in per-binade ulps)
    report("exp256", "[-30,30]", a, 1.1);
  }
  {
    SweepResult a = sweep_range(vlog, [](double x) { return std::log(x); },
                                1e-9, 1e3, 8'000'000, true);
    SweepResult b = sweep_range(vlog, [](double x) { return std::log(x); },
                                0.5, 2.0, 8'000'000, false);
    if (b.maxulp > a.maxulp) a = b;
    report("log256", "[1e-9,1e3]", a, 2.0);
  }
  {
    SweepResult a = sweep_range(vl1p, [](double x) { return std::log1p(x); },
                                9e-14, 1e13, 8'000'000, true);
    SweepResult b = sweep_range(vl1p, [](double x) { return std::log1p(x); },
                                0.0, 4.0, 4'000'000, false);
    if (b.maxulp > a.maxulp) a = b;
    report("log1p256", "[9e-14,1e13]", a, 2.0);
  }
  {
    SweepResult a = sweep_range(vsig, ref_sigmoid, -30, 30, 8'000'000, false);
    SweepResult b = sweep_range(vsig, ref_sigmoid, -1e-3, 1e-3, 2'000'000, false);
    if (b.maxulp > a.maxulp) a = b;
    report("sigmoid256", "[-30,30]", a, 2.0);
  }
  {
    // floor ~2.5-2.8: exp256's ~1.0 ulp passes through + mul/div/corr chain
    SweepResult a = sweep_range(vsil, ref_silu, -30, 30, 8'000'000, false);
    SweepResult b = sweep_range(vsil, ref_silu, -1e-3, 1e-3, 2'000'000, false);
    if (b.maxulp > a.maxulp) a = b;
    report("silu256", "[-30,30]", a, 3.0);
  }
  {
    // floor ~2.4: exp256's ~1.0 ulp passes through + log1p chain
    SweepResult a = sweep_range(vsp, ref_softplus, -30, 30, 8'000'000, false);
    SweepResult b = sweep_range(vsp, ref_softplus, 19.0, 21.0, 2'000'000, false);
    if (b.maxulp > a.maxulp) a = b;
    report("softplus256", "[-30,30]", a, 2.5);
  }
  {
    SweepResult a = sweep_range(vth, [](double x) { return std::tanh(x); },
                                -20, 20, 8'000'000, false);
    report("tanh256", "[-20,20]", a, 2.0);
    SweepResult c = sweep_range(vth, [](double x) { return std::tanh(x); },
                                -1.5, 1.5, 16'000'000, false);
    report("tanh256", "[-1.5,1.5]", c, 2.0);
    SweepResult d = sweep_range(vth, [](double x) { return std::tanh(x); },
                                1e-30, 1.0, 4'000'000, true);
    SweepResult e = sweep_range(vth, [](double x) { return std::tanh(x); },
                                -1.0, -1e-30, 4'000'000, false);
    if (e.maxulp > d.maxulp) d = e;
    report("tanh256", "near0/log", d, 2.0);
  }

  // point checks
  alignas(32) float in[8] = {0.0f, -0.0f, 20.0f, std::nextafterf(20.0f, 30.0f),
                             1e-41f, -1e-41f, 88.0f, -30.0f};
  alignas(32) float out[8];
  _mm256_store_ps(out, fx2::tanh256_ps(_mm256_load_ps(in)));
  CHECK(out[0] == 0.0f && !std::signbit(out[0]), "tanh(+0) != +0");
  CHECK(out[1] == 0.0f && std::signbit(out[1]), "tanh(-0) != -0");
  _mm256_store_ps(out, fx2::sigmoid256_ps(_mm256_setzero_ps()));
  CHECK(out[0] == 0.5f, "sigmoid(0) != 0.5");
  _mm256_store_ps(out, fx2::softplus256_ps(_mm256_load_ps(in)));
  CHECK(out[3] == in[3], "softplus(x>20) must return x");
  {
    double r = std::log1p(std::exp(20.0));
    CHECK(ulp_err(out[2], r) <= 2.0, "softplus(20) off: %g vs %g", out[2], r);
  }
  _mm256_store_ps(out, fx2::silu256_ps(_mm256_load_ps(in)));
  CHECK(out[1] == 0.0f && std::signbit(out[1]), "silu(-0) != -0");
}

// ---------------- glue: rms-norm + quant vs naive ----------------
static void fill_x(float* x, int n, int kind) {
  float scale = 1.0f;
  switch (kind % 6) {
    case 0: scale = 1.0f; break;
    case 1: scale = 1e-3f; break;
    case 2: scale = 1e3f; break;
    case 3: scale = 30.0f; break;
    case 4: scale = 1e-6f; break;
    case 5: scale = 1e5f; break;
  }
  for (int i = 0; i < n; i++) x[i] = rnd_normal() * scale;
  if (kind % 7 == 3) x[rnd64() % n] = 0.0f;
  if (kind % 11 == 5) x[rnd64() % n] = -0.0f;
  if (kind % 13 == 7) x[rnd64() % n] = 1e-41f;  // subnormal (FTZ off)
}

static float rnd_scale() {
  // positive, bf16-rounded like real activation scales, wide magnitude range
  float s = std::ldexp(1.0f + rndu(), static_cast<int>(rnd64() % 17) - 10);
  uint32_t b;
  std::memcpy(&b, &s, 4);
  b = (b + 0x8000u) & 0xFFFF0000u;  // bf16 round-to-nearest-even-ish
  std::memcpy(&s, &b, 4);
  return s;
}

static void naive_rmsq(const float* x, int n, float* xn, const float* s, int m,
                       uint8_t* q) {
  fx2::rms_norm_vec(x, xn, n);
  for (int k = 0; k < m; k++) {
    int8_t tmp[192];
    fx2::quantize_i8(xn, n, n, s[k], tmp);
    for (int i = 0; i < n; i++) q[k * 192 + i] = static_cast<uint8_t>(tmp[i] ^ 0x80);
  }
}

static void test_rms_norm_quant() {
  std::printf("== rms_norm_quant vs naive (bit-exact) ==\n");
  alignas(32) float x[192], xn_ref[192], xn_opt[192];
  alignas(32) uint8_t q_ref[8 * 192], q_opt[8 * 192];
  float s[8];
  long sat_lo = 0, sat_hi = 0;
  const int trials = 10000;
  for (int t = 0; t < trials; t++) {
    fill_x(x, 192, t);
    int m = 1 + static_cast<int>(rnd64() % 7);  // 1..7 (exercises generic too)
    for (int k = 0; k < m; k++) s[k] = rnd_scale();
    if (t % 9 == 0) s[0] = 1e-6f;  // force saturation
    naive_rmsq(x, 192, xn_ref, s, m, q_ref);
    fx2::opt::rms_norm_quant192_multi(x, xn_opt, s, m, q_opt);
    CHECK(std::memcmp(xn_ref, xn_opt, sizeof(xn_ref)) == 0,
          "xn mismatch t=%d", t);
    CHECK(std::memcmp(q_ref, q_opt, static_cast<size_t>(m) * 192) == 0,
          "q mismatch t=%d m=%d", t, m);
    for (int i = 0; i < m * 192; i++) {
      if (q_ref[i] == 0) sat_lo++;
      if (q_ref[i] == 255) sat_hi++;
    }
    // x3 and x1 wrappers
    if (m >= 3) {
      alignas(32) uint8_t a[192], b[192], c[192];
      fx2::opt::rms_norm_quant192_x3(x, xn_opt, s, a, b, c);
      CHECK(std::memcmp(a, q_ref, 192) == 0 &&
                std::memcmp(b, q_ref + 192, 192) == 0 &&
                std::memcmp(c, q_ref + 384, 192) == 0,
            "x3 mismatch t=%d", t);
    }
    fx2::opt::rms_norm_quant192(x, xn_opt, s[0], q_opt);
    CHECK(std::memcmp(q_opt, q_ref, 192) == 0, "x1 mismatch t=%d", t);
    CHECK(std::memcmp(xn_ref, xn_opt, sizeof(xn_ref)) == 0, "x1 xn t=%d", t);
  }
  std::printf("  10k trials ok (saturated lanes: %ld low, %ld high)\n",
              sat_lo, sat_hi);

  // all-zero x: denom = sqrt(FLT_EPSILON), xn = 0, q = biased 128
  std::memset(x, 0, sizeof(x));
  float s3[3] = {rnd_scale(), rnd_scale(), rnd_scale()};
  naive_rmsq(x, 192, xn_ref, s3, 3, q_ref);
  fx2::opt::rms_norm_quant192_multi(x, xn_opt, s3, 3, q_opt);
  CHECK(std::memcmp(xn_ref, xn_opt, sizeof(xn_ref)) == 0, "zero-x xn");
  CHECK(std::memcmp(q_ref, q_opt, 3 * 192) == 0, "zero-x q");
  CHECK(fx2::opt::rms_denom192(x) == std::sqrt(FLT_EPSILON), "zero-x denom");
  for (int i = 0; i < 3 * 192; i++)
    CHECK(q_opt[i] == 128, "zero-x biased q not 128");

  // rms_norm64 / rms_norm192 / rms_denom
  for (int t = 0; t < 2000; t++) {
    fill_x(x, 192, t);
    fx2::rms_norm_vec(x, xn_ref, 192);
    fx2::opt::rms_norm192(x, xn_opt);
    CHECK(std::memcmp(xn_ref, xn_opt, 192 * 4) == 0, "rms_norm192 t=%d", t);
    fx2::rms_norm_vec(x, xn_ref, 64);
    fx2::opt::rms_norm64(x, xn_opt);
    CHECK(std::memcmp(xn_ref, xn_opt, 64 * 4) == 0, "rms_norm64 t=%d", t);
  }
  std::printf("  rms_norm64/192, zero-x, saturation: ok\n");
}

static void test_plain_quant() {
  std::printf("== quant192/64_u8, relu2_quant768 vs naive ==\n");
  alignas(32) float x[768];
  alignas(32) int8_t qi[768];
  alignas(32) uint8_t qr[768], qo[768];
  for (int t = 0; t < 10000; t++) {
    fill_x(x, 768, t);
    float s = rnd_scale();
    if (t % 9 == 0) s = 1e-6f;
    fx2::quantize_i8(x, 192, 192, s, qi);
    for (int i = 0; i < 192; i++) qr[i] = static_cast<uint8_t>(qi[i] ^ 0x80);
    fx2::opt::quant192_u8(x, s, qo);
    CHECK(std::memcmp(qr, qo, 192) == 0, "quant192 t=%d", t);
    fx2::quantize_i8(x, 64, 64, s, qi);
    for (int i = 0; i < 64; i++) qr[i] = static_cast<uint8_t>(qi[i] ^ 0x80);
    fx2::opt::quant64_u8(x, s, qo);
    CHECK(std::memcmp(qr, qo, 64) == 0, "quant64 t=%d", t);
    {  // plain-int8 variant (attention per-head post-rope quant)
      alignas(32) int8_t qs8[64];
      fx2::opt::quant64_i8(x, s, qs8);
      CHECK(std::memcmp(qi, qs8, 64) == 0, "quant64_i8 t=%d", t);
    }
    // relu^2 then quantize, unbiased
    float h2[768];
    for (int i = 0; i < 768; i++) {
      float hj = x[i];
      h2[i] = hj > 0.0f ? hj * hj : 0.0f;  // model.cpp shape
    }
    fx2::quantize_i8(h2, 768, 768, s, qi);
    fx2::opt::relu2_quant768(x, s, qo);
    CHECK(std::memcmp(qi, qo, 768) == 0, "relu2_quant768 t=%d", t);
  }
  std::printf("  10k trials ok\n");
}

// ---------------- residual ops ----------------
// reference loops with the EXACT model.cpp source shapes (same compile flags
// => same contraction as model.o; also cross-checked against explicit
// std::fma shapes below)
__attribute__((noinline)) static void ref_axpby(float a, float* x, float bcoef,
                                                const float* tok) {
  for (int i = 0; i < 192; i++) x[i] = a * x[i] + bcoef * tok[i];
}
__attribute__((noinline)) static void ref_addsc(float* x, float w,
                                                const float* s) {
  for (int i = 0; i < 192; i++) x[i] += w * s[i];
}
__attribute__((noinline)) static void ref_add(float* x, const float* y) {
  for (int i = 0; i < 192; i++) x[i] += y[i];
}

static void test_residual_ops() {
  std::printf("== residual/coefficient ops (bit-exact) ==\n");
  alignas(32) float x0[192], tok[192], xr[192], xo[192], xf[192];
  int shapeA = 0, shapeB = 0, shapeO = 0;
  for (int t = 0; t < 10000; t++) {
    fill_x(x0, 192, t);
    fill_x(tok, 192, t + 1);
    float a = rnd_normal(), b = rnd_normal(), w = rnd_normal();
    // axpby
    std::memcpy(xr, x0, sizeof(xr));
    std::memcpy(xo, x0, sizeof(xo));
    ref_axpby(a, xr, b, tok);
    fx2::opt::axpby_tok192(a, xo, b, tok);
    CHECK(std::memcmp(xr, xo, sizeof(xr)) == 0, "axpby t=%d", t);
    // contraction shape census (informational)
    for (int i = 0; i < 192; i++) {
      float fa = std::fma(a, x0[i], b * tok[i]);       // shape A (model.o)
      float fb = std::fma(b, tok[i], a * x0[i]);       // shape B
      float fo = a * x0[i] + b * tok[i];               // may itself contract
      (void)fo;
      if (xr[i] == fa || (std::isnan(xr[i]) && std::isnan(fa))) shapeA++;
      if (xr[i] == fb || (std::isnan(xr[i]) && std::isnan(fb))) shapeB++;
      shapeO++;
    }
    // add_scaled
    std::memcpy(xr, x0, sizeof(xr));
    std::memcpy(xo, x0, sizeof(xo));
    ref_addsc(xr, w, tok);
    fx2::opt::add_scaled192(xo, w, tok);
    CHECK(std::memcmp(xr, xo, sizeof(xr)) == 0, "add_scaled t=%d", t);
    for (int i = 0; i < 192; i++) xf[i] = std::fma(w, tok[i], x0[i]);
    CHECK(std::memcmp(xr, xf, sizeof(xr)) == 0, "add_scaled != fma(w,s,x) t=%d", t);
    // add
    std::memcpy(xr, x0, sizeof(xr));
    std::memcpy(xo, x0, sizeof(xo));
    ref_add(xr, tok);
    fx2::opt::add192(xo, tok);
    CHECK(std::memcmp(xr, xo, sizeof(xr)) == 0, "add t=%d", t);
  }
  std::printf("  10k trials ok; axpby contraction: fma(a,x,b*t) matched "
              "%d/%d lanes, fma(b,t,a*x) matched %d\n",
              shapeA, shapeO, shapeB);
}

// ---------------- rope ----------------
static void test_rope() {
  std::printf("== rope_apply_64/192 vs naive rope_apply (bit-exact) ==\n");
  alignas(32) float h1[192], h2[192], sn[32], cs[32];
  for (int t = 0; t < 10000; t++) {
    fill_x(h1, 192, t);
    std::memcpy(h2, h1, sizeof(h1));
    float ang0 = rndrange(0.0f, 6.2832f);
    for (int i = 0; i < 32; i++) {
      float ang = ang0 * std::pow(0.74f, i);
      sn[i] = std::sin(ang);
      cs[i] = std::cos(ang);
    }
    fx2::rope_apply(h1, sn, cs);
    fx2::opt::rope_apply_192(h2, sn, cs);
    CHECK(std::memcmp(h1, h2, sizeof(h1)) == 0, "rope t=%d", t);
  }
  std::printf("  10k trials ok\n");
}

// ---------------- prior path ----------------
static void test_prior_path() {
  std::printf("== prior f16->f32, quant + sparse extraction ==\n");
  uint16_t h[205];
  alignas(32) float pref[208], popt[208];
  alignas(32) uint8_t qb_ref[208], qb[208];
  alignas(32) int8_t qi[208];
  long nz_total = 0, clamp_hits = 0;
  for (int t = 0; t < 10000; t++) {
    // ~15 nonzeros typical; some dense, some empty, some saturating
    std::memset(h, 0, sizeof(h));
    int nnz = (t % 17 == 0) ? 205 : static_cast<int>(rnd64() % 31);
    for (int k = 0; k < nnz; k++) {
      int i = static_cast<int>(rnd64() % 205);
      float v = rndu();
      if (t % 5 == 0) v *= 300.0f;  // force clamp at 127 for small scales
      h[i] = _cvtss_sh(v, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
    }
    // conversion: naive = f16_to_f32 + explicit pad zero (model.cpp step)
    fx2::f16_to_f32(h, pref, 205);
    pref[205] = pref[206] = pref[207] = 0.0f;
    fx2::opt::prior_f16_to_f32(h, popt);
    CHECK(std::memcmp(pref, popt, sizeof(pref)) == 0, "f16 conv t=%d", t);
    // quant: naive quantize_i8(p, 205, 208, s) then bias
    float s = rnd_scale() * 0.01f;
    fx2::quantize_i8(pref, 205, 208, s, qi);
    for (int i = 0; i < 208; i++) qb_ref[i] = static_cast<uint8_t>(qi[i] ^ 0x80);
    fx2::SparseActs sp;
    fx2::opt::prior_quant(popt, s, qb, &sp);
    CHECK(std::memcmp(qb_ref, qb, 208) == 0, "prior quant t=%d", t);
    {  // raw variant (qmat contract): unbiased bytes == naive int8 bits
      alignas(32) uint8_t qraw[208];
      fx2::opt::prior_quant_raw(popt, s, qraw);
      CHECK(std::memcmp(qi, qraw, 208) == 0, "prior_quant_raw t=%d", t);
    }
    // sparse extraction vs scalar scan
    int n = 0;
    bool ok = true;
    for (int i = 0; i < 208; i++) {
      if (qi[i] != 0) {
        if (n >= sp.n || sp.idx[n] != i || sp.q[n] != qi[i]) ok = false;
        n++;
      }
      if (qi[i] == 127) clamp_hits++;
    }
    if (n != sp.n) ok = false;
    CHECK(ok, "sparse extraction t=%d (n=%d vs %d)", t, n, sp.n);
    nz_total += n;
    // sparse_cap: above the cap the dense vector must still be complete and
    // n must be the -1 sentinel; at/below the cap identical to uncapped
    if (t % 50 == 0) {
      fx2::SparseActs spc;
      alignas(32) uint8_t qb2[208];
      fx2::opt::prior_quant(popt, s, qb2, &spc, 10);
      CHECK(std::memcmp(qb_ref, qb2, 208) == 0, "capped qb t=%d", t);
      if (n > 10) {
        CHECK(spc.n == -1, "cap sentinel t=%d (n=%d spc.n=%d)", t, n, spc.n);
      } else {
        CHECK(spc.n == n && std::memcmp(spc.idx, sp.idx, n * 2) == 0 &&
                  std::memcmp(spc.q, sp.q, n) == 0,
              "capped extraction t=%d", t);
      }
    }
  }
  std::printf("  10k trials ok (mean nnz %.1f, clamped-to-127 lanes %ld)\n",
              nz_total / 10000.0, clamp_hits);
}

static void test_embed_combine() {
  std::printf("== embed_combine192 (bit-exact) ==\n");
  alignas(32) float tok[192], y[192], yn[192], xr[192], xo[192];
  for (int t = 0; t < 10000; t++) {
    fill_x(tok, 192, t);
    fill_x(y, 192, t + 3);
    fx2::rms_norm_vec(y, yn, 192);
    for (int i = 0; i < 192; i++) xr[i] = tok[i] + yn[i];  // model.cpp shape
    fx2::opt::embed_combine192(tok, y, xo);
    CHECK(std::memcmp(xr, xo, sizeof(xr)) == 0, "embed_combine t=%d", t);
  }
  // normed embedding table
  {
    int8_t eq[205 * 192];
    float sc[205];
    for (int i = 0; i < 205 * 192; i++)
      eq[i] = static_cast<int8_t>(static_cast<int>(rnd64() % 15) - 7);
    for (int c = 0; c < 205; c++) sc[c] = rnd_scale();
    static float tref[205 * 192], topt[205 * 192];
    for (int c = 0; c < 205; c++) {
      float* row = tref + c * 192;
      for (int i = 0; i < 192; i++) row[i] = static_cast<float>(eq[c * 192 + i]) * sc[c];
      fx2::rms_norm_vec(row, row, 192);
    }
    fx2::opt::build_normed_embedding_table(eq, sc, topt);
    CHECK(std::memcmp(tref, topt, sizeof(tref)) == 0, "embedding table");
  }
  std::printf("  10k trials + table ok\n");
}

// ---------------- head ----------------
static void naive_head(float* l, float* probs) {  // model.cpp semantics, libm
  for (int i = 0; i < 205; i++) l[i] = 15.0f * std::tanh(l[i] / 15.0f);
  float m = l[0];
  for (int i = 1; i < 205; i++)
    if (l[i] > m) m = l[i];
  float den = 0.0f;
  for (int i = 0; i < 205; i++) {
    float e = std::exp(l[i] - m);
    probs[i] = e;
    den += e;
  }
  for (int i = 0; i < 205; i++) probs[i] /= den;
}

static void double_head(const float* l, double* probs) {
  double lc[205];
  for (int i = 0; i < 205; i++)
    lc[i] = 15.0 * std::tanh(static_cast<double>(l[i]) / 15.0);
  double m = lc[0];
  for (int i = 1; i < 205; i++) m = std::max(m, lc[i]);
  double den = 0.0;
  for (int i = 0; i < 205; i++) {
    probs[i] = std::exp(lc[i] - m);
    den += probs[i];
  }
  for (int i = 0; i < 205; i++) probs[i] /= den;
}

static void test_head() {
  std::printf("== head softcap+softmax (tanh256/exp256 replace libm) ==\n");
  alignas(32) float raw[208], ln[208], lo[208], pn[208], po[208];
  double pd[205];
  double cap_vs_naive = 0, cap_vs_dbl = 0, capn_vs_dbl = 0;
  double p_vs_naive = 0, p_vs_dbl = 0, pn_vs_dbl = 0;
  double p_relmax = 0, dlogp_max = 0;
  long f16_mismatch = 0, f16_rows = 0;
  const int trials = 10000;
  for (int t = 0; t < trials; t++) {
    float sg = (t % 4 == 0) ? 1.0f : (t % 4 == 1 ? 5.0f : (t % 4 == 2 ? 20.0f : 100.0f));
    for (int i = 0; i < 205; i++) raw[i] = rnd_normal() * sg;
    if (t % 10 == 0) raw[rnd64() % 205] = 500.0f;  // tanh saturation
    std::memcpy(ln, raw, sizeof(float) * 205);
    naive_head(ln, pn);
    std::memcpy(lo, raw, sizeof(float) * 205);
    fx2::opt::head_softcap_softmax(lo, po);
    double_head(raw, pd);
    for (int i = 0; i < 205; i++) {
      cap_vs_naive = std::max(cap_vs_naive, ulp_err(lo[i], static_cast<double>(ln[i])));
      cap_vs_dbl = std::max(cap_vs_dbl,
                            ulp_err(lo[i], 15.0 * std::tanh(static_cast<double>(raw[i]) / 15.0)));
      capn_vs_dbl = std::max(capn_vs_dbl,
                             ulp_err(ln[i], 15.0 * std::tanh(static_cast<double>(raw[i]) / 15.0)));
      p_vs_naive = std::max(p_vs_naive, ulp_err(po[i], static_cast<double>(pn[i])));
      p_vs_dbl = std::max(p_vs_dbl, ulp_err(po[i], pd[i]));
      pn_vs_dbl = std::max(pn_vs_dbl, ulp_err(pn[i], pd[i]));
      if (pd[i] > 1e-12)
        p_relmax = std::max(p_relmax, std::fabs(po[i] - pd[i]) / pd[i]);
    }
    // -log p effect on plausible targets (p >= 1e-6)
    for (int i = 0; i < 205; i++) {
      if (pd[i] >= 1e-6) {
        double d = std::fabs(fx2::opt::neg_log_prob(po, i) - (-std::log(pd[i])));
        dlogp_max = std::max(dlogp_max, d);
      }
    }
    // pads
    CHECK(po[205] == 0.0f && po[206] == 0.0f && po[207] == 0.0f, "prob pads");
    CHECK(lo[205] == -15.0f && lo[207] == -15.0f, "logit pads");
    // f16 emit
    uint16_t f16n[205], f16o[205];
    fx2::opt::probs_to_f16(po, f16o);
    for (int i = 0; i < 205; i++)
      f16n[i] = _cvtss_sh(pn[i], _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
    bool rowdiff = false;
    for (int i = 0; i < 205; i++) {
      if (f16n[i] != f16o[i]) {
        f16_mismatch++;
        rowdiff = true;
        CHECK(std::abs(static_cast<int>(f16n[i]) - static_cast<int>(f16o[i])) <= 1,
              "f16 diff > 1 ulp t=%d i=%d", t, i);
      }
    }
    f16_rows += rowdiff;
    // sum check
    float sum = 0;
    for (int i = 0; i < 205; i++) sum += po[i];
    CHECK(std::fabs(sum - 1.0f) < 1e-5f, "probs don't sum to 1: %g", sum);
  }
  std::printf("  capped logits: max ulp vs naive-libm %.2f | mine vs double %.2f | naive vs double %.2f\n",
              cap_vs_naive, cap_vs_dbl, capn_vs_dbl);
  std::printf("  probs:         max ulp vs naive-libm %.2f | mine vs double %.2f | naive vs double %.2f\n",
              p_vs_naive, p_vs_dbl, pn_vs_dbl);
  std::printf("  probs max rel err vs double (p>1e-12): %.3g\n", p_relmax);
  std::printf("  max |delta(-log p[target])| (p>=1e-6):  %.3g nats\n", dlogp_max);
  std::printf("  f16 emit vs naive-libm-f16: %ld/%d rows differ (%ld lanes, all <=1 f16 ulp)\n",
              f16_rows, trials, f16_mismatch);
  // the full chain div(l,15) -> tanh -> mul(15,..) has 3 roundings plus slope
  // amplification; the naive libm chain itself measures ~3.5 ulp vs double.
  // Gate: no worse than naive + 1 ulp (tanh256 alone is <= 2 ulp, see above).
  CHECK(cap_vs_dbl <= capn_vs_dbl + 1.0, "capped logits much worse than naive");
  CHECK(cap_vs_dbl <= 4.5, "capped logits vs double > 4.5 ulp");
  CHECK(dlogp_max < 1e-4, "delta -log p too large");
}

int main() {
  std::printf("test_glue: opt vec_math + glue vs naive reference\n");
  unsigned mxcsr = _mm_getcsr();
  std::printf("MXCSR = 0x%04x (FTZ %s, DAZ %s — must be off to match naive)\n\n",
              mxcsr, (mxcsr & 0x8000) ? "ON" : "off", (mxcsr & 0x40) ? "ON" : "off");
  vec_math_accuracy();
  std::printf("\n");
  test_rms_norm_quant();
  test_plain_quant();
  test_residual_ops();
  test_rope();
  test_prior_path();
  test_embed_combine();
  test_head();
  std::printf("\n%s (%d failures)\n", g_fail == 0 ? "ALL PASS" : "FAILURES", g_fail);
  return g_fail == 0 ? 0 : 1;
}
