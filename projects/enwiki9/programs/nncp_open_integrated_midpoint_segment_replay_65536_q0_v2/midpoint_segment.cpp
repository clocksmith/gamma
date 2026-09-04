#include "midpoint_segment.hpp"

#include "profile_forward.hpp"
#include "profile_state.hpp"

#include <algorithm>
#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>

namespace gamma_enwiki9::nncp {

MidpointSegmentResult RunMidpointSegment(
    const ProfileGeometry& production_geometry,
    ProfileWeights& weights,
    ProfileAdamState& optimizer,
    const std::vector<Bf16Buffer>& memory,
    const std::vector<std::uint32_t>& input_symbols,
    const std::vector<std::uint32_t>& targets,
    float learning_rate) {
  constexpr std::size_t kStates = 64;
  constexpr std::size_t kHalf = 32;
  if (production_geometry.transformer.states != kStates ||
      production_geometry.loss_start != 0 ||
      production_geometry.loss_length != kStates) {
    throw std::invalid_argument(
        "midpoint schedule requires the frozen full 64-state geometry");
  }
  if (optimizer.next_update_exponent >
      std::numeric_limits<std::uint64_t>::max() - 2) {
    throw std::invalid_argument("midpoint optimizer exponent cannot advance twice");
  }
  const std::size_t streams = production_geometry.transformer.streams;
  if (streams == 0 ||
      kStates > std::numeric_limits<std::size_t>::max() / streams) {
    throw std::invalid_argument("midpoint sample geometry is invalid");
  }
  const std::size_t samples = kStates * streams;
  if (input_symbols.size() != samples || targets.size() != samples) {
    throw std::invalid_argument("midpoint symbol population differs");
  }
  if (production_geometry.vocabulary == 0 ||
      samples > std::numeric_limits<std::size_t>::max() /
          production_geometry.vocabulary) {
    throw std::invalid_argument("midpoint probability geometry is invalid");
  }
  F32Buffer coded_probabilities(
      samples * production_geometry.vocabulary);
  ProfileAdamUpdateResult first_update;
  {
    std::vector<std::uint32_t> first_inputs = input_symbols;
    std::vector<std::uint32_t> first_targets = targets;
    for (std::size_t state = kHalf; state < kStates; ++state) {
      std::fill_n(first_inputs.begin() + state * streams, streams, 0);
      std::fill_n(first_targets.begin() + state * streams, streams, 0);
    }
    ProfileGeometry first_geometry = production_geometry;
    first_geometry.loss_start = 0;
    first_geometry.loss_length = kHalf;
    const ProfileCache first_cache = ProfileForward(
        first_geometry, weights, first_inputs, first_targets, memory);
    const std::size_t first_values =
        kHalf * streams * production_geometry.vocabulary;
    std::copy_n(
        first_cache.probabilities.begin(),
        first_values,
        coded_probabilities.begin());
    const ProfileBackwardResult first_backward =
        ProfileBackward(first_geometry, weights, first_cache);
    first_update = ApplyProfileAdamUpdate(
        first_geometry,
        weights,
        first_backward.gradients,
        optimizer,
        learning_rate);
  }

  ProfileGeometry second_geometry = production_geometry;
  second_geometry.loss_start = kHalf;
  second_geometry.loss_length = kHalf;
  const ProfileCache rebuilt_cache = ProfileForward(
      second_geometry, weights, input_symbols, targets, memory);
  const std::size_t first_values =
      kHalf * streams * production_geometry.vocabulary;
  std::copy(
      rebuilt_cache.probabilities.begin() + first_values,
      rebuilt_cache.probabilities.end(),
      coded_probabilities.begin() + first_values);
  const ProfileBackwardResult second_backward =
      ProfileBackward(second_geometry, weights, rebuilt_cache);
  ProfileAdamUpdateResult second_update = ApplyProfileAdamUpdate(
      second_geometry,
      weights,
      second_backward.gradients,
      optimizer,
      learning_rate);
  std::vector<Bf16Buffer> next_memory =
      AdvanceProfileMemory(second_geometry, memory, rebuilt_cache);
  return {
      .coded_probabilities = std::move(coded_probabilities),
      .first_update = std::move(first_update),
      .second_update = std::move(second_update),
      .next_memory = std::move(next_memory),
  };
}

}  // namespace gamma_enwiki9::nncp
