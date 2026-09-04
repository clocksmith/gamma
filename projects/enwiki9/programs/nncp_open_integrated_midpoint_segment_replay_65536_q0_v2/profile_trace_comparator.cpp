#include "midpoint_kernels.hpp"
#include "profile_population.hpp"
#include "profile_trace.hpp"

#include <algorithm>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace fs = std::filesystem;
namespace nncp = gamma_enwiki9::nncp;

namespace {

std::string ReadRegularText(
    const fs::path& path,
    std::size_t maximum_bytes) {
  const fs::file_status status = fs::symlink_status(path);
  if (fs::is_symlink(status) || !fs::is_regular_file(status) ||
      fs::file_size(path) > maximum_bytes) {
    throw std::runtime_error("invalid treatment text input: " + path.string());
  }
  std::ifstream input(path, std::ios::binary);
  const std::string value{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  if (!input.eof() && input.fail()) {
    throw std::runtime_error("cannot read treatment text input");
  }
  return value;
}

std::unordered_map<std::string, std::string> ParseReceipt(
    const std::string& text) {
  std::unordered_map<std::string, std::string> values;
  std::istringstream input(text);
  std::string line;
  while (std::getline(input, line)) {
    const std::size_t separator = line.find('=');
    if (separator == std::string::npos || separator == 0 ||
        separator + 1 == line.size()) {
      throw std::runtime_error("population treatment receipt is malformed");
    }
    const auto [unused, inserted] = values.emplace(
        line.substr(0, separator), line.substr(separator + 1));
    static_cast<void>(unused);
    if (!inserted) {
      throw std::runtime_error("population treatment receipt has duplicate keys");
    }
  }
  return values;
}

bool IsLowerHexDigest(std::string_view value) {
  return value.size() == 64 &&
      std::all_of(value.begin(), value.end(), [](char byte) {
        return (byte >= '0' && byte <= '9') ||
            (byte >= 'a' && byte <= 'f');
      });
}

std::string LearningRateLine(std::size_t model_batch) {
  std::ostringstream output;
  output << "learning_rate=" << std::hexfloat
         << nncp::FrozenProfileLearningRate(model_batch);
  return output.str();
}

void ValidateStateWitness(const std::string& text, std::string_view arm) {
  if (text.empty() || text.back() != '\n') {
    throw std::runtime_error("population state witness is not terminated");
  }
  std::istringstream input(text);
  std::vector<std::string> lines;
  std::string line;
  while (std::getline(input, line)) lines.push_back(std::move(line));
  constexpr std::size_t kModelBatches = 32;
  constexpr std::size_t kHeaderLines = 4;
  constexpr std::size_t kLinesPerSegment = 6;
  if (lines.size() != kHeaderLines + kModelBatches * kLinesPerSegment ||
      lines[0] !=
          "schema=gamma.enwiki9.nncp-open-population-state-witness.v1" ||
      lines[1] != "arm=" + std::string(arm) ||
      lines[2] != "initial_next_update_exponent=1" ||
      !lines[3].starts_with("initial_state_sha256=") ||
      !IsLowerHexDigest(lines[3].substr(21))) {
    throw std::runtime_error("population state witness header differs");
  }
  std::size_t offset = kHeaderLines;
  for (std::size_t model_batch = 0;
       model_batch < kModelBatches;
       ++model_batch) {
    if (lines[offset] != "model_batch=" + std::to_string(model_batch) ||
        lines[offset + 1] != LearningRateLine(model_batch) ||
        lines[offset + 2] !=
            "first_update_exponent=" + std::to_string(1 + 2 * model_batch) ||
        lines[offset + 3] !=
            "second_update_exponent=" + std::to_string(2 + 2 * model_batch) ||
        lines[offset + 4] !=
            "next_update_exponent=" + std::to_string(3 + 2 * model_batch) ||
        !lines[offset + 5].starts_with("state_sha256=") ||
        !IsLowerHexDigest(lines[offset + 5].substr(13))) {
      throw std::runtime_error("population state witness segment differs");
    }
    offset += kLinesPerSegment;
  }
}

fs::path ValidateCompleteTreatment(const fs::path& directory) {
  const fs::file_status status = fs::symlink_status(directory);
  if (fs::is_symlink(status) || !fs::is_directory(status)) {
    throw std::runtime_error("population treatment is not a regular directory");
  }
  const std::set<std::string> expected{
      "branch-trace.bin",
      "complete.marker",
      "state-witnesses.txt",
      "treatment.txt",
  };
  std::set<std::string> observed;
  for (const fs::directory_entry& entry : fs::directory_iterator(directory)) {
    const fs::file_status entry_status = entry.symlink_status();
    if (fs::is_symlink(entry_status) || !fs::is_regular_file(entry_status)) {
      throw std::runtime_error("population treatment contains a non-regular output");
    }
    observed.insert(entry.path().filename().string());
  }
  if (observed != expected) {
    throw std::runtime_error("population treatment output closure differs");
  }
  if (ReadRegularText(directory / "complete.marker", 32) != "COMPLETE\n") {
    throw std::runtime_error("population treatment is incomplete");
  }
  const std::unordered_map<std::string, std::string> receipt =
      ParseReceipt(ReadRegularText(directory / "treatment.txt", 4096));
  const auto require = [&receipt](std::string_view key, std::string_view value) {
    const auto found = receipt.find(std::string(key));
    if (found == receipt.end() || found->second != value) {
      throw std::runtime_error("population treatment receipt contract differs");
    }
  };
  require("schema", "gamma.enwiki9.nncp-open-population-treatment.v2");
  require("symbols", "65536");
  require("streams", "32");
  require("stream_stride", "2048");
  require("model_batches", "32");
  require("analytical_segments", "1024");
  require("states_per_stream_segment", "64");
  require("first_half_states", "32");
  require("vocabulary", "16392");
  require("final_next_update_exponent", "65");
  require("teacher_inputs", "0");
  require("oracle_inputs", "0");
  require("objective_credit_bytes", "0");
  const auto arm = receipt.find("arm");
  if (arm == receipt.end() ||
      (arm->second != "O" && arm->second != "K" &&
       arm->second != "F" && arm->second != "S")) {
    throw std::runtime_error("population treatment arm differs");
  }
  if (receipt.size() != 15 || receipt.find("claim_label") == receipt.end()) {
    throw std::runtime_error("population treatment receipt population differs");
  }
  ValidateStateWitness(
      ReadRegularText(directory / "state-witnesses.txt", 16384),
      arm->second);
  return directory / "branch-trace.bin";
}

void WriteReceipt(const fs::path& path, const std::string& text) {
  if (fs::exists(path)) throw std::runtime_error("trace receipt already exists");
  const fs::path partial = path.string() + ".partial";
  if (fs::exists(partial)) throw std::runtime_error("trace receipt partial exists");
  if (text.size() > static_cast<std::size_t>(
                        std::numeric_limits<std::streamsize>::max())) {
    throw std::runtime_error("trace receipt is too large");
  }
  std::ofstream output(partial, std::ios::binary | std::ios::trunc);
  output.write(text.data(), static_cast<std::streamsize>(text.size()));
  output.flush();
  if (!output) throw std::runtime_error("cannot write trace receipt");
  output.close();
  fs::rename(partial, path);
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 4) {
      std::cerr << "usage: " << argv[0]
                << " COMPLETE_TREATMENT_DIR INDEXED_ORACLE RECEIPT\n";
      return 2;
    }
    nncp::ValidateArithmeticEnvironment();
    const fs::path candidate = ValidateCompleteTreatment(argv[1]);
    const nncp::TraceComparisonSummary result =
        nncp::CompareCandidateTraceToIndexedOracle(
            candidate, argv[2], 65536, 16392);
    std::ostringstream receipt;
    receipt << "schema=gamma.enwiki9.nncp-open-branch-trace-comparator.v2\n"
            << "rows=" << result.rows << '\n'
            << "branches=" << result.branches << '\n'
            << "probability_mismatches=" << result.probability_mismatches << '\n'
            << "maximum_probability_difference="
            << result.maximum_probability_difference << '\n';
    if (result.first_mismatch.has_value()) {
      receipt << "first_mismatch_row=" << result.first_mismatch->row << '\n'
              << "first_mismatch_branch="
              << static_cast<unsigned int>(result.first_mismatch->branch) << '\n'
              << "first_mismatch_expected="
              << result.first_mismatch->expected_probability << '\n'
              << "first_mismatch_observed="
              << result.first_mismatch->observed_probability << '\n';
    } else {
      receipt << "first_mismatch_row=none\n"
              << "first_mismatch_branch=none\n"
              << "first_mismatch_expected=none\n"
              << "first_mismatch_observed=none\n";
    }
    receipt << "exact_parity=" << (result.exact() ? 1 : 0) << '\n'
            << "objective_credit_bytes=0\n";
    WriteReceipt(argv[3], receipt.str());
    std::cout << (result.exact() ? "MIDPOINT_TRACE_COMPARATOR_EXACT\n"
                                 : "MIDPOINT_TRACE_COMPARATOR_DIFFERENT\n");
    return result.exact() ? 0 : 3;
  } catch (const std::exception& error) {
    std::cerr << "trace comparator failed: " << error.what() << '\n';
    return 1;
  }
}
