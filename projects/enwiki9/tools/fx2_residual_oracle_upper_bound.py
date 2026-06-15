#!/usr/bin/env python3
"""Oracle upper-bound scan for fx2 residual structural states.

This tool is intentionally non-constructive: it assumes a perfect per-state
calibration table after seeing the scored rows. If a state family cannot clear
the target under this optimistic bound, its causal implementation should be
pruned before writing more candidate wrappers.
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
    return {key: parse_value(value) for key, value in pairs} if pairs else None


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


def value_for(row: dict[str, Any], field: str, p_buckets: int, p1: int) -> Any:
    if field == "p_bucket":
        return prob_bucket(p1, p_buckets)
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
class Bucket:
    zeros: int = 0
    ones: int = 0
    baseline_qbits: int = 0

    def update(self, bit: int, baseline_qbits: int) -> None:
        if bit:
            self.ones += 1
        else:
            self.zeros += 1
        self.baseline_qbits += baseline_qbits

    @property
    def rows(self) -> int:
        return self.zeros + self.ones

    def oracle_bits(self) -> float:
        total = self.rows
        if total == 0 or self.zeros == 0 or self.ones == 0:
            return 0.0
        p0 = self.zeros / total
        p1 = self.ones / total
        return -self.zeros * math.log2(p0) - self.ones * math.log2(p1)


@dataclass
class Model:
    fields: tuple[str, ...]
    p_buckets: int
    table_bits_per_state: int
    buckets: dict[tuple[Any, ...], Bucket] = field(default_factory=dict)
    rows: int = 0

    @property
    def key_name(self) -> str:
        return ",".join(self.fields)

    def update(self, row: dict[str, Any]) -> None:
        bit = as_int(row, "bit", -1)
        if bit not in {0, 1}:
            return
        p1 = max(1, min(65535, as_int(row, "p1", 32768)))
        baseline_qbits = as_int(row, "baseline_qbits", 0)
        key = key_for(row, self.fields, self.p_buckets, p1)
        self.buckets.setdefault(key, Bucket()).update(bit, baseline_qbits)
        self.rows += 1

    def result(self, scope_bits: int, required_bits: int) -> dict[str, Any]:
        baseline_bits = sum(bucket.baseline_qbits for bucket in self.buckets.values()) / 256.0
        oracle_bits = sum(bucket.oracle_bits() for bucket in self.buckets.values())
        table_cost_bits = len(self.buckets) * self.table_bits_per_state
        gain_bits = baseline_bits - oracle_bits
        net_bits = gain_bits - table_cost_bits
        projected_net_bits = (net_bits / self.rows * scope_bits) if self.rows else 0.0
        return {
            "key": self.key_name,
            "p_buckets": self.p_buckets,
            "rows": self.rows,
            "unique_contexts": len(self.buckets),
            "baseline_bits": baseline_bits,
            "oracle_bits": oracle_bits,
            "oracle_gain_bits": gain_bits,
            "table_cost_bits": table_cost_bits,
            "net_bits": net_bits,
            "net_bits_per_bit": net_bits / self.rows if self.rows else 0.0,
            "projected_net_bits": projected_net_bits,
            "projected_net_bytes": projected_net_bits / 8.0,
            "projected_clears_target": projected_net_bits >= required_bits,
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--spec", action="append", default=[])
    parser.add_argument("--p-buckets", default="32")
    parser.add_argument("--scope-bits", type=int, default=8_000_000_000)
    parser.add_argument("--required-bits", type=int, default=5_448_912)
    parser.add_argument("--table-bits-per-state", type=int, default=16)
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if not args.log.exists():
        raise SystemExit(f"missing log: {args.log}")

    specs = parse_specs(args.spec)
    p_buckets = [int(part) for part in args.p_buckets.split(",") if part]
    models = [
        Model(fields=spec, p_buckets=buckets, table_bits_per_state=args.table_bits_per_state)
        for spec in specs
        for buckets in p_buckets
    ]

    rows = 0
    with args.log.open("r", errors="replace") as f:
        for line in f:
            row = parse_row(line)
            if row is None:
                continue
            rows += 1
            for model in models:
                model.update(row)

    results = [model.result(args.scope_bits, args.required_bits) for model in models]
    results.sort(
        key=lambda item: (
            -float(item["projected_net_bits"]),
            int(item["unique_contexts"]),
            item["key"],
            int(item["p_buckets"]),
        )
    )
    payload = {
        "log": str(args.log),
        "rows": rows,
        "scope_bits": args.scope_bits,
        "required_bits": args.required_bits,
        "table_bits_per_state": args.table_bits_per_state,
        "specs_tested": len(results),
        "top": results[: args.top],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    if args.print_summary:
        print(f"rows={rows} specs_tested={len(results)}")
        for i, item in enumerate(payload["top"][:10], 1):
            print(
                f"{i}. key={item['key']} buckets={item['p_buckets']} "
                f"oracle_gain_bits={item['oracle_gain_bits']:.3f} "
                f"net_bits={item['net_bits']:.3f} "
                f"projected_bytes={item['projected_net_bytes']:.1f} "
                f"contexts={item['unique_contexts']} "
                f"clears={item['projected_clears_target']}"
            )
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
