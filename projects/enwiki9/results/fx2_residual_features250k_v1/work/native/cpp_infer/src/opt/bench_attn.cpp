// bench_attn: realistic-cache benchmark of the optimized vanilla attention.
// Maintains the REAL 3-layer KV rings (captured article22 q/k/v) and between
// the three per-token attention calls streams a ~5.9 MB dummy buffer through
// the core (1/3 per gap) to emulate the per-token weight stream evicting
// L1/L2 — K/V is then read from L3 exactly as in full-transformer inference.
//
// Reports core cycles/token for the attention component (all 3 layers,
// kernel only) bucketed at window sizes ~{64, 256, 863(mean), 1024(fixed)}
// with skip on/off, for the three KV layout variants (int8-K production,
// int16-K, fp32-V mirror), plus the insert-path cost per token.
//
// Pin with BENCH_CPU=<cpu> (defaults to 104, an idle core of the measured
// CCX 40-43/104-107).
#include <cstdint>
#include <cstring>
#include <memory>
#include <string>
#include <vector>

#include "../../bench/bench_common.h"
#include "../kernels.h"
#include "attn.h"
#include "qkv_capture.h"

using fx2::opt::AttnKV;
using fx2::opt::AttnKV16;
using fx2::opt::AttnKVF32;
using fx2::opt::QkvCapture;

// naive-reference adapter (src/kernels.h) so the same Replay harness can
// benchmark the pre-optimization baseline under identical cache conditions
namespace fx2 {
namespace opt {
struct NaiveKV {
  alignas(64) int8_t k[1024][192];
  alignas(64) int8_t v[1024][192];
};
inline void attn_kv_insert(NaiveKV& kv, int slot, const int8_t* k192,
                           const int8_t* v192) {
  std::memcpy(kv.k[slot], k192, 192);
  std::memcpy(kv.v[slot], v192, 192);
}
inline void attn_step_var(const NaiveKV& kv, const int8_t* q192,
                          const float* coef3, const float* sv3, int n,
                          float* out192, float thr, int* kept3) {
  fx2::attention_step_var(q192, kv.k[0], kv.v[0], coef3, sv3, n, out192, thr);
  if (kept3) kept3[0] = kept3[1] = kept3[2] = n;  // not reported by naive
}
inline void attn_step_fixed(const NaiveKV& kv, const int8_t* q192,
                            const float* coef3, const float* sv3,
                            float* out192, float thr, int* kept3) {
  fx2::attention_step_fixed(q192, kv.k[0], kv.v[0], coef3, sv3, out192, thr);
  if (kept3) kept3[0] = kept3[1] = kept3[2] = 1024;
}
}  // namespace opt
}  // namespace fx2

static volatile float g_fsink;
static volatile uint32_t g_isink;

// ---- weight-stream emulation: 3 chunks of 1.875 MiB = 5.625 MiB = 5.90 MB
static constexpr size_t THRASH_CHUNK = 1966080;  // 1.875 MiB
static constexpr size_t THRASH_TOTAL = 3 * THRASH_CHUNK;
static const uint8_t* g_thrash;

__attribute__((noinline)) static void thrash_chunk(int c) {
  const uint8_t* p = g_thrash + size_t(c) * THRASH_CHUNK;
  __m256i s0 = _mm256_setzero_si256(), s1 = s0, s2 = s0, s3 = s0;
  for (size_t i = 0; i < THRASH_CHUNK; i += 128) {
    s0 = _mm256_or_si256(s0, _mm256_load_si256((const __m256i*)(p + i)));
    s1 = _mm256_or_si256(s1, _mm256_load_si256((const __m256i*)(p + i + 32)));
    s2 = _mm256_or_si256(s2, _mm256_load_si256((const __m256i*)(p + i + 64)));
    s3 = _mm256_or_si256(s3, _mm256_load_si256((const __m256i*)(p + i + 96)));
  }
  s0 = _mm256_or_si256(_mm256_or_si256(s0, s1), _mm256_or_si256(s2, s3));
  g_isink = (uint32_t)_mm256_extract_epi32(s0, 0);
}

struct Buckets {
  // [t_lo, t_hi) chosen so mean n over the bucket = the nominal window
  static constexpr int N = 5;
  const char* name[N] = {"n64", "n256", "n863", "n1024", "all"};
  long lo[N] = {47, 191, 798, 1023, 0};
  long hi[N] = {80, 320, 928, 1 << 30, 1 << 30};
  double cyc[N] = {};
  double kept[N] = {};
  long cnt[N] = {};
  void add(long t, double c, double k) {
    for (int b = 0; b < N; b++)
      if (t >= lo[b] && t < hi[b]) {
        cyc[b] += c;
        kept[b] += k;
        cnt[b]++;
      }
  }
};

struct LayerParams {
  float coef[3], sv[3];
};

template <class KV>
struct Replay {
  const QkvCapture& cap;
  LayerParams lp[3];
  std::unique_ptr<KV[]> kv{new KV[3]};

  explicit Replay(const QkvCapture& c) : cap(c) {
    for (int li = 0; li < 3; li++)
      for (int h = 0; h < 3; h++) {
        lp[li].coef[h] = c.coef(li, h);
        lp[li].sv[h] = c.sv(li, h);
      }
  }

  // one full-article pass; returns per-token attention cycles (3 layers,
  // kernels only; inserts untimed here — measured by insert_pass)
  Buckets run(float thr) {
    for (int li = 0; li < 3; li++) std::memset(&kv[li], 0x55, sizeof(KV));
    alignas(32) float out[192];
    Buckets bk;
    const long npos = cap.n_pos;
    for (long t = 0; t < npos; t++) {
      const int slot = int(t & 1023);
      const int n = int(t + 1 < 1024 ? t + 1 : 1024);
      double ticks = 0;
      int keptsum = 0;
      for (int li = 0; li < 3; li++) {
        thrash_chunk(li);
        fx2::opt::attn_kv_insert(kv[li], slot, cap.krow(li, t),
                                 cap.vrow(li, t));
        int kept3[3];
        const uint64_t t0 = rdtsc_ser();
        if (n < 1024)
          fx2::opt::attn_step_var(kv[li], cap.qrow(li, t), lp[li].coef,
                                  lp[li].sv, n, out, thr, kept3);
        else
          fx2::opt::attn_step_fixed(kv[li], cap.qrow(li, t), lp[li].coef,
                                    lp[li].sv, out, thr, kept3);
        const uint64_t t1 = rdtsc_ser();
        ticks += double(t1 - t0);
        keptsum += kept3[0] + kept3[1] + kept3[2];
      }
      g_fsink = out[0] + out[191];
      bk.add(t, ticks_to_cycles(ticks), keptsum / 9.0);
    }
    return bk;
  }

  // insert-path cost: thrash, then the 3 per-layer inserts timed together
  double insert_pass() {
    for (int li = 0; li < 3; li++) std::memset(&kv[li], 0x55, sizeof(KV));
    // rdtsc pair bias
    double bias;
    {
      std::vector<double> d;
      for (int i = 0; i < 512; i++) {
        const uint64_t a = rdtsc_ser();
        const uint64_t b = rdtsc_ser();
        d.push_back(double(b - a));
      }
      std::sort(d.begin(), d.end());
      bias = d[d.size() / 2];
    }
    const long npos = cap.n_pos;
    double total = 0;
    for (long t = 0; t < npos; t++) {
      const int slot = int(t & 1023);
      for (int c = 0; c < 3; c++) thrash_chunk(c);
      const uint64_t t0 = rdtsc_ser();
      for (int li = 0; li < 3; li++)
        fx2::opt::attn_kv_insert(kv[li], slot, cap.krow(li, t),
                                 cap.vrow(li, t));
      const uint64_t t1 = rdtsc_ser();
      total += double(t1 - t0) - bias;
    }
    return ticks_to_cycles(total / double(npos));  // per token (3 inserts)
  }
};

template <class KV>
static void bench_variant(const char* name, const QkvCapture& cap, int reps) {
  Replay<KV> rp(cap);
  for (float thr : {21.0f, 0.0f}) {
    std::vector<Buckets> runs;
    for (int r = 0; r < reps; r++) {
      std::memset(fx2::opt::g_attn_prof, 0, sizeof(fx2::opt::g_attn_prof));
      runs.push_back(rp.run(thr));
      if (fx2::opt::g_attn_prof[3]) {  // ATTN_PROFILE build
        const double per_tok = 3.0 / double(cap.n_pos);  // 3 layer calls/token
        std::printf(
            "  [prof %s thr=%g] per token: qk %.0f exp %.0f pv %.0f cyc\n",
            name, thr, ticks_to_cycles(double(fx2::opt::g_attn_prof[0])) * per_tok / 3.0,
            ticks_to_cycles(double(fx2::opt::g_attn_prof[1])) * per_tok / 3.0,
            ticks_to_cycles(double(fx2::opt::g_attn_prof[2])) * per_tok / 3.0);
      }
    }
    std::printf("%-6s skip=%-3s |", name, thr > 0 ? "on" : "off");
    for (int b = 0; b < Buckets::N; b++) {
      std::vector<double> v;
      for (auto& bk : runs) v.push_back(bk.cyc[b] / std::max(bk.cnt[b], 1l));
      std::sort(v.begin(), v.end());
      const double med = v[v.size() / 2];
      const double kept = runs[0].kept[b] / std::max(runs[0].cnt[b], 1l);
      std::printf("  %s %7.0f cyc (kept %5.0f)", runs[0].name[b], med, kept);
    }
    std::printf("\n");
    fflush(stdout);
  }
  std::vector<double> ins;
  for (int r = 0; r < reps; r++) ins.push_back(rp.insert_pass());
  std::sort(ins.begin(), ins.end());
  std::printf("%-6s insert     |  %7.1f cyc/token (3 layers) = %5.1f/insert\n",
              name, ins[ins.size() / 2], ins[ins.size() / 2] / 3.0);
  fflush(stdout);
}

int main(int argc, char** argv) {
  const char* cap_path = nullptr;
  int reps = 3;
  bool all_variants = true;
  bool with_naive = false;
  for (int i = 1; i < argc; i++) {
    if (std::strcmp(argv[i], "--capture") == 0 && i + 1 < argc)
      cap_path = argv[++i];
    else if (std::strcmp(argv[i], "--reps") == 0 && i + 1 < argc)
      reps = atoi(argv[++i]);
    else if (std::strcmp(argv[i], "--kv8-only") == 0)
      all_variants = false;
    else if (std::strcmp(argv[i], "--with-naive") == 0)
      with_naive = true;
    else {
      fprintf(stderr,
              "usage: %s [--capture FILE] [--reps N] [--kv8-only] "
              "[--with-naive]\n",
              argv[0]);
      return 2;
    }
  }
  if (!getenv("BENCH_CPU")) setenv("BENCH_CPU", "104", 1);
  pin_from_env();

  QkvCapture cap;
  {
    std::string p = fx2::opt::find_capture(cap_path);
    if (p.empty() || !cap.load(p)) {
      fprintf(stderr, "cannot load capture (run capture_qkv first)\n");
      return 1;
    }
  }

  uint8_t* tb = (uint8_t*)alloc_buf(THRASH_TOTAL);
  for (size_t i = 0; i < THRASH_TOTAL; i++) tb[i] = uint8_t(i * 2654435761u);
  g_thrash = tb;

  Calib c = calibrate();
  print_calib("bench_attn", c);
  std::printf(
      "# article22 replay: %u tokens; per token: 3x(1.875MiB thrash + insert "
      "+ attention kernel); attention cycles = kernels only, 2 rdtsc/layer "
      "(~%d cyc overhead/token incl.)\n",
      cap.n_pos, 3 * 67);
  std::printf(
      "# buckets: mean window n64/n256/n863 (var kernel), n1024 (fixed), "
      "all = whole article; kept = mean kept positions per head\n");

  bench_variant<AttnKV>("kv8", cap, reps);
  if (all_variants) {
    bench_variant<AttnKV16>("kv16", cap, reps);
    bench_variant<AttnKVF32>("kvf32", cap, reps);
  }
  if (with_naive) bench_variant<fx2::opt::NaiveKV>("naive", cap, reps);

  Calib c2 = calibrate(true, 0.1);
  print_calib("bench_attn_end", c2);
  return 0;
}
