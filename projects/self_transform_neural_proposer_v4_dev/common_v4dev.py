"""Shared development machinery for `self_transform_neural_proposer_v4_dev` (CPU only).

DEVELOPMENT ONLY. Nothing here is a pre-registered or sealed result.

Seed plan (all >= 20,000,000; the largest seed any v3 code path uses is the confirmation
seed 9,863,011, and v3 upstream/calibration/regen seeds are all < 4,000,000):
    proposer init           20,000,000 + lineage
    meta-train stream       21,000,000 + lineage * 100,000 + idx          (idx < 100,000)
    upstream validation     40,000,000 + lineage * 10,000 + k             (early stopping only)
    K-FAC calibration       41,000,000 + lineage * 10,000 + k
    held-out evaluation     50,000,000 + lineage * 10,000 + fam * 1,000 + t
    stage-3 child batch     60,000,000 + lineage * 100,000 + idx
    in-family meta-train    70,000,000 + lineage * 100,000 + idx
    in-family calibration   81,000,000 + lineage * 10,000 + fam * 1,000 + k
    in-family validation    82,000,000 + lineage * 10,000 + fam * 1,000 + k
Lineages 0..89 are study lineages, 90..99 are pilot lineages used only to pick meta-optimiser
hyper-parameters on upstream validation tasks (never on held-out evaluation tasks).
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import statistics
import sys
import time
from typing import Any, Callable

import torch

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from baselines_v4dev import (  # noqa: E402
    DEV_SEED_FLOOR,
    ChargedTargetOracleV3,
    NeuralTargetTaskV3,
    _build_baseline_pools_56,
    build_upstream_task_dev,
    normalized_loss_ratio,
    run_kfac_no_proposer_v3,
    smooth_anchor_score,
)
from proposer_v4dev import (  # noqa: E402
    OUT_DIM_V3,
    KfacBaseConfig,
    ProposerWeightsV3,
    init_opt_state_v3,
    init_residual_proposer,
    propose_update_residual,
)
from tasks_v4dev import DEV_HELDOUT_FAMILIES, build_heldout_task_dev  # noqa: E402

REPO_ROOT = THIS_DIR.parent.parent
OUTPUT_DIR = REPO_ROOT / ".work" / "self-transform-neural-proposer-v4-dev"
DEVICE = torch.device("cpu")
MAX_V3_SEED = 9_863_011


def configure_cpu(threads: int = 1) -> None:
    assert 1 <= threads <= 4
    torch.set_num_threads(threads)
    # No tensor in this project is ever moved off the CPU; DEVICE is passed nowhere else.
    assert not any(a.startswith("PYTORCH_MPS") for a in os.environ), "MPS env overrides present"


def _chk(seed: int) -> int:
    assert seed >= DEV_SEED_FLOOR > MAX_V3_SEED
    return int(seed)


def seed_init(lineage: int) -> int:
    assert 0 <= lineage < 100
    return _chk(20_000_000 + lineage)


def seed_meta_train(lineage: int, idx: int) -> int:
    assert 0 <= lineage < 100 and 0 <= idx < 100_000
    return _chk(21_000_000 + lineage * 100_000 + idx)


def seed_upstream_val(lineage: int, k: int) -> int:
    assert 0 <= lineage < 100 and 0 <= k < 10_000
    return _chk(40_000_000 + lineage * 10_000 + k)


def seed_calib(lineage: int, k: int) -> int:
    assert 0 <= lineage < 100 and 0 <= k < 10_000
    return _chk(41_000_000 + lineage * 10_000 + k)


def seed_heldout(lineage: int, fam_idx: int, t: int) -> int:
    assert 0 <= lineage < 100 and 0 <= fam_idx < 10 and 0 <= t < 1000
    return _chk(50_000_000 + lineage * 10_000 + fam_idx * 1000 + t)


def seed_stage3_child(lineage: int, idx: int) -> int:
    assert 0 <= lineage < 100 and 0 <= idx < 100_000
    return _chk(60_000_000 + lineage * 100_000 + idx)


def seed_infamily_train(lineage: int, idx: int) -> int:
    assert 0 <= lineage < 100 and 0 <= idx < 100_000
    return _chk(70_000_000 + lineage * 100_000 + idx)


def seed_infamily_calib(lineage: int, fam_idx: int, k: int) -> int:
    assert 0 <= lineage < 100 and 0 <= fam_idx < 10 and 0 <= k < 1000
    return _chk(81_000_000 + lineage * 10_000 + fam_idx * 1000 + k)


def seed_infamily_val(lineage: int, fam_idx: int, k: int) -> int:
    assert 0 <= lineage < 100 and 0 <= fam_idx < 10 and 0 <= k < 1000
    return _chk(82_000_000 + lineage * 10_000 + fam_idx * 1000 + k)


def upstream_task(seed: int, idx: int) -> NeuralTargetTaskV3:
    """v3 upstream generator; `idx` cycles the 8 task variants and the 4 difficulty levels."""
    return build_upstream_task_dev(raw_seed=seed, gen_idx=(idx // 8) % 4, task_idx=idx % 8)


def upstream_train_task(lineage: int, idx: int) -> NeuralTargetTaskV3:
    return upstream_task(seed_meta_train(lineage, idx), idx)


def upstream_val_tasks(lineage: int, count: int) -> list[NeuralTargetTaskV3]:
    return [upstream_task(seed_upstream_val(lineage, k), k) for k in range(count)]


def upstream_calib_tasks(lineage: int, count: int) -> list[NeuralTargetTaskV3]:
    return [upstream_task(seed_calib(lineage, k), k) for k in range(count)]


def heldout_specs(lineage: int, per_family: int) -> list[dict[str, Any]]:
    return [
        {"family": fam, "seed": seed_heldout(lineage, fi, t)}
        for fi, fam in enumerate(DEV_HELDOUT_FAMILIES)
        for t in range(per_family)
    ]


def infamily_train_task(lineage: int, idx: int) -> NeuralTargetTaskV3:
    fam = DEV_HELDOUT_FAMILIES[idx % len(DEV_HELDOUT_FAMILIES)]
    return build_heldout_task_dev(fam, seed_infamily_train(lineage, idx))


def infamily_calib_tasks(lineage: int, per_family: int) -> list[NeuralTargetTaskV3]:
    return [
        build_heldout_task_dev(fam, seed_infamily_calib(lineage, fi, k))
        for fi, fam in enumerate(DEV_HELDOUT_FAMILIES)
        for k in range(per_family)
    ]


def infamily_val_tasks(lineage: int, per_family: int) -> list[NeuralTargetTaskV3]:
    return [
        build_heldout_task_dev(fam, seed_infamily_val(lineage, fi, k))
        for fi, fam in enumerate(DEV_HELDOUT_FAMILIES)
        for k in range(per_family)
    ]


def kfac_pool() -> list[dict[str, Any]]:
    """The sealed 56-point `kfac_no_proposer` grid (7 lr x 4 mixes x 2 decays)."""
    return _build_baseline_pools_56()["kfac_no_proposer"]


def cfg_key(cfg: dict[str, Any]) -> str:
    return json.dumps({"lr": cfg["lr"], "wd": cfg["weight_decay"], "bw": list(cfg["basis_weights"])})


def calibrate_kfac(tasks: list[NeuralTargetTaskV3], pool: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Score every grid point on `tasks` with the v3 calibration objective; return the best one."""
    pool = pool if pool is not None else kfac_pool()
    scored = []
    passes = 0
    for cfg in pool:
        vals = []
        for t in tasks:
            res = run_kfac_no_proposer_v3(cfg, t)
            passes += int(res["passes_used"])
            vals.append(smooth_anchor_score(res, t.loss_type))
        scored.append({"config": cfg, "mean_smooth_score": sum(vals) / len(vals)})
    best = min(scored, key=lambda x: x["mean_smooth_score"])
    return {"best_config": best["config"], "best_score": best["mean_smooth_score"], "all": scored, "passes": passes}


def _pack_metrics(init_m: dict[str, float], fin_m: dict[str, float], passes: int) -> dict[str, float]:
    return {
        "init_query_loss": init_m["query_loss"],
        "final_query_loss": fin_m["query_loss"],
        "final_support_loss": fin_m["support_loss"],
        "query_accuracy": fin_m.get("query_accuracy", 0.0),
        "query_hinge": fin_m.get("query_hinge", 0.0),
        "query_r2": fin_m.get("query_r2", 0.0),
        "passes_used": passes,
    }


def run_residual_cold(
    phi: ProposerWeightsV3 | None,
    base: KfacBaseConfig,
    task: NeuralTargetTaskV3,
    row_mode: str = "per_row",
    const_raw: torch.Tensor | None = None,
    record: list[dict] | None = None,
    return_layers: bool = False,
) -> dict[str, Any]:
    """Cold 10-pass run of the residual proposer (no gradient); mirrors `run_proposer_v3_cold`."""
    oracle = ChargedTargetOracleV3(task, allow_meta_query_pass=False)
    layers = task.clone_cold_layers(requires_grad=False)
    init_m = oracle.evaluate_query(layers)
    opt_state = init_opt_state_v3(layers)
    B = oracle.support_budget
    trajectory = []
    for s_idx in range(B):
        loss_s, grads_s, act_in, err_out = oracle.forward_backward_support(layers, differentiable_graph=False)
        with torch.no_grad():
            layers = propose_update_residual(
                phi=phi,
                base=base,
                layers=[w.detach() for w in layers],
                grads=[g.detach() for g in grads_s],
                act_inputs=act_in,
                err_outputs=err_out,
                opt_state=opt_state,
                step_idx=s_idx,
                total_steps=B,
                cur_loss=loss_s.detach(),
                differentiable_target=False,
                row_mode=row_mode,
                const_raw=const_raw,
                record=record,
            )
        if return_layers:
            trajectory.append([w.detach().clone() for w in layers])
    fin_m = oracle.evaluate_query(layers)
    assert oracle.passes_used == B
    out: dict[str, Any] = _pack_metrics(init_m, fin_m, oracle.passes_used)
    if return_layers:
        out["trajectory"] = trajectory
    return out


def kfac_trajectory(cfg: dict[str, Any], task: NeuralTargetTaskV3) -> list[list[torch.Tensor]]:
    """Per-step weights of the sealed-logic `kfac_no_proposer` update (same loop as the runner)."""
    from proposer_v4dev import compute_five_basis_v3

    oracle = ChargedTargetOracleV3(task)
    layers = task.clone_cold_layers(requires_grad=False)
    st = init_opt_state_v3(layers)
    B = oracle.support_budget
    w_vec = [float(x) for x in cfg["basis_weights"]]
    lr = float(cfg["lr"])
    wd = float(cfg["weight_decay"])
    traj = []
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
        traj.append([w.detach().clone() for w in layers])
    return traj


def diff_task_objective(
    phi: ProposerWeightsV3 | None,
    base: KfacBaseConfig,
    task: NeuralTargetTaskV3,
    row_mode: str = "per_row",
    const_raw: torch.Tensor | None = None,
    clip_hooks: bool = True,
) -> torch.Tensor:
    """Differentiable (second-order, 10-step unroll) v3 meta-objective for one task."""
    oracle = ChargedTargetOracleV3(task, allow_meta_query_pass=True)
    layers = task.clone_cold_layers(requires_grad=True)
    init_ql = oracle.evaluate_query(layers)["query_loss"]
    opt_st = init_opt_state_v3(layers)
    for s_idx in range(oracle.support_budget):
        loss_s, grads_s, act_in, err_out = oracle.forward_backward_support(layers, differentiable_graph=True)
        layers = propose_update_residual(
            phi=phi,
            base=base,
            layers=layers,
            grads=grads_s,
            act_inputs=act_in,
            err_outputs=err_out,
            opt_state=opt_st,
            step_idx=s_idx,
            total_steps=oracle.support_budget,
            cur_loss=loss_s,
            differentiable_target=True,
            row_mode=row_mode,
            const_raw=const_raw,
            clip_hooks=clip_hooks,
        )
    return oracle.evaluate_diff_query_v3(layers, init_ql)


def eval_score(
    phi: ProposerWeightsV3 | None,
    base: KfacBaseConfig,
    tasks: list[NeuralTargetTaskV3],
    row_mode: str = "per_row",
    const_raw: torch.Tensor | None = None,
) -> float:
    vals = []
    for t in tasks:
        res = run_residual_cold(phi, base, t, row_mode=row_mode, const_raw=const_raw)
        vals.append(smooth_anchor_score(res, t.loss_type))
    return sum(vals) / len(vals)


def meta_train_adam(
    arm: str,
    base: KfacBaseConfig,
    init_seed: int,
    task_fn: Callable[[int], NeuralTargetTaskV3],
    val_tasks: list[NeuralTargetTaskV3],
    n_steps: int,
    tasks_per_step: int,
    lr: float,
    val_every: int,
    clip_hooks: bool = True,
    grad_clip: float = 1.0,
    log: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Plain Adam meta-training, no accept/reject filter. Validation is used for early stopping only.

    arm = 'proposer' : train all 1,688 residual-proposer weights (row_mode 'per_row').
    arm = 'const'    : train only 8 raw constants (row_mode 'constant') on the same task stream.
    Step-0 validation is the untouched `kfac_no_proposer(base)` in both arms.
    """
    assert arm in ("proposer", "const")
    if arm == "proposer":
        phi = init_residual_proposer(init_seed)
        params = [w.requires_grad_(True) for w in phi.as_list()]
        phi = ProposerWeightsV3.from_list(params)
        const_raw = None
        row_mode = "per_row"
    else:
        phi = None
        const_raw = torch.zeros(OUT_DIM_V3, dtype=torch.float64, requires_grad=True)
        params = [const_raw]
        row_mode = "constant"

    def snapshot() -> list[float]:
        return torch.cat([p.detach().reshape(-1) for p in params]).tolist()

    def val_now() -> float:
        if arm == "proposer":
            return eval_score(phi.clone_detached(), base, val_tasks, row_mode="per_row")
        return eval_score(None, base, val_tasks, row_mode="constant", const_raw=const_raw.detach().clone())

    opt = torch.optim.Adam(params, lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, n_steps), eta_min=0.1 * lr)
    t0 = time.monotonic()
    val0 = val_now()
    best = {"step": 0, "val": val0, "flat": snapshot()}
    curve = [{"step": 0, "val": val0, "train_loss": None}]
    train_losses: list[float] = []
    step_rms: list[float] = []
    nonfinite_steps = 0
    for step in range(n_steps):
        opt.zero_grad()
        objs = []
        for i in range(tasks_per_step):
            objs.append(diff_task_objective(phi, base, task_fn(step * tasks_per_step + i), row_mode, const_raw, clip_hooks))
        loss = torch.stack(objs).mean()
        loss.backward()
        gnorm = torch.sqrt(sum((p.grad.pow(2).sum() for p in params)))
        if not (math.isfinite(float(loss.item())) and math.isfinite(float(gnorm.item()))):
            nonfinite_steps += 1
            sched.step()
            continue
        torch.nn.utils.clip_grad_norm_(params, grad_clip)
        before = torch.cat([p.detach().reshape(-1) for p in params]).clone()
        opt.step()
        sched.step()
        after = torch.cat([p.detach().reshape(-1) for p in params])
        step_rms.append(float((after - before).pow(2).mean().sqrt().item()))
        train_losses.append(float(loss.item()))
        if (step + 1) % val_every == 0 or step + 1 == n_steps:
            v = val_now()
            recent = train_losses[-val_every:]
            curve.append({"step": step + 1, "val": v, "train_loss": sum(recent) / len(recent)})
            if v < best["val"] - 1e-9:
                best = {"step": step + 1, "val": v, "flat": snapshot()}
            if log is not None:
                log(f"  [{arm}] step {step + 1}/{n_steps} train={curve[-1]['train_loss']:.4f} val={v:.4f} best={best['val']:.4f}@{best['step']} t={time.monotonic() - t0:.0f}s")
    return {
        "arm": arm,
        "n_steps": n_steps,
        "tasks_per_step": tasks_per_step,
        "meta_lr": lr,
        "clip_hooks": clip_hooks,
        "val_curve": curve,
        "val_step0_is_kfac_base": val0,
        "best_step": best["step"],
        "best_val": best["val"],
        "best_flat": best["flat"],
        "final_flat": snapshot(),
        "mean_step_rms": statistics.mean(step_rms) if step_rms else 0.0,
        "nonfinite_steps": nonfinite_steps,
        "upstream_passes": n_steps * tasks_per_step * 11 + len(curve) * len(val_tasks) * 10,
        "wall_s": time.monotonic() - t0,
    }


def row_from_result(res: dict[str, Any], task: NeuralTargetTaskV3, seed: int, lineage: int, arm: str) -> dict[str, Any]:
    r = {k: v for k, v in res.items() if k != "trajectory"}
    return {
        **r,
        "task_id": task.task_id,
        "family": task.family,
        "seed": int(seed),
        "loss_type": task.loss_type,
        "lineage": int(lineage),
        "arm": arm,
        "normalized_loss_ratio": normalized_loss_ratio(res),
        "smooth_score": smooth_anchor_score(res, task.loss_type),
    }


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=1, allow_nan=False) + "\n")
    os.replace(tmp, path)
