#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <deque>
#include <fstream>
#include <iostream>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

constexpr int kTotal = 1 << 16;
constexpr int kScale = 256;
constexpr int kBlock = 64;
constexpr int kSignatures = 4;
constexpr int kRecent = 4;
constexpr int kMaxEdits = 8;
constexpr int kFixedCommandBytes = 7;
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

struct Command {
  int target;
  int source;
  std::vector<std::pair<unsigned char, unsigned char>> edits;
};

std::vector<unsigned char> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open file");
  return std::vector<unsigned char>(
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
}

uint64_t Signature(const std::vector<unsigned char>& bytes, int start, int residue) {
  uint64_t key = 0;
  for (int index = 0; index < 8; ++index) {
    key = (key << 8) | bytes[start + residue + 8 * index];
  }
  return key;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "usage: sparse_substitution_syndrome_gate TRACE ARCHIVE RAW OUTPUT\n";
    return 2;
  }
  const std::string trace_path = argv[1];
  const std::string archive_path = argv[2];
  const uint64_t raw_bytes = std::stoull(argv[3]);
  const std::string output_path = argv[4];

  const auto trace = ReadFile(trace_path);
  if (trace.size() < 8 || (trace.size() - 8) % 3 ||
      !std::equal(trace.begin(), trace.begin() + 8, kMagic)) {
    throw std::runtime_error("invalid trace");
  }
  const int64_t rows = static_cast<int64_t>((trace.size() - 8) / 3);
  if (rows % 8) throw std::runtime_error("unaligned trace");
  const int byte_count = static_cast<int>(rows / 8);
  std::vector<unsigned char> bytes(byte_count);
  std::vector<uint16_t> probabilities(rows);
  std::vector<unsigned char> truth(rows);
  std::vector<int64_t> prefix_qbits(byte_count + 1, 0);
  RangeEncoder baseline;
  for (int byte = 0; byte < byte_count; ++byte) {
    unsigned char value = 0;
    int64_t qbits = 0;
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
      qbits += static_cast<int64_t>(
          std::llround(-std::log2(probability) * kScale));
      baseline.Update(p1, bit);
    }
    bytes[byte] = value;
    prefix_qbits[byte + 1] = prefix_qbits[byte] + qbits;
  }
  baseline.Finish();

  const auto archive = ReadFile(archive_path);
  uint64_t wrt_bytes = archive.at(0) & 0x7fU;
  for (int index = 1; index < 5; ++index) wrt_bytes = (wrt_bytes << 8) | archive.at(index);
  const size_t header_bytes = wrt_bytes < 10000 ? 5 : 37;
  const std::vector<unsigned char> parent_payload(
      archive.begin() + static_cast<std::ptrdiff_t>(header_bytes), archive.end());
  const bool parent_identity = parent_payload == baseline.output;

  using Queue = std::deque<int>;
  std::array<std::unordered_map<uint64_t, Queue>, kSignatures> indexes;
  std::vector<Command> commands;
  std::vector<unsigned char> selected(byte_count, 0);
  int admitted_candidates = 0;

  for (int target = 0; target + kBlock <= byte_count; target += kBlock) {
    std::set<int> sources;
    for (int signature = 0; signature < kSignatures; ++signature) {
      const int residue = 2 * signature;
      const uint64_t key = Signature(bytes, target, residue);
      auto found = indexes[signature].find(key);
      if (found != indexes[signature].end()) {
        sources.insert(found->second.begin(), found->second.end());
      }
    }

    int best_source = -1;
    std::vector<std::pair<unsigned char, unsigned char>> best_edits;
    for (int source : sources) {
      std::vector<std::pair<unsigned char, unsigned char>> edits;
      for (int offset = 0; offset < kBlock; ++offset) {
        if (bytes[source + offset] != bytes[target + offset]) {
          edits.push_back({static_cast<unsigned char>(offset),
                           bytes[target + offset]});
          if (static_cast<int>(edits.size()) > kMaxEdits) break;
        }
      }
      if (static_cast<int>(edits.size()) <= kMaxEdits &&
          (best_source < 0 || edits.size() < best_edits.size() ||
           (edits.size() == best_edits.size() && source > best_source))) {
        best_source = source;
        best_edits = std::move(edits);
      }
    }

    if (best_source >= 0) {
      ++admitted_candidates;
      const int command_bytes =
          kFixedCommandBytes + 2 * static_cast<int>(best_edits.size());
      const int64_t omitted =
          prefix_qbits[target + kBlock] - prefix_qbits[target];
      if (omitted > static_cast<int64_t>(command_bytes) * 8 * kScale) {
        commands.push_back({target, best_source, best_edits});
        for (int offset = 0; offset < kBlock; ++offset) selected[target + offset] = 1;
      }
    }

    for (int signature = 0; signature < kSignatures; ++signature) {
      const int residue = 2 * signature;
      const uint64_t key = Signature(bytes, target, residue);
      auto& queue = indexes[signature][key];
      queue.push_front(target);
      if (static_cast<int>(queue.size()) > kRecent) queue.pop_back();
    }
  }

  RangeEncoder literal_encoder;
  std::vector<unsigned char> literals;
  for (int byte = 0; byte < byte_count; ++byte) {
    if (!selected[byte]) {
      literals.push_back(bytes[byte]);
      for (int bit = 0; bit < 8; ++bit) {
        const int64_t row = static_cast<int64_t>(byte) * 8 + bit;
        literal_encoder.Update(probabilities[row], truth[row]);
      }
    }
  }
  literal_encoder.Finish();

  std::vector<int> command_at(byte_count, -1);
  for (size_t index = 0; index < commands.size(); ++index) {
    command_at[commands[index].target] = static_cast<int>(index);
  }
  std::vector<unsigned char> reconstructed;
  reconstructed.reserve(byte_count);
  size_t literal_index = 0;
  for (int position = 0; position < byte_count;) {
    const int command_index = command_at[position];
    if (command_index < 0) {
      reconstructed.push_back(literals[literal_index++]);
      ++position;
      continue;
    }
    const Command& command = commands[command_index];
    std::array<unsigned char, kBlock> block{};
    for (int offset = 0; offset < kBlock; ++offset) {
      block[offset] = reconstructed[command.source + offset];
    }
    for (const auto& edit : command.edits) block[edit.first] = edit.second;
    reconstructed.insert(reconstructed.end(), block.begin(), block.end());
    position += kBlock;
  }
  const bool roundtrip = reconstructed == bytes && literal_index == literals.size();

  int64_t side_bytes = kHeaderBytes;
  for (const auto& command : commands) {
    side_bytes += kFixedCommandBytes + 2 * command.edits.size();
  }
  const int64_t candidate_total =
      static_cast<int64_t>(literal_encoder.output.size()) + side_bytes;
  const int64_t net = static_cast<int64_t>(baseline.output.size()) - candidate_total;
  const double net_bpm = net * 1000000.0 / raw_bytes;
  const bool pass = parent_identity && roundtrip && net_bpm >= kTargetBpm;

  std::ofstream output(output_path);
  if (!output) throw std::runtime_error("cannot create output");
  output << "{\n";
  output << "  \"schema\": \"sparse_substitution_syndrome_gate_v1\",\n";
  output << "  \"candidate\": \"sparse_substitution_syndrome_b64_v1\",\n";
  output << "  \"raw_scope_bytes\": " << raw_bytes << ",\n";
  output << "  \"wrt_bytes\": " << byte_count << ",\n";
  output << "  \"parent_payload_bytes\": " << parent_payload.size() << ",\n";
  output << "  \"parent_payload_identity\": "
         << (parent_identity ? "true" : "false") << ",\n";
  output << "  \"admitted_candidates\": " << admitted_candidates << ",\n";
  output << "  \"selected_blocks\": " << commands.size() << ",\n";
  output << "  \"literal_payload_bytes\": " << literal_encoder.output.size() << ",\n";
  output << "  \"side_bytes\": " << side_bytes << ",\n";
  output << "  \"candidate_total_bytes\": " << candidate_total << ",\n";
  output << "  \"net_saved_bytes\": " << net << ",\n";
  output << "  \"net_saved_bpm\": " << net_bpm << ",\n";
  output << "  \"roundtrip_ok\": " << (roundtrip ? "true" : "false") << ",\n";
  output << "  \"required_net_saved_bpm\": " << kTargetBpm << ",\n";
  output << "  \"pass\": " << (pass ? "true" : "false") << ",\n";
  output << "  \"decision\": \""
         << (pass ? "promote_sparse_substitution_to_native_gate"
                  : "retire_sparse_substitution_b64")
         << "\",\n";
  output << "  \"score_credit_bytes\": 0,\n";
  output << "  \"claim_boundary\": \"Exact parent identity and byte transform "
            "roundtrip shadow; native source and decoder integration uncounted.\"\n";
  output << "}\n";
  std::cout << "net_bpm=" << net_bpm << " selected=" << commands.size()
            << " admitted=" << admitted_candidates
            << " decision=" << (pass ? "promote" : "retire") << "\n";
  return 0;
}
