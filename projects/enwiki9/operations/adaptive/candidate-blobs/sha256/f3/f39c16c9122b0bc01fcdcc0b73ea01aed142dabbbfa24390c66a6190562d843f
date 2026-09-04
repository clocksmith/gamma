#ifndef GAMMA_ENWIKI9_NNCP_PROFILE_FIXTURE_HPP
#define GAMMA_ENWIKI9_NNCP_PROFILE_FIXTURE_HPP

#include "profile_backward.hpp"

#include <filesystem>
#include <vector>

namespace gamma_enwiki9::nncp {

enum class FutureInputPolicy {
  // Preserve all 64 source inputs. Used only for the retained full-segment
  // implementation comparator.
  kPreserve,
  // Reproduce the frozen midpoint construction: states 32..63 are zero while
  // the first-half gradient graph is built.
  kZeroSecondHalf,
};

struct ProfileFixtureInputs {
  ProfileWeights weights;
  std::vector<std::uint32_t> input_symbols;
  std::vector<std::uint32_t> targets;
  std::vector<Bf16Buffer> memory_inputs;
};

ProfileFixtureInputs LoadProfileFixture(
    const ProfileGeometry& geometry,
    const std::filesystem::path& parameter_container,
    const std::filesystem::path& state_container,
    FutureInputPolicy future_policy);

// Production population loader for the block-zero boundary. The state
// container must contain only input_all_streams, target_all_streams, and one
// mem_h tensor per layer; retained train_h activations are rejected.
ProfileFixtureInputs LoadProfileInitialFixture(
    const ProfileGeometry& geometry,
    const std::filesystem::path& parameter_container,
    const std::filesystem::path& initial_state_container);

}  // namespace gamma_enwiki9::nncp

#endif
