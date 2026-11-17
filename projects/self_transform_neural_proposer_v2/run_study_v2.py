"""Multi-seed cumulative self-improvement confirmation runner for B2 v2 (Items 5–7).

Protocol:
- `S = 5` independent evolutionary lineage seeds (`LINEAGE_SEEDS = [101, 202, 303, 404, 505]`),
  each evolving across `G = 4` cold-subprocess generations (`g = 0 -> 1 -> 2 -> 3 -> 4`).
- Three proposer lineages per seed under explicit selection & reconstruction cost accounting:
  1. `exact` (`exact_gen0..gen4`): Recursive self-modification (`M_{Phi_g}` modifies `Phi_g`) across
     isolated OS subprocesses; consumes `1,320` upstream target-oracle passes/gen (`5,280` total,
     including `240` active-opponent passes + `120` parent-anchor passes + `960` proposal/selection passes).
  2. `regen` (`regen_gen1..gen4`): True 4-generation weight-free behavioral regeneration at EVERY
     generation boundary (`512` behavioral probes + `240` fresh-init distillation steps per boundary,
     zero weights crossing any generation boundary!); `1,320 * g` target passes + `80 * g` FLOP-equivalent
     reconstruction allowance = `1,400 * g` (`5,600`) total pass-equivalents.
  3. `fixed_proposer` (`fixed_proposer_gen1..gen4`): Identical `1,320 * g` budget, anchor, active
     opponents, and radii, except `self_modify_proposer_v2` keeps the proposer rule fixed at `M_{Phi_0}`.
- Conventional controls (`SGD+Nesterov`, `AdamW+Cosine`, `Damped L-BFGS`):
  Each receives `1,400 * g` (`1400, 2800, 4200, 5600`) upstream target-oracle passes (`14` configs/gen x
  `10` calibration tasks x `10` passes = `56` configs total), strictly `>=` both `exact` and `regen`
  budgets including full selection and behavioral reconstruction costs.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from math import comb
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import time
from typing import Any
import torch

THIS_DIR = Path(__file__).resolve().parent
V1_B2_DIR = THIS_DIR.parent / "self_transform_neural_proposer_v1"
for d in (THIS_DIR, V1_B2_DIR):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

from baselines import _pack_flat, _unpack_flat, _weight_decay_mask
from proposer_v2 import FEAT_DIM_V2, ProposerWeightsV2, forward_proposer_v2, init_gen0_proposer_v2
from tasks_b2_v2 import (
    ChargedTargetOracleV2,
    NeuralTargetTask,
    V2_CONFIRMATION_FAMILIES,
    build_progressive_meta_task,
    build_v2_confirmation_task,
)

LINEAGE_SEEDS = (101, 202, 303, 404, 505)
PROPOSER_PASSES_PER_GEN = 1320
CONV_PASSES_PER_GEN = 1400  # 1320 target passes + 80 reconstruction pass-equivalent allowance


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def exact_sign_p(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    return min(1.0, 2.0 * sum(comb(n, j) for j in range(k + 1)) / float(2 ** n))


def invoke_worker_v2(payload: dict[str, Any]) -> dict[str, Any]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }
    proc = subprocess.run(
        [sys.executable, str(THIS_DIR / "worker_v2.py")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=True,
    )
    resp = json.loads(proc.stdout.strip().splitlines()[-1])
    assert resp.get("ok") is True, f"worker_v2 failed: {proc.stderr}"
    assert resp["pid"] != os.getpid()
    return resp


def run_sgd_v2(cfg: dict[str, float], task: NeuralTargetTask) -> dict[str, float]:
    oracle = ChargedTargetOracleV2(task)
    layers = task.clone_cold_layers(requires_grad=False)
    init_m = oracle.evaluate_query(layers)
    lr, mom, wd = float(cfg["lr"]), float(cfg["momentum"]), float(cfg["weight_decay"])
    wd_mask = _weight_decay_mask(layers)
    theta = _pack_flat(layers)
    vel = torch.zeros_like(theta)
    B = oracle.budget
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
        "query_accuracy": fin_m.get("query_accuracy", 0.0),
        "query_r2": fin_m.get("query_r2", 0.0),
        "passes_used": oracle.passes_used,
    }


def run_adamw_v2(cfg: dict[str, float], task: NeuralTargetTask) -> dict[str, float]:
    oracle = ChargedTargetOracleV2(task)
    layers = task.clone_cold_layers(requires_grad=False)
    init_m = oracle.evaluate_query(layers)
    lr, b1, b2, wd = float(cfg["lr"]), float(cfg["beta1"]), float(cfg["beta2"]), float(cfg["weight_decay"])
    wd_mask = _weight_decay_mask(layers)
    theta = _pack_flat(layers)
    m_t = torch.zeros_like(theta)
    v_t = torch.zeros_like(theta)
    B = oracle.budget
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
        "query_accuracy": fin_m.get("query_accuracy", 0.0),
        "query_r2": fin_m.get("query_r2", 0.0),
        "passes_used": oracle.passes_used,
    }


def run_lbfgs_v2(cfg: dict[str, float], task: NeuralTargetTask) -> dict[str, float]:
    oracle = ChargedTargetOracleV2(task)
    layers = task.clone_cold_layers(requires_grad=False)
    init_m = oracle.evaluate_query(layers)
    lr, damp, wd, max_step = float(cfg["lr"]), float(cfg["damping"]), float(cfg["weight_decay"]), float(cfg["max_step"])
    wd_mask = _weight_decay_mask(layers)
    theta = _pack_flat(layers)
    loss0, grads0, _, _ = oracle.forward_backward_support(_unpack_flat(theta, layers), differentiable_graph=False)
    f_cur = float(loss0.item()) + 0.5 * wd * float((wd_mask * theta * theta).sum().item())
    g_cur = _pack_flat(grads0) + wd * wd_mask * theta
    s_hist, y_hist, rho_hist = [], [], []
    while oracle.passes_used < oracle.budget:
        q = g_cur.clone()
        alphas = []
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
                    s_hist.pop(0); y_hist.pop(0); rho_hist.pop(0)
                s_hist.append(s_k); y_hist.append(y_k); rho_hist.append(1.0 / sy_k)
            theta, f_cur, g_cur = cand_theta, f_cand, g_cand
        else:
            lr *= 0.45
    fin_m = oracle.evaluate_query(_unpack_flat(theta, layers))
    assert oracle.passes_used == oracle.budget
    return {
        "init_query_loss": init_m["query_loss"],
        "final_query_loss": fin_m["query_loss"],
        "query_accuracy": fin_m.get("query_accuracy", 0.0),
        "query_r2": fin_m.get("query_r2", 0.0),
        "passes_used": oracle.passes_used,
    }


def calibrate_conventional_by_budget(lineage_seed: int, generations: int = 4) -> dict[str, dict[int, dict[str, Any]]]:
    """Calibrate SGD+Nesterov, AdamW, and Damped L-BFGS at `1,400 * g` upstream pass budgets (`14` cfgs/gen x `100` passes)."""
    rng = random.Random(600000 + lineage_seed)
    cal_tasks = [
        build_progressive_meta_task(lineage_seed=lineage_seed + 19000, gen_idx=(k % 4), task_idx=k)
        for k in range(10)
    ]

    sgd_pool = [
        {"lr": lr, "momentum": mom, "weight_decay": wd}
        for lr in (0.01, 0.02, 0.035, 0.06, 0.10, 0.16, 0.28)
        for mom in (0.50, 0.70, 0.82, 0.90)
        for wd in (0.005, 0.03)
    ]  # 56 configs
    adam_pool = [
        {"lr": lr, "beta1": b1, "beta2": 0.98, "weight_decay": wd}
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

    out: dict[str, dict[int, dict[str, Any]]] = {}
    for name, pool, fn in (
        ("sgd_nesterov", sgd_pool, run_sgd_v2),
        ("adamw_cosine", adam_pool, run_adamw_v2),
        ("damped_lbfgs", lbfgs_pool, run_lbfgs_v2),
    ):
        ordered = list(pool)
        rng.shuffle(ordered)
        out[name] = {}
        best_ratio = float("inf")
        best_cfg = ordered[0]
        cum_passes = 0
        for g in range(1, generations + 1):
            slice_cfgs = ordered[(g - 1) * 14 : g * 14]  # 14 configs x 10 tasks x 10 passes = 1,400 passes!
            for cfg in slice_cfgs:
                ratios = []
                for ct in cal_tasks:
                    res = fn(cfg, ct)
                    cum_passes += res["passes_used"]
                    r = res["final_query_loss"] / max(res["init_query_loss"], 1e-6)
                    ratios.append(min(r, 10.0) if math.isfinite(r) else 10.0)
                mr = sum(ratios) / len(ratios)
                if mr < best_ratio:
                    best_ratio = mr
                    best_cfg = cfg
            assert cum_passes == CONV_PASSES_PER_GEN * g
            out[name][g] = {
                "best_config": best_cfg,
                "cal_mean_norm_ratio": best_ratio,
                "cumulative_upstream_passes": cum_passes,
            }
    return out


def generate_probes_v2(seed: int, n_probes: int = 512) -> list[list[float]]:
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    X = torch.tanh(0.85 * torch.randn((n_probes, FEAT_DIM_V2), generator=gen, dtype=torch.float64))
    X[:, 0:3] = torch.rand((n_probes, 3), generator=gen, dtype=torch.float64)
    X[:, 1] = (torch.rand(n_probes, generator=gen, dtype=torch.float64) > 0.7).double()
    return X.tolist()


def normalized_loss_ratio(row: dict[str, Any]) -> float:
    return min(10.0, float(row["final_query_loss"]) / max(float(row["init_query_loss"]), 1e-6))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=list(LINEAGE_SEEDS))
    ap.add_argument("--generations", type=int, default=4)
    ap.add_argument("--confirmation-seed-base", type=int, default=850000)
    ap.add_argument("--confirmation-tasks-per-family", type=int, default=16)
    args = ap.parse_args()

    torch.set_num_threads(1)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    t0_all = time.monotonic()

    hashes = {
        f: file_sha256(THIS_DIR / f)
        for f in ("proposer_v2.py", "tasks_b2_v2.py", "worker_v2.py", "run_study_v2.py")
    }
    args.output_json.with_suffix(".protocol.json").write_text(json.dumps({
        "schema": "gamma.b2.self_transform_neural_proposer_v2.protocol/v2",
        "lineage_seeds": args.seeds,
        "generations": args.generations,
        "proposer_target_passes_per_generation": PROPOSER_PASSES_PER_GEN,
        "regen_pass_equivalent_allowance_per_generation": 80,
        "conventional_passes_per_generation": CONV_PASSES_PER_GEN,
        "cold_target_oracle_budget": 10,
        "confirmation_seed_base": args.confirmation_seed_base,
        "confirmation_families": list(V2_CONFIRMATION_FAMILIES),
        "confirmation_tasks_per_family": args.confirmation_tasks_per_family,
        "code_sha256": hashes,
    }, indent=2))

    conf_specs = [
        {"family": fam, "seed": args.confirmation_seed_base + f_i * 1000 + k}
        for f_i, fam in enumerate(V2_CONFIRMATION_FAMILIES)
        for k in range(args.confirmation_tasks_per_family)
    ]
    conf_tasks_obj = [build_v2_confirmation_task(sp["family"], sp["seed"]) for sp in conf_specs]

    candidate_ledger: list[dict[str, Any]] = []
    per_seed_summaries: dict[str, Any] = {}
    curves_by_lineage: dict[str, dict[int, list[float]]] = {
        "exact": {g: [] for g in range(args.generations + 1)},
        "regen": {g: [] for g in range(args.generations + 1)},
        "fixed_proposer": {g: [] for g in range(args.generations + 1)},
    }
    subprocesses_spawned = 0
    pooled_pairs: dict[str, list[tuple[float, float]]] = {}

    for s in args.seeds:
        ts_seed = time.monotonic()
        conv_by_g = calibrate_conventional_by_budget(lineage_seed=s, generations=args.generations)

        phi0 = init_gen0_proposer_v2(seed=200000 + s)
        phi0_flat = phi0.to_flat_list()

        lineages_weights: dict[str, dict[int, list[float]]] = {
            "exact": {0: phi0_flat},
            "regen": {0: phi0_flat},
            "fixed_proposer": {0: phi0_flat},
        }
        lineages_traces: dict[str, list[dict[str, Any]]] = {"exact": [], "regen": [], "fixed_proposer": []}

        # Evolve all 3 proposer lineages across g = 0 .. G-1 in isolated OS subprocesses
        for lin_name in ("exact", "regen", "fixed_proposer"):
            cum_passes = 0
            cum_pass_equiv = 0
            cum_wall_ms = 0.0
            for g in range(args.generations):
                r_imp = invoke_worker_v2({
                    "mode": "self_improve_v2",
                    "lineage_tag": lin_name,
                    "lineage_seed": s,
                    "generation": g,
                    "parent_weights": lineages_weights[lin_name][g],
                    "fixed_proposer_weights": phi0_flat if lin_name == "fixed_proposer" else None,
                    "meta_batches": 3,
                    "train_tasks_per_batch": 4,
                    "anchor_tasks": 12,
                })
                subprocesses_spawned += 1
                cum_passes += r_imp["oracle_passes_billed"]
                cum_pass_equiv += r_imp["oracle_passes_billed"]
                cum_wall_ms += r_imp["wall_ms"]
                assert cum_passes == PROPOSER_PASSES_PER_GEN * (g + 1)
                candidate_ledger.extend(r_imp["candidates"])

                child_w = r_imp["child_weights"]
                regen_info = None
                if lin_name == "regen":
                    # True weight-free hereditary boundary at EVERY generation!
                    teacher_phi = ProposerWeightsV2.from_flat_list(child_w)
                    px = generate_probes_v2(seed=910000 + s * 10 + g, n_probes=512)
                    with torch.no_grad():
                        py = forward_proposer_v2(teacher_phi, torch.tensor(px, dtype=torch.float64))[0].tolist()
                    r_reg = invoke_worker_v2({
                        "mode": "behavioral_regen_v2",
                        "probe_inputs": px,
                        "probe_outputs": py,
                        "regen_seed": 950000 + s * 10 + g,
                        "distill_steps": 240,
                    })
                    subprocesses_spawned += 1
                    cum_pass_equiv += r_reg["oracle_pass_equivalent_allowance"]
                    cum_wall_ms += r_reg["wall_ms"]
                    t_vec = torch.tensor(child_w, dtype=torch.float64)
                    s_vec = torch.tensor(r_reg["regenerated_weights"], dtype=torch.float64)
                    raw_cos = float(((t_vec * s_vec).sum() / (t_vec.norm() * s_vec.norm()).clamp_min(1e-12)).item())
                    child_w = r_reg["regenerated_weights"]
                    regen_info = {
                        "regen_pid": r_reg["pid"],
                        "functional_mse_after": r_reg["functional_mse_after"],
                        "raw_parameter_cosine_vs_teacher": raw_cos,
                        "reconstruction_flops_estimated": r_reg["reconstruction_flops_estimated"],
                        "regen_wall_ms": r_reg["wall_ms"],
                    }

                lineages_weights[lin_name][g + 1] = child_w
                lineages_traces[lin_name].append({
                    "generation": g + 1,
                    "pid": r_imp["pid"],
                    "active_opponent": r_imp["active_opponent"],
                    "parent_sha256": r_imp["parent_sha256"],
                    "child_sha256": r_imp["child_sha256"],
                    "anchor_val_before": r_imp["anchor_val_before"],
                    "anchor_val_after": r_imp["anchor_val_after"],
                    "accepted_proposals": sum(1 for c in r_imp["candidates"] if c["accepted"]),
                    "cumulative_target_passes": cum_passes,
                    "cumulative_total_pass_equivalents": cum_pass_equiv,
                    "cumulative_wall_ms": cum_wall_ms,
                    "behavioral_regen": regen_info,
                })

        # Evaluate cold confirmation performance across all generations & budget-matched controls
        eval_rows_by_arm: dict[str, list[dict[str, Any]]] = {}
        r_g0 = invoke_worker_v2({"mode": "evaluate_cold_v2", "weights": phi0_flat, "tasks": conf_specs})
        subprocesses_spawned += 1
        eval_rows_by_arm["gen0"] = r_g0["results"]

        for lin_name in ("exact", "regen", "fixed_proposer"):
            eval_rows_by_arm[f"{lin_name}_gen0"] = eval_rows_by_arm["gen0"]
            for g in range(1, args.generations + 1):
                r_ev = invoke_worker_v2({"mode": "evaluate_cold_v2", "weights": lineages_weights[lin_name][g], "tasks": conf_specs})
                subprocesses_spawned += 1
                eval_rows_by_arm[f"{lin_name}_gen{g}"] = r_ev["results"]

        G_final = args.generations
        for cname, cfn in (("sgd_nesterov", run_sgd_v2), ("adamw_cosine", run_adamw_v2), ("damped_lbfgs", run_lbfgs_v2)):
            cfg_cache: dict[str, list[dict[str, Any]]] = {}
            for g in range(1, G_final + 1):
                cfg_g = conv_by_g[cname][g]["best_config"]
                ck = json.dumps(cfg_g, sort_keys=True)
                if ck not in cfg_cache:
                    cfg_cache[ck] = [
                        {"task_id": t.task_id, "family": t.family, **cfn(cfg_g, t)}
                        for t in conf_tasks_obj
                    ]
                eval_rows_by_arm[f"{cname}_b{CONV_PASSES_PER_GEN * g}"] = cfg_cache[ck]

        heldout_curve = {}
        for arm_k, r_list in eval_rows_by_arm.items():
            mean_ratio = statistics.mean(normalized_loss_ratio(r) for r in r_list)
            by_fam = {}
            for fam in V2_CONFIRMATION_FAMILIES:
                sub = [r for r in r_list if r["family"] == fam]
                by_fam[fam] = {
                    "mean_final_query_loss": statistics.mean(r["final_query_loss"] for r in sub),
                    "mean_norm_loss_ratio": statistics.mean(normalized_loss_ratio(r) for r in sub),
                    "mean_query_accuracy": statistics.mean(r["query_accuracy"] for r in sub) if ("cls" in fam or "adapter" in fam) else None,
                    "mean_query_r2": statistics.mean(r["query_r2"] for r in sub) if "reg" in fam else None,
                }
            heldout_curve[arm_k] = {"pooled_mean_norm_loss_ratio": mean_ratio, "by_family": by_fam}

        for lin_name in ("exact", "regen", "fixed_proposer"):
            for g in range(args.generations + 1):
                curves_by_lineage[lin_name][g].append(heldout_curve[f"{lin_name}_gen{g}"]["pooled_mean_norm_loss_ratio"])

        # Paired comparisons across generations, fixed-proposer control, and equal/higher-budget conventional controls
        for lin_name in ("exact", "regen"):
            for g in range(1, G_final + 1):
                g_rows = eval_rows_by_arm[f"{lin_name}_gen{g}"]
                for ref_arm in (
                    "gen0",
                    f"fixed_proposer_gen{g}",
                    f"sgd_nesterov_b{CONV_PASSES_PER_GEN * g}",
                    f"adamw_cosine_b{CONV_PASSES_PER_GEN * g}",
                    f"damped_lbfgs_b{CONV_PASSES_PER_GEN * g}",
                ):
                    ref_rows = eval_rows_by_arm[ref_arm]
                    pooled_pairs.setdefault(f"{lin_name}_gen{g}_vs_{ref_arm}", []).extend(
                        (fr["final_query_loss"], rr["final_query_loss"]) for fr, rr in zip(g_rows, ref_rows)
                    )
            fin_rows = eval_rows_by_arm[f"{lin_name}_gen{G_final}"]
            for prev_g in range(1, G_final):
                prev_rows = eval_rows_by_arm[f"{lin_name}_gen{prev_g}"]
                pooled_pairs.setdefault(f"{lin_name}_gen{G_final}_vs_{lin_name}_gen{prev_g}", []).extend(
                    (fr["final_query_loss"], rr["final_query_loss"]) for fr, rr in zip(fin_rows, prev_rows)
                )

        per_seed_summaries[str(s)] = {
            "seed": s,
            "elapsed_s": time.monotonic() - ts_seed,
            "lineages_traces": lineages_traces,
            "conventional_calibration_by_gen": conv_by_g,
            "heldout_confirmation": heldout_curve,
        }
        ex_str = " -> ".join(f"g{g}={heldout_curve[f'exact_gen{g}']['pooled_mean_norm_loss_ratio']:.4f}" for g in range(G_final + 1))
        rg_str = " -> ".join(f"g{g}={heldout_curve[f'regen_gen{g}']['pooled_mean_norm_loss_ratio']:.4f}" for g in range(G_final + 1))
        fp_fin = heldout_curve[f"fixed_proposer_gen{G_final}"]["pooled_mean_norm_loss_ratio"]
        print(
            f"[b2-v2] seed={s} | exact: {ex_str} | regen: {rg_str} | fixed_prop_g4={fp_fin:.4f} | "
            f"sgd={heldout_curve[f'sgd_nesterov_b{CONV_PASSES_PER_GEN*G_final}']['pooled_mean_norm_loss_ratio']:.4f} "
            f"adamw={heldout_curve[f'adamw_cosine_b{CONV_PASSES_PER_GEN*G_final}']['pooled_mean_norm_loss_ratio']:.4f} "
            f"lbfgs={heldout_curve[f'damped_lbfgs_b{CONV_PASSES_PER_GEN*G_final}']['pooled_mean_norm_loss_ratio']:.4f}",
            flush=True,
        )

    paired_summary = {}
    for comp_name, pairs in pooled_pairs.items():
        wins = sum(1 for (f_v, r_v) in pairs if f_v < r_v - 1e-9)
        losses = sum(1 for (f_v, r_v) in pairs if f_v > r_v + 1e-9)
        rel_gains = [max(-200.0, min(100.0, 100.0 * (r_v - f_v) / max(r_v, 1e-8))) for (f_v, r_v) in pairs]
        paired_summary[comp_name] = {
            "focal_wins": wins,
            "ref_wins": losses,
            "total_pairs": len(pairs),
            "clipped_mean_relative_gain_pct": statistics.mean(rel_gains),
            "sign_test_two_sided_p": exact_sign_p(wins, losses),
        }

    mean_curves = {
        lin_name: {
            f"gen{g}": {
                "mean_norm_loss_ratio": statistics.mean(curves_by_lineage[lin_name][g]),
                "std_across_seeds": statistics.pstdev(curves_by_lineage[lin_name][g]),
                "per_seed": curves_by_lineage[lin_name][g],
            }
            for g in range(args.generations + 1)
        }
        for lin_name in ("exact", "regen", "fixed_proposer")
    }

    receipt = {
        "schema": "gamma.b2.self_transform_neural_proposer_v2.receipt/v2",
        "proposer_parameter_count": init_gen0_proposer_v2(101).num_parameters(),
        "lineage_seeds": args.seeds,
        "generations": args.generations,
        "proposer_target_passes_per_generation": PROPOSER_PASSES_PER_GEN,
        "regen_pass_equivalent_allowance_per_generation": 80,
        "conventional_passes_per_generation": CONV_PASSES_PER_GEN,
        "cold_target_oracle_budget": 10,
        "confirmation_tasks_per_seed": len(conf_specs),
        "total_candidate_proposals_logged": len(candidate_ledger),
        "subprocesses_spawned": subprocesses_spawned,
        "elapsed_seconds": time.monotonic() - t0_all,
        "code_sha256": hashes,
        "generational_heldout_curves": mean_curves,
        "pooled_paired_comparisons": paired_summary,
        "per_seed_summaries": per_seed_summaries,
        "candidate_ledger": candidate_ledger,
    }
    args.output_json.write_text(json.dumps(receipt, indent=2))
    print(f"[b2-v2] COMPLETE in {receipt['elapsed_seconds']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
