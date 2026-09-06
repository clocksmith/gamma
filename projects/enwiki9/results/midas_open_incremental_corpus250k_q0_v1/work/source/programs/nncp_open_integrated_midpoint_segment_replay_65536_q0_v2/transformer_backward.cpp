#include "transformer_backward.hpp"

#include <algorithm>
#include <cmath>
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

void Require(const Bf16Buffer& values, std::size_t expected, const char* label) {
  if (values.size() != expected) {
    throw std::invalid_argument(
        std::string(label) + " size differs: " + std::to_string(values.size()) +
        " != " + std::to_string(expected));
  }
}

Bf16Buffer JoinPositionMajor(
    const Bf16Buffer& first,
    const Bf16Buffer& second) {
  Bf16Buffer result;
  result.reserve(first.size() + second.size());
  result.insert(result.end(), first.begin(), first.end());
  result.insert(result.end(), second.begin(), second.end());
  return result;
}

Bf16Buffer MergeSplitHeadsStateMajor(
    const Bf16Buffer& split,
    std::size_t states,
    std::size_t streams,
    std::size_t heads,
    std::size_t width) {
  const std::size_t model = Product({heads, width}, "split-head model");
  Require(split, Product({states, streams, model}, "split-head source"),
          "split-head source");
  // The split representation keeps head and feature adjacent, so this is an
  // explicit identity copy that records the semantic boundary.
  return split;
}

struct LinearBackwardResult {
  Bf16Buffer weight_gradient;
  Bf16Buffer bias_gradient;
  Bf16Buffer input_adjoint;
};

LinearBackwardResult LinearBackward(
    const Bf16Buffer& weights,
    const Bf16Buffer& inputs,
    const Bf16Buffer& incoming,
    std::size_t states,
    std::size_t streams,
    std::size_t input_features,
    std::size_t output_features,
    bool sequential_parameters) {
  Require(weights, Product({input_features, output_features}, "linear weights"),
          "linear weights");
  Require(inputs, Product({states, streams, input_features}, "linear inputs"),
          "linear inputs");
  Require(incoming, Product({states, streams, output_features}, "linear incoming"),
          "linear incoming");
  Bf16Buffer weight_gradient = sequential_parameters
      ? StatewiseWeightGradient(
            inputs,
            incoming,
            states,
            streams,
            input_features,
            output_features)
      : Flat128WeightGradient(
            inputs,
            incoming,
            states * streams,
            input_features,
            output_features);
  Bf16Buffer bias_gradient = sequential_parameters
      ? StatewiseBiasGradient(incoming, states, streams, output_features)
      : FlatBiasGradient(incoming, states * streams, output_features);
  Bf16Buffer input_adjoint = Panel128InputAdjoint(
      weights,
      incoming,
      states * streams,
      output_features,
      input_features);
  return {
      std::move(weight_gradient),
      std::move(bias_gradient),
      std::move(input_adjoint),
  };
}

}  // namespace

TransformerLayerBackwardResult TransformerLayerBackward(
    const TransformerGeometry& geometry,
    const TransformerLayerWeights& weights,
    const TransformerLayerCache& cache,
    const Bf16Buffer& incoming_hidden_adjoint) {
  const std::size_t model =
      Product({geometry.heads, geometry.head_width}, "transformer model");
  const std::size_t positions =
      Sum(geometry.memory, geometry.states, "attention positions");
  const std::size_t two_inner = Product({2, geometry.inner}, "double FF inner");
  const std::size_t two_model = Product({2, model}, "double model");
  const std::size_t samples =
      Product({geometry.states, geometry.streams}, "transformer samples");
  const std::size_t state_model = Product({samples, model}, "state model");
  const std::size_t all_position_model =
      Product({positions, geometry.streams, model}, "position model");
  const std::size_t split_state = Product(
      {geometry.states, geometry.streams, geometry.heads, geometry.head_width},
      "split state");
  const std::size_t split_position = Product(
      {geometry.streams, geometry.heads, positions, geometry.head_width},
      "split position");
  const std::size_t attention_elements = Product(
      {geometry.states, geometry.streams, geometry.heads, positions},
      "attention elements");

  Require(incoming_hidden_adjoint, state_model, "incoming hidden adjoint");
  Require(cache.hidden_input, state_model, "hidden input");
  Require(cache.attention_input, state_model, "attention input");
  Require(cache.attention_residual, state_model, "attention residual");
  Require(cache.feedforward_input, state_model, "feedforward input");
  Require(cache.merged_attention, state_model, "merged attention");
  Require(
      cache.ff1_output,
      Product({samples, two_inner}, "FF1 output"),
      "FF1 output");
  Require(cache.geglu, Product({samples, geometry.inner}, "GEGLU"), "GEGLU");
  Require(
      cache.memory_attention_input,
      Product({geometry.memory, geometry.streams, model}, "memory attention input"),
      "memory attention input");
  Require(cache.query, split_state, "query");
  Require(cache.key, split_position, "key");
  Require(cache.value, split_position, "value");
  Require(cache.attention_probability, attention_elements, "attention probability");
  Require(weights.ln_g1, model, "ln_g1");
  Require(weights.w_q, Product({model, model}, "w_q"), "w_q");
  Require(weights.w_kv, Product({model, two_model}, "w_kv"), "w_kv");
  Require(weights.relative_weight,
          Product({geometry.heads, positions, geometry.head_width}, "w_r"),
          "w_r");
  Require(weights.w_o, Product({model, model}, "w_o"), "w_o");
  Require(weights.ln_g2, model, "ln_g2");
  Require(weights.ff1, Product({model, two_inner}, "ff1"), "ff1");
  Require(weights.ff2, Product({geometry.inner, model}, "ff2"), "ff2");

  // Feed-forward residual: the incoming adjoint reaches both the direct branch
  // and the FF2 projection.
  const LinearBackwardResult ff2 = LinearBackward(
      weights.ff2,
      cache.geglu,
      incoming_hidden_adjoint,
      geometry.states,
      geometry.streams,
      geometry.inner,
      model,
      false);
  const GegluBackwardResult geglu = GegluBackward(
      cache.ff1_output,
      ff2.input_adjoint,
      samples,
      geometry.inner);
  const LinearBackwardResult ff1 = LinearBackward(
      weights.ff1,
      cache.feedforward_input,
      geglu.ff1_output_adjoint,
      geometry.states,
      geometry.streams,
      model,
      two_inner,
      true);
  const RmsNormBackwardResult norm2 = RmsNormBackward(
      cache.attention_residual,
      ff1.input_adjoint,
      weights.ln_g2,
      geometry.states,
      geometry.streams,
      model,
      RmsNormSchedule::kSequentialStates);
  const Bf16Buffer attention_residual_adjoint =
      AddBf16(norm2.input_adjoint, incoming_hidden_adjoint);

  // Attention residual: the total adjoint reaches both w_o and the layer's
  // direct residual branch.
  const LinearBackwardResult w_o = LinearBackward(
      weights.w_o,
      cache.merged_attention,
      attention_residual_adjoint,
      geometry.states,
      geometry.streams,
      model,
      model,
      true);
  const Bf16Buffer attended_adjoint = MergeSplitHeadsStateMajor(
      w_o.input_adjoint,
      geometry.states,
      geometry.streams,
      geometry.heads,
      geometry.head_width);
  const AttentionGeometry attention_geometry{
      geometry.states,
      geometry.streams,
      geometry.heads,
      positions,
      geometry.head_width,
  };
  const Bf16Buffer probability_adjoint_source = AttentionProbabilityAdjoint(
      cache.value, attended_adjoint, attention_geometry);
  const Bf16Buffer probability_adjoint_stream = AttentionSourceToStreamMajor(
      probability_adjoint_source, attention_geometry);
  const Bf16Buffer softmax_adjoint = SoftmaxBackward(
      cache.attention_probability,
      probability_adjoint_stream,
      geometry.states * geometry.streams * geometry.heads,
      positions);
  const float inverse_key_scale = RoundToBf16(
      1.0F / std::sqrt(static_cast<float>(geometry.head_width)));
  const Bf16Buffer score_adjoint = ScaleBf16(softmax_adjoint, inverse_key_scale);

  const Bf16Buffer value_gradient = AttentionValueGradient(
      cache.attention_probability, attended_adjoint, attention_geometry);
  const AttentionDotBackwardResult content = AttentionDotBackward(
      cache.key, cache.query, score_adjoint, attention_geometry);
  const Bf16Buffer raw_relative_adjoint = RelativeShiftBackward(
      score_adjoint,
      geometry.states,
      geometry.streams,
      geometry.heads,
      positions);
  const float relative_bias_scale = RoundToBf16(std::sqrt(
      static_cast<float>(Product(
          {geometry.head_width, model}, "relative bias scale"))));
  const RelativeProjectionBackwardResult relative = RelativeProjectionBackward(
      cache.query,
      weights.relative_weight,
      raw_relative_adjoint,
      attention_geometry,
      relative_bias_scale);
  const Bf16Buffer query_adjoint_split =
      AddBf16(content.query_adjoint, relative.query_adjoint);
  const Bf16Buffer query_adjoint = MergeSplitHeadsStateMajor(
      query_adjoint_split,
      geometry.states,
      geometry.streams,
      geometry.heads,
      geometry.head_width);

  const LinearBackwardResult w_q = LinearBackward(
      weights.w_q,
      cache.attention_input,
      query_adjoint,
      geometry.states,
      geometry.streams,
      model,
      model,
      true);
  const Bf16Buffer merged_kv_adjoint = MergeKeyValueAdjoints(
      content.key_adjoint,
      value_gradient,
      geometry.streams,
      geometry.heads,
      positions,
      geometry.head_width);
  const Bf16Buffer all_attention_input = JoinPositionMajor(
      cache.memory_attention_input, cache.attention_input);
  Require(all_attention_input, all_position_model, "all attention input");
  const LinearBackwardResult w_kv = LinearBackward(
      weights.w_kv,
      all_attention_input,
      merged_kv_adjoint,
      positions,
      geometry.streams,
      model,
      two_model,
      false);
  const Bf16Buffer current_kv_input_adjoint = SlicePositionRange(
      w_kv.input_adjoint,
      positions,
      geometry.streams,
      model,
      geometry.memory,
      geometry.states);
  const Bf16Buffer attention_input_adjoint =
      AddBf16(w_q.input_adjoint, current_kv_input_adjoint);
  const RmsNormBackwardResult norm1 = RmsNormBackward(
      cache.hidden_input,
      attention_input_adjoint,
      weights.ln_g1,
      geometry.states,
      geometry.streams,
      model,
      RmsNormSchedule::kSequentialStates);
  Bf16Buffer hidden_input_adjoint =
      AddBf16(norm1.input_adjoint, attention_residual_adjoint);

  TransformerLayerGradients gradients{
      .ff2 = ff2.weight_gradient,
      .ff1 = ff1.weight_gradient,
      .ln_g2 = norm2.gain_gradient,
      .ln_b2 = norm2.bias_gradient,
      .ff_bias1 = ff1.bias_gradient,
      .ff_bias2 = ff2.bias_gradient,
      .w_o = w_o.weight_gradient,
      .w_r = relative.weight_gradient,
      .w_kv = w_kv.weight_gradient,
      .w_q = w_q.weight_gradient,
      .ln_g1 = norm1.gain_gradient,
      .ln_b1 = norm1.bias_gradient,
      .relative_bias_contribution = relative.bias_gradient,
  };
  return {
      std::move(gradients),
      std::move(hidden_input_adjoint),
      probability_adjoint_source,
      probability_adjoint_stream,
      score_adjoint,
  };
}

}  // namespace gamma_enwiki9::nncp
