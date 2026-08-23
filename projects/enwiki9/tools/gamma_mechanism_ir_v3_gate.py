#!/usr/bin/env python3
"""Bind a verified Mechanism IR source lock to independent compiler evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any


OUTPUT_SCHEMA = "gamma.enwiki9.gamma-mechanism-ir-v3-gate.v1"
COMPILER_PATH = "projects/enwiki9/tools/gamma_mechanism_ir_compile_v2.py"
IR_PATH = "projects/enwiki9/operations/planning/cmix_obias_safe_fork_midas64_q0_v1.mechanism-ir.json"
CLOSURE_PATH = "projects/enwiki9/operations/planning/cmix_obias_safe_fork_midas64_q0_v1.causal-closure.json"
REQUIRED_LOCK_PATHS = {
    "projects/enwiki9/contracts/research/v1/gamma-mechanism-ir-v3-gate.schema.json",
    "projects/enwiki9/contracts/research/v1/gamma-mechanism-ir-compilation-receipt-v2.schema.json",
    "projects/enwiki9/contracts/research/v1/gamma-mechanism-ir-compilation-verification-v2.schema.json",
    "projects/enwiki9/contracts/research/v1/gamma-mechanism-ir-program-lock.schema.json",
    "projects/enwiki9/contracts/research/v1/gamma-mechanism-ir-program-lock-verification.schema.json",
    "projects/enwiki9/operations/planning/gamma_mechanism_ir_v3.json",
    "projects/enwiki9/operations/planning/gamma_mechanism_ir_v3_commands.json",
    "projects/enwiki9/operations/planning/gamma_mechanism_ir_v3_source_contract.json",
    "projects/enwiki9/tools/gamma_mechanism_ir_compile_v2.py",
    "projects/enwiki9/tools/gamma_mechanism_ir_compile_v2_verify.py",
    "projects/enwiki9/tools/gamma_mechanism_ir_program_lock_materialize.py",
    "projects/enwiki9/tools/gamma_mechanism_ir_program_lock_verify.py",
    "projects/enwiki9/tools/gamma_mechanism_ir_v3_gate.py",
    IR_PATH,
    CLOSURE_PATH,
}
PROGRAM_LOCK_CHECK_KEYS = {
    "contract_identity_pass",
    "path_closure_pass",
    "file_identity_pass",
    "artifact_set_pass",
    "filesystem_safety_pass",
}
NEGATIVE_CONTROL_KEYS = {
    "source_after_use",
    "missing_state_role",
    "raw_d_posterior_write",
    "mismatched_k_write_set",
    "incomplete_join_discard",
    "incomplete_forbidden_copy",
    "unknown_arm_state",
    "active_exclusive_lease",
}


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def identity(path: Path, display: str) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"path": display, "bytes": len(raw), "sha256": sha256_bytes(raw)}


def regular_file(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise SystemExit(f"{label}: symlink component forbidden: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise SystemExit(f"{label}: expected single-link regular file")
    return absolute.resolve(strict=True)


def require_clear_lease(path: Path) -> None:
    lease = json.loads(regular_file(path, "exclusive lease").read_text(encoding="utf-8"))
    if not isinstance(lease, dict) or lease.get("active") is not False:
        raise SystemExit("exclusive lease is active or lacks an explicit inactive decision")


def load_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"{label} parse failure: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{label} must be a JSON object")
    return value, raw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--program-lock", type=Path, required=True)
    parser.add_argument("--program-lock-verification", type=Path, required=True)
    parser.add_argument("--compilation-verification", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    require_clear_lease(args.exclusive_lease)
    lock_path = regular_file(args.program_lock, "program lock")
    lock_verification_path = regular_file(args.program_lock_verification, "program-lock verification")
    compilation_verification_path = regular_file(args.compilation_verification, "compilation verification")
    if args.receipt.exists() or args.receipt.is_symlink():
        raise SystemExit("receipt already exists")
    lock, lock_raw = load_object(lock_path, "program lock")
    lock_verification, lock_verification_raw = load_object(lock_verification_path, "program-lock verification")
    compilation_verification, compilation_verification_raw = load_object(compilation_verification_path, "compilation verification")

    errors: list[str] = []
    checks = {
        "program_lock_verification_pass": True,
        "compilation_verification_pass": True,
        "locked_compiler_identity_pass": True,
        "locked_ir_identity_pass": True,
        "locked_closure_identity_pass": True,
        "required_program_closure_pass": True,
    }
    lock_checks = lock_verification.get("checks")
    lock_source_contract = lock.get("source_contract")
    if (
        lock_verification.get("schema") != "gamma.enwiki9.gamma-mechanism-ir-program-lock-verification.v1"
        or lock_verification.get("verified") is not True
        or lock_verification.get("errors") != []
        or lock_verification.get("program_lock_sha256") != sha256_bytes(lock_raw)
        or not isinstance(lock_checks, dict)
        or set(lock_checks) != PROGRAM_LOCK_CHECK_KEYS
        or not all(lock_checks[key] is True for key in PROGRAM_LOCK_CHECK_KEYS)
        or not isinstance(lock_source_contract, dict)
        or lock_verification.get("source_contract_sha256") != lock_source_contract.get("sha256")
        or lock_verification.get("recomputed_artifact_set_sha256") != lock.get("artifact_set_sha256")
    ):
        errors.append("program-lock verification is not a positive decision bound to the supplied lock")
        checks["program_lock_verification_pass"] = False
    repeat = compilation_verification.get("repeat")
    controls = compilation_verification.get("negative_controls")
    evidence_root = compilation_verification.get("evidence_root")
    controls_pass = (
        isinstance(controls, dict)
        and set(controls) == NEGATIVE_CONTROL_KEYS
        and all(
            isinstance(controls[key], dict)
            and controls[key].get("return_code") != 0
            and controls[key].get("rejected") is True
            and controls[key].get("no_final_output_pass") is True
            for key in NEGATIVE_CONTROL_KEYS
        )
    )
    if (
        compilation_verification.get("schema") != "gamma.enwiki9.gamma-mechanism-ir-compilation-verification.v2"
        or compilation_verification.get("verified") is not True
        or compilation_verification.get("errors") != []
        or not isinstance(repeat, dict)
        or repeat.get("run_a_return_code") != 0
        or repeat.get("run_b_return_code") != 0
        or repeat.get("receipt_identity_pass") is not True
        or repeat.get("artifact_identity_pass") is not True
        or not isinstance(repeat.get("artifact_set_sha256"), str)
        or len(repeat["artifact_set_sha256"]) != 64
        or not controls_pass
        or not isinstance(evidence_root, dict)
        or evidence_root.get("filesystem_anomaly_absence_pass") is not True
        or not isinstance(evidence_root.get("regular_file_count"), int)
        or evidence_root["regular_file_count"] <= 0
        or not isinstance(evidence_root.get("regular_file_bytes"), int)
        or evidence_root["regular_file_bytes"] <= 0
    ):
        errors.append("compilation verification is not a positive independent A/B and rejection decision")
        checks["compilation_verification_pass"] = False
    locked_files: dict[str, dict[str, Any]] = {}
    values = lock.get("files")
    if isinstance(values, list):
        for value in values:
            if isinstance(value, dict) and isinstance(value.get("path"), str) and value["path"] not in locked_files:
                locked_files[value["path"]] = value
    if not REQUIRED_LOCK_PATHS <= set(locked_files):
        errors.append("program lock omits required v3 program closure")
        checks["required_program_closure_pass"] = False
    compiler_hash = locked_files.get(COMPILER_PATH, {}).get("sha256")
    if compiler_hash != compilation_verification.get("compiler_sha256"):
        errors.append("compilation verification does not bind the locked v2 compiler")
        checks["locked_compiler_identity_pass"] = False
    ir_hash = locked_files.get(IR_PATH, {}).get("sha256")
    if ir_hash != compilation_verification.get("source_ir_sha256"):
        errors.append("compilation verification does not bind the locked Mechanism IR")
        checks["locked_ir_identity_pass"] = False
    closure_hash = locked_files.get(CLOSURE_PATH, {}).get("sha256")
    if closure_hash != compilation_verification.get("causal_closure_sha256"):
        errors.append("compilation verification does not bind the locked causal closure")
        checks["locked_closure_identity_pass"] = False

    output = {
        "schema": OUTPUT_SCHEMA,
        "program_id": "gamma_mechanism_ir_v3",
        "verified": not errors,
        "errors": errors,
        "program_lock": {"path": os.fspath(args.program_lock), "bytes": len(lock_raw), "sha256": sha256_bytes(lock_raw)},
        "program_lock_verification": {"path": os.fspath(args.program_lock_verification), "bytes": len(lock_verification_raw), "sha256": sha256_bytes(lock_verification_raw)},
        "compilation_verification": {"path": os.fspath(args.compilation_verification), "bytes": len(compilation_verification_raw), "sha256": sha256_bytes(compilation_verification_raw)},
        "checks": checks,
        "claim_authority": "none",
        "execution_authority": False,
        "promotion_authority": False,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("xb") as stream:
        stream.write(json_bytes(output))
        stream.flush()
        os.fsync(stream.fileno())
    return 0 if output["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
