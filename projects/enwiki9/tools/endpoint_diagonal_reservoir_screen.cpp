// Fixed-point diagonal reservoir residual endpoint over a causal P1 stream.

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr std::uint32_t kTotal = 65536;
constexpr std::int64_t kWeightScale = std::int64_t{1} << 20;
constexpr std::uint32_t kMaxCode = 0xffffffffu;
constexpr std::uint64_t kBlockBytes = 65536;

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

std::int64_t ShiftTowardZero(std::int64_t value, unsigned int shift) {
  return value >= 0 ? value >> shift : -((-value) >> shift);
}

std::int64_t DivideRoundNearest(std::int64_t value, std::int64_t divisor) {
  return value >= 0 ? (value + divisor / 2) / divisor
                    : -((-value + divisor / 2) / divisor);
}

std::uint64_t Mix64(std::uint64_t value) {
  value ^= value >> 30;
  value *= 0xbf58476d1ce4e5b9ULL;
  value ^= value >> 27;
  value *= 0x94d049bb133111ebULL;
  return value ^ (value >> 31);
}

std::int32_t Log2Q16(std::uint32_t value) {
  if (value == 0) throw std::runtime_error("log2 input is zero");
  unsigned int integer = 0;
  for (std::uint32_t copy = value; copy >>= 1;) ++integer;
  std::uint64_t normalized = static_cast<std::uint64_t>(value) << (31 - integer);
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
    for (std::uint32_t p = 1; p < kTotal; ++p) {
      if (Probability(logit[p]) != p) {
        throw std::runtime_error("native logit inverse self-check failed");
      }
    }
  }

  std::uint16_t Probability(std::int64_t target) const {
    const auto begin = logit.begin() + 1;
    const auto high_it = std::lower_bound(begin, logit.end(), target);
    if (high_it == begin) return 1;
    if (high_it == logit.end()) return kTotal - 1;
    const std::uint16_t high =
        static_cast<std::uint16_t>(high_it - logit.begin());
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

struct Config {
  unsigned int cells;
  unsigned int update_shift;
  std::string Name() const {
    return "c" + std::to_string(cells) + "_u" +
        std::to_string(update_shift);
  }
};

struct Stats {
  std::int64_t train_qbits = 0;
  std::int64_t development_qbits = 0;
  std::int64_t holdout_qbits = 0;
  std::vector<std::int64_t> block_qbits;
};

class DiagonalReservoir {
 public:
  DiagonalReservoir(Config config, const Tables& tables)
      : config_(config), tables_(tables), state_(config.cells, 0),
        features_(config.cells + 1, 0), weights_(32 * (config.cells + 1), 0) {
    features_.back() = 65536;
  }

  std::uint16_t Predict(std::uint16_t base, unsigned int bit_position) {
    base_ = base;
    const unsigned int confidence = ConfidenceBin(base);
    context_ = bit_position * 4 + confidence;
    std::int64_t correction = 0;
    const std::size_t offset = context_ * features_.size();
    for (unsigned int cell = 0; cell < state_.size(); ++cell) {
      features_[cell] = state_[cell];
      correction += static_cast<std::int64_t>(weights_[offset + cell]) *
          features_[cell];
    }
    correction += static_cast<std::int64_t>(weights_[offset + state_.size()]) *
        features_.back();
    predicted_ = tables_.Probability(tables_.logit[base] +
        DivideRoundNearest(correction, kWeightScale));
    return predicted_;
  }

  void Perceive(int bit) {
    const std::int64_t error =
        (bit ? static_cast<std::int64_t>(kTotal) : 0) - predicted_;
    const std::size_t offset = context_ * features_.size();
    for (unsigned int feature = 0; feature < features_.size(); ++feature) {
      const std::int64_t step =
          ShiftTowardZero(error * features_[feature], config_.update_shift);
      if (config_.update_shift == 44 && step != 0) {
        throw std::runtime_error("zero-rate control produced a nonzero update");
      }
      std::int64_t updated = weights_[offset + feature] + step;
      weights_[offset + feature] = static_cast<std::int32_t>(
          std::max<std::int64_t>(-kWeightScale,
              std::min<std::int64_t>(kWeightScale, updated)));
    }
  }

  void ObserveByte(unsigned char value) {
    static constexpr std::array<std::uint32_t, 8> leak = {
        32768, 49152, 57344, 61440, 63488, 64512, 65024, 65280};
    for (unsigned int cell = 0; cell < state_.size(); ++cell) {
      const std::uint32_t retain = leak[cell & 7];
      const std::int32_t target =
          (Mix64((static_cast<std::uint64_t>(value) << 32) ^
                 (0x9e3779b97f4a7c15ULL * (cell + 1))) & 1)
              ? 65536
              : -65536;
      const std::int64_t delta =
          static_cast<std::int64_t>(target) - state_[cell];
      state_[cell] += static_cast<std::int32_t>(
          ShiftTowardZero(delta * (65536 - retain), 16));
    }
  }

  std::uint64_t StateBytes() const {
    return (state_.size() + features_.size() + weights_.size()) * 4;
  }

  std::int32_t MaxAbsoluteWeight() const {
    std::int32_t result = 0;
    for (const auto weight : weights_) {
      result = std::max(result, static_cast<std::int32_t>(
          std::min<std::int64_t>(std::abs(static_cast<std::int64_t>(weight)),
                                 0x7fffffff)));
    }
    return result;
  }

 private:
  static unsigned int ConfidenceBin(std::uint16_t base) {
    const unsigned int distance =
        base > 32768 ? base - 32768 : 32768 - base;
    if (distance < 4096) return 0;
    if (distance < 12288) return 1;
    if (distance < 24576) return 2;
    return 3;
  }

  Config config_;
  const Tables& tables_;
  std::vector<std::int32_t> state_;
  std::vector<std::int32_t> features_;
  std::vector<std::int32_t> weights_;
  unsigned int context_ = 0;
  std::uint16_t base_ = 32768;
  std::uint16_t predicted_ = 32768;
};

struct Args {
  std::string p1;
  std::string pair_trace;
  unsigned int pair_endpoint = 0;
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
    else if (key == "--pair-trace") args.pair_trace = value;
    else if (key == "--pair-endpoint") {
      args.pair_endpoint = static_cast<unsigned int>(std::stoul(value));
    }
    else if (key == "--wrt-store") args.store = value;
    else if (key == "--output") args.output = value;
    else throw std::runtime_error("unknown option " + key);
  }
  if ((args.p1.empty() == args.pair_trace.empty()) || args.store.empty() ||
      args.output.empty() || args.pair_endpoint > 1) {
    throw std::runtime_error(
        "exactly one of --p1 or --pair-trace, a --pair-endpoint in 0..1, "
        "--wrt-store, and --output are required");
  }
  return args;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const Args args = ParseArgs(argc, argv);
    const auto base_trace = ReadFile(
        args.p1.empty() ? args.pair_trace : args.p1);
    const auto store = ReadFile(args.store);
    const std::array<unsigned char, 8> p1_magic = {
        'C', 'M', 'X', '2', '1', 'P', '1', 0};
    const std::array<unsigned char, 8> pair_magic = {
        'C', 'M', 'X', 'A', 'U', 'X', '1', 0};
    const bool use_pair = !args.pair_trace.empty();
    const auto& expected_magic = use_pair ? pair_magic : p1_magic;
    if (base_trace.size() < 16 || !std::equal(expected_magic.begin(),
                                               expected_magic.end(),
                                               base_trace.begin())) {
      throw std::runtime_error(use_pair ? "invalid pair-trace magic"
                                        : "invalid P1 magic");
    }
    const std::uint64_t rows = ReadU64(base_trace.data() + 8);
    const std::uint64_t record_bytes = use_pair ? 4 : 2;
    if (rows == 0 || (rows & 7) != 0 ||
        base_trace.size() != 16 + rows * record_bytes ||
        store.size() != 5 + rows / 8) {
      throw std::runtime_error("base trace/store dimensions differ");
    }

    const std::vector<Config> configs = {
        {8, 25}, {8, 26}, {8, 27}, {8, 28}, {8, 29}, {8, 30}, {8, 44},
        {16, 25}, {16, 26}, {16, 27}, {16, 28}, {16, 29}, {16, 30}, {16, 44},
        {32, 25}, {32, 26}, {32, 27}, {32, 28}, {32, 29}, {32, 30}, {32, 44},
        {64, 25}, {64, 26}, {64, 27}, {64, 28}, {64, 29}, {64, 30}, {64, 44},
        {128, 25}, {128, 26}, {128, 27}, {128, 28}, {128, 29}, {128, 30},
        {128, 44}};
    Tables tables;
    std::vector<DiagonalReservoir> models;
    models.reserve(configs.size());
    for (const auto& config : configs) models.emplace_back(config, tables);
    std::vector<Stats> stats(configs.size());
    const std::size_t blocks = (rows / 8 + kBlockBytes - 1) / kBlockBytes;
    for (auto& score : stats) score.block_qbits.assign(blocks, 0);
    std::vector<RangeCounter> coders(configs.size());
    RangeCounter baseline;
    const std::uint64_t train_end = rows * 3 / 5;
    const std::uint64_t holdout_start = rows * 4 / 5;

    for (std::uint64_t row = 0; row < rows; ++row) {
      const unsigned char* record = base_trace.data() + 16 +
          row * record_bytes + (use_pair ? args.pair_endpoint * 2 : 0);
      const std::uint16_t base =
          static_cast<std::uint16_t>(record[0] | (record[1] << 8));
      if (base == 0) throw std::runtime_error("zero P1 probability");
      const unsigned char truth_byte = store[5 + row / 8];
      const int bit = (truth_byte >> (7 - (row & 7))) & 1;
      baseline.Encode(bit, base);
      for (std::size_t index = 0; index < models.size(); ++index) {
        const std::uint16_t candidate =
            models[index].Predict(base, row & 7);
        coders[index].Encode(bit, candidate);
        const std::int64_t gain =
            tables.Loss(bit, base) - tables.Loss(bit, candidate);
        if (row < train_end) stats[index].train_qbits += gain;
        else if (row < holdout_start) stats[index].development_qbits += gain;
        else stats[index].holdout_qbits += gain;
        stats[index].block_qbits[(row / 8) / kBlockBytes] += gain;
        models[index].Perceive(bit);
      }
      if ((row & 7) == 7) {
        for (auto& model : models) model.ObserveByte(truth_byte);
      }
    }
    baseline.Finish();
    for (auto& coder : coders) coder.Finish();

    std::size_t best = 0;
    for (std::size_t index = 1; index < configs.size(); ++index) {
      if (stats[index].development_qbits > stats[best].development_qbits ||
          (stats[index].development_qbits == stats[best].development_qbits &&
           configs[index].Name() < configs[best].Name())) {
        best = index;
      }
    }

    std::ofstream out(args.output);
    if (!out) throw std::runtime_error("cannot create " + args.output);
    out << "{\n  \"schema_version\": 1,\n"
        << "  \"receipt_type\": \"endpoint_diagonal_reservoir_screen\",\n"
        << "  \"evidence_level\": \"causal_endpoint428_probability_shadow\",\n"
        << "  \"rows\": " << rows << ",\n"
        << "  \"raw_bytes\": " << rows / 8 << ",\n"
        << "  \"base_trace_kind\": \""
        << (use_pair ? "same_execution_pair_endpoint" : "p1") << "\",\n"
        << "  \"pair_endpoint\": "
        << (use_pair ? std::to_string(args.pair_endpoint) : "null") << ",\n"
        << "  \"selection_reads_holdout\": false,\n"
        << "  \"baseline_payload_bytes\": " << baseline.bytes() << ",\n"
        << "  \"best_variant_id\": \"" << configs[best].Name() << "\",\n"
        << "  \"variants\": [\n";
    for (std::size_t index = 0; index < configs.size(); ++index) {
      unsigned int positive = 0;
      unsigned int regressing = 0;
      for (const auto value : stats[index].block_qbits) {
        positive += value > 0;
        regressing += value < 0;
      }
      out << "    {\"variant_id\": \"" << configs[index].Name()
          << "\", \"cells\": " << configs[index].cells
          << ", \"update_shift\": " << configs[index].update_shift
          << ", \"state_bytes\": " << models[index].StateBytes()
          << ", \"max_absolute_weight\": "
          << models[index].MaxAbsoluteWeight()
          << ", \"train_qbits\": " << stats[index].train_qbits
          << ", \"development_qbits\": "
          << stats[index].development_qbits
          << ", \"holdout_qbits\": " << stats[index].holdout_qbits
          << ", \"exact_saved_bytes\": "
          << static_cast<std::int64_t>(baseline.bytes()) -
                 static_cast<std::int64_t>(coders[index].bytes())
          << ", \"candidate_payload_bytes\": " << coders[index].bytes()
          << ", \"positive_blocks\": " << positive
          << ", \"regressing_blocks\": " << regressing << "}";
      if (index + 1 != configs.size()) out << ',';
      out << '\n';
    }
    out << "  ],\n  \"promotion_authorized\": false,\n"
        << "  \"claim_boundary\": \"Causal exact-coder shadow only; source cost, native integration, disjoint transfer, resources, and full-corpus proof remain required.\"\n}\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
