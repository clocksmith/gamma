"""Cold-target evaluation for `M_Phi` and strong training-calibrated conventional optimizers (`SGD+Nesterov`, `AdamW`, `L-BFGS`).

All optimizers execute through the SAME `ChargedTargetOracle(task)` with `budget = 10` forward-backward passes
and ZERO carried state (`state = None` at step 0 on every cold target!).
"""
from __future__ import annotations

import math
from typing import Any
import torch

from proposer import ProposerWeights, init_optimizer_state, propose_network_update
from targets import ChargedTargetOracle, NeuralTargetTask


def run_proposer_on_cold_target(phi: ProposerWeights, task: NeuralTargetTask) -> dict[str, float]:
    """Run `M_Phi` on a brand-new cold target network with `state = None` (zero carried optimizer state)."""
    oracle = ChargedTargetOracle(task)
    phi_clean = phi.clone_detached(requires_grad=False)
    layers = task.clone_cold_layers(requires_grad=False)
    init_metrics = oracle.evaluate_query(layers)

    opt_state = init_optimizer_state(layers)
    B = oracle.budget
    for step_idx in range(B):
        loss, grads, act_inputs, err_outputs = oracle.forward_backward_support(layers, differentiable_graph=False)
        with torch.no_grad():
            layers = propose_network_update(
                phi=phi_clean,
                layers=[w.detach() for w in layers],
                grads=[g.detach() for g in grads],
                act_inputs=act_inputs,
                err_outputs=err_outputs,
                opt_state=opt_state,
                step_idx=step_idx,
                total_steps=B,
                cur_loss=loss.detach(),
                capture_self_acts=None,
            )
    final_metrics = oracle.evaluate_query(layers)
    assert oracle.passes_used == B
    return {
        "init_query_loss": init_metrics["query_loss"],
        "final_query_loss": final_metrics["query_loss"],
        "final_support_loss": final_metrics["support_loss"],
        "query_accuracy": final_metrics.get("query_accuracy", 0.0),
        "query_r2": final_metrics.get("query_r2", 0.0),
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
    """Apply L2 weight decay to weight columns only (excluding homogeneous bias last column), matching neural practice."""
    masks = []
    for w in template:
        m = torch.ones_like(w.detach())
        m[:, -1] = 0.0
        masks.append(m.reshape(-1))
    return torch.cat(masks)


def run_sgd_nesterov(cfg: dict[str, float], task: NeuralTargetTask) -> dict[str, float]:
    oracle = ChargedTargetOracle(task)
    layers = task.clone_cold_layers(requires_grad=False)
    init_m = oracle.evaluate_query(layers)

    lr = float(cfg["lr"])
    mom = float(cfg["momentum"])
    wd = float(cfg["weight_decay"])
    wd_mask = _weight_decay_mask(layers)
    theta = _pack_flat(layers)
    vel = torch.zeros_like(theta)
    B = oracle.budget

    for step_idx in range(B):
        cur_layers = _unpack_flat(theta, layers)
        _, grads, _, _ = oracle.forward_backward_support(cur_layers, differentiable_graph=False)
        g = _pack_flat(grads) + wd * wd_mask * theta
        # Cosine step decay + gradient norm safety clip
        gn = float(g.norm().item())
        if gn > 20.0:
            g = g * (20.0 / gn)
        lr_t = lr * (0.25 + 0.75 * 0.5 * (1.0 + math.cos(math.pi * step_idx / max(1, B - 1))))
        vel = mom * vel + g
        step_dir = g + mom * vel
        theta = theta - lr_t * step_dir

    fin_m = oracle.evaluate_query(_unpack_flat(theta, layers))
    assert oracle.passes_used == B
    return {
        "init_query_loss": init_m["query_loss"],
        "final_query_loss": fin_m["query_loss"],
        "final_support_loss": fin_m["support_loss"],
        "query_accuracy": fin_m.get("query_accuracy", 0.0),
        "query_r2": fin_m.get("query_r2", 0.0),
        "passes_used": oracle.passes_used,
    }


def run_adamw_cosine(cfg: dict[str, float], task: NeuralTargetTask) -> dict[str, float]:
    oracle = ChargedTargetOracle(task)
    layers = task.clone_cold_layers(requires_grad=False)
    init_m = oracle.evaluate_query(layers)

    lr = float(cfg["lr"])
    b1 = float(cfg.get("beta1", 0.85))
    b2 = float(cfg.get("beta2", 0.98))
    wd = float(cfg["weight_decay"])
    wd_mask = _weight_decay_mask(layers)
    theta = _pack_flat(layers)
    m_t = torch.zeros_like(theta)
    v_t = torch.zeros_like(theta)
    B = oracle.budget

    for step_idx in range(B):
        t = step_idx + 1
        cur_layers = _unpack_flat(theta, layers)
        _, grads, _, _ = oracle.forward_backward_support(cur_layers, differentiable_graph=False)
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
        "query_r2": fin_m.get("query_r2", 0.0),
        "passes_used": oracle.passes_used,
    }


def run_damped_lbfgs(cfg: dict[str, float], task: NeuralTargetTask) -> dict[str, float]:
    """Two-loop Damped L-BFGS with trust-region step cap and charged backtracking."""
    oracle = ChargedTargetOracle(task)
    layers = task.clone_cold_layers(requires_grad=False)
    init_m = oracle.evaluate_query(layers)

    lr = float(cfg["lr"])
    damp = float(cfg["damping"])
    wd = float(cfg["weight_decay"])
    max_step = float(cfg.get("max_step", 1.5))
    mem = 5
    wd_mask = _weight_decay_mask(layers)

    theta = _pack_flat(layers)
    loss_t, grads0, _, _ = oracle.forward_backward_support(_unpack_flat(theta, layers), differentiable_graph=False)
    f_cur = float(loss_t.item()) + 0.5 * wd * float((wd_mask * theta * theta).sum().item())
    g_cur = _pack_flat(grads0) + wd * wd_mask * theta

    s_hist: list[torch.Tensor] = []
    y_hist: list[torch.Tensor] = []
    rho_hist: list[float] = []

    while oracle.passes_used < oracle.budget:
        q = g_cur.clone()
        alphas: list[float] = []
        for s_i, y_i, r_i in zip(reversed(s_hist), reversed(y_hist), reversed(rho_hist)):
            a_i = r_i * float((s_i * q).sum().item())
            alphas.append(a_i)
            q = q - a_i * y_i

        if s_hist:
            s_last, y_last = s_hist[-1], y_hist[-1]
            yy = float((y_last * y_last).sum().item())
            sy = float((s_last * y_last).sum().item())
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
        cand_loss_t, cand_grads, _, _ = oracle.forward_backward_support(
            _unpack_flat(cand_theta, layers), differentiable_graph=False
        )
        f_cand = float(cand_loss_t.item()) + 0.5 * wd * float((wd_mask * cand_theta * cand_theta).sum().item())
        g_cand = _pack_flat(cand_grads) + wd * wd_mask * cand_theta

        if math.isfinite(f_cand) and f_cand <= f_cur + 0.15 * abs(f_cur) + 0.05:
            s_k = cand_theta - theta
            y_k = g_cand - g_cur + damp * s_k
            sy_k = float((s_k * y_k).sum().item())
            if sy_k > 1e-10:
                if len(s_hist) >= mem:
                    s_hist.pop(0); y_hist.pop(0); rho_hist.pop(0)
                s_hist.append(s_k)
                y_hist.append(y_k)
                rho_hist.append(1.0 / sy_k)
            theta, f_cur, g_cur = cand_theta, f_cand, g_cand
        else:
            # Rejected step IS STILL CHARGED in oracle.passes_used; shrink step radius
            lr *= 0.45

    fin_m = oracle.evaluate_query(_unpack_flat(theta, layers))
    assert oracle.passes_used == oracle.budget
    return {
        "init_query_loss": init_m["query_loss"],
        "final_query_loss": fin_m["query_loss"],
        "final_support_loss": fin_m["support_loss"],
        "query_accuracy": fin_m.get("query_accuracy", 0.0),
        "query_r2": fin_m.get("query_r2", 0.0),
        "passes_used": oracle.passes_used,
    }


def calibrate_conventional_optimizers(cal_tasks: list[NeuralTargetTask]) -> dict[str, dict[str, Any]]:
    """Grid-calibrate SGD+Nesterov, AdamW, and Damped L-BFGS on separate calibration tasks for held-out query loss."""
    sgd_grid = [
        {"lr": lr, "momentum": mom, "weight_decay": wd}
        for lr in (0.03, 0.08, 0.20, 0.45, 0.90)
        for mom in (0.5, 0.85)
        for wd in (0.0, 0.01, 0.05)
    ]
    adam_grid = [
        {"lr": lr, "beta1": 0.85, "beta2": 0.98, "weight_decay": wd}
        for lr in (0.005, 0.015, 0.04, 0.10, 0.22)
        for wd in (0.0, 0.01, 0.05, 0.15)
    ]
    lbfgs_grid = [
        {"lr": lr, "damping": dmp, "weight_decay": wd, "max_step": ms}
        for lr in (0.35, 0.75, 1.0)
        for dmp in (0.05, 0.25, 0.80)
        for wd in (0.0, 0.02, 0.08)
        for ms in (0.8, 2.0)
    ]

    best: dict[str, dict[str, Any]] = {}
    for name, grid, fn in (
        ("sgd_nesterov", sgd_grid, run_sgd_nesterov),
        ("adamw_cosine", adam_grid, run_adamw_cosine),
        ("damped_lbfgs", lbfgs_grid, run_damped_lbfgs),
    ):
        best_loss = float("inf")
        best_cfg = grid[0]
        passes_billed = 0
        for cfg in grid:
            losses = []
            for t in cal_tasks:
                res = fn(cfg, t)
                passes_billed += res["passes_used"]
                losses.append(res["final_query_loss"] if math.isfinite(res["final_query_loss"]) else 1e6)
            mean_l = sum(losses) / len(losses)
            if mean_l < best_loss:
                best_loss = mean_l
                best_cfg = cfg
        best[name] = {
            "best_config": best_cfg,
            "calibration_mean_query_loss": best_loss,
            "calibration_oracle_passes": passes_billed,
        }
    return best
