#include "profile_fixture.hpp"

#include "tensor_container.hpp"

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
    if (factor == 0 || result > std::numeric_limits<std::size_t>::max() / factor) {
      throw std::invalid_argument(std::string(label) + " geometry is invalid");
    }
    result *= factor;
  }
  return result;
}

std::size_t Sum(std::size_t left, std::size_t right, const char* label) {
  if (left == 0 || right == 0 ||
      left > std::numeric_limits<std::size_t>::max() - right) {
    throw std::invalid_argument(std::string(label) + " geometry is invalid");
  }
  return left + right;
}

std::string LayerName(const char* prefix, std::size_t layer) {
  return std::string(prefix) + "_" + std::to_string(layer);
}

}  // namespace

static ProfileFixtureInputs LoadProfileFixtureInternal(
    const ProfileGeometry& geometry,
    const std::filesystem::path& parameter_container,
    const std::filesystem::path& state_container,
    FutureInputPolicy future_policy,
    bool require_train_h_comparators) {
  const std::size_t states = geometry.transformer.states;
  const std::size_t streams = geometry.transformer.streams;
  const std::size_t heads = geometry.transformer.heads;
  const std::size_t head_width = geometry.transformer.head_width;
  const std::size_t memory = geometry.transformer.memory;
  const std::size_t inner = geometry.transformer.inner;
  const std::size_t model = Product({heads, head_width}, "fixture model");
  const std::size_t positions = Sum(memory, states, "fixture attention positions");
  const std::size_t two_model = Product({2, model}, "fixture double model");
  const std::size_t two_inner = Product({2, inner}, "fixture double inner");
  if (geometry.layers == 0) {
    throw std::invalid_argument("fixture layer population is zero");
  }
  const TensorContainer parameters(parameter_container);
  const TensorContainer state(state_container);
  const std::size_t expected_parameters = Sum(
      Product({geometry.layers, 12}, "fixture parameter population"),
      6,
      "fixture parameter population");
  const std::size_t expected_state = Sum(
      Product(
          {geometry.layers, require_train_h_comparators ? 2U : 1U},
          "fixture state population"),
      2,
      "fixture state population");
  if (parameters.tensors().size() != expected_parameters) {
    throw std::runtime_error("fixture parameter population differs");
  }
  if (state.tensors().size() != expected_state) {
    throw std::runtime_error("fixture state population differs");
  }

  ProfileWeights weights;
  weights.shared_relative_bias = parameters.CopyBf16("b_r_0", {positions, heads});
  weights.layers.reserve(geometry.layers);
  for (std::size_t layer = 0; layer < geometry.layers; ++layer) {
    weights.layers.push_back({
        .ln_g1 = parameters.CopyBf16(
            LayerName("ln_g", 2 * layer), {model}),
        .ln_b1 = parameters.CopyBf16(
            LayerName("ln_b", 2 * layer), {model}),
        .w_q = parameters.CopyBf16(
            LayerName("w_q", layer), {model, model}),
        .w_kv = parameters.CopyBf16(
            LayerName("w_kv", layer), {two_model, model}),
        .relative_weight = parameters.CopyBf16(
            LayerName("w_r", layer), {head_width, positions, heads}),
        .w_o = parameters.CopyBf16(
            LayerName("w_o", layer), {model, model}),
        .ln_g2 = parameters.CopyBf16(
            LayerName("ln_g", 2 * layer + 1), {model}),
        .ln_b2 = parameters.CopyBf16(
            LayerName("ln_b", 2 * layer + 1), {model}),
        .ff1 = parameters.CopyBf16(
            LayerName("ff1", layer), {two_inner, model}),
        .ff_bias1 = parameters.CopyBf16(
            LayerName("ff_bias1", layer), {two_inner}),
        .ff2 = parameters.CopyBf16(
            LayerName("ff2", layer), {model, inner}),
        .ff_bias2 = parameters.CopyBf16(
            LayerName("ff_bias2", layer), {model}),
    });
  }
  weights.final_ln_gain = parameters.CopyBf16(
      LayerName("ln_g", 2 * geometry.layers), {model});
  weights.final_ln_bias = parameters.CopyBf16(
      LayerName("ln_b", 2 * geometry.layers), {model});
  weights.embedding = parameters.CopyF32(
      "embed", {model, geometry.vocabulary});
  weights.output_weight = parameters.CopyBf16(
      "embed_out", {geometry.vocabulary, model});
  weights.output_bias = parameters.CopyBf16("out_bias", {geometry.vocabulary});

  std::vector<std::uint32_t> input_symbols = state.CopyU32(
      "input_all_streams", {streams, states});
  std::vector<std::uint32_t> targets = state.CopyU32(
      "target_all_streams", {streams, states});
  for (std::size_t index = 0; index < input_symbols.size(); ++index) {
    if (input_symbols[index] >= geometry.vocabulary ||
        targets[index] >= geometry.vocabulary) {
      throw std::runtime_error("fixture symbol lies outside the vocabulary");
    }
  }
  if (future_policy == FutureInputPolicy::kZeroSecondHalf) {
    if (states != 64 || geometry.loss_start != 0 || geometry.loss_length != 32) {
      throw std::invalid_argument(
          "zero-second-half policy requires the frozen 0..31 of 64 loss");
    }
    for (std::size_t state_index = 32; state_index < states; ++state_index) {
      for (std::size_t stream = 0; stream < streams; ++stream) {
        input_symbols[state_index * streams + stream] = 0;
      }
    }
  }

  std::vector<Bf16Buffer> memory_inputs;
  memory_inputs.reserve(geometry.layers);
  for (std::size_t layer = 0; layer < geometry.layers; ++layer) {
    memory_inputs.push_back(state.CopyBf16(
        LayerName("mem_h", layer), {model, streams, memory}));
    if (require_train_h_comparators) {
      // train_h is a teacher activation/comparator, never copied into the
      // returned treatment inputs.
      const TensorMetadata& train = state.metadata(LayerName("train_h", layer));
      if (train.type != 1 ||
          train.dimensions !=
              std::vector<std::size_t>({model, streams, states})) {
        throw std::runtime_error("fixture train_h comparator geometry differs");
      }
    }
  }
  return {
      .weights = std::move(weights),
      .input_symbols = std::move(input_symbols),
      .targets = std::move(targets),
      .memory_inputs = std::move(memory_inputs),
  };
}

ProfileFixtureInputs LoadProfileFixture(
    const ProfileGeometry& geometry,
    const std::filesystem::path& parameter_container,
    const std::filesystem::path& state_container,
    FutureInputPolicy future_policy) {
  return LoadProfileFixtureInternal(
      geometry,
      parameter_container,
      state_container,
      future_policy,
      true);
}

ProfileFixtureInputs LoadProfileInitialFixture(
    const ProfileGeometry& geometry,
    const std::filesystem::path& parameter_container,
    const std::filesystem::path& initial_state_container) {
  return LoadProfileFixtureInternal(
      geometry,
      parameter_container,
      initial_state_container,
      FutureInputPolicy::kPreserve,
      false);
}

}  // namespace gamma_enwiki9::nncp
