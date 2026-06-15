#!/usr/bin/env python3
"""Single-pass search for causal fx2 residual correction keys.

This is the large-log companion to fx2_residual_state_search.py. It parses each
FX2_RESIDUAL_ROW once, updates all requested candidate keys, and ranks them by
causal train/test or all-stream log-loss gain.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
from dataclasses import dataclass, field
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


def as_int(row: dict[str, Any], key: str, default: int = 0) -> int:
    value = row.get(key, default)
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def qbits_for(bit: int, p1: float) -> int:
    p1 = max(1.0, min(65535.0, p1))
    prob = p1 / 65536.0 if bit else (65536.0 - p1) / 65536.0
    return int((-math.log2(prob)) * 256.0 + 0.5)


def prob_bucket(p1: int, buckets: int) -> int:
    if buckets <= 1:
        return 0
    p1 = max(1, min(65535, p1))
    return min(buckets - 1, (p1 * buckets) >> 16)


def value_for(row: dict[str, Any], field_name: str, p_buckets: int, p1: int) -> Any:
    if field_name == "p_bucket":
        return prob_bucket(p1, p_buckets)
    if field_name == "markup_compact":
        return (
            as_int(row, "field") & 7,
            as_int(row, "mode") & 7,
            as_int(row, "in_tag") & 1,
            as_int(row, "ref") & 1,
            as_int(row, "url") & 3,
        )
    return row.get(field_name, 0)


def key_for(row: dict[str, Any], fields: tuple[str, ...], p_buckets: int, p1: int) -> tuple[Any, ...]:
    return tuple(value_for(row, item, p_buckets, p1) for item in fields)


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

    @property
    def gain_bits_per_bit(self) -> float:
        return self.gain_bits / self.rows if self.rows else 0.0


@dataclass
class Model:
    fields: tuple[str, ...]
    p_buckets: int
    blend_ppm: int
    alpha: float
    counters: dict[tuple[Any, ...], Counter] = field(default_factory=dict)
    totals: dict[str, Totals] = field(
        default_factory=lambda: {"train": Totals(), "test": Totals(), "all": Totals()}
    )

    @property
    def key_name(self) -> str:
        return ",".join(self.fields)

    def update(self, row: dict[str, Any], split: str) -> None:
        bit = as_int(row, "bit", -1)
        if bit not in {0, 1}:
            return
        base_p1 = max(1, min(65535, as_int(row, "p1", 32768)))
        base_qbits = as_int(row, "baseline_qbits", qbits_for(bit, base_p1))
        key = key_for(row, self.fields, self.p_buckets, base_p1)
        counter = self.counters.setdefault(key, Counter())
        blend = max(0.0, min(1.0, self.blend_ppm / 1_000_000.0))
        corrected_p1 = base_p1 + (counter.p1(self.alpha) - base_p1) * blend
        corrected_qbits = qbits_for(bit, corrected_p1)

        for name in (split, "all"):
            if name == "all" and split == "all":
                continue
            total = self.totals[name]
            total.rows += 1
            total.baseline_qbits += base_qbits
            total.corrected_qbits += corrected_qbits
        if split == "all":
            total = self.totals["all"]
            total.rows += 1
            total.baseline_qbits += base_qbits
            total.corrected_qbits += corrected_qbits
        counter.update(bit)

    def to_json(self) -> dict[str, Any]:
        return {
            "key": self.key_name,
            "p_buckets": self.p_buckets,
            "blend_ppm": self.blend_ppm,
            "alpha": self.alpha,
            "unique_contexts": len(self.counters),
            "splits": {
                name: {
                    "rows": total.rows,
                    "baseline_bits": total.baseline_qbits / 256.0,
                    "corrected_bits": total.corrected_qbits / 256.0,
                    "gain_bits": total.gain_bits,
                    "gain_bytes": total.gain_bits / 8.0,
                    "gain_bits_per_bit": total.gain_bits_per_bit,
                }
                for name, total in self.totals.items()
            },
        }


def default_specs() -> list[tuple[str, ...]]:
    return [
        ("p_bucket", "bit_pos"),
        ("p_bucket", "bit_pos", "mode"),
        ("p_bucket", "bit_pos", "char_class"),
        ("p_bucket", "bit_pos", "mode", "char_class"),
        ("p_bucket", "bit_pos", "field", "mode", "char_class"),
        ("p_bucket", "bit_pos", "markup_compact"),
        ("bit_pos", "mode"),
        ("bit_pos", "char_class"),
    ]


def parse_specs(values: list[str]) -> list[tuple[str, ...]]:
    if not values:
        return default_specs()
    specs: list[tuple[str, ...]] = []
    for value in values:
        fields = tuple(part for part in value.split(",") if part)
        if fields:
            specs.append(fields)
    return specs


def split_for(row: dict[str, Any], train_bytes: int) -> str:
    if train_bytes <= 0:
        return "all"
    return "train" if as_int(row, "pos") < train_bytes else "test"


def run_search(args: argparse.Namespace) -> dict[str, Any]:
    specs = parse_specs(args.spec)
    p_buckets = [int(part) for part in args.p_buckets.split(",") if part]
    blends = [int(part) for part in args.blend_ppm.split(",") if part]
    models = [
        Model(fields=spec, p_buckets=buckets, blend_ppm=blend, alpha=args.alpha)
        for spec in specs
        for buckets in p_buckets
        for blend in blends
    ]

    rows = 0
    with args.log.open("r", errors="replace") as f:
        for line in f:
            row = parse_row(line)
            if row is None:
                continue
            rows += 1
            split = split_for(row, args.train_bytes)
            for model in models:
                model.update(row, split)

    rank_split = args.rank_split
    if rank_split == "test" and args.train_bytes <= 0:
        rank_split = "all"
    ranked = [model.to_json() for model in models]
    ranked.sort(
        key=lambda item: (
            -float(item["splits"][rank_split]["gain_bits"]),
            int(item["unique_contexts"]),
            item["key"],
            int(item["p_buckets"]),
            int(item["blend_ppm"]),
        )
    )
    return {
        "log": str(args.log),
        "rows": rows,
        "train_bytes": args.train_bytes,
        "rank_split": rank_split,
        "specs_tested": len(ranked),
        "top": ranked[: args.top],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--spec", action="append", default=[])
    parser.add_argument("--p-buckets", default="32")
    parser.add_argument("--blend-ppm", default="25000,50000,125000")
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--train-bytes", type=int, default=0)
    parser.add_argument("--rank-split", choices=["all", "train", "test"], default="test")
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if not args.log.exists():
        raise SystemExit(f"missing log: {args.log}")
    payload = run_search(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        print(
            f"rows={payload['rows']} specs_tested={payload['specs_tested']} "
            f"rank_split={payload['rank_split']}"
        )
        for i, item in enumerate(payload["top"][:10], 1):
            split = item["splits"][payload["rank_split"]]
            print(
                f"{i}. key={item['key']} buckets={item['p_buckets']} "
                f"blend={item['blend_ppm']} gain_bits={split['gain_bits']:.6f} "
                f"gain_bpb={split['gain_bits_per_bit']:.9f} "
                f"contexts={item['unique_contexts']}"
            )
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
