#include "midpoint_kernels.hpp"
#include "midpoint_segment.hpp"
#include "profile_fixture.hpp"
#include "profile_population.hpp"
#include "profile_trace.hpp"

#include <algorithm>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace fs = std::filesystem;
namespace nncp = gamma_enwiki9::nncp;

namespace {

constexpr std::size_t kSymbols = 65536;
constexpr std::size_t kStreams = 32;
constexpr std::size_t kStates = 64;
constexpr std::size_t kModelBatches = 32;
constexpr std::size_t kAnalyticalSegments = 1024;
constexpr std::size_t kVocabulary = 16392;

void RequireRegularInput(const fs::path& path, const char* label) {
  const fs::file_status status = fs::symlink_status(path);
  if (fs::is_symlink(status) || !fs::is_regular_file(status)) {
    throw std::runtime_error(std::string(label) + " is not a regular file");
  }
}

void ValidateClaimLabel(std::string_view value) {
  if (value.empty() || value.size() > 128) {
    throw std::runtime_error("claim label length is invalid");
  }
  for (const unsigned char byte : value) {
    const bool ascii_alphanumeric =
        (byte >= '0' && byte <= '9') ||
        (byte >= 'A' && byte <= 'Z') ||
        (byte >= 'a' && byte <= 'z');
    if (!(ascii_alphanumeric || byte == '.' || byte == '_' || byte == '-')) {
      throw std::runtime_error("claim label contains a forbidden byte");
    }
  }
}

std::pair<nncp::MidpointArm, std::string> ParseArm(std::string_view value) {
  if (value == "O") return {nncp::MidpointArm::kO, "O"};
  if (value == "K") return {nncp::MidpointArm::kK, "K"};
  if (value == "F") return {nncp::MidpointArm::kF, "F"};
  if (value == "S") return {nncp::MidpointArm::kS, "S"};
  throw std::runtime_error("population arm must be O, K, F, or S");
}

void WriteText(const fs::path& path, const std::string& value) {
  if (fs::exists(path)) {
    throw std::runtime_error("refusing to replace " + path.string());
  }
  const fs::path partial = path.string() + ".partial";
  if (fs::exists(partial)) {
    throw std::runtime_error("partial output already exists: " + partial.string());
  }
  if (value.size() > static_cast<std::size_t>(
                         std::numeric_limits<std::streamsize>::max())) {
    throw std::runtime_error("text output is too large");
  }
  std::ofstream output(partial, std::ios::binary | std::ios::trunc);
  if (!output) throw std::runtime_error("cannot create " + partial.string());
  output.write(value.data(), static_cast<std::streamsize>(value.size()));
  output.flush();
  if (!output) throw std::runtime_error("cannot write " + partial.string());
  output.close();
  if (!output) throw std::runtime_error("cannot close " + partial.string());
  fs::rename(partial, path);
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 8) {
      std::cerr << "usage: " << argv[0]
                << " PARAMETERS OPTIMIZER INITIAL_STATE SYMBOLS_BE16"
                   " O|K|F|S OUTPUT_DIR CLAIM_LABEL\n";
      return 2;
    }
    nncp::ValidateArithmeticEnvironment();
    const fs::path parameters = argv[1];
    const fs::path optimizer_path = argv[2];
    const fs::path initial_state = argv[3];
    const fs::path symbol_path = argv[4];
    const auto [arm, arm_name] = ParseArm(argv[5]);
    const fs::path output = argv[6];
    const std::string claim_label = argv[7];
    ValidateClaimLabel(claim_label);
    RequireRegularInput(parameters, "parameter input");
    RequireRegularInput(optimizer_path, "optimizer input");
    RequireRegularInput(initial_state, "initial-state input");
    RequireRegularInput(symbol_path, "symbol input");
    if (fs::exists(output) || !fs::create_directory(output)) {
      throw std::runtime_error("population output directory must not exist");
    }

    const nncp::ProfileGeometry geometry{
        .transformer = {kStates, kStreams, 8, 128, 256, 3072},
        .layers = 20,
        .vocabulary = kVocabulary,
        .loss_start = 0,
        .loss_length = kStates,
    };
    nncp::ProfileFixtureInputs fixture = nncp::LoadProfileInitialFixture(
        geometry,
        parameters,
        initial_state);
    nncp::ProfileAdamState optimizer = nncp::LoadProfileAdamState(
        geometry, optimizer_path, 1);
    const std::vector<std::uint32_t> symbols =
        nncp::LoadBigEndianProfileSymbols(
            symbol_path, kSymbols, kVocabulary);
    const nncp::ProfilePopulationBatch initial_batch =
        nncp::BuildProfilePopulationBatch(
            symbols, kStreams, kStates, 0, kVocabulary);
    if (fixture.input_symbols != initial_batch.input_symbols ||
        fixture.targets != initial_batch.targets) {
      throw std::runtime_error(
          "initial-state symbols differ from population batch zero");
    }

    const fs::path witnesses = output / "state-witnesses.txt";
    const fs::path witness_partial = witnesses.string() + ".partial";
    std::ofstream witness_stream(
        witness_partial, std::ios::binary | std::ios::trunc);
    if (!witness_stream) {
      throw std::runtime_error("cannot create state witness output");
    }
    witness_stream
        << "schema=gamma.enwiki9.nncp-open-population-state-witness.v1\n"
        << "arm=" << arm_name << '\n'
        << "initial_next_update_exponent=1\n"
        << "initial_state_sha256="
        << nncp::ProfileFutureStateSha256(
               geometry, fixture.weights, optimizer, fixture.memory_inputs)
        << '\n';
    if (!witness_stream) {
      throw std::runtime_error("cannot write initial state witness");
    }

    std::vector<bool> observed_coordinates(kSymbols, false);
    nncp::CandidateBranchTraceWriter trace(output / "branch-trace.bin", kVocabulary);
    std::vector<nncp::Bf16Buffer> memory = std::move(fixture.memory_inputs);
    for (std::size_t model_batch = 0;
         model_batch < kModelBatches;
         ++model_batch) {
      nncp::ProfilePopulationBatch batch = nncp::BuildProfilePopulationBatch(
          symbols, kStreams, kStates, model_batch, kVocabulary);
      const float learning_rate = nncp::FrozenProfileLearningRate(model_batch);
      nncp::MidpointSegmentResult result = nncp::RunMidpointSegmentArm(
          geometry,
          arm,
          fixture.weights,
          optimizer,
          memory,
          batch.input_symbols,
          batch.targets,
          learning_rate);
      const std::size_t expected_probability_values =
          kStates * kStreams * kVocabulary;
      if (result.coded_probabilities.size() != expected_probability_values ||
          result.first_update.update_exponent != 1 + 2 * model_batch ||
          result.second_update.update_exponent != 2 + 2 * model_batch ||
          optimizer.next_update_exponent != 3 + 2 * model_batch) {
        throw std::runtime_error("population model-batch schedule differs");
      }
      for (std::size_t execution = 0;
           execution < batch.targets.size();
           ++execution) {
        const std::uint64_t original = batch.original_coordinates[execution];
        if (original >= observed_coordinates.size() ||
            observed_coordinates[original]) {
          throw std::runtime_error("population coordinate is duplicate or invalid");
        }
        observed_coordinates[original] = true;
        trace.WriteRow(
            original,
            static_cast<std::uint16_t>(batch.targets[execution]),
            std::span<const float>(
                result.coded_probabilities.data() + execution * kVocabulary,
                kVocabulary));
      }
      memory = std::move(result.next_memory);
      witness_stream
          << "model_batch=" << model_batch << '\n'
          << "learning_rate=" << std::hexfloat << learning_rate
          << std::defaultfloat << '\n'
          << "first_update_exponent=" << result.first_update.update_exponent
          << '\n'
          << "second_update_exponent=" << result.second_update.update_exponent
          << '\n'
          << "next_update_exponent=" << optimizer.next_update_exponent << '\n'
          << "state_sha256="
          << nncp::ProfileFutureStateSha256(
                 geometry, fixture.weights, optimizer, memory)
          << '\n';
      if (!witness_stream) {
        throw std::runtime_error("cannot write population state witness");
      }
    }
    if (!std::all_of(
            observed_coordinates.begin(),
            observed_coordinates.end(),
            [](bool value) { return value; })) {
      throw std::runtime_error("population coordinate coverage is incomplete");
    }
    trace.Finalize();
    witness_stream.flush();
    if (!witness_stream) {
      throw std::runtime_error("cannot finalize population state witness");
    }
    witness_stream.close();
    if (!witness_stream) {
      throw std::runtime_error("cannot close population state witness");
    }
    fs::rename(witness_partial, witnesses);

    std::ostringstream receipt;
    receipt
        << "schema=gamma.enwiki9.nncp-open-population-treatment.v2\n"
        << "arm=" << arm_name << '\n'
        << "claim_label=" << claim_label << '\n'
        << "symbols=65536\n"
        << "streams=32\n"
        << "stream_stride=2048\n"
        << "model_batches=32\n"
        << "analytical_segments=1024\n"
        << "states_per_stream_segment=64\n"
        << "first_half_states=32\n"
        << "vocabulary=16392\n"
        << "final_next_update_exponent=65\n"
        << "teacher_inputs=0\n"
        << "oracle_inputs=0\n"
        << "objective_credit_bytes=0\n";
    WriteText(output / "treatment.txt", receipt.str());
    WriteText(output / "complete.marker", "COMPLETE\n");
    std::cout << "MIDPOINT_PROFILE_POPULATION_COMPLETE\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "profile population treatment failed: " << error.what() << '\n';
    return 1;
  }
}
