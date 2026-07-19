// Decoder-causal fixed-share stack over preserved probability endpoints.
// Configuration selection reads development rows only; the selected model is
// replayed from an empty state before sealed holdout is measured.

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
#include <utility>
#include <vector>

namespace {

constexpr std::uint64_t kScale = std::uint64_t{1} << 40;
constexpr std::uint64_t kPpm = 1000000;
constexpr std::uint32_t kProbabilityTotal = 65536;

std::vector<unsigned char> ReadFile(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open " + path);
  input.seekg(0, std::ios::end);
  const std::streamoff size = input.tellg();
  if (size < 0) throw std::runtime_error("cannot size " + path);
  input.seekg(0, std::ios::beg);
  std::vector<unsigned char> result(static_cast<std::size_t>(size));
  if (!result.empty()) input.read(reinterpret_cast<char*>(result.data()), size);
  if (!input) throw std::runtime_error("cannot read " + path);
  return result;
}

void WriteFile(const std::string& path, const std::vector<unsigned char>& data) {
  std::ofstream output(path, std::ios::binary);
  if (!output) throw std::runtime_error("cannot create " + path);
  output.write(reinterpret_cast<const char*>(data.data()), data.size());
  if (!output) throw std::runtime_error("cannot write " + path);
}

std::uint64_t ReadU64(const unsigned char* input) {
  std::uint64_t value = 0;
  for (unsigned shift = 0; shift < 64; shift += 8) {
    value |= std::uint64_t{*input++} << shift;
  }
  return value;
}

void AppendU64(std::vector<unsigned char>* output, std::uint64_t value) {
  for (unsigned shift = 0; shift < 64; shift += 8) {
    output->push_back(static_cast<unsigned char>(value >> shift));
  }
}

struct Endpoint {
  std::string name;
  std::string path;
  std::vector<unsigned char> data;
  std::uint64_t rows = 0;

  std::uint16_t Probability(std::uint64_t row) const {
    const unsigned char* p = data.data() + 16 + row * 2;
    return static_cast<std::uint16_t>(p[0] | (std::uint16_t{p[1]} << 8));
  }
};

Endpoint ReadEndpoint(const std::string& specification) {
  const std::size_t separator = specification.find('=');
  if (separator == std::string::npos || separator == 0 ||
      separator + 1 == specification.size()) {
    throw std::runtime_error("endpoint must be NAME=PATH");
  }
  Endpoint endpoint;
  endpoint.name = specification.substr(0, separator);
  endpoint.path = specification.substr(separator + 1);
  endpoint.data = ReadFile(endpoint.path);
  if (endpoint.data.size() < 16) {
    throw std::runtime_error("endpoint header is truncated: " + endpoint.path);
  }
  endpoint.rows = ReadU64(endpoint.data.data() + 8);
  if (endpoint.rows == 0 || endpoint.data.size() != 16 + endpoint.rows * 2) {
    throw std::runtime_error("endpoint dimensions are invalid: " + endpoint.path);
  }
  return endpoint;
}

struct Truth {
  explicit Truth(const std::string& path) : path(path), data(ReadFile(path)) {
    if (data.size() < 6) throw std::runtime_error("truth store is truncated");
    rows = (data.size() - 5) * 8;
  }

  int Bit(std::uint64_t row) const {
    return (data[5 + row / 8] >> (7 - (row & 7))) & 1;
  }

  unsigned char PreviousByte(std::uint64_t row) const {
    const std::uint64_t byte = row / 8;
    return byte == 0 ? 0 : data[5 + byte - 1];
  }

  std::string path;
  std::vector<unsigned char> data;
  std::uint64_t rows = 0;
};

enum class ContextKind { kGlobal, kBitPosition, kByteRegime };

struct Config {
  std::string name;
  ContextKind context;
  std::uint32_t base_prior_ppm;
  std::uint32_t share_ppm;
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

std::uint32_t ConfidenceBin(std::uint16_t probability) {
  const std::uint32_t distance = probability > 32768
      ? probability - 32768 : 32768 - probability;
  if (distance < 4096) return 0;
  if (distance < 12288) return 1;
  if (distance < 24576) return 2;
  return 3;
}

std::uint32_t ContextCount(ContextKind kind) {
  if (kind == ContextKind::kGlobal) return 1;
  if (kind == ContextKind::kBitPosition) return 8;
  return 8 * 8 * 4;
}

std::uint32_t Context(const Config& config, const Truth& truth,
                      std::uint64_t row, std::uint16_t base) {
  if (config.context == ContextKind::kGlobal) return 0;
  if (config.context == ContextKind::kBitPosition) return row & 7;
  return ((row & 7) * 8 + ByteClass(truth.PreviousByte(row))) * 4 +
      ConfidenceBin(base);
}

const char* ContextName(ContextKind kind) {
  if (kind == ContextKind::kGlobal) return "global";
  if (kind == ContextKind::kBitPosition) return "bit_position";
  return "previous_byte_class_bit_position_base_confidence";
}

struct LossTables {
  LossTables() {
    for (std::uint32_t p = 1; p < kProbabilityTotal; ++p) {
      loss0[p] = static_cast<std::int32_t>(
          -std::log2(double(kProbabilityTotal - p) / kProbabilityTotal) *
              256.0 + 0.5);
      loss1[p] = static_cast<std::int32_t>(
          -std::log2(double(p) / kProbabilityTotal) * 256.0 + 0.5);
    }
  }

  std::int32_t Loss(int bit, std::uint16_t probability) const {
    return bit ? loss1[probability] : loss0[probability];
  }

  std::array<std::int32_t, kProbabilityTotal> loss0{};
  std::array<std::int32_t, kProbabilityTotal> loss1{};
};

class FixedShareStack {
 public:
  FixedShareStack(const Config& config, std::size_t endpoint_count)
      : config_(config), endpoint_count_(endpoint_count),
        prior_(endpoint_count),
        weights_(ContextCount(config.context) * endpoint_count) {
    if (endpoint_count < 2) throw std::runtime_error("at least two endpoints required");
    const std::uint64_t base =
        (kScale * config.base_prior_ppm + kPpm / 2) / kPpm;
    prior_[0] = base;
    const std::uint64_t alternate = (kScale - base) / (endpoint_count - 1);
    for (std::size_t i = 1; i < endpoint_count; ++i) prior_[i] = alternate;
    prior_.back() += kScale - Sum(prior_.data());
    for (std::uint32_t context = 0; context < ContextCount(config.context);
         ++context) {
      std::copy(prior_.begin(), prior_.end(),
                weights_.begin() + context * endpoint_count);
    }
    share_ = (kScale * config.share_ppm + kPpm / 2) / kPpm;
  }

  std::uint16_t Predict(std::uint32_t context,
                        const std::vector<std::uint16_t>& probabilities) {
    context_ = context;
    probabilities_ = probabilities;
    const std::uint64_t* weights = &weights_[context * endpoint_count_];
    unsigned __int128 numerator = 0;
    for (std::size_t i = 0; i < endpoint_count_; ++i) {
      numerator += static_cast<unsigned __int128>(weights[i]) * probabilities[i];
    }
    const std::uint64_t total = Sum(weights);
    const std::uint64_t mixed = static_cast<std::uint64_t>(
        (numerator + total / 2) / total);
    return static_cast<std::uint16_t>(std::max<std::uint64_t>(
        1, std::min<std::uint64_t>(kProbabilityTotal - 1, mixed)));
  }

  void Update(int bit) {
    std::uint64_t* weights = &weights_[context_ * endpoint_count_];
    std::vector<unsigned __int128> unnormalized(endpoint_count_);
    unsigned __int128 total = 0;
    for (std::size_t i = 0; i < endpoint_count_; ++i) {
      const std::uint64_t likelihood = bit ? probabilities_[i]
          : kProbabilityTotal - probabilities_[i];
      unnormalized[i] = static_cast<unsigned __int128>(weights[i]) * likelihood;
      total += unnormalized[i];
    }
    std::uint64_t assigned = 0;
    for (std::size_t i = 0; i < endpoint_count_; ++i) {
      const std::uint64_t posterior = static_cast<std::uint64_t>(
          (unnormalized[i] * kScale + total / 2) / total);
      const unsigned __int128 shared =
          static_cast<unsigned __int128>(kScale - share_) * posterior +
          static_cast<unsigned __int128>(share_) * prior_[i];
      weights[i] = std::max<std::uint64_t>(1,
          static_cast<std::uint64_t>((shared + kScale / 2) / kScale));
      assigned += weights[i];
    }
    if (assigned != kScale) {
      const std::int64_t delta = static_cast<std::int64_t>(kScale) -
          static_cast<std::int64_t>(assigned);
      weights[0] = static_cast<std::uint64_t>(
          static_cast<std::int64_t>(weights[0]) + delta);
    }
  }

 private:
  std::uint64_t Sum(const std::uint64_t* values) const {
    std::uint64_t result = 0;
    for (std::size_t i = 0; i < endpoint_count_; ++i) result += values[i];
    return result;
  }

  Config config_;
  std::size_t endpoint_count_;
  std::vector<std::uint64_t> prior_;
  std::vector<std::uint64_t> weights_;
  std::uint64_t share_ = 0;
  std::uint32_t context_ = 0;
  std::vector<std::uint16_t> probabilities_;
};

class RangeEncoder {
 public:
  void Encode(int bit, std::uint16_t p1) {
    const std::uint32_t span = x2_ - x1_;
    const std::uint32_t midpoint = x1_ + (span >> 16) * p1 +
        (((span & 0xffff) * p1) >> 16);
    if (bit) x2_ = midpoint;
    else x1_ = midpoint + 1;
    while (((x1_ ^ x2_) & 0xff000000) == 0) {
      output_.push_back(static_cast<unsigned char>(x2_ >> 24));
      x1_ <<= 8;
      x2_ = (x2_ << 8) + 255;
    }
  }

  std::vector<unsigned char> Finish() {
    while (((x1_ ^ x2_) & 0xff000000) == 0) {
      output_.push_back(static_cast<unsigned char>(x2_ >> 24));
      x1_ <<= 8;
      x2_ = (x2_ << 8) + 255;
    }
    output_.push_back(static_cast<unsigned char>(x2_ >> 24));
    return output_;
  }

 private:
  std::uint32_t x1_ = 0;
  std::uint32_t x2_ = 0xffffffff;
  std::vector<unsigned char> output_;
};

struct Score {
  std::int64_t train_gain_qbits = 0;
  std::int64_t dev_gain_qbits = 0;
  std::int64_t holdout_gain_qbits = 0;
  std::vector<std::uint16_t> probabilities;
};

Score Run(const Config& config, const std::vector<Endpoint>& endpoints,
          const Truth& truth, const LossTables& tables, std::uint64_t end,
          std::uint64_t train_end, std::uint64_t dev_end, bool save) {
  FixedShareStack stack(config, endpoints.size());
  Score score;
  if (save) score.probabilities.resize(end);
  std::vector<std::uint16_t> probabilities(endpoints.size());
  for (std::uint64_t row = 0; row < end; ++row) {
    for (std::size_t i = 0; i < endpoints.size(); ++i) {
      probabilities[i] = endpoints[i].Probability(row);
    }
    const int bit = truth.Bit(row);
    const std::uint16_t candidate = stack.Predict(
        Context(config, truth, row, probabilities[0]), probabilities);
    const std::int64_t gain = tables.Loss(bit, probabilities[0]) -
        tables.Loss(bit, candidate);
    if (row < train_end) score.train_gain_qbits += gain;
    else if (row < dev_end) score.dev_gain_qbits += gain;
    else score.holdout_gain_qbits += gain;
    if (save) score.probabilities[row] = candidate;
    stack.Update(bit);
  }
  return score;
}

std::pair<std::size_t, std::size_t> ExactBytes(
    const Truth& truth, const Endpoint& base,
    const std::vector<std::uint16_t>& candidate,
    std::uint64_t start, std::uint64_t end) {
  RangeEncoder base_encoder;
  RangeEncoder candidate_encoder;
  for (std::uint64_t row = start; row < end; ++row) {
    const int bit = truth.Bit(row);
    base_encoder.Encode(bit, base.Probability(row));
    candidate_encoder.Encode(bit, candidate[row]);
  }
  return {base_encoder.Finish().size(), candidate_encoder.Finish().size()};
}

struct Args {
  std::vector<std::string> endpoint_specs;
  std::string truth_store;
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
    if (option == "--endpoint") args.endpoint_specs.push_back(Value(&index, argc, argv));
    else if (option == "--wrt-store") args.truth_store = Value(&index, argc, argv);
    else if (option == "--output-p1") args.output_p1 = Value(&index, argc, argv);
    else if (option == "--output-json") args.output_json = Value(&index, argc, argv);
    else if (option == "--train-end-ppm") args.train_end_ppm = std::stoul(Value(&index, argc, argv));
    else if (option == "--dev-end-ppm") args.dev_end_ppm = std::stoul(Value(&index, argc, argv));
    else throw std::runtime_error("unknown option " + option);
  }
  if (args.endpoint_specs.size() < 2 || args.truth_store.empty() ||
      args.output_p1.empty() || args.output_json.empty()) {
    throw std::runtime_error("two endpoints and all output/truth paths are required");
  }
  if (args.train_end_ppm == 0 || args.train_end_ppm >= args.dev_end_ppm ||
      args.dev_end_ppm >= kPpm) throw std::runtime_error("invalid split boundaries");
  return args;
}

std::vector<Config> Configs() {
  return {
      {"global_p90_s10", ContextKind::kGlobal, 900000, 10},
      {"global_p99_s10", ContextKind::kGlobal, 990000, 10},
      {"bitpos_p90_s10", ContextKind::kBitPosition, 900000, 10},
      {"bitpos_p99_s10", ContextKind::kBitPosition, 990000, 10},
      {"regime_p90_s10", ContextKind::kByteRegime, 900000, 10},
      {"regime_p99_s10", ContextKind::kByteRegime, 990000, 10},
      {"regime_p99_s1000", ContextKind::kByteRegime, 990000, 1000},
  };
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const Args args = ParseArgs(argc, argv);
    const Truth truth(args.truth_store);
    std::vector<Endpoint> endpoints;
    for (const std::string& specification : args.endpoint_specs) {
      endpoints.push_back(ReadEndpoint(specification));
      if (endpoints.back().rows != truth.rows) {
        throw std::runtime_error("endpoint and truth row counts differ");
      }
    }
    const std::uint64_t train_end = truth.rows * args.train_end_ppm / kPpm;
    const std::uint64_t dev_end = truth.rows * args.dev_end_ppm / kPpm;
    const LossTables tables;
    const std::vector<Config> configs = Configs();
    std::vector<Score> discovery;
    for (const Config& config : configs) {
      discovery.push_back(Run(config, endpoints, truth, tables, dev_end,
                              train_end, dev_end, false));
    }
    std::size_t selected = 0;
    for (std::size_t i = 1; i < configs.size(); ++i) {
      if (discovery[i].dev_gain_qbits > discovery[selected].dev_gain_qbits) {
        selected = i;
      }
    }
    const Score exact = Run(configs[selected], endpoints, truth, tables,
                            truth.rows, train_end, dev_end, true);
    const Score repeated = Run(configs[selected], endpoints, truth, tables,
                               truth.rows, train_end, dev_end, true);
    const bool deterministic = exact.probabilities == repeated.probabilities &&
        exact.train_gain_qbits == repeated.train_gain_qbits &&
        exact.dev_gain_qbits == repeated.dev_gain_qbits &&
        exact.holdout_gain_qbits == repeated.holdout_gain_qbits;
    const auto full = ExactBytes(truth, endpoints[0], exact.probabilities,
                                 0, truth.rows);
    const auto holdout = ExactBytes(truth, endpoints[0], exact.probabilities,
                                    dev_end, truth.rows);

    std::vector<unsigned char> p1 = {'C', 'M', 'X', '2', '1', 'P', '1', 0};
    AppendU64(&p1, truth.rows);
    p1.reserve(16 + 2 * truth.rows);
    for (std::uint16_t probability : exact.probabilities) {
      p1.push_back(static_cast<unsigned char>(probability));
      p1.push_back(static_cast<unsigned char>(probability >> 8));
    }
    WriteFile(args.output_p1, p1);

    std::ofstream output(args.output_json);
    if (!output) throw std::runtime_error("cannot create output JSON");
    output << "{\n  \"schema\": \"endpoint_fixed_share_stack_v1\",\n";
    output << "  \"evidence_level\": \"causal_dev_selected_exact_arithmetic_shadow\",\n";
    output << "  \"scope\": {\"rows\": " << truth.rows
           << ", \"train_end_row\": " << train_end
           << ", \"dev_end_row\": " << dev_end
           << ", \"selection_reads_holdout\": false},\n";
    output << "  \"causality\": {\"prediction_precedes_truth\": true, "
              "\"posterior_updates_after_truth\": true, "
              "\"shipped_weights_required\": false},\n";
    output << "  \"endpoints\": [";
    for (std::size_t i = 0; i < endpoints.size(); ++i) {
      output << (i ? ", " : "") << "\"" << endpoints[i].name << "\"";
    }
    output << "],\n  \"configs\": [\n";
    for (std::size_t i = 0; i < configs.size(); ++i) {
      output << "    {\"name\": \"" << configs[i].name
             << "\", \"context\": \"" << ContextName(configs[i].context)
             << "\", \"base_prior_ppm\": " << configs[i].base_prior_ppm
             << ", \"share_ppm\": " << configs[i].share_ppm
             << ", \"train_gain_qbits\": " << discovery[i].train_gain_qbits
             << ", \"dev_gain_qbits\": " << discovery[i].dev_gain_qbits
             << "}" << (i + 1 == configs.size() ? "\n" : ",\n");
    }
    output << "  ],\n  \"selection\": {\"index\": " << selected
           << ", \"name\": \"" << configs[selected].name << "\"},\n";
    output << "  \"qbit_replay\": {\"train_gain_qbits\": "
           << exact.train_gain_qbits << ", \"dev_gain_qbits\": "
           << exact.dev_gain_qbits << ", \"holdout_gain_qbits\": "
           << exact.holdout_gain_qbits << "},\n";
    output << "  \"exact_replay\": {\"full\": {\"base_payload_bytes\": "
           << full.first << ", \"candidate_payload_bytes\": " << full.second
           << ", \"saved_bytes\": "
           << static_cast<std::int64_t>(full.first) - full.second
           << "}, \"holdout\": {\"base_payload_bytes\": " << holdout.first
           << ", \"candidate_payload_bytes\": " << holdout.second
           << ", \"saved_bytes\": "
           << static_cast<std::int64_t>(holdout.first) - holdout.second
           << "}},\n";
    output << "  \"deterministic_probability_replay\": "
           << (deterministic ? "true" : "false") << ",\n";
    output << "  \"claim_boundary\": \"Causal trace replay only; endpoint "
              "integration, counted code, native roundtrip, resources, broader "
              "transfer, and full-corpus proof remain required.\"\n}\n";
    if (!output) throw std::runtime_error("cannot write output JSON");
    return deterministic ? 0 : 2;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
