// Causal hierarchical WRT event-phase residual SSE over exact FX2 probabilities.

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr std::uint32_t kTotal = 65536;
constexpr std::uint32_t kMaxCode = 0xffffffffu;
constexpr std::uint32_t kFamilies = 10;
constexpr std::uint32_t kLegacyFeatureMask = 0xff;
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

std::uint64_t Mix64(std::uint64_t value) {
  value ^= value >> 30;
  value *= 0xbf58476d1ce4e5b9ULL;
  value ^= value >> 27;
  value *= 0x94d049bb133111ebULL;
  return value ^ (value >> 31);
}

std::uint64_t Combine(std::uint64_t left, std::uint64_t right) {
  return Mix64(left ^ (right + 0x9e3779b97f4a7c15ULL + (left << 6) + (left >> 2)));
}

std::uint32_t CountBits(std::uint32_t value) {
  std::uint32_t count = 0;
  while (value) {
    count += value & 1u;
    value >>= 1;
  }
  return count;
}

unsigned char WrtTransform(unsigned char value) {
  if (value >= static_cast<unsigned char>('{') && value < 127) {
    value += static_cast<unsigned char>('P' - '{');
  } else if (value >= static_cast<unsigned char>('P') && value < static_cast<unsigned char>('T')) {
    value -= static_cast<unsigned char>('P' - '{');
  } else if ((value >= ':' && value <= '?') || (value >= 'J' && value <= 'O')) {
    value ^= 0x70;
  }
  if (value == 'X' || value == '`') value ^= static_cast<unsigned char>('X' ^ '`');
  return value;
}

struct Tables {
  Tables() {
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

class RangeCounter {
 public:
  void Encode(int bit, std::uint16_t p1) {
    const std::uint32_t delta = high_ - low_;
    const std::uint32_t midpoint = low_ + (delta >> 16) * p1 +
        static_cast<std::uint32_t>((static_cast<std::uint64_t>(delta & 0xffffu) * p1) >> 16);
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
  unsigned int hash_bits;
  std::uint32_t prior;
  std::uint32_t strength_ppm;
  std::uint32_t feature_mask = kLegacyFeatureMask;
  std::string Name() const {
    std::string name = "h" + std::to_string(hash_bits) + "_p" + std::to_string(prior) +
        "_s" + std::to_string(strength_ppm);
    if (feature_mask != kLegacyFeatureMask) {
      std::ostringstream suffix;
      suffix << "_m" << std::hex << std::setw(2) << std::setfill('0') << feature_mask;
      name += suffix.str();
    }
    return name;
  }
};

struct Stats {
  std::int64_t train_qbits = 0;
  std::int64_t development_qbits = 0;
  std::int64_t holdout_qbits = 0;
  std::vector<std::int64_t> block_qbits;
  std::uint64_t active_rows = 0;
};

class HashedSse {
 public:
  explicit HashedSse(Config config)
      : config_(config), size_(std::uint32_t{1} << config.hash_bits), mask_(size_ - 1) {
    std::size_t active = 0;
    family_offsets_.fill(std::numeric_limits<std::size_t>::max());
    for (std::uint32_t family = 0; family < kFamilies; ++family) {
      if ((config_.feature_mask & (std::uint32_t{1} << family)) == 0) continue;
      family_offsets_[family] = active++ * size_;
    }
    counts_.assign(active * size_, 0);
    sums_.assign(active * size_, 0);
  }

  std::uint16_t Predict(std::uint16_t base, const std::array<std::uint64_t, kFamilies>& hashes) {
    std::int64_t total = 0;
    std::uint32_t used = 0;
    for (std::uint32_t family = 0; family < kFamilies; ++family) {
      if ((config_.feature_mask & (std::uint32_t{1} << family)) == 0) continue;
      const std::size_t index = family_offsets_[family] +
          static_cast<std::uint32_t>(hashes[family] & mask_);
      indices_[family] = index;
      const std::uint32_t count = counts_[index];
      if (count) {
        total += sums_[index] / static_cast<std::int64_t>(count + config_.prior);
        ++used;
      }
    }
    base_ = base;
    if (!used) {
      predicted_ = base;
      return predicted_;
    }
    const std::int64_t correction = total / used;
    const std::int64_t scaled = correction * config_.strength_ppm / 1000000;
    predicted_ = static_cast<std::uint16_t>(std::max<std::int64_t>(
        1, std::min<std::int64_t>(kTotal - 1, static_cast<std::int64_t>(base) + scaled)));
    return predicted_;
  }

  void Update(int bit) {
    const std::int64_t residual = (bit ? static_cast<std::int64_t>(kTotal) : 0) - base_;
    for (std::uint32_t family = 0; family < kFamilies; ++family) {
      if ((config_.feature_mask & (std::uint32_t{1} << family)) == 0) continue;
      const std::size_t index = indices_[family];
      if (counts_[index] != std::numeric_limits<std::uint32_t>::max()) ++counts_[index];
      sums_[index] += residual;
    }
  }

  std::uint64_t StateBytes() const {
    return counts_.size() * sizeof(counts_[0]) + sums_.size() * sizeof(sums_[0]);
  }

 private:
  Config config_;
  std::uint32_t size_;
  std::uint32_t mask_;
  std::vector<std::uint32_t> counts_;
  std::vector<std::int64_t> sums_;
  std::array<std::size_t, kFamilies> family_offsets_{};
  std::array<std::size_t, kFamilies> indices_{};
  std::uint16_t base_ = 32768;
  std::uint16_t predicted_ = 32768;
};

struct EventState {
  std::vector<unsigned char> buffer;
  std::vector<std::uint64_t> history;
  std::size_t expected = 0;
  unsigned char previous_byte = 0;

  std::uint32_t ByteIndex() const { return static_cast<std::uint32_t>(buffer.size()); }

  std::uint64_t CurrentPrefixHash() const {
    std::uint64_t hash = 0xcbf29ce484222325ULL ^ expected;
    for (const unsigned char value : buffer) {
      hash ^= value;
      hash *= 0x100000001b3ULL;
    }
    return Mix64(hash ^ buffer.size());
  }

  std::uint32_t LeadClass() const {
    if (buffer.empty()) return 0;
    const unsigned char value = WrtTransform(buffer.front());
    if (value == 0x0c) return 1;
    if (value > 0xcf) return 2 + std::min<std::uint32_t>((value - 0xd0) >> 3, 5);
    if (value >= 'a' && value <= 'z') return 8;
    if (value >= 'A' && value <= 'Z') return 9;
    if (value >= '0' && value <= '9') return 10;
    if (value == ' ' || value == '\n' || value == '\t') return 11;
    if (value == '<' || value == '>' || value == '/' || value == '=') return 12;
    if (value == '\'' || value == '"') return 13;
    if (value < 128) return 14;
    return 15;
  }

  std::array<std::uint64_t, 5> Suffixes() const {
    constexpr std::array<unsigned int, 5> lengths = {1, 2, 4, 8, 16};
    std::array<std::uint64_t, 5> output{};
    for (std::size_t slot = 0; slot < lengths.size(); ++slot) {
      const std::size_t begin = history.size() > lengths[slot] ? history.size() - lengths[slot] : 0;
      std::uint64_t hash = 0x6a09e667f3bcc909ULL ^ lengths[slot];
      for (std::size_t index = begin; index < history.size(); ++index) {
        hash = Combine(hash, history[index]);
      }
      output[slot] = hash;
    }
    return output;
  }

  void ObserveByte(unsigned char value) {
    previous_byte = value;
    buffer.push_back(value);
    if (buffer.size() == 1) {
      const unsigned char first = WrtTransform(buffer[0]);
      expected = (first == 0x0c || first > 0xcf) ? 2 : 1;
    } else if (buffer.size() == 2 && WrtTransform(buffer[0]) > 0xcf &&
               WrtTransform(buffer[1]) > 0xcf) {
      expected = 3;
    }
    if (expected && buffer.size() == expected) {
      std::uint64_t hash = 0xcbf29ce484222325ULL;
      for (const unsigned char byte : buffer) {
        hash ^= byte;
        hash *= 0x100000001b3ULL;
      }
      history.push_back(Mix64(hash ^ buffer.size()));
      if (history.size() > 16) history.erase(history.begin());
      buffer.clear();
      expected = 0;
    }
  }
};

struct HierarchicalConfig {
  std::uint32_t prior;
  std::uint32_t strength_ppm;
  bool lead_class;
  bool log_bucket;
  std::string Name() const {
    return "p" + std::to_string(prior) + "_s" + std::to_string(strength_ppm) +
        (lead_class ? "_lead16" : "") + (log_bucket ? "_log128" : "");
  }
};

class HierarchicalSse {
 public:
  explicit HierarchicalSse(HierarchicalConfig config) : config_(config) {
    const std::size_t scale = config_.log_bucket ? 2 : 1;
    for (std::size_t level = 0; level < kBaseLevelSizes.size(); ++level) {
      level_sizes_[level] = kBaseLevelSizes[level] * scale;
      if (level == 3 && !config_.lead_class) continue;
      counts_[level].assign(level_sizes_[level], 0);
      sums_[level].assign(level_sizes_[level], 0);
    }
  }

  std::uint16_t Predict(std::uint16_t base, const EventState& event,
                        unsigned int bit_position, unsigned int byte_prefix) {
    const std::uint32_t bucket = Bucket(base);
    const std::uint32_t bucket_count = config_.log_bucket ? 128 : 64;
    const std::uint32_t position = event.ByteIndex() * 8 + bit_position;
    indices_[0] = position * bucket_count + bucket;
    indices_[1] = (position * 4 + (byte_prefix & 3u)) * bucket_count + bucket;
    indices_[2] = (position * 16 + (byte_prefix & 15u)) * bucket_count + bucket;
    indices_[3] = ((event.LeadClass() * 24 + position) * 16 +
                   (byte_prefix & 15u)) * bucket_count + bucket;
    indices_[4] = (position * 256 + byte_prefix) * bucket_count + bucket;
    std::int64_t posterior = 0;
    for (std::size_t level = 0; level < kBaseLevelSizes.size(); ++level) {
      if (level == 3 && !config_.lead_class) continue;
      const std::size_t index = indices_[level];
      posterior = (sums_[level][index] +
                   static_cast<std::int64_t>(config_.prior) * posterior) /
          static_cast<std::int64_t>(counts_[level][index] + config_.prior);
    }
    base_ = base;
    const std::int64_t correction = posterior * config_.strength_ppm / 1000000;
    return static_cast<std::uint16_t>(std::max<std::int64_t>(
        1, std::min<std::int64_t>(kTotal - 1, static_cast<std::int64_t>(base) + correction)));
  }

  void Update(int bit) {
    const std::int64_t residual = (bit ? static_cast<std::int64_t>(kTotal) : 0) - base_;
    for (std::size_t level = 0; level < kBaseLevelSizes.size(); ++level) {
      if (level == 3 && !config_.lead_class) continue;
      const std::size_t index = indices_[level];
      if (counts_[level][index] != std::numeric_limits<std::uint32_t>::max()) {
        ++counts_[level][index];
      }
      sums_[level][index] += residual;
    }
  }

  std::uint64_t StateBytes() const {
    std::uint64_t total = 0;
    for (std::size_t level = 0; level < kBaseLevelSizes.size(); ++level) {
      if (level != 3 || config_.lead_class) total += level_sizes_[level] * 12;
    }
    return total;
  }

 private:
  std::uint32_t Bucket(std::uint16_t base) const {
    if (!config_.log_bucket) return base >> 10;
    const bool upper = base >= 32768;
    std::uint32_t distance = upper ? kTotal - base : base;
    unsigned int exponent = 0;
    for (std::uint32_t value = distance; value > 1; value >>= 1) ++exponent;
    const std::uint32_t normalized = distance << (15 - exponent);
    const std::uint32_t mantissa = (normalized >> 13) & 3u;
    return (upper ? 64u : 0u) + exponent * 4 + mantissa;
  }

  static constexpr std::array<std::size_t, 5> kBaseLevelSizes = {
      2048, 8192, 32768, 524288, 524288};
  HierarchicalConfig config_;
  std::array<std::size_t, 5> level_sizes_{};
  std::array<std::vector<std::uint32_t>, 5> counts_;
  std::array<std::vector<std::int64_t>, 5> sums_;
  std::array<std::size_t, 5> indices_{};
  std::uint16_t base_ = 32768;
};

[[maybe_unused]] std::array<std::uint64_t, kFamilies> Features(
    const EventState& state, const std::array<std::uint64_t, 5>& suffixes,
    std::uint16_t base, unsigned int bit_position, unsigned int byte_prefix) {
  const std::uint64_t bucket = base >> 10;
  const std::uint64_t phase = (static_cast<std::uint64_t>(state.ByteIndex()) << 12) |
      (static_cast<std::uint64_t>(bit_position) << 8) | byte_prefix;
  const std::uint64_t direct_phase =
      (((static_cast<std::uint64_t>(state.ByteIndex()) * 8 + bit_position) * 256 +
        byte_prefix) * 64 + bucket);
  return {
      Mix64(0x10ULL ^ (bucket << 4) ^ bit_position),
      Combine(suffixes[0], phase ^ (bucket << 20)),
      Combine(suffixes[1], phase ^ (bucket << 21)),
      Combine(suffixes[2], phase ^ (bucket << 22)),
      Combine(suffixes[3], phase ^ (bucket << 23)),
      Combine(suffixes[4], phase ^ (bucket << 24)),
      Mix64(0x70ULL ^ phase ^ (bucket << 32)),
      Mix64(0x80ULL ^ state.previous_byte ^ (bucket << 8) ^ bit_position),
      Combine(state.CurrentPrefixHash(), phase ^ (bucket << 25)),
      direct_phase,
  };
}

std::string JsonEscape(const std::string& value) {
  std::string output;
  for (const char ch : value) {
    if (ch == '\\' || ch == '"') output.push_back('\\');
    output.push_back(ch);
  }
  return output;
}

[[maybe_unused]] void WriteJson(const std::string& path, const std::vector<Config>& configs,
               const std::vector<Stats>& stats, const std::vector<RangeCounter>& coders,
               std::uint64_t baseline_bytes, std::uint64_t rows, std::uint64_t stream_bytes,
               std::size_t best) {
  std::ofstream out(path);
  if (!out) throw std::runtime_error("cannot create " + path);
  out << "{\n  \"schema_version\": 2,\n"
      << "  \"receipt_type\": \"wrt_hashed_residual_online_screen\",\n"
      << "  \"evidence_level\": \"causal_exact_fx2_probability_trace_shadow\",\n"
      << "  \"claim_boundary\": \"Selection-window shadow only; native integration, source cost, disjoint confirmation, and full-corpus proof remain required.\",\n"
      << "  \"rows\": " << rows << ",\n  \"wrt_bytes\": " << stream_bytes << ",\n"
      << "  \"baseline_payload_bytes\": " << baseline_bytes << ",\n"
      << "  \"selection_rule\": \"maximum development qbits; ties by holdout then name\",\n"
      << "  \"best_variant_id\": \"" << JsonEscape(configs[best].Name()) << "\",\n"
      << "  \"variants\": [\n";
  for (std::size_t index = 0; index < configs.size(); ++index) {
    const auto& config = configs[index];
    const auto& score = stats[index];
    std::uint32_t positive = 0;
    std::uint32_t regressing = 0;
    for (const auto value : score.block_qbits) {
      positive += value > 0;
      regressing += value < 0;
    }
    out << "    {\"variant_id\": \"" << config.Name() << "\", \"hash_bits\": "
        << config.hash_bits << ", \"prior\": " << config.prior
        << ", \"strength_ppm\": " << config.strength_ppm
        << ", \"feature_mask\": " << config.feature_mask
        << ", \"state_bytes\": "
        << (static_cast<std::uint64_t>(CountBits(config.feature_mask)) *
            (std::uint64_t{1} << config.hash_bits) * 12)
        << ", \"train_qbits\": " << score.train_qbits
        << ", \"development_qbits\": " << score.development_qbits
        << ", \"holdout_qbits\": " << score.holdout_qbits
        << ", \"train_saved_bytes\": " << score.train_qbits / 2048.0
        << ", \"development_saved_bytes\": " << score.development_qbits / 2048.0
        << ", \"holdout_saved_bytes\": " << score.holdout_qbits / 2048.0
        << ", \"exact_saved_bytes\": "
        << static_cast<std::int64_t>(baseline_bytes) - static_cast<std::int64_t>(coders[index].bytes())
        << ", \"candidate_payload_bytes\": " << coders[index].bytes()
        << ", \"positive_blocks\": " << positive
        << ", \"regressing_blocks\": " << regressing
        << ", \"active_rows\": " << score.active_rows << ", \"block_qbits\": [";
    for (std::size_t block = 0; block < score.block_qbits.size(); ++block) {
      if (block) out << ", ";
      out << score.block_qbits[block];
    }
    out << "]}";
    if (index + 1 != configs.size()) out << ',';
    out << '\n';
  }
  out << "  ],\n  \"promotion_authorized\": false\n}\n";
}

void WriteHierarchicalJson(const std::string& path,
                           const std::vector<HierarchicalConfig>& configs,
                           const std::vector<Stats>& stats,
                           const std::vector<RangeCounter>& coders,
                           const std::vector<HierarchicalSse>& models,
                           std::uint64_t baseline_bytes, std::uint64_t rows,
                           std::uint64_t stream_bytes, std::size_t best) {
  std::ofstream out(path);
  if (!out) throw std::runtime_error("cannot create " + path);
  out << "{\n  \"schema_version\": 1,\n"
      << "  \"receipt_type\": \"wrt_hierarchical_phase_residual_screen\",\n"
      << "  \"evidence_level\": \"causal_exact_fx2_probability_trace_shadow\",\n"
      << "  \"combiner\": \"coarse_to_full_integer_bayesian_residual_backoff\",\n"
      << "  \"levels\": [\"event_phase\", \"suffix2\", \"suffix4\", \"optional_lead16_suffix4\", \"full_prefix\"],\n"
      << "  \"claim_boundary\": \"Selection-window shadow only; disjoint confirmation, endpoint428 transfer, source cost, and native integration remain required.\",\n"
      << "  \"rows\": " << rows << ",\n  \"wrt_bytes\": " << stream_bytes << ",\n"
      << "  \"baseline_payload_bytes\": " << baseline_bytes << ",\n"
      << "  \"selection_rule\": \"maximum development qbits; ties by holdout then name\",\n"
      << "  \"best_variant_id\": \"" << configs[best].Name() << "\",\n"
      << "  \"variants\": [\n";
  for (std::size_t index = 0; index < configs.size(); ++index) {
    const auto& config = configs[index];
    const auto& score = stats[index];
    std::uint32_t positive = 0;
    std::uint32_t regressing = 0;
    for (const auto value : score.block_qbits) {
      positive += value > 0;
      regressing += value < 0;
    }
    out << "    {\"variant_id\": \"" << config.Name() << "\", \"prior\": "
        << config.prior << ", \"strength_ppm\": " << config.strength_ppm
        << ", \"lead_class\": " << (config.lead_class ? "true" : "false")
        << ", \"log_bucket\": " << (config.log_bucket ? "true" : "false")
        << ", \"state_bytes\": " << models[index].StateBytes()
        << ", \"train_qbits\": " << score.train_qbits
        << ", \"development_qbits\": " << score.development_qbits
        << ", \"holdout_qbits\": " << score.holdout_qbits
        << ", \"exact_saved_bytes\": "
        << static_cast<std::int64_t>(baseline_bytes) -
               static_cast<std::int64_t>(coders[index].bytes())
        << ", \"candidate_payload_bytes\": " << coders[index].bytes()
        << ", \"positive_blocks\": " << positive
        << ", \"regressing_blocks\": " << regressing
        << ", \"active_rows\": " << score.active_rows << ", \"block_qbits\": [";
    for (std::size_t block = 0; block < score.block_qbits.size(); ++block) {
      if (block) out << ", ";
      out << score.block_qbits[block];
    }
    out << "]}";
    if (index + 1 != configs.size()) out << ',';
    out << '\n';
  }
  out << "  ],\n  \"promotion_authorized\": false\n}\n";
}

struct Args {
  std::string trace;
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
    if (key == "--trace") args.trace = value;
    else if (key == "--wrt-store") args.store = value;
    else if (key == "--output") args.output = value;
    else if (key == "--train-end-ppm") args.train_end_ppm = std::stoul(value);
    else if (key == "--holdout-start-ppm") args.holdout_start_ppm = std::stoul(value);
    else throw std::runtime_error("unknown option " + key);
  }
  if (args.trace.empty() || args.store.empty() || args.output.empty()) {
    throw std::runtime_error("--trace, --wrt-store, and --output are required");
  }
  if (!(args.train_end_ppm < args.holdout_start_ppm && args.holdout_start_ppm < 1000000)) {
    throw std::runtime_error("invalid split boundaries");
  }
  return args;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const Args args = ParseArgs(argc, argv);
    const auto trace = ReadFile(args.trace);
    const auto store = ReadFile(args.store);
    const std::array<unsigned char, 8> magic = {'F', 'X', '2', 'P', 'T', '0', '1', '\n'};
    if (trace.size() < 8 || !std::equal(magic.begin(), magic.end(), trace.begin()) ||
        (trace.size() - 8) % 3 != 0) {
      throw std::runtime_error("invalid FX2 probability trace");
    }
    const std::uint64_t rows = (trace.size() - 8) / 3;
    if ((rows & 7) != 0 || store.size() != 5 + rows / 8) {
      throw std::runtime_error("trace/store dimensions differ");
    }
    std::vector<HierarchicalConfig> configs;
    for (const std::uint32_t prior : {64u, 128u, 256u}) {
      for (const std::uint32_t strength : {250000u, 500000u}) {
        configs.push_back({prior, strength, false, false});
        configs.push_back({prior, strength, true, false});
      }
    }
    configs.push_back({128, 250000, false, true});
    configs.push_back({256, 250000, false, true});
    std::vector<HierarchicalSse> models;
    for (const auto& config : configs) models.emplace_back(config);
    std::vector<Stats> stats(configs.size());
    const std::size_t blocks = (rows / 8 + kBlockBytes - 1) / kBlockBytes;
    for (auto& score : stats) score.block_qbits.assign(blocks, 0);
    std::vector<RangeCounter> coders(configs.size());
    RangeCounter baseline;
    Tables tables;
    EventState event;
    const std::uint64_t train_end = rows * args.train_end_ppm / 1000000;
    const std::uint64_t holdout_start = rows * args.holdout_start_ppm / 1000000;

    for (std::uint64_t byte_index = 0; byte_index < rows / 8; ++byte_index) {
      const unsigned char truth_byte = store[5 + byte_index];
      unsigned int prefix = 0;
      for (unsigned int bit_position = 0; bit_position < 8; ++bit_position) {
        const std::uint64_t row = byte_index * 8 + bit_position;
        const unsigned char* record = trace.data() + 8 + row * 3;
        const std::uint16_t base = static_cast<std::uint16_t>(record[0] | (record[1] << 8));
        const int bit = record[2];
        const int expected_bit = (truth_byte >> (7 - bit_position)) & 1;
        if (bit != expected_bit || base == 0) throw std::runtime_error("trace truth mismatch");
        baseline.Encode(bit, base);
        for (std::size_t index = 0; index < models.size(); ++index) {
          const std::uint16_t candidate =
              models[index].Predict(base, event, bit_position, prefix);
          coders[index].Encode(bit, candidate);
          const std::int64_t gain = tables.Loss(bit, base) - tables.Loss(bit, candidate);
          if (row < train_end) stats[index].train_qbits += gain;
          else if (row < holdout_start) stats[index].development_qbits += gain;
          else stats[index].holdout_qbits += gain;
          stats[index].block_qbits[byte_index / kBlockBytes] += gain;
          stats[index].active_rows += candidate != base;
          models[index].Update(bit);
        }
        prefix = (prefix << 1) | bit;
      }
      if (byte_index >= 6) event.ObserveByte(truth_byte);
      else event.previous_byte = truth_byte;
    }
    baseline.Finish();
    for (auto& coder : coders) coder.Finish();
    std::size_t best = 0;
    for (std::size_t index = 1; index < configs.size(); ++index) {
      if (stats[index].development_qbits > stats[best].development_qbits ||
          (stats[index].development_qbits == stats[best].development_qbits &&
           (stats[index].holdout_qbits > stats[best].holdout_qbits ||
            (stats[index].holdout_qbits == stats[best].holdout_qbits &&
             configs[index].Name() < configs[best].Name())))) {
        best = index;
      }
    }
    WriteHierarchicalJson(
        args.output, configs, stats, coders, models, baseline.bytes(), rows, rows / 8, best);
    std::cout << configs[best].Name() << " development_qbits="
              << stats[best].development_qbits << " holdout_qbits="
              << stats[best].holdout_qbits << " exact_saved_bytes="
              << static_cast<std::int64_t>(baseline.bytes()) -
                     static_cast<std::int64_t>(coders[best].bytes())
              << '\n';
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
