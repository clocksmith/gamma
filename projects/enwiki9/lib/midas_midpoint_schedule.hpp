#pragma once

#include "midas_native_codec.hpp"

namespace gamma_enwiki9::midas_codec {

enum class Arm : std::uint8_t { P = 0, K = 1, F = 2, S = 3 };

// Model contract (no teacher tensors or future input are accepted):
//   Counts predict_byte(); void observe_byte(uint8_t);
//   Bytes sequence_origin() const;
//   void full_update(origin, decoded_inputs, decoded_targets);
//   void rebuild(origin, decoded_inputs);
//   Bytes serialize() const; static Model restore(Bytes);
// full_update must train the declared complete model and optimizer, not merely
// an output bias. The backend's own gradient and state tests prove that property.
// origin is a decoder-derived detached recurrent boundary, NOT an old activation
// cache. Every update is followed by recomputation of the active decoded prefix.
template<class Model>
class MidpointSchedule {
 public:
  explicit MidpointSchedule(Model model, Arm arm)
      : model_(std::move(model)), arm_(arm), origin_(model_.sequence_origin()) {
    require(static_cast<unsigned>(arm_) <= 3, "unknown midpoint arm");
  }

  BytePrefix::Counts predict_byte() {
    require(!pending_, "consume the pending byte before another prediction");
    const auto counts = model_.predict_byte();
    BytePrefix validation; validation.begin_byte(counts);
    distribution_ = counts; pending_ = true;
    return counts;
  }

  void observe_byte(std::uint8_t decoded_byte) {
    require(pending_, "byte prediction must precede observation");
    require(position_ != std::numeric_limits<std::uint64_t>::max(),
            "midpoint byte position overflow");
    model_.observe_byte(decoded_byte);
    decoded_.push_back(decoded_byte); ++position_;
    pending_ = false; distribution_.fill(0);
    if (decoded_.size() == 32 && arm_ != Arm::P) {
      const auto targets = midpoint_targets();
      if (arm_ == Arm::K) {
        const auto original = model_.serialize();
        Model shadow = Model::restore(original);
        train_and_rebuild(shadow, targets);
        last_shadow_ = shadow.serialize();
        require(model_.serialize() == original, "bookkeeping modified the parent");
        ++shadow_updates_;
      } else {
        train_and_rebuild(model_, targets);
        ++midpoint_updates_;
      }
    }
    if (decoded_.size() == 64) {
      // P is itself an online parent: its ordinary full-model update is shared
      // by every arm. F/S add only the prospectively defined midpoint update.
      train_and_rebuild(model_, decoded_);
      ++parent_updates_;
      decoded_.clear();
      origin_ = model_.sequence_origin();
    }
  }

  const Model& model() const { return model_; }
  std::uint64_t position() const { return position_; }
  bool pending_byte() const { return pending_; }
  const BytePrefix::Counts& pending_distribution() const { return distribution_; }
  std::uint64_t parent_updates() const { return parent_updates_; }
  std::uint64_t midpoint_updates() const { return midpoint_updates_; }
  std::uint64_t shadow_updates() const { return shadow_updates_; }
  const Bytes& last_shadow() const { return last_shadow_; }

  // Explicit P/K identity projection: K's observational counters and discarded
  // shadow cannot influence later predictions. Full checkpoints retain them.
  // F and S remain distinct even before their first update.
  Bytes parent_identity_state() const {
    Bytes out{'M', 'P', 'R', 'E', 1};
    const auto effective = arm_ == Arm::K ? Arm::P : arm_;
    put(out, static_cast<unsigned>(effective), 1);
    append_predictive(out);
    return out;
  }

  Bytes serialize() const {
    Bytes out{'M', 'S', 'C', 'H', 1};
    put(out, static_cast<unsigned>(arm_), 1);
    append_predictive(out);
    put(out, midpoint_updates_, 8); put(out, shadow_updates_, 8);
    append_blob(out, last_shadow_);
    return out;
  }

  static MidpointSchedule restore(const Bytes& bytes,
                                  std::uint64_t maximum_component_bytes) {
    Reader in(bytes); in.magic("MSCH\1", 5);
    const auto arm = in.get(1);
    require(arm <= 3, "invalid checkpoint arm");
    const auto position = in.get(8), parent_updates = in.get(8);
    const auto pending = in.get(1);
    require(pending <= 1, "invalid pending-byte flag");
    BytePrefix::Counts distribution;
    for (auto& count : distribution) count = static_cast<std::uint32_t>(in.get(4));
    const auto decoded = read_blob(in, 63);
    const auto origin = read_blob(in, maximum_component_bytes);
    Model model = Model::restore(read_blob(in, maximum_component_bytes));
    const auto midpoint_updates = in.get(8), shadow_updates = in.get(8);
    const auto shadow = read_blob(in, maximum_component_bytes);
    in.end();
    require(position % 64 == decoded.size() && parent_updates == position / 64,
            "checkpoint midpoint population disagrees with its byte clock");
    const auto opportunities = position / 64 + (position % 64 >= 32 ? 1 : 0);
    require(midpoint_updates == ((arm == 2 || arm == 3) ? opportunities : 0),
            "checkpoint midpoint update count disagrees with schedule");
    require(shadow_updates == (arm == 1 ? opportunities : 0),
            "checkpoint bookkeeping count disagrees with schedule");
    require(shadow.empty() == (shadow_updates == 0),
            "checkpoint shadow state disagrees with bookkeeping count");
    if (pending) {
      BytePrefix validation; validation.begin_byte(distribution);
    } else {
      require(std::all_of(distribution.begin(), distribution.end(),
                          [](auto value) { return value == 0; }),
              "inactive prediction retains a distribution");
    }
    MidpointSchedule result(std::move(model), static_cast<Arm>(arm));
    result.position_ = position; result.parent_updates_ = parent_updates;
    result.pending_ = pending != 0; result.distribution_ = distribution;
    result.decoded_ = decoded; result.origin_ = origin;
    result.midpoint_updates_ = midpoint_updates; result.shadow_updates_ = shadow_updates;
    result.last_shadow_ = shadow;
    return result;
  }

 private:
  Model model_;
  Arm arm_;
  Bytes origin_, decoded_, last_shadow_;
  BytePrefix::Counts distribution_{};
  std::uint64_t position_ = 0, parent_updates_ = 0;
  std::uint64_t midpoint_updates_ = 0, shadow_updates_ = 0;
  bool pending_ = false;

  static void append_blob(Bytes& output, const Bytes& blob) {
    put(output, blob.size(), 8);
    output.insert(output.end(), blob.begin(), blob.end());
  }
  static Bytes read_blob(Reader& input, std::uint64_t maximum) {
    const auto size = input.get(8);
    require(size <= maximum && size <= input.remaining(),
            "checkpoint component exceeds its bound");
    return input.take(static_cast<std::size_t>(size));
  }
  Bytes midpoint_targets() const {
    require(decoded_.size() == 32, "midpoint update outside frozen boundary");
    Bytes targets = decoded_;
    if (arm_ == Arm::S) std::rotate(targets.begin(), targets.begin() + 1, targets.end());
    return targets;
  }
  void train_and_rebuild(Model& model, const Bytes& targets) {
    require(targets.size() == decoded_.size(), "training population mismatch");
    model.full_update(origin_, decoded_, targets);
    model.rebuild(origin_, decoded_);
  }
  void append_predictive(Bytes& output) const {
    put(output, position_, 8); put(output, parent_updates_, 8); put(output, pending_, 1);
    for (auto count : distribution_) put(output, count, 4);
    append_blob(output, decoded_); append_blob(output, origin_);
    append_blob(output, model_.serialize());
  }
};

}  // namespace gamma_enwiki9::midas_codec
