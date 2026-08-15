#!/usr/bin/env python3
"""Rebuild the central driver ledger from historical result JSON files."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any

import research_contracts


ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
PROGRAMS_DIR = ROOT / "programs"
LEDGER_PATH = RESULTS_DIR / "run_ledger.jsonl"
DRIVER_RESULT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{6}(?:\.\d+)?\.json$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ledger",
        type=pathlib.Path,
        default=LEDGER_PATH,
        help="ledger output path (default: results/run_ledger.jsonl)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="append to existing ledger instead of replacing it",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="explicitly replace existing ledger (default)",
    )
    parser.add_argument(
        "--program-id",
        action="append",
        nargs="+",
        default=None,
        help="limit to one or more program IDs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="do not write the ledger; print planned row count and checks",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail if any result JSON is malformed",
    )
    return parser.parse_args()


def load_json(path: pathlib.Path, *, strict: bool) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        if strict:
            raise SystemExit(f"invalid JSON in {path}: {exc}") from exc
        print(f"[warn] skip malformed JSON: {path}", file=sys.stderr)
        return None


def load_program_name(program_id: str) -> str | None:
    meta = PROGRAMS_DIR / program_id / "meta.json"
    if not meta.exists():
        return None
    raw = load_json(meta, strict=False)
    if not isinstance(raw, dict):
        return None
    if isinstance(raw.get("name"), str) and raw["name"].strip():
        return raw["name"].strip()
    if isinstance(raw.get("description"), str) and raw["description"].strip():
        return raw["description"].strip()
    return None


def build_ledger_row(
    result: dict[str, Any],
    result_path: pathlib.Path,
    program_name: str | None,
) -> dict[str, Any] | None:
    program_id = result.get("program_id")
    if not isinstance(program_id, str):
        print(f"[warn] skip row missing program_id: {result_path}", file=sys.stderr)
        return None
    timestamp = result.get("timestamp")
    if not isinstance(timestamp, str) or not timestamp:
        print(
            f"[warn] skip row missing timestamp: {result_path}",
            file=sys.stderr,
        )
        return None

    return research_contracts.build_driver_run_ledger_row(
        result,
        result_path,
        program_name=program_name,
    )


def collect_results(program_ids: list[str] | None) -> list[pathlib.Path]:
    if not RESULTS_DIR.exists():
        return []
    rows: list[pathlib.Path] = []
    for entry in sorted(RESULTS_DIR.iterdir()):
        if not entry.is_dir() or entry.name == LEDGER_PATH.name:
            continue
        if program_ids and entry.name not in program_ids:
            continue
        rows.extend(
            path
            for path in sorted(entry.glob("*.json"))
            if DRIVER_RESULT_RE.fullmatch(path.name)
        )
    return rows


def main() -> int:
    args = parse_args()
    program_ids: list[str] | None = (
        [pid for group in args.program_id for pid in group]
        if args.program_id
        else None
    )
    if args.append and args.overwrite:
        print(
            "[warn] both --append and --overwrite provided; --append wins",
            file=sys.stderr,
        )
    result_paths = collect_results(program_ids)
    if not result_paths:
        if args.append:
            print("[info] no result JSON files found; leaving ledger untouched")
        else:
            print("[info] no result JSON files found")
        return 0

    seen_run_ids: set[str] = set()
    rows: list[tuple[str, str, str]] = []
    skipped = 0

    for path in result_paths:
        payload = load_json(path, strict=args.strict)
        if payload is None:
            skipped += 1
            continue
        if not isinstance(payload, dict):
            skipped += 1
            print(f"[warn] skip non-object JSON: {path}", file=sys.stderr)
            continue
        program_id = payload.get("program_id")
        if not isinstance(program_id, str):
            skipped += 1
            print(f"[warn] skip malformed payload missing program_id: {path}", file=sys.stderr)
            continue

        program_name = load_program_name(program_id)
        row = build_ledger_row(payload, path, program_name)
        if row is None:
            skipped += 1
            continue
        if row["run_id"] in seen_run_ids:
            print(f"[warn] duplicate run_id skipped: {row['run_id']} ({path})", file=sys.stderr)
            skipped += 1
            continue
        seen_run_ids.add(row["run_id"])
        rows.append((row["timestamp"], row["program_id"], json.dumps(row, sort_keys=True)))

    rows.sort(key=lambda item: (item[0], item[1], item[2]))

    if args.dry_run:
        print(
            json.dumps(
                {
                    "planned_rows": len(rows),
                    "skipped_inputs": skipped,
                    "ledger_target": str(args.ledger),
                    "append": args.append,
                },
                indent=2,
            )
        )
        return 0

    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.append else "w"
    with args.ledger.open(mode, encoding="utf-8") as fh:
        for _, _, row in rows:
            fh.write(row + "\n")
    print(
        json.dumps(
            {
                "rows_written": len(rows),
                "skipped_inputs": skipped,
                "ledger_path": str(args.ledger),
                "mode": "append" if args.append else "overwrite",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
