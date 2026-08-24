#!/usr/bin/env python3
"""Terminalize the preserved Arm B full-1G run after its host OOM interruption.

This recovery tool is deliberately specific to the observed Arm B execution.
It never launches, signals, resumes, or cleans the codec or its scratch tree.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_full1g_roundtrip_b_qm0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
RUNTIME = ROOT / "operations" / "runtime"
LEASE = RUNTIME / "exclusive_full1g.json"
MEMORY = RUNTIME / "arm_b_memory_observation.json"
SCRATCH = Path("/dev/shm/cmix_obias_source_full1g_roundtrip_b_qm0_v1-9f67kctt")
TERMINAL_RECEIPT = RESULT / "oom-terminal-receipt.json"
DECISION = RESULT / "decision.json"
LEASE_SNAPSHOT = RESULT / "terminal-lease.json"
MEMORY_SNAPSHOT = RESULT / "terminal-memory-observation.json"
OOM_LOG = RESULT / "oom-journal.log"
EXPECTED = {
    "archive9": (108_022_224, "ade610d6391ac1aee59becf8694c73f4617d435ad0c96d48c372acc4f9450711"),
    "out.cmix": (107_730_531, "889aa8074e0a84eb89997986899f1ef9f7cc0e52e87d1d36f86899fc679f5490"),
}
WRAPPER_PID = 1_545_589
ENCODE_CODEC_PID = 1_545_692
DECODE_PID = 1_318_929
OOM_VICTIM_PID = 2_389_293
OOM_VICTIM_ANON_RSS_KIB = 84_222_224
ARCHIVE9_RSS_KIB = 9_029_448
OOM_EVENT_UTC = "2026-08-23T12:39:47Z"
MEMORY_LIMIT_KIB = 9_765_625
OBSERVED_VMHWM_KIB = 10_425_744


class TerminalizationError(Exception):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(16 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def write_atomic(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise TerminalizationError(f"short write: {temporary}")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def process_matches() -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            argv = [
                part.decode("utf-8", "replace")
                for part in (entry / "cmdline").read_bytes().split(b"\0")
                if part
            ]
            cwd = str((entry / "cwd").resolve())
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        joined = " ".join(argv)
        if CANDIDATE_ID in joined or "cmix_obias_source_full1g_roundtrip_b_qm0" in joined or cwd.startswith(str(SCRATCH)):
            matches.append({"pid": int(entry.name), "argv": argv, "cwd": cwd})
    return matches


def capture_oom_journal() -> bytes:
    commands = [
        [
            "journalctl", "-k", "--since", "2026-08-23 08:39:40",
            "--until", "2026-08-23 08:40:05", "--no-pager",
        ],
        [
            "journalctl", "--user", "--since", "2026-08-23 08:39:40",
            "--until", "2026-08-23 08:40:05", "--no-pager",
        ],
    ]
    sections: list[bytes] = []
    for command in commands:
        completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        sections.append(("$ " + " ".join(command) + "\n").encode() + completed.stdout)
    raw = b"\n".join(sections)
    required = [
        b"Out of memory: Killed process 2389293 (python3)",
        b"anon-rss:84222224kB",
        b"[1545589]",
        b"[1318929]",
        b"archive9",
        b"The kernel OOM killer killed some processes in this unit",
        b"Failed with result 'oom-kill'",
    ]
    missing = [value.decode("utf-8", "replace") for value in required if value not in raw]
    if missing:
        raise TerminalizationError(f"OOM journal evidence is incomplete: {missing}")
    return raw


def scratch_manifest() -> dict[str, object]:
    if not SCRATCH.is_dir():
        raise TerminalizationError(f"preserved scratch is missing: {SCRATCH}")
    files: list[dict[str, object]] = []
    logical = 0
    allocated = 0
    for path in sorted(SCRATCH.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        stat = path.stat()
        logical += stat.st_size
        allocated += stat.st_blocks * 512
        files.append(
            {
                "path": str(path.relative_to(SCRATCH)),
                "logical_bytes": stat.st_size,
                "allocated_bytes": stat.st_blocks * 512,
                "mtime_ns": stat.st_mtime_ns,
            }
        )
    if not files:
        raise TerminalizationError("preserved scratch contains no files")
    return {
        "path": str(SCRATCH),
        "present": True,
        "retained_unchanged": True,
        "content_hash_claimed": False,
        "logical_bytes": logical,
        "allocated_bytes": allocated,
        "files": files,
    }


def main() -> int:
    if DECISION.exists() or TERMINAL_RECEIPT.exists():
        raise TerminalizationError("Arm B terminal artifacts already exist; refusing overwrite")
    matches = process_matches()
    if matches:
        raise TerminalizationError(f"Arm B still has live processes: {matches}")
    for path in (LEASE, MEMORY, RESULT / "archive9", RESULT / "out.cmix", RESULT / "encode.log", RESULT / "decode.log"):
        if not path.is_file():
            raise TerminalizationError(f"required retained artifact is missing: {path}")
    lease = json.loads(LEASE.read_text())
    memory = json.loads(MEMORY.read_text())
    if lease.get("candidate_id") != CANDIDATE_ID or lease.get("lease_mode") != "read_only_sidecar":
        raise TerminalizationError("stale lease does not bind the expected Arm B sidecar")
    if lease.get("pid") != WRAPPER_PID or lease.get("codec_pid") != ENCODE_CODEC_PID:
        raise TerminalizationError("stale lease PID identity differs from observed Arm B")
    if memory.get("candidate_id") != CANDIDATE_ID or memory.get("memory_pass") is not False:
        raise TerminalizationError("memory observation does not preserve the expected failure")
    if memory.get("observed_vm_hwm_kib") != OBSERVED_VMHWM_KIB:
        raise TerminalizationError("memory observation VmHWM differs from terminal lock")
    for name, (expected_bytes, expected_sha256) in EXPECTED.items():
        path = RESULT / name
        if path.stat().st_size != expected_bytes or sha256(path) != expected_sha256:
            raise TerminalizationError(f"retained Arm B artifact mismatch: {name}")
    decode_raw = (RESULT / "decode.log").read_bytes()
    progress = [float(value) for value in re.findall(rb"progress: ([0-9]+(?:\.[0-9]+)?)%", decode_raw)]
    if not progress or progress[-1] != 39.07:
        raise TerminalizationError(f"unexpected terminal decode progress: {progress[-1:]}")

    program_reference = ROOT / "results" / "cmix_obias_source_1m_roundtrip_qm3_v1"
    for path in (program_reference / "cmix", program_reference / "head.blob"):
        if not path.is_file():
            raise TerminalizationError(f"required packaged-program reference is missing: {path}")
    program = {
        "packaged_compressor": artifact(program_reference / "cmix"),
        "head": artifact(program_reference / "head.blob"),
        "total_bytes": 491_483,
    }

    journal_raw = capture_oom_journal()
    scratch = scratch_manifest()
    shutil.copyfile(LEASE, LEASE_SNAPSHOT)
    shutil.copyfile(MEMORY, MEMORY_SNAPSHOT)
    write_atomic(OOM_LOG, journal_raw)
    lease_snapshot_artifact = artifact(LEASE_SNAPSHOT)
    memory_snapshot_artifact = artifact(MEMORY_SNAPSHOT)
    oom_artifact = artifact(OOM_LOG)

    LEASE.unlink()
    MEMORY.unlink()

    receipt = {
        "$schema": "../../contracts/research/v1/cmix-obias-full1g-oom-terminal-receipt.schema.json",
        "schema": "gamma.enwiki9.cmix-obias-full1g-oom-terminal.v1",
        "candidate_id": CANDIDATE_ID,
        "terminal_status": "infrastructure_failure",
        "failure_class": "host_oom_scope_termination",
        "claim_boundary": (
            "Host-local terminalization of the preserved Arm B execution. The completed encode "
            "is retained, the inverse is incomplete, strict memory failed, and no determinism, "
            "official verification, Gamma authorship, or score credit follows."
        ),
        "score_credit_bytes": 0,
        "observed": {
            "wrapper_pid": WRAPPER_PID,
            "bound_encode_codec_pid": ENCODE_CODEC_PID,
            "decode_pid": DECODE_PID,
            "all_bound_processes_absent": True,
            "decode_last_progress_percent": progress[-1],
            "oom_event_utc": OOM_EVENT_UTC,
            "oom_selected_victim_pid": OOM_VICTIM_PID,
            "oom_selected_victim_anon_rss_kib": OOM_VICTIM_ANON_RSS_KIB,
            "archive9_rss_kib_at_oom": ARCHIVE9_RSS_KIB,
            "wrapper_present_in_oom_snapshot": True,
            "archive9_present_in_oom_snapshot": True,
            "tmux_scope_failed_oom": True,
        },
        "artifacts": {
            "archive": artifact(RESULT / "archive9"),
            "payload": artifact(RESULT / "out.cmix"),
            "encode_log": artifact(RESULT / "encode.log"),
            "decode_log": artifact(RESULT / "decode.log"),
            "terminal_lease_snapshot": lease_snapshot_artifact,
            "memory_observation_snapshot": memory_snapshot_artifact,
            "oom_journal": oom_artifact,
        },
        "resource": {
            "strict_decimal_limit_kib": MEMORY_LIMIT_KIB,
            "observed_vmhwm_kib": OBSERVED_VMHWM_KIB,
            "over_limit_kib": OBSERVED_VMHWM_KIB - MEMORY_LIMIT_KIB,
            "strict_memory_pass": False,
            "memory_failure_irrevocable_for_execution": True,
        },
        "scratch": scratch,
        "runtime_marker_disposition": {
            "lease_archived_before_removal": True,
            "memory_observation_archived_before_removal": True,
            "live_lease_removed": True,
            "live_memory_observation_removed": True,
        },
        "next_action": (
            "Preserve Arm B unchanged and qualify the correction-only file-backed memory-safe "
            "parent from the smallest controlled identity and resource gate."
        ),
    }
    write_atomic(TERMINAL_RECEIPT, canonical_json(receipt))

    decision = {
        "schema": "enwiki9_cmix_obias_source_full1g_roundtrip_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "claim_boundary": receipt["claim_boundary"],
        "target_bytes": 105_000_000,
        "prize_ceiling_bytes": 109_685_196,
        "score_credit_bytes": 0,
        "program": program,
        "encode": {
            "returncode": 0,
            "terminal_inference": "wrapper entered decode after retaining payload and archive",
            "log": artifact(RESULT / "encode.log"),
        },
        "payload": artifact(RESULT / "out.cmix"),
        "archive": artifact(RESULT / "archive9"),
        "counted_score_bytes": 108_513_707,
        "decode": {
            "returncode": None,
            "terminal_status": "interrupted_by_host_oom_scope_failure",
            "last_progress_percent": progress[-1],
            "log": artifact(RESULT / "decode.log"),
        },
        "restored": {
            "exists": False,
            "bytes": None,
            "sha256": None,
            "byte_identical_to_canonical": False,
        },
        "error": "HostOOMScopeTermination: Arm B wrapper and decode exited without terminal receipt",
        "scratch_path": str(SCRATCH),
        "scratch_cleaned": False,
        "peak_scratch": {
            "logical_bytes": scratch["logical_bytes"],
            "allocated_bytes": scratch["allocated_bytes"],
        },
        "resource": receipt["resource"],
        "terminal_receipt": artifact(TERMINAL_RECEIPT),
        "gates": {
            "full_scope_exact": False,
            "raw_roundtrip_exact": False,
            "temporary_disk_within_100gb": max(
                int(scratch["logical_bytes"]), int(scratch["allocated_bytes"])
            ) <= 100_000_000_000,
            "current_prize_ceiling_pass": True,
            "project_105m_target_pass": False,
            "scratch_cleaned": False,
            "strict_memory_pass": False,
        },
        "overall_pass": False,
        "verdict": "source_built_full1g_roundtrip_infrastructure_oom_incomplete",
    }
    write_atomic(DECISION, canonical_json(decision))
    print(canonical_json({"event": "arm_b_oom_terminalized", "overall_pass": False}).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
