"""Stage 2: does conditioning the K-FAC constants on the family or the task buy anything?

DEVELOPMENT ONLY. No proposer is involved: this bounds what ANY learned mapping from task
state to constant K-FAC controls could gain on the held-out families.

POST-HOC MENU CHANGE (made after reading Stage 1, before running Stage 2): Stage 1's trained
constants moved weight decay to roughly 3-5x the sealed grid's maximum (0.025) and the step to
roughly 2x the selected grid value. The sealed 56-point grid cannot express that, so per-task
tuning inside it would be confounded with "the grid is too narrow". The menu here is therefore
`ext_pool()`: 5 learning rates x the 2 mixes the sealed calibration actually selects x 4 decays
(0.025 .. 0.25) = 40 points. The choice of menu used only upstream-derived information (the
trained constants), not held-out scores, but it was not planned in advance.

The same step also yields `kfac_ext_upstream`: plain K-FAC calibrated on upstream tasks from the
wider menu, evaluated on all Stage-1 held-out tasks, i.e. the fair constant baseline for the
Stage-1 proposer.

Arms, per lineage, on that lineage's first `per_family` held-out tasks of each family:
  sealed_grid_upstream   the Stage-1 baseline config (sealed 56-grid tuned on upstream tasks; reference)
  global_upstream        one config from the wider menu, tuned on upstream calibration tasks
  global_infamily        one config, tuned on in-family calibration tasks (disjoint seeds), pooled
  per_family             one config per family, tuned on the same in-family calibration tasks
  per_task_halfA         one config per held-out task, picked on query half A (even rows);
                         every arm is scored on query half B (odd rows) for this comparison
  per_task_oracle_full   one config per task picked AND scored on the full query set
                         (leaky upper bound, labelled as such)
  global_heldout_oracle  one config picked AND scored on the lineage's held-out tasks (leaky)

Pre-declared reading: "per-task conditioning clearly helps" only if per_task_halfA beats
global_infamily on half-B lineage-mean normalized_loss_ratio with two-sided paired t p < 0.05.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import statistics
import time
from typing import Any

import torch

import common_v4dev as C
from baselines_v4dev import compute_task_loss_v3, forward_target_v3, run_kfac_no_proposer_v3, smooth_multiclass_hinge
from stats_v4dev import paired_lineage_summary
from tasks_v4dev import DEV_HELDOUT_FAMILIES, build_heldout_task_dev


def ext_pool() -> list[dict[str, Any]]:
    """Wider K-FAC menu (post hoc, see module docstring): 5 lr x 2 mixes x 4 decays = 40 points."""
    mixes = ([0.50, 0.20, 0.40, 0.40, 0.20], [0.15, 0.15, 0.30, 0.75, 0.25])
    return [
        {"lr": lr, "basis_weights": bw, "weight_decay": wd}
        for lr in (0.045, 0.075, 0.11, 0.16, 0.24)
        for bw in mixes
        for wd in (0.025, 0.06, 0.12, 0.25)
    ]


@torch.no_grad()
def subset_metrics(task, init_layers, final_layers, idx: torch.Tensor) -> dict[str, float]:
    X, Y = task.X_qry[idx], task.Y_qry[idx]
    p0 = forward_target_v3(task, [w.detach() for w in init_layers], X)[0]
    p1 = forward_target_v3(task, [w.detach() for w in final_layers], X)[0]
    il = max(float(compute_task_loss_v3(task, p0, Y)), 1e-6)
    ql = float(compute_task_loss_v3(task, p1, Y))
    ratio = min(10.0, ql / il) if ql == ql else 10.0
    out = {"normalized_loss_ratio": ratio}
    if task.loss_type == "cross_entropy":
        hinge = float(smooth_multiclass_hinge(p1, Y))
        out["smooth_score"] = 0.75 * min(ratio, 4.0) + 0.25 * min(hinge, 4.0)
        out["accuracy"] = float((p1.argmax(dim=-1) == Y).float().mean())
    else:
        out["smooth_score"] = min(ratio, 4.0)
        out["r2"] = 1.0 - ql / float(Y.var().clamp_min(1e-8))
    return out


def _stage2_lineage(job: dict[str, Any]) -> dict[str, Any]:
    C.configure_cpu(1)
    t0 = time.monotonic()
    cpu0 = time.process_time()
    lineage = int(job["lineage"])
    pool = ext_pool()
    keys = [C.cfg_key(c) for c in pool]
    sealed_cfg = job["upstream_base_config"]
    sealed_key = "SEALED::" + C.cfg_key(sealed_cfg)
    up_cal = C.calibrate_kfac(C.upstream_calib_tasks(lineage, int(job["n_upstream_calib"])), pool)
    up_key = C.cfg_key(up_cal["best_config"])

    # in-family calibration (disjoint seeds from the held-out evaluation tasks)
    cal_tasks = C.infamily_calib_tasks(lineage, int(job["calib_per_family"]))
    cal_scores: dict[str, dict[str, list[float]]] = {k: {f: [] for f in DEV_HELDOUT_FAMILIES} for k in keys}
    for cfg, k in zip(pool, keys):
        for t in cal_tasks:
            fin = C.kfac_trajectory(cfg, t)[-1]
            n_q = t.X_qry.shape[0]
            cal_scores[k][t.family].append(subset_metrics(t, t.init_layers, fin, torch.arange(n_q))["smooth_score"])
    pooled = {k: statistics.mean(v for f in DEV_HELDOUT_FAMILIES for v in cal_scores[k][f]) for k in keys}
    global_in_key = min(keys, key=lambda k: pooled[k])
    per_family_key = {f: min(keys, key=lambda k: statistics.mean(cal_scores[k][f])) for f in DEV_HELDOUT_FAMILIES}

    # held-out tasks: every grid point, three query views
    specs = [sp for sp in C.heldout_specs(lineage, int(job["stage1_heldout_per_family"]))]
    per_fam_count: dict[str, int] = {f: 0 for f in DEV_HELDOUT_FAMILIES}
    use_specs = []
    for sp in specs:
        if per_fam_count[sp["family"]] < int(job["per_family"]):
            per_fam_count[sp["family"]] += 1
            use_specs.append(sp)
    grid_rows: list[dict[str, Any]] = []
    by_task: dict[int, dict[str, dict[str, dict[str, float]]]] = {}
    fam_of: dict[int, str] = {}
    for sp in use_specs:
        task = build_heldout_task_dev(sp["family"], sp["seed"])
        n_q = task.X_qry.shape[0]
        views = {"full": torch.arange(n_q), "halfA": torch.arange(0, n_q, 2), "halfB": torch.arange(1, n_q, 2)}
        fam_of[sp["seed"]] = sp["family"]
        by_task[sp["seed"]] = {}
        for cfg, k in list(zip(pool, keys)) + [(sealed_cfg, sealed_key)]:
            fin = C.kfac_trajectory(cfg, task)[-1]
            m = {v: subset_metrics(task, task.init_layers, fin, idx) for v, idx in views.items()}
            by_task[sp["seed"]][k] = m
            grid_rows.append({"lineage": lineage, "family": sp["family"], "seed": sp["seed"], "config": cfg, **{
                f"{v}_{name}": val for v, mm in m.items() for name, val in mm.items()
            }})

    seeds = [sp["seed"] for sp in use_specs]
    heldout_oracle_key = min(keys, key=lambda k: statistics.mean(by_task[s][k]["full"]["smooth_score"] for s in seeds))
    choice: dict[str, dict[int, str]] = {
        "sealed_grid_upstream": {s: sealed_key for s in seeds},
        "global_upstream": {s: up_key for s in seeds},
        "global_infamily": {s: global_in_key for s in seeds},
        "per_family": {s: per_family_key[fam_of[s]] for s in seeds},
        "per_task_halfA": {s: min(keys, key=lambda k: by_task[s][k]["halfA"]["smooth_score"]) for s in seeds},
        "per_task_oracle_full": {s: min(keys, key=lambda k: by_task[s][k]["full"]["smooth_score"]) for s in seeds},
        "global_heldout_oracle": {s: heldout_oracle_key for s in seeds},
    }
    arm_rows: list[dict[str, Any]] = []
    for arm, ch in choice.items():
        for s in seeds:
            m = by_task[s][ch[s]]
            arm_rows.append({
                "lineage": lineage, "arm": arm, "family": fam_of[s], "seed": s, "chosen_config": json.loads(ch[s].replace("SEALED::", "")),
                **{f"{v}_{name}": val for v, mm in m.items() for name, val in mm.items()},
            })
    # plain K-FAC from the wider menu, upstream-calibrated, on ALL Stage-1 held-out tasks (Stage-1 row format)
    ext_rows = []
    for sp in specs:
        task = build_heldout_task_dev(sp["family"], sp["seed"])
        ext_rows.append(C.row_from_result(run_kfac_no_proposer_v3(up_cal["best_config"], task), task, sp["seed"], lineage, "kfac_ext_upstream"))
    return {
        "lineage": lineage,
        "kfac_ext_upstream_rows": ext_rows,
        "upstream_calibration_ext": [{"config": a["config"], "mean_smooth_score": a["mean_smooth_score"]} for a in up_cal["all"]],
        "sealed_grid_upstream_config": sealed_cfg,
        "global_upstream_config": json.loads(up_key),
        "global_infamily_config": json.loads(global_in_key),
        "per_family_config": {f: json.loads(k) for f, k in per_family_key.items()},
        "global_heldout_oracle_config": json.loads(heldout_oracle_key),
        "arm_rows": arm_rows,
        "grid_rows": grid_rows,
        "timing": {"wall_s": time.monotonic() - t0, "cpu_s": time.process_time() - cpu0},
    }


def run_stage2(args) -> None:
    t0 = time.monotonic()
    s1 = json.loads((C.OUTPUT_DIR / "stage1_v4dev.json").read_text())
    base_cfgs = {ln["lineage"]: ln["base_config"] for ln in s1["lineages"]}
    lineages = sorted(base_cfgs)[: args.lineages]
    cfg = {"per_family": 6, "calib_per_family": 5, "n_upstream_calib": s1["config"]["n_calib_tasks"],
           "stage1_heldout_per_family": s1["config"]["heldout_per_family"], "menu": ext_pool()}
    jobs = [{**cfg, "lineage": ln, "upstream_base_config": base_cfgs[ln]} for ln in lineages]
    res: dict[int, dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for fut in as_completed([ex.submit(_stage2_lineage, j) for j in jobs]):
            r = fut.result()
            res[r["lineage"]] = r
            print(f"[stage2] lineage {r['lineage']} done in {r['timing']['wall_s']:.0f}s "
                  f"global_infamily={r['global_infamily_config']}", flush=True)

    arm_rows = [row for ln in lineages for row in res[ln]["arm_rows"]]
    arms = ["sealed_grid_upstream", "global_upstream", "global_infamily", "per_family", "per_task_halfA", "per_task_oracle_full", "global_heldout_oracle"]

    def lin_mean(arm: str, field: str, family: str | None = None) -> list[float]:
        out = []
        for ln in lineages:
            vals = [r[field] for r in arm_rows if r["arm"] == arm and r["lineage"] == ln
                    and field in r and (family is None or r["family"] == family)]
            out.append(statistics.mean(vals))
        return out

    table = {
        arm: {
            "halfB_normalized_loss_ratio": lin_mean(arm, "halfB_normalized_loss_ratio"),
            "full_normalized_loss_ratio": lin_mean(arm, "full_normalized_loss_ratio"),
            "halfB_cls_accuracy": lin_mean(arm, "halfB_accuracy"),
            "full_cls_accuracy": lin_mean(arm, "full_accuracy"),
            "halfB_reg_r2": lin_mean(arm, "halfB_r2"),
            **{f"halfB_normalized_loss_ratio::{f}": lin_mean(arm, "halfB_normalized_loss_ratio", f) for f in DEV_HELDOUT_FAMILIES},
        }
        for arm in arms
    }

    def cmp_(focal: str, ref: str) -> dict[str, Any]:
        return {
            m: paired_lineage_summary(table[focal][m], table[ref][m], higher_is_better=("accuracy" in m or "r2" in m))
            for m in table[focal]
        }

    comparisons = {
        "per_task_halfA_vs_global_infamily": cmp_("per_task_halfA", "global_infamily"),
        "per_family_vs_global_infamily": cmp_("per_family", "global_infamily"),
        "global_infamily_vs_global_upstream": cmp_("global_infamily", "global_upstream"),
        "per_task_halfA_vs_global_upstream": cmp_("per_task_halfA", "global_upstream"),
        "global_upstream_vs_sealed_grid_upstream": cmp_("global_upstream", "sealed_grid_upstream"),
        "LEAKY_per_task_oracle_full_vs_global_infamily": cmp_("per_task_oracle_full", "global_infamily"),
        "LEAKY_global_heldout_oracle_vs_global_infamily": cmp_("global_heldout_oracle", "global_infamily"),
    }
    # Stage-1 arms vs plain K-FAC from the wider menu, on the full Stage-1 held-out set
    from run_dev_v4 import compare, lineage_metric_table
    s1_arms = ["kfac_no_proposer", "proposer_best", "trained_constants_best", "proposer_best_global_constant_ablation"]
    ext_rows = [row for ln in lineages for row in res[ln]["kfac_ext_upstream_rows"]]
    s1_rows = [r for r in s1["rows"] if r["lineage"] in lineages and r["arm"] in s1_arms]
    s1_table = lineage_metric_table(s1_rows + ext_rows, lineages, s1_arms + ["kfac_ext_upstream"])
    stage1_vs_ext = {
        "proposer_best_vs_kfac_ext_upstream": compare(s1_table, "proposer_best", "kfac_ext_upstream"),
        "trained_constants_best_vs_kfac_ext_upstream": compare(s1_table, "trained_constants_best", "kfac_ext_upstream"),
        "kfac_ext_upstream_vs_kfac_no_proposer": compare(s1_table, "kfac_ext_upstream", "kfac_no_proposer"),
    }
    primary = comparisons["per_task_halfA_vs_global_infamily"]["halfB_normalized_loss_ratio"]
    clearly = bool(primary["mean_diff_focal_minus_ref"] < 0 and primary["two_sided_t_p"] < 0.05)
    out = {
        "schema": "gamma.b2.self_transform_neural_proposer_v4_dev.stage2/dev",
        "development_only": True,
        "config": cfg,
        "pre_declared_rule": "per-task conditioning 'clearly helps' iff per_task_halfA < global_infamily on half-B lineage-mean normalized_loss_ratio with paired t p < 0.05",
        "per_task_conditioning_clearly_helps": clearly,
        "per_lineage_metric_means": {"lineages": lineages, "arms": table},
        "comparisons": comparisons,
        "stage1_arms_vs_kfac_ext_upstream": {"per_lineage_metric_means": s1_table, "comparisons": stage1_vs_ext},
        "kfac_ext_upstream_rows": ext_rows,
        "lineages": [{k: v for k, v in res[ln].items() if k not in ("arm_rows", "grid_rows", "kfac_ext_upstream_rows")} for ln in lineages],
        "arm_rows": arm_rows,
        "grid_rows": [row for ln in lineages for row in res[ln]["grid_rows"]],
        "wall_s": time.monotonic() - t0,
        "cpu_s_sum_over_workers": sum(res[ln]["timing"]["cpu_s"] for ln in lineages),
    }
    C.save_json(C.OUTPUT_DIR / "stage2_v4dev.json", out)
    print(f"[stage2] wrote {C.OUTPUT_DIR / 'stage2_v4dev.json'} in {time.monotonic() - t0:.0f}s", flush=True)
    for name, c in comparisons.items():
        for metric in ("halfB_normalized_loss_ratio", "full_normalized_loss_ratio", "halfB_cls_accuracy", "halfB_reg_r2"):
            s = c[metric]
            print(
                f"[stage2] {name:46s} {metric:28s} focal={s['focal_mean']:.4f} ref={s['ref_mean']:.4f} "
                f"diff={s['mean_diff_focal_minus_ref']:+.4f} W/L/T={s['wins']}/{s['losses']}/{s['ties']} p={s['two_sided_t_p']:.4g}",
                flush=True,
            )
    for name, c in stage1_vs_ext.items():
        for metric in ("normalized_loss_ratio", "smooth_score", "cls_accuracy", "reg_r2"):
            s = c[metric]
            print(
                f"[stage2] {name:46s} {metric:28s} focal={s['focal_mean']:.4f} ref={s['ref_mean']:.4f} "
                f"diff={s['mean_diff_focal_minus_ref']:+.4f} W/L/T={s['wins']}/{s['losses']}/{s['ties']} p={s['two_sided_t_p']:.4g}",
                flush=True,
            )
    print(f"[stage2] per_task_conditioning_clearly_helps = {clearly}", flush=True)
