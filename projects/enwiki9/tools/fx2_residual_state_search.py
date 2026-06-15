#!/usr/bin/env python3
"""Search causal fx2 residual correction keys on FX2_RESIDUAL_ROW logs.

The search model matches fx2_residual_apm_score.py: for each bit, predict from
the current table state, score the bit, then update the table. This is an online
decoder-realizable search, not an offline oracle.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
from dataclasses import dataclass
from typing import Any, Iterable


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


def read_rows(path: pathlib.Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", errors="replace") as f:
        for line in f:
            row = parse_row(line)
            if row is not None:
                rows.append(row)
    rows.sort(key=lambda row: (as_int(row, "pos"), as_int(row, "bit_pos")))
    return rows


def as_int(row: dict[str, Any], key: str, default: int = 0) -> int:
    value = row.get(key, default)
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clamp_p1(p1: float) -> float:
    return max(1.0, min(65535.0, float(p1)))


def qbits_for(bit: int, p1: float) -> int:
    p1 = clamp_p1(p1)
    prob = p1 / 65536.0 if bit else (65536.0 - p1) / 65536.0
    return int((-math.log2(prob)) * 256.0 + 0.5)


def prob_bucket(p1: int, buckets: int) -> int:
    if buckets <= 1:
        return 0
    p1 = max(1, min(65535, p1))
    return min(buckets - 1, (p1 * buckets) >> 16)


def value_for(row: dict[str, Any], field: str, p_buckets: int, p1: int) -> Any:
    if field == "p_bucket":
        return prob_bucket(p1, p_buckets)
    if field == "byte_region":
        pos = as_int(row, "pos")
        if pos < 4096:
            return 0
        if pos < 65536:
            return 1
        if pos < 1_000_000:
            return 2
        if pos < 10_000_000:
            return 3
        return 4
    if field == "markup_compact":
        return (
            as_int(row, "field") & 7,
            as_int(row, "mode") & 7,
            as_int(row, "in_tag") & 1,
            as_int(row, "ref") & 1,
            as_int(row, "url") & 3,
        )
    return row.get(field, 0)


def key_for(row: dict[str, Any], fields: tuple[str, ...], p_buckets: int, p1: int) -> tuple[Any, ...]:
    return tuple(value_for(row, field, p_buckets, p1) for field in fields)


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


def split_name(row: dict[str, Any], train_bytes: int) -> str:
    if train_bytes <= 0:
        return "all"
    return "train" if as_int(row, "pos") < train_bytes else "test"


def score_spec(
    rows: Iterable[dict[str, Any]],
    fields: tuple[str, ...],
    p_buckets: int,
    blend_ppm: int,
    alpha: float,
    train_bytes: int,
) -> dict[str, Any]:
    counters: dict[tuple[Any, ...], Counter] = {}
    totals = {"train": Totals(), "test": Totals(), "all": Totals()}
    blend = max(0.0, min(1.0, blend_ppm / 1_000_000.0))

    for row in rows:
        bit = as_int(row, "bit", -1)
        if bit not in {0, 1}:
            continue
        base_p1 = max(1, min(65535, as_int(row, "p1", 32768)))
        base_qbits = as_int(row, "baseline_qbits", qbits_for(bit, base_p1))
        key = key_for(row, fields, p_buckets, base_p1)
        counter = counters.setdefault(key, Counter())
        kt_p1 = counter.p1(alpha)
        corrected_p1 = base_p1 + (kt_p1 - base_p1) * blend
        corrected_qbits = qbits_for(bit, corrected_p1)
        split = split_name(row, train_bytes)
        for name in ((split,) if split == "all" else (split, "all")):
            totals[name].rows += 1
            totals[name].baseline_qbits += base_qbits
            totals[name].corrected_qbits += corrected_qbits
        counter.update(bit)

    return {
        "key": ",".join(fields),
        "p_buckets": p_buckets,
        "blend_ppm": blend_ppm,
        "alpha": alpha,
        "unique_contexts": len(counters),
        "splits": {
            name: {
                "rows": total.rows,
                "baseline_bits": total.baseline_qbits / 256.0,
                "corrected_bits": total.corrected_qbits / 256.0,
                "gain_bits": total.gain_bits,
                "gain_bytes": total.gain_bits / 8.0,
                "gain_bits_per_bit": total.gain_bits / total.rows if total.rows else 0.0,
            }
            for name, total in totals.items()
        },
    }


def default_specs() -> list[tuple[str, ...]]:
    return [
        ("p_bucket", "bit_pos"),
        ("p_bucket", "bit_pos", "field"),
        ("p_bucket", "bit_pos", "mode"),
        ("p_bucket", "bit_pos", "field", "mode"),
        ("p_bucket", "bit_pos", "slot"),
        ("p_bucket", "bit_pos", "char_class"),
        ("p_bucket", "bit_pos", "number_class"),
        ("p_bucket", "bit_pos", "word_len"),
        ("p_bucket", "bit_pos", "col_bucket"),
        ("p_bucket", "bit_pos", "template_depth"),
        ("p_bucket", "bit_pos", "in_tag"),
        ("p_bucket", "bit_pos", "ref"),
        ("p_bucket", "bit_pos", "url"),
        ("p_bucket", "bit_pos", "field", "slot"),
        ("p_bucket", "bit_pos", "field", "char_class"),
        ("p_bucket", "bit_pos", "mode", "char_class"),
        ("p_bucket", "bit_pos", "markup_compact"),
        ("p_bucket", "bit_pos", "byte_region"),
        ("bit_pos", "field"),
        ("bit_pos", "mode"),
        ("bit_pos", "char_class"),
        ("bit_pos", "markup_compact"),
    ]


def parse_specs(values: list[str]) -> list[tuple[str, ...]]:
    if not values:
        return default_specs()
    specs: list[tuple[str, ...]] = []
    for value in values:
        fields = tuple(field for field in value.split(",") if field)
        if fields:
            specs.append(fields)
    return specs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--spec", action="append", default=[])
    parser.add_argument("--p-buckets", default="16,32,64")
    parser.add_argument("--blend-ppm", default="31250,62500,125000,250000")
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--train-bytes", type=int, default=0)
    parser.add_argument("--rank-split", choices=["all", "train", "test"], default="test")
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if not args.log.exists():
        raise SystemExit(f"missing log: {args.log}")
    rows = read_rows(args.log)
    if not rows:
        raise SystemExit("no FX2_RESIDUAL_ROW rows found")

    specs = parse_specs(args.spec)
    p_buckets = [int(part) for part in args.p_buckets.split(",") if part]
    blends = [int(part) for part in args.blend_ppm.split(",") if part]
    rank_split = args.rank_split
    if rank_split == "test" and args.train_bytes <= 0:
        rank_split = "all"

    results: list[dict[str, Any]] = []
    for spec in specs:
        for buckets in p_buckets:
            for blend in blends:
                row = score_spec(
                    rows,
                    fields=spec,
                    p_buckets=buckets,
                    blend_ppm=blend,
                    alpha=args.alpha,
                    train_bytes=args.train_bytes,
                )
                results.append(row)

    results.sort(
        key=lambda row: (
            -float(row["splits"][rank_split]["gain_bits"]),
            int(row["unique_contexts"]),
            row["key"],
            int(row["blend_ppm"]),
        )
    )
    payload = {
        "log": str(args.log),
        "rows": len(rows),
        "train_bytes": args.train_bytes,
        "rank_split": rank_split,
        "specs_tested": len(results),
        "top": results[: args.top],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        print(f"rows={len(rows)} specs_tested={len(results)} rank_split={rank_split}")
        for i, row in enumerate(results[: min(args.top, 10)], 1):
            split = row["splits"][rank_split]
            print(
                f"{i}. key={row['key']} buckets={row['p_buckets']} "
                f"blend={row['blend_ppm']} gain_bits={split['gain_bits']:.6f} "
                f"gain_bpb={split['gain_bits_per_bit']:.9f} contexts={row['unique_contexts']}"
            )
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
