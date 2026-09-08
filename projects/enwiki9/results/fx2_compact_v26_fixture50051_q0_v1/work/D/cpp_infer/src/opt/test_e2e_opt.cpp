// test_e2e_opt: src/test_e2e.cpp adapted to the optimized TransformerOpt.
// Streams the test articles, computes the loss two ways, compares with
// ref_loss.txt and the reference probability file (SPEC section 6).
#include <cmath>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <string>
#include <vector>

#include "../kernels.h"
#include "../testdata.h"
#include "model_opt.h"

namespace {

double now_s() {
  timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return double(ts.tv_sec) + 1e-9 * double(ts.tv_nsec);
}

}  // namespace

int main(int argc, char** argv) {
  const char* data_dir = nullptr;
  int n_articles = -1;
  fx2::opt::AttnKind kind = fx2::opt::AttnKind::KVF32;
  for (int i = 1; i < argc; i++) {
    if (std::strcmp(argv[i], "--data") == 0 && i + 1 < argc)
      data_dir = argv[++i];
    else if (std::strcmp(argv[i], "--articles") == 0 && i + 1 < argc)
      n_articles = std::atoi(argv[++i]);
    else if (std::strcmp(argv[i], "--attn") == 0 && i + 1 < argc) {
      ++i;
      if (std::strcmp(argv[i], "int8") == 0)
        kind = fx2::opt::AttnKind::KVI8;
      else if (std::strcmp(argv[i], "f32") == 0)
        kind = fx2::opt::AttnKind::KVF32;
      else {
        std::fprintf(stderr, "--attn must be f32 or int8\n");
        return 2;
      }
    } else {
      std::fprintf(stderr,
                   "usage: %s [--data DIR] [--articles N] [--attn f32|int8]\n",
                   argv[0]);
      return 2;
    }
  }

  std::string dir = fx2::find_data_dir(data_dir);
  fx2::TestData td;
  td.load(dir, /*with_ref_probs=*/true);
  if (n_articles < 0 || n_articles > td.n_articles)
    n_articles = td.n_articles;

  // reference loss (line "fp32 <sum> <count> <mean>")
  double ref_sum = 0, ref_mean = 0;
  long ref_count = 0;
  {
    std::string t = fx2::read_text_file(dir + "/ref_loss.txt");
    if (std::sscanf(t.c_str(), "fp32 %lf %ld %lf", &ref_sum, &ref_count,
                    &ref_mean) != 3)
      fx2::td_die("cannot parse ref_loss.txt");
  }

  fx2::opt::TransformerOpt model((dir + "/weights.bin").c_str(), kind);
  std::printf("attention KV variant: %s\n",
              kind == fx2::opt::AttnKind::KVF32 ? "f32-V (fast)"
                                                : "int8-V (compact)");

  double loss_logits = 0.0;  // PRIMARY: -(l[target] - logsumexp(l)), double acc
  double loss_probs = 0.0;   // sanity: -log(p[target])
  long count = 0;

  double l1_max = 0.0, l1_sum = 0.0;
  double prob_abs_max = 0.0;
  long rows_l1_gt = 0, rows_cmp = 0;
  int l1_max_article = -1;
  long l1_max_t = -1;

  std::vector<float> probs(205), refp(205);
  double t0 = now_s();

  for (int a = 0; a < n_articles; a++) {
    long g0 = td.bounds[a];
    long len = td.bounds[a + 1] - g0;
    if (len < 2) continue;
    model.begin_article(td.rope_offsets[a]);
    for (long t = 0; t < len - 1; t++) {
      model.step(td.tokens[g0 + t], td.prior_row(g0 + t), probs.data());
      int target = td.tokens[g0 + t + 1];

      const float* l = model.last_logits();
      float m = l[0];
      for (int i = 1; i < 205; i++)
        if (l[i] > m) m = l[i];
      double den = 0.0;
      for (int i = 0; i < 205; i++) den += std::exp(double(l[i]) - double(m));
      double lse = double(m) + std::log(den);
      loss_logits += -(double(l[target]) - lse);

      loss_probs += -std::log(double(probs[target]));
      count++;

      fx2::f16_to_f32(td.ref_prob_row(g0 + t), refp.data(), 205);
      double l1 = 0.0;
      for (int i = 0; i < 205; i++) {
        double d = std::fabs(double(probs[i]) - double(refp[i]));
        l1 += d;
        if (d > prob_abs_max) prob_abs_max = d;
      }
      l1_sum += l1;
      rows_cmp++;
      if (l1 > l1_max) {
        l1_max = l1;
        l1_max_article = a;
        l1_max_t = t;
      }
      if (l1 > 1e-2) rows_l1_gt++;
    }
    if ((a + 1) % 128 == 0)
      std::fprintf(stderr, "  ... %d/%d articles, %ld tokens, %.0f tok/s\n",
                   a + 1, n_articles, count, count / (now_s() - t0));
  }
  double dt = now_s() - t0;

  double mean_logits = loss_logits / double(count);
  double mean_probs = loss_probs / double(count);

  std::printf("\narticles: %d, predicted tokens: %ld, %.1f s, %.0f tokens/s\n",
              n_articles, count, dt, count / dt);
  std::printf("\nloss (a, PRIMARY, from logits):  sum %.6f  mean %.10f\n",
              loss_logits, mean_logits);
  std::printf("loss (b, sanity, from probs):    sum %.6f  mean %.10f\n",
              loss_probs, mean_probs);

  bool full_run = (n_articles == td.n_articles);
  if (full_run) {
    if (count != ref_count)
      std::printf("WARNING: predicted-token count %ld != reference %ld\n",
                  count, ref_count);
    double rel = (mean_logits - ref_mean) / ref_mean;
    std::printf("\nreference fp32 mean loss:        %.10f\n", ref_mean);
    std::printf("C++ opt mean loss (from logits): %.10f\n", mean_logits);
    std::printf("relative delta:                  %+.6e  (%+.4f%%)\n", rel,
                100.0 * rel);
    const char* verdict =
        std::fabs(rel) <= 1e-4
            ? "PASS (within the 0.01% target)"
            : (std::fabs(rel) <= 1e-3 ? "PASS (within the 0.1% budget)"
                                      : "FAIL (exceeds the 0.1% budget)");
    std::printf("VERDICT: %s\n", verdict);
    std::printf(
        "\nprobs vs test_ref_probs.f16 (excluding article-final rows):\n");
    std::printf("  rows compared:        %ld\n", rows_cmp);
    std::printf("  mean row L1:          %.6e\n", l1_sum / double(rows_cmp));
    std::printf("  max row L1:           %.6e  (article %d, position %ld)\n",
                l1_max, l1_max_article, l1_max_t);
    std::printf("  max single-prob diff: %.6e\n", prob_abs_max);
    std::printf("  rows with L1 > 1e-2:  %ld\n", rows_l1_gt);
    return std::fabs(rel) <= 1e-3 ? 0 : 1;
  } else {
    std::printf(
        "\n(subset run: %d articles -- no verdict; reference mean over "
        "ALL articles is %.10f)\n",
        n_articles, ref_mean);
    std::printf(
        "probs vs test_ref_probs.f16: rows %ld, mean L1 %.3e, max L1 "
        "%.3e, max prob diff %.3e, rows L1>1e-2: %ld\n",
        rows_cmp, l1_sum / double(rows_cmp), l1_max, prob_abs_max, rows_l1_gt);
    return 0;
  }
}
