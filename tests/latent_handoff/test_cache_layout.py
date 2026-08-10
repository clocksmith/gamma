from types import SimpleNamespace

import numpy as np
import torch

from src.mind_meld.bridges.kv_cache_handler import PyTorchKVCache
from src.mind_meld.latent_handoff.hf_cache import LBSHDCache


def _config() -> SimpleNamespace:
    return SimpleNamespace(
        model_type="qwen3",
        num_hidden_layers=2,
        num_attention_heads=4,
        num_key_value_heads=2,
        hidden_size=32,
        head_dim=8,
    )


def test_legacy_wrapper_uses_sequence_axis_not_kv_head_axis() -> None:
    cache = tuple(
        (torch.randn(1, 2, 7, 8), torch.randn(1, 2, 7, 8)) for _ in range(2)
    )
    wrapped = PyTorchKVCache(cache, _config())
    assert wrapped.sequence_length == 7
    assert wrapped.can_resume(_config(), required_length=7)

    prefix = wrapped.copy_prefix(3)
    assert prefix.key.shape == (2, 1, 2, 3, 8)
    assert prefix.value.shape == (2, 1, 2, 3, 8)
    np.testing.assert_array_equal(prefix.key, wrapped.key[:, :, :, :3, :])


def test_lbshd_dynamic_cache_round_trip() -> None:
    original = LBSHDCache(
        torch.randn(2, 1, 2, 7, 8),
        torch.randn(2, 1, 2, 7, 8),
    )
    recovered = LBSHDCache.capture(original.to_dynamic_cache())
    assert recovered.geometry == original.geometry
    torch.testing.assert_close(recovered.key, original.key, rtol=0, atol=0)
    torch.testing.assert_close(recovered.value, original.value, rtol=0, atol=0)


def test_lbshd_prefix_slices_axis_three() -> None:
    cache = LBSHDCache(torch.randn(3, 1, 2, 9, 4), torch.randn(3, 1, 2, 9, 4))
    prefix = cache.copy_prefix(4)
    assert prefix.key.shape == (3, 1, 2, 4, 4)
    torch.testing.assert_close(prefix.key, cache.key[:, :, :, :4, :])
