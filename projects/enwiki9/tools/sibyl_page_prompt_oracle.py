#!/usr/bin/env python3
"""Measure paid page-level calibration headroom on an exact CMIX P1 trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from wrt_exact import parse_store


P1_MAGIC = b"CMX21P1\0"
P1_HEADER_BYTES = 16
MAX_CODE = (1 << 32) - 1
TOTAL = 1 << 16
QBITS_SCALE = 256
PAGE_MAP_RECORD = struct.Struct("<QQQQ")
LABEL_BITS = 4
LABEL_FRAME_BYTES = 16

# (scale numerator, scale denominator, signed P1 bias)
CURVES: tuple[tuple[int, int, int], ...] = (
    (1, 1, 0),
    (1, 2, 0),
    (2, 3, 0),
    (3, 4, 0),
    (7, 8, 0),
    (9, 8, 0),
    (5, 4, 0),
    (3, 2, 0),
    (1, 1, -1024),
    (1, 1, -512),
    (1, 1, -256),
    (1, 1, 256),
    (1, 1, 512),
    (1, 1, 1024),
    (7, 8, -512),
    (7, 8, 512),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def read_p1(path: Path) -> np.memmap:
    with path.open("rb") as source:
        header = source.read(P1_HEADER_BYTES)
    if len(header) != P1_HEADER_BYTES or header[:8] != P1_MAGIC:
        raise ValueError("invalid CMIX final-P1 trace header")
    rows = int.from_bytes(header[8:16], "little")
    if rows <= 0 or rows % 8:
        raise ValueError("P1 row count must be positive and byte aligned")
    if path.stat().st_size != P1_HEADER_BYTES + 2 * rows:
        raise ValueError("P1 trace size does not match its row count")
    return np.memmap(
        path, mode="r", dtype="<u2", offset=P1_HEADER_BYTES, shape=(rows,)
    )


def truth_bits(store: Path, rows: int) -> np.ndarray:
    if store.stat().st_size != 5 + rows // 8:
        raise ValueError("WRT store size does not match P1 rows")
    stored = np.memmap(store, mode="r", dtype="u1")
    if bytes(stored[:5]) != b"\x80\x00\x00\x00\x00":
        raise ValueError("invalid outer WRT store header")
    return np.unpackbits(stored[5:], bitorder="big")


def archive_payload(path: Path) -> tuple[int, int, int]:
    with path.open("rb") as source:
        header = source.read(5)
    if len(header) != 5:
        raise ValueError("archive is truncated")
    wrt_bytes = header[0] & 0x7F
    for value in header[1:]:
        wrt_bytes = (wrt_bytes << 8) | value
    header_bytes = 5 if wrt_bytes < 10_000 else 37
    payload_bytes = path.stat().st_size - header_bytes
    if payload_bytes <= 0:
        raise ValueError("archive has no arithmetic payload")
    return payload_bytes, header_bytes, wrt_bytes


def transform_curve(values: np.ndarray, curve_id: int) -> np.ndarray:
    numerator, denominator, bias = CURVES[curve_id]
    centered = values.astype(np.int64) - 32768
    magnitude = (
        np.abs(centered) * numerator + denominator // 2
    ) // denominator
    scaled = np.where(centered < 0, -magnitude, magnitude)
    return np.clip(32768 + scaled + bias, 1, 65535).astype(np.uint16)


def qbit_table(bit: int) -> np.ndarray:
    probabilities = np.arange(TOTAL, dtype=np.float64) / TOTAL
    selected = probabilities if bit else 1.0 - probabilities
    np.clip(selected, 1.0 / TOTAL, 1.0 - 1.0 / TOTAL, out=selected)
    return np.rint(-np.log2(selected) * QBITS_SCALE).astype(np.int32)


def page_intervals(parsed: Any) -> list[tuple[int, int, int, int]]:
    raw = parsed.decoded
    raw_spans: list[tuple[int, int]] = []
    cursor = 0
    while True:
        start = raw.find(b"<page>", cursor)
        if start < 0:
            break
        close = raw.find(b"</page>", start + 6)
        if close < 0:
            break
        end = close + len(b"</page>")
        raw_spans.append((start, end))
        cursor = end

    starts: dict[int, int] = {}
    ends: dict[int, int] = {0: 6}
    raw_position = 0
    for event in parsed.events:
        starts.setdefault(raw_position, event.start)
        raw_position += len(event.decoded)
        ends.setdefault(raw_position, event.end)
    if raw_position != len(raw):
        raise ValueError("event/raw length mismatch")

    intervals: list[tuple[int, int, int, int]] = []
    for raw_start, raw_end in raw_spans:
        if raw_start not in starts or raw_end not in ends:
            raise ValueError(
                f"page boundary cuts a WRT event: raw [{raw_start}, {raw_end})"
            )
        row_start = starts[raw_start] * 8
        row_end = ends[raw_end] * 8
        if not 0 <= row_start < row_end <= len(parsed.stream) * 8:
            raise ValueError("invalid mapped page rows")
        intervals.append((raw_start, raw_end, row_start, row_end))
    return intervals


def select_labels(
    p1: np.ndarray,
    truth: np.ndarray,
    intervals: list[tuple[int, int, int, int]],
) -> tuple[np.ndarray, np.ndarray]:
    costs = np.zeros((len(intervals), len(CURVES)), dtype=np.int64)
    zero_cost = qbit_table(0)
    one_cost = qbit_table(1)
    for curve_id in range(len(CURVES)):
        transformed = transform_curve(p1, curve_id)
        for page_id, (_, _, start, end) in enumerate(intervals):
            values = transformed[start:end]
            bits = truth[start:end]
            costs[page_id, curve_id] = int(
                np.where(bits != 0, one_cost[values], zero_cost[values]).sum()
            )
    labels = np.argmin(costs, axis=1).astype(np.uint8)
    return labels, costs


def apply_labels(
    p1: np.ndarray,
    intervals: list[tuple[int, int, int, int]],
    labels: np.ndarray,
) -> np.ndarray:
    output = np.asarray(p1).copy()
    for (_, _, start, end), label in zip(intervals, labels, strict=True):
        output[start:end] = transform_curve(output[start:end], int(label))
    return output


def count_payload(probabilities: np.ndarray, truth: np.ndarray) -> int:
    x1 = 0
    x2 = MAX_CODE
    output_bytes = 0
    chunk_rows = 1 << 20
    for start in range(0, len(truth), chunk_rows):
        stop = min(len(truth), start + chunk_rows)
        p_chunk = probabilities[start:stop].tolist()
        b_chunk = truth[start:stop].tolist()
        for p1, bit in zip(p_chunk, b_chunk, strict=True):
            delta = x2 - x1
            midpoint = x1 + (delta >> 16) * p1 + (
                (delta & 0xFFFF) * p1 >> 16
            )
            if bit:
                x2 = midpoint
            else:
                x1 = midpoint + 1
            while ((x1 ^ x2) & 0xFF000000) == 0:
                output_bytes += 1
                x1 = (x1 << 8) & MAX_CODE
                x2 = ((x2 << 8) & MAX_CODE) + 255
    while ((x1 ^ x2) & 0xFF000000) == 0:
        output_bytes += 1
        x1 = (x1 << 8) & MAX_CODE
        x2 = ((x2 << 8) & MAX_CODE) + 255
    return output_bytes + 1


def replay(
    name: str,
    probabilities: np.ndarray,
    truth: np.ndarray,
    baseline_payload_bytes: int,
    charged_bytes: int,
) -> dict[str, Any]:
    payload_bytes = count_payload(probabilities, truth)
    gross_saved = baseline_payload_bytes - payload_bytes
    return {
        "name": name,
        "payload_bytes": payload_bytes,
        "gross_saved_bytes": gross_saved,
        "charged_bytes": charged_bytes,
        "net_saved_bytes": gross_saved - charged_bytes,
    }


def write_page_map(
    path: Path, intervals: list[tuple[int, int, int, int]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as target:
        target.write(b"SIBMAP1\0")
        target.write(struct.pack("<Q", len(intervals)))
        for record in intervals:
            target.write(PAGE_MAP_RECORD.pack(*record))


def write_labels(path: Path, labels: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as target:
        target.write(b"SIBLBL1\0")
        target.write(struct.pack("<Q", len(labels)))
        target.write(labels.tobytes())


def run(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    p1 = read_p1(args.p1_trace)
    truth = truth_bits(args.wrt_store, len(p1))
    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("exact WRT reconstruction differs from raw input")
    intervals = page_intervals(parsed)
    if not intervals:
        raise ValueError("no complete pages found")
    labels, qbit_costs = select_labels(p1, truth, intervals)
    write_page_map(args.page_map, intervals)
    write_labels(args.labels, labels)

    payload_bytes, archive_header_bytes, archive_wrt_bytes = archive_payload(
        args.archive
    )
    baseline = replay("Z0_parent", p1, truth, payload_bytes, 0)
    if baseline["payload_bytes"] != payload_bytes:
        raise ValueError(
            "final-P1 replay does not reproduce the parent arithmetic payload"
        )

    global_curve = int(np.argmin(qbit_costs.sum(axis=0)))
    global_labels = np.full(len(intervals), global_curve, dtype=np.uint8)
    pagewise = apply_labels(p1, intervals, labels)
    fixed_label_bytes = LABEL_FRAME_BYTES + (
        len(labels) * LABEL_BITS + 7
    ) // 8
    controls = {
        "Z0": baseline,
        "Z1": replay(
            "Z1_global_curve",
            apply_labels(p1, intervals, global_labels),
            truth,
            payload_bytes,
            1,
        ),
        "Z16": replay(
            "Z16_paid_pagewise",
            pagewise,
            truth,
            payload_bytes,
            fixed_label_bytes,
        ),
        "ZR": replay(
            "ZR_rotated_labels",
            apply_labels(p1, intervals, np.roll(labels, 1)),
            truth,
            payload_bytes,
            fixed_label_bytes,
        ),
    }
    selected = controls["Z16"]
    raw_page_bytes = sum(end - start for start, end, _, _ in intervals)
    mapped_rows = sum(end - start for _, _, start, end in intervals)
    projected_10m_net = selected["net_saved_bytes"] * 10
    if selected["net_saved_bytes"] <= 0:
        verdict = "opening_sign_negative_retire_simple_page_calibration"
        next_action = "reject proposal without component tracing or larger replay"
    elif projected_10m_net < args.canonical_gross_gate:
        verdict = "opening_positive_below_target_scale"
        next_action = (
            "retain as complementary evidence only; do not build component trace"
        )
    else:
        verdict = "opening_target_scale_signal_authorizes_canonical_trace"
        next_action = (
            "materialize exact canonical-10M P1 trace and rerun frozen curves"
        )

    manifest = {
        "schema": "endpoint_final_trace_manifest_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "exact_pre_truth_final_p1_trace_identity",
        "artifacts": {
            "binary": artifact(args.binary),
            "raw_input": artifact(args.raw_input),
            "wrt_store": artifact(args.wrt_store),
            "dictionary": artifact(args.dictionary),
            "archive": artifact(args.archive),
            "p1_trace": artifact(args.p1_trace),
            "page_map": artifact(args.page_map),
            "selected_labels": artifact(args.labels),
        },
        "proof": {
            "p1_rows": len(p1),
            "coded_wrt_bytes": len(p1) // 8,
            "wrt_store_bytes_excluding_outer_header": (
                args.wrt_store.stat().st_size - 5
            ),
            "trace_rows_equal_coded_wrt_bits": True,
            "truth_bits_equal_wrt_store": True,
            "exact_wrt_reconstruction_equal_raw_input": True,
            "parent_arithmetic_payload_bytes": payload_bytes,
            "trace_replay_payload_bytes": baseline["payload_bytes"],
            "trace_reproduces_parent_payload": True,
            "archive_header_bytes": archive_header_bytes,
            "archive_declared_wrt_bytes": archive_wrt_bytes,
            "complete_page_count": len(intervals),
            "mapped_raw_page_bytes": raw_page_bytes,
            "mapped_trace_rows": mapped_rows,
        },
        "claim_boundary": (
            "Observation-only trace evidence. It changes no coded probability and "
            "receives zero score credit. Raw/page mapping covers complete pages only."
        ),
    }
    decision = {
        "schema": "sibyl_page_prompt_oracle_v0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "future_informed_paid_label_oracle_exact_range_replay",
        "proposal_id": "sibyl_mdl_paid_page_regime_v1",
        "curve_contract": [
            {
                "curve_id": index,
                "scale_numerator": curve[0],
                "scale_denominator": curve[1],
                "p1_bias": curve[2],
            }
            for index, curve in enumerate(CURVES)
        ],
        "selection": {
            "method": "minimum_integer_qbit_cost_per_complete_page",
            "qbits_per_bit": QBITS_SCALE,
            "tie_break": "lowest_curve_id",
            "future_page_truth_used": True,
            "score_credit": 0,
            "global_curve_id": global_curve,
            "label_counts": {
                str(key): value
                for key, value in sorted(Counter(map(int, labels)).items())
            },
            "fixed_label_bits_per_page": LABEL_BITS,
            "label_framing_bytes": LABEL_FRAME_BYTES,
            "charged_label_stream_bytes": fixed_label_bytes,
        },
        "scope": {
            "raw_bytes": len(raw),
            "complete_pages": len(intervals),
            "complete_page_raw_bytes": raw_page_bytes,
            "trace_rows": len(p1),
            "page_trace_rows": mapped_rows,
        },
        "controls": controls,
        "screen": {
            "canonical_10m_gate_bytes": args.canonical_gross_gate,
            "opening_net_saved_bytes": selected["net_saved_bytes"],
            "naive_10m_net_projection_bytes": projected_10m_net,
            "verdict": verdict,
            "next_action": next_action,
        },
        "unrun_control": {
            "ZP": "causal title/prefix label prediction is authorized only after V0",
        },
        "claim_boundary": (
            "The page labels use complete-page truth and are explicitly charged but "
            "are not constructive. This is an oracle headroom measurement with zero "
            "score credit. Exact source bytes, native integration, offset transfer, "
            "runtime, and full-corpus score remain unproved."
        ),
    }
    return manifest, decision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--p1-trace", type=Path, required=True)
    parser.add_argument("--page-map", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--canonical-gross-gate", type=int, default=45_000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest, decision = run(args)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.decision.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    args.decision.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
