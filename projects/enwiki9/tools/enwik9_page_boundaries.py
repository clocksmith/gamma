#!/usr/bin/env python3
"""Seal exact enwik9 page boundaries and prompt economics by population."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


PAGE_OPEN = b"<page>"
PAGE_CLOSE = b"</page>"


def find_offsets(path: Path, needle: bytes) -> list[int]:
    offsets: list[int] = []
    tail = b""
    consumed = 0
    last_emitted = -1
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            data = tail + chunk
            base = consumed - len(tail)
            cursor = 0
            while True:
                found = data.find(needle, cursor)
                if found < 0:
                    break
                absolute = base + found
                if absolute > last_emitted:
                    offsets.append(absolute)
                    last_emitted = absolute
                cursor = found + 1
            consumed += len(chunk)
            tail = data[-(len(needle) - 1) :]
    return offsets


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def percentile(sorted_values: list[int], numerator: int, denominator: int) -> int | None:
    if not sorted_values:
        return None
    index = ((len(sorted_values) - 1) * numerator) // denominator
    return sorted_values[index]


def population_receipt(label: str, path: Path, debt_bytes: int) -> dict[str, Any]:
    starts = find_offsets(path, PAGE_OPEN)
    closes = find_offsets(path, PAGE_CLOSE)
    complete: list[tuple[int, int]] = []
    close_index = 0
    for start in starts:
        while close_index < len(closes) and closes[close_index] < start:
            close_index += 1
        if close_index >= len(closes):
            break
        end = closes[close_index] + len(PAGE_CLOSE)
        complete.append((start, end))
        close_index += 1
    sizes = sorted(end - start for start, end in complete)
    started_pages = len(starts)
    complete_pages = len(complete)
    return {
        "label": label,
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
        "page_open_offsets": starts,
        "page_close_end_offsets": [offset + len(PAGE_CLOSE) for offset in closes],
        "started_pages": started_pages,
        "complete_pages": complete_pages,
        "incomplete_tail_pages": max(started_pages - complete_pages, 0),
        "required_net_bytes_per_started_page": (
            debt_bytes / started_pages if started_pages else None
        ),
        "required_net_bytes_per_complete_page": (
            debt_bytes / complete_pages if complete_pages else None
        ),
        "complete_page_size_bytes": {
            "minimum": sizes[0] if sizes else None,
            "p25": percentile(sizes, 1, 4),
            "median": percentile(sizes, 1, 2),
            "p75": percentile(sizes, 3, 4),
            "p90": percentile(sizes, 9, 10),
            "p99": percentile(sizes, 99, 100),
            "maximum": sizes[-1] if sizes else None,
            "mean": sum(sizes) / len(sizes) if sizes else None,
        },
    }


def parse_population(value: str) -> tuple[str, Path]:
    label, separator, raw_path = value.partition("=")
    if not separator or not label or not raw_path:
        raise argparse.ArgumentTypeError("population must be LABEL=PATH")
    path = Path(raw_path)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"population file is missing: {path}")
    return label, path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--population",
        action="append",
        type=parse_population,
        required=True,
        help="LABEL=PATH; repeat for each population",
    )
    parser.add_argument("--debt-bytes", type=int, default=1_524_268)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [
        population_receipt(label, path, args.debt_bytes)
        for label, path in args.population
    ]
    receipt = {
        "schema": "enwik9_page_boundaries_v1",
        "design_target_bytes": 108_000_000,
        "planning_baseline_bytes": 109_524_268,
        "design_debt_bytes": args.debt_bytes,
        "boundary_contract": {
            "page_open": PAGE_OPEN.decode(),
            "page_close": PAGE_CLOSE.decode(),
            "offsets_are_zero_based": True,
            "close_offsets_are_exclusive": True,
            "prompt_economics_use_started_pages": True,
        },
        "populations": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(
        json.dumps(
            {
                row["label"]: {
                    "bytes": row["bytes"],
                    "started_pages": row["started_pages"],
                    "complete_pages": row["complete_pages"],
                    "required_net_bytes_per_started_page": row[
                        "required_net_bytes_per_started_page"
                    ],
                }
                for row in rows
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
