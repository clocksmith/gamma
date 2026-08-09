#!/usr/bin/env python3
"""Encode and bare-decode full enwik9 with the clean source-built program."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_full1g_roundtrip_a_qm0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
PROGRAM_REFERENCE = ROOT / "results" / "cmix_obias_source_1m_roundtrip_qm3_v1"
CANONICAL = Path("/home/x/enwiki9-quarantine/mattmahoney-20260711/enwik9")
RAW_BYTES = 1_000_000_000
TARGET_BYTES = 105_000_000
PRIZE_CEILING_BYTES = 109_685_196
TEMP_DISK_LIMIT_BYTES = 100_000_000_000
MIN_SCRATCH_FREE_BYTES = 35_000_000_000
EXPECTED = {
    "canonical": "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc",
    "cmix": "4ba53d3652c4e6de4126b4c03006e45a5f7e0511abd5d9661bf8132236ef1d2a",
    "head.blob": "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(16 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def same_bytes(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as a, right.open("rb") as b:
        while True:
            aa = a.read(16 << 20)
            bb = b.read(16 << 20)
            if aa != bb:
                return False
            if not aa:
                return True


def scratch_usage(root: Path) -> dict[str, int]:
    logical = 0
    allocated = 0
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            stat = path.stat()
            logical += stat.st_size
            allocated += stat.st_blocks * 512
    return {"logical_bytes": logical, "allocated_bytes": allocated}


def update_peak(peak: dict[str, int], observed: dict[str, int]) -> None:
    for key, value in observed.items():
        peak[key] = max(peak[key], value)


def terminate_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def run_stage(
    args: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    log_path: Path,
    scratch: Path,
    peak_scratch: dict[str, int],
) -> dict[str, object]:
    started = time.monotonic()
    disk_violation: dict[str, int] | None = None
    with log_path.open("wb") as log:
        process = subprocess.Popen(
            args,
            cwd=cwd,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        while process.poll() is None:
            observed = scratch_usage(scratch)
            update_peak(peak_scratch, observed)
            if max(observed.values()) > TEMP_DISK_LIMIT_BYTES:
                disk_violation = observed
                terminate_group(process)
                break
            time.sleep(15)
        returncode = process.wait()
    observed = scratch_usage(scratch)
    update_peak(peak_scratch, observed)
    receipt = {
        "command": args,
        "cwd": str(cwd),
        "environment": environment,
        "returncode": returncode,
        "elapsed_seconds_diagnostic": time.monotonic() - started,
        "log": artifact(log_path),
        "scratch_after": observed,
        "disk_violation": disk_violation,
    }
    if disk_violation is not None:
        raise RuntimeError(f"temporary-disk limit exceeded: {disk_violation}")
    if returncode != 0:
        raise RuntimeError(f"stage failed with return code {returncode}: {args}")
    return receipt


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def main() -> int:
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    RESULT.mkdir(parents=True)
    decision_path = RESULT / "decision.json"
    scratch: Path | None = None
    error: str | None = None
    peak_scratch = {"logical_bytes": 0, "allocated_bytes": 0}
    result: dict[str, object] = {
        "schema": "enwiki9_cmix_obias_source_full1g_roundtrip_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "claim_boundary": (
            "Exact source-built full-1G encode and bare inverse. Concurrent-run "
            "timing is diagnostic; final official eligibility remains separate."
        ),
        "target_bytes": TARGET_BYTES,
        "prize_ceiling_bytes": PRIZE_CEILING_BYTES,
        "score_credit_bytes": 0,
    }
    try:
        if CANONICAL.stat().st_size != RAW_BYTES or sha256(CANONICAL) != EXPECTED["canonical"]:
            raise ValueError("canonical enwik9 identity mismatch")
        for name in ("cmix", "head.blob"):
            path = PROGRAM_REFERENCE / name
            if not path.is_file() or sha256(path) != EXPECTED[name]:
                raise ValueError(f"source-built program reference mismatch: {name}")
        if shutil.disk_usage("/dev/shm").free < MIN_SCRATCH_FREE_BYTES:
            raise RuntimeError("insufficient free /dev/shm for full-corpus gate")

        scratch = Path(tempfile.mkdtemp(prefix=f"{CANDIDATE_ID}-", dir="/dev/shm"))
        encode_dir = scratch / "encode"
        encode_dir.mkdir()
        cmix = encode_dir / "cmix"
        head = encode_dir / "head.blob"
        shutil.copy2(PROGRAM_REFERENCE / "cmix", cmix)
        shutil.copy2(PROGRAM_REFERENCE / "head.blob", head)
        cmix.chmod(0o755)
        program = {
            "packaged_compressor": artifact(cmix),
            "head": artifact(head),
            "total_bytes": cmix.stat().st_size + head.stat().st_size,
        }
        result["program"] = program
        encode_environment = {
            "PATH": "/usr/bin:/bin",
            "KH_BITLSTM32": str(head.resolve()),
        }
        result["encode"] = run_stage(
            ["./cmix", "-e", str(CANONICAL), "out.cmix"],
            cwd=encode_dir,
            environment=encode_environment,
            log_path=RESULT / "encode.log",
            scratch=scratch,
            peak_scratch=peak_scratch,
        )
        payload = encode_dir / "out.cmix"
        archive = encode_dir / "archive9"
        if not payload.is_file() or not archive.is_file():
            raise FileNotFoundError("full encode did not produce payload and archive")
        shutil.copy2(payload, RESULT / "out.cmix")
        shutil.copy2(archive, RESULT / "archive9")
        result["payload"] = artifact(RESULT / "out.cmix")
        result["archive"] = artifact(RESULT / "archive9")
        counted_score = int(program["total_bytes"]) + archive.stat().st_size
        result["counted_score_bytes"] = counted_score

        shutil.rmtree(encode_dir)
        decode_dir = scratch / "decode"
        decode_dir.mkdir()
        local_archive = decode_dir / "archive9"
        shutil.copy2(RESULT / "archive9", local_archive)
        local_archive.chmod(0o755)
        result["decode"] = run_stage(
            ["./archive9"],
            cwd=decode_dir,
            environment={},
            log_path=RESULT / "decode.log",
            scratch=scratch,
            peak_scratch=peak_scratch,
        )
        restored = decode_dir / "enwik9_uncompressed"
        raw_exact = (
            restored.is_file()
            and restored.stat().st_size == RAW_BYTES
            and sha256(restored) == EXPECTED["canonical"]
            and same_bytes(restored, CANONICAL)
        )
        result["restored"] = {
            "exists": restored.is_file(),
            "bytes": restored.stat().st_size if restored.is_file() else None,
            "sha256": sha256(restored) if restored.is_file() else None,
            "byte_identical_to_canonical": raw_exact,
        }
        if not raw_exact:
            raise ValueError("full source-built archive did not reconstruct enwik9")
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        result["error"] = error
    finally:
        if scratch is not None:
            update_peak(peak_scratch, scratch_usage(scratch))
            shutil.rmtree(scratch, ignore_errors=False)
            result["scratch_path"] = str(scratch)
            result["scratch_cleaned"] = not scratch.exists()
        result["peak_scratch"] = peak_scratch

    score = result.get("counted_score_bytes")
    raw_exact = result.get("restored", {}).get("byte_identical_to_canonical") is True
    passed = bool(
        error is None
        and raw_exact
        and result.get("scratch_cleaned") is True
        and isinstance(score, int)
        and score <= PRIZE_CEILING_BYTES
    )
    result["gates"] = {
        "full_scope_exact": result.get("restored", {}).get("bytes") == RAW_BYTES,
        "raw_roundtrip_exact": raw_exact,
        "temporary_disk_within_100gb": max(peak_scratch.values()) <= TEMP_DISK_LIMIT_BYTES,
        "current_prize_ceiling_pass": isinstance(score, int) and score <= PRIZE_CEILING_BYTES,
        "project_105m_target_pass": isinstance(score, int) and score <= TARGET_BYTES,
        "scratch_cleaned": result.get("scratch_cleaned") is True,
    }
    result["overall_pass"] = passed
    result["verdict"] = (
        "source_built_full1g_roundtrip_prize_ceiling_candidate"
        if passed
        else "source_built_full1g_roundtrip_rejected_or_incomplete"
    )
    write_json(decision_path, result)
    print(json.dumps({"event": "full1g_terminal", "overall_pass": passed}), flush=True)
    if error is not None:
        raise RuntimeError(error)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
