#!/usr/bin/env python3
"""Create a repeated exact endpoint428 P1 trace without changing its stream."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import paid_block_vector_codebook as payload_codec
from endpoint428_parent_recovery_gate import ORIGINAL, PROJECT, artifact, observed_artifact, run_guarded
from wrt_exact import parse_store


P1_MAGIC = b"CMX21P1\0"


def read_p1(path: Path, expected_rows: int) -> np.ndarray:
    raw = path.read_bytes()
    if len(raw) < 16 or raw[:8] != P1_MAGIC:
        raise ValueError(f"invalid parent P1 trace: {path}")
    rows = struct.unpack_from("<Q", raw, 8)[0]
    values = np.frombuffer(raw, dtype="<u2", offset=16).copy()
    if rows != expected_rows or len(values) != expected_rows:
        raise ValueError(f"parent P1 row mismatch: {rows} != {expected_rows}")
    if np.any(values == 0):
        raise ValueError("parent P1 trace contains an illegal zero probability")
    return values


def range_decode(payload: bytes, probabilities: np.ndarray) -> np.ndarray:
    if len(payload) < 4:
        raise ValueError("range payload is too short")
    cursor = 4
    code = int.from_bytes(payload[:4], "big")
    low = 0
    high = 0xFFFFFFFF
    truth = np.empty(len(probabilities), dtype=np.uint8)
    for index, probability in enumerate(probabilities):
        p1 = int(probability)
        delta = high - low
        midpoint = low + (delta >> 16) * p1 + (((delta & 0xFFFF) * p1) >> 16)
        if code <= midpoint:
            truth[index] = 1
            high = midpoint
        else:
            truth[index] = 0
            low = midpoint + 1
        while ((low ^ high) & 0xFF000000) == 0:
            low = (low << 8) & 0xFFFFFFFF
            high = ((high << 8) & 0xFFFFFFFF) + 255
            next_byte = payload[cursor] if cursor < len(payload) else 0
            cursor += 1
            code = ((code << 8) & 0xFFFFFFFF) + next_byte
    return truth


def traced_encode(label: str, output_dir: Path, program: Path, raw_input: Path) -> dict[str, object]:
    archive = output_dir / f"archive_{label}.bin"
    trace = output_dir / f"native_{label}.p1"
    for path in (archive, trace):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite trace artifact: {path}")
    command = [
        "/usr/bin/env",
        f"CMIX_P1_TRACE={trace}",
        str(program),
        "c",
        str(raw_input),
        str(archive),
    ]
    phase = run_guarded(f"trace_{label}", output_dir, command)
    return {
        "archive": archive,
        "trace": trace,
        "phase": phase,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--raw-input", type=Path, default=PROJECT / "data/enwik9_1000000.bin"
    )
    parser.add_argument(
        "--wrt-store",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/results/fx2_wrt_store_1m.bin"),
    )
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=ORIGINAL / "clean-build-a/build/english.dic",
    )
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_input = args.raw_input.resolve()
    reference_archive = args.reference_archive.resolve()
    parsed = parse_store(args.wrt_store.resolve(), args.dictionary.resolve())
    raw = raw_input.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("recovered WRT store does not invert to canonical 1M input")
    truth = np.unpackbits(np.frombuffer(parsed.stream, dtype=np.uint8), bitorder="big")

    runs = {
        "a": traced_encode(
            "a", output_dir, (ORIGINAL / "clean-build-a/comp9a-decomp9").resolve(), raw_input
        ),
        "b": traced_encode(
            "b", output_dir, (ORIGINAL / "clean-build-b/comp9a-decomp9").resolve(), raw_input
        ),
    }
    reference = reference_archive.read_bytes()
    for name, run in runs.items():
        archive_bytes = run["archive"].read_bytes()
        if archive_bytes != reference:
            raise ValueError(f"trace-enabled archive {name} differs from recovered parent")

    p1_a = read_p1(runs["a"]["trace"], len(truth))
    p1_b = read_p1(runs["b"]["trace"], len(truth))
    if not np.array_equal(p1_a, p1_b):
        raise ValueError("independent clean parent P1 traces differ")

    parent_payload, header_bytes, declared_wrt_bytes = payload_codec.read_archive(reference_archive)
    if declared_wrt_bytes != len(parsed.stream):
        raise ValueError("archive WRT length differs from recovered WRT stream")
    replay_payload = payload_codec.encode_payload(p1_a, truth)
    if replay_payload != parent_payload:
        raise ValueError("parent P1 replay differs from receipt-bound arithmetic payload")
    decoded = range_decode(parent_payload, p1_a)
    if not np.array_equal(decoded, truth):
        raise ValueError("parent arithmetic decode differs from WRT truth")

    decision = {
        "schema": "endpoint428_exact_parent_p1_trace_gate_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "typed_event_sleeping_bayes_parent_trace_q0_v1",
        "evidence_level": "exact_pre_truth_frontier_parent_p1_trace_identity",
        "inputs": {
            "reference_archive": observed_artifact(reference_archive),
            "raw_input": observed_artifact(raw_input),
            "wrt_store": observed_artifact(args.wrt_store.resolve()),
            "dictionary": observed_artifact(args.dictionary.resolve()),
            "program_a": artifact(
                (ORIGINAL / "clean-build-a/comp9a-decomp9").resolve(),
                (2_326_416, "37ee8cd73ade9845b1afcb39f3bbd9358956c3ff9aea3b69328da7441ee32361"),
            ),
            "program_b": artifact(
                (ORIGINAL / "clean-build-b/comp9a-decomp9").resolve(),
                (2_326_416, "37ee8cd73ade9845b1afcb39f3bbd9358956c3ff9aea3b69328da7441ee32361"),
            ),
        },
        "artifacts": {
            "archive_a": observed_artifact(runs["a"]["archive"]),
            "archive_b": observed_artifact(runs["b"]["archive"]),
            "p1_a": observed_artifact(runs["a"]["trace"]),
            "p1_b": observed_artifact(runs["b"]["trace"]),
            "parent_payload_bytes": len(parent_payload),
            "parent_payload_sha256": hashlib.sha256(parent_payload).hexdigest(),
            "replay_payload_bytes": len(replay_payload),
            "replay_payload_sha256": hashlib.sha256(replay_payload).hexdigest(),
        },
        "scope": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(parsed.stream),
            "trace_rows": len(truth),
            "archive_header_bytes": header_bytes,
        },
        "proof": {
            "trace_enabled_archive_a_equals_parent": True,
            "trace_enabled_archive_b_equals_parent": True,
            "independent_p1_identity": True,
            "all_probabilities_legal_nonzero": True,
            "trace_rows_equal_wrt_truth_bits": True,
            "trace_replay_payload_identity": True,
            "exact_arithmetic_decode": True,
            "wrt_inverse_equals_canonical_raw": True,
            "decimal_memory_ok": all(
                run["phase"]["guard"]["official_decimal_over_limit_kib"] == 0
                for run in runs.values()
            ),
        },
        "decision": {
            "verdict": "exact_frontier_parent_trace_certified",
            "typed_event_shadow_authorized": True,
            "native_integration_authorized": False,
            "full_1g_authorized": False,
            "score_credit_bytes": 0,
            "next_action": "Freeze and run the opening-1M same-stream typed-event control family.",
        },
        "claim_boundary": "Observation-only repeated parent P1 trace tied to the recovered exact 1M archive, WRT truth, and canonical raw inverse. It changes no coded probability and earns zero score credit.",
    }
    decision_path = output_dir / "decision.json"
    temporary = decision_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(decision_path)
    print(json.dumps({"decision_path": str(decision_path), "verdict": decision["decision"]["verdict"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
