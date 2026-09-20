"""FP32 training adapters for FX2's explicit reference kernels (batch one).

Copied into a derived package beside the authenticated upstream reference file.
These compute actual reference operations, never impersonate an installed FLA.
"""
import torch
from torch import nn

from .kda_reference import (
    causal_conv1d_silu_reference,
    fused_rmsnorm_gated_reference,
    kda_recurrent_reference,
)


def chunk_kda(*, q, k, v, g, beta, A_log, dt_bias,
              use_qk_l2norm_in_kernel, use_gate_in_kernel, cu_seqlens):
    if not use_qk_l2norm_in_kernel or not use_gate_in_kernel:
        raise ValueError("reference profile requires normalized keys and internal gates")
    output = kda_recurrent_reference(q, k, v, g, beta, A_log, dt_bias,
                                    cu_seqlens=cu_seqlens, dtype=torch.float32)
    return output, None


def causal_conv1d(*, x, weight, activation, cu_seqlens):
    if activation != "silu":
        raise ValueError("reference profile requires SiLU")
    return causal_conv1d_silu_reference(x, weight, cu_seqlens, dtype=torch.float32), None


class FusedRMSNormGated(nn.Module):
    def __init__(self, hidden_size, activation):
        super().__init__()
        if activation != "sigmoid":
            raise ValueError("reference profile requires sigmoid")
        self.weight = nn.Parameter(torch.ones(hidden_size))

    def forward(self, x, gate):
        return fused_rmsnorm_gated_reference(x, gate, self.weight, dtype=torch.float32)
