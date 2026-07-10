#!/usr/bin/env python3
"""Merge aligned translation prediction files into a labeled candidate pool."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]
ALIGNMENT_FIELDS = ("pair", "src_lang", "tgt_lang", "source", "target_pos")


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


def _parse_prediction_specs(values: list[str]) -> list[tuple[str, Path]]:
    specs: list[tuple[str, Path]] = []
    labels: set[str] = set()
    for value in values:
        if "=" not in value:
            raise RuntimeError(f"Invalid --prediction spec, expected label=path: {value}")
        label, raw_path = value.split("=", 1)
        label = label.strip()
        path = Path(raw_path.strip()).expanduser().resolve()
        if not label or label in labels:
            raise RuntimeError(f"Prediction labels must be non-empty and unique: {label!r}")
        if not path.is_file():
            raise RuntimeError(f"Prediction file does not exist: {path}")
        labels.add(label)
        specs.append((label, path))
    if len(specs) < 2:
        raise RuntimeError("At least two --prediction inputs are required.")
    return specs


def _merge_rows(inputs: list[tuple[str, list[dict[str, Any]]]]) -> list[dict[str, Any]]:
    expected_count = len(inputs[0][1])
    if any(len(rows) != expected_count for _, rows in inputs):
        raise RuntimeError("Prediction inputs have different row counts.")
    output: list[dict[str, Any]] = []
    for row_index in range(expected_count):
        baseline = inputs[0][1][row_index]
        expected = tuple(str(baseline.get(field) or "") for field in ALIGNMENT_FIELDS)
        candidates: list[str] = []
        labels: list[str] = []
        for label, rows in inputs:
            row = rows[row_index]
            actual = tuple(str(row.get(field) or "") for field in ALIGNMENT_FIELDS)
            if actual != expected:
                raise RuntimeError(f"Prediction alignment mismatch at row {row_index + 1}: {label}")
            prediction = " ".join(str(row.get("pred") or "").split())
            if not prediction:
                raise RuntimeError(f"Empty prediction at row {row_index + 1}: {label}")
            labels.append(label)
            candidates.append(prediction)
        merged = {key: value for key, value in baseline.items() if key not in {"candidates", "candidate_sources"}}
        merged["pred"] = candidates[0]
        merged["candidates"] = candidates
        merged["candidate_sources"] = labels
        output.append(merged)
    return output


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction", action="append", required=True, help="label=predictions.jsonl")
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary-out", required=True)
    parser.add_argument("--pair", default="", help="Optional pair filter such as es-en.")
    parser.add_argument("--limit", type=int, default=0, help="0 = all aligned rows after filtering.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    specs = _parse_prediction_specs(list(args.prediction))
    inputs: list[tuple[str, list[dict[str, Any]]]] = []
    for label, path in specs:
        rows = _load_jsonl(path)
        if str(args.pair).strip():
            rows = [row for row in rows if str(row.get("pair") or "") == str(args.pair).strip()]
        if int(args.limit) > 0:
            rows = rows[: int(args.limit)]
        inputs.append((label, rows))
    rows = _merge_rows(inputs)
    out_path = Path(args.out).expanduser().resolve()
    summary_path = Path(args.summary_out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {
        "rows": len(rows),
        "candidate_sources": [label for label, _ in specs],
        "pair_filter": str(args.pair).strip(),
        "limit": int(args.limit),
        "inputs": [
            {"label": label, "path": _project_path(path), "sha256": _sha256_path(path)}
            for label, path in specs
        ],
        "output": {"path": _project_path(out_path), "sha256": _sha256_path(out_path)},
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[candidate-pool] rows={len(rows)} sources={','.join(summary['candidate_sources'])}")
    print(f"[candidate-pool] out={out_path}")
    print(f"[candidate-pool] summary={summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
