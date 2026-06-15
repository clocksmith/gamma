#!/usr/bin/env python3
"""Score a tiny causal residual APM on FX2_RESIDUAL_ROW logs.

The input is produced by fx2 builds compiled with FX2_RESIDUAL_LOG. This tool
does not use future bits: it predicts from current counts, emits corrected loss,
then updates the count table with the observed bit.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
from dataclasses import dataclass
from typing import Any


PAIR_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([^ \t]+)")
PREFIX = "FX2_RESIDUAL_ROW "


def parse_value(value: str) -> Any:
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def parse_row(line: str) -> dict[str, Any] | None:
    if PREFIX not in line:
        return None
    payload = line.split(PREFIX, 1)[1]
    pairs = PAIR_RE.findall(payload)
    if not pairs:
        return None
    return {key: parse_value(value) for key, value in pairs}


def read_rows(path: pathlib.Path):
    with path.open("r", errors="replace") as f:
        for line in f:
            row = parse_row(line)
            if row is not None:
                yield row


def as_int(row: dict[str, Any], key: str, default: int = 0) -> int:
    value = row.get(key, default)
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def prob_bucket(p1: int, buckets: int) -> int:
    if buckets <= 1:
        return 0
    p1 = max(1, min(65535, p1))
    return min(buckets - 1, (p1 * buckets) >> 16)


def qbits_for(bit: int, p1: float) -> int:
    p1 = max(1.0, min(65535.0, p1))
    prob = p1 / 65536.0 if bit else (65536.0 - p1) / 65536.0
    return int((-math.log2(prob)) * 256.0 + 0.5)


def key_for(row: dict[str, Any], fields: list[str], buckets: int) -> tuple[Any, ...]:
    out: list[Any] = []
    for field in fields:
        if field == "p_bucket":
            out.append(prob_bucket(as_int(row, "p1", 32768), buckets))
        else:
            out.append(row.get(field, 0))
    return tuple(out)


@dataclass
class Counter:
    zeros: int = 0
    ones: int = 0

    def p1(self, alpha: float) -> float:
        total = self.zeros + self.ones
        return 65536.0 * (self.ones + alpha) / (total + 2.0 * alpha)

    def update(self, bit: int) -> None:
        if bit:
            self.ones += 1
        else:
            self.zeros += 1


@dataclass
class Totals:
    rows: int = 0
    baseline_qbits: int = 0
    corrected_qbits: int = 0

    @property
    def gain_bits(self) -> float:
        return (self.baseline_qbits - self.corrected_qbits) / 256.0


def split_for(row: dict[str, Any], train_bytes: int) -> str:
    if train_bytes <= 0:
        return "all"
    return "train" if as_int(row, "pos") < train_bytes else "test"


def score(
    rows,
    fields: list[str],
    p_buckets: int,
    alpha: float,
    blend_ppm: int,
    train_bytes: int,
    output: pathlib.Path,
) -> dict[str, Any]:
    counters: dict[tuple[Any, ...], Counter] = {}
    totals = {"train": Totals(), "test": Totals(), "all": Totals()}
    blend = max(0.0, min(1.0, blend_ppm / 1_000_000.0))

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as out:
        for row in rows:
            bit = as_int(row, "bit")
            base_p1 = max(1, min(65535, as_int(row, "p1", 32768)))
            base_qbits = as_int(row, "baseline_qbits", qbits_for(bit, base_p1))
            key = key_for(row, fields, p_buckets)
            counter = counters.setdefault(key, Counter())
            kt_p1 = counter.p1(alpha)
            corrected_p1 = base_p1 + (kt_p1 - base_p1) * blend
            corrected_qbits = qbits_for(bit, corrected_p1)
            split = split_for(row, train_bytes)

            for name in ((split,) if split == "all" else (split, "all")):
                totals[name].rows += 1
                totals[name].baseline_qbits += base_qbits
                totals[name].corrected_qbits += corrected_qbits

            payload = {
                "split": split,
                "baseline_qbits": base_qbits,
                "corrected_qbits": corrected_qbits,
                "bit_count": 1,
                "pos": as_int(row, "pos"),
                "bit_pos": as_int(row, "bit_pos"),
            }
            for field in fields:
                payload[field] = key_for(row, [field], p_buckets)[0]
            out.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
            counter.update(bit)

    return {
        "fields": fields,
        "p_buckets": p_buckets,
        "alpha": alpha,
        "blend_ppm": blend_ppm,
        "train_bytes": train_bytes,
        "unique_contexts": len(counters),
        "output": str(output),
        "splits": {
            name: {
                "rows": total.rows,
                "baseline_bits": total.baseline_qbits / 256.0,
                "corrected_bits": total.corrected_qbits / 256.0,
                "gain_bits": total.gain_bits,
                "gain_bytes": total.gain_bits / 8.0,
            }
            for name, total in totals.items()
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--summary", type=pathlib.Path)
    parser.add_argument(
        "--key",
        default="p_bucket,bit_pos,field,mode",
        help="comma-separated key fields; use p_bucket for fx2 probability bucket",
    )
    parser.add_argument("--p-buckets", type=int, default=32)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--blend-ppm", type=int, default=125000)
    parser.add_argument(
        "--train-bytes",
        type=int,
        default=0,
        help="rows with pos below this value are train; later rows are test",
    )
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if not args.log.exists():
        raise SystemExit(f"missing log: {args.log}")
    if args.p_buckets <= 0:
        raise SystemExit("--p-buckets must be positive")
    if args.alpha <= 0:
        raise SystemExit("--alpha must be positive")
    fields = [field for field in args.key.split(",") if field]
    if not fields:
        raise SystemExit("--key must include at least one field")

    summary = score(
        read_rows(args.log),
        fields=fields,
        p_buckets=args.p_buckets,
        alpha=args.alpha,
        blend_ppm=args.blend_ppm,
        train_bytes=args.train_bytes,
        output=args.output,
    )
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
