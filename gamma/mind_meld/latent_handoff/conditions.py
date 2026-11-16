"""Pre-registered latent and textual comparison conditions."""

from __future__ import annotations

from enum import Enum
import torch

from .contract import ContractError
from .hf_cache import LBSHDCache


class Condition(str, Enum):
    TARGET_NATIVE_CACHE = "TARGET_NATIVE_CACHE"
    TARGET_REPREFILL_TIMED = "TARGET_REPREFILL_TIMED"
    NO_HISTORY = "NO_HISTORY"
    SUMMARY_750_WORDS = "SUMMARY_750_WORDS"
    SUMMARY_TOKEN_MATCHED = "SUMMARY_TOKEN_MATCHED"
    DIRECT_COPY = "DIRECT_COPY"
    RANDOM_ORTHOGONAL = "RANDOM_ORTHOGONAL"
    RIDGE_K1 = "RIDGE_K1"
    RIDGE_K4 = "RIDGE_K4"
    RIDGE_K8 = "RIDGE_K8"
    RIDGE_ALL = "RIDGE_ALL"
    WRONG_CACHE_SAME_LENGTH = "WRONG_CACHE_SAME_LENGTH"
    PERMUTED_MAP = "PERMUTED_MAP"
    ZERO_CACHE = "ZERO_CACHE"


def zero_cache(reference: LBSHDCache) -> LBSHDCache:
    return LBSHDCache(torch.zeros_like(reference.key), torch.zeros_like(reference.value))


def wrong_cache(correct: LBSHDCache, unrelated: LBSHDCache) -> LBSHDCache:
    if correct.geometry != unrelated.geometry:
        raise ContractError("wrong-cache control must have exactly matching geometry")
    if correct.tensor_digest() == unrelated.tensor_digest():
        raise ContractError("wrong-cache control is identical to correct cache")
    return unrelated


def permuted_cache(reference: LBSHDCache, seed: int) -> LBSHDCache:
    generator = torch.Generator(device=reference.key.device).manual_seed(seed)
    layer_order = torch.randperm(reference.geometry.layers, generator=generator, device=reference.key.device)
    head_order = torch.randperm(reference.geometry.kv_heads, generator=generator, device=reference.key.device)
    return LBSHDCache(
        reference.key[layer_order][:, :, head_order],
        reference.value[layer_order][:, :, head_order],
    )


def random_orthogonal_cache(reference: LBSHDCache, seed: int) -> LBSHDCache:
    generator = torch.Generator(device=reference.key.device).manual_seed(seed)
    dim = reference.geometry.head_dim
    matrix = torch.randn((dim, dim), generator=generator, device=reference.key.device, dtype=torch.float32)
    q, _ = torch.linalg.qr(matrix)
    return LBSHDCache(
        torch.einsum("lbhse,ed->lbhsd", reference.key.float(), q).to(reference.key.dtype),
        torch.einsum("lbhse,ed->lbhsd", reference.value.float(), q).to(reference.value.dtype),
    )
