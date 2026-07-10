#!/usr/bin/env python3
"""Build a decontaminated sequence-distillation set with replay rows."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[4]
PROMPT_FRAGMENTS = (
    "<start_of_turn>",
    "<end_of_turn>",
    "<bos>",
    "<eos>",
)


def _normalize(value: Any) -> str:
    return " ".join(re.findall(r"\w+", str(value or "").casefold()))


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
            value = json.loads(line)
            if not isinstance(value, dict):
                raise RuntimeError(f"{path}:{line_number}: expected a JSON object")
            rows.append(value)
    return rows


def _evaluation_sources(paths: Iterable[Path]) -> set[tuple[str, str]]:
    sources: set[tuple[str, str]] = set()
    for path in paths:
        for row in _load_jsonl(path):
            src_lang = str(row.get("src_lang") or row.get("source_lang") or "").strip()
            source = str(row.get("source") or row.get("query") or "").strip()
            if src_lang and source:
                sources.add((src_lang, _normalize(source)))
    return sources


def _row_id(kind: str, src_lang: str, tgt_lang: str, source: str, target: str) -> str:
    payload = "\0".join((kind, src_lang, tgt_lang, source, target)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _canonical_row(
    *,
    source_row: dict[str, Any],
    target: str,
    kind: str,
    teacher_model: str,
) -> dict[str, Any]:
    src_lang = str(source_row.get("src_lang") or source_row.get("source_lang") or "").strip()
    tgt_lang = str(source_row.get("tgt_lang") or source_row.get("target_lang") or "").strip()
    source = str(source_row.get("source") or source_row.get("query") or "").strip()
    pair = str(source_row.get("pair") or f"{src_lang}-{tgt_lang}").strip()
    if not src_lang or not tgt_lang or not source or not target:
        raise RuntimeError("Cannot build a canonical row with empty translation fields.")
    if pair != f"{src_lang}-{tgt_lang}":
        raise RuntimeError(f"Pair mismatch: {pair} != {src_lang}-{tgt_lang}")

    row: dict[str, Any] = {
        "src_lang": src_lang,
        "tgt_lang": tgt_lang,
        "pair": pair,
        "source": source,
        "target_pos": target,
        "target_neg": "",
        "lang": tgt_lang,
        "query": source,
        "pos": target,
        "neg": "",
        "row_id": _row_id(kind, src_lang, tgt_lang, source, target),
        "distill_source": kind,
    }
    if kind == "sequence_teacher":
        row["teacher_model"] = teacher_model
        row["gold_target_pos"] = str(source_row.get("target_pos") or source_row.get("pos") or "").strip()
    return row


def _build_sequence_rows(
    rows: list[dict[str, Any]],
    *,
    teacher_model: str,
    evaluation_sources: set[tuple[str, str]],
    counts: Counter[str],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        counts["teacher_rows"] += 1
        src_lang = str(row.get("src_lang") or row.get("source_lang") or "").strip()
        tgt_lang = str(row.get("tgt_lang") or row.get("target_lang") or "").strip()
        source = str(row.get("source") or row.get("query") or "").strip()
        prediction = " ".join(str(row.get("pred") or "").split())
        if not src_lang or not tgt_lang or not source or not prediction:
            counts["rejected_empty"] += 1
            continue
        if any(fragment in prediction for fragment in PROMPT_FRAGMENTS):
            counts["rejected_prompt_fragment"] += 1
            continue
        source_key = (src_lang, _normalize(source))
        if source_key in evaluation_sources:
            counts["rejected_eval_source"] += 1
            continue
        dedupe_key = (src_lang, tgt_lang, _normalize(source))
        if dedupe_key in seen:
            counts["rejected_duplicate"] += 1
            continue
        seen.add(dedupe_key)
        output.append(
            _canonical_row(
                source_row=row,
                target=prediction,
                kind="sequence_teacher",
                teacher_model=teacher_model,
            )
        )
    return output


def _sample_replay_rows(
    paths: list[Path],
    *,
    limit: int,
    directions: set[str],
    evaluation_sources: set[tuple[str, str]],
    rng: random.Random,
    counts: Counter[str],
) -> list[dict[str, Any]]:
    eligible: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for path in paths:
        for row in _load_jsonl(path):
            counts["replay_rows"] += 1
            src_lang = str(row.get("src_lang") or row.get("source_lang") or "").strip()
            tgt_lang = str(row.get("tgt_lang") or row.get("target_lang") or "").strip()
            source = str(row.get("source") or row.get("query") or "").strip()
            target = str(row.get("target_pos") or row.get("pos") or "").strip()
            pair = str(row.get("pair") or f"{src_lang}-{tgt_lang}").strip()
            if directions and pair not in directions:
                continue
            if not src_lang or not tgt_lang or not source or not target:
                counts["replay_rejected_empty"] += 1
                continue
            if (src_lang, _normalize(source)) in evaluation_sources:
                counts["replay_rejected_eval_source"] += 1
                continue
            dedupe_key = (src_lang, tgt_lang, _normalize(source))
            if dedupe_key in seen:
                counts["replay_rejected_duplicate"] += 1
                continue
            seen.add(dedupe_key)
            eligible.append(
                _canonical_row(
                    source_row=row,
                    target=target,
                    kind="replay",
                    teacher_model="",
                )
            )
    if limit > len(eligible):
        raise RuntimeError(f"Requested {limit} replay rows but only {len(eligible)} are eligible.")
    if limit <= 0 or limit == len(eligible):
        return eligible
    return rng.sample(eligible, limit)


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
    parser.add_argument("--teacher-predictions", required=True)
    parser.add_argument("--teacher-model", required=True)
    parser.add_argument("--replay", action="append", default=[])
    parser.add_argument("--replay-rows", type=int, default=0)
    parser.add_argument("--replay-directions", default="")
    parser.add_argument("--eval", action="append", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--usage-scope", default="local_research_only")
    parser.add_argument("--out", required=True)
    parser.add_argument("--manifest-out", required=True)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    teacher_path = Path(args.teacher_predictions).expanduser().resolve()
    replay_paths = [Path(value).expanduser().resolve() for value in args.replay]
    eval_paths = [Path(value).expanduser().resolve() for value in args.eval]
    out_path = Path(args.out).expanduser().resolve()
    manifest_path = Path(args.manifest_out).expanduser().resolve()
    for path in [teacher_path, *replay_paths, *eval_paths]:
        if not path.is_file():
            raise RuntimeError(f"Input does not exist: {path}")
    if not args.force and (out_path.exists() or manifest_path.exists()):
        raise RuntimeError("Output already exists; pass --force to replace it.")

    rng = random.Random(int(args.seed))
    eval_sources = _evaluation_sources(eval_paths)
    counts: Counter[str] = Counter()
    sequence_rows = _build_sequence_rows(
        _load_jsonl(teacher_path),
        teacher_model=str(args.teacher_model),
        evaluation_sources=eval_sources,
        counts=counts,
    )
    directions = {value.strip() for value in str(args.replay_directions).split(",") if value.strip()}
    replay_rows = _sample_replay_rows(
        replay_paths,
        limit=int(args.replay_rows),
        directions=directions,
        evaluation_sources=eval_sources,
        rng=rng,
        counts=counts,
    )
    rows = sequence_rows + replay_rows
    _assign_negatives(rows)
    rng.shuffle(rows)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    row_kinds = Counter(str(row["distill_source"]) for row in rows)
    pair_counts = Counter(str(row["pair"]) for row in rows)
    manifest = {
        "teacher": {
            "model": str(args.teacher_model),
            "predictions": _project_path(teacher_path),
            "predictions_sha256": _sha256_path(teacher_path),
        },
        "replay": {
            "inputs": [
                {"path": _project_path(path), "sha256": _sha256_path(path)}
                for path in replay_paths
            ],
            "requested_rows": int(args.replay_rows),
            "directions": sorted(directions),
        },
        "evaluation_exclusions": [
            {"path": _project_path(path), "sha256": _sha256_path(path)}
            for path in eval_paths
        ],
        "selection": {
            "seed": int(args.seed),
            "counts": dict(sorted(counts.items())),
            "rows": len(rows),
            "rows_by_source": dict(sorted(row_kinds.items())),
            "rows_by_pair": dict(sorted(pair_counts.items())),
        },
        "usage_scope": str(args.usage_scope),
        "output": {"path": _project_path(out_path), "sha256": _sha256_path(out_path)},
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"[sequence-distill] rows={len(rows)} sequence={len(sequence_rows)} "
        f"replay={len(replay_rows)} pairs={dict(sorted(pair_counts.items()))}"
    )
    print(f"[sequence-distill] out={out_path}")
    print(f"[sequence-distill] manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
