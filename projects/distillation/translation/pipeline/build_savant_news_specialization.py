#!/usr/bin/env python3
"""Build a decontaminated EN<->ES News Commentary specialization set."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUT = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "savant_news"
    / "news_commentary_en_es.local.jsonl"
)
DEFAULT_MANIFEST = DEFAULT_OUT.with_suffix(".manifest.json")


def _norm_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return " ".join(re.findall(r"\w+", text, flags=re.UNICODE))


def _word_ngrams(text: str, size: int = 4) -> set[tuple[str, ...]]:
    words = _norm_text(text).split()
    if len(words) < size:
        return {tuple(words)} if words else set()
    return {tuple(words[idx : idx + size]) for idx in range(len(words) - size + 1)}


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())


def _load_eval_texts(paths: Iterable[Path]) -> tuple[set[str], list[set[tuple[str, ...]]]]:
    exact: set[str] = set()
    ngram_sets: list[set[tuple[str, ...]]] = []
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                for key in ("source", "target_pos"):
                    text = str(row.get(key, "")).strip()
                    normalized = _norm_text(text)
                    if not normalized:
                        continue
                    exact.add(normalized)
                    grams = _word_ngrams(text)
                    if grams:
                        ngram_sets.append(grams)
    return exact, ngram_sets


def _build_ngram_index(
    eval_ngrams: list[set[tuple[str, ...]]],
) -> dict[tuple[str, ...], set[int]]:
    index: dict[tuple[str, ...], set[int]] = defaultdict(set)
    for text_idx, grams in enumerate(eval_ngrams):
        for gram in grams:
            index[gram].add(text_idx)
    return dict(index)


def _near_eval_duplicate(
    text: str,
    *,
    eval_ngrams: list[set[tuple[str, ...]]],
    ngram_index: dict[tuple[str, ...], set[int]],
    threshold: float,
) -> bool:
    grams = _word_ngrams(text)
    if not grams:
        return False
    candidate_ids: set[int] = set()
    for gram in grams:
        candidate_ids.update(ngram_index.get(gram, ()))
    for text_idx in candidate_ids:
        other = eval_ngrams[text_idx]
        union = len(grams | other)
        if union and len(grams & other) / union >= threshold:
            return True
    return False


def _quality_pair(en: str, es: str, *, min_words: int, max_words: int, max_ratio: float) -> bool:
    en_words = _norm_text(en).split()
    es_words = _norm_text(es).split()
    if not (min_words <= len(en_words) <= max_words):
        return False
    if not (min_words <= len(es_words) <= max_words):
        return False
    if _norm_text(en) == _norm_text(es):
        return False
    ratio = max(len(en_words), len(es_words)) / max(1, min(len(en_words), len(es_words)))
    return ratio <= max_ratio


def _reservoir_add(
    reservoir: list[tuple[str, str]],
    pair: tuple[str, str],
    *,
    eligible_count: int,
    limit: int,
    rng: random.Random,
) -> None:
    if len(reservoir) < limit:
        reservoir.append(pair)
        return
    replacement = rng.randrange(eligible_count)
    if replacement < limit:
        reservoir[replacement] = pair


def _row_id(src_lang: str, tgt_lang: str, source: str, target: str) -> str:
    payload = "\0".join((src_lang, tgt_lang, source, target)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _build_rows(pairs: list[tuple[str, str]], *, seed: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, (en, es) in enumerate(pairs):
        next_en, next_es = pairs[(idx + 1) % len(pairs)]
        rows.extend(
            (
                {
                    "src_lang": "en",
                    "tgt_lang": "es",
                    "pair": "en-es",
                    "source": en,
                    "target_pos": es,
                    "target_neg": next_es,
                    "lang": "es",
                    "query": en,
                    "pos": es,
                    "neg": next_es,
                    "row_id": _row_id("en", "es", en, es),
                },
                {
                    "src_lang": "es",
                    "tgt_lang": "en",
                    "pair": "es-en",
                    "source": es,
                    "target_pos": en,
                    "target_neg": next_en,
                    "lang": "en",
                    "query": es,
                    "pos": en,
                    "neg": next_en,
                    "row_id": _row_id("es", "en", es, en),
                },
            )
        )
    random.Random(seed).shuffle(rows)
    return rows


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="Helsinki-NLP/news_commentary")
    parser.add_argument("--config", default="en-es")
    parser.add_argument(
        "--revision",
        default="bbaf548083e788e0e6d2ca68efc325283fe2aff5",
    )
    parser.add_argument("--parallel-pairs", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-words", type=int, default=6)
    parser.add_argument("--max-words", type=int, default=72)
    parser.add_argument("--max-length-ratio", type=float, default=2.0)
    parser.add_argument("--near-duplicate-threshold", type=float, default=0.8)
    parser.add_argument("--eval", action="append", required=True)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--manifest-out", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    out_path = Path(args.out).expanduser().resolve()
    manifest_path = Path(args.manifest_out).expanduser().resolve()
    if not args.force and (out_path.exists() or manifest_path.exists()):
        raise RuntimeError("Output already exists; pass --force to replace it.")

    eval_paths = [Path(value).expanduser().resolve() for value in args.eval]
    for path in eval_paths:
        if not path.is_file():
            raise RuntimeError(f"Evaluation file does not exist: {path}")
    eval_exact, eval_ngrams = _load_eval_texts(eval_paths)
    ngram_index = _build_ngram_index(eval_ngrams)

    from datasets import load_dataset
    from huggingface_hub import HfApi

    resolved_revision = HfApi().dataset_info(
        str(args.dataset),
        revision=str(args.revision),
    ).sha

    stream = load_dataset(
        str(args.dataset),
        str(args.config),
        split="train",
        revision=str(args.revision),
        streaming=True,
    )
    rng = random.Random(int(args.seed))
    reservoir: list[tuple[str, str]] = []
    seen_pairs: set[tuple[str, str]] = set()
    counts = defaultdict(int)

    for item in stream:
        counts["scanned"] += 1
        translation = item.get("translation") or {}
        en = " ".join(str(translation.get("en", "")).split())
        es = " ".join(str(translation.get("es", "")).split())
        if not _quality_pair(
            en,
            es,
            min_words=int(args.min_words),
            max_words=int(args.max_words),
            max_ratio=float(args.max_length_ratio),
        ):
            counts["rejected_quality"] += 1
            continue
        normalized_pair = (_norm_text(en), _norm_text(es))
        if normalized_pair in seen_pairs:
            counts["rejected_duplicate"] += 1
            continue
        seen_pairs.add(normalized_pair)
        if normalized_pair[0] in eval_exact or normalized_pair[1] in eval_exact:
            counts["rejected_eval_exact"] += 1
            continue
        if _near_eval_duplicate(
            en,
            eval_ngrams=eval_ngrams,
            ngram_index=ngram_index,
            threshold=float(args.near_duplicate_threshold),
        ) or _near_eval_duplicate(
            es,
            eval_ngrams=eval_ngrams,
            ngram_index=ngram_index,
            threshold=float(args.near_duplicate_threshold),
        ):
            counts["rejected_eval_near"] += 1
            continue

        counts["eligible"] += 1
        _reservoir_add(
            reservoir,
            (en, es),
            eligible_count=int(counts["eligible"]),
            limit=int(args.parallel_pairs),
            rng=rng,
        )

    if len(reservoir) != int(args.parallel_pairs):
        raise RuntimeError(
            f"Requested {args.parallel_pairs} parallel pairs but selected {len(reservoir)}."
        )

    rows = _build_rows(reservoir, seed=int(args.seed))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "dataset": str(args.dataset),
        "config": str(args.config),
        "revision": str(args.revision),
        "resolved_revision": str(resolved_revision),
        "license": "unknown",
        "usage_scope": "local_research_only",
        "selection": {
            "seed": int(args.seed),
            "parallel_pairs": int(args.parallel_pairs),
            "rows": len(rows),
            "counts_by_pair": {"en-es": len(reservoir), "es-en": len(reservoir)},
            "min_words": int(args.min_words),
            "max_words": int(args.max_words),
            "max_length_ratio": float(args.max_length_ratio),
            "near_duplicate_threshold": float(args.near_duplicate_threshold),
            "counts": {
                key: int(counts[key])
                for key in (
                    "scanned",
                    "eligible",
                    "rejected_quality",
                    "rejected_duplicate",
                    "rejected_eval_exact",
                    "rejected_eval_near",
                )
            },
        },
        "evaluation_exclusions": [
            {"path": _manifest_path(path), "sha256": _sha256_path(path)} for path in eval_paths
        ],
        "output": {"path": _manifest_path(out_path), "sha256": _sha256_path(out_path)},
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"[savant-news] scanned={counts['scanned']} eligible={counts['eligible']} "
        f"parallel_pairs={len(reservoir)} rows={len(rows)}"
    )
    print(f"[savant-news] out={out_path}")
    print(f"[savant-news] manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
