// SPDX-License-Identifier: MIT
// Production initialization parity only; no forward, gradient, update or coding.
#include "midpoint_kernels.hpp"
#include "profile_artifacts.hpp"
#include "profile_fixture.hpp"
#include "profile_population.hpp"

#include <algorithm>
#include <bit>
#include <cstdint>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <span>
#include <stdexcept>
#include <vector>

namespace nncp = gamma_enwiki9::nncp;
namespace fs = std::filesystem;

static std::string SymbolDigest(const std::vector<std::uint32_t>& symbols) {
  if constexpr (std::endian::native != std::endian::little) {
    throw std::runtime_error("initialization witness requires little endian");
  }
  return nncp::Sha256Hex(std::span<const std::uint8_t>(
      reinterpret_cast<const std::uint8_t*>(symbols.data()),
      symbols.size() * sizeof(std::uint32_t)));
}

int main(int argc, char** argv) {
  try {
    if (argc != 6) {
      std::cerr << "usage: " << argv[0]
                << " PARAMETERS OPTIMIZER INITIAL_STATE SYMBOLS_BE16 OUTPUT_JSON\n";
      return 2;
    }
    for (int index = 1; index != 5; ++index) {
      const auto status = fs::symlink_status(argv[index]);
      if (!fs::is_regular_file(status) || fs::is_symlink(status)) {
        throw std::runtime_error("fixture input must be a regular non-symlink file");
      }
    }
    if (fs::exists(argv[5])) throw std::runtime_error("output already exists");
    nncp::ValidateArithmeticEnvironment();
    const nncp::ProfileGeometry geometry{
        .transformer = {64, 32, 8, 128, 256, 3072},
        .layers = 20, .vocabulary = 16392, .loss_start = 0, .loss_length = 64};
    auto fixture = nncp::LoadProfileInitialFixture(geometry, argv[1], argv[3]);
    const auto optimizer = nncp::LoadProfileAdamState(geometry, argv[2], 1);
    const auto symbols = nncp::LoadBigEndianProfileSymbols(argv[4], 65536, 16392);
    const auto batch = nncp::BuildProfilePopulationBatch(symbols, 32, 64, 0, 16392);
    if (fixture.input_symbols != batch.input_symbols || fixture.targets != batch.targets) {
      throw std::runtime_error("loaded initial batch differs from the symbol population");
    }
    for (const auto& memory : fixture.memory_inputs) {
      if (std::any_of(memory.begin(), memory.end(), [](auto word) { return word != 0; })) {
        throw std::runtime_error("loaded initial recurrent memory is nonzero");
      }
    }
    const auto parameters = nncp::CanonicalParameterArtifacts(geometry, fixture.weights);
    if (parameters.size() != 246 || optimizer.tensors.size() != 246 ||
        optimizer.next_update_exponent != 1 || fixture.memory_inputs.size() != 20) {
      throw std::runtime_error("loaded production topology differs");
    }
    const auto state_digest = nncp::ProfileFutureStateSha256(
        geometry, fixture.weights, optimizer, fixture.memory_inputs);
    std::ofstream output(argv[5], std::ios::binary);
    output << "{\n"
           << "  \"schema\": \"gamma.enwiki9.open-midas-initial-state-witness.v1\",\n"
           << "  \"futureStateSha256\": \"" << state_digest << "\",\n"
           << "  \"inputBatchSha256\": \"" << SymbolDigest(fixture.input_symbols) << "\",\n"
           << "  \"targetBatchSha256\": \"" << SymbolDigest(fixture.targets) << "\",\n"
           << "  \"parameterTensors\": 246, \"optimizerTensors\": 246,\n"
           << "  \"memoryTensors\": 20, \"nextUpdateExponent\": 1,\n"
           << "  \"populationSymbols\": 65536, \"batchSymbols\": 2048,\n"
           << "  \"forwardCalls\": 0, \"gradientCalls\": 0, \"updateCalls\": 0,\n"
           << "  \"codedSymbols\": 0, \"objectiveCreditBytes\": 0\n}\n";
    output.flush();
    if (!output) throw std::runtime_error("cannot write complete state witness");
    output.close();
    if (!output) throw std::runtime_error("cannot close state witness");
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
