#pragma once

#include "midas_midpoint_schedule.hpp"

namespace gamma_enwiki9::midas_codec {

// Joins the byte-level learning schedule to the coder's pre-truth bit boundary.
// No model architecture or corpus gate is selected here. A real Model must still
// prove its full gradients, optimizer and rebuild semantics independently.
template<class Model>
class MidpointBitPredictor {
 public:
  explicit MidpointBitPredictor(Model model, Arm arm)
      : schedule_(std::move(model), arm) {}

  std::uint16_t predict() {
    if (!prefix_.active()) prefix_.begin_byte(schedule_.predict_byte());
    return prefix_.predict();
  }
  void observe(unsigned decoded_bit) {
    if (const auto byte = prefix_.observe(decoded_bit)) schedule_.observe_byte(*byte);
  }
  std::uint64_t bit_position() const { return prefix_.position(); }
  const MidpointSchedule<Model>& schedule() const { return schedule_; }

  Bytes serialize() const {
    validate_join();
    return join("MBIT\1", schedule_.serialize(), prefix_.serialize());
  }
  Bytes parent_identity_state() const {
    validate_join();
    return join("MBPI\1", schedule_.parent_identity_state(), prefix_.serialize());
  }

  static MidpointBitPredictor restore(const Bytes& bytes,
                                      std::uint64_t maximum_checkpoint_bytes) {
    require(bytes.size() <= maximum_checkpoint_bytes, "bit checkpoint exceeds budget");
    Reader in(bytes); in.magic("MBIT\1", 5);
    auto schedule = MidpointSchedule<Model>::restore(blob(in), maximum_checkpoint_bytes);
    auto prefix = BytePrefix::restore(blob(in)); in.end();
    MidpointBitPredictor result(std::move(schedule), std::move(prefix));
    result.validate_join();
    return result;
  }

 private:
  MidpointSchedule<Model> schedule_;
  BytePrefix prefix_;

  MidpointBitPredictor(MidpointSchedule<Model> schedule, BytePrefix prefix)
      : schedule_(std::move(schedule)), prefix_(std::move(prefix)) {}

  void validate_join() const {
    require(prefix_.position() / 8 == schedule_.position(),
            "byte and bit checkpoint clocks disagree");
    require(prefix_.active() == schedule_.pending_byte(),
            "checkpoint pending byte crosses component boundaries");
    require(prefix_.distribution() == schedule_.pending_distribution(),
            "checkpoint pre-truth distributions disagree");
  }
  static Bytes blob(Reader& in) {
    const auto size = in.get(8);
    require(size <= in.remaining(), "truncated bit checkpoint component");
    return in.take(static_cast<std::size_t>(size));
  }
  static Bytes join(const char* magic, const Bytes& schedule, const Bytes& prefix) {
    Bytes out(magic, magic + 5);
    for (const auto* component : {&schedule, &prefix}) {
      put(out, component->size(), 8);
      out.insert(out.end(), component->begin(), component->end());
    }
    return out;
  }
};

}  // namespace gamma_enwiki9::midas_codec
