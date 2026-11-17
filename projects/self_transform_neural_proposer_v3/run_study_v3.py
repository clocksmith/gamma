"""Track B2 v3 confirmation runner and pre-registered lineage-level statistical evaluator.

Default invocation (`python run_study_v3.py`) performs a read-only preflight verifying
both `protocol_v3.json` (Commit 1 core lock) and `protocol_addendum_v3.json` (Commit 2
additive lock binding `tasks_b2_v3.py`, `run_study_v3.py`, and the locally provisioned
stock `Qwen/Qwen3.5-0.8B` checkpoint and tokenizer digests) without opening any
confirmation target.

Pass `--execute --output <dir>` only after both protocol locks pass. Retains all
per-task `rows`, candidate ledgers, wall-clock timings, and exact lineage-level
(`S = 12`) paired `t`, exact Wilcoxon signed-rank, and exact sign tests.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def preflight(verify_checkpoint: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol_path = HERE / "protocol_v3.json"
    addendum_path = HERE / "protocol_addendum_v3.json"
    protocol = json.loads(protocol_path.read_text())
    for name, expected in protocol["locked_code_sha256"].items():
        if digest(HERE / name) != expected:
            raise ValueError(f"Locked Commit-1 source changed: {name}")

    if not addendum_path.is_file():
        raise FileNotFoundError("protocol_addendum_v3.json missing")
    addendum = json.loads(addendum_path.read_text())
    if digest(protocol_path) != addendum["protocol_v3_sha256"]:
        raise ValueError("protocol_v3.json digest mismatch against addendum")
    for name, expected in addendum["bound_code_sha256"].items():
        if digest(HERE / name) != expected:
            raise ValueError(f"Bound Commit-2 source changed: {name}")

    if verify_checkpoint:
        from tasks_b2_v3 import QWEN35_LOCAL_DIR, QWEN35_SAFETENSORS_FILE

        tok_path = QWEN35_LOCAL_DIR / "tokenizer.json"
        if not QWEN35_SAFETENSORS_FILE.is_file() or not tok_path.is_file():
            raise FileNotFoundError("Provisioned Qwen/Qwen3.5-0.8B checkpoint/tokenizer missing")
        if digest(QWEN35_SAFETENSORS_FILE) != addendum["bound_assets_sha256"]["model_safetensors"]:
            raise ValueError("Qwen/Qwen3.5-0.8B safetensors SHA-256 mismatch")
        if digest(tok_path) != addendum["bound_assets_sha256"]["tokenizer_json"]:
            raise ValueError("Qwen/Qwen3.5-0.8B tokenizer.json SHA-256 mismatch")

    return protocol, addendum


def confirmation_specs(protocol: dict[str, Any], seed_index: int) -> list[dict[str, Any]]:
    if seed_index < 0 or seed_index >= len(protocol["lineage_seeds"]):
        raise ValueError("Unknown lineage index")
    base = int(protocol["confirmation_seed_base"])
    if base < int(protocol["confirmation_seed_minimum_lock"]):
        raise ValueError("confirmation_seed_base violates minimum lock")
    count = int(protocol["confirmation_tasks_per_family_per_seed"])
    fams = list(protocol["confirmation_families"])
    if count >= 1000 or len(fams) >= 10:
        raise ValueError("Protocol seed offsets would overlap")
    return [
        {"family": family, "seed": base + seed_index * 10000 + fi * 1000 + ti}
        for fi, family in enumerate(fams)
        for ti in range(count)
    ]


def invoke_worker(request: dict[str, Any], timeout: int = 3600) -> dict[str, Any]:
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    run = subprocess.run(
        [sys.executable, "-B", str(HERE / "worker_v3.py")],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        timeout=timeout,
        env=env,
    )
    if run.returncode != 0:
        raise RuntimeError("Worker failed: " + run.stderr[-4000:])
    result = json.loads(run.stdout.strip().splitlines()[-1])
    if result.get("ok") is not True:
        raise RuntimeError("Worker did not confirm success")
    return result


def save_atomic(path: Path, value: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    os.replace(tmp, path)


def _student_t_two_sided_p(t_stat: float, df: int) -> float:
    """Exact two-sided Student-t p-value via numerical Simpson integration of the t PDF."""
    if df <= 0 or not math.isfinite(t_stat):
        return 1.0
    t_abs = abs(float(t_stat))
    if t_abs == 0.0:
        return 1.0
    # Transform u = df / (df + x^2) in (0, 1]; P(|T| >= t_abs) = I_{u0}(df/2, 1/2)
    u0 = float(df) / (float(df) + t_abs * t_abs)
    a = 0.5 * float(df)
    b = 0.5
    log_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    n_steps = 2000
    h = u0 / n_steps

    def f(u: float) -> float:
        if u <= 0.0:
            return 0.0
        if u >= 1.0:
            u = 1.0 - 1e-15
        return math.exp((a - 1.0) * math.log(u) + (b - 1.0) * math.log(1.0 - u) - log_beta)

    acc = f(0.0) + f(u0)
    for i in range(1, n_steps):
        acc += (4.0 if (i % 2 == 1) else 2.0) * f(i * h)
    p = (h / 3.0) * acc
    return max(0.0, min(1.0, p))


def exact_sign_two_sided_p(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(math.comb(n, j) for j in range(k + 1)) / float(2 ** n)
    return min(1.0, 2.0 * tail)


def exact_wilcoxon_signed_rank_two_sided_p(diffs: list[float], tol: float = 1e-12) -> float:
    """Exact two-sided Wilcoxon signed-rank p-value via full 2^m sign enumeration (exact for m <= 20)."""
    nz = [float(d) for d in diffs if abs(d) > tol]
    m = len(nz)
    if m == 0:
        return 1.0
    abs_sorted = sorted((abs(d), idx) for idx, d in enumerate(nz))
    ranks = [0.0] * m
    i = 0
    while i < m:
        j = i
        while j + 1 < m and abs(abs_sorted[j + 1][0] - abs_sorted[i][0]) <= tol:
            j += 1
        avg_rank = 0.5 * ((i + 1) + (j + 1))
        for k in range(i, j + 1):
            ranks[abs_sorted[k][1]] = avg_rank
        i = j + 1

    w_pos = sum(ranks[idx] for idx, d in enumerate(nz) if d > 0.0)
    total_rank_sum = 0.5 * m * (m + 1)
    obs_dev = abs(w_pos - 0.5 * total_rank_sum)

    extreme = 0
    for mask in range(1 << m):
        s = 0.0
        for bit in range(m):
            if (mask >> bit) & 1:
                s += ranks[bit]
        if abs(s - 0.5 * total_rank_sum) >= obs_dev - 1e-12:
            extreme += 1
    return min(1.0, float(extreme) / float(1 << m))


def paired_lineage_summary(focal_vals: list[float], ref_vals: list[float], higher_is_better: bool) -> dict[str, Any]:
    assert len(focal_vals) == len(ref_vals) and len(focal_vals) >= 2
    n = len(focal_vals)
    # Signed improvement: positive means focal is better than ref
    imp = [
        (f - r) if higher_is_better else (r - f)
        for f, r in zip(focal_vals, ref_vals)
    ]
    raw_diff = [f - r for f, r in zip(focal_vals, ref_vals)]
    mean_diff = statistics.mean(raw_diff)
    sd_diff = statistics.stdev(raw_diff)
    if sd_diff > 1e-15:
        t_stat = mean_diff / (sd_diff / math.sqrt(n))
        t_p = _student_t_two_sided_p(t_stat, df=n - 1)
    elif abs(mean_diff) > 1e-15:
        t_stat = math.copysign(1e9, mean_diff)
        t_p = 0.0
    else:
        t_stat = 0.0
        t_p = 1.0
    wins = sum(1 for x in imp if x > 1e-12)
    losses = sum(1 for x in imp if x < -1e-12)
    ties = n - wins - losses
    return {
        "n_lineages": n,
        "focal_mean": statistics.mean(focal_vals),
        "focal_sd": statistics.stdev(focal_vals),
        "ref_mean": statistics.mean(ref_vals),
        "ref_sd": statistics.stdev(ref_vals),
        "mean_diff_focal_minus_ref": mean_diff,
        "sd_diff": sd_diff,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "t_stat": t_stat,
        "two_sided_t_p": t_p,
        "exact_wilcoxon_two_sided_p": exact_wilcoxon_signed_rank_two_sided_p(imp),
        "exact_sign_two_sided_p": exact_sign_two_sided_p(wins, losses),
        "per_seed_focal_minus_ref": raw_diff,
    }


def _run_single_lineage_seed(args_tuple: tuple[int, int, dict[str, Any]]) -> dict[str, Any]:
    seed_idx, seed, protocol = args_tuple
    import torch
    from baselines_v3 import BASELINE_RUNNERS_V3, calibrate_all_baselines_v3, normalized_loss_ratio
    from proposer_v3 import FEAT_DIM_V3, ProposerWeightsV3, forward_proposer_v3, init_gen0_proposer_v3
    from tasks_b2_v3 import build_v3_confirmation_task

    torch.set_num_threads(1)
    t0 = time.monotonic()

    # 1. Calibrate all 6 baselines beforehand on upstream calibration tasks (strictly disjoint from confirmation)
    t_cal0 = time.monotonic()
    calibration = calibrate_all_baselines_v3(seed, int(protocol["generations"]))
    cal_wall_ms = (time.monotonic() - t_cal0) * 1000.0

    initial = init_gen0_proposer_v3(seed).to_flat_list()
    states = {name: list(initial) for name in ("exact", "regen", "fixed_proposer")}
    specs = confirmation_specs(protocol, seed_idx)

    lineage_traces: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    subprocesses_spawned = 0

    for generation in range(int(protocol["generations"]) + 1):
        for name in ("exact", "regen", "fixed_proposer"):
            if generation > 0:
                req: dict[str, Any] = {
                    "mode": "self_improve_v3",
                    "lineage_seed": seed,
                    "generation": generation - 1,
                    "parent_weights": states[name],
                    "lineage_tag": name,
                    "meta_steps": int(protocol["meta_steps_per_generation"]),
                    "train_tasks_per_step": int(protocol["meta_train_tasks_per_step"]),
                    "anchor_tasks": int(protocol["validation_anchor_tasks"]),
                }
                if name == "fixed_proposer":
                    req["fixed_proposer_weights"] = initial
                result = invoke_worker(req)
                subprocesses_spawned += 1
                if int(result["oracle_passes_billed"]) != int(protocol["proposer_exact_passes_per_generation"]):
                    raise ValueError("Actual exact pass billing differs from locked protocol")
                states[name] = result["child_weights"]
                result_slim = {k: v for k, v in result.items() if k != "child_weights"}
                trace: dict[str, Any] = {
                    "seed": seed,
                    "lineage": name,
                    "generation": generation,
                    "self_improve": result_slim,
                }
                if name == "regen":
                    gen_rng = torch.Generator().manual_seed(910000 + seed * 10 + generation)
                    x_probe = torch.randn(
                        (int(protocol["behavioral_regen_probes"]), FEAT_DIM_V3),
                        generator=gen_rng,
                        dtype=torch.float64,
                    )
                    teacher = ProposerWeightsV3.from_flat_list(states[name])
                    with torch.no_grad():
                        y_probe = forward_proposer_v3(teacher, x_probe, capture_activations=False)[0]
                    regen = invoke_worker({
                        "mode": "behavioral_regen_v3",
                        "probe_inputs": x_probe.tolist(),
                        "probe_outputs": y_probe.tolist(),
                        "regen_seed": 950000 + seed * 10 + generation,
                        "distill_steps": int(protocol["behavioral_regen_distill_steps"]),
                        "mean_target_pass_flops": result["measured_mean_target_pass_flops"],
                    })
                    subprocesses_spawned += 1
                    total_rg_passes = int(result["oracle_passes_billed"]) + int(regen["oracle_pass_equivalents_billed"])
                    if total_rg_passes > int(protocol["conventional_regen_matched_passes_per_generation"]):
                        raise ValueError(f"Regen pass-equivalents {total_rg_passes} exceed matched control budget")
                    states[name] = regen["regenerated_weights"]
                    trace["regeneration"] = {k: v for k, v in regen.items() if k != "regenerated_weights"}
                lineage_traces.append(trace)

            # Evaluate cold confirmation targets in isolated subprocess (for gen 0 evaluate once under 'gen0' + per-lineage)
            if generation == 0 and name != "exact":
                # Gen 0 weights are identical across exact/regen/fixed_proposer; duplicate rows without redundant subprocess
                for r0 in [r for r in rows if r["generation"] == 0 and r["arm"] == "exact_gen0"]:
                    rows.append({**r0, "arm": f"{name}_gen0"})
                continue

            evaluated = invoke_worker({
                "mode": "evaluate_cold_v3",
                "weights": states[name],
                "tasks": specs,
                "allow_synthetic_qwen_fallback": False,
            })
            subprocesses_spawned += 1
            arm_label = f"{name}_gen{generation}"
            for row in evaluated["results"]:
                r_entry = {
                    **row,
                    "lineage_seed": seed,
                    "generation": generation,
                    "arm": arm_label,
                    "budget": "exact" if name != "regen" else "regen",
                    "normalized_loss_ratio": normalized_loss_ratio(row),
                }
                rows.append(r_entry)
                if generation == 0 and name == "exact":
                    rows.append({**r_entry, "arm": "gen0"})

    # Evaluate all 6 baselines at Generation 4 (both exact_matched=4800 and regen_matched=5600) AND Gen 1..3 for curves
    built_tasks = [
        (spec, build_v3_confirmation_task(**spec, allow_synthetic_qwen_fallback=False))
        for spec in specs
    ]
    for generation in range(1, int(protocol["generations"]) + 1):
        for bname, runner in BASELINE_RUNNERS_V3.items():
            for budget_tag in ("exact_matched", "regen_matched"):
                configured = calibration[bname][budget_tag][generation]
                arm_label = f"{bname}_{budget_tag}_gen{generation}"
                for spec, task in built_tasks:
                    row = runner(configured["best_config"], task)
                    rows.append({
                        **row,
                        "task_id": task.task_id,
                        "family": task.family,
                        "seed": int(spec["seed"]),
                        "loss_type": task.loss_type,
                        "lineage_seed": seed,
                        "generation": generation,
                        "arm": arm_label,
                        "budget": budget_tag,
                        "normalized_loss_ratio": normalized_loss_ratio(row),
                    })

    return {
        "seed": seed,
        "elapsed_s": time.monotonic() - t0,
        "calibration_wall_ms": cal_wall_ms,
        "subprocesses_spawned": subprocesses_spawned,
        "calibration": calibration,
        "lineages": lineage_traces,
        "rows": rows,
    }


def analyze_receipt(rows: list[dict[str, Any]], lineages: list[dict[str, Any]], protocol: dict[str, Any]) -> dict[str, Any]:
    seeds = [int(s) for s in protocol["lineage_seeds"]]
    cls_fams = [f for f in protocol["confirmation_families"] if f != "fourier_kan_multifreq_reg"]
    reg_fam = "fourier_kan_multifreq_reg"
    real_fam = "real_qwen35_swiglu_lora_cls"

    by_arm_seed: dict[tuple[str, int], list[dict[str, Any]]] = {}
    arms_present: list[str] = []
    for r in rows:
        arm = str(r["arm"])
        if arm not in arms_present:
            arms_present.append(arm)
        by_arm_seed.setdefault((arm, int(r["lineage_seed"])), []).append(r)

    arm_seed_metrics: dict[str, dict[str, list[float]]] = {}
    arm_summaries: dict[str, Any] = {}
    for arm in arms_present:
        norm_v, cls_v, reg_v, real_v, real_loss_v = [], [], [], [], []
        by_fam_acc: dict[str, list[float]] = {f: [] for f in protocol["confirmation_families"]}
        by_fam_norm: dict[str, list[float]] = {f: [] for f in protocol["confirmation_families"]}
        for s in seeds:
            rs = by_arm_seed[(arm, s)]
            norm_v.append(statistics.mean(x["normalized_loss_ratio"] for x in rs))
            cls_v.append(statistics.mean(x["query_accuracy"] for x in rs if x["family"] in cls_fams))
            reg_v.append(statistics.mean(x["query_r2"] for x in rs if x["family"] == reg_fam))
            real_v.append(statistics.mean(x["query_accuracy"] for x in rs if x["family"] == real_fam))
            real_loss_v.append(statistics.mean(x["normalized_loss_ratio"] for x in rs if x["family"] == real_fam))
            for f in protocol["confirmation_families"]:
                frs = [x for x in rs if x["family"] == f]
                by_fam_norm[f].append(statistics.mean(x["normalized_loss_ratio"] for x in frs))
                key_m = "query_r2" if f == reg_fam else "query_accuracy"
                by_fam_acc[f].append(statistics.mean(x[key_m] for x in frs))

        arm_seed_metrics[arm] = {
            "norm_loss_ratio": norm_v,
            "cls_accuracy": cls_v,
            "reg_r2": reg_v,
            "real_qwen35_accuracy": real_v,
            "real_qwen35_norm_loss": real_loss_v,
        }
        arm_summaries[arm] = {
            "mean_norm_loss_ratio": statistics.mean(norm_v),
            "sd_norm_loss_ratio": statistics.stdev(norm_v),
            "mean_cls_accuracy": statistics.mean(cls_v),
            "sd_cls_accuracy": statistics.stdev(cls_v),
            "mean_reg_r2": statistics.mean(reg_v),
            "sd_reg_r2": statistics.stdev(reg_v),
            "mean_real_qwen35_accuracy": statistics.mean(real_v),
            "sd_real_qwen35_accuracy": statistics.stdev(real_v),
            "by_family": {
                f: {
                    "mean_norm_loss_ratio": statistics.mean(by_fam_norm[f]),
                    "sd_norm_loss_ratio": statistics.stdev(by_fam_norm[f]),
                    "mean_primary_metric": statistics.mean(by_fam_acc[f]),
                    "sd_primary_metric": statistics.stdev(by_fam_acc[f]),
                }
                for f in protocol["confirmation_families"]
            },
            "per_seed_norm_loss_ratio": norm_v,
            "per_seed_cls_accuracy": cls_v,
            "per_seed_reg_r2": reg_v,
            "per_seed_real_qwen35_accuracy": real_v,
        }

    # Acceptance rate across generations
    acc_rates_by_gen: dict[str, dict[int, float]] = {}
    for ltag in ("exact", "regen", "fixed_proposer"):
        acc_rates_by_gen[ltag] = {}
        for g in range(1, int(protocol["generations"]) + 1):
            trs = [t for t in lineages if t["lineage"] == ltag and int(t["generation"]) == g]
            rates = [
                sum(1 for c in t["self_improve"]["candidates"] if c.get("accepted")) / max(1, len(t["self_improve"]["candidates"]))
                for t in trs
            ]
            acc_rates_by_gen[ltag][g] = statistics.mean(rates)

    # Lineage-level paired tests (S = len(seeds))
    G = int(protocol["generations"])
    ex_top = f"exact_gen{G}"
    rg_top = f"regen_gen{G}"
    fx_top = f"fixed_proposer_gen{G}"
    comparisons: dict[str, Any] = {}
    ref_arms = (
        ["gen0"]
        + [f"exact_gen{g}" for g in range(1, G)]
        + [fx_top]
        + [f"{b}_exact_matched_gen{G}" for b in protocol["required_baselines"]]
        + [f"{b}_regen_matched_gen{G}" for b in protocol["required_baselines"]]
    )
    for ref in ref_arms:
        comparisons[f"{ex_top}_vs_{ref}"] = {
            "norm_loss_ratio": paired_lineage_summary(
                arm_seed_metrics[ex_top]["norm_loss_ratio"],
                arm_seed_metrics[ref]["norm_loss_ratio"],
                higher_is_better=False,
            ),
            "cls_accuracy": paired_lineage_summary(
                arm_seed_metrics[ex_top]["cls_accuracy"],
                arm_seed_metrics[ref]["cls_accuracy"],
                higher_is_better=True,
            ),
            "reg_r2": paired_lineage_summary(
                arm_seed_metrics[ex_top]["reg_r2"],
                arm_seed_metrics[ref]["reg_r2"],
                higher_is_better=True,
            ),
            "real_qwen35_accuracy": paired_lineage_summary(
                arm_seed_metrics[ex_top]["real_qwen35_accuracy"],
                arm_seed_metrics[ref]["real_qwen35_accuracy"],
                higher_is_better=True,
            ),
        }

    for ref in ["gen0", fx_top] + [f"{b}_regen_matched_gen{G}" for b in protocol["required_baselines"]]:
        comparisons[f"{rg_top}_vs_{ref}"] = {
            "norm_loss_ratio": paired_lineage_summary(
                arm_seed_metrics[rg_top]["norm_loss_ratio"],
                arm_seed_metrics[ref]["norm_loss_ratio"],
                higher_is_better=False,
            ),
            "cls_accuracy": paired_lineage_summary(
                arm_seed_metrics[rg_top]["cls_accuracy"],
                arm_seed_metrics[ref]["cls_accuracy"],
                higher_is_better=True,
            ),
            "real_qwen35_accuracy": paired_lineage_summary(
                arm_seed_metrics[rg_top]["real_qwen35_accuracy"],
                arm_seed_metrics[ref]["real_qwen35_accuracy"],
                higher_is_better=True,
            ),
        }

    # Gate 1 evaluation
    ex_vs_fix_loss = comparisons[f"{ex_top}_vs_{fx_top}"]["norm_loss_ratio"]
    ex_vs_fix_acc = comparisons[f"{ex_top}_vs_{fx_top}"]["cls_accuracy"]
    gen_top_acc_rate = acc_rates_by_gen["exact"][G]
    improves_at_proposing = (
        ex_vs_fix_loss["mean_diff_focal_minus_ref"] < 0.0
        and ex_vs_fix_loss["two_sided_t_p"] < 0.05
        and gen_top_acc_rate > 0.0
    )
    meta_improves_rule = (
        comparisons[f"{ex_top}_vs_gen0"]["norm_loss_ratio"]["mean_diff_focal_minus_ref"] < 0.0
        and comparisons[f"{ex_top}_vs_gen0"]["norm_loss_ratio"]["two_sided_t_p"] < 0.05
    )

    # Gate 2 evaluation (wins on real_qwen35_swiglu_lora_cls accuracy against ALL 6 exact-matched baselines)
    real_wins_all_6 = all(
        comparisons[f"{ex_top}_vs_{b}_exact_matched_gen{G}"]["real_qwen35_accuracy"]["mean_diff_focal_minus_ref"] > 0.0
        for b in protocol["required_baselines"]
    )
    real_sig_all_6 = all(
        comparisons[f"{ex_top}_vs_{b}_exact_matched_gen{G}"]["real_qwen35_accuracy"]["mean_diff_focal_minus_ref"] > 0.0
        and comparisons[f"{ex_top}_vs_{b}_exact_matched_gen{G}"]["real_qwen35_accuracy"]["two_sided_t_p"] < 0.05
        for b in protocol["required_baselines"]
    )

    return {
        "arm_summaries": arm_summaries,
        "accepted_proposal_rate_by_generation": acc_rates_by_gen,
        "lineage_level_paired_comparisons": comparisons,
        "gate_verdicts": {
            "meta_training_improves_rule_over_gen0": meta_improves_rule,
            "improves_at_proposing_vs_fixed_proposer": improves_at_proposing,
            "gate1_classification": (
                "improves_at_proposing"
                if improves_at_proposing
                else ("meta_training_improves_a_rule" if meta_improves_rule else "null")
            ),
            "exact_vs_fixed_norm_loss_t_p": ex_vs_fix_loss["two_sided_t_p"],
            "exact_vs_fixed_cls_acc_t_p": ex_vs_fix_acc["two_sided_t_p"],
            "beats_all_6_baselines_point_estimate_on_real_qwen35_acc": real_wins_all_6,
            "beats_all_6_baselines_stat_sig_on_real_qwen35_acc": real_sig_all_6,
        },
    }


def execute(output: Path, protocol: dict[str, Any], addendum: dict[str, Any], workers: int = 6) -> dict[str, Any]:
    from tasks_b2_v3 import QWEN35_SAFETENSORS_FILE

    output.mkdir(parents=True, exist_ok=False)
    path = output / "confirmation_receipt_v3.json"
    t0 = time.monotonic()

    receipt: dict[str, Any] = {
        "schema": "gamma.b2.self_transform_neural_proposer_v3.confirmation_receipt/v3",
        "started_unix": time.time(),
        "completed": False,
        "acceptance_gates_evaluated": False,
        "protocol": protocol,
        "protocol_sha256": digest(HERE / "protocol_v3.json"),
        "protocol_addendum": addendum,
        "protocol_addendum_sha256": digest(HERE / "protocol_addendum_v3.json"),
        "source_sha256": {p.name: digest(p) for p in sorted(HERE.glob("*.py"))},
        "checkpoint_sha256": digest(QWEN35_SAFETENSORS_FILE),
        "rows": [],
        "lineages": [],
        "calibrations": [],
        "per_seed_timing": [],
    }
    save_atomic(path, receipt)

    seeds = [int(s) for s in protocol["lineage_seeds"]]
    jobs = [(idx, s, protocol) for idx, s in enumerate(seeds)]
    seed_outputs: dict[int, dict[str, Any]] = {}

    try:
        if workers <= 1:
            for jb in jobs:
                res = _run_single_lineage_seed(jb)
                seed_outputs[res["seed"]] = res
                print(f"[B2-v3] Completed lineage seed {res['seed']} in {res['elapsed_s']:.1f}s", flush=True)
        else:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                fut_map = {ex.submit(_run_single_lineage_seed, jb): jb[1] for jb in jobs}
                for fut in as_completed(fut_map):
                    res = fut.result()
                    seed_outputs[res["seed"]] = res
                    print(
                        f"[B2-v3] Completed lineage seed {res['seed']} ({len(seed_outputs)}/{len(seeds)}) in {res['elapsed_s']:.1f}s",
                        flush=True,
                    )

        for s in seeds:
            so = seed_outputs[s]
            receipt["calibrations"].append({"seed": s, "calibration_wall_ms": so["calibration_wall_ms"], "result": so["calibration"]})
            receipt["lineages"].extend(so["lineages"])
            receipt["rows"].extend(so["rows"])
            receipt["per_seed_timing"].append({
                "seed": s,
                "elapsed_s": so["elapsed_s"],
                "subprocesses_spawned": so["subprocesses_spawned"],
            })

        receipt["analysis"] = analyze_receipt(receipt["rows"], receipt["lineages"], protocol)
        receipt["completed"] = True
        receipt["acceptance_gates_evaluated"] = True
        receipt["elapsed_seconds"] = time.monotonic() - t0
    except BaseException as error:
        receipt["failure"] = {"type": type(error).__name__, "message": str(error)}
        raise
    finally:
        receipt["finished_unix"] = time.time()
        save_atomic(path, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Execute untouched S=12 confirmation study")
    parser.add_argument("--output", type=Path, help="New directory for confirmation_receipt_v3.json")
    parser.add_argument("--workers", type=int, default=6, help="Parallel lineage seed workers")
    args = parser.parse_args()

    protocol, addendum = preflight(verify_checkpoint=args.execute)
    if not args.execute:
        print(json.dumps({
            "preflight": "passed",
            "study_started": False,
            "lineages": len(protocol["lineage_seeds"]),
            "targets_per_lineage": len(confirmation_specs(protocol, 0)),
            "total_disjoint_confirmation_targets": len(protocol["lineage_seeds"]) * len(confirmation_specs(protocol, 0)),
        }))
        return
    if args.output is None:
        parser.error("--execute requires --output <new_dir>")
    execute(args.output, protocol, addendum, workers=args.workers)


if __name__ == "__main__":
    main()
