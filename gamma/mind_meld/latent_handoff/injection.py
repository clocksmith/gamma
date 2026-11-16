"""Fail-closed target cache injection and continuation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
import time
from typing import Any

import torch

from .contract import (
    CacheGeometry,
    ContractError,
    ExperimentContract,
    ModelIdentity,
    RouteOutcome,
)
from .hf_cache import LBSHDCache
from .rope import rope_contract_from_config


@dataclass(frozen=True)
class InjectionResult:
    logits: torch.Tensor
    cache: LBSHDCache
    route: RouteOutcome
    cache_position: torch.Tensor
    cache_creation_seconds: float
    forward_seconds: float
    attention_outputs: tuple[torch.Tensor, ...]


def _synchronize(device: torch.device) -> None:
    if device.type == "cuda" and torch.cuda.is_available():
        torch.cuda.synchronize(device)


def assert_geometry(actual: CacheGeometry, expected: CacheGeometry, label: str) -> None:
    if actual != expected:
        raise ContractError(f"{label} cache geometry mismatch: {actual} != {expected}")


@torch.no_grad()
def inject_and_forward(
    model: Any,
    cache: LBSHDCache,
    input_ids: torch.Tensor,
    contract: ExperimentContract,
    *,
    target_identity: ModelIdentity,
    capture_attention_outputs: bool = True,
) -> InjectionResult:
    """Decode from an admitted cache without any reset, replay, or fallback."""

    contract.validate()
    if target_identity != contract.target:
        raise ContractError("loaded target model identity does not match the contract")
    config = getattr(model, "config", None)
    if config is None:
        raise ContractError("target model has no configuration")
    expected_layers = int(getattr(config, "num_hidden_layers", 0))
    expected_heads = int(
        getattr(config, "num_key_value_heads", None)
        or getattr(config, "num_attention_heads", 0)
    )
    expected_head_dim = getattr(config, "head_dim", None)
    if expected_head_dim is None:
        expected_head_dim = config.hidden_size // config.num_attention_heads
    if (
        cache.geometry.layers,
        cache.geometry.kv_heads,
        cache.geometry.head_dim,
    ) != (expected_layers, expected_heads, int(expected_head_dim)):
        raise ContractError("target model attention geometry does not match the cache")
    if rope_contract_from_config(config) != contract.target_rope:
        raise ContractError("target model RoPE identity does not match the contract")
    from transformers import __version__ as active_transformers_version

    if active_transformers_version != contract.transformers_version:
        raise ContractError("Transformers runtime version does not match the contract")
    if getattr(config, "_attn_implementation", None) != contract.attention_implementation:
        raise ContractError("attention implementation does not match the contract")
    if not torch.are_deterministic_algorithms_enabled():
        raise ContractError("deterministic algorithms are not enabled in the active runtime")
    assert_geometry(cache.geometry, contract.target_geometry, "target")
    if contract.route not in (RouteOutcome.NATIVE_TARGET_CACHE, RouteOutcome.MAPPED_CACHE):
        raise ContractError(f"prohibited route: {contract.route}")
    if input_ids.ndim != 2 or input_ids.shape[0] != cache.geometry.batch:
        raise ContractError("receiver input_ids must be [B,S] with matching batch")
    start = cache.sequence_length
    cache_position = torch.arange(
        start, start + input_ids.shape[1], device=input_ids.device, dtype=torch.long
    )
    position_ids = cache_position.unsqueeze(0).expand(input_ids.shape[0], -1)
    attention_mask = torch.ones(
        (input_ids.shape[0], start + input_ids.shape[1]),
        device=input_ids.device,
        dtype=torch.long,
    )
    _synchronize(cache.key.device)
    creation_started = time.perf_counter()
    dynamic_cache = cache.to_dynamic_cache(getattr(model, "config", None))
    _synchronize(cache.key.device)
    creation_elapsed = time.perf_counter() - creation_started
    attention_outputs: list[torch.Tensor] = []
    handles = []
    if capture_attention_outputs:
        layers = getattr(getattr(model, "model", None), "layers", None)
        if layers is None:
            raise ContractError("target model does not expose Qwen3 attention layers")

        def capture_attention(_module: Any, _inputs: Any, output: Any) -> None:
            value = output[0] if isinstance(output, tuple) else output
            attention_outputs.append(value.detach().clone())

        handles = [layer.self_attn.register_forward_hook(capture_attention) for layer in layers]
    forward_started = time.perf_counter()
    try:
        output = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            cache_position=cache_position,
            past_key_values=dynamic_cache,
            use_cache=True,
            return_dict=True,
        )
    finally:
        for handle in handles:
            handle.remove()
    _synchronize(cache.key.device)
    forward_elapsed = time.perf_counter() - forward_started
    if capture_attention_outputs and len(attention_outputs) != expected_layers:
        raise ContractError(
            f"captured {len(attention_outputs)} attention outputs for {expected_layers} layers"
        )
    if output.past_key_values is None:
        raise ContractError("target model did not return a cache")
    return InjectionResult(
        logits=output.logits,
        cache=LBSHDCache.capture(output.past_key_values),
        route=contract.route,
        cache_position=cache_position,
        cache_creation_seconds=creation_elapsed,
        forward_seconds=forward_elapsed,
        attention_outputs=tuple(attention_outputs),
    )


@torch.no_grad()
def greedy_continue(
    model: Any,
    initial: InjectionResult,
    contract: ExperimentContract,
    *,
    target_identity: ModelIdentity,
    max_new_tokens: int,
) -> tuple[torch.Tensor, list[InjectionResult]]:
    """Greedily continue an admitted route while retaining every cache boundary."""

    if max_new_tokens <= 0:
        raise ContractError("max_new_tokens must be positive")
    tokens: list[torch.Tensor] = []
    steps: list[InjectionResult] = []
    current = initial
    for _ in range(max_new_tokens):
        token = current.logits[:, -1, :].argmax(dim=-1, keepdim=True)
        tokens.append(token)
        step_contract = replace(
            contract,
            source_geometry=current.cache.geometry,
            target_geometry=current.cache.geometry,
        )
        current = inject_and_forward(
            model,
            current.cache,
            token,
            step_contract,
            target_identity=target_identity,
            capture_attention_outputs=False,
        )
        steps.append(current)
    return torch.cat(tokens, dim=1), steps
