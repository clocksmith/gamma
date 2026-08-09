#!/usr/bin/env python3
"""Run the exact native NNCP midpoint schedule at 65,536 symbols."""

from __future__ import annotations

import hashlib
import json
import lzma
import os
from pathlib import Path
import subprocess
import tempfile
import time

import nncp_libnc_exact_midsegment32_qm2 as q2


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_exact_midsegment32_65536_qm3_v1"
SYMBOL_COUNT = 65_536
GAIN_GATE_BYTES = 3_000
PARENT_DECISION = ROOT / "results/nncp_libnc_exact_midsegment32_qm2_v1/decision.json"
PARENT_DECISION_SHA256 = "71032efdb387c62dd09057d843041b7a838fe53a9b2cb5ea3d0b3862025283f3"


def run(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
) -> dict[str, object]:
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        check=True,
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
    required = (q2.SOURCE_TAR, q2.PATCH, q2.INPUT, PARENT_DECISION)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(f"missing inputs: {missing}")
    if q2.sha256(q2.SOURCE_TAR) != q2.EXPECTED["source_tar"]:
        raise ValueError("NNCP source-tar identity mismatch")
    if q2.sha256(PARENT_DECISION) != PARENT_DECISION_SHA256:
        raise ValueError("exact native parent decision identity mismatch")

    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    baseline_archive = output_dir / "baseline.nncp"
    candidate_archive = output_dir / "candidate.nncp"
    restored = output_dir / "restored.raw"

    with tempfile.TemporaryDirectory(prefix="nncp-exact-midsegment32-65536-") as tmp:
        build_root = Path(tmp)
        extract = run(
            ["tar", "-xzf", str(q2.SOURCE_TAR), "-C", str(build_root)],
            cwd=build_root,
        )
        source_root = build_root / "nncp-2024-06-05"
        build_parent = run(["make", "-j4"], cwd=source_root)
        binary = source_root / "nncp"
        environment = os.environ.copy()
        environment["LD_LIBRARY_PATH"] = str(source_root)
        common = [
            str(binary),
            "-q",
            "-T",
            "4",
            "--profile",
            "enwik9",
            "--preprocess",
            "16384,512",
            "--max_size",
            str(SYMBOL_COUNT),
        ]
        print(json.dumps({"event": "baseline_encode_start"}), flush=True)
        baseline_encode = run(
            [*common, "c", str(q2.INPUT), str(baseline_archive)],
            cwd=source_root,
            environment=environment,
        )
        print(
            json.dumps(
                {
                    "archive_bytes": baseline_archive.stat().st_size,
                    "event": "baseline_encode_complete",
                }
            ),
            flush=True,
        )
        patch_run = run(
            ["patch", "-p1", "-i", str(q2.PATCH)],
            cwd=source_root,
        )
        build_candidate = run(["make", "-j4"], cwd=source_root)
        candidate_binary = {
            "bytes": binary.stat().st_size,
            "sha256": q2.sha256(binary),
        }
        print(json.dumps({"event": "candidate_encode_start"}), flush=True)
        candidate_encode = run(
            [
                *common[:-2],
                "--midsegment32",
                *common[-2:],
                "c",
                str(q2.INPUT),
                str(candidate_archive),
            ],
            cwd=source_root,
            environment=environment,
        )
        print(
            json.dumps(
                {
                    "archive_bytes": candidate_archive.stat().st_size,
                    "event": "candidate_encode_complete",
                }
            ),
            flush=True,
        )
        print(json.dumps({"event": "candidate_decode_start"}), flush=True)
        candidate_decode = run(
            [str(binary), "-q", "-T", "4", "d", str(candidate_archive), str(restored)],
            cwd=source_root,
            environment=environment,
        )

    baseline_bytes = baseline_archive.stat().st_size
    candidate_bytes = candidate_archive.stat().st_size
    actual_gain = baseline_bytes - candidate_bytes
    restored_bytes = restored.read_bytes()
    raw_prefix_identity = bool(restored_bytes) and q2.INPUT.read_bytes().startswith(restored_bytes)
    schedule_header = q2.serialized_schedule_header(candidate_archive)
    compressed_patch_bytes = len(lzma.compress(q2.PATCH.read_bytes(), preset=9))
    source_package_bytes = q2.SOURCE_TAR.stat().st_size + compressed_patch_bytes
    failed: list[str] = []
    if actual_gain < GAIN_GATE_BYTES:
        failed.append("actual_gain_below_3000")
    if not raw_prefix_identity:
        failed.append("raw_prefix_decode_failed")
    if not schedule_header["valid"]:
        failed.append("serialized_schedule_header_invalid")
    if source_package_bytes > q2.MAX_SOURCE_PACKAGE_BYTES:
        failed.append("source_package_above_1300000")
    promotion = not failed

    decision = {
        "schema": "enwiki9_nncp_libnc_exact_midsegment32_65536_qm3_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "AUTHORIZED_NATIVE_LARGER_GATE" if promotion else "REJECT",
        "verdict": "authorize_exact_native_larger_gate" if promotion else "retire_exact_native_maturity_promotion",
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Fresh clean-source parent and exact patched candidate on the same "
            "65,536 post-preprocess symbols, with patched raw decode. This is "
            "not a full-corpus score or runtime-eligibility receipt."
        ),
        "configuration": {
            "profile": "enwik9",
            "threads": 4,
            "batch_size": 32,
            "segment_length": 64,
            "midpoint": 32,
            "symbols": SYMBOL_COUNT,
            "preprocess": "16384,512",
        },
        "comparison": {
            "baseline_archive_bytes": baseline_bytes,
            "baseline_archive_sha256": q2.sha256(baseline_archive),
            "candidate_archive_bytes": candidate_bytes,
            "candidate_archive_sha256": q2.sha256(candidate_archive),
            "actual_gain_bytes": actual_gain,
            "required_actual_gain_bytes": GAIN_GATE_BYTES,
            "gain_bytes_per_million_symbols": actual_gain * 1_000_000.0 / SYMBOL_COUNT,
        },
        "integrity": {
            "raw_prefix_decode_exact": raw_prefix_identity,
            "restored_raw_bytes": len(restored_bytes),
            "restored_raw_sha256": q2.sha256(restored),
            "serialized_schedule_header": schedule_header,
        },
        "program_accounting": {
            "source_tar_bytes": q2.SOURCE_TAR.stat().st_size,
            "patch_bytes": q2.PATCH.stat().st_size,
            "compressed_patch_bytes": compressed_patch_bytes,
            "complete_source_package_bytes": source_package_bytes,
            "maximum_source_package_bytes": q2.MAX_SOURCE_PACKAGE_BYTES,
            "compiled_candidate_binary": candidate_binary,
        },
        "execution": {
            "extract": extract,
            "build_parent": build_parent,
            "baseline_encode": baseline_encode,
            "patch": patch_run,
            "build_candidate": build_candidate,
            "candidate_encode": candidate_encode,
            "candidate_decode": candidate_decode,
        },
        "inputs": {
            "source_tar": {
                "path": str(q2.SOURCE_TAR),
                "bytes": q2.SOURCE_TAR.stat().st_size,
                "sha256": q2.sha256(q2.SOURCE_TAR),
            },
            "patch": {
                "path": str(q2.PATCH),
                "bytes": q2.PATCH.stat().st_size,
                "sha256": q2.sha256(q2.PATCH),
            },
            "input": {
                "path": str(q2.INPUT),
                "bytes": q2.INPUT.stat().st_size,
                "sha256": q2.sha256(q2.INPUT),
            },
            "parent_decision": {
                "path": str(PARENT_DECISION),
                "bytes": PARENT_DECISION.stat().st_size,
                "sha256": q2.sha256(PARENT_DECISION),
            },
        },
        "failed_conditions": failed,
        "decision": {
            "promotion_authorized": promotion,
            "verified_full_1g_score_bytes": None,
            "forecast_bytes": 109_389_323,
            "target_bytes": 105_000_000,
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
        print(f"nncp-libnc-exact-midsegment32-65536-qm3: {error}", file=os.sys.stderr)
        raise
