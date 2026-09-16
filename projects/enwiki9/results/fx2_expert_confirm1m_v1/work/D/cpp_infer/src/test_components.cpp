// test_components: stream the diagnostic dump articles through the C++
// transformer and compare every dumped intermediate component (SPEC section 5)
#include <cmath>
#include <cstdio>
#include <cstring>
#include <map>
#include <set>
#include <string>
#include <vector>

#include "model.h"
#include "npy.h"
#include "testdata.h"

namespace {

constexpr bool KIMI[12] = {true, true, true,  false, true, true,
                           true, false, true, true,  true, false};

// components upstream of the first KDA state update: bit-clean vs the
// reference apart from fp32 reduction-order noise (expect <= ~1e-4 rel)
const std::set<std::string> CLEAN_UPSTREAM = {
    "00_x0",          "00_block_input",   "00_kimi_conv_q",
    "00_kimi_conv_k", "00_kimi_conv_v",   "00_kimi_g_raw",
    "00_kimi_beta_raw", "00_kimi_out_gate", "00_kimi_gate_in",
};

struct Cmp {
  fx2::Npy ref;
  double max_abs = 0;
  long ma_t = -1, ma_i = -1;
  double ma_ref = 0;
  double max_rel = 0;  // over elements with |ref| > 1e-2
  long mr_t = -1;
  double mr_ref = 0, mr_diff = 0;
  double ssd = 0, ssr = 0;  // sum diff^2 / sum ref^2 -> relative RMS
  // decomposition for the clean-upstream gate: "smooth" ulp-level noise
  // (|diff| <= 1e-4) vs isolated knife-edge quantization flips (|diff| > 1e-4)
  double ssd_smooth = 0;
  long n_large = 0;
  long n_nonfinite = 0;
  long n_flips = 0;         // quantized comps: elements differing
  double max_int_diff = 0;  // quantized comps: max |mine - ref| in ints
  size_t n_elems = 0;
  bool quantized = false;  // *_int8 / *_quant

  double rel_rms() const { return ssr > 0 ? std::sqrt(ssd / ssr) : 0.0; }
  double smooth_rel_rms() const {
    return ssr > 0 ? std::sqrt(ssd_smooth / ssr) : 0.0;
  }
  double flip_fraction() const {
    return n_elems > 0 ? double(n_large) / double(n_elems) : 0.0;
  }
};

std::vector<std::string> component_names() {
  std::vector<std::string> names;
  names.push_back("00_x0");
  char nm[64];
  for (int l = 0; l < 12; l++) {
    auto add = [&](const char* c) {
      std::snprintf(nm, sizeof nm, "%02d_%s", l, c);
      names.push_back(nm);
    };
    add("block_input");
    add("attn_out");
    add("mlp_out");
    add("block_output");
    if (KIMI[l]) {
      add("kimi_conv_q");
      add("kimi_conv_k");
      add("kimi_conv_v");
      add("kimi_g_raw");
      add("kimi_beta_raw");
      add("kimi_out_gate");
      add("kimi_gate_in");
      add("kimi_kda_out");
      add("kimi_gated_norm_out");
    } else {
      add("attn_q_quant");
      add("attn_k_quant");
      add("attn_v_quant");
      add("attn_q_int8");
      add("attn_k_int8");
      add("attn_v_int8");
      add("attn_pre_oproj");
    }
  }
  names.push_back("12_final_norm");
  names.push_back("12_logits");
  names.push_back("12_probabilities");
  return names;
}

bool is_quantized_name(const std::string& n) {
  return n.size() > 5 && (n.compare(n.size() - 5, 5, "_int8") == 0 ||
                          n.compare(n.size() - 6, 6, "_quant") == 0);
}

struct ArticleResult {
  bool failed = false;
  std::vector<std::string> failures;
};

const char* g_save_logits = nullptr;  // debug: raw fp32 logits rows

// forced == true: teacher-forced pass -- every block's input is replaced by
// the reference block_input dump row, so each block is compared against exact
// reference inputs (tight tolerances, catches per-block bugs).
// forced == false: chained streaming pass -- the reference's own tf32 KDA
// noise is amplified through quantization roundings, so only robust aggregate
// gates apply; the table and position-bucket analysis are for review.
ArticleResult run_article(fx2::Transformer& model, const fx2::TestData& td,
                          int subset_index, bool forced) {
  std::string adir =
      td.dir + "/dumps/article" + std::to_string(subset_index);
  std::string meta = fx2::read_text_file(adir + "/meta.json");
  long rope_offset = fx2::meta_int(meta, "rope_offset");
  long n_dump = fx2::meta_int(meta, "dumped_positions");
  long meta_len = fx2::meta_int(meta, "length_tokens");

  long g0 = td.bounds[subset_index];
  long len = td.bounds[subset_index + 1] - g0;
  if (len != meta_len) fx2::td_die("meta length mismatch vs test_bounds");

  std::printf(
      "=== article%d (%s): %ld tokens, %ld dumped positions, rope offset %ld "
      "===\n",
      subset_index, forced ? "teacher-forced block inputs" : "chained",
      len, n_dump, rope_offset);

  std::map<std::string, Cmp> comps;
  for (const std::string& n : component_names()) {
    Cmp c;
    c.ref = fx2::load_npy(adir + "/" + n + ".npy");
    if (static_cast<long>(c.ref.rows()) != n_dump)
      fx2::td_die(n + ": unexpected row count");
    c.quantized = is_quantized_name(n);
    comps.emplace(n, std::move(c));
  }

  // block-output max-abs diff by position bucket for selected layers
  const int bucket_layers[4] = {0, 3, 6, 11};
  double bucket_max[4][4] = {};
  auto bucket_of = [](long t) {
    if (t < 256) return 0;
    if (t < 1024) return 1;
    if (t < 2048) return 2;
    return 3;
  };

  long cur_t = 0;
  model.set_capture([&](const char* name, const float* d, int n) {
    auto it = comps.find(name);
    if (it == comps.end()) return;
    Cmp& c = it->second;
    if (static_cast<size_t>(n) != c.ref.row_elems()) {
      std::fprintf(stderr, "%s: captured %d elems, dump row has %zu\n", name,
                   n, c.ref.row_elems());
      std::exit(1);
    }
    const float* refrow_f = nullptr;
    const int8_t* refrow_i = nullptr;
    if (c.ref.is_f32())
      refrow_f = c.ref.f32() + size_t(cur_t) * n;
    else
      refrow_i = c.ref.i8() + size_t(cur_t) * n;
    for (int i = 0; i < n; i++) {
      double mine = d[i];
      double ref = refrow_f ? refrow_f[i] : double(refrow_i[i]);
      if (!std::isfinite(mine)) {
        c.n_nonfinite++;
        continue;
      }
      double diff = std::fabs(mine - ref);
      c.n_elems++;
      c.ssd += diff * diff;
      c.ssr += ref * ref;
      if (diff <= 1e-4)
        c.ssd_smooth += diff * diff;
      else
        c.n_large++;
      if (diff > c.max_abs) {
        c.max_abs = diff;
        c.ma_t = cur_t;
        c.ma_i = i;
        c.ma_ref = ref;
      }
      if (std::fabs(ref) > 1e-2) {
        double rel = diff / std::fabs(ref);
        if (rel > c.max_rel) {
          c.max_rel = rel;
          c.mr_t = cur_t;
          c.mr_ref = ref;
          c.mr_diff = diff;
        }
      }
      if (c.quantized) {
        // for *_int8 diff is already in ints; for *_quant it is in units of
        // the (per-head) scale times the int difference -- count flips only
        // for the int8 arrays where the unit is exact
        if (c.ref.is_i8()) {
          if (diff > 0) c.n_flips++;
          if (diff > c.max_int_diff) c.max_int_diff = diff;
        }
      }
    }
    // bucket bookkeeping
    for (int b = 0; b < 4; b++) {
      char want[32];
      std::snprintf(want, sizeof want, "%02d_block_output", bucket_layers[b]);
      if (std::strcmp(name, want) == 0) {
        int bk = bucket_of(cur_t);
        const float* rf = c.ref.f32() + size_t(cur_t) * n;
        for (int i = 0; i < n; i++) {
          double diff = std::fabs(double(d[i]) - double(rf[i]));
          if (diff > bucket_max[b][bk]) bucket_max[b][bk] = diff;
        }
      }
    }
  });

  if (forced) {
    model.set_block_input_override([&](int layer) -> const float* {
      char nm[32];
      std::snprintf(nm, sizeof nm, "%02d_block_input", layer);
      const fx2::Npy& ref = comps.at(nm).ref;
      return ref.f32() + size_t(cur_t) * 192;
    });
  }
  FILE* save = nullptr;
  if (g_save_logits && !forced) {
    std::string p = std::string(g_save_logits) + std::to_string(subset_index);
    save = std::fopen(p.c_str(), "wb");
  }
  model.begin_article(rope_offset);
  std::vector<float> probs(205);
  for (long t = 0; t < n_dump; t++) {
    cur_t = t;
    model.step(td.tokens[g0 + t], td.prior_row(g0 + t), probs.data());
    if (save) std::fwrite(model.last_logits(), sizeof(float), 205, save);
  }
  if (save) std::fclose(save);
  model.set_capture(nullptr);
  model.set_block_input_override(nullptr);

  // ---- report ----
  // Gating rationale: per-element max-rel is reported for review but cannot
  // gate downstream components in the CHAINED pass: the reference's own tf32
  // KDA noise flips knife-edge quantization roundings downstream, producing
  // quantum-sized per-element jumps even for an exactly correct
  // implementation (verified against an independent exact-fp32 numpy chain
  // that reproduces the C++ values, and diverges from the dumps identically).
  // The teacher-forced pass removes chained divergence, so it carries the
  // tight 3% rel-RMS gate; the chained pass keeps a loose 15% catastrophic
  // gate plus the clean-upstream and NaN/Inf gates.
  ArticleResult res;
  double gross_gate = forced ? 0.03 : 0.15;
  std::printf("%-24s %11s %13s %11s %11s  %s\n", "component", "max-abs",
              "(t,i)", "max-rel", "rel-RMS", "notes (rel over |ref|>1e-2)");
  for (auto& [name, c] : comps) {
    bool trivially_forced =
        forced && name.find("block_input") != std::string::npos;
    char loc[32];
    std::snprintf(loc, sizeof loc, "(%ld,%ld)", c.ma_t, c.ma_i);
    char note[128] = "";
    if (trivially_forced)
      std::snprintf(note, sizeof note, "(forced input, trivially equal)");
    else if (c.quantized && c.ref.is_i8())
      std::snprintf(note, sizeof note, "int flips %ld/%zu, max int diff %.0f",
                    c.n_flips, c.n_elems, c.max_int_diff);
    else if (CLEAN_UPSTREAM.count(name))
      std::snprintf(note, sizeof note,
                    "clean: smooth rel-RMS %.2e, flips %ld/%zu",
                    c.smooth_rel_rms(), c.n_large, c.n_elems);
    std::printf("%-24s %11.3e %13s %11.3e %11.3e  %s\n", name.c_str(),
                c.max_abs, loc, c.max_rel, c.rel_rms(), note);

    if (c.n_nonfinite > 0) {
      res.failed = true;
      res.failures.push_back(name + ": " + std::to_string(c.n_nonfinite) +
                             " non-finite values");
    }
    if (trivially_forced) continue;
    if (CLEAN_UPSTREAM.count(name)) {
      // ulp-level ("smooth") noise must stay below 1e-4 rel-RMS, and
      // knife-edge quantization flips must stay rare (< 0.1% of elements);
      // a systematic bug breaks one of these by >= 100x
      if (c.smooth_rel_rms() > 1e-4 || c.flip_fraction() > 1e-3) {
        res.failed = true;
        char m[224];
        std::snprintf(m, sizeof m,
                      "%s: clean-upstream smooth rel-RMS %.3g (gate 1e-4), "
                      "flip fraction %.3g (gate 1e-3)",
                      name.c_str(), c.smooth_rel_rms(), c.flip_fraction());
        res.failures.push_back(m);
      }
    }
    if (c.rel_rms() > gross_gate) {
      res.failed = true;
      char m[192];
      std::snprintf(m, sizeof m, "%s: rel-RMS %.3g > %.0f%% (max-rel %.3g)",
                    name.c_str(), c.rel_rms(), 100.0 * gross_gate, c.max_rel);
      res.failures.push_back(m);
    }
  }

  if (!forced) {
    std::printf(
        "\nblock-output max-abs diff by position bucket (window/rope/state "
        "regressions show up as jumps):\n");
    std::printf("%-8s %12s %12s %12s %12s\n", "layer", "0-255", "256-1023",
                "1024-2047", "2048+");
    for (int b = 0; b < 4; b++) {
      std::printf("%-8d", bucket_layers[b]);
      for (int bk = 0; bk < 4; bk++) {
        long lo[4] = {0, 256, 1024, 2048};
        if (n_dump > lo[bk])
          std::printf(" %12.3e", bucket_max[b][bk]);
        else
          std::printf(" %12s", "-");
      }
      std::printf("\n");
    }
  }
  std::printf("\n");
  return res;
}

}  // namespace

int main(int argc, char** argv) {
  const char* data_dir = nullptr;
  std::vector<int> articles = {0, 4, 22};
  for (int i = 1; i < argc; i++) {
    if (std::strcmp(argv[i], "--data") == 0 && i + 1 < argc)
      data_dir = argv[++i];
    else if (std::strcmp(argv[i], "--articles") == 0 && i + 1 < argc) {
      articles.clear();
      char* s = argv[++i];
      while (*s) {
        articles.push_back(static_cast<int>(std::strtol(s, &s, 10)));
        if (*s == ',') s++;
      }
    } else if (std::strcmp(argv[i], "--save-logits") == 0 && i + 1 < argc) {
      g_save_logits = argv[++i];  // debug: writes <prefix><article> raw f32
    } else {
      std::fprintf(stderr,
                   "usage: %s [--data DIR] [--articles 0,4,22] "
                   "[--save-logits PREFIX]\n",
                   argv[0]);
      return 2;
    }
  }

  std::string dir = fx2::find_data_dir(data_dir);
  fx2::TestData td;
  td.load(dir, /*with_ref_probs=*/false);
  fx2::Transformer model((dir + "/weights.bin").c_str());

  bool failed = false;
  std::vector<std::string> all_failures;
  for (int a : articles) {
    for (bool forced : {true, false}) {
      ArticleResult r = run_article(model, td, a, forced);
      if (r.failed) {
        failed = true;
        for (auto& f : r.failures)
          all_failures.push_back("article" + std::to_string(a) +
                                 (forced ? " (forced): " : " (chained): ") + f);
      }
    }
  }

  if (failed) {
    std::printf("FAIL: gross component errors detected:\n");
    for (auto& f : all_failures) std::printf("  %s\n", f.c_str());
    return 1;
  }
  std::printf(
      "PASS: no gross errors -- teacher-forced pass (exact reference block "
      "inputs) within 3%% rel-RMS everywhere; clean-upstream components at "
      "ulp-level smooth noise (<1e-4 rel-RMS) with only rare knife-edge "
      "quantization flips (<0.1%%); chained pass free of NaN/Inf and "
      "catastrophic (>15%% rel-RMS) divergence. Remaining chained divergence "
      "is the reference's tf32 KDA noise amplified through knife-edge "
      "quantization roundings -- tables above are for human review.\n");
  return 0;
}
