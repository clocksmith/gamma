#include <algorithm>
#include <cmath>
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

constexpr int kScale = 256;
constexpr int kBlockBytes = 8;
constexpr int kDescriptorBytes = 6;
constexpr int kHeaderBytes = 4;

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

struct Fiber {
  int source = 0;
  std::vector<int> targets;
  int64_t rank_bits = 0;
  int64_t ideal_gain_qbits = 0;
};

std::vector<uint8_t> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open " + path);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

long double Log2Choose(int64_t n, int64_t k) {
  if (k == 0 || k == n) return 0;
  return (std::lgammal(static_cast<long double>(n) + 1) -
          std::lgammal(static_cast<long double>(k) + 1) -
          std::lgammal(static_cast<long double>(n - k) + 1)) /
         std::log(2.0L);
}

uint64_t BlockKey(const std::vector<uint8_t>& bytes, int block) {
  uint64_t key = 0;
  const int start = block * kBlockBytes;
  for (int i = 0; i < kBlockBytes; ++i) key = (key << 8) | bytes[start + i];
  return key;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "usage: amortized_block_fiber_gate TRACE ARCHIVE DECISION\n";
    return 2;
  }
  try {
    const auto trace = ReadFile(argv[1]);
    const auto archive = ReadFile(argv[2]);
    constexpr char magic[] = "FX2PT01\n";
    if (trace.size() < 8 || std::memcmp(trace.data(), magic, 8) != 0 ||
        (trace.size() - 8) % 3 != 0) {
      throw std::runtime_error("invalid trace");
    }
    const int64_t rows = static_cast<int64_t>((trace.size() - 8) / 3);
    if (rows % 8) throw std::runtime_error("unaligned trace");
    const int n = static_cast<int>(rows / 8);
    const int block_count = n / kBlockBytes;
    std::vector<uint16_t> probabilities(rows);
    std::vector<uint8_t> truth(rows), bytes(n);
    std::vector<int64_t> block_qbits(block_count, 0);
    RangeEncoder baseline;
    for (int byte = 0; byte < n; ++byte) {
      uint8_t value = 0;
      for (int bit_index = 0; bit_index < 8; ++bit_index) {
        const int64_t row = static_cast<int64_t>(byte) * 8 + bit_index;
        const size_t offset = 8 + static_cast<size_t>(row) * 3;
        const uint16_t p1 = static_cast<uint16_t>(
            trace[offset] | (static_cast<uint16_t>(trace[offset + 1]) << 8));
        const int bit = trace[offset + 2];
        if (p1 == 0 || bit > 1) throw std::runtime_error("invalid row");
        probabilities[row] = p1;
        truth[row] = static_cast<uint8_t>(bit);
        value = static_cast<uint8_t>((value << 1) | bit);
        const double probability =
            bit ? static_cast<double>(p1) / 65536.0
                : 1.0 - static_cast<double>(p1) / 65536.0;
        if (byte / kBlockBytes < block_count) {
          block_qbits[byte / kBlockBytes] += static_cast<int64_t>(
              std::llround(-std::log2(probability) * kScale));
        }
        baseline.Update(p1, bit);
      }
      bytes[byte] = value;
    }
    baseline.Finish();

    uint64_t wrt_bytes = archive.at(0) & 0x7fu;
    for (int i = 1; i < 5; ++i) wrt_bytes = (wrt_bytes << 8) | archive.at(i);
    const size_t header_bytes = wrt_bytes < 10000 ? 5 : 37;
    const std::vector<uint8_t> parent_payload(
        archive.begin() + static_cast<std::ptrdiff_t>(header_bytes),
        archive.end());
    const bool parent_identity = parent_payload == baseline.output;

    std::unordered_map<uint64_t, std::vector<int>> classes;
    classes.reserve(block_count * 2);
    for (int block = 0; block < block_count; ++block)
      classes[BlockKey(bytes, block)].push_back(block);

    std::vector<Fiber> fibers;
    for (auto& entry : classes) {
      auto& positions = entry.second;
      if (positions.size() < 2) continue;
      const int source = positions.front();
      std::vector<int> candidates(positions.begin() + 1, positions.end());
      std::sort(candidates.begin(), candidates.end(), [&](int a, int b) {
        if (block_qbits[a] != block_qbits[b])
          return block_qbits[a] > block_qbits[b];
        return a < b;
      });
      int best_k = 0;
      int64_t best_gain = 0;
      int64_t best_rank_bits = 0;
      int64_t prefix = 0;
      for (int k = 1; k <= static_cast<int>(candidates.size()); ++k) {
        prefix += block_qbits[candidates[k - 1]];
        const int64_t rank_bits =
            static_cast<int64_t>(std::ceil(Log2Choose(block_count - 1, k)));
        const int64_t gain =
            prefix -
            static_cast<int64_t>(kScale) *
                (kDescriptorBytes * 8 + rank_bits);
        if (gain > best_gain) {
          best_gain = gain;
          best_k = k;
          best_rank_bits = rank_bits;
        }
      }
      if (best_k > 0) {
        candidates.resize(best_k);
        std::sort(candidates.begin(), candidates.end());
        fibers.push_back({source, std::move(candidates), best_rank_bits, best_gain});
      }
    }
    std::sort(fibers.begin(), fibers.end(),
              [](const Fiber& a, const Fiber& b) { return a.source < b.source; });

    std::vector<int> target_source(block_count, -1);
    int64_t total_rank_bits = 0;
    for (const auto& fiber : fibers) {
      total_rank_bits += fiber.rank_bits;
      for (int target : fiber.targets) {
        if (target_source[target] >= 0)
          throw std::runtime_error("duplicate block target");
        target_source[target] = fiber.source;
      }
    }

    RangeEncoder literal_encoder;
    std::vector<uint8_t> literals;
    literals.reserve(n);
    for (int byte = 0; byte < n; ++byte) {
      const int block = byte / kBlockBytes;
      const bool selected =
          block < block_count && target_source[block] >= 0;
      if (selected) continue;
      literals.push_back(bytes[byte]);
      for (int bit = 0; bit < 8; ++bit) {
        const int64_t row = static_cast<int64_t>(byte) * 8 + bit;
        literal_encoder.Update(probabilities[row], truth[row]);
      }
    }
    literal_encoder.Finish();

    std::vector<uint8_t> reconstructed;
    reconstructed.reserve(n);
    size_t literal_index = 0;
    for (int block = 0; block < block_count; ++block) {
      if (target_source[block] >= 0) {
        const int source_byte = target_source[block] * kBlockBytes;
        if (source_byte + kBlockBytes > static_cast<int>(reconstructed.size()))
          throw std::runtime_error("invalid fiber source");
        for (int i = 0; i < kBlockBytes; ++i)
          reconstructed.push_back(reconstructed[source_byte + i]);
      } else {
        for (int i = 0; i < kBlockBytes; ++i) {
          if (literal_index >= literals.size())
            throw std::runtime_error("literal underrun");
          reconstructed.push_back(literals[literal_index++]);
        }
      }
    }
    while (static_cast<int>(reconstructed.size()) < n) {
      if (literal_index >= literals.size())
        throw std::runtime_error("tail underrun");
      reconstructed.push_back(literals[literal_index++]);
    }
    const bool roundtrip =
        reconstructed == bytes && literal_index == literals.size();
    const int64_t selected_targets = std::count_if(
        target_source.begin(), target_source.end(), [](int s) { return s >= 0; });
    const int64_t side_bytes =
        kHeaderBytes +
        static_cast<int64_t>(fibers.size()) * kDescriptorBytes +
        (total_rank_bits + 7) / 8;
    const int64_t candidate_bytes =
        static_cast<int64_t>(literal_encoder.output.size()) + side_bytes;
    const int64_t net =
        static_cast<int64_t>(baseline.output.size()) - candidate_bytes;
    const bool passes_gate = net >= 2000;

    std::ofstream out(argv[3]);
    if (!out) throw std::runtime_error("cannot write decision");
    out << "{\n"
        << "  \"id\": \"amortized_block_fiber_b8_v1\",\n"
        << "  \"status\": \"" << (passes_gate ? "promote" : "terminal_negative")
        << "\",\n"
        << "  \"score_credit_bytes\": 0,\n"
        << "  \"block_bytes\": " << kBlockBytes << ",\n"
        << "  \"block_count\": " << block_count << ",\n"
        << "  \"selected_fibers\": " << fibers.size() << ",\n"
        << "  \"selected_targets\": " << selected_targets << ",\n"
        << "  \"rank_bits\": " << total_rank_bits << ",\n"
        << "  \"baseline_payload_bytes\": " << baseline.output.size() << ",\n"
        << "  \"literal_payload_bytes\": " << literal_encoder.output.size() << ",\n"
        << "  \"side_bytes\": " << side_bytes << ",\n"
        << "  \"candidate_total_bytes\": " << candidate_bytes << ",\n"
        << "  \"net_saved_bytes\": " << net << ",\n"
        << "  \"net_bytes_per_million_raw\": " << net << ",\n"
        << "  \"target_gate_bytes_per_million\": 2000,\n"
        << "  \"parent_archive_identity\": "
        << (parent_identity ? "true" : "false") << ",\n"
        << "  \"exact_wrt_roundtrip\": " << (roundtrip ? "true" : "false") << ",\n"
        << "  \"decision\": \""
        << (passes_gate ? "authorize_distant_amortized_block_fibers"
                        : "retire_amortized_block_fiber_b8")
        << "\"\n"
        << "}\n";
    out.close();

    std::cout << "fibers=" << fibers.size()
              << " targets=" << selected_targets
              << " rank_bits=" << total_rank_bits
              << " baseline=" << baseline.output.size()
              << " literal=" << literal_encoder.output.size()
              << " side=" << side_bytes
              << " net=" << net
              << " parent_identity=" << parent_identity
              << " roundtrip=" << roundtrip << "\n";
    return (parent_identity && roundtrip) ? 0 : 1;
  } catch (const std::exception& e) {
    std::cerr << e.what() << "\n";
    return 1;
  }
}
