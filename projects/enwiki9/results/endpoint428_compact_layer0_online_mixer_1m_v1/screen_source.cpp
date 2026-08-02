// Causal fixed-point online residual mixer over endpoint428 and the compact
// layer-0 endpoints. Hyperparameters are selected before sealed holdout rows.

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

constexpr std::uint32_t kProbabilityTotal = 65536;
constexpr std::uint32_t kWeightScale = 1u << 20;
constexpr std::uint32_t kEndpointCount = 26;
constexpr std::uint32_t kFeatureCount = kEndpointCount + 1;
constexpr std::uint32_t kPpm = 1000000;

std::vector<unsigned char> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open " + path);
  input.seekg(0, std::ios::end);
  const std::streamoff length = input.tellg();
  if (length < 0) throw std::runtime_error("cannot size " + path);
  input.seekg(0, std::ios::beg);
  std::vector<unsigned char> result(static_cast<std::size_t>(length));
  if (!result.empty()) {
    input.read(reinterpret_cast<char*>(result.data()), length);
    if (!input) throw std::runtime_error("cannot read " + path);
  }
  return result;
}

void WriteFile(const std::string& path, const std::vector<unsigned char>& data) {
  std::ofstream output(path, std::ios::binary);
  if (!output) throw std::runtime_error("cannot create " + path);
  if (!data.empty()) {
    output.write(reinterpret_cast<const char*>(data.data()), data.size());
  }
  if (!output) throw std::runtime_error("cannot write " + path);
}

std::uint64_t ReadU64(const unsigned char* input) {
  std::uint64_t value = 0;
  for (unsigned int shift = 0; shift < 64; shift += 8) {
    value |= static_cast<std::uint64_t>(*input++) << shift;
  }
  return value;
}

void AppendU64(std::vector<unsigned char>* output, std::uint64_t value) {
  for (unsigned int shift = 0; shift < 64; shift += 8) {
    output->push_back(static_cast<unsigned char>(value >> shift));
  }
}

std::int64_t ShiftTowardZero(std::int64_t value, unsigned int shift) {
  if (value >= 0) return value >> shift;
  return -((-value) >> shift);
}

std::int64_t DivideRoundNearest(std::int64_t value, std::int64_t divisor) {
  if (value >= 0) return (value + divisor / 2) / divisor;
  return -((-value + divisor / 2) / divisor);
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
    logit[0] = Log2Q16(1) - Log2Q16(kProbabilityTotal - 1);
    for (std::uint32_t p = 1; p < kProbabilityTotal; ++p) {
      logit[p] = Log2Q16(p) - Log2Q16(kProbabilityTotal - p);
      loss0[p] = static_cast<std::int32_t>(
          -std::log2(static_cast<double>(kProbabilityTotal - p) /
                     kProbabilityTotal) * 256.0 + 0.5);
      loss1[p] = static_cast<std::int32_t>(
          -std::log2(static_cast<double>(p) / kProbabilityTotal) * 256.0 +
          0.5);
    }
    for (std::uint32_t p : {1u, 8192u, 32768u, 49152u, 65535u}) {
      if (Probability(logit[p]) != p) {
        throw std::runtime_error("native logit inverse self-check failed");
      }
    }
  }

  std::uint16_t Probability(std::int64_t target) const {
    const auto begin = logit.begin() + 1;
    const auto end = logit.end();
    auto high_it = std::lower_bound(begin, end, target);
    if (high_it == begin) return 1;
    if (high_it == end) return kProbabilityTotal - 1;
    const std::uint32_t high = static_cast<std::uint32_t>(high_it - logit.begin());
    const std::uint32_t low = high - 1;
    return target - logit[low] <= logit[high] - target ? low : high;
  }

  std::int32_t Loss(int bit, std::uint16_t p1) const {
    return bit ? loss1[p1] : loss0[p1];
  }

  std::array<std::int32_t, kProbabilityTotal> logit{};
  std::array<std::int32_t, kProbabilityTotal> loss0{};
  std::array<std::int32_t, kProbabilityTotal> loss1{};
};

struct Inputs {
  Inputs(const std::string& layer_path, const std::string& base_path,
         const std::string& store_path)
      : layer(ReadFile(layer_path)), base(ReadFile(base_path)),
        store(ReadFile(store_path)) {
    const std::array<unsigned char, 8> layer_magic = {
        'C', 'M', 'L', '0', 'P', '1', 'V', '1'};
    if (layer.size() < 16 ||
        !std::equal(layer_magic.begin(), layer_magic.end(), layer.begin())) {
      throw std::runtime_error("invalid layer-0 trace magic");
    }
    rows = ReadU64(layer.data() + 8);
    if (rows == 0 || layer.size() != 16 + rows * kEndpointCount * 2) {
      throw std::runtime_error("invalid layer-0 trace dimensions");
    }
    if (base.size() != 16 + rows * 2 || ReadU64(base.data() + 8) != rows) {
      throw std::runtime_error("invalid base P1 dimensions");
    }
    if ((rows & 7) != 0 || store.size() != 5 + rows / 8) {
      throw std::runtime_error("invalid WRT truth-store dimensions");
    }
  }

  std::uint16_t Base(std::uint64_t row) const {
    const unsigned char* p = base.data() + 16 + 2 * row;
    return static_cast<std::uint16_t>(p[0] | (std::uint16_t{p[1]} << 8));
  }

  std::uint16_t Endpoint(std::uint64_t row, std::uint32_t endpoint) const {
    const unsigned char* p = layer.data() + 16 +
        2 * (row * kEndpointCount + endpoint);
    return static_cast<std::uint16_t>(p[0] | (std::uint16_t{p[1]} << 8));
  }

  int Bit(std::uint64_t row) const {
    return (store[5 + row / 8] >> (7 - (row & 7))) & 1;
  }

  unsigned char PreviousByte(std::uint64_t row) const {
    const std::uint64_t byte = row / 8;
    return byte == 0 ? 0 : store[5 + byte - 1];
  }

  std::vector<unsigned char> layer;
  std::vector<unsigned char> base;
  std::vector<unsigned char> store;
  std::uint64_t rows = 0;
};

enum class ContextKind { kGlobal, kBitPosition, kByteRegime };

struct Config {
  std::string name;
  ContextKind context = ContextKind::kGlobal;
  unsigned int global_shift = 22;
  unsigned int local_shift = 0;
  bool gated = false;
  unsigned int regret_shift = 12;
  std::uint32_t gate_warmup = 128;
};

std::uint32_t ByteClass(unsigned char value) {
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

std::uint32_t ConfidenceBin(std::uint16_t base) {
  const std::uint32_t distance = base > 32768 ? base - 32768 : 32768 - base;
  if (distance < 4096) return 0;
  if (distance < 12288) return 1;
  if (distance < 24576) return 2;
  return 3;
}

std::uint32_t LocalContextCount(ContextKind kind) {
  if (kind == ContextKind::kGlobal) return 0;
  if (kind == ContextKind::kBitPosition) return 8;
  return 8 * 8 * 4;
}

std::uint32_t LocalContext(const Config& config, const Inputs& input,
                           std::uint64_t row, std::uint16_t base) {
  if (config.context == ContextKind::kBitPosition) return row & 7;
  if (config.context == ContextKind::kByteRegime) {
    return ((row & 7) * 8 + ByteClass(input.PreviousByte(row))) * 4 +
        ConfidenceBin(base);
  }
  return 0;
}

class OnlineMixer {
 public:
  OnlineMixer(const Config& config, const Tables& tables)
      : config_(config), tables_(tables), global_(kFeatureCount, 0),
        local_(LocalContextCount(config.context) * kFeatureCount, 0),
        regret_(std::max<std::uint32_t>(1, LocalContextCount(config.context)), 0),
        seen_(regret_.size(), 0) {}

  std::uint16_t Predict(const Inputs& input, std::uint64_t row) {
    base_ = input.Base(row);
    const std::int32_t base_logit = tables_.logit[base_];
    for (std::uint32_t endpoint = 0; endpoint < kEndpointCount; ++endpoint) {
      std::int32_t feature = tables_.logit[input.Endpoint(row, endpoint)] -
          base_logit;
      features_[endpoint] = std::max<std::int32_t>(-262144,
          std::min<std::int32_t>(262144, feature));
    }
    features_[kEndpointCount] = 65536;
    context_ = LocalContext(config_, input, row, base_);
    std::int64_t correction = 0;
    for (std::uint32_t feature = 0; feature < kFeatureCount; ++feature) {
      correction += static_cast<std::int64_t>(global_[feature]) *
          features_[feature];
    }
    if (!local_.empty()) {
      const std::size_t offset = context_ * kFeatureCount;
      for (std::uint32_t feature = 0; feature < kFeatureCount; ++feature) {
        correction += static_cast<std::int64_t>(local_[offset + feature]) *
            features_[feature];
      }
    }
    hypothetical_ = tables_.Probability(base_logit +
        DivideRoundNearest(correction, kWeightScale));
    const std::uint32_t gate_context = local_.empty() ? 0 : context_;
    gate_open_ = !config_.gated ||
        (seen_[gate_context] >= config_.gate_warmup && regret_[gate_context] > 0);
    return gate_open_ ? hypothetical_ : base_;
  }

  void Update(int bit) {
    const std::int64_t error =
        (bit ? static_cast<std::int64_t>(kProbabilityTotal) : 0) -
        static_cast<std::int64_t>(hypothetical_);
    for (std::uint32_t feature = 0; feature < kFeatureCount; ++feature) {
      UpdateWeight(&global_[feature], error, features_[feature],
                   config_.global_shift);
    }
    if (!local_.empty()) {
      const std::size_t offset = context_ * kFeatureCount;
      for (std::uint32_t feature = 0; feature < kFeatureCount; ++feature) {
        UpdateWeight(&local_[offset + feature], error, features_[feature],
                     config_.local_shift);
      }
    }
    const std::uint32_t gate_context = local_.empty() ? 0 : context_;
    const std::int64_t gain = tables_.Loss(bit, base_) -
        tables_.Loss(bit, hypothetical_);
    regret_[gate_context] += gain -
        ShiftTowardZero(regret_[gate_context], config_.regret_shift);
    ++seen_[gate_context];
    if ((seen_[gate_context] & 1023u) == 0) {
      Decay(global_.data(), kFeatureCount);
      if (!local_.empty()) {
        Decay(local_.data() + context_ * kFeatureCount, kFeatureCount);
      }
    }
  }

 private:
  static void UpdateWeight(std::int32_t* weight, std::int64_t error,
                           std::int32_t feature, unsigned int shift) {
    const std::int64_t delta = ShiftTowardZero(error * feature, shift);
    const std::int64_t updated = static_cast<std::int64_t>(*weight) + delta;
    *weight = static_cast<std::int32_t>(std::max<std::int64_t>(
        -static_cast<std::int64_t>(kWeightScale),
        std::min<std::int64_t>(kWeightScale, updated)));
  }

  static void Decay(std::int32_t* weights, std::uint32_t count) {
    for (std::uint32_t index = 0; index < count; ++index) {
      weights[index] -= static_cast<std::int32_t>(
          ShiftTowardZero(weights[index], 18));
    }
  }

  Config config_;
  const Tables& tables_;
  std::vector<std::int32_t> global_;
  std::vector<std::int32_t> local_;
  std::vector<std::int64_t> regret_;
  std::vector<std::uint32_t> seen_;
  std::array<std::int32_t, kFeatureCount> features_{};
  std::uint32_t context_ = 0;
  std::uint16_t base_ = 32768;
  std::uint16_t hypothetical_ = 32768;
  bool gate_open_ = true;
};

struct Score {
  std::int64_t train_gain_qbits = 0;
  std::int64_t dev_gain_qbits = 0;
  std::int64_t holdout_gain_qbits = 0;
};

Score Run(const Inputs& input, const Tables& tables, const Config& config,
          std::uint64_t end, std::uint64_t train_end, std::uint64_t dev_end,
          std::vector<std::uint16_t>* output) {
  OnlineMixer mixer(config, tables);
  Score score;
  if (output != nullptr) output->resize(end);
  for (std::uint64_t row = 0; row < end; ++row) {
    const int bit = input.Bit(row);
    const std::uint16_t base = input.Base(row);
    const std::uint16_t candidate = mixer.Predict(input, row);
    const std::int64_t gain = tables.Loss(bit, base) -
        tables.Loss(bit, candidate);
    if (row < train_end) score.train_gain_qbits += gain;
    else if (row < dev_end) score.dev_gain_qbits += gain;
    else score.holdout_gain_qbits += gain;
    if (output != nullptr) (*output)[row] = candidate;
    mixer.Update(bit);
  }
  return score;
}

struct Args {
  std::string layer0_trace;
  std::string base_p1;
  std::string wrt_store;
  std::string output_p1;
  std::string output_json;
  std::uint32_t train_end_ppm = 600000;
  std::uint32_t dev_end_ppm = 800000;
};

std::string Value(int* index, int argc, char** argv) {
  if (++*index >= argc) throw std::runtime_error("missing option value");
  return argv[*index];
}

Args ParseArgs(int argc, char** argv) {
  Args args;
  for (int index = 1; index < argc; ++index) {
    const std::string option = argv[index];
    if (option == "--layer0-trace") args.layer0_trace = Value(&index, argc, argv);
    else if (option == "--base-p1") args.base_p1 = Value(&index, argc, argv);
    else if (option == "--wrt-store") args.wrt_store = Value(&index, argc, argv);
    else if (option == "--output-p1") args.output_p1 = Value(&index, argc, argv);
    else if (option == "--output-json") args.output_json = Value(&index, argc, argv);
    else if (option == "--train-end-ppm") {
      args.train_end_ppm = std::stoul(Value(&index, argc, argv));
    } else if (option == "--dev-end-ppm") {
      args.dev_end_ppm = std::stoul(Value(&index, argc, argv));
    } else {
      throw std::runtime_error("unknown option " + option);
    }
  }
  if (args.layer0_trace.empty() || args.base_p1.empty() ||
      args.wrt_store.empty() || args.output_p1.empty() || args.output_json.empty()) {
    throw std::runtime_error("all path options are required");
  }
  if (args.train_end_ppm == 0 || args.train_end_ppm >= args.dev_end_ppm ||
      args.dev_end_ppm >= kPpm) {
    throw std::runtime_error("invalid train/development boundaries");
  }
  return args;
}

std::vector<Config> Configs() {
  return {
      {"global_lr22", ContextKind::kGlobal, 22, 0, false, 12, 128},
      {"global_lr24", ContextKind::kGlobal, 24, 0, false, 12, 128},
      {"hier_bitpos_g24_l21", ContextKind::kBitPosition, 24, 21, false, 12, 128},
      {"hier_bitpos_g24_l23", ContextKind::kBitPosition, 24, 23, false, 12, 128},
      {"hier_regime_g24_l20", ContextKind::kByteRegime, 24, 20, false, 12, 128},
      {"hier_regime_g24_l22", ContextKind::kByteRegime, 24, 22, false, 12, 128},
      {"hier_regime_g24_l20_regret", ContextKind::kByteRegime, 24, 20, true, 12, 128},
      {"hier_regime_g24_l22_regret", ContextKind::kByteRegime, 24, 22, true, 14, 256},
  };
}

const char* ContextName(ContextKind kind) {
  if (kind == ContextKind::kGlobal) return "global";
  if (kind == ContextKind::kBitPosition) return "bit_position";
  return "previous_byte_class_bit_position_base_confidence";
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const Args args = ParseArgs(argc, argv);
    const Inputs input(args.layer0_trace, args.base_p1, args.wrt_store);
    const Tables tables;
    const std::uint64_t train_end = input.rows * args.train_end_ppm / kPpm;
    const std::uint64_t dev_end = input.rows * args.dev_end_ppm / kPpm;
    const std::vector<Config> configs = Configs();
    std::vector<Score> discovery;
    discovery.reserve(configs.size());
    for (const Config& config : configs) {
      discovery.push_back(Run(input, tables, config, dev_end, train_end, dev_end,
                              nullptr));
    }
    std::size_t selected = 0;
    for (std::size_t index = 1; index < configs.size(); ++index) {
      if (discovery[index].dev_gain_qbits > discovery[selected].dev_gain_qbits) {
        selected = index;
      }
    }

    std::vector<std::uint16_t> candidate;
    const Score exact = Run(input, tables, configs[selected], input.rows,
                            train_end, dev_end, &candidate);
    std::vector<std::uint16_t> confirmation;
    const Score repeated = Run(input, tables, configs[selected], input.rows,
                               train_end, dev_end, &confirmation);
    const bool deterministic = candidate == confirmation &&
        exact.train_gain_qbits == repeated.train_gain_qbits &&
        exact.dev_gain_qbits == repeated.dev_gain_qbits &&
        exact.holdout_gain_qbits == repeated.holdout_gain_qbits;

    std::vector<unsigned char> p1;
    const std::array<unsigned char, 8> magic = {
        'C', 'M', 'X', '2', '1', 'P', '1', 0};
    p1.insert(p1.end(), magic.begin(), magic.end());
    AppendU64(&p1, input.rows);
    p1.reserve(16 + 2 * input.rows);
    for (std::uint16_t probability : candidate) {
      p1.push_back(static_cast<unsigned char>(probability));
      p1.push_back(static_cast<unsigned char>(probability >> 8));
    }
    WriteFile(args.output_p1, p1);

    std::ofstream output(args.output_json);
    if (!output) throw std::runtime_error("cannot create output JSON");
    output << "{\n";
    output << "  \"schema\": \"compact_layer0_online_mixer_screen_v1\",\n";
    output << "  \"evidence_level\": \"causal_train_dev_selected_pre_exact_replay\",\n";
    output << "  \"scope\": {\"rows\": " << input.rows
           << ", \"train_end_row\": " << train_end
           << ", \"dev_end_row\": " << dev_end
           << ", \"selection_reads_holdout\": false},\n";
    output << "  \"causality\": {\"prediction_precedes_current_truth\": true, "
           << "\"weights_update_after_current_truth\": true, "
           << "\"previous_byte_context_only\": true, "
           << "\"shipped_weights_required\": false},\n";
    output << "  \"configs\": [\n";
    for (std::size_t index = 0; index < configs.size(); ++index) {
      const Config& config = configs[index];
      output << "    {\"name\": \"" << config.name
             << "\", \"context\": \"" << ContextName(config.context)
             << "\", \"global_shift\": " << config.global_shift
             << ", \"local_shift\": " << config.local_shift
             << ", \"gated\": " << (config.gated ? "true" : "false")
             << ", \"train_gain_qbits\": " << discovery[index].train_gain_qbits
             << ", \"dev_gain_qbits\": " << discovery[index].dev_gain_qbits
             << "}" << (index + 1 == configs.size() ? "\n" : ",\n");
    }
    output << "  ],\n";
    output << "  \"selection\": {\"name\": \"" << configs[selected].name
           << "\", \"index\": " << selected
           << ", \"dev_gain_qbits\": " << discovery[selected].dev_gain_qbits
           << "},\n";
    output << "  \"qbit_replay\": {\"train_gain_qbits\": "
           << exact.train_gain_qbits << ", \"dev_gain_qbits\": "
           << exact.dev_gain_qbits << ", \"holdout_gain_qbits\": "
           << exact.holdout_gain_qbits << "},\n";
    output << "  \"deterministic_probability_replay\": "
           << (deterministic ? "true" : "false") << ",\n";
    output << "  \"candidate_p1_path\": \"" << args.output_p1 << "\",\n";
    output << "  \"claim_boundary\": \"Causal probability replay only; exact "
           << "range coding, native integration, program accounting, memory, and "
           << "full-corpus proof remain required.\"\n";
    output << "}\n";
    if (!output) throw std::runtime_error("cannot write output JSON");
    return deterministic ? 0 : 2;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
