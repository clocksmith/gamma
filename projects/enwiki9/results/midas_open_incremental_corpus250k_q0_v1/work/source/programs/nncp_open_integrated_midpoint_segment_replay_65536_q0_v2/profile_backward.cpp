#include "profile_backward.hpp"

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
  if (left > std::numeric_limits<std::size_t>::max() - right) {
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

void Require(const F32Buffer& values, std::size_t expected, const char* label) {
  if (values.size() != expected) {
    throw std::invalid_argument(
        std::string(label) + " size differs: " + std::to_string(values.size()) +
        " != " + std::to_string(expected));
  }
}

F32Buffer EmbeddingGradient(
    const Bf16Buffer& incoming,
    const std::vector<std::uint32_t>& input_symbols,
    std::size_t states,
    std::size_t streams,
    std::size_t model,
    std::size_t vocabulary) {
  const std::size_t samples = Product({states, streams}, "embedding samples");
  Require(incoming, Product({samples, model}, "embedding incoming"),
          "embedding incoming");
  if (input_symbols.size() != samples) {
    throw std::invalid_argument("embedding symbol population differs");
  }
  F32Buffer gradient(Product({vocabulary, model}, "embedding gradient"), 0.0F);
  const float multiplier = RoundToBf16(std::sqrt(static_cast<float>(model)));
  for (std::size_t state = 0; state < states; ++state) {
    for (std::size_t stream = 0; stream < streams; ++stream) {
      const std::size_t sample = state * streams + stream;
      const std::uint32_t symbol = input_symbols[sample];
      if (symbol >= vocabulary) {
        throw std::invalid_argument("embedding input symbol is outside vocabulary");
      }
      for (std::size_t feature = 0; feature < model; ++feature) {
        const float contribution = RoundToBf16(
            Bf16ToFloat(incoming[sample * model + feature]) * multiplier);
        float& destination = gradient[static_cast<std::size_t>(symbol) * model + feature];
        destination += contribution;
        if (!std::isfinite(destination)) {
          throw std::runtime_error("non-finite embedding gradient");
        }
      }
    }
  }
  return gradient;
}

void AddDescriptor(
    std::vector<GradientDescriptor>& descriptors,
    std::string name,
    GradientElementType element_type,
    std::vector<std::size_t> dimensions) {
  descriptors.push_back(
      {std::move(name), element_type, std::move(dimensions)});
}

}  // namespace

std::vector<GradientDescriptor> CanonicalGradientDescriptors(
    const ProfileGeometry& geometry) {
  const std::size_t model = Product(
      {geometry.transformer.heads, geometry.transformer.head_width},
      "profile model");
  const std::size_t positions = geometry.transformer.memory + geometry.transformer.states;
  if (positions < geometry.transformer.memory || positions < geometry.transformer.states) {
    throw std::invalid_argument("profile attention positions overflow");
  }
  const std::size_t two_inner =
      Product({2, geometry.transformer.inner}, "profile double inner");
  const std::size_t two_model = Product({2, model}, "profile double model");
  std::vector<GradientDescriptor> descriptors;
  descriptors.reserve(Sum(
      Product({geometry.layers, 12}, "profile layer descriptors"),
      6,
      "profile descriptors"));
  AddDescriptor(
      descriptors,
      "embed_out",
      GradientElementType::kBf16,
      {geometry.vocabulary, model});
  for (std::size_t reverse = geometry.layers; reverse != 0; --reverse) {
    const std::size_t layer = reverse - 1;
    const std::string suffix = "_" + std::to_string(layer);
    AddDescriptor(descriptors, "ff2" + suffix, GradientElementType::kBf16,
                  {model, geometry.transformer.inner});
    AddDescriptor(descriptors, "ff1" + suffix, GradientElementType::kBf16,
                  {two_inner, model});
    AddDescriptor(descriptors, "ln_g_" + std::to_string(2 * layer + 1),
                  GradientElementType::kBf16, {model});
    AddDescriptor(descriptors, "ln_b_" + std::to_string(2 * layer + 1),
                  GradientElementType::kBf16, {model});
    AddDescriptor(descriptors, "ff_bias1" + suffix, GradientElementType::kBf16,
                  {two_inner});
    AddDescriptor(descriptors, "ff_bias2" + suffix, GradientElementType::kBf16,
                  {model});
    AddDescriptor(descriptors, "w_o" + suffix, GradientElementType::kBf16,
                  {model, model});
    AddDescriptor(descriptors, "w_r" + suffix, GradientElementType::kBf16,
                  {geometry.transformer.head_width, positions,
                   geometry.transformer.heads});
    if (layer == 0) {
      AddDescriptor(descriptors, "b_r_0", GradientElementType::kBf16,
                    {positions, geometry.transformer.heads});
    }
    AddDescriptor(descriptors, "w_kv" + suffix, GradientElementType::kBf16,
                  {two_model, model});
    AddDescriptor(descriptors, "w_q" + suffix, GradientElementType::kBf16,
                  {model, model});
    AddDescriptor(descriptors, "ln_g_" + std::to_string(2 * layer),
                  GradientElementType::kBf16, {model});
    AddDescriptor(descriptors, "ln_b_" + std::to_string(2 * layer),
                  GradientElementType::kBf16, {model});
  }
  AddDescriptor(descriptors, "embed", GradientElementType::kF32,
                {model, geometry.vocabulary});
  AddDescriptor(descriptors, "ln_g_" + std::to_string(2 * geometry.layers),
                GradientElementType::kBf16, {model});
  AddDescriptor(descriptors, "ln_b_" + std::to_string(2 * geometry.layers),
                GradientElementType::kBf16, {model});
  AddDescriptor(descriptors, "out_bias", GradientElementType::kBf16,
                {geometry.vocabulary});
  return descriptors;
}

ProfileBackwardResult ProfileBackward(
    const ProfileGeometry& geometry,
    const ProfileWeights& weights,
    const ProfileCache& cache) {
  const std::size_t model = Product(
      {geometry.transformer.heads, geometry.transformer.head_width},
      "profile model");
  const std::size_t samples = Product(
      {geometry.transformer.states, geometry.transformer.streams},
      "profile samples");
  const std::size_t hidden_elements =
      Product({samples, model}, "profile hidden elements");
  if (geometry.layers == 0 || weights.layers.size() != geometry.layers ||
      cache.layers.size() != geometry.layers) {
    throw std::invalid_argument("profile layer population differs");
  }
  Require(weights.output_weight,
          Product({model, geometry.vocabulary}, "output weight"),
          "output weight");
  Require(weights.final_ln_gain, model, "final layer-norm gain");
  Require(cache.pre_final_hidden, hidden_elements, "pre-final hidden");
  Require(cache.final_hidden, hidden_elements, "final hidden");
  Require(cache.probabilities,
          Product({samples, geometry.vocabulary}, "output probabilities"),
          "output probabilities");
  if (cache.targets.size() != samples || cache.input_symbols.size() != samples) {
    throw std::invalid_argument("profile symbol population differs");
  }

  Bf16Buffer logit_residual = CrossEntropyLogitResidual(
      cache.probabilities,
      cache.targets,
      geometry.transformer.states,
      geometry.transformer.streams,
      geometry.vocabulary,
      geometry.loss_start,
      geometry.loss_length);
  Bf16Buffer output_weight_gradient = Flat128WeightGradient(
      cache.final_hidden,
      logit_residual,
      samples,
      model,
      geometry.vocabulary);
  Bf16Buffer output_bias_gradient =
      FlatBiasGradient(logit_residual, samples, geometry.vocabulary);
  Bf16Buffer final_hidden_adjoint = Panel128InputAdjoint(
      weights.output_weight,
      logit_residual,
      samples,
      geometry.vocabulary,
      model);
  const RmsNormBackwardResult final_norm = RmsNormBackward(
      cache.pre_final_hidden,
      final_hidden_adjoint,
      weights.final_ln_gain,
      geometry.transformer.states,
      geometry.transformer.streams,
      model,
      RmsNormSchedule::kFinalRoot);

  Bf16Buffer hidden_adjoint = final_norm.input_adjoint;
  std::vector<TransformerLayerGradients> layer_gradients(geometry.layers);
  Bf16Buffer shared_relative_bias;
  Bf16Buffer top_probability_source;
  Bf16Buffer top_probability_stream;
  for (std::size_t reverse = geometry.layers; reverse != 0; --reverse) {
    const std::size_t layer = reverse - 1;
    TransformerLayerBackwardResult current = TransformerLayerBackward(
        geometry.transformer,
        weights.layers[layer],
        cache.layers[layer],
        hidden_adjoint);
    if (shared_relative_bias.empty()) {
      shared_relative_bias = current.gradients.relative_bias_contribution;
    } else {
      shared_relative_bias = AddBf16(
          shared_relative_bias, current.gradients.relative_bias_contribution);
    }
    if (layer == geometry.layers - 1) {
      top_probability_source =
          std::move(current.attention_probability_adjoint_source_order);
      top_probability_stream =
          std::move(current.attention_probability_adjoint_stream_major);
    }
    hidden_adjoint = std::move(current.hidden_input_adjoint);
    layer_gradients[layer] = std::move(current.gradients);
  }
  F32Buffer embedding_gradient = EmbeddingGradient(
      hidden_adjoint,
      cache.input_symbols,
      geometry.transformer.states,
      geometry.transformer.streams,
      model,
      geometry.vocabulary);

  ProfileGradients gradients{
      .output_weight = std::move(output_weight_gradient),
      .layers = std::move(layer_gradients),
      .shared_relative_bias = std::move(shared_relative_bias),
      .embedding = std::move(embedding_gradient),
      .final_ln_gain = final_norm.gain_gradient,
      .final_ln_bias = final_norm.bias_gradient,
      .output_bias = std::move(output_bias_gradient),
  };
  ProfileBackwardCheckpoints checkpoints{
      .logit_residual = std::move(logit_residual),
      .final_hidden_adjoint = std::move(final_hidden_adjoint),
      .embedding_input_adjoint = std::move(hidden_adjoint),
      .top_attention_probability_adjoint_source_order =
          std::move(top_probability_source),
      .top_attention_probability_adjoint_stream_major =
          std::move(top_probability_stream),
  };
  return {std::move(gradients), std::move(checkpoints)};
}

}  // namespace gamma_enwiki9::nncp
