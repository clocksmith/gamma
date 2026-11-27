"""Recompute the v4-dev headline numbers from the per-task rows only (no model code, no torch).

    .venv/bin/python projects/self_transform_neural_proposer_v4_dev/analyze_v4dev.py

Reads `.work/self-transform-neural-proposer-v4-dev/stage{1,2}_v4dev.json`, rebuilds every lineage
mean from the raw rows, and runs the paired tests with scipy (an implementation independent of
`stats_v4dev.py`). Writes `summary_v4dev.json` next to the inputs. DEVELOPMENT ONLY.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import statistics

from scipy import stats

HERE = Path(__file__).resolve().parent
OUT = HERE.parent.parent / ".work" / "self-transform-neural-proposer-v4-dev"


def paired(focal: list[float], ref: list[float], lower_is_better: bool) -> dict:
    d = [f - r for f, r in zip(focal, ref)]
    better = [(-x if lower_is_better else x) for x in d]
    t = stats.ttest_rel(focal, ref)
    try:
        w = float(stats.wilcoxon(d).pvalue)
    except ValueError:
        w = 1.0
    return {
        "n_lineages": len(d),
        "focal_mean": statistics.mean(focal),
        "ref_mean": statistics.mean(ref),
        "mean_diff_focal_minus_ref": statistics.mean(d),
        "wins": sum(x > 1e-12 for x in better),
        "losses": sum(x < -1e-12 for x in better),
        "ties": sum(abs(x) <= 1e-12 for x in better),
        "t_stat": float(t.statistic),
        "paired_t_two_sided_p": float(t.pvalue),
        "wilcoxon_two_sided_p": w,
        "per_lineage_diff": d,
    }


def lineage_means(rows: list[dict], arm: str, field: str, lineages: list[int], where=lambda r: True) -> list[float]:
    out = []
    for ln in lineages:
        vals = [r[field] for r in rows if r["arm"] == arm and r["lineage"] == ln and field in r and where(r)]
        assert vals, (arm, field, ln)
        out.append(statistics.mean(vals))
    return out


def main() -> None:
    s1 = json.loads((OUT / "stage1_v4dev.json").read_text())
    s2 = json.loads((OUT / "stage2_v4dev.json").read_text())
    lineages = sorted({r["lineage"] for r in s1["rows"]})
    rows1 = s1["rows"] + s2["kfac_ext_upstream_rows"]
    is_cls = lambda r: r["loss_type"] == "cross_entropy"  # noqa: E731
    is_reg = lambda r: r["loss_type"] == "mse"  # noqa: E731
    metrics = [
        ("normalized_loss_ratio", "normalized_loss_ratio", lambda r: True, True),
        ("cls_accuracy", "query_accuracy", is_cls, False),
        ("reg_r2", "query_r2", is_reg, False),
    ]
    pairs1 = [
        ("proposer_best", "kfac_no_proposer"),
        ("trained_constants_best", "kfac_no_proposer"),
        ("kfac_ext_upstream", "kfac_no_proposer"),
        ("proposer_best", "trained_constants_best"),
        ("proposer_best", "kfac_ext_upstream"),
        ("proposer_best", "proposer_best_layer_mean_ablation"),
        ("proposer_best", "proposer_best_global_constant_ablation"),
    ]
    stage1 = {}
    for focal, ref in pairs1:
        stage1[f"{focal}_vs_{ref}"] = {
            name: paired(lineage_means(rows1, focal, field, lineages, w), lineage_means(rows1, ref, field, lineages, w), lib)
            for name, field, w, lib in metrics
        }
    n_tasks = {ln: len([r for r in s1["rows"] if r["arm"] == "proposer_best" and r["lineage"] == ln]) for ln in lineages}

    rows2 = s2["arm_rows"]
    metrics2 = [
        ("halfB_normalized_loss_ratio", "halfB_normalized_loss_ratio", True),
        ("halfB_cls_accuracy", "halfB_accuracy", False),
        ("halfB_reg_r2", "halfB_r2", False),
    ]
    pairs2 = [
        ("per_task_halfA", "global_infamily"),
        ("per_family", "global_infamily"),
        ("per_task_halfA", "per_family"),
        ("per_task_halfA", "global_upstream"),
        ("per_family", "global_upstream"),
        ("global_upstream", "sealed_grid_upstream"),
    ]
    stage2 = {}
    for focal, ref in pairs2:
        stage2[f"{focal}_vs_{ref}"] = {
            name: paired(lineage_means(rows2, focal, field, lineages), lineage_means(rows2, ref, field, lineages), lib)
            for name, field, lib in metrics2
        }

    sources = sorted(p for p in HERE.glob("*.py"))
    summary = {
        "schema": "gamma.b2.self_transform_neural_proposer_v4_dev.summary/dev",
        "development_only": True,
        "lineages": lineages,
        "heldout_tasks_per_lineage_stage1": n_tasks,
        "heldout_tasks_per_lineage_stage2": {ln: len([r for r in rows2 if r["arm"] == "per_family" and r["lineage"] == ln]) for ln in lineages},
        "stage1": stage1,
        "stage2": stage2,
        "stage3": "not run: the Stage-1 proposer ties, and does not beat, constant K-FAC once the constants are tuned outside the sealed grid",
        "compute": {
            "stage1_wall_s": s1["wall_s"], "stage1_cpu_s": s1["cpu_s_sum_over_workers"],
            "stage2_wall_s": s2["wall_s"], "stage2_cpu_s": s2["cpu_s_sum_over_workers"],
        },
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "output_sha256": {n: hashlib.sha256((OUT / n).read_bytes()).hexdigest() for n in ("pilot_v4dev.json", "stage1_v4dev.json", "stage2_v4dev.json")},
    }
    (OUT / "summary_v4dev.json").write_text(json.dumps(summary, indent=1) + "\n")
    for block, name in ((stage1, "stage1"), (stage2, "stage2")):
        for cmp_name, ms in block.items():
            for m, s in ms.items():
                print(f"[{name}] {cmp_name:58s} {m:28s} {s['focal_mean']:.4f} vs {s['ref_mean']:.4f} diff={s['mean_diff_focal_minus_ref']:+.4f} "
                      f"W/L/T={s['wins']}/{s['losses']}/{s['ties']} t={s['t_stat']:+.2f} p={s['paired_t_two_sided_p']:.3g} wilcoxon_p={s['wilcoxon_two_sided_p']:.3g}")
    print(f"wrote {OUT / 'summary_v4dev.json'}")


if __name__ == "__main__":
    main()
