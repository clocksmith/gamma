"""Validate translation rows and legacy pos/neg aliases in a JSONL file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def check_row(row: str) -> tuple[bool, str]:
    try:
        data = json.loads(row)
        if data["pos"] != data["target_pos"]:
            return False, "pos != target_pos"
        if data["neg"] != data["target_neg"]:
            return False, "neg != target_neg"
        if not data["source"] or not data["target_pos"] or not data["target_neg"]:
            return False, "empty field"
        return True, ""
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return False, str(exc)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("existing_rows.jsonl"),
        help="JSONL file to validate (default: existing_rows.jsonl)",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=10,
        help="Maximum validation errors to print",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[tuple[int, str]] = []
    row_count = 0

    with args.path.open("r", encoding="utf-8") as rows:
        for row_count, row in enumerate(rows, start=1):
            is_valid, reason = check_row(row)
            if not is_valid:
                errors.append((row_count, reason))

    print(f"Found {len(errors)} errors in {row_count} rows.")
    for row_number, error in errors[: args.max_errors]:
        print(f"Row {row_number}: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
