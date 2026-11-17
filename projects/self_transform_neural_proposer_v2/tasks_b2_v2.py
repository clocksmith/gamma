"""Progressive meta-curriculum and untouched 4-family unseen confirmation tasks for B2 v2."""
from __future__ import annotations

from pathlib import Path
import sys
import torch
import torch.nn.functional as F

V1_B2_DIR = Path(__file__).resolve().parents[1] / "self_transform_neural_proposer_v1"
if str(V1_B2_DIR) not in sys.path:
    sys.path.insert(0, str(V1_B2_DIR))

from targets import (
    ChargedTargetOracle,
    NeuralTargetTask,
    OracleBudgetExceededError,
    _anisotropic_inputs,
    _hom,
    _rand_init_matrix,
    build_target_family_task as _build_v1_family_task,
    compute_task_loss,
)

V2_CONFIRMATION_FAMILIES = (
    "unseen_swiglu_3layer_cls",
    "unseen_bottleneck_4layer_reg",
    "unseen_fastweight_adapter_bridge",
    "unseen_deep_elu_5layer_cls",
)


def forward_target_v2(
    task: NeuralTargetTask,
    layers: list[torch.Tensor],
    X: torch.Tensor,
    retain_preacts: bool = False,
) -> tuple[torch.Tensor, list[torch.Tensor], list[torch.Tensor]]:
    """Extends v1 target forward with ELU support for the 5-layer unseen confirmation family."""
    if task.activation != "elu":
        from targets import forward_target_network
        return forward_target_network(task, layers, X, retain_preacts=retain_preacts)

    act_inputs: list[torch.Tensor] = []
    preacts: list[torch.Tensor] = []
    h = X
    L = len(layers)
    for idx, W in enumerate(layers):
        a_hom = _hom(h)
        z = a_hom @ W.T
        if retain_preacts:
            z.retain_grad()
        act_inputs.append(a_hom.detach())
        preacts.append(z)
        h = z if idx == L - 1 else F.elu(z)
    return h, act_inputs, preacts


class ChargedTargetOracleV2(ChargedTargetOracle):
    def forward_backward_support(self, layers: list[torch.Tensor], differentiable_graph: bool = False):
        if self.passes_used >= self.budget:
            raise OracleBudgetExceededError(f"Task {self.task.task_id}: exceeded budget {self.budget}")
        self.passes_used += 1
        leaf_layers = [w if w.requires_grad else w.detach().clone().requires_grad_(True) for w in layers]
        preds, act_inputs, preacts = forward_target_v2(self.task, leaf_layers, self.task.X_sup, retain_preacts=True)
        loss = compute_task_loss(self.task, preds, self.task.Y_sup)
        all_grads = torch.autograd.grad(
            loss, leaf_layers + preacts, create_graph=differentiable_graph, retain_graph=differentiable_graph
        )
        n_l = len(leaf_layers)
        w_grads = list(all_grads[:n_l])
        e_outs = [g.detach() * float(self.task.X_sup.shape[0]) for g in all_grads[n_l:]]
        return loss, w_grads, act_inputs, e_outs

    @torch.no_grad()
    def evaluate_query(self, layers: list[torch.Tensor]) -> dict[str, float]:
        clean = [w.detach() for w in layers]
        preds_q, _, _ = forward_target_v2(self.task, clean, self.task.X_qry, retain_preacts=False)
        preds_s, _, _ = forward_target_v2(self.task, clean, self.task.X_sup, retain_preacts=False)
        ql = float(compute_task_loss(self.task, preds_q, self.task.Y_qry).item())
        sl = float(compute_task_loss(self.task, preds_s, self.task.Y_sup).item())
        out = {"query_loss": ql, "support_loss": sl, "passes_used": self.passes_used}
        if self.task.loss_type == "cross_entropy":
            out["query_accuracy"] = float((preds_q.argmax(dim=-1) == self.task.Y_qry).float().mean().item())
        else:
            out["query_r2"] = 1.0 - ql / float(self.task.Y_qry.var().clamp_min(1e-8).item())
        return out


def evaluate_diff_query_v2(task: NeuralTargetTask, layers: list[torch.Tensor]) -> torch.Tensor:
    preds_q, _, _ = forward_target_v2(task, layers, task.X_qry, retain_preacts=False)
    return compute_task_loss(task, preds_q, task.Y_qry)


def build_progressive_meta_task(lineage_seed: int, gen_idx: int, task_idx: int, dtype=torch.float64) -> NeuralTargetTask:
    """Progressive multi-depth & gated meta-curriculum (strictly disjoint dims/seeds from confirmation!)."""
    s = 400000 + lineage_seed * 1009 + gen_idx * 10007 + task_idx * 137
    gen = torch.Generator(device="cpu")
    gen.manual_seed(s)

    # At gen_idx >= 1, every 4th task is a synthetic 1-to-2 block gated bilinear network (`d_in=14, h=18`)
    # so later generations learn quadratic gating & small-head temperature control!
    use_gated = (gen_idx >= 1) and ((task_idx % 4) == 3)
    is_cls = (task_idx % 2) == 0 or use_gated
    noise_rate = 0.10 + 0.03 * min(gen_idx, 3)

    if use_gated:
        n_blocks = 1 if gen_idx == 1 else 2
        d_in, d_hid, d_out = 14, 18, 4
        n_sup, n_qry = 44, 128
        X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, log10_span=1.05 + 0.10 * gen_idx, dtype=dtype)
        teacher = []
        cur_d = d_in
        for _ in range(n_blocks):
            teacher.append(_rand_init_matrix(gen, d_hid, cur_d, scale=1.8, dtype=dtype))
            teacher.append(_rand_init_matrix(gen, d_hid, cur_d, scale=1.8, dtype=dtype))
            cur_d = d_hid
        teacher.append(_rand_init_matrix(gen, d_out, cur_d, scale=2.0, dtype=dtype))
        dummy = NeuralTargetTask("m", "meta_gated", "cross_entropy", "swiglu_net", "swiglu", teacher, [], X_all, X_all, X_all, X_all)
        with torch.no_grad():
            raw_out, _, _ = forward_target_v2(dummy, teacher, X_all)
            y_all = raw_out.argmax(dim=-1)
        X_sup, X_qry = X_all[:n_sup], X_all[n_sup:]
        Y_sup = y_all[:n_sup].clone()
        flip = torch.rand(n_sup, generator=gen) < noise_rate
        Y_sup[flip] = torch.randint(0, d_out, (int(flip.sum().item()),), generator=gen)
        Y_qry = y_all[n_sup:]

        init_layers = []
        cur_d = d_in
        for b_i in range(n_blocks):
            init_layers.append(_rand_init_matrix(gen, d_hid, cur_d, scale=1.4 if b_i == 0 else 0.7, dtype=dtype))
            init_layers.append(_rand_init_matrix(gen, d_hid, cur_d, scale=0.7 if b_i == 0 else 1.3, dtype=dtype))
            cur_d = d_hid
        init_layers.append(_rand_init_matrix(gen, d_out, cur_d, scale=(0.22 if (task_idx % 2 == 1) else 0.75), dtype=dtype))
        return NeuralTargetTask(
            task_id=f"pmeta-gated-s{lineage_seed}-g{gen_idx}-t{task_idx}",
            family="progressive_meta_mlp",
            loss_type="cross_entropy",
            arch_kind="swiglu_net",
            activation="swiglu",
            init_layers=init_layers,
            frozen_trunk=[],
            X_sup=X_sup,
            Y_sup=Y_sup,
            X_qry=X_qry,
            Y_qry=Y_qry,
            budget=10,
        )

    depth = 2 if gen_idx == 0 else (2 + (task_idx % min(3, gen_idx + 1)))  # 2, 2..3, 2..4 layers
    act = ("tanh", "gelu", "silu")[(gen_idx + task_idx) % 3]

    d_in, d_hid, d_out = 16, 24, (5 if is_cls else 4)
    n_sup, n_qry = 48, 128
    X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, log10_span=1.0 + 0.12 * gen_idx, dtype=dtype)

    dims = [d_in] + [d_hid] * (depth - 1) + [d_out]
    teacher = [_rand_init_matrix(gen, dims[k + 1], dims[k], scale=2.0, dtype=dtype) for k in range(len(dims) - 1)]
    dummy = NeuralTargetTask("m", "meta", "mse", "mlp_act", act, teacher, [], X_all, X_all, X_all, X_all)
    with torch.no_grad():
        raw_out, _, _ = forward_target_v2(dummy, teacher, X_all)

    X_sup, X_qry = X_all[:n_sup], X_all[n_sup:]
    if is_cls:
        y_all = raw_out.argmax(dim=-1)
        Y_sup = y_all[:n_sup].clone()
        flip = torch.rand(n_sup, generator=gen) < noise_rate
        Y_sup[flip] = torch.randint(0, d_out, (int(flip.sum().item()),), generator=gen)
        Y_qry = y_all[n_sup:]
        loss_type = "cross_entropy"
    else:
        y_norm = raw_out / raw_out.std().clamp_min(1e-6)
        Y_sup = y_norm[:n_sup] + (0.15 + 0.04 * gen_idx) * torch.randn((n_sup, d_out), generator=gen, dtype=dtype)
        Y_qry = y_norm[n_sup:]
        loss_type = "mse"

    scales = [1.8 if (k % 2 == 0) else 0.55 for k in range(len(dims) - 1)]
    scales[-1] = (0.20, 0.55, 1.65)[task_idx % 3]
    init_layers = [_rand_init_matrix(gen, dims[k + 1], dims[k], scale=scales[k], dtype=dtype) for k in range(len(dims) - 1)]

    return NeuralTargetTask(
        task_id=f"pmeta-s{lineage_seed}-g{gen_idx}-t{task_idx}",
        family="progressive_meta_mlp",
        loss_type=loss_type,
        arch_kind="mlp_act",
        activation=act,
        init_layers=init_layers,
        frozen_trunk=[],
        X_sup=X_sup,
        Y_sup=Y_sup,
        X_qry=X_qry,
        Y_qry=Y_qry,
        budget=10,
    )


def build_shared_val_anchor(lineage_seed: int, count: int = 12) -> list[NeuralTargetTask]:
    """Fixed per-seed meta-validation anchor spanning 2/3/4-layer + gated noisy tasks (`12` tasks = `120` passes/check)."""
    return [
        build_progressive_meta_task(lineage_seed=lineage_seed + 9000, gen_idx=(k % 4), task_idx=k)
        for k in range(count)
    ]


def build_v2_confirmation_task(family: str, seed: int, dtype=torch.float64) -> NeuralTargetTask:
    """Build an instance of the 4 unseen confirmation neural target architectures (`seed_base = 850000`)."""
    assert family in V2_CONFIRMATION_FAMILIES, f"Unknown v2 family: {family}"
    if family != "unseen_deep_elu_5layer_cls":
        return _build_v1_family_task(family, seed=seed, dtype=dtype)

    # 4th brand-new unseen family: 5-layer deep ELU classifier (22 -> 24 -> 24 -> 24 -> 24 -> 6) with 15% label noise!
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    dims = [22, 24, 24, 24, 24, 6]
    n_sup, n_qry = 52, 160
    X_all = _anisotropic_inputs(gen, n_sup + n_qry, dims[0], log10_span=1.30, dtype=dtype)
    teacher = [_rand_init_matrix(gen, dims[k + 1], dims[k], scale=1.85, dtype=dtype) for k in range(5)]
    tmp = NeuralTargetTask("tmp", family, "cross_entropy", "mlp_act", "elu", teacher, [], X_all, X_all, X_all, X_all)
    with torch.no_grad():
        logits, _, _ = forward_target_v2(tmp, teacher, X_all)
        y_all = logits.argmax(dim=-1)
    Y_sup = y_all[:n_sup].clone()
    flip = torch.rand(n_sup, generator=gen) < 0.15
    Y_sup[flip] = torch.randint(0, dims[-1], (int(flip.sum().item()),), generator=gen)
    Y_qry = y_all[n_sup:]

    scales = [2.0, 0.55, 1.9, 0.55, 1.4]
    init_layers = [_rand_init_matrix(gen, dims[k + 1], dims[k], scale=scales[k], dtype=dtype) for k in range(5)]
    return NeuralTargetTask(
        task_id=f"{family}-{seed}",
        family=family,
        loss_type="cross_entropy",
        arch_kind="mlp_act",
        activation="elu",
        init_layers=init_layers,
        frozen_trunk=[],
        X_sup=X_all[:n_sup],
        Y_sup=Y_sup,
        X_qry=X_all[n_sup:],
        Y_qry=Y_qry,
        budget=10,
    )
