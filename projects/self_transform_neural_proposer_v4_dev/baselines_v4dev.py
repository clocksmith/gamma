"""DEVELOPMENT COPY of `self_transform_neural_proposer_v3/baselines_v3.py` (sealed original untouched).

Edits relative to the sealed file (everything else is byte-identical, see `test_identity_v4dev.py`):
- imports come from `proposer_v4dev` instead of `proposer_v3`;
- `build_progressive_meta_task_v3` became `build_upstream_task_dev(raw_seed, gen_idx, task_idx)`:
  same four task generators, but the RNG seed is passed in directly and must be a development
  seed (`>= DEV_SEED_FLOOR`), so no v3 upstream / calibration / confirmation seed can be reused;
- `build_shared_val_anchor_v3`, `measure_mean_curriculum_pass_flops` and `calibrate_all_baselines_v3`
  were removed (they are tied to the v3 seed formulas); calibration lives in `common_v4dev.py`.

Original v3 docstring follows.

Charged target oracle, upstream meta-curriculum, and all 6 matched-budget baselines for B2 v3.

Includes:
- `ChargedTargetOracleV3`: bills every `forward_backward_support` pass (`B = 10`) AND bills `+1` pass
  for every `evaluate_diff_query` meta-query evaluation (`11` passes per meta-train task).
- Six cold-target baselines calibrated beforehand per lineage seed on upstream calibration tasks at
  both the `exact`-matched budget (`1,200 * g >= 1,160 * g` passes) and the `regen`-matched budget
  (`1,400 * g >= (1,160 + ceil(regen_flops / mean_target_pass_flops)) * g` pass-equivalents):
  1. `sgd_nesterov`
  2. `adamw_cosine`
  3. `damped_lbfgs`
  4. `zero_head_adam` (`layers[-1]` zeroed at `t = 0`, then AdamW with cosine decay)
  5. `constant_step_rule` (constant scalar step-size + momentum rule without proposer network)
  6. `kfac_no_proposer` (exact same 5-basis Woodbury K-FAC + Newton-Schulz + Adam preconditioning
     and cosine step schedule without the neural proposer network `Phi`)
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import random
import statistics
import sys
from typing import Any
import torch
import torch.nn.functional as F

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from proposer_v4dev import (
    ProposerWeightsV3,
    compute_five_basis_v3,
    init_opt_state_v3,
    propose_update_v3,
)

PROPOSER_EXACT_PASSES_PER_GEN = 1160  # 120 parent-anchor + 5 * (8 * 11 meta-train + 120 anchor)
CONV_EXACT_MATCHED_PASSES_PER_GEN = 1200  # 12 configs/gen * 10 cal tasks * 10 passes >= 1160
CONV_REGEN_MATCHED_PASSES_PER_GEN = 1400  # 14 configs/gen * 10 cal tasks * 10 passes >= 1365


class OracleBudgetExceededError(RuntimeError):
    """Raised immediately if any learned or conventional optimizer exceeds its pass budget."""


@dataclass
class NeuralTargetTaskV3:
    task_id: str
    family: str
    loss_type: str                        # 'cross_entropy' | 'mse'
    arch_kind: str
    activation: str
    init_layers: list[torch.Tensor]       # trainable homogeneous matrices W_l in R^{d_out x (d_in + 1)}
    aux_tensors: dict[str, torch.Tensor]
    X_sup: torch.Tensor
    Y_sup: torch.Tensor
    X_qry: torch.Tensor
    Y_qry: torch.Tensor
    budget: int = 10

    def clone_cold_layers(self, requires_grad: bool = True) -> list[torch.Tensor]:
        return [w.detach().clone().requires_grad_(requires_grad) for w in self.init_layers]

    def estimate_single_support_pass_flops(self) -> int:
        n_sup = int(self.X_sup.shape[0])
        trainable_macs = sum(int(w.numel()) for w in self.init_layers)
        # Forward (2 * N * P) + Backward wrt weights & pre-activations (4 * N * P) = 6 * N * P FLOPs
        return int(6 * n_sup * trainable_macs)


def _hom(x: torch.Tensor) -> torch.Tensor:
    ones = torch.ones((x.shape[0], 1), dtype=x.dtype, device=x.device)
    return torch.cat([x, ones], dim=-1)


def _apply_act(z: torch.Tensor, act: str) -> torch.Tensor:
    if act == "tanh":
        return torch.tanh(z)
    if act == "gelu":
        return F.gelu(z)
    if act == "silu":
        return F.silu(z)
    if act == "leaky_relu":
        return F.leaky_relu(z, negative_slope=0.1)
    if act == "softplus":
        return F.softplus(z) - math.log(2.0)
    if act == "celu":
        return F.celu(z)
    raise ValueError(f"Unsupported activation: {act}")


def _linear_step(
    h: torch.Tensor,
    W: torch.Tensor,
    act_inputs: list[torch.Tensor],
    preacts: list[torch.Tensor],
    retain_preacts: bool,
) -> torch.Tensor:
    a_hom = _hom(h)
    z = a_hom @ W.T
    if retain_preacts:
        z.retain_grad()
    act_inputs.append(a_hom.detach())
    preacts.append(z)
    return z


def _layer_norm_noaffine(h: torch.Tensor, eps: float = 1e-5) -> torch.Tensor:
    mean = h.mean(dim=-1, keepdim=True)
    var = (h - mean).pow(2).mean(dim=-1, keepdim=True)
    return (h - mean) * torch.rsqrt(var + eps)


def forward_target_v3(
    task: NeuralTargetTaskV3,
    layers: list[torch.Tensor],
    X: torch.Tensor,
    retain_preacts: bool = False,
) -> tuple[torch.Tensor, list[torch.Tensor], list[torch.Tensor]]:
    """Forward `X` through `task` using `layers`, returning `(outputs, act_inputs, preacts)`."""
    act_inputs: list[torch.Tensor] = []
    preacts: list[torch.Tensor] = []
    kind = task.arch_kind

    if kind == "mlp_act":
        h = X
        L = len(layers)
        for idx, W in enumerate(layers):
            z = _linear_step(h, W, act_inputs, preacts, retain_preacts)
            h = z if idx == L - 1 else _apply_act(z, task.activation)
        return h, act_inputs, preacts

    if kind == "synth_frozen_readout_lora":
        # Upstream synthetic zero-init LoRA adapter [A_lora, B_lora] with frozen readout
        d_in = int(task.aux_tensors["d_in"].item())
        h_in = X[:, :d_in]
        y_base = X[:, d_in:]
        W_readout = task.aux_tensors["W_readout"]
        z_a = _linear_step(h_in, layers[0], act_inputs, preacts, retain_preacts)
        dy = _linear_step(z_a, layers[1], act_inputs, preacts, retain_preacts)
        y = y_base + 0.50 * dy
        y_n = y * torch.rsqrt(y.pow(2).mean(dim=-1, keepdim=True) + 1e-6)
        logits = y_n @ W_readout.T
        return logits, act_inputs, preacts

    if kind == "qwen35_full_down_lora":
        # Full-width stock Qwen/Qwen3.5-0.8B Layer-23 SwiGLU down_proj LoRA + RMSNorm + unembedding readout
        d_ff = int(task.aux_tensors["d_ff"].item())
        m0 = X[:, :d_ff]
        y0 = X[:, d_ff:]
        ln_final_w = task.aux_tensors["ln_final_w"]
        U_verb = task.aux_tensors["U_verb"]
        lora_alpha = float(task.aux_tensors["lora_alpha"].item())
        z_a = _linear_step(m0, layers[0], act_inputs, preacts, retain_preacts)
        dy = _linear_step(z_a, layers[1], act_inputs, preacts, retain_preacts)
        y = y0 + lora_alpha * dy
        yn = (1.0 + ln_final_w) * y * torch.rsqrt(y.pow(2).mean(dim=-1, keepdim=True) + 1e-6)
        logits = yn @ U_verb.T
        return logits, act_inputs, preacts

    if kind == "fourier_kan_reg":
        # Fourier-basis + SiLU residual KAN regression: layers = [W_sin, W_cos, W_res, W_mix, W_out]
        assert len(layers) == 5
        z_sin = _linear_step(X, layers[0], act_inputs, preacts, retain_preacts)
        z_cos = _linear_step(X, layers[1], act_inputs, preacts, retain_preacts)
        z_res = _linear_step(X, layers[2], act_inputs, preacts, retain_preacts)
        basis = torch.cat([torch.sin(z_sin), torch.cos(z_cos), F.silu(z_res)], dim=-1)
        h_mix = F.silu(_linear_step(basis, layers[3], act_inputs, preacts, retain_preacts))
        out = _linear_step(h_mix, layers[4], act_inputs, preacts, retain_preacts)
        return out, act_inputs, preacts

    if kind == "bilinear_gated_cls":
        # Multiplicative bilinear interaction classifier: layers = [W_a1, W_b1, W_a2, W_b2, W_cls]
        assert len(layers) == 5
        za1 = _linear_step(X, layers[0], act_inputs, preacts, retain_preacts)
        zb1 = _linear_step(X, layers[1], act_inputs, preacts, retain_preacts)
        h1 = za1 * torch.tanh(zb1)
        za2 = _linear_step(h1, layers[2], act_inputs, preacts, retain_preacts)
        zb2 = _linear_step(h1, layers[3], act_inputs, preacts, retain_preacts)
        h2 = za2 * torch.tanh(zb2)
        logits = _linear_step(h2, layers[4], act_inputs, preacts, retain_preacts)
        return logits, act_inputs, preacts

    if kind == "layernorm_res_gelu_cls":
        # Pre-LayerNorm residual deep GELU classifier: layers = [W_in, W_r1, W_r2, W_r3, W_cls]
        assert len(layers) == 5
        h = F.gelu(_linear_step(X, layers[0], act_inputs, preacts, retain_preacts))
        for b_idx in (1, 2, 3):
            h_ln = _layer_norm_noaffine(h)
            h = h + F.gelu(_linear_step(h_ln, layers[b_idx], act_inputs, preacts, retain_preacts))
        h_final = _layer_norm_noaffine(h)
        logits = _linear_step(h_final, layers[4], act_inputs, preacts, retain_preacts)
        return logits, act_inputs, preacts

    raise ValueError(f"Unknown arch_kind: {kind}")


def compute_task_loss_v3(task: NeuralTargetTaskV3, preds: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    if task.loss_type == "cross_entropy":
        return F.cross_entropy(preds, targets)
    return F.mse_loss(preds, targets)


def smooth_multiclass_hinge(logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    n = logits.shape[0]
    idx = torch.arange(n, device=logits.device)
    z_true = logits[idx, targets]
    mask = torch.ones_like(logits, dtype=torch.bool)
    mask[idx, targets] = False
    z_other_max = logits.masked_fill(~mask, -1e9).max(dim=-1).values
    return F.softplus(1.0 - (z_true - z_other_max), beta=2.0).mean()


class ChargedTargetOracleV3:
    """Enforces exact pass accounting on both support passes and differentiable meta-query passes."""

    def __init__(self, task: NeuralTargetTaskV3, allow_meta_query_pass: bool = False):
        self.task = task
        self.support_budget = int(task.budget)
        self.max_total_passes = self.support_budget + (1 if allow_meta_query_pass else 0)
        self.support_passes_used = 0
        self.passes_used = 0

    def forward_backward_support(
        self,
        layers: list[torch.Tensor],
        differentiable_graph: bool = False,
    ) -> tuple[torch.Tensor, list[torch.Tensor], list[torch.Tensor], list[torch.Tensor]]:
        if self.support_passes_used >= self.support_budget or self.passes_used >= self.max_total_passes:
            raise OracleBudgetExceededError(
                f"Task {self.task.task_id}: exceeded support pass budget {self.support_budget}"
            )
        self.support_passes_used += 1
        self.passes_used += 1

        leaf_layers = [w if w.requires_grad else w.detach().clone().requires_grad_(True) for w in layers]
        preds, act_inputs, preacts = forward_target_v3(
            self.task, leaf_layers, self.task.X_sup, retain_preacts=True
        )
        loss = compute_task_loss_v3(self.task, preds, self.task.Y_sup)
        all_grads = torch.autograd.grad(
            loss,
            leaf_layers + preacts,
            create_graph=differentiable_graph,
            retain_graph=differentiable_graph,
        )
        n_l = len(leaf_layers)
        w_grads = list(all_grads[:n_l])
        e_outs = [g.detach() * float(self.task.X_sup.shape[0]) for g in all_grads[n_l:]]
        return loss, w_grads, act_inputs, e_outs

    def evaluate_diff_query_v3(self, layers: list[torch.Tensor], init_query_loss: float) -> torch.Tensor:
        """Differentiable meta-query evaluation, explicitly billed (`+1` pass) inside `ChargedTargetOracleV3`."""
        if self.passes_used >= self.max_total_passes:
            raise OracleBudgetExceededError(
                f"Task {self.task.task_id}: exceeded total pass budget {self.max_total_passes}"
            )
        self.passes_used += 1
        preds_q, _, _ = forward_target_v3(self.task, layers, self.task.X_qry, retain_preacts=False)
        raw_loss = compute_task_loss_v3(self.task, preds_q, self.task.Y_qry)
        norm_r = raw_loss / max(init_query_loss, 1e-4)
        smooth_r = 3.0 * torch.tanh(norm_r / 3.0)
        if self.task.loss_type == "cross_entropy":
            hinge = smooth_multiclass_hinge(preds_q, self.task.Y_qry)
            return 0.75 * smooth_r + 0.25 * (3.0 * torch.tanh(hinge / 3.0))
        return smooth_r

    @torch.no_grad()
    def evaluate_query(self, layers: list[torch.Tensor]) -> dict[str, float]:
        clean = [w.detach() for w in layers]
        preds_q, _, _ = forward_target_v3(self.task, clean, self.task.X_qry, retain_preacts=False)
        preds_s, _, _ = forward_target_v3(self.task, clean, self.task.X_sup, retain_preacts=False)
        ql = float(compute_task_loss_v3(self.task, preds_q, self.task.Y_qry).item())
        sl = float(compute_task_loss_v3(self.task, preds_s, self.task.Y_sup).item())
        out = {"query_loss": ql, "support_loss": sl, "passes_used": self.passes_used}
        if self.task.loss_type == "cross_entropy":
            out["query_accuracy"] = float((preds_q.argmax(dim=-1) == self.task.Y_qry).float().mean().item())
            out["query_hinge"] = float(smooth_multiclass_hinge(preds_q, self.task.Y_qry).item())
        else:
            out["query_r2"] = 1.0 - ql / float(self.task.Y_qry.var().clamp_min(1e-8).item())
        return out


def normalized_loss_ratio(row: dict[str, Any]) -> float:
    ql = float(row["final_query_loss"])
    il = max(float(row["init_query_loss"]), 1e-6)
    if not math.isfinite(ql):
        return 10.0
    return min(10.0, ql / il)


def smooth_anchor_score(res: dict[str, float], loss_type: str) -> float:
    """Co-primary smooth validation/calibration objective shared by `M_Phi_v3` and all 6 baselines."""
    ql = float(res["final_query_loss"])
    il = max(float(res["init_query_loss"]), 1e-6)
    if not math.isfinite(ql):
        return 4.0
    r = min(ql / il, 4.0)
    if loss_type == "cross_entropy":
        h = min(float(res.get("query_hinge", r)), 4.0)
        return 0.75 * r + 0.25 * h
    return r


def _rand_init_matrix(gen: torch.Generator, d_out: int, d_in: int, scale: float = 1.0, dtype=torch.float64) -> torch.Tensor:
    std = scale / math.sqrt(max(1, d_in))
    W = std * torch.randn((d_out, d_in + 1), generator=gen, dtype=dtype)
    W[:, -1] *= 0.1
    return W


def _anisotropic_inputs(gen: torch.Generator, n: int, d: int, log10_span: float, dtype=torch.float64) -> torch.Tensor:
    raw = torch.randn((n, d), generator=gen, dtype=dtype)
    exps = torch.linspace(-log10_span, log10_span, d, dtype=dtype)
    scales = (10.0 ** exps)[torch.randperm(d, generator=gen)]
    q_mat, _ = torch.linalg.qr(torch.randn((d, d), generator=gen, dtype=dtype))
    return (raw * scales.unsqueeze(0)) @ q_mat.T


DEV_SEED_FLOOR = 20_000_000  # every v3 seed is <= 9,863,011 (see common_v4dev.SEED_PLAN)


def build_upstream_task_dev(
    raw_seed: int,
    gen_idx: int,
    task_idx: int,
    dtype: torch.dtype = torch.float64,
) -> NeuralTargetTaskV3:
    """v3 upstream task generators (4 modes) driven by an explicit development seed."""
    s = int(raw_seed)
    assert s >= DEV_SEED_FLOOR, f"Development seed {s} must be >= {DEV_SEED_FLOOR} (disjoint from all v3 seeds)"
    lineage_seed = s  # only used in task_id strings below
    gen = torch.Generator(device="cpu")
    gen.manual_seed(s)
    mode = task_idx % 4

    if mode == 0:
        # Synthetic frozen-readout zero-init rank-6 LoRA task (strictly synthetic leaky_relu, 48->32)
        d_in, d_out, r, n_cls = 48, 32, 6, 5
        n_sup, n_qry = 52, 112
        h_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, 1.15 + 0.08 * gen_idx, dtype)
        W_base = (0.35 / math.sqrt(d_in)) * torch.randn((d_out, d_in), generator=gen, dtype=dtype)
        act_h = F.leaky_relu(h_all, negative_slope=0.1)
        y_base = act_h @ W_base.T
        X_all = torch.cat([act_h, y_base], dim=-1)
        W_readout = (2.6 / math.sqrt(d_out)) * torch.randn((n_cls, d_out), generator=gen, dtype=dtype)
        aux = {"d_in": torch.tensor(d_in), "W_readout": W_readout}

        t_A = _rand_init_matrix(gen, r, d_in, 1.8, dtype)
        t_B = _rand_init_matrix(gen, d_out, r, 2.2, dtype)
        tmp = NeuralTargetTaskV3(
            "m", "meta_synth_lora", "cross_entropy", "synth_frozen_readout_lora",
            "leaky_relu", [t_A, t_B], aux, X_all, X_all, X_all, X_all,
        )
        with torch.no_grad():
            y_all = forward_target_v3(tmp, [t_A, t_B], X_all)[0].argmax(dim=-1)
        Y_sup = y_all[:n_sup].clone()
        flip = torch.rand(n_sup, generator=gen) < 0.08
        Y_sup[flip] = torch.randint(0, n_cls, (int(flip.sum().item()),), generator=gen)

        init_A = _rand_init_matrix(gen, r, d_in, 1.0, dtype)
        init_A[:, -1] = 0.0
        init_B = torch.zeros((d_out, r + 1), dtype=dtype)
        return NeuralTargetTaskV3(
            task_id=f"meta-lora-s{lineage_seed}-g{gen_idx}-t{task_idx}",
            family="meta_synth_lora",
            loss_type="cross_entropy",
            arch_kind="synth_frozen_readout_lora",
            activation="leaky_relu",
            init_layers=[init_A, init_B],
            aux_tensors=aux,
            X_sup=X_all[:n_sup],
            Y_sup=Y_sup,
            X_qry=X_all[n_sup:],
            Y_qry=y_all[n_sup:],
            budget=10,
        )

    if mode == 1:
        # Anisotropic noisy multi-class MLP
        d_in, d_h, n_cls = 16, 24, 5
        n_sup, n_qry = 48, 112
        act = "tanh" if (gen_idx % 2 == 0) else "silu"
        X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, 1.20 + 0.10 * gen_idx, dtype)
        t_layers = [
            _rand_init_matrix(gen, d_h, d_in, 2.0, dtype),
            _rand_init_matrix(gen, d_h, d_h, 1.8, dtype),
            _rand_init_matrix(gen, n_cls, d_h, 2.2, dtype),
        ]
        tmp = NeuralTargetTaskV3("m", "meta_mlp_cls", "cross_entropy", "mlp_act", act, t_layers, {}, X_all, X_all, X_all, X_all)
        with torch.no_grad():
            y_all = forward_target_v3(tmp, t_layers, X_all)[0].argmax(dim=-1)
        Y_sup = y_all[:n_sup].clone()
        flip = torch.rand(n_sup, generator=gen) < (0.12 + 0.03 * min(gen_idx, 3))
        Y_sup[flip] = torch.randint(0, n_cls, (int(flip.sum().item()),), generator=gen)
        init_layers = [
            _rand_init_matrix(gen, d_h, d_in, 1.6, dtype),
            _rand_init_matrix(gen, d_h, d_h, 0.6, dtype),
            _rand_init_matrix(gen, n_cls, d_h, 0.5, dtype),
        ]
        return NeuralTargetTaskV3(
            task_id=f"meta-cls-s{lineage_seed}-g{gen_idx}-t{task_idx}",
            family="meta_mlp_cls",
            loss_type="cross_entropy",
            arch_kind="mlp_act",
            activation=act,
            init_layers=init_layers,
            aux_tensors={},
            X_sup=X_all[:n_sup],
            Y_sup=Y_sup,
            X_qry=X_all[n_sup:],
            Y_qry=y_all[n_sup:],
            budget=10,
        )

    if mode == 2:
        # Ill-conditioned multi-output regression
        d_in, d_h, d_out = 14, 22, 3
        n_sup, n_qry = 48, 112
        act = "softplus" if (task_idx % 8 == 2) else "tanh"
        X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, 1.25 + 0.10 * gen_idx, dtype)
        t_layers = [
            _rand_init_matrix(gen, d_h, d_in, 2.1, dtype),
            _rand_init_matrix(gen, d_h, d_h, 1.9, dtype),
            _rand_init_matrix(gen, d_out, d_h, 1.9, dtype),
        ]
        tmp = NeuralTargetTaskV3("m", "meta_mlp_reg", "mse", "mlp_act", act, t_layers, {}, X_all, X_all, X_all, X_all)
        with torch.no_grad():
            raw = forward_target_v3(tmp, t_layers, X_all)[0]
            y_all = raw / raw.std().clamp_min(1e-6)
        Y_sup = y_all[:n_sup] + 0.16 * torch.randn((n_sup, d_out), generator=gen, dtype=dtype)
        init_layers = [
            _rand_init_matrix(gen, d_h, d_in, 1.7, dtype),
            _rand_init_matrix(gen, d_h, d_h, 0.55, dtype),
            _rand_init_matrix(gen, d_out, d_h, 0.45, dtype),
        ]
        return NeuralTargetTaskV3(
            task_id=f"meta-reg-s{lineage_seed}-g{gen_idx}-t{task_idx}",
            family="meta_mlp_reg",
            loss_type="mse",
            arch_kind="mlp_act",
            activation=act,
            init_layers=init_layers,
            aux_tensors={},
            X_sup=X_all[:n_sup],
            Y_sup=Y_sup,
            X_qry=X_all[n_sup:],
            Y_qry=y_all[n_sup:],
            budget=10,
        )

    # Mode 3: 4-layer mismatched-scale CELU classifier
    dims = [18, 20, 20, 20, 5]
    n_sup, n_qry = 50, 112
    X_all = _anisotropic_inputs(gen, n_sup + n_qry, dims[0], 1.20 + 0.08 * gen_idx, dtype)
    t_layers = [_rand_init_matrix(gen, dims[i + 1], dims[i], 1.9, dtype) for i in range(4)]
    tmp = NeuralTargetTaskV3("m", "meta_deep_cls", "cross_entropy", "mlp_act", "celu", t_layers, {}, X_all, X_all, X_all, X_all)
    with torch.no_grad():
        y_all = forward_target_v3(tmp, t_layers, X_all)[0].argmax(dim=-1)
    Y_sup = y_all[:n_sup].clone()
    flip = torch.rand(n_sup, generator=gen) < 0.12
    Y_sup[flip] = torch.randint(0, dims[-1], (int(flip.sum().item()),), generator=gen)
    scales = [2.0, 0.45, 1.8, 0.40]
    init_layers = [_rand_init_matrix(gen, dims[i + 1], dims[i], scales[i], dtype) for i in range(4)]
    return NeuralTargetTaskV3(
        task_id=f"meta-deep-s{lineage_seed}-g{gen_idx}-t{task_idx}",
        family="meta_deep_cls",
        loss_type="cross_entropy",
        arch_kind="mlp_act",
        activation="celu",
        init_layers=init_layers,
        aux_tensors={},
        X_sup=X_all[:n_sup],
        Y_sup=Y_sup,
        X_qry=X_all[n_sup:],
        Y_qry=y_all[n_sup:],
        budget=10,
    )


def run_proposer_v3_cold(phi: ProposerWeightsV3, task: NeuralTargetTaskV3) -> dict[str, float]:
    """Evaluate `M_Phi_v3` on a fresh cold target network with `opt_state = None` (`B = 10` support passes)."""
    oracle = ChargedTargetOracleV3(task, allow_meta_query_pass=False)
    phi_clean = phi.clone_detached(requires_grad=False)
    layers = task.clone_cold_layers(requires_grad=False)
    init_m = oracle.evaluate_query(layers)
    opt_state = init_opt_state_v3(layers)
    B = oracle.support_budget
    for s_idx in range(B):
        loss_s, grads_s, act_in, err_out = oracle.forward_backward_support(layers, differentiable_graph=False)
        with torch.no_grad():
            layers = propose_update_v3(
                phi=phi_clean,
                layers=[w.detach() for w in layers],
                grads=[g.detach() for g in grads_s],
                act_inputs=act_in,
                err_outputs=err_out,
                opt_state=opt_state,
                step_idx=s_idx,
                total_steps=B,
                cur_loss=loss_s.detach(),
                capture_self_acts=None,
                differentiable_target=False,
            )
    fin_m = oracle.evaluate_query(layers)
    assert oracle.passes_used == B
    return {
        "init_query_loss": init_m["query_loss"],
        "final_query_loss": fin_m["query_loss"],
        "final_support_loss": fin_m["support_loss"],
        "query_accuracy": fin_m.get("query_accuracy", 0.0),
        "query_hinge": fin_m.get("query_hinge", 0.0),
        "query_r2": fin_m.get("query_r2", 0.0),
        "passes_used": oracle.passes_used,
    }


def _pack_flat(layers: list[torch.Tensor]) -> torch.Tensor:
    return torch.cat([w.detach().reshape(-1) for w in layers])


def _unpack_flat(flat: torch.Tensor, template: list[torch.Tensor]) -> list[torch.Tensor]:
    out = []
    off = 0
    for w in template:
        n = w.numel()
        out.append(flat[off : off + n].reshape(w.shape).clone())
        off += n
    return out


def _weight_decay_mask(template: list[torch.Tensor]) -> torch.Tensor:
    masks = []
    for w in template:
        m = torch.ones_like(w.detach())
        m[:, -1] = 0.0
        masks.append(m.reshape(-1))
    return torch.cat(masks)


def run_sgd_nesterov_v3(cfg: dict[str, Any], task: NeuralTargetTaskV3) -> dict[str, float]:
    oracle = ChargedTargetOracleV3(task)
    layers = task.clone_cold_layers(requires_grad=False)
    init_m = oracle.evaluate_query(layers)
    lr, mom, wd = float(cfg["lr"]), float(cfg["momentum"]), float(cfg["weight_decay"])
    wd_mask = _weight_decay_mask(layers)
    theta = _pack_flat(layers)
    vel = torch.zeros_like(theta)
    B = oracle.support_budget
    for step_idx in range(B):
        _, grads, _, _ = oracle.forward_backward_support(_unpack_flat(theta, layers), differentiable_graph=False)
        g = _pack_flat(grads) + wd * wd_mask * theta
        gn = float(g.norm().item())
        if gn > 20.0:
            g = g * (20.0 / gn)
        lr_t = lr * (0.25 + 0.75 * 0.5 * (1.0 + math.cos(math.pi * step_idx / max(1, B - 1))))
        vel = mom * vel + g
        theta = theta - lr_t * (g + mom * vel)
    fin_m = oracle.evaluate_query(_unpack_flat(theta, layers))
    assert oracle.passes_used == B
    return {
        "init_query_loss": init_m["query_loss"],
        "final_query_loss": fin_m["query_loss"],
        "final_support_loss": fin_m["support_loss"],
        "query_accuracy": fin_m.get("query_accuracy", 0.0),
        "query_hinge": fin_m.get("query_hinge", 0.0),
        "query_r2": fin_m.get("query_r2", 0.0),
        "passes_used": oracle.passes_used,
    }


def _run_adamw_core(cfg: dict[str, Any], task: NeuralTargetTaskV3, zero_head: bool) -> dict[str, float]:
    oracle = ChargedTargetOracleV3(task)
    layers = task.clone_cold_layers(requires_grad=False)
    init_m = oracle.evaluate_query(layers)
    if zero_head:
        layers[-1] = torch.zeros_like(layers[-1])
    lr = float(cfg["lr"])
    b1 = float(cfg.get("beta1", 0.85))
    b2 = float(cfg.get("beta2", 0.96))
    wd = float(cfg["weight_decay"])
    wd_mask = _weight_decay_mask(layers)
    theta = _pack_flat(layers)
    m_t = torch.zeros_like(theta)
    v_t = torch.zeros_like(theta)
    B = oracle.support_budget
    for step_idx in range(B):
        t = step_idx + 1
        _, grads, _, _ = oracle.forward_backward_support(_unpack_flat(theta, layers), differentiable_graph=False)
        g = _pack_flat(grads)
        m_t = b1 * m_t + (1.0 - b1) * g
        v_t = b2 * v_t + (1.0 - b2) * (g * g)
        m_hat = m_t / (1.0 - b1 ** t)
        v_hat = v_t / (1.0 - b2 ** t)
        lr_t = lr * (0.20 + 0.80 * 0.5 * (1.0 + math.cos(math.pi * step_idx / max(1, B - 1))))
        theta = theta * (1.0 - lr_t * wd * wd_mask) - lr_t * (m_hat / (v_hat.sqrt() + 1e-8))
    fin_m = oracle.evaluate_query(_unpack_flat(theta, layers))
    assert oracle.passes_used == B
    return {
        "init_query_loss": init_m["query_loss"],
        "final_query_loss": fin_m["query_loss"],
        "final_support_loss": fin_m["support_loss"],
        "query_accuracy": fin_m.get("query_accuracy", 0.0),
        "query_hinge": fin_m.get("query_hinge", 0.0),
        "query_r2": fin_m.get("query_r2", 0.0),
        "passes_used": oracle.passes_used,
    }


def run_adamw_cosine_v3(cfg: dict[str, Any], task: NeuralTargetTaskV3) -> dict[str, float]:
    return _run_adamw_core(cfg, task, zero_head=False)


def run_zero_head_adam_v3(cfg: dict[str, Any], task: NeuralTargetTaskV3) -> dict[str, float]:
    """`layers[-1]` zeroed at `t = 0`, followed by pre-calibrated AdamW with cosine decay."""
    return _run_adamw_core(cfg, task, zero_head=True)


def run_damped_lbfgs_v3(cfg: dict[str, Any], task: NeuralTargetTaskV3) -> dict[str, float]:
    oracle = ChargedTargetOracleV3(task)
    layers = task.clone_cold_layers(requires_grad=False)
    init_m = oracle.evaluate_query(layers)
    lr = float(cfg["lr"])
    damp = float(cfg["damping"])
    wd = float(cfg["weight_decay"])
    max_step = float(cfg["max_step"])
    wd_mask = _weight_decay_mask(layers)
    theta = _pack_flat(layers)
    loss0, grads0, _, _ = oracle.forward_backward_support(_unpack_flat(theta, layers), differentiable_graph=False)
    f_cur = float(loss0.item()) + 0.5 * wd * float((wd_mask * theta * theta).sum().item())
    g_cur = _pack_flat(grads0) + wd * wd_mask * theta
    s_hist: list[torch.Tensor] = []
    y_hist: list[torch.Tensor] = []
    rho_hist: list[float] = []
    while oracle.passes_used < oracle.support_budget:
        q = g_cur.clone()
        alphas: list[float] = []
        for s_i, y_i, r_i in zip(reversed(s_hist), reversed(y_hist), reversed(rho_hist)):
            a_i = r_i * float((s_i * q).sum().item())
            alphas.append(a_i)
            q = q - a_i * y_i
        if s_hist:
            sy = float((s_hist[-1] * y_hist[-1]).sum().item())
            yy = float((y_hist[-1] * y_hist[-1]).sum().item())
            gamma = max(0.05, min(5.0, sy / max(yy, 1e-12)))
        else:
            gamma = 1.0 / max(float(g_cur.norm().item()), 1.0)
        r = (gamma / (1.0 + damp)) * q
        for (s_i, y_i, r_i), a_i in zip(zip(s_hist, y_hist, rho_hist), reversed(alphas)):
            b_i = r_i * float((y_i * r).sum().item())
            r = r + s_i * (a_i - b_i)
        step_vec = -lr * r
        sn = float(step_vec.norm().item())
        if sn > max_step:
            step_vec = step_vec * (max_step / sn)
        cand_theta = theta + step_vec
        cl, cg, _, _ = oracle.forward_backward_support(_unpack_flat(cand_theta, layers), differentiable_graph=False)
        f_cand = float(cl.item()) + 0.5 * wd * float((wd_mask * cand_theta * cand_theta).sum().item())
        g_cand = _pack_flat(cg) + wd * wd_mask * cand_theta
        if math.isfinite(f_cand) and f_cand <= f_cur + 0.15 * abs(f_cur) + 0.05:
            s_k = cand_theta - theta
            y_k = g_cand - g_cur + damp * s_k
            sy_k = float((s_k * y_k).sum().item())
            if sy_k > 1e-10:
                if len(s_hist) >= 5:
                    s_hist.pop(0)
                    y_hist.pop(0)
                    rho_hist.pop(0)
                s_hist.append(s_k)
                y_hist.append(y_k)
                rho_hist.append(1.0 / sy_k)
            theta, f_cur, g_cur = cand_theta, f_cand, g_cand
        else:
            lr *= 0.45
    fin_m = oracle.evaluate_query(_unpack_flat(theta, layers))
    assert oracle.passes_used == oracle.support_budget
    return {
        "init_query_loss": init_m["query_loss"],
        "final_query_loss": fin_m["query_loss"],
        "final_support_loss": fin_m["support_loss"],
        "query_accuracy": fin_m.get("query_accuracy", 0.0),
        "query_hinge": fin_m.get("query_hinge", 0.0),
        "query_r2": fin_m.get("query_r2", 0.0),
        "passes_used": oracle.passes_used,
    }


def run_constant_step_rule_v3(cfg: dict[str, Any], task: NeuralTargetTaskV3) -> dict[str, float]:
    """Constant scalar step-size + momentum rule without proposer network or schedule."""
    oracle = ChargedTargetOracleV3(task)
    layers = task.clone_cold_layers(requires_grad=False)
    init_m = oracle.evaluate_query(layers)
    st = init_opt_state_v3(layers)
    lr = float(cfg["lr"])
    mom = float(cfg["momentum"])
    wd = float(cfg["weight_decay"])
    moms = [torch.zeros_like(w) for w in layers]
    B = oracle.support_budget
    for _ in range(B):
        _, grads, _, _ = oracle.forward_backward_support(layers, differentiable_graph=False)
        new_layers = []
        for l_idx, W in enumerate(layers):
            g = grads[l_idx].detach()
            moms[l_idx] = mom * moms[l_idx] + (1.0 - mom) * g
            d_unit = moms[l_idx] / (moms[l_idx].pow(2).mean() + 1e-16).sqrt()
            eta = lr * float(st["base_scales"][l_idx])
            sm = torch.ones((1, W.shape[1]), dtype=W.dtype, device=W.device)
            sm[0, -1] = 0.0
            new_layers.append(W - eta * d_unit - wd * sm * W)
        layers = new_layers
    fin_m = oracle.evaluate_query(layers)
    assert oracle.passes_used == B
    return {
        "init_query_loss": init_m["query_loss"],
        "final_query_loss": fin_m["query_loss"],
        "final_support_loss": fin_m["support_loss"],
        "query_accuracy": fin_m.get("query_accuracy", 0.0),
        "query_hinge": fin_m.get("query_hinge", 0.0),
        "query_r2": fin_m.get("query_r2", 0.0),
        "passes_used": oracle.passes_used,
    }


def run_kfac_no_proposer_v3(cfg: dict[str, Any], task: NeuralTargetTaskV3) -> dict[str, float]:
    """Exact same 5-basis Woodbury K-FAC + Newton-Schulz + Adam preconditioning WITHOUT neural proposer `Phi`."""
    oracle = ChargedTargetOracleV3(task)
    layers = task.clone_cold_layers(requires_grad=False)
    init_m = oracle.evaluate_query(layers)
    st = init_opt_state_v3(layers)
    B = oracle.support_budget
    w_vec = [float(x) for x in cfg["basis_weights"]]
    lr = float(cfg["lr"])
    wd = float(cfg["weight_decay"])
    for step_idx in range(B):
        st["steps_seen"] = int(st.get("steps_seen", 0)) + 1
        _, grads, act_in, err_out = oracle.forward_backward_support(layers, differentiable_graph=False)
        cos_env = 0.25 + 0.75 * 0.5 * (1.0 + math.cos(math.pi * step_idx / max(1, B - 1)))
        new_layers = []
        for l_idx, W in enumerate(layers):
            G = grads[l_idx].detach()
            (Bg, Bm, Ba, Bk, Bs), _, norm_dir = compute_five_basis_v3(
                W, G, G, act_in[l_idx], err_out[l_idx], st, l_idx, st["steps_seen"], differentiable_target=False
            )
            D_comb = w_vec[0] * Bg + w_vec[1] * Bm + w_vec[2] * Ba + w_vec[3] * Bk + w_vec[4] * Bs
            B_comb = norm_dir(D_comb)
            eta = lr * cos_env * float(st["base_scales"][l_idx])
            sm = torch.ones((1, W.shape[1]), dtype=W.dtype, device=W.device)
            sm[0, -1] = 0.0
            new_layers.append(W - eta * B_comb - wd * sm * W)
        layers = new_layers
    fin_m = oracle.evaluate_query(layers)
    assert oracle.passes_used == B
    return {
        "init_query_loss": init_m["query_loss"],
        "final_query_loss": fin_m["query_loss"],
        "final_support_loss": fin_m["support_loss"],
        "query_accuracy": fin_m.get("query_accuracy", 0.0),
        "query_hinge": fin_m.get("query_hinge", 0.0),
        "query_r2": fin_m.get("query_r2", 0.0),
        "passes_used": oracle.passes_used,
    }


BASELINE_RUNNERS_V3 = {
    "sgd_nesterov": run_sgd_nesterov_v3,
    "adamw_cosine": run_adamw_cosine_v3,
    "damped_lbfgs": run_damped_lbfgs_v3,
    "zero_head_adam": run_zero_head_adam_v3,
    "constant_step_rule": run_constant_step_rule_v3,
    "kfac_no_proposer": run_kfac_no_proposer_v3,
}


def _build_baseline_pools_56() -> dict[str, list[dict[str, Any]]]:
    sgd_pool = [
        {"lr": lr, "momentum": mom, "weight_decay": wd}
        for lr in (0.01, 0.02, 0.035, 0.06, 0.10, 0.16, 0.28)
        for mom in (0.50, 0.70, 0.82, 0.90)
        for wd in (0.005, 0.03)
    ]  # 56 configs
    adam_pool = [
        {"lr": lr, "beta1": b1, "beta2": 0.96, "weight_decay": wd}
        for lr in (0.003, 0.006, 0.012, 0.022, 0.04, 0.075, 0.14)
        for b1 in (0.80, 0.90)
        for wd in (0.005, 0.02, 0.06, 0.15)
    ]  # 56 configs
    lbfgs_pool = [
        {"lr": lr, "damping": dmp, "weight_decay": wd, "max_step": ms}
        for lr in (0.12, 0.22, 0.35, 0.55, 0.75, 0.95, 1.20)
        for dmp in (0.08, 0.40)
        for wd in (0.02, 0.10)
        for ms in (0.6, 1.4)
    ]  # 56 configs
    zero_head_pool = [
        {"lr": lr, "beta1": b1, "beta2": 0.96, "weight_decay": wd}
        for lr in (0.004, 0.008, 0.016, 0.03, 0.055, 0.10, 0.18)
        for b1 in (0.80, 0.90)
        for wd in (0.005, 0.02, 0.06, 0.15)
    ]  # 56 configs
    const_pool = [
        {"lr": lr, "momentum": mom, "weight_decay": wd}
        for lr in (0.015, 0.028, 0.045, 0.07, 0.10, 0.14, 0.20)
        for mom in (0.0, 0.50, 0.75, 0.88)
        for wd in (0.005, 0.025)
    ]  # 56 configs
    basis_presets = (
        [0.50, 0.20, 0.40, 0.40, 0.20],
        [0.25, 0.20, 0.55, 0.55, 0.30],
        [0.15, 0.15, 0.30, 0.75, 0.25],
        [0.20, 0.25, 0.65, 0.35, 0.40],
    )
    kfac_pool = [
        {"lr": lr, "basis_weights": bw, "weight_decay": wd}
        for lr in (0.025, 0.045, 0.075, 0.11, 0.16, 0.22, 0.30)
        for bw in basis_presets
        for wd in (0.005, 0.025)
    ]  # 56 configs
    pools = {
        "sgd_nesterov": sgd_pool,
        "adamw_cosine": adam_pool,
        "damped_lbfgs": lbfgs_pool,
        "zero_head_adam": zero_head_pool,
        "constant_step_rule": const_pool,
        "kfac_no_proposer": kfac_pool,
    }
    for k, v in pools.items():
        assert len(v) == 56, f"{k} expected 56 configs, got {len(v)}"
    return pools
