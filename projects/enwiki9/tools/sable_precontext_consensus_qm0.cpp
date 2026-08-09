#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
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

constexpr uint64_t kExpectedSize = 587138826ULL;
constexpr uint32_t kWindow = 32;
constexpr uint64_t kAnchorMask = 63;
constexpr uint64_t kMinimumDistance = 60000000ULL;
constexpr uint64_t kGrossGateBytes = 4056825ULL;
constexpr uint32_t kShiftControl = 37;

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

struct State {
  uint32_t representative_context;
  uint32_t latest_continuation;
  uint32_t consensus_length;
  uint32_t occurrences;
};

struct Interval {
  uint64_t start;
  uint32_t length;
};

uint64_t Lcp(const uint8_t* data, uint64_t first, uint64_t second,
             uint64_t limit) {
  uint64_t length = 0;
  while (length + sizeof(uint64_t) <= limit) {
    uint64_t a = 0;
    uint64_t b = 0;
    std::memcpy(&a, data + first + length, sizeof(a));
    std::memcpy(&b, data + second + length, sizeof(b));
    if (a != b) break;
    length += sizeof(uint64_t);
  }
  while (length < limit && data[first + length] == data[second + length]) {
    ++length;
  }
  return length;
}

void PutLe32(std::ofstream& output, uint32_t value) {
  for (unsigned i = 0; i < 4; ++i) {
    output.put(static_cast<char>((value >> (8 * i)) & 255));
  }
}

void PutLe64(std::ofstream& output, uint64_t value) {
  for (unsigned i = 0; i < 8; ++i) {
    output.put(static_cast<char>((value >> (8 * i)) & 255));
  }
}

void PrintArray(const std::array<uint64_t, 3>& values) {
  std::cout << "[" << values[0] << "," << values[1] << "," << values[2]
            << "]";
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 3) {
    std::cerr << "usage: sable_precontext_consensus_qm0 INPUT INTERVALS\n";
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
    std::cerr << "input identity size mismatch\n";
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

  auto InitialHash = [&](uint64_t start,
                         const std::array<uint64_t, 256>& table) {
    uint64_t hash = 0;
    for (uint32_t i = 0; i < kWindow; ++i) {
      hash = RotL(hash, 1) ^ table[data[start + i]];
    }
    return hash;
  };
  auto AdvanceHash = [&](uint64_t hash, uint64_t start,
                         const std::array<uint64_t, 256>& table) {
    return RotL(hash, 1) ^ RotL(table[data[start]], kWindow) ^
           table[data[start + kWindow]];
  };

  uint64_t current_hash1 = InitialHash(0, table1);
  uint64_t current_hash2 = InitialHash(0, table2);
  uint64_t delayed_hash1 = current_hash1;
  uint64_t delayed_hash2 = current_hash2;

  std::unordered_map<Key, State, KeyHash> states;
  states.max_load_factor(0.85f);
  states.reserve(static_cast<size_t>(size / 58));

  uint64_t preceding_anchors = 0;
  uint64_t admitted_sources = 0;
  uint64_t repeated_source_contexts = 0;
  uint64_t eligible_targets = 0;
  uint64_t singleton_targets = 0;
  uint64_t multi_source_targets = 0;
  uint64_t correct_consensus_targets = 0;
  uint64_t consensus_candidate_bytes = 0;
  uint64_t correct_consensus_bytes_raw = 0;
  uint64_t distinct_consensus_bytes = 0;
  uint64_t shifted37_correct_bytes_raw = 0;
  uint64_t distinct_shifted37_bytes = 0;
  uint64_t last_end = 0;
  uint64_t shifted_last_end = 0;
  uint64_t maximum_occurrences = 0;
  uint64_t maximum_consensus = 0;
  std::array<uint64_t, 3> split_distinct{};
  std::array<uint64_t, 3> split_targets{};
  std::vector<Interval> intervals;
  intervals.reserve(100000);

  const uint64_t final_context_start = size - kWindow;
  for (uint64_t context_start = 0; context_start <= final_context_start;
       ++context_start) {
    if (context_start > kMinimumDistance) {
      const uint64_t source_context = context_start - kMinimumDistance - 1;
      if ((delayed_hash1 & kAnchorMask) == 0) {
        const Key key{delayed_hash1, delayed_hash2};
        const uint64_t continuation = source_context + kWindow;
        auto [it, inserted] = states.emplace(
            key, State{static_cast<uint32_t>(source_context),
                       static_cast<uint32_t>(continuation),
                       static_cast<uint32_t>(size - continuation), 1});
        ++admitted_sources;
        if (!inserted) {
          State& state = it->second;
          if (std::memcmp(data + state.representative_context,
                          data + source_context, kWindow) != 0) {
            std::cerr << "128-bit context hash collision\n";
            return 3;
          }
          const uint64_t representative =
              static_cast<uint64_t>(state.representative_context) + kWindow;
          const uint64_t limit = std::min<uint64_t>(
              state.consensus_length,
              std::min(size - representative, size - continuation));
          state.consensus_length = static_cast<uint32_t>(
              Lcp(data, representative, continuation, limit));
          state.latest_continuation = static_cast<uint32_t>(continuation);
          ++state.occurrences;
          ++repeated_source_contexts;
        }
        maximum_occurrences = std::max<uint64_t>(maximum_occurrences,
                                                  it->second.occurrences);
      }
      if (source_context < final_context_start) {
        delayed_hash1 = AdvanceHash(delayed_hash1, source_context, table1);
        delayed_hash2 = AdvanceHash(delayed_hash2, source_context, table2);
      }
    }

    if ((current_hash1 & kAnchorMask) == 0) {
      ++preceding_anchors;
      const Key key{current_hash1, current_hash2};
      const auto found = states.find(key);
      if (found != states.end()) {
        const State& state = found->second;
        if (std::memcmp(data + state.representative_context,
                        data + context_start, kWindow) != 0) {
          std::cerr << "target context hash collision\n";
          return 3;
        }
        const uint64_t target = context_start + kWindow;
        const uint64_t representative =
            static_cast<uint64_t>(state.representative_context) + kWindow;
        const uint64_t causal_closed =
            target - static_cast<uint64_t>(state.latest_continuation);
        const uint64_t limit = std::min<uint64_t>(
            state.consensus_length,
            std::min(causal_closed, size - target));
        ++eligible_targets;
        singleton_targets += state.occurrences == 1;
        multi_source_targets += state.occurrences > 1;
        consensus_candidate_bytes += limit;
        maximum_consensus = std::max(maximum_consensus, limit);
        const uint64_t correct = Lcp(data, target, representative, limit);
        correct_consensus_bytes_raw += correct;
        if (correct) {
          ++correct_consensus_targets;
          const uint64_t start = std::max(target, last_end);
          const uint64_t end = target + correct;
          if (end > start) {
            const uint64_t added = end - start;
            intervals.push_back(
                Interval{start, static_cast<uint32_t>(added)});
            distinct_consensus_bytes += added;
            const unsigned split = std::min<uint64_t>(2, start * 3 / size);
            split_distinct[split] += added;
            ++split_targets[split];
            last_end = end;
          }
        }

        if (representative + kShiftControl < size) {
          const uint64_t shifted_limit = std::min<uint64_t>(
              limit, size - representative - kShiftControl);
          const uint64_t shifted = Lcp(
              data, target, representative + kShiftControl, shifted_limit);
          shifted37_correct_bytes_raw += shifted;
          const uint64_t shifted_start = std::max(target, shifted_last_end);
          const uint64_t shifted_end = target + shifted;
          if (shifted_end > shifted_start) {
            distinct_shifted37_bytes += shifted_end - shifted_start;
            shifted_last_end = shifted_end;
          }
        }
      }
    }

    if (context_start < final_context_start) {
      current_hash1 = AdvanceHash(current_hash1, context_start, table1);
      current_hash2 = AdvanceHash(current_hash2, context_start, table2);
    }
  }

  std::ofstream output(argv[2], std::ios::binary | std::ios::trunc);
  if (!output) {
    std::cerr << "cannot create interval artifact\n";
    return 2;
  }
  output.write("SABLEA1\0", 8);
  PutLe64(output, intervals.size());
  PutLe64(output, distinct_consensus_bytes);
  for (const Interval& interval : intervals) {
    PutLe64(output, interval.start);
    PutLe32(output, interval.length);
  }
  output.close();
  if (!output) {
    std::cerr << "interval write failed\n";
    return 2;
  }

  const uint64_t entry_payload_bytes =
      states.size() * sizeof(std::pair<const Key, State>);
  const uint64_t bucket_pointer_bytes = states.bucket_count() * sizeof(void*);
  const uint64_t compact_minimum_bytes =
      states.size() * (sizeof(Key) + sizeof(State));
  std::cout << "{\n";
  std::cout << "\"schema\":\"sable_precontext_consensus_scan_v1\",\n";
  std::cout << "\"input_bytes\":" << size << ",\n";
  std::cout << "\"window_bytes\":" << kWindow << ",\n";
  std::cout << "\"anchor_mask\":" << kAnchorMask << ",\n";
  std::cout << "\"minimum_distance\":" << kMinimumDistance << ",\n";
  std::cout << "\"gross_gate_bytes\":" << kGrossGateBytes << ",\n";
  std::cout << "\"preceding_context_anchors\":" << preceding_anchors << ",\n";
  std::cout << "\"admitted_sources\":" << admitted_sources << ",\n";
  std::cout << "\"unique_far_contexts\":" << states.size() << ",\n";
  std::cout << "\"repeated_source_contexts\":" << repeated_source_contexts << ",\n";
  std::cout << "\"eligible_targets\":" << eligible_targets << ",\n";
  std::cout << "\"singleton_targets\":" << singleton_targets << ",\n";
  std::cout << "\"multi_source_targets\":" << multi_source_targets << ",\n";
  std::cout << "\"correct_consensus_targets\":" << correct_consensus_targets << ",\n";
  std::cout << "\"consensus_candidate_bytes\":" << consensus_candidate_bytes << ",\n";
  std::cout << "\"correct_consensus_bytes_raw\":" << correct_consensus_bytes_raw << ",\n";
  std::cout << "\"distinct_consensus_bytes\":" << distinct_consensus_bytes << ",\n";
  std::cout << "\"split_distinct_consensus_bytes\":"; PrintArray(split_distinct); std::cout << ",\n";
  std::cout << "\"split_contributing_targets\":"; PrintArray(split_targets); std::cout << ",\n";
  std::cout << "\"shifted37_correct_bytes_raw\":" << shifted37_correct_bytes_raw << ",\n";
  std::cout << "\"distinct_shifted37_bytes\":" << distinct_shifted37_bytes << ",\n";
  std::cout << "\"maximum_occurrences_per_context\":" << maximum_occurrences << ",\n";
  std::cout << "\"maximum_consensus_length\":" << maximum_consensus << ",\n";
  std::cout << "\"interval_records\":" << intervals.size() << ",\n";
  std::cout << "\"state_key_bytes\":" << sizeof(Key) << ",\n";
  std::cout << "\"state_value_bytes\":" << sizeof(State) << ",\n";
  std::cout << "\"compact_minimum_resident_bytes\":" << compact_minimum_bytes << ",\n";
  std::cout << "\"unordered_entry_payload_bytes\":" << entry_payload_bytes << ",\n";
  std::cout << "\"unordered_bucket_pointer_bytes\":" << bucket_pointer_bytes << ",\n";
  std::cout << "\"all_sources_strictly_beyond_ring\":true,\n";
  std::cout << "\"activation_uses_preceding_context_only\":true,\n";
  std::cout << "\"target_bytes_excluded_from_activation\":true,\n";
  std::cout << "\"all_hash_matches_exactly_verified\":true\n";
  std::cout << "}\n";

  munmap(const_cast<uint8_t*>(data), size);
  close(fd);
  return 0;
}
