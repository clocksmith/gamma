#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

constexpr uint32_t kAlpha = 16;
constexpr uint32_t kMinimumSupport = 32;
constexpr uint32_t kPriorAuxWeight = 4096;

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

struct Counts {
  uint32_t zeros = 0;
  uint32_t ones = 0;
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

uint64_t Key(int state, int previous, int bit_position, int prefix) {
  return static_cast<uint64_t>(state) |
         (static_cast<uint64_t>(previous) << 4) |
         (static_cast<uint64_t>(bit_position) << 13) |
         (static_cast<uint64_t>(prefix) << 16);
}

uint16_t Mix(uint16_t parent, uint16_t auxiliary, uint32_t weight) {
  uint64_t q =
      (static_cast<uint64_t>(65536u - weight) * parent +
       static_cast<uint64_t>(weight) * auxiliary) >>
      16;
  q = std::max<uint64_t>(1, std::min<uint64_t>(65535, q));
  return static_cast<uint16_t>(q);
}

uint32_t UpdateWeight(uint32_t weight, uint16_t parent, uint16_t auxiliary,
                      int bit) {
  const uint32_t parent_truth = bit ? parent : 65536u - parent;
  const uint32_t auxiliary_truth = bit ? auxiliary : 65536u - auxiliary;
  const uint64_t a = static_cast<uint64_t>(weight) * auxiliary_truth;
  const uint64_t b =
      static_cast<uint64_t>(65536u - weight) * parent_truth;
  if (a + b == 0) return weight;
  uint64_t updated = (a * 65536u + (a + b) / 2) / (a + b);
  return static_cast<uint32_t>(
      std::max<uint64_t>(1, std::min<uint64_t>(65535, updated)));
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "usage: heading_state_bayes_gate TRACE ARCHIVE MAP DECISION\n";
    return 2;
  }
  try {
    const auto trace = ReadFile(argv[1]);
    const auto archive = ReadFile(argv[2]);
    const auto map = ReadFile(argv[3]);
    if (trace.size() < 8 || std::memcmp(trace.data(), "FX2PT01\n", 8) != 0 ||
        (trace.size() - 8) % 3 != 0) {
      throw std::runtime_error("invalid trace");
    }
    if (map.size() < 24 || std::memcmp(map.data(), "HEADMAP1", 8) != 0)
      throw std::runtime_error("invalid heading map");
    const int64_t rows = static_cast<int64_t>((trace.size() - 8) / 3);
    if (rows % 8) throw std::runtime_error("unaligned trace");
    const uint64_t wrt_bytes = Load64(map.data() + 8);
    const uint64_t raw_bytes = Load64(map.data() + 16);
    if (wrt_bytes != static_cast<uint64_t>(rows / 8) ||
        map.size() != 24 + wrt_bytes) {
      throw std::runtime_error("map length mismatch");
    }

    std::unordered_map<uint64_t, Counts> table;
    table.reserve(1 << 18);
    std::array<uint32_t, 10> weights{};
    weights.fill(kPriorAuxWeight);
    RangeEncoder baseline, candidate;
    int previous = 256;
    int prefix = 0;
    uint64_t mixed_rows = 0;
    for (int64_t row = 0; row < rows; ++row) {
      const size_t offset = 8 + static_cast<size_t>(row) * 3;
      const uint16_t parent = static_cast<uint16_t>(
          trace[offset] | (static_cast<uint16_t>(trace[offset + 1]) << 8));
      const int bit = trace[offset + 2];
      if (parent == 0 || bit > 1) throw std::runtime_error("invalid row");
      const int bit_position = static_cast<int>(row & 7);
      if (bit_position == 0) prefix = 0;
      const int state = map[24 + row / 8];
      const uint64_t key = Key(state, previous, bit_position, prefix);
      Counts& counts = table[key];
      const uint32_t support = counts.zeros + counts.ones;
      uint16_t auxiliary = parent;
      if (support >= kMinimumSupport) {
        uint32_t value =
            ((counts.ones + kAlpha) * 65536u) /
            (support + 2 * kAlpha);
        value = std::max<uint32_t>(1, std::min<uint32_t>(65535, value));
        auxiliary = static_cast<uint16_t>(value);
      }
      const uint16_t q = Mix(parent, auxiliary, weights[state]);
      mixed_rows += q != parent;
      baseline.Update(parent, bit);
      candidate.Update(q, bit);
      weights[state] = UpdateWeight(weights[state], parent, auxiliary, bit);
      if (bit) ++counts.ones;
      else ++counts.zeros;
      if (counts.zeros + counts.ones >= 32768) {
        counts.zeros = (counts.zeros + 1) / 2;
        counts.ones = (counts.ones + 1) / 2;
      }
      prefix = (prefix << 1) | bit;
      if (bit_position == 7) previous = prefix;
    }
    baseline.Finish();
    candidate.Finish();

    uint64_t parent_wrt_bytes = archive.at(0) & 0x7fu;
    for (int i = 1; i < 5; ++i)
      parent_wrt_bytes = (parent_wrt_bytes << 8) | archive.at(i);
    const size_t header_bytes = parent_wrt_bytes < 10000 ? 5 : 37;
    const std::vector<uint8_t> parent_payload(
        archive.begin() + static_cast<std::ptrdiff_t>(header_bytes),
        archive.end());
    const bool parent_identity = parent_payload == baseline.output;
    const int64_t net =
        static_cast<int64_t>(baseline.output.size()) -
        static_cast<int64_t>(candidate.output.size());
    const bool passes_gate = net >= 2000;

    std::ofstream out(argv[4]);
    if (!out) throw std::runtime_error("cannot write decision");
    out << "{\n"
        << "  \"id\": \"heading_state_bayes_switch_v1\",\n"
        << "  \"status\": \"" << (passes_gate ? "promote" : "terminal_negative")
        << "\",\n"
        << "  \"score_credit_bytes\": 0,\n"
        << "  \"raw_bytes\": " << raw_bytes << ",\n"
        << "  \"wrt_bytes\": " << wrt_bytes << ",\n"
        << "  \"table_rows\": " << table.size() << ",\n"
        << "  \"mixed_rows\": " << mixed_rows << ",\n"
        << "  \"baseline_payload_bytes\": " << baseline.output.size() << ",\n"
        << "  \"candidate_payload_bytes\": " << candidate.output.size() << ",\n"
        << "  \"net_saved_bytes\": " << net << ",\n"
        << "  \"net_bytes_per_million_raw\": " << net << ",\n"
        << "  \"target_gate_bytes_per_million\": 2000,\n"
        << "  \"parent_archive_identity\": "
        << (parent_identity ? "true" : "false") << ",\n"
        << "  \"final_aux_weights_q16\": [";
    for (size_t i = 0; i < weights.size(); ++i) {
      if (i) out << ", ";
      out << weights[i];
    }
    out << "],\n"
        << "  \"decision\": \""
        << (passes_gate ? "authorize_distant_heading_bayes_switch"
                        : "retire_heading_bayes_switch")
        << "\"\n"
        << "}\n";
    out.close();

    std::cout << "table=" << table.size()
              << " mixed=" << mixed_rows
              << " baseline=" << baseline.output.size()
              << " candidate=" << candidate.output.size()
              << " net=" << net
              << " weights=";
    for (uint32_t weight : weights) std::cout << weight << ",";
    std::cout << " parent_identity=" << parent_identity << "\n";
    return parent_identity ? 0 : 1;
  } catch (const std::exception& e) {
    std::cerr << e.what() << "\n";
    return 1;
  }
}
