#ifndef GAMMA_ENWIKI9_NNCP_MIDPOINT_KERNELS_HPP
#define GAMMA_ENWIKI9_NNCP_MIDPOINT_KERNELS_HPP

#include <cstddef>
#include <cstdint>
#include <vector>

namespace gamma_enwiki9::nncp {

using Bf16 = std::uint16_t;
using Bf16Buffer = std::vector<Bf16>;

struct AttentionGeometry {
  std::size_t states;
  std::size_t streams;
  std::size_t heads;
  std::size_t keys;
  std::size_t width;
};

enum class RmsNormSchedule {
  // Final normalization is one factorized root over the complete population.
  kFinalRoot,
  // Layer-local pre-normalizations retain one materialization per graph state.
  kSequentialStates,
};

struct RmsNormBackwardResult {
  Bf16Buffer gain_gradient;
  Bf16Buffer bias_gradient;
  Bf16Buffer input_adjoint;
};

void ValidateArithmeticEnvironment();

float Bf16ToFloat(Bf16 value);
Bf16 FloatToBf16(float value);
float RoundToBf16(float value);

// Gradients emitted by sequential NNCP graph nodes are accumulated at every
// chronological state boundary. The prior materialized BF16 value is decoded,
// the current 32-stream contribution is evaluated, and the sum is rounded once.
Bf16Buffer StatewiseBiasGradient(
    const Bf16Buffer& residuals,
    std::size_t states,
    std::size_t streams,
    std::size_t features);

// One factorized root reduction over [sample, feature], with a final BF16
// materialization. This is the attributed output-head/final-root schedule.
Bf16Buffer FlatBiasGradient(
    const Bf16Buffer& residuals,
    std::size_t samples,
    std::size_t features);

// Inputs are [state, stream, input], residuals are [state, stream, output], and
// the result is the LibNC payload order [input, output]. Outputs must be a
// multiple of eight because adjacent output coordinates are the frozen lanes.
Bf16Buffer StatewiseWeightGradient(
    const Bf16Buffer& inputs,
    const Bf16Buffer& residuals,
    std::size_t states,
    std::size_t streams,
    std::size_t inputs_count,
    std::size_t outputs_count);

// One factorized outer-product reduction over ordered 128-sample panels.
Bf16Buffer Flat128WeightGradient(
    const Bf16Buffer& inputs,
    const Bf16Buffer& residuals,
    std::size_t samples,
    std::size_t inputs_count,
    std::size_t outputs_count);

// Weights arrive in serialized [destination, reduction] order. Incoming
// adjoints are [sample, reduction]. Each destination lane is accumulated over
// ordered 128-coordinate panels and rounded once to BF16 at the output node.
Bf16Buffer Panel128InputAdjoint(
    const Bf16Buffer& weights,
    const Bf16Buffer& incoming,
    std::size_t samples,
    std::size_t reduction,
    std::size_t destination);

struct GegluBackwardResult {
  Bf16Buffer ff2_input_adjoint;
  Bf16Buffer ff1_output_adjoint;
};

GegluBackwardResult GegluBackward(
    const Bf16Buffer& ff1_output,
    const Bf16Buffer& incoming,
    std::size_t samples,
    std::size_t inner);

Bf16Buffer AddBf16(
    const Bf16Buffer& left,
    const Bf16Buffer& right);

// Probabilities are [state, stream, symbol] F32 values from the exact open
// forward. Only the frozen loss window contributes; all other rows are zero.
Bf16Buffer CrossEntropyLogitResidual(
    const std::vector<float>& probabilities,
    const std::vector<std::uint32_t>& targets,
    std::size_t states,
    std::size_t streams,
    std::size_t vocabulary,
    std::size_t loss_start,
    std::size_t loss_length);

// Probability and incoming adjoint share [row, key] BF16 stream-major layout.
// The reduction is strictly scalar key order with contraction disabled.
Bf16Buffer SoftmaxBackward(
    const Bf16Buffer& probability,
    const Bf16Buffer& incoming,
    std::size_t rows,
    std::size_t keys);

Bf16Buffer ScaleBf16(const Bf16Buffer& values, float scale);

// Invert the fixed Transformer-XL relative shift. Both buffers use
// [state, stream, head, position]. Coordinates discarded by the forward shift
// receive zero adjoint.
Bf16Buffer RelativeShiftBackward(
    const Bf16Buffer& shifted,
    std::size_t states,
    std::size_t streams,
    std::size_t heads,
    std::size_t positions);

// Probability uses [state, stream, head, key]; incoming attended adjoints use
// [state, stream, head, width]. The result is [stream, head, key, width].
Bf16Buffer AttentionValueGradient(
    const Bf16Buffer& probability,
    const Bf16Buffer& incoming,
    const AttentionGeometry& geometry);

struct AttentionDotBackwardResult {
  Bf16Buffer key_adjoint;
  Bf16Buffer query_adjoint;
};

// Backward for score = key dot query. Key is [stream, head, key, width], query
// is [state, stream, head, width], and score is [state, stream, head, key].
AttentionDotBackwardResult AttentionDotBackward(
    const Bf16Buffer& key,
    const Bf16Buffer& query,
    const Bf16Buffer& score_adjoint,
    const AttentionGeometry& geometry);

struct RelativeProjectionBackwardResult {
  Bf16Buffer weight_gradient;
  Bf16Buffer bias_gradient;
  Bf16Buffer query_adjoint;
};

// Query is [state, stream, head, width], relative weights are
// [head, position, width], and raw adjoints are
// [state, stream, head, position]. Returned weights preserve the same layout;
// bias is [head, position], and query adjoint preserves query layout.
RelativeProjectionBackwardResult RelativeProjectionBackward(
    const Bf16Buffer& query,
    const Bf16Buffer& relative_weight,
    const Bf16Buffer& raw_adjoint,
    const AttentionGeometry& geometry,
    float bias_scale);

// Merge split-head K/V adjoints to the projection output order
// [position, stream, 2 * heads * width].
Bf16Buffer MergeKeyValueAdjoints(
    const Bf16Buffer& key_adjoint,
    const Bf16Buffer& value_adjoint,
    std::size_t streams,
    std::size_t heads,
    std::size_t positions,
    std::size_t width);

// Extract current positions from [position, stream, features], preserving
// [state, stream, features] order.
Bf16Buffer SlicePositionRange(
    const Bf16Buffer& values,
    std::size_t positions,
    std::size_t streams,
    std::size_t features,
    std::size_t start,
    std::size_t length);

// All buffers use [state, stream, feature], except gain which is [feature].
// The two schedules encode the independently attributed arithmetic distinction
// between the final concat root and layer-local sequential graph nodes.
RmsNormBackwardResult RmsNormBackward(
    const Bf16Buffer& input,
    const Bf16Buffer& incoming,
    const Bf16Buffer& gain,
    std::size_t states,
    std::size_t streams,
    std::size_t width,
    RmsNormSchedule schedule,
    float epsilon = 1.0e-5F);

// Value is [stream, head, key, width], incoming is
// [state, stream, head, width], and the native treatment layout is
// [state, head, stream, key].
Bf16Buffer AttentionProbabilityAdjoint(
    const Bf16Buffer& value,
    const Bf16Buffer& incoming,
    const AttentionGeometry& geometry);

// Frozen zero-credit comparator bridge. Only head and stream axes move:
// [state, head, stream, key] -> [state, stream, head, key].
Bf16Buffer AttentionSourceToStreamMajor(
    const Bf16Buffer& source_order,
    const AttentionGeometry& geometry);

}  // namespace gamma_enwiki9::nncp

#endif
