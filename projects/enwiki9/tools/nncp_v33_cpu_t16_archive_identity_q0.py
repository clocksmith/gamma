#!/usr/bin/env python3
"""Run the source-native NNCP CPU T16 archive-identity gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_cpu_t16_archive_identity_q0_v1"
REFERENCE_BYTES = 9_246
REFERENCE_SHA256 = (
    "097102977cbaa563e460ef87bf88af99ae6409a5fa3902198316f0308300ffc5"
)
REFERENCE_SECONDS = 279.797
REQUIRED_REDUCTION = 0.50
LIMIT_KIB = 9_765_625


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binary",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/nncp"),
    )
    parser.add_argument(
        "--library",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/libnc.so"),
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "fx2_full_attribution_trace_1m_v1.restored"
        ),
    )
    parser.add_argument(
        "--reference-archive",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "nncp_teacher_trace_smoke_v1/trace_off.bin"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID,
    )
    parser.add_argument("--threads", type=int, default=16)
    args = parser.parse_args()
    decision_path = args.output_dir / "decision.json"
    if decision_path.exists():
        raise FileExistsError("refusing to overwrite a CPU concurrency decision")
    required = (args.binary, args.library, args.input, args.reference_archive)
    if not all(path.is_file() for path in required):
        raise SystemExit("missing NNCP binary, library, input, or reference archive")
    if args.threads != 16:
        raise ValueError("Q0 freezes exactly 16 LibNC CPU workers")
    if (
        args.reference_archive.stat().st_size != REFERENCE_BYTES
        or sha256(args.reference_archive) != REFERENCE_SHA256
    ):
        raise ValueError("reference T4 archive identity mismatch")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    archive = args.output_dir / "t16_archive.bin"
    guard = args.output_dir / "rss_guard.json"
    command = [
        str(args.binary.resolve()),
        "-q",
        "-T",
        str(args.threads),
        "--profile",
        "enwik9",
        "--preprocess",
        "16384,512",
        "--max_size",
        "10000",
        "c",
        str(args.input.resolve()),
        str(archive.resolve()),
    ]
    guarded_command = [
        sys.executable,
        str((ROOT / "tools/run_with_rss_guard.py").resolve()),
        "--limit-kib",
        str(LIMIT_KIB),
        "--limit-mode",
        "tree",
        "--official-decimal-limit-kib",
        str(LIMIT_KIB),
        "--sample-interval",
        "0.2",
        "--guard-json",
        str(guard.resolve()),
        "--label",
        CANDIDATE_ID,
        "--",
        *command,
    ]
    environment = dict(os.environ)
    environment.pop("NNCP_TEACHER_TRACE", None)
    environment.pop("NNCP_BRANCH_TRACE", None)
    completed = subprocess.run(
        guarded_command,
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if not guard.is_file():
        raise RuntimeError("RSS guard did not produce a receipt")
    guard_receipt = json.loads(guard.read_text())
    if completed.returncode != 0 or guard_receipt.get("status") != "complete":
        raise RuntimeError(
            "guarded T16 execution failed: "
            f"returncode={completed.returncode} status={guard_receipt.get('status')}"
        )
    if not archive.is_file():
        raise RuntimeError("T16 execution did not produce an archive")
    archive_bytes = archive.stat().st_size
    archive_sha256 = sha256(archive)
    archive_identity = (
        archive_bytes == REFERENCE_BYTES
        and archive_sha256 == REFERENCE_SHA256
        and archive.read_bytes() == args.reference_archive.read_bytes()
    )
    elapsed = float(guard_receipt["elapsed_s"])
    elapsed_reduction = 1.0 - elapsed / REFERENCE_SECONDS
    memory_clean = (
        not guard_receipt.get("rss_guard_exceeded", False)
        and int(guard_receipt["max_sampled_single_rss_kib"]) <= LIMIT_KIB
    )
    passed = (
        archive_identity
        and memory_clean
        and elapsed_reduction >= REQUIRED_REDUCTION
    )
    result = {
        "schema": "gamma.nncp_v33_cpu_t16_archive_identity_q0.v1",
        "candidate_id": CANDIDATE_ID,
        "status": "PASS" if passed else "REJECT",
        "score_credit_bytes": 0,
        "contract": {
            "profile": "enwik9",
            "batch_size": 32,
            "teacher_symbols": 10_000,
            "reference_threads": 4,
            "candidate_threads": args.threads,
            "reference_elapsed_seconds": REFERENCE_SECONDS,
            "required_elapsed_reduction_fraction": REQUIRED_REDUCTION,
            "decimal_memory_limit_kib": LIMIT_KIB,
        },
        "inputs": {
            "script_sha256": sha256(Path(__file__).resolve()),
            "binary_bytes": args.binary.stat().st_size,
            "binary_sha256": sha256(args.binary),
            "library_bytes": args.library.stat().st_size,
            "library_sha256": sha256(args.library),
            "input_bytes": args.input.stat().st_size,
            "input_sha256": sha256(args.input),
            "reference_archive_bytes": REFERENCE_BYTES,
            "reference_archive_sha256": REFERENCE_SHA256,
            "logical_cpu_count": os.cpu_count(),
        },
        "execution": {
            "command": command,
            "guarded_command": guarded_command,
            "guard_stdout_sha256": hashlib.sha256(
                completed.stdout.encode()
            ).hexdigest(),
            "guard_stderr_sha256": hashlib.sha256(
                completed.stderr.encode()
            ).hexdigest(),
            "archive_bytes": archive_bytes,
            "archive_sha256": archive_sha256,
            "archive_byte_identical": archive_identity,
            "elapsed_seconds": elapsed,
            "elapsed_reduction_fraction": elapsed_reduction,
            "max_sampled_single_rss_kib": guard_receipt[
                "max_sampled_single_rss_kib"
            ],
            "max_sampled_tree_rss_kib": guard_receipt[
                "max_sampled_tree_rss_kib"
            ],
            "memory_clean": memory_clean,
            "rss_guard_sha256": sha256(guard),
        },
        "decision": {
            "promotion_authorized": passed,
            "authorized_next_action": (
                "freeze one T16 trace-off/trace-on/decode identity gate"
                if passed
                else "retire local NNCP CPU thread scaling"
            ),
            "forecast_bytes": 109_389_323,
            "verified_full_1g_score_bytes": None,
        },
    }
    decision_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
