#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
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
constexpr int kContext = 4;
constexpr int kEntryBytes = 11;
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

struct Occurrence {
  uint32_t context;
  int position;
  unsigned char value;
};

struct Entry {
  uint32_t context;
  unsigned char prototype;
  int occurrences;
  int exceptions;
  double mask_bits;
  std::vector<unsigned char> exception_mask;
  size_t cursor = 0;
};

std::vector<unsigned char> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open file");
  return std::vector<unsigned char>(
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
}

uint32_t ContextKey(const std::vector<unsigned char>& bytes, int position) {
  uint32_t key = 0;
  for (int offset = kContext; offset > 0; --offset) {
    key = (key << 8) | bytes[position - offset];
  }
  return key;
}

double LogChoose(int n, int k) {
  if (k < 0 || k > n) return std::numeric_limits<double>::infinity();
  if (k == 0 || k == n) return 0.0;
  return (std::lgamma(n + 1.0) - std::lgamma(k + 1.0) -
          std::lgamma(n - k + 1.0)) / std::log(2.0);
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "usage: enumerative_exception_dictionary_gate TRACE ARCHIVE RAW OUTPUT\n";
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
  std::vector<int64_t> byte_qbits(byte_count, 0);
  RangeEncoder baseline;
  for (int byte = 0; byte < byte_count; ++byte) {
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
      byte_qbits[byte] += static_cast<int64_t>(
          std::llround(-std::log2(probability) * kScale));
      baseline.Update(p1, bit);
    }
    bytes[byte] = value;
  }
  baseline.Finish();

  const auto archive = ReadFile(archive_path);
  uint64_t wrt_bytes = archive.at(0) & 0x7fU;
  for (int index = 1; index < 5; ++index) wrt_bytes = (wrt_bytes << 8) | archive.at(index);
  const size_t header_bytes = wrt_bytes < 10000 ? 5 : 37;
  const std::vector<unsigned char> parent_payload(
      archive.begin() + static_cast<std::ptrdiff_t>(header_bytes), archive.end());
  const bool parent_identity = parent_payload == baseline.output;

  std::vector<Occurrence> occurrences;
  occurrences.reserve(byte_count - kContext);
  for (int position = kContext; position < byte_count; ++position) {
    occurrences.push_back({ContextKey(bytes, position), position, bytes[position]});
  }
  std::sort(occurrences.begin(), occurrences.end(),
            [](const Occurrence& left, const Occurrence& right) {
              if (left.context != right.context) return left.context < right.context;
              return left.position < right.position;
            });

  std::vector<Entry> entries;
  for (size_t begin = 0; begin < occurrences.size();) {
    size_t end = begin + 1;
    while (end < occurrences.size() &&
           occurrences[end].context == occurrences[begin].context) ++end;
    std::array<int, 256> counts{};
    for (size_t index = begin; index < end; ++index) {
      ++counts[occurrences[index].value];
    }
    int prototype = 0;
    for (int value = 1; value < 256; ++value) {
      if (counts[value] > counts[prototype]) prototype = value;
    }
    const int n = static_cast<int>(end - begin);
    const int e = n - counts[prototype];
    const double mask_bits = LogChoose(n, e);
    int64_t omitted_qbits = 0;
    std::vector<unsigned char> mask;
    mask.reserve(n);
    for (size_t index = begin; index < end; ++index) {
      const bool exception = occurrences[index].value != prototype;
      mask.push_back(static_cast<unsigned char>(exception));
      if (!exception) omitted_qbits += byte_qbits[occurrences[index].position];
    }
    const double side_qbits =
        (kEntryBytes * 8.0 + mask_bits) * kScale;
    if (omitted_qbits > side_qbits) {
      entries.push_back({occurrences[begin].context,
                         static_cast<unsigned char>(prototype),
                         n, e, mask_bits, std::move(mask), 0});
    }
    begin = end;
  }

  std::unordered_map<uint32_t, int> entry_index;
  for (size_t index = 0; index < entries.size(); ++index) {
    entry_index[entries[index].context] = static_cast<int>(index);
  }
  std::vector<unsigned char> omitted(byte_count, 0);
  for (int position = kContext; position < byte_count; ++position) {
    auto found = entry_index.find(ContextKey(bytes, position));
    if (found == entry_index.end()) continue;
    Entry& entry = entries[found->second];
    const bool exception = entry.exception_mask[entry.cursor++];
    if (!exception) omitted[position] = 1;
  }

  RangeEncoder literal_encoder;
  std::vector<unsigned char> literals;
  for (int byte = 0; byte < byte_count; ++byte) {
    if (!omitted[byte]) {
      literals.push_back(bytes[byte]);
      for (int bit = 0; bit < 8; ++bit) {
        const int64_t row = static_cast<int64_t>(byte) * 8 + bit;
        literal_encoder.Update(probabilities[row], truth[row]);
      }
    }
  }
  literal_encoder.Finish();

  for (auto& entry : entries) entry.cursor = 0;
  std::vector<unsigned char> reconstructed;
  reconstructed.reserve(byte_count);
  size_t literal_cursor = 0;
  for (int position = 0; position < byte_count; ++position) {
    if (position < kContext) {
      reconstructed.push_back(literals[literal_cursor++]);
      continue;
    }
    const uint32_t context = ContextKey(reconstructed, position);
    auto found = entry_index.find(context);
    if (found == entry_index.end()) {
      reconstructed.push_back(literals[literal_cursor++]);
      continue;
    }
    Entry& entry = entries[found->second];
    const bool exception = entry.exception_mask[entry.cursor++];
    reconstructed.push_back(
        exception ? literals[literal_cursor++] : entry.prototype);
  }
  const bool roundtrip =
      reconstructed == bytes && literal_cursor == literals.size();

  double pooled_mask_bits = 0.0;
  for (const auto& entry : entries) pooled_mask_bits += entry.mask_bits;
  const int64_t side_bytes =
      kHeaderBytes + static_cast<int64_t>(entries.size()) * kEntryBytes +
      static_cast<int64_t>(std::ceil(pooled_mask_bits / 8.0));
  const int64_t candidate_total =
      static_cast<int64_t>(literal_encoder.output.size()) + side_bytes;
  const int64_t net =
      static_cast<int64_t>(baseline.output.size()) - candidate_total;
  const double net_bpm = net * 1000000.0 / raw_bytes;
  const bool pass = parent_identity && roundtrip && net_bpm >= kTargetBpm;

  std::ofstream output(output_path);
  if (!output) throw std::runtime_error("cannot create output");
  output << "{\n";
  output << "  \"schema\": \"enumerative_exception_dictionary_gate_v1\",\n";
  output << "  \"candidate\": \"enumerative_exception_dictionary_c4_v1\",\n";
  output << "  \"raw_scope_bytes\": " << raw_bytes << ",\n";
  output << "  \"wrt_bytes\": " << byte_count << ",\n";
  output << "  \"parent_payload_bytes\": " << parent_payload.size() << ",\n";
  output << "  \"parent_payload_identity\": "
         << (parent_identity ? "true" : "false") << ",\n";
  output << "  \"selected_entries\": " << entries.size() << ",\n";
  output << "  \"omitted_wrt_bytes\": "
         << std::count(omitted.begin(), omitted.end(), 1) << ",\n";
  output << "  \"pooled_mask_bits\": " << pooled_mask_bits << ",\n";
  output << "  \"literal_payload_bytes\": " << literal_encoder.output.size() << ",\n";
  output << "  \"side_bytes\": " << side_bytes << ",\n";
  output << "  \"candidate_total_bytes\": " << candidate_total << ",\n";
  output << "  \"net_saved_bytes\": " << net << ",\n";
  output << "  \"net_saved_bpm\": " << net_bpm << ",\n";
  output << "  \"roundtrip_ok\": " << (roundtrip ? "true" : "false") << ",\n";
  output << "  \"required_net_saved_bpm\": " << kTargetBpm << ",\n";
  output << "  \"pass\": " << (pass ? "true" : "false") << ",\n";
  output << "  \"decision\": \""
         << (pass ? "promote_exception_dictionary_to_native_gate"
                  : "retire_exception_dictionary_c4")
         << "\",\n";
  output << "  \"score_credit_bytes\": 0,\n";
  output << "  \"claim_boundary\": \"Exact parent identity and reconstructed "
            "WRT shadow; enumerative masks are exactly bit-counted but native "
            "rank coding and source package remain unimplemented.\"\n";
  output << "}\n";
  std::cout << "net_bpm=" << net_bpm << " entries=" << entries.size()
            << " decision=" << (pass ? "promote" : "retire") << "\n";
  return 0;
}
