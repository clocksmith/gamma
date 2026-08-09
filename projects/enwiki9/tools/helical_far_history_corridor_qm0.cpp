#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unordered_map>
#include <unistd.h>
#include <vector>

namespace {

constexpr uint64_t kExpectedSize = 1000000000ULL;
constexpr uint32_t kWindow = 32;
constexpr uint64_t kAnchorMask = 63;
constexpr uint64_t kMinimumDistance = 100000000ULL;
constexpr size_t kRecentSources = 8;
constexpr size_t kCandidateCap = 16;
constexpr uint64_t kInfinite = std::numeric_limits<uint64_t>::max() / 4;

uint64_t RotL(uint64_t value, unsigned shift) {
  shift &= 63;
  return shift ? (value << shift) | (value >> (64 - shift)) : value;
}

uint64_t SplitMix(uint64_t& state) {
  uint64_t z = (state += 0x9e3779b97f4a7c15ULL);
  z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
  z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
  return z ^ (z >> 31);
}

struct Key {
  uint64_t first;
  uint64_t second;
  bool operator==(const Key& other) const {
    return first == other.first && second == other.second;
  }
};

struct KeyHash {
  size_t operator()(const Key& key) const {
    uint64_t value = key.first ^ RotL(key.second, 29);
    value ^= value >> 33;
    value *= 0xff51afd7ed558ccdULL;
    value ^= value >> 33;
    return static_cast<size_t>(value);
  }
};

struct Anchor {
  uint64_t first;
  uint64_t second;
  uint32_t position;
};

struct Recent {
  std::array<uint32_t, kRecentSources> positions{};
  uint8_t count = 0;
  uint8_t next = 0;

  void Add(uint32_t position) {
    positions[next] = position;
    next = static_cast<uint8_t>((next + 1) % kRecentSources);
    if (count < kRecentSources) ++count;
  }
};

struct Row {
  uint32_t target;
  uint32_t original_source;
  uint32_t length;
  uint32_t gap;
  uint8_t count = 0;
  std::array<uint32_t, kCandidateCap> sources{};
};

uint64_t ReadLe64(const uint8_t* data) {
  uint64_t value = 0;
  for (unsigned i = 0; i < 8; ++i) value |= uint64_t(data[i]) << (8 * i);
  return value;
}

std::vector<uint64_t> ReadUlebs(const uint8_t* data, size_t size,
                                uint64_t expected) {
  std::vector<uint64_t> values;
  values.reserve(expected);
  uint64_t value = 0;
  unsigned shift = 0;
  for (size_t i = 0; i < size; ++i) {
    value |= uint64_t(data[i] & 127) << shift;
    if (data[i] < 128) {
      values.push_back(value);
      value = 0;
      shift = 0;
    } else {
      shift += 7;
      if (shift >= 64) throw std::runtime_error("ULEB overflow");
    }
  }
  if (shift != 0 || values.size() != expected) {
    throw std::runtime_error("invalid ULEB column");
  }
  return values;
}

size_t UlebBytes(uint64_t value) {
  size_t bytes = 1;
  while (value >= 128) {
    value >>= 7;
    ++bytes;
  }
  return bytes;
}

uint64_t ZigZag(int64_t value) {
  return (uint64_t(value) << 1) ^ uint64_t(value >> 63);
}

void PutUleb(std::vector<uint8_t>& output, uint64_t value) {
  do {
    uint8_t byte = static_cast<uint8_t>(value & 127);
    value >>= 7;
    if (value) byte |= 128;
    output.push_back(byte);
  } while (value);
}

void PutLe64(std::vector<uint8_t>& output, uint64_t value) {
  for (unsigned i = 0; i < 8; ++i) {
    output.push_back(static_cast<uint8_t>((value >> (8 * i)) & 255));
  }
}

void WriteFile(const std::string& path, const std::vector<uint8_t>& payload) {
  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  output.write(reinterpret_cast<const char*>(payload.data()), payload.size());
  if (!output) throw std::runtime_error("output write failed");
}

unsigned Bin(uint64_t value) {
  unsigned result = 0;
  while (value > 1) {
    value >>= 1;
    ++result;
  }
  return result;
}

std::vector<Row> ParseRows(const std::string& path, uint64_t& distance_bytes,
                           uint64_t& length_bytes) {
  std::ifstream input(path, std::ios::binary | std::ios::ate);
  if (!input) throw std::runtime_error("cannot open ledger");
  const size_t size = static_cast<size_t>(input.tellg());
  input.seekg(0);
  std::vector<uint8_t> payload(size);
  input.read(reinterpret_cast<char*>(payload.data()), payload.size());
  if (!input || size < 40 || std::memcmp(payload.data(), "FHCLQ1\0\0", 8)) {
    throw std::runtime_error("bad ledger");
  }
  const uint64_t records = ReadLe64(payload.data() + 8);
  const uint64_t gap_size = ReadLe64(payload.data() + 16);
  const uint64_t distance_size = ReadLe64(payload.data() + 24);
  const uint64_t length_size = ReadLe64(payload.data() + 32);
  if (40 + gap_size + distance_size + length_size != size) {
    throw std::runtime_error("ledger columns do not cover file");
  }
  const auto gaps = ReadUlebs(payload.data() + 40, gap_size, records);
  const auto distances = ReadUlebs(payload.data() + 40 + gap_size,
                                   distance_size, records);
  const auto lengths = ReadUlebs(payload.data() + 40 + gap_size + distance_size,
                                 length_size, records);
  distance_bytes = distance_size;
  length_bytes = length_size;
  std::vector<Row> rows;
  rows.reserve(records);
  uint64_t target = 0;
  for (size_t i = 0; i < records; ++i) {
    target += gaps[i];
    if (target > UINT32_MAX || lengths[i] > UINT32_MAX ||
        distances[i] > target || target - distances[i] > UINT32_MAX) {
      throw std::runtime_error("ledger coordinate overflow");
    }
    Row row{};
    row.target = static_cast<uint32_t>(target);
    row.original_source = static_cast<uint32_t>(target - distances[i]);
    row.length = static_cast<uint32_t>(lengths[i]);
    row.gap = static_cast<uint32_t>(gaps[i]);
    rows.push_back(row);
    target += lengths[i];
  }
  return rows;
}

std::vector<Anchor> BuildAnchors(const uint8_t* data, uint64_t size) {
  std::array<uint64_t, 256> table1{};
  std::array<uint64_t, 256> table2{};
  uint64_t seed1 = 0x46a7c15d3b92e801ULL;
  uint64_t seed2 = 0xd1b54a32d192ed03ULL;
  for (size_t i = 0; i < 256; ++i) {
    table1[i] = SplitMix(seed1);
    table2[i] = SplitMix(seed2);
  }
  uint64_t hash1 = 0;
  uint64_t hash2 = 0;
  for (uint32_t i = 0; i < kWindow; ++i) {
    hash1 = RotL(hash1, 1) ^ table1[data[i]];
    hash2 = RotL(hash2, 1) ^ table2[data[i]];
  }
  std::vector<Anchor> anchors;
  anchors.reserve(static_cast<size_t>(size / 58));
  for (uint64_t position = 0; position + kWindow <= size; ++position) {
    if ((hash1 & kAnchorMask) == 0) {
      anchors.push_back(Anchor{hash1, hash2, static_cast<uint32_t>(position)});
    }
    if (position + kWindow < size) {
      hash1 = RotL(hash1, 1) ^ RotL(table1[data[position]], kWindow) ^
              table1[data[position + kWindow]];
      hash2 = RotL(hash2, 1) ^ RotL(table2[data[position]], kWindow) ^
              table2[data[position + kWindow]];
    }
  }
  return anchors;
}

bool AddCandidate(Row& row, uint64_t source, const uint8_t* data) {
  if (source > UINT32_MAX || source >= row.target ||
      uint64_t(row.target) - source < kMinimumDistance ||
      row.length > uint64_t(row.target) - source) {
    return false;
  }
  const uint32_t source32 = static_cast<uint32_t>(source);
  for (size_t i = 0; i < row.count; ++i) {
    if (row.sources[i] == source32) return true;
  }
  if (std::memcmp(data + source32, data + row.target, row.length) != 0) {
    return false;
  }
  if (row.count == kCandidateCap) return false;
  row.sources[row.count++] = source32;
  return true;
}

struct PathResult {
  uint64_t address_bytes = 0;
  uint64_t corridors = 0;
  uint64_t continuations = 0;
  uint64_t shifts = 0;
  std::vector<uint32_t> sources;
  std::vector<uint8_t> modes;
};

PathResult Optimize(const std::vector<Row>& rows, bool allow_shift) {
  std::array<uint64_t, kCandidateCap> previous{};
  std::array<uint64_t, kCandidateCap> current{};
  std::vector<std::array<uint8_t, kCandidateCap>> parents(rows.size());
  std::vector<std::array<uint8_t, kCandidateCap>> modes(rows.size());
  for (size_t j = 0; j < rows[0].count; ++j) {
    previous[j] = UlebBytes(uint64_t(rows[0].target) - rows[0].sources[j]);
    parents[0][j] = 0;
    modes[0][j] = 0;
  }
  for (size_t i = 1; i < rows.size(); ++i) {
    for (size_t j = 0; j < rows[i].count; ++j) {
      const uint64_t diagonal = uint64_t(rows[i].target) - rows[i].sources[j];
      uint64_t best = kInfinite;
      uint8_t best_parent = 0;
      uint8_t best_mode = 0;
      for (size_t k = 0; k < rows[i - 1].count; ++k) {
        const uint64_t prior_diagonal =
            uint64_t(rows[i - 1].target) - rows[i - 1].sources[k];
        uint64_t increment = UlebBytes(diagonal);
        uint8_t mode = 0;
        if (diagonal == prior_diagonal) {
          increment = 0;
          mode = 1;
        } else if (allow_shift) {
          const int64_t delta = static_cast<int64_t>(diagonal) -
                                static_cast<int64_t>(prior_diagonal);
          const uint64_t shift_cost = 1 + UlebBytes(ZigZag(delta));
          if (shift_cost < increment) {
            increment = shift_cost;
            mode = 2;
          }
        }
        const uint64_t candidate = previous[k] + increment;
        if (candidate < best ||
            (candidate == best && (mode < best_mode ||
             (mode == best_mode && rows[i - 1].sources[k] <
                                   rows[i - 1].sources[best_parent])))) {
          best = candidate;
          best_parent = static_cast<uint8_t>(k);
          best_mode = mode;
        }
      }
      current[j] = best;
      parents[i][j] = best_parent;
      modes[i][j] = best_mode;
    }
    previous = current;
  }
  uint8_t selected = 0;
  for (size_t j = 1; j < rows.back().count; ++j) {
    if (previous[j] < previous[selected] ||
        (previous[j] == previous[selected] &&
         rows.back().sources[j] < rows.back().sources[selected])) {
      selected = static_cast<uint8_t>(j);
    }
  }
  PathResult result;
  result.address_bytes = previous[selected];
  result.sources.resize(rows.size());
  result.modes.resize(rows.size());
  for (size_t reverse = rows.size(); reverse-- > 0;) {
    result.sources[reverse] = rows[reverse].sources[selected];
    result.modes[reverse] = modes[reverse][selected];
    if (reverse) selected = parents[reverse][selected];
  }
  result.modes[0] = 0;
  for (uint8_t mode : result.modes) {
    if (mode == 0) ++result.corridors;
    else if (mode == 1) ++result.continuations;
    else ++result.shifts;
  }
  return result;
}

std::vector<uint8_t> Serialize(const std::vector<Row>& rows,
                               const PathResult& path, const char magic[8]) {
  std::vector<uint8_t> output;
  output.reserve(rows.size() * 7);
  output.insert(output.end(), magic, magic + 8);
  PutLe64(output, rows.size());
  uint64_t previous_target_end = 0;
  uint64_t previous_diagonal = 0;
  for (size_t i = 0; i < rows.size(); ++i) {
    const uint64_t gap = uint64_t(rows[i].target) - previous_target_end;
    const uint64_t diagonal = uint64_t(rows[i].target) - path.sources[i];
    PutUleb(output, gap);
    output.push_back(path.modes[i]);
    if (path.modes[i] == 0) {
      PutUleb(output, diagonal);
    } else if (path.modes[i] == 2) {
      PutUleb(output, ZigZag(static_cast<int64_t>(diagonal) -
                            static_cast<int64_t>(previous_diagonal)));
    }
    PutUleb(output, rows[i].length);
    previous_target_end = uint64_t(rows[i].target) + rows[i].length;
    previous_diagonal = diagonal;
  }
  return output;
}

uint64_t ShuffledC0AddressBytes(const std::vector<Row>& rows) {
  struct BucketRow {
    size_t row;
    std::vector<uint64_t> diagonals;
  };
  std::array<std::vector<BucketRow>, 64 * 64> buckets;
  for (size_t i = 0; i < rows.size(); ++i) {
    const uint64_t original_distance =
        uint64_t(rows[i].target) - rows[i].original_source;
    const unsigned bucket = Bin(rows[i].length) * 64 + Bin(original_distance);
    BucketRow item;
    item.row = i;
    for (size_t j = 0; j < rows[i].count; ++j) {
      item.diagonals.push_back(uint64_t(rows[i].target) - rows[i].sources[j]);
    }
    buckets[bucket].push_back(std::move(item));
  }
  std::vector<std::vector<uint64_t>> shuffled(rows.size());
  uint64_t random = 0x48454c4943414c31ULL;
  for (auto& bucket : buckets) {
    for (size_t i = bucket.size(); i > 1; --i) {
      const size_t j = SplitMix(random) % i;
      std::swap(bucket[i - 1].diagonals, bucket[j].diagonals);
    }
    for (auto& item : bucket) shuffled[item.row] = std::move(item.diagonals);
  }
  std::vector<uint64_t> previous;
  for (uint64_t diagonal : shuffled[0]) previous.push_back(UlebBytes(diagonal));
  for (size_t i = 1; i < shuffled.size(); ++i) {
    std::vector<uint64_t> current(shuffled[i].size(), kInfinite);
    for (size_t j = 0; j < shuffled[i].size(); ++j) {
      for (size_t k = 0; k < shuffled[i - 1].size(); ++k) {
        const uint64_t increment =
            shuffled[i][j] == shuffled[i - 1][k] ? 0 : UlebBytes(shuffled[i][j]);
        current[j] = std::min(current[j], previous[k] + increment);
      }
    }
    previous.swap(current);
  }
  return *std::min_element(previous.begin(), previous.end());
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "usage: helical_far_history_corridor_qm0 INPUT LEDGER C0 C1\n";
    return 2;
  }
  try {
    uint64_t distance_stream_bytes = 0;
    uint64_t length_stream_bytes = 0;
    auto rows = ParseRows(argv[2], distance_stream_bytes, length_stream_bytes);
    const int fd = open(argv[1], O_RDONLY);
    if (fd < 0) throw std::runtime_error("cannot open input");
    struct stat status {};
    if (fstat(fd, &status) || uint64_t(status.st_size) != kExpectedSize) {
      throw std::runtime_error("input must be canonical 1G size");
    }
    const auto* data = static_cast<const uint8_t*>(
        mmap(nullptr, kExpectedSize, PROT_READ, MAP_PRIVATE, fd, 0));
    if (data == MAP_FAILED) throw std::runtime_error("mmap failed");
    madvise(const_cast<uint8_t*>(data), kExpectedSize, MADV_SEQUENTIAL);

    auto anchors = BuildAnchors(data, kExpectedSize);
    std::unordered_map<Key, Recent, KeyHash> eligible;
    eligible.max_load_factor(0.85f);
    eligible.reserve(static_cast<size_t>(anchors.size() * 0.82));
    size_t eligible_index = 0;
    size_t target_anchor_index = 0;
    uint64_t alternatives = 0;
    uint64_t exact_candidates = 0;
    uint64_t rows_with_alternatives = 0;
    uint64_t missing_target_anchor = 0;
    std::vector<uint32_t> prior_sources;

    for (auto& row : rows) {
      while (target_anchor_index < anchors.size() &&
             anchors[target_anchor_index].position < row.target) {
        ++target_anchor_index;
      }
      if (target_anchor_index == anchors.size() ||
          uint64_t(anchors[target_anchor_index].position) + kWindow >
              uint64_t(row.target) + row.length) {
        ++missing_target_anchor;
        throw std::runtime_error("selected match lacks internal frozen anchor");
      }
      const Anchor& target_anchor = anchors[target_anchor_index];
      while (eligible_index < anchors.size() &&
             uint64_t(anchors[eligible_index].position) + kMinimumDistance <=
                 target_anchor.position) {
        const Anchor& anchor = anchors[eligible_index++];
        eligible[Key{anchor.first, anchor.second}].Add(anchor.position);
      }
      const uint64_t offset = uint64_t(target_anchor.position) - row.target;
      AddCandidate(row, row.original_source, data);
      for (uint32_t prior_source : prior_sources) {
        const uint64_t projected = uint64_t(prior_source) +
            (uint64_t(row.target) - rows[&row - rows.data() - 1].target);
        AddCandidate(row, projected, data);
      }
      const auto found = eligible.find(Key{target_anchor.first, target_anchor.second});
      if (found != eligible.end()) {
        const Recent& recent = found->second;
        for (size_t i = 0; i < recent.count; ++i) {
          if (recent.positions[i] >= offset) {
            AddCandidate(row, uint64_t(recent.positions[i]) - offset, data);
          }
        }
      }
      if (row.count == 0 || row.sources[0] != row.original_source) {
        throw std::runtime_error("original source failed exact validation");
      }
      exact_candidates += row.count;
      if (row.count > 1) {
        ++rows_with_alternatives;
        alternatives += row.count - 1;
      }
      prior_sources.assign(row.sources.begin(), row.sources.begin() + row.count);
    }

    const PathResult c0 = Optimize(rows, false);
    const PathResult c1 = Optimize(rows, true);
    const uint64_t cs_address_bytes = ShuffledC0AddressBytes(rows);
    const auto c0_payload = Serialize(rows, c0, "HFCC0\0\0\0");
    const auto c1_payload = Serialize(rows, c1, "HFCC1\0\0\0");
    WriteFile(argv[3], c0_payload);
    WriteFile(argv[4], c1_payload);

    uint64_t m0 = 0;
    uint64_t copied = 0;
    for (const Row& row : rows) {
      const uint64_t distance = uint64_t(row.target) - row.original_source;
      m0 += 1 + UlebBytes(distance) + UlebBytes(row.length);
      copied += row.length;
    }
    const uint64_t c0_inline = m0 - distance_stream_bytes + c0.address_bytes;
    const uint64_t c1_inline = m0 - distance_stream_bytes + c1.address_bytes;
    std::cout << "{\n"
              << "\"schema\":\"helical_far_history_corridor_scan_v1\",\n"
              << "\"input_bytes\":" << kExpectedSize << ",\n"
              << "\"records\":" << rows.size() << ",\n"
              << "\"copied_bytes\":" << copied << ",\n"
              << "\"anchors\":" << anchors.size() << ",\n"
              << "\"candidate_cap\":" << kCandidateCap << ",\n"
              << "\"recent_source_cap\":" << kRecentSources << ",\n"
              << "\"exact_candidates\":" << exact_candidates << ",\n"
              << "\"alternative_candidates\":" << alternatives << ",\n"
              << "\"rows_with_alternatives\":" << rows_with_alternatives << ",\n"
              << "\"missing_target_anchors\":" << missing_target_anchor << ",\n"
              << "\"m0_inline_bytes\":" << m0 << ",\n"
              << "\"distance_stream_bytes\":" << distance_stream_bytes << ",\n"
              << "\"length_stream_bytes\":" << length_stream_bytes << ",\n"
              << "\"c0_address_bytes\":" << c0.address_bytes << ",\n"
              << "\"c0_inline_bytes\":" << c0_inline << ",\n"
              << "\"c0_corridors\":" << c0.corridors << ",\n"
              << "\"c0_continuations\":" << c0.continuations << ",\n"
              << "\"c1_address_bytes\":" << c1.address_bytes << ",\n"
              << "\"c1_inline_bytes\":" << c1_inline << ",\n"
              << "\"c1_corridors\":" << c1.corridors << ",\n"
              << "\"c1_continuations\":" << c1.continuations << ",\n"
              << "\"c1_shifts\":" << c1.shifts << ",\n"
              << "\"cs_address_bytes\":" << cs_address_bytes << ",\n"
              << "\"c0_serialized_bytes\":" << c0_payload.size() << ",\n"
              << "\"c1_serialized_bytes\":" << c1_payload.size() << ",\n"
              << "\"all_candidates_exact\":true,\n"
              << "\"all_sources_strictly_prior\":true,\n"
              << "\"all_sources_fully_closed\":true\n"
              << "}\n";
    munmap(const_cast<uint8_t*>(data), kExpectedSize);
    close(fd);
  } catch (const std::exception& error) {
    std::cerr << error.what() << "\n";
    return 2;
  }
  return 0;
}
