#!/usr/bin/env python3
"""
Unified, resumable end-to-end pipeline for EmbeddingGemma subset data + training.

Workspace layout (single raw root):
  <workspace>/
    raw/
      wiki/<lang>.jsonl
      gemini/<lang>.jsonl
      merged/<lang>.jsonl
    corpora/<lang>.txt
    datasets/<lang>/dataset.json
    training/distill_pairs.jsonl
    models/distilled/<...>
    eval/benchmark/...
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
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
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


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
    valid = ["init", "fetch", "gemini", "merge", "dataset", "pairs", "distill", "benchmark"]
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace-dir", default="gamma/projects/embeddinggemma_subsets/workspaces/main")
    ap.add_argument("--steps", default="init,fetch,gemini,merge,dataset,pairs")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--from-scratch", action="store_true", help="Delete workspace before running.")
    ap.add_argument("--langs", default=LANGS_DEFAULT)
    ap.add_argument(
        "--distill-targets",
        default=None,
        help="Optional comma-separated distill targets. Supports bundles like en-es,fr-pt. "
        "If omitted, defaults to --langs.",
    )

    # Common model settings
    ap.add_argument("--base-model", default="/Users/xyz/.cache/huggingface/hub/models--google--embeddinggemma-300m/snapshots/57c266a740f537b4dc058e1b0cda161fd15afa75")
    ap.add_argument("--subset-root", default="gamma/projects/embeddinggemma_subsets/output")
    ap.add_argument("--subset-pattern", default="google__embeddinggemma-300m-{lang}-vocab{k}")

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

    # benchmark step
    ap.add_argument("--benchmark-repeats", type=int, default=3)
    ap.add_argument("--benchmark-device", default="cpu")
    ap.add_argument("--benchmark-max-length", type=int, default=96)
    ap.add_argument("--benchmark-batch-size", type=int, default=64)
    ap.add_argument("--benchmark-iters", type=int, default=2)
    ap.add_argument("--benchmark-warmup", type=int, default=1)

    args = ap.parse_args()
    langs = _parse_csv(str(args.langs))
    steps = _parse_steps(str(args.steps))
    distill_targets = _parse_distill_targets(args.distill_targets, langs)

    ws = Path(args.workspace_dir)
    raw_root = ws / "raw"
    wiki_dir = raw_root / "wiki"
    gemini_dir = raw_root / "gemini"
    merged_dir = raw_root / "merged"
    corpora_dir = ws / "corpora"
    datasets_dir = ws / "datasets"
    pairs_path = ws / "training" / "distill_pairs.jsonl"
    distill_root = Path(args.distill_out_root) if args.distill_out_root else (ws / "models" / "distilled")
    benchmark_out = ws / "eval" / "benchmark"

    if args.from_scratch and ws.exists():
        shutil.rmtree(ws)

    if "init" in steps:
        for d in [wiki_dir, gemini_dir, merged_dir, corpora_dir, datasets_dir, pairs_path.parent, distill_root, benchmark_out]:
            d.mkdir(parents=True, exist_ok=True)
        print(f"initialized workspace: {ws}")

    py = sys.executable
    fetch_script = Path("gamma/projects/embeddinggemma_subsets/data_tools/fetch_wikipedia_jsonl.py")
    gemini_script = Path("gamma/projects/embeddinggemma_subsets/data_tools/generate_gemini_seed_jsonl.py")
    corpus_script = Path("gamma/projects/embeddinggemma_subsets/data_tools/make_wiki_corpus.py")
    pairs_script = Path("gamma/projects/embeddinggemma_subsets/training/make_distill_pairs.py")
    distill_script = Path("gamma/projects/embeddinggemma_subsets/training/distill_subset.py")
    benchmark_script = Path("gamma/projects/embeddinggemma_subsets/eval/run_benchmark.py")

    if "fetch" in steps:
        for lang in langs:
            out = wiki_dir / f"{lang}.jsonl"
            if args.resume and _count_jsonl(out) >= int(args.wiki_max_rows):
                print(f"[fetch] skip {lang}: existing rows >= {args.wiki_max_rows}")
                continue
            _run([
                py, str(fetch_script),
                "--mode", "api",
                "--langs", lang,
                "--out-dir", str(wiki_dir),
                "--max-output-mb", str(int(args.wiki_max_output_mb)),
                "--max-rows", str(int(args.wiki_max_rows)),
                "--max-requests", str(int(args.wiki_max_requests)),
                "--batch-pages", str(int(args.wiki_batch_pages)),
                "--min-chars", str(int(args.wiki_min_chars)),
                "--sleep-ms", str(int(args.wiki_sleep_ms)),
                "--retry-429-base-s", str(float(args.wiki_retry_429_base_s)),
                "--retry-429-max-s", str(float(args.wiki_retry_429_max_s)),
                "--max-consecutive-errors", str(int(args.wiki_max_consecutive_errors)),
            ])

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
                "--parallel-workers", str(int(args.gemini_parallel_workers)),
            ])

    if "merge" in steps:
        merge_sources = _parse_csv(str(args.merge_sources))
        if not merge_sources:
            raise SystemExit("merge step requires at least one source in --merge-sources")
        for lang in langs:
            out = merged_dir / f"{lang}.jsonl"
            if args.resume and _count_jsonl(out) >= int(args.merge_max_rows):
                print(f"[merge] skip {lang}: existing rows >= {args.merge_max_rows}")
                continue
            srcs = [(name, raw_root / name / f"{lang}.jsonl") for name in merge_sources]
            rows = _merge_lang(
                srcs,
                out,
                max_rows=int(args.merge_max_rows),
                min_chars=int(args.merge_min_chars),
            )
            print(f"[merge] {lang}: sources={','.join(merge_sources)} wrote {rows} rows -> {out}")

    if "dataset" in steps:
        for lang in langs:
            src = merged_dir / f"{lang}.jsonl"
            out_corpus = corpora_dir / f"{lang}.txt"
            out_ds = datasets_dir / lang / "dataset.json"
            if args.resume and _count_dataset_docs(out_ds) > 0:
                print(f"[dataset] skip {lang}: dataset already populated")
                continue
            _run([
                py, str(corpus_script),
                "--lang", lang,
                "--jsonl", str(src),
                "--out-corpus", str(out_corpus),
                "--out-dataset", str(out_ds),
                "--max-paragraphs", str(int(args.max_paragraphs)),
                "--max-docs", str(int(args.max_docs)),
                "--max-queries", str(int(args.max_queries)),
                "--mode", "hard",
                "--keywords-per-query", str(int(args.keywords_per_query)),
                "--distractors-per-query", str(int(args.distractors_per_query)),
                "--seed", str(int(args.seed)),
            ])

    if "pairs" in steps:
        if args.resume and _count_jsonl(pairs_path) > 0:
            print(f"[pairs] skip: existing non-empty {pairs_path}")
        else:
            _run([
                py, str(pairs_script),
                "--datasets-dir", str(datasets_dir),
                "--langs", ",".join(langs),
                "--pairs-per-lang", str(int(args.pairs_per_lang)),
                "--out", str(pairs_path),
            ])

    if "distill" in steps:
        for target in distill_targets:
            target_langs = _target_langs(target)
            if not target_langs:
                print(f"[distill] skip empty target: {target!r}")
                continue

            k = _target_k(target)
            subset_dir = Path(args.subset_root) / str(args.subset_pattern).format(lang=target, k=k)
            if not subset_dir.exists():
                print(f"[distill] skip {target}: missing subset dir {subset_dir}")
                continue

            out_dir = Path(distill_root) / f"{subset_dir.name}-distilled"
            if args.resume and (out_dir / "train_summary.json").exists():
                print(f"[distill] skip {target}: resume and output exists {out_dir}")
                continue

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
                "--seed", str(int(args.seed)),
            ])

    if "benchmark" in steps:
        if args.resume and (benchmark_out / "benchmark_summary.json").exists():
            print(f"[benchmark] skip: existing {benchmark_out / 'benchmark_summary.json'}")
        else:
            _run([
                py, str(benchmark_script),
                "--base-model", str(args.base_model),
                "--dataset", str(datasets_dir),
                "--subset-root", str(distill_root),
                "--subset-pattern", "google__embeddinggemma-300m-{lang}-vocab{k}-distilled",
                "--langs", ",".join(langs),
                "--repeats", str(int(args.benchmark_repeats)),
                "--device", str(args.benchmark_device),
                "--max-length", str(int(args.benchmark_max_length)),
                "--batch-size", str(int(args.benchmark_batch_size)),
                "--bench-iters", str(int(args.benchmark_iters)),
                "--bench-warmup", str(int(args.benchmark_warmup)),
                "--out", str(benchmark_out),
            ])

    print("pipeline complete")
    print(f"workspace={ws}")
    print(f"raw_root={raw_root}")
    print(f"pairs={pairs_path}")
    print(f"distilled_models={distill_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
