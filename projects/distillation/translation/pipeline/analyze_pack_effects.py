#!/usr/bin/env python3
"""Analyze per-pack marginal effects from leave-two-out grid results.

Reads orchestrator manifests to map run timestamps to dropped packs,
cross-references with best_external_by_run.csv, fits an additive linear
model, ranks packs, and writes results to a markdown analysis file.

Usage:
    python3 projects/distillation/translation/pipeline/analyze_pack_effects.py
"""

import csv
import itertools
import json
import os
import re
import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parent.parent / "runs"
MANIFESTS_DIR = RUNS_ROOT / "orchestrator_manifests"
BEST_CSV = RUNS_ROOT / "results_bundle" / "best_external_by_run.csv"
OUTPUT_MD = RUNS_ROOT / "results_bundle" / "pack_effect_analysis.md"
OUTPUT_JSON = RUNS_ROOT / "results_bundle" / "pack_effect_analysis.json"

PACK_IDS = [f"{i:02d}" for i in range(1, 9)]
TIMESTAMP_RE = re.compile(r"_(\d{8}T\d{6}Z)$")


def load_manifest_mappings():
    """Build run_name -> (dropped_a, dropped_b).

    Uses two sources:
    1. Orchestrator manifests (run_name -> label mapping)
    2. Direct sources.json inspection (pack composition from input files)

    The second source catches runs that were re-launched outside the original
    manifest or whose manifest entry has a stale/missing run_name.
    """
    mapping = {}

    # Source 1: orchestrator manifests
    if MANIFESTS_DIR.is_dir():
        for manifest_path in sorted(MANIFESTS_DIR.glob("gold_leave_two_out_grid_*.json")):
            with open(manifest_path) as f:
                manifest = json.load(f)
            entries = manifest.get("entries", []) if isinstance(manifest, dict) else manifest
            for entry in entries:
                label = entry.get("label", "")
                run_name = entry.get("run_name", "")
                omitted = entry.get("omitted_packs", [])
                m = re.search(r"rows1920_drop_(\d{2})_(\d{2})", label)
                if m and run_name:
                    mapping[run_name] = (m.group(1), m.group(2))
                elif len(omitted) == 2 and run_name:
                    ids = []
                    for p in omitted:
                        pm = re.search(r"pack_(\d{2})", p)
                        if pm:
                            ids.append(pm.group(1))
                    if len(ids) == 2:
                        mapping[run_name] = (ids[0], ids[1])

    # Source 2: direct sources.json inspection for any rows1920 goldgrid run
    # not already mapped
    all_packs = set(PACK_IDS)
    for run_dir in RUNS_ROOT.iterdir():
        run_name = run_dir.name
        if run_name in mapping:
            continue
        if "rows1920" not in run_name or "goldgrid" not in run_name:
            continue
        sources_path = run_dir / "inputs" / "train_pairs.rows1920.merged.jsonl.sources.json"
        if not sources_path.exists():
            continue
        try:
            with open(sources_path) as f:
                data = json.load(f)
            included = []
            for s in data.get("sources", []):
                pm = re.search(r"pack_(\d{2})", s.get("path", ""))
                if pm:
                    included.append(pm.group(1))
            if len(included) == 6:
                dropped = sorted(all_packs - set(included))
                if len(dropped) == 2:
                    mapping[run_name] = (dropped[0], dropped[1])
        except (json.JSONDecodeError, KeyError):
            continue

    return mapping


def load_best_external():
    """Load best_external_by_run.csv, return list of dicts."""
    rows = []
    with open(BEST_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def extract_timestamp(run_name):
    """Extract trailing timestamp from a run name."""
    m = TIMESTAMP_RE.search(run_name)
    return m.group(1) if m else None


def fit_additive_model(observations):
    """Fit per-pack effects using ordinary least squares on a binary design matrix.

    Each observation is (included_packs: set, bleu: float).
    Returns (intercept, {pack_id: effect}).

    The model is: BLEU = intercept + sum(effect_i for i in included_packs)
    Since every run includes exactly 6 packs, intercept absorbs the mean of 6 effects.
    We use numpy-free manual OLS via normal equations (X^T X)^{-1} X^T y.
    """
    n = len(observations)
    p = len(PACK_IDS) + 1  # intercept + 8 pack indicators

    # Build design matrix X and response y
    X = []
    y = []
    for included, bleu in observations:
        row = [1.0]  # intercept
        for pid in PACK_IDS:
            row.append(1.0 if pid in included else 0.0)
        X.append(row)
        y.append(bleu)

    # Solve X^T X beta = X^T y using Gaussian elimination
    # Build augmented normal equations
    XtX = [[0.0] * p for _ in range(p)]
    Xty = [0.0] * p
    for i in range(n):
        for j in range(p):
            for k in range(p):
                XtX[j][k] += X[i][j] * X[i][k]
            Xty[j] += X[i][j] * y[i]

    # Gaussian elimination with partial pivoting
    aug = [XtX[i][:] + [Xty[i]] for i in range(p)]
    for col in range(p):
        # Pivot
        max_row = col
        for row in range(col + 1, p):
            if abs(aug[row][col]) > abs(aug[max_row][col]):
                max_row = row
        aug[col], aug[max_row] = aug[max_row], aug[col]
        if abs(aug[col][col]) < 1e-12:
            continue
        for row in range(col + 1, p):
            factor = aug[row][col] / aug[col][col]
            for k in range(col, p + 1):
                aug[row][k] -= factor * aug[col][k]

    # Back substitution
    beta = [0.0] * p
    for i in range(p - 1, -1, -1):
        s = aug[i][p]
        for j in range(i + 1, p):
            s -= aug[i][j] * beta[j]
        if abs(aug[i][i]) > 1e-12:
            beta[i] = s / aug[i][i]

    intercept = beta[0]
    effects = {}
    for idx, pid in enumerate(PACK_IDS):
        effects[pid] = beta[idx + 1]

    # Compute residuals and R-squared
    y_mean = sum(y) / n
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    ss_res = 0.0
    residuals = []
    for i in range(n):
        y_hat = sum(X[i][j] * beta[j] for j in range(p))
        residuals.append(y[i] - y_hat)
        ss_res += (y[i] - y_hat) ** 2
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return intercept, effects, r_squared, residuals


def predict_bleu(intercept, effects, included_packs):
    """Predict BLEU for a given set of included packs."""
    return intercept + sum(effects.get(p, 0.0) for p in included_packs)


def main():
    # Load mappings
    name_to_dropped = load_manifest_mappings()
    best_rows = load_best_external()
    print(f"Loaded {len(name_to_dropped)} manifest entries, {len(best_rows)} CSV rows")

    # Match runs to dropped packs
    observations_bleu = []
    observations_chrf = []
    matched_rows = []

    for row in best_rows:
        run_name = row.get("run_name", "")
        if "rows1920" not in run_name or "goldgrid" not in run_name:
            continue
        if run_name not in name_to_dropped:
            continue
        bleu_str = row.get("external_bleu", "")
        chrf_str = row.get("external_chrf", "")
        if not bleu_str:
            continue
        dropped = name_to_dropped[run_name]
        included = set(PACK_IDS) - {dropped[0], dropped[1]}
        bleu = float(bleu_str)
        chrf = float(chrf_str) if chrf_str else None

        observations_bleu.append((included, bleu))
        if chrf is not None:
            observations_chrf.append((included, chrf))
        matched_rows.append({
            "run_name": run_name,
            "dropped": list(dropped),
            "included": sorted(included),
            "bleu": bleu,
            "chrf": chrf,
        })

    if len(observations_bleu) < 3:
        print(f"Only {len(observations_bleu)} matched leave-two-out runs. Need more data.")
        sys.exit(1)

    # Fit models
    intercept_b, effects_b, r2_b, residuals_b = fit_additive_model(observations_bleu)
    intercept_c, effects_c, r2_c, residuals_c = fit_additive_model(observations_chrf)

    # Rank packs
    ranked_bleu = sorted(effects_b.items(), key=lambda x: x[1], reverse=True)
    ranked_chrf = sorted(effects_c.items(), key=lambda x: x[1], reverse=True)

    # Generate predictions for confirmation ladder
    rank_order = [pid for pid, _ in ranked_bleu]
    predictions = {}
    for k in range(1, 9):
        top_k = set(rank_order[:k])
        pred_bleu = predict_bleu(intercept_b, effects_b, top_k)
        pred_chrf = predict_bleu(intercept_c, effects_c, top_k)
        predictions[k] = {
            "packs": sorted(top_k),
            "rows": k * 320,
            "predicted_bleu": round(pred_bleu, 4),
            "predicted_chrf": round(pred_chrf, 4),
        }

    # Build confirmation ladder
    ladder = []
    # Best-4
    ladder.append({"label": "best-4", "packs": sorted(rank_order[:4]), "rows": 1280,
                    "purpose": "Can curated 1280 beat legacy 1280?"})
    # Best-5
    ladder.append({"label": "best-5", "packs": sorted(rank_order[:5]), "rows": 1600,
                    "purpose": "Untested size class -- sweet spot?"})
    # Best-6
    ladder.append({"label": "best-6", "packs": sorted(rank_order[:6]), "rows": 1920,
                    "purpose": "Confirm predicted top-6 matches observed best"})
    # Best-7
    ladder.append({"label": "best-7", "packs": sorted(rank_order[:7]), "rows": 2240,
                    "purpose": "Does adding the 7th pack help or dilute?"})
    # Swap-6: replace worst-included with next-best-excluded
    swap_packs = set(rank_order[:6])
    swap_packs.discard(rank_order[5])
    swap_packs.add(rank_order[6])
    ladder.append({"label": "swap-6", "packs": sorted(swap_packs), "rows": 1920,
                    "purpose": f"Swap test: {rank_order[5]} out, {rank_order[6]} in"})
    # Best-8 (all packs, already have anchor)
    ladder.append({"label": "best-8 (anchor)", "packs": sorted(PACK_IDS), "rows": 2560,
                    "purpose": "Already tested -- all packs"})

    # Detect missing combinations
    observed_drops = {tuple(m["dropped"]) for m in matched_rows}
    all_combos = list(itertools.combinations(PACK_IDS, 2))
    missing = {}
    for combo in all_combos:
        if combo not in observed_drops:
            missing[f"drop_{combo[0]}_{combo[1]}"] = "not matched"

    # Write JSON output
    result = {
        "generated_utc": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "matched_runs": len(observations_bleu),
        "missing_runs": missing,
        "model_fit": {
            "bleu": {
                "intercept": round(intercept_b, 4),
                "r_squared": round(r2_b, 4),
                "effects": {k: round(v, 4) for k, v in effects_b.items()},
                "ranking": [pid for pid, _ in ranked_bleu],
                "max_residual": round(max(abs(r) for r in residuals_b), 4),
            },
            "chrf": {
                "intercept": round(intercept_c, 4),
                "r_squared": round(r2_c, 4),
                "effects": {k: round(v, 4) for k, v in effects_c.items()},
                "ranking": [pid for pid, _ in ranked_chrf],
                "max_residual": round(max(abs(r) for r in residuals_c), 4),
            },
        },
        "predictions": predictions,
        "confirmation_ladder": ladder,
        "observations": matched_rows,
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(f"Wrote {OUTPUT_JSON}")

    # Write markdown output
    lines = []
    lines.append("# Per-Pack Effect Analysis")
    lines.append("")
    lines.append(f"Generated: {result['generated_utc']}")
    lines.append(f"Matched leave-two-out runs: {len(observations_bleu)} of 28")
    lines.append("")
    lines.append("Missing runs:")
    for label, status in result["missing_runs"].items():
        lines.append(f"- `{label}`: {status}")
    lines.append("")

    lines.append("## Model Fit")
    lines.append("")
    lines.append(f"- BLEU R-squared: {r2_b:.4f} (max residual: {max(abs(r) for r in residuals_b):.4f})")
    lines.append(f"- chrF R-squared: {r2_c:.4f} (max residual: {max(abs(r) for r in residuals_c):.4f})")
    lines.append("")
    if r2_b > 0.7:
        lines.append("The additive model explains most of the variance. Pack effects are roughly independent.")
    elif r2_b > 0.4:
        lines.append("The additive model explains moderate variance. Some pack interactions may exist.")
    else:
        lines.append("WARNING: The additive model is a poor fit. Pack interactions are likely significant.")
    lines.append("")

    lines.append("## Pack Ranking (by external BLEU effect)")
    lines.append("")
    lines.append("| Rank | Pack | BLEU Effect | chrF Effect | Quality Score |")
    lines.append("| --- | --- | --- | --- | --- |")
    for rank_idx, (pid, bleu_eff) in enumerate(ranked_bleu, 1):
        chrf_eff = effects_c.get(pid, 0.0)
        # Find pack quality score from filename
        lines.append(f"| {rank_idx} | pack_{pid} | {bleu_eff:+.4f} | {chrf_eff:+.4f} | - |")
    lines.append("")

    lines.append("## BLEU and chrF Ranking Agreement")
    lines.append("")
    bleu_rank = [pid for pid, _ in ranked_bleu]
    chrf_rank = [pid for pid, _ in ranked_chrf]
    if bleu_rank == chrf_rank:
        lines.append("BLEU and chrF rankings are identical. Strong signal.")
    else:
        lines.append(f"BLEU ranking: {' > '.join(bleu_rank)}")
        lines.append(f"chrF ranking: {' > '.join(chrf_rank)}")
        # Check top-4 agreement
        if set(bleu_rank[:4]) == set(chrf_rank[:4]):
            lines.append("Top-4 sets agree between BLEU and chrF.")
        else:
            lines.append("Top-4 sets DISAGREE between BLEU and chrF. Treat boundary packs with caution.")
    lines.append("")

    lines.append("## Predicted BLEU by Pack Count (top-K)")
    lines.append("")
    lines.append("| Packs | Rows | Packs Included | Predicted BLEU | Predicted chrF |")
    lines.append("| --- | --- | --- | --- | --- |")
    for k in range(1, 9):
        p = predictions[k]
        packs_str = ", ".join(p["packs"])
        lines.append(f"| {k} | {p['rows']} | {packs_str} | {p['predicted_bleu']:.4f} | {p['predicted_chrf']:.4f} |")
    lines.append("")

    lines.append("## Confirmation Ladder")
    lines.append("")
    lines.append("These are the recommended targeted runs to explore the full size spectrum.")
    lines.append("")
    lines.append("| Label | Packs | Rows | Predicted BLEU | Purpose |")
    lines.append("| --- | --- | --- | --- | --- |")
    for step in ladder:
        packs_str = ", ".join(step["packs"])
        pred = predict_bleu(intercept_b, effects_b, set(step["packs"]))
        lines.append(f"| {step['label']} | {packs_str} | {step['rows']} | {pred:.4f} | {step['purpose']} |")
    lines.append("")

    lines.append("## Observed Run Data")
    lines.append("")
    lines.append("| Dropped | Included | Best BLEU | Best chrF |")
    lines.append("| --- | --- | --- | --- |")
    for obs in sorted(matched_rows, key=lambda x: x["bleu"], reverse=True):
        dropped_str = ", ".join(obs["dropped"])
        included_str = ", ".join(obs["included"])
        chrf_str = f"{obs['chrf']:.4f}" if obs["chrf"] else "n/a"
        lines.append(f"| {dropped_str} | {included_str} | {obs['bleu']:.4f} | {chrf_str} |")
    lines.append("")

    with open(OUTPUT_MD, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
