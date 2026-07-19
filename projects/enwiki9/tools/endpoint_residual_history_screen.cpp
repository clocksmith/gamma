// Causal endpoint-residual history retrieval over an exact P1 stream.

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
constexpr unsigned int kHashBits = 20;
constexpr std::uint32_t kPrior = 256;
constexpr std::uint32_t kStrengthPpm = 250000;
constexpr std::array<unsigned int, 3> kHistoryLengths = {2, 4, 8};

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

struct LossTables {
  LossTables() {
    for (std::uint32_t p = 1; p < kTotal; ++p) {
      loss0[p] = static_cast<std::int32_t>(
          -std::log2(static_cast<double>(kTotal - p) / kTotal) * 256.0 + 0.5);
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

class ResidualHistory {
 public:
  explicit ResidualHistory(unsigned int history_length)
      : history_length_(history_length), counts_(std::size_t{1} << kHashBits),
        sums_(std::size_t{1} << kHashBits) {}

  std::uint16_t Predict(std::uint16_t base, unsigned int bit_position,
                        unsigned int byte_prefix) {
    std::uint64_t history_code = 0;
    for (unsigned int offset = 0; offset < history_length_; ++offset) {
      history_code = (history_code << 3) | history_[(cursor_ - 1 - offset) & 7];
    }
    const std::uint64_t key = history_code |
        (static_cast<std::uint64_t>(bit_position) << 24) |
        (static_cast<std::uint64_t>(byte_prefix & 15u) << 27) |
        (static_cast<std::uint64_t>(LogBucket(base)) << 31) |
        (static_cast<std::uint64_t>(history_length_) << 39);
    index_ = static_cast<std::size_t>(Mix64(key)) &
             ((std::size_t{1} << kHashBits) - 1);
    base_ = base;
    const std::int64_t posterior = sums_[index_] /
        static_cast<std::int64_t>(counts_[index_] + kPrior);
    const std::int64_t correction = posterior * kStrengthPpm / 1000000;
    return static_cast<std::uint16_t>(std::max<std::int64_t>(
        1, std::min<std::int64_t>(kTotal - 1,
                                  static_cast<std::int64_t>(base) + correction)));
  }

  void Perceive(int bit) {
    const std::int64_t residual =
        (bit ? static_cast<std::int64_t>(kTotal) : 0) - base_;
    if (counts_[index_] != std::numeric_limits<std::uint32_t>::max()) {
      ++counts_[index_];
    }
    sums_[index_] += residual;
    const std::uint32_t assigned = bit ? base_ : kTotal - base_;
    history_[cursor_++ & 7] = Surprise(assigned);
  }

  std::uint64_t StateBytes() const {
    return (std::uint64_t{1} << kHashBits) * 12;
  }

 private:
  static std::uint32_t LogBucket(std::uint16_t base) {
    const bool upper = base >= 32768;
    const std::uint32_t distance = upper ? kTotal - base : base;
    unsigned int exponent = 0;
    for (std::uint32_t value = distance; value > 1; value >>= 1) ++exponent;
    const std::uint32_t normalized = distance << (15 - exponent);
    const std::uint32_t mantissa = (normalized >> 13) & 3u;
    return (upper ? 64u : 0u) + exponent * 4 + mantissa;
  }

  static unsigned char Surprise(std::uint32_t assigned) {
    if (assigned >= 57344) return 0;
    if (assigned >= 49152) return 1;
    if (assigned >= 32768) return 2;
    if (assigned >= 16384) return 3;
    if (assigned >= 8192) return 4;
    if (assigned >= 4096) return 5;
    if (assigned >= 2048) return 6;
    return 7;
  }

  unsigned int history_length_;
  std::vector<std::uint32_t> counts_;
  std::vector<std::int64_t> sums_;
  std::array<unsigned char, 8> history_{};
  std::uint64_t cursor_ = 0;
  std::size_t index_ = 0;
  std::uint16_t base_ = 32768;
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
    std::array<ResidualHistory, 3> models = {
        ResidualHistory(kHistoryLengths[0]), ResidualHistory(kHistoryLengths[1]),
        ResidualHistory(kHistoryLengths[2])};
    std::array<Stats, 3> stats;
    for (auto& score : stats) score.block_qbits.assign(blocks, 0);
    std::array<RangeCounter, 3> coders;
    RangeCounter baseline;
    LossTables losses;
    unsigned int byte_prefix = 0;

    for (std::uint64_t row = 0; row < rows; ++row) {
      const int bit = (store[5 + row / 8] >> (7 - (row & 7))) & 1;
      const unsigned char* record = p1.data() + 16 + row * 2;
      const std::uint16_t base = static_cast<std::uint16_t>(
          record[0] | (std::uint16_t{record[1]} << 8));
      if (base == 0) throw std::runtime_error("zero P1 probability");
      baseline.Encode(bit, base);
      for (std::size_t index = 0; index < models.size(); ++index) {
        const std::uint16_t predicted =
            models[index].Predict(base, row & 7, byte_prefix);
        coders[index].Encode(bit, predicted);
        const std::int64_t gain =
            losses.Loss(bit, base) - losses.Loss(bit, predicted);
        if (row < train_end) stats[index].train_qbits += gain;
        else if (row < holdout_start) stats[index].development_qbits += gain;
        else stats[index].holdout_qbits += gain;
        stats[index].block_qbits[(row / 8) / kBlockBytes] += gain;
        stats[index].active_rows += predicted != base;
        models[index].Perceive(bit);
      }
      byte_prefix = ((byte_prefix << 1) | bit) & 0xffu;
      if ((row & 7) == 7) byte_prefix = 0;
    }
    baseline.Finish();
    for (auto& coder : coders) coder.Finish();

    std::size_t selected = 0;
    for (std::size_t index = 1; index < stats.size(); ++index) {
      if (stats[index].development_qbits > stats[selected].development_qbits) {
        selected = index;
      }
    }
    std::ofstream output(args.output);
    if (!output) throw std::runtime_error("cannot create " + args.output);
    output << "{\n  \"schema_version\": 1,\n"
           << "  \"receipt_type\": \"endpoint_residual_history_screen\",\n"
           << "  \"evidence_level\": \"causal_exact_p1_shadow\",\n"
           << "  \"hypothesis\": \"Recent endpoint surprise sequences identify recurring residual regimes not represented by decoded byte context alone.\",\n"
           << "  \"claim_boundary\": \"Causal P1 replay only; native integration, source accounting, resources, and full-corpus proof remain required.\",\n"
           << "  \"causality\": {\"prediction_precedes_truth\": true, \"surprise_history_updates_after_truth\": true, \"payload_bytes\": 0},\n"
           << "  \"selection_rule\": \"Highest development qbits; holdout is confirmation only.\",\n"
           << "  \"rows\": " << rows << ",\n"
           << "  \"baseline_payload_bytes\": " << baseline.bytes()
           << ",\n  \"variants\": [\n";
    for (std::size_t index = 0; index < models.size(); ++index) {
      std::uint32_t positive = 0;
      std::uint32_t regressing = 0;
      for (const std::int64_t value : stats[index].block_qbits) {
        positive += value > 0;
        regressing += value < 0;
      }
      output << "    {\"variant_id\": \"surprise_history_"
             << kHistoryLengths[index] << "\", \"history_length\": "
             << kHistoryLengths[index] << ", \"state_bytes\": "
             << models[index].StateBytes() << ", \"train_qbits\": "
             << stats[index].train_qbits << ", \"development_qbits\": "
             << stats[index].development_qbits << ", \"holdout_qbits\": "
             << stats[index].holdout_qbits
             << ", \"candidate_payload_bytes\": " << coders[index].bytes()
             << ", \"exact_saved_bytes\": "
             << static_cast<std::int64_t>(baseline.bytes()) -
                    static_cast<std::int64_t>(coders[index].bytes())
             << ", \"positive_blocks\": " << positive
             << ", \"regressing_blocks\": " << regressing
             << ", \"active_rows\": " << stats[index].active_rows
             << ", \"block_qbits\": " << Values(stats[index].block_qbits)
             << "}" << (index + 1 == models.size() ? "\n" : ",\n");
    }
    output << "  ],\n  \"selected_variant\": \"surprise_history_"
           << kHistoryLengths[selected] << "\",\n"
           << "  \"promotion_authorized\": false\n}\n";
    if (!output) throw std::runtime_error("cannot write " + args.output);
    std::cout << "baseline_payload_bytes=" << baseline.bytes();
    for (std::size_t index = 0; index < coders.size(); ++index) {
      std::cout << " history" << kHistoryLengths[index] << "_saved_bytes="
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
