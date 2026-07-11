#!/usr/bin/env python3
"""Rank compact causal XML/Wiki residual corrections on cached FX2 traces."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from dataclasses import dataclass, field
from typing import Any

from fx2_shadow_residual_coder import (
    BinaryArithmeticEncoder,
    TOTAL,
    as_int,
    clamp_p1,
    iter_rows,
    prob_bucket,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_TRACE = ROOT / "results" / "fx2_residual_cache" / "apm1m_full_4805936.tsv"
DEFAULT_OUT = ROOT / "results" / "fx2_residual_probe" / "fx2_xml_residual_screen_v1" / "receipt.json"

REQUIRED_FULL_GAIN_BYTES = 681_114
TARGET_NATIVE_SCOPE_BYTES = 10_000_000

PRESET_KEYS: dict[str, tuple[str, ...]] = {
    "p": ("p_bucket",),
    "p_bit": ("p_bucket", "bit_pos"),
    "mode": ("p_bucket", "bit_pos", "mode"),
    "in_tag": ("p_bucket", "bit_pos", "in_tag"),
    "mode_in_tag": ("p_bucket", "bit_pos", "mode", "in_tag"),
    "char": ("p_bucket", "bit_pos", "char_class"),
    "mode_char": ("p_bucket", "bit_pos", "mode", "char_class"),
    "xml_char": ("p_bucket", "bit_pos", "mode", "in_tag", "char_class"),
    "number": ("p_bucket", "bit_pos", "number_class"),
    "mode_number": ("p_bucket", "bit_pos", "mode", "number_class"),
    "word_len": ("p_bucket", "bit_pos", "word_len"),
    "mode_word": ("p_bucket", "bit_pos", "mode", "word_len"),
    "column": ("p_bucket", "bit_pos", "col_bucket"),
    "mode_column": ("p_bucket", "bit_pos", "mode", "col_bucket"),
    "layout": ("p_bucket", "bit_pos", "mode", "in_tag", "col_bucket", "word_len"),
    "template": ("p_bucket", "bit_pos", "template_depth", "template_arg"),
    "ref_url": ("p_bucket", "bit_pos", "ref", "url", "number_class"),
    "wiki_compact": ("p_bucket", "bit_pos", "mode", "in_tag", "char_class", "number_class"),
}


def qbits_for(bit: int, p1: int) -> int:
    p1 = clamp_p1(p1)
    probability = p1 / TOTAL if bit else (TOTAL - p1) / TOTAL
    return int((-math.log2(probability)) * 256.0 + 0.5)


def parse_key_specs(raw: str) -> list[tuple[str, tuple[str, ...]]]:
    out: list[tuple[str, tuple[str, ...]]] = []
    for item in raw.split(","):
        name = item.strip()
        if not name:
            continue
        if name in PRESET_KEYS:
            out.append((name, PRESET_KEYS[name]))
        else:
            fields = tuple(part for part in name.split("+") if part)
            if not fields:
                raise SystemExit(f"empty key spec: {item!r}")
            out.append((name, fields))
    if not out:
        raise SystemExit("at least one key spec is required")
    return out


def key_value(row: dict[str, Any], field_name: str, p1: int, p_buckets: int) -> int:
    if field_name == "p_bucket":
        return prob_bucket(p1, p_buckets)
    return as_int(row, field_name, default=0)


def key_for(row: dict[str, Any], fields: tuple[str, ...], p1: int, p_buckets: int) -> tuple[int, ...]:
    return tuple(key_value(row, field_name, p1, p_buckets) for field_name in fields)


@dataclass
class BiasCounter:
    count: int = 0
    residual_sum: int = 0

    def predict(self, p1: int, *, blend_ppm: int, min_count: int, max_abs_delta: int) -> int:
        if self.count < min_count or blend_ppm <= 0:
            return p1
        delta = (self.residual_sum * blend_ppm) // (self.count * 1_000_000)
        if max_abs_delta > 0:
            delta = max(-max_abs_delta, min(max_abs_delta, delta))
        return clamp_p1(p1 + delta)

    def update(self, bit: int, p1: int) -> None:
        if bit:
            self.residual_sum += TOTAL - p1
        else:
            self.residual_sum -= p1
        self.count += 1


@dataclass
class CandidateState:
    name: str
    fields: tuple[str, ...]
    p_buckets: int
    blend_ppm: int
    min_count: int
    max_abs_delta: int
    encoder: BinaryArithmeticEncoder = field(default_factory=BinaryArithmeticEncoder)
    heldout_encoder: BinaryArithmeticEncoder = field(default_factory=BinaryArithmeticEncoder)
    table: dict[tuple[int, ...], BiasCounter] = field(default_factory=dict)
    saved_qbits: int = 0
    heldout_saved_qbits: int = 0
    heldout_rows: int = 0
    block_saved_qbits: dict[int, int] = field(default_factory=dict)

    def score(self, row: dict[str, Any], bit: int, p1: int, base_qbits: int, heldout: bool, block_id: int) -> None:
        key = key_for(row, self.fields, p1, self.p_buckets)
        counter = self.table.get(key)
        if counter is None:
            counter = BiasCounter()
            self.table[key] = counter
        predicted = counter.predict(
            p1,
            blend_ppm=self.blend_ppm,
            min_count=self.min_count,
            max_abs_delta=self.max_abs_delta,
        )
        self.encoder.encode(bit, predicted)
        corrected_qbits = qbits_for(bit, predicted)
        delta_qbits = base_qbits - corrected_qbits
        self.saved_qbits += delta_qbits
        if heldout:
            self.heldout_encoder.encode(bit, predicted)
            self.heldout_rows += 1
            self.heldout_saved_qbits += delta_qbits
            self.block_saved_qbits[block_id] = self.block_saved_qbits.get(block_id, 0) + delta_qbits
        counter.update(bit, p1)

    def finish(self) -> None:
        self.encoder.finish()
        if self.heldout_rows:
            self.heldout_encoder.finish()

    def ranked_item(
        self,
        baseline_bits: int,
        heldout_baseline_bits: int,
        code_bytes: int,
        trace_rows: int,
        heldout_scope_bytes: int,
        block_bytes: int,
    ) -> dict[str, Any]:
        saved_bits = baseline_bits - self.encoder.bit_count
        heldout_saved_bits = heldout_baseline_bits - self.heldout_encoder.bit_count if self.heldout_rows else 0
        saved_bytes = (saved_bits // 8) if saved_bits >= 0 else -((-saved_bits + 7) // 8)
        heldout_saved_bytes = (
            (heldout_saved_bits // 8)
            if heldout_saved_bits >= 0
            else -((-heldout_saved_bits + 7) // 8)
        )
        block_deltas = [
            {"block": block_id, "saved_qbytes": round(delta / 2048.0, 6)}
            for block_id, delta in sorted(self.block_saved_qbits.items())
        ]
        regressions = [delta for delta in self.block_saved_qbits.values() if delta < 0]
        projected_10m_saved_bytes = (
            heldout_saved_bytes * TARGET_NATIVE_SCOPE_BYTES / heldout_scope_bytes
            if heldout_scope_bytes > 0
            else None
        )
        required_10m_gain_bytes = REQUIRED_FULL_GAIN_BYTES * TARGET_NATIVE_SCOPE_BYTES / 1_000_000_000
        return {
            "key": self.name,
            "fields": list(self.fields),
            "contexts": len(self.table),
            "exact_shadow_arithmetic": {
                "encoded_rows": trace_rows,
                "saved_bits": saved_bits,
                "saved_bytes": saved_bytes,
                "heldout_rows": self.heldout_rows,
                "heldout_saved_bits": heldout_saved_bits,
                "heldout_saved_bytes": heldout_saved_bytes,
                "baseline_bits": baseline_bits,
                "candidate_bits": self.encoder.bit_count,
                "heldout_baseline_bits": heldout_baseline_bits,
                "heldout_candidate_bits": self.heldout_encoder.bit_count if self.heldout_rows else 0,
            },
            "model_cost": {
                "added_code_bytes_estimate": code_bytes,
                "added_table_bytes": 0,
                "net_heldout_saved_bytes_after_code": heldout_saved_bytes - code_bytes,
                "runtime_contexts_not_payload": len(self.table),
            },
            "heldout_blocks": {
                "block_bytes": block_bytes,
                "block_count": len(self.block_saved_qbits),
                "regression_count": len(regressions),
                "largest_regression_qbytes": round(min(regressions) / 2048.0, 6) if regressions else 0.0,
                "block_delta_qbytes": block_deltas,
            },
            "projection_non_proof": {
                "heldout_scope_bytes": heldout_scope_bytes,
                "projected_10m_saved_bytes": projected_10m_saved_bytes,
                "required_10m_gain_bytes_before_added_code": required_10m_gain_bytes,
                "passes_proportional_10m_screen": bool(
                    projected_10m_saved_bytes is not None
                    and projected_10m_saved_bytes > required_10m_gain_bytes + code_bytes
                    and heldout_saved_bytes > code_bytes
                    and not regressions
                ),
            },
        }


def run_screen(args: argparse.Namespace) -> dict[str, Any]:
    key_specs = parse_key_specs(args.keys)
    candidates = [
        CandidateState(
            name=name,
            fields=fields,
            p_buckets=args.p_buckets,
            blend_ppm=args.blend_ppm,
            min_count=args.min_count,
            max_abs_delta=args.max_abs_delta,
        )
        for name, fields in key_specs
    ]
    baseline = BinaryArithmeticEncoder()
    heldout_baseline = BinaryArithmeticEncoder()
    rows = 0
    heldout_rows = 0
    min_pos: int | None = None
    max_pos: int | None = None
    heldout_min_pos: int | None = None
    heldout_max_pos: int | None = None

    for row in iter_rows(pathlib.Path(args.trace)):
        bit = as_int(row, "bit", default=-1)
        p1 = as_int(row, "p1", "fx2_p1", "probability", default=0)
        if bit not in (0, 1) or not (0 < p1 < TOTAL):
            continue
        p1 = clamp_p1(p1)
        pos = as_int(row, "pos", "position", default=-1)
        if pos >= 0:
            min_pos = pos if min_pos is None else min(min_pos, pos)
            max_pos = pos if max_pos is None else max(max_pos, pos)
        heldout = pos >= args.train_bytes if args.train_bytes > 0 and pos >= 0 else rows >= args.train_rows
        block_id = pos // args.block_bytes if pos >= 0 and args.block_bytes > 0 else rows // max(1, args.block_rows)
        base_qbits = qbits_for(bit, p1)
        baseline.encode(bit, p1)
        if heldout:
            heldout_rows += 1
            heldout_baseline.encode(bit, p1)
            if pos >= 0:
                heldout_min_pos = pos if heldout_min_pos is None else min(heldout_min_pos, pos)
                heldout_max_pos = pos if heldout_max_pos is None else max(heldout_max_pos, pos)
        for candidate in candidates:
            candidate.score(row, bit, p1, base_qbits, heldout, block_id)
        rows += 1
        if args.max_rows > 0 and rows >= args.max_rows:
            break

    baseline.finish()
    if heldout_rows:
        heldout_baseline.finish()
    for candidate in candidates:
        candidate.finish()

    heldout_scope_bytes = (
        (heldout_max_pos - heldout_min_pos + 1)
        if heldout_min_pos is not None and heldout_max_pos is not None
        else 0
    )
    ranked = [
        candidate.ranked_item(
            baseline_bits=baseline.bit_count,
            heldout_baseline_bits=heldout_baseline.bit_count if heldout_rows else 0,
            code_bytes=args.code_bytes,
            trace_rows=rows,
            heldout_scope_bytes=heldout_scope_bytes,
            block_bytes=args.block_bytes,
        )
        for candidate in candidates
    ]
    ranked.sort(
        key=lambda item: (
            item["exact_shadow_arithmetic"]["heldout_saved_bytes"],
            item["exact_shadow_arithmetic"]["saved_bytes"],
        ),
        reverse=True,
    )
    best = ranked[0] if ranked else None
    return {
        "receipt_type": "fx2_xml_residual_screen",
        "candidate_family": {
            "id": "fx2_xml_residual_screen_v1",
            "description": "Fast cached-trace screen for compact causal XML/Wiki residual corrections over FX2 probabilities.",
        },
        "trace": {
            "path": str(args.trace),
            "rows": rows,
            "min_pos": min_pos,
            "max_pos": max_pos,
            "heldout_rows": heldout_rows,
            "heldout_min_pos": heldout_min_pos,
            "heldout_max_pos": heldout_max_pos,
            "heldout_scope_bytes": heldout_scope_bytes,
            "train_bytes": args.train_bytes,
            "train_rows": args.train_rows,
        },
        "params": {
            "keys": args.keys,
            "p_buckets": args.p_buckets,
            "blend_ppm": args.blend_ppm,
            "min_count": args.min_count,
            "max_abs_delta": args.max_abs_delta,
            "block_bytes": args.block_bytes,
            "code_bytes": args.code_bytes,
            "max_rows": args.max_rows,
        },
        "baseline": {
            "bits": baseline.bit_count,
            "bytes": baseline.byte_count,
            "heldout_bits": heldout_baseline.bit_count if heldout_rows else 0,
            "heldout_bytes": heldout_baseline.byte_count if heldout_rows else 0,
        },
        "shadow_ranked": ranked,
        "best": best,
        "verdict": (
            "positive_shadow_only"
            if best and best["exact_shadow_arithmetic"]["heldout_saved_bytes"] > 0
            else "negative_shadow"
        ),
        "claim_boundary": "Cached FX2 residual shadow screen only; not a compressor score or 10.95 proof.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=pathlib.Path, default=DEFAULT_TRACE)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--keys", default=",".join(PRESET_KEYS))
    parser.add_argument("--p-buckets", type=int, default=16)
    parser.add_argument("--blend-ppm", type=int, default=50_000)
    parser.add_argument("--min-count", type=int, default=8)
    parser.add_argument("--max-abs-delta", type=int, default=4096)
    parser.add_argument("--train-bytes", type=int, default=300_000)
    parser.add_argument("--train-rows", type=int, default=0)
    parser.add_argument("--block-bytes", type=int, default=65_536)
    parser.add_argument("--block-rows", type=int, default=524_288)
    parser.add_argument("--code-bytes", type=int, default=6_144)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if not args.trace.exists():
        raise SystemExit(f"missing trace: {args.trace}")
    if args.p_buckets <= 0:
        raise SystemExit("--p-buckets must be positive")
    if args.blend_ppm < 0 or args.blend_ppm > 1_000_000:
        raise SystemExit("--blend-ppm must be between 0 and 1000000")
    if args.min_count < 0:
        raise SystemExit("--min-count must be non-negative")
    if args.max_abs_delta < 0:
        raise SystemExit("--max-abs-delta must be non-negative")
    if args.block_bytes <= 0 or args.block_rows <= 0:
        raise SystemExit("--block-bytes and --block-rows must be positive")
    if args.code_bytes < 0:
        raise SystemExit("--code-bytes must be non-negative")

    payload = run_screen(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        best = payload.get("best") or {}
        exact = best.get("exact_shadow_arithmetic", {}) if isinstance(best, dict) else {}
        cost = best.get("model_cost", {}) if isinstance(best, dict) else {}
        projection = best.get("projection_non_proof", {}) if isinstance(best, dict) else {}
        print(
            json.dumps(
                {
                    "status": payload.get("verdict"),
                    "best_key": best.get("key") if isinstance(best, dict) else None,
                    "rows": payload["trace"]["rows"],
                    "heldout_rows": payload["trace"]["heldout_rows"],
                    "heldout_saved_bytes": exact.get("heldout_saved_bytes"),
                    "net_heldout_saved_bytes_after_code": cost.get("net_heldout_saved_bytes_after_code"),
                    "projected_10m_saved_bytes": projection.get("projected_10m_saved_bytes"),
                    "passes_proportional_10m_screen": projection.get("passes_proportional_10m_screen"),
                    "output": str(args.output),
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
