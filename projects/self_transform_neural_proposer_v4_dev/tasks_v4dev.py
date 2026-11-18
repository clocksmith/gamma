"""DEVELOPMENT COPY of the three synthetic families of `self_transform_neural_proposer_v3/tasks_b2_v3.py`.

The generator bodies below `build_heldout_task_dev`'s header are copied verbatim from
`build_v3_confirmation_task` (checked in `test_identity_v4dev.py`). Differences:
- `real_qwen35_swiglu_lora_cls` is NOT included: it mean-pools token embeddings through one MLP
  layer and sits in a memorisation regime, so it is not a real model edit. Nothing in v4-dev
  loads Qwen weights.
- Seeds must be development seeds (`>= DEV_SEED_FLOOR`); v3 confirmation seeds
  (9,750,000 .. 9,863,011) can never be built here.
"""
from __future__ import annotations

from pathlib import Path
import sys
import torch

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from baselines_v4dev import (
    DEV_SEED_FLOOR,
    NeuralTargetTaskV3,
    _anisotropic_inputs,
    _rand_init_matrix,
    forward_target_v3,
)

DEV_HELDOUT_FAMILIES = (
    "fourier_kan_multifreq_reg",
    "bilinear_gated_interaction_cls",
    "layernorm_residual_gelu_cls",
)


def build_heldout_task_dev(
    family: str,
    seed: int,
    dtype: torch.dtype = torch.float64,
) -> NeuralTargetTaskV3:
    """Build one held-out synthetic task (v3 generators, development seed)."""
    assert family in DEV_HELDOUT_FAMILIES, f"Unknown / excluded family: {family}"
    assert int(seed) >= DEV_SEED_FLOOR, f"Development seed {seed} must be >= {DEV_SEED_FLOOR}"

    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)

    if family == "fourier_kan_multifreq_reg":
        d_in, d_b, d_mix, d_out = 20, 16, 24, 4
        n_sup, n_qry = 56, 144
        X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, log10_span=1.30, dtype=dtype)
        teacher = [
            _rand_init_matrix(gen, d_b, d_in, scale=2.3, dtype=dtype),
            _rand_init_matrix(gen, d_b, d_in, scale=2.3, dtype=dtype),
            _rand_init_matrix(gen, d_b, d_in, scale=1.7, dtype=dtype),
            _rand_init_matrix(gen, d_mix, 3 * d_b, scale=1.9, dtype=dtype),
            _rand_init_matrix(gen, d_out, d_mix, scale=1.8, dtype=dtype),
        ]
        tmp = NeuralTargetTaskV3("tmp", family, "mse", "fourier_kan_reg", "silu", teacher, {}, X_all, X_all, X_all, X_all)
        with torch.no_grad():
            raw_y = forward_target_v3(tmp, teacher, X_all)[0]
            y_all = raw_y / raw_y.std().clamp_min(1e-6)
        Y_sup = y_all[:n_sup] + 0.18 * torch.randn((n_sup, d_out), generator=gen, dtype=dtype)
        Y_qry = y_all[n_sup:]
        init_layers = [
            _rand_init_matrix(gen, d_b, d_in, scale=2.1, dtype=dtype),
            _rand_init_matrix(gen, d_b, d_in, scale=2.1, dtype=dtype),
            _rand_init_matrix(gen, d_b, d_in, scale=0.55, dtype=dtype),
            _rand_init_matrix(gen, d_mix, 3 * d_b, scale=1.6, dtype=dtype),
            _rand_init_matrix(gen, d_out, d_mix, scale=0.45, dtype=dtype),
        ]
        return NeuralTargetTaskV3(
            task_id=f"{family}-{seed}",
            family=family,
            loss_type="mse",
            arch_kind="fourier_kan_reg",
            activation="silu",
            init_layers=init_layers,
            aux_tensors={},
            X_sup=X_all[:n_sup],
            Y_sup=Y_sup,
            X_qry=X_all[n_sup:],
            Y_qry=Y_qry,
            budget=10,
        )

    if family == "bilinear_gated_interaction_cls":
        d_in, d1, d2, n_cls = 22, 28, 22, 6
        n_sup, n_qry = 54, 144
        X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, log10_span=1.25, dtype=dtype)
        teacher = [
            _rand_init_matrix(gen, d1, d_in, scale=2.0, dtype=dtype),
            _rand_init_matrix(gen, d1, d_in, scale=2.0, dtype=dtype),
            _rand_init_matrix(gen, d2, d1, scale=1.9, dtype=dtype),
            _rand_init_matrix(gen, d2, d1, scale=1.9, dtype=dtype),
            _rand_init_matrix(gen, n_cls, d2, scale=2.2, dtype=dtype),
        ]
        tmp = NeuralTargetTaskV3("tmp", family, "cross_entropy", "bilinear_gated_cls", "tanh", teacher, {}, X_all, X_all, X_all, X_all)
        with torch.no_grad():
            y_all = forward_target_v3(tmp, teacher, X_all)[0].argmax(dim=-1)
        Y_sup = y_all[:n_sup].clone()
        flip = torch.rand(n_sup, generator=gen) < 0.12
        Y_sup[flip] = torch.randint(0, n_cls, (int(flip.sum().item()),), generator=gen)
        Y_qry = y_all[n_sup:]
        init_layers = [
            _rand_init_matrix(gen, d1, d_in, scale=1.8, dtype=dtype),
            _rand_init_matrix(gen, d1, d_in, scale=0.55, dtype=dtype),
            _rand_init_matrix(gen, d2, d1, scale=0.60, dtype=dtype),
            _rand_init_matrix(gen, d2, d1, scale=1.75, dtype=dtype),
            _rand_init_matrix(gen, n_cls, d2, scale=0.50, dtype=dtype),
        ]
        return NeuralTargetTaskV3(
            task_id=f"{family}-{seed}",
            family=family,
            loss_type="cross_entropy",
            arch_kind="bilinear_gated_cls",
            activation="tanh",
            init_layers=init_layers,
            aux_tensors={},
            X_sup=X_all[:n_sup],
            Y_sup=Y_sup,
            X_qry=X_all[n_sup:],
            Y_qry=Y_qry,
            budget=10,
        )

    # Family 4: layernorm_residual_gelu_cls
    d_in, d_res, n_cls = 24, 28, 6
    n_sup, n_qry = 56, 144
    X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, log10_span=1.45, dtype=dtype)
    teacher = [
        _rand_init_matrix(gen, d_res, d_in, scale=2.0, dtype=dtype),
        _rand_init_matrix(gen, d_res, d_res, scale=1.8, dtype=dtype),
        _rand_init_matrix(gen, d_res, d_res, scale=1.8, dtype=dtype),
        _rand_init_matrix(gen, d_res, d_res, scale=1.8, dtype=dtype),
        _rand_init_matrix(gen, n_cls, d_res, scale=2.2, dtype=dtype),
    ]
    tmp = NeuralTargetTaskV3("tmp", family, "cross_entropy", "layernorm_res_gelu_cls", "gelu", teacher, {}, X_all, X_all, X_all, X_all)
    with torch.no_grad():
        y_all = forward_target_v3(tmp, teacher, X_all)[0].argmax(dim=-1)
    Y_sup = y_all[:n_sup].clone()
    flip = torch.rand(n_sup, generator=gen) < 0.12
    Y_sup[flip] = torch.randint(0, n_cls, (int(flip.sum().item()),), generator=gen)
    Y_qry = y_all[n_sup:]
    init_layers = [
        _rand_init_matrix(gen, d_res, d_in, scale=1.9, dtype=dtype),
        _rand_init_matrix(gen, d_res, d_res, scale=0.40, dtype=dtype),
        _rand_init_matrix(gen, d_res, d_res, scale=1.60, dtype=dtype),
        _rand_init_matrix(gen, d_res, d_res, scale=0.40, dtype=dtype),
        _rand_init_matrix(gen, n_cls, d_res, scale=0.55, dtype=dtype),
    ]
    return NeuralTargetTaskV3(
        task_id=f"{family}-{seed}",
        family=family,
        loss_type="cross_entropy",
        arch_kind="layernorm_res_gelu_cls",
        activation="gelu",
        init_layers=init_layers,
        aux_tensors={},
        X_sup=X_all[:n_sup],
        Y_sup=Y_sup,
        X_qry=X_all[n_sup:],
        Y_qry=Y_qry,
        budget=10,
    )
