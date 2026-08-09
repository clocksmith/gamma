#!/usr/bin/env python3
"""Run the frozen source-native NNCP train_len=32 surrogate gate."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_trainlen32_surrogate_qm1_v1"
BINARY = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/nncp")
LIBRARY = BINARY.parent / "libnc.so"
INPUT = Path(
    "/home/x/enwiki9-nonproof/results/"
    "fx2_full_attribution_trace_1m_v1.restored"
)
BASELINE_ARCHIVE = ROOT / "results/nncp_v33_cpu_t16_archive_identity_q0_v1/t16_archive.bin"
BASELINE_BYTES = 9_246
BASELINE_SHA256 = "097102977cbaa563e460ef87bf88af99ae6409a5fa3902198316f0308300ffc5"
GAIN_GATE_BYTES = 500


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command: list[str], environment: dict[str, str]) -> dict[str, object]:
    started = time.monotonic()
    completed = subprocess.run(
        command,
        check=True,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "command": command,
        "elapsed_seconds": time.monotonic() - started,
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
    }


def main() -> int:
    required = (BINARY, LIBRARY, INPUT, BASELINE_ARCHIVE)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(f"missing inputs: {missing}")
    if (
        BASELINE_ARCHIVE.stat().st_size != BASELINE_BYTES
        or sha256(BASELINE_ARCHIVE) != BASELINE_SHA256
    ):
        raise ValueError("source-native 10,000-symbol baseline identity mismatch")

    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    archive_a = output_dir / "archive_a.nncp"
    archive_b = output_dir / "archive_b.nncp"
    restored = output_dir / "restored.raw"
    environment = os.environ.copy()
    environment["LD_LIBRARY_PATH"] = str(BINARY.parent)

    common = [
        str(BINARY),
        "-q",
        "-T",
        "4",
        "--profile",
        "enwik9",
        "--train_len",
        "32",
        "--d_pos",
        "288",
        "--preprocess",
        "16384,512",
        "--max_size",
        "10000",
        "c",
        str(INPUT),
    ]
    print(json.dumps({"event": "encode_a_start"}), flush=True)
    encode_a = run([*common, str(archive_a)], environment)
    print(
        json.dumps(
            {"archive_bytes": archive_a.stat().st_size, "event": "encode_a_complete"}
        ),
        flush=True,
    )
    print(json.dumps({"event": "encode_b_start"}), flush=True)
    encode_b = run([*common, str(archive_b)], environment)
    print(
        json.dumps(
            {"archive_bytes": archive_b.stat().st_size, "event": "encode_b_complete"}
        ),
        flush=True,
    )
    print(json.dumps({"event": "decode_start"}), flush=True)
    decode = run(
        [str(BINARY), "-q", "-T", "4", "d", str(archive_a), str(restored)],
        environment,
    )

    archive_identity = archive_a.read_bytes() == archive_b.read_bytes()
    restored_bytes = restored.read_bytes()
    raw_prefix_identity = INPUT.read_bytes().startswith(restored_bytes)
    candidate_bytes = archive_a.stat().st_size
    actual_gain = BASELINE_BYTES - candidate_bytes
    failed: list[str] = []
    if not archive_identity:
        failed.append("repeated_archives_differ")
    if not raw_prefix_identity or not restored_bytes:
        failed.append("raw_prefix_decode_failed")
    if actual_gain < GAIN_GATE_BYTES:
        failed.append("actual_gain_below_500")
    promotion = not failed

    decision = {
        "schema": "enwiki9_nncp_libnc_trainlen32_surrogate_qm1_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "AUTHORIZED_NATIVE_TRAINLEN32" if promotion else "REJECT",
        "verdict": (
            "authorize_exact_native_schedule_patch"
            if promotion
            else "retire_builtin_trainlen32_surrogate"
        ),
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Exact source-native 10,000-symbol built-in train_len=32 surrogate. "
            "It changes segment geometry and is not identical to the ROCm "
            "post-midpoint KV-rebuild schedule; no published or full-corpus "
            "score is inherited."
        ),
        "configuration": {
            "profile": "enwik9",
            "threads": 4,
            "batch_size": 32,
            "train_len": 32,
            "relative_positions": 288,
            "preprocess": "16384,512",
            "max_symbols": 10_000,
            "program_delta_bytes": 0,
        },
        "comparison": {
            "baseline_archive_bytes": BASELINE_BYTES,
            "baseline_archive_sha256": BASELINE_SHA256,
            "candidate_archive_bytes": candidate_bytes,
            "candidate_archive_sha256": sha256(archive_a),
            "actual_gain_bytes": actual_gain,
            "required_actual_gain_bytes": GAIN_GATE_BYTES,
        },
        "integrity": {
            "archive_repeat_byte_identical": archive_identity,
            "raw_prefix_decode_exact": raw_prefix_identity,
            "restored_raw_bytes": len(restored_bytes),
            "restored_raw_sha256": sha256(restored),
        },
        "execution": {
            "encode_a": encode_a,
            "encode_b": encode_b,
            "decode": decode,
        },
        "inputs": {
            "binary_bytes": BINARY.stat().st_size,
            "binary_sha256": sha256(BINARY),
            "library_bytes": LIBRARY.stat().st_size,
            "library_sha256": sha256(LIBRARY),
            "input_bytes": INPUT.stat().st_size,
            "input_sha256": sha256(INPUT),
            "baseline_archive_path": str(BASELINE_ARCHIVE),
            "driver_script_sha256": sha256(Path(__file__)),
        },
        "failed_conditions": failed,
        "decision": {
            "promotion_authorized": promotion,
            "verified_full_1g_score_bytes": None,
            "forecast_bytes": 109_389_323,
        },
    }
    decision_path = output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"nncp-libnc-trainlen32-surrogate-qm1: {error}", file=sys.stderr)
        raise
