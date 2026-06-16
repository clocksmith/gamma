#!/usr/bin/env python3
"""Partition fx2 residual rows by causal fields and summarize loss mass.

This is a lock-safe audit tool. It reads cached TSV or FX2_RESIDUAL_ROW logs and
aggregates baseline qbits by selected causal coordinates. The output is not a
claim of achievable gain; it tells us where residual log-loss is concentrated
before building another side-state model.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from fx2_shadow_residual_coder import as_int, iter_rows


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "residual_heatmap.json"


def qbits_for(bit: int, p1: int | float) -> int:
    p1 = max(1.0, min(65535.0, float(p1)))
    prob = p1 / 65536.0 if bit else (65536.0 - p1) / 65536.0
    import math

    return int((-math.log2(prob)) * 256.0 + 0.5)


@dataclass
class BucketStats:
    rows: int = 0
    qbits: int = 0
    ones: int = 0

    def update(self, bit: int, qbits: int) -> None:
        self.rows += 1
        self.qbits += qbits
        self.ones += bit

    def to_json(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "bits": self.qbits / 256.0,
            "bytes": self.qbits / 2048.0,
            "ones": self.ones,
            "one_rate": self.ones / self.rows if self.rows else 0.0,
            "bits_per_row": self.qbits / (256.0 * self.rows) if self.rows else 0.0,
        }


def key_for(row: dict[str, Any], fields: tuple[str, ...]) -> tuple[int, ...]:
    return tuple(as_int(row, field, default=0) for field in fields)


def run_heatmap(args: argparse.Namespace) -> dict[str, Any]:
    path = pathlib.Path(args.rows)
    groups = [tuple(part for part in spec.split(",") if part) for spec in args.group]
    if not groups:
        groups = [("mode",), ("char_class",), ("mode", "char_class"), ("bit_pos",)]

    totals = BucketStats()
    maps: dict[str, dict[tuple[int, ...], BucketStats]] = {
        ",".join(group): defaultdict(BucketStats) for group in groups
    }
    rows = 0
    for row in iter_rows(path):
        bit = as_int(row, "bit", default=-1)
        p1 = as_int(row, "p1", default=0)
        if bit not in (0, 1) or not (0 < p1 < 65536):
            continue
        qbits = as_int(row, "baseline_qbits", default=-1)
        if qbits < 0:
            qbits = qbits_for(bit, p1)
        totals.update(bit, qbits)
        for group in groups:
            maps[",".join(group)][key_for(row, group)].update(bit, qbits)
        rows += 1
        if args.max_rows > 0 and rows >= args.max_rows:
            break

    output_maps: dict[str, list[dict[str, Any]]] = {}
    for group_name, buckets in maps.items():
        rows_out = []
        for key, stats in sorted(
            buckets.items(),
            key=lambda item: (item[1].qbits, item[1].rows),
            reverse=True,
        )[: args.top]:
            payload = stats.to_json()
            payload["key"] = list(key)
            payload["share_of_bits"] = (
                stats.qbits / totals.qbits if totals.qbits else 0.0
            )
            payload["share_of_rows"] = (
                stats.rows / totals.rows if totals.rows else 0.0
            )
            rows_out.append(payload)
        output_maps[group_name] = rows_out

    return {
        "input": str(path),
        "rows": totals.rows,
        "total": totals.to_json(),
        "groups": output_maps,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize residual qbit loss by causal groups.")
    parser.add_argument("rows")
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    parser.add_argument("--group", action="append", default=[])
    parser.add_argument("--top", type=int, default=16)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if args.top <= 0:
        raise SystemExit("--top must be positive")
    if args.max_rows < 0:
        raise SystemExit("--max-rows must be non-negative")

    payload = run_heatmap(args)
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        print(
            json.dumps(
                {
                    "status": "ok" if payload["rows"] else "no_rows",
                    "rows": payload["rows"],
                    "total_bits": payload["total"]["bits"],
                    "total_bytes": payload["total"]["bytes"],
                    "groups": list(payload["groups"]),
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
