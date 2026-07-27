#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr int kScale = 256;
constexpr int kExperts = 9;
constexpr int kFeatures = 6;
constexpr int kIdentity = 3;
constexpr int kModelBytes = 3;
constexpr std::array<int, kExperts> kMultipliers{
    2048, 3072, 3584, 4096, 4681, 5461, 6144, 7168, 8192};
constexpr std::array<int, kFeatures> kCardinalities{8, 17, 17, 16, 10, 8};

struct RangeEncoder {
  uint32_t x1 = 0;
  uint32_t x2 = 0xffffffffu;
  std::vector<uint8_t> output;
  void Update(uint16_t p1, int bit) {
    const uint32_t delta = x2 - x1;
    const uint32_t midpoint =
        x1 + (delta >> 16) * p1 + ((delta & 0xffffu) * p1 >> 16);
    if (bit) x2 = midpoint;
    else x1 = midpoint + 1;
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      output.push_back(static_cast<uint8_t>(x2 >> 24));
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
  }
  void Finish() {
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      output.push_back(static_cast<uint8_t>(x2 >> 24));
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
    output.push_back(static_cast<uint8_t>(x2 >> 24));
  }
};

using Losses = std::array<int64_t, kExperts>;

struct Family {
  int first = 0;
  int second = -1;
  int categories = 0;
  std::vector<Losses> losses;
};

struct Rule {
  bool active = false;
  int family = -1;
  int category = -1;
  int expert = kIdentity;
  int64_t training_gain_qbits = 0;
};

std::vector<uint8_t> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open " + path);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

uint64_t Load64(const uint8_t* data) {
  uint64_t value = 0;
  for (int i = 7; i >= 0; --i) value = (value << 8) | data[i];
  return value;
}

uint16_t Correct(uint16_t p, int expert) {
  const uint64_t multiplier = kMultipliers[expert];
  const uint64_t numerator = static_cast<uint64_t>(p) * multiplier;
  const uint64_t denominator =
      numerator + static_cast<uint64_t>(65536u - p) * 4096u;
  uint64_t q = (numerator * 65536u + denominator / 2) / denominator;
  q = std::max<uint64_t>(1, std::min<uint64_t>(65535, q));
  return static_cast<uint16_t>(q);
}

int Category(const Family& family,
             const std::array<uint8_t, kFeatures>& features) {
  if (family.second < 0) return features[family.first];
  return features[family.first] * kCardinalities[family.second] +
         features[family.second];
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "usage: finite_residual_rule_gate TRACE ARCHIVE HEADING_MAP DECISION\n";
    return 2;
  }
  try {
    const auto trace = ReadFile(argv[1]);
    const auto archive = ReadFile(argv[2]);
    const auto heading_map = ReadFile(argv[3]);
    if (trace.size() < 8 || std::memcmp(trace.data(), "FX2PT01\n", 8) != 0 ||
        (trace.size() - 8) % 3 != 0) {
      throw std::runtime_error("invalid trace");
    }
    if (heading_map.size() < 24 ||
        std::memcmp(heading_map.data(), "HEADMAP1", 8) != 0) {
      throw std::runtime_error("invalid heading map");
    }
    const int64_t rows = static_cast<int64_t>((trace.size() - 8) / 3);
    if (rows % 16) throw std::runtime_error("half trace not byte aligned");
    const int64_t train_rows = rows / 2;
    const uint64_t wrt_bytes = Load64(heading_map.data() + 8);
    if (wrt_bytes != static_cast<uint64_t>(rows / 8))
      throw std::runtime_error("heading map mismatch");

    std::vector<uint16_t> probabilities(rows);
    std::vector<uint8_t> truth(rows), bytes(rows / 8);
    for (int64_t row = 0; row < rows; ++row) {
      const size_t offset = 8 + static_cast<size_t>(row) * 3;
      probabilities[row] = static_cast<uint16_t>(
          trace[offset] | (static_cast<uint16_t>(trace[offset + 1]) << 8));
      truth[row] = trace[offset + 2];
      if (probabilities[row] == 0 || truth[row] > 1)
        throw std::runtime_error("invalid row");
      bytes[row / 8] =
          static_cast<uint8_t>((bytes[row / 8] << 1) | truth[row]);
    }

    std::vector<std::array<uint8_t, kFeatures>> feature_rows(rows);
    int64_t error_age = 0;
    for (int64_t row = 0; row < rows; ++row) {
      const int64_t byte_index = row / 8;
      const int previous =
          byte_index == 0 ? 256 : static_cast<int>(bytes[byte_index - 1]);
      int age_bucket = 0;
      int64_t value = error_age + 1;
      while (value > 1 && age_bucket < 7) {
        value >>= 1;
        ++age_bucket;
      }
      feature_rows[row] = {
          static_cast<uint8_t>(row & 7),
          static_cast<uint8_t>(previous == 256 ? 16 : previous >> 4),
          static_cast<uint8_t>(previous == 256 ? 16 : previous & 15),
          static_cast<uint8_t>(probabilities[row] >> 12),
          heading_map[24 + byte_index],
          static_cast<uint8_t>(age_bucket)};
      const int modal = probabilities[row] >= 32768 ? 1 : 0;
      if (truth[row] != modal) error_age = 0;
      else ++error_age;
    }

    std::vector<int32_t> loss0(kExperts * 65536);
    std::vector<int32_t> loss1(kExperts * 65536);
    for (int expert = 0; expert < kExperts; ++expert) {
      for (int p = 1; p < 65536; ++p) {
        const uint16_t q = Correct(static_cast<uint16_t>(p), expert);
        loss0[expert * 65536 + p] = static_cast<int32_t>(
            std::llround(-std::log2(
                static_cast<double>(65536u - q) / 65536.0) * kScale));
        loss1[expert * 65536 + p] = static_cast<int32_t>(
            std::llround(-std::log2(
                static_cast<double>(q) / 65536.0) * kScale));
      }
    }

    std::vector<Family> families;
    for (int first = 0; first < kFeatures; ++first) {
      Family family;
      family.first = first;
      family.categories = kCardinalities[first];
      family.losses.resize(family.categories);
      families.push_back(std::move(family));
    }
    for (int first = 0; first < kFeatures; ++first) {
      for (int second = first + 1; second < kFeatures; ++second) {
        Family family;
        family.first = first;
        family.second = second;
        family.categories =
            kCardinalities[first] * kCardinalities[second];
        family.losses.resize(family.categories);
        families.push_back(std::move(family));
      }
    }

    for (int64_t row = 0; row < train_rows; ++row) {
      const int p = probabilities[row];
      std::array<int32_t, kExperts> row_losses{};
      for (int expert = 0; expert < kExperts; ++expert) {
        row_losses[expert] =
            truth[row] ? loss1[expert * 65536 + p]
                       : loss0[expert * 65536 + p];
      }
      for (Family& family : families) {
        Losses& totals = family.losses[Category(family, feature_rows[row])];
        for (int expert = 0; expert < kExperts; ++expert)
          totals[expert] += row_losses[expert];
      }
    }

    Rule rule;
    const int64_t price_qbits = kModelBytes * 8LL * kScale;
    for (size_t family_index = 0; family_index < families.size(); ++family_index) {
      const Family& family = families[family_index];
      for (int category = 0; category < family.categories; ++category) {
        const Losses& losses = family.losses[category];
        for (int expert = 0; expert < kExperts; ++expert) {
          if (expert == kIdentity) continue;
          const int64_t gain =
              losses[kIdentity] - losses[expert] - price_qbits;
          if (gain > rule.training_gain_qbits) {
            rule = {true, static_cast<int>(family_index), category, expert, gain};
          }
        }
      }
    }

    auto matches = [&](int64_t row) {
      return rule.active &&
             Category(families[rule.family], feature_rows[row]) == rule.category;
    };
    RangeEncoder parent_full, candidate_full, parent_holdout, candidate_holdout;
    uint64_t fired_full = 0, fired_holdout = 0;
    for (int64_t row = 0; row < rows; ++row) {
      const bool fire = matches(row);
      const uint16_t q =
          fire ? Correct(probabilities[row], rule.expert) : probabilities[row];
      fired_full += fire;
      parent_full.Update(probabilities[row], truth[row]);
      candidate_full.Update(q, truth[row]);
      if (row >= train_rows) {
        fired_holdout += fire;
        parent_holdout.Update(probabilities[row], truth[row]);
        candidate_holdout.Update(q, truth[row]);
      }
    }
    parent_full.Finish();
    candidate_full.Finish();
    parent_holdout.Finish();
    candidate_holdout.Finish();

    uint64_t parent_wrt_bytes = archive.at(0) & 0x7fu;
    for (int i = 1; i < 5; ++i)
      parent_wrt_bytes = (parent_wrt_bytes << 8) | archive.at(i);
    const size_t header_bytes = parent_wrt_bytes < 10000 ? 5 : 37;
    const std::vector<uint8_t> parent_payload(
        archive.begin() + static_cast<std::ptrdiff_t>(header_bytes),
        archive.end());
    const bool parent_identity = parent_payload == parent_full.output;
    const int64_t model_bytes = rule.active ? kModelBytes : 0;
    const int64_t full_net =
        static_cast<int64_t>(parent_full.output.size()) -
        static_cast<int64_t>(candidate_full.output.size()) - model_bytes;
    const int64_t holdout_net =
        static_cast<int64_t>(parent_holdout.output.size()) -
        static_cast<int64_t>(candidate_holdout.output.size()) - model_bytes;
    const bool passes_gate = full_net >= 2000 && holdout_net >= 1000;

    std::ofstream out(argv[4]);
    if (!out) throw std::runtime_error("cannot write decision");
    out << "{\n"
        << "  \"id\": \"finite_residual_rule_pair_v1\",\n"
        << "  \"status\": \"" << (passes_gate ? "promote" : "terminal_negative")
        << "\",\n"
        << "  \"score_credit_bytes\": 0,\n"
        << "  \"rule_active\": " << (rule.active ? "true" : "false") << ",\n"
        << "  \"family_index\": " << rule.family << ",\n"
        << "  \"category\": " << rule.category << ",\n"
        << "  \"expert\": " << rule.expert << ",\n"
        << "  \"training_gain_qbits_after_price\": "
        << rule.training_gain_qbits << ",\n"
        << "  \"model_bytes\": " << model_bytes << ",\n"
        << "  \"fired_full_rows\": " << fired_full << ",\n"
        << "  \"fired_holdout_rows\": " << fired_holdout << ",\n"
        << "  \"parent_full_payload_bytes\": " << parent_full.output.size() << ",\n"
        << "  \"candidate_full_payload_bytes\": " << candidate_full.output.size() << ",\n"
        << "  \"full_net_saved_bytes\": " << full_net << ",\n"
        << "  \"parent_holdout_payload_bytes\": " << parent_holdout.output.size() << ",\n"
        << "  \"candidate_holdout_payload_bytes\": "
        << candidate_holdout.output.size() << ",\n"
        << "  \"holdout_net_saved_bytes\": " << holdout_net << ",\n"
        << "  \"holdout_net_bytes_per_million_raw\": " << holdout_net * 2 << ",\n"
        << "  \"parent_archive_identity\": "
        << (parent_identity ? "true" : "false") << ",\n"
        << "  \"decision\": \""
        << (passes_gate ? "authorize_distant_finite_residual_rule"
                        : "retire_one_rule_single_pair_conjunctions")
        << "\"\n"
        << "}\n";
    out.close();

    std::cout << "rule=" << rule.active
              << " family=" << rule.family
              << " category=" << rule.category
              << " expert=" << rule.expert
              << " train_gain_qbits=" << rule.training_gain_qbits
              << " fired_full=" << fired_full
              << " fired_holdout=" << fired_holdout
              << " full_net=" << full_net
              << " holdout_net=" << holdout_net
              << " parent_identity=" << parent_identity << "\n";
    return parent_identity ? 0 : 1;
  } catch (const std::exception& e) {
    std::cerr << e.what() << "\n";
    return 1;
  }
}
