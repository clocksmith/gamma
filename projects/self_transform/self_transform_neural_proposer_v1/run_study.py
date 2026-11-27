"""End-to-end frozen runner for B2 (`self_transform_neural_proposer_v1`).

Executes:
1. Conventional optimizer calibration (`SGD+Nesterov`, `AdamW`, `Damped L-BFGS`) on disjoint calibration seeds
   (`seed = 610000..`, `8` tasks x `3` families = `24` calibration tasks) under the exact `B = 10` oracle budget.
2. Four-generation (`g = 0 -> 1 -> 2 -> 3 -> 4`) cold-subprocess hereditary evolution across TWO independent lineages:
   - Lineage A (`exact_cold_reconstruct`): Child `Phi_{g+1}` reconstructed in a fresh OS process with `state = None`.
   - Lineage B (`functional_self_regen`): Parent `Phi_{g+1}` queried ONLY via synthetic Gaussian probe inputs across an
     OS pipe (zero weights transmitted!); fresh random SwiGLU network `hat_Phi_{g+1}` distilled from behavior alone and
     used as the parent of generation `g + 2`!
3. Sealed cold-target confirmation across `16` fresh unseen seeds x `3` unseen neural target architectures (`48` cold
   neural networks, never touched during meta-training or calibration!), comparing:
   - `Gen-0 Fixed Proposer` (`M_Phi_0`)
   - `Gen-1..Gen-4 Exact Lineage` (`M_Phi_1 .. M_Phi_4`, cold subprocess, `state = None`)
   - `Gen-1..Gen-4 Functional Self-Regen Lineage` (`hat_M_Phi_1 .. hat_M_Phi_4`, cold subprocess, `state = None`)
   - `Tuned SGD + Nesterov`
   - `Tuned AdamW + Cosine`
   - `Tuned Damped L-BFGS`
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import comb
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
import torch

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from baselines import (
    calibrate_conventional_optimizers,
    run_adamw_cosine,
    run_damped_lbfgs,
    run_sgd_nesterov,
)
from proposer import FEAT_DIM, ProposerWeights, forward_proposer_net, init_gen0_proposer
from targets import CONFIRMATION_FAMILIES, build_target_family_task
from worker import weights_sha256


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def exact_sign_test_two_sided_p(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(comb(n, j) for j in range(k + 1)) / float(2 ** n)
    return min(1.0, 2.0 * tail)


def invoke_worker_subprocess(payload: dict[str, Any]) -> dict[str, Any]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }
    proc = subprocess.run(
        [sys.executable, str(THIS_DIR / "worker.py")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=True,
    )
    resp = json.loads(proc.stdout.strip().splitlines()[-1])
    assert resp.get("ok") is True, f"Worker failed: {proc.stderr}"
    assert resp["pid"] != os.getpid(), "Subprocess isolation violated!"
    return resp


def generate_synthetic_probes(seed: int, n_probes: int = 512) -> list[list[float]]:
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    X = torch.tanh(0.85 * torch.randn((n_probes, FEAT_DIM), generator=gen, dtype=torch.float64))
    # Ensure realistic structural feature ranges on depth/step columns 0..2 in [0, 1]
    X[:, 0:3] = torch.rand((n_probes, 3), generator=gen, dtype=torch.float64)
    return X.tolist()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--generations", type=int, default=4)
    ap.add_argument("--confirmation-seeds", type=int, default=16)
    ap.add_argument("--meta-steps", type=int, default=12)
    args = ap.parse_args()

    torch.set_num_threads(1)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    t_start = time.monotonic()

    code_hashes = {
        f: file_sha256(THIS_DIR / f)
        for f in ("proposer.py", "targets.py", "baselines.py", "worker.py", "run_study.py")
    }
    proto_path = args.output_json.with_suffix(".protocol.json")
    proto_path.write_text(json.dumps({
        "schema": "gamma.b2.self_transform_neural_proposer.protocol/v1",
        "generations": args.generations,
        "confirmation_seeds": args.confirmation_seeds,
        "meta_steps_per_gen": args.meta_steps,
        "cold_target_oracle_budget": 10,
        "confirmation_families": list(CONFIRMATION_FAMILIES),
        "meta_seed_base": 510000,
        "calibration_seed_base": 610000,
        "confirmation_seed_base": 710000,
        "code_sha256": code_hashes,
    }, indent=2))

    # Phase 1: Calibrate conventional optimizers on disjoint calibration tasks (seeds 610000..)
    cal_tasks = [
        build_target_family_task(fam, seed=610000 + f_i * 1000 + k)
        for f_i, fam in enumerate(CONFIRMATION_FAMILIES)
        for k in range(8)
    ]
    t_cal0 = time.monotonic()
    conv_cal = calibrate_conventional_optimizers(cal_tasks)
    cal_ms = (time.monotonic() - t_cal0) * 1000.0
    print(f"[b2] calibrated conventional optimizers in {cal_ms:.1f}ms: {json.dumps({k: v['best_config'] for k, v in conv_cal.items()})}", flush=True)

    # Phase 2: Evolve 4 generations in isolated cold subprocesses across BOTH Exact and Behavioral-Regen lineages!
    phi0 = init_gen0_proposer(seed=202611)
    phi0_flat = phi0.to_flat_list()

    exact_lineage: dict[int, list[float]] = {0: phi0_flat}
    regen_lineage: dict[int, list[float]] = {0: phi0_flat}
    lineage_receipts = {"exact": [], "behavioral_regen": []}
    subprocesses_spawned = 0

    for g in range(args.generations):
        # Lineage A: Exact cold subprocess self-improvement
        r_ex = invoke_worker_subprocess({
            "mode": "self_improve",
            "generation": g,
            "parent_weights": exact_lineage[g],
            "meta_seed": 510000,
            "meta_steps": args.meta_steps,
            "tasks_per_step": 4,
        })
        subprocesses_spawned += 1
        exact_lineage[g + 1] = r_ex["child_weights"]
        lineage_receipts["exact"].append({k: v for k, v in r_ex.items() if k != "child_weights"})
        print(
            f"[b2] Exact Gen {g}->{g+1} pid={r_ex['pid']} meta_val={r_ex['meta_val_ratio_before']:.4f}->{r_ex['meta_val_ratio_after']:.4f}",
            flush=True,
        )

        # Lineage B: Self-improve from regenerated parent `regen_lineage[g]`, THEN reconstruct child via weight-free probes!
        r_rg_imp = invoke_worker_subprocess({
            "mode": "self_improve",
            "generation": g,
            "parent_weights": regen_lineage[g],
            "meta_seed": 510000,
            "meta_steps": args.meta_steps,
            "tasks_per_step": 4,
        })
        subprocesses_spawned += 1
        teacher_phi = ProposerWeights.from_flat_list(r_rg_imp["child_weights"])
        probes_x = generate_synthetic_probes(seed=810000 + g * 97, n_probes=512)
        with torch.no_grad():
            probes_y = forward_proposer_net(teacher_phi, torch.tensor(probes_x, dtype=torch.float64))[0].tolist()

        # Spawn fresh child subprocess receiving ZERO weights — only `(probe_inputs, probe_outputs)`!
        r_rg_dist = invoke_worker_subprocess({
            "mode": "behavioral_regen",
            "probe_inputs": probes_x,
            "probe_outputs": probes_y,
            "regen_seed": 890000 + g * 137,
            "distill_steps": 240,
        })
        subprocesses_spawned += 1
        regen_w = r_rg_dist["regenerated_weights"]
        regen_lineage[g + 1] = regen_w

        # Measure raw parameter cosine & L2 distance between teacher and functionally regenerated child (proving non-triviality!)
        t_vec = torch.tensor(r_rg_imp["child_weights"], dtype=torch.float64)
        s_vec = torch.tensor(regen_w, dtype=torch.float64)
        raw_param_cos = float(((t_vec * s_vec).sum() / (t_vec.norm() * s_vec.norm()).clamp_min(1e-12)).item())
        raw_param_l2 = float((t_vec - s_vec).norm().item())

        lineage_receipts["behavioral_regen"].append({
            "generation_out": g + 1,
            "improve_pid": r_rg_imp["pid"],
            "regen_pid": r_rg_dist["pid"],
            "meta_val_ratio_before": r_rg_imp["meta_val_ratio_before"],
            "meta_val_ratio_after": r_rg_imp["meta_val_ratio_after"],
            "oracle_passes_billed": r_rg_imp["oracle_passes_billed"],
            "distill_steps_billed": r_rg_dist["distill_steps_billed"],
            "functional_mse_before": r_rg_dist["functional_mse_before"],
            "functional_mse_after": r_rg_dist["functional_mse_after"],
            "raw_parameter_cosine_vs_teacher": raw_param_cos,
            "raw_parameter_l2_vs_teacher": raw_param_l2,
            "regenerated_sha256": r_rg_dist["regenerated_sha256"],
        })
        print(
            f"[b2] Regen Gen {g}->{g+1} pid={r_rg_dist['pid']} func_mse={r_rg_dist['functional_mse_after']:.6f} raw_param_cos={raw_param_cos:.3f}",
            flush=True,
        )

    # Phase 3: Sealed cold-target confirmation across 16 fresh seeds x 3 unseen neural target families!
    conf_specs = [
        {"family": fam, "seed": 710000 + f_i * 1000 + s_i}
        for f_i, fam in enumerate(CONFIRMATION_FAMILIES)
        for s_i in range(args.confirmation_seeds)
    ]

    arm_weights_to_eval = {"gen0_fixed": phi0_flat}
    for g in range(1, args.generations + 1):
        arm_weights_to_eval[f"exact_gen{g}"] = exact_lineage[g]
        arm_weights_to_eval[f"regen_gen{g}"] = regen_lineage[g]

    arm_rows: dict[str, list[dict[str, Any]]] = {}
    for arm_name, w_flat in arm_weights_to_eval.items():
        r_eval = invoke_worker_subprocess({
            "mode": "evaluate_cold",
            "weights": w_flat,
            "tasks": conf_specs,
        })
        subprocesses_spawned += 1
        arm_rows[arm_name] = r_eval["results"]

    # Run calibrated conventional optimizers on the EXACT same 48 cold confirmation tasks & B=10 budget!
    for conv_name, fn in (
        ("sgd_nesterov", run_sgd_nesterov),
        ("adamw_cosine", run_adamw_cosine),
        ("damped_lbfgs", run_damped_lbfgs),
    ):
        cfg = conv_cal[conv_name]["best_config"]
        c_res = []
        for sp in conf_specs:
            task = build_target_family_task(sp["family"], sp["seed"])
            out = fn(cfg, task)
            c_res.append({"task_id": task.task_id, "family": task.family, "seed": sp["seed"], **out})
        arm_rows[conv_name] = c_res

    # Summarize per-family and pooled metrics + exact paired dominance gates
    family_summaries: dict[str, Any] = {}
    for fam in CONFIRMATION_FAMILIES:
        f_summary = {}
        for arm_name, r_list in arm_rows.items():
            sub = [r for r in r_list if r["family"] == fam]
            mean_ql = sum(r["final_query_loss"] for r in sub) / len(sub)
            mean_init = sum(r["init_query_loss"] for r in sub) / len(sub)
            rel_red = 100.0 * (mean_init - mean_ql) / max(mean_init, 1e-8)
            entry = {
                "mean_init_query_loss": mean_init,
                "mean_final_query_loss": mean_ql,
                "relative_loss_reduction_pct": rel_red,
            }
            if "cls" in fam or "adapter" in fam:
                entry["mean_query_accuracy"] = sum(r["query_accuracy"] for r in sub) / len(sub)
            else:
                entry["mean_query_r2"] = sum(r["query_r2"] for r in sub) / len(sub)
            f_summary[arm_name] = entry
        family_summaries[fam] = f_summary

    def compare_pair(focal_arm: str, ref_arm: str, fam_filter: str | None = None) -> dict[str, Any]:
        f_list = [r for r in arm_rows[focal_arm] if fam_filter is None or r["family"] == fam_filter]
        r_map = {r["task_id"]: r for r in arm_rows[ref_arm] if fam_filter is None or r["family"] == fam_filter}
        wins = 0
        losses = 0
        rel_gains = []
        for fr in f_list:
            rr = r_map[fr["task_id"]]
            if fr["final_query_loss"] < rr["final_query_loss"] - 1e-9:
                wins += 1
            elif fr["final_query_loss"] > rr["final_query_loss"] + 1e-9:
                losses += 1
            rel_gains.append(100.0 * (rr["final_query_loss"] - fr["final_query_loss"]) / max(rr["final_query_loss"], 1e-8))
        return {
            "focal_wins": wins,
            "ref_wins": losses,
            "total": len(f_list),
            "mean_relative_query_loss_gain_pct": sum(rel_gains) / len(rel_gains),
            "sign_test_two_sided_p": exact_sign_test_two_sided_p(wins, losses),
        }

    g_last = args.generations
    comparisons = {
        "pooled_48_tasks": {
            f"exact_gen{g_last}_vs_gen0_fixed": compare_pair(f"exact_gen{g_last}", "gen0_fixed"),
            f"exact_gen{g_last}_vs_exact_gen1": compare_pair(f"exact_gen{g_last}", "exact_gen1"),
            f"regen_gen{g_last}_vs_gen0_fixed": compare_pair(f"regen_gen{g_last}", "gen0_fixed"),
            f"regen_gen{g_last}_vs_regen_gen1": compare_pair(f"regen_gen{g_last}", "regen_gen1"),
            f"exact_gen{g_last}_vs_sgd_nesterov": compare_pair(f"exact_gen{g_last}", "sgd_nesterov"),
            f"exact_gen{g_last}_vs_adamw_cosine": compare_pair(f"exact_gen{g_last}", "adamw_cosine"),
            f"exact_gen{g_last}_vs_damped_lbfgs": compare_pair(f"exact_gen{g_last}", "damped_lbfgs"),
            f"regen_gen{g_last}_vs_sgd_nesterov": compare_pair(f"regen_gen{g_last}", "sgd_nesterov"),
            f"regen_gen{g_last}_vs_adamw_cosine": compare_pair(f"regen_gen{g_last}", "adamw_cosine"),
            f"regen_gen{g_last}_vs_damped_lbfgs": compare_pair(f"regen_gen{g_last}", "damped_lbfgs"),
        },
        "by_family": {
            fam: {
                f"exact_gen{g_last}_vs_gen0_fixed": compare_pair(f"exact_gen{g_last}", "gen0_fixed", fam),
                f"regen_gen{g_last}_vs_gen0_fixed": compare_pair(f"regen_gen{g_last}", "gen0_fixed", fam),
                f"exact_gen{g_last}_vs_sgd_nesterov": compare_pair(f"exact_gen{g_last}", "sgd_nesterov", fam),
                f"exact_gen{g_last}_vs_adamw_cosine": compare_pair(f"exact_gen{g_last}", "adamw_cosine", fam),
                f"exact_gen{g_last}_vs_damped_lbfgs": compare_pair(f"exact_gen{g_last}", "damped_lbfgs", fam),
                f"regen_gen{g_last}_vs_sgd_nesterov": compare_pair(f"regen_gen{g_last}", "sgd_nesterov", fam),
                f"regen_gen{g_last}_vs_adamw_cosine": compare_pair(f"regen_gen{g_last}", "adamw_cosine", fam),
                f"regen_gen{g_last}_vs_damped_lbfgs": compare_pair(f"regen_gen{g_last}", "damped_lbfgs", fam),
            }
            for fam in CONFIRMATION_FAMILIES
        },
    }

    receipt = {
        "schema": "gamma.b2.self_transform_neural_proposer.receipt/v1",
        "proposer_parameter_count": phi0.num_parameters(),
        "generations": args.generations,
        "confirmation_seeds_per_family": args.confirmation_seeds,
        "total_confirmation_tasks": len(conf_specs),
        "cold_target_oracle_budget": 10,
        "subprocesses_spawned": subprocesses_spawned,
        "elapsed_seconds": time.monotonic() - t_start,
        "code_sha256": code_hashes,
        "gen0_sha256": weights_sha256(phi0_flat),
        "conventional_calibration": conv_cal,
        "lineage_receipts": lineage_receipts,
        "family_summaries": family_summaries,
        "paired_comparisons": comparisons,
        "arm_rows": arm_rows,
    }
    args.output_json.write_text(json.dumps(receipt, indent=2))
    print(f"[b2] COMPLETE in {receipt['elapsed_seconds']:.1f}s | pooled={json.dumps(comparisons['pooled_48_tasks'])}", flush=True)


if __name__ == "__main__":
    main()
