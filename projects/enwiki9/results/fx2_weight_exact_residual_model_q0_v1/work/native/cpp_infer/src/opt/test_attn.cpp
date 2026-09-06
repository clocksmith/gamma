// test_attn: exactness of the optimized attention kernels (attn.h) against
// the naive reference (src/kernels.h) on random inputs AND the captured real
// q/k/v of article22; covers var + fixed kernels, ring wraparound, articles
// shorter than the window, and the t=1023 -> 1024 transition. Also produces
// the real-data skip statistics: kept-count distribution and the exact-vs-skip
// output deviation.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <memory>
#include <random>
#include <vector>

#include "../kernels.h"
#include "attn.h"
#include "qkv_capture.h"

using fx2::opt::AttnKV;
using fx2::opt::AttnKV16;
using fx2::opt::AttnKVF32;

namespace {

int g_fail = 0;

struct Naive {
  int8_t k[1024][192];
  int8_t v[1024][192];
};

void naive_step(const Naive& ns, const int8_t* q, const float* coef,
                const float* sv, int n, float* out, float thr) {
  if (n < 1024)
    fx2::attention_step_var(q, ns.k[0], ns.v[0], coef, sv, n, out, thr);
  else
    fx2::attention_step_fixed(q, ns.k[0], ns.v[0], coef, sv, out, thr);
}

struct Diff {
  double max_abs = 0, rel = 0;
};
Diff diff192(const float* a, const float* b) {
  double ma = 0, ref = 0;
  for (int i = 0; i < 192; i++) {
    ma = std::max(ma, std::fabs(double(a[i]) - double(b[i])));
    ref = std::max(ref, std::fabs(double(b[i])));
  }
  return {ma, ma / std::max(ref, 1e-30)};
}

void gate(const char* what, const Diff& d, double rel_gate, int t, int n) {
  if (!(d.rel <= rel_gate) || !std::isfinite(d.max_abs)) {
    std::printf("FAIL %s: t=%d n=%d max_abs=%.3e rel=%.3e (gate %.0e)\n", what,
                t, n, d.max_abs, d.rel, rel_gate);
    g_fail++;
  }
}

void bitwise_gate(const char* what, const float* a, const float* b, int t) {
  if (std::memcmp(a, b, 192 * sizeof(float)) != 0) {
    Diff d = diff192(a, b);
    std::printf("FAIL %s not bitwise-equal: t=%d max_abs=%.3e\n", what, t,
                d.max_abs);
    g_fail++;
  }
}

// -------------------------------------------------------------------------
// random-input exactness: adversarial int8 data, garbage-prefilled rings
// (catches any read of a not-yet-valid slot), several article lengths
// -------------------------------------------------------------------------
void test_random() {
  std::mt19937 rng(12345);
  std::uniform_int_distribution<int> di8(-128, 127);
  std::uniform_real_distribution<float> dsc(0.004f, 0.05f);

  auto ns = std::make_unique<Naive>();
  auto kv8 = std::make_unique<AttnKV>();
  auto kv16 = std::make_unique<AttnKV16>();
  auto kvf = std::make_unique<AttnKVF32>();

  const int lens[] = {1, 2, 3, 15, 16, 17, 31, 33, 100, 257, 1023, 1024, 1025, 2200};
  const float thrs[] = {0.0f, 21.0f, 5.0f};  // exact, SPEC skip, aggressive skip

  long checked = 0;
  for (int len : lens) {
    // garbage-fill every ring so stale/invalid slots are poisoned
    for (size_t i = 0; i < sizeof(Naive); i++)
      reinterpret_cast<int8_t*>(ns.get())[i] = int8_t(di8(rng));
    for (size_t i = 0; i < sizeof(AttnKV); i++)
      reinterpret_cast<int8_t*>(kv8.get())[i] = int8_t(di8(rng));
    for (size_t i = 0; i < sizeof(AttnKV16); i++)
      reinterpret_cast<int8_t*>(kv16.get())[i] = int8_t(di8(rng));
    for (size_t i = 0; i < sizeof(AttnKVF32); i++)
      reinterpret_cast<int8_t*>(kvf.get())[i] = int8_t(di8(rng));

    float sq[3], sk[3], coef[3], sv[3];
    for (int h = 0; h < 3; h++) {
      sq[h] = dsc(rng);
      sk[h] = dsc(rng);
      coef[h] = 0.125f * sq[h] * sk[h];
      sv[h] = dsc(rng);
    }

    alignas(32) int8_t q[192], k[192], v[192];
    alignas(32) float ref[192], o8[192], o16[192], of[192];
    for (int t = 0; t < len; t++) {
      const bool extreme = (t % 37 == 5);  // max-|dot| rows now and then
      for (int i = 0; i < 192; i++) {
        q[i] = extreme ? ((i & 1) ? 127 : -128) : int8_t(di8(rng));
        k[i] = extreme ? ((i & 1) ? -128 : 127) : int8_t(di8(rng));
        v[i] = int8_t(di8(rng));
      }
      const int slot = t & 1023;
      std::memcpy(ns->k[slot], k, 192);
      std::memcpy(ns->v[slot], v, 192);
      fx2::opt::attn_kv_insert(*kv8, slot, k, v);
      fx2::opt::attn_kv_insert(*kv16, slot, k, v);
      fx2::opt::attn_kv_insert(*kvf, slot, k, v);

      const int n = std::min(t + 1, 1024);
      // check every step below 1100 (covers var, transition, first wrap),
      // then sparsely (keeps the naive-reference cost sane)
      if (t >= 1100 && (t % 97) != 0 && t != len - 1) continue;

      for (float thr : thrs) {
        naive_step(*ns, q, coef, sv, n, ref, thr);
        int kept3[3] = {-1, -1, -1};
        if (n < 1024) {
          fx2::opt::attn_step_var(*kv8, q, coef, sv, n, o8, thr, kept3);
          fx2::opt::attn_step_var(*kv16, q, coef, sv, n, o16, thr);
          fx2::opt::attn_step_var(*kvf, q, coef, sv, n, of, thr);
        } else {
          fx2::opt::attn_step_fixed(*kv8, q, coef, sv, o8, thr, kept3);
          fx2::opt::attn_step_fixed(*kv16, q, coef, sv, o16, thr);
          fx2::opt::attn_step_fixed(*kvf, q, coef, sv, of, thr);
        }
        gate("rand kv8 vs naive", diff192(o8, ref), 1e-5, t, n);
        bitwise_gate("rand kv16 vs kv8", o16, o8, t);
        bitwise_gate("rand kvf32 vs kv8", of, o8, t);
        // scalar recompute of the kept counts (thr on, small n only)
        if (thr > 0.0f && n <= 257) {
          for (int h = 0; h < 3; h++) {
            float m = -INFINITY;
            std::vector<float> s(n);
            for (int j = 0; j < n; j++) {
              int32_t dot = 0;
              for (int i = 0; i < 64; i++)
                dot += int(q[h * 64 + i]) * int(ns->k[j][h * 64 + i]);
              s[j] = coef[h] * float(dot);
              m = std::max(m, s[j]);
            }
            int kept = 0;
            for (int j = 0; j < n; j++)
              if (!(s[j] - m < -thr)) kept++;
            if (kept != kept3[h]) {
              std::printf("FAIL kept count: t=%d h=%d mine=%d scalar=%d\n", t,
                          h, kept3[h], kept);
              g_fail++;
            }
          }
        }
        checked++;
      }
    }
  }
  std::printf("random exactness: %ld kernel checks done (%s)\n", checked,
              g_fail ? "FAILURES above" : "all within gates");
}

// -------------------------------------------------------------------------
// real data: exactness vs naive, kept-count distribution, skip deviation
// -------------------------------------------------------------------------
struct Pct {
  double mean, p50, p90, p99, mx;
};
Pct pct(std::vector<int>& v) {
  if (v.empty()) return {0, 0, 0, 0, 0};
  std::sort(v.begin(), v.end());
  double s = 0;
  for (int x : v) s += x;
  auto at = [&](double q) { return double(v[size_t(q * (v.size() - 1))]); };
  return {s / v.size(), at(0.5), at(0.9), at(0.99), double(v.back())};
}

void test_real(const std::string& path) {
  fx2::opt::QkvCapture cap;
  if (!cap.load(path)) {
    std::printf("FAIL: cannot load capture %s (run capture_qkv first)\n",
                path.c_str());
    g_fail++;
    return;
  }
  std::printf("\nreal data: %u positions, article22\n", cap.n_pos);

  auto ns = std::make_unique<Naive>();
  auto kv8 = std::make_unique<AttnKV>();
  const int van_layers[3] = {3, 7, 11};

  double g_dev_abs = 0, g_dev_rel = 0, g_exact_rel = 0, g_skip_rel = 0;
  for (int li = 0; li < 3; li++) {
    float coef[3], sv[3];
    for (int h = 0; h < 3; h++) {
      coef[h] = cap.coef(li, h);
      sv[h] = cap.sv(li, h);
    }
    std::memset(ns.get(), 0x55, sizeof(Naive));
    std::memset(kv8.get(), 0x55, sizeof(AttnKV));

    std::vector<int> kept_var, kept_fixed;
    double dev_abs = 0, dev_rel = 0, exact_rel = 0, skip_rel = 0;
    alignas(32) float ref[192], refs[192], oe[192], os[192];
    for (long t = 0; t < cap.n_pos; t++) {
      const int slot = int(t & 1023);
      std::memcpy(ns->k[slot], cap.krow(li, t), 192);
      std::memcpy(ns->v[slot], cap.vrow(li, t), 192);
      fx2::opt::attn_kv_insert(*kv8, slot, cap.krow(li, t), cap.vrow(li, t));
      const int n = int(std::min(t + 1l, 1024l));
      const int8_t* q = cap.qrow(li, t);
      int kept3[3];
      naive_step(*ns, q, coef, sv, n, ref, 0.0f);
      naive_step(*ns, q, coef, sv, n, refs, 21.0f);
      if (n < 1024) {
        fx2::opt::attn_step_var(*kv8, q, coef, sv, n, oe, 0.0f);
        fx2::opt::attn_step_var(*kv8, q, coef, sv, n, os, 21.0f, kept3);
      } else {
        fx2::opt::attn_step_fixed(*kv8, q, coef, sv, oe, 0.0f);
        fx2::opt::attn_step_fixed(*kv8, q, coef, sv, os, 21.0f, kept3);
      }
      Diff de = diff192(oe, ref);   // exact mode vs naive exact
      Diff ds = diff192(os, refs);  // skip mode vs naive skip
      gate("real kv8 exact vs naive", de, 1e-5, int(t), n);
      gate("real kv8 skip vs naive-skip", ds, 1e-5, int(t), n);
      exact_rel = std::max(exact_rel, de.rel);
      skip_rel = std::max(skip_rel, ds.rel);
      Diff dv = diff192(os, oe);  // skip deviation (the approximation error)
      dev_abs = std::max(dev_abs, dv.max_abs);
      dev_rel = std::max(dev_rel, dv.rel);
      for (int h = 0; h < 3; h++)
        (n < 1024 ? kept_var : kept_fixed).push_back(kept3[h]);
    }
    Pct pv = pct(kept_var), pf = pct(kept_fixed);
    std::printf(
        "layer %2d: kept/head var-regime  mean %7.1f p50 %5.0f p90 %5.0f p99 "
        "%5.0f max %5.0f  (of n=t+1)\n",
        van_layers[li], pv.mean, pv.p50, pv.p90, pv.p99, pv.mx);
    std::printf(
        "layer %2d: kept/head fixed(1024) mean %7.1f p50 %5.0f p90 %5.0f p99 "
        "%5.0f max %5.0f\n",
        van_layers[li], pf.mean, pf.p50, pf.p90, pf.p99, pf.mx);
    std::printf(
        "layer %2d: skip-vs-exact max-abs %.3e max-rel %.3e | vs-naive rel: "
        "exact %.3e skip %.3e\n",
        van_layers[li], dev_abs, dev_rel, exact_rel, skip_rel);
    g_dev_abs = std::max(g_dev_abs, dev_abs);
    g_dev_rel = std::max(g_dev_rel, dev_rel);
    g_exact_rel = std::max(g_exact_rel, exact_rel);
    g_skip_rel = std::max(g_skip_rel, skip_rel);
  }
  std::printf(
      "real data overall: exact-vs-naive rel %.3e | skip(21) deviation "
      "max-abs %.3e max-rel %.3e\n",
      g_exact_rel, g_dev_abs, g_dev_rel);
}

// what tighter (loss-unsafe without e2e re-verification) thresholds WOULD
// prune: kept counts + deviation vs exact, optimized kernel only
void sweep_real(const std::string& path) {
  fx2::opt::QkvCapture cap;
  if (!cap.load(path)) return;
  const float thrs[] = {15.0f, 12.0f, 10.0f, 8.0f, 5.0f};
  const int NT = 5;
  std::printf(
      "\nthreshold sweep (kept/head in the fixed-1024 regime; deviation = "
      "skip vs exact max over article):\n%-8s", "layer");
  for (float t : thrs) std::printf("   thr=%-4.0f kept p50/p99      dev", t);
  std::printf("\n");
  auto kv8 = std::make_unique<AttnKV>();
  for (int li = 0; li < 3; li++) {
    float coef[3], sv[3];
    for (int h = 0; h < 3; h++) {
      coef[h] = cap.coef(li, h);
      sv[h] = cap.sv(li, h);
    }
    std::memset(kv8.get(), 0x55, sizeof(AttnKV));
    std::vector<int> kept[NT];
    double dev[NT] = {};
    alignas(32) float oe[192], os[192];
    for (long t = 0; t < cap.n_pos; t++) {
      const int slot = int(t & 1023);
      fx2::opt::attn_kv_insert(*kv8, slot, cap.krow(li, t), cap.vrow(li, t));
      const int n = int(std::min(t + 1l, 1024l));
      const int8_t* q = cap.qrow(li, t);
      if (n < 1024)
        fx2::opt::attn_step_var(*kv8, q, coef, sv, n, oe, 0.0f);
      else
        fx2::opt::attn_step_fixed(*kv8, q, coef, sv, oe, 0.0f);
      for (int ti = 0; ti < NT; ti++) {
        int kept3[3];
        if (n < 1024)
          fx2::opt::attn_step_var(*kv8, q, coef, sv, n, os, thrs[ti], kept3);
        else
          fx2::opt::attn_step_fixed(*kv8, q, coef, sv, os, thrs[ti], kept3);
        dev[ti] = std::max(dev[ti], diff192(os, oe).max_abs);
        if (n == 1024)
          for (int h = 0; h < 3; h++) kept[ti].push_back(kept3[h]);
      }
    }
    std::printf("%-8d", li == 0 ? 3 : li == 1 ? 7 : 11);
    for (int ti = 0; ti < NT; ti++) {
      Pct p = pct(kept[ti]);
      std::printf("   %5.0f/%-5.0f          %.1e", p.p50, p.p99, dev[ti]);
    }
    std::printf("\n");
  }
}

}  // namespace

int main(int argc, char** argv) {
  const char* cap_path = nullptr;
  bool with_real = true;
  for (int i = 1; i < argc; i++) {
    if (std::strcmp(argv[i], "--capture") == 0 && i + 1 < argc)
      cap_path = argv[++i];
    else if (std::strcmp(argv[i], "--no-real") == 0)
      with_real = false;
    else {
      std::fprintf(stderr, "usage: %s [--capture FILE] [--no-real]\n", argv[0]);
      return 2;
    }
  }
  test_random();
  if (with_real) {
    std::string p = fx2::opt::find_capture(cap_path);
    if (p.empty()) {
      std::printf("FAIL: capture file not found (run capture_qkv)\n");
      g_fail++;
    } else {
      test_real(p);
      sweep_real(p);
    }
  }
  if (g_fail) {
    std::printf("FAIL: %d failures\n", g_fail);
    return 1;
  }
  std::printf("PASS: optimized attention matches the naive reference "
              "(var+fixed, wraparound, transition, short articles, real "
              "data); kv16/kvf32 variants bitwise-equal to kv8\n");
  return 0;
}
