#ifndef GAMMA_ENWIKI9_NNCP_PROFILE_OUTPUT_HEAD_HPP
#define GAMMA_ENWIKI9_NNCP_PROFILE_OUTPUT_HEAD_HPP

#include "profile_backward.hpp"

namespace gamma_enwiki9::nncp {

struct ProfileOutputHeadBackwardResult {
  Bf16Buffer output_weight;
  Bf16Buffer output_bias;
  Bf16Buffer logit_residual;
};

// Computes exactly the two gradients retained by the output-head-only
// attribution arm. No deeper model adjoint is allocated or evaluated.
ProfileOutputHeadBackwardResult ProfileOutputHeadBackward(
    const ProfileGeometry& geometry,
    const ProfileCache& cache);

}  // namespace gamma_enwiki9::nncp

#endif
