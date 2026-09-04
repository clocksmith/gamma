#ifndef GAMMA_ENWIKI9_NNCP_PROFILE_STATE_HPP
#define GAMMA_ENWIKI9_NNCP_PROFILE_STATE_HPP

#include "profile_backward.hpp"

#include <vector>

namespace gamma_enwiki9::nncp {

// Reproduces TransformerModel::mem_update. The current layer inputs are the
// decoder-visible attention_input caches from the completed segment forward.
std::vector<Bf16Buffer> AdvanceProfileMemory(
    const ProfileGeometry& geometry,
    const std::vector<Bf16Buffer>& prior_memory,
    const ProfileCache& completed_segment);

}  // namespace gamma_enwiki9::nncp

#endif
