#!/usr/bin/env python3
"""Decode the hash-bound full cmix-obias archive in a sealed filesystem."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_full1g_sealedfs_decode_qm0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
DEPENDENCY = ROOT / "results" / "cmix_obias_full1g_bare_decode_qm0_v1" / "decision.json"
ARCHIVE = Path("/home/x/enwiki9-nonproof/cmix-obias-donor/final/archive9")
CANONICAL = Path("/home/x/enwiki9-quarantine/mattmahoney-20260711/enwik9")
BWRAP = Path("/usr/bin/bwrap")
RAW_BYTES = 1_000_000_000
ARCHIVE_BYTES = 108_009_834
ARCHIVE_SHA256 = "664823c5d9f167bda342745d7b34a3ccb98fd7108723ba83643d9d09bf693900"
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
DEPENDENCY_VERDICT = "bare_full_1g_decode_verified_resource_and_source_qualification_remain"
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
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    if not DEPENDENCY.is_file():
        raise FileNotFoundError(f"first full decode has not terminalized: {DEPENDENCY}")
    dependency = json.loads(DEPENDENCY.read_text())
    if not (
        dependency.get("overall_pass") is True
        and dependency.get("verdict") == DEPENDENCY_VERDICT
    ):
        raise RuntimeError("first full decode did not authorize sealed second decode")
    if not BWRAP.is_file():
        raise FileNotFoundError(BWRAP)
    if ARCHIVE.stat().st_size != ARCHIVE_BYTES or sha256(ARCHIVE) != ARCHIVE_SHA256:
        raise ValueError("external archive identity mismatch")
    if CANONICAL.stat().st_size != RAW_BYTES or sha256(CANONICAL) != CANONICAL_SHA256:
        raise ValueError("canonical enwik9 identity mismatch")
    scratch_free_before = shutil.disk_usage("/dev/shm").free
    if scratch_free_before < MIN_SCRATCH_FREE:
        raise RuntimeError(
            f"insufficient /dev/shm space: {scratch_free_before} < {MIN_SCRATCH_FREE}"
        )

    RESULT.mkdir(parents=True)
    scratch: Path | None = None
    result: dict[str, object] = {
        "schema": "enwiki9_cmix_obias_full1g_sealedfs_decode_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "claim_boundary": (
            "Independent sealed-filesystem second decode of an external full-1G "
            "archive. Zero compression, encoder-reproduction, source-eligibility, "
            "counted-score, or committee-acceptance credit."
        ),
        "score_credit_bytes": 0,
        "dependency": {
            "path": str(DEPENDENCY),
            "verdict": dependency.get("verdict"),
        },
        "archive": {
            "path": str(ARCHIVE),
            "bytes": ARCHIVE_BYTES,
            "sha256": ARCHIVE_SHA256,
        },
        "canonical": {
            "path": str(CANONICAL),
            "bytes": RAW_BYTES,
            "sha256": CANONICAL_SHA256,
        },
        "scratch_free_before_bytes": scratch_free_before,
    }
    error: str | None = None
    returncode: int | None = None
    peak_scratch_bytes = 0
    started = time.monotonic()
    try:
        scratch = Path(tempfile.mkdtemp(prefix=f"{CANDIDATE_ID}-", dir="/dev/shm"))
        local_archive = scratch / "archive9"
        shutil.copyfile(ARCHIVE, local_archive)
        local_archive.chmod(0o755)
        command = [
            str(BWRAP),
            "--unshare-all",
            "--die-with-parent",
            "--new-session",
            "--ro-bind",
            "/usr",
            "/usr",
            "--ro-bind",
            "/bin",
            "/bin",
            "--ro-bind",
            "/lib",
            "/lib",
            "--ro-bind",
            "/lib64",
            "/lib64",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            "--bind",
            str(scratch),
            "/work",
            "--chdir",
            "/work",
            "--clearenv",
            "--",
            "./archive9",
        ]
        log_path = RESULT / "decode.log"
        with log_path.open("wb") as log:
            process = subprocess.Popen(
                command,
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
        restored = scratch / "enwik9_uncompressed"
        output_exists = restored.is_file()
        output_size = restored.stat().st_size if output_exists else None
        output_hash = sha256(restored) if output_exists else None
        byte_identity = output_exists and same_bytes(restored, CANONICAL)
        result.update(
            {
                "command": command,
                "outer_environment": {},
                "filesystem_contract": {
                    "network_namespace_unshared": True,
                    "writable_paths": ["/work", "/tmp", "/dev"],
                    "read_only_standard_paths": ["/usr", "/bin", "/lib", "/lib64"],
                    "procfs_mounted_for_decoder_rss_control": True,
                    "host_data_paths_visible": False,
                },
                "returncode": returncode,
                "output": {
                    "exists": output_exists,
                    "bytes": output_size,
                    "sha256": output_hash,
                    "byte_identical_to_canonical": byte_identity,
                },
                "decode_log": {
                    "path": str(log_path),
                    "bytes": log_path.stat().st_size,
                    "sha256": sha256(log_path),
                },
                "peak_scratch_bytes_observed": peak_scratch_bytes,
            }
        )
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        result["error"] = error
    finally:
        if scratch is not None:
            shutil.rmtree(scratch, ignore_errors=False)
            result["scratch_path"] = str(scratch)
            result["scratch_cleaned"] = not scratch.exists()
        result["elapsed_seconds_diagnostic"] = time.monotonic() - started

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
        "output_sha256_exact": result.get("output", {}).get("sha256") == CANONICAL_SHA256,
        "byte_identity_exact": result.get("output", {}).get("byte_identical_to_canonical") is True,
        "scratch_cleaned": result.get("scratch_cleaned") is True,
    }
    result["overall_pass"] = passed
    result["verdict"] = (
        "sealed_full_1g_second_decode_verified"
        if passed
        else "sealed_full_1g_second_decode_rejected_or_incomplete"
    )
    write_json(RESULT / "decision.json", result)
    print(json.dumps({"event": "sealed_full1g_terminal", "overall_pass": passed}), flush=True)
    if error is not None:
        raise RuntimeError(error)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
