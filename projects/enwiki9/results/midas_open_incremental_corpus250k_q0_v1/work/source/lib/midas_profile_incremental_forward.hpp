#pragma once

#include "midas_native_codec.hpp"
#include "../programs/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/profile_forward.hpp"

namespace gamma_enwiki9::nncp {

// Separate implementation identity for the fixed one-layer open integration
// fixture. Not a generic multi-layer cache and not an architecture selection.
// The owner must reset after every parameter or detached-memory change.
class IncrementalProfileForward {
 public:
  static ProfileGeometry geometry() { return {{64, 1, 1, 64, 8, 8}, 1, 256, 0, 64}; }
  void reset(const ProfileWeights&, const std::vector<Bf16Buffer>& memory);
  void advance(const ProfileWeights&, std::uint8_t input_symbol);
  bool initialized() const { return initialized_; }
  std::size_t rows() const { return inputs_.size(); }
  const midas_codec::Bytes& inputs() const { return inputs_; }
  const F32Buffer& probabilities() const { return probabilities_; }
  midas_codec::Bytes serialize() const;
  static IncrementalProfileForward restore(
      const midas_codec::Bytes&, const ProfileWeights&, const std::vector<Bf16Buffer>& memory);

 private:
  bool initialized_ = false;
  midas_codec::Bytes inputs_;
  Bf16Buffer key_, value_;
  F32Buffer probabilities_;
};

}  // namespace gamma_enwiki9::nncp
