"""Calibration-only single-source probes and top-k layer selection."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable, Iterable, Sequence

import torch

from .contract import ContractError
from .hf_cache import LBSHDCache
from .ridge import RidgeAccumulator


@dataclass(frozen=True)
class LayerProbe:
    target_layer: int
    source_layer: int
    score: float


PairSource = Sequence[tuple[LBSHDCache, LBSHDCache]] | Callable[
    [], Iterable[tuple[LBSHDCache, LBSHDCache]]
]


def _iter_pairs(source: PairSource) -> Iterable[tuple[LBSHDCache, LBSHDCache]]:
    return source() if callable(source) else iter(source)


def _first_pair(source: PairSource) -> tuple[LBSHDCache, LBSHDCache]:
    try:
        return next(iter(_iter_pairs(source)))
    except StopIteration as exc:
        raise ContractError("calibration pair source is empty") from exc


def _features(cache: torch.Tensor, layer_indices: Sequence[int]) -> torch.Tensor:
    # [K,B,H,S,D] -> [B*S,K*H*D]
    selected = cache[list(layer_indices)]
    return selected.permute(1, 3, 0, 2, 4).reshape(
        selected.shape[1] * selected.shape[3], -1
    )


def _targets(cache: torch.Tensor, layer: int, head: int) -> torch.Tensor:
    # [B,S,D]
    value = cache[layer, :, head]
    return value.permute(0, 1, 2).reshape(-1, value.shape[-1])


def _head_features(
    cache: torch.Tensor, layer_indices: Sequence[int], head: int
) -> torch.Tensor:
    # [K,B,S,D] -> [B*S,K*D]
    selected = cache[list(layer_indices), :, head]
    return selected.permute(1, 2, 0, 3).reshape(
        selected.shape[1] * selected.shape[2], -1
    )


def select_source_layers(
    pairs: PairSource,
    *,
    top_k: int,
    ridge_lambda: float = 0.01,
) -> tuple[tuple[int, ...], ...]:
    """Select source layers using calibration data only.

    Each single-source score averages independently fitted K and V R2 values
    across target KV heads, matching the selection granularity of the paper.
    """

    first_source, first_target = _first_pair(pairs)
    source_layers = first_source.geometry.layers
    target_geometry = first_target.geometry
    if first_source.geometry.kv_heads != target_geometry.kv_heads:
        raise ContractError("v0 layer probes require matched source and target KV heads")
    if top_k <= 0 or top_k > source_layers:
        raise ContractError(f"invalid top_k={top_k} for {source_layers} source layers")
    output_dim = target_geometry.layers * target_geometry.head_dim
    accumulators: dict[tuple[str, int, int], RidgeAccumulator] = {}
    for family in ("key", "value"):
        for source_layer in range(source_layers):
            for head in range(target_geometry.kv_heads):
                accumulators[(family, source_layer, head)] = RidgeAccumulator(
                    first_source.geometry.head_dim,
                    output_dim,
                )
    for source, target in _iter_pairs(pairs):
        for family in ("key", "value"):
            source_family = getattr(source, family)
            target_family = getattr(target, family)
            for head in range(target_geometry.kv_heads):
                target_all_layers = target_family[:, :, head].permute(1, 2, 0, 3).reshape(
                    -1, output_dim
                )
                for source_layer in range(source_layers):
                    accumulators[(family, source_layer, head)].update(
                        _head_features(source_family, (source_layer,), head),
                        target_all_layers,
                    )
    scores: dict[tuple[int, int], list[float]] = {
        (target_layer, source_layer): []
        for target_layer in range(target_geometry.layers)
        for source_layer in range(source_layers)
    }
    for family in ("key", "value"):
        for source_layer in range(source_layers):
            for head in range(target_geometry.kv_heads):
                accumulator = accumulators[(family, source_layer, head)]
                weight, _ = accumulator.solve(ridge_lambda)
                output_scores = accumulator.r2_by_output(weight).reshape(
                    target_geometry.layers, target_geometry.head_dim
                )
                for target_layer in range(target_geometry.layers):
                    scores[(target_layer, source_layer)].append(
                        float(output_scores[target_layer].mean().item())
                    )
    selected: list[tuple[int, ...]] = []
    for target_layer in range(target_geometry.layers):
        probes = [
            LayerProbe(
                target_layer,
                source_layer,
                sum(scores[(target_layer, source_layer)])
                / len(scores[(target_layer, source_layer)]),
            )
            for source_layer in range(source_layers)
        ]
        probes.sort(key=lambda probe: (-probe.score, probe.source_layer))
        selected.append(tuple(probe.source_layer for probe in probes[:top_k]))
    return tuple(selected)


__all__ = [
    "LayerProbe",
    "select_source_layers",
    "_features",
    "_head_features",
    "_targets",
    "PairSource",
    "_first_pair",
    "_iter_pairs",
]
