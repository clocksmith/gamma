#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unordered_map>
#include <unistd.h>
#include <vector>

namespace {

constexpr uint64_t kExpectedStoreSize = 647798597ULL;
constexpr uint64_t kExpectedStreamSize = 647798592ULL;
constexpr uint32_t kStreamBegin = 6;
constexpr uint32_t kWindow = 32;
constexpr uint64_t kAnchorMask = 63;
constexpr uint64_t kMinimumDistance = 100000000ULL;
constexpr uint64_t kMinimumLength = 64;
constexpr uint64_t kArchiveForecast = 109128198ULL;

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

uint8_t Transform(uint8_t value) {
  if (value >= '{' && value < 127) value += 'P' - '{';
  else if (value >= 'P' && value < 'T') value -= 'P' - '{';
  else if ((value >= ':' && value <= '?') || (value >= 'J' && value <= 'O')) value ^= 0x70;
  if (value == 'X' || value == '`') value ^= 'X' ^ '`';
  return value;
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

void SetBoundary(std::vector<uint8_t>& bits, uint64_t position) {
  bits[position >> 3] |= static_cast<uint8_t>(1U << (position & 7));
}

bool Boundary(const std::vector<uint8_t>& bits, uint64_t position) {
  return bits[position >> 3] & static_cast<uint8_t>(1U << (position & 7));
}

void PutUleb(std::vector<uint8_t>& output, uint64_t value) {
  do {
    uint8_t byte = static_cast<uint8_t>(value & 127);
    value >>= 7;
    if (value) byte |= 128;
    output.push_back(byte);
  } while (value);
}

void PutLe64(std::ofstream& output, uint64_t value) {
  for (unsigned i = 0; i < 8; ++i) output.put(static_cast<char>((value >> (8 * i)) & 255));
}

void PrintArray(const std::array<uint64_t, 3>& values) {
  std::cout << '[' << values[0] << ',' << values[1] << ',' << values[2] << ']';
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 3) {
    std::cerr << "usage: helical_wrt_far_history_discovery_qm3 STORE LEDGER\n";
    return 2;
  }
  try {
    const int fd = open(argv[1], O_RDONLY);
    if (fd < 0) throw std::runtime_error("cannot open WRT store");
    struct stat status {};
    if (fstat(fd, &status) || uint64_t(status.st_size) != kExpectedStoreSize) {
      throw std::runtime_error("unexpected WRT store size");
    }
    const auto* stored = static_cast<const uint8_t*>(
        mmap(nullptr, kExpectedStoreSize, PROT_READ, MAP_PRIVATE, fd, 0));
    if (stored == MAP_FAILED) throw std::runtime_error("mmap failed");
    if (stored[1] || stored[2] || stored[3] || stored[4] || stored[5] != 7) {
      throw std::runtime_error("invalid WRT store header");
    }
    const uint8_t* data = stored + 5;
    std::vector<uint8_t> boundaries((kExpectedStreamSize + 8) / 8, 0);
    SetBoundary(boundaries, kStreamBegin);
    uint64_t events = 0;
    uint64_t controls = 0;
    uint64_t cursor = kStreamBegin;
    while (cursor < kExpectedStreamSize) {
      const uint8_t first = Transform(data[cursor++]);
      if (first == 0x0c) {
        if (cursor >= kExpectedStreamSize) throw std::runtime_error("truncated escape");
        ++cursor;
      } else if (first == 0x07 || first == 0x06 || first == 0x40) {
        ++controls;
      } else if (first >= 0x80 && first > 0xcf) {
        if (cursor >= kExpectedStreamSize) throw std::runtime_error("truncated token");
        const uint8_t second = Transform(data[cursor++]);
        if (second > 0xcf) {
          if (cursor >= kExpectedStreamSize) throw std::runtime_error("truncated token");
          ++cursor;
        }
      }
      SetBoundary(boundaries, cursor);
      ++events;
    }

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
      hash1 = RotL(hash1, 1) ^ table1[data[kStreamBegin + i]];
      hash2 = RotL(hash2, 1) ^ table2[data[kStreamBegin + i]];
    }
    std::unordered_map<Key, uint32_t, KeyHash> earliest;
    earliest.max_load_factor(0.85f);
    earliest.reserve(static_cast<size_t>(kExpectedStreamSize / 58));
    std::vector<uint8_t> gaps;
    std::vector<uint8_t> distances;
    std::vector<uint8_t> lengths;
    uint64_t anchors = 0;
    uint64_t repeated = 0;
    uint64_t exact = 0;
    uint64_t far = 0;
    uint64_t collisions = 0;
    uint64_t selected = 0;
    uint64_t copied = 0;
    uint64_t last_target_end = kStreamBegin;
    std::array<uint64_t, 3> split_matches{};
    std::array<uint64_t, 3> split_copied{};
    for (uint64_t position = kStreamBegin;
         position + kWindow <= kExpectedStreamSize; ++position) {
      if ((hash1 & kAnchorMask) == 0) {
        ++anchors;
        const Key key{hash1, hash2};
        const auto found = earliest.find(key);
        if (found == earliest.end()) {
          earliest.emplace(key, static_cast<uint32_t>(position));
        } else {
          ++repeated;
          const uint64_t source_anchor = found->second;
          if (std::memcmp(data + source_anchor, data + position, kWindow) != 0) {
            ++collisions;
          } else {
            ++exact;
            if (position >= source_anchor + kMinimumDistance) {
              ++far;
              if (position >= last_target_end) {
                uint64_t target = position;
                uint64_t source = source_anchor;
                while (target > last_target_end && source > kStreamBegin &&
                       data[target - 1] == data[source - 1]) {
                  --target;
                  --source;
                }
                while (target <= position &&
                       (!Boundary(boundaries, target) || !Boundary(boundaries, source))) {
                  ++target;
                  ++source;
                }
                if (target <= position) {
                  const uint64_t distance = target - source;
                  uint64_t length = position + kWindow - target;
                  const uint64_t closed = std::min(distance, kExpectedStreamSize - target);
                  while (length < closed && data[target + length] == data[source + length]) ++length;
                  while (length && (!Boundary(boundaries, target + length) ||
                                    !Boundary(boundaries, source + length))) --length;
                  if (length >= kMinimumLength) {
                    PutUleb(gaps, target - last_target_end);
                    PutUleb(distances, distance);
                    PutUleb(lengths, length);
                    const unsigned split = std::min<uint64_t>(2, target * 3 / kExpectedStreamSize);
                    ++selected;
                    copied += length;
                    ++split_matches[split];
                    split_copied[split] += length;
                    last_target_end = target + length;
                  }
                }
              }
            }
          }
        }
      }
      if (position + kWindow < kExpectedStreamSize) {
        hash1 = RotL(hash1, 1) ^ RotL(table1[data[position]], kWindow) ^
                table1[data[position + kWindow]];
        hash2 = RotL(hash2, 1) ^ RotL(table2[data[position]], kWindow) ^
                table2[data[position + kWindow]];
      }
    }
    std::ofstream ledger(argv[2], std::ios::binary | std::ios::trunc);
    if (!ledger) throw std::runtime_error("cannot create ledger");
    ledger.write("HWFHQ3\0\0", 8);
    PutLe64(ledger, selected);
    PutLe64(ledger, gaps.size());
    PutLe64(ledger, distances.size());
    PutLe64(ledger, lengths.size());
    ledger.write(reinterpret_cast<const char*>(gaps.data()), gaps.size());
    ledger.write(reinterpret_cast<const char*>(distances.data()), distances.size());
    ledger.write(reinterpret_cast<const char*>(lengths.data()), lengths.size());
    if (!ledger) throw std::runtime_error("ledger write failed");
    const long double gross = static_cast<long double>(copied) * kArchiveForecast /
                              static_cast<long double>(kExpectedStreamSize);
    std::cout << "{\n";
    std::cout << "\"schema\":\"helical_wrt_far_history_discovery_scan_v1\",\n";
    std::cout << "\"store_bytes\":" << kExpectedStoreSize << ",\n";
    std::cout << "\"stream_bytes\":" << kExpectedStreamSize << ",\n";
    std::cout << "\"events\":" << events << ",\n";
    std::cout << "\"control_events\":" << controls << ",\n";
    std::cout << "\"window_bytes\":" << kWindow << ",\n";
    std::cout << "\"anchor_mask\":" << kAnchorMask << ",\n";
    std::cout << "\"minimum_distance\":" << kMinimumDistance << ",\n";
    std::cout << "\"minimum_length\":" << kMinimumLength << ",\n";
    std::cout << "\"anchors\":" << anchors << ",\n";
    std::cout << "\"unique_anchor_keys\":" << earliest.size() << ",\n";
    std::cout << "\"repeated_keys\":" << repeated << ",\n";
    std::cout << "\"exact_anchor_matches\":" << exact << ",\n";
    std::cout << "\"far_anchor_matches\":" << far << ",\n";
    std::cout << "\"rejected_hash_collisions\":" << collisions << ",\n";
    std::cout << "\"selected_matches\":" << selected << ",\n";
    std::cout << "\"copied_wrt_bytes\":" << copied << ",\n";
    std::cout << "\"gap_stream_bytes\":" << gaps.size() << ",\n";
    std::cout << "\"distance_stream_bytes\":" << distances.size() << ",\n";
    std::cout << "\"length_stream_bytes\":" << lengths.size() << ",\n";
    std::cout << "\"ledger_raw_bytes\":" << 40 + gaps.size() + distances.size() + lengths.size() << ",\n";
    std::cout << "\"split_matches\":"; PrintArray(split_matches); std::cout << ",\n";
    std::cout << "\"split_copied_wrt_bytes\":"; PrintArray(split_copied); std::cout << ",\n";
    std::cout << "\"average_rate_gross_bytes\":" << static_cast<double>(gross) << ",\n";
    std::cout << "\"all_selected_spans_event_aligned\":true,\n";
    std::cout << "\"all_selected_spans_exact_prior_and_closed\":true\n";
    std::cout << "}\n";
    munmap(const_cast<uint8_t*>(stored), kExpectedStoreSize);
    close(fd);
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
  return 0;
}
