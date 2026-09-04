#ifndef GAMMA_ENWIKI9_NNCP_PROFILE_TRACE_HPP
#define GAMMA_ENWIKI9_NNCP_PROFILE_TRACE_HPP

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <span>

namespace gamma_enwiki9::nncp {

struct TraceMismatch {
  std::uint64_t row = 0;
  std::uint8_t branch = 0;
  std::uint16_t expected_probability = 0;
  std::uint16_t observed_probability = 0;
};

struct TraceComparisonSummary {
  std::uint64_t rows = 0;
  std::uint64_t branches = 0;
  std::uint64_t probability_mismatches = 0;
  std::uint16_t maximum_probability_difference = 0;
  std::optional<TraceMismatch> first_mismatch;

  bool exact() const { return probability_mismatches == 0; }
};

// A treatment-only compact trace. It derives the exact LibNC binary-tree path
// from each open F32 distribution and truth but contains no teacher input.
class CandidateBranchTraceWriter {
 public:
  CandidateBranchTraceWriter(
      const std::filesystem::path& output,
      std::uint32_t vocabulary);
  ~CandidateBranchTraceWriter();

  CandidateBranchTraceWriter(const CandidateBranchTraceWriter&) = delete;
  CandidateBranchTraceWriter& operator=(const CandidateBranchTraceWriter&) = delete;

  void WriteRow(
      std::uint64_t original_coordinate,
      std::uint16_t symbol,
      std::span<const float> probabilities);
  void Finalize();

 private:
  class Impl;
  std::unique_ptr<Impl> impl_;
};

// Reads a completed candidate trace and the retained NNNTR4 indexed oracle.
// It is intentionally separate from trace generation.
TraceComparisonSummary CompareCandidateTraceToIndexedOracle(
    const std::filesystem::path& candidate,
    const std::filesystem::path& oracle,
    std::uint64_t expected_rows,
    std::uint32_t expected_vocabulary);

}  // namespace gamma_enwiki9::nncp

#endif
