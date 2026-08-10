import torch

from src.mind_meld.latent_handoff.hf_cache import LBSHDCache
from src.mind_meld.latent_handoff.layer_selection import select_source_layers
from src.mind_meld.latent_handoff.ridge import (
    RidgeAccumulator,
    coefficient_of_determination,
)


def test_streaming_sufficient_statistic_r2_matches_explicit_predictions() -> None:
    torch.manual_seed(5)
    x = torch.randn(64, 5)
    y = x @ torch.randn(5, 3) + torch.randn(3)
    accumulator = RidgeAccumulator(5, 3)
    accumulator.update(x[:31], y[:31])
    accumulator.update(x[31:], y[31:])
    weight, bias = accumulator.solve(0.01)
    explicit = []
    prediction = x @ weight + bias
    for output in range(3):
        explicit.append(
            coefficient_of_determination(
                y[:, output : output + 1], prediction[:, output : output + 1]
            )
        )
    torch.testing.assert_close(
        accumulator.r2_by_output(weight),
        torch.tensor(explicit, dtype=torch.float64),
        rtol=1e-7,
        atol=1e-7,
    )


def test_layer_probe_selects_predictive_same_head_source_layer() -> None:
    torch.manual_seed(12)
    source = LBSHDCache(torch.randn(2, 1, 2, 48, 3), torch.randn(2, 1, 2, 48, 3))
    target = LBSHDCache(
        torch.stack((source.key[1], source.key[0])),
        torch.stack((source.value[1], source.value[0])),
    )
    assert select_source_layers([(source, target)], top_k=1, ridge_lambda=1e-8) == (
        (1,),
        (0,),
    )
