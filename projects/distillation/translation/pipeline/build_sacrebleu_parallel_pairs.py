#!/usr/bin/env python3
"""Build bidirectional translation rows from a SacreBLEU dataset."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import random
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

import sacrebleu


PROJECT_ROOT = Path(__file__).resolve().parents[4]


def _normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return " ".join(re.findall(r"\w+", text, flags=re.UNICODE))


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise RuntimeError(f"{path}:{line_number}: expected a JSON object")
            rows.append(row)
    return rows


def _evaluation_keys(
    paths: Iterable[Path],
) -> tuple[set[tuple[str, str]], set[tuple[str, str, str, str]]]:
    sources: set[tuple[str, str]] = set()
    pairs: set[tuple[str, str, str, str]] = set()
    for path in paths:
        for row in _load_jsonl(path):
            src_lang = str(row.get("src_lang") or row.get("source_lang") or "").strip()
            tgt_lang = str(row.get("tgt_lang") or row.get("target_lang") or "").strip()
            source = str(row.get("source") or row.get("query") or "").strip()
            target = str(row.get("target_pos") or row.get("pos") or "").strip()
            if src_lang and source:
                sources.add((src_lang, _normalize(source)))
            if src_lang and tgt_lang and source and target:
                pairs.add((src_lang, tgt_lang, _normalize(source), _normalize(target)))
    return sources, pairs


def _row_id(dataset: str, index: int, src_lang: str, tgt_lang: str, source: str, target: str) -> str:
    payload = "\0".join(
        (dataset, str(index), src_lang, tgt_lang, source, target)
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _make_row(
    *,
    dataset: str,
    index: int,
    src_lang: str,
    tgt_lang: str,
    source: str,
    target: str,
) -> dict[str, Any]:
    return {
        "src_lang": src_lang,
        "tgt_lang": tgt_lang,
        "pair": f"{src_lang}-{tgt_lang}",
        "source": source,
        "target_pos": target,
        "target_neg": "",
        "lang": tgt_lang,
        "query": source,
        "pos": target,
        "neg": "",
        "row_id": _row_id(dataset, index, src_lang, tgt_lang, source, target),
        "source_dataset": dataset,
        "source_index": index,
    }


def _assign_negatives(rows: list[dict[str, Any]]) -> None:
    by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_target[str(row["tgt_lang"])].append(row)
    for target_rows in by_target.values():
        if len(target_rows) < 2:
            raise RuntimeError("At least two rows per target language are required for negatives.")
        for index, row in enumerate(target_rows):
            negative = str(target_rows[(index + 1) % len(target_rows)]["target_pos"])
            row["target_neg"] = negative
            row["neg"] = negative


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="wmt12")
    parser.add_argument("--langpair", default="en-es")
    parser.add_argument("--bidirectional", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--eval", action="append", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--usage-scope", default="local_research_only")
    parser.add_argument("--out", required=True)
    parser.add_argument("--manifest-out", required=True)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    out_path = Path(args.out).expanduser().resolve()
    manifest_path = Path(args.manifest_out).expanduser().resolve()
    eval_paths = [Path(value).expanduser().resolve() for value in args.eval]
    for path in eval_paths:
        if not path.is_file():
            raise RuntimeError(f"Evaluation file does not exist: {path}")
    if not args.force and (out_path.exists() or manifest_path.exists()):
        raise RuntimeError("Output already exists; pass --force to replace it.")

    dataset_name = str(args.dataset)
    langpair = str(args.langpair)
    if dataset_name not in sacrebleu.DATASETS:
        raise RuntimeError(f"Unknown SacreBLEU dataset: {dataset_name}")
    dataset = sacrebleu.DATASETS[dataset_name]
    if langpair not in dataset.langpairs:
        raise RuntimeError(f"Dataset {dataset_name} does not provide {langpair}")
    source_lang, target_lang = langpair.split("-", 1)
    source_path = Path(dataset.get_source_file(langpair)).resolve()
    reference_paths = [Path(path).resolve() for path in dataset.get_reference_files(langpair)]
    if len(reference_paths) != 1:
        raise RuntimeError(f"Expected one reference for {dataset_name}/{langpair}")
    reference_path = reference_paths[0]
    sources = source_path.read_text(encoding="utf-8").splitlines()
    references = reference_path.read_text(encoding="utf-8").splitlines()
    if len(sources) != len(references):
        raise RuntimeError(
            f"Parallel row mismatch: sources={len(sources)} references={len(references)}"
        )

    eval_sources, eval_pairs = _evaluation_keys(eval_paths)
    counts: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    directions = [(source_lang, target_lang)]
    if bool(args.bidirectional):
        directions.append((target_lang, source_lang))
    for index, (source_text, reference_text) in enumerate(
        zip(sources, references, strict=True)
    ):
        forward = {
            source_lang: source_text.strip(),
            target_lang: reference_text.strip(),
        }
        for src_lang, tgt_lang in directions:
            counts["candidates"] += 1
            source = forward[src_lang]
            target = forward[tgt_lang]
            if not source or not target:
                counts["rejected_empty"] += 1
                continue
            source_key = (src_lang, _normalize(source))
            pair_key = (src_lang, tgt_lang, _normalize(source), _normalize(target))
            if source_key in eval_sources or pair_key in eval_pairs:
                counts["rejected_eval_overlap"] += 1
                continue
            if pair_key in seen:
                counts["rejected_duplicate"] += 1
                continue
            seen.add(pair_key)
            rows.append(
                _make_row(
                    dataset=f"sacrebleu:{dataset_name}:{langpair}",
                    index=index,
                    src_lang=src_lang,
                    tgt_lang=tgt_lang,
                    source=source,
                    target=target,
                )
            )

    _assign_negatives(rows)
    random.Random(int(args.seed)).shuffle(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    pair_counts = Counter(str(row["pair"]) for row in rows)
    manifest = {
        "dataset": dataset_name,
        "langpair": langpair,
        "bidirectional": bool(args.bidirectional),
        "sacrebleu_version": str(sacrebleu.__version__),
        "source_files": [
            {"path": str(source_path), "sha256": _sha256_path(source_path)},
            {"path": str(reference_path), "sha256": _sha256_path(reference_path)},
        ],
        "evaluation_exclusions": [
            {"path": _project_path(path), "sha256": _sha256_path(path)}
            for path in eval_paths
        ],
        "selection": {
            "seed": int(args.seed),
            "counts": dict(sorted(counts.items())),
            "rows": len(rows),
            "rows_by_pair": dict(sorted(pair_counts.items())),
        },
        "license": "unknown",
        "usage_scope": str(args.usage_scope),
        "output": {"path": _project_path(out_path), "sha256": _sha256_path(out_path)},
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[sacrebleu-pairs] rows={len(rows)} pairs={dict(sorted(pair_counts.items()))}")
    print(f"[sacrebleu-pairs] out={out_path}")
    print(f"[sacrebleu-pairs] manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
