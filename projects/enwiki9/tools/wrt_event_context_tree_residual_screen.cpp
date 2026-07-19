// Causal residual context tree over completed WRT events and an exact P1 stream.

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr std::uint32_t kTotal = 65536;
constexpr std::uint32_t kMaxCode = 0xffffffffu;
constexpr std::uint64_t kBlockBytes = 65536;
constexpr unsigned int kHashBits = 19;
constexpr std::uint32_t kPrior = 256;
constexpr std::uint32_t kStrengthPpm = 250000;

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

std::uint64_t Mix64(std::uint64_t value) {
  value ^= value >> 30;
  value *= 0xbf58476d1ce4e5b9ULL;
  value ^= value >> 27;
  value *= 0x94d049bb133111ebULL;
  return value ^ (value >> 31);
}

std::uint64_t Combine(std::uint64_t left, std::uint64_t right) {
  return Mix64(left ^ (right + 0x9e3779b97f4a7c15ULL + (left << 6) +
                       (left >> 2)));
}

unsigned char WrtTransform(unsigned char value) {
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

struct EventState {
  std::vector<unsigned char> current;
  std::array<std::uint64_t, 2> history{};
  std::size_t expected = 0;

  std::uint32_t ByteIndex() const {
    return static_cast<std::uint32_t>(current.size());
  }

  std::uint64_t LastEvent() const { return history[0]; }
  std::uint64_t LastTwoEvents() const {
    return Combine(history[1], history[0]);
  }

  void ObserveByte(unsigned char value) {
    current.push_back(value);
    if (current.size() == 1) {
      const unsigned char first = WrtTransform(current[0]);
      expected = (first == 0x0c || first > 0xcf) ? 2 : 1;
    } else if (current.size() == 2 && WrtTransform(current[0]) > 0xcf &&
               WrtTransform(current[1]) > 0xcf) {
      expected = 3;
    }
    if (expected == 0 || current.size() != expected) return;
    std::uint64_t hash = 0xcbf29ce484222325ULL;
    for (const unsigned char byte : current) {
      hash ^= byte;
      hash *= 0x100000001b3ULL;
    }
    history[1] = history[0];
    history[0] = Mix64(hash ^ current.size());
    current.clear();
    expected = 0;
  }
};

class ResidualTree {
 public:
  explicit ResidualTree(bool event_context)
      : event_context_(event_context), level_count_(event_context ? 5 : 3) {
    for (std::size_t level = 0; level < level_count_; ++level) {
      counts_[level].assign(std::size_t{1} << kHashBits, 0);
      sums_[level].assign(std::size_t{1} << kHashBits, 0);
    }
  }

  std::uint16_t Predict(std::uint16_t base, const EventState& event,
                        unsigned int bit_position, unsigned int byte_prefix) {
    const std::uint32_t bucket = LogBucket(base);
    const std::uint32_t position = event.ByteIndex() * 8 + bit_position;
    const std::uint64_t phase =
        (static_cast<std::uint64_t>(position) << 16) |
        (static_cast<std::uint64_t>(byte_prefix) << 8) | bucket;
    keys_[0] = Mix64(0x10ULL ^ (static_cast<std::uint64_t>(position) << 8) ^
                     bucket);
    keys_[1] = Mix64(0x20ULL ^
                     (static_cast<std::uint64_t>(position) << 10) ^
                     (static_cast<std::uint64_t>(byte_prefix & 3u) << 8) ^
                     bucket);
    keys_[2] = Mix64(0x30ULL ^
                     (static_cast<std::uint64_t>(position) << 12) ^
                     (static_cast<std::uint64_t>(byte_prefix & 15u) << 8) ^
                     bucket);
    if (event_context_) {
      keys_[3] = Combine(event.LastEvent(), 0x40ULL ^ phase);
      keys_[4] = Combine(event.LastTwoEvents(), 0x50ULL ^ phase);
    }

    std::int64_t posterior = 0;
    for (std::size_t level = 0; level < level_count_; ++level) {
      indices_[level] = static_cast<std::size_t>(keys_[level]) &
                        ((std::size_t{1} << kHashBits) - 1);
      const std::size_t index = indices_[level];
      posterior = (sums_[level][index] +
                   static_cast<std::int64_t>(kPrior) * posterior) /
                  static_cast<std::int64_t>(counts_[level][index] + kPrior);
    }
    base_ = base;
    const std::int64_t correction = posterior * kStrengthPpm / 1000000;
    predicted_ = static_cast<std::uint16_t>(std::max<std::int64_t>(
        1, std::min<std::int64_t>(kTotal - 1,
                                  static_cast<std::int64_t>(base) +
                                      correction)));
    return predicted_;
  }

  void Update(int bit) {
    const std::int64_t residual =
        (bit ? static_cast<std::int64_t>(kTotal) : 0) - base_;
    for (std::size_t level = 0; level < level_count_; ++level) {
      const std::size_t index = indices_[level];
      if (counts_[level][index] != std::numeric_limits<std::uint32_t>::max()) {
        ++counts_[level][index];
      }
      sums_[level][index] += residual;
    }
  }

  std::uint64_t StateBytes() const {
    return level_count_ * (std::uint64_t{1} << kHashBits) * 12;
  }

 private:
  static std::uint32_t LogBucket(std::uint16_t base) {
    const bool upper = base >= 32768;
    std::uint32_t distance = upper ? kTotal - base : base;
    unsigned int exponent = 0;
    for (std::uint32_t value = distance; value > 1; value >>= 1) ++exponent;
    const std::uint32_t normalized = distance << (15 - exponent);
    const std::uint32_t mantissa = (normalized >> 13) & 3u;
    return (upper ? 64u : 0u) + exponent * 4 + mantissa;
  }

  bool event_context_;
  std::size_t level_count_;
  std::array<std::vector<std::uint32_t>, 5> counts_;
  std::array<std::vector<std::int64_t>, 5> sums_;
  std::array<std::uint64_t, 5> keys_{};
  std::array<std::size_t, 5> indices_{};
  std::uint16_t base_ = 32768;
  std::uint16_t predicted_ = 32768;
};

class AdaptiveResidualTree {
 public:
  explicit AdaptiveResidualTree(unsigned int decay_shift)
      : decay_shift_(decay_shift) {
    for (std::size_t level = 0; level < kLevelCount; ++level) {
      seen_[level].assign(std::size_t{1} << kHashBits, 0);
      means_[level].assign(std::size_t{1} << kHashBits, 0);
    }
  }

  std::uint16_t Predict(std::uint16_t base, const EventState& event,
                        unsigned int bit_position, unsigned int byte_prefix) {
    const std::uint32_t bucket = LogBucket(base);
    const std::uint32_t position = event.ByteIndex() * 8 + bit_position;
    keys_[0] = Mix64(0x60ULL ^ (static_cast<std::uint64_t>(position) << 8) ^
                     bucket);
    keys_[1] = Mix64(0x70ULL ^
                     (static_cast<std::uint64_t>(position) << 10) ^
                     (static_cast<std::uint64_t>(byte_prefix & 3u) << 8) ^
                     bucket);
    keys_[2] = Mix64(0x80ULL ^
                     (static_cast<std::uint64_t>(position) << 12) ^
                     (static_cast<std::uint64_t>(byte_prefix & 15u) << 8) ^
                     bucket);
    keys_[3] = Mix64(0x90ULL ^
                     (static_cast<std::uint64_t>(position) << 16) ^
                     (static_cast<std::uint64_t>(byte_prefix) << 8) ^ bucket);

    std::int64_t posterior = 0;
    for (std::size_t level = 0; level < kLevelCount; ++level) {
      indices_[level] = static_cast<std::size_t>(keys_[level]) &
                        ((std::size_t{1} << kHashBits) - 1);
      const std::size_t index = indices_[level];
      const std::uint32_t support = std::min<std::uint32_t>(seen_[level][index],
                                                            4096);
      posterior =
          (static_cast<std::int64_t>(support) * means_[level][index] +
           static_cast<std::int64_t>(kPrior) * posterior) /
          static_cast<std::int64_t>(support + kPrior);
    }
    base_ = base;
    const std::int64_t correction = posterior * kStrengthPpm / 1000000;
    predicted_ = static_cast<std::uint16_t>(std::max<std::int64_t>(
        1, std::min<std::int64_t>(kTotal - 1,
                                  static_cast<std::int64_t>(base) +
                                      correction)));
    return predicted_;
  }

  void Update(int bit) {
    const std::int64_t residual =
        (bit ? static_cast<std::int64_t>(kTotal) : 0) - base_;
    for (std::size_t level = 0; level < kLevelCount; ++level) {
      const std::size_t index = indices_[level];
      std::int64_t delta = residual - means_[level][index];
      const std::int64_t adjustment =
          delta >= 0 ? delta >> decay_shift_ : -((-delta) >> decay_shift_);
      means_[level][index] = static_cast<std::int32_t>(
          static_cast<std::int64_t>(means_[level][index]) + adjustment);
      if (seen_[level][index] != std::numeric_limits<std::uint32_t>::max()) {
        ++seen_[level][index];
      }
    }
  }

  std::uint64_t StateBytes() const {
    return kLevelCount * (std::uint64_t{1} << kHashBits) * 8;
  }

 private:
  static std::uint32_t LogBucket(std::uint16_t base) {
    const bool upper = base >= 32768;
    std::uint32_t distance = upper ? kTotal - base : base;
    unsigned int exponent = 0;
    for (std::uint32_t value = distance; value > 1; value >>= 1) ++exponent;
    const std::uint32_t normalized = distance << (15 - exponent);
    const std::uint32_t mantissa = (normalized >> 13) & 3u;
    return (upper ? 64u : 0u) + exponent * 4 + mantissa;
  }

  static constexpr std::size_t kLevelCount = 4;
  unsigned int decay_shift_;
  std::array<std::vector<std::uint32_t>, kLevelCount> seen_;
  std::array<std::vector<std::int32_t>, kLevelCount> means_;
  std::array<std::uint64_t, kLevelCount> keys_{};
  std::array<std::size_t, kLevelCount> indices_{};
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
  std::string output;
  std::uint32_t train_end_ppm = 333333;
  std::uint32_t holdout_start_ppm = 666667;
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
    else if (key == "--train-end-ppm") args.train_end_ppm = std::stoul(value);
    else if (key == "--holdout-start-ppm") {
      args.holdout_start_ppm = std::stoul(value);
    } else {
      throw std::runtime_error("unknown option " + key);
    }
  }
  if (args.p1.empty() || args.store.empty() || args.output.empty()) {
    throw std::runtime_error("--p1, --wrt-store, and --output are required");
  }
  if (!(args.train_end_ppm < args.holdout_start_ppm &&
        args.holdout_start_ppm < 1000000)) {
    throw std::runtime_error("invalid split boundaries");
  }
  return args;
}

std::string JsonArray(const std::vector<std::int64_t>& values) {
  std::string output = "[";
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index) output += ", ";
    output += std::to_string(values[index]);
  }
  return output + "]";
}

template <typename Model>
void WriteResult(std::ofstream& output, const char* name,
                 const Model& model, const Stats& stats,
                 const RangeCounter& coder, std::uint64_t baseline_bytes,
                 bool trailing_comma) {
  std::uint32_t positive = 0;
  std::uint32_t regressing = 0;
  for (const std::int64_t gain : stats.block_qbits) {
    positive += gain > 0;
    regressing += gain < 0;
  }
  output << "    {\"variant_id\": \"" << name
         << "\", \"state_bytes\": " << model.StateBytes()
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
         << ", \"block_qbits\": " << JsonArray(stats.block_qbits) << "}";
  if (trailing_comma) output << ',';
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

    std::array<ResidualTree, 2> models = {ResidualTree(false),
                                          ResidualTree(true)};
    std::array<Stats, 2> stats;
    std::array<AdaptiveResidualTree, 3> adaptive_models = {
        AdaptiveResidualTree(6), AdaptiveResidualTree(8),
        AdaptiveResidualTree(10)};
    std::array<Stats, 3> adaptive_stats;
    const std::size_t block_count =
        (rows / 8 + kBlockBytes - 1) / kBlockBytes;
    for (auto& score : stats) score.block_qbits.assign(block_count, 0);
    for (auto& score : adaptive_stats) {
      score.block_qbits.assign(block_count, 0);
    }
    std::array<RangeCounter, 2> coders;
    std::array<RangeCounter, 3> adaptive_coders;
    RangeCounter baseline;
    LossTables losses;
    EventState event;
    const std::uint64_t train_end = rows * args.train_end_ppm / 1000000;
    const std::uint64_t holdout_start =
        rows * args.holdout_start_ppm / 1000000;

    for (std::uint64_t byte_index = 0; byte_index < rows / 8; ++byte_index) {
      const unsigned char truth_byte = store[5 + byte_index];
      unsigned int prefix = 0;
      for (unsigned int bit_position = 0; bit_position < 8; ++bit_position) {
        const std::uint64_t row = byte_index * 8 + bit_position;
        const unsigned char* record = p1.data() + 16 + row * 2;
        const std::uint16_t base = static_cast<std::uint16_t>(
            record[0] | (std::uint16_t{record[1]} << 8));
        const int bit = (truth_byte >> (7 - bit_position)) & 1;
        if (base == 0) throw std::runtime_error("zero P1 probability");
        baseline.Encode(bit, base);
        for (std::size_t index = 0; index < models.size(); ++index) {
          const std::uint16_t candidate =
              models[index].Predict(base, event, bit_position, prefix);
          coders[index].Encode(bit, candidate);
          const std::int64_t gain =
              losses.Loss(bit, base) - losses.Loss(bit, candidate);
          if (row < train_end) stats[index].train_qbits += gain;
          else if (row < holdout_start) stats[index].development_qbits += gain;
          else stats[index].holdout_qbits += gain;
          stats[index].block_qbits[byte_index / kBlockBytes] += gain;
          stats[index].active_rows += candidate != base;
          models[index].Update(bit);
        }
        for (std::size_t index = 0; index < adaptive_models.size(); ++index) {
          const std::uint16_t candidate = adaptive_models[index].Predict(
              base, event, bit_position, prefix);
          adaptive_coders[index].Encode(bit, candidate);
          const std::int64_t gain =
              losses.Loss(bit, base) - losses.Loss(bit, candidate);
          if (row < train_end) adaptive_stats[index].train_qbits += gain;
          else if (row < holdout_start) {
            adaptive_stats[index].development_qbits += gain;
          } else {
            adaptive_stats[index].holdout_qbits += gain;
          }
          adaptive_stats[index].block_qbits[byte_index / kBlockBytes] += gain;
          adaptive_stats[index].active_rows += candidate != base;
          adaptive_models[index].Update(bit);
        }
        prefix = (prefix << 1) | bit;
      }
      if (byte_index >= 6) event.ObserveByte(truth_byte);
    }
    baseline.Finish();
    for (auto& coder : coders) coder.Finish();
    for (auto& coder : adaptive_coders) coder.Finish();

    std::ofstream output(args.output);
    if (!output) throw std::runtime_error("cannot create " + args.output);
    output << std::fixed << std::setprecision(6)
           << "{\n  \"schema_version\": 1,\n"
           << "  \"receipt_type\": \"wrt_residual_mechanism_screen\",\n"
           << "  \"evidence_level\": \"causal_exact_p1_shadow\",\n"
           << "  \"claim_boundary\": \"Causal probability replay only; code cost, native integration, roundtrip, resources, and full-corpus proof remain required.\",\n"
           << "  \"causality\": {\"prediction_precedes_truth\": true, \"event_history_completed_only\": true, \"payload_bytes\": 0},\n"
           << "  \"parameters\": {\"hash_bits\": " << kHashBits
           << ", \"prior\": " << kPrior
           << ", \"strength_ppm\": " << kStrengthPpm
           << ", \"adaptive_decay_shifts\": [6, 8, 10]},\n"
           << "  \"rows\": " << rows << ",\n"
           << "  \"wrt_bytes\": " << rows / 8 << ",\n"
           << "  \"baseline_payload_bytes\": " << baseline.bytes()
           << ",\n  \"variants\": [\n";
    WriteResult(output, "phase_prefix_control", models[0], stats[0], coders[0],
                baseline.bytes(), true);
    WriteResult(output, "nested_completed_event_context", models[1], stats[1],
                coders[1], baseline.bytes(), true);
    for (std::size_t index = 0; index < adaptive_models.size(); ++index) {
      const std::string name = "adaptive_phase_prefix_d" +
                               std::to_string(std::array<int, 3>{6, 8, 10}[index]);
      WriteResult(output, name.c_str(), adaptive_models[index],
                  adaptive_stats[index], adaptive_coders[index],
                  baseline.bytes(), index + 1 != adaptive_models.size());
    }
    output << "  ],\n  \"promotion_authorized\": false\n}\n";
    if (!output) throw std::runtime_error("cannot write " + args.output);

    std::cout << "baseline_payload_bytes=" << baseline.bytes()
              << " control_saved_bytes="
              << static_cast<std::int64_t>(baseline.bytes()) -
                     static_cast<std::int64_t>(coders[0].bytes())
              << " context_saved_bytes="
              << static_cast<std::int64_t>(baseline.bytes()) -
                     static_cast<std::int64_t>(coders[1].bytes())
              << " adaptive_d6_saved_bytes="
              << static_cast<std::int64_t>(baseline.bytes()) -
                     static_cast<std::int64_t>(adaptive_coders[0].bytes())
              << " adaptive_d8_saved_bytes="
              << static_cast<std::int64_t>(baseline.bytes()) -
                     static_cast<std::int64_t>(adaptive_coders[1].bytes())
              << " adaptive_d10_saved_bytes="
              << static_cast<std::int64_t>(baseline.bytes()) -
                     static_cast<std::int64_t>(adaptive_coders[2].bytes())
              << '\n';
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
