#!/usr/bin/env python3
"""Align a causal NNCP distribution trace with exact Gamma WRT qbits."""

from __future__ import annotations

import argparse
import json
import struct
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from radix_island_oracle import (
    artifact,
    emission_groups,
    load_p1,
    load_truth,
    qbit_tables,
)
from verify_nncp_symbol_map import HEADER_BYTES, ROW_DTYPE
from verify_nncp_teacher_distribution import HEADER, ROW, rows
from wrt_exact import parse_store


def page_phase(raw: bytes, position: int) -> str:
    page = raw.rfind(b"<page>", 0, position + 1)
    if page < 0 or raw.rfind(b"</page>", 0, position + 1) > page:
        return "envelope"
    text = raw.rfind(b"<text", page, position + 1)
    text_end = raw.rfind(b"</text>", page, position + 1)
    if text >= 0 and text > text_end:
        return "text"
    revision = raw.rfind(b"<revision>", page, position + 1)
    if revision >= 0:
        return "revision_metadata"
    return "page_header"


def run(args: argparse.Namespace) -> dict[str, Any]:
    raw = args.raw_input.read_bytes()
    parsed = parse_store(args.wrt_store, args.dictionary)
    if parsed.decoded != raw:
        raise ValueError("Gamma WRT reconstruction differs from raw")
    p1 = load_p1(args.gamma_p1)
    truth = load_truth(args.wrt_store, len(p1))
    zero, one = qbit_tables()
    groups = emission_groups(parsed)
    gamma_boundaries = {group.raw_end for group in groups}

    symbol_map = np.memmap(
        args.symbol_map,
        mode="r",
        dtype=ROW_DTYPE,
        offset=HEADER_BYTES,
    )
    teacher_rows = list(rows(args.teacher_trace))
    if any(fixed[0] != index for index, (fixed, _) in enumerate(teacher_rows)):
        raise ValueError("teacher trace is not causal symbol order")
    traced_ends = [
        int(symbol_map[index]["raw_end"]) for index in range(len(teacher_rows))
    ]
    common = [
        end
        for end in traced_ends
        if end in gamma_boundaries and end > 0
    ]
    if not common:
        raise ValueError("no common positive raw boundary")
    raw_end = max(common)
    teacher_count = max(
        index + 1 for index, end in enumerate(traced_ends) if end <= raw_end
    )
    teacher_bits = 0.0
    phase_teacher: dict[str, float] = defaultdict(float)
    phase_rows: Counter[str] = Counter()
    prior_symbol = 0
    previous_symbol_loss: dict[int, list[float]] = defaultdict(list)
    for index, (fixed, distribution) in enumerate(teacher_rows[:teacher_count]):
        true_symbol = fixed[6]
        loss = -float(np.log2(float(distribution[true_symbol])))
        teacher_bits += loss
        start = int(symbol_map[index]["raw_start"])
        phase = page_phase(raw, start)
        phase_teacher[phase] += loss
        phase_rows[phase] += 1
        previous_symbol_loss[prior_symbol].append(loss)
        prior_symbol = true_symbol

    gamma_qbits = 0
    gamma_rows = 0
    for group in groups:
        if group.raw_end > raw_end:
            break
        start = group.stream_start * 8
        end = group.stream_end * 8
        values = p1[start:end]
        bits = truth[start:end]
        gamma_qbits += int(np.where(bits != 0, one[values], zero[values]).sum())
        gamma_rows += end - start
    gamma_bits = gamma_qbits / 256.0
    gap_bits = gamma_bits - teacher_bits
    return {
        "schema": "nncp_gamma_gap_map_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "exact_common_boundary_cross_representation_gap_zero_credit",
        "artifacts": {
            "raw_input": artifact(args.raw_input),
            "wrt_store": artifact(args.wrt_store),
            "dictionary": artifact(args.dictionary),
            "gamma_p1": artifact(args.gamma_p1),
            "symbol_map": artifact(args.symbol_map),
            "teacher_trace": artifact(args.teacher_trace),
        },
        "scope": {
            "common_raw_bytes": raw_end,
            "teacher_symbols": teacher_count,
            "gamma_wrt_rows": gamma_rows,
        },
        "comparison": {
            "gamma_qbits": gamma_qbits,
            "gamma_bits": gamma_bits,
            "teacher_true_logloss_bits": teacher_bits,
            "teacher_minus_gamma_saved_bits": gap_bits,
            "teacher_minus_gamma_saved_bytes": gap_bits / 8.0,
            "teacher_minus_gamma_saved_bytes_per_1m": (
                gap_bits / 8.0 * 1_000_000 / raw_end
            ),
            "teacher_better_than_gamma": gap_bits > 0,
        },
        "attribution": {
            "teacher_rows_by_page_phase": dict(sorted(phase_rows.items())),
            "teacher_bits_by_page_phase": dict(sorted(phase_teacher.items())),
            "previous_symbol_contexts": len(previous_symbol_loss),
        },
        "gate": {
            "passed": gap_bits > 0,
            "verdict": (
                "bounded_teacher_gap_positive"
                if gap_bits > 0
                else "bounded_teacher_gap_negative"
            ),
            "next_action": (
                "run fixed-budget quotient screen"
                if gap_bits > 0
                else "do not train a student on this startup population"
            ),
        },
        "claim_boundary": (
            "The total comparison ends at an exact shared raw boundary. "
            "Teacher length is ideal true-symbol log loss, while Gamma length "
            "is exact integer qbits; neither is a native archive comparison."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--gamma-p1", type=Path, required=True)
    parser.add_argument("--symbol-map", type=Path, required=True)
    parser.add_argument("--teacher-trace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
