"""Development runner for `self_transform_neural_proposer_v4_dev` (CPU only, <= 4 single-thread workers).

DEVELOPMENT ONLY: nothing produced here is pre-registered or sealed.

    .venv/bin/python projects/self_transform_neural_proposer_v4_dev/run_dev_v4.py pilot
    .venv/bin/python projects/self_transform_neural_proposer_v4_dev/run_dev_v4.py stage1
    .venv/bin/python projects/self_transform_neural_proposer_v4_dev/run_dev_v4.py stage2
    .venv/bin/python projects/self_transform_neural_proposer_v4_dev/analyze_v4dev.py

Stage 3 (differentiated self-update vs RMS-matched Adam) is NOT implemented: its gate did not
open (the Stage-1 proposer ties constant K-FAC once the constants are tuned beyond the sealed
grid). Edits made to this file after the Stage-1/2 runs: this paragraph and the removal of the
`stage3` sub-command only.

Outputs go to `.work/self-transform-neural-proposer-v4-dev/`.

Stage 1 design (transfer regime, as in v3): for each lineage, the `kfac_no_proposer` grid (56 points)
is calibrated on upstream tasks; the residual proposer is centred on that lineage's selected
grid point (generation 0 == that baseline), meta-trained with Adam on a fresh upstream task
stream (no accept/reject), early-stopped on upstream validation tasks, then both are evaluated
on fresh tasks from the three held-out synthetic families. Pre-declared primary metric: the
lineage mean of `normalized_loss_ratio` over that lineage's held-out tasks (lower is better),
proposer (best-validation checkpoint) vs `kfac_no_proposer`, paired by lineage.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import statistics
import sys
import time
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import torch  # noqa: E402

import common_v4dev as C  # noqa: E402
from baselines_v4dev import run_kfac_no_proposer_v3  # noqa: E402
from proposer_v4dev import OUT_DIM_V3, KfacBaseConfig, ProposerWeightsV3  # noqa: E402
from stats_v4dev import paired_lineage_summary  # noqa: E402
from tasks_v4dev import DEV_HELDOUT_FAMILIES, build_heldout_task_dev  # noqa: E402

STAGE1_DEFAULTS = {
    "lineages": list(range(8)),
    "n_calib_tasks": 16,
    "n_val_tasks": 16,
    "meta_steps": 250,
    "tasks_per_step": 4,
    "val_every": 25,
    "heldout_per_family": 12,
}


def _log(msg: str) -> None:
    print(msg, flush=True)


# ----------------------------------------------------------------------------- pilot
def _pilot_job(job: dict[str, Any]) -> dict[str, Any]:
    C.configure_cpu(1)
    lineage = int(job["lineage"])
    base = KfacBaseConfig.from_cfg(job["base_cfg"])
    val_tasks = C.upstream_val_tasks(lineage, int(job["n_val_tasks"]))
    out = C.meta_train_adam(
        arm=job["arm"],
        base=base,
        init_seed=C.seed_init(lineage),
        task_fn=lambda i: C.upstream_train_task(lineage, i),
        val_tasks=val_tasks,
        n_steps=int(job["meta_steps"]),
        tasks_per_step=int(job["tasks_per_step"]),
        lr=float(job["lr"]),
        val_every=int(job["val_every"]),
        clip_hooks=bool(job["clip_hooks"]),
    )
    out.pop("best_flat")
    out.pop("final_flat")
    return {**{k: job[k] for k in ("arm", "lr", "clip_hooks", "lineage")}, **out}


def run_pilot(args: argparse.Namespace) -> None:
    """Pick meta-optimiser hyper-parameters on a pilot lineage, using upstream validation only."""
    C.configure_cpu(1)
    t0 = time.monotonic()
    lineage = 90
    calib = C.calibrate_kfac(C.upstream_calib_tasks(lineage, STAGE1_DEFAULTS["n_calib_tasks"]))
    _log(f"[pilot] base config {calib['best_config']} score {calib['best_score']:.4f} ({time.monotonic() - t0:.0f}s)")
    grid = [
        ("proposer", 0.003, True), ("proposer", 0.01, True),
        ("proposer", 0.003, False), ("proposer", 0.01, False),
        ("const", 0.01, True), ("const", 0.03, True),
        ("const", 0.01, False), ("const", 0.03, False),
    ]
    jobs = [
        {
            "arm": arm, "lr": lr, "clip_hooks": hooks, "lineage": lineage, "base_cfg": calib["best_config"],
            "n_val_tasks": STAGE1_DEFAULTS["n_val_tasks"], "meta_steps": args.pilot_steps,
            "tasks_per_step": STAGE1_DEFAULTS["tasks_per_step"], "val_every": 20,
        }
        for arm, lr, hooks in grid
    ]
    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for fut in as_completed([ex.submit(_pilot_job, j) for j in jobs]):
            r = fut.result()
            results.append(r)
            _log(
                f"[pilot] {r['arm']:8s} lr={r['lr']:<6} hooks={r['clip_hooks']!s:5s} val0={r['val_step0_is_kfac_base']:.4f} "
                f"best={r['best_val']:.4f}@{r['best_step']} final={r['val_curve'][-1]['val']:.4f} "
                f"rms/step={r['mean_step_rms']:.4f} nonfinite={r['nonfinite_steps']} wall={r['wall_s']:.0f}s"
            )
    C.save_json(C.OUTPUT_DIR / "pilot_v4dev.json", {
        "schema": "gamma.b2.self_transform_neural_proposer_v4_dev.pilot/dev",
        "development_only": True,
        "pilot_lineage": lineage,
        "selection_data": "upstream validation tasks of the pilot lineage only (no held-out family tasks)",
        "base_config": calib["best_config"],
        "runs": sorted(results, key=lambda r: (r["arm"], r["lr"], r["clip_hooks"])),
        "wall_s": time.monotonic() - t0,
    })
    _log(f"[pilot] done in {time.monotonic() - t0:.0f}s")


# ----------------------------------------------------------------------------- stage 1
def _phi_from_flat(flat: list[float]) -> ProposerWeightsV3:
    return ProposerWeightsV3.from_flat_list(flat)


def _stage1_lineage(job: dict[str, Any]) -> dict[str, Any]:
    C.configure_cpu(1)
    t0 = time.monotonic()
    lineage = int(job["lineage"])
    cpu0 = time.process_time()

    calib = C.calibrate_kfac(C.upstream_calib_tasks(lineage, int(job["n_calib_tasks"])))
    base = KfacBaseConfig.from_cfg(calib["best_config"])
    t_cal = time.monotonic() - t0
    val_tasks = C.upstream_val_tasks(lineage, int(job["n_val_tasks"]))

    trained: dict[str, dict[str, Any]] = {}
    for arm, lr in (("proposer", float(job["lr_proposer"])), ("const", float(job["lr_const"]))):
        trained[arm] = C.meta_train_adam(
            arm=arm,
            base=base,
            init_seed=C.seed_init(lineage),
            task_fn=lambda i: C.upstream_train_task(lineage, i),
            val_tasks=val_tasks,
            n_steps=int(job["meta_steps"]),
            tasks_per_step=int(job["tasks_per_step"]),
            lr=lr,
            val_every=int(job["val_every"]),
            clip_hooks=bool(job["clip_hooks"]),
        )

    phi_best = _phi_from_flat(trained["proposer"]["best_flat"])
    phi_final = _phi_from_flat(trained["proposer"]["final_flat"])
    const_best = torch.tensor(trained["const"]["best_flat"], dtype=torch.float64)

    specs = C.heldout_specs(lineage, int(job["heldout_per_family"]))
    tasks = [(sp, build_heldout_task_dev(sp["family"], sp["seed"])) for sp in specs]
    rows: list[dict[str, Any]] = []
    records: list[dict] = []
    for sp, task in tasks:
        rows.append(C.row_from_result(run_kfac_no_proposer_v3(base.to_cfg(), task), task, sp["seed"], lineage, "kfac_no_proposer"))
        rows.append(C.row_from_result(C.run_residual_cold(phi_best, base, task, record=records), task, sp["seed"], lineage, "proposer_best"))
        rows.append(C.row_from_result(C.run_residual_cold(phi_best, base, task, row_mode="layer_mean"), task, sp["seed"], lineage, "proposer_best_layer_mean_ablation"))
        rows.append(C.row_from_result(C.run_residual_cold(phi_final, base, task), task, sp["seed"], lineage, "proposer_final"))
        rows.append(C.row_from_result(C.run_residual_cold(None, base, task, row_mode="constant", const_raw=const_best), task, sp["seed"], lineage, "trained_constants_best"))

    # Global-constant ablation: one raw 8-vector = row-weighted mean of the proposer's own outputs
    # over every row, layer, step and held-out task of this lineage (uses no labels).
    raw_all = torch.cat([r["raw"] for r in records], dim=0)
    const_mean = raw_all.mean(dim=0)
    raw_sd_total = raw_all.std(dim=0)
    within_layer_sd = torch.stack([r["raw"].std(dim=0) for r in records if r["raw"].shape[0] > 1]).mean(dim=0)
    for sp, task in tasks:
        rows.append(C.row_from_result(
            C.run_residual_cold(None, base, task, row_mode="constant", const_raw=const_mean),
            task, sp["seed"], lineage, "proposer_best_global_constant_ablation",
        ))

    for arm in trained:
        trained[arm]["best_flat_sha_len"] = len(trained[arm]["best_flat"])
    return {
        "lineage": lineage,
        "base_config": base.to_cfg(),
        "calibration": {"best_score": calib["best_score"], "passes": calib["passes"],
                        "all": [{"config": a["config"], "mean_smooth_score": a["mean_smooth_score"]} for a in calib["all"]]},
        "training": {arm: {k: v for k, v in tr.items() if k not in ("final_flat",)} for arm, tr in trained.items()},
        "proposer_output_stats_on_heldout": {
            "mean_raw": const_mean.tolist(),
            "sd_raw_over_all_rows": raw_sd_total.tolist(),
            "mean_within_layer_sd_raw": within_layer_sd.tolist(),
            "output_names": ["mix_grad", "mix_mom", "mix_adam", "mix_kfac", "mix_polar", "step_log_mult", "row_log_mult_raw", "decay_log_mult"],
        },
        "trained_constants_raw": const_best.tolist(),
        "rows": rows,
        "timing": {"calibration_wall_s": t_cal, "wall_s": time.monotonic() - t0, "cpu_s": time.process_time() - cpu0},
    }


def lineage_metric_table(rows: list[dict[str, Any]], lineages: list[int], arms: list[str]) -> dict[str, dict[str, list[float]]]:
    """Per-arm, per-lineage means. cls accuracy = mean over the two classification families' tasks."""
    out: dict[str, dict[str, list[float]]] = {}
    for arm in arms:
        m: dict[str, list[float]] = {"normalized_loss_ratio": [], "smooth_score": [], "cls_accuracy": [], "reg_r2": []}
        fam_m: dict[str, list[float]] = {f"normalized_loss_ratio::{f}": [] for f in DEV_HELDOUT_FAMILIES}
        for ln in lineages:
            rs = [r for r in rows if r["arm"] == arm and r["lineage"] == ln]
            assert rs, (arm, ln)
            m["normalized_loss_ratio"].append(statistics.mean(r["normalized_loss_ratio"] for r in rs))
            m["smooth_score"].append(statistics.mean(r["smooth_score"] for r in rs))
            m["cls_accuracy"].append(statistics.mean(r["query_accuracy"] for r in rs if r["loss_type"] == "cross_entropy"))
            m["reg_r2"].append(statistics.mean(r["query_r2"] for r in rs if r["loss_type"] == "mse"))
            for f in DEV_HELDOUT_FAMILIES:
                fam_m[f"normalized_loss_ratio::{f}"].append(statistics.mean(r["normalized_loss_ratio"] for r in rs if r["family"] == f))
        out[arm] = {**m, **fam_m}
    return out


HIGHER_IS_BETTER = {"normalized_loss_ratio": False, "smooth_score": False, "cls_accuracy": True, "reg_r2": True}


def compare(table: dict[str, dict[str, list[float]]], focal: str, ref: str) -> dict[str, Any]:
    res = {}
    for metric in table[focal]:
        hib = HIGHER_IS_BETTER.get(metric.split("::")[0], False)
        res[metric] = paired_lineage_summary(table[focal][metric], table[ref][metric], higher_is_better=hib)
    return res


def run_stage1(args: argparse.Namespace) -> None:
    t0 = time.monotonic()
    cfg = dict(STAGE1_DEFAULTS)
    cfg.update({
        "lineages": list(range(args.lineage_offset, args.lineage_offset + args.lineages)),
        "meta_steps": args.meta_steps,
        "tasks_per_step": args.tasks_per_step,
        "lr_proposer": args.lr_proposer,
        "lr_const": args.lr_const,
        "clip_hooks": bool(args.clip_hooks),
    })
    jobs = [{**cfg, "lineage": ln} for ln in cfg["lineages"]]
    per_lineage: dict[int, dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for fut in as_completed([ex.submit(_stage1_lineage, j) for j in jobs]):
            r = fut.result()
            per_lineage[r["lineage"]] = r
            tp = r["training"]["proposer"]
            tc = r["training"]["const"]
            _log(
                f"[stage1] lineage {r['lineage']} base={r['base_config']} "
                f"proposer val {tp['val_step0_is_kfac_base']:.4f}->{tp['best_val']:.4f}@{tp['best_step']} "
                f"const val ->{tc['best_val']:.4f}@{tc['best_step']} wall={r['timing']['wall_s']:.0f}s"
            )
    lineages = sorted(per_lineage)
    rows = [row for ln in lineages for row in per_lineage[ln]["rows"]]
    arms = [
        "kfac_no_proposer", "proposer_best", "proposer_final", "proposer_best_layer_mean_ablation",
        "proposer_best_global_constant_ablation", "trained_constants_best",
    ]
    table = lineage_metric_table(rows, lineages, arms)
    comparisons = {
        "proposer_best_vs_kfac_no_proposer": compare(table, "proposer_best", "kfac_no_proposer"),
        "proposer_final_vs_kfac_no_proposer": compare(table, "proposer_final", "kfac_no_proposer"),
        "trained_constants_best_vs_kfac_no_proposer": compare(table, "trained_constants_best", "kfac_no_proposer"),
        "proposer_best_vs_trained_constants_best": compare(table, "proposer_best", "trained_constants_best"),
        "proposer_best_vs_layer_mean_ablation": compare(table, "proposer_best", "proposer_best_layer_mean_ablation"),
        "proposer_best_vs_global_constant_ablation": compare(table, "proposer_best", "proposer_best_global_constant_ablation"),
    }
    out = {
        "schema": "gamma.b2.self_transform_neural_proposer_v4_dev.stage1/dev",
        "development_only": True,
        "regime": "transfer: meta-train + K-FAC calibration on v3 upstream generators; evaluation on three held-out synthetic families",
        "excluded": "real_qwen35_swiglu_lora_cls (pooled-embedding toy) is not built or evaluated",
        "primary_metric": "lineage mean normalized_loss_ratio, proposer_best vs kfac_no_proposer, two-sided paired t over lineages",
        "config": cfg,
        "seed_plan": C.__doc__,
        "per_lineage_metric_means": {"lineages": lineages, "arms": table},
        "comparisons": comparisons,
        "lineages": [{k: v for k, v in per_lineage[ln].items() if k != "rows"} for ln in lineages],
        "rows": rows,
        "wall_s": time.monotonic() - t0,
        "cpu_s_sum_over_workers": sum(per_lineage[ln]["timing"]["cpu_s"] for ln in lineages),
    }
    C.save_json(C.OUTPUT_DIR / args.out_name, out)
    _log(f"[stage1] wrote {C.OUTPUT_DIR / args.out_name} in {time.monotonic() - t0:.0f}s")
    for name, cmp_ in comparisons.items():
        for metric in ("normalized_loss_ratio", "smooth_score", "cls_accuracy", "reg_r2"):
            s = cmp_[metric]
            _log(
                f"[stage1] {name:48s} {metric:22s} focal={s['focal_mean']:.4f} ref={s['ref_mean']:.4f} "
                f"diff={s['mean_diff_focal_minus_ref']:+.4f} W/L/T={s['wins']}/{s['losses']}/{s['ties']} "
                f"t={s['t_stat']:+.2f} p={s['two_sided_t_p']:.4g}"
            )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["pilot", "stage1", "stage2"])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--lineages", type=int, default=8)
    ap.add_argument("--lineage-offset", type=int, default=0, help="0 for the study; >= 90 for smoke tests on pilot lineages")
    ap.add_argument("--meta-steps", type=int, default=STAGE1_DEFAULTS["meta_steps"])
    ap.add_argument("--tasks-per-step", type=int, default=STAGE1_DEFAULTS["tasks_per_step"])
    ap.add_argument("--lr-proposer", type=float, default=0.006)
    ap.add_argument("--lr-const", type=float, default=0.03)
    ap.add_argument("--clip-hooks", type=int, default=1)
    ap.add_argument("--pilot-steps", type=int, default=120)
    ap.add_argument("--out-name", type=str, default="stage1_v4dev.json")
    args = ap.parse_args()
    assert 1 <= args.workers <= 4, "CPU budget: at most 4 single-thread workers"
    print(
        f"[run-contract] run_name=v4dev-{args.stage} pairs_input_spec=synthetic-generators resume_from=none resume_stage=none "
        f"decode=n/a eval_dataset_paths=n/a device=cpu schedule=n/a runtime_mode=cpu sweep_mode=after_train",
        flush=True,
    )
    if args.stage == "pilot":
        run_pilot(args)
    elif args.stage == "stage1":
        run_stage1(args)
    else:
        from stage2_v4dev import run_stage2
        run_stage2(args)


if __name__ == "__main__":
    main()
