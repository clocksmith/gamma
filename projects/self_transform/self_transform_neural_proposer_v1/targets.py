"""Multi-layer neural target families and strict forward-backward oracle counter for B2."""
from __future__ import annotations

from dataclasses import dataclass
import math
import torch
import torch.nn.functional as F

CONFIRMATION_FAMILIES = (
    "unseen_swiglu_3layer_cls",
    "unseen_bottleneck_4layer_reg",
    "unseen_fastweight_adapter_bridge",
)


class OracleBudgetExceededError(RuntimeError):
    """Raised immediately if any learned or conventional optimizer exceeds the step budget B."""


@dataclass
class NeuralTargetTask:
    task_id: str
    family: str
    loss_type: str                        # 'cross_entropy' | 'mse'
    arch_kind: str                        # 'mlp_act' | 'swiglu_net' | 'frozen_trunk_swiglu_adapter'
    activation: str                       # 'tanh' | 'gelu' | 'silu' | 'swiglu'
    init_layers: list[torch.Tensor]       # trainable homogeneous matrices W_l in R^{d_out x (d_in + 1)}
    frozen_trunk: list[torch.Tensor]      # empty unless arch_kind == 'frozen_trunk_swiglu_adapter'
    X_sup: torch.Tensor
    Y_sup: torch.Tensor
    X_qry: torch.Tensor
    Y_qry: torch.Tensor
    budget: int = 10

    def clone_cold_layers(self, requires_grad: bool = True) -> list[torch.Tensor]:
        return [w.detach().clone().requires_grad_(requires_grad) for w in self.init_layers]


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
    raise ValueError(f"Unsupported activation: {act}")


def forward_target_network(
    task: NeuralTargetTask,
    layers: list[torch.Tensor],
    X: torch.Tensor,
    retain_preacts: bool = False,
) -> tuple[torch.Tensor, list[torch.Tensor], list[torch.Tensor]]:
    """Forward `X` through `task` using `layers`, returning `(outputs, act_inputs, preacts)`."""
    act_inputs: list[torch.Tensor] = []
    preacts: list[torch.Tensor] = []

    h = X
    if task.arch_kind == "frozen_trunk_swiglu_adapter":
        with torch.no_grad():
            for f_w in task.frozen_trunk:
                h = F.gelu(_hom(h) @ f_w.T)

    if task.arch_kind == "mlp_act":
        L = len(layers)
        for idx, W in enumerate(layers):
            a_hom = _hom(h)
            z = a_hom @ W.T
            if retain_preacts:
                z.retain_grad()
            act_inputs.append(a_hom.detach())
            preacts.append(z)
            h = z if idx == L - 1 else _apply_act(z, task.activation)
        return h, act_inputs, preacts

    assert len(layers) % 2 == 1, "SwiGLU network expects 2*K + 1 matrices"
    n_blocks = (len(layers) - 1) // 2
    for b in range(n_blocks):
        W_g = layers[2 * b]
        W_u = layers[2 * b + 1]
        a_hom = _hom(h)
        zg = a_hom @ W_g.T
        zu = a_hom @ W_u.T
        if retain_preacts:
            zg.retain_grad()
            zu.retain_grad()
        act_inputs.append(a_hom.detach())
        act_inputs.append(a_hom.detach())
        preacts.append(zg)
        preacts.append(zu)
        h = F.silu(zg) * zu

    W_head = layers[-1]
    a_last = _hom(h)
    z_out = a_last @ W_head.T
    if retain_preacts:
        z_out.retain_grad()
    act_inputs.append(a_last.detach())
    preacts.append(z_out)
    return z_out, act_inputs, preacts


def compute_task_loss(task: NeuralTargetTask, preds: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    if task.loss_type == "cross_entropy":
        return F.cross_entropy(preds, targets)
    return F.mse_loss(preds, targets)


class ChargedTargetOracle:
    """Enforces an exact forward-backward pass budget across EVERY optimizer arm."""

    def __init__(self, task: NeuralTargetTask):
        self.task = task
        self.budget = int(task.budget)
        self.passes_used = 0

    def forward_backward_support(
        self,
        layers: list[torch.Tensor],
        differentiable_graph: bool = False,
    ) -> tuple[torch.Tensor, list[torch.Tensor], list[torch.Tensor], list[torch.Tensor]]:
        if self.passes_used >= self.budget:
            raise OracleBudgetExceededError(
                f"Task {self.task.task_id}: exceeded oracle budget {self.budget}"
            )
        self.passes_used += 1

        leaf_layers = [w if w.requires_grad else w.detach().clone().requires_grad_(True) for w in layers]
        preds, act_inputs, preacts = forward_target_network(
            self.task, leaf_layers, self.task.X_sup, retain_preacts=True
        )
        loss = compute_task_loss(self.task, preds, self.task.Y_sup)
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

    @torch.no_grad()
    def evaluate_query(self, layers: list[torch.Tensor]) -> dict[str, float]:
        clean_layers = [w.detach() for w in layers]
        preds_q, _, _ = forward_target_network(self.task, clean_layers, self.task.X_qry, retain_preacts=False)
        preds_s, _, _ = forward_target_network(self.task, clean_layers, self.task.X_sup, retain_preacts=False)
        q_loss = float(compute_task_loss(self.task, preds_q, self.task.Y_qry).item())
        s_loss = float(compute_task_loss(self.task, preds_s, self.task.Y_sup).item())
        out = {"query_loss": q_loss, "support_loss": s_loss, "passes_used": self.passes_used}
        if self.task.loss_type == "cross_entropy":
            out["query_accuracy"] = float((preds_q.argmax(dim=-1) == self.task.Y_qry).float().mean().item())
        else:
            y_var = float(self.task.Y_qry.var().clamp_min(1e-8).item())
            out["query_r2"] = 1.0 - q_loss / y_var
        return out


def evaluate_differentiable_query_loss(task: NeuralTargetTask, layers: list[torch.Tensor]) -> torch.Tensor:
    preds_q, _, _ = forward_target_network(task, layers, task.X_qry, retain_preacts=False)
    return compute_task_loss(task, preds_q, task.Y_qry)


def _rand_init_matrix(gen: torch.Generator, d_out: int, d_in: int, scale: float = 1.0, dtype=torch.float64) -> torch.Tensor:
    std = scale / math.sqrt(max(1, d_in))
    W = std * torch.randn((d_out, d_in + 1), generator=gen, dtype=dtype)
    W[:, -1] *= 0.1
    return W


def _anisotropic_inputs(gen: torch.Generator, n: int, d: int, log10_span: float, dtype=torch.float64) -> torch.Tensor:
    raw = torch.randn((n, d), generator=gen, dtype=dtype)
    exps = torch.linspace(-log10_span, log10_span, d, dtype=dtype)
    perm = torch.randperm(d, generator=gen)
    scales = (10.0 ** exps)[perm]
    q_mat, _ = torch.linalg.qr(torch.randn((d, d), generator=gen, dtype=dtype))
    return (raw * scales.unsqueeze(0)) @ q_mat.T


def build_meta_training_task(seed: int, gen_idx: int, task_idx: int, dtype=torch.float64) -> NeuralTargetTask:
    """2-layer Tanh / GELU neural tasks (strictly distinct architectures from confirmation families!)."""
    s = seed + gen_idx * 10007 + task_idx * 131
    gen = torch.Generator(device="cpu")
    gen.manual_seed(s)

    is_cls = (task_idx % 2) == 0
    act = "tanh" if (task_idx % 4) < 2 else "gelu"
    d_in, d_hid, d_out = 16, 24, 4
    n_sup, n_qry = 44, 128

    X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, log10_span=1.1, dtype=dtype)
    teacher = [
        _rand_init_matrix(gen, d_hid, d_in, scale=2.2, dtype=dtype),
        _rand_init_matrix(gen, d_hid, d_hid, scale=1.8, dtype=dtype),
        _rand_init_matrix(gen, d_out, d_hid, scale=2.0, dtype=dtype),
    ]
    dummy = NeuralTargetTask("t", "meta", "mse", "mlp_act", act, teacher, [], X_all, X_all, X_all, X_all)
    with torch.no_grad():
        clean_logits, _, _ = forward_target_network(dummy, teacher, X_all)

    X_sup, X_qry = X_all[:n_sup], X_all[n_sup:]
    if is_cls:
        y_clean = clean_logits.argmax(dim=-1)
        Y_sup = y_clean[:n_sup].clone()
        flip = torch.rand(n_sup, generator=gen) < 0.12
        rand_lbl = torch.randint(0, d_out, (n_sup,), generator=gen)
        Y_sup[flip] = rand_lbl[flip]
        Y_qry = y_clean[n_sup:]
        loss_type = "cross_entropy"
    else:
        std_y = clean_logits.std().clamp_min(1e-6)
        y_norm = clean_logits / std_y
        Y_sup = y_norm[:n_sup] + 0.22 * torch.randn((n_sup, d_out), generator=gen, dtype=dtype)
        Y_qry = y_norm[n_sup:]
        loss_type = "mse"

    s1 = 1.6 if (task_idx % 3 == 0) else 0.55
    s2 = 0.50 if (task_idx % 3 == 0) else 1.50
    init_layers = [
        _rand_init_matrix(gen, d_hid, d_in, scale=s1, dtype=dtype),
        _rand_init_matrix(gen, d_out, d_hid, scale=s2, dtype=dtype),
    ]
    return NeuralTargetTask(
        task_id=f"meta-g{gen_idx}-t{task_idx}",
        family="meta_2layer_mlp",
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


def build_target_family_task(family: str, seed: int, dtype=torch.float64) -> NeuralTargetTask:
    """Construct an instance of one of the 3 unseen neural target architectures under `seed`."""
    assert family in CONFIRMATION_FAMILIES, f"Unknown target family: {family}"
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)

    if family == "unseen_swiglu_3layer_cls":
        d_in, h1, h2, n_cls = 20, 28, 20, 5
        n_sup, n_qry = 48, 160
        X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, log10_span=1.35, dtype=dtype)
        teacher = [
            _rand_init_matrix(gen, h1, d_in, 2.0, dtype),
            _rand_init_matrix(gen, h1, d_in, 2.0, dtype),
            _rand_init_matrix(gen, h2, h1, 1.8, dtype),
            _rand_init_matrix(gen, h2, h1, 1.8, dtype),
            _rand_init_matrix(gen, n_cls, h2, 2.2, dtype),
        ]
        tmp = NeuralTargetTask("tmp", family, "cross_entropy", "swiglu_net", "swiglu", teacher, [], X_all, X_all, X_all, X_all)
        with torch.no_grad():
            logits, _, _ = forward_target_network(tmp, teacher, X_all)
            y_all = logits.argmax(dim=-1)
        Y_sup = y_all[:n_sup].clone()
        flip = torch.rand(n_sup, generator=gen) < 0.12
        Y_sup[flip] = torch.randint(0, n_cls, (int(flip.sum().item()),), generator=gen)
        Y_qry = y_all[n_sup:]

        init_layers = [
            _rand_init_matrix(gen, h1, d_in, 1.7, dtype),
            _rand_init_matrix(gen, h1, d_in, 0.6, dtype),
            _rand_init_matrix(gen, h2, h1, 0.5, dtype),
            _rand_init_matrix(gen, h2, h1, 1.6, dtype),
            _rand_init_matrix(gen, n_cls, h2, 0.8, dtype),
        ]
        return NeuralTargetTask(
            task_id=f"{family}-{seed}",
            family=family,
            loss_type="cross_entropy",
            arch_kind="swiglu_net",
            activation="swiglu",
            init_layers=init_layers,
            frozen_trunk=[],
            X_sup=X_all[:n_sup],
            Y_sup=Y_sup,
            X_qry=X_all[n_sup:],
            Y_qry=Y_qry,
            budget=10,
        )

    if family == "unseen_bottleneck_4layer_reg":
        d_in, d_wide, d_bot, d_out = 18, 32, 8, 4
        n_sup, n_qry = 48, 160
        X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, log10_span=1.25, dtype=dtype)
        teacher = [
            _rand_init_matrix(gen, d_wide, d_in, 2.0, dtype),
            _rand_init_matrix(gen, d_bot, d_wide, 1.8, dtype),
            _rand_init_matrix(gen, d_wide, d_bot, 2.0, dtype),
            _rand_init_matrix(gen, d_out, d_wide, 1.8, dtype),
        ]
        tmp = NeuralTargetTask("tmp", family, "mse", "mlp_act", "silu", teacher, [], X_all, X_all, X_all, X_all)
        with torch.no_grad():
            raw_y, _, _ = forward_target_network(tmp, teacher, X_all)
            y_all = raw_y / raw_y.std().clamp_min(1e-6)
        Y_sup = y_all[:n_sup] + 0.20 * torch.randn((n_sup, d_out), generator=gen, dtype=dtype)
        Y_qry = y_all[n_sup:]

        init_layers = [
            _rand_init_matrix(gen, d_wide, d_in, 2.1, dtype),
            _rand_init_matrix(gen, d_bot, d_wide, 0.45, dtype),
            _rand_init_matrix(gen, d_wide, d_bot, 1.8, dtype),
            _rand_init_matrix(gen, d_out, d_wide, 0.50, dtype),
        ]
        return NeuralTargetTask(
            task_id=f"{family}-{seed}",
            family=family,
            loss_type="mse",
            arch_kind="mlp_act",
            activation="silu",
            init_layers=init_layers,
            frozen_trunk=[],
            X_sup=X_all[:n_sup],
            Y_sup=Y_sup,
            X_qry=X_all[n_sup:],
            Y_qry=Y_qry,
            budget=10,
        )

    d_in, d_feat, d_rank, n_cls = 24, 48, 16, 6
    n_sup, n_qry = 44, 160
    X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, log10_span=1.20, dtype=dtype)
    frozen_trunk = [
        _rand_init_matrix(gen, d_feat, d_in, 1.6, dtype),
        _rand_init_matrix(gen, d_feat, d_feat, 1.4, dtype),
    ]
    teacher_adapter = [
        _rand_init_matrix(gen, d_rank, d_feat, 2.2, dtype),
        _rand_init_matrix(gen, d_rank, d_feat, 2.2, dtype),
        _rand_init_matrix(gen, n_cls, d_rank, 2.4, dtype),
    ]
    tmp = NeuralTargetTask(
        "tmp", family, "cross_entropy", "frozen_trunk_swiglu_adapter", "swiglu", teacher_adapter, frozen_trunk, X_all, X_all, X_all, X_all
    )
    with torch.no_grad():
        logits, _, _ = forward_target_network(tmp, teacher_adapter, X_all)
        y_all = logits.argmax(dim=-1)
    Y_sup = y_all[:n_sup].clone()
    flip = torch.rand(n_sup, generator=gen) < 0.10
    Y_sup[flip] = torch.randint(0, n_cls, (int(flip.sum().item()),), generator=gen)
    Y_qry = y_all[n_sup:]

    init_adapter = [
        _rand_init_matrix(gen, d_rank, d_feat, 0.9, dtype),
        _rand_init_matrix(gen, d_rank, d_feat, 0.9, dtype),
        _rand_init_matrix(gen, n_cls, d_rank, 0.2, dtype),
    ]
    return NeuralTargetTask(
        task_id=f"{family}-{seed}",
        family=family,
        loss_type="cross_entropy",
        arch_kind="frozen_trunk_swiglu_adapter",
        activation="swiglu",
        init_layers=init_adapter,
        frozen_trunk=frozen_trunk,
        X_sup=X_all[:n_sup],
        Y_sup=Y_sup,
        X_qry=X_all[n_sup:],
        Y_qry=Y_qry,
        budget=10,
    )
