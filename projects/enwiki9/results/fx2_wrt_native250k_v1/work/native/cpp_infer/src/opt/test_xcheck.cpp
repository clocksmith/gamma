// test_xcheck: run the naive Transformer and the optimized TransformerOpt
// side by side over the first N articles (default 64) and compare the output
// probability rows (and capped logits) row by row. Expected divergence:
// vanilla-softmax reassociation ~4e-6 + KDA exp-family drift <= ~1e-5;
// anything much larger indicates an integration bug.
#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "../model.h"
#include "../testdata.h"
#include "model_opt.h"

int main(int argc, char** argv) {
  const char* data_dir = nullptr;
  int n_articles = 64;
  double gate = 5e-5;
  double trace_thr = 0.0;  // > 0: report first row with rowmax > thr
  fx2::opt::AttnKind kind = fx2::opt::AttnKind::KVF32;
  for (int i = 1; i < argc; i++) {
    if (std::strcmp(argv[i], "--data") == 0 && i + 1 < argc)
      data_dir = argv[++i];
    else if (std::strcmp(argv[i], "--articles") == 0 && i + 1 < argc)
      n_articles = std::atoi(argv[++i]);
    else if (std::strcmp(argv[i], "--gate") == 0 && i + 1 < argc)
      gate = std::atof(argv[++i]);
    else if (std::strcmp(argv[i], "--trace") == 0 && i + 1 < argc)
      trace_thr = std::atof(argv[++i]);
    else if (std::strcmp(argv[i], "--attn") == 0 && i + 1 < argc) {
      ++i;
      kind = std::strcmp(argv[i], "int8") == 0 ? fx2::opt::AttnKind::KVI8
                                               : fx2::opt::AttnKind::KVF32;
    } else {
      std::fprintf(
          stderr,
          "usage: %s [--data DIR] [--articles N] [--attn f32|int8] "
          "[--gate X]\n",
          argv[0]);
      return 2;
    }
  }

  std::string dir = fx2::find_data_dir(data_dir);
  fx2::TestData td;
  td.load(dir, /*with_ref_probs=*/false);
  if (n_articles < 0 || n_articles > td.n_articles)
    n_articles = td.n_articles;

  fx2::Transformer naive((dir + "/weights.bin").c_str());
  fx2::opt::TransformerOpt opt((dir + "/weights.bin").c_str(), kind);
  std::printf("attention KV variant: %s\n",
              kind == fx2::opt::AttnKind::KVF32 ? "f32-V" : "int8-V");

  std::vector<float> pn(205), po(205);
  double pmax = 0.0, psum = 0.0;
  double lmax = 0.0;
  long rows = 0;
  int pmax_article = -1;
  long pmax_t = -1;
  long hist[4] = {};  // rows with rowmax > 1e-5, 1e-4, 1e-3, 1e-2
  double loss_n = 0.0, loss_o = 0.0;  // -log p[target] sums (from probs)

  for (int a = 0; a < n_articles; a++) {
    long g0 = td.bounds[a];
    long len = td.bounds[a + 1] - g0;
    if (len < 2) continue;
    naive.begin_article(td.rope_offsets[a]);
    opt.begin_article(td.rope_offsets[a]);
    for (long t = 0; t < len - 1; t++) {
      naive.step(td.tokens[g0 + t], td.prior_row(g0 + t), pn.data());
      opt.step(td.tokens[g0 + t], td.prior_row(g0 + t), po.data());
      double rowmax = 0.0;
      for (int i = 0; i < 205; i++) {
        double d = std::fabs(double(pn[i]) - double(po[i]));
        if (d > rowmax) rowmax = d;
      }
      {
        int target = td.tokens[g0 + t + 1];
        loss_n += -std::log(double(pn[target]));
        loss_o += -std::log(double(po[target]));
      }
      if (rowmax > 1e-5) hist[0]++;
      if (rowmax > 1e-4) hist[1]++;
      if (rowmax > 1e-3) hist[2]++;
      if (rowmax > 1e-2) hist[3]++;
      const float* ln = naive.last_logits();
      const float* lo = opt.last_logits();
      double lrow = 0.0;
      int lrow_i = -1;
      for (int i = 0; i < 205; i++) {
        double d = std::fabs(double(ln[i]) - double(lo[i]));
        if (d > lrow) {
          lrow = d;
          lrow_i = i;
        }
      }
      if (lrow > lmax) lmax = lrow;
      if (trace_thr > 0.0 && (rowmax > trace_thr || lrow > 100 * trace_thr))
        std::printf("  a%d t%ld: probdiff %.3e  logitdiff %.3e @i=%d "
                    "(ln=%.6f lo=%.6f)\n",
                    a, t, rowmax, lrow, lrow_i, ln[lrow_i], lo[lrow_i]);
      psum += rowmax;
      rows++;
      if (rowmax > pmax) {
        pmax = rowmax;
        pmax_article = a;
        pmax_t = t;
      }
    }
    if ((a + 1) % 16 == 0)
      std::fprintf(stderr, "  ... %d/%d articles, running max prob diff %.3e\n",
                   a + 1, n_articles, pmax);
  }

  std::printf("\nnaive vs opt over %d articles (%ld rows):\n", n_articles,
              rows);
  std::printf("  max  abs prob diff:  %.6e  (article %d, position %ld)\n",
              pmax, pmax_article, pmax_t);
  std::printf("  mean row-max diff:   %.6e\n", psum / double(rows));
  std::printf("  max capped-logit diff: %.6e\n", lmax);
  std::printf("  rows with maxdiff > 1e-5/1e-4/1e-3/1e-2: %ld / %ld / %ld / "
              "%ld  (of %ld)\n",
              hist[0], hist[1], hist[2], hist[3], rows);
  std::printf("  subset mean -log p[target]: naive %.10f  opt %.10f  "
              "delta %+.3e (%+.5f%%)\n",
              loss_n / double(rows), loss_o / double(rows),
              (loss_o - loss_n) / double(rows),
              100.0 * (loss_o - loss_n) / loss_n);
  bool pass = pmax <= gate;
  std::printf("VERDICT: %s (gate %.1e; expected <= ~1e-5)\n",
              pass ? "PASS" : "FAIL", gate);
  return pass ? 0 : 1;
}
