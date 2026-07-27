#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr int kDepth = 10;
constexpr int kNodes = (1 << (kDepth + 1)) - 1;
constexpr int kActions = 9;
constexpr int kTotal = 1 << 16;
constexpr uint32_t kMaxCode = 0xffffffffU;
constexpr int kScale = 256;
constexpr double kTargetBpm = 2000.0;
constexpr std::array<int, kActions> kNum = {1, 1, 3, 7, 1, 8, 4, 2, 4};
constexpr std::array<int, kActions> kDen = {4, 2, 4, 8, 1, 7, 3, 1, 1};
constexpr char kMagic[] = "FX2PT01\n";

struct RangeEncoder {
  uint32_t x1 = 0;
  uint32_t x2 = kMaxCode;
  std::vector<unsigned char> output;

  void Update(uint16_t p1, int bit) {
    const uint32_t delta = x2 - x1;
    const uint32_t midpoint =
        x1 + (delta >> 16) * p1 + ((delta & 0xffffU) * p1 >> 16);
    if (bit) {
      x2 = midpoint;
    } else {
      x1 = midpoint + 1;
    }
    while (((x1 ^ x2) & 0xff000000U) == 0) {
      output.push_back(static_cast<unsigned char>(x2 >> 24));
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
  }

  void Finish() {
    while (((x1 ^ x2) & 0xff000000U) == 0) {
      output.push_back(static_cast<unsigned char>(x2 >> 24));
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
    output.push_back(static_cast<unsigned char>(x2 >> 24));
  }
};

struct Row {
  uint16_t p1;
  int bit;
};

Row ReadRow(std::ifstream& input) {
  unsigned char bytes[3];
  input.read(reinterpret_cast<char*>(bytes), 3);
  if (!input) throw std::runtime_error("truncated FX2PT row");
  const uint16_t p1 =
      static_cast<uint16_t>(bytes[0] | (static_cast<uint16_t>(bytes[1]) << 8));
  if (p1 == 0 || bytes[2] > 1) throw std::runtime_error("invalid FX2PT row");
  return {p1, static_cast<int>(bytes[2])};
}

uint16_t Correct(int action, uint16_t p1) {
  const uint64_t numerator = static_cast<uint64_t>(kNum[action]) * p1;
  const uint64_t denominator =
      static_cast<uint64_t>(kDen[action]) * (kTotal - p1) + numerator;
  uint64_t q = (static_cast<uint64_t>(kTotal) * numerator + denominator / 2) /
               denominator;
  q = std::max<uint64_t>(1, std::min<uint64_t>(kTotal - 1, q));
  return static_cast<uint16_t>(q);
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "usage: residual_odds_tree_gate TRACE RAW_BYTES OUTPUT\n";
    return 2;
  }
  const std::string trace_path = argv[1];
  const uint64_t raw_bytes = std::stoull(argv[2]);
  const std::string output_path = argv[3];

  std::ifstream input(trace_path, std::ios::binary | std::ios::ate);
  if (!input) throw std::runtime_error("cannot open trace");
  const uint64_t size = static_cast<uint64_t>(input.tellg());
  if (size < 8 || (size - 8) % 3 != 0) throw std::runtime_error("bad size");
  const uint64_t rows = (size - 8) / 3;
  uint64_t split = rows / 2;
  split -= split % 8;
  input.seekg(0);
  char magic[8];
  input.read(magic, 8);
  if (!input || !std::equal(magic, magic + 8, kMagic)) {
    throw std::runtime_error("bad magic");
  }

  std::array<std::array<uint16_t, kTotal>, kActions> adjusted{};
  std::array<std::array<int32_t, kTotal>, kActions> cost0{};
  std::array<std::array<int32_t, kTotal>, kActions> cost1{};
  for (int action = 0; action < kActions; ++action) {
    for (int p = 1; p < kTotal; ++p) {
      const uint16_t q = Correct(action, static_cast<uint16_t>(p));
      adjusted[action][p] = q;
      const double probability = static_cast<double>(q) / kTotal;
      cost0[action][p] =
          static_cast<int32_t>(std::llround(-std::log2(1.0 - probability) * kScale));
      cost1[action][p] =
          static_cast<int32_t>(std::llround(-std::log2(probability) * kScale));
    }
  }

  std::vector<std::array<int64_t, kActions>> losses(kNodes);
  for (auto& row : losses) row.fill(0);
  uint32_t history = 0;
  const uint32_t history_mask = (1U << kDepth) - 1;

  for (uint64_t index = 0; index < split; ++index) {
    const Row row = ReadRow(input);
    int node = 0;
    for (int depth = 0; depth <= kDepth; ++depth) {
      for (int action = 0; action < kActions; ++action) {
        losses[node][action] +=
            row.bit ? cost1[action][row.p1] : cost0[action][row.p1];
      }
      if (depth < kDepth) {
        const int branch = (history >> depth) & 1U;
        node = 2 * node + 1 + branch;
      }
    }
    const int residual = row.bit ^ (row.p1 >= kTotal / 2);
    history = ((history << 1) | residual) & history_mask;
  }

  std::vector<int64_t> optimum(kNodes, 0);
  std::vector<int> action_choice(kNodes, 0);
  std::vector<unsigned char> split_choice(kNodes, 0);
  constexpr int64_t kLeafPrice = 5 * kScale;
  constexpr int64_t kSplitPrice = 1 * kScale;
  for (int node = kNodes - 1; node >= 0; --node) {
    int best_action = 0;
    for (int action = 1; action < kActions; ++action) {
      if (losses[node][action] < losses[node][best_action]) best_action = action;
    }
    const int64_t leaf = losses[node][best_action] + kLeafPrice;
    action_choice[node] = best_action;
    const int left = 2 * node + 1;
    if (left >= kNodes) {
      optimum[node] = leaf;
      continue;
    }
    const int64_t split_cost = kSplitPrice + optimum[left] + optimum[left + 1];
    if (split_cost < leaf) {
      optimum[node] = split_cost;
      split_choice[node] = 1;
    } else {
      optimum[node] = leaf;
    }
  }

  int leaves = 0;
  int splits = 0;
  std::array<int, kActions> action_leaves{};
  std::vector<int> stack = {0};
  while (!stack.empty()) {
    const int node = stack.back();
    stack.pop_back();
    if (split_choice[node]) {
      ++splits;
      stack.push_back(2 * node + 2);
      stack.push_back(2 * node + 1);
    } else {
      ++leaves;
      ++action_leaves[action_choice[node]];
    }
  }
  const int model_bits = splits + 5 * leaves;
  const int model_bytes = (model_bits + 7) / 8;

  RangeEncoder baseline;
  RangeEncoder candidate;
  const uint64_t holdout_rows = rows - split;
  for (uint64_t index = split; index < rows; ++index) {
    const Row row = ReadRow(input);
    int node = 0;
    int depth = 0;
    while (split_choice[node] && depth < kDepth) {
      const int branch = (history >> depth) & 1U;
      node = 2 * node + 1 + branch;
      ++depth;
    }
    const int action = action_choice[node];
    baseline.Update(row.p1, row.bit);
    candidate.Update(adjusted[action][row.p1], row.bit);
    const int residual = row.bit ^ (row.p1 >= kTotal / 2);
    history = ((history << 1) | residual) & history_mask;
  }
  baseline.Finish();
  candidate.Finish();

  const int64_t gross =
      static_cast<int64_t>(baseline.output.size()) -
      static_cast<int64_t>(candidate.output.size());
  const int64_t net = gross - model_bytes;
  const double holdout_raw =
      static_cast<double>(raw_bytes) * holdout_rows / rows;
  const double net_bpm = net * 1000000.0 / holdout_raw;
  const bool pass = net_bpm >= kTargetBpm;

  std::ofstream output(output_path);
  if (!output) throw std::runtime_error("cannot create output");
  output << "{\n";
  output << "  \"schema\": \"residual_odds_tree_gate_v1\",\n";
  output << "  \"candidate\": \"residual_odds_tree_d10_v1\",\n";
  output << "  \"rows\": " << rows << ",\n";
  output << "  \"train_rows\": " << split << ",\n";
  output << "  \"holdout_rows\": " << holdout_rows << ",\n";
  output << "  \"depth\": " << kDepth << ",\n";
  output << "  \"actions\": " << kActions << ",\n";
  output << "  \"split_nodes\": " << splits << ",\n";
  output << "  \"leaf_nodes\": " << leaves << ",\n";
  output << "  \"model_bits\": " << model_bits << ",\n";
  output << "  \"model_bytes\": " << model_bytes << ",\n";
  output << "  \"baseline_payload_bytes\": " << baseline.output.size() << ",\n";
  output << "  \"candidate_payload_bytes\": " << candidate.output.size() << ",\n";
  output << "  \"gross_saved_bytes\": " << gross << ",\n";
  output << "  \"net_saved_bytes\": " << net << ",\n";
  output << "  \"net_saved_bpm\": " << net_bpm << ",\n";
  output << "  \"required_net_saved_bpm\": " << kTargetBpm << ",\n";
  output << "  \"pass\": " << (pass ? "true" : "false") << ",\n";
  output << "  \"decision\": \""
         << (pass ? "promote_residual_odds_tree_to_distant_gate"
                  : "retire_residual_odds_tree_d10")
         << "\",\n";
  output << "  \"score_credit_bytes\": 0,\n";
  output << "  \"claim_boundary\": \"Chronological exact range replay; model bits "
            "charged; native integration and distant transfer absent.\"\n";
  output << "}\n";
  output.close();
  std::cout << "net_bpm=" << net_bpm << " leaves=" << leaves
            << " decision=" << (pass ? "promote" : "retire") << "\n";
  return 0;
}
