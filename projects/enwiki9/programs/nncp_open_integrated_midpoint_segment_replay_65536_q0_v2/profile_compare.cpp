#include "profile_compare.hpp"

#include "profile_artifacts.hpp"
#include "tensor_container.hpp"

#include <algorithm>
#include <array>
#include <cerrno>
#include <cstring>
#include <fcntl.h>
#include <fstream>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <sys/stat.h>
#include <unistd.h>
#include <utility>

namespace gamma_enwiki9::nncp {
namespace {

namespace fs = std::filesystem;

constexpr std::string_view kTreatmentSchema =
    "gamma.enwiki9.nncp-open-midpoint-treatment.v2";
constexpr std::string_view kOracleBoundary =
    "block_idx=256\n"
    "train_step_before=4\n"
    "learning_rate=0x1.4f7e76p-13\n"
    "block_idx_after=320\n"
    "train_step_after=5\n"
    "learning_rate_after=0x1.4f7e76p-13\n";

class RegularFile {
 public:
  explicit RegularFile(const fs::path& path) : path_(path) {
    descriptor_ = open(path.c_str(), O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (descriptor_ < 0) {
      throw std::runtime_error(
          "cannot open regular file " + path.string() + ": " +
          std::strerror(errno));
    }
    struct stat status {};
    if (fstat(descriptor_, &status) != 0 || !S_ISREG(status.st_mode) ||
        status.st_size < 0) {
      close(descriptor_);
      descriptor_ = -1;
      throw std::runtime_error("path is not a regular file: " + path.string());
    }
    size_ = static_cast<std::uint64_t>(status.st_size);
  }

  ~RegularFile() {
    if (descriptor_ >= 0) close(descriptor_);
  }

  RegularFile(const RegularFile&) = delete;
  RegularFile& operator=(const RegularFile&) = delete;

  std::uint64_t size() const { return size_; }

  std::size_t Read(std::uint8_t* destination, std::size_t capacity) {
    for (;;) {
      const ssize_t count = read(descriptor_, destination, capacity);
      if (count >= 0) return static_cast<std::size_t>(count);
      if (errno != EINTR) {
        throw std::runtime_error(
            "cannot read regular file " + path_.string() + ": " +
            std::strerror(errno));
      }
    }
  }

 private:
  fs::path path_;
  int descriptor_ = -1;
  std::uint64_t size_ = 0;
};

std::vector<std::uint8_t> ReadRegularFile(const fs::path& path) {
  RegularFile input(path);
  if (input.size() > static_cast<std::uint64_t>(
                         std::numeric_limits<std::size_t>::max())) {
    throw std::runtime_error("regular file is too large: " + path.string());
  }
  std::vector<std::uint8_t> bytes(static_cast<std::size_t>(input.size()));
  std::size_t offset = 0;
  while (offset < bytes.size()) {
    const std::size_t count = input.Read(bytes.data() + offset, bytes.size() - offset);
    if (count == 0) {
      throw std::runtime_error("regular file shortened while reading: " + path.string());
    }
    offset += count;
  }
  std::uint8_t trailing = 0;
  if (input.Read(&trailing, 1) != 0) {
    throw std::runtime_error("regular file grew while reading: " + path.string());
  }
  return bytes;
}

std::string ReadRegularText(const fs::path& path) {
  const std::vector<std::uint8_t> bytes = ReadRegularFile(path);
  return std::string(bytes.begin(), bytes.end());
}

void RequireDirectory(const fs::path& path, const char* label) {
  const fs::file_status status = fs::symlink_status(path);
  if (fs::is_symlink(status) || !fs::is_directory(status)) {
    throw std::runtime_error(std::string(label) + " is not a non-symlink directory");
  }
}

void RequireExactDirectoryEntries(
    const fs::path& directory,
    const std::set<std::string>& expected,
    bool files_only) {
  RequireDirectory(directory, "comparison directory");
  std::set<std::string> observed;
  for (const fs::directory_entry& entry : fs::directory_iterator(directory)) {
    const fs::file_status status = entry.symlink_status();
    if (fs::is_symlink(status) || (files_only && !fs::is_regular_file(status))) {
      throw std::runtime_error(
          "comparison directory contains a forbidden entry: " +
          entry.path().filename().string());
    }
    observed.insert(entry.path().filename().string());
  }
  if (observed != expected) {
    throw std::runtime_error(
        "comparison directory population differs: " + directory.string());
  }
}

std::map<std::string, std::string> ParseTreatmentReceipt(const fs::path& path) {
  const std::string text = ReadRegularText(path);
  if (text.empty() || text.back() != '\n') {
    throw std::runtime_error("treatment receipt is empty or unterminated");
  }
  std::map<std::string, std::string> fields;
  std::size_t begin = 0;
  while (begin < text.size()) {
    const std::size_t end = text.find('\n', begin);
    if (end == std::string::npos || end == begin) {
      throw std::runtime_error("treatment receipt contains an invalid line");
    }
    const std::string_view line(text.data() + begin, end - begin);
    const std::size_t separator = line.find('=');
    if (separator == std::string_view::npos || separator == 0 ||
        separator + 1 == line.size()) {
      throw std::runtime_error("treatment receipt contains an invalid field");
    }
    const auto [unused, inserted] = fields.emplace(
        std::string(line.substr(0, separator)),
        std::string(line.substr(separator + 1)));
    static_cast<void>(unused);
    if (!inserted) {
      throw std::runtime_error("treatment receipt contains a duplicate field");
    }
    begin = end + 1;
  }
  return fields;
}

void ValidateTreatmentBeforeOracle(
    const ProfileGeometry& geometry,
    const fs::path& treatment_root) {
  RequireDirectory(treatment_root, "treatment root");
  RequireExactDirectoryEntries(
      treatment_root,
      {"checkpoints", "complete.marker", "gradients", "treatment.txt"},
      false);
  if (ReadRegularText(treatment_root / "complete.marker") != "COMPLETE\n") {
    throw std::runtime_error("treatment completion marker differs");
  }
  const std::map<std::string, std::string> fields =
      ParseTreatmentReceipt(treatment_root / "treatment.txt");
  const std::set<std::string> expected_fields{
      "claim_label",
      "gradient_count",
      "mode",
      "objective_credit_bytes",
      "schema",
      "teacher_gradient_inputs",
  };
  std::set<std::string> observed_fields;
  for (const auto& [name, unused] : fields) {
    static_cast<void>(unused);
    observed_fields.insert(name);
  }
  if (observed_fields != expected_fields ||
      fields.at("schema") != kTreatmentSchema ||
      fields.at("mode") != "full-comparator" ||
      fields.at("teacher_gradient_inputs") != "0" ||
      fields.at("objective_credit_bytes") != "0" ||
      fields.at("gradient_count") != std::to_string(
          CanonicalGradientDescriptors(geometry).size())) {
    throw std::runtime_error("treatment receipt contract differs");
  }
}

void RecordFirstMismatch(
    ProfileComparisonSummary& summary,
    std::string kind,
    std::string name,
    const ExactFileComparison& comparison) {
  if (!summary.first_mismatch.has_value() && comparison.first_mismatch.has_value()) {
    summary.first_mismatch_kind = std::move(kind);
    summary.first_mismatch_name = std::move(name);
    summary.first_mismatch = comparison.first_mismatch;
  }
}

ExactFileComparison CompareToMemory(
    const std::uint8_t* expected,
    std::size_t expected_size,
    const fs::path& observed_path) {
  RegularFile observed(observed_path);
  ExactFileComparison result{
      .expected_bytes = expected_size,
      .observed_bytes = observed.size(),
      .mismatch_bytes = 0,
      .first_mismatch = std::nullopt,
  };
  constexpr std::size_t kBufferSize = 1U << 20U;
  std::array<std::uint8_t, kBufferSize> buffer{};
  std::uint64_t offset = 0;
  while (offset < observed.size()) {
    const std::size_t requested = static_cast<std::size_t>(std::min<std::uint64_t>(
        buffer.size(), observed.size() - offset));
    const std::size_t count = observed.Read(buffer.data(), requested);
    if (count == 0) {
      throw std::runtime_error("observed file shortened while comparing");
    }
    for (std::size_t index = 0; index < count; ++index) {
      const std::uint64_t absolute = offset + index;
      const bool expected_present = absolute < expected_size;
      const int expected_byte = expected_present ? expected[absolute] : -1;
      if (!expected_present || expected_byte != buffer[index]) {
        ++result.mismatch_bytes;
        if (!result.first_mismatch.has_value()) {
          result.first_mismatch = FileMismatch{
              .offset = absolute,
              .expected_byte = expected_byte,
              .observed_byte = buffer[index],
          };
        }
      }
    }
    offset += count;
  }
  if (expected_size > observed.size()) {
    const std::uint64_t missing = expected_size - observed.size();
    result.mismatch_bytes += missing;
    if (!result.first_mismatch.has_value()) {
      result.first_mismatch = FileMismatch{
          .offset = observed.size(),
          .expected_byte = expected[observed.size()],
          .observed_byte = -1,
      };
    }
  }
  std::uint8_t trailing = 0;
  if (observed.Read(&trailing, 1) != 0) {
    throw std::runtime_error("observed file grew while comparing");
  }
  return result;
}

}  // namespace

ExactFileComparison CompareRegularFilesExact(
    const fs::path& expected_path,
    const fs::path& observed_path) {
  RegularFile expected(expected_path);
  RegularFile observed(observed_path);
  ExactFileComparison result{
      .expected_bytes = expected.size(),
      .observed_bytes = observed.size(),
      .mismatch_bytes = 0,
      .first_mismatch = std::nullopt,
  };
  constexpr std::size_t kBufferSize = 1U << 20U;
  std::array<std::uint8_t, kBufferSize> expected_buffer{};
  std::array<std::uint8_t, kBufferSize> observed_buffer{};
  std::uint64_t offset = 0;
  const std::uint64_t common = std::min(expected.size(), observed.size());
  while (offset < common) {
    const std::size_t requested = static_cast<std::size_t>(
        std::min<std::uint64_t>(kBufferSize, common - offset));
    const std::size_t expected_count = expected.Read(expected_buffer.data(), requested);
    const std::size_t observed_count = observed.Read(observed_buffer.data(), requested);
    if (expected_count != requested || observed_count != requested) {
      throw std::runtime_error("regular file changed while comparing");
    }
    for (std::size_t index = 0; index < requested; ++index) {
      if (expected_buffer[index] != observed_buffer[index]) {
        ++result.mismatch_bytes;
        if (!result.first_mismatch.has_value()) {
          result.first_mismatch = FileMismatch{
              .offset = offset + index,
              .expected_byte = expected_buffer[index],
              .observed_byte = observed_buffer[index],
          };
        }
      }
    }
    offset += requested;
  }
  if (expected.size() != observed.size()) {
    result.mismatch_bytes += expected.size() > observed.size()
        ? expected.size() - observed.size()
        : observed.size() - expected.size();
    if (!result.first_mismatch.has_value()) {
      std::uint8_t extra = 0;
      RegularFile& longer = expected.size() > common ? expected : observed;
      if (longer.Read(&extra, 1) != 1) {
        throw std::runtime_error("regular file changed while comparing length");
      }
      result.first_mismatch = FileMismatch{
          .offset = common,
          .expected_byte = expected.size() > common ? extra : -1,
          .observed_byte = observed.size() > common ? extra : -1,
      };
    }
  }
  return result;
}

ExactFileComparison CompareRegularFileToBytes(
    const std::vector<std::uint8_t>& expected,
    const fs::path& observed) {
  return CompareToMemory(expected.data(), expected.size(), observed);
}

ProfileComparisonSummary CompareCompleteProfileTreatment(
    const ProfileGeometry& geometry,
    const fs::path& treatment_root,
    const fs::path& oracle_root) {
  ValidateTreatmentBeforeOracle(geometry, treatment_root);

  // No oracle path is touched above this line.
  RequireDirectory(oracle_root, "oracle root");
  if (ReadRegularText(oracle_root / "complete.marker") != "COMPLETE\n") {
    throw std::runtime_error("oracle completion marker differs");
  }
  if (ReadRegularText(oracle_root / "boundary.txt") != kOracleBoundary) {
    throw std::runtime_error("oracle boundary differs");
  }

  const std::vector<GradientDescriptor> descriptors =
      CanonicalGradientDescriptors(geometry);
  std::set<std::string> gradient_names;
  for (std::size_t index = 0; index < descriptors.size(); ++index) {
    const std::string stem = CanonicalGradientArtifactStem(index, descriptors[index]);
    gradient_names.insert(stem + ".bin");
    gradient_names.insert(stem + ".meta");
  }
  RequireExactDirectoryEntries(
      treatment_root / "gradients", gradient_names, true);
  RequireExactDirectoryEntries(oracle_root / "gradients", gradient_names, true);

  std::set<std::string> checkpoint_names{
      "embedding_input_adjoint.bf16",
      "output_probabilities.f32",
      "top_attention_dp_source.bf16",
      "top_attention_dp_stream_major.bf16",
  };
  for (std::size_t layer = 0; layer < geometry.layers; ++layer) {
    checkpoint_names.insert("train_h_" + std::to_string(layer) + ".bf16");
  }
  RequireExactDirectoryEntries(
      treatment_root / "checkpoints", checkpoint_names, true);

  ProfileComparisonSummary summary;
  for (std::size_t index = 0; index < descriptors.size(); ++index) {
    const std::string stem = CanonicalGradientArtifactStem(index, descriptors[index]);
    const ExactFileComparison metadata = CompareRegularFilesExact(
        oracle_root / "gradients" / (stem + ".meta"),
        treatment_root / "gradients" / (stem + ".meta"));
    summary.gradient_metadata_bytes += metadata.expected_bytes;
    summary.gradient_metadata_mismatch_bytes += metadata.mismatch_bytes;
    RecordFirstMismatch(summary, "gradient_metadata", stem, metadata);
    const ExactFileComparison payload = CompareRegularFilesExact(
        oracle_root / "gradients" / (stem + ".bin"),
        treatment_root / "gradients" / (stem + ".bin"));
    summary.gradient_payload_bytes += payload.expected_bytes;
    summary.gradient_payload_mismatch_bytes += payload.mismatch_bytes;
    RecordFirstMismatch(summary, "gradient_payload", stem, payload);
    ++summary.gradient_count;
  }

  const TensorContainer oracle_state(oracle_root / "state_initial.params");
  const std::size_t model = geometry.transformer.heads *
      geometry.transformer.head_width;
  for (std::size_t layer = 0; layer < geometry.layers; ++layer) {
    const std::string name = "train_h_" + std::to_string(layer);
    const Bf16Buffer expected = oracle_state.CopyBf16(
        name,
        {model, geometry.transformer.streams, geometry.transformer.states});
    if (expected.size() > std::numeric_limits<std::size_t>::max() / sizeof(Bf16)) {
      throw std::runtime_error("train_h byte count overflows");
    }
    const std::uint8_t* bytes =
        reinterpret_cast<const std::uint8_t*>(expected.data());
    const std::size_t byte_count = expected.size() * sizeof(Bf16);
    const ExactFileComparison comparison = CompareToMemory(
        bytes,
        byte_count,
        treatment_root / "checkpoints" / (name + ".bf16"));
    summary.train_h_bytes += comparison.expected_bytes;
    summary.train_h_mismatch_bytes += comparison.mismatch_bytes;
    RecordFirstMismatch(summary, "train_h", name, comparison);
    ++summary.train_h_count;
  }
  return summary;
}

}  // namespace gamma_enwiki9::nncp
