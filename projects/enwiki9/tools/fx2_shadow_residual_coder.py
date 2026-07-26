#!/usr/bin/env python3
"""Exact shadow-coder certificate for causal fx2 residual corrections.

This is stricter than a log-loss ledger. Given per-bit fx2 residual rows, it
drives a deterministic binary arithmetic coder with corrected causal
probabilities and reports the exact byte count that this proposed coder emits.

Rows can be JSONL, TSV, key=value lines, or FX2_RESIDUAL_ROW logs. Required row
fields are:

  bit=<0|1> p1=<1..65535>

If corrected_p1 is present, it is used directly. Otherwise the tool builds a
tiny adaptive KT-style table keyed by --key and blends it with p1. The table is
updated only after the current bit is encoded, so the model is decoder-realizable.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
from dataclasses import dataclass
from typing import Any, Iterable


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DEFAULT = ROOT / "shadow_residual_coder_certificate.json"

DEFAULT_BASELINE_SCORE = 110_181_114
DEFAULT_TARGET_SCORE = 108_000_000
DEFAULT_SCOPE_BYTES = 1_000_000_000

PAIR_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([^ \t]+)")
FX2_PREFIX = "FX2_RESIDUAL_ROW "
TOTAL = 1 << 16
MAX_CODE = (1 << 32) - 1
HALF = 1 << 31
FIRST_QTR = 1 << 30
THIRD_QTR = FIRST_QTR * 3


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
    if not line or line.startswith("#"):
        return None
    if FX2_PREFIX in line:
        line = line.split(FX2_PREFIX, 1)[1]
    if line.startswith("{"):
        data = json.loads(line)
        return data if isinstance(data, dict) else None
    if header is not None:
        values = next(csv.reader([line], delimiter="\t"))
        return {key: parse_value(value) for key, value in zip(header, values) if key}
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
            if (
                first_data_line
                and "\t" in stripped
                and "=" not in stripped
                and not stripped.startswith("{")
            ):
                header = next(csv.reader([stripped], delimiter="\t"))
                first_data_line = False
                continue
            first_data_line = False
            row = parse_line(stripped, header)
            if row is not None:
                yield row


def as_int(row: dict[str, Any], *keys: str, default: int = 0) -> int:
    for key in keys:
        value = row.get(key)
        if isinstance(value, bool) or value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return default


def clamp_p1(p1: int) -> int:
    return max(1, min(TOTAL - 1, int(p1)))


def prob_bucket(p1: int, buckets: int) -> int:
    if buckets <= 1:
        return 0
    return min(buckets - 1, (clamp_p1(p1) * buckets) >> 16)


def key_for(row: dict[str, Any], fields: list[str], p_buckets: int, p1: int) -> tuple[Any, ...]:
    out: list[Any] = []
    for field in fields:
        if field == "p_bucket":
            out.append(prob_bucket(p1, p_buckets))
        else:
            out.append(row.get(field, 0))
    return tuple(out)


class BitCounter:
    def __init__(self) -> None:
        self.bits = 0

    def write_bit(self, _bit: int) -> None:
        self.bits += 1

    @property
    def bytes(self) -> int:
        return (self.bits + 7) // 8


class BinaryArithmeticEncoder:
    """Classic 32-bit binary arithmetic encoder with bit-level output."""

    def __init__(self) -> None:
        self.low = 0
        self.high = MAX_CODE
        self.pending = 0
        self.out = BitCounter()

    def _bit_plus_follow(self, bit: int) -> None:
        self.out.write_bit(bit)
        while self.pending:
            self.out.write_bit(1 - bit)
            self.pending -= 1

    def encode(self, bit: int, p1: int) -> None:
        p1 = clamp_p1(p1)
        zeros = TOTAL - p1
        span = self.high - self.low + 1
        split = self.low + (span * zeros) // TOTAL
        if bit:
            self.low = split
        else:
            self.high = split - 1

        while True:
            if self.high < HALF:
                self._bit_plus_follow(0)
            elif self.low >= HALF:
                self._bit_plus_follow(1)
                self.low -= HALF
                self.high -= HALF
            elif self.low >= FIRST_QTR and self.high < THIRD_QTR:
                self.pending += 1
                self.low -= FIRST_QTR
                self.high -= FIRST_QTR
            else:
                break
            self.low = (self.low << 1) & MAX_CODE
            self.high = ((self.high << 1) & MAX_CODE) | 1

    def finish(self) -> None:
        self.pending += 1
        if self.low < FIRST_QTR:
            self._bit_plus_follow(0)
        else:
            self._bit_plus_follow(1)

    @property
    def bit_count(self) -> int:
        return self.out.bits

    @property
    def byte_count(self) -> int:
        return self.out.bytes


@dataclass
class Counter:
    zeros: int = 0
    ones: int = 0

    def kt_p1(self) -> int:
        # Exact KT alpha=1/2 estimate:
        # P(1) = (ones + 1/2) / (zeros + ones + 1).
        denom = 2 * (self.zeros + self.ones + 1)
        numer = (2 * self.ones + 1) * TOTAL
        return clamp_p1(numer // denom)

    def update(self, bit: int) -> None:
        if bit:
            self.ones += 1
        else:
            self.zeros += 1


@dataclass
class RunStats:
    rows: int = 0
    encoded_rows: int = 0
    ignored_rows: int = 0
    corrected_p1_rows: int = 0
    adaptive_rows: int = 0
    min_pos: int | None = None
    max_pos: int | None = None

    def add_pos(self, pos: int) -> None:
        self.min_pos = pos if self.min_pos is None else min(self.min_pos, pos)
        self.max_pos = pos if self.max_pos is None else max(self.max_pos, pos)


def corrected_probability(
    row: dict[str, Any],
    counters: dict[tuple[Any, ...], Counter],
    fields: list[str],
    p_buckets: int,
    blend_ppm: int,
    base_p1: int,
    stats: RunStats,
) -> tuple[int, Counter | None]:
    explicit = as_int(
        row,
        "corrected_p1",
        "shadow_p1",
        "residual_p1",
        "p1_corrected",
        default=-1,
    )
    if explicit > 0:
        stats.corrected_p1_rows += 1
        return clamp_p1(explicit), None

    key = key_for(row, fields, p_buckets, base_p1)
    counter = counters.setdefault(key, Counter())
    kt_p1 = counter.kt_p1()
    blend_ppm = max(0, min(1_000_000, blend_ppm))
    p1 = (base_p1 * (1_000_000 - blend_ppm) + kt_p1 * blend_ppm) // 1_000_000
    stats.adaptive_rows += 1
    return clamp_p1(p1), counter


def encode_shadow(
    rows: Iterable[dict[str, Any]],
    fields: list[str],
    p_buckets: int,
    blend_ppm: int,
) -> tuple[dict[str, Any], dict[tuple[Any, ...], Counter]]:
    baseline = BinaryArithmeticEncoder()
    shadow = BinaryArithmeticEncoder()
    counters: dict[tuple[Any, ...], Counter] = {}
    stats = RunStats()

    for row in rows:
        stats.rows += 1
        bit_raw = as_int(row, "bit", "actual_bit", default=-1)
        if bit_raw not in {0, 1}:
            stats.ignored_rows += 1
            continue
        bit = int(bit_raw)
        base_p1 = clamp_p1(as_int(row, "p1", "fx2_p1", "probability", default=32768))
        corrected_p1, counter = corrected_probability(
            row,
            counters,
            fields,
            p_buckets,
            blend_ppm,
            base_p1,
            stats,
        )

        baseline.encode(bit, base_p1)
        shadow.encode(bit, corrected_p1)
        if counter is not None:
            counter.update(bit)

        stats.encoded_rows += 1
        pos = as_int(row, "pos", "position", default=-1)
        if pos >= 0:
            stats.add_pos(pos)

    baseline.finish()
    shadow.finish()

    summary = {
        "row_counters": {
            "rows": stats.rows,
            "encoded_rows": stats.encoded_rows,
            "ignored_rows": stats.ignored_rows,
            "corrected_p1_rows": stats.corrected_p1_rows,
            "adaptive_rows": stats.adaptive_rows,
            "unique_contexts": len(counters),
        },
        "position_span": {
            "min_pos": stats.min_pos,
            "max_pos": stats.max_pos,
        },
        "baseline_same_coder": {
            "encoded_bits": baseline.bit_count,
            "archive_bytes": baseline.byte_count,
        },
        "shadow_coder": {
            "encoded_bits": shadow.bit_count,
            "archive_bytes": shadow.byte_count,
        },
        "same_coder_delta": {
            "saved_bits": baseline.bit_count - shadow.bit_count,
            "saved_bytes": baseline.byte_count - shadow.byte_count,
        },
    }
    return summary, counters


def build_certificate(
    *,
    log: pathlib.Path,
    coder_summary: dict[str, Any],
    fields: list[str],
    p_buckets: int,
    blend_ppm: int,
    baseline_score: int,
    target_score: int,
    scope_bytes: int,
    fx2_decoder_bytes: int | None,
    patch_bytes: int,
    table_bytes: int,
    full_coverage: bool,
) -> dict[str, Any]:
    encoded_rows = int(coder_summary["row_counters"]["encoded_rows"])
    scope_bits = scope_bytes * 8
    shadow_archive_bytes = int(coder_summary["shadow_coder"]["archive_bytes"])
    decoder_bytes_known = fx2_decoder_bytes is not None
    score_upper_bound = (
        shadow_archive_bytes + fx2_decoder_bytes + patch_bytes + table_bytes
        if decoder_bytes_known
        else None
    )
    coverage_fraction = min(1.0, encoded_rows / scope_bits) if scope_bits else 0.0
    constructive = (
        decoder_bytes_known
        and full_coverage
        and encoded_rows >= scope_bits
        and score_upper_bound is not None
        and score_upper_bound <= target_score
    )
    projected_archive_bytes = (
        int(round(shadow_archive_bytes * scope_bits / encoded_rows))
        if encoded_rows
        else None
    )
    projected_score = (
        projected_archive_bytes + fx2_decoder_bytes + patch_bytes + table_bytes
        if projected_archive_bytes is not None and decoder_bytes_known
        else None
    )

    return {
        "theorem": (
            "Given corpus x, decoder D', and shadow encoder E' using only causal "
            "state, if E'(x) emits archive A' and D'(A') = x, then |A'| + |D'| "
            "is a constructive upper bound. This tool certifies that theorem only "
            "when the trace covers the asserted target stream and decoder bytes "
            "are counted."
        ),
        "input_log": str(log),
        "model": {
            "name": "fx2_shadow_residual_coder_v1",
            "key_fields": fields,
            "p_buckets": p_buckets,
            "blend_ppm": blend_ppm,
            "correction": (
                "explicit corrected_p1 rows when present; otherwise causal KT "
                "counts blended with fx2 p1 and updated after each bit"
            ),
            "arithmetic_coder": "deterministic 32-bit binary arithmetic coder",
        },
        "target": {
            "baseline_score": baseline_score,
            "target_score": target_score,
            "required_net_gain_bytes": baseline_score - target_score,
            "required_net_gain_bits": (baseline_score - target_score) * 8,
            "scope_bytes": scope_bytes,
            "scope_bits": scope_bits,
        },
        "decoder_cost": {
            "fx2_decoder_bytes": fx2_decoder_bytes,
            "patch_bytes": patch_bytes,
            "table_bytes": table_bytes,
            "decoder_bytes_known": decoder_bytes_known,
        },
        "coverage": {
            "full_coverage_asserted": full_coverage,
            "encoded_bits_from_trace": encoded_rows,
            "coverage_fraction": coverage_fraction,
        },
        "exact_shadow_arithmetic": coder_summary,
        "score_upper_bound": {
            "candidate_score": score_upper_bound,
            "beats_target": bool(
                score_upper_bound is not None and score_upper_bound <= target_score
            ),
            "constructive_10_95_certificate": constructive,
            "projected_archive_bytes_non_proof": projected_archive_bytes,
            "projected_score_non_proof": projected_score,
            "projected_beats_target_non_proof": bool(
                projected_score is not None and projected_score <= target_score
            ),
            "notes": [
                "Projection is not a proof.",
                "A constructive proof requires full coverage and counted decoder bytes.",
                "The correction model is causal: counters update only after the current bit.",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, default=OUT_DEFAULT)
    parser.add_argument(
        "--key",
        default="p_bucket,bit_pos,field,mode",
        help="comma-separated key fields; p_bucket is derived from p1",
    )
    parser.add_argument("--p-buckets", type=int, default=32)
    parser.add_argument("--blend-ppm", type=int, default=125000)
    parser.add_argument("--baseline-score", type=int, default=DEFAULT_BASELINE_SCORE)
    parser.add_argument("--target-score", type=int, default=DEFAULT_TARGET_SCORE)
    parser.add_argument("--scope-bytes", type=int, default=DEFAULT_SCOPE_BYTES)
    parser.add_argument("--fx2-decoder-bytes", type=int)
    parser.add_argument("--patch-bytes", type=int, default=0)
    parser.add_argument("--table-bytes", type=int, default=0)
    parser.add_argument(
        "--full-coverage",
        action="store_true",
        help="assert the trace covers the full --scope-bytes stream bit-by-bit",
    )
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if not args.log.exists():
        raise SystemExit(f"missing log: {args.log}")
    if args.p_buckets <= 0:
        raise SystemExit("--p-buckets must be positive")
    if args.scope_bytes <= 0:
        raise SystemExit("--scope-bytes must be positive")
    if args.baseline_score < args.target_score:
        raise SystemExit("--baseline-score must be >= --target-score")
    if args.fx2_decoder_bytes is not None and args.fx2_decoder_bytes < 0:
        raise SystemExit("--fx2-decoder-bytes must be non-negative")
    if args.patch_bytes < 0 or args.table_bytes < 0:
        raise SystemExit("--patch-bytes and --table-bytes must be non-negative")

    fields = [field for field in args.key.split(",") if field]
    if not fields:
        raise SystemExit("--key must include at least one field")

    coder_summary, _counters = encode_shadow(
        iter_rows(args.log),
        fields=fields,
        p_buckets=args.p_buckets,
        blend_ppm=args.blend_ppm,
    )
    cert = build_certificate(
        log=args.log,
        coder_summary=coder_summary,
        fields=fields,
        p_buckets=args.p_buckets,
        blend_ppm=args.blend_ppm,
        baseline_score=args.baseline_score,
        target_score=args.target_score,
        scope_bytes=args.scope_bytes,
        fx2_decoder_bytes=args.fx2_decoder_bytes,
        patch_bytes=args.patch_bytes,
        table_bytes=args.table_bytes,
        full_coverage=args.full_coverage,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(cert, indent=2, sort_keys=True) + "\n")

    if args.print_summary:
        exact = cert["exact_shadow_arithmetic"]
        score = cert["score_upper_bound"]
        print(f"encoded_rows={exact['row_counters']['encoded_rows']}")
        print(f"shadow_archive_bytes={exact['shadow_coder']['archive_bytes']}")
        print(f"same_coder_saved_bytes={exact['same_coder_delta']['saved_bytes']}")
        print(f"candidate_score={score['candidate_score']}")
        print(f"constructive_10_95_certificate={score['constructive_10_95_certificate']}")
        print(f"projected_score_non_proof={score['projected_score_non_proof']}")
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
