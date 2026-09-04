#ifndef GAMMA_ENWIKI9_NNCP_PROFILE_COMPARE_HPP
#define GAMMA_ENWIKI9_NNCP_PROFILE_COMPARE_HPP

#include "profile_backward.hpp"

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace gamma_enwiki9::nncp {

struct FileMismatch {
  std::uint64_t offset = 0;
  int expected_byte = -1;
  int observed_byte = -1;
};

struct ExactFileComparison {
  std::uint64_t expected_bytes = 0;
  std::uint64_t observed_bytes = 0;
  std::uint64_t mismatch_bytes = 0;
  std::optional<FileMismatch> first_mismatch;

  bool exact() const {
    return mismatch_bytes == 0 && expected_bytes == observed_bytes;
  }
};

struct ProfileComparisonSummary {
  std::size_t gradient_count = 0;
  std::uint64_t gradient_metadata_bytes = 0;
  std::uint64_t gradient_metadata_mismatch_bytes = 0;
  std::uint64_t gradient_payload_bytes = 0;
  std::uint64_t gradient_payload_mismatch_bytes = 0;
  std::size_t train_h_count = 0;
  std::uint64_t train_h_bytes = 0;
  std::uint64_t train_h_mismatch_bytes = 0;
  std::string first_mismatch_kind = "none";
  std::string first_mismatch_name = "none";
  std::optional<FileMismatch> first_mismatch;

  bool exact() const {
    return gradient_metadata_mismatch_bytes == 0 &&
           gradient_payload_mismatch_bytes == 0 &&
           train_h_mismatch_bytes == 0 && !first_mismatch.has_value();
  }
};

// Both operands must be regular, non-symlink files. The comparison accounts
// for every differing byte and every byte present on only one side.
ExactFileComparison CompareRegularFilesExact(
    const std::filesystem::path& expected,
    const std::filesystem::path& observed);

ExactFileComparison CompareRegularFileToBytes(
    const std::vector<std::uint8_t>& expected,
    const std::filesystem::path& observed);

// Fail-closed ordering is part of this API: treatment completeness and its
// zero-teacher receipt are validated before any oracle path is opened.
ProfileComparisonSummary CompareCompleteProfileTreatment(
    const ProfileGeometry& geometry,
    const std::filesystem::path& treatment_root,
    const std::filesystem::path& oracle_root);

}  // namespace gamma_enwiki9::nncp

#endif
