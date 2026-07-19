// Causal fixed-point Newton residual endpoint over decoder-visible WRT phase.

#include "wrt_phase_residual_native.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr std::uint32_t kTotal = 65536;
constexpr std::uint32_t kMaxCode = 0xffffffffu;
constexpr std::uint64_t kBlockBytes = 65536;
constexpr std::array<std::uint32_t, 3> kPriorObservations = {64, 256, 1024};
constexpr std::array<std::size_t, 4> kLevelSizes = {
    4096, 16384, 65536, 1048576};

std::vector<unsigned char> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open " + path);
  input.seekg(0, std::ios::end);
  const auto size = input.tellg();
  if (size < 0) throw std::runtime_error("cannot size " + path);
  input.seekg(0, std::ios::beg);
  std::vector<unsigned char> data(static_cast<std::size_t>(size));
  if (!data.empty()) input.read(reinterpret_cast<char*>(data.data()), size);
  if (!input) throw std::runtime_error("cannot read " + path);
  return data;
}

std::uint64_t ReadU64(const unsigned char* input) {
  std::uint64_t value = 0;
  for (unsigned int shift = 0; shift < 64; shift += 8) {
    value |= static_cast<std::uint64_t>(*input++) << shift;
  }
  return value;
}

std::int32_t Log2Q16(std::uint32_t value) {
  if (value == 0) throw std::runtime_error("log2 input is zero");
  const unsigned int integer = 31U - __builtin_clz(value);
  std::uint64_t normalized =
      static_cast<std::uint64_t>(value) << (31U - integer);
  std::uint32_t fraction = 0;
  for (int bit = 15; bit >= 0; --bit) {
    std::uint64_t squared = (normalized * normalized) >> 31;
    if (squared >= (std::uint64_t{1} << 32)) {
      squared >>= 1;
      fraction |= std::uint32_t{1} << bit;
    }
    normalized = squared;
  }
  return static_cast<std::int32_t>((integer << 16) | fraction);
}

struct Tables {
  Tables() {
    logit[0] = Log2Q16(1) - Log2Q16(kTotal - 1);
    for (std::uint32_t p = 1; p < kTotal; ++p) {
      logit[p] = Log2Q16(p) - Log2Q16(kTotal - p);
      loss0[p] = static_cast<std::int32_t>(
          -std::log2(static_cast<double>(kTotal - p) / kTotal) * 256.0 + 0.5);
      loss1[p] = static_cast<std::int32_t>(
          -std::log2(static_cast<double>(p) / kTotal) * 256.0 + 0.5);
    }
  }

  std::uint16_t Probability(std::int64_t target) const {
    const auto begin = logit.begin() + 1;
    const auto end = logit.end();
    const auto upper = std::lower_bound(begin, end, target);
    if (upper == begin) return 1;
    if (upper == end) return kTotal - 1;
    const std::uint16_t high =
        static_cast<std::uint16_t>(upper - logit.begin());
    const std::uint16_t low = high - 1;
    return target - logit[low] <= logit[high] - target ? low : high;
  }

  std::int32_t Loss(int bit, std::uint16_t p1) const {
    return bit ? loss1[p1] : loss0[p1];
  }

  std::array<std::int32_t, kTotal> logit{};
  std::array<std::int32_t, kTotal> loss0{};
  std::array<std::int32_t, kTotal> loss1{};
};

class RangeCounter {
 public:
  void Encode(int bit, std::uint16_t p1) {
    const std::uint32_t delta = high_ - low_;
    const std::uint32_t midpoint = low_ + (delta >> 16) * p1 +
        static_cast<std::uint32_t>(
            (static_cast<std::uint64_t>(delta & 0xffffu) * p1) >> 16);
    if (bit) high_ = midpoint;
    else low_ = midpoint + 1;
    while (((low_ ^ high_) & 0xff000000u) == 0) {
      ++bytes_;
      low_ <<= 8;
      high_ = (high_ << 8) + 255;
    }
  }

  void Finish() {
    while (((low_ ^ high_) & 0xff000000u) == 0) {
      ++bytes_;
      low_ <<= 8;
      high_ = (high_ << 8) + 255;
    }
    ++bytes_;
  }

  std::uint64_t bytes() const { return bytes_; }

 private:
  std::uint32_t low_ = 0;
  std::uint32_t high_ = kMaxCode;
  std::uint64_t bytes_ = 0;
};

class WrtPhaseNewtonResidual {
 public:
  WrtPhaseNewtonResidual(const Tables* tables, std::uint32_t prior)
      : tables_(tables), prior_curvature_(static_cast<std::uint64_t>(prior) *
            (kTotal / 4)) {
    for (std::size_t level = 0; level < kLevelSizes.size(); ++level) {
      gradients_[level].assign(kLevelSizes[level], 0);
      curvatures_[level].assign(kLevelSizes[level], 0);
    }
  }

  std::uint16_t Predict(std::uint16_t base) {
    const std::uint32_t bucket = Bucket(base);
    const std::uint32_t bit_position = row_ & 7;
    const std::uint32_t position = event_size_ * 8 + bit_position;
    indices_[0] = position * 128 + bucket;
    indices_[1] = (position * 4 + (current_byte_ & 3u)) * 128 + bucket;
    indices_[2] = (position * 16 + (current_byte_ & 15u)) * 128 + bucket;
    indices_[3] = (position * 256 + current_byte_) * 128 + bucket;

    std::int64_t correction_q16 = 0;
    for (std::size_t level = 0; level < kLevelSizes.size(); ++level) {
      const std::size_t index = indices_[level];
      const std::int64_t numerator = gradients_[level][index] * kTotal +
          correction_q16 * static_cast<std::int64_t>(prior_curvature_);
      const std::uint64_t denominator =
          curvatures_[level][index] + prior_curvature_;
      correction_q16 = numerator / static_cast<std::int64_t>(denominator);
    }
    base_ = base;
    // A quarter Newton step is fixed before evaluation to limit sparse-state
    // overshoot while still correcting in the proper log-loss geometry.
    predicted_ = tables_->Probability(
        static_cast<std::int64_t>(tables_->logit[base]) + correction_q16 / 4);
    return predicted_;
  }

  void Perceive(int bit) {
    const std::int64_t gradient =
        (bit ? static_cast<std::int64_t>(kTotal) : 0) - base_;
    const std::uint64_t curvature = std::max<std::uint64_t>(1,
        static_cast<std::uint64_t>(base_) * (kTotal - base_) / kTotal);
    for (std::size_t level = 0; level < kLevelSizes.size(); ++level) {
      const std::size_t index = indices_[level];
      gradients_[level][index] += gradient;
      const std::uint64_t old = curvatures_[level][index];
      curvatures_[level][index] =
          std::min<std::uint64_t>(std::numeric_limits<std::uint64_t>::max() -
                                      curvature,
                                  old) == old
              ? old + curvature
              : std::numeric_limits<std::uint64_t>::max();
    }
    current_byte_ = static_cast<unsigned char>((current_byte_ << 1) | bit);
    ++row_;
    if ((row_ & 7) == 0) {
      if (row_ / 8 > 6) ObserveByte(current_byte_);
      current_byte_ = 0;
    }
  }

  std::uint64_t StateBytes() const {
    std::uint64_t total = 0;
    for (const std::size_t size : kLevelSizes) total += size * 16;
    return total;
  }

 private:
  static unsigned char WrtTransform(unsigned char value) {
    if (value >= static_cast<unsigned char>('{') && value < 127) {
      value += static_cast<unsigned char>('P' - '{');
    } else if (value >= static_cast<unsigned char>('P') &&
               value < static_cast<unsigned char>('T')) {
      value -= static_cast<unsigned char>('P' - '{');
    } else if ((value >= ':' && value <= '?') ||
               (value >= 'J' && value <= 'O')) {
      value ^= 0x70;
    }
    if (value == 'X' || value == '`') {
      value ^= static_cast<unsigned char>('X' ^ '`');
    }
    return value;
  }

  static std::uint32_t Bucket(std::uint16_t base) {
    const bool upper = base >= 32768;
    const std::uint32_t distance = upper ? kTotal - base : base;
    unsigned int exponent = 0;
    for (std::uint32_t value = distance; value > 1; value >>= 1) ++exponent;
    const std::uint32_t normalized = distance << (15 - exponent);
    const std::uint32_t mantissa = (normalized >> 13) & 3u;
    return (upper ? 64u : 0u) + exponent * 4 + mantissa;
  }

  void ObserveByte(unsigned char value) {
    event_buffer_[event_size_++] = value;
    if (event_size_ == 1) {
      const unsigned char first = WrtTransform(event_buffer_[0]);
      expected_event_size_ = (first == 0x0c || first > 0xcf) ? 2 : 1;
    } else if (event_size_ == 2 && WrtTransform(event_buffer_[0]) > 0xcf &&
               WrtTransform(event_buffer_[1]) > 0xcf) {
      expected_event_size_ = 3;
    }
    if (expected_event_size_ && event_size_ == expected_event_size_) {
      event_size_ = 0;
      expected_event_size_ = 0;
    }
  }

  const Tables* tables_;
  const std::uint64_t prior_curvature_;
  std::array<std::vector<std::int64_t>, 4> gradients_;
  std::array<std::vector<std::uint64_t>, 4> curvatures_;
  std::array<std::size_t, 4> indices_{};
  std::array<unsigned char, 3> event_buffer_{};
  std::uint64_t row_ = 0;
  std::uint16_t base_ = 32768;
  std::uint16_t predicted_ = 32768;
  unsigned char current_byte_ = 0;
  unsigned int event_size_ = 0;
  unsigned int expected_event_size_ = 0;
};

struct Stats {
  std::int64_t train_qbits = 0;
  std::int64_t development_qbits = 0;
  std::int64_t holdout_qbits = 0;
  std::vector<std::int64_t> block_qbits;
  std::uint64_t active_rows = 0;
};

struct Args {
  std::string p1;
  std::string store;
  std::string output;
};

Args ParseArgs(int argc, char** argv) {
  Args args;
  for (int index = 1; index < argc; ++index) {
    const std::string key = argv[index];
    if (++index >= argc) throw std::runtime_error("missing value for " + key);
    const std::string value = argv[index];
    if (key == "--p1") args.p1 = value;
    else if (key == "--wrt-store") args.store = value;
    else if (key == "--output") args.output = value;
    else throw std::runtime_error("unknown option " + key);
  }
  if (args.p1.empty() || args.store.empty() || args.output.empty()) {
    throw std::runtime_error("--p1, --wrt-store, and --output are required");
  }
  return args;
}

std::string Values(const std::vector<std::int64_t>& values) {
  std::string output = "[";
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index) output += ", ";
    output += std::to_string(values[index]);
  }
  return output + "]";
}

void WriteStats(std::ofstream& output, std::uint32_t prior,
                const Stats& stats, const RangeCounter& coder,
                std::uint64_t baseline_bytes, std::uint64_t state_bytes,
                bool comma) {
  std::uint32_t positive = 0;
  std::uint32_t regressing = 0;
  for (const std::int64_t value : stats.block_qbits) {
    positive += value > 0;
    regressing += value < 0;
  }
  output << "    {\"variant_id\": \"newton_prior" << prior
         << "\", \"prior_observations\": " << prior
         << ", \"damping_numerator\": 1, \"damping_denominator\": 4"
         << ", \"state_bytes\": " << state_bytes
         << ", \"train_qbits\": " << stats.train_qbits
         << ", \"development_qbits\": " << stats.development_qbits
         << ", \"holdout_qbits\": " << stats.holdout_qbits
         << ", \"candidate_payload_bytes\": " << coder.bytes()
         << ", \"exact_saved_bytes\": "
         << static_cast<std::int64_t>(baseline_bytes) -
                static_cast<std::int64_t>(coder.bytes())
         << ", \"positive_blocks\": " << positive
         << ", \"regressing_blocks\": " << regressing
         << ", \"active_rows\": " << stats.active_rows
         << ", \"block_qbits\": " << Values(stats.block_qbits) << "}";
  if (comma) output << ',';
  output << '\n';
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const Args args = ParseArgs(argc, argv);
    const auto p1 = ReadFile(args.p1);
    const auto store = ReadFile(args.store);
    const std::array<unsigned char, 8> magic = {'C', 'M', 'X', '2', '1',
                                                'P', '1', 0};
    if (p1.size() < 16 ||
        !std::equal(magic.begin(), magic.end(), p1.begin())) {
      throw std::runtime_error("invalid P1 magic");
    }
    const std::uint64_t rows = ReadU64(p1.data() + 8);
    if (rows == 0 || p1.size() != 16 + rows * 2 || (rows & 7) != 0 ||
        store.size() != 5 + rows / 8) {
      throw std::runtime_error("P1/store dimensions differ");
    }
    const std::uint64_t train_end = rows / 3;
    const std::uint64_t holdout_start = rows * 2 / 3;
    const std::size_t blocks = (rows / 8 + kBlockBytes - 1) / kBlockBytes;
    Tables tables;
    std::array<WrtPhaseNewtonResidual, 3> candidates = {
        WrtPhaseNewtonResidual(&tables, kPriorObservations[0]),
        WrtPhaseNewtonResidual(&tables, kPriorObservations[1]),
        WrtPhaseNewtonResidual(&tables, kPriorObservations[2])};
    WrtPhaseResidual frozen;
    std::array<Stats, 5> stats;
    for (auto& score : stats) score.block_qbits.assign(blocks, 0);
    std::array<RangeCounter, 5> coders;
    RangeCounter baseline;

    for (std::uint64_t row = 0; row < rows; ++row) {
      const int bit = (store[5 + row / 8] >> (7 - (row & 7))) & 1;
      const unsigned char* record = p1.data() + 16 + row * 2;
      const std::uint16_t base = static_cast<std::uint16_t>(
          record[0] | (std::uint16_t{record[1]} << 8));
      if (base == 0) throw std::runtime_error("zero P1 probability");
      baseline.Encode(bit, base);
      const std::uint16_t frozen_p1 = frozen.Predict(base);
      std::array<std::uint16_t, 3> newton_p1{};
      for (std::size_t index = 0; index < candidates.size(); ++index) {
        const std::uint16_t predicted = candidates[index].Predict(base);
        newton_p1[index] = predicted;
        coders[index].Encode(bit, predicted);
        const std::int64_t gain =
            tables.Loss(bit, base) - tables.Loss(bit, predicted);
        if (row < train_end) stats[index].train_qbits += gain;
        else if (row < holdout_start) stats[index].development_qbits += gain;
        else stats[index].holdout_qbits += gain;
        stats[index].block_qbits[(row / 8) / kBlockBytes] += gain;
        stats[index].active_rows += predicted != base;
        candidates[index].Perceive(bit);
      }
      const std::array<std::uint16_t, 2> comparison = {
          frozen_p1,
          static_cast<std::uint16_t>((static_cast<std::uint32_t>(frozen_p1) +
                                      newton_p1[0]) /
                                     2)};
      for (std::size_t offset = 0; offset < comparison.size(); ++offset) {
        const std::size_t index = candidates.size() + offset;
        const std::uint16_t predicted = comparison[offset];
        coders[index].Encode(bit, predicted);
        const std::int64_t gain =
            tables.Loss(bit, base) - tables.Loss(bit, predicted);
        if (row < train_end) stats[index].train_qbits += gain;
        else if (row < holdout_start) stats[index].development_qbits += gain;
        else stats[index].holdout_qbits += gain;
        stats[index].block_qbits[(row / 8) / kBlockBytes] += gain;
        stats[index].active_rows += predicted != base;
      }
      frozen.Perceive(bit);
    }
    baseline.Finish();
    for (auto& coder : coders) coder.Finish();

    std::ofstream output(args.output);
    if (!output) throw std::runtime_error("cannot create " + args.output);
    output << "{\n  \"schema_version\": 1,\n"
           << "  \"receipt_type\": \"wrt_phase_newton_residual_screen\",\n"
           << "  \"evidence_level\": \"causal_exact_p1_shadow\",\n"
           << "  \"hypothesis\": \"Confidence-weighted logit Newton statistics retain more endpoint residual gain than probability-space averaging.\",\n"
           << "  \"claim_boundary\": \"Causal P1 replay only; native integration, source accounting, resources, and full-corpus proof remain required.\",\n"
           << "  \"causality\": {\"prediction_precedes_truth\": true, \"statistics_update_after_truth\": true, \"payload_bytes\": 0},\n"
           << "  \"selection_rule\": \"Highest development qbits; holdout is confirmation only.\",\n"
           << "  \"rows\": " << rows << ",\n"
           << "  \"baseline_payload_bytes\": " << baseline.bytes()
           << ",\n  \"variants\": [\n";
    for (std::size_t index = 0; index < candidates.size(); ++index) {
      WriteStats(output, kPriorObservations[index], stats[index], coders[index],
                 baseline.bytes(), candidates[index].StateBytes(),
                 true);
    }
    const auto write_comparison = [&](const char* name, std::size_t index,
                                      std::uint64_t state_bytes, bool comma) {
      std::uint32_t positive = 0;
      std::uint32_t regressing = 0;
      for (const std::int64_t value : stats[index].block_qbits) {
        positive += value > 0;
        regressing += value < 0;
      }
      output << "    {\"variant_id\": \"" << name
             << "\", \"state_bytes\": " << state_bytes
             << ", \"train_qbits\": " << stats[index].train_qbits
             << ", \"development_qbits\": "
             << stats[index].development_qbits
             << ", \"holdout_qbits\": " << stats[index].holdout_qbits
             << ", \"candidate_payload_bytes\": " << coders[index].bytes()
             << ", \"exact_saved_bytes\": "
             << static_cast<std::int64_t>(baseline.bytes()) -
                    static_cast<std::int64_t>(coders[index].bytes())
             << ", \"positive_blocks\": " << positive
             << ", \"regressing_blocks\": " << regressing
             << ", \"active_rows\": " << stats[index].active_rows
             << ", \"block_qbits\": " << Values(stats[index].block_qbits)
             << "}";
      if (comma) output << ',';
      output << '\n';
    };
    write_comparison("frozen_phase_control", 3, frozen.StateBytes(), true);
    write_comparison("equal_correction_blend", 4,
                     frozen.StateBytes() + candidates[0].StateBytes(), false);
    std::size_t selected = 0;
    for (std::size_t index = 1; index < candidates.size(); ++index) {
      if (stats[index].development_qbits > stats[selected].development_qbits) {
        selected = index;
      }
    }
    output << "  ],\n  \"selected_newton_variant\": \"newton_prior"
           << kPriorObservations[selected] << "\",\n"
           << "  \"promotion_authorized\": false\n}\n";
    if (!output) throw std::runtime_error("cannot write " + args.output);
    std::cout << "baseline_payload_bytes=" << baseline.bytes();
    for (std::size_t index = 0; index < candidates.size(); ++index) {
      std::cout << " prior" << kPriorObservations[index] << "_saved_bytes="
                << static_cast<std::int64_t>(baseline.bytes()) -
                       static_cast<std::int64_t>(coders[index].bytes());
    }
    std::cout << '\n';
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
