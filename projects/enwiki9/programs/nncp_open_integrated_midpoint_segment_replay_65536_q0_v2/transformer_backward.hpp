#ifndef GAMMA_ENWIKI9_NNCP_TRANSFORMER_BACKWARD_HPP
#define GAMMA_ENWIKI9_NNCP_TRANSFORMER_BACKWARD_HPP

#include "midpoint_kernels.hpp"

#include <cstddef>

namespace gamma_enwiki9::nncp {

struct TransformerGeometry {
  std::size_t states;
  std::size_t streams;
  std::size_t heads;
  std::size_t head_width;
  std::size_t memory;
  std::size_t inner;
};

struct TransformerLayerWeights {
  Bf16Buffer ln_g1;
  Bf16Buffer w_q;
  Bf16Buffer w_kv;
  Bf16Buffer relative_weight;
  Bf16Buffer w_o;
  Bf16Buffer ln_g2;
  Bf16Buffer ff1;
  Bf16Buffer ff2;
};

struct TransformerLayerCache {
  // State-major [state, stream, model].
  Bf16Buffer hidden_input;
  Bf16Buffer attention_input;
  Bf16Buffer attention_residual;
  Bf16Buffer feedforward_input;
  Bf16Buffer merged_attention;
  Bf16Buffer ff1_output;
  Bf16Buffer geglu;

  // Memory is [position, stream, model]. Query is state-major split-head.
  Bf16Buffer memory_attention_input;
  Bf16Buffer query;

  // Key/value are [stream, head, position, head_width]. Probability is
  // [state, stream, head, position].
  Bf16Buffer key;
  Bf16Buffer value;
  Bf16Buffer attention_probability;
};

struct TransformerLayerGradients {
  Bf16Buffer ff2;
  Bf16Buffer ff1;
  Bf16Buffer ln_g2;
  Bf16Buffer ln_b2;
  Bf16Buffer ff_bias1;
  Bf16Buffer ff_bias2;
  Bf16Buffer w_o;
  Bf16Buffer w_r;
  Bf16Buffer w_kv;
  Bf16Buffer w_q;
  Bf16Buffer ln_g1;
  Bf16Buffer ln_b1;
  Bf16Buffer relative_bias_contribution;
};

struct TransformerLayerBackwardResult {
  TransformerLayerGradients gradients;
  Bf16Buffer hidden_input_adjoint;
  Bf16Buffer attention_probability_adjoint_source_order;
  Bf16Buffer attention_probability_adjoint_stream_major;
  Bf16Buffer attention_score_adjoint;
};

TransformerLayerBackwardResult TransformerLayerBackward(
    const TransformerGeometry& geometry,
    const TransformerLayerWeights& weights,
    const TransformerLayerCache& cache,
    const Bf16Buffer& incoming_hidden_adjoint);

}  // namespace gamma_enwiki9::nncp

#endif
