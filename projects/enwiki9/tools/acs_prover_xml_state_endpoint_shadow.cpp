#include <algorithm>
#include <array>
#include <charconv>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

constexpr uint32_t TOTAL = 1u << 16;
constexpr uint32_t MAX_CODE = 0xffffffffu;
constexpr uint64_t SHRINKAGE = 256;
constexpr int STATE_COUNT = 5;
constexpr int BIT_POSITIONS = 8;
constexpr int PROBABILITY_BINS = 16;
constexpr std::array<int, 2> STRENGTH_NUMERATORS = {1, 2};
constexpr int STRENGTH_DENOMINATOR = 2;

enum class XmlState : uint8_t {
  TEXT = 0,
  AFTER_LT = 1,
  TAG = 2,
  DOUBLE_QUOTE = 3,
  SINGLE_QUOTE = 4,
};

struct RangeCounter {
  uint32_t x1 = 0;
  uint32_t x2 = MAX_CODE;
  uint64_t output_bytes = 0;

  void encode(int bit, uint32_t p1) {
    p1 = std::max<uint32_t>(1, std::min<uint32_t>(TOTAL - 1, p1));
    const uint32_t delta = x2 - x1;
    const uint64_t midpoint64 =
        static_cast<uint64_t>(x1) +
        static_cast<uint64_t>(delta >> 16) * p1 +
        ((static_cast<uint64_t>(delta & 0xffffu) * p1) >> 16);
    const uint32_t midpoint = static_cast<uint32_t>(midpoint64);
    if (bit) {
      x2 = midpoint;
    } else {
      x1 = midpoint + 1;
    }
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      ++output_bytes;
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
  }

  uint64_t finish_bytes() {
    while (((x1 ^ x2) & 0xff000000u) == 0) {
      ++output_bytes;
      x1 <<= 8;
      x2 = (x2 << 8) + 255;
    }
    ++output_bytes;
    return output_bytes;
  }
};

struct ResidualStats {
  int64_t residual_sum = 0;
  uint64_t count = 0;
};

struct Calibrator {
  std::array<ResidualStats,
             STATE_COUNT * BIT_POSITIONS * PROBABILITY_BINS>
      state_aware{};
  std::array<ResidualStats, BIT_POSITIONS * PROBABILITY_BINS> state_blind{};

  static size_t aware_index(XmlState state, int bit_pos, int bin) {
    return ((static_cast<size_t>(state) * BIT_POSITIONS +
             static_cast<size_t>(bit_pos)) *
                PROBABILITY_BINS +
            static_cast<size_t>(bin));
  }

  static size_t blind_index(int bit_pos, int bin) {
    return static_cast<size_t>(bit_pos) * PROBABILITY_BINS +
           static_cast<size_t>(bin);
  }

  static uint32_t adjusted_probability(uint32_t base,
                                       const ResidualStats &stats,
                                       int strength_numerator) {
    const int64_t denominator =
        static_cast<int64_t>(STRENGTH_DENOMINATOR) *
        static_cast<int64_t>(stats.count + SHRINKAGE);
    const int64_t adjustment =
        (stats.residual_sum * strength_numerator) / denominator;
    const int64_t adjusted = static_cast<int64_t>(base) + adjustment;
    return static_cast<uint32_t>(
        std::max<int64_t>(1, std::min<int64_t>(TOTAL - 1, adjusted)));
  }

  uint32_t predict_aware(uint32_t base, XmlState state, int bit_pos,
                         int strength_numerator) const {
    const int bin = std::min<int>(PROBABILITY_BINS - 1, base >> 12);
    return adjusted_probability(
        base, state_aware.at(aware_index(state, bit_pos, bin)),
        strength_numerator);
  }

  uint32_t predict_blind(uint32_t base, int bit_pos,
                         int strength_numerator) const {
    const int bin = std::min<int>(PROBABILITY_BINS - 1, base >> 12);
    return adjusted_probability(
        base, state_blind.at(blind_index(bit_pos, bin)), strength_numerator);
  }

  void update(uint32_t base, XmlState state, int bit_pos, int bit) {
    const int bin = std::min<int>(PROBABILITY_BINS - 1, base >> 12);
    const int64_t residual =
        (bit ? static_cast<int64_t>(TOTAL) : 0) - static_cast<int64_t>(base);
    auto &aware = state_aware.at(aware_index(state, bit_pos, bin));
    aware.residual_sum += residual;
    ++aware.count;
    auto &blind = state_blind.at(blind_index(bit_pos, bin));
    blind.residual_sum += residual;
    ++blind.count;
  }
};

struct CoderSet {
  RangeCounter baseline;
  std::array<RangeCounter, 2> aware;
  std::array<RangeCounter, 2> blind;

  void encode(int bit, uint32_t base,
              const std::array<uint32_t, 2> &aware_probabilities,
              const std::array<uint32_t, 2> &blind_probabilities) {
    baseline.encode(bit, base);
    for (size_t i = 0; i < aware.size(); ++i) {
      aware[i].encode(bit, aware_probabilities[i]);
      blind[i].encode(bit, blind_probabilities[i]);
    }
  }
};

struct FinishedSet {
  uint64_t baseline = 0;
  std::array<uint64_t, 2> aware{};
  std::array<uint64_t, 2> blind{};
};

FinishedSet finish(CoderSet &coders) {
  FinishedSet result;
  result.baseline = coders.baseline.finish_bytes();
  for (size_t i = 0; i < coders.aware.size(); ++i) {
    result.aware[i] = coders.aware[i].finish_bytes();
    result.blind[i] = coders.blind[i].finish_bytes();
  }
  return result;
}

uint64_t parse_uint(std::string_view text) {
  uint64_t value = 0;
  const auto parsed =
      std::from_chars(text.data(), text.data() + text.size(), value);
  if (parsed.ec != std::errc() || parsed.ptr != text.data() + text.size()) {
    throw std::runtime_error("invalid unsigned integer in trace");
  }
  return value;
}

std::array<uint64_t, 4> parse_first_four(std::string_view line) {
  std::array<uint64_t, 4> values{};
  size_t begin = 0;
  for (size_t i = 0; i < values.size(); ++i) {
    const size_t end = line.find('\t', begin);
    if (end == std::string_view::npos) {
      throw std::runtime_error("trace row has fewer than four fields");
    }
    values[i] = parse_uint(line.substr(begin, end - begin));
    begin = end + 1;
  }
  return values;
}

std::vector<uint8_t> read_binary(const std::string &path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) {
    throw std::runtime_error("cannot open raw input: " + path);
  }
  input.seekg(0, std::ios::end);
  const std::streamoff size = input.tellg();
  input.seekg(0, std::ios::beg);
  std::vector<uint8_t> data(static_cast<size_t>(size));
  if (!data.empty()) {
    input.read(reinterpret_cast<char *>(data.data()), size);
  }
  if (!input) {
    throw std::runtime_error("cannot read raw input: " + path);
  }
  return data;
}

XmlState advance_xml_state(XmlState state, uint8_t byte) {
  switch (state) {
  case XmlState::TEXT:
    return byte == '<' ? XmlState::AFTER_LT : XmlState::TEXT;
  case XmlState::AFTER_LT:
  case XmlState::TAG:
    if (byte == '>') {
      return XmlState::TEXT;
    }
    if (byte == '"') {
      return XmlState::DOUBLE_QUOTE;
    }
    if (byte == '\'') {
      return XmlState::SINGLE_QUOTE;
    }
    return XmlState::TAG;
  case XmlState::DOUBLE_QUOTE:
    return byte == '"' ? XmlState::TAG : XmlState::DOUBLE_QUOTE;
  case XmlState::SINGLE_QUOTE:
    return byte == '\'' ? XmlState::TAG : XmlState::SINGLE_QUOTE;
  }
  throw std::runtime_error("invalid XML state");
}

size_t best_index(const std::array<uint64_t, 2> &values) {
  return values[1] < values[0] ? 1 : 0;
}

double bytes_per_million(int64_t saved, uint64_t raw_bytes) {
  if (raw_bytes == 0) {
    return 0.0;
  }
  return static_cast<double>(saved) * 1000000.0 /
         static_cast<double>(raw_bytes);
}

void print_array(const std::array<uint64_t, 2> &values) {
  std::cout << '[' << values[0] << ',' << values[1] << ']';
}

} // namespace

int main(int argc, char **argv) {
  try {
    if (argc != 4) {
      throw std::runtime_error(
          "usage: shadow TRACE_TSV RAW_INPUT EXPECTED_ROWS");
    }
    const std::string trace_path = argv[1];
    const std::string raw_path = argv[2];
    const uint64_t expected_rows = parse_uint(argv[3]);
    const uint64_t dev_begin = expected_rows * 3 / 5;
    const uint64_t holdout_begin = expected_rows * 4 / 5;

    const std::vector<uint8_t> raw = read_binary(raw_path);
    std::ifstream trace(trace_path);
    if (!trace) {
      throw std::runtime_error("cannot open trace: " + trace_path);
    }

    std::string line;
    if (!std::getline(trace, line)) {
      throw std::runtime_error("empty trace");
    }

    Calibrator calibrator;
    CoderSet all;
    CoderSet development;
    CoderSet holdout;
    XmlState xml_state = XmlState::TEXT;
    uint64_t row_index = 0;
    uint64_t raw_offset = 0;
    uint64_t development_raw_bytes = 0;
    uint64_t holdout_raw_bytes = 0;

    while (std::getline(trace, line)) {
      if (line.empty()) {
        continue;
      }
      const std::string_view row(line);
      const auto first = parse_first_four(row);
      const int bit_pos = static_cast<int>(first[1]);
      const int bit = static_cast<int>(first[2]);
      const uint32_t base = static_cast<uint32_t>(first[3]);
      if (bit_pos < 0 || bit_pos >= BIT_POSITIONS || (bit != 0 && bit != 1) ||
          base >= TOTAL) {
        throw std::runtime_error("trace field outside supported range");
      }
      const size_t final_tab = row.rfind('\t');
      if (final_tab == std::string_view::npos) {
        throw std::runtime_error("trace row has no final field");
      }
      const uint64_t reconstructed =
          parse_uint(row.substr(final_tab + 1));
      if (reconstructed < raw_offset || reconstructed > raw.size()) {
        throw std::runtime_error(
            "cumulative reconstruction count is not a valid raw prefix");
      }
      const uint64_t newly_reconstructed = reconstructed - raw_offset;
      for (; raw_offset < reconstructed; ++raw_offset) {
        xml_state = advance_xml_state(xml_state, raw[raw_offset]);
      }

      std::array<uint32_t, 2> aware_probabilities{};
      std::array<uint32_t, 2> blind_probabilities{};
      for (size_t i = 0; i < STRENGTH_NUMERATORS.size(); ++i) {
        aware_probabilities[i] = calibrator.predict_aware(
            base, xml_state, bit_pos, STRENGTH_NUMERATORS[i]);
        blind_probabilities[i] = calibrator.predict_blind(
            base, bit_pos, STRENGTH_NUMERATORS[i]);
      }

      all.encode(bit, base, aware_probabilities, blind_probabilities);
      if (row_index >= dev_begin && row_index < holdout_begin) {
        development.encode(bit, base, aware_probabilities,
                           blind_probabilities);
        development_raw_bytes += newly_reconstructed;
      } else if (row_index >= holdout_begin) {
        holdout.encode(bit, base, aware_probabilities, blind_probabilities);
        holdout_raw_bytes += newly_reconstructed;
      }

      calibrator.update(base, xml_state, bit_pos, bit);
      ++row_index;
    }

    if (row_index != expected_rows) {
      throw std::runtime_error("trace row count differs from expected rows");
    }
    FinishedSet all_result = finish(all);
    FinishedSet development_result = finish(development);
    FinishedSet holdout_result = finish(holdout);
    const size_t aware_choice = best_index(development_result.aware);
    const size_t blind_choice = best_index(development_result.blind);
    const int64_t holdout_saved =
        static_cast<int64_t>(holdout_result.baseline) -
        static_cast<int64_t>(holdout_result.aware[aware_choice]);
    const int64_t blind_holdout_saved =
        static_cast<int64_t>(holdout_result.baseline) -
        static_cast<int64_t>(holdout_result.blind[blind_choice]);
    const int64_t incremental_state_saved =
        static_cast<int64_t>(holdout_result.blind[blind_choice]) -
        static_cast<int64_t>(holdout_result.aware[aware_choice]);
    const int64_t all_saved =
        static_cast<int64_t>(all_result.baseline) -
        static_cast<int64_t>(all_result.aware[aware_choice]);
    const double holdout_bpm =
        bytes_per_million(holdout_saved, holdout_raw_bytes);

    std::string decision = "retire";
    if (holdout_saved > 0 && incremental_state_saved > 0 && all_saved > 0) {
      decision = holdout_bpm >= 2100.0
                     ? "promote_to_offset_gate"
                     : (holdout_bpm >= 600.0 ? "retain_complementary"
                                             : "retire_negligible");
    }

    std::cout << '{';
    std::cout << "\"schema\":\"acs_prover_xml_state_endpoint_shadow_v1\",";
    std::cout << "\"evidence_tier\":\"causal_shadow\",";
    std::cout << "\"rows\":" << row_index << ',';
    std::cout << "\"raw_bytes\":" << raw_offset << ',';
    std::cout << "\"raw_input_bytes\":" << raw.size() << ',';
    std::cout << "\"development_rows\":" << holdout_begin - dev_begin << ',';
    std::cout << "\"development_raw_bytes\":" << development_raw_bytes << ',';
    std::cout << "\"holdout_rows\":" << expected_rows - holdout_begin << ',';
    std::cout << "\"holdout_raw_bytes\":" << holdout_raw_bytes << ',';
    std::cout << "\"strength_numerators\":[1,2],";
    std::cout << "\"strength_denominator\":2,";
    std::cout << "\"shrinkage\":" << SHRINKAGE << ',';
    std::cout << "\"all_baseline_bytes\":" << all_result.baseline << ',';
    std::cout << "\"all_state_aware_bytes\":";
    print_array(all_result.aware);
    std::cout << ',';
    std::cout << "\"all_state_blind_bytes\":";
    print_array(all_result.blind);
    std::cout << ',';
    std::cout << "\"development_baseline_bytes\":"
              << development_result.baseline << ',';
    std::cout << "\"development_state_aware_bytes\":";
    print_array(development_result.aware);
    std::cout << ',';
    std::cout << "\"development_state_blind_bytes\":";
    print_array(development_result.blind);
    std::cout << ',';
    std::cout << "\"selected_state_aware_index\":" << aware_choice << ',';
    std::cout << "\"selected_state_blind_index\":" << blind_choice << ',';
    std::cout << "\"holdout_baseline_bytes\":" << holdout_result.baseline << ',';
    std::cout << "\"holdout_state_aware_bytes\":";
    print_array(holdout_result.aware);
    std::cout << ',';
    std::cout << "\"holdout_state_blind_bytes\":";
    print_array(holdout_result.blind);
    std::cout << ',';
    std::cout << "\"holdout_saved_bytes\":" << holdout_saved << ',';
    std::cout << "\"holdout_state_blind_saved_bytes\":" << blind_holdout_saved
              << ',';
    std::cout << "\"holdout_incremental_state_saved_bytes\":"
              << incremental_state_saved << ',';
    std::cout << "\"holdout_saved_bytes_per_million\":" << holdout_bpm << ',';
    std::cout << "\"all_saved_bytes\":" << all_saved << ',';
    std::cout << "\"decision\":\"" << decision << "\"";
    std::cout << "}\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
