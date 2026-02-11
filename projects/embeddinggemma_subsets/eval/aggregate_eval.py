#!/usr/bin/env python3
"""
Aggregate per-language eval runs into cross-language summaries and charts.
"""

from __future__ import annotations

import argparse
import csv
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


def _dir_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                n += p.stat().st_size
            except OSError:
                continue
    return int(n)


def _resolve_hf_cache_dir(model_ref: str) -> Path | None:
    p = Path(model_ref)
    if p.exists():
        return p
    safe = model_ref.replace("/", "--")
    root = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{safe}"
    snaps = root / "snapshots"
    if not snaps.exists():
        return None
    cand = sorted([x for x in snaps.iterdir() if x.is_dir()])
    return cand[-1] if cand else None


def _plot_bars(categories: list[str], series: dict[str, list[float]], title: str, path: Path, *, ylabel: str) -> None:
    _set_mpl_env()
    import matplotlib.pyplot as plt
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    x = np.arange(len(categories))
    n = max(1, len(series))
    width = 0.8 / n
    plt.figure(figsize=(max(9.0, 1.3 * len(categories)), 5.0))
    for i, (name, vals) in enumerate(series.items()):
        plt.bar(x + (i - (n - 1) / 2) * width, vals, width, label=name)
    plt.xticks(x, categories, rotation=25, ha="right")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _plot_scatter(xs: list[float], ys: list[float], labels: list[str], title: str, path: Path, *, xlabel: str, ylabel: str) -> None:
    _set_mpl_env()
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(7.0, 6.0))
    plt.scatter(xs, ys, s=48, alpha=0.85)
    for x, y, lbl in zip(xs, ys, labels):
        plt.annotate(lbl, (x, y), textcoords="offset points", xytext=(4, 4), fontsize=8)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    runs_root = Path(args.runs_root)
    out_dir = Path(args.out)
    charts_dir = out_dir / "charts"
    metric_files = sorted(runs_root.glob("*/metrics.json"))
    if not metric_files:
        raise SystemExit(f"No metrics.json files found under: {runs_root}")

    rows: dict[str, dict[str, Any]] = {}
    meta: dict[str, Any] = {}
    subset_sizes: dict[str, int] = {}

    for mf in metric_files:
        obj = _load_json(mf)
        langs = obj.get("langs", [])
        if not isinstance(langs, list) or len(langs) != 1:
            continue
        lang = str(langs[0])
        per = obj.get("per_lang", {}).get(lang, {})
        if not isinstance(per, dict):
            continue

        rows[lang] = per
        subset_dir = obj.get("subset_dir")
        if isinstance(subset_dir, str) and subset_dir:
            subset_sizes[lang] = _dir_size_bytes(Path(subset_dir))
        if not meta:
            for k in ("base_model", "device", "max_length", "bench_iters", "bench_warmup", "k"):
                if k in obj:
                    meta[k] = obj[k]

    if not rows:
        raise SystemExit("No usable one-language metrics runs found.")

    base_dir = _resolve_hf_cache_dir(str(meta.get("base_model", "")))
    base_size = _dir_size_bytes(base_dir) if base_dir else 0
    meta["base_model_dir"] = str(base_dir) if base_dir else None
    meta["base_model_size_bytes"] = int(base_size)

    langs = sorted(rows.keys())
    leaderboard: list[dict[str, Any]] = []

    base_r1 = []
    sub_r1 = []
    retention_r1 = []
    base_mrr10 = []
    sub_mrr10 = []
    retention_mrr10 = []
    oov_q = []
    top1 = []
    spearman = []
    qps_base = []
    qps_sub = []
    speedup = []
    size_mb = []
    size_ratio = []

    for l in langs:
        per = rows[l]
        b_r1 = _get(per, ["base", "retrieval", "recall@1"])
        s_r1 = _get(per, ["subset", "retrieval", "recall@1"])
        b_m = _get(per, ["base", "retrieval", "mrr@10"])
        s_m = _get(per, ["subset", "retrieval", "mrr@10"])
        b_qps = _get(per, ["base", "timing", "queries", "texts_per_s_p50"])
        s_qps = _get(per, ["subset", "timing", "queries", "texts_per_s_p50"])
        oov = _get(per, ["subset", "timing", "queries", "oov_rate"])
        t1 = _get(per, ["subset", "agreement", "top1_agreement"])
        sp = _get(per, ["subset", "agreement", "spearman_mean"])
        sbytes = int(subset_sizes.get(l, 0))

        rr1 = (s_r1 / b_r1) if b_r1 > 0 else 0.0
        rm = (s_m / b_m) if b_m > 0 else 0.0
        spdup = (s_qps / b_qps) if b_qps > 0 else 0.0
        sr = (sbytes / base_size) if base_size > 0 else 0.0

        base_r1.append(b_r1)
        sub_r1.append(s_r1)
        retention_r1.append(rr1)
        base_mrr10.append(b_m)
        sub_mrr10.append(s_m)
        retention_mrr10.append(rm)
        oov_q.append(oov)
        top1.append(t1)
        spearman.append(sp)
        qps_base.append(b_qps)
        qps_sub.append(s_qps)
        speedup.append(spdup)
        size_mb.append(sbytes / (1024.0 * 1024.0))
        size_ratio.append(sr)

        leaderboard.append(
            {
                "lang": l,
                "subset_size_mb": round(size_mb[-1], 2),
                "subset_size_ratio": round(sr, 4),
                "recall1_base": round(b_r1, 6),
                "recall1_subset": round(s_r1, 6),
                "recall1_retention": round(rr1, 6),
                "mrr10_base": round(b_m, 6),
                "mrr10_subset": round(s_m, 6),
                "mrr10_retention": round(rm, 6),
                "speed_qps_base": round(b_qps, 3),
                "speed_qps_subset": round(s_qps, 3),
                "speedup_vs_base": round(spdup, 4),
                "oov_rate_queries": round(oov, 6),
                "top1_agreement": round(t1, 6),
                "spearman_mean": round(sp, 6),
            }
        )

    leaderboard.sort(
        key=lambda r: (
            r["recall1_retention"],
            r["mrr10_retention"],
            r["speedup_vs_base"],
            -r["oov_rate_queries"],
        ),
        reverse=True,
    )

    summary = {
        "meta": meta,
        "langs": langs,
        "per_lang": rows,
        "leaderboard": leaderboard,
    }
    _write_json(out_dir / "summary.json", summary)

    csv_path = out_dir / "leaderboard.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(leaderboard[0].keys()))
        writer.writeheader()
        writer.writerows(leaderboard)

    _plot_bars(
        langs,
        {"base_recall@1": base_r1, "subset_recall@1": sub_r1},
        "Recall@1 per language",
        charts_dir / "summary_recall1.png",
        ylabel="Recall@1",
    )
    _plot_bars(
        langs,
        {"retention_recall@1": retention_r1, "retention_mrr@10": retention_mrr10},
        "Quality retention vs base",
        charts_dir / "summary_quality_retention.png",
        ylabel="ratio (subset/base)",
    )
    _plot_bars(
        langs,
        {"subset_oov_rate_queries": oov_q},
        "Subset OOV rate (queries)",
        charts_dir / "summary_oov_rate.png",
        ylabel="OOV rate",
    )
    _plot_bars(
        langs,
        {"top1_agreement": top1, "spearman_mean": spearman},
        "Ranking agreement vs base",
        charts_dir / "summary_agreement.png",
        ylabel="score",
    )
    _plot_bars(
        langs,
        {"base_qps": qps_base, "subset_qps": qps_sub, "speedup_vs_base": speedup},
        "Query throughput and speedup",
        charts_dir / "summary_speed.png",
        ylabel="texts/s or ratio",
    )
    _plot_scatter(
        size_ratio,
        retention_r1,
        langs,
        "Size-quality frontier",
        charts_dir / "summary_size_vs_quality.png",
        xlabel="subset_size / base_size",
        ylabel="recall@1 retention",
    )
    _plot_scatter(
        oov_q,
        retention_r1,
        langs,
        "OOV vs quality retention",
        charts_dir / "summary_oov_vs_quality.png",
        xlabel="oov_rate_queries",
        ylabel="recall@1 retention",
    )

    print(f"Wrote: {out_dir / 'summary.json'}")
    print(f"Wrote: {csv_path}")
    print(f"Wrote charts: {charts_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
