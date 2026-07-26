#!/usr/bin/env python3
"""Certify residual-gain evidence for fx2 probability corrections.

This tool is the pathfinder counterpart to hutter_upper_bound_certificate.py.
It does not compress by itself. It checks whether a proposed causal correction
model has enough measured log-loss gain over fx2 to pay the 10.95% debt.

Input rows may be JSONL or TSV. The strongest row schema is exact per-bit data:

  baseline_qbits=<int> corrected_qbits=<int> split=<train|test>

where qbits are fixed-point bits scaled by --qbit-scale, default 256. Rows may
also provide floating losses:

  baseline_bits=<float> corrected_bits=<float>

Rows without corrected loss can still be summarized as oracle evidence when
they contain oracle_gap_qbits, but oracle rows are never marked constructive.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any, Iterable


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DEFAULT = ROOT / "residual_gain_certificate.json"

DEFAULT_BASELINE_SCORE = 110_181_114
DEFAULT_TARGET_SCORE = 109_000_000
DEFAULT_FULL_SCOPE_BYTES = 1_000_000_000

PAIR_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([^ \t]+)")


@dataclass
class GainTotals:
    rows: int = 0
    baseline_bits: float = 0.0
    corrected_bits: float = 0.0
    gain_bits: float = 0.0
    oracle_gap_bits: float = 0.0
    covered_bits: int = 0

    def add_exact(self, baseline_bits: float, corrected_bits: float, bit_count: int) -> None:
        self.rows += 1
        self.baseline_bits += baseline_bits
        self.corrected_bits += corrected_bits
        self.gain_bits += baseline_bits - corrected_bits
        self.covered_bits += bit_count

    def add_oracle(self, oracle_gap_bits: float, bit_count: int) -> None:
        self.rows += 1
        self.oracle_gap_bits += max(0.0, oracle_gap_bits)
        self.covered_bits += bit_count


def parse_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def parse_line(line: str, header: list[str] | None = None) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None
    if line.startswith("{"):
        data = json.loads(line)
        return data if isinstance(data, dict) else None
    if header is not None:
        values = next(csv.reader([line], delimiter="\t"))
        return {
            key: parse_value(value)
            for key, value in zip(header, values)
            if key
        }
    pairs = PAIR_RE.findall(line)
    if pairs:
        return {key: parse_value(value) for key, value in pairs}
    return None


def iter_rows(path: pathlib.Path) -> Iterable[dict[str, Any]]:
    with path.open("r", errors="replace", newline="") as f:
        first_data_line = True
        header: list[str] | None = None
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if first_data_line and "\t" in stripped and "=" not in stripped and not stripped.startswith("{"):
                header = next(csv.reader([stripped], delimiter="\t"))
                first_data_line = False
                continue
            first_data_line = False
            row = parse_line(stripped, header)
            if row is not None:
                yield row


def number(row: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = row.get(key)
        if isinstance(value, bool) or value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def split_name(row: dict[str, Any], default: str) -> str:
    value = row.get("split", default)
    if not isinstance(value, str):
        return default
    normalized = value.lower()
    if normalized in {"train", "test", "holdout", "validation", "val", "all"}:
        return "test" if normalized in {"holdout", "validation", "val"} else normalized
    return default


def row_bit_count(row: dict[str, Any]) -> int:
    value = number(row, "bit_count", "bits_covered", "weight", "ledger_stride")
    if value is None:
        return 1
    return max(1, int(value))


def accumulate(
    rows: Iterable[dict[str, Any]],
    qbit_scale: int,
    default_split: str,
) -> tuple[dict[str, GainTotals], dict[str, int]]:
    totals: dict[str, GainTotals] = {
        "train": GainTotals(),
        "test": GainTotals(),
        "all": GainTotals(),
    }
    counters = {
        "rows": 0,
        "exact_rows": 0,
        "oracle_rows": 0,
        "ignored_rows": 0,
    }
    for row in rows:
        counters["rows"] += 1
        split = split_name(row, default_split)
        if split not in totals:
            split = default_split
        bit_count = row_bit_count(row)

        baseline_qbits = number(row, "baseline_qbits", "fx2_qbits", "qbits")
        corrected_qbits = number(row, "corrected_qbits", "residual_qbits")
        baseline_bits = number(row, "baseline_bits", "fx2_bits")
        corrected_bits = number(row, "corrected_bits", "residual_bits")

        if baseline_qbits is not None and corrected_qbits is not None:
            base = baseline_qbits / qbit_scale
            corr = corrected_qbits / qbit_scale
            for name in ((split,) if split == "all" else (split, "all")):
                totals[name].add_exact(base, corr, bit_count)
            counters["exact_rows"] += 1
            continue
        if baseline_bits is not None and corrected_bits is not None:
            for name in ((split,) if split == "all" else (split, "all")):
                totals[name].add_exact(baseline_bits, corrected_bits, bit_count)
            counters["exact_rows"] += 1
            continue

        oracle_qbits = number(row, "oracle_gap_qbits")
        oracle_bits = number(row, "oracle_gap_bits")
        if oracle_qbits is not None:
            gap = oracle_qbits / qbit_scale
            for name in ((split,) if split == "all" else (split, "all")):
                totals[name].add_oracle(gap, bit_count)
            counters["oracle_rows"] += 1
            continue
        if oracle_bits is not None:
            for name in ((split,) if split == "all" else (split, "all")):
                totals[name].add_oracle(oracle_bits, bit_count)
            counters["oracle_rows"] += 1
            continue
        counters["ignored_rows"] += 1
    return totals, counters


def totals_record(total: GainTotals) -> dict[str, Any]:
    return {
        "rows": total.rows,
        "covered_bits": total.covered_bits,
        "covered_bytes": total.covered_bits / 8.0,
        "baseline_bits": total.baseline_bits,
        "corrected_bits": total.corrected_bits,
        "gain_bits": total.gain_bits,
        "gain_bytes": total.gain_bits / 8.0,
        "oracle_gap_bits": total.oracle_gap_bits,
        "oracle_gap_bytes": total.oracle_gap_bits / 8.0,
        "gain_bits_per_bit": total.gain_bits / total.covered_bits
        if total.covered_bits
        else 0.0,
        "oracle_gap_bits_per_bit": total.oracle_gap_bits / total.covered_bits
        if total.covered_bits
        else 0.0,
    }


def build_certificate(
    log: pathlib.Path,
    totals: dict[str, GainTotals],
    counters: dict[str, int],
    baseline_score: int,
    target_score: int,
    scope_bytes: int,
    patch_bytes: int,
    table_bits: int,
    full_coverage: bool,
    split_for_gate: str,
) -> dict[str, Any]:
    required_gain_bits = (baseline_score - target_score) * 8
    code_cost_bits = patch_bytes * 8 + table_bits
    gate_total = totals.get(split_for_gate, GainTotals())
    measured_net_gain_bits = gate_total.gain_bits - code_cost_bits
    scope_bits = scope_bytes * 8
    coverage_fraction = (
        min(1.0, gate_total.covered_bits / scope_bits) if scope_bits else 0.0
    )
    projected_gain_bits = (
        gate_total.gain_bits / gate_total.covered_bits * scope_bits
        if gate_total.covered_bits
        else 0.0
    )
    projected_net_gain_bits = projected_gain_bits - code_cost_bits
    has_exact_residual = counters["exact_rows"] > 0
    constructive_residual_certificate = (
        has_exact_residual
        and full_coverage
        and gate_total.covered_bits >= scope_bits
        and measured_net_gain_bits >= required_gain_bits
    )
    projected_pass = (
        has_exact_residual
        and gate_total.covered_bits > 0
        and projected_net_gain_bits >= required_gain_bits
    )

    return {
        "theorem": (
            "For a causal decoder-realizable correction model with measured "
            "per-bit corrected loss, L_new <= L_fx2 - residual_gain + model_cost. "
            "The inequality is constructive only when rows cover the full target "
            "stream with exact baseline and corrected losses."
        ),
        "input_log": str(log),
        "row_counters": counters,
        "target": {
            "baseline_score": baseline_score,
            "target_score": target_score,
            "required_net_gain_bytes": baseline_score - target_score,
            "required_gain_bits": required_gain_bits,
            "scope_bytes": scope_bytes,
            "scope_bits": scope_bits,
            "required_gain_bits_per_bit": required_gain_bits / scope_bits
            if scope_bits
            else math.inf,
        },
        "model_cost": {
            "patch_bytes": patch_bytes,
            "table_bits": table_bits,
            "total_code_cost_bits": code_cost_bits,
            "total_code_cost_bytes": code_cost_bits / 8.0,
        },
        "gate": {
            "split": split_for_gate,
            "full_coverage_asserted": full_coverage,
            "coverage_fraction": coverage_fraction,
            "constructive_residual_certificate": constructive_residual_certificate,
            "projected_pass_non_proof": projected_pass,
            "measured_net_gain_bits": measured_net_gain_bits,
            "measured_net_gain_bytes": measured_net_gain_bits / 8.0,
            "projected_net_gain_bits": projected_net_gain_bits,
            "projected_net_gain_bytes": projected_net_gain_bits / 8.0,
            "notes": [
                "Projected pass is not a proof unless full coverage is asserted and present.",
                "Oracle-gap rows are attribution evidence only; they do not certify a decoder.",
                "Exact residual rows must come from a causal model updated only after decoded bits.",
            ],
        },
        "splits": {name: totals_record(total) for name, total in totals.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, default=OUT_DEFAULT)
    parser.add_argument("--baseline-score", type=int, default=DEFAULT_BASELINE_SCORE)
    parser.add_argument("--target-score", type=int, default=DEFAULT_TARGET_SCORE)
    parser.add_argument("--scope-bytes", type=int, default=DEFAULT_FULL_SCOPE_BYTES)
    parser.add_argument("--patch-bytes", type=int, default=0)
    parser.add_argument("--table-bits", type=int, default=0)
    parser.add_argument("--qbit-scale", type=int, default=256)
    parser.add_argument("--default-split", choices=["train", "test", "all"], default="test")
    parser.add_argument("--gate-split", choices=["train", "test", "all"], default="test")
    parser.add_argument(
        "--full-coverage",
        action="store_true",
        help="assert the log covers the whole target stream for the gate split",
    )
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if args.qbit_scale <= 0:
        raise SystemExit("--qbit-scale must be positive")
    if args.patch_bytes < 0:
        raise SystemExit("--patch-bytes must be non-negative")
    if args.table_bits < 0:
        raise SystemExit("--table-bits must be non-negative")
    if args.baseline_score < args.target_score:
        raise SystemExit("--baseline-score must be >= --target-score")
    if not args.log.exists():
        raise SystemExit(f"missing log: {args.log}")

    totals, counters = accumulate(
        iter_rows(args.log),
        qbit_scale=args.qbit_scale,
        default_split=args.default_split,
    )
    cert = build_certificate(
        log=args.log,
        totals=totals,
        counters=counters,
        baseline_score=args.baseline_score,
        target_score=args.target_score,
        scope_bytes=args.scope_bytes,
        patch_bytes=args.patch_bytes,
        table_bits=args.table_bits,
        full_coverage=args.full_coverage,
        split_for_gate=args.gate_split,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(cert, indent=2, sort_keys=True) + "\n")

    if args.print_summary:
        gate = cert["gate"]
        target = cert["target"]
        split = cert["splits"][args.gate_split]
        print(f"rows={counters['rows']} exact_rows={counters['exact_rows']} oracle_rows={counters['oracle_rows']}")
        print(f"gate_split={args.gate_split} covered_bits={split['covered_bits']}")
        print(f"gain_bits={split['gain_bits']:.6f} gain_bytes={split['gain_bytes']:.6f}")
        print(f"required_gain_bits={target['required_gain_bits']}")
        print(f"measured_net_gain_bits={gate['measured_net_gain_bits']:.6f}")
        print(f"projected_net_gain_bits={gate['projected_net_gain_bits']:.6f}")
        print(f"constructive_residual_certificate={gate['constructive_residual_certificate']}")
        print(f"projected_pass_non_proof={gate['projected_pass_non_proof']}")
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
