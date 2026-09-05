#ifndef GAMMA_ENWIKI9_NNCP_PROFILE_POPULATION_HPP
#define GAMMA_ENWIKI9_NNCP_PROFILE_POPULATION_HPP

#include "adam_update.hpp"

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <span>
#include <string>
#include <vector>

namespace gamma_enwiki9::nncp {

struct ProfilePopulationBatch {
  // All three arrays use [state, stream] execution order.
  std::vector<std::uint32_t> input_symbols;
  std::vector<std::uint32_t> targets;
  std::vector<std::uint64_t> original_coordinates;
};

// Loads exactly expected_symbols unsigned 16-bit big-endian symbols from a
// regular, non-symlink input and rejects values outside the frozen vocabulary.
std::vector<std::uint32_t> LoadBigEndianProfileSymbols(
    const std::filesystem::path& path,
    std::size_t expected_symbols,
    std::size_t vocabulary);

// Transposes one stream-major source segment into the state-major execution
// order used by ProfileForward. Position zero in each stream has the causal
// zero predecessor used by the retained NNCP implementation.
ProfilePopulationBatch BuildProfilePopulationBatch(
    std::span<const std::uint32_t> stream_major_symbols,
    std::size_t streams,
    std::size_t states,
    std::size_t model_batch_index,
    std::size_t vocabulary);

// Exact frozen enwik9 profile interpolation at parent-segment indexes 0..31.
float FrozenProfileLearningRate(std::size_t parent_model_batch_index);

// General SHA-256 helper used by the self-test and state witness implementation.
std::string Sha256Hex(std::span<const std::uint8_t> bytes);

// Hashes every future-affecting parameter, compensated low word, Adam second
// moment, optimizer exponent, and recurrent-memory byte in canonical order.
std::string ProfileFutureStateSha256(
    const ProfileGeometry& geometry,
    ProfileWeights& weights,
    const ProfileAdamState& optimizer,
    const std::vector<Bf16Buffer>& memory);

}  // namespace gamma_enwiki9::nncp

#endif
