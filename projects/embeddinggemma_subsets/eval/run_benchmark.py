#!/usr/bin/env python3
"""
Repeated benchmark mode with confidence intervals for quality + performance.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np


DEFAULT_K_MAP = {
    "en": 50000,
    "es": 50000,
    "ar": 50000,
    "fr": 50000,
    "pt": 50000,
    "zh": 80000,
    "ja": 80000,
    "hi": 80000,
}


def _set_mpl_env() -> None:
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/xdg-cache")
    os.environ.setdefault("FC_CACHEDIR", "/tmp/fontconfig")
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["FC_CACHEDIR"]).mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _mean_std_ci(values: list[float]) -> dict[str, float]:
    if not values:
        return {"n": 0.0, "mean": 0.0, "std": 0.0, "ci95": 0.0}
    arr = np.array(values, dtype=np.float64)
    n = float(len(arr))
    mean = float(arr.mean())
    std = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0
    ci = float(1.96 * std / np.sqrt(max(1.0, n))) if len(arr) > 1 else 0.0
    return {"n": n, "mean": mean, "std": std, "ci95": ci}


def _plot_error_bars(
    categories: list[str],
    series: dict[str, tuple[list[float], list[float]]],
    *,
    title: str,
    ylabel: str,
    path: Path,
) -> None:
    _set_mpl_env()
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.arange(len(categories))
    n = max(1, len(series))
    width = 0.8 / n
    plt.figure(figsize=(max(9.0, 1.3 * len(categories)), 5.0))
    for i, (name, (vals, errs)) in enumerate(series.items()):
        offs = x + (i - (n - 1) / 2) * width
        plt.bar(offs, vals, width=width, label=name)
        plt.errorbar(offs, vals, yerr=errs, fmt="none", ecolor="black", elinewidth=1, capsize=2)
    plt.xticks(x, categories, rotation=25, ha="right")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path)
    plt.close()


def _run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def _subset_dir(subset_root: Path, lang: str, k_map: dict[str, int], pattern: str) -> Path:
    k = int(k_map.get(lang, 50000))
    return subset_root / pattern.format(lang=lang, k=k)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", default=None, help="Base model path/repo when comparing against a fixed teacher.")
    ap.add_argument("--base-root", default=None, help="Base subset root for per-language base models.")
    ap.add_argument("--base-pattern", default="google__embeddinggemma-300m-{lang}-vocab{k}", help="Base subset pattern when --base-root is set.")
    ap.add_argument("--base-tokenizer", default=None, help="Optional tokenizer source path/repo for both models.")
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--subset-root", default="gamma/projects/embeddinggemma_subsets/output")
    ap.add_argument("--subset-pattern", default="google__embeddinggemma-300m-{lang}-vocab{k}")
    ap.add_argument("--langs", default="en,es,zh,ja,ar,fr,pt,hi")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--max-length", type=int, default=96)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--bench-iters", type=int, default=3)
    ap.add_argument("--bench-warmup", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    has_base_model = bool(args.base_model)
    has_base_root = bool(args.base_root)
    if has_base_model == has_base_root:
        raise SystemExit("Exactly one of --base-model or --base-root must be set.")

    root = Path(args.out)
    runs_root = root / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    langs = [x.strip() for x in str(args.langs).split(",") if x.strip()]
    k_map = dict(DEFAULT_K_MAP)
    run_eval = Path("gamma/projects/embeddinggemma_subsets/eval/run_eval.py")

    for rep in range(int(args.repeats)):
        for lang in langs:
            out = runs_root / f"repeat_{rep:02d}" / lang
            subset = _subset_dir(Path(args.subset_root), lang, k_map, str(args.subset_pattern))
            if has_base_model:
                base_arg = str(args.base_model)
            else:
                base_arg = str(_subset_dir(Path(args.base_root), lang, k_map, str(args.base_pattern)))
            cmd = [
                sys.executable,
                str(run_eval),
                "--base-model",
                base_arg,
                "--subset-dir",
                str(subset),
                "--dataset",
                str(args.dataset),
                "--langs",
                lang,
                "--device",
                str(args.device),
                "--max-length",
                str(int(args.max_length)),
                "--batch-size",
                str(int(args.batch_size)),
                "--bench-iters",
                str(int(args.bench_iters)),
                "--bench-warmup",
                str(int(args.bench_warmup)),
                "--out",
                str(out),
            ]
            if args.base_tokenizer:
                cmd.extend(["--base-tokenizer", str(args.base_tokenizer)])
            _run(cmd)

    per_lang: dict[str, Any] = {}
    for lang in langs:
        rows: list[dict[str, float]] = []
        for rep in range(int(args.repeats)):
            mf = runs_root / f"repeat_{rep:02d}" / lang / "metrics.json"
            obj = _load_json(mf)
            pl = obj["per_lang"][lang]
            base = pl["base"]
            sub = pl["subset"]
            row = {
                "recall1_base": float(base["retrieval"].get("recall@1", 0.0)),
                "recall1_subset": float(sub["retrieval"].get("recall@1", 0.0)),
                "mrr10_base": float(base["retrieval"].get("mrr@10", 0.0)),
                "mrr10_subset": float(sub["retrieval"].get("mrr@10", 0.0)),
                "oov_rate_queries": float(sub["timing"]["queries"].get("oov_rate", 0.0)),
                "qps_base": float(base["timing"]["queries"].get("texts_per_s_total", base["timing"]["queries"].get("texts_per_s_p50", 0.0))),
                "qps_subset": float(sub["timing"]["queries"].get("texts_per_s_total", sub["timing"]["queries"].get("texts_per_s_p50", 0.0))),
                "prefill_ms_base": float(base["timing"]["queries"].get("prefill_ms", 0.0)),
                "prefill_ms_subset": float(sub["timing"]["queries"].get("prefill_ms", 0.0)),
                "vram_mb_base": float(base["timing"]["queries"].get("peak_vram_allocated_mb", 0.0)),
                "vram_mb_subset": float(sub["timing"]["queries"].get("peak_vram_allocated_mb", 0.0)),
            }
            row["recall1_retention"] = (row["recall1_subset"] / row["recall1_base"]) if row["recall1_base"] > 0 else 0.0
            row["mrr10_retention"] = (row["mrr10_subset"] / row["mrr10_base"]) if row["mrr10_base"] > 0 else 0.0
            row["speedup"] = (row["qps_subset"] / row["qps_base"]) if row["qps_base"] > 0 else 0.0
            rows.append(row)

        agg = {}
        for key in rows[0].keys():
            agg[key] = _mean_std_ci([r[key] for r in rows])
        per_lang[lang] = {"runs": rows, "aggregate": agg}

    summary = {
        "base_model": str(args.base_model) if has_base_model else None,
        "base_root": str(args.base_root) if has_base_root else None,
        "base_pattern": str(args.base_pattern) if has_base_root else None,
        "base_tokenizer": str(args.base_tokenizer) if args.base_tokenizer else None,
        "dataset": str(args.dataset),
        "device": str(args.device),
        "max_length": int(args.max_length),
        "batch_size": int(args.batch_size),
        "repeats": int(args.repeats),
        "bench_iters": int(args.bench_iters),
        "bench_warmup": int(args.bench_warmup),
        "per_lang": per_lang,
    }
    _write_json(root / "benchmark_summary.json", summary)

    charts = root / "charts"
    cats = langs
    r1_ret_m = [per_lang[l]["aggregate"]["recall1_retention"]["mean"] for l in cats]
    r1_ret_ci = [per_lang[l]["aggregate"]["recall1_retention"]["ci95"] for l in cats]
    sp_m = [per_lang[l]["aggregate"]["speedup"]["mean"] for l in cats]
    sp_ci = [per_lang[l]["aggregate"]["speedup"]["ci95"] for l in cats]
    pf_b = [per_lang[l]["aggregate"]["prefill_ms_base"]["mean"] for l in cats]
    pf_b_ci = [per_lang[l]["aggregate"]["prefill_ms_base"]["ci95"] for l in cats]
    pf_s = [per_lang[l]["aggregate"]["prefill_ms_subset"]["mean"] for l in cats]
    pf_s_ci = [per_lang[l]["aggregate"]["prefill_ms_subset"]["ci95"] for l in cats]
    vr_b = [per_lang[l]["aggregate"]["vram_mb_base"]["mean"] for l in cats]
    vr_b_ci = [per_lang[l]["aggregate"]["vram_mb_base"]["ci95"] for l in cats]
    vr_s = [per_lang[l]["aggregate"]["vram_mb_subset"]["mean"] for l in cats]
    vr_s_ci = [per_lang[l]["aggregate"]["vram_mb_subset"]["ci95"] for l in cats]

    _plot_error_bars(
        cats,
        {"recall1_retention": (r1_ret_m, r1_ret_ci)},
        title="Recall@1 retention vs base (mean +/- 95% CI)",
        ylabel="retention",
        path=charts / "benchmark_recall1_retention_ci.png",
    )
    _plot_error_bars(
        cats,
        {"speedup_qps": (sp_m, sp_ci)},
        title="Throughput speedup vs base (mean +/- 95% CI)",
        ylabel="speedup",
        path=charts / "benchmark_speedup_ci.png",
    )
    _plot_error_bars(
        cats,
        {"prefill_base_ms": (pf_b, pf_b_ci), "prefill_subset_ms": (pf_s, pf_s_ci)},
        title="Prefill latency (mean +/- 95% CI)",
        ylabel="ms",
        path=charts / "benchmark_prefill_ci.png",
    )
    _plot_error_bars(
        cats,
        {"vram_base_mb": (vr_b, vr_b_ci), "vram_subset_mb": (vr_s, vr_s_ci)},
        title="Peak VRAM allocated (mean +/- 95% CI)",
        ylabel="MB",
        path=charts / "benchmark_vram_ci.png",
    )

    print(f"Wrote: {root / 'benchmark_summary.json'}")
    print(f"Wrote charts: {charts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
