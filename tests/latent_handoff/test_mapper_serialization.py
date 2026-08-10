from pathlib import Path

import torch

from src.mind_meld.latent_handoff.contract import ModelIdentity
from src.mind_meld.latent_handoff.hf_cache import LBSHDCache
from src.mind_meld.latent_handoff.mapper import (
    DirectionalMapper,
    fit_directional_mapper,
)


def identity(name: str) -> ModelIdentity:
    return ModelIdentity(name, "0123456789abcdef", "w", "c", "t", "h")


def test_streamed_ridge_mapper_recovers_known_head_maps_and_serializes(tmp_path: Path) -> None:
    torch.manual_seed(4)
    source = LBSHDCache(torch.randn(2, 1, 2, 32, 3), torch.randn(2, 1, 2, 32, 3))
    selected = ((0,), (1,))
    key_weights = torch.randn(2, 2, 6, 3)
    value_weights = torch.randn(2, 2, 6, 3)
    key_bias = torch.randn(2, 2, 3)
    value_bias = torch.randn(2, 2, 3)

    def apply(weights: torch.Tensor, biases: torch.Tensor, family: torch.Tensor) -> torch.Tensor:
        layers = []
        for layer, selection in enumerate(selected):
            x = family[list(selection)].permute(1, 3, 0, 2, 4).reshape(32, 6)
            y = torch.einsum("nf,hfd->nhd", x, weights[layer]) + biases[layer]
            layers.append(y.reshape(1, 32, 2, 3).permute(0, 2, 1, 3))
        return torch.stack(layers)

    target = LBSHDCache(
        apply(key_weights, key_bias, source.key),
        apply(value_weights, value_bias, source.value),
    )
    mapper = fit_directional_mapper(
        [(source, target)],
        source_identity=identity("source"),
        target_identity=identity("target"),
        selected_layers=selected,
        calibration_digest="calibration",
        validation_digest="validation",
        fit_code_commit="abcdef123456",
        ridge_lambda=1e-8,
    )
    mapped = mapper.map_content(source)
    torch.testing.assert_close(mapped.key, target.key, rtol=2e-4, atol=2e-4)
    torch.testing.assert_close(mapped.value, target.value, rtol=2e-4, atol=2e-4)

    digest = mapper.save(tmp_path)
    loaded = DirectionalMapper.load(tmp_path)
    assert loaded.direction == mapper.direction
    assert loaded.save(tmp_path / "copy") == digest
    remapped = loaded.map_content(source)
    torch.testing.assert_close(remapped.key, mapped.key, rtol=0, atol=0)


def test_same_head_ablation_uses_only_corresponding_source_head() -> None:
    torch.manual_seed(9)
    source = LBSHDCache(torch.randn(1, 1, 2, 24, 3), torch.randn(1, 1, 2, 24, 3))
    weights = torch.randn(2, 3, 3)
    key = torch.stack(
        [source.key[0, :, head] @ weights[head] for head in range(2)], dim=1
    ).unsqueeze(0)
    value = torch.stack(
        [source.value[0, :, head] @ weights[head] for head in range(2)], dim=1
    ).unsqueeze(0)
    target = LBSHDCache(key, value)
    mapper = fit_directional_mapper(
        [(source, target)],
        source_identity=identity("source"),
        target_identity=identity("target"),
        selected_layers=((0,),),
        calibration_digest="calibration",
        validation_digest="validation",
        fit_code_commit="abcdef123456",
        ridge_lambda=1e-8,
        feature_policy="same-source-head",
    )
    assert mapper.key_weight.shape == (1, 2, 3, 3)
    mapped = mapper.map_content(source)
    torch.testing.assert_close(mapped.key, target.key, rtol=2e-4, atol=2e-4)
    torch.testing.assert_close(mapped.value, target.value, rtol=2e-4, atol=2e-4)
