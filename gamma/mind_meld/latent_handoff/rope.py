"""Exact default-RoPE strip and application for canonical LBSHD keys."""

from __future__ import annotations

import torch

from .contract import ContractError, RopeContract, digest_object


def rope_contract_from_config(config: object) -> RopeContract:
    scaling = getattr(config, "rope_scaling", None)
    rope_type = "default"
    if isinstance(scaling, dict):
        rope_type = scaling.get("rope_type", scaling.get("type", "default"))
    head_dim = getattr(config, "head_dim", None)
    if head_dim is None:
        head_dim = config.hidden_size // config.num_attention_heads
    return RopeContract(
        rope_type=rope_type,
        theta=float(getattr(config, "rope_theta", 10000.0)),
        scaling_digest=digest_object(scaling),
        rotary_dim=int(head_dim),
        position_base=0,
    )


def rotate_half(value: torch.Tensor) -> torch.Tensor:
    if value.shape[-1] % 2:
        raise ContractError("RoPE dimension must be even")
    left, right = value.chunk(2, dim=-1)
    return torch.cat((-right, left), dim=-1)


def qwen3_cos_sin(
    config: object,
    position_ids: torch.Tensor,
    *,
    dtype: torch.dtype,
    device: torch.device | str,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return [B,1,S,D] cos/sin using Transformers' pinned Qwen3 code."""

    from transformers.models.qwen3.modeling_qwen3 import Qwen3RotaryEmbedding

    contract = rope_contract_from_config(config)
    contract.validate()
    if position_ids.ndim != 2:
        raise ContractError("position_ids must be [B,S]")
    probe = torch.empty(
        (position_ids.shape[0], position_ids.shape[1], contract.rotary_dim),
        dtype=dtype,
        device=device,
    )
    rotary = Qwen3RotaryEmbedding(config, device=device).to(device)
    cos, sin = rotary(probe, position_ids.to(device))
    return cos.unsqueeze(1), sin.unsqueeze(1)


def apply_rope(keys: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    if keys.ndim not in (4, 5):
        raise ContractError("RoPE keys must be [B,H,S,D] or [L,B,H,S,D]")
    if keys.ndim == 5:
        cos, sin = cos.unsqueeze(0), sin.unsqueeze(0)
    return keys * cos + rotate_half(keys) * sin


def strip_rope(keys: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    """Invert scaled rotary embedding, including non-unit attention scaling."""

    if keys.ndim not in (4, 5):
        raise ContractError("RoPE keys must be [B,H,S,D] or [L,B,H,S,D]")
    if keys.ndim == 5:
        cos, sin = cos.unsqueeze(0), sin.unsqueeze(0)
    scale_sq = cos.square() + sin.square()
    if torch.any(scale_sq == 0):
        raise ContractError("RoPE scaling is singular")
    return (keys * cos - rotate_half(keys) * sin) / scale_sq
