// Causal regret routing over scaled outputs from the frozen WRT phase residual.

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
constexpr std::array<int, 5> kStrengthNumerators = {0, 1, 2, 4, 8};
constexpr int kStrengthDenominator = 2;

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

class RangeCounter {
 public:
  void Encode(int bit, std::uint16_t p1) {
    const std::uint32_t delta = high_ - low_;
    const std::uint32_t midpoint =
        low_ + (delta >> 16) * p1 +
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

struct LossTables {
  LossTables() {
    for (std::uint32_t p = 1; p < kTotal; ++p) {
      loss0[p] = static_cast<std::int32_t>(
          -std::log2(static_cast<double>(kTotal - p) / kTotal) * 256.0 +
          0.5);
      loss1[p] = static_cast<std::int32_t>(
          -std::log2(static_cast<double>(p) / kTotal) * 256.0 + 0.5);
    }
  }

  std::int32_t Loss(int bit, std::uint16_t p1) const {
    return bit ? loss1[p1] : loss0[p1];
  }

  std::array<std::int32_t, kTotal> loss0{};
  std::array<std::int32_t, kTotal> loss1{};
};

unsigned int ByteClass(unsigned char value) {
  if (value >= 'a' && value <= 'z') return 0;
  if (value >= 'A' && value <= 'Z') return 1;
  if (value >= '0' && value <= '9') return 2;
  if (value == ' ' || value == '\n' || value == '\t') return 3;
  if (value == '<' || value == '>' || value == '{' || value == '}' ||
      value == '[' || value == ']' || value == '|' || value == '=') return 4;
  if (value >= 128) return 5;
  if (value == '/' || value == ':' || value == '&' || value == ';' ||
      value == '_' || value == '-') return 6;
  return 7;
}

unsigned int ConfidenceBin(std::uint16_t base) {
  const unsigned int distance =
      base > 32768 ? base - 32768 : 32768 - base;
  if (distance < 4096) return 0;
  if (distance < 12288) return 1;
  if (distance < 24576) return 2;
  return 3;
}

unsigned int CorrectionBin(std::uint16_t base, std::uint16_t phase) {
  const int difference = static_cast<int>(phase) - base;
  const unsigned int magnitude = static_cast<unsigned int>(
      difference < 0 ? -difference : difference);
  unsigned int bucket = 0;
  if (magnitude >= 64) bucket = 1;
  if (magnitude >= 256) bucket = 2;
  if (magnitude >= 1024) bucket = 3;
  return bucket * 2 + (difference < 0);
}

std::int64_t ShiftTowardZero(std::int64_t value, unsigned int shift) {
  return value >= 0 ? value >> shift : -((-value) >> shift);
}

class StrengthRouter {
 public:
  StrengthRouter(bool contextual, const LossTables* losses)
      : contextual_(contextual), losses_(losses), context_count_(contextual ? 2048 : 1),
        regrets_(context_count_), seen_(context_count_, 0) {}

  std::uint16_t Predict(std::uint16_t base, std::uint16_t phase,
                        std::uint64_t row, unsigned char previous_byte) {
    base_ = base;
    const std::int64_t correction = static_cast<std::int64_t>(phase) - base;
    for (std::size_t index = 0; index < candidates_.size(); ++index) {
      const std::int64_t scaled = correction * kStrengthNumerators[index] /
                                  kStrengthDenominator;
      candidates_[index] = static_cast<std::uint16_t>(
          std::max<std::int64_t>(1, std::min<std::int64_t>(
              kTotal - 1, static_cast<std::int64_t>(base) + scaled)));
    }
    context_ = 0;
    if (contextual_) {
      context_ = (((ByteClass(previous_byte) * 8 + (row & 7)) * 4 +
                   ConfidenceBin(base)) * 8) + CorrectionBin(base, phase);
    }
    selected_ = 2;
    if (seen_[context_] >= 64) {
      for (std::size_t index = 0; index < candidates_.size(); ++index) {
        if (regrets_[context_][index] < regrets_[context_][selected_]) {
          selected_ = index;
        }
      }
    }
    return candidates_[selected_];
  }

  void Update(int bit) {
    const std::int32_t base_loss = losses_->Loss(bit, base_);
    for (std::size_t index = 0; index < candidates_.size(); ++index) {
      regrets_[context_][index] +=
          losses_->Loss(bit, candidates_[index]) - base_loss;
    }
    if ((++seen_[context_] & 4095u) == 0) {
      for (auto& regret : regrets_[context_]) {
        regret -= ShiftTowardZero(regret, 1);
      }
    }
  }

  std::uint64_t StateBytes() const {
    return context_count_ * (sizeof(regrets_[0]) + sizeof(seen_[0]));
  }

 private:
  bool contextual_;
  const LossTables* losses_;
  std::size_t context_count_;
  std::vector<std::array<std::int64_t, 5>> regrets_;
  std::vector<std::uint32_t> seen_;
  std::array<std::uint16_t, 5> candidates_{};
  std::size_t context_ = 0;
  std::size_t selected_ = 2;
  std::uint16_t base_ = 32768;
};

class ShellRegimeResidual {
 public:
  ShellRegimeResidual() {
    counts_[0].assign(256 * 8 * 128, 0);
    sums_[0].assign(256 * 8 * 128, 0);
    counts_[1].assign(256 * 8 * 8 * 128, 0);
    sums_[1].assign(256 * 8 * 8 * 128, 0);
  }

  std::uint16_t Predict(std::uint16_t phase, unsigned char regime,
                        unsigned int bit_position, unsigned int prefix) {
    const std::uint32_t bucket = Bucket(phase);
    indices_[0] = ((static_cast<std::size_t>(regime) * 8 + bit_position) *
                   128) + bucket;
    indices_[1] = (((static_cast<std::size_t>(regime) * 8 + bit_position) *
                    8 + (prefix & 7u)) * 128) + bucket;
    std::int64_t posterior = 0;
    for (std::size_t level = 0; level < counts_.size(); ++level) {
      const std::size_t index = indices_[level];
      posterior = (sums_[level][index] + 256 * posterior) /
                  static_cast<std::int64_t>(counts_[level][index] + 256);
    }
    base_ = phase;
    const std::int64_t correction = posterior / 4;
    predicted_ = static_cast<std::uint16_t>(std::max<std::int64_t>(
        1, std::min<std::int64_t>(kTotal - 1,
                                  static_cast<std::int64_t>(phase) +
                                      correction)));
    return predicted_;
  }

  void Update(int bit) {
    const std::int64_t residual =
        (bit ? static_cast<std::int64_t>(kTotal) : 0) - base_;
    for (std::size_t level = 0; level < counts_.size(); ++level) {
      const std::size_t index = indices_[level];
      if (counts_[level][index] != std::numeric_limits<std::uint32_t>::max()) {
        ++counts_[level][index];
      }
      sums_[level][index] += residual;
    }
  }

  std::uint64_t StateBytes() const {
    std::uint64_t total = 0;
    for (const auto& level : counts_) total += level.size() * 12;
    return total;
  }

 private:
  static std::uint32_t Bucket(std::uint16_t probability) {
    const bool upper = probability >= 32768;
    const std::uint32_t distance =
        upper ? kTotal - probability : probability;
    unsigned int exponent = 0;
    for (std::uint32_t value = distance; value > 1; value >>= 1) ++exponent;
    const std::uint32_t normalized = distance << (15 - exponent);
    const std::uint32_t mantissa = (normalized >> 13) & 3u;
    return (upper ? 64u : 0u) + exponent * 4 + mantissa;
  }

  std::array<std::vector<std::uint32_t>, 2> counts_;
  std::array<std::vector<std::int64_t>, 2> sums_;
  std::array<std::size_t, 2> indices_{};
  std::uint16_t base_ = 32768;
  std::uint16_t predicted_ = 32768;
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
  std::string regime;
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
    else if (key == "--regime") args.regime = value;
    else if (key == "--output") args.output = value;
    else throw std::runtime_error("unknown option " + key);
  }
  if (args.p1.empty() || args.store.empty() || args.regime.empty() ||
      args.output.empty()) {
    throw std::runtime_error(
        "--p1, --wrt-store, --regime, and --output are required");
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

void WriteStats(std::ofstream& output, const char* name, const Stats& stats,
                const RangeCounter& coder, std::uint64_t baseline_bytes,
                std::uint64_t state_bytes, bool comma) {
  std::uint32_t positive = 0;
  std::uint32_t regressing = 0;
  for (const std::int64_t value : stats.block_qbits) {
    positive += value > 0;
    regressing += value < 0;
  }
  output << "    {\"variant_id\": \"" << name
         << "\", \"state_bytes\": " << state_bytes
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
    const auto regime = ReadFile(args.regime);
    const std::array<unsigned char, 8> magic = {'C', 'M', 'X', '2', '1',
                                                'P', '1', 0};
    if (p1.size() < 16 ||
        !std::equal(magic.begin(), magic.end(), p1.begin())) {
      throw std::runtime_error("invalid P1 magic");
    }
    const std::uint64_t rows = ReadU64(p1.data() + 8);
    if (rows == 0 || p1.size() != 16 + rows * 2 || (rows & 7) != 0 ||
        store.size() != 5 + rows / 8 || regime.size() != rows) {
      throw std::runtime_error("P1/store dimensions differ");
    }
    const std::uint64_t train_end = rows / 3;
    const std::uint64_t holdout_start = rows * 2 / 3;
    const std::size_t blocks =
        (rows / 8 + kBlockBytes - 1) / kBlockBytes;
    LossTables losses;
    WrtPhaseResidual phase;
    StrengthRouter global(false, &losses);
    StrengthRouter contextual(true, &losses);
    ShellRegimeResidual shell_regime;
    std::array<Stats, 4> stats;
    for (auto& score : stats) score.block_qbits.assign(blocks, 0);
    std::array<RangeCounter, 4> coders;
    RangeCounter baseline;
    unsigned char previous_byte = 0;
    unsigned int current_prefix = 0;

    for (std::uint64_t row = 0; row < rows; ++row) {
      const unsigned char truth_byte = store[5 + row / 8];
      const int bit = (truth_byte >> (7 - (row & 7))) & 1;
      const unsigned char* record = p1.data() + 16 + row * 2;
      const std::uint16_t base = static_cast<std::uint16_t>(
          record[0] | (std::uint16_t{record[1]} << 8));
      if (base == 0) throw std::runtime_error("zero P1 probability");
      const std::uint16_t phase_p1 = phase.Predict(base);
      const std::array<std::uint16_t, 4> candidates = {
          phase_p1, global.Predict(base, phase_p1, row, previous_byte),
          contextual.Predict(base, phase_p1, row, previous_byte),
          shell_regime.Predict(phase_p1, regime[row], row & 7,
                               current_prefix)};
      baseline.Encode(bit, base);
      for (std::size_t index = 0; index < candidates.size(); ++index) {
        coders[index].Encode(bit, candidates[index]);
        const std::int64_t gain =
            losses.Loss(bit, base) - losses.Loss(bit, candidates[index]);
        if (row < train_end) stats[index].train_qbits += gain;
        else if (row < holdout_start) stats[index].development_qbits += gain;
        else stats[index].holdout_qbits += gain;
        stats[index].block_qbits[(row / 8) / kBlockBytes] += gain;
        stats[index].active_rows += candidates[index] != base;
      }
      phase.Perceive(bit);
      global.Update(bit);
      contextual.Update(bit);
      shell_regime.Update(bit);
      current_prefix = ((current_prefix << 1) | bit) & 0xffu;
      if ((row & 7) == 7) {
        previous_byte = truth_byte;
        current_prefix = 0;
      }
    }
    baseline.Finish();
    for (auto& coder : coders) coder.Finish();

    std::ofstream output(args.output);
    if (!output) throw std::runtime_error("cannot create " + args.output);
    output << "{\n  \"schema_version\": 1,\n"
           << "  \"receipt_type\": \"wrt_phase_strength_router_screen\",\n"
           << "  \"evidence_level\": \"causal_exact_p1_shadow\",\n"
           << "  \"claim_boundary\": \"Causal P1 replay only; native integration, source accounting, resources, and full-corpus proof remain required.\",\n"
           << "  \"causality\": {\"prediction_precedes_truth\": true, \"regret_updates_after_truth\": true, \"payload_bytes\": 0},\n"
           << "  \"strength_multipliers\": [0.0, 0.5, 1.0, 2.0, 4.0],\n"
           << "  \"rows\": " << rows << ",\n"
           << "  \"baseline_payload_bytes\": " << baseline.bytes()
           << ",\n  \"variants\": [\n";
    WriteStats(output, "frozen_phase", stats[0], coders[0], baseline.bytes(),
               phase.StateBytes(), true);
    WriteStats(output, "global_strength_regret", stats[1], coders[1],
               baseline.bytes(), phase.StateBytes() + global.StateBytes(), true);
    WriteStats(output, "contextual_strength_regret", stats[2], coders[2],
               baseline.bytes(), phase.StateBytes() + contextual.StateBytes(), true);
    WriteStats(output, "shell_regime_after_phase", stats[3], coders[3],
               baseline.bytes(), phase.StateBytes() + shell_regime.StateBytes(),
               false);
    output << "  ],\n  \"promotion_authorized\": false\n}\n";
    if (!output) throw std::runtime_error("cannot write " + args.output);
    std::cout << "baseline_payload_bytes=" << baseline.bytes()
              << " phase_saved_bytes="
              << static_cast<std::int64_t>(baseline.bytes()) -
                     static_cast<std::int64_t>(coders[0].bytes())
              << " global_saved_bytes="
              << static_cast<std::int64_t>(baseline.bytes()) -
                     static_cast<std::int64_t>(coders[1].bytes())
              << " contextual_saved_bytes="
              << static_cast<std::int64_t>(baseline.bytes()) -
                     static_cast<std::int64_t>(coders[2].bytes())
              << " shell_regime_saved_bytes="
              << static_cast<std::int64_t>(baseline.bytes()) -
                     static_cast<std::int64_t>(coders[3].bytes()) << '\n';
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
