// Prospective Gamma argmax unit gate; no codec or compression claim.
// Build with the exact adapter and an independently retained, unmodified parent.
#include <array>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <numeric>
#include <sched.h>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unistd.h>
#include <utility>
#include <valarray>
#include <vector>

#include "models/byte-model.h"

#if !defined(GAMMA_FX2_ARGMAX_INSTRUMENT) || !GAMMA_FX2_ARGMAX_INSTRUMENT
#error "The unit probe requires GAMMA_FX2_ARGMAX_INSTRUMENT=1"
#endif

#if !defined(GAMMA_FX2_ORIGINAL_BYTE_MODEL_HEADER) || \
    !defined(GAMMA_FX2_ORIGINAL_BYTE_MODEL_SOURCE)
#error "Provide the retained unmodified parent header and source paths"
#endif
// Compile the actual pinned parent into this same binary under a distinct name.
// The model.h dependency is shared and must match its pinned original hash.
#undef BYTE_MODEL_H
#define ByteModel GammaPublicByteModel
#include GAMMA_FX2_ORIGINAL_BYTE_MODEL_HEADER
#include GAMMA_FX2_ORIGINAL_BYTE_MODEL_SOURCE
#undef ByteModel

static_assert(sizeof(float) == 4 && std::numeric_limits<float>::is_iec559,
              "This gate requires IEEE binary32");

namespace {
using Arm = ByteModel::GammaArgmaxArm;
using Stats = ByteModel::GammaArgmaxStats;
constexpr std::array<Arm, 4> kArms = {Arm::P, Arm::K, Arm::D, Arm::C};
constexpr std::array<const char*, 4> kNames = {"P", "K", "D", "C"};
constexpr std::uint64_t kFnvOffset = 14695981039346656037ULL;

std::uint32_t Bits(float value) {
  std::uint32_t result;
  std::memcpy(&result, &value, sizeof(result));
  return result;
}

float Float(std::uint32_t bits) {
  float result;
  std::memcpy(&result, &bits, sizeof(result));
  return result;
}

void Require(bool condition, const std::string& reason) {
  if (!condition) throw std::runtime_error(reason);
}

void HashWord(std::uint64_t& hash, std::uint32_t value) {
  for (unsigned shift = 0; shift < 32; shift += 8) {
    hash ^= (value >> shift) & 255U;
    hash *= 1099511628211ULL;
  }
}

std::string Hex(std::uint64_t value) {
  std::ostringstream out;
  out << std::hex << std::setfill('0') << std::setw(16) << value;
  return out.str();
}

struct Row {
  std::string name;
  std::array<float, 256> values;
  std::vector<bool> vocab = std::vector<bool>(256, true);
  bool normalize_after_base_update = false;

  Row(std::string label, float value) : name(std::move(label)) {
    values.fill(value);
  }
};

std::vector<bool> PublicVocab() {
  // Authenticated archive 540574386; also bound in the adapter JSON.
  constexpr unsigned char bitmap[32] = {
      232, 22, 4, 0, 255, 255, 255, 3, 1, 252, 15, 249, 254, 255, 255, 7,
      255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255};
  std::vector<bool> result(256);
  unsigned count = 0;
  for (unsigned i = 0; i < 256; ++i) {
    result[i] = (bitmap[i / 8] & (1U << (i % 8))) != 0;
    count += result[i];
  }
  Require(count == 205, "authenticated vocabulary population differs");
  return result;
}

std::vector<Row> Rows() {
  std::vector<Row> rows;
  rows.emplace_back("uniform", 1.0f / 256);
  rows.emplace_back("uniform_public_205_mask", 1.0f / 256);
  rows.back().vocab = PublicVocab();
  rows.emplace_back("ties_across_every_bit_boundary", 1.0f);
  for (int i : {0, 1, 63, 64, 127, 128, 191, 192, 254, 255})
    rows.back().values[i] = 9.0f;
  rows.emplace_back("checkerboard_ties", 1.0f);
  for (int i = 0; i < 256; i += 2) rows.back().values[i] = 3.0f;
  for (int peak : {0, 1, 63, 64, 127, 128, 254, 255}) {
    rows.emplace_back("peaked_" + std::to_string(peak), 0.001f);
    rows.back().values[peak] = 1.0f;
  }
  rows.emplace_back("all_zero", 0.0f);
  rows.emplace_back("signed_zero_ties", 0.0f);
  for (int i = 0; i < 256; i += 2) rows.back().values[i] = Float(0x80000000U);
  rows.emplace_back("all_masked", 1.0f);
  rows.back().vocab.assign(256, false);
  rows.emplace_back("ascending", 0.0f);
  for (int i = 0; i < 256; ++i) rows.back().values[i] = float(i + 1);
  rows.emplace_back("descending", 0.0f);
  for (int i = 0; i < 256; ++i) rows.back().values[i] = float(256 - i);
  rows.emplace_back("subnormal_ties", 0.0f);
  for (int i = 0; i < 256; ++i) rows.back().values[i] = Float(1 + i % 64);
  rows.emplace_back("negative_finite", 0.0f);
  for (int i = 0; i < 256; ++i) rows.back().values[i] = -float(i % 17 + 1);
  rows.emplace_back("nan_initial_bot", 1.0f);
  rows.back().values[0] = Float(0x7fc00001U);
  rows.emplace_back("nan_new_bot_128_retained_winner_200", 1.0f);
  rows.back().values[128] = Float(0x7fc12345U);
  rows.back().values[200] = 8.0f;
  rows.emplace_back("nan_new_bot_64_retained_winner_127", 1.0f);
  rows.back().values[64] = Float(0xffc00007U);
  rows.back().values[127] = 8.0f;
  rows.emplace_back("nan_interior_tied_winners", 1.0f);
  rows.back().values[31] = Float(0x7fc00003U);
  rows.back().values[191] = Float(0xffc00009U);
  rows.back().values[32] = rows.back().values[128] = 8.0f;
  rows.emplace_back("all_nan_payloads", 0.0f);
  for (int i = 0; i < 256; ++i) rows.back().values[i] = Float(0x7fc00000U + i);
  rows.emplace_back("positive_infinity_ties", 1.0f);
  rows.back().values[0] = rows.back().values[255] = Float(0x7f800000U);
  rows.emplace_back("mixed_infinities", 1.0f);
  rows.back().values[0] = Float(0xff800000U);
  rows.back().values[64] = rows.back().values[192] = Float(0x7f800000U);
  rows.emplace_back("negative_infinity_ties", Float(0xff800000U));
  rows.emplace_back("masked_nonfinite", 1.0f);
  rows.back().vocab = PublicVocab();
  for (int i = 0; i < 256; ++i)
    if (!rows.back().vocab[i]) rows.back().values[i] = Float(0x7fc00001U);
  rows.emplace_back("post_base_normalize_public_205", 0.0f);
  rows.back().vocab = PublicVocab();
  rows.back().normalize_after_base_update = true;
  for (int i = 0; i < 256; ++i) rows.back().values[i] = float(i % 31 + 1);
  rows.emplace_back("post_base_normalize_overflow", Float(0x7effffffU));
  // Pre-base winner 200 becomes a zero-row tie at 0 after normalization.
  rows.back().values[200] = Float(0x7f7fffffU);
  rows.back().normalize_after_base_update = true;
  rows.emplace_back("post_base_normalize_zero_to_nan", 0.0f);
  rows.back().normalize_after_base_update = true;
  return rows;
}

template <class Base> class FixtureModel : public Base {
 public:
  explicit FixtureModel(const std::vector<bool>& vocab) : Base(vocab) {}

  void Load(const Row& row) {
    for (unsigned i = 0; i < 256; ++i) this->probs_[i] = row.values[i];
    this->ByteUpdate();
    // Match PPMD's audited order; never seed the cache inside ByteUpdate.
    if (row.normalize_after_base_update) this->probs_ /= this->probs_.sum();
  }

  std::array<std::uint32_t, 5> State() const {
    return {Bits(this->outputs_[0]), std::uint32_t(this->ex),
            std::uint32_t(this->bot_), std::uint32_t(this->top_),
            std::uint32_t(this->mid_)};
  }
};

struct Run {
  std::string rows_json;
  std::vector<std::uint32_t> reference_transcript;
  std::uint64_t comparisons = 0;
  std::uint64_t cached_comparisons = 0;
  std::uint64_t cache_hits = 0;
  std::uint64_t nan_fallbacks = 0;
  std::uint64_t state_checks = 0;
  std::uint64_t probability_row_checks = 0;
};

void StatsJson(std::ostream& out, const Stats& s) {
  out << "{\"predict_calls\":" << s.predict_calls
      << ",\"argmax_comparisons\":" << s.argmax_comparisons
      << ",\"scans\":" << s.scans << ",\"cache_hits\":" << s.cache_hits
      << ",\"byte_updates\":" << s.byte_updates
      << ",\"forced_invalidations\":" << s.forced_invalidations
      << ",\"cache_range_misses\":" << s.cache_range_misses
      << ",\"nan_bot_checks\":" << s.nan_bot_checks
      << ",\"nan_bot_fallbacks\":" << s.nan_bot_fallbacks << '}';
}

void CheckStats(const Stats& s, unsigned arm, const std::string& row) {
  Require(s.predict_calls == 4096, row + ": unexpected prediction count");
  Require(s.scans + s.cache_hits == s.predict_calls, row + ": scan accounting");
  if (arm != 2) {
    Require(s.argmax_comparisons == 257024, row + ": original scan count changed");
    Require(s.cache_hits == 0, row + ": control used cache");
  } else {
    Require(s.argmax_comparisons <= 257024, row + ": cached scan count grew");
  }
  Require(s.forced_invalidations == (arm == 3 ? s.predict_calls : 0),
          row + ": forced invalidation control failed");
}

void Exercise(const Row& row, bool constructor_only, Run& run, std::ostream& out) {
  std::unique_ptr<FixtureModel<GammaPublicByteModel>> reference;
  std::array<std::unique_ptr<FixtureModel<ByteModel>>, 4> models;
  std::array<std::uint64_t, 5> digests;
  digests.fill(kFnvOffset);
  std::array<Stats, 4> totals{};

  auto construct = [&]() {
    reference.reset(new FixtureModel<GammaPublicByteModel>(row.vocab));
    for (unsigned a = 0; a < 4; ++a) {
      models[a].reset(new FixtureModel<ByteModel>(row.vocab));
      Require(models[a]->GammaGetArgmaxArm() == Arm::P, "default arm is not P");
      models[a]->GammaSetArgmaxArm(kArms[a]);
    }
  };
  construct();
  auto check = [&](int truth, int bit, const char* event) {
    const auto expected = reference->State();
    for (auto word : expected) {
      run.reference_transcript.push_back(word);
      HashWord(digests[0], word);
    }
    for (unsigned a = 0; a < 4; ++a) {
      const auto actual = models[a]->State();
      ++run.state_checks;
      if (actual != expected) {
        std::ostringstream why;
        why << row.name << ": first divergence arm=" << kNames[a]
            << " truth=" << truth << " bit=" << bit << " event=" << event
            << " probability_bits=" << actual[0] << '/' << expected[0]
            << " ex=" << actual[1] << '/' << expected[1]
            << " bot=" << actual[2] << '/' << expected[2]
            << " top=" << actual[3] << '/' << expected[3]
            << " mid=" << actual[4] << '/' << expected[4];
        throw std::runtime_error(why.str());
      }
      for (auto word : actual) HashWord(digests[a + 1], word);
    }
  };

  for (int truth = 0; truth < 256; ++truth) {
    if (constructor_only) {
      construct();
    } else {
      reference->Load(row);
      for (auto& model : models) model->Load(row);
    }
    check(truth, 8, constructor_only ? "constructor" : "byte_update");
    for (unsigned a = 0; a < 4; ++a) {
      for (int i = 0; i < 256; ++i) {
        Require(Bits(models[a]->BytePredict()[i]) == Bits(reference->BytePredict()[i]),
                row.name + ": probability row differs after update");
        ++run.probability_row_checks;
      }
    }
    for (int bit = 7; bit >= 0; --bit) {
      // Repeated predict checks reuse without an intervening decoded bit.
      for (int repeat = 0; repeat < 2; ++repeat) {
        reference->Predict();
        for (auto& model : models) model->Predict();
        check(truth, bit, repeat ? "repeated_predict" : "predict");
      }
      const int decoded_bit = (truth >> bit) & 1;
      reference->Perceive(decoded_bit);
      for (auto& model : models) model->Perceive(decoded_bit);
      check(truth, bit, "perceive");
    }
    if (constructor_only) {
      for (unsigned a = 0; a < 4; ++a) {
        const auto s = models[a]->GammaArgmaxCounters();
        auto& t = totals[a];
        t.predict_calls += s.predict_calls;
        t.argmax_comparisons += s.argmax_comparisons;
        t.scans += s.scans;
        t.cache_hits += s.cache_hits;
        t.byte_updates += s.byte_updates;
        t.forced_invalidations += s.forced_invalidations;
        t.cache_range_misses += s.cache_range_misses;
        t.nan_bot_checks += s.nan_bot_checks;
        t.nan_bot_fallbacks += s.nan_bot_fallbacks;
      }
    }
  }
  if (!constructor_only)
    for (unsigned a = 0; a < 4; ++a) totals[a] = models[a]->GammaArgmaxCounters();
  out << "{\"row\":\"" << row.name << "\",\"truth_paths\":256,"
      << "\"reference_state_fnv1a64\":\"" << Hex(digests[0]) << "\",\"arms\":{";
  for (unsigned a = 0; a < 4; ++a) {
    CheckStats(totals[a], a, row.name);
    Require(totals[a].byte_updates == (constructor_only ? 0 : 256),
            row.name + ": byte update accounting failed");
    Require(digests[a + 1] == digests[0], row.name + ": transcript digest differs");
    if (a) out << ',';
    out << '"' << kNames[a] << "\":";
    StatsJson(out, totals[a]);
  }
  out << "}}";
  run.comparisons += totals[0].argmax_comparisons;
  run.cached_comparisons += totals[2].argmax_comparisons;
  run.cache_hits += totals[2].cache_hits;
  run.nan_fallbacks += totals[2].nan_bot_fallbacks;
}

Run Execute() {
  Run run;
  std::ostringstream out;
  out << '[';
  Exercise(Row("constructor_uniform_no_byte_update", 1.0f / 256), true, run, out);
  for (const auto& row : Rows()) {
    out << ',';
    Exercise(row, false, run, out);
  }
  out << ']';
  run.rows_json = out.str();
  Require(run.cache_hits > 0 && run.cached_comparisons < run.comparisons,
          "cached arm never reduced argmax comparisons");
  Require(run.nan_fallbacks > 0, "NaN boundary fallback was not exercised");
  return run;
}

std::string JsonEscape(const std::string& value) {
  std::string result;
  for (char c : value) {
    if (c == '"' || c == '\\') result += '\\';
    if (c == '\n') result += "\\n";
    else result += c;
  }
  return result;
}
}  // namespace

int main(int argc, char** argv) {
  try {
    Require(argc == 2 && std::string(argv[1]) == "--all-arms",
            "usage: fx2_bytemodel_argmax_probe --all-arms");
    cpu_set_t affinity;
    CPU_ZERO(&affinity);
    Require(sched_getaffinity(0, sizeof(affinity), &affinity) == 0 &&
                CPU_COUNT(&affinity) == 1 && CPU_ISSET(2, &affinity),
            "unit gate requires process CPU affinity exactly {2}");
    alarm(30);  // Scientific process budget; outer guard must retain the exit.
    const Run first = Execute();
    const Run repeat = Execute();
    Require(first.reference_transcript == repeat.reference_transcript,
            "repeat parent state transcript differs byte for byte");
    Require(first.rows_json == repeat.rows_json, "repeat counters or digests differ");
    std::cout << "{\"schema\":\"gamma.enwiki9.fx2-argmax-unit.v1\",\"status\":\"pass\","
              << "\"scope\":\"synthetic probability and expert-index unit gate; no codec gain\","
              << "\"cpu\":2,\"process_budget_seconds\":30,\"repeats\":2,"
              << "\"row_families\":" << Rows().size() + 1
              << ",\"truth_paths_per_row\":256,\"predicts_per_bit\":2,"
              << "\"exact_state_checks_per_repeat\":" << first.state_checks
              << ",\"exact_probability_row_checks_per_repeat\":" << first.probability_row_checks
              << ",\"exact_repeat_reference_words\":" << first.reference_transcript.size()
              << ",\"repeat_exact\":true,\"digest_role\":\"diagnostic; equality checked per call\","
              << "\"parent_argmax_comparisons_per_repeat\":" << first.comparisons
              << ",\"cached_argmax_comparisons_per_repeat\":" << first.cached_comparisons
              << ",\"cached_hits_per_repeat\":" << first.cache_hits
              << ",\"nan_fallbacks_per_repeat\":" << first.nan_fallbacks
              << ",\"parent_model_bytes\":" << sizeof(GammaPublicByteModel)
              << ",\"instrumented_model_bytes\":" << sizeof(ByteModel)
              << ",\"full_corpus_score_bytes\":null,\"Gamma_compression_gain_bytes\":null,"
              << "\"rows\":" << first.rows_json << "}\n";
    alarm(0);
    return 0;
  } catch (const std::exception& e) {
    std::cout << "{\"schema\":\"gamma.enwiki9.fx2-argmax-unit.v1\",\"status\":\"fail\","
              << "\"first_failure\":\"" << JsonEscape(e.what()) << "\"}\n";
    return 1;
  }
}
