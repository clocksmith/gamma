#include "profile_state.hpp"

#include <algorithm>
#include <initializer_list>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

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

std::vector<Bf16Buffer> AdvanceProfileMemory(
    const ProfileGeometry& geometry,
    const std::vector<Bf16Buffer>& prior_memory,
    const ProfileCache& completed_segment) {
  const std::size_t states = geometry.transformer.states;
  const std::size_t streams = geometry.transformer.streams;
  const std::size_t memory = geometry.transformer.memory;
  const std::size_t model = Product(
      {geometry.transformer.heads, geometry.transformer.head_width},
      "memory model");
  const std::size_t position_elements =
      Product({streams, model}, "memory position");
  const std::size_t memory_elements =
      Product({memory, position_elements}, "memory input");
  const std::size_t state_elements =
      Product({states, position_elements}, "memory current states");
  if (geometry.layers == 0 || prior_memory.size() != geometry.layers ||
      completed_segment.layers.size() != geometry.layers) {
    throw std::invalid_argument("memory layer population differs");
  }
  std::vector<Bf16Buffer> next;
  next.reserve(geometry.layers);
  for (std::size_t layer = 0; layer < geometry.layers; ++layer) {
    const Bf16Buffer& prior = prior_memory[layer];
    const Bf16Buffer& current =
        completed_segment.layers[layer].attention_input;
    if (prior.size() != memory_elements || current.size() != state_elements) {
      throw std::invalid_argument("memory tensor geometry differs at layer " +
                                  std::to_string(layer));
    }
    Bf16Buffer output;
    output.reserve(memory_elements);
    if (memory > states) {
      const std::size_t discarded = states * position_elements;
      output.insert(output.end(), prior.begin() + discarded, prior.end());
      output.insert(output.end(), current.begin(), current.end());
    } else {
      const std::size_t first_state = states - memory;
      output.insert(
          output.end(),
          current.begin() + first_state * position_elements,
          current.end());
    }
    if (output.size() != memory_elements) {
      throw std::logic_error("memory transition produced the wrong size");
    }
    next.push_back(std::move(output));
  }
  return next;
}

}  // namespace gamma_enwiki9::nncp
