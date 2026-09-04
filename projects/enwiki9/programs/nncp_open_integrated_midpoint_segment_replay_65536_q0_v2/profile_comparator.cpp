#include "profile_compare.hpp"

#include "midpoint_kernels.hpp"

#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>

namespace fs = std::filesystem;
namespace nncp = gamma_enwiki9::nncp;

namespace {

void WriteReceipt(const fs::path& path, const std::string& text) {
  if (fs::exists(path)) {
    throw std::runtime_error("refusing to replace comparator receipt");
  }
  if (text.size() > static_cast<std::size_t>(
                        std::numeric_limits<std::streamsize>::max())) {
    throw std::runtime_error("comparator receipt is too large");
  }
  const fs::path partial = path.string() + ".partial";
  if (fs::exists(partial)) {
    throw std::runtime_error("comparator partial receipt already exists");
  }
  std::ofstream output(partial, std::ios::binary | std::ios::trunc);
  if (!output) throw std::runtime_error("cannot create comparator receipt");
  output.write(text.data(), static_cast<std::streamsize>(text.size()));
  output.flush();
  if (!output) throw std::runtime_error("cannot write comparator receipt");
  output.close();
  if (!output) throw std::runtime_error("cannot close comparator receipt");
  fs::rename(partial, path);
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 4) {
      std::cerr << "usage: " << argv[0]
                << " COMPLETE_TREATMENT ORACLE_FIXTURE RECEIPT\n";
      return 2;
    }
    nncp::ValidateArithmeticEnvironment();
    const nncp::ProfileGeometry geometry{
        .transformer = {64, 32, 8, 128, 256, 3072},
        .layers = 20,
        .vocabulary = 16392,
        .loss_start = 0,
        .loss_length = 64,
    };
    const nncp::ProfileComparisonSummary result =
        nncp::CompareCompleteProfileTreatment(geometry, argv[1], argv[2]);
    std::ostringstream receipt;
    receipt << "schema=gamma.enwiki9.nncp-open-midpoint-comparator.v2\n"
            << "gradient_count=" << result.gradient_count << '\n'
            << "gradient_metadata_bytes=" << result.gradient_metadata_bytes << '\n'
            << "gradient_metadata_mismatch_bytes="
            << result.gradient_metadata_mismatch_bytes << '\n'
            << "gradient_payload_bytes=" << result.gradient_payload_bytes << '\n'
            << "gradient_payload_mismatch_bytes="
            << result.gradient_payload_mismatch_bytes << '\n'
            << "train_h_count=" << result.train_h_count << '\n'
            << "train_h_bytes=" << result.train_h_bytes << '\n'
            << "train_h_mismatch_bytes=" << result.train_h_mismatch_bytes << '\n'
            << "first_mismatch_kind=" << result.first_mismatch_kind << '\n'
            << "first_mismatch_name=" << result.first_mismatch_name << '\n';
    if (result.first_mismatch.has_value()) {
      receipt << "first_mismatch_offset=" << result.first_mismatch->offset << '\n'
              << "first_mismatch_expected="
              << result.first_mismatch->expected_byte << '\n'
              << "first_mismatch_observed="
              << result.first_mismatch->observed_byte << '\n';
    } else {
      receipt << "first_mismatch_offset=none\n"
              << "first_mismatch_expected=none\n"
              << "first_mismatch_observed=none\n";
    }
    receipt << "exact_parity=" << (result.exact() ? 1 : 0) << '\n'
            << "objective_credit_bytes=0\n";
    WriteReceipt(argv[3], receipt.str());
    std::cout << (result.exact() ? "MIDPOINT_PROFILE_COMPARATOR_EXACT\n"
                                 : "MIDPOINT_PROFILE_COMPARATOR_DIFFERENT\n");
    return result.exact() ? 0 : 3;
  } catch (const std::exception& error) {
    std::cerr << "profile comparator failed: " << error.what() << '\n';
    return 1;
  }
}
