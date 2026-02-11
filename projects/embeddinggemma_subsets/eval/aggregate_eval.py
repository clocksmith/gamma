#!/usr/bin/env python3
"""
Aggregate many per-language eval runs (each with metrics.json) into a single summary.

Typical usage:
  gamma/.venv/bin/python gamma/projects/embeddinggemma_subsets/eval/aggregate_eval.py \
    --runs-root gamma/projects/embeddinggemma_subsets/eval_output/tier_run2 \
    --out gamma/projects/embeddinggemma_subsets/eval_output/tier_run2/summary
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def _set_mpl_env() -> None:
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/xdg-cache")
    os.environ.setdefault("FC_CACHEDIR", "/tmp/fontconfig")
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["FC_CACHEDIR"]).mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _plot_bars(categories: list[str], series: dict[str, list[float]], title: str, path: Path, *, ylabel: str) -> None:
    _set_mpl_env()
    import matplotlib.pyplot as plt
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    x = np.arange(len(categories))
    n = max(1, len(series))
    width = 0.8 / n

    plt.figure(figsize=(max(8.0, 1.2 * len(categories)), 4.5))
    for i, (name, vals) in enumerate(series.items()):
        plt.bar(x + (i - (n - 1) / 2) * width, vals, width, label=name)

    plt.xticks(x, categories, rotation=25, ha="right")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _get(d: dict, path: list[str], default: float = 0.0) -> float:
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    try:
        return float(cur)
    except Exception:
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", required=True, help="Directory with per-language subdirs each containing metrics.json")
    ap.add_argument("--out", required=True, help="Output directory for aggregated summary + charts")
    args = ap.parse_args()

    runs_root = Path(args.runs_root)
    out_dir = Path(args.out)
    charts_dir = out_dir / "charts"

    metric_files = sorted(runs_root.glob("*/metrics.json"))
    if not metric_files:
        raise SystemExit(f"No metrics.json files found under: {runs_root}")

    rows: dict[str, dict[str, Any]] = {}
    meta: dict[str, Any] = {}

    for mf in metric_files:
        obj = _load_json(mf)
        langs = obj.get("langs", [])
        if not isinstance(langs, list) or len(langs) != 1:
            # This aggregator expects each run to be one-language.
            continue
        lang = str(langs[0])
        per = obj.get("per_lang", {}).get(lang, {})
        if not isinstance(per, dict):
            continue

        rows[lang] = per
        # Keep some shared metadata from the first entry.
        if not meta:
            for k in ("base_model", "device", "max_length", "bench_iters", "bench_warmup", "k"):
                if k in obj:
                    meta[k] = obj[k]

    if not rows:
        raise SystemExit("No usable per-language runs found (expected one language per metrics.json).")

    langs = sorted(rows.keys())

    # Collect series.
    base_r1 = []
    sub_r1 = []
    base_mrr10 = []
    sub_mrr10 = []
    oov_q = []
    top1 = []
    spearman = []
    qps = []

    for l in langs:
        per = rows[l]
        base_r1.append(_get(per, ["base", "retrieval", "recall@1"]))
        sub_r1.append(_get(per, ["subset", "retrieval", "recall@1"]))
        base_mrr10.append(_get(per, ["base", "retrieval", "mrr@10"]))
        sub_mrr10.append(_get(per, ["subset", "retrieval", "mrr@10"]))
        oov_q.append(_get(per, ["subset", "timing", "queries", "oov_rate"]))
        top1.append(_get(per, ["subset", "agreement", "top1_agreement"]))
        spearman.append(_get(per, ["subset", "agreement", "spearman_mean"]))
        qps.append(_get(per, ["subset", "timing", "queries", "texts_per_s_p50"]))

    summary = {
        "meta": meta,
        "langs": langs,
        "per_lang": rows,
    }
    _write_json(out_dir / "summary.json", summary)

    # Charts that directly answer "how is each language doing".
    _plot_bars(
        langs,
        {"base_recall@1": base_r1, "subset_recall@1": sub_r1},
        "Recall@1 (base vs subset) per language",
        charts_dir / "summary_recall1.png",
        ylabel="Recall@1",
    )
    _plot_bars(
        langs,
        {"base_mrr@10": base_mrr10, "subset_mrr@10": sub_mrr10},
        "MRR@10 (base vs subset) per language",
        charts_dir / "summary_mrr10.png",
        ylabel="MRR@10",
    )
    _plot_bars(
        langs,
        {"subset_oov_rate_queries": oov_q},
        "Subset OOV rate on queries (lower is better)",
        charts_dir / "summary_oov_rate.png",
        ylabel="OOV rate",
    )
    _plot_bars(
        langs,
        {"top1_agreement": top1, "spearman_mean": spearman},
        "Agreement vs base rankings (higher is better)",
        charts_dir / "summary_agreement.png",
        ylabel="Score",
    )
    _plot_bars(
        langs,
        {"subset_texts_per_s_p50": qps},
        "Speed (subset queries batch) texts/sec p50",
        charts_dir / "summary_speed_qps.png",
        ylabel="texts/sec (p50)",
    )

    print(f"Wrote: {out_dir / 'summary.json'}")
    print(f"Wrote charts: {charts_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

