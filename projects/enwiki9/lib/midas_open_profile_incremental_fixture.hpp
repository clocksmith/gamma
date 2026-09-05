#pragma once

#include "midas_bit_predictor.hpp"
#include "midas_profile_incremental_forward.hpp"
#include "../programs/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/adam_update.hpp"
#include "../programs/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/profile_artifacts.hpp"
#include "../programs/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/profile_forward.hpp"
#include "../programs/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/profile_state.hpp"

#include <bit>
#include <cmath>
#include <numeric>
#include <type_traits>

namespace gamma_enwiki9::midas_codec {

// Executable integration fixture, not a selected competitive architecture.
// Reuses Gamma's existing open full-model kernels without calling the legacy
// replay's differently defined K/S arms. No trained tensors or teacher input.
// New cached-forward identity. The reference OpenProfileFixture is unchanged.
// Full-batch training and detached-memory rebuilding retain the same kernels.
// The archive model tag stays shared only to test exact cross-decoding; the
// checkpoint magic differs because the complete predictive cache is retained.
class OpenProfileIncrementalFixture {
 public:
  static constexpr std::uint32_t model_tag = 0x4f504601U;
  static constexpr std::size_t checkpoint_bound = 2 * 1024 * 1024;
  static nncp::ProfileGeometry geometry() {
    return {{64, 1, 1, 64, 8, 8}, 1, 256, 0, 64};
  }

  OpenProfileIncrementalFixture() {
    nncp::ValidateArithmeticEnvironment();
    initialize();
  }

  BytePrefix::Counts predict_byte() {
    require(!dirty_ && !predicted_, "profile prediction before rebuild or observation");
    if (!cache_valid_) refresh_prediction();
    predicted_ = true;
    return cached_;
  }
  void observe_byte(std::uint8_t byte) {
    require(!dirty_ && predicted_ && prefix_.size() < 64,
            "profile observation without a causal prediction");
    require(position_ != std::numeric_limits<std::uint64_t>::max(),
            "profile byte clock overflow");
    prefix_.push_back(byte); ++position_;
    predicted_ = false; cache_valid_ = false; cached_.fill(0);
  }

  Bytes sequence_origin() const {
    Bytes out{'O','R','I','G',1};
    put(out, position_ - prefix_.size(), 8); put(out, predecessor_, 1);
    for (const auto& row : memory_) write_vector(out, row);
    return out;
  }

  void full_update(const Bytes& origin, const Bytes& decoded, const Bytes& targets) {
    require(!dirty_ && !predicted_ && origin == sequence_origin() && decoded == prefix_ &&
            (decoded.size() == 32 || decoded.size() == 64) && targets.size() == decoded.size(),
            "profile update is not the exact completed causal prefix");
    auto g = geometry(); g.loss_length = decoded.size();
    const auto inputs = inputs_for(decoded, false);
    std::vector<std::uint32_t> loss_targets(64, 0);
    std::copy(targets.begin(), targets.end(), loss_targets.begin());
    const auto cache = nncp::ProfileForward(g, weights_, inputs, loss_targets, memory_);
    const auto backward = nncp::ProfileBackward(g, weights_, cache);
    const auto update = nncp::ApplyProfileAdamUpdate(
        g, weights_, backward.gradients, optimizer_, 0x1p-12F);
    require(update.tensors.size() == optimizer_.tensors.size(),
            "profile update omitted a declared parameter tensor");
    dirty_ = true; cache_valid_ = false; cached_.fill(0);
    incremental_ = {};  // Every full-model update invalidates all K/V rows.
  }

  void rebuild(const Bytes& origin, const Bytes& decoded) {
    require(dirty_ && origin == sequence_origin() && decoded == prefix_,
            "profile rebuild changed its detached causal boundary");
    if (prefix_.size() == 64) {
      const auto cache = forward(false);
      memory_ = nncp::AdvanceProfileMemory(geometry(), memory_, cache);
      predecessor_ = prefix_.back(); prefix_.clear();
    }
    // Recompute the next pre-truth distribution under the new full model. At a
    // segment boundary, carry only the explicitly detached updated memory and
    // previous decoded byte, never an old active-prefix activation cache.
    dirty_ = false;
    refresh_prediction();
  }

  std::uint64_t position() const { return position_; }
  std::uint64_t updates() const { return optimizer_.next_update_exponent - 1; }

  Bytes serialize() const {
    Bytes out{'O','P','F','I',1}; put(out, model_tag, 4);
    put(out, position_, 8); put(out, predecessor_, 1);
    put(out, dirty_, 1); put(out, predicted_, 1); put(out, cache_valid_, 1);
    put(out, prefix_.size(), 1); out.insert(out.end(), prefix_.begin(), prefix_.end());
    for (auto count : cached_) put(out, count, 4);
    for (const auto& row : memory_) write_vector(out, row);
    // CanonicalParameterArtifacts exposes mutable views. Take a snapshot so
    // checkpointing cannot mutate the authoritative model through that API.
    auto snapshot = weights_;
    for (const auto& item : nncp::CanonicalParameterArtifacts(geometry(), snapshot)) {
      if (item.bf16_values) write_vector(out, *item.bf16_values);
      else write_vector(out, *item.f32_values);
    }
    put(out, optimizer_.next_update_exponent, 8);
    for (const auto& tensor : optimizer_.tensors) {
      write_vector(out, tensor.low_words); write_vector(out, tensor.variance_bf16);
      write_vector(out, tensor.variance_f32);
    }
    const auto incremental = incremental_.serialize();
    put(out, incremental.size(), 8); out.insert(out.end(), incremental.begin(), incremental.end());
    return out;
  }

  static OpenProfileIncrementalFixture restore(const Bytes& bytes) {
    require(bytes.size() <= checkpoint_bound, "profile checkpoint exceeds fixture bound");
    Reader in(bytes); in.magic("OPFI\1", 5);
    require(in.get(4) == model_tag, "profile checkpoint model differs");
    OpenProfileIncrementalFixture model;
    model.position_ = in.get(8); model.predecessor_ = static_cast<std::uint8_t>(in.get(1));
    model.dirty_ = read_flag(in); model.predicted_ = read_flag(in);
    model.cache_valid_ = read_flag(in);
    const auto length = in.get(1);
    require(length <= 64 && length <= model.position_ &&
            (model.position_ - length) % 64 == 0,
            "profile checkpoint prefix disagrees with its byte clock");
    model.prefix_ = in.take(static_cast<std::size_t>(length));
    for (auto& count : model.cached_) count = static_cast<std::uint32_t>(in.get(4));
    for (auto& row : model.memory_) read_vector(in, row, false);
    for (const auto& item : nncp::CanonicalParameterArtifacts(geometry(), model.weights_)) {
      if (item.bf16_values) read_vector(in, *item.bf16_values, false);
      else read_vector(in, *item.f32_values, false);
    }
    model.optimizer_.next_update_exponent = in.get(8);
    require(model.optimizer_.next_update_exponent > 0, "zero profile optimizer exponent");
    for (auto& tensor : model.optimizer_.tensors) {
      read_vector(in, tensor.low_words, true);
      read_vector(in, tensor.variance_bf16, false);
      read_vector(in, tensor.variance_f32, false);
      require(std::all_of(tensor.variance_bf16.begin(), tensor.variance_bf16.end(),
                          [](auto value) { return nncp::Bf16ToFloat(value) >= 0; }) &&
              std::all_of(tensor.variance_f32.begin(), tensor.variance_f32.end(),
                          [](auto value) { return value >= 0; }),
              "negative profile second moment");
    }
    const auto incremental_size = in.get(8);
    require(incremental_size <= 32 * 1024, "incremental checkpoint exceeds bound");
    model.incremental_ = nncp::IncrementalProfileForward::restore(
        in.take(incremental_size), model.weights_, model.memory_);
    in.end();
    if (model.incremental_.initialized()) {
      require(!model.dirty_ && model.incremental_.rows() == length + model.cache_valid_,
              "incremental cursor disagrees with profile clock");
      const auto expected_inputs = model.inputs_for(model.prefix_, model.cache_valid_);
      require(std::equal(model.incremental_.inputs().begin(), model.incremental_.inputs().end(),
                         expected_inputs.begin()), "incremental inputs disagree with decoded prefix");
    } else {
      require(!model.cache_valid_ && (model.dirty_ || length == 0),
              "profile checkpoint lost its incremental cache");
    }
    require(!model.predicted_ || (model.cache_valid_ && !model.dirty_),
            "pending profile prediction lacks a valid distribution");
    require(!model.dirty_ || (!model.cache_valid_ && !model.predicted_),
            "dirty profile checkpoint retains a prediction");
    if (model.cache_valid_) {
      BytePrefix check; check.begin_byte(model.cached_);
      const auto saved = model.cached_;
      model.refresh_prediction();
      require(model.cached_ == saved, "profile cached distribution disagrees with model state");
    } else {
      require(std::all_of(model.cached_.begin(), model.cached_.end(),
                          [](auto count) { return count == 0; }),
              "invalidated profile checkpoint retains probability counts");
    }
    return model;
  }

  // Exact component snapshots for attribution and first-divergence reporting.
  std::vector<std::pair<std::string, Bytes>> parameter_states() const {
    std::vector<std::pair<std::string, Bytes>> result;
    auto snapshot = weights_;
    for (const auto& item : nncp::CanonicalParameterArtifacts(geometry(), snapshot)) {
      Bytes bytes;
      if (item.bf16_values) write_vector(bytes, *item.bf16_values);
      else write_vector(bytes, *item.f32_values);
      result.emplace_back(item.descriptor.name, std::move(bytes));
    }
    return result;
  }

  // A diagnostic assertion, never called by normal prediction or coding.
  Bytes reference_state() const {
    auto bytes = serialize();
    bytes.resize(bytes.size() - 8 - incremental_.serialize().size());
    bytes[3] = 'X';
    return bytes;  // Compare the full model/optimizer state across backends.
  }

  // The cache remains present in serialize(); reference_state is NOT a complete
  // incremental checkpoint or state witness and is used only for attribution.
  // Compare the unquantized F32 row bit-for-bit, not only final Q16 counts.
  void verify_reference_row() const {
    require(!dirty_ && cache_valid_ && incremental_.rows() == prefix_.size() + 1,
            "reference comparison lacks a current incremental row");
    const auto reference = forward(true);
    for (std::size_t b = 0; b != 256; ++b)
      require(std::bit_cast<std::uint32_t>(reference.probabilities[prefix_.size() * 256 + b]) ==
              std::bit_cast<std::uint32_t>(incremental_.probabilities()[b]),
              "incremental F32 probability differs from full reference");
  }

 private:
  nncp::IncrementalProfileForward incremental_;
  nncp::ProfileWeights weights_;
  nncp::ProfileAdamState optimizer_{};
  std::vector<nncp::Bf16Buffer> memory_;
  Bytes prefix_;
  BytePrefix::Counts cached_{};
  std::uint64_t position_ = 0;
  std::uint8_t predecessor_ = 0;
  bool dirty_ = false, predicted_ = false, cache_valid_ = false;

  static bool read_flag(Reader& in) {
    const auto flag = in.get(1); require(flag <= 1, "invalid profile checkpoint flag");
    return flag != 0;
  }
  template<class T> static void write_vector(Bytes& out, const std::vector<T>& values) {
    put(out, values.size(), 8);
    for (auto value : values) {
      if constexpr (std::is_same_v<T, float>) put(out, std::bit_cast<std::uint32_t>(value), 4);
      else put(out, value, 2);
    }
  }
  template<class T> static void read_vector(Reader& in, std::vector<T>& values, bool low_words) {
    require(in.get(8) == values.size(), "profile tensor geometry differs");
    for (auto& value : values) {
      if constexpr (std::is_same_v<T, float>) {
        value = std::bit_cast<float>(static_cast<std::uint32_t>(in.get(4)));
        require(std::isfinite(value), "nonfinite profile F32 tensor");
      } else {
        value = static_cast<T>(in.get(2));
        require(low_words || std::isfinite(nncp::Bf16ToFloat(value)),
                "nonfinite profile BF16 tensor");
      }
    }
  }

  std::vector<std::uint32_t> inputs_for(const Bytes& decoded, bool next_prediction) const {
    require(decoded.size() <= 64, "profile prefix exceeds segment");
    std::vector<std::uint32_t> inputs(64, 0);
    inputs[0] = predecessor_;
    const auto known = std::min<std::size_t>(64, decoded.size() + (next_prediction ? 1 : 0));
    for (std::size_t i = 1; i < known; ++i) inputs[i] = decoded[i - 1];
    return inputs;
  }
  nncp::ProfileCache forward(bool next_prediction) const {
    return nncp::ProfileForward(geometry(), weights_, inputs_for(prefix_, next_prediction),
                                std::vector<std::uint32_t>(64, 0), memory_);
  }
  void refresh_prediction() {
    require(!dirty_ && prefix_.size() < 64, "profile prediction outside a rebuilt segment");
    if (!incremental_.initialized()) incremental_.reset(weights_, memory_);
    while (incremental_.rows() <= prefix_.size()) {
      const auto row = incremental_.rows();
      incremental_.advance(weights_, row == 0 ? predecessor_ : prefix_[row - 1]);
    }
    require(incremental_.rows() == prefix_.size() + 1, "incremental forward cursor escaped prefix");
    const auto& probabilities = incremental_.probabilities();
    double sum = 0;
    for (unsigned b = 0; b != 256; ++b) {
      const auto p = probabilities[b];
      require(std::isfinite(p) && p >= 0, "invalid open profile probability"); sum += p;
    }
    require(sum > 0 && std::isfinite(sum), "empty open profile distribution");
    std::array<double, 256> remainder;
    std::array<unsigned, 256> order;
    std::iota(order.begin(), order.end(), 0U);
    unsigned assigned = 0;
    for (unsigned b = 0; b != 256; ++b) {
      const auto scaled = 65280.0 * probabilities[b] / sum;
      const auto whole = static_cast<unsigned>(std::floor(scaled));
      cached_[b] = whole + 1; assigned += cached_[b]; remainder[b] = scaled - whole;
    }
    require(assigned <= 65536 && 65536 - assigned <= 256, "profile quantization overflow");
    std::stable_sort(order.begin(), order.end(), [&](auto a, auto b) {
      return remainder[a] > remainder[b];
    });
    for (unsigned i = 0; i != 65536 - assigned; ++i) ++cached_[order[i]];
    cache_valid_ = true;
  }

  void initialize() {
    constexpr std::size_t model = 64, inner = 8, positions = 72;
    const auto zeros = [](std::size_t n) { return nncp::Bf16Buffer(n, 0); };
    const auto gains = [](std::size_t n) { return nncp::Bf16Buffer(n, nncp::FloatToBf16(1)); };
    weights_ = {
      .output_weight = zeros(256 * model), .final_ln_gain = gains(model),
      .layers = {{gains(model), zeros(model), zeros(model * model), zeros(2 * model * model),
                  zeros(model * positions), zeros(model * model), gains(model), zeros(model),
                  zeros(2 * inner * model), zeros(2 * inner), zeros(model * inner), zeros(model)}},
      .embedding = nncp::F32Buffer(256 * model, 0),
      .shared_relative_bias = zeros(positions), .final_ln_bias = zeros(model),
      .output_bias = zeros(256)};
    // Fixed integer PRNG used only at initialization, not a hidden model asset.
    std::uint32_t random = 123;
    for (auto& item : nncp::CanonicalParameterArtifacts(geometry(), weights_)) {
      const auto& name = item.descriptor.name;
      if (name.rfind("ln_", 0) == 0 || name.find("bias") != std::string::npos || name == "b_r_0")
        continue;
      const auto next = [&]() {
        random = random * 1664525U + 1013904223U;
        return (static_cast<int>(random >> 16) - 32768) * 0x1p-20F;
      };
      if (item.bf16_values) for (auto& value : *item.bf16_values) value = nncp::FloatToBf16(next());
      else for (auto& value : *item.f32_values) value = next();
    }
    optimizer_.next_update_exponent = 1;
    for (const auto& descriptor : nncp::CanonicalGradientDescriptors(geometry())) {
      std::size_t count = 1; for (auto n : descriptor.dimensions) count *= n;
      nncp::AdamTensorState state{descriptor, {}, {}, {}};
      if (descriptor.element_type == nncp::GradientElementType::kBf16) {
        state.low_words.assign(count, 0x8000); state.variance_bf16.assign(count, 0);
      } else state.variance_f32.assign(count, 0);
      optimizer_.tensors.push_back(std::move(state));
    }
    memory_ = {zeros(8 * model)};
  }
};

}  // namespace gamma_enwiki9::midas_codec
