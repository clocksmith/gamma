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

constexpr uint64_t kRawSize = 1000000000ULL;
constexpr uint8_t kTextSegment = 7;
constexpr uint8_t kUppercase = 0x07;
constexpr uint8_t kEndUpper = 0x06;
constexpr uint8_t kCapitalized = 0x40;
constexpr uint8_t kEscape = 0x0c;

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

uint8_t Transform(uint8_t value) {
  if (value >= '{' && value < 127) value += 'P' - '{';
  else if (value >= 'P' && value < 'T') value -= 'P' - '{';
  else if ((value >= ':' && value <= '?') || (value >= 'J' && value <= 'O')) value ^= 0x70;
  if (value == 'X' || value == '`') value ^= 'X' ^ '`';
  return value;
}

std::vector<uint8_t> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary | std::ios::ate);
  if (!input) throw std::runtime_error("cannot open file");
  const size_t size = static_cast<size_t>(input.tellg());
  input.seekg(0);
  std::vector<uint8_t> payload(size);
  input.read(reinterpret_cast<char*>(payload.data()), payload.size());
  if (!input) throw std::runtime_error("file read failed");
  return payload;
}

void WriteFile(const std::string& path, const std::vector<uint8_t>& payload) {
  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  output.write(reinterpret_cast<const char*>(payload.data()), payload.size());
  if (!output) throw std::runtime_error("file write failed");
}

std::vector<std::string> ReadDictionary(const std::string& path) {
  const auto data = ReadFile(path);
  std::vector<std::string> words;
  std::string current;
  for (uint8_t value : data) {
    if (value >= 'a' && value <= 'z') current.push_back(static_cast<char>(value));
    else if (!current.empty()) {
      words.push_back(current);
      current.clear();
    }
  }
  if (!current.empty()) words.push_back(current);
  return words;
}

uint64_t TokenIndex(const std::vector<uint8_t>& code) {
  if (code.size() == 1 && code[0] >= 0x80 && code[0] <= 0xcf) return code[0] - 0x80;
  if (code.size() == 2 && code[0] >= 0xd0 && code[0] <= 0xff &&
      code[1] >= 0x80 && code[1] <= 0xcf) {
    return 80 + uint64_t(code[0] - 0xd0) * 80 + code[1] - 0x80;
  }
  if (code.size() == 3 && code[0] >= 0xf0 && code[1] >= 0xd0 &&
      code[1] <= 0xef && code[2] >= 0x80 && code[2] <= 0xcf) {
    return 3920 + uint64_t(code[0] - 0xf0) * 32 * 80 +
           uint64_t(code[1] - 0xd0) * 80 + code[2] - 0x80;
  }
  throw std::runtime_error("invalid WRT token code");
}

struct Match {
  uint32_t target;
  uint32_t source;
  uint32_t length;
};

struct WrtMatch {
  uint32_t raw_target;
  uint32_t raw_length;
  uint32_t wrt_target;
  uint32_t wrt_source;
  uint32_t wrt_length;
};

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
    if (mode == 0) distance = ReadUleb(payload, offset);
    else if (mode == 2) {
      const int64_t next = static_cast<int64_t>(distance) +
                           UnZigZag(ReadUleb(payload, offset));
      if (next <= 0) throw std::runtime_error("invalid C1 shift");
      distance = static_cast<uint64_t>(next);
    } else if (mode != 1) throw std::runtime_error("invalid C1 mode");
    const uint64_t length = ReadUleb(payload, offset);
    const uint64_t target = target_end + gap;
    if (target > UINT32_MAX || length > UINT32_MAX || distance > target) {
      throw std::runtime_error("C1 coordinate overflow");
    }
    matches.push_back(Match{static_cast<uint32_t>(target),
                            static_cast<uint32_t>(target - distance),
                            static_cast<uint32_t>(length)});
    target_end = target + length;
  }
  if (offset != payload.size()) throw std::runtime_error("trailing C1 bytes");
  return matches;
}

struct Columns {
  std::vector<uint8_t> gaps;
  std::vector<uint8_t> modes;
  std::vector<uint8_t> opens;
  std::vector<uint8_t> shifts;
  std::vector<uint8_t> lengths;
  uint64_t matches = 0;
  uint64_t raw_bytes = 0;
  uint64_t wrt_bytes = 0;
  uint64_t openings = 0;
  uint64_t continuations = 0;
  uint64_t shift_count = 0;
  std::array<uint64_t, 3> split_raw{};
  std::array<uint64_t, 3> split_wrt{};
};

Columns BuildColumns(const std::vector<WrtMatch>& matches, uint64_t floor) {
  Columns result;
  uint64_t prior_target_end = 6;
  uint64_t prior_distance = 0;
  for (const WrtMatch& match : matches) {
    const uint64_t distance = uint64_t(match.wrt_target) - match.wrt_source;
    if (distance <= floor) continue;
    PutUleb(result.gaps, uint64_t(match.wrt_target) - prior_target_end);
    uint8_t mode = 0;
    if (result.matches && distance == prior_distance) {
      mode = 1;
      ++result.continuations;
    } else if (result.matches) {
      const int64_t delta = static_cast<int64_t>(distance) -
                            static_cast<int64_t>(prior_distance);
      if (1 + UlebBytes(ZigZag(delta)) < UlebBytes(distance)) {
        mode = 2;
        PutUleb(result.shifts, ZigZag(delta));
        ++result.shift_count;
      } else {
        PutUleb(result.opens, distance);
        ++result.openings;
      }
    } else {
      PutUleb(result.opens, distance);
      ++result.openings;
    }
    result.modes.push_back(mode);
    PutUleb(result.lengths, match.wrt_length);
    prior_target_end = uint64_t(match.wrt_target) + match.wrt_length;
    prior_distance = distance;
    ++result.matches;
    result.raw_bytes += match.raw_length;
    result.wrt_bytes += match.wrt_length;
    const unsigned split = std::min<uint64_t>(2, uint64_t(match.raw_target) * 3 / kRawSize);
    result.split_raw[split] += match.raw_length;
    result.split_wrt[split] += match.wrt_length;
  }
  return result;
}

void WriteColumns(const std::string& prefix, const std::string& arm,
                  const Columns& columns) {
  WriteFile(prefix + "." + arm + ".gaps", columns.gaps);
  WriteFile(prefix + "." + arm + ".modes", columns.modes);
  WriteFile(prefix + "." + arm + ".opens", columns.opens);
  WriteFile(prefix + "." + arm + ".shifts", columns.shifts);
  WriteFile(prefix + "." + arm + ".lengths", columns.lengths);
}

void PrintColumns(const std::string& name, const Columns& value) {
  std::cout << "\"" << name << "\":{";
  std::cout << "\"matches\":" << value.matches << ',';
  std::cout << "\"raw_bytes\":" << value.raw_bytes << ',';
  std::cout << "\"wrt_bytes\":" << value.wrt_bytes << ',';
  std::cout << "\"openings\":" << value.openings << ',';
  std::cout << "\"continuations\":" << value.continuations << ',';
  std::cout << "\"shifts\":" << value.shift_count << ',';
  std::cout << "\"split_raw_bytes\":[" << value.split_raw[0] << ','
            << value.split_raw[1] << ',' << value.split_raw[2] << "],";
  std::cout << "\"split_wrt_bytes\":[" << value.split_wrt[0] << ','
            << value.split_wrt[1] << ',' << value.split_wrt[2] << "],";
  std::cout << "\"raw_column_bytes\":{";
  std::cout << "\"gaps\":" << value.gaps.size() << ',';
  std::cout << "\"modes\":" << value.modes.size() << ',';
  std::cout << "\"opens\":" << value.opens.size() << ',';
  std::cout << "\"shifts\":" << value.shifts.size() << ',';
  std::cout << "\"lengths\":" << value.lengths.size() << "}}";
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 6) {
    std::cerr << "usage: helical_far_history_wrt_event_map_qm2 RAW STORE DICT C1 PREFIX\n";
    return 2;
  }
  try {
    const auto matches = ParseC1(argv[4]);
    std::vector<uint32_t> queries;
    queries.reserve(matches.size() * 4);
    for (const Match& match : matches) {
      queries.push_back(match.target);
      queries.push_back(match.target + match.length);
      queries.push_back(match.source);
      queries.push_back(match.source + match.length);
    }
    std::sort(queries.begin(), queries.end());
    queries.erase(std::unique(queries.begin(), queries.end()), queries.end());
    std::vector<uint32_t> boundaries(queries.size(), UINT32_MAX);

    const int raw_fd = open(argv[1], O_RDONLY);
    const int store_fd = open(argv[2], O_RDONLY);
    if (raw_fd < 0 || store_fd < 0) throw std::runtime_error("cannot open raw/store");
    struct stat raw_status {}, store_status {};
    if (fstat(raw_fd, &raw_status) || uint64_t(raw_status.st_size) != kRawSize ||
        fstat(store_fd, &store_status)) throw std::runtime_error("invalid raw/store size");
    const auto* raw = static_cast<const uint8_t*>(
        mmap(nullptr, kRawSize, PROT_READ, MAP_PRIVATE, raw_fd, 0));
    const uint64_t store_size = store_status.st_size;
    const auto* stored = static_cast<const uint8_t*>(
        mmap(nullptr, store_size, PROT_READ, MAP_PRIVATE, store_fd, 0));
    if (raw == MAP_FAILED || stored == MAP_FAILED) throw std::runtime_error("mmap failed");
    if (store_size < 11 || stored[1] || stored[2] || stored[3] || stored[4] ||
        stored[5] != kTextSegment) throw std::runtime_error("invalid full WRT store header");
    const uint8_t* stream = stored + 5;
    const uint64_t stream_size = store_size - 5;
    const uint64_t declared_raw = (uint64_t(stream[1]) << 24) |
        (uint64_t(stream[2]) << 16) | (uint64_t(stream[3]) << 8) | stream[4];
    if (stream[0] != kTextSegment || stream[5] != kTextSegment || declared_raw != kRawSize) {
      throw std::runtime_error("invalid WRT text segment");
    }
    const auto dictionary = ReadDictionary(argv[3]);
    bool uppercase = false;
    bool capitalized = false;
    uint64_t position = 6;
    uint64_t raw_offset = 0;
    uint64_t events = 0;
    uint64_t controls = 0;
    size_t query_index = 0;
    while (query_index < queries.size() && queries[query_index] == 0) {
      boundaries[query_index++] = 6;
    }
    auto emit = [&](uint8_t value) {
      if (raw_offset >= kRawSize || raw[raw_offset] != value) {
        throw std::runtime_error("WRT inverse differs from canonical raw input");
      }
      ++raw_offset;
    };
    while (position < stream_size) {
      uint8_t first = Transform(stream[position++]);
      bool produced = false;
      if (first == kEscape) {
        if (position >= stream_size) throw std::runtime_error("truncated escape");
        emit(Transform(stream[position++]));
        uppercase = false;
        produced = true;
      } else if (first == kUppercase || first == kEndUpper || first == kCapitalized) {
        if (first == kUppercase) uppercase = true;
        else if (first == kEndUpper) uppercase = false;
        else capitalized = true;
        ++controls;
      } else if (first >= 0x80) {
        std::vector<uint8_t> code{first};
        if (first > 0xcf) {
          if (position >= stream_size) throw std::runtime_error("truncated token");
          code.push_back(Transform(stream[position++]));
          if (code.back() > 0xcf) {
            if (position >= stream_size) throw std::runtime_error("truncated token");
            code.push_back(Transform(stream[position++]));
          }
        }
        const uint64_t index = TokenIndex(code);
        if (index >= dictionary.size()) throw std::runtime_error("token exceeds dictionary");
        const std::string& word = dictionary[index];
        for (size_t i = 0; i < word.size(); ++i) {
          uint8_t value = static_cast<uint8_t>(word[i]);
          if (i == 0 && capitalized) {
            value = static_cast<uint8_t>(value - 'a' + 'A');
            capitalized = false;
          }
          if (uppercase) value = static_cast<uint8_t>(value - 'a' + 'A');
          emit(value);
        }
        produced = true;
      } else {
        const bool alpha = (first >= 'a' && first <= 'z') || (first >= 'A' && first <= 'Z');
        if (!alpha) uppercase = false;
        if (capitalized || uppercase) first = static_cast<uint8_t>(first - 'a' + 'A');
        if (capitalized) capitalized = false;
        emit(first);
        produced = true;
      }
      ++events;
      if (produced) {
        while (query_index < queries.size() && queries[query_index] < raw_offset) ++query_index;
        while (query_index < queries.size() && queries[query_index] == raw_offset) {
          boundaries[query_index++] = static_cast<uint32_t>(position);
        }
      }
    }
    if (raw_offset != kRawSize || position != stream_size) {
      throw std::runtime_error("WRT stream does not close exactly");
    }
    auto boundary = [&](uint32_t raw_position) -> uint32_t {
      const auto found = std::lower_bound(queries.begin(), queries.end(), raw_position);
      if (found == queries.end() || *found != raw_position) throw std::runtime_error("missing query");
      return boundaries[found - queries.begin()];
    };
    std::vector<WrtMatch> compatible;
    compatible.reserve(matches.size());
    uint64_t event_aligned = 0;
    uint64_t encoded_equal = 0;
    uint64_t aligned_raw_bytes = 0;
    uint64_t encoded_equal_raw_bytes = 0;
    for (const Match& match : matches) {
      const uint32_t ts = boundary(match.target);
      const uint32_t te = boundary(match.target + match.length);
      const uint32_t ss = boundary(match.source);
      const uint32_t se = boundary(match.source + match.length);
      if (ts == UINT32_MAX || te == UINT32_MAX || ss == UINT32_MAX || se == UINT32_MAX) continue;
      ++event_aligned;
      aligned_raw_bytes += match.length;
      if (te < ts || se < ss || te - ts != se - ss ||
          std::memcmp(stream + ts, stream + ss, te - ts) != 0) continue;
      ++encoded_equal;
      encoded_equal_raw_bytes += match.length;
      compatible.push_back(WrtMatch{match.target, match.length, ts, ss, te - ts});
    }
    const Columns endpoint = BuildColumns(compatible, 100000000ULL);
    const Columns cmix = BuildColumns(compatible, 60000000ULL);
    WriteColumns(argv[5], "endpoint", endpoint);
    WriteColumns(argv[5], "cmix", cmix);
    std::cout << "{\n";
    std::cout << "\"schema\":\"helical_far_history_wrt_event_map_scan_v1\",\n";
    std::cout << "\"raw_bytes\":" << kRawSize << ",\n";
    std::cout << "\"store_bytes\":" << store_size << ",\n";
    std::cout << "\"wrt_stream_bytes\":" << stream_size << ",\n";
    std::cout << "\"wrt_events\":" << events << ",\n";
    std::cout << "\"wrt_control_events\":" << controls << ",\n";
    std::cout << "\"input_matches\":" << matches.size() << ",\n";
    std::cout << "\"event_aligned_matches\":" << event_aligned << ",\n";
    std::cout << "\"event_aligned_raw_bytes\":" << aligned_raw_bytes << ",\n";
    std::cout << "\"encoded_equal_matches\":" << encoded_equal << ",\n";
    std::cout << "\"encoded_equal_raw_bytes\":" << encoded_equal_raw_bytes << ",\n";
    PrintColumns("endpoint100m", endpoint);
    std::cout << ",\n";
    PrintColumns("cmix60m", cmix);
    std::cout << ",\n\"full_wrt_inverse_exact\":true,\n";
    std::cout << "\"all_selected_wrt_spans_exact_equal\":true\n}\n";
    munmap(const_cast<uint8_t*>(raw), kRawSize);
    munmap(const_cast<uint8_t*>(stored), store_size);
    close(raw_fd);
    close(store_fd);
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
  return 0;
}
