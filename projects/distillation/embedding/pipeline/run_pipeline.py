#!/usr/bin/env python3
"""
Unified, resumable end-to-end pipeline for EmbeddingGemma subset data + training.

Workspace layout (single raw root):
  <workspace>/
    raw/
      wiki/<lang>.jsonl
      gemini/<lang>.jsonl
      merged/<lang>.jsonl
      train/<lang>.jsonl
      eval/<lang>.jsonl
    corpora/
      train/<lang>.txt
      eval/<lang>.txt
    datasets/
      train/<lang>/dataset.json
      eval/<lang>/dataset.json
    training/distill_pairs.jsonl
    models/distilled/<...>
    eval/benchmark/...
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path


LANGS_DEFAULT = "en,es,zh,ja,ar,fr,pt,hi"
K_MAP = {
    "en": 50000,
    "es": 50000,
    "ar": 50000,
    "fr": 50000,
    "pt": 50000,
    "zh": 80000,
    "ja": 80000,
    "hi": 80000,
}


def _run(cmd: list[str]) -> None:
    start = time.perf_counter()
    print("+", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    finally:
        elapsed = time.perf_counter() - start
        print(f"[run] elapsed={elapsed:.2f}s")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _config_hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _write_done_manifest(path: Path, *, step: str, config_hash: str, outputs: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "step": step,
        "completed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config_hash": config_hash,
        "outputs": [
            {
                "path": str(p),
                "bytes": int(p.stat().st_size),
                "sha256": _sha256_file(p),
            }
            for p in outputs
            if p.exists() and p.is_file()
        ],
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _done_manifest_matches(path: Path, *, config_hash: str, outputs: list[Path]) -> bool:
    if not path.exists():
        return False
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if str(obj.get("config_hash", "")) != str(config_hash):
        return False
    by_path = {
        str(item.get("path", "")): item
        for item in obj.get("outputs", [])
        if isinstance(item, dict) and item.get("path")
    }
    for out in outputs:
        if not out.exists() or not out.is_file():
            return False
        rec = by_path.get(str(out))
        if not rec:
            return False
        try:
            want_bytes = int(rec.get("bytes", -1))
        except Exception:
            return False
        if int(out.stat().st_size) != want_bytes:
            return False
        if str(rec.get("sha256", "")) != _sha256_file(out):
            return False
    return True


def _resolve_hf_snapshot_dir(model_ref: str) -> str:
    """
    If `model_ref` points at a HuggingFace cache model root directory like:
      .../models--ORG--NAME/
    then resolve it to the newest snapshot directory:
      .../models--ORG--NAME/snapshots/<hash>

    If `model_ref` already points at a snapshot (contains tokenizer/config/model files),
    it is returned unchanged. Non-path refs (HF ids) are returned unchanged.
    """
    s = str(model_ref).strip()
    if not s:
        return s
    p = Path(s)
    if not p.exists() or not p.is_dir():
        return str(model_ref)

    # If the directory already looks like a model snapshot/checkout, keep it.
    if (p / "config.json").exists() and ((p / "tokenizer.json").exists() or (p / "tokenizer.model").exists()):
        return str(p)

    snaps = p / "snapshots"
    if not snaps.exists() or not snaps.is_dir():
        return str(p)

    cand = [d for d in snaps.iterdir() if d.is_dir()]
    if not cand:
        return str(p)

    # Choose newest by mtime for robustness.
    cand.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return str(cand[0])


def _validate_model_ref(model_ref: str, *, arg_name: str) -> None:
    s = str(model_ref).strip()
    if not s:
        raise SystemExit(
            f"{arg_name} is empty. If you passed --base-model \"$BASE_MODEL\", "
            "export BASE_MODEL first or pass the full model path directly."
        )
    p = Path(s)
    if p.exists() and p.is_dir():
        if (p / "config.json").exists():
            return
        snaps = p / "snapshots"
        if snaps.exists() and snaps.is_dir() and any(d.is_dir() for d in snaps.iterdir()):
            return
        raise SystemExit(
            f"{arg_name} points to a directory that does not look like a HF model: {p}. "
            "Expected config.json or snapshots/<hash>/."
        )


def _run_parallel(items: list[str], fn, *, max_workers: int, label: str) -> None:
    if not items:
        return
    workers = max(1, min(int(max_workers), len(items)))
    if workers <= 1:
        for item in items:
            fn(item)
        return
    print(f"[{label}] parallel workers={workers} tasks={len(items)}")
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        fut_map = {ex.submit(fn, item): item for item in items}
        for fut in cf.as_completed(fut_map):
            item = fut_map[fut]
            try:
                fut.result()
            except Exception as e:
                raise RuntimeError(f"[{label}] failed for {item}: {e}") from e


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def _count_dataset_docs(ds_path: Path) -> int:
    if not ds_path.exists():
        return 0
    try:
        obj = json.loads(ds_path.read_text(encoding="utf-8"))
        return int(len(obj.get("docs", [])))
    except Exception:
        return 0


def _read_jsonl_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            txt = str(obj.get("text", "")).strip()
            if not txt:
                continue
            rows.append(obj)
    return rows


def _stable_lang_seed(base_seed: int, lang: str) -> int:
    return int(base_seed) + sum((i + 1) * ord(ch) for i, ch in enumerate(lang))


def _split_jsonl_train_eval(src: Path, out_train: Path, out_eval: Path, *, train_frac: float, seed: int) -> tuple[int, int]:
    rows = _read_jsonl_rows(src)
    out_train.parent.mkdir(parents=True, exist_ok=True)
    out_eval.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        out_train.write_text("", encoding="utf-8")
        out_eval.write_text("", encoding="utf-8")
        return (0, 0)

    rnd = random.Random(int(seed))
    rnd.shuffle(rows)

    split = int(len(rows) * float(train_frac))
    split = max(1, min(len(rows) - 1, split)) if len(rows) > 1 else len(rows)
    train_rows = rows[:split]
    eval_rows = rows[split:]

    with out_train.open("w", encoding="utf-8") as f:
        for obj in train_rows:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    with out_eval.open("w", encoding="utf-8") as f:
        for obj in eval_rows:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    return (len(train_rows), len(eval_rows))


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _existing_langs_for_pattern(root: Path, pattern: str, langs: list[str]) -> list[str]:
    out: list[str] = []
    for lang in langs:
        k = int(K_MAP.get(lang, 50000))
        model_dir = root / pattern.format(lang=lang, k=k)
        if model_dir.exists():
            out.append(lang)
    return out


def _resolve_benchmark_dataset_dir(datasets_eval_dir: Path, datasets_root: Path) -> Path:
    if datasets_eval_dir.exists():
        return datasets_eval_dir
    return datasets_root


def _summarize_benchmark_tracks(benchmark_out: Path, tracks: list[str]) -> None:
    summary: dict[str, dict] = {"tracks": {}}
    for track in tracks:
        p = benchmark_out / track / "benchmark_summary.json"
        if not p.exists():
            continue
        obj = _load_json(p)
        per_lang = obj.get("per_lang", {})
        track_langs: dict[str, dict] = {}
        for lang, blob in per_lang.items():
            agg = blob.get("aggregate", {})
            track_langs[lang] = {
                "recall1_retention_mean": float(agg.get("recall1_retention", {}).get("mean", 0.0)),
                "mrr10_retention_mean": float(agg.get("mrr10_retention", {}).get("mean", 0.0)),
                "speedup_mean": float(agg.get("speedup", {}).get("mean", 0.0)),
                "prefill_ms_base_mean": float(agg.get("prefill_ms_base", {}).get("mean", 0.0)),
                "prefill_ms_subset_mean": float(agg.get("prefill_ms_subset", {}).get("mean", 0.0)),
                "oov_rate_queries_mean": float(agg.get("oov_rate_queries", {}).get("mean", 0.0)),
            }
        summary["tracks"][track] = {
            "source_summary": str(p),
            "langs": track_langs,
        }
    pre = summary["tracks"].get("base_vs_pre", {}).get("langs", {})
    post = summary["tracks"].get("base_vs_post", {}).get("langs", {})
    derived: dict[str, dict] = {}
    for lang in sorted(set(pre.keys()) & set(post.keys())):
        pre_l = pre[lang]
        post_l = post[lang]
        pre_r1 = float(pre_l.get("recall1_retention_mean", 0.0))
        pre_mrr = float(pre_l.get("mrr10_retention_mean", 0.0))
        pre_spd = float(pre_l.get("speedup_mean", 0.0))
        post_r1 = float(post_l.get("recall1_retention_mean", 0.0))
        post_mrr = float(post_l.get("mrr10_retention_mean", 0.0))
        post_spd = float(post_l.get("speedup_mean", 0.0))
        derived[lang] = {
            "recall1_post_over_pre": (post_r1 / pre_r1) if pre_r1 > 0 else 0.0,
            "mrr10_post_over_pre": (post_mrr / pre_mrr) if pre_mrr > 0 else 0.0,
            "speedup_post_over_pre": (post_spd / pre_spd) if pre_spd > 0 else 0.0,
            "oov_rate_delta_post_minus_pre": float(post_l.get("oov_rate_queries_mean", 0.0)) - float(pre_l.get("oov_rate_queries_mean", 0.0)),
            "prefill_ms_delta_post_minus_pre": float(post_l.get("prefill_ms_subset_mean", 0.0)) - float(pre_l.get("prefill_ms_subset_mean", 0.0)),
        }
    summary["derived"] = {"pre_vs_post_from_base_relative": derived}
    out = benchmark_out / "benchmark_compare_summary.json"
    out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[benchmark] wrote combined summary: {out}")
    _write_compare_charts(benchmark_out, summary)


def _write_compare_charts(benchmark_out: Path, summary: dict) -> None:
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/xdg-cache")
    os.environ.setdefault("FC_CACHEDIR", "/tmp/fontconfig")
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["FC_CACHEDIR"]).mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib

        import matplotlib.pyplot as plt
    except Exception as e:
        print(f"[benchmark] skip combined charts: matplotlib unavailable ({e})")
        return

    tracks = summary.get("tracks", {})
    track_order = ["base_vs_pre", "base_vs_post", "pre_vs_post"]
    track_labels = {
        "base_vs_pre": "main vs pre",
        "base_vs_post": "main vs post",
        "pre_vs_post": "pre vs post",
    }

    langs: list[str] = []
    seen: set[str] = set()
    for t in track_order:
        for lang in tracks.get(t, {}).get("langs", {}).keys():
            if lang not in seen:
                seen.add(lang)
                langs.append(lang)
    if not langs:
        return

    charts_dir = benchmark_out / "compare_charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    metric_defs = [
        ("recall1_retention_mean", "Recall@1 Retention", "retention"),
        ("mrr10_retention_mean", "MRR@10 Retention", "retention"),
        ("speedup_mean", "Throughput Speedup", "speedup"),
    ]

    def _plot_grouped(metric_key: str, title: str, ylabel: str, out_name: str) -> None:
        x = list(range(len(langs)))
        n = len(track_order)
        width = 0.8 / max(1, n)
        plt.figure(figsize=(max(10.0, 1.2 * len(langs)), 5.0))
        for i, t in enumerate(track_order):
            vals = []
            for lang in langs:
                vals.append(float(tracks.get(t, {}).get("langs", {}).get(lang, {}).get(metric_key, 0.0)))
            offs = [xi + (i - (n - 1) / 2) * width for xi in x]
            plt.bar(offs, vals, width=width, label=track_labels.get(t, t))
        plt.xticks(x, langs, rotation=25, ha="right")
        plt.title(title)
        plt.ylabel(ylabel)
        plt.legend()
        plt.tight_layout()
        plt.savefig(charts_dir / out_name)
        plt.close()

    for key, title, ylabel in metric_defs:
        _plot_grouped(
            key,
            f"{title} by Language (main/pre/post comparisons)",
            ylabel,
            f"by_language_{key}.png",
        )

    # Aggregate over all languages per track (simple mean of available languages).
    agg_metrics = ["recall1_retention_mean", "mrr10_retention_mean", "speedup_mean", "oov_rate_queries_mean"]
    agg_values: dict[str, dict[str, float]] = {}
    for t in track_order:
        by_lang = tracks.get(t, {}).get("langs", {})
        agg_values[t] = {}
        for m in agg_metrics:
            vals = [float(by_lang.get(lang, {}).get(m, 0.0)) for lang in by_lang.keys()]
            agg_values[t][m] = (sum(vals) / len(vals)) if vals else 0.0

    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    ax_list = [axes[0][0], axes[0][1], axes[1][0], axes[1][1]]
    titles = {
        "recall1_retention_mean": "Mean Recall@1 Retention",
        "mrr10_retention_mean": "Mean MRR@10 Retention",
        "speedup_mean": "Mean Throughput Speedup",
        "oov_rate_queries_mean": "Mean OOV Rate (queries)",
    }
    for ax, m in zip(ax_list, agg_metrics):
        vals = [agg_values[t][m] for t in track_order]
        labs = [track_labels.get(t, t) for t in track_order]
        ax.bar(labs, vals)
        ax.set_title(titles[m])
        ax.tick_params(axis="x", rotation=20)
    plt.tight_layout()
    plt.savefig(charts_dir / "aggregate_all_languages.png")
    plt.close()
    print(f"[benchmark] wrote combined charts: {charts_dir}")


def _iter_jsonl_texts(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            txt = str(obj.get("text", "")).strip()
            if txt:
                yield txt


def _norm(s: str) -> str:
    return " ".join(s.split()).strip().lower()


def _merge_lang(sources: list[tuple[str, Path]], out: Path, *, max_rows: int, min_chars: int) -> int:
    seen: set[str] = set()
    rows = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    # Resume-safe behavior: keep existing merged rows and append only novel rows.
    if out.exists():
        with out.open("r", encoding="utf-8", errors="replace") as rf:
            for line in rf:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                txt = str(obj.get("text", "")).strip()
                if not txt:
                    continue
                seen.add(_norm(txt))
                rows += 1
        if max_rows > 0 and rows >= max_rows:
            return rows
    with out.open("a", encoding="utf-8") as f:
        for source_name, src in sources:
            for txt in _iter_jsonl_texts(src):
                if len(txt) < min_chars:
                    continue
                key = _norm(txt)
                if key in seen:
                    continue
                seen.add(key)
                f.write(json.dumps({"text": txt, "source": source_name}, ensure_ascii=False) + "\n")
                rows += 1
                if max_rows > 0 and rows >= max_rows:
                    return rows
    return rows


def _parse_steps(s: str) -> list[str]:
    # NOTE: `subsets` builds the "pre" vocab-pruned checkpoints (vocab50000/vocab80000)
    # from the workspace corpora, writing them to --subset-root using --subset-pattern.
    valid = ["init", "fetch", "gemini", "merge", "dataset", "pairs", "subsets", "distill", "benchmark"]
    out = [x.strip() for x in s.split(",") if x.strip()]
    for x in out:
        if x not in valid:
            raise SystemExit(f"Unknown step '{x}'. Valid: {','.join(valid)}")
    return out


def _parse_csv(s: str) -> list[str]:
    return [x.strip() for x in str(s).split(",") if x.strip()]


def _parse_distill_targets(distill_targets: str | None, langs: list[str]) -> list[str]:
    if distill_targets is None:
        return list(langs)
    targets = _parse_csv(distill_targets)
    return targets if targets else list(langs)


def _target_langs(target: str) -> list[str]:
    return [x.strip() for x in str(target).split("-") if x.strip()]


def _target_k(target: str) -> int:
    langs = _target_langs(target)
    if not langs:
        return 50000
    return max(int(K_MAP.get(lang, 50000)) for lang in langs)


def main() -> int:
    pipeline_start = time.perf_counter()
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace-dir", default="gamma/projects/distillation/embedding/workspaces/main")
    ap.add_argument("--steps", default="init,fetch,gemini,merge,dataset,pairs")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--from-scratch", action="store_true", help="Delete workspace before running.")
    ap.add_argument("--langs", default=LANGS_DEFAULT)
    ap.add_argument(
        "--parallel-workers",
        type=int,
        default=4,
        help="Parallel workers for per-language independent steps (fetch/merge/dataset/distill).",
    )
    ap.add_argument(
        "--distill-targets",
        default=None,
        help="Optional comma-separated distill targets. Supports bundles like en-es,fr-pt. "
        "If omitted, defaults to --langs.",
    )

    # Common model settings
    ap.add_argument(
        "--base-model",
        default=os.environ.get("BASE_MODEL", ""),
        help=(
            "Teacher/base model reference (HF id or local path). "
            "Defaults to $BASE_MODEL when set."
        ),
    )
    ap.add_argument("--subset-root", default="gamma/projects/distillation/embedding/output")
    ap.add_argument("--subset-pattern", default="google__embeddinggemma-300m-{lang}-vocab{k}")
    ap.add_argument(
        "--subset-model",
        default=None,
        help="Model reference for vocab subsetting (HF id or local path). Defaults to --base-model.",
    )

    # subsets step (pre models)
    ap.add_argument("--subset-min-count", type=int, default=2)
    ap.add_argument("--subset-max-lines", type=int, default=None)
    ap.add_argument("--subset-write-checkpoint", action="store_true", help="Write pruned checkpoint files (required for distill).")
    ap.add_argument("--no-subset-write-checkpoint", dest="subset_write_checkpoint", action="store_false")
    ap.set_defaults(subset_write_checkpoint=True)
    ap.add_argument("--subset-fill-to-top-k", action="store_true")
    ap.add_argument("--no-subset-fill-to-top-k", dest="subset_fill_to_top_k", action="store_false")
    ap.set_defaults(subset_fill_to_top_k=True)
    ap.add_argument("--subset-fill-strategy", default="spm_score", choices=["spm_score", "id"])
    ap.add_argument("--subset-dtype", default="auto", choices=["auto", "fp16", "bf16", "fp32"])
    ap.add_argument("--subset-also-prune-output", action="store_true")
    ap.add_argument("--subset-allow-download", action="store_true", help="Allow HF downloads if needed (default: offline).")

    # fetch step
    ap.add_argument("--wiki-max-output-mb", type=int, default=8)
    ap.add_argument("--wiki-max-rows", type=int, default=64)
    ap.add_argument("--wiki-max-requests", type=int, default=80)
    ap.add_argument("--wiki-batch-pages", type=int, default=20)
    ap.add_argument("--wiki-min-chars", type=int, default=80)
    ap.add_argument("--wiki-sleep-ms", type=int, default=80)
    ap.add_argument("--wiki-retry-429-base-s", type=float, default=2.0)
    ap.add_argument("--wiki-retry-429-max-s", type=float, default=30.0)
    ap.add_argument("--wiki-max-consecutive-errors", type=int, default=12)
    ap.add_argument("--wiki-api-source", choices=["random", "search", "hybrid"], default="hybrid")
    ap.add_argument("--wiki-topic-buckets", default="news,science,culture,law,health,finance,informal")
    ap.add_argument("--wiki-purity-mode", choices=["off", "basic"], default="basic")
    ap.add_argument("--wiki-purity-threshold", type=float, default=0.55)
    ap.add_argument("--wiki-max-latin-ratio-nonlatin", type=float, default=0.35)
    ap.add_argument("--wiki-dedupe-near", action="store_true")
    ap.add_argument("--no-wiki-dedupe-near", dest="wiki_dedupe_near", action="store_false")
    ap.add_argument("--wiki-drop-boilerplate", action="store_true")
    ap.add_argument("--no-wiki-drop-boilerplate", dest="wiki_drop_boilerplate", action="store_false")
    ap.add_argument("--wiki-priority-langs", default="hi,ar,pt", help="Langs that should fetch more wiki rows by default.")
    ap.add_argument("--wiki-priority-multiplier", type=float, default=2.0, help="Row/MB multiplier for --wiki-priority-langs.")
    ap.set_defaults(wiki_dedupe_near=True, wiki_drop_boilerplate=True)

    # gemini step
    ap.add_argument("--gemini-model", default="gemini-3-flash-preview")
    ap.add_argument("--gemini-rows-per-lang", type=int, default=1000)
    ap.add_argument("--gemini-batch-size", type=int, default=8)
    ap.add_argument("--gemini-min-chars", type=int, default=300)
    ap.add_argument("--gemini-max-chars", type=int, default=1200)
    ap.add_argument("--gemini-temperature", type=float, default=1.0)
    ap.add_argument("--gemini-sleep-ms", type=int, default=250)
    ap.add_argument("--gemini-seed-examples-per-call", type=int, default=6)
    ap.add_argument("--gemini-prompt-style", choices=["balanced", "creative", "exotic"], default="exotic")
    ap.add_argument("--gemini-writing-profile-mode", choices=["off", "random"], default="random")
    ap.add_argument("--gemini-prompt-mix-mode", choices=["off", "random"], default="random")
    ap.add_argument("--gemini-prompt-mix-count", type=int, default=2)
    ap.add_argument("--gemini-prompt-mix-pool", default="")
    ap.add_argument("--gemini-parallel-workers", type=int, default=1)

    # merge step
    ap.add_argument("--merge-max-rows", type=int, default=20000)
    ap.add_argument("--merge-min-chars", type=int, default=120)
    ap.add_argument(
        "--merge-sources",
        default="wiki,gemini",
        help="Comma-separated raw source subdirs under <workspace>/raw to merge. "
        "Example: wiki,gemini,synthetic",
    )

    # dataset step
    ap.add_argument("--max-paragraphs", type=int, default=300000)
    ap.add_argument("--max-docs", type=int, default=5000)
    ap.add_argument("--max-queries", type=int, default=5000)
    ap.add_argument("--keywords-per-query", type=int, default=14)
    ap.add_argument("--distractors-per-query", type=int, default=30)
    ap.add_argument("--seed", type=int, default=101)

    # pairs step
    ap.add_argument("--pairs-per-lang", type=int, default=10000)
    ap.add_argument("--pairs-neg-strategy", choices=["random", "lexical_hard"], default="lexical_hard")
    ap.add_argument("--pairs-hard-neg-pool", type=int, default=128)
    ap.add_argument(
        "--train-frac",
        type=float,
        default=0.5,
        help="Fraction of merged raw rows used for distill training; remainder used for eval/benchmark.",
    )

    # distill step
    ap.add_argument("--distill-out-root", default=None)
    ap.add_argument("--distill-device", default="cpu")
    ap.add_argument("--distill-steps", type=int, default=300)
    ap.add_argument("--distill-batch-size", type=int, default=32)
    ap.add_argument("--distill-max-length", type=int, default=96)
    ap.add_argument("--distill-lr", type=float, default=2e-5)
    ap.add_argument("--distill-weight-decay", type=float, default=0.01)
    ap.add_argument("--distill-temperature", type=float, default=0.05)
    ap.add_argument("--distill-alpha-contrastive", type=float, default=1.0)
    ap.add_argument("--distill-beta-distill", type=float, default=1.0)
    ap.add_argument("--distill-alpha-triplet", type=float, default=0.25)
    ap.add_argument("--distill-triplet-margin", type=float, default=0.05)
    ap.add_argument("--distill-alpha-sim-distill", type=float, default=0.25)
    ap.add_argument("--distill-save-every", type=int, default=100)
    ap.add_argument("--distill-select-best-checkpoint", action="store_true")
    ap.add_argument("--no-distill-select-best-checkpoint", dest="distill_select_best_checkpoint", action="store_false")
    ap.set_defaults(distill_select_best_checkpoint=True)

    # benchmark step
    ap.add_argument("--benchmark-repeats", type=int, default=3)
    ap.add_argument("--benchmark-device", default="cpu")
    ap.add_argument("--benchmark-max-length", type=int, default=96)
    ap.add_argument("--benchmark-batch-size", type=int, default=64)
    ap.add_argument("--benchmark-iters", type=int, default=2)
    ap.add_argument("--benchmark-warmup", type=int, default=1)
    ap.add_argument("--benchmark-pre-root", default=None, help="Pre-distill subset root. Defaults to --subset-root.")
    ap.add_argument("--benchmark-pre-pattern", default=None, help="Pre-distill subset pattern. Defaults to --subset-pattern.")
    ap.add_argument("--benchmark-post-root", default=None, help="Post-distill subset root. Defaults to distill output root.")
    ap.add_argument(
        "--benchmark-post-pattern",
        default="google__embeddinggemma-300m-{lang}-vocab{k}-distilled",
        help="Post-distill subset pattern.",
    )

    args = ap.parse_args()
    if args.subset_model is not None and not str(args.subset_model).strip():
        args.subset_model = None
    langs = _parse_csv(str(args.langs))
    steps = _parse_steps(str(args.steps))
    distill_targets = _parse_distill_targets(args.distill_targets, langs)

    base_model_required = (
        ("distill" in steps)
        or ("benchmark" in steps)
        or (("subsets" in steps) and args.subset_model is None)
    )

    # Resolve HF cache roots (models--org--name/) to snapshots/<hash> so transformers can load.
    if str(args.base_model).strip():
        args.base_model = _resolve_hf_snapshot_dir(str(args.base_model))
        _validate_model_ref(str(args.base_model), arg_name="--base-model")
    elif base_model_required:
        raise SystemExit(
            "--base-model is required for the selected steps "
            "(distill/benchmark, or subsets without --subset-model). "
            "Set --base-model explicitly or export BASE_MODEL."
        )

    if args.subset_model is not None:
        args.subset_model = _resolve_hf_snapshot_dir(str(args.subset_model))
        _validate_model_ref(str(args.subset_model), arg_name="--subset-model")

    ws = Path(args.workspace_dir)
    raw_root = ws / "raw"
    wiki_dir = raw_root / "wiki"
    gemini_dir = raw_root / "gemini"
    merged_dir = raw_root / "merged"
    split_train_dir = raw_root / "train"
    split_eval_dir = raw_root / "eval"
    corpora_root = ws / "corpora"
    corpora_train_dir = corpora_root / "train"
    corpora_eval_dir = corpora_root / "eval"
    datasets_root = ws / "datasets"
    datasets_train_dir = datasets_root / "train"
    datasets_eval_dir = datasets_root / "eval"
    pairs_path = ws / "training" / "distill_pairs.jsonl"
    distill_root = Path(args.distill_out_root) if args.distill_out_root else (ws / "models" / "distilled")
    benchmark_out = ws / "eval" / "benchmark"
    state_dir = ws / "pipeline_state"

    if not (0.0 < float(args.train_frac) < 1.0):
        raise SystemExit(f"--train-frac must be in (0,1), got {args.train_frac}")

    if args.from_scratch and ws.exists():
        shutil.rmtree(ws)

    if "init" in steps:
        for d in [
            wiki_dir,
            gemini_dir,
            merged_dir,
            split_train_dir,
            split_eval_dir,
            corpora_train_dir,
            corpora_eval_dir,
            datasets_train_dir,
            datasets_eval_dir,
            pairs_path.parent,
            distill_root,
            benchmark_out,
        ]:
            d.mkdir(parents=True, exist_ok=True)
        print(f"initialized workspace: {ws}")

    py = sys.executable
    fetch_script = Path("gamma/projects/distillation/shared/data_tools/fetch_wikipedia_jsonl.py")
    gemini_script = Path("gamma/projects/distillation/shared/data_tools/generate_gemini_seed_jsonl.py")
    corpus_script = Path("gamma/projects/distillation/shared/data_tools/make_wiki_corpus.py")
    pairs_script = Path("gamma/projects/distillation/embedding/training/make_distill_pairs.py")
    vocab_subset_script = Path("gamma/tools/vocab_subset.py")
    distill_script = Path("gamma/projects/distillation/embedding/training/distill_subset.py")
    benchmark_script = Path("gamma/projects/distillation/embedding/eval/run_benchmark.py")

    if "fetch" in steps:
        wiki_priority_langs = set(_parse_csv(str(args.wiki_priority_langs)))

        def _fetch_lang(lang: str) -> None:
            priority_mult = float(args.wiki_priority_multiplier) if lang in wiki_priority_langs else 1.0
            max_rows_lang = max(1, int(round(int(args.wiki_max_rows) * priority_mult)))
            max_mb_lang = max(0, int(round(int(args.wiki_max_output_mb) * priority_mult)))
            out = wiki_dir / f"{lang}.jsonl"
            if args.resume and _count_jsonl(out) >= int(max_rows_lang):
                print(f"[fetch] skip {lang}: existing rows >= {max_rows_lang}")
                return
            _run([
                py, str(fetch_script),
                "--mode", "api",
                "--langs", lang,
                "--out-dir", str(wiki_dir),
                "--max-output-mb", str(int(max_mb_lang)),
                "--max-rows", str(int(max_rows_lang)),
                "--max-requests", str(int(args.wiki_max_requests)),
                "--batch-pages", str(int(args.wiki_batch_pages)),
                "--min-chars", str(int(args.wiki_min_chars)),
                "--sleep-ms", str(int(args.wiki_sleep_ms)),
                "--retry-429-base-s", str(float(args.wiki_retry_429_base_s)),
                "--retry-429-max-s", str(float(args.wiki_retry_429_max_s)),
                "--max-consecutive-errors", str(int(args.wiki_max_consecutive_errors)),
                "--api-source", str(args.wiki_api_source),
                "--topic-buckets", str(args.wiki_topic_buckets),
                "--purity-mode", str(args.wiki_purity_mode),
                "--purity-threshold", str(float(args.wiki_purity_threshold)),
                "--max-latin-ratio-nonlatin", str(float(args.wiki_max_latin_ratio_nonlatin)),
                "--wiki-dedupe-near" if bool(args.wiki_dedupe_near) else "--no-wiki-dedupe-near",
                "--drop-boilerplate" if bool(args.wiki_drop_boilerplate) else "--no-drop-boilerplate",
            ])
        _run_parallel(langs, _fetch_lang, max_workers=int(args.parallel_workers), label="fetch")

    if "gemini" in steps:
        langs_to_run: list[str] = []
        for lang in langs:
            out = gemini_dir / f"{lang}.jsonl"
            if args.resume and _count_jsonl(out) >= int(args.gemini_rows_per_lang):
                print(f"[gemini] skip {lang}: existing rows >= {args.gemini_rows_per_lang}")
                continue
            langs_to_run.append(lang)
        if not langs_to_run:
            print("[gemini] all requested languages already at target; nothing to run")
        else:
            _run([
                py, str(gemini_script),
                "--langs", ",".join(langs_to_run),
                "--out-dir", str(gemini_dir),
                "--model", str(args.gemini_model),
                "--rows-per-lang", str(int(args.gemini_rows_per_lang)),
                "--batch-size", str(int(args.gemini_batch_size)),
                "--min-chars", str(int(args.gemini_min_chars)),
                "--max-chars", str(int(args.gemini_max_chars)),
                "--temperature", str(float(args.gemini_temperature)),
                "--sleep-ms", str(int(args.gemini_sleep_ms)),
                "--seed-jsonl-dir", str(wiki_dir),
                "--seed-examples-per-call", str(int(args.gemini_seed_examples_per_call)),
                "--prompt-style", str(args.gemini_prompt_style),
                "--writing-profile-mode", str(args.gemini_writing_profile_mode),
                "--prompt-mix-mode", str(args.gemini_prompt_mix_mode),
                "--prompt-mix-count", str(int(args.gemini_prompt_mix_count)),
                "--parallel-workers", str(int(args.gemini_parallel_workers)),
            ] + (["--prompt-mix-pool", str(args.gemini_prompt_mix_pool)] if str(args.gemini_prompt_mix_pool).strip() else []))

    if "merge" in steps:
        merge_sources = _parse_csv(str(args.merge_sources))
        if not merge_sources:
            raise SystemExit("merge step requires at least one source in --merge-sources")
        def _merge_one(lang: str) -> None:
            out = merged_dir / f"{lang}.jsonl"
            if args.resume and _count_jsonl(out) >= int(args.merge_max_rows):
                print(f"[merge] skip {lang}: existing rows >= {args.merge_max_rows}")
                return
            srcs = [(name, raw_root / name / f"{lang}.jsonl") for name in merge_sources]
            rows = _merge_lang(
                srcs,
                out,
                max_rows=int(args.merge_max_rows),
                min_chars=int(args.merge_min_chars),
            )
            print(f"[merge] {lang}: sources={','.join(merge_sources)} wrote {rows} rows -> {out}")
        _run_parallel(langs, _merge_one, max_workers=int(args.parallel_workers), label="merge")

    if "dataset" in steps:
        def _dataset_one(lang: str) -> None:
            src = merged_dir / f"{lang}.jsonl"
            train_jsonl = split_train_dir / f"{lang}.jsonl"
            eval_jsonl = split_eval_dir / f"{lang}.jsonl"
            train_ds = datasets_train_dir / lang / "dataset.json"
            eval_ds = datasets_eval_dir / lang / "dataset.json"
            train_corpus = corpora_train_dir / f"{lang}.txt"
            eval_corpus = corpora_eval_dir / f"{lang}.txt"

            have_train = _count_dataset_docs(train_ds) > 0
            have_eval = _count_dataset_docs(eval_ds) > 0
            if args.resume and have_train and have_eval:
                print(f"[dataset] skip {lang}: train/eval datasets already populated")
                return

            n_train, n_eval = _split_jsonl_train_eval(
                src,
                train_jsonl,
                eval_jsonl,
                train_frac=float(args.train_frac),
                seed=_stable_lang_seed(int(args.seed), lang),
            )
            print(
                f"[split] {lang}: train={n_train} eval={n_eval} "
                f"(train_frac={float(args.train_frac):.2f}) -> {train_jsonl}, {eval_jsonl}"
            )

            _run([
                py, str(corpus_script),
                "--lang", lang,
                "--jsonl", str(train_jsonl),
                "--out-corpus", str(train_corpus),
                "--out-dataset", str(train_ds),
                "--max-paragraphs", str(int(args.max_paragraphs)),
                "--max-docs", str(int(args.max_docs)),
                "--max-queries", str(int(args.max_queries)),
                "--mode", "hard",
                "--keywords-per-query", str(int(args.keywords_per_query)),
                "--distractors-per-query", str(int(args.distractors_per_query)),
                "--seed", str(int(args.seed)),
            ])

            _run([
                py, str(corpus_script),
                "--lang", lang,
                "--jsonl", str(eval_jsonl),
                "--out-corpus", str(eval_corpus),
                "--out-dataset", str(eval_ds),
                "--max-paragraphs", str(int(args.max_paragraphs)),
                "--max-docs", str(int(args.max_docs)),
                "--max-queries", str(int(args.max_queries)),
                "--mode", "hard",
                "--keywords-per-query", str(int(args.keywords_per_query)),
                "--distractors-per-query", str(int(args.distractors_per_query)),
                "--seed", str(int(args.seed) + 1),
            ])
        _run_parallel(langs, _dataset_one, max_workers=int(args.parallel_workers), label="dataset")

    if "pairs" in steps:
        pairs_cfg_hash = _config_hash(
            {
                "datasets_train_dir": str(datasets_train_dir),
                "langs": langs,
                "pairs_per_lang": int(args.pairs_per_lang),
                "neg_strategy": str(args.pairs_neg_strategy),
                "hard_neg_pool": int(args.pairs_hard_neg_pool),
            }
        )
        pairs_done = state_dir / "pairs.done.json"
        if args.resume and _done_manifest_matches(pairs_done, config_hash=pairs_cfg_hash, outputs=[pairs_path]):
            print(f"[pairs] skip: done manifest verified at {pairs_done}")
        else:
            _run([
                py, str(pairs_script),
                "--datasets-dir", str(datasets_train_dir),
                "--langs", ",".join(langs),
                "--pairs-per-lang", str(int(args.pairs_per_lang)),
                "--neg-strategy", str(args.pairs_neg_strategy),
                "--hard-neg-pool", str(int(args.pairs_hard_neg_pool)),
                "--out", str(pairs_path),
            ])
            _write_done_manifest(pairs_done, step="pairs", config_hash=pairs_cfg_hash, outputs=[pairs_path])

    if "subsets" in steps:
        subset_model_ref = str(args.subset_model) if args.subset_model else str(args.base_model)
        subset_root = Path(args.subset_root)
        subset_root.mkdir(parents=True, exist_ok=True)
        if not vocab_subset_script.exists():
            raise SystemExit(f"Missing tool: {vocab_subset_script}")

        def _subset_one(lang: str) -> None:
            k = int(K_MAP.get(lang, 50000))
            out_dir = subset_root / str(args.subset_pattern).format(lang=lang, k=k)
            # Heuristic for "done": checkpoint + remap exist.
            if args.resume and (out_dir / "model.safetensors").exists() and (out_dir / "id_remap.json").exists():
                print(f"[subsets] skip {lang}: existing {out_dir}")
                return

            corpus = corpora_train_dir / f"{lang}.txt"
            if not corpus.exists():
                raise RuntimeError(f"[subsets] missing corpus for {lang}: {corpus} (run dataset step first)")

            print(
                f"[subsets] start lang={lang} k={k} "
                f"write_checkpoint={bool(args.subset_write_checkpoint)} out={out_dir}"
            )
            t0 = time.perf_counter()
            cmd = [
                py,
                str(vocab_subset_script),
                "--model",
                subset_model_ref,
                "--out",
                str(out_dir),
                "--top-k",
                str(int(k)),
                "--min-count",
                str(int(args.subset_min_count)),
                "--dtype",
                str(args.subset_dtype),
            ]
            if bool(args.subset_fill_to_top_k):
                cmd += ["--fill-to-top-k", "--fill-strategy", str(args.subset_fill_strategy)]
            if bool(args.subset_allow_download):
                cmd += ["--allow-download"]
            if args.subset_max_lines is not None:
                cmd += ["--max-lines", str(int(args.subset_max_lines))]
            cmd += ["--text", str(corpus)]
            if bool(args.subset_write_checkpoint):
                cmd += ["--write-checkpoint"]
            if bool(args.subset_also_prune_output):
                cmd += ["--also-prune-output"]
            _run(cmd)
            print(f"[subsets] done lang={lang} elapsed={time.perf_counter() - t0:.2f}s out={out_dir}")

        _run_parallel(langs, _subset_one, max_workers=int(args.parallel_workers), label="subsets")

    if "distill" in steps:
        def _distill_target(target: str) -> None:
            target_langs = _target_langs(target)
            if not target_langs:
                print(f"[distill] skip empty target: {target!r}")
                return

            k = _target_k(target)
            subset_dir = Path(args.subset_root) / str(args.subset_pattern).format(lang=target, k=k)
            if not subset_dir.exists():
                print(f"[distill] skip {target}: missing subset dir {subset_dir}")
                return

            out_dir = Path(distill_root) / f"{subset_dir.name}-distilled"
            distill_cfg_hash = _config_hash(
                {
                    "target": target,
                    "target_langs": target_langs,
                    "base_model": str(args.base_model),
                    "subset_dir": str(subset_dir),
                    "pairs_path": str(pairs_path),
                    "device": str(args.distill_device),
                    "max_length": int(args.distill_max_length),
                    "batch_size": int(args.distill_batch_size),
                    "steps": int(args.distill_steps),
                    "lr": float(args.distill_lr),
                    "weight_decay": float(args.distill_weight_decay),
                    "temperature": float(args.distill_temperature),
                    "alpha_contrastive": float(args.distill_alpha_contrastive),
                    "beta_distill": float(args.distill_beta_distill),
                    "alpha_triplet": float(args.distill_alpha_triplet),
                    "triplet_margin": float(args.distill_triplet_margin),
                    "alpha_sim_distill": float(args.distill_alpha_sim_distill),
                    "seed": int(args.seed),
                }
            )
            safe_target = target.replace("/", "_")
            distill_done = state_dir / f"distill.{safe_target}.done.json"
            distill_outputs = [out_dir / "train_summary.json", out_dir / "id_remap.json"]
            if args.resume and _done_manifest_matches(distill_done, config_hash=distill_cfg_hash, outputs=distill_outputs):
                print(f"[distill] skip {target}: done manifest verified at {distill_done}")
                return

            print(
                f"[distill] start target={target} langs={','.join(target_langs)} "
                f"device={args.distill_device} steps={int(args.distill_steps)} out={out_dir}"
            )
            t0 = time.perf_counter()
            _run([
                py, str(distill_script),
                "--teacher-model", str(args.base_model),
                "--student-subset-dir", str(subset_dir),
                "--pairs", str(pairs_path),
                "--langs", ",".join(target_langs),
                "--out", str(out_dir),
                "--device", str(args.distill_device),
                "--max-length", str(int(args.distill_max_length)),
                "--batch-size", str(int(args.distill_batch_size)),
                "--steps", str(int(args.distill_steps)),
                "--lr", str(float(args.distill_lr)),
                "--weight-decay", str(float(args.distill_weight_decay)),
                "--temperature", str(float(args.distill_temperature)),
                "--alpha-contrastive", str(float(args.distill_alpha_contrastive)),
                "--beta-distill", str(float(args.distill_beta_distill)),
                "--alpha-triplet", str(float(args.distill_alpha_triplet)),
                "--triplet-margin", str(float(args.distill_triplet_margin)),
                "--alpha-sim-distill", str(float(args.distill_alpha_sim_distill)),
                "--save-every", str(int(args.distill_save_every)),
                "--seed", str(int(args.seed)),
            ] + (["--select-best-checkpoint"] if bool(args.distill_select_best_checkpoint) else ["--no-select-best-checkpoint"]) + (
                ["--resume", "--resume-from", str(out_dir)] if bool(args.resume) else []
            ))
            _write_done_manifest(distill_done, step=f"distill:{target}", config_hash=distill_cfg_hash, outputs=distill_outputs)
            print(f"[distill] done target={target} elapsed={time.perf_counter() - t0:.2f}s out={out_dir}")
        _run_parallel(distill_targets, _distill_target, max_workers=int(args.parallel_workers), label="distill")

    if "benchmark" in steps:
        benchmark_dataset_dir = _resolve_benchmark_dataset_dir(datasets_eval_dir, datasets_root)
        pre_root = Path(args.benchmark_pre_root) if args.benchmark_pre_root else Path(args.subset_root)
        pre_pattern = str(args.benchmark_pre_pattern) if args.benchmark_pre_pattern else str(args.subset_pattern)
        post_root = Path(args.benchmark_post_root) if args.benchmark_post_root else Path(distill_root)
        post_pattern = str(args.benchmark_post_pattern)

        track_defs = [
            ("base_vs_pre", "base_model", str(args.base_model), pre_root, pre_pattern, None, None),
            ("base_vs_post", "base_model", str(args.base_model), post_root, post_pattern, None, None),
            ("pre_vs_post", "base_root", str(pre_root), post_root, post_pattern, pre_pattern, str(args.base_model)),
        ]

        for track_name, base_mode, base_value, sub_root, sub_pattern, base_pattern, base_tokenizer in track_defs:
            track_out = benchmark_out / track_name
            summary_file = track_out / "benchmark_summary.json"
            if args.resume and summary_file.exists():
                print(f"[benchmark] skip {track_name}: existing {summary_file}")
                continue

            if base_mode == "base_model":
                active_langs_base = list(langs)
            else:
                if not base_pattern:
                    raise RuntimeError(f"[benchmark] missing base_pattern for {track_name}")
                active_langs_base = _existing_langs_for_pattern(Path(base_value), base_pattern, langs)
            active_langs_sub = _existing_langs_for_pattern(sub_root, sub_pattern, langs)
            active_langs = [lang for lang in active_langs_base if lang in active_langs_sub]

            if not active_langs:
                print(
                    f"[benchmark] skip {track_name}: no active languages found for "
                    f"base={base_value} subset_root={sub_root}"
                )
                continue

            print(
                f"[benchmark] start track={track_name} langs={','.join(active_langs)} "
                f"device={args.benchmark_device} repeats={int(args.benchmark_repeats)}"
            )
            t0 = time.perf_counter()
            cmd = [
                py, str(benchmark_script),
                "--dataset", str(benchmark_dataset_dir),
                "--subset-root", str(sub_root),
                "--subset-pattern", str(sub_pattern),
                "--langs", ",".join(active_langs),
                "--repeats", str(int(args.benchmark_repeats)),
                "--device", str(args.benchmark_device),
                "--max-length", str(int(args.benchmark_max_length)),
                "--batch-size", str(int(args.benchmark_batch_size)),
                "--bench-iters", str(int(args.benchmark_iters)),
                "--bench-warmup", str(int(args.benchmark_warmup)),
                "--out", str(track_out),
            ]
            if base_mode == "base_model":
                cmd += ["--base-model", str(base_value)]
            else:
                cmd += ["--base-root", str(base_value), "--base-pattern", str(base_pattern)]
            if base_tokenizer:
                cmd += ["--base-tokenizer", str(base_tokenizer)]
            _run(cmd)
            print(
                f"[benchmark] done track={track_name} elapsed={time.perf_counter() - t0:.2f}s "
                f"summary={summary_file}"
            )

        _summarize_benchmark_tracks(
            benchmark_out,
            tracks=["base_vs_pre", "base_vs_post", "pre_vs_post"],
        )

    print("pipeline complete")
    print(f"workspace={ws}")
    print(f"raw_root={raw_root}")
    print(f"datasets_train={datasets_train_dir}")
    print(f"datasets_eval={datasets_eval_dir}")
    print(f"pairs={pairs_path}")
    print(f"distilled_models={distill_root}")
    print(f"elapsed_total_s={time.perf_counter() - pipeline_start:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
