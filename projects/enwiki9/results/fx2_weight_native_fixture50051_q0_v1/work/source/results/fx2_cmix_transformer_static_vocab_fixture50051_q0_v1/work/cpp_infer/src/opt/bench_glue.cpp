// bench_glue: cycles for the opt vec_math + glue ops (core cycles via the
// bench_common.h calibration; pin with BENCH_CPU, default 107).
//
// "dep" numbers are dependent-chain (each call's input depends on the
// previous call's output — the realistic serial critical-path cost);
// "tput" numbers let independent iterations overlap.
#include "../../bench/bench_common.h"

#include <cstdint>
#include <cstring>

#include "glue.h"
#include "vec_math.h"

static uint64_t g_rng = 0x243F6A8885A308D3ULL;
static uint64_t rnd64() {
  uint64_t x = g_rng;
  x ^= x << 13;
  x ^= x >> 7;
  x ^= x << 17;
  return g_rng = x;
}
static float rnd_normal() {
  float s = 0;
  for (int i = 0; i < 12; i++)
    s += static_cast<float>((rnd64() >> 40) * (1.0 / 16777216.0));
  return s - 6.0f;
}

static volatile float g_fsink;

// ---------------- vec math: cycles/element on L1-resident 4096 ----------------
template <__m256 F(__m256)>
__attribute__((noinline)) static void vec_pass(const float* in, float* out, int n) {
  for (int i = 0; i < n; i += 32) {
    _mm256_store_ps(out + i + 0, F(_mm256_load_ps(in + i + 0)));
    _mm256_store_ps(out + i + 8, F(_mm256_load_ps(in + i + 8)));
    _mm256_store_ps(out + i + 16, F(_mm256_load_ps(in + i + 16)));
    _mm256_store_ps(out + i + 24, F(_mm256_load_ps(in + i + 24)));
  }
}
template <float F(float)>
__attribute__((noinline)) static void libm_pass(const float* in, float* out, int n) {
  for (int i = 0; i < n; i++) out[i] = F(in[i]);
}

template <typename F>
static double time_rate(F onepass, double units_per_pass, double target_s = 0.03) {
  onepass();
  uint64_t t0 = rdtsc_ser();
  onepass();
  uint64_t one = rdtsc_ser() - t0;
  if (one < 1000) one = 1000;
  uint64_t P = (uint64_t)(target_s * g_cal.tsc_hz / (double)one);
  if (P < 2) P = 2;
  t0 = rdtsc_ser();
  for (uint64_t i = 0; i < P; i++) onepass();
  double cyc = ticks_to_cycles((double)(rdtsc_ser() - t0));
  return cyc / (units_per_pass * P);  // cycles per unit
}

// cycles/call for a closure, median of 5
template <typename F>
static double cycles_per_call(F call, int iters) {
  auto run = [&] {
    uint64_t t0 = rdtsc_ser();
    for (int i = 0; i < iters; i++) call();
    return ticks_to_cycles((double)(rdtsc_ser() - t0)) / iters;
  };
  Stats s = repeat_stat(run, 5, 1);
  return s.med;
}

int main() {
  if (!getenv("BENCH_CPU")) setenv("BENCH_CPU", "107", 0);
  pin_from_env();
  Calib c = calibrate();
  print_calib("bench_glue", c);

  // ---------------- vec math ----------------
  {
    const int NE = 4096;
    float* ein = (float*)alloc_buf(NE * 4);
    float* epos = (float*)alloc_buf(NE * 4);
    float* eout = (float*)alloc_buf(NE * 4);
    for (int i = 0; i < NE; i++) {
      ein[i] = -30.0f + 60.0f * (float)i / NE;
      epos[i] = 1e-6f + 1000.0f * (float)i / NE;
    }
    printf("\n== vec_math cycles/element (L1, 4096 elems) ==\n");
    struct Row { const char* name; double c; };
    auto meas = [&](auto pass, const float* in) {
      Stats s = repeat_stat([&] { return time_rate([&] { pass(in, eout, NE); }, NE); });
      g_fsink = eout[7];
      return s.med;
    };
    double ce = meas(vec_pass<fx2::exp256_ps>, ein);
    double cl = meas(vec_pass<fx2::log256_ps>, epos);
    double c1 = meas(vec_pass<fx2::log1p256_ps>, epos);
    double cs = meas(vec_pass<fx2::sigmoid256_ps>, ein);
    double cz = meas(vec_pass<fx2::silu256_ps>, ein);
    double cp = meas(vec_pass<fx2::softplus256_ps>, ein);
    double ct = meas(vec_pass<fx2::tanh256_ps>, ein);
    double lt = meas(libm_pass<tanhf>, ein);
    double lx = meas(libm_pass<expf>, ein);
    printf("  exp256      %5.2f c/elem\n", ce);
    printf("  log256      %5.2f c/elem\n", cl);
    printf("  log1p256    %5.2f c/elem\n", c1);
    printf("  sigmoid256  %5.2f c/elem\n", cs);
    printf("  silu256     %5.2f c/elem\n", cz);
    printf("  softplus256 %5.2f c/elem\n", cp);
    printf("  tanh256     %5.2f c/elem   (libm tanhf %.1f => %.0fx)\n", ct, lt, lt / ct);
    printf("  [libm expf  %5.2f c/elem]\n", lx);
    fflush(stdout);
  }

  // ---------------- glue ops ----------------
  alignas(64) static float x[192], xn[192], tok[192], y192[192], h768[768];
  alignas(64) static float logits_src[208], l[208], probs[208];
  alignas(64) static uint8_t q[8 * 192], q768[768];
  alignas(64) static uint16_t pf16[208], probs16[208];
  alignas(64) static float p208[208];
  float s5[5] = {0.02f, 0.017f, 0.031f, 0.024f, 0.011f};
  for (int i = 0; i < 192; i++) x[i] = rnd_normal();
  for (int i = 0; i < 192; i++) tok[i] = rnd_normal();
  for (int i = 0; i < 192; i++) y192[i] = rnd_normal();
  for (int i = 0; i < 768; i++) h768[i] = rnd_normal() * 2.0f;
  for (int i = 0; i < 205; i++) logits_src[i] = rnd_normal() * 5.0f;
  std::memset(pf16, 0, sizeof(pf16));
  for (int k = 0; k < 15; k++)
    pf16[rnd64() % 205] = _cvtss_sh(0.05f + 0.1f * (float)(k % 7),
                                    _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
  fx2::SparseActs sp;

  printf("\n== glue ops, cycles/call (L1-hot; dep = dependent chain) ==\n");

  // rms_norm_quant, hot x, dependent chain via q feedback into x[0]
  {
    const float x0 = x[0];
    auto dep = [&](int m) {
      return cycles_per_call(
          [&] {
            fx2::opt::rms_norm_quant192_multi(x, xn, s5, m, q);
            x[0] = x0 + 1e-40f * (float)q[0];
          },
          20000);
    };
    auto tput = [&](int m) {
      return cycles_per_call([&] { fx2::opt::rms_norm_quant192_multi(x, xn, s5, m, q); }, 20000);
    };
    printf("  rms_norm_quant192 m=1   %6.1f dep  %6.1f tput\n", dep(1), tput(1));
    printf("  rms_norm_quant192 m=3   %6.1f dep  %6.1f tput   (vanilla qkv triple)\n", dep(3), tput(3));
    printf("  rms_norm_quant192 m=5   %6.1f dep  %6.1f tput   (kimi qkv+fg+og)\n", dep(5), tput(5));
    x[0] = x0;
  }
  // cold-ish x: pool walked with a large stride (defeats next-line prefetch),
  // dependent chain through the pool index
  {
    for (size_t foot : {size_t(340), size_t(8192)}) {  // ~256 KB, ~6 MB pools
      float* pool = (float*)alloc_buf(foot * 192 * 4);
      for (size_t i = 0; i < foot * 192; i++) pool[i] = rnd_normal();
      size_t idx = 0;
      auto cold = [&](int m) {
        return cycles_per_call(
            [&] {
              const float* xp = pool + idx * 192;
              fx2::opt::rms_norm_quant192_multi(xp, xn, s5, m, q);
              idx = (idx + 97 + (q[0] & 1)) % foot;
            },
            foot > 1000 ? 20000 : 8000);
      };
      const char* lvl = foot > 1000 ? "L3" : "L2";
      printf("  rms_norm_quant192 m=3   %6.1f dep   (x cold from %s pool %.1f MB)\n",
             cold(3), lvl, foot * 768.0 / 1048576.0);
      printf("  rms_norm_quant192 m=5   %6.1f dep   (x cold from %s pool)\n", cold(5), lvl);
    }
  }
  {
    alignas(32) static int8_t qs8[64];
    double a = cycles_per_call([&] { fx2::opt::quant192_u8(x, 0.02f, q); g_fsink = (float)q[0]; }, 20000);
    double b = cycles_per_call([&] { fx2::opt::quant64_u8(x, 0.02f, q); g_fsink = (float)q[0]; }, 20000);
    double b8 = cycles_per_call([&] { fx2::opt::quant64_i8(x, 0.02f, qs8); g_fsink = (float)qs8[0]; }, 20000);
    double r2 = cycles_per_call([&] { fx2::opt::relu2_quant768(h768, 0.02f, q768); g_fsink = (float)q768[0]; }, 20000);
    printf("  quant192_u8             %6.1f\n", a);
    printf("  quant64_u8              %6.1f\n", b);
    printf("  quant64_i8              %6.1f\n", b8);
    printf("  relu2_quant768          %6.1f\n", r2);
  }
  {
    double a = cycles_per_call([&] { fx2::opt::rms_norm192(x, xn); g_fsink = xn[0]; }, 20000);
    double b = cycles_per_call([&] { fx2::opt::rms_norm64(x, xn); g_fsink = xn[0]; }, 20000);
    printf("  rms_norm192             %6.1f\n", a);
    printf("  rms_norm64              %6.1f\n", b);
  }
  {  // residual ops, dependent by nature (in-place)
    double a = cycles_per_call([&] { fx2::opt::axpby_tok192(0.98f, x, 0.11f, tok); }, 20000);
    double b = cycles_per_call([&] { fx2::opt::add192(x, y192); }, 20000);
    double cc = cycles_per_call([&] { fx2::opt::add_scaled192(x, 0.31f, y192); }, 20000);
    for (int i = 0; i < 192; i++) x[i] = rnd_normal();  // renormalize
    printf("  axpby_tok192            %6.1f\n", a);
    printf("  add192                  %6.1f\n", b);
    printf("  add_scaled192           %6.1f\n", cc);
  }
  {  // rope
    alignas(64) static float sn[32], cs[32];
    for (int i = 0; i < 32; i++) { sn[i] = 0.6f; cs[i] = 0.8f; }
    double a = cycles_per_call([&] { fx2::opt::rope_apply_64(x, sn, cs); }, 20000);
    double b = cycles_per_call([&] { fx2::opt::rope_apply_192(x, sn, cs); }, 20000);
    for (int i = 0; i < 192; i++) x[i] = rnd_normal();
    printf("  rope_apply_64           %6.1f\n", a);
    printf("  rope_apply_192          %6.1f\n", b);
  }
  {  // prior path
    double a = cycles_per_call([&] { fx2::opt::prior_f16_to_f32(pf16, p208); g_fsink = p208[0]; }, 20000);
    double braw = cycles_per_call(
        [&] {
          fx2::opt::prior_quant_raw(p208, 0.005f, q);
          g_fsink = (float)q[0];
        },
        20000);
    printf("  prior_quant_raw         %6.1f   (qmat contract; + their qsparse_make_idx)\n", braw);
    double b = cycles_per_call(
        [&] {
          fx2::opt::prior_quant(p208, 0.005f, q, &sp);
          g_fsink = (float)sp.n;
        },
        20000);
    // dense prior
    alignas(64) static float pdense[208];
    for (int i = 0; i < 205; i++) pdense[i] = 0.004f + 0.0001f * (i % 32);
    pdense[205] = pdense[206] = pdense[207] = 0.0f;
    double bd = cycles_per_call(
        [&] {
          fx2::opt::prior_quant(pdense, 0.005f, q, &sp);
          g_fsink = (float)sp.n;
        },
        20000);
    double e = cycles_per_call([&] { fx2::opt::embed_combine192(tok, y192, x); }, 20000);
    for (int i = 0; i < 192; i++) x[i] = rnd_normal();
    printf("  prior_f16_to_f32        %6.1f\n", a);
    printf("  prior_quant (~15 nz)    %6.1f\n", b);
    printf("  prior_quant (dense 205) %6.1f\n", bd);
    printf("  embed_combine192        %6.1f\n", e);
  }
  {  // head: copy-in + softcap+softmax (+f16); subtract bare copy loop
    double bare = cycles_per_call(
        [&] {
          std::memcpy(l, logits_src, sizeof(l));
          logits_src[0] += 1e-40f * probs[0];
        },
        20000);
    double head = cycles_per_call(
        [&] {
          std::memcpy(l, logits_src, sizeof(l));
          fx2::opt::head_softcap_softmax(l, probs);
          logits_src[0] += 1e-40f * probs[0];
        },
        20000);
    double headf16 = cycles_per_call(
        [&] {
          std::memcpy(l, logits_src, sizeof(l));
          fx2::opt::head_softcap_softmax(l, probs);
          fx2::opt::probs_to_f16(probs, probs16);
          logits_src[0] += 1e-40f * probs[0] + 1e-40f * (float)probs16[3];
        },
        20000);
    printf("  head_softcap_softmax    %6.1f   (copy-in overhead %.0f subtracted)\n",
           head - bare, bare);
    printf("  head + probs_to_f16     %6.1f\n", headf16 - bare);
    printf("  probs_to_f16 alone      %6.1f\n", headf16 - head);
  }

  // ---------------- per-token glue estimate ----------------
  printf("\n== estimated 'everything else' glue cost per token (from dep numbers above) ==\n");
  printf("  9 kimi:  m=5 rmsq + oproj q192 + 2x q64 | 3 van: m=3 rmsq + oproj q192\n");
  printf("  12 mlp:  m=1 rmsq + relu2q768 | 12x axpby+2xadd | 6x add_scaled\n");
  printf("  head:    m=1 rmsq + softcap/softmax | embed: f16conv+priorq+combine\n");
  printf("  18x rms_norm64 + 6x rope_apply_192 (vanilla q/k)\n");

  Calib c2 = calibrate(true, 0.1);
  print_calib("bench_glue_end", c2);
  return 0;
}
