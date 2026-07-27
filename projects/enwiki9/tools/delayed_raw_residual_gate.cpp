#include <algorithm>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <list>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

constexpr size_t kCapacity = 65536;
constexpr uint32_t kAlpha = 16;
constexpr uint32_t kMinimumSupport = 8;
constexpr uint32_t kBlendDenominator = 8;
constexpr uint32_t kAuxiliaryWeight = 1;

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

struct Entry {
  uint32_t zeros = 0;
  uint32_t ones = 0;
  std::list<uint64_t>::iterator position;
};

class Table {
 public:
  uint16_t Predict(uint64_t key, uint16_t parent) {
    auto it = rows_.find(key);
    if (it == rows_.end()) return parent;
    Touch(it);
    const uint32_t support = it->second.zeros + it->second.ones;
    if (support < kMinimumSupport) return parent;
    const uint32_t auxiliary =
        ((it->second.ones + kAlpha) * 65536u) /
        (support + 2 * kAlpha);
    uint32_t corrected =
        ((kBlendDenominator - kAuxiliaryWeight) * parent +
         kAuxiliaryWeight * auxiliary) /
        kBlendDenominator;
    corrected = std::max<uint32_t>(1, std::min<uint32_t>(65535, corrected));
    return static_cast<uint16_t>(corrected);
  }

  void Update(uint64_t key, int bit) {
    auto it = rows_.find(key);
    if (it == rows_.end()) {
      if (rows_.size() == kCapacity) {
        rows_.erase(lru_.back());
        lru_.pop_back();
        ++evictions_;
      }
      lru_.push_front(key);
      it = rows_.emplace(key, Entry{0, 0, lru_.begin()}).first;
    } else {
      Touch(it);
    }
    if (bit) ++it->second.ones;
    else ++it->second.zeros;
    if (it->second.zeros + it->second.ones >= 32768) {
      it->second.zeros = (it->second.zeros + 1) / 2;
      it->second.ones = (it->second.ones + 1) / 2;
    }
  }

  size_t Size() const { return rows_.size(); }
  uint64_t Evictions() const { return evictions_; }

 private:
  using Iterator = std::unordered_map<uint64_t, Entry>::iterator;
  void Touch(Iterator it) {
    lru_.erase(it->second.position);
    lru_.push_front(it->first);
    it->second.position = lru_.begin();
  }
  std::unordered_map<uint64_t, Entry> rows_;
  std::list<uint64_t> lru_;
  uint64_t evictions_ = 0;
};

std::vector<uint8_t> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open " + path);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

uint64_t MixKey(uint64_t raw_hash, int bit_position, int byte_prefix) {
  uint64_t value =
      raw_hash ^ (static_cast<uint64_t>(bit_position) << 56) ^
      (static_cast<uint64_t>(byte_prefix) << 48);
  value ^= value >> 30;
  value *= 0xbf58476d1ce4e5b9ULL;
  value ^= value >> 27;
  value *= 0x94d049bb133111ebULL;
  return value ^ (value >> 31);
}

uint64_t Load64(const uint8_t* data) {
  uint64_t value = 0;
  for (int i = 7; i >= 0; --i) value = (value << 8) | data[i];
  return value;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "usage: delayed_raw_residual_gate TRACE ARCHIVE HASHMAP DECISION\n";
    return 2;
  }
  try {
    const auto trace = ReadFile(argv[1]);
    const auto archive = ReadFile(argv[2]);
    const auto map = ReadFile(argv[3]);
    constexpr char trace_magic[] = "FX2PT01\n";
    if (trace.size() < 8 ||
        std::memcmp(trace.data(), trace_magic, 8) != 0 ||
        (trace.size() - 8) % 3 != 0) {
      throw std::runtime_error("invalid trace");
    }
    if (map.size() < 24 || std::memcmp(map.data(), "RAWHASH1", 8) != 0)
      throw std::runtime_error("invalid raw hash map");
    const int64_t rows = static_cast<int64_t>((trace.size() - 8) / 3);
    if (rows % 8) throw std::runtime_error("unaligned trace");
    const uint64_t wrt_bytes = Load64(map.data() + 8);
    const uint64_t raw_bytes = Load64(map.data() + 16);
    if (wrt_bytes != static_cast<uint64_t>(rows / 8) ||
        map.size() != 24 + wrt_bytes * 8) {
      throw std::runtime_error("trace and raw map disagree");
    }

    RangeEncoder baseline, candidate;
    Table table;
    int byte_prefix = 0;
    uint64_t corrected_rows = 0;
    for (int64_t row = 0; row < rows; ++row) {
      const size_t offset = 8 + static_cast<size_t>(row) * 3;
      const uint16_t p1 = static_cast<uint16_t>(
          trace[offset] | (static_cast<uint16_t>(trace[offset + 1]) << 8));
      const int bit = trace[offset + 2];
      if (p1 == 0 || bit > 1) throw std::runtime_error("invalid trace row");
      const int bit_position = static_cast<int>(row & 7);
      if (bit_position == 0) byte_prefix = 0;
      const uint64_t raw_hash =
          Load64(map.data() + 24 + static_cast<size_t>(row / 8) * 8);
      const uint64_t key = MixKey(raw_hash, bit_position, byte_prefix);
      const uint16_t corrected = table.Predict(key, p1);
      corrected_rows += corrected != p1;
      baseline.Update(p1, bit);
      candidate.Update(corrected, bit);
      table.Update(key, bit);
      byte_prefix = (byte_prefix << 1) | bit;
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
        << "  \"id\": \"delayed_raw_residual_apm_v1\",\n"
        << "  \"status\": \"" << (passes_gate ? "promote" : "terminal_negative")
        << "\",\n"
        << "  \"score_credit_bytes\": 0,\n"
        << "  \"raw_bytes\": " << raw_bytes << ",\n"
        << "  \"wrt_bytes\": " << wrt_bytes << ",\n"
        << "  \"trace_rows\": " << rows << ",\n"
        << "  \"table_capacity\": " << kCapacity << ",\n"
        << "  \"table_rows\": " << table.Size() << ",\n"
        << "  \"table_evictions\": " << table.Evictions() << ",\n"
        << "  \"corrected_rows\": " << corrected_rows << ",\n"
        << "  \"baseline_payload_bytes\": " << baseline.output.size() << ",\n"
        << "  \"candidate_payload_bytes\": " << candidate.output.size() << ",\n"
        << "  \"net_saved_bytes\": " << net << ",\n"
        << "  \"net_bytes_per_million_raw\": " << net << ",\n"
        << "  \"target_gate_bytes_per_million\": 2000,\n"
        << "  \"parent_archive_identity\": "
        << (parent_identity ? "true" : "false") << ",\n"
        << "  \"decision\": \""
        << (passes_gate ? "authorize_distant_delayed_raw_residual"
                        : "retire_delayed_raw_residual_apm")
        << "\"\n"
        << "}\n";
    out.close();

    std::cout << "corrected=" << corrected_rows
              << " rows=" << table.Size()
              << " evictions=" << table.Evictions()
              << " baseline=" << baseline.output.size()
              << " candidate=" << candidate.output.size()
              << " net=" << net
              << " parent_identity=" << parent_identity << "\n";
    return parent_identity ? 0 : 1;
  } catch (const std::exception& e) {
    std::cerr << e.what() << "\n";
    return 1;
  }
}
