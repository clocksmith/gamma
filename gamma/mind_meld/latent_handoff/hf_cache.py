"""Typed Hugging Face cache capture and reconstruction in canonical LBSHD."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Iterator

import torch

from .contract import CacheGeometry, CacheLayout, ContractError


def _iter_layers(cache: Any) -> Iterator[tuple[torch.Tensor, torch.Tensor]]:
    if cache is None:
        raise ContractError("cannot capture an empty cache")
    if hasattr(cache, "to_legacy_cache"):
        cache = cache.to_legacy_cache()
    if not isinstance(cache, (tuple, list)):
        raise ContractError(f"unsupported Hugging Face cache class: {type(cache).__name__}")
    for index, layer in enumerate(cache):
        if not isinstance(layer, (tuple, list)) or len(layer) != 2:
            raise ContractError(f"cache layer {index} is not a K/V pair")
        key, value = layer
        if not isinstance(key, torch.Tensor) or not isinstance(value, torch.Tensor):
            raise ContractError(f"cache layer {index} does not contain tensors")
        yield key, value


@dataclass(frozen=True)
class LBSHDCache:
    key: torch.Tensor
    value: torch.Tensor

    def __post_init__(self) -> None:
        if self.key.ndim != 5 or self.value.ndim != 5:
            raise ContractError("canonical cache tensors must have rank 5 [L,B,H,S,D]")
        if self.key.shape != self.value.shape:
            raise ContractError("key and value cache shapes differ")
        if self.key.dtype != self.value.dtype:
            raise ContractError("key and value cache dtypes differ")
        if any(size <= 0 for size in self.key.shape):
            raise ContractError("cache dimensions must be positive")
        if self.key.device != self.value.device:
            raise ContractError("key and value cache devices differ")

    @classmethod
    def capture(cls, cache: Any, *, clone: bool = True) -> "LBSHDCache":
        keys: list[torch.Tensor] = []
        values: list[torch.Tensor] = []
        expected_shape: tuple[int, ...] | None = None
        for index, (key, value) in enumerate(_iter_layers(cache)):
            if key.ndim != 4 or value.ndim != 4:
                raise ContractError(
                    f"cache layer {index} must be [B,H,S,D], got {tuple(key.shape)}"
                )
            if key.shape != value.shape:
                raise ContractError(f"cache layer {index} K/V shapes differ")
            if expected_shape is None:
                expected_shape = tuple(key.shape)
            elif tuple(key.shape) != expected_shape:
                raise ContractError("hybrid or sliding-window layer shapes are unsupported")
            keys.append(key.detach().clone() if clone else key.detach())
            values.append(value.detach().clone() if clone else value.detach())
        if not keys:
            raise ContractError("cache has no populated layers")
        return cls(torch.stack(keys, dim=0), torch.stack(values, dim=0))

    @property
    def geometry(self) -> CacheGeometry:
        layers, batch, heads, sequence, head_dim = self.key.shape
        return CacheGeometry(
            layout=CacheLayout.LBSHD,
            layers=layers,
            batch=batch,
            kv_heads=heads,
            sequence=sequence,
            head_dim=head_dim,
            dtype=str(self.key.dtype).removeprefix("torch."),
        )

    @property
    def sequence_length(self) -> int:
        return self.key.shape[3]

    def copy_prefix(self, length: int) -> "LBSHDCache":
        if length <= 0 or length > self.sequence_length:
            raise ContractError(f"invalid cache prefix length: {length}")
        return LBSHDCache(
            self.key[:, :, :, :length, :].clone(),
            self.value[:, :, :, :length, :].clone(),
        )

    def to_dynamic_cache(self, config: Any | None = None) -> Any:
        from transformers.cache_utils import DynamicCache

        legacy = tuple((self.key[i], self.value[i]) for i in range(self.key.shape[0]))
        try:
            return DynamicCache.from_legacy_cache(legacy)
        except (AttributeError, TypeError):
            return DynamicCache(ddp_cache_data=legacy, config=config)

    def tensor_digest(self) -> str:
        digest = hashlib.sha256()
        for name, tensor in (("key", self.key), ("value", self.value)):
            contiguous = tensor.detach().to("cpu").contiguous()
            digest.update(name.encode("ascii"))
            digest.update(str(contiguous.dtype).encode("ascii"))
            digest.update(str(tuple(contiguous.shape)).encode("ascii"))
            digest.update(contiguous.view(torch.uint8).numpy().tobytes())
        return digest.hexdigest()
