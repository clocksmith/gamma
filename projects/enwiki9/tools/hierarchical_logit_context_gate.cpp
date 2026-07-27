#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr int kScale = 256;
constexpr int kExperts = 65;
constexpr int kPreviousValues = 257;
constexpr int kBitPositions = 8;

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

struct Choice {
  bool split = false;
  int expert = 0;
  int64_t priced_qbits = 0;
  int64_t model_bits = 0;
};

std::vector<uint8_t> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open " + path);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

uint16_t Correct(uint16_t p, int expert) {
  const uint64_t multiplier = static_cast<uint64_t>(512 + 128 * expert);
  const uint64_t numerator = static_cast<uint64_t>(p) * multiplier;
  const uint64_t denominator =
      numerator + static_cast<uint64_t>(65536u - p) * 4096u;
  uint64_t q = (numerator * 65536u + denominator / 2) / denominator;
  q = std::max<uint64_t>(1, std::min<uint64_t>(65535, q));
  return static_cast<uint16_t>(q);
}

Choice BestLeaf(const std::array<int64_t, kExperts>& losses) {
  int best = 0;
  for (int k = 1; k < kExperts; ++k)
    if (losses[k] < losses[best]) best = k;
  return {false, best, losses[best] + 8LL * kScale, 8};
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 3) {
    std::cerr << "usage: hierarchical_logit_context_gate TRACE DECISION\n";
    return 2;
  }
  try {
    const auto trace = ReadFile(argv[1]);
    constexpr char magic[] = "FX2PT01\n";
    if (trace.size() < 8 || std::memcmp(trace.data(), magic, 8) != 0 ||
        (trace.size() - 8) % 3 != 0) {
      throw std::runtime_error("invalid trace");
    }
    const int64_t rows = static_cast<int64_t>((trace.size() - 8) / 3);
    if (rows % 16) throw std::runtime_error("half trace is not byte aligned");
    const int64_t train_rows = rows / 2;
    std::vector<uint16_t> probabilities(rows);
    std::vector<uint8_t> truth(rows), bytes(rows / 8);
    for (int64_t row = 0; row < rows; ++row) {
      const size_t offset = 8 + static_cast<size_t>(row) * 3;
      probabilities[row] = static_cast<uint16_t>(
          trace[offset] | (static_cast<uint16_t>(trace[offset + 1]) << 8));
      truth[row] = trace[offset + 2];
      if (probabilities[row] == 0 || truth[row] > 1)
        throw std::runtime_error("invalid trace row");
      bytes[row / 8] =
          static_cast<uint8_t>((bytes[row / 8] << 1) | truth[row]);
    }

    std::vector<int32_t> loss0(kExperts * 65536);
    std::vector<int32_t> loss1(kExperts * 65536);
    for (int k = 0; k < kExperts; ++k) {
      for (int p = 1; p < 65536; ++p) {
        const uint16_t q = Correct(static_cast<uint16_t>(p), k);
        loss0[k * 65536 + p] = static_cast<int32_t>(
            std::llround(-std::log2(
                static_cast<double>(65536u - q) / 65536.0) * kScale));
        loss1[k * 65536 + p] = static_cast<int32_t>(
            std::llround(-std::log2(
                static_cast<double>(q) / 65536.0) * kScale));
      }
    }

    using Losses = std::array<int64_t, kExperts>;
    std::vector<Losses> group_losses(kBitPositions * kPreviousValues);
    for (int64_t row = 0; row < train_rows; ++row) {
      const int bit_position = static_cast<int>(row & 7);
      const int64_t byte_index = row / 8;
      const int previous =
          byte_index == 0 ? 256 : static_cast<int>(bytes[byte_index - 1]);
      auto& losses =
          group_losses[bit_position * kPreviousValues + previous];
      const int p = probabilities[row];
      for (int k = 0; k < kExperts; ++k) {
        losses[k] += truth[row] ? loss1[k * 65536 + p]
                               : loss0[k * 65536 + p];
      }
    }

    std::array<Losses, kBitPositions> bit_losses{};
    Losses root_losses{};
    for (int bit = 0; bit < kBitPositions; ++bit) {
      for (int previous = 0; previous < kPreviousValues; ++previous) {
        const auto& losses =
            group_losses[bit * kPreviousValues + previous];
        for (int k = 0; k < kExperts; ++k)
          bit_losses[bit][k] += losses[k];
      }
      for (int k = 0; k < kExperts; ++k)
        root_losses[k] += bit_losses[bit][k];
    }

    std::vector<Choice> group_choices(group_losses.size());
    for (size_t i = 0; i < group_losses.size(); ++i)
      group_choices[i] = BestLeaf(group_losses[i]);
    std::array<Choice, kBitPositions> bit_choices{};
    for (int bit = 0; bit < kBitPositions; ++bit) {
      const Choice leaf = BestLeaf(bit_losses[bit]);
      int64_t split_cost = kScale;
      int64_t split_bits = 1;
      for (int previous = 0; previous < kPreviousValues; ++previous) {
        const Choice& child =
            group_choices[bit * kPreviousValues + previous];
        split_cost += child.priced_qbits;
        split_bits += child.model_bits;
      }
      if (split_cost < leaf.priced_qbits)
        bit_choices[bit] = {true, 0, split_cost, split_bits};
      else
        bit_choices[bit] = leaf;
    }
    const Choice root_leaf = BestLeaf(root_losses);
    int64_t root_split_cost = kScale;
    int64_t root_split_bits = 1;
    for (const Choice& child : bit_choices) {
      root_split_cost += child.priced_qbits;
      root_split_bits += child.model_bits;
    }
    Choice root_choice = root_leaf;
    if (root_split_cost < root_leaf.priced_qbits)
      root_choice = {true, 0, root_split_cost, root_split_bits};

    auto expert_for = [&](int64_t row) {
      if (!root_choice.split) return root_choice.expert;
      const int bit = static_cast<int>(row & 7);
      if (!bit_choices[bit].split) return bit_choices[bit].expert;
      const int64_t byte_index = row / 8;
      const int previous =
          byte_index == 0 ? 256 : static_cast<int>(bytes[byte_index - 1]);
      return group_choices[bit * kPreviousValues + previous].expert;
    };

    RangeEncoder baseline, candidate;
    for (int64_t row = train_rows; row < rows; ++row) {
      baseline.Update(probabilities[row], truth[row]);
      candidate.Update(Correct(probabilities[row], expert_for(row)), truth[row]);
    }
    baseline.Finish();
    candidate.Finish();
    const int64_t model_bytes = (root_choice.model_bits + 7) / 8;
    const int64_t net =
        static_cast<int64_t>(baseline.output.size()) -
        static_cast<int64_t>(candidate.output.size()) - model_bytes;
    const double bpm = static_cast<double>(net) * 2.0;
    const bool passes_gate = bpm >= 2000.0;
    int split_bits = 0;
    for (const Choice& choice : bit_choices) split_bits += choice.split;
    const int leaf_count =
        !root_choice.split
            ? 1
            : std::accumulate(
                  bit_choices.begin(), bit_choices.end(), 0,
                  [](int total, const Choice& choice) {
                    return total + (choice.split ? kPreviousValues : 1);
                  });

    std::ofstream out(argv[2]);
    if (!out) throw std::runtime_error("cannot write decision");
    out << "{\n"
        << "  \"id\": \"hierarchical_logit_context_prevbyte_v1\",\n"
        << "  \"status\": \"" << (passes_gate ? "promote" : "terminal_negative")
        << "\",\n"
        << "  \"score_credit_bytes\": 0,\n"
        << "  \"train_rows\": " << train_rows << ",\n"
        << "  \"holdout_rows\": " << (rows - train_rows) << ",\n"
        << "  \"root_split\": " << (root_choice.split ? "true" : "false") << ",\n"
        << "  \"bit_nodes_split\": " << split_bits << ",\n"
        << "  \"selected_leaves\": " << leaf_count << ",\n"
        << "  \"model_bits\": " << root_choice.model_bits << ",\n"
        << "  \"model_bytes\": " << model_bytes << ",\n"
        << "  \"baseline_holdout_payload_bytes\": " << baseline.output.size() << ",\n"
        << "  \"candidate_holdout_payload_bytes\": " << candidate.output.size() << ",\n"
        << "  \"net_saved_bytes\": " << net << ",\n"
        << "  \"net_bytes_per_million_raw\": " << bpm << ",\n"
        << "  \"target_gate_bytes_per_million\": 2000,\n"
        << "  \"decision\": \""
        << (passes_gate ? "authorize_distant_hierarchical_logit_context"
                        : "retire_prevbyte_logit_hierarchy")
        << "\"\n"
        << "}\n";
    out.close();

    std::cout << "root_split=" << root_choice.split
              << " bit_splits=" << split_bits
              << " leaves=" << leaf_count
              << " model=" << model_bytes
              << " baseline=" << baseline.output.size()
              << " candidate=" << candidate.output.size()
              << " net=" << net
              << " bpm=" << bpm << "\n";
    return 0;
  } catch (const std::exception& e) {
    std::cerr << e.what() << "\n";
    return 1;
  }
}
