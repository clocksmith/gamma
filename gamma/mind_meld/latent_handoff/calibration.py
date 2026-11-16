"""Paired Qwen3 activation capture with explicit RoPE-space boundaries."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

import torch

from .contract import ContractError
from .hf_cache import LBSHDCache
from .mapper import DirectionalMapper
from .rope import apply_rope, qwen3_cos_sin, strip_rope


@dataclass(frozen=True)
class PrefillCapture:
    token_ids: torch.Tensor
    position_ids: torch.Tensor
    logits: torch.Tensor
    rotated_cache: LBSHDCache
    content_cache: LBSHDCache
    elapsed_seconds: float
    synchronization_seconds: float
    cache_capture_seconds: float
    rope_removal_seconds: float


def _synchronize(device: torch.device) -> None:
    if device.type == "cuda" and torch.cuda.is_available():
        torch.cuda.synchronize(device)


@torch.no_grad()
def capture_prefill(model: Any, token_ids: torch.Tensor) -> PrefillCapture:
    if token_ids.ndim != 2 or token_ids.shape[1] == 0:
        raise ContractError("prefill token_ids must be non-empty [B,S]")
    position_ids = torch.arange(
        token_ids.shape[1], device=token_ids.device, dtype=torch.long
    ).unsqueeze(0).expand(token_ids.shape[0], -1)
    cache_position = torch.arange(token_ids.shape[1], device=token_ids.device)
    attention_mask = torch.ones_like(token_ids)
    sync_started = time.perf_counter()
    _synchronize(token_ids.device)
    synchronization_elapsed = time.perf_counter() - sync_started
    started = time.perf_counter()
    output = model(
        input_ids=token_ids,
        attention_mask=attention_mask,
        position_ids=position_ids,
        cache_position=cache_position,
        use_cache=True,
        return_dict=True,
    )
    _synchronize(token_ids.device)
    elapsed = time.perf_counter() - started
    capture_started = time.perf_counter()
    rotated = LBSHDCache.capture(output.past_key_values)
    _synchronize(rotated.key.device)
    capture_elapsed = time.perf_counter() - capture_started
    cos, sin = qwen3_cos_sin(
        model.config,
        position_ids,
        dtype=rotated.key.dtype,
        device=rotated.key.device,
    )
    _synchronize(rotated.key.device)
    rope_started = time.perf_counter()
    content = LBSHDCache(strip_rope(rotated.key, cos, sin), rotated.value.clone())
    _synchronize(rotated.key.device)
    rope_elapsed = time.perf_counter() - rope_started
    return PrefillCapture(
        token_ids=token_ids.detach().clone(),
        position_ids=position_ids,
        logits=output.logits.detach().clone(),
        rotated_cache=rotated,
        content_cache=content,
        elapsed_seconds=elapsed,
        synchronization_seconds=synchronization_elapsed,
        cache_capture_seconds=capture_elapsed,
        rope_removal_seconds=rope_elapsed,
    )


def apply_directional_mapper(
    mapper: DirectionalMapper,
    source_content: LBSHDCache,
    target_config: Any,
    position_ids: torch.Tensor,
) -> LBSHDCache:
    mapped, _, _ = apply_directional_mapper_timed(
        mapper, source_content, target_config, position_ids
    )
    return mapped


@dataclass(frozen=True)
class MappingTimings:
    feature_gather_and_kv_mapping_seconds: float
    target_rope_application_seconds: float
    total_seconds: float


def apply_directional_mapper_timed(
    mapper: DirectionalMapper,
    source_content: LBSHDCache,
    target_config: Any,
    position_ids: torch.Tensor,
) -> tuple[LBSHDCache, MappingTimings, LBSHDCache]:
    _synchronize(source_content.key.device)
    total_started = time.perf_counter()
    mapping_started = time.perf_counter()
    mapped = mapper.map_content(source_content)
    _synchronize(mapped.key.device)
    mapping_elapsed = time.perf_counter() - mapping_started
    cos, sin = qwen3_cos_sin(
        target_config,
        position_ids,
        dtype=mapped.key.dtype,
        device=mapped.key.device,
    )
    _synchronize(mapped.key.device)
    rope_started = time.perf_counter()
    rotated = LBSHDCache(apply_rope(mapped.key, cos, sin), mapped.value)
    _synchronize(mapped.key.device)
    rope_elapsed = time.perf_counter() - rope_started
    return (
        rotated,
        MappingTimings(
            feature_gather_and_kv_mapping_seconds=mapping_elapsed,
            target_rope_application_seconds=rope_elapsed,
            total_seconds=time.perf_counter() - total_started,
        ),
        mapped,
    )
