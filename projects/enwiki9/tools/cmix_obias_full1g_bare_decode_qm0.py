#!/usr/bin/env python3
"""Independently bare-decode the hash-bound full cmix-obias archive."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_full1g_bare_decode_qm0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
ARCHIVE = Path("/home/x/enwiki9-nonproof/cmix-obias-donor/final/archive9")
CANONICAL = Path("/home/x/enwiki9-quarantine/mattmahoney-20260711/enwik9")
ARCHIVE_SHA256 = "664823c5d9f167bda342745d7b34a3ccb98fd7108723ba83643d9d09bf693900"
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
RAW_BYTES = 1_000_000_000
MIN_SCRATCH_FREE = 30_000_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(16 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def same_bytes(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as a, right.open("rb") as b:
        while True:
            aa = a.read(16 * 1024 * 1024)
            bb = b.read(16 * 1024 * 1024)
            if aa != bb:
                return False
            if not aa:
                return True


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def main() -> int:
    RESULT.mkdir(parents=True, exist_ok=True)
    decision_path = RESULT / "decision.json"
    if decision_path.exists():
        raise RuntimeError(f"refusing to overwrite terminal receipt: {decision_path}")

    archive_size = ARCHIVE.stat().st_size
    archive_hash = sha256(ARCHIVE)
    canonical_size = CANONICAL.stat().st_size
    canonical_hash = sha256(CANONICAL)
    if archive_size != 108_009_834 or archive_hash != ARCHIVE_SHA256:
        raise RuntimeError("external archive identity mismatch")
    if canonical_size != RAW_BYTES or canonical_hash != CANONICAL_SHA256:
        raise RuntimeError("canonical enwik9 identity mismatch")

    scratch_free_before = shutil.disk_usage("/dev/shm").free
    if scratch_free_before < MIN_SCRATCH_FREE:
        raise RuntimeError(
            f"insufficient /dev/shm space: {scratch_free_before} < {MIN_SCRATCH_FREE}"
        )

    scratch: Path | None = None
    started = time.time()
    result: dict[str, object] = {
        "schema": "enwiki9_cmix_obias_full1g_bare_decode_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "claim_boundary": (
            "Independent bare decode and resource observation of an external archive. "
            "Zero compression, score, source-eligibility, or committee-acceptance credit."
        ),
        "archive": {
            "path": str(ARCHIVE),
            "bytes": archive_size,
            "sha256": archive_hash,
        },
        "canonical": {
            "path": str(CANONICAL),
            "bytes": canonical_size,
            "sha256": canonical_hash,
        },
        "environment_contract": "empty environment; cwd is unique /dev/shm scratch",
        "scratch_free_before_bytes": scratch_free_before,
    }
    returncode: int | None = None
    peak_scratch_bytes = 0
    error: str | None = None

    try:
        scratch = Path(tempfile.mkdtemp(prefix=f"{CANDIDATE_ID}-", dir="/dev/shm"))
        (RESULT / "scratch_state.txt").write_text(f"active {scratch}\n")
        local_archive = scratch / "archive9"
        shutil.copyfile(ARCHIVE, local_archive)
        local_archive.chmod(0o755)
        log_path = RESULT / "decode.log"
        print(json.dumps({"event": "bare_decode_start", "scratch": str(scratch)}), flush=True)
        with log_path.open("wb") as log:
            process = subprocess.Popen(
                ["./archive9"],
                cwd=scratch,
                env={},
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            while process.poll() is None:
                current_free = shutil.disk_usage("/dev/shm").free
                peak_scratch_bytes = max(
                    peak_scratch_bytes, scratch_free_before - current_free
                )
                time.sleep(10)
            returncode = process.returncode

        current_free = shutil.disk_usage("/dev/shm").free
        peak_scratch_bytes = max(peak_scratch_bytes, scratch_free_before - current_free)
        output = scratch / "enwik9_uncompressed"
        output_exists = output.is_file()
        output_size = output.stat().st_size if output_exists else None
        output_hash = sha256(output) if output_exists else None
        byte_identity = output_exists and same_bytes(output, CANONICAL)
        log_hash = sha256(log_path)
        result.update(
            {
                "returncode": returncode,
                "output": {
                    "expected_path": str(output),
                    "exists": output_exists,
                    "bytes": output_size,
                    "sha256": output_hash,
                    "byte_identical_to_canonical": byte_identity,
                },
                "decode_log": {
                    "path": str(log_path),
                    "bytes": log_path.stat().st_size,
                    "sha256": log_hash,
                },
                "peak_scratch_bytes_observed": peak_scratch_bytes,
            }
        )
    except Exception as exc:  # preserve a terminal diagnostic before re-raising
        error = f"{type(exc).__name__}: {exc}"
        result["error"] = error
    finally:
        if scratch is not None:
            shutil.rmtree(scratch, ignore_errors=False)
            result["scratch_path"] = str(scratch)
            result["scratch_cleaned"] = not scratch.exists()
            (RESULT / "scratch_state.txt").write_text(f"cleaned {scratch}\n")
        result["elapsed_seconds_diagnostic"] = time.time() - started

    passed = bool(
        error is None
        and returncode == 0
        and result.get("output", {}).get("bytes") == RAW_BYTES
        and result.get("output", {}).get("sha256") == CANONICAL_SHA256
        and result.get("output", {}).get("byte_identical_to_canonical") is True
        and result.get("scratch_cleaned") is True
    )
    result["gates"] = {
        "returncode_zero": returncode == 0,
        "output_size_exact": result.get("output", {}).get("bytes") == RAW_BYTES,
        "output_sha256_exact": result.get("output", {}).get("sha256")
        == CANONICAL_SHA256,
        "byte_identity_exact": result.get("output", {}).get(
            "byte_identical_to_canonical"
        )
        is True,
        "scratch_cleaned": result.get("scratch_cleaned") is True,
    }
    result["overall_pass"] = passed
    result["verdict"] = (
        "bare_full_1g_decode_verified_resource_and_source_qualification_remain"
        if passed
        else "external_archive_bare_decode_rejected_or_incomplete"
    )
    write_json(decision_path, result)
    print(json.dumps({"event": "bare_decode_terminal", "overall_pass": passed}), flush=True)
    if error is not None:
        raise RuntimeError(error)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
