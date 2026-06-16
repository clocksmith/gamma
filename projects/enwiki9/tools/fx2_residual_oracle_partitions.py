#!/usr/bin/env python3
"""Screen causal row partitions with oracle and held-out empirical bounds.

This is an offline triage tool. It asks whether a candidate structural key has
enough residual loss mass to justify implementation work. The all-slice oracle
uses post-hoc empirical bit rates per key, so it is not decoder-realizable. The
held-out score trains per-key KT probabilities on the prefix and scores the
suffix without updating those probabilities.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from fx2_shadow_residual_coder import as_int, iter_rows, prob_bucket


ROOT = pathlib.Path(__file__).resolve().parents[1]
TOTAL = 1 << 16
DEFAULT_OUT = ROOT / "residual_oracle_partitions.json"


def qbits_for_prob(bit: int, p1: float) -> float:
    p1 = max(1.0, min(65535.0, p1))
    prob = p1 / 65536.0 if bit else (65536.0 - p1) / 65536.0
    import math

    return -math.log2(prob) * 256.0


def qbits_for_counts(bit: int, zeros: int, ones: int) -> float:
    denom = 2.0 * (zeros + ones + 1)
    p1 = ((2 * ones + 1) * TOTAL) / denom
    return qbits_for_prob(bit, p1)


def baseline_qbits(row: dict[str, Any]) -> float:
    qbits = as_int(row, "baseline_qbits", default=-1)
    if qbits >= 0:
        return float(qbits)
    bit = as_int(row, "bit", default=0)
    p1 = as_int(row, "p1", default=32768)
    return qbits_for_prob(bit, p1)


def value_for(row: dict[str, Any], field: str) -> int:
    p1 = as_int(row, "p1", default=32768)
    if field == "p_bucket":
        return prob_bucket(p1, 16)
    return as_int(row, field, default=0)


def key_for(row: dict[str, Any], fields: tuple[str, ...]) -> tuple[int, ...]:
    return tuple(value_for(row, field) for field in fields)


@dataclass
class Counts:
    zeros: int = 0
    ones: int = 0

    def update(self, bit: int) -> None:
        if bit:
            self.ones += 1
        else:
            self.zeros += 1


def load_rows(path: pathlib.Path, max_rows: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in iter_rows(path):
        bit = as_int(row, "bit", default=-1)
        p1 = as_int(row, "p1", default=0)
        if bit not in (0, 1) or not (0 < p1 < TOTAL):
            continue
        rows.append(row)
        if max_rows > 0 and len(rows) >= max_rows:
            break
    return rows


def score_group(rows: list[dict[str, Any]], fields: tuple[str, ...], train_rows: int) -> dict[str, Any]:
    all_counts: dict[tuple[int, ...], Counts] = defaultdict(Counts)
    train_counts: dict[tuple[int, ...], Counts] = defaultdict(Counts)
    baseline_all = 0.0
    baseline_test = 0.0
    test_rows = 0

    for idx, row in enumerate(rows, start=1):
        bit = as_int(row, "bit", default=0)
        key = key_for(row, fields)
        all_counts[key].update(bit)
        baseline_all += baseline_qbits(row)
        if train_rows <= 0 or idx <= train_rows:
            train_counts[key].update(bit)
        else:
            baseline_test += baseline_qbits(row)
            test_rows += 1

    oracle_all = 0.0
    heldout_static = 0.0
    for idx, row in enumerate(rows, start=1):
        bit = as_int(row, "bit", default=0)
        key = key_for(row, fields)
        counts = all_counts[key]
        oracle_all += qbits_for_counts(bit, counts.zeros, counts.ones)
        if train_rows > 0 and idx > train_rows:
            train = train_counts.get(key)
            if train is None:
                heldout_static += 256.0
            else:
                heldout_static += qbits_for_counts(bit, train.zeros, train.ones)

    out = {
        "fields": list(fields),
        "rows": len(rows),
        "contexts": len(all_counts),
        "baseline_bits": baseline_all / 256.0,
        "oracle_bits": oracle_all / 256.0,
        "oracle_gain_bits": (baseline_all - oracle_all) / 256.0,
        "oracle_gain_bytes": (baseline_all - oracle_all) / 2048.0,
        "test_rows": test_rows,
    }
    if train_rows > 0:
        out.update(
            {
                "test_baseline_bits": baseline_test / 256.0,
                "test_static_bits": heldout_static / 256.0,
                "test_static_gain_bits": (baseline_test - heldout_static) / 256.0,
                "test_static_gain_bytes": (baseline_test - heldout_static) / 2048.0,
            }
        )
    return out


def run(args: argparse.Namespace) -> dict[str, Any]:
    rows = load_rows(pathlib.Path(args.rows), args.max_rows)
    groups = [tuple(part for part in spec.split(",") if part) for spec in args.group]
    if not groups:
        groups = [
            ("mode",),
            ("char_class",),
            ("mode", "char_class"),
            ("bit_pos",),
            ("p_bucket", "bit_pos"),
            ("mode", "char_class", "bit_pos"),
        ]
    results = [score_group(rows, group, args.train_rows) for group in groups]
    results.sort(key=lambda item: item.get("test_static_gain_bits", item["oracle_gain_bits"]), reverse=True)
    return {
        "input": args.rows,
        "rows": len(rows),
        "train_rows": args.train_rows,
        "groups": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Screen residual partition oracle mass.")
    parser.add_argument("rows")
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    parser.add_argument("--group", action="append", default=[])
    parser.add_argument("--train-rows", type=int, default=0)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if args.train_rows < 0:
        raise SystemExit("--train-rows must be non-negative")
    if args.max_rows < 0:
        raise SystemExit("--max-rows must be non-negative")

    payload = run(args)
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        top = payload["groups"][0] if payload["groups"] else {}
        print(
            json.dumps(
                {
                    "status": "ok" if payload["rows"] else "no_rows",
                    "rows": payload["rows"],
                    "top_fields": top.get("fields"),
                    "top_oracle_gain_bits": top.get("oracle_gain_bits"),
                    "top_test_static_gain_bits": top.get("test_static_gain_bits"),
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
