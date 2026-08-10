import torch
from transformers import Qwen3Config

from src.mind_meld.latent_handoff.rope import (
    apply_rope,
    qwen3_cos_sin,
    strip_rope,
)


def test_qwen3_rope_strip_reapply_round_trip() -> None:
    config = Qwen3Config(
        vocab_size=64,
        hidden_size=32,
        intermediate_size=64,
        num_hidden_layers=2,
        num_attention_heads=4,
        num_key_value_heads=2,
        head_dim=8,
        max_position_embeddings=256,
        rope_theta=1_000_000.0,
    )
    keys = torch.randn(2, 1, 2, 17, 8)
    positions = torch.arange(17).unsqueeze(0)
    cos, sin = qwen3_cos_sin(config, positions, dtype=keys.dtype, device=keys.device)
    rotated = apply_rope(keys, cos, sin)
    content = strip_rope(rotated, cos, sin)
    recovered = apply_rope(content, cos, sin)
    torch.testing.assert_close(content, keys, rtol=1e-5, atol=1e-6)
    torch.testing.assert_close(recovered, rotated, rtol=1e-5, atol=1e-6)
