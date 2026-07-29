#!/usr/bin/env python3
"""Exact paid fixed-population residual context quotient over endpoint428."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

import numpy as np

from janus_paid_residual_mdl_oracle import (
    range_decode,
    range_encode,
    read_p1,
    sha256_bytes,
    sha256_file,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRACE = (
    ROOT
    / "results"
    / "endpoint428_pair_layer0_online_native_trace_10m_v1"
    / "native.p1"
)
DEFAULT_WRT = (
    ROOT
    / "results"
    / "endpoint428_pair_layer0_online_native_trace_10m_v1"
    / "wrt_store.bin"
)
DEFAULT_ARCHIVE = (
    ROOT
    / "results"
    / "endpoint428_pair_layer0_online_native_trace_10m_v1"
    / "archive.bin"
)
DEFAULT_INVERSE = (
    ROOT
    / "results"
    / "endpoint428_wrt_store_inverse_10m_v1"
    / "decision.json"
)
DEFAULT_RESULTS = ROOT / "results" / "janus_paid_context_quotient_10m_q0_v1"

TABLE_BITS = 16
TABLE_SIZE = 1 << TABLE_BITS
HISTORY_BYTES = 4
CONFIDENCE_BITS = 5
CORRECTIONS = (
    (1, 4),
    (1, 2),
    (2, 3),
    (1, 1),
    (3, 2),
    (2, 1),
    (4, 1),
    (1, 1),
)
IDENTITY_CODE = 3
FIT_PRIORITY = np.asarray((5, 3, 2, 0, 1, 4, 6, 7), dtype=np.int64)
SHIFT_STATES = 8191
DECODER_ALLOWANCE = 24_576
FRAME_BYTES = 64
PACKAGE_CEILING = 128 * 1024
GROSS_GATE_BPM = 3000.0
NET_GATE_BPM = 2100.0
RAW_BYTES = 10_000_000
PARENT_PAYLOAD_BYTES = 1_635_137

HASH_MULTIPLIERS = (
    np.uint64(0x9E3779B185EBCA87),
    np.uint64(0xC2B2AE3D27D4EB4F),
    np.uint64(0x165667B19E3779F9),
    np.uint64(0x85EBCA77C2B2AE63),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p1", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--wrt", type=Path, default=DEFAULT_WRT)
    parser.add_argument("--parent-archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--inverse-receipt", type=Path, default=DEFAULT_INVERSE)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--raw-bytes", type=int, default=RAW_BYTES)
    parser.add_argument(
        "--expected-parent-payload",
        type=int,
        default=PARENT_PAYLOAD_BYTES,
    )
    parser.add_argument("--root-parent-payload-bytes", type=int, default=0)
    parser.add_argument("--upstream-package-bytes", type=int, default=0)
    parser.add_argument(
        "--package-ceiling",
        type=int,
        default=PACKAGE_CEILING,
    )
    return parser.parse_args()


def qbit_tables() -> tuple[np.ndarray, np.ndarray]:
    values = np.arange(65536, dtype=np.float64)
    values[0] = 1.0
    p1 = values / 65536.0
    p0 = 1.0 - p1
    return (
        np.rint(-np.log2(p0) * 256.0).astype(np.int64),
        np.rint(-np.log2(p1) * 256.0).astype(np.int64),
    )


def correction_maps() -> np.ndarray:
    base = np.arange(65536, dtype=np.int64)
    base[0] = 1
    output = np.empty((len(CORRECTIONS), 65536), dtype=np.uint16)
    for code, (numerator, denominator) in enumerate(CORRECTIONS):
        top = 65536 * numerator * base
        bottom = denominator * (65536 - base) + numerator * base
        adjusted = (top + bottom // 2) // bottom
        output[code] = np.clip(adjusted, 1, 65535).astype(np.uint16)
    return output


def previous_bytes(wrt: np.ndarray) -> tuple[np.ndarray, ...]:
    history = []
    for depth in range(1, HISTORY_BYTES + 1):
        values = np.zeros(len(wrt), dtype=np.uint8)
        values[depth:] = wrt[:-depth]
        history.append(values)
    return tuple(history)


def quotient_indexes(
    wrt: np.ndarray,
    history: tuple[np.ndarray, ...],
    base_p1: np.ndarray,
    bit_position: int,
) -> np.ndarray:
    if bit_position == 0:
        prefix = np.zeros(len(wrt), dtype=np.uint16)
    else:
        prefix = wrt.astype(np.uint16) >> (8 - bit_position)
    node = np.uint64(1 << bit_position) + prefix.astype(np.uint64)
    confidence = (
        base_p1.astype(np.uint64) >> (16 - CONFIDENCE_BITS)
    )
    value = node * np.uint64(0xD6E8FEB86659FD93)
    value ^= confidence * np.uint64(0xA0761D6478BD642F)
    for prior, multiplier in zip(history, HASH_MULTIPLIERS, strict=True):
        value ^= prior.astype(np.uint64) * multiplier
    value ^= value >> np.uint64(33)
    value *= np.uint64(0xFF51AFD7ED558CCD)
    value ^= value >> np.uint64(33)
    return (value & np.uint64(TABLE_SIZE - 1)).astype(np.int64)


def fit_table(
    wrt: np.ndarray,
    parent_p1: np.ndarray,
    adjusted: np.ndarray,
    zero_qbits: np.ndarray,
    one_qbits: np.ndarray,
) -> np.ndarray:
    history = previous_bytes(wrt)
    costs = np.zeros((len(CORRECTIONS), TABLE_SIZE), dtype=np.int64)
    for bit_position in range(8):
        base = np.asarray(parent_p1[bit_position::8], dtype=np.uint16)
        truth = ((wrt >> (7 - bit_position)) & 1).astype(np.uint8)
        indexes = quotient_indexes(wrt, history, base, bit_position)
        for code in range(len(CORRECTIONS)):
            candidate = adjusted[code, base]
            row_cost = np.where(
                truth != 0,
                one_qbits[candidate],
                zero_qbits[candidate],
            )
            aggregate = np.bincount(
                indexes,
                weights=row_cost,
                minlength=TABLE_SIZE,
            )
            costs[code] += np.rint(aggregate).astype(np.int64)
    ranked = costs * 16 + FIT_PRIORITY[:, None]
    table = np.argmin(ranked, axis=0).astype(np.uint8)
    empty = np.all(costs == 0, axis=0)
    table[empty] = IDENTITY_CODE
    return table


def apply_table(
    wrt: np.ndarray,
    parent_p1: np.ndarray,
    table: np.ndarray,
    adjusted: np.ndarray,
) -> np.ndarray:
    history = previous_bytes(wrt)
    candidate = np.asarray(parent_p1, dtype=np.uint16).copy()
    for bit_position in range(8):
        base = np.asarray(parent_p1[bit_position::8], dtype=np.uint16)
        indexes = quotient_indexes(wrt, history, base, bit_position)
        codes = table[indexes]
        candidate[bit_position::8] = adjusted[codes, base]
    return candidate


def serialize_model(table: np.ndarray) -> bytes:
    output = bytearray(b"JQDG1\0")
    output.extend(
        struct.pack(
            "<IIIII",
            1,
            TABLE_BITS,
            HISTORY_BYTES,
            CONFIDENCE_BITS,
            len(CORRECTIONS),
        )
    )
    for numerator, denominator in CORRECTIONS:
        output.extend(struct.pack("<HH", numerator, denominator))
    output.extend(table.tobytes(order="C"))
    return bytes(output)


def exact_decode(payload: bytes, p1: np.ndarray, truth: np.ndarray) -> bool:
    decoded = range_decode(payload, p1)
    return np.array_equal(decoded, truth)


def main() -> int:
    args = parse_args()
    args.results.mkdir(parents=True, exist_ok=True)

    wrt_file = args.wrt.read_bytes()
    if len(wrt_file) <= 5:
        raise ValueError("WRT store is truncated")
    wrt = np.frombuffer(wrt_file, dtype=np.uint8, offset=5).copy()
    _, parent_p1 = read_p1(args.p1, len(wrt) * 8)
    truth = np.unpackbits(wrt, bitorder="big")

    parent_payload = range_encode(parent_p1, truth)
    if len(parent_payload) != args.expected_parent_payload:
        raise ValueError("parent payload length differs from frozen receipt")
    archive = args.parent_archive.read_bytes()
    receipt_payload = archive[-len(parent_payload) :]
    parent_identity = parent_payload == receipt_payload
    if not parent_identity:
        raise ValueError("parent payload byte identity failed")

    inverse_text = args.inverse_receipt.read_text()
    wrt_sha256 = sha256_file(args.wrt)
    inverse_bound = wrt_sha256 in inverse_text
    if not inverse_bound:
        raise ValueError("WRT/raw inverse receipt does not bind this store")

    zero_qbits, one_qbits = qbit_tables()
    adjusted = correction_maps()
    table_a = fit_table(wrt, parent_p1, adjusted, zero_qbits, one_qbits)
    table_b = fit_table(wrt, parent_p1, adjusted, zero_qbits, one_qbits)
    model_a = serialize_model(table_a)
    model_b = serialize_model(table_b)
    model_identity = model_a == model_b

    candidate_a = apply_table(wrt, parent_p1, table_a, adjusted)
    candidate_b = apply_table(wrt, parent_p1, table_b, adjusted)
    p1_identity = np.array_equal(candidate_a, candidate_b)
    payload_a = range_encode(candidate_a, truth)
    payload_b = range_encode(candidate_b, truth)
    payload_identity = payload_a == payload_b
    decode_a = exact_decode(payload_a, candidate_a, truth)
    decode_b = exact_decode(payload_b, candidate_b, truth)

    shifted_table = np.roll(table_a, SHIFT_STATES)
    shifted_p1 = apply_table(wrt, parent_p1, shifted_table, adjusted)
    shifted_payload = range_encode(shifted_p1, truth)
    shifted_decode = exact_decode(shifted_payload, shifted_p1, truth)

    compressed_model = zlib.compress(model_a, level=9)
    package_bytes = len(compressed_model) + DECODER_ALLOWANCE + FRAME_BYTES
    gross_gain = len(parent_payload) - len(payload_a)
    gross_bpm = gross_gain * 1_000_000.0 / args.raw_bytes
    net_bpm = gross_bpm - package_bytes / 1000.0
    root_parent_payload = (
        args.root_parent_payload_bytes
        if args.root_parent_payload_bytes
        else len(parent_payload)
    )
    joint_package_bytes = package_bytes + args.upstream_package_bytes
    joint_gross_gain = root_parent_payload - len(payload_a)
    joint_gross_bpm = joint_gross_gain * 1_000_000.0 / args.raw_bytes
    joint_net_bpm = joint_gross_bpm - joint_package_bytes / 1000.0
    exactness = all(
        (
            parent_identity,
            inverse_bound,
            model_identity,
            p1_identity,
            payload_identity,
            decode_a,
            decode_b,
            shifted_decode,
        )
    )
    authorized = all(
        (
            exactness,
            joint_gross_bpm >= GROSS_GATE_BPM,
            joint_net_bpm >= NET_GATE_BPM,
            len(payload_a) < len(shifted_payload),
            joint_package_bytes <= args.package_ceiling,
        )
    )
    decision = "AUTHORIZED_SUCCESSOR" if authorized else "REJECT"

    (args.results / "model.jqdg1").write_bytes(model_a)
    (args.results / "model.jqdg1.zlib").write_bytes(compressed_model)
    (args.results / "candidate.payload").write_bytes(payload_a)
    (args.results / "shifted.payload").write_bytes(shifted_payload)

    counts = np.bincount(table_a, minlength=len(CORRECTIONS))
    receipt = {
        "schema": "janus_paid_context_quotient_decision_v1",
        "candidate": "janus_paid_context_quotient_q0_v1",
        "decision": decision,
        "claim_boundary": (
            "Paid fixed-population oracle evidence only; score credit remains "
            "zero until a native counted codec passes all gates."
        ),
        "inputs": {
            "raw_bytes": args.raw_bytes,
            "wrt_bytes": len(wrt),
            "wrt_sha256": wrt_sha256,
            "p1_path": str(args.p1),
            "p1_sha256": sha256_file(args.p1),
            "parent_archive_sha256": sha256_file(args.parent_archive),
        },
        "model": {
            "states": TABLE_SIZE,
            "history_bytes": HISTORY_BYTES,
            "confidence_bins": 1 << CONFIDENCE_BITS,
            "corrections": [list(item) for item in CORRECTIONS],
            "code_counts": counts.astype(int).tolist(),
            "raw_bytes": len(model_a),
            "compressed_bytes": len(compressed_model),
            "raw_sha256": sha256_bytes(model_a),
            "compressed_sha256": sha256_bytes(compressed_model),
            "decoder_allowance_bytes": DECODER_ALLOWANCE,
            "frame_bytes": FRAME_BYTES,
            "complete_package_bytes": package_bytes,
            "upstream_package_bytes": args.upstream_package_bytes,
            "joint_package_bytes": joint_package_bytes,
            "package_ceiling_bytes": args.package_ceiling,
        },
        "payloads": {
            "J0_parent": {
                "bytes": len(parent_payload),
                "sha256": sha256_bytes(parent_payload),
            },
            "JQ_context_quotient": {
                "bytes": len(payload_a),
                "sha256": sha256_bytes(payload_a),
            },
            "JS_shifted_table": {
                "bytes": len(shifted_payload),
                "sha256": sha256_bytes(shifted_payload),
                "shift_states": SHIFT_STATES,
            },
        },
        "economics": {
            "gross_gain_bytes": gross_gain,
            "gross_gain_bytes_per_million": gross_bpm,
            "package_adjusted_gain_bytes_per_million": net_bpm,
            "root_parent_payload_bytes": root_parent_payload,
            "joint_gross_gain_bytes": joint_gross_gain,
            "joint_gross_gain_bytes_per_million": joint_gross_bpm,
            "joint_package_adjusted_gain_bytes_per_million": joint_net_bpm,
            "literal_10m_two_part_bytes": len(payload_a) + package_bytes,
        },
        "gates": {
            "gross_required_bytes_per_million": GROSS_GATE_BPM,
            "net_required_bytes_per_million": NET_GATE_BPM,
            "gross_pass": joint_gross_bpm >= GROSS_GATE_BPM,
            "net_pass": joint_net_bpm >= NET_GATE_BPM,
            "shift_specificity_pass": len(payload_a) < len(shifted_payload),
            "package_pass": joint_package_bytes <= args.package_ceiling,
        },
        "exactness": {
            "parent_payload_identity": parent_identity,
            "inverse_receipt_bound": inverse_bound,
            "ab_model_identity": model_identity,
            "ab_p1_identity": p1_identity,
            "ab_payload_identity": payload_identity,
            "candidate_a_decode": decode_a,
            "candidate_b_decode": decode_b,
            "shifted_decode": shifted_decode,
        },
        "score_credit_bytes": 0,
    }
    decision_path = args.results / "decision.json"
    decision_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"janus-paid-context-quotient: {error}", file=sys.stderr)
        raise
