#ifndef GAMMA_ENWIKI9_NNCP_ADAM_UPDATE_HPP
#define GAMMA_ENWIKI9_NNCP_ADAM_UPDATE_HPP

#include "profile_backward.hpp"

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace gamma_enwiki9::nncp {

struct AdamTensorState {
  GradientDescriptor descriptor;
  // BF16 parameters retain a biased low word and a BF16 second moment.
  // F32 parameters use only variance_f32.
  std::vector<std::uint16_t> low_words;
  Bf16Buffer variance_bf16;
  F32Buffer variance_f32;
};

struct ProfileAdamState {
  // Bias correction for the next update uses beta2^next_update_exponent.
  std::uint64_t next_update_exponent;
  std::vector<AdamTensorState> tensors;
};

struct AdamTensorDiagnostic {
  std::string name;
  float gradient_norm;
  float gradient_scale;
};

struct ProfileAdamUpdateResult {
  std::uint64_t update_exponent;
  float beta2_power;
  float bias_correction;
  float alpha;
  float epsilon_squared;
  std::size_t clipped_tensors;
  std::vector<AdamTensorDiagnostic> tensors;
};

// The serialized optimizer container does not carry the scalar update count;
// its prospectively bound next exponent is therefore an explicit input.
ProfileAdamState LoadProfileAdamState(
    const ProfileGeometry& geometry,
    const std::filesystem::path& optimizer_container,
    std::uint64_t next_update_exponent);

// Applies the exact no-first-moment LibNC Adam variant in canonical parameter
// topology. Each tensor is clipped independently. The state exponent advances
// only after all tensor updates complete.
ProfileAdamUpdateResult ApplyProfileAdamUpdate(
    const ProfileGeometry& geometry,
    ProfileWeights& weights,
    const ProfileGradients& gradients,
    ProfileAdamState& state,
    float learning_rate);

}  // namespace gamma_enwiki9::nncp

#endif
