// Build this translation unit INSTEAD OF profile_forward.cpp. Including the
// immutable source preserves its ProfileForward implementation and exact local
// arithmetic helpers; linking both translation units is a duplicate definition.
#include "../programs/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/profile_forward.cpp"
#include "midas_profile_incremental_forward.hpp"

#include <bit>

namespace gamma_enwiki9::nncp {
namespace {
constexpr std::size_t fixture_states = 64, fixture_width = 64;
constexpr std::size_t fixture_memory = 8, fixture_positions = 72, fixture_inner = 8;

Bf16Buffer FixtureEmbedding(const ProfileWeights& weights, std::uint8_t symbol) {
  Require(weights.embedding, 256 * fixture_width, "incremental embedding");
  Bf16Buffer hidden(fixture_width);
  const float scale = RoundToBf16(std::sqrt(static_cast<float>(fixture_width)));
  for (std::size_t feature = 0; feature < fixture_width; ++feature) {
    const auto source = weights.embedding[std::size_t(symbol) * fixture_width + feature];
    midas_codec::require(std::isfinite(source), "nonfinite incremental embedding");
    hidden[feature] = FloatToBf16(RoundToBf16(source) * scale);
  }
  return hidden;
}

Bf16Buffer FixtureAttentionProbability(const Bf16Buffer& content,
    const Bf16Buffer& relative, const Bf16Buffer& bias, std::size_t state) {
  Require(content, fixture_positions, "incremental content");
  Require(relative, fixture_positions, "incremental relative");
  Require(bias, fixture_positions, "incremental bias");
  const float bias_scale = RoundToBf16(std::sqrt(float(fixture_width * fixture_width)));
  const float score_scale = RoundToBf16(1.0F / std::sqrt(float(fixture_width)));
  F32Buffer scores(fixture_positions, -std::numeric_limits<float>::infinity());
  for (std::size_t position = 0; position <= fixture_memory + state; ++position) {
    // The original full-graph relative shift uses states=64, NOT states=1.
    // For every unmasked entry: raw_state=state, raw_position=63-state+position.
    const auto raw_position = fixture_states - 1 - state + position;
    const float repeated_bias = RoundToBf16(Bf16ToFloat(bias[raw_position]) * bias_scale);
    const float shifted = RoundToBf16(Bf16ToFloat(relative[raw_position]) + repeated_bias);
    scores[position] = RoundToBf16(
        RoundToBf16(Bf16ToFloat(content[position]) + shifted) * score_scale);
  }
  // Keep all 72 slots and the original softmax. Its exponential floor can
  // leave nonzero masked weights; truncating the row would change arithmetic.
  const auto probabilities = SoftmaxForward(std::move(scores), fixture_positions);
  Bf16Buffer output(probabilities.size());
  std::transform(probabilities.begin(), probabilities.end(), output.begin(), FloatToBf16);
  return output;
}
}  // namespace

void IncrementalProfileForward::reset(
    const ProfileWeights& weights, const std::vector<Bf16Buffer>& memory) {
  // The full forward also validates the exact geometry. One layer is essential:
  // its future zero-symbol K/V rows are independent of earlier hidden outputs.
  // Preserve these placeholders, not numerical zero, including their tiny
  // masked value contributions. This reference reset is included in timings.
  const auto cache = ProfileForward(geometry(), weights,
      std::vector<std::uint32_t>(fixture_states, 0),
      std::vector<std::uint32_t>(fixture_states, 0), memory);
  key_ = cache.layers[0].key; value_ = cache.layers[0].value;
  inputs_.clear(); probabilities_.clear(); initialized_ = true;
}

void IncrementalProfileForward::advance(const ProfileWeights& weights, std::uint8_t symbol) {
  midas_codec::require(initialized_ && rows() < fixture_states && weights.layers.size() == 1,
                       "incremental forward requires a reset fixed one-layer segment");
  const auto& layer = weights.layers[0];
  auto hidden = FixtureEmbedding(weights, symbol);
  const auto attention_input = RmsNormForward(hidden, layer.ln_g1, layer.ln_b1, 1, fixture_width);
  const auto query = LinearForward(layer.w_q, attention_input, nullptr, 1, fixture_width, fixture_width);
  const auto kv = LinearForward(layer.w_kv, attention_input, nullptr, 1, fixture_width, 2 * fixture_width);
  const auto offset = (fixture_memory + rows()) * fixture_width;
  std::copy_n(kv.begin(), fixture_width, key_.begin() + offset);
  std::copy_n(kv.begin() + fixture_width, fixture_width, value_.begin() + offset);
  const auto content = DotKeyQuery(key_, query, 1, 1, 1, fixture_positions, fixture_width);
  const auto relative = DotRelativeQuery(layer.relative_weight, query, 1, 1, 1, fixture_positions, fixture_width);
  const auto attention = FixtureAttentionProbability(content, relative, weights.shared_relative_bias, rows());
  const auto merged = AttendValues(value_, attention, 1, 1, 1, fixture_positions, fixture_width);
  const auto attention_output = LinearForward(layer.w_o, merged, nullptr, 1, fixture_width, fixture_width);
  const auto residual = AddBf16(hidden, attention_output);
  const auto feedforward_input = RmsNormForward(residual, layer.ln_g2, layer.ln_b2, 1, fixture_width);
  const auto ff1 = LinearForward(layer.ff1, feedforward_input, &layer.ff_bias1,
                                 1, fixture_width, 2 * fixture_inner);
  const auto geglu = GegluForward(ff1, 1, fixture_inner);
  const auto ff2 = LinearForward(layer.ff2, geglu, &layer.ff_bias2, 1, fixture_inner, fixture_width);
  hidden = AddBf16(residual, ff2);
  const auto final_hidden = RmsNormForward(hidden, weights.final_ln_gain, weights.final_ln_bias, 1, fixture_width);
  const auto logits = LinearForward(weights.output_weight, final_hidden, &weights.output_bias, 1, fixture_width, 256);
  F32Buffer f32_logits(logits.size());
  std::transform(logits.begin(), logits.end(), f32_logits.begin(), Bf16ToFloat);
  probabilities_ = SoftmaxForward(std::move(f32_logits), 256);
  inputs_.push_back(symbol);
}

midas_codec::Bytes IncrementalProfileForward::serialize() const {
  using midas_codec::put;
  midas_codec::Bytes out{'I','F','W','D',1};
  put(out, initialized_, 1); put(out, rows(), 1);
  out.insert(out.end(), inputs_.begin(), inputs_.end());
  for (const auto* values : {&key_, &value_}) {
    put(out, values->size(), 8); for (auto value : *values) put(out, value, 2);
  }
  put(out, probabilities_.size(), 8);
  for (auto value : probabilities_) put(out, std::bit_cast<std::uint32_t>(value), 4);
  return out;
}

IncrementalProfileForward IncrementalProfileForward::restore(
    const midas_codec::Bytes& bytes, const ProfileWeights& weights, const std::vector<Bf16Buffer>& memory) {
  using midas_codec::require;
  require(bytes.size() <= 32 * 1024, "incremental checkpoint exceeds fixed geometry bound");
  midas_codec::Reader in(bytes); in.magic("IFWD\1", 5);
  const auto initialized = in.get(1), rows = in.get(1);
  require(initialized <= 1 && rows <= fixture_states && (initialized || rows == 0),
          "invalid incremental flags or cursor");
  const auto inputs = in.take(rows);
  for (unsigned i = 0; i != 2; ++i) {
    const auto size = in.get(8);
    require(size == (initialized ? fixture_positions * fixture_width : 0),
            "incremental K/V shape differs");
    in.take(size * 2);
  }
  const auto probabilities = in.get(8);
  require(probabilities == (rows ? 256U : 0U), "incremental output shape differs");
  in.take(probabilities * 4); in.end();
  // Validate every retained cache bit against parameters, memory, and input
  // history, including placeholders and F32 output. Do not silently repair it.
  IncrementalProfileForward rebuilt;
  if (initialized) rebuilt.reset(weights, memory);
  for (auto symbol : inputs) rebuilt.advance(weights, symbol);
  require(rebuilt.serialize() == bytes, "incremental cache disagrees with causal model state");
  return rebuilt;
}

}  // namespace gamma_enwiki9::nncp
