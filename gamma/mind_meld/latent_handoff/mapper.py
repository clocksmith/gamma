"""Frozen, direction-specific dense ridge mapper artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
from typing import Any

import torch

from .contract import ContractError, ModelIdentity, canonical_json, digest_object
from .hf_cache import LBSHDCache
from .layer_selection import (
    PairSource,
    _features,
    _first_pair,
    _head_features,
    _iter_pairs,
    _targets,
)
from .ridge import RidgeAccumulator


MAPPER_SCHEMA = "gamma.latent-handoff-mapper/v1"


@dataclass(frozen=True)
class DirectionalMapper:
    source: ModelIdentity
    target: ModelIdentity
    selected_layers: tuple[tuple[int, ...], ...]
    ridge_lambda: float
    calibration_digest: str
    validation_digest: str
    fit_code_commit: str
    key_weight: torch.Tensor  # [Lt,Ht,F,Dt]
    key_bias: torch.Tensor  # [Lt,Ht,Dt]
    value_weight: torch.Tensor
    value_bias: torch.Tensor
    source_kv_heads: int
    source_head_dim: int
    target_kv_heads: int
    target_head_dim: int
    feature_policy: str = "all-source-kv-heads"
    schema: str = MAPPER_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != MAPPER_SCHEMA:
            raise ContractError(f"unsupported mapper schema: {self.schema}")
        self.source.validate()
        self.target.validate()
        if self.ridge_lambda < 0 or not self.selected_layers:
            raise ContractError("invalid mapper fit policy")
        if self.feature_policy not in ("all-source-kv-heads", "same-source-head"):
            raise ContractError(f"unsupported mapper feature policy: {self.feature_policy}")
        if self.feature_policy == "same-source-head" and self.source_kv_heads != self.target_kv_heads:
            raise ContractError("same-source-head requires equal source and target KV-head counts")
        shapes = (
            self.key_weight.shape,
            self.value_weight.shape,
            self.key_bias.shape,
            self.value_bias.shape,
        )
        if shapes[0] != shapes[1] or shapes[2] != shapes[3]:
            raise ContractError("K/V mapper tensor shapes differ")
        layers, heads, feature_dim, head_dim = self.key_weight.shape
        if self.key_bias.shape != (layers, heads, head_dim):
            raise ContractError("mapper bias shape is incompatible with weights")
        if layers != len(self.selected_layers) or heads != self.target_kv_heads:
            raise ContractError("mapper target geometry does not match selected layers")
        if head_dim != self.target_head_dim:
            raise ContractError("mapper target head dimension mismatch")
        for selection in self.selected_layers:
            source_heads = self.source_kv_heads if self.feature_policy == "all-source-kv-heads" else 1
            expected = len(selection) * source_heads * self.source_head_dim
            if feature_dim != expected:
                raise ContractError("mapper feature width does not match source selection")

    @property
    def direction(self) -> str:
        return f"{self.source.repository}@{self.source.revision}->{self.target.repository}@{self.target.revision}"

    def to(
        self, device: torch.device | str, dtype: torch.dtype | None = None
    ) -> "DirectionalMapper":
        """Return a mapper whose executable tensors share a device and dtype."""

        def move(tensor: torch.Tensor) -> torch.Tensor:
            return tensor.to(device=device, dtype=dtype or tensor.dtype)

        return replace(
            self,
            key_weight=move(self.key_weight),
            key_bias=move(self.key_bias),
            value_weight=move(self.value_weight),
            value_bias=move(self.value_bias),
        )

    def map_content(self, source: LBSHDCache) -> LBSHDCache:
        if source.geometry.kv_heads != self.source_kv_heads:
            raise ContractError("mapper source KV-head count mismatch")
        if source.geometry.head_dim != self.source_head_dim:
            raise ContractError("mapper source head dimension mismatch")
        keys: list[torch.Tensor] = []
        values: list[torch.Tensor] = []
        for target_layer, selection in enumerate(self.selected_layers):
            if self.feature_policy == "all-source-kv-heads":
                xk = _features(source.key, selection).to(
                    device=self.key_weight.device, dtype=self.key_weight.dtype
                )
                xv = _features(source.value, selection).to(
                    device=self.value_weight.device, dtype=self.value_weight.dtype
                )
                mapped_k = torch.einsum("nf,hfd->nhd", xk, self.key_weight[target_layer])
                mapped_v = torch.einsum("nf,hfd->nhd", xv, self.value_weight[target_layer])
            else:
                mapped_keys = []
                mapped_values = []
                for head in range(self.target_kv_heads):
                    xk = _head_features(source.key, selection, head).to(
                        device=self.key_weight.device, dtype=self.key_weight.dtype
                    )
                    xv = _head_features(source.value, selection, head).to(
                        device=self.value_weight.device, dtype=self.value_weight.dtype
                    )
                    mapped_keys.append(xk @ self.key_weight[target_layer, head])
                    mapped_values.append(xv @ self.value_weight[target_layer, head])
                mapped_k = torch.stack(mapped_keys, dim=1)
                mapped_v = torch.stack(mapped_values, dim=1)
            mapped_k += self.key_bias[target_layer]
            mapped_v += self.value_bias[target_layer]
            batch, sequence = source.geometry.batch, source.geometry.sequence
            keys.append(mapped_k.reshape(batch, sequence, self.target_kv_heads, -1).permute(0, 2, 1, 3))
            values.append(mapped_v.reshape(batch, sequence, self.target_kv_heads, -1).permute(0, 2, 1, 3))
        return LBSHDCache(torch.stack(keys), torch.stack(values))

    def _metadata(self, tensor_digests: dict[str, str]) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source": asdict(self.source),
            "target": asdict(self.target),
            "direction": self.direction,
            "selectedSourceLayers": [list(value) for value in self.selected_layers],
            "ridgeLambda": self.ridge_lambda,
            "calibrationDigest": self.calibration_digest,
            "validationDigest": self.validation_digest,
            "fitCodeCommit": self.fit_code_commit,
            "geometry": {
                "sourceKvHeads": self.source_kv_heads,
                "sourceHeadDim": self.source_head_dim,
                "targetKvHeads": self.target_kv_heads,
                "targetHeadDim": self.target_head_dim,
            },
            "featurePolicy": self.feature_policy,
            "tensorDigests": tensor_digests,
        }

    def save(self, directory: Path) -> str:
        from safetensors.torch import save_file

        directory.mkdir(parents=True, exist_ok=True)
        tensors = {
            "key_weight": self.key_weight.detach().cpu().contiguous(),
            "key_bias": self.key_bias.detach().cpu().contiguous(),
            "value_weight": self.value_weight.detach().cpu().contiguous(),
            "value_bias": self.value_bias.detach().cpu().contiguous(),
        }
        tensor_digests = {
            name: hashlib.sha256(tensor.view(torch.uint8).numpy().tobytes()).hexdigest()
            for name, tensor in tensors.items()
        }
        metadata = self._metadata(tensor_digests)
        artifact_digest = digest_object(metadata)
        metadata["artifactDigest"] = artifact_digest
        save_file(tensors, directory / "mapper.safetensors")
        (directory / "mapper.json").write_bytes(canonical_json(metadata) + b"\n")
        return artifact_digest

    @classmethod
    def load(cls, directory: Path) -> "DirectionalMapper":
        from safetensors.torch import load_file

        metadata = json.loads((directory / "mapper.json").read_text(encoding="utf-8"))
        artifact_digest = metadata.pop("artifactDigest")
        if digest_object(metadata) != artifact_digest:
            raise ContractError("mapper metadata digest mismatch")
        tensors = load_file(directory / "mapper.safetensors")
        for name, expected in metadata["tensorDigests"].items():
            actual = hashlib.sha256(tensors[name].contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()
            if actual != expected:
                raise ContractError(f"mapper tensor digest mismatch: {name}")
        geometry = metadata["geometry"]
        return cls(
            source=ModelIdentity(**metadata["source"]),
            target=ModelIdentity(**metadata["target"]),
            selected_layers=tuple(tuple(v) for v in metadata["selectedSourceLayers"]),
            ridge_lambda=metadata["ridgeLambda"],
            calibration_digest=metadata["calibrationDigest"],
            validation_digest=metadata["validationDigest"],
            fit_code_commit=metadata["fitCodeCommit"],
            key_weight=tensors["key_weight"],
            key_bias=tensors["key_bias"],
            value_weight=tensors["value_weight"],
            value_bias=tensors["value_bias"],
            source_kv_heads=geometry["sourceKvHeads"],
            source_head_dim=geometry["sourceHeadDim"],
            target_kv_heads=geometry["targetKvHeads"],
            target_head_dim=geometry["targetHeadDim"],
            feature_policy=metadata["featurePolicy"],
        )


def fit_directional_mapper(
    pairs: PairSource,
    *,
    source_identity: ModelIdentity,
    target_identity: ModelIdentity,
    selected_layers: tuple[tuple[int, ...], ...],
    calibration_digest: str,
    validation_digest: str,
    fit_code_commit: str,
    ridge_lambda: float = 0.01,
    feature_policy: str = "all-source-kv-heads",
) -> DirectionalMapper:
    first_source, first_target = _first_pair(pairs)
    source_geometry, target_geometry = first_source.geometry, first_target.geometry
    if len({len(value) for value in selected_layers}) != 1:
        raise ContractError("v0 mapper artifact requires a common k across target layers")
    if feature_policy not in ("all-source-kv-heads", "same-source-head"):
        raise ContractError(f"unsupported mapper feature policy: {feature_policy}")
    if feature_policy == "same-source-head" and source_geometry.kv_heads != target_geometry.kv_heads:
        raise ContractError("same-source-head requires equal KV-head counts")
    feature_heads = source_geometry.kv_heads if feature_policy == "all-source-kv-heads" else 1
    feature_dim = len(selected_layers[0]) * feature_heads * source_geometry.head_dim
    weights: dict[str, list[torch.Tensor]] = {"key": [], "value": []}
    biases: dict[str, list[torch.Tensor]] = {"key": [], "value": []}
    for family in ("key", "value"):
        for target_layer, selection in enumerate(selected_layers):
            if feature_policy == "all-source-kv-heads":
                accumulator = RidgeAccumulator(
                    feature_dim,
                    target_geometry.kv_heads * target_geometry.head_dim,
                )
                for source, target in _iter_pairs(pairs):
                    source_features = _features(getattr(source, family), selection)
                    target_layer_values = getattr(target, family)[target_layer]
                    all_targets = target_layer_values.permute(0, 2, 1, 3).reshape(
                        -1, target_geometry.kv_heads * target_geometry.head_dim
                    )
                    accumulator.update(source_features, all_targets)
                weight, bias = accumulator.solve(ridge_lambda)
                weights[family].append(
                    weight.reshape(
                        feature_dim,
                        target_geometry.kv_heads,
                        target_geometry.head_dim,
                    ).permute(1, 0, 2)
                )
                biases[family].append(
                    bias.reshape(target_geometry.kv_heads, target_geometry.head_dim)
                )
                continue
            head_weights: list[torch.Tensor] = []
            head_biases: list[torch.Tensor] = []
            for target_head in range(target_geometry.kv_heads):
                accumulator = RidgeAccumulator(feature_dim, target_geometry.head_dim)
                for source, target in _iter_pairs(pairs):
                    source_features = _head_features(
                        getattr(source, family), selection, target_head
                    )
                    accumulator.update(
                        source_features,
                        _targets(getattr(target, family), target_layer, target_head),
                    )
                weight, bias = accumulator.solve(ridge_lambda)
                head_weights.append(weight)
                head_biases.append(bias)
            weights[family].append(torch.stack(head_weights))
            biases[family].append(torch.stack(head_biases))
    return DirectionalMapper(
        source=source_identity,
        target=target_identity,
        selected_layers=selected_layers,
        ridge_lambda=ridge_lambda,
        calibration_digest=calibration_digest,
        validation_digest=validation_digest,
        fit_code_commit=fit_code_commit,
        key_weight=torch.stack(weights["key"]),
        key_bias=torch.stack(biases["key"]),
        value_weight=torch.stack(weights["value"]),
        value_bias=torch.stack(biases["value"]),
        source_kv_heads=source_geometry.kv_heads,
        source_head_dim=source_geometry.head_dim,
        target_kv_heads=target_geometry.kv_heads,
        target_head_dim=target_geometry.head_dim,
        feature_policy=feature_policy,
    )
