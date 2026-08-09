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
#include <unistd.h>
#include <vector>

namespace {

constexpr uint64_t kExpectedSize = 1000000000ULL;
constexpr uint32_t kWindow = 32;
constexpr uint64_t kAnchorMask = 63;
constexpr uint64_t kMinimumDistance = 100000000ULL;

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

uint64_t ReadLe64(const uint8_t* data) {
  uint64_t value = 0;
  for (unsigned i = 0; i < 8; ++i) value |= uint64_t(data[i]) << (8 * i);
  return value;
}

uint64_t ReadUleb(const std::vector<uint8_t>& data, size_t& offset) {
  uint64_t value = 0;
  unsigned shift = 0;
  while (offset < data.size()) {
    const uint8_t byte = data[offset++];
    value |= uint64_t(byte & 127) << shift;
    if (byte < 128) return value;
    shift += 7;
    if (shift >= 64) throw std::runtime_error("ULEB overflow");
  }
  throw std::runtime_error("truncated ULEB");
}

void PutUleb(std::vector<uint8_t>& output, uint64_t value) {
  do {
    uint8_t byte = static_cast<uint8_t>(value & 127);
    value >>= 7;
    if (value) byte |= 128;
    output.push_back(byte);
  } while (value);
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

int64_t UnZigZag(uint64_t value) {
  return static_cast<int64_t>((value >> 1) ^ uint64_t(-int64_t(value & 1)));
}

struct Match {
  uint32_t target;
  uint32_t length;
  uint32_t distance;
};

struct Run {
  uint32_t start_chunk;
  uint32_t chunk_count;
  uint32_t distance;
};

std::vector<uint8_t> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary | std::ios::ate);
  if (!input) throw std::runtime_error("cannot open input file");
  const size_t size = static_cast<size_t>(input.tellg());
  input.seekg(0);
  std::vector<uint8_t> payload(size);
  input.read(reinterpret_cast<char*>(payload.data()), payload.size());
  if (!input) throw std::runtime_error("input read failed");
  return payload;
}

void WriteFile(const std::string& path, const std::vector<uint8_t>& payload) {
  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  output.write(reinterpret_cast<const char*>(payload.data()), payload.size());
  if (!output) throw std::runtime_error("output write failed");
}

std::vector<Match> ParseC1(const std::string& path) {
  const auto payload = ReadFile(path);
  if (payload.size() < 16 || std::memcmp(payload.data(), "HFCC1\0\0\0", 8)) {
    throw std::runtime_error("bad C1 stream");
  }
  const uint64_t count = ReadLe64(payload.data() + 8);
  std::vector<Match> matches;
  matches.reserve(count);
  size_t offset = 16;
  uint64_t target_end = 0;
  uint64_t distance = 0;
  for (uint64_t i = 0; i < count; ++i) {
    const uint64_t gap = ReadUleb(payload, offset);
    if (offset >= payload.size()) throw std::runtime_error("missing C1 mode");
    const uint8_t mode = payload[offset++];
    if (mode == 0) {
      distance = ReadUleb(payload, offset);
    } else if (mode == 2) {
      const int64_t shifted = static_cast<int64_t>(distance) +
                              UnZigZag(ReadUleb(payload, offset));
      if (shifted <= 0) throw std::runtime_error("invalid shifted distance");
      distance = static_cast<uint64_t>(shifted);
    } else if (mode != 1) {
      throw std::runtime_error("invalid C1 mode");
    }
    const uint64_t length = ReadUleb(payload, offset);
    const uint64_t target = target_end + gap;
    if (target > UINT32_MAX || length > UINT32_MAX || distance > UINT32_MAX) {
      throw std::runtime_error("C1 coordinate overflow");
    }
    matches.push_back(Match{static_cast<uint32_t>(target),
                            static_cast<uint32_t>(length),
                            static_cast<uint32_t>(distance)});
    target_end = target + length;
  }
  if (offset != payload.size()) throw std::runtime_error("trailing C1 bytes");
  return matches;
}

std::vector<uint32_t> BuildAnchors(const uint8_t* data, uint64_t size) {
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
  std::vector<uint32_t> anchors;
  anchors.reserve(static_cast<size_t>(size / 58));
  for (uint64_t position = 0; position + kWindow <= size; ++position) {
    if ((hash1 & kAnchorMask) == 0) anchors.push_back(position);
    if (position + kWindow < size) {
      hash1 = RotL(hash1, 1) ^ RotL(table1[data[position]], kWindow) ^
              table1[data[position + kWindow]];
      hash2 = RotL(hash2, 1) ^ RotL(table2[data[position]], kWindow) ^
              table2[data[position + kWindow]];
    }
  }
  return anchors;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 9) {
    std::cerr << "usage: helical_far_history_cdc_implicit_qm1 INPUT C1 "
                 "BITSET GAP COUNT ADDR_MODE OPEN SHIFT\n";
    return 2;
  }
  try {
    const auto matches = ParseC1(argv[2]);
    const int fd = open(argv[1], O_RDONLY);
    if (fd < 0) throw std::runtime_error("cannot open corpus");
    struct stat status {};
    if (fstat(fd, &status) || uint64_t(status.st_size) != kExpectedSize) {
      throw std::runtime_error("corpus must be canonical 1G size");
    }
    const auto* data = static_cast<const uint8_t*>(
        mmap(nullptr, kExpectedSize, PROT_READ, MAP_PRIVATE, fd, 0));
    if (data == MAP_FAILED) throw std::runtime_error("mmap failed");
    madvise(const_cast<uint8_t*>(data), kExpectedSize, MADV_SEQUENTIAL);
    const auto anchors = BuildAnchors(data, kExpectedSize);
    if (anchors.size() < 2) throw std::runtime_error("insufficient anchors");
    const uint64_t chunks = anchors.size() - 1;
    std::vector<uint8_t> bitset((chunks + 7) / 8, 0);
    std::vector<Run> runs;
    runs.reserve(matches.size());
    uint64_t copied_bytes = 0;
    uint64_t copied_chunks = 0;
    uint64_t matches_with_chunks = 0;
    std::array<uint64_t, 3> split_copied{};

    for (const Match& match : matches) {
      const uint64_t end = uint64_t(match.target) + match.length;
      auto first = std::lower_bound(anchors.begin(), anchors.end(), match.target);
      auto after = std::upper_bound(first, anchors.end(), end - kWindow);
      if (first == anchors.end() || after - first < 2) continue;
      const size_t start_index = static_cast<size_t>(first - anchors.begin());
      const size_t end_index = static_cast<size_t>(after - anchors.begin() - 1);
      const uint64_t start = anchors[start_index];
      const uint64_t finish = anchors[end_index];
      if (start < match.target || finish > end || finish <= start ||
          match.distance < kMinimumDistance || match.distance > start) {
        throw std::runtime_error("invalid complete chunk interval");
      }
      const uint64_t source_start = start - match.distance;
      const uint64_t source_finish = finish - match.distance;
      if (!std::binary_search(anchors.begin(), anchors.end(), source_start) ||
          !std::binary_search(anchors.begin(), anchors.end(), source_finish) ||
          std::memcmp(data + start, data + source_start, finish - start) != 0) {
        throw std::runtime_error("source CDC boundaries or content mismatch");
      }
      const uint32_t count = static_cast<uint32_t>(end_index - start_index);
      if (!runs.empty() &&
          uint64_t(runs.back().start_chunk) + runs.back().chunk_count == start_index &&
          runs.back().distance == match.distance) {
        runs.back().chunk_count += count;
      } else {
        runs.push_back(Run{static_cast<uint32_t>(start_index), count,
                           match.distance});
      }
      for (size_t chunk = start_index; chunk < end_index; ++chunk) {
        if (bitset[chunk >> 3] & (1U << (chunk & 7))) {
          throw std::runtime_error("overlapping copied CDC chunk");
        }
        bitset[chunk >> 3] |= static_cast<uint8_t>(1U << (chunk & 7));
      }
      const uint64_t width = finish - start;
      copied_bytes += width;
      copied_chunks += count;
      ++matches_with_chunks;
      split_copied[std::min<uint64_t>(2, start * 3 / kExpectedSize)] += width;
    }

    std::vector<uint8_t> gaps;
    std::vector<uint8_t> counts;
    std::vector<uint8_t> address_modes;
    std::vector<uint8_t> opens;
    std::vector<uint8_t> shifts;
    uint64_t prior_chunk_end = 0;
    uint64_t prior_distance = 0;
    uint64_t openings = 0;
    uint64_t continuations = 0;
    uint64_t shift_count = 0;
    for (const Run& run : runs) {
      PutUleb(gaps, uint64_t(run.start_chunk) - prior_chunk_end);
      PutUleb(counts, run.chunk_count);
      uint8_t mode = 0;
      if (prior_chunk_end && run.distance == prior_distance) {
        mode = 1;
        ++continuations;
      } else if (prior_chunk_end) {
        const int64_t delta = static_cast<int64_t>(run.distance) -
                              static_cast<int64_t>(prior_distance);
        if (1 + UlebBytes(ZigZag(delta)) < UlebBytes(run.distance)) {
          mode = 2;
          PutUleb(shifts, ZigZag(delta));
          ++shift_count;
        } else {
          PutUleb(opens, run.distance);
          ++openings;
        }
      } else {
        PutUleb(opens, run.distance);
        ++openings;
      }
      address_modes.push_back(mode);
      prior_chunk_end = uint64_t(run.start_chunk) + run.chunk_count;
      prior_distance = run.distance;
    }
    WriteFile(argv[3], bitset);
    WriteFile(argv[4], gaps);
    WriteFile(argv[5], counts);
    WriteFile(argv[6], address_modes);
    WriteFile(argv[7], opens);
    WriteFile(argv[8], shifts);
    std::cout << "{\n"
              << "\"schema\":\"helical_far_history_cdc_implicit_scan_v1\",\n"
              << "\"input_bytes\":" << kExpectedSize << ",\n"
              << "\"matches\":" << matches.size() << ",\n"
              << "\"anchors\":" << anchors.size() << ",\n"
              << "\"chunks\":" << chunks << ",\n"
              << "\"matches_with_complete_chunks\":" << matches_with_chunks << ",\n"
              << "\"copy_runs\":" << runs.size() << ",\n"
              << "\"copied_chunks\":" << copied_chunks << ",\n"
              << "\"copied_bytes\":" << copied_bytes << ",\n"
              << "\"split_copied_bytes\":[" << split_copied[0] << ","
              << split_copied[1] << "," << split_copied[2] << "],\n"
              << "\"openings\":" << openings << ",\n"
              << "\"continuations\":" << continuations << ",\n"
              << "\"shifts\":" << shift_count << ",\n"
              << "\"bitset_bytes\":" << bitset.size() << ",\n"
              << "\"gap_stream_bytes\":" << gaps.size() << ",\n"
              << "\"count_stream_bytes\":" << counts.size() << ",\n"
              << "\"address_mode_bytes\":" << address_modes.size() << ",\n"
              << "\"open_stream_bytes\":" << opens.size() << ",\n"
              << "\"shift_stream_bytes\":" << shifts.size() << ",\n"
              << "\"all_source_boundaries_decoder_visible\":true,\n"
              << "\"all_chunks_exact_prior_and_closed\":true\n"
              << "}\n";
    munmap(const_cast<uint8_t*>(data), kExpectedSize);
    close(fd);
  } catch (const std::exception& error) {
    std::cerr << error.what() << "\n";
    return 2;
  }
  return 0;
}
