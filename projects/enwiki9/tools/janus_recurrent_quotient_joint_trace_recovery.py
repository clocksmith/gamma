#!/usr/bin/env python3
"""Recover and certify the missing exact JANUS-plus-quotient P1 trace."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

from janus_paid_context_quotient import (
    CONFIDENCE_BITS,
    CORRECTIONS,
    HISTORY_BYTES,
    TABLE_BITS,
    TABLE_SIZE,
    apply_table,
    correction_maps,
    serialize_model,
)
from janus_paid_residual_mdl_oracle import range_decode, range_encode, read_p1


ROOT = Path(__file__).resolve().parents[1]
P1_MAGIC = b"CMX21P1\0"
MODEL_MAGIC = b"JQDG1\0"
EXPECTED_JANUS_PAYLOAD_BYTES = 1_620_395
EXPECTED_JOINT_PAYLOAD_BYTES = 1_617_484


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def observed(path: Path) -> dict[str, object]:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def deserialize_model(raw: bytes) -> np.ndarray:
    header_bytes = len(MODEL_MAGIC) + struct.calcsize("<IIIII")
    correction_bytes = len(CORRECTIONS) * struct.calcsize("<HH")
    expected_bytes = header_bytes + correction_bytes + TABLE_SIZE
    if len(raw) != expected_bytes or raw[: len(MODEL_MAGIC)] != MODEL_MAGIC:
        raise ValueError("paid quotient model size or magic mismatch")
    header = struct.unpack_from("<IIIII", raw, len(MODEL_MAGIC))
    expected_header = (
        1,
        TABLE_BITS,
        HISTORY_BYTES,
        CONFIDENCE_BITS,
        len(CORRECTIONS),
    )
    if header != expected_header:
        raise ValueError(f"paid quotient model header mismatch: {header}")
    cursor = header_bytes
    encoded_corrections = []
    for _ in CORRECTIONS:
        encoded_corrections.append(struct.unpack_from("<HH", raw, cursor))
        cursor += struct.calcsize("<HH")
    if tuple(encoded_corrections) != CORRECTIONS:
        raise ValueError("paid quotient correction map declaration mismatch")
    table = np.frombuffer(raw, dtype=np.uint8, offset=cursor).copy()
    if len(table) != TABLE_SIZE:
        raise ValueError("paid quotient table state count mismatch")
    if np.any(table >= len(CORRECTIONS)):
        raise ValueError("paid quotient table contains an invalid code")
    if serialize_model(table) != raw:
        raise ValueError("paid quotient model does not roundtrip canonically")
    return table


def serialize_p1(probabilities: np.ndarray) -> bytes:
    values = np.asarray(probabilities, dtype="<u2")
    return P1_MAGIC + struct.pack("<Q", len(values)) + values.tobytes(order="C")


def assert_receipt_binding(
    decision: dict[str, object],
    janus_p1: Path,
    janus_payload: Path,
    model_path: Path,
    joint_payload: Path,
    wrt_path: Path,
) -> None:
    inputs = decision["inputs"]
    model = decision["model"]
    payloads = decision["payloads"]
    bindings = (
        (sha256_file(janus_p1), inputs["p1_sha256"], "JANUS P1"),
        (
            sha256_file(janus_payload),
            payloads["J0_parent"]["sha256"],
            "JANUS payload",
        ),
        (sha256_file(model_path), model["raw_sha256"], "quotient model"),
        (
            sha256_file(joint_payload),
            payloads["JQ_context_quotient"]["sha256"],
            "joint payload",
        ),
        (sha256_file(wrt_path), inputs["wrt_sha256"], "WRT store"),
    )
    for actual, expected, label in bindings:
        if actual != expected:
            raise ValueError(f"{label} hash differs from terminal joint receipt")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--janus-p1",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_10m_v1/export/janus_candidate.p1",
    )
    parser.add_argument(
        "--janus-payload",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_10m_v1/export/janus_candidate.payload",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_10m_v1/joint/model.jqdg1",
    )
    parser.add_argument(
        "--joint-payload",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_10m_v1/joint/candidate.payload",
    )
    parser.add_argument(
        "--joint-decision",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_10m_v1/joint/decision.json",
    )
    parser.add_argument(
        "--wrt-store",
        type=Path,
        default=ROOT
        / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin",
    )
    parser.add_argument(
        "--inverse-receipt",
        type=Path,
        default=ROOT / "results/endpoint428_wrt_store_inverse_10m_v1/decision.json",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_p1 = output_dir / "joint_candidate.p1"
    decision_path = output_dir / "decision.json"
    if output_p1.exists() or decision_path.exists():
        raise FileExistsError("refusing to overwrite a prior trace recovery artifact")

    terminal_decision = json.loads(args.joint_decision.read_text())
    if terminal_decision.get("decision") != "REJECT":
        raise ValueError("joint input is not the frozen terminal decision")
    assert_receipt_binding(
        terminal_decision,
        args.janus_p1,
        args.janus_payload,
        args.model,
        args.joint_payload,
        args.wrt_store,
    )

    wrt_store = args.wrt_store.read_bytes()
    if len(wrt_store) <= 5:
        raise ValueError("WRT store is truncated")
    wrt = np.frombuffer(wrt_store, dtype=np.uint8, offset=5).copy()
    truth = np.unpackbits(wrt, bitorder="big")
    magic_hex, janus_p1 = read_p1(args.janus_p1, len(truth))
    if bytes.fromhex(magic_hex) != P1_MAGIC:
        raise ValueError("JANUS P1 magic is not the canonical CMX21 P1 magic")
    if np.any(janus_p1 == 0):
        raise ValueError("JANUS P1 contains an illegal zero probability")

    receipt_janus_payload = args.janus_payload.read_bytes()
    replay_janus_payload = range_encode(janus_p1, truth)
    if len(replay_janus_payload) != EXPECTED_JANUS_PAYLOAD_BYTES:
        raise ValueError("JANUS replay payload length mismatch")
    if replay_janus_payload != receipt_janus_payload:
        raise ValueError("JANUS P1 does not reproduce its receipt-bound payload")

    raw_model = args.model.read_bytes()
    table = deserialize_model(raw_model)
    adjusted = correction_maps()
    candidate_a = apply_table(wrt, janus_p1, table, adjusted)
    candidate_b = apply_table(wrt, janus_p1, table, adjusted)
    if not np.array_equal(candidate_a, candidate_b):
        raise ValueError("repeated adjusted P1 generation differs")
    if np.any(candidate_a == 0):
        raise ValueError("joint adjusted P1 contains an illegal zero probability")

    serialized_a = serialize_p1(candidate_a)
    serialized_b = serialize_p1(candidate_b)
    if serialized_a != serialized_b:
        raise ValueError("repeated serialized adjusted P1 traces differ")
    output_p1.write_bytes(serialized_a)

    payload_a = range_encode(candidate_a, truth)
    payload_b = range_encode(candidate_b, truth)
    receipt_joint_payload = args.joint_payload.read_bytes()
    if len(payload_a) != EXPECTED_JOINT_PAYLOAD_BYTES:
        raise ValueError("joint replay payload length mismatch")
    if payload_a != receipt_joint_payload or payload_b != receipt_joint_payload:
        raise ValueError("joint P1 does not reproduce its receipt-bound payload")
    decoded = range_decode(receipt_joint_payload, candidate_a)
    if not np.array_equal(decoded, truth):
        raise ValueError("joint arithmetic decode differs from complete WRT truth")

    wrt_sha256 = sha256_file(args.wrt_store)
    if wrt_sha256 not in args.inverse_receipt.read_text():
        raise ValueError("official inverse receipt does not bind the WRT store")

    decision = {
        "schema": "janus_recurrent_quotient_joint_trace_recovery_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "janus_recurrent_quotient_joint_trace_recovery_q0_v1",
        "evidence_level": "exact_observation_only_joint_p1_trace",
        "inputs": {
            "janus_p1": observed(args.janus_p1),
            "janus_payload": observed(args.janus_payload),
            "quotient_model": observed(args.model),
            "joint_payload": observed(args.joint_payload),
            "joint_decision": observed(args.joint_decision),
            "wrt_store": observed(args.wrt_store),
            "inverse_receipt": observed(args.inverse_receipt),
        },
        "artifact": {
            "joint_p1": observed(output_p1),
            "rows": len(candidate_a),
            "wrt_bytes": len(wrt),
        },
        "proof": {
            "terminal_receipt_bindings_exact": True,
            "model_schema_exact": True,
            "model_reserialization_exact": True,
            "janus_parent_payload_identity": True,
            "repeated_adjusted_p1_identity": True,
            "repeated_serialized_p1_identity": True,
            "all_probabilities_legal_nonzero": True,
            "joint_payload_identity_a": True,
            "joint_payload_identity_b": True,
            "exact_arithmetic_decode": True,
            "complete_wrt_truth_identity": True,
            "official_inverse_receipt_bound": True,
        },
        "economics": terminal_decision["economics"],
        "decision": {
            "verdict": "exact_joint_p1_trace_recovered",
            "residual_attribution_authorized": True,
            "candidate_reopened": False,
            "native_integration_authorized": False,
            "full_1g_authorized": False,
            "score_credit_bytes": 0,
            "forecast_credit_bytes": 0,
            "next_action": (
                "Attribute residual loss only to frozen decoder-visible regimes; "
                "materialize no successor unless a new-information upper bound "
                "clears 3,000 B/M."
            ),
        },
        "claim_boundary": (
            "Observation-only recovery of a missing reproducible trace from an "
            "already-terminal exact 10M composition. No codec or score changed."
        ),
    }
    temporary = decision_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(decision_path)
    print(
        json.dumps(
            {
                "decision_path": str(decision_path),
                "joint_p1_sha256": decision["artifact"]["joint_p1"]["sha256"],
                "verdict": decision["decision"]["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
