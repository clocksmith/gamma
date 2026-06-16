#!/usr/bin/env python3
"""Causal MWCC/router exact-shadow test over fx2 residual rows.

MWCC here means a deterministic mixture-of-weak-causal-corrections router. Each
expert is a tiny residual-bias table keyed by causal row fields. The router
tracks each expert's prior online loss and picks the currently best expert for
the next bit. All experts update only after the bit is encoded.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from dataclasses import dataclass, field
from typing import Any, Iterable

from fx2_shadow_residual_coder import (
    BinaryArithmeticEncoder,
    TOTAL,
    as_int,
    clamp_p1,
    iter_rows,
    prob_bucket,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "mwcc_router_shadow.json"


PRESET_KEYS: dict[str, tuple[str, ...]] = {
    "base": (),
    "p": ("p_bucket",),
    "p_bit": ("p_bucket", "bit_pos"),
    "field": ("p_bucket", "bit_pos", "field"),
    "mode": ("p_bucket", "bit_pos", "mode"),
    "char": ("p_bucket", "bit_pos", "char_class"),
    "field_mode": ("p_bucket", "bit_pos", "field", "mode"),
    "mode_char": ("p_bucket", "bit_pos", "mode", "char_class"),
    "wiki_shape": (
        "p_bucket",
        "bit_pos",
        "field",
        "mode",
        "char_class",
        "template_depth",
    ),
    "layout": ("p_bucket", "bit_pos", "slot", "col_bucket", "word_len"),
    "ref_url": ("p_bucket", "bit_pos", "ref", "url", "number_class"),
}


def qbits_for(bit: int, p1: int | float) -> int:
    p1 = max(1.0, min(65535.0, float(p1)))
    prob = p1 / 65536.0 if bit else (65536.0 - p1) / 65536.0
    # A small local import keeps this tool aligned with the existing scripts
    # without adding global startup cost to simple help invocations.
    import math

    return int((-math.log2(prob)) * 256.0 + 0.5)


def field_value(row: dict[str, Any], field_name: str, p1: int, p_buckets: int) -> int:
    if field_name == "p_bucket":
        return prob_bucket(p1, p_buckets)
    return as_int(row, field_name, default=0)


def key_for(row: dict[str, Any], fields: tuple[str, ...], p1: int, p_buckets: int) -> tuple[int, ...]:
    return tuple(field_value(row, field_name, p1, p_buckets) for field_name in fields)


@dataclass
class BiasCounter:
    count: int = 0
    residual_sum: int = 0

    def correction(self, p1: int, blend_ppm: int) -> int:
        if self.count <= 0 or blend_ppm <= 0:
            return p1
        delta = (self.residual_sum * blend_ppm) // (self.count * 1_000_000)
        return clamp_p1(p1 + delta)

    def update(self, bit: int, p1: int) -> None:
        if bit:
            self.residual_sum += TOTAL - p1
        else:
            self.residual_sum -= p1
        self.count += 1


@dataclass
class Expert:
    name: str
    fields: tuple[str, ...]
    p_buckets: int
    blend_ppm: int
    table: dict[tuple[int, ...], BiasCounter] = field(default_factory=dict)
    loss_ema_qbits: int = 256
    selected: int = 0

    def predict(self, row: dict[str, Any], p1: int) -> int:
        if not self.fields:
            return p1
        key = key_for(row, self.fields, p1, self.p_buckets)
        counter = self.table.get(key)
        if counter is None:
            return p1
        return counter.correction(p1, self.blend_ppm)

    def update(self, row: dict[str, Any], bit: int, p1: int, predicted_p1: int, ema_shift: int) -> None:
        loss = qbits_for(bit, predicted_p1)
        self.loss_ema_qbits += (loss - self.loss_ema_qbits) >> ema_shift
        if not self.fields:
            return
        key = key_for(row, self.fields, p1, self.p_buckets)
        counter = self.table.get(key)
        if counter is None:
            counter = BiasCounter()
            self.table[key] = counter
        counter.update(bit, p1)


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


def is_heldout(row: dict[str, Any], row_index: int, train_bytes: int, train_rows: int) -> bool:
    if train_bytes > 0:
        return as_int(row, "pos", default=0) >= train_bytes
    if train_rows > 0:
        return row_index > train_rows
    return False


def parse_experts(spec: str, p_buckets: int, blend_ppm: int) -> list[Expert]:
    experts: list[Expert] = []
    for raw_name in spec.split(","):
        name = raw_name.strip()
        if not name:
            continue
        if name in PRESET_KEYS:
            fields = PRESET_KEYS[name]
        else:
            fields = tuple(part for part in name.split("+") if part)
            if not fields:
                raise SystemExit(f"empty expert spec: {raw_name}")
        experts.append(Expert(name=name, fields=fields, p_buckets=p_buckets, blend_ppm=blend_ppm))
    if not experts:
        raise SystemExit("at least one expert is required")
    if experts[0].name != "base":
        experts.insert(0, Expert(name="base", fields=(), p_buckets=p_buckets, blend_ppm=0))
    return experts


def run_router(args: argparse.Namespace) -> dict[str, Any]:
    path = pathlib.Path(args.residual_rows)
    rows = load_rows(path, args.max_rows)
    experts = parse_experts(args.experts, args.p_buckets, args.blend_ppm)

    baseline = BinaryArithmeticEncoder()
    routed = BinaryArithmeticEncoder()
    heldout_baseline = BinaryArithmeticEncoder()
    heldout_routed = BinaryArithmeticEncoder()
    heldout_rows = 0
    selection_counts: dict[str, int] = {expert.name: 0 for expert in experts}
    heldout_selection_counts: dict[str, int] = {expert.name: 0 for expert in experts}

    for row_index, row in enumerate(rows, start=1):
        bit = as_int(row, "bit", default=0)
        p1 = clamp_p1(as_int(row, "p1", default=0))
        predictions = [expert.predict(row, p1) for expert in experts]
        best_index = min(range(len(experts)), key=lambda idx: (experts[idx].loss_ema_qbits, idx))
        best = experts[best_index]
        best_p1 = predictions[best_index]
        heldout = is_heldout(row, row_index, args.train_bytes, args.train_rows)

        baseline.encode(bit, p1)
        routed.encode(bit, best_p1)
        selection_counts[best.name] += 1
        if heldout:
            heldout_rows += 1
            heldout_baseline.encode(bit, p1)
            heldout_routed.encode(bit, best_p1)
            heldout_selection_counts[best.name] += 1

        for expert, predicted_p1 in zip(experts, predictions):
            expert.update(row, bit, p1, predicted_p1, args.ema_shift)

    baseline.finish()
    routed.finish()
    if heldout_rows:
        heldout_baseline.finish()
        heldout_routed.finish()

    expert_payload = []
    for expert in experts:
        expert_payload.append(
            {
                "name": expert.name,
                "fields": list(expert.fields),
                "contexts": len(expert.table),
                "loss_ema_qbits": expert.loss_ema_qbits,
                "selected": selection_counts.get(expert.name, 0),
                "heldout_selected": heldout_selection_counts.get(expert.name, 0),
            }
        )

    return {
        "input": str(path),
        "method": "mwcc_router_residual_bias_shadow",
        "params": {
            "experts": args.experts,
            "p_buckets": args.p_buckets,
            "blend_ppm": args.blend_ppm,
            "ema_shift": args.ema_shift,
            "train_bytes": args.train_bytes,
            "train_rows": args.train_rows,
            "max_rows": args.max_rows,
        },
        "rows": len(rows),
        "heldout_rows": heldout_rows,
        "baseline_bits": baseline.bit_count,
        "routed_bits": routed.bit_count,
        "saved_bits": baseline.bit_count - routed.bit_count,
        "baseline_bytes": baseline.byte_count,
        "routed_bytes": routed.byte_count,
        "saved_bytes": baseline.byte_count - routed.byte_count,
        "heldout_baseline_bits": heldout_baseline.bit_count if heldout_rows else 0,
        "heldout_routed_bits": heldout_routed.bit_count if heldout_rows else 0,
        "heldout_saved_bits": (
            heldout_baseline.bit_count - heldout_routed.bit_count if heldout_rows else 0
        ),
        "heldout_baseline_bytes": heldout_baseline.byte_count if heldout_rows else 0,
        "heldout_routed_bytes": heldout_routed.byte_count if heldout_rows else 0,
        "heldout_saved_bytes": (
            heldout_baseline.byte_count - heldout_routed.byte_count if heldout_rows else 0
        ),
        "selection_counts": selection_counts,
        "heldout_selection_counts": heldout_selection_counts,
        "expert_summary": expert_payload,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a causal MWCC/router exact-shadow test.")
    parser.add_argument("residual_rows")
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    parser.add_argument(
        "--experts",
        default="base,p_bit,field,mode,char,field_mode,mode_char,layout,ref_url",
        help="comma-separated presets or + joined row-field keys",
    )
    parser.add_argument("--p-buckets", type=int, default=16)
    parser.add_argument("--blend-ppm", type=int, default=50_000)
    parser.add_argument("--ema-shift", type=int, default=8)
    parser.add_argument("--train-bytes", type=int, default=0)
    parser.add_argument("--train-rows", type=int, default=0)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if args.p_buckets <= 0:
        raise SystemExit("--p-buckets must be positive")
    if args.blend_ppm < 0 or args.blend_ppm > 1_000_000:
        raise SystemExit("--blend-ppm must be between 0 and 1000000")
    if args.ema_shift <= 0 or args.ema_shift > 16:
        raise SystemExit("--ema-shift must be between 1 and 16")
    if args.max_rows < 0:
        raise SystemExit("--max-rows must be non-negative")

    payload = run_router(args)
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        print(
            json.dumps(
                {
                    "status": "ok" if payload["rows"] else "no_rows",
                    "rows": payload["rows"],
                    "saved_bits": payload["saved_bits"],
                    "saved_bytes": payload["saved_bytes"],
                    "heldout_rows": payload["heldout_rows"],
                    "heldout_saved_bits": payload["heldout_saved_bits"],
                    "heldout_saved_bytes": payload["heldout_saved_bytes"],
                    "selection_counts": payload["selection_counts"],
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
