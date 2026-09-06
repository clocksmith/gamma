#ifndef GAMMA_ENWIKI9_NNCP_PROFILE_BACKWARD_HPP
#define GAMMA_ENWIKI9_NNCP_PROFILE_BACKWARD_HPP

#include "transformer_backward.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace gamma_enwiki9::nncp {

using F32Buffer = std::vector<float>;

struct ProfileGeometry {
  TransformerGeometry transformer;
  std::size_t layers;
  std::size_t vocabulary;
  std::size_t loss_start;
  std::size_t loss_length;
};

struct ProfileWeights {
  // The LibNC payload order for both matrices is [input, output].
  Bf16Buffer output_weight;
  Bf16Buffer final_ln_gain;
  std::vector<TransformerLayerWeights> layers;
  F32Buffer embedding;
  Bf16Buffer shared_relative_bias;
  Bf16Buffer final_ln_bias;
  Bf16Buffer output_bias;
};

struct ProfileCache {
  // All hidden buffers are [state, stream, model].
  Bf16Buffer pre_final_hidden;
  Bf16Buffer final_hidden;
  std::vector<TransformerLayerCache> layers;

  // Probabilities are F32 [state, stream, vocabulary]. Symbols are
  // [state, stream] in the same chronological order.
  F32Buffer probabilities;
  std::vector<std::uint32_t> targets;
  std::vector<std::uint32_t> input_symbols;
};

struct ProfileGradients {
  Bf16Buffer output_weight;
  std::vector<TransformerLayerGradients> layers;
  Bf16Buffer shared_relative_bias;
  F32Buffer embedding;
  Bf16Buffer final_ln_gain;
  Bf16Buffer final_ln_bias;
  Bf16Buffer output_bias;
};

struct ProfileBackwardCheckpoints {
  Bf16Buffer logit_residual;
  Bf16Buffer final_hidden_adjoint;
  Bf16Buffer embedding_input_adjoint;
  Bf16Buffer top_attention_probability_adjoint_source_order;
  Bf16Buffer top_attention_probability_adjoint_stream_major;
};

struct ProfileBackwardResult {
  ProfileGradients gradients;
  ProfileBackwardCheckpoints checkpoints;
};

enum class GradientElementType {
  kBf16,
  kF32,
};

struct GradientDescriptor {
  std::string name;
  GradientElementType element_type;
  std::vector<std::size_t> dimensions;
};

// Returns the exact 246-entry source order for the production 20-layer
// profile. For a generic layer count the same reverse-layer topology is used.
std::vector<GradientDescriptor> CanonicalGradientDescriptors(
    const ProfileGeometry& geometry);

ProfileBackwardResult ProfileBackward(
    const ProfileGeometry& geometry,
    const ProfileWeights& weights,
    const ProfileCache& cache);

}  // namespace gamma_enwiki9::nncp

#endif
