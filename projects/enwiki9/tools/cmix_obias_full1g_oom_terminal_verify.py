#!/usr/bin/env python3
"""Independently verify the preserved Arm B OOM terminalization."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_full1g_roundtrip_b_qm0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
RECEIPT = RESULT / "oom-terminal-receipt.json"
DECISION = RESULT / "decision.json"
SCRATCH = Path("/dev/shm/cmix_obias_source_full1g_roundtrip_b_qm0_v1-9f67kctt")
BOUND_PIDS = (1_545_589, 1_545_692, 1_318_929, 2_389_293)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(16 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_matches(record: dict[str, Any]) -> bool:
    path = Path(record.get("path", ""))
    return bool(
        path.is_file()
        and path.stat().st_size == record.get("bytes")
        and sha256(path) == record.get("sha256")
    )


def write_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise OSError(f"short write: {temporary}")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def process_absent() -> bool:
    if any((Path("/proc") / str(pid)).exists() for pid in BOUND_PIDS):
        return False
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cwd = str((entry / "cwd").resolve())
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if cwd.startswith(str(SCRATCH)):
            return False
    return True


def verify() -> tuple[dict[str, object], bool]:
    errors: list[str] = []
    if not RECEIPT.is_file() or not DECISION.is_file():
        errors.append("terminal receipt or decision is missing")
        return {}, False
    receipt = json.loads(RECEIPT.read_text())
    decision = json.loads(DECISION.read_text())
    checks = {
        "receipt_schema": receipt.get("schema") == "gamma.enwiki9.cmix-obias-full1g-oom-terminal.v1",
        "receipt_candidate": receipt.get("candidate_id") == CANDIDATE_ID,
        "decision_candidate": decision.get("candidate_id") == CANDIDATE_ID,
        "decision_terminal_failure": decision.get("overall_pass") is False
        and decision.get("verdict") == "source_built_full1g_roundtrip_infrastructure_oom_incomplete",
        "zero_score_credit": receipt.get("score_credit_bytes") == decision.get("score_credit_bytes") == 0,
        "encode_artifacts_match": all(
            artifact_matches(receipt["artifacts"][name]) for name in ("archive", "payload", "encode_log")
        ),
        "decode_log_matches": artifact_matches(receipt["artifacts"]["decode_log"]),
        "terminal_evidence_matches": all(
            artifact_matches(receipt["artifacts"][name])
            for name in ("terminal_lease_snapshot", "memory_observation_snapshot", "oom_journal")
        ),
        "archive_expected": receipt["artifacts"]["archive"].get("bytes") == 108_022_224
        and receipt["artifacts"]["archive"].get("sha256")
        == "ade610d6391ac1aee59becf8694c73f4617d435ad0c96d48c372acc4f9450711",
        "payload_expected": receipt["artifacts"]["payload"].get("bytes") == 107_730_531
        and receipt["artifacts"]["payload"].get("sha256")
        == "889aa8074e0a84eb89997986899f1ef9f7cc0e52e87d1d36f86899fc679f5490",
        "decode_progress_terminal": receipt["observed"].get("decode_last_progress_percent") == 39.07,
        "memory_failure_preserved": receipt["resource"].get("strict_memory_pass") is False
        and receipt["resource"].get("observed_vmhwm_kib") == 10_425_744,
        "oom_evidence_preserved": b"Out of memory: Killed process 2389293 (python3)"
        in Path(receipt["artifacts"]["oom_journal"]["path"]).read_bytes(),
        "bound_processes_absent": process_absent(),
        "scratch_retained": SCRATCH.is_dir() and receipt["scratch"].get("retained_unchanged") is True,
        "live_runtime_markers_absent": not (ROOT / "operations/runtime/exclusive_full1g.json").exists()
        and not (ROOT / "operations/runtime/arm_b_memory_observation.json").exists(),
        "decision_binds_receipt": artifact_matches(decision["terminal_receipt"]),
        "no_false_inverse": decision["restored"].get("byte_identical_to_canonical") is False
        and decision["gates"].get("raw_roundtrip_exact") is False,
    }
    for name, passed in checks.items():
        if not passed:
            errors.append(f"check failed: {name}")
    output: dict[str, object] = {
        "schema": "gamma.enwiki9.cmix-obias-full1g-oom-terminal-verification.v1",
        "candidate_id": CANDIDATE_ID,
        "verified": not errors,
        "checks": checks,
        "errors": errors,
    }
    return output, not errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        output, verified = verify()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        output = {
            "schema": "gamma.enwiki9.cmix-obias-full1g-oom-terminal-verification.v1",
            "candidate_id": CANDIDATE_ID,
            "verified": False,
            "checks": {},
            "errors": [f"{type(exc).__name__}: {exc}"],
        }
        verified = False
    payload = (json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if args.output is not None:
        write_atomic(args.output, payload)
    sys.stdout.write(payload.decode())
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
