#!/usr/bin/env python3
"""Certify endpoint-union headroom on an exact pre-truth MIXREGRET trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


TRACE_MAGIC = b"MIXRGT1\0"
TRACE_VERSION = 1
TRACE_HEADER_BYTES = 36
ENDPOINT_COUNT = 30
ROW_BYTES = 1 + 2 * ENDPOINT_COUNT
MAX_CODE = (1 << 32) - 1
TOTAL = 1 << 16
QBITS_SCALE = 256
U0_GATE_BPM = 6000.0
NULL_MARGIN_BPM = 1000.0
SHIFT_ROWS = (8192, 17 * 8192, 101 * 8192)
ENDPOINT_NAMES = (
    "M0_final_parent",
    "fixed_blend",
    *(f"layer0_{index:02d}" for index in range(26)),
    "base_post_sse",
    "fx2_endpoint428",
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


def read_trace(path: Path) -> tuple[np.memmap, np.ndarray, np.ndarray]:
    with path.open("rb") as source:
        header = source.read(TRACE_HEADER_BYTES)
    if len(header) != TRACE_HEADER_BYTES or header[:8] != TRACE_MAGIC:
        raise ValueError("invalid MIXREGRET trace header")
    version, header_bytes, row_bytes, endpoint_count, feature_count = (
        struct.unpack_from("<IIIII", header, 8)
    )
    rows = struct.unpack_from("<Q", header, 28)[0]
    if (
        version != TRACE_VERSION
        or header_bytes != TRACE_HEADER_BYTES
        or row_bytes != ROW_BYTES
        or endpoint_count != ENDPOINT_COUNT
        or feature_count != 0
        or rows == 0
    ):
        raise ValueError("unsupported MIXREGRET trace contract")
    if path.stat().st_size != TRACE_HEADER_BYTES + rows * ROW_BYTES:
        raise ValueError("MIXREGRET trace size does not match row count")
    mapped = np.memmap(
        path,
        mode="r",
        dtype=np.uint8,
        offset=TRACE_HEADER_BYTES,
        shape=(rows, ROW_BYTES),
    )
    truth = mapped[:, 0]
    if np.any(truth > 1):
        raise ValueError("trace truth field is not binary")
    endpoints = mapped[:, 1:].reshape(rows, 2 * ENDPOINT_COUNT).view("<u2")
    endpoints = endpoints.reshape(rows, ENDPOINT_COUNT)
    if np.any(endpoints == 0):
        raise ValueError("trace contains zero probability")
    return mapped, truth, endpoints


def read_archive_payload(path: Path) -> tuple[bytes, int, int]:
    data = path.read_bytes()
    if len(data) < 6:
        raise ValueError("parent archive is truncated")
    wrt_bytes = data[0] & 0x7F
    for value in data[1:5]:
        wrt_bytes = (wrt_bytes << 8) | value
    header_bytes = 5 if wrt_bytes < 10_000 else 37
    if len(data) <= header_bytes:
        raise ValueError("parent archive has no arithmetic payload")
    return data[header_bytes:], header_bytes, wrt_bytes


def qbit_tables() -> tuple[np.ndarray, np.ndarray]:
    p1 = np.arange(TOTAL, dtype=np.float64) / TOTAL
    p1[0] = 1.0 / TOTAL
    p0 = 1.0 - p1
    p0[0] = 1.0 - 1.0 / TOTAL
    return (
        np.rint(-np.log2(p0) * QBITS_SCALE).astype(np.int32),
        np.rint(-np.log2(p1) * QBITS_SCALE).astype(np.int32),
    )


def encode_payload(probabilities: np.ndarray, truth: np.ndarray) -> bytes:
    x1 = 0
    x2 = MAX_CODE
    output = bytearray()
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
                output.append((x2 >> 24) & 0xFF)
                x1 = (x1 << 8) & MAX_CODE
                x2 = ((x2 << 8) & MAX_CODE) + 255
    while ((x1 ^ x2) & 0xFF000000) == 0:
        output.append((x2 >> 24) & 0xFF)
        x1 = (x1 << 8) & MAX_CODE
        x2 = ((x2 << 8) & MAX_CODE) + 255
    output.append((x2 >> 24) & 0xFF)
    return bytes(output)


def select_union(
    endpoints: np.ndarray,
    truth: np.ndarray,
    zero_cost: np.ndarray,
    one_cost: np.ndarray,
    shift_rows: int = 0,
) -> tuple[np.ndarray, np.ndarray, int, list[int]]:
    rows = len(truth)
    selected = np.asarray(endpoints[:, 0]).copy()
    selected_cost = np.where(
        truth != 0, one_cost[selected], zero_cost[selected]
    )
    winners = np.zeros(rows, dtype=np.uint8)
    counts = [0] * ENDPOINT_COUNT
    for endpoint in range(1, ENDPOINT_COUNT):
        if shift_rows:
            values = np.roll(
                np.asarray(endpoints[:, endpoint]),
                shift_rows * endpoint,
            )
        else:
            values = np.asarray(endpoints[:, endpoint])
        cost = np.where(truth != 0, one_cost[values], zero_cost[values])
        better = cost < selected_cost
        selected[better] = values[better]
        selected_cost[better] = cost[better]
        winners[better] = endpoint
    unique, frequency = np.unique(winners, return_counts=True)
    for endpoint, count in zip(unique.tolist(), frequency.tolist(), strict=True):
        counts[int(endpoint)] = int(count)
    return selected, selected_cost, int(selected_cost.sum()), counts


def evaluate(
    name: str,
    selected: np.ndarray,
    selected_qbits: int,
    baseline_qbits: int,
    truth: np.ndarray,
    parent_payload: bytes,
    raw_bytes: int,
    winner_counts: list[int],
) -> dict[str, Any]:
    payload = encode_payload(selected, truth)
    exact_saved = len(parent_payload) - len(payload)
    qbit_saved = (baseline_qbits - selected_qbits) / QBITS_SCALE
    return {
        "name": name,
        "payload_bytes": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "exact_saved_bytes": exact_saved,
        "exact_saved_bpm": exact_saved * 1_000_000.0 / raw_bytes,
        "qbit_saved_bits": qbit_saved,
        "qbit_saved_bpm": qbit_saved / 8.0 * 1_000_000.0 / raw_bytes,
        "winner_rows": {
            ENDPOINT_NAMES[index]: winner_counts[index]
            for index in range(ENDPOINT_COUNT)
            if winner_counts[index]
        },
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    mapped, truth, endpoints = read_trace(args.trace)
    parent_payload, archive_header_bytes, wrt_bytes = read_archive_payload(
        args.archive
    )
    zero_cost, one_cost = qbit_tables()
    baseline = np.asarray(endpoints[:, 0])
    baseline_cost = np.where(
        truth != 0, one_cost[baseline], zero_cost[baseline]
    )
    baseline_qbits = int(baseline_cost.sum())
    replay = encode_payload(baseline, truth)
    trace_identity = replay == parent_payload
    if not trace_identity:
        raise ValueError(
            "M0 range replay differs from the parent arithmetic payload"
        )

    selected, selected_cost, selected_qbits, counts = select_union(
        endpoints, truth, zero_cost, one_cost
    )
    real = evaluate(
        "U0_real",
        selected,
        selected_qbits,
        baseline_qbits,
        truth,
        parent_payload,
        args.raw_bytes,
        counts,
    )
    nulls = []
    for shift_rows in SHIFT_ROWS:
        shifted, shifted_cost, shifted_qbits, shifted_counts = select_union(
            endpoints, truth, zero_cost, one_cost, shift_rows
        )
        nulls.append(
            evaluate(
                f"SHIFT_{shift_rows}",
                shifted,
                shifted_qbits,
                baseline_qbits,
                truth,
                parent_payload,
                args.raw_bytes,
                shifted_counts,
            )
        )
        del shifted, shifted_cost

    max_null_bpm = max(item["exact_saved_bpm"] for item in nulls)
    u0_pass = real["exact_saved_bpm"] >= U0_GATE_BPM
    alignment_pass = real["exact_saved_bpm"] >= (
        max_null_bpm + NULL_MARGIN_BPM
    )
    authorized = u0_pass and alignment_pass
    decision = (
        "authorize_u1_decoder_selectability"
        if authorized
        else "retire_component_recombination_unchanged"
    )
    result = {
        "schema": "mixregret_component_union_decision_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate": "mixregret_cert_component_union_v1",
        "claim_boundary": (
            "U0 and shift controls are truth-aware zero-credit oracles. "
            "They do not change the source-bound forecast or authorize a "
            "codec unless every predeclared gate passes."
        ),
        "inputs": {
            "trace": artifact(args.trace),
            "archive": artifact(args.archive),
            "raw_bytes": args.raw_bytes,
            "trace_rows": len(truth),
            "wrt_bytes": wrt_bytes,
            "archive_header_bytes": archive_header_bytes,
            "endpoint_names": list(ENDPOINT_NAMES),
        },
        "identity": {
            "m0_payload_bytes": len(replay),
            "parent_payload_bytes": len(parent_payload),
            "m0_payload_sha256": hashlib.sha256(replay).hexdigest(),
            "parent_payload_sha256": hashlib.sha256(parent_payload).hexdigest(),
            "exact_payload_identity": trace_identity,
        },
        "controls": {
            "U0": real,
            "shift_nulls": nulls,
            "max_shift_exact_saved_bpm": max_null_bpm,
        },
        "gates": {
            "u0_min_exact_saved_bpm": U0_GATE_BPM,
            "null_alignment_margin_bpm": NULL_MARGIN_BPM,
            "u0_pass": u0_pass,
            "alignment_pass": alignment_pass,
            "authorize_u1": authorized,
        },
        "decision": decision,
        "score_credit_bytes": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    del mapped, selected, selected_cost
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--raw-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    result = run(parse_args())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
