#!/usr/bin/env python3
"""Align an exact ROCm branch trace with Gamma at a shared raw boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

import numpy as np

from radix_island_oracle import (
    artifact,
    emission_groups,
    load_p1,
    load_truth,
    qbit_tables,
)
from verify_nncp_symbol_map import HEADER_BYTES, ROW_DTYPE
from wrt_exact import parse_store


TRACE_MAGIC = b"RQ0TR1\0\0"
VOCABULARY = 16392


def read_branch_trace(path: Path):
    raw = path.read_bytes()
    if len(raw) < 24 or raw[:8] != TRACE_MAGIC:
        raise ValueError("invalid ROCm branch trace header")
    symbols, branches = struct.unpack("<QQ", raw[8:24])
    probabilities = np.frombuffer(raw, dtype="<u2", offset=24).copy()
    if len(probabilities) != branches:
        raise ValueError(
            f"branch count mismatch: {len(probabilities)} != {branches}"
        )
    return int(symbols), probabilities


def teacher_loss(symbols, branch_probabilities, symbol_count):
    losses = 0.0
    branch_index = 0
    for symbol_value in symbols[:symbol_count]:
        symbol = int(symbol_value)
        start = 0
        active = VOCABULARY
        while active > 1:
            if branch_index >= len(branch_probabilities):
                raise ValueError("branch trace ended inside a symbol")
            probability_zero = int(branch_probabilities[branch_index])
            branch_index += 1
            left = active >> 1
            bit = int(symbol >= start + left)
            mass = (
                65536 - probability_zero if bit else probability_zero
            )
            if not 0 < mass < 65536:
                raise ValueError("invalid teacher branch probability")
            losses -= math.log2(mass / 65536.0)
            if bit:
                start += left
                active -= left
            else:
                active = left
    return losses, branch_index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-input", required=True, type=Path)
    parser.add_argument("--wrt-store", required=True, type=Path)
    parser.add_argument("--dictionary", required=True, type=Path)
    parser.add_argument("--gamma-p1", required=True, type=Path)
    parser.add_argument("--symbol-map", required=True, type=Path)
    parser.add_argument("--preprocessed", required=True, type=Path)
    parser.add_argument("--teacher-trace", required=True, type=Path)
    parser.add_argument("--teacher-payload", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    raw = args.raw_input.read_bytes()
    parsed = parse_store(args.wrt_store, args.dictionary)
    if parsed.decoded != raw:
        raise ValueError("Gamma WRT reconstruction differs from raw")
    p1 = load_p1(args.gamma_p1)
    truth = load_truth(args.wrt_store, len(p1))
    zero, one = qbit_tables()
    groups = emission_groups(parsed)
    gamma_boundaries = {group.raw_end for group in groups}

    mapped = np.memmap(
        args.symbol_map,
        mode="r",
        dtype=ROW_DTYPE,
        offset=HEADER_BYTES,
    )
    declared_symbols, branch_probabilities = read_branch_trace(
        args.teacher_trace
    )
    symbols = np.memmap(args.preprocessed, mode="r", dtype=">u2")
    if declared_symbols > len(mapped) or declared_symbols > len(symbols):
        raise ValueError("trace declares more symbols than its inputs")
    traced_ends = [
        int(mapped[index]["raw_end"]) for index in range(declared_symbols)
    ]
    common = [
        end
        for end in traced_ends
        if end in gamma_boundaries and end > 0
    ]
    if not common:
        raise ValueError("no shared positive raw boundary")
    raw_end = max(common)
    teacher_count = max(
        index + 1
        for index, end in enumerate(traced_ends)
        if end <= raw_end
    )
    teacher_bits, consumed_branches = teacher_loss(
        symbols, branch_probabilities, teacher_count
    )

    gamma_qbits = 0
    gamma_rows = 0
    for group in groups:
        if group.raw_end > raw_end:
            break
        start = group.stream_start * 8
        end = group.stream_end * 8
        values = p1[start:end]
        bits = truth[start:end]
        gamma_qbits += int(
            np.where(bits != 0, one[values], zero[values]).sum()
        )
        gamma_rows += end - start
    gamma_bits = gamma_qbits / 256.0
    gap_bits = gamma_bits - teacher_bits
    gap_bpm = gap_bits / 8.0 * 1_000_000.0 / raw_end
    payload = args.teacher_payload.read_bytes()

    receipt = {
        "schema": "nncp_rocm_branch_gap_map_v1",
        "candidate": "nncp_rocm_batched_causal_teacher_v1",
        "score_credit_bytes": 0,
        "artifacts": {
            "raw_input": artifact(args.raw_input),
            "wrt_store": artifact(args.wrt_store),
            "dictionary": artifact(args.dictionary),
            "gamma_p1": artifact(args.gamma_p1),
            "symbol_map": artifact(args.symbol_map),
            "preprocessed": artifact(args.preprocessed),
            "teacher_trace": artifact(args.teacher_trace),
            "teacher_payload": {
                "path": str(args.teacher_payload),
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            },
        },
        "scope": {
            "common_raw_bytes": raw_end,
            "teacher_symbols": teacher_count,
            "teacher_branches": consumed_branches,
            "gamma_wrt_rows": gamma_rows,
            "complete_teacher_payload_raw_bytes": int(
                mapped[declared_symbols - 1]["raw_end"]
            ),
            "complete_teacher_payload_bytes": len(payload),
        },
        "comparison": {
            "gamma_qbits": gamma_qbits,
            "gamma_bits": gamma_bits,
            "teacher_branch_logloss_bits": teacher_bits,
            "teacher_minus_gamma_saved_bits": gap_bits,
            "teacher_minus_gamma_saved_bytes": gap_bits / 8.0,
            "teacher_minus_gamma_saved_bytes_per_1m": gap_bpm,
            "teacher_better_than_gamma": gap_bits > 0,
        },
        "gate": {
            "startup_headroom_positive": gap_bits > 0,
            "target_scale_3000_bpm": gap_bpm >= 3000.0,
            "verdict": (
                "startup_teacher_gap_target_scale"
                if gap_bpm >= 3000.0
                else (
                    "startup_teacher_gap_positive_subscale"
                    if gap_bits > 0
                    else "startup_teacher_gap_negative"
                )
            ),
        },
        "claim_boundary": (
            "The comparison uses ideal true-branch teacher log loss and "
            "Gamma integer qbits at an exact shared raw boundary. The exact "
            "teacher payload is bound separately for its complete prefix. "
            "This is zero-credit startup evidence, not a native score."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
