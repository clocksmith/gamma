#ifndef GAMMA_ENWIKI9_NNCP_PROFILE_FORWARD_HPP
#define GAMMA_ENWIKI9_NNCP_PROFILE_FORWARD_HPP

#include "profile_backward.hpp"

#include <cstdint>
#include <vector>

namespace gamma_enwiki9::nncp {

// Memory inputs are one [memory, stream, model] BF16 payload per layer. The
// returned cache contains every decoder-visible activation required by
// ProfileBackward. Input symbols may include the frozen zero-filled future
// half used by the midpoint graph construction; targets never affect forward.
ProfileCache ProfileForward(
    const ProfileGeometry& geometry,
    const ProfileWeights& weights,
    const std::vector<std::uint32_t>& input_symbols,
    const std::vector<std::uint32_t>& targets,
    const std::vector<Bf16Buffer>& memory_inputs);

}  // namespace gamma_enwiki9::nncp

#endif
