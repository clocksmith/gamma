#!/usr/bin/env python3
"""Bare-decode the source-built opening archive in a sealed filesystem."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_sealedfs_1m_decode_qm0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
ARCHIVE = ROOT / "results" / "cmix_obias_source_1m_roundtrip_qm3_v1" / "archive9"
CANONICAL = Path("/home/x/enwiki9-quarantine/mattmahoney-20260711/enwik9")
BWRAP = Path("/usr/bin/bwrap")
RAW_BYTES = 1_000_000
EXPECTED_ARCHIVE = "9065eaf54f81e441598fd53c39f909db49d6a9627ae0456eabb8c77099b8ccc4"
EXPECTED_RAW = "369b688978f649681136198fb96db14c1616756260c55fb4b65e9bc049552cad"


def sha256(path: Path, limit: int | None = None) -> str:
    digest = hashlib.sha256()
    remaining = limit
    with path.open("rb") as source:
        while remaining is None or remaining > 0:
            size = 8 << 20 if remaining is None else min(8 << 20, remaining)
            chunk = source.read(size)
            if not chunk:
                break
            digest.update(chunk)
            if remaining is not None:
                remaining -= len(chunk)
    return digest.hexdigest()


def scratch_usage(root: Path) -> dict[str, int]:
    logical = 0
    allocated = 0
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            stat = path.stat()
            logical += stat.st_size
            allocated += stat.st_blocks * 512
    return {"logical_bytes": logical, "allocated_bytes": allocated}


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def main() -> int:
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    RESULT.mkdir(parents=True)
    if not BWRAP.is_file():
        raise FileNotFoundError(BWRAP)
    if ARCHIVE.stat().st_size != 464_298 or sha256(ARCHIVE) != EXPECTED_ARCHIVE:
        raise ValueError("opening archive identity mismatch")
    if CANONICAL.stat().st_size != 1_000_000_000 or sha256(CANONICAL, RAW_BYTES) != EXPECTED_RAW:
        raise ValueError("canonical opening population mismatch")

    scratch: Path | None = None
    result: dict[str, object] = {
        "schema": "enwiki9_cmix_obias_sealedfs_1m_decode_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "claim_boundary": (
            "Opening-1M sealed-filesystem inverse preflight. It proves no "
            "full-corpus score, determinism, or final resource eligibility."
        ),
        "score_credit_bytes": 0,
        "archive": {
            "path": str(ARCHIVE),
            "bytes": ARCHIVE.stat().st_size,
            "sha256": EXPECTED_ARCHIVE,
        },
        "population": {"bytes": RAW_BYTES, "sha256": EXPECTED_RAW},
    }
    error: str | None = None
    returncode: int | None = None
    started = time.monotonic()
    try:
        scratch = Path(tempfile.mkdtemp(prefix=f"{CANDIDATE_ID}-", dir="/dev/shm"))
        local_archive = scratch / "archive9"
        shutil.copy2(ARCHIVE, local_archive)
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
            completed = subprocess.run(
                command,
                env={},
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        returncode = completed.returncode
        restored = scratch / "enwik9_uncompressed"
        raw_exact = (
            restored.is_file()
            and restored.stat().st_size == RAW_BYTES
            and sha256(restored) == EXPECTED_RAW
        )
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
                    "exists": restored.is_file(),
                    "bytes": restored.stat().st_size if restored.is_file() else None,
                    "sha256": sha256(restored) if restored.is_file() else None,
                    "raw_exact": raw_exact,
                },
                "decode_log": {
                    "path": str(log_path),
                    "bytes": log_path.stat().st_size,
                    "sha256": sha256(log_path),
                },
                "scratch_before_cleanup": scratch_usage(scratch),
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
        and result.get("output", {}).get("raw_exact") is True
        and result.get("scratch_cleaned") is True
    )
    result["overall_pass"] = passed
    result["verdict"] = (
        "authorize_sealed_filesystem_full1g_second_decode"
        if passed
        else "sealed_filesystem_decode_preflight_rejected_or_incomplete"
    )
    write_json(RESULT / "decision.json", result)
    print(json.dumps({"event": "sealedfs_terminal", "overall_pass": passed}), flush=True)
    if error is not None:
        raise RuntimeError(error)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
