#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <deque>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

constexpr int kTotal = 1 << 16;
constexpr int kScale = 256;
constexpr int kKeyBytes = 8;
constexpr int kRecent = 4;
constexpr int kMaxLength = 255;
constexpr int kCommandBytes = 7;
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

struct Candidate {
  int start;
  int source;
  int length;
  int end;
  int64_t weight;
};

uint64_t Key(const std::vector<unsigned char>& bytes, int position) {
  uint64_t key = 0;
  for (int offset = 0; offset < kKeyBytes; ++offset) {
    key = (key << 8) | bytes[position + offset];
  }
  return key;
}

std::vector<unsigned char> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open file");
  return std::vector<unsigned char>(
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "usage: causal_copy_cover_gate TRACE ARCHIVE RAW_BYTES OUTPUT\n";
    return 2;
  }
  const std::string trace_path = argv[1];
  const std::string archive_path = argv[2];
  const uint64_t raw_bytes = std::stoull(argv[3]);
  const std::string output_path = argv[4];

  const std::vector<unsigned char> trace = ReadFile(trace_path);
  if (trace.size() < 8 || (trace.size() - 8) % 3 != 0 ||
      !std::equal(trace.begin(), trace.begin() + 8, kMagic)) {
    throw std::runtime_error("invalid FX2PT trace");
  }
  const int64_t rows = static_cast<int64_t>((trace.size() - 8) / 3);
  if (rows % 8 != 0) throw std::runtime_error("trace is not byte aligned");
  const int byte_count = static_cast<int>(rows / 8);

  std::vector<uint16_t> probabilities(rows);
  std::vector<unsigned char> truth(rows);
  std::vector<unsigned char> bytes(byte_count);
  std::vector<int64_t> prefix_qbits(byte_count + 1, 0);
  RangeEncoder baseline;
  for (int byte = 0; byte < byte_count; ++byte) {
    unsigned char value = 0;
    int64_t byte_qbits = 0;
    for (int bit_index = 0; bit_index < 8; ++bit_index) {
      const int64_t row = static_cast<int64_t>(byte) * 8 + bit_index;
      const size_t offset = 8 + static_cast<size_t>(row) * 3;
      const uint16_t p1 = static_cast<uint16_t>(
          trace[offset] | (static_cast<uint16_t>(trace[offset + 1]) << 8));
      const int bit = trace[offset + 2];
      if (p1 == 0 || bit > 1) throw std::runtime_error("invalid trace row");
      probabilities[row] = p1;
      truth[row] = static_cast<unsigned char>(bit);
      value = static_cast<unsigned char>((value << 1) | bit);
      const double probability = bit
          ? static_cast<double>(p1) / kTotal
          : 1.0 - static_cast<double>(p1) / kTotal;
      byte_qbits += static_cast<int64_t>(
          std::llround(-std::log2(probability) * kScale));
      baseline.Update(p1, bit);
    }
    bytes[byte] = value;
    prefix_qbits[byte + 1] = prefix_qbits[byte] + byte_qbits;
  }
  baseline.Finish();

  const std::vector<unsigned char> archive = ReadFile(archive_path);
  if (archive.size() < 38) throw std::runtime_error("archive truncated");
  uint64_t wrt_bytes = archive[0] & 0x7fU;
  for (int index = 1; index < 5; ++index) {
    wrt_bytes = (wrt_bytes << 8) | archive[index];
  }
  const size_t header_bytes = wrt_bytes < 10000 ? 5 : 37;
  const std::vector<unsigned char> parent_payload(
      archive.begin() + static_cast<std::ptrdiff_t>(header_bytes), archive.end());
  const bool parent_identity = parent_payload == baseline.output;

  std::unordered_map<uint64_t, std::deque<int>> recent;
  std::vector<Candidate> candidates;
  candidates.reserve(byte_count / 4);
  for (int start = 0; start + kKeyBytes <= byte_count; ++start) {
    const uint64_t key = Key(bytes, start);
    auto found = recent.find(key);
    int best_source = -1;
    int best_length = 0;
    if (found != recent.end()) {
      for (int source : found->second) {
        int length = kKeyBytes;
        while (length < kMaxLength && start + length < byte_count &&
               bytes[source + length] == bytes[start + length]) {
          ++length;
        }
        if (length > best_length ||
            (length == best_length && source > best_source)) {
          best_source = source;
          best_length = length;
        }
      }
    }
    if (best_source >= 0) {
      const int64_t omitted =
          prefix_qbits[start + best_length] - prefix_qbits[start];
      const int64_t weight = omitted - kCommandBytes * 8 * kScale;
      if (weight > 0) {
        candidates.push_back(
            {start, best_source, best_length, start + best_length, weight});
      }
    }
    auto& queue = recent[key];
    queue.push_front(start);
    if (static_cast<int>(queue.size()) > kRecent) queue.pop_back();
  }

  std::sort(candidates.begin(), candidates.end(),
            [](const Candidate& left, const Candidate& right) {
              if (left.end != right.end) return left.end < right.end;
              if (left.start != right.start) return left.start < right.start;
              if (left.source != right.source) return left.source < right.source;
              return left.length < right.length;
            });
  std::vector<int> ends;
  ends.reserve(candidates.size());
  for (const auto& candidate : candidates) ends.push_back(candidate.end);
  std::vector<int64_t> dp(candidates.size() + 1, 0);
  std::vector<int> predecessor(candidates.size(), -1);
  std::vector<unsigned char> take(candidates.size() + 1, 0);
  for (size_t index = 0; index < candidates.size(); ++index) {
    const int pred = static_cast<int>(
        std::upper_bound(ends.begin(), ends.begin() + index,
                         candidates[index].start) -
        ends.begin()) - 1;
    predecessor[index] = pred;
    const int64_t include = candidates[index].weight + dp[pred + 1];
    const int64_t exclude = dp[index];
    if (include > exclude) {
      dp[index + 1] = include;
      take[index + 1] = 1;
    } else {
      dp[index + 1] = exclude;
    }
  }

  std::vector<Candidate> selected;
  int cursor = static_cast<int>(candidates.size());
  while (cursor > 0) {
    if (take[cursor]) {
      const int candidate_index = cursor - 1;
      selected.push_back(candidates[candidate_index]);
      cursor = predecessor[candidate_index] + 1;
    } else {
      --cursor;
    }
  }
  std::reverse(selected.begin(), selected.end());

  std::vector<unsigned char> copied(byte_count, 0);
  std::vector<int> command_at(byte_count, -1);
  for (size_t index = 0; index < selected.size(); ++index) {
    command_at[selected[index].start] = static_cast<int>(index);
    for (int offset = 0; offset < selected[index].length; ++offset) {
      copied[selected[index].start + offset] = 1;
    }
  }

  RangeEncoder literal_encoder;
  std::vector<unsigned char> literals;
  for (int byte = 0; byte < byte_count; ++byte) {
    if (!copied[byte]) {
      literals.push_back(bytes[byte]);
      for (int bit = 0; bit < 8; ++bit) {
        const int64_t row = static_cast<int64_t>(byte) * 8 + bit;
        literal_encoder.Update(probabilities[row], truth[row]);
      }
    }
  }
  literal_encoder.Finish();

  std::vector<unsigned char> reconstructed;
  reconstructed.reserve(byte_count);
  size_t literal_index = 0;
  for (int position = 0; position < byte_count;) {
    const int command_index = command_at[position];
    if (command_index >= 0) {
      const Candidate& command = selected[command_index];
      for (int offset = 0; offset < command.length; ++offset) {
        reconstructed.push_back(reconstructed[command.source + offset]);
      }
      position += command.length;
    } else {
      reconstructed.push_back(literals[literal_index++]);
      ++position;
    }
  }
  const bool roundtrip = reconstructed == bytes && literal_index == literals.size();

  const int64_t side_bytes =
      kHeaderBytes + static_cast<int64_t>(selected.size()) * kCommandBytes;
  const int64_t candidate_bytes =
      static_cast<int64_t>(literal_encoder.output.size()) + side_bytes;
  const int64_t net =
      static_cast<int64_t>(baseline.output.size()) - candidate_bytes;
  const double net_bpm = net * 1000000.0 / raw_bytes;
  const bool pass = parent_identity && roundtrip && net_bpm >= kTargetBpm;

  std::ofstream output(output_path);
  if (!output) throw std::runtime_error("cannot create output");
  output << "{\n";
  output << "  \"schema\": \"causal_copy_cover_gate_v1\",\n";
  output << "  \"candidate\": \"causal_copy_cover_recent4_v1\",\n";
  output << "  \"raw_scope_bytes\": " << raw_bytes << ",\n";
  output << "  \"trace_rows\": " << rows << ",\n";
  output << "  \"wrt_bytes\": " << byte_count << ",\n";
  output << "  \"parent_payload_bytes\": " << parent_payload.size() << ",\n";
  output << "  \"baseline_payload_bytes\": " << baseline.output.size() << ",\n";
  output << "  \"parent_payload_identity\": "
         << (parent_identity ? "true" : "false") << ",\n";
  output << "  \"candidate_count\": " << candidates.size() << ",\n";
  output << "  \"selected_copies\": " << selected.size() << ",\n";
  output << "  \"copied_wrt_bytes\": "
         << (byte_count - static_cast<int>(literals.size())) << ",\n";
  output << "  \"literal_payload_bytes\": " << literal_encoder.output.size()
         << ",\n";
  output << "  \"side_bytes\": " << side_bytes << ",\n";
  output << "  \"candidate_total_bytes\": " << candidate_bytes << ",\n";
  output << "  \"net_saved_bytes\": " << net << ",\n";
  output << "  \"net_saved_bpm\": " << net_bpm << ",\n";
  output << "  \"roundtrip_ok\": " << (roundtrip ? "true" : "false") << ",\n";
  output << "  \"required_net_saved_bpm\": " << kTargetBpm << ",\n";
  output << "  \"pass\": " << (pass ? "true" : "false") << ",\n";
  output << "  \"decision\": \""
         << (pass ? "promote_causal_copy_cover_to_native_gate"
                  : "retire_causal_copy_cover_recent4")
         << "\",\n";
  output << "  \"score_credit_bytes\": 0,\n";
  output << "  \"claim_boundary\": \"Exact parent payload identity and byte "
            "transform roundtrip shadow; source and native decoder integration "
            "remain uncounted.\"\n";
  output << "}\n";
  std::cout << "net_bpm=" << net_bpm << " copies=" << selected.size()
            << " identity=" << parent_identity << " roundtrip=" << roundtrip
            << " decision=" << (pass ? "promote" : "retire") << "\n";
  return 0;
}
