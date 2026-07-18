// Matched-stream endpoint economics screen for the constructive no-PAQ 96x2
// CMIX21/FX2 hybrid.
//
// The input trace is emitted by the quarantined CMIX_MATCHED_TRACE build.  It
// contains the exact archive-producing 96x2 post-SSE probability, continuous
// 160/200-cell byte endpoints, and every layer-0 mixer endpoint before the
// current bit is learned.  This tool selects only on the development prefix,
// then performs byte-exact CMIX range-coder encode/decode replay.

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

constexpr std::uint32_t kTraceVersion = 1;
constexpr std::uint32_t kTraceHeaderBytes = 36;
constexpr std::uint32_t kFixedEndpoints = 5;
constexpr std::uint64_t kPpm = 1000000;
constexpr std::uint64_t kProbabilityTotal = 65536;
constexpr std::uint32_t kRangeMask = 0xffffffffu;

std::uint32_t ReadU32(const unsigned char* p) {
  return static_cast<std::uint32_t>(p[0]) |
      (static_cast<std::uint32_t>(p[1]) << 8) |
      (static_cast<std::uint32_t>(p[2]) << 16) |
      (static_cast<std::uint32_t>(p[3]) << 24);
}

std::uint64_t ReadU64(const unsigned char* p) {
  std::uint64_t value = 0;
  for (unsigned int i = 0; i < 8; ++i) {
    value |= static_cast<std::uint64_t>(p[i]) << (8 * i);
  }
  return value;
}

std::string JsonEscape(const std::string& value) {
  std::ostringstream out;
  for (unsigned char c : value) {
    switch (c) {
      case '\\': out << "\\\\"; break;
      case '"': out << "\\\""; break;
      case '\n': out << "\\n"; break;
      case '\r': out << "\\r"; break;
      case '\t': out << "\\t"; break;
      default:
        if (c < 0x20) {
          out << "\\u" << std::hex << std::setw(4) << std::setfill('0')
              << static_cast<unsigned int>(c) << std::dec;
        } else {
          out << c;
        }
    }
  }
  return out.str();
}

std::vector<unsigned char> ReadFile(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) throw std::runtime_error("cannot open: " + path);
  in.seekg(0, std::ios::end);
  const std::streamoff length = in.tellg();
  if (length < 0) throw std::runtime_error("cannot size: " + path);
  in.seekg(0, std::ios::beg);
  std::vector<unsigned char> data(static_cast<std::size_t>(length));
  if (!data.empty()) {
    in.read(reinterpret_cast<char*>(data.data()), length);
    if (!in) throw std::runtime_error("cannot read: " + path);
  }
  return data;
}

void WriteFile(const std::string& path, const std::vector<unsigned char>& data) {
  if (path.empty()) return;
  std::ofstream out(path, std::ios::binary);
  if (!out) throw std::runtime_error("cannot create: " + path);
  if (!data.empty()) {
    out.write(reinterpret_cast<const char*>(data.data()), data.size());
  }
  if (!out) throw std::runtime_error("cannot write: " + path);
}

struct Trace {
  explicit Trace(const std::string& path) : bytes(ReadFile(path)) {
    if (bytes.size() < kTraceHeaderBytes) {
      throw std::runtime_error("trace shorter than header");
    }
    const std::array<unsigned char, 8> expected = {
        'C', 'M', 'N', 'E', 'S', 'T', '1', 0};
    if (!std::equal(expected.begin(), expected.end(), bytes.begin())) {
      throw std::runtime_error("matched trace magic mismatch");
    }
    version = ReadU32(bytes.data() + 8);
    header_bytes = ReadU32(bytes.data() + 12);
    row_bytes = ReadU32(bytes.data() + 16);
    endpoint_count = ReadU32(bytes.data() + 20);
    internal_endpoint_count = endpoint_count;
    layer0_count = ReadU32(bytes.data() + 24);
    rows = ReadU64(bytes.data() + 28);
    if (version != kTraceVersion || header_bytes != kTraceHeaderBytes) {
      throw std::runtime_error("unsupported matched trace version/header");
    }
    const bool full_nested_contract =
        endpoint_count == kFixedEndpoints + layer0_count;
    const bool minimal_base_contract = endpoint_count == 1 && layer0_count == 0;
    if ((!full_nested_contract && !minimal_base_contract) ||
        row_bytes != 1 + 2 * endpoint_count) {
      throw std::runtime_error("matched trace endpoint/row contract mismatch");
    }
    const std::uint64_t expected_size =
        static_cast<std::uint64_t>(header_bytes) + rows * row_bytes;
    if (expected_size != bytes.size()) {
      throw std::runtime_error("matched trace row count/file size mismatch");
    }
    if (rows == 0) throw std::runtime_error("matched trace has zero rows");
  }

  const unsigned char* Row(std::uint64_t row) const {
    return bytes.data() + header_bytes + row * row_bytes;
  }

  int Bit(std::uint64_t row) const { return Row(row)[0]; }

  std::uint32_t P1(std::uint64_t row, std::uint32_t endpoint) const {
    if (endpoint == internal_endpoint_count && !external_p1.empty()) {
      return external_p1[row];
    }
    const unsigned char* p = Row(row) + 1 + 2 * endpoint;
    return static_cast<std::uint32_t>(p[0]) |
        (static_cast<std::uint32_t>(p[1]) << 8);
  }

  std::string EndpointName(std::uint32_t endpoint) const {
    if (endpoint == internal_endpoint_count && !external_p1.empty()) {
      return external_endpoint_name;
    }
    switch (endpoint) {
      case 0: return "base_post_sse_96x2";
      case 1: return "base_pre_sse_96x2";
      case 2: return "byte_lstm96_continuous";
      case 3: return "byte_lstm160_continuous_probe";
      case 4: return "byte_lstm200_continuous_probe";
      default: {
        static const std::array<const char*, 26> layer0_names = {
            "layer0_byte0_ctx8_lr005",
            "layer0_byte0_ctx8_lr0005",
            "layer0_byte1_ctx8_lr005",
            "layer0_byte1_ctx8_lr0005",
            "layer0_byte2_ctx4_lr005",
            "layer0_byte3_ctx2_lr002",
            "layer0_recent_byte2_lr002",
            "layer0_recent_byte3_lr005",
            "layer0_zero_context_lr00005",
            "layer0_line_break_lr0007",
            "layer0_longest_match_lr0005",
            "layer0_wrt_context_lr002",
            "layer0_auxiliary_context_lr0005",
            "layer0_interval_ascii_thresholds_lr001",
            "layer0_interval_markup_thresholds_lr001",
            "layer0_interval_alnum_unicode_lr001",
            "layer0_bitctx_alnum_unicode_lr005",
            "layer0_interval_classmap_a_lr001",
            "layer0_interval_classmap_a15_lr001",
            "layer0_bitctx_classmap_a_lr005",
            "layer0_interval_classmap_b_lr001",
            "layer0_intervalhash_classmap_b_lr001",
            "layer0_bitctx_classmap_b_lr005",
            "layer0_bitctx_previous_byte_lr005",
            "layer0_combined_recent1_recent0_lr005",
            "layer0_combined_recent2_recent1_lr003"};
        const std::uint32_t index = endpoint - kFixedEndpoints;
        if (index < layer0_names.size()) return layer0_names[index];
        return "layer0_mixer_" + std::to_string(index);
      }
    }
  }

  void LoadExternalEndpoint(const std::string& path, const std::string& name) {
    const std::vector<unsigned char> data = ReadFile(path);
    if (data.size() < 16 ||
        !std::equal(data.begin(), data.begin() + 8,
            std::array<unsigned char, 8>{'C', 'M', 'X', '2', '1', 'P', '1', 0}.begin())) {
      throw std::runtime_error("external endpoint magic mismatch");
    }
    const std::uint64_t external_rows = ReadU64(data.data() + 8);
    if (external_rows != rows || data.size() != 16 + 2 * rows) {
      throw std::runtime_error("external endpoint row count/size mismatch");
    }
    external_p1.resize(rows);
    for (std::uint64_t row = 0; row < rows; ++row) {
      const unsigned char* p = data.data() + 16 + 2 * row;
      external_p1[row] = static_cast<std::uint32_t>(p[0]) |
          (static_cast<std::uint32_t>(p[1]) << 8);
    }
    external_endpoint_name = name;
    endpoint_count = internal_endpoint_count + 1;
  }

  std::vector<unsigned char> bytes;
  std::uint32_t version = 0;
  std::uint32_t header_bytes = 0;
  std::uint32_t row_bytes = 0;
  std::uint32_t endpoint_count = 0;
  std::uint32_t internal_endpoint_count = 0;
  std::uint32_t layer0_count = 0;
  std::uint64_t rows = 0;
  std::vector<std::uint32_t> external_p1;
  std::string external_endpoint_name;
};

void ExportBaseEndpoint(const Trace& trace, const std::string& path) {
  if (path.empty()) return;
  std::vector<unsigned char> output;
  output.reserve(static_cast<std::size_t>(16 + 2 * trace.rows));
  const std::array<unsigned char, 8> magic = {
      'F', 'X', '2', 'P', '1', 'V', '1', 0};
  output.insert(output.end(), magic.begin(), magic.end());
  for (unsigned int shift = 0; shift < 64; shift += 8) {
    output.push_back(static_cast<unsigned char>(trace.rows >> shift));
  }
  for (std::uint64_t row = 0; row < trace.rows; ++row) {
    const std::uint32_t p1 = trace.P1(row, 0);
    output.push_back(static_cast<unsigned char>(p1));
    output.push_back(static_cast<unsigned char>(p1 >> 8));
  }
  WriteFile(path, output);
}

class CmixRangeEncoder {
 public:
  void Encode(int bit, std::uint32_t p1) {
    if (p1 == 0 || p1 >= kProbabilityTotal) {
      throw std::runtime_error("probability outside CMIX coder range");
    }
    const std::uint32_t span = x2_ - x1_;
    const std::uint32_t xmid = x1_ + (span >> 16) * p1 +
        ((span & 0xffffu) * p1 >> 16);
    if (bit) {
      x2_ = xmid;
    } else {
      x1_ = xmid + 1;
    }
    Normalize();
  }

  void Finish() {
    Normalize();
    output_.push_back(static_cast<unsigned char>(x2_ >> 24));
  }

  const std::vector<unsigned char>& Output() const { return output_; }

 private:
  void Normalize() {
    while (((x1_ ^ x2_) & 0xff000000u) == 0) {
      output_.push_back(static_cast<unsigned char>(x2_ >> 24));
      x1_ <<= 8;
      x2_ = (x2_ << 8) + 255;
    }
  }

  std::uint32_t x1_ = 0;
  std::uint32_t x2_ = kRangeMask;
  std::vector<unsigned char> output_;
};

class CmixRangeDecoder {
 public:
  explicit CmixRangeDecoder(const std::vector<unsigned char>& input)
      : input_(input) {
    for (int i = 0; i < 4; ++i) x_ = (x_ << 8) + ReadByte();
  }

  int Decode(std::uint32_t p1) {
    const std::uint32_t span = x2_ - x1_;
    const std::uint32_t xmid = x1_ + (span >> 16) * p1 +
        ((span & 0xffffu) * p1 >> 16);
    int bit = 0;
    if (x_ <= xmid) {
      bit = 1;
      x2_ = xmid;
    } else {
      x1_ = xmid + 1;
    }
    while (((x1_ ^ x2_) & 0xff000000u) == 0) {
      x1_ <<= 8;
      x2_ = (x2_ << 8) + 255;
      x_ = (x_ << 8) + ReadByte();
    }
    return bit;
  }

 private:
  std::uint32_t ReadByte() {
    if (position_ >= input_.size()) return 0;
    return input_[position_++];
  }

  const std::vector<unsigned char>& input_;
  std::size_t position_ = 0;
  std::uint32_t x1_ = 0;
  std::uint32_t x2_ = kRangeMask;
  std::uint32_t x_ = 0;
};

std::uint32_t MixFixed(
    std::uint32_t base, std::uint32_t endpoint, std::uint32_t weight_ppm) {
  const std::uint64_t numerator =
      static_cast<std::uint64_t>(base) * (kPpm - weight_ppm) +
      static_cast<std::uint64_t>(endpoint) * weight_ppm + kPpm / 2;
  return std::max<std::uint32_t>(1, std::min<std::uint32_t>(65535,
      static_cast<std::uint32_t>(numerator / kPpm)));
}

std::uint32_t MixCentered(std::uint32_t base, std::uint32_t endpoint,
    std::int32_t coefficient_ppm) {
  const std::int64_t product =
      (static_cast<std::int64_t>(endpoint) - 32768) * coefficient_ppm;
  const std::int64_t correction = product >= 0
      ? (product + static_cast<std::int64_t>(kPpm / 2)) /
          static_cast<std::int64_t>(kPpm)
      : -((-product + static_cast<std::int64_t>(kPpm / 2)) /
          static_cast<std::int64_t>(kPpm));
  const std::int64_t mixed = static_cast<std::int64_t>(base) + correction;
  return static_cast<std::uint32_t>(std::max<std::int64_t>(1,
      std::min<std::int64_t>(65535, mixed)));
}

class FixedSharePosterior {
 public:
  FixedSharePosterior(std::uint32_t prior_ppm, std::uint32_t share_ppm,
      unsigned int weight_bits = 24)
      : scale_(std::uint64_t{1} << weight_bits) {
    initial_ = (scale_ * prior_ppm + kPpm / 2) / kPpm;
    initial_ = std::max<std::uint64_t>(1,
        std::min<std::uint64_t>(scale_ - 1, initial_));
    weight_ = initial_;
    share_ = (scale_ * share_ppm + kPpm / 2) / kPpm;
    share_ = std::min(scale_, share_);
  }

  std::uint32_t Mix(std::uint32_t base, std::uint32_t endpoint) const {
    const std::uint64_t numerator =
        (scale_ - weight_) * base + weight_ * endpoint + scale_ / 2;
    return std::max<std::uint32_t>(1, std::min<std::uint32_t>(65535,
        static_cast<std::uint32_t>(numerator / scale_)));
  }

  void Update(int bit, std::uint32_t base, std::uint32_t endpoint) {
    const std::uint64_t base_likelihood = bit ? base : kProbabilityTotal - base;
    const std::uint64_t endpoint_likelihood =
        bit ? endpoint : kProbabilityTotal - endpoint;
    const std::uint64_t endpoint_numerator = weight_ * endpoint_likelihood;
    const std::uint64_t denominator = endpoint_numerator +
        (scale_ - weight_) * base_likelihood;
    const unsigned __int128 scaled =
        static_cast<unsigned __int128>(endpoint_numerator) * scale_;
    std::uint64_t posterior = static_cast<std::uint64_t>(
        (scaled + denominator / 2) / denominator);
    posterior = std::max<std::uint64_t>(1,
        std::min<std::uint64_t>(scale_ - 1, posterior));
    const std::uint64_t shared =
        ((scale_ - share_) * posterior + share_ * initial_ + scale_ / 2) /
        scale_;
    weight_ = std::max<std::uint64_t>(1,
        std::min<std::uint64_t>(scale_ - 1, shared));
  }

 private:
  std::uint64_t scale_ = 0;
  std::uint64_t initial_ = 0;
  std::uint64_t weight_ = 0;
  std::uint64_t share_ = 0;
};

enum class ConfigKind { kFixed, kCentered, kCausal };

struct Config {
  ConfigKind kind = ConfigKind::kFixed;
  std::uint32_t endpoint = 1;
  std::uint32_t weight_ppm = 0;
  std::int32_t centered_coefficient_ppm = 0;
  std::uint32_t prior_ppm = 500000;
  std::uint32_t share_ppm = 1000;
  double train_loss = 0;
  double dev_loss = 0;
  double dev_gain_bits = -std::numeric_limits<double>::infinity();
  double oracle_dev_gain_bits = 0;
};

std::string ConfigKindName(ConfigKind kind) {
  if (kind == ConfigKind::kFixed) return "fixed_blend";
  if (kind == ConfigKind::kCentered) return "centered_residual";
  return "causal_fixed_share";
}

std::uint32_t Probability(const Config& config, FixedSharePosterior* posterior,
    std::uint32_t base, std::uint32_t endpoint) {
  if (config.kind == ConfigKind::kFixed) {
    return MixFixed(base, endpoint, config.weight_ppm);
  }
  if (config.kind == ConfigKind::kCentered) {
    return MixCentered(base, endpoint, config.centered_coefficient_ppm);
  }
  return posterior->Mix(base, endpoint);
}

std::size_t CmixHeaderBytes(const std::vector<unsigned char>& archive) {
  if (archive.size() < 5) throw std::runtime_error("base archive lacks header");
  std::uint64_t length = 0;
  for (int i = 0; i < 5; ++i) {
    unsigned char c = archive[i];
    if (i == 0) c &= 0x7f;
    length = (length << 8) + c;
  }
  const std::size_t header = length >= 10000 ? 37 : 5;
  if (archive.size() < header) throw std::runtime_error("base archive header truncated");
  return header;
}

struct Args {
  std::string trace;
  std::string base_archive;
  std::string reference_archive;
  std::string wrt_store;
  std::string base_endpoint_name = "base_post_sse_96x2";
  std::string external_endpoint;
  std::string external_endpoint_name = "external_cmix21_post_sse";
  std::string output;
  std::string candidate_payload;
  std::string export_base_p1;
  std::uint64_t raw_scope_bytes = 0;
  std::uint32_t dev_start_ppm = 600000;
  std::uint32_t holdout_start_ppm = 800000;
  std::uint32_t top_endpoints = 8;
  std::uint64_t baseline_score_bytes = 109789279;
  std::uint64_t target_score_bytes = 109500000;
  double native_integration_margin_bytes_per_1m = 500.0;
  std::uint64_t payload_bytes = 0;
  bool payload_known = false;
  bool frozen = false;
  Config frozen_config;
};

std::string NeedValue(int* i, int argc, char** argv) {
  if (++(*i) >= argc) throw std::runtime_error("missing option value");
  return argv[*i];
}

std::uint64_t ParseUnsigned(const std::string& value, const std::string& name) {
  std::size_t used = 0;
  const std::uint64_t parsed = std::stoull(value, &used);
  if (used != value.size()) throw std::runtime_error("invalid " + name);
  return parsed;
}

std::int64_t ParseSigned(const std::string& value, const std::string& name) {
  std::size_t used = 0;
  const std::int64_t parsed = std::stoll(value, &used);
  if (used != value.size()) throw std::runtime_error("invalid " + name);
  return parsed;
}

Args ParseArgs(int argc, char** argv) {
  Args args;
  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    if (arg == "--trace") args.trace = NeedValue(&i, argc, argv);
    else if (arg == "--base-archive") args.base_archive = NeedValue(&i, argc, argv);
    else if (arg == "--reference-archive") {
      args.reference_archive = NeedValue(&i, argc, argv);
    }
    else if (arg == "--wrt-store") args.wrt_store = NeedValue(&i, argc, argv);
    else if (arg == "--base-endpoint-name") {
      args.base_endpoint_name = NeedValue(&i, argc, argv);
    }
    else if (arg == "--external-endpoint") {
      args.external_endpoint = NeedValue(&i, argc, argv);
    } else if (arg == "--external-endpoint-name") {
      args.external_endpoint_name = NeedValue(&i, argc, argv);
    }
    else if (arg == "--output") args.output = NeedValue(&i, argc, argv);
    else if (arg == "--candidate-payload") {
      args.candidate_payload = NeedValue(&i, argc, argv);
    } else if (arg == "--export-base-p1") {
      args.export_base_p1 = NeedValue(&i, argc, argv);
    } else if (arg == "--raw-scope-bytes") {
      args.raw_scope_bytes = ParseUnsigned(NeedValue(&i, argc, argv), arg);
    } else if (arg == "--dev-start-ppm") {
      args.dev_start_ppm = ParseUnsigned(NeedValue(&i, argc, argv), arg);
    } else if (arg == "--holdout-start-ppm") {
      args.holdout_start_ppm = ParseUnsigned(NeedValue(&i, argc, argv), arg);
    } else if (arg == "--top-endpoints") {
      args.top_endpoints = ParseUnsigned(NeedValue(&i, argc, argv), arg);
    } else if (arg == "--baseline-score-bytes") {
      args.baseline_score_bytes = ParseUnsigned(NeedValue(&i, argc, argv), arg);
    } else if (arg == "--target-score-bytes") {
      args.target_score_bytes = ParseUnsigned(NeedValue(&i, argc, argv), arg);
    } else if (arg == "--native-integration-margin-bytes-per-1m") {
      args.native_integration_margin_bytes_per_1m =
          std::stod(NeedValue(&i, argc, argv));
    } else if (arg == "--payload-bytes") {
      args.payload_bytes = ParseUnsigned(NeedValue(&i, argc, argv), arg);
      args.payload_known = true;
    } else if (arg == "--frozen-kind") {
      const std::string value = NeedValue(&i, argc, argv);
      args.frozen = true;
      if (value == "fixed_blend") args.frozen_config.kind = ConfigKind::kFixed;
      else if (value == "centered_residual") {
        args.frozen_config.kind = ConfigKind::kCentered;
      }
      else if (value == "causal_fixed_share") {
        args.frozen_config.kind = ConfigKind::kCausal;
      } else throw std::runtime_error("invalid --frozen-kind");
    } else if (arg == "--frozen-endpoint") {
      args.frozen = true;
      args.frozen_config.endpoint = ParseUnsigned(NeedValue(&i, argc, argv), arg);
    } else if (arg == "--frozen-weight-ppm") {
      args.frozen_config.weight_ppm = ParseUnsigned(NeedValue(&i, argc, argv), arg);
    } else if (arg == "--frozen-centered-coefficient-ppm") {
      args.frozen_config.centered_coefficient_ppm =
          ParseSigned(NeedValue(&i, argc, argv), arg);
    } else if (arg == "--frozen-prior-ppm") {
      args.frozen_config.prior_ppm = ParseUnsigned(NeedValue(&i, argc, argv), arg);
    } else if (arg == "--frozen-share-ppm") {
      args.frozen_config.share_ppm = ParseUnsigned(NeedValue(&i, argc, argv), arg);
    } else {
      throw std::runtime_error("unknown option: " + arg);
    }
  }
  if (args.trace.empty() || args.base_archive.empty() || args.output.empty() ||
      args.raw_scope_bytes == 0) {
    throw std::runtime_error(
        "required: --trace --base-archive --output --raw-scope-bytes");
  }
  if (args.dev_start_ppm >= args.holdout_start_ppm ||
      args.holdout_start_ppm >= kPpm || args.top_endpoints == 0) {
    throw std::runtime_error("invalid split/top-endpoint options");
  }
  if (args.baseline_score_bytes < args.target_score_bytes ||
      args.native_integration_margin_bytes_per_1m < 0.0) {
    throw std::runtime_error("invalid score/integration economics");
  }
  if (args.reference_archive.empty()) args.reference_archive = args.base_archive;
  return args;
}

double GainRate(double gain_bits, std::uint64_t scope_bytes) {
  return gain_bits / 8.0 * 1000000.0 / scope_bytes;
}

bool TraceTruthMatchesWrtStore(const Trace& trace, const std::string& path) {
  const std::vector<unsigned char> store = ReadFile(path);
  if ((trace.rows & 7) != 0 || store.size() != 5 + trace.rows / 8) {
    return false;
  }
  for (std::uint64_t row = 0; row < trace.rows; ++row) {
    const int expected = (store[5 + row / 8] >> (7 - (row & 7))) & 1;
    if (trace.Bit(row) != expected) return false;
  }
  return true;
}

struct ExactResult {
  std::vector<unsigned char> base_payload;
  std::vector<unsigned char> candidate_payload;
  std::uint64_t train_base_bytes = 0;
  std::uint64_t train_candidate_bytes = 0;
  std::uint64_t dev_base_bytes = 0;
  std::uint64_t dev_candidate_bytes = 0;
  std::uint64_t holdout_base_bytes = 0;
  std::uint64_t holdout_candidate_bytes = 0;
  bool decoder_replay_ok = false;
  std::uint64_t decoder_mismatch_row = 0;
  std::uint64_t holdout_blocks = 0;
  std::uint64_t block_regressions = 0;
  std::int64_t largest_block_regression_bytes = 0;
  std::int64_t total_block_regression_bytes = 0;
};

ExactResult ExactReplay(const Trace& trace, const Config& config,
    std::uint64_t dev_start, std::uint64_t holdout_start) {
  ExactResult result;
  CmixRangeEncoder base_full;
  CmixRangeEncoder candidate_full;
  CmixRangeEncoder base_train;
  CmixRangeEncoder candidate_train;
  CmixRangeEncoder base_dev;
  CmixRangeEncoder candidate_dev;
  CmixRangeEncoder base_holdout;
  CmixRangeEncoder candidate_holdout;
  FixedSharePosterior posterior(config.prior_ppm, config.share_ppm);

  const std::uint64_t block_rows = std::max<std::uint64_t>(1,
      (trace.rows - holdout_start + 15) / 16);
  CmixRangeEncoder block_base;
  CmixRangeEncoder block_candidate;
  std::uint64_t block_count = 0;
  auto finish_block = [&]() {
    if (block_count == 0) return;
    block_base.Finish();
    block_candidate.Finish();
    const std::int64_t gain = static_cast<std::int64_t>(
        block_base.Output().size()) -
        static_cast<std::int64_t>(block_candidate.Output().size());
    ++result.holdout_blocks;
    if (gain < 0) {
      ++result.block_regressions;
      result.largest_block_regression_bytes = std::max(
          result.largest_block_regression_bytes, -gain);
      result.total_block_regression_bytes += -gain;
    }
    block_base = CmixRangeEncoder();
    block_candidate = CmixRangeEncoder();
    block_count = 0;
  };

  for (std::uint64_t row = 0; row < trace.rows; ++row) {
    const int bit = trace.Bit(row);
    const std::uint32_t base = trace.P1(row, 0);
    const std::uint32_t endpoint = trace.P1(row, config.endpoint);
    const std::uint32_t mixed = Probability(config, &posterior, base, endpoint);
    base_full.Encode(bit, base);
    candidate_full.Encode(bit, mixed);
    if (row < dev_start) {
      base_train.Encode(bit, base);
      candidate_train.Encode(bit, mixed);
    } else if (row < holdout_start) {
      base_dev.Encode(bit, base);
      candidate_dev.Encode(bit, mixed);
    } else {
      base_holdout.Encode(bit, base);
      candidate_holdout.Encode(bit, mixed);
      block_base.Encode(bit, base);
      block_candidate.Encode(bit, mixed);
      ++block_count;
      if (block_count == block_rows) finish_block();
    }
    if (config.kind == ConfigKind::kCausal) {
      posterior.Update(bit, base, endpoint);
    }
  }
  finish_block();
  base_full.Finish();
  candidate_full.Finish();
  base_train.Finish();
  candidate_train.Finish();
  base_dev.Finish();
  candidate_dev.Finish();
  base_holdout.Finish();
  candidate_holdout.Finish();
  result.base_payload = base_full.Output();
  result.candidate_payload = candidate_full.Output();
  result.train_base_bytes = base_train.Output().size();
  result.train_candidate_bytes = candidate_train.Output().size();
  result.dev_base_bytes = base_dev.Output().size();
  result.dev_candidate_bytes = candidate_dev.Output().size();
  result.holdout_base_bytes = base_holdout.Output().size();
  result.holdout_candidate_bytes = candidate_holdout.Output().size();

  CmixRangeDecoder decoder(result.candidate_payload);
  FixedSharePosterior decode_posterior(config.prior_ppm, config.share_ppm);
  result.decoder_replay_ok = true;
  for (std::uint64_t row = 0; row < trace.rows; ++row) {
    const std::uint32_t base = trace.P1(row, 0);
    const std::uint32_t endpoint = trace.P1(row, config.endpoint);
    const std::uint32_t mixed =
        Probability(config, &decode_posterior, base, endpoint);
    const int decoded = decoder.Decode(mixed);
    if (decoded != trace.Bit(row)) {
      result.decoder_replay_ok = false;
      result.decoder_mismatch_row = row;
      break;
    }
    if (config.kind == ConfigKind::kCausal) {
      decode_posterior.Update(decoded, base, endpoint);
    }
  }
  return result;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const Args args = ParseArgs(argc, argv);
    Trace trace(args.trace);
    ExportBaseEndpoint(trace, args.export_base_p1);
    if (!args.external_endpoint.empty()) {
      trace.LoadExternalEndpoint(
          args.external_endpoint, args.external_endpoint_name);
    }
    const bool minimal_base_trace = trace.internal_endpoint_count == 1;
    const bool wrt_store_identity = args.wrt_store.empty()
        ? true : TraceTruthMatchesWrtStore(trace, args.wrt_store);
    if (args.frozen && args.frozen_config.endpoint >= trace.endpoint_count) {
      throw std::runtime_error("frozen endpoint outside trace");
    }
    const std::uint64_t dev_start = trace.rows * args.dev_start_ppm / kPpm;
    const std::uint64_t holdout_start =
        trace.rows * args.holdout_start_ppm / kPpm;
    std::array<double, 65536> loss_bits{};
    loss_bits[0] = std::numeric_limits<double>::infinity();
    for (std::uint32_t i = 1; i < loss_bits.size(); ++i) {
      loss_bits[i] = -std::log2(static_cast<double>(i) / kProbabilityTotal);
    }

    double base_train_loss = 0;
    double base_dev_loss = 0;
    for (std::uint64_t row = 0; row < holdout_start; ++row) {
      const int bit = trace.Bit(row);
      const std::uint32_t p = trace.P1(row, 0);
      const std::uint32_t likelihood = bit ? p : kProbabilityTotal - p;
      if (row < dev_start) base_train_loss += loss_bits[likelihood];
      else base_dev_loss += loss_bits[likelihood];
    }

    std::vector<Config> ranked_fixed;
    std::vector<Config> ranked_centered;
    std::vector<Config> ranked_causal;
    std::vector<Config> ranked_oracle;
    Config selected;
    if (args.frozen) {
      selected = args.frozen_config;
    } else {
      selected.endpoint = 1;
      selected.weight_ppm = 0;
      selected.train_loss = base_train_loss;
      selected.dev_loss = base_dev_loss;
      selected.dev_gain_bits = 0;
      const std::array<std::uint32_t, 5> coarse_weights = {
          62500, 125000, 250000, 500000, 1000000};
      const std::array<std::int32_t, 10> coarse_centered = {
          -500000, -250000, -125000, -62500, -31250,
          31250, 62500, 125000, 250000, 500000};
      std::vector<Config> coarse;
      for (std::uint32_t endpoint = 1; endpoint < trace.endpoint_count; ++endpoint) {
        Config best;
        best.endpoint = endpoint;
        double oracle_dev_loss = 0;
        for (std::uint64_t row = dev_start; row < holdout_start; ++row) {
          const int bit = trace.Bit(row);
          const std::uint32_t base = trace.P1(row, 0);
          const std::uint32_t candidate = trace.P1(row, endpoint);
          const double base_loss = loss_bits[
              bit ? base : kProbabilityTotal - base];
          const double candidate_loss = loss_bits[
              bit ? candidate : kProbabilityTotal - candidate];
          oracle_dev_loss += std::min(base_loss, candidate_loss);
        }
        best.oracle_dev_gain_bits = base_dev_loss - oracle_dev_loss;
        for (std::uint32_t weight : coarse_weights) {
          double dev_loss = 0;
          for (std::uint64_t row = dev_start; row < holdout_start; ++row) {
            const int bit = trace.Bit(row);
            const std::uint32_t mixed = MixFixed(trace.P1(row, 0),
                trace.P1(row, endpoint), weight);
            dev_loss += loss_bits[bit ? mixed : kProbabilityTotal - mixed];
          }
          const double gain = base_dev_loss - dev_loss;
          if (gain > best.dev_gain_bits) {
            best.weight_ppm = weight;
            best.dev_loss = dev_loss;
            best.dev_gain_bits = gain;
          }
        }
        for (std::int32_t coefficient : coarse_centered) {
          double dev_loss = 0;
          for (std::uint64_t row = dev_start; row < holdout_start; ++row) {
            const int bit = trace.Bit(row);
            const std::uint32_t mixed = MixCentered(trace.P1(row, 0),
                trace.P1(row, endpoint), coefficient);
            dev_loss += loss_bits[bit ? mixed : kProbabilityTotal - mixed];
          }
          const double gain = base_dev_loss - dev_loss;
          if (gain > best.dev_gain_bits) {
            best.kind = ConfigKind::kCentered;
            best.centered_coefficient_ppm = coefficient;
            best.dev_loss = dev_loss;
            best.dev_gain_bits = gain;
          }
        }
        coarse.push_back(best);
      }
      ranked_oracle = coarse;
      std::sort(ranked_oracle.begin(), ranked_oracle.end(),
          [](const Config& a, const Config& b) {
            return a.oracle_dev_gain_bits > b.oracle_dev_gain_bits;
          });
      std::sort(coarse.begin(), coarse.end(), [](const Config& a, const Config& b) {
        return a.dev_gain_bits > b.dev_gain_bits;
      });
      const std::size_t top = std::min<std::size_t>(args.top_endpoints, coarse.size());
      std::vector<std::uint32_t> refine_endpoints;
      for (std::size_t rank = 0; rank < top; ++rank) {
        refine_endpoints.push_back(coarse[rank].endpoint);
      }
      const std::size_t oracle_top = std::min<std::size_t>(4, ranked_oracle.size());
      for (std::size_t rank = 0; rank < oracle_top; ++rank) {
        const std::uint32_t endpoint = ranked_oracle[rank].endpoint;
        if (std::find(refine_endpoints.begin(), refine_endpoints.end(), endpoint) ==
            refine_endpoints.end()) {
          refine_endpoints.push_back(endpoint);
        }
      }
      // The base pre-SSE, active 96-cell byte endpoint, and continuous
      // 160/200-cell probes are contractual endpoints. Always measure them at
      // the refined grid even when a coarse blend ranks them poorly.
      for (std::uint32_t endpoint = 1;
           endpoint <= 4 && endpoint < trace.endpoint_count; ++endpoint) {
        if (std::find(refine_endpoints.begin(), refine_endpoints.end(), endpoint) ==
            refine_endpoints.end()) {
          refine_endpoints.push_back(endpoint);
        }
      }
      const std::array<std::uint32_t, 11> weights = {
          0, 31250, 62500, 125000, 250000, 375000,
          500000, 625000, 750000, 875000, 1000000};
      const std::array<std::int32_t, 19> centered_coefficients = {
          -1000000, -750000, -500000, -375000, -250000,
          -187500, -125000, -62500, -31250, 0,
          31250, 62500, 125000, 187500, 250000,
          375000, 500000, 750000, 1000000};
      for (std::uint32_t endpoint : refine_endpoints) {
        Config best_fixed;
        best_fixed.endpoint = endpoint;
        for (std::uint32_t weight : weights) {
          double train_loss = 0;
          double dev_loss = 0;
          for (std::uint64_t row = 0; row < holdout_start; ++row) {
            const int bit = trace.Bit(row);
            const std::uint32_t mixed = MixFixed(trace.P1(row, 0),
                trace.P1(row, endpoint), weight);
            const double loss = loss_bits[
                bit ? mixed : kProbabilityTotal - mixed];
            if (row < dev_start) train_loss += loss;
            else dev_loss += loss;
          }
          const double gain = base_dev_loss - dev_loss;
          if (gain > best_fixed.dev_gain_bits) {
            best_fixed.weight_ppm = weight;
            best_fixed.train_loss = train_loss;
            best_fixed.dev_loss = dev_loss;
            best_fixed.dev_gain_bits = gain;
          }
        }
        ranked_fixed.push_back(best_fixed);

        Config best_centered;
        best_centered.kind = ConfigKind::kCentered;
        best_centered.endpoint = endpoint;
        for (std::int32_t coefficient : centered_coefficients) {
          double train_loss = 0;
          double dev_loss = 0;
          for (std::uint64_t row = 0; row < holdout_start; ++row) {
            const int bit = trace.Bit(row);
            const std::uint32_t mixed = MixCentered(trace.P1(row, 0),
                trace.P1(row, endpoint), coefficient);
            const double loss = loss_bits[
                bit ? mixed : kProbabilityTotal - mixed];
            if (row < dev_start) train_loss += loss;
            else dev_loss += loss;
          }
          const double gain = base_dev_loss - dev_loss;
          if (gain > best_centered.dev_gain_bits) {
            best_centered.centered_coefficient_ppm = coefficient;
            best_centered.train_loss = train_loss;
            best_centered.dev_loss = dev_loss;
            best_centered.dev_gain_bits = gain;
          }
        }
        ranked_centered.push_back(best_centered);
      }
      std::sort(ranked_fixed.begin(), ranked_fixed.end(),
          [](const Config& a, const Config& b) {
            return a.dev_gain_bits > b.dev_gain_bits;
          });
      std::sort(ranked_centered.begin(), ranked_centered.end(),
          [](const Config& a, const Config& b) {
            return a.dev_gain_bits > b.dev_gain_bits;
          });
      if (!ranked_fixed.empty() &&
          ranked_fixed.front().dev_gain_bits > selected.dev_gain_bits) {
        selected = ranked_fixed.front();
      }
      if (!ranked_centered.empty() &&
          ranked_centered.front().dev_gain_bits > selected.dev_gain_bits) {
        selected = ranked_centered.front();
      }

      const std::size_t causal_top = std::min<std::size_t>(4, coarse.size());
      std::vector<std::uint32_t> causal_endpoints;
      for (std::size_t rank = 0; rank < causal_top; ++rank) {
        causal_endpoints.push_back(coarse[rank].endpoint);
      }
      for (std::size_t rank = 0; rank < oracle_top; ++rank) {
        const std::uint32_t endpoint = ranked_oracle[rank].endpoint;
        if (std::find(causal_endpoints.begin(), causal_endpoints.end(), endpoint) ==
            causal_endpoints.end()) {
          causal_endpoints.push_back(endpoint);
        }
      }
      for (std::uint32_t endpoint = 2;
           endpoint <= 4 && endpoint < trace.endpoint_count; ++endpoint) {
        if (std::find(causal_endpoints.begin(), causal_endpoints.end(), endpoint) ==
            causal_endpoints.end()) {
          causal_endpoints.push_back(endpoint);
        }
      }
      const std::array<std::uint32_t, 3> priors = {250000, 500000, 750000};
      const std::array<std::uint32_t, 2> shares = {10, 1000};
      for (std::uint32_t endpoint : causal_endpoints) {
        for (std::uint32_t prior : priors) {
          for (std::uint32_t share : shares) {
            Config config;
            config.kind = ConfigKind::kCausal;
            config.endpoint = endpoint;
            config.prior_ppm = prior;
            config.share_ppm = share;
            FixedSharePosterior posterior(prior, share);
            for (std::uint64_t row = 0; row < holdout_start; ++row) {
              const int bit = trace.Bit(row);
              const std::uint32_t base = trace.P1(row, 0);
              const std::uint32_t endpoint_p = trace.P1(row, endpoint);
              const std::uint32_t mixed = posterior.Mix(base, endpoint_p);
              const double loss = loss_bits[
                  bit ? mixed : kProbabilityTotal - mixed];
              if (row < dev_start) config.train_loss += loss;
              else config.dev_loss += loss;
              posterior.Update(bit, base, endpoint_p);
            }
            config.dev_gain_bits = base_dev_loss - config.dev_loss;
            ranked_causal.push_back(config);
          }
        }
      }
      std::sort(ranked_causal.begin(), ranked_causal.end(),
          [](const Config& a, const Config& b) {
            return a.dev_gain_bits > b.dev_gain_bits;
          });
      if (!ranked_causal.empty() &&
          ranked_causal.front().dev_gain_bits > selected.dev_gain_bits) {
        selected = ranked_causal.front();
      }
    }

    const ExactResult exact = ExactReplay(trace, selected, dev_start, holdout_start);
    const std::vector<unsigned char> archive = ReadFile(args.base_archive);
    const std::vector<unsigned char> reference_archive =
        ReadFile(args.reference_archive);
    const bool reference_archive_identity = archive == reference_archive;
    const std::size_t archive_header_bytes = CmixHeaderBytes(archive);
    const std::vector<unsigned char> archive_payload(
        archive.begin() + archive_header_bytes, archive.end());
    const bool base_archive_identity = archive_payload == exact.base_payload;
    WriteFile(args.candidate_payload, exact.candidate_payload);

    const std::int64_t full_saved = static_cast<std::int64_t>(
        exact.base_payload.size()) -
        static_cast<std::int64_t>(exact.candidate_payload.size());
    const std::int64_t train_saved = static_cast<std::int64_t>(
        exact.train_base_bytes) - exact.train_candidate_bytes;
    const std::int64_t dev_saved = static_cast<std::int64_t>(
        exact.dev_base_bytes) - exact.dev_candidate_bytes;
    const std::int64_t holdout_saved = static_cast<std::int64_t>(
        exact.holdout_base_bytes) - exact.holdout_candidate_bytes;
    const double full_rate = static_cast<double>(full_saved) * 1000000.0 /
        args.raw_scope_bytes;
    const std::uint64_t dev_scope = args.raw_scope_bytes *
        (args.holdout_start_ppm - args.dev_start_ppm) / kPpm;
    const std::uint64_t holdout_scope = args.raw_scope_bytes *
        (kPpm - args.holdout_start_ppm) / kPpm;
    const double holdout_rate = static_cast<double>(holdout_saved) *
        1000000.0 / std::max<std::uint64_t>(1, holdout_scope);
    const double projected_1g_gross_gain = full_rate * 1000.0;
    const double forecast_debt_rate = static_cast<double>(
        args.baseline_score_bytes - args.target_score_bytes) / 1000.0;
    const double full_margin_rate = full_rate - forecast_debt_rate;
    const double holdout_margin_rate = holdout_rate - forecast_debt_rate;
    const double forecast_score_before_new_payload =
        static_cast<double>(args.baseline_score_bytes) - projected_1g_gross_gain;
    const double forecast_score_after_new_payload = args.payload_known
        ? forecast_score_before_new_payload + args.payload_bytes
        : std::numeric_limits<double>::quiet_NaN();

    std::string verdict;
    if (!wrt_store_identity) verdict = "invalid_wrt_truth_stream_identity";
    else if (!reference_archive_identity) verdict = "invalid_observation_archive_identity";
    else if (!base_archive_identity) verdict = "invalid_base_probability_stream_identity";
    else if (!exact.decoder_replay_ok) verdict = "invalid_decoder_replay";
    else if (full_rate < forecast_debt_rate) {
      verdict = "insufficient_gross_gain_for_forecast_debt";
    }
    else if (args.payload_known &&
        forecast_score_after_new_payload > args.target_score_bytes) {
      verdict = "insufficient_counted_gain_for_forecast_debt";
    }
    else if (full_margin_rate < args.native_integration_margin_bytes_per_1m ||
        holdout_margin_rate < args.native_integration_margin_bytes_per_1m) {
      verdict = "insufficient_demonstrated_margin_for_native_integration";
    } else if (args.frozen) {
      verdict = "disjoint_screen_pass_requires_counted_native_integration";
    } else {
      verdict = "discovery_screen_pass_requires_frozen_disjoint_confirmation";
    }

    std::ofstream out(args.output);
    if (!out) throw std::runtime_error("cannot create output receipt");
    out << std::fixed << std::setprecision(6);
    out << "{\n";
    out << "  \"schema\": \"fx2_cmix21_nested_endpoint_screen_v1\",\n";
    out << "  \"evidence_level\": \"matched_trace_exact_shadow_nonproof\",\n";
    out << "  \"mode\": \"" << (args.frozen ? "frozen_confirmation" : "discovery_selection") << "\",\n";
    out << "  \"trace\": {\"path\": \"" << JsonEscape(args.trace)
        << "\", \"rows\": " << trace.rows << ", \"row_bytes\": "
        << trace.row_bytes << ", \"endpoint_count\": " << trace.endpoint_count
        << ", \"layer0_count\": " << trace.layer0_count
        << ", \"wrt_store_path\": "
        << (args.wrt_store.empty() ? "null" : "\"" + JsonEscape(args.wrt_store) + "\"")
        << ", \"wrt_truth_stream_identity\": "
        << (args.wrt_store.empty() ? "null" : (wrt_store_identity ? "true" : "false"))
        << ", \"external_endpoint_path\": "
        << (args.external_endpoint.empty() ? "null" :
            "\"" + JsonEscape(args.external_endpoint) + "\"")
        << ", \"exported_base_p1_path\": "
        << (args.export_base_p1.empty() ? "null" :
            "\"" + JsonEscape(args.export_base_p1) + "\"")
        << "},\n";
    out << "  \"trace_contract\": {"
        << "\"probability_timing\": \"all endpoints recorded before current-bit update\", "
        << "\"recurrent_schedule\": \""
        << (minimal_base_trace
            ? "recorded base endpoint and separate recurrent external endpoint are aligned row-for-row; external state advances continuously"
            : "96, 160, and 200-cell byte endpoints advance on every decoded byte")
        << "\", "
        << "\"rng_initialization_order\": \""
        << (minimal_base_trace
            ? "base trace preserves its source schedule; observation adds no base probes"
            : "active96_then_probe160_then_probe200_after_single_seed")
        << "\", "
        << "\"probe_influences_base\": false, "
        << "\"external_endpoint_alignment\": "
        << (args.external_endpoint.empty()
            ? "null"
            : "\"separate continuous run over byte-identical WRT truth rows\"")
        << "},\n";
    out << "  \"scope_raw_bytes\": " << args.raw_scope_bytes << ",\n";
    out << "  \"split\": {\"dev_start_row\": " << dev_start
        << ", \"holdout_start_row\": " << holdout_start
        << ", \"selection_reads_holdout\": false, "
        << "\"holdout_boundary\": \"internal contiguous holdout; disjoint corpus confirmation still required\"},\n";
    out << "  \"base\": {\"endpoint\": 0, \"name\": \""
        << JsonEscape(args.base_endpoint_name) << "\", "
        << "\"archive_path\": \"" << JsonEscape(args.base_archive)
        << "\", \"archive_header_bytes\": " << archive_header_bytes
        << ", \"reference_archive_path\": \""
        << JsonEscape(args.reference_archive)
        << "\", \"reference_archive_identity\": "
        << (reference_archive_identity ? "true" : "false")
        << ", \"archive_payload_bytes\": " << archive_payload.size()
        << ", \"replayed_payload_bytes\": " << exact.base_payload.size()
        << ", \"archive_payload_identity\": "
        << (base_archive_identity ? "true" : "false") << "},\n";
    out << "  \"selected\": {\"kind\": \"" << ConfigKindName(selected.kind)
        << "\", \"endpoint\": " << selected.endpoint << ", \"endpoint_name\": \""
        << JsonEscape(trace.EndpointName(selected.endpoint)) << "\", \"weight_ppm\": "
        << selected.weight_ppm << ", \"centered_coefficient_ppm\": "
        << selected.centered_coefficient_ppm
        << ", \"prior_ppm\": " << selected.prior_ppm
        << ", \"share_ppm\": " << selected.share_ppm << "},\n";
    out << "  \"noncausal_endpoint_oracle_dev_ranking\": [\n";
    for (std::size_t i = 0; i < ranked_oracle.size(); ++i) {
      const Config& config = ranked_oracle[i];
      out << "    {\"endpoint\": " << config.endpoint << ", \"endpoint_name\": \""
          << JsonEscape(trace.EndpointName(config.endpoint))
          << "\", \"oracle_dev_gain_bits\": " << config.oracle_dev_gain_bits
          << ", \"oracle_dev_gain_bytes_per_proportional_1m_raw\": "
          << GainRate(config.oracle_dev_gain_bits,
              std::max<std::uint64_t>(1, dev_scope))
          << "}" << (i + 1 == ranked_oracle.size() ? "\n" : ",\n");
    }
    out << "  ],\n";
    out << "  \"fixed_blend_dev_ranking\": [\n";
    for (std::size_t i = 0; i < ranked_fixed.size(); ++i) {
      const Config& config = ranked_fixed[i];
      out << "    {\"endpoint\": " << config.endpoint << ", \"endpoint_name\": \""
          << JsonEscape(trace.EndpointName(config.endpoint)) << "\", \"weight_ppm\": "
          << config.weight_ppm << ", \"dev_gain_bits\": " << config.dev_gain_bits
          << ", \"dev_gain_bytes_per_proportional_1m_raw\": "
          << GainRate(config.dev_gain_bits, std::max<std::uint64_t>(1, dev_scope))
          << "}" << (i + 1 == ranked_fixed.size() ? "\n" : ",\n");
    }
    out << "  ],\n";
    out << "  \"centered_residual_dev_ranking\": [\n";
    for (std::size_t i = 0; i < ranked_centered.size(); ++i) {
      const Config& config = ranked_centered[i];
      out << "    {\"endpoint\": " << config.endpoint << ", \"endpoint_name\": \""
          << JsonEscape(trace.EndpointName(config.endpoint))
          << "\", \"centered_coefficient_ppm\": "
          << config.centered_coefficient_ppm << ", \"dev_gain_bits\": "
          << config.dev_gain_bits
          << ", \"dev_gain_bytes_per_proportional_1m_raw\": "
          << GainRate(config.dev_gain_bits, std::max<std::uint64_t>(1, dev_scope))
          << "}" << (i + 1 == ranked_centered.size() ? "\n" : ",\n");
    }
    out << "  ],\n";
    out << "  \"causal_fixed_share_dev_ranking\": [\n";
    for (std::size_t i = 0; i < ranked_causal.size(); ++i) {
      const Config& config = ranked_causal[i];
      out << "    {\"endpoint\": " << config.endpoint << ", \"endpoint_name\": \""
          << JsonEscape(trace.EndpointName(config.endpoint))
          << "\", \"prior_ppm\": " << config.prior_ppm
          << ", \"share_ppm\": " << config.share_ppm
          << ", \"dev_gain_bits\": " << config.dev_gain_bits
          << ", \"dev_gain_bytes_per_proportional_1m_raw\": "
          << GainRate(config.dev_gain_bits, std::max<std::uint64_t>(1, dev_scope))
          << "}" << (i + 1 == ranked_causal.size() ? "\n" : ",\n");
    }
    out << "  ],\n";
    out << "  \"exact_cmix_replay\": {\n";
    out << "    \"candidate_payload_path\": "
        << (args.candidate_payload.empty() ? "null" : "\"" + JsonEscape(args.candidate_payload) + "\"") << ",\n";
    out << "    \"candidate_payload_bytes\": " << exact.candidate_payload.size() << ",\n";
    out << "    \"full_saved_bytes\": " << full_saved << ",\n";
    out << "    \"full_saved_bytes_per_1m_raw\": " << full_rate << ",\n";
    out << "    \"train_saved_bytes\": " << train_saved << ",\n";
    out << "    \"dev_saved_bytes\": " << dev_saved << ",\n";
    out << "    \"holdout_saved_bytes\": " << holdout_saved << ",\n";
    out << "    \"holdout_saved_bytes_per_proportional_1m_raw\": " << holdout_rate << ",\n";
    out << "    \"decoder_replay_ok\": " << (exact.decoder_replay_ok ? "true" : "false") << ",\n";
    out << "    \"decoder_mismatch_row\": "
        << (exact.decoder_replay_ok ? "null" : std::to_string(exact.decoder_mismatch_row)) << ",\n";
    out << "    \"holdout_blocks\": " << exact.holdout_blocks << ",\n";
    out << "    \"holdout_block_regressions\": " << exact.block_regressions << ",\n";
    out << "    \"largest_holdout_block_regression_bytes\": "
        << exact.largest_block_regression_bytes << ",\n";
    out << "    \"total_holdout_block_regression_bytes\": "
        << exact.total_block_regression_bytes << "\n";
    out << "  },\n";
    out << "  \"economics\": {\n";
    out << "    \"baseline_score_bytes\": " << args.baseline_score_bytes << ",\n";
    out << "    \"target_score_bytes\": " << args.target_score_bytes << ",\n";
    out << "    \"forecast_debt_bytes_per_1m\": " << forecast_debt_rate << ",\n";
    out << "    \"native_integration_margin_bytes_per_1m\": "
        << args.native_integration_margin_bytes_per_1m << ",\n";
    out << "    \"full_margin_after_forecast_debt_bytes_per_1m\": "
        << full_margin_rate << ",\n";
    out << "    \"holdout_margin_after_forecast_debt_bytes_per_1m\": "
        << holdout_margin_rate << ",\n";
    out << "    \"payload_bytes_known\": " << (args.payload_known ? "true" : "false") << ",\n";
    out << "    \"payload_bytes\": " << (args.payload_known ? std::to_string(args.payload_bytes) : "null") << ",\n";
    out << "    \"linear_projected_1g_gross_gain_bytes\": "
        << projected_1g_gross_gain << ",\n";
    out << "    \"linear_forecast_score_before_new_payload_bytes\": "
        << forecast_score_before_new_payload << ",\n";
    out << "    \"linear_forecast_score_after_new_payload_bytes\": "
        << (args.payload_known ? std::to_string(forecast_score_after_new_payload) : "null") << "\n";
    out << "  },\n";
    out << "  \"verdict\": \"" << verdict << "\",\n";
    out << "  \"promotion_authorized\": false,\n";
    out << "  \"claim_boundary\": \"Matched same-execution shadow and exact range-coder replay only; not native integration, counted package evidence, an official 1G score, or a 10.95 percent claim.\"\n";
    out << "}\n";
    if (!out) throw std::runtime_error("cannot write output receipt");
    std::cout << verdict << " full_saved_bytes=" << full_saved
              << " holdout_saved_bytes=" << holdout_saved
              << " base_identity=" << (base_archive_identity ? "true" : "false")
              << " decode=" << (exact.decoder_replay_ok ? "true" : "false")
              << "\n";
    return (wrt_store_identity && reference_archive_identity && base_archive_identity &&
        exact.decoder_replay_ok) ? 0 : 2;
  } catch (const std::exception& error) {
    std::cerr << "error: " << error.what() << "\n";
    return 1;
  }
}
