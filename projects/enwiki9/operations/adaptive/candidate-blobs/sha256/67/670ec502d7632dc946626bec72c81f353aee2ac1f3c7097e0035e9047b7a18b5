#include "profile_trace.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstring>
#include <fstream>
#include <immintrin.h>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace gamma_enwiki9::nncp {
namespace {

namespace fs = std::filesystem;

constexpr std::array<std::uint8_t, 8> kCandidateMagic{
    'N', 'N', 'O', 'C', 'T', '1', 0, 0};
constexpr std::array<std::uint8_t, 8> kOracleMagic{
    'N', 'N', 'N', 'T', 'R', '4', 0, 0};
constexpr std::size_t kCandidateHeaderBytes = 32;
constexpr std::size_t kCandidateRowBytes = 20;
constexpr std::size_t kOracleHeaderBytes = 40;
constexpr std::size_t kOracleRowBytes = 71;
constexpr std::size_t kBranchBytes = 3;
constexpr int kProbabilityUnit = 32768;

void PutLittle(
    std::uint8_t* destination,
    std::uint64_t value,
    std::size_t bytes) {
  for (std::size_t index = 0; index < bytes; ++index) {
    destination[index] = static_cast<std::uint8_t>(value >> (8U * index));
  }
}

std::uint64_t GetLittle(
    const std::uint8_t* source,
    std::size_t bytes) {
  std::uint64_t value = 0;
  for (std::size_t index = 0; index < bytes; ++index) {
    value |= static_cast<std::uint64_t>(source[index]) << (8U * index);
  }
  return value;
}

std::vector<std::uint8_t> ReadFile(const fs::path& path) {
  if (fs::is_symlink(fs::symlink_status(path))) {
    throw std::runtime_error("trace path is a symlink");
  }
  std::ifstream input(path, std::ios::binary | std::ios::ate);
  if (!input) throw std::runtime_error("cannot open trace " + path.string());
  const std::streamoff end = input.tellg();
  if (end < 0 || static_cast<std::uintmax_t>(end) >
                     std::numeric_limits<std::size_t>::max()) {
    throw std::runtime_error("cannot size trace " + path.string());
  }
  std::vector<std::uint8_t> bytes(static_cast<std::size_t>(end));
  input.seekg(0);
  if (!bytes.empty()) {
    input.read(
        reinterpret_cast<char*>(bytes.data()),
        static_cast<std::streamsize>(bytes.size()));
  }
  if (!input || input.peek() != std::char_traits<char>::eof()) {
    throw std::runtime_error("trace changed or truncated while reading");
  }
  return bytes;
}

float LibncSum64(const __m256 (&values)[8]) {
  const __m256 u23 = _mm256_unpacklo_ps(values[2], values[3]);
  const __m256 u67 = _mm256_unpacklo_ps(values[6], values[7]);
  const __m256 u01 = _mm256_unpacklo_ps(values[0], values[1]);
  const __m256 h23 = _mm256_unpackhi_ps(values[2], values[3]);
  const __m256 h01 = _mm256_unpackhi_ps(values[0], values[1]);
  const __m256 u45 = _mm256_unpacklo_ps(values[4], values[5]);
  const __m256 h45 = _mm256_unpackhi_ps(values[4], values[5]);
  const __m256 h67 = _mm256_unpackhi_ps(values[6], values[7]);
  const __m256 a = _mm256_shuffle_ps(u01, u23, 0x44);
  const __m256 b = _mm256_shuffle_ps(h01, h23, 0x44);
  const __m256 c = _mm256_shuffle_ps(u01, u23, 0xee);
  const __m256 d = _mm256_shuffle_ps(h01, h23, 0xee);
  const __m256 e = _mm256_shuffle_ps(u45, u67, 0x44);
  const __m256 f = _mm256_shuffle_ps(h45, h67, 0x44);
  const __m256 g = _mm256_shuffle_ps(h45, h67, 0xee);
  const __m256 h = _mm256_shuffle_ps(u45, u67, 0xee);
  const __m256 left_low =
      _mm256_insertf128_ps(a, _mm256_castps256_ps128(e), 1);
  __m256 left_high =
      _mm256_insertf128_ps(c, _mm256_castps256_ps128(h), 1);
  const __m256 right_low =
      _mm256_insertf128_ps(b, _mm256_castps256_ps128(f), 1);
  __m256 right_high =
      _mm256_insertf128_ps(d, _mm256_castps256_ps128(g), 1);
  const __m256 left_low_high = _mm256_permute2f128_ps(a, e, 0x31);
  left_high = _mm256_add_ps(left_high, left_low);
  const __m256 left_high_high = _mm256_permute2f128_ps(c, h, 0x31);
  const __m256 right_low_high = _mm256_permute2f128_ps(b, f, 0x31);
  const __m256 right_high_high = _mm256_permute2f128_ps(d, g, 0x31);
  const __m256 left_tail = _mm256_add_ps(left_low_high, left_high_high);
  right_high = _mm256_add_ps(right_high, right_low);
  const __m256 right_tail = _mm256_add_ps(right_low_high, right_high_high);
  right_high = _mm256_add_ps(left_high, right_high);
  __m256 total = _mm256_add_ps(left_tail, right_tail);
  total = _mm256_add_ps(right_high, total);
  total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0xb1));
  total = _mm256_add_ps(total, _mm256_shuffle_ps(total, total, 0x4e));
  total =
      _mm256_add_ps(total, _mm256_permute2f128_ps(total, total, 0x01));
  return _mm_cvtss_f32(_mm256_castps256_ps128(total));
}

float LibncSum(const float* source, std::size_t count) {
  if (count == 0) throw std::invalid_argument("trace sum width is zero");
  std::array<float, 8 * sizeof(std::size_t)> partials{};
  std::size_t blocks = 0;
  std::size_t index = 0;
  while (index + 64 <= count) {
    __m256 values[8]{};
    for (std::size_t lane = 0; lane < 8; ++lane) {
      values[lane] = _mm256_loadu_ps(source + index + lane * 8);
    }
    float block_sum = LibncSum64(values);
    std::size_t slot = 0;
    while ((blocks & (std::size_t{1} << slot)) != 0) {
      block_sum += partials[slot];
      partials[slot++] = 0.0F;
    }
    partials[slot] = block_sum;
    ++blocks;
    index += 64;
  }
  if (index < count) {
    alignas(32) std::array<float, 64> tail{};
    std::copy_n(source + index, count - index, tail.data());
    __m256 values[8]{};
    for (std::size_t lane = 0; lane < 8; ++lane) {
      values[lane] = _mm256_load_ps(tail.data() + lane * 8);
    }
    float block_sum = LibncSum64(values);
    std::size_t slot = 0;
    while ((blocks & (std::size_t{1} << slot)) != 0) {
      block_sum += partials[slot];
      partials[slot++] = 0.0F;
    }
    partials[slot] = block_sum;
    ++blocks;
  }
  float total = 0.0F;
  std::size_t slots = 0;
  for (std::size_t remaining = blocks; remaining != 0; remaining >>= 1U) {
    ++slots;
  }
  for (std::size_t slot = 0; slot < slots; ++slot) total += partials[slot];
  return total;
}

struct Branch {
  std::uint16_t probability;
  std::uint8_t bit;
};

std::vector<Branch> BranchPath(
    std::span<const float> probabilities,
    std::uint16_t symbol) {
  if (probabilities.size() <= 1 ||
      probabilities.size() > std::numeric_limits<std::uint16_t>::max() ||
      symbol >= probabilities.size()) {
    throw std::invalid_argument("trace probability geometry differs");
  }
  for (const float probability : probabilities) {
    if (!std::isfinite(probability) || probability < 0.0F) {
      throw std::invalid_argument("trace probability is not finite and nonnegative");
    }
  }
  std::vector<Branch> branches;
  std::size_t start = 0;
  std::size_t range = probabilities.size();
  float total = 1.0F;
  while (range > 1) {
    const std::size_t left = range >> 1U;
    const float part = LibncSum(probabilities.data() + start, left);
    if (!std::isfinite(part) || !std::isfinite(total) || total <= 0.0F) {
      throw std::runtime_error("trace branch mass is invalid");
    }
    int probability = std::lrint(part * kProbabilityUnit / total);
    probability = std::clamp(probability, 1, kProbabilityUnit - 1);
    const bool bit = symbol >= start + left;
    branches.push_back({
        .probability = static_cast<std::uint16_t>(probability),
        .bit = static_cast<std::uint8_t>(bit),
    });
    if (bit) {
      start += left;
      range -= left;
      total -= part;
    } else {
      range = left;
      total = part;
    }
  }
  if (start != symbol || branches.size() > 255) {
    throw std::logic_error("trace branch path did not resolve the symbol");
  }
  return branches;
}

void RequireAvailable(
    const std::vector<std::uint8_t>& bytes,
    std::size_t offset,
    std::size_t count,
    const char* label) {
  if (offset > bytes.size() || count > bytes.size() - offset) {
    throw std::runtime_error(std::string("truncated ") + label);
  }
}

void ValidateCandidateTraceBeforeOracle(
    const std::vector<std::uint8_t>& candidate,
    std::uint64_t expected_rows,
    std::uint32_t expected_vocabulary) {
  RequireAvailable(candidate, 0, kCandidateHeaderBytes, "candidate header");
  if (!std::equal(
          kCandidateMagic.begin(), kCandidateMagic.end(), candidate.begin())) {
    throw std::runtime_error("candidate trace magic differs");
  }
  const std::uint64_t rows = GetLittle(candidate.data() + 8, 8);
  const std::uint64_t branches = GetLittle(candidate.data() + 16, 8);
  const std::uint32_t vocabulary =
      static_cast<std::uint32_t>(GetLittle(candidate.data() + 24, 4));
  const std::uint32_t complete =
      static_cast<std::uint32_t>(GetLittle(candidate.data() + 28, 4));
  if (complete != 1 || rows != expected_rows ||
      vocabulary != expected_vocabulary) {
    throw std::runtime_error("candidate trace header contract differs");
  }
  std::size_t offset = kCandidateHeaderBytes;
  std::uint64_t counted_branches = 0;
  for (std::uint64_t row = 0; row < rows; ++row) {
    RequireAvailable(candidate, offset, kCandidateRowBytes, "candidate row");
    const std::uint64_t execution = GetLittle(candidate.data() + offset + 8, 8);
    const std::uint16_t symbol = static_cast<std::uint16_t>(
        GetLittle(candidate.data() + offset + 16, 2));
    const std::uint8_t count = candidate[offset + 18];
    const std::uint8_t reserved = candidate[offset + 19];
    if (execution != row || symbol >= vocabulary || count == 0 || reserved != 0) {
      throw std::runtime_error("candidate trace row contract differs");
    }
    offset += kCandidateRowBytes;
    RequireAvailable(
        candidate,
        offset,
        static_cast<std::size_t>(count) * kBranchBytes,
        "candidate branches");
    for (std::size_t branch = 0; branch < count; ++branch) {
      const std::uint16_t probability = static_cast<std::uint16_t>(GetLittle(
          candidate.data() + offset + branch * kBranchBytes, 2));
      const std::uint8_t bit = candidate[offset + branch * kBranchBytes + 2];
      if (probability == 0 || probability >= kProbabilityUnit || bit > 1) {
        throw std::runtime_error("candidate trace branch contract differs");
      }
    }
    offset += static_cast<std::size_t>(count) * kBranchBytes;
    counted_branches += count;
  }
  if (offset != candidate.size() || counted_branches != branches) {
    throw std::runtime_error("candidate trace terminal population differs");
  }
}

}  // namespace

class CandidateBranchTraceWriter::Impl {
 public:
  Impl(fs::path output, std::uint32_t vocabulary)
      : output_(std::move(output)),
        partial_(output_.string() + ".partial"),
        vocabulary_(vocabulary) {
    if (vocabulary_ <= 1 || vocabulary_ >
                                std::numeric_limits<std::uint16_t>::max()) {
      throw std::invalid_argument("candidate trace vocabulary is invalid");
    }
    if (fs::exists(output_) || fs::exists(partial_)) {
      throw std::runtime_error("candidate trace output already exists");
    }
    stream_.open(partial_, std::ios::binary | std::ios::trunc);
    if (!stream_) throw std::runtime_error("cannot create candidate trace");
    std::array<std::uint8_t, kCandidateHeaderBytes> header{};
    std::copy(kCandidateMagic.begin(), kCandidateMagic.end(), header.begin());
    PutLittle(header.data() + 24, vocabulary_, 4);
    stream_.write(
        reinterpret_cast<const char*>(header.data()),
        static_cast<std::streamsize>(header.size()));
    if (!stream_) throw std::runtime_error("cannot write candidate trace header");
  }

  void WriteRow(
      std::uint64_t original_coordinate,
      std::uint16_t symbol,
      std::span<const float> probabilities) {
    if (finalized_) throw std::logic_error("candidate trace is already finalized");
    if (probabilities.size() != vocabulary_) {
      throw std::invalid_argument("candidate trace row vocabulary differs");
    }
    const std::vector<Branch> branches = BranchPath(probabilities, symbol);
    std::array<std::uint8_t, kCandidateRowBytes> row{};
    PutLittle(row.data(), original_coordinate, 8);
    PutLittle(row.data() + 8, rows_, 8);
    PutLittle(row.data() + 16, symbol, 2);
    row[18] = static_cast<std::uint8_t>(branches.size());
    stream_.write(
        reinterpret_cast<const char*>(row.data()),
        static_cast<std::streamsize>(row.size()));
    for (const Branch& branch : branches) {
      std::array<std::uint8_t, kBranchBytes> bytes{};
      PutLittle(bytes.data(), branch.probability, 2);
      bytes[2] = branch.bit;
      stream_.write(
          reinterpret_cast<const char*>(bytes.data()),
          static_cast<std::streamsize>(bytes.size()));
    }
    if (!stream_) throw std::runtime_error("cannot write candidate trace row");
    if (branches_ > std::numeric_limits<std::uint64_t>::max() -
                        branches.size() ||
        rows_ == std::numeric_limits<std::uint64_t>::max()) {
      throw std::overflow_error("candidate trace population overflows");
    }
    branches_ += branches.size();
    ++rows_;
  }

  void Finalize() {
    if (finalized_) throw std::logic_error("candidate trace is already finalized");
    std::array<std::uint8_t, kCandidateHeaderBytes> header{};
    std::copy(kCandidateMagic.begin(), kCandidateMagic.end(), header.begin());
    PutLittle(header.data() + 8, rows_, 8);
    PutLittle(header.data() + 16, branches_, 8);
    PutLittle(header.data() + 24, vocabulary_, 4);
    PutLittle(header.data() + 28, 1, 4);
    stream_.seekp(0);
    stream_.write(
        reinterpret_cast<const char*>(header.data()),
        static_cast<std::streamsize>(header.size()));
    stream_.flush();
    if (!stream_) throw std::runtime_error("cannot finalize candidate trace");
    stream_.close();
    if (!stream_) throw std::runtime_error("cannot close candidate trace");
    fs::rename(partial_, output_);
    finalized_ = true;
  }

 private:
  fs::path output_;
  fs::path partial_;
  std::uint32_t vocabulary_;
  std::ofstream stream_;
  std::uint64_t rows_ = 0;
  std::uint64_t branches_ = 0;
  bool finalized_ = false;
};

CandidateBranchTraceWriter::CandidateBranchTraceWriter(
    const fs::path& output,
    std::uint32_t vocabulary)
    : impl_(std::make_unique<Impl>(output, vocabulary)) {}

CandidateBranchTraceWriter::~CandidateBranchTraceWriter() = default;

void CandidateBranchTraceWriter::WriteRow(
    std::uint64_t original_coordinate,
    std::uint16_t symbol,
    std::span<const float> probabilities) {
  impl_->WriteRow(original_coordinate, symbol, probabilities);
}

void CandidateBranchTraceWriter::Finalize() { impl_->Finalize(); }

TraceComparisonSummary CompareCandidateTraceToIndexedOracle(
    const fs::path& candidate_path,
    const fs::path& oracle_path,
    std::uint64_t expected_rows,
    std::uint32_t expected_vocabulary) {
  const std::vector<std::uint8_t> candidate = ReadFile(candidate_path);
  // Oracle bytes are unreachable until the candidate is independently known
  // to be complete and structurally closed.
  ValidateCandidateTraceBeforeOracle(
      candidate, expected_rows, expected_vocabulary);
  const std::vector<std::uint8_t> oracle = ReadFile(oracle_path);
  RequireAvailable(oracle, 0, kOracleHeaderBytes, "oracle header");
  if (!std::equal(kCandidateMagic.begin(), kCandidateMagic.end(), candidate.begin()) ||
      !std::equal(kOracleMagic.begin(), kOracleMagic.end(), oracle.begin())) {
    throw std::runtime_error("trace magic differs");
  }
  const std::uint64_t candidate_rows = GetLittle(candidate.data() + 8, 8);
  const std::uint64_t candidate_branches = GetLittle(candidate.data() + 16, 8);
  const std::uint32_t candidate_vocabulary =
      static_cast<std::uint32_t>(GetLittle(candidate.data() + 24, 4));
  const std::uint32_t candidate_complete =
      static_cast<std::uint32_t>(GetLittle(candidate.data() + 28, 4));
  const std::uint64_t oracle_rows = GetLittle(oracle.data() + 8, 8);
  const std::uint64_t oracle_branches = GetLittle(oracle.data() + 16, 8);
  const std::uint64_t oracle_trees = GetLittle(oracle.data() + 24, 8);
  const std::uint64_t oracle_checkpoints = GetLittle(oracle.data() + 32, 8);
  if (candidate_complete != 1 || candidate_rows != expected_rows ||
      oracle_rows != expected_rows || candidate_vocabulary != expected_vocabulary ||
      oracle_trees != 0 || oracle_checkpoints != 0) {
    throw std::runtime_error("trace header contract differs");
  }

  TraceComparisonSummary summary;
  std::size_t candidate_offset = kCandidateHeaderBytes;
  std::size_t oracle_offset = kOracleHeaderBytes;
  std::uint64_t counted_candidate_branches = 0;
  std::uint64_t counted_oracle_branches = 0;
  for (std::uint64_t row_index = 0; row_index < expected_rows; ++row_index) {
    RequireAvailable(
        candidate, candidate_offset, kCandidateRowBytes, "candidate row");
    RequireAvailable(oracle, oracle_offset, kOracleRowBytes, "oracle row");
    const std::uint64_t candidate_original =
        GetLittle(candidate.data() + candidate_offset, 8);
    const std::uint64_t candidate_execution =
        GetLittle(candidate.data() + candidate_offset + 8, 8);
    const std::uint16_t candidate_symbol = static_cast<std::uint16_t>(
        GetLittle(candidate.data() + candidate_offset + 16, 2));
    const std::uint8_t candidate_count = candidate[candidate_offset + 18];
    const std::uint8_t candidate_reserved = candidate[candidate_offset + 19];
    const std::uint64_t oracle_original =
        GetLittle(oracle.data() + oracle_offset, 8);
    const std::uint64_t oracle_execution =
        GetLittle(oracle.data() + oracle_offset + 8, 8);
    const std::uint16_t oracle_symbol = static_cast<std::uint16_t>(
        GetLittle(oracle.data() + oracle_offset + 64, 2));
    const std::uint16_t oracle_vocabulary = static_cast<std::uint16_t>(
        GetLittle(oracle.data() + oracle_offset + 66, 2));
    const std::uint8_t oracle_count = oracle[oracle_offset + 68];
    const std::uint8_t oracle_tree = oracle[oracle_offset + 69];
    const std::uint8_t oracle_checkpoint = oracle[oracle_offset + 70];
    if (candidate_execution != row_index || oracle_execution != row_index ||
        candidate_original != oracle_original ||
        candidate_symbol != oracle_symbol ||
        candidate_symbol >= expected_vocabulary ||
        oracle_vocabulary != expected_vocabulary || candidate_reserved != 0 ||
        oracle_tree != 0 || oracle_checkpoint != 0) {
      throw std::runtime_error("trace row identity differs");
    }
    candidate_offset += kCandidateRowBytes;
    oracle_offset += kOracleRowBytes;
    RequireAvailable(
        candidate,
        candidate_offset,
        static_cast<std::size_t>(candidate_count) * kBranchBytes,
        "candidate branches");
    RequireAvailable(
        oracle,
        oracle_offset,
        static_cast<std::size_t>(oracle_count) * kBranchBytes,
        "oracle branches");
    const std::size_t common = std::min(candidate_count, oracle_count);
    for (std::size_t branch = 0; branch < common; ++branch) {
      const std::uint16_t observed = static_cast<std::uint16_t>(GetLittle(
          candidate.data() + candidate_offset + branch * kBranchBytes, 2));
      const std::uint8_t observed_bit =
          candidate[candidate_offset + branch * kBranchBytes + 2];
      const std::uint16_t expected = static_cast<std::uint16_t>(GetLittle(
          oracle.data() + oracle_offset + branch * kBranchBytes, 2));
      const std::uint8_t expected_bit =
          oracle[oracle_offset + branch * kBranchBytes + 2];
      if (observed_bit > 1 || expected_bit > 1 || observed_bit != expected_bit) {
        throw std::runtime_error("trace truth branch differs");
      }
      if (observed != expected) {
        ++summary.probability_mismatches;
        const unsigned int difference = observed > expected
            ? observed - expected
            : expected - observed;
        summary.maximum_probability_difference = std::max(
            summary.maximum_probability_difference,
            static_cast<std::uint16_t>(difference));
        if (!summary.first_mismatch.has_value()) {
          summary.first_mismatch = TraceMismatch{
              .row = row_index,
              .branch = static_cast<std::uint8_t>(branch),
              .expected_probability = expected,
              .observed_probability = observed,
          };
        }
      }
    }
    if (candidate_count != oracle_count) {
      summary.probability_mismatches += candidate_count > oracle_count
          ? candidate_count - oracle_count
          : oracle_count - candidate_count;
      summary.maximum_probability_difference = kProbabilityUnit - 1;
      if (!summary.first_mismatch.has_value()) {
        summary.first_mismatch = TraceMismatch{
            .row = row_index,
            .branch = static_cast<std::uint8_t>(common),
            .expected_probability = 0,
            .observed_probability = 0,
        };
      }
    }
    candidate_offset += static_cast<std::size_t>(candidate_count) * kBranchBytes;
    oracle_offset += static_cast<std::size_t>(oracle_count) * kBranchBytes;
    counted_candidate_branches += candidate_count;
    counted_oracle_branches += oracle_count;
    ++summary.rows;
  }
  if (candidate_offset != candidate.size() || oracle_offset != oracle.size() ||
      counted_candidate_branches != candidate_branches ||
      counted_oracle_branches != oracle_branches) {
    throw std::runtime_error("trace terminal population differs");
  }
  summary.branches = counted_oracle_branches;
  return summary;
}

}  // namespace gamma_enwiki9::nncp
