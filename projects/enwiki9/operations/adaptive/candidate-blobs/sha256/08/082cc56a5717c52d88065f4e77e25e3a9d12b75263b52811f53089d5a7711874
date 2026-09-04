#ifndef GAMMA_ENWIKI9_NNCP_PROFILE_ARTIFACTS_HPP
#define GAMMA_ENWIKI9_NNCP_PROFILE_ARTIFACTS_HPP

#include "profile_backward.hpp"

#include <cstddef>
#include <filesystem>
#include <vector>

namespace gamma_enwiki9::nncp {

// A non-owning view of one gradient in canonical LibNC source order. Exactly
// one value pointer is populated, as selected by descriptor.element_type.
struct GradientArtifactView {
  GradientDescriptor descriptor;
  const Bf16Buffer* bf16_values = nullptr;
  const F32Buffer* f32_values = nullptr;
};

// Binds every canonical descriptor to the corresponding treatment-owned
// buffer and rejects missing, duplicate, wrong-type, or wrong-size bindings.
std::vector<GradientArtifactView> CanonicalGradientArtifacts(
    const ProfileGeometry& geometry,
    const ProfileGradients& gradients);

// Creates directory and writes one .bin/.meta pair per canonical gradient.
// The directory must not already exist.
void WriteCanonicalGradientArtifacts(
    const std::filesystem::path& directory,
    const ProfileGeometry& geometry,
    const ProfileGradients& gradients);

}  // namespace gamma_enwiki9::nncp

#endif
