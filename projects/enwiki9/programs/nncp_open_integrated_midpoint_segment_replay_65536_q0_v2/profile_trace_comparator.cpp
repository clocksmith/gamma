#include "midpoint_kernels.hpp"
#include "profile_trace.hpp"

#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>

namespace fs = std::filesystem;
namespace nncp = gamma_enwiki9::nncp;

namespace {

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
                << " COMPLETE_CANDIDATE_TRACE INDEXED_ORACLE RECEIPT\n";
      return 2;
    }
    nncp::ValidateArithmeticEnvironment();
    const nncp::TraceComparisonSummary result =
        nncp::CompareCandidateTraceToIndexedOracle(
            argv[1], argv[2], 65536, 16392);
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
