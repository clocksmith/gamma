#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr int kTotal = 1 << 16;
constexpr int kScale = 256;
constexpr int kHeaderBytes = 4;
constexpr double kTargetBpm = 2000.0;
constexpr uint32_t kMaxCode = 0xffffffffU;
constexpr char kMagic[] = "FX2PT01\n";

struct RangeEncoder {
  uint32_t x1 = 0;
  uint32_t x2 = kMaxCode;
  std::vector<unsigned char> output;
  void Update(uint16_t p1, int bit) {
    const uint32_t delta = x2 - x1;
    const uint32_t midpoint =
        x1 + (delta >> 16) * p1 + ((delta & 0xffffU) * p1 >> 16);
    if (bit) x2 = midpoint;
    else x1 = midpoint + 1;
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

std::vector<unsigned char> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open file");
  return std::vector<unsigned char>(
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "usage: sparse_surprise_extraction_gate TRACE ARCHIVE RAW OUTPUT\n";
    return 2;
  }
  const auto trace = ReadFile(argv[1]);
  const auto archive = ReadFile(argv[2]);
  const uint64_t raw_bytes = std::stoull(argv[3]);
  const std::string output_path = argv[4];

  if (trace.size() < 8 || (trace.size() - 8) % 3 ||
      !std::equal(trace.begin(), trace.begin() + 8, kMagic)) {
    throw std::runtime_error("invalid trace");
  }
  const int64_t rows = static_cast<int64_t>((trace.size() - 8) / 3);
  if (rows % 8) throw std::runtime_error("unaligned trace");
  const int n = static_cast<int>(rows / 8);
  std::vector<unsigned char> bytes(n);
  std::vector<uint16_t> probabilities(rows);
  std::vector<unsigned char> truth(rows);
  std::vector<int64_t> weights(n, 0);
  RangeEncoder baseline;
  for (int byte = 0; byte < n; ++byte) {
    unsigned char value = 0;
    for (int bit_index = 0; bit_index < 8; ++bit_index) {
      const int64_t row = static_cast<int64_t>(byte) * 8 + bit_index;
      const size_t offset = 8 + static_cast<size_t>(row) * 3;
      const uint16_t p1 = static_cast<uint16_t>(
          trace[offset] | (static_cast<uint16_t>(trace[offset + 1]) << 8));
      const int bit = trace[offset + 2];
      if (p1 == 0 || bit > 1) throw std::runtime_error("invalid row");
      probabilities[row] = p1;
      truth[row] = static_cast<unsigned char>(bit);
      value = static_cast<unsigned char>((value << 1) | bit);
      const double probability = bit ? static_cast<double>(p1) / kTotal
                                     : 1.0 - static_cast<double>(p1) / kTotal;
      weights[byte] += static_cast<int64_t>(
          std::llround(-std::log2(probability) * kScale));
      baseline.Update(p1, bit);
    }
    bytes[byte] = value;
  }
  baseline.Finish();

  uint64_t wrt_bytes = archive.at(0) & 0x7fU;
  for (int index = 1; index < 5; ++index) wrt_bytes = (wrt_bytes << 8) | archive.at(index);
  const size_t header_bytes = wrt_bytes < 10000 ? 5 : 37;
  const std::vector<unsigned char> parent_payload(
      archive.begin() + static_cast<std::ptrdiff_t>(header_bytes), archive.end());
  const bool parent_identity = parent_payload == baseline.output;

  std::vector<int> order(n);
  std::iota(order.begin(), order.end(), 0);
  std::sort(order.begin(), order.end(), [&](int left, int right) {
    if (weights[left] != weights[right]) return weights[left] > weights[right];
    return left < right;
  });

  int best_k = 0;
  double best_ideal_bits = -kHeaderBytes * 8.0;
  double best_log_choose = 0.0;
  int64_t prefix_qbits = 0;
  double log_choose = 0.0;
  for (int k = 1; k <= n; ++k) {
    prefix_qbits += weights[order[k - 1]];
    log_choose += std::log2(static_cast<double>(n - k + 1)) -
                  std::log2(static_cast<double>(k));
    const double benefit_bits =
        static_cast<double>(prefix_qbits) / kScale -
        kHeaderBytes * 8.0 - k * 8.0 - log_choose;
    if (benefit_bits > best_ideal_bits) {
      best_ideal_bits = benefit_bits;
      best_k = k;
      best_log_choose = log_choose;
    }
  }

  std::vector<unsigned char> selected(n, 0);
  for (int index = 0; index < best_k; ++index) selected[order[index]] = 1;
  RangeEncoder literal_encoder;
  std::vector<unsigned char> literals;
  std::vector<unsigned char> selected_values;
  for (int byte = 0; byte < n; ++byte) {
    if (selected[byte]) {
      selected_values.push_back(bytes[byte]);
    } else {
      literals.push_back(bytes[byte]);
      for (int bit = 0; bit < 8; ++bit) {
        const int64_t row = static_cast<int64_t>(byte) * 8 + bit;
        literal_encoder.Update(probabilities[row], truth[row]);
      }
    }
  }
  literal_encoder.Finish();

  std::vector<unsigned char> reconstructed;
  reconstructed.reserve(n);
  size_t literal_cursor = 0;
  size_t selected_cursor = 0;
  for (int position = 0; position < n; ++position) {
    reconstructed.push_back(
        selected[position] ? selected_values[selected_cursor++]
                           : literals[literal_cursor++]);
  }
  const bool roundtrip = reconstructed == bytes;
  const int64_t position_bytes =
      static_cast<int64_t>(std::ceil(best_log_choose / 8.0));
  const int64_t side_bytes =
      kHeaderBytes + static_cast<int64_t>(best_k) + position_bytes;
  const int64_t candidate_total =
      static_cast<int64_t>(literal_encoder.output.size()) + side_bytes;
  const int64_t net =
      static_cast<int64_t>(baseline.output.size()) - candidate_total;
  const double net_bpm = net * 1000000.0 / raw_bytes;
  const bool pass = parent_identity && roundtrip && net_bpm >= kTargetBpm;

  std::ofstream output(output_path);
  if (!output) throw std::runtime_error("cannot create output");
  output << "{\n";
  output << "  \"schema\": \"sparse_surprise_extraction_gate_v1\",\n";
  output << "  \"candidate\": \"sparse_surprise_enumerative_v1\",\n";
  output << "  \"raw_scope_bytes\": " << raw_bytes << ",\n";
  output << "  \"wrt_bytes\": " << n << ",\n";
  output << "  \"parent_payload_bytes\": " << parent_payload.size() << ",\n";
  output << "  \"parent_payload_identity\": "
         << (parent_identity ? "true" : "false") << ",\n";
  output << "  \"selected_bytes\": " << best_k << ",\n";
  output << "  \"ideal_selected_benefit_bits\": " << best_ideal_bits << ",\n";
  output << "  \"position_rank_bytes\": " << position_bytes << ",\n";
  output << "  \"literal_payload_bytes\": " << literal_encoder.output.size() << ",\n";
  output << "  \"side_bytes\": " << side_bytes << ",\n";
  output << "  \"candidate_total_bytes\": " << candidate_total << ",\n";
  output << "  \"net_saved_bytes\": " << net << ",\n";
  output << "  \"net_saved_bpm\": " << net_bpm << ",\n";
  output << "  \"roundtrip_ok\": " << (roundtrip ? "true" : "false") << ",\n";
  output << "  \"required_net_saved_bpm\": " << kTargetBpm << ",\n";
  output << "  \"pass\": " << (pass ? "true" : "false") << ",\n";
  output << "  \"decision\": \""
         << (pass ? "promote_sparse_surprise_to_native_gate"
                  : "retire_sparse_surprise_enumerative")
         << "\",\n";
  output << "  \"score_credit_bytes\": 0,\n";
  output << "  \"claim_boundary\": \"Exact parent identity and transform "
            "roundtrip; enumerative position bits are exactly counted but native "
            "rank coding and source package are unimplemented.\"\n";
  output << "}\n";
  std::cout << "net_bpm=" << net_bpm << " selected=" << best_k
            << " ideal_bits=" << best_ideal_bits
            << " decision=" << (pass ? "promote" : "retire") << "\n";
  return 0;
}
