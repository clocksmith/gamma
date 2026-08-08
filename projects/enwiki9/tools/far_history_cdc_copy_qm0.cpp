#include <algorithm>
#include <array>
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <iostream>
#include <limits>
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unordered_map>
#include <unistd.h>

namespace {

constexpr uint64_t kExpectedSize = 1000000000ULL;
constexpr uint32_t kWindow = 32;
constexpr uint64_t kAnchorMask = 63;
constexpr uint64_t kMinimumDistance = 100000000ULL;
constexpr uint64_t kMinimumLength = 64;
constexpr uint64_t kArchiveOnlyForecast = 109128198ULL;

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

size_t UlebBytes(uint64_t value) {
  size_t bytes = 1;
  while (value >= 128) {
    value >>= 7;
    ++bytes;
  }
  return bytes;
}

unsigned Bin(uint64_t value) {
  unsigned result = 0;
  while (value > 1 && result < 63) {
    value >>= 1;
    ++result;
  }
  return result;
}

void PrintArray(const std::array<uint64_t, 3>& values) {
  std::cout << "[" << values[0] << "," << values[1] << "," << values[2] << "]";
}

void PrintHistogram(const std::array<uint64_t, 64>& values) {
  std::cout << "[";
  for (size_t i = 0; i < values.size(); ++i) {
    if (i) std::cout << ",";
    std::cout << values[i];
  }
  std::cout << "]";
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 2) {
    std::cerr << "usage: far_history_cdc_copy_qm0 INPUT\n";
    return 2;
  }
  const int fd = open(argv[1], O_RDONLY);
  if (fd < 0) {
    std::perror("open");
    return 2;
  }
  struct stat status {};
  if (fstat(fd, &status) != 0) {
    std::perror("fstat");
    close(fd);
    return 2;
  }
  const uint64_t size = static_cast<uint64_t>(status.st_size);
  if (size != kExpectedSize) {
    std::cerr << "input size must be exactly 1000000000 bytes\n";
    close(fd);
    return 2;
  }
  const auto* data = static_cast<const uint8_t*>(
      mmap(nullptr, size, PROT_READ, MAP_PRIVATE, fd, 0));
  if (data == MAP_FAILED) {
    std::perror("mmap");
    close(fd);
    return 2;
  }
  madvise(const_cast<uint8_t*>(data), size, MADV_SEQUENTIAL);

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

  std::unordered_map<Key, uint32_t, KeyHash> earliest;
  earliest.max_load_factor(0.85f);
  earliest.reserve(static_cast<size_t>(size / 58));

  uint64_t anchors = 0;
  uint64_t repeated_keys = 0;
  uint64_t exact_anchor_matches = 0;
  uint64_t rejected_hash_collisions = 0;
  uint64_t far_anchor_matches = 0;
  uint64_t selected_matches = 0;
  uint64_t copied_bytes = 0;
  uint64_t command_bytes = 0;
  uint64_t maximum_length = 0;
  uint64_t maximum_distance = 0;
  uint64_t last_target_end = 0;
  std::array<uint64_t, 3> split_matches{};
  std::array<uint64_t, 3> split_copied{};
  std::array<uint64_t, 3> split_commands{};
  std::array<uint64_t, 64> length_histogram{};
  std::array<uint64_t, 64> distance_histogram{};

  for (uint64_t position = 0; position + kWindow <= size; ++position) {
    if ((hash1 & kAnchorMask) == 0) {
      ++anchors;
      const Key key{hash1, hash2};
      const auto found = earliest.find(key);
      if (found == earliest.end()) {
        earliest.emplace(key, static_cast<uint32_t>(position));
      } else {
        ++repeated_keys;
        const uint64_t source_anchor = found->second;
        if (std::memcmp(data + source_anchor, data + position, kWindow) != 0) {
          ++rejected_hash_collisions;
        } else {
          ++exact_anchor_matches;
          if (position >= source_anchor + kMinimumDistance) {
            ++far_anchor_matches;
            if (position >= last_target_end) {
              uint64_t target = position;
              uint64_t source = source_anchor;
              while (target > last_target_end && source > 0 &&
                     data[target - 1] == data[source - 1]) {
                --target;
                --source;
              }
              const uint64_t distance = target - source;
              uint64_t length = position + kWindow - target;
              const uint64_t maximum_closed_length = std::min(distance, size - target);
              while (length < maximum_closed_length &&
                     data[target + length] == data[source + length]) {
                ++length;
              }
              if (length >= kMinimumLength) {
                const uint64_t cost = 1 + UlebBytes(distance) + UlebBytes(length);
                const unsigned split = std::min<uint64_t>(2, target * 3 / size);
                ++selected_matches;
                copied_bytes += length;
                command_bytes += cost;
                split_matches[split] += 1;
                split_copied[split] += length;
                split_commands[split] += cost;
                length_histogram[Bin(length)] += 1;
                distance_histogram[Bin(distance)] += 1;
                maximum_length = std::max(maximum_length, length);
                maximum_distance = std::max(maximum_distance, distance);
                last_target_end = target + length;
              }
            }
          }
        }
      }
    }
    if (position + kWindow < size) {
      hash1 = RotL(hash1, 1) ^ RotL(table1[data[position]], kWindow) ^
              table1[data[position + kWindow]];
      hash2 = RotL(hash2, 1) ^ RotL(table2[data[position]], kWindow) ^
              table2[data[position + kWindow]];
    }
  }

  const long double gross = static_cast<long double>(copied_bytes) *
      static_cast<long double>(kArchiveOnlyForecast) /
      static_cast<long double>(kExpectedSize);
  const long double net = gross - static_cast<long double>(command_bytes);

  std::cout << "{\n";
  std::cout << "\"schema\":\"far_history_cdc_copy_scan_v1\",\n";
  std::cout << "\"input_bytes\":" << size << ",\n";
  std::cout << "\"window_bytes\":" << kWindow << ",\n";
  std::cout << "\"anchor_mask\":" << kAnchorMask << ",\n";
  std::cout << "\"minimum_distance\":" << kMinimumDistance << ",\n";
  std::cout << "\"minimum_length\":" << kMinimumLength << ",\n";
  std::cout << "\"anchors\":" << anchors << ",\n";
  std::cout << "\"unique_anchor_keys\":" << earliest.size() << ",\n";
  std::cout << "\"repeated_keys\":" << repeated_keys << ",\n";
  std::cout << "\"exact_anchor_matches\":" << exact_anchor_matches << ",\n";
  std::cout << "\"rejected_hash_collisions\":" << rejected_hash_collisions << ",\n";
  std::cout << "\"far_anchor_matches\":" << far_anchor_matches << ",\n";
  std::cout << "\"selected_matches\":" << selected_matches << ",\n";
  std::cout << "\"copied_bytes\":" << copied_bytes << ",\n";
  std::cout << "\"command_bytes\":" << command_bytes << ",\n";
  std::cout << "\"maximum_length\":" << maximum_length << ",\n";
  std::cout << "\"maximum_distance\":" << maximum_distance << ",\n";
  std::cout << "\"split_matches\":"; PrintArray(split_matches); std::cout << ",\n";
  std::cout << "\"split_copied_bytes\":"; PrintArray(split_copied); std::cout << ",\n";
  std::cout << "\"split_command_bytes\":"; PrintArray(split_commands); std::cout << ",\n";
  std::cout << "\"length_log2_histogram\":"; PrintHistogram(length_histogram); std::cout << ",\n";
  std::cout << "\"distance_log2_histogram\":"; PrintHistogram(distance_histogram); std::cout << ",\n";
  std::cout << "\"archive_only_forecast_bytes\":" << kArchiveOnlyForecast << ",\n";
  std::cout << "\"average_rate_equivalent_gross_bytes\":" << static_cast<double>(gross) << ",\n";
  std::cout << "\"average_rate_equivalent_net_before_source\":" << static_cast<double>(net) << ",\n";
  std::cout << "\"selected_sources_strictly_prior\":true,\n";
  std::cout << "\"selected_sources_fully_closed\":true,\n";
  std::cout << "\"selected_anchors_exactly_verified\":true\n";
  std::cout << "}\n";

  munmap(const_cast<uint8_t*>(data), size);
  close(fd);
  return 0;
}

