#include "profile_output_head.hpp"

#include "midpoint_kernels.hpp"

#include <initializer_list>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>

namespace gamma_enwiki9::nncp {
namespace {

std::size_t Product(
    std::initializer_list<std::size_t> factors,
    const char* label) {
  std::size_t result = 1;
  for (const std::size_t factor : factors) {
    if (factor == 0 ||
        result > std::numeric_limits<std::size_t>::max() / factor) {
      throw std::invalid_argument(std::string(label) + " geometry is invalid");
    }
    result *= factor;
  }
  return result;
}

}  // namespace

ProfileOutputHeadBackwardResult ProfileOutputHeadBackward(
    const ProfileGeometry& geometry,
    const ProfileCache& cache) {
  const std::size_t states = geometry.transformer.states;
  const std::size_t streams = geometry.transformer.streams;
  const std::size_t model = Product(
      {geometry.transformer.heads, geometry.transformer.head_width},
      "output-head model");
  const std::size_t samples = Product(
      {states, streams}, "output-head samples");
  if (geometry.vocabulary == 0 || geometry.loss_length == 0 ||
      geometry.loss_start > states ||
      geometry.loss_length > states - geometry.loss_start ||
      cache.final_hidden.size() != Product(
          {samples, model}, "output-head hidden") ||
      cache.probabilities.size() != Product(
          {samples, geometry.vocabulary}, "output-head probabilities") ||
      cache.targets.size() != samples) {
    throw std::invalid_argument("output-head cache or loss geometry differs");
  }
  Bf16Buffer residual = CrossEntropyLogitResidual(
      cache.probabilities,
      cache.targets,
      states,
      streams,
      geometry.vocabulary,
      geometry.loss_start,
      geometry.loss_length);
  Bf16Buffer weight = Flat128WeightGradient(
      cache.final_hidden,
      residual,
      samples,
      model,
      geometry.vocabulary);
  Bf16Buffer bias =
      FlatBiasGradient(residual, samples, geometry.vocabulary);
  return {
      .output_weight = std::move(weight),
      .output_bias = std::move(bias),
      .logit_residual = std::move(residual),
  };
}

}  // namespace gamma_enwiki9::nncp
