#ifndef GAMMA_ENWIKI9_NNCP_MIDPOINT_SEGMENT_HPP
#define GAMMA_ENWIKI9_NNCP_MIDPOINT_SEGMENT_HPP

#include "adam_update.hpp"
#include "profile_backward.hpp"

#include <cstdint>
#include <vector>

namespace gamma_enwiki9::nncp {

enum class MidpointArm {
  // Full first-half backward and update.
  kF,
  // Direct output-head-only first-half backward and selected update.
  kO,
  // Full first-half bookkeeping, but commit only the same head update as O.
  kK,
  // O with the frozen next-state cyclic truth association in the first half.
  kS,
};

struct MidpointSegmentResult {
  // [state, stream, vocabulary]: states 0..31 come from the incoming model;
  // states 32..63 come from the midpoint-updated rebuild.
  F32Buffer coded_probabilities;
  ProfileAdamUpdateResult first_update;
  ProfileAdamUpdateResult second_update;
  std::vector<Bf16Buffer> next_memory;
};

// Executes the exact frozen 64-state schedule: zero-filled future graph,
// first-half backward/update, full causal rebuild, second-half
// backward/update, then one persistent-memory shift. Both updates use the same
// parent-segment learning rate.
MidpointSegmentResult RunMidpointSegment(
    const ProfileGeometry& production_geometry,
    ProfileWeights& weights,
    ProfileAdamState& optimizer,
    const std::vector<Bf16Buffer>& memory,
    const std::vector<std::uint32_t>& input_symbols,
    const std::vector<std::uint32_t>& targets,
    float learning_rate);

MidpointSegmentResult RunMidpointSegmentArm(
    const ProfileGeometry& production_geometry,
    MidpointArm arm,
    ProfileWeights& weights,
    ProfileAdamState& optimizer,
    const std::vector<Bf16Buffer>& memory,
    const std::vector<std::uint32_t>& input_symbols,
    const std::vector<std::uint32_t>& targets,
    float learning_rate);

}  // namespace gamma_enwiki9::nncp

#endif
