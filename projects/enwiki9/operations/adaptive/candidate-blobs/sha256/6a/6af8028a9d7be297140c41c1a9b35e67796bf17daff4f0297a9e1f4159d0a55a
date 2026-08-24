#!/usr/bin/env python3
"""Independently verify one SAFE-MIX v2 activation receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
from typing import Any

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
CID, SUBJECT = "gamma_safe_mix_v2", "gamma_safe_mix_v1"
PLAN = ROOT / "operations/planning/gamma_safe_mix_v2_execution.json"
PLAN_SCHEMA = ROOT / "operations/planning/gamma-safe-mix-v2-execution.schema.json"
RECEIPT_SCHEMA = ROOT / "programs/gamma_safe_mix_v2/activation-receipt.schema.json"
OUTPUT_SCHEMA = ROOT / "programs/gamma_safe_mix_v2/activation-verification.schema.json"
LEASE = ROOT / "operations/runtime/exclusive_full1g.json"
LOCK = ROOT / "operations/runtime/exclusive_full1g.json.lock"
PYTHON = Path("/usr/bin/python3.14")
CANONICAL_MANAGER = ROOT / "tools/managed_exclusive_lease.py"
ENV = {"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0", "TZ": "UTC"}
PHASES = {
    "build_negative_controls": ("gamma.enwiki9.safe-mix-build-negative-controls-receipt.v1", ("positive_fixture_pass", "all_controls_rejected_pass")),
    "build_a": ("gamma.enwiki9.safe-mix-build-receipt.v1", ("terminal_pass",)),
    "build_b": ("gamma.enwiki9.safe-mix-build-receipt.v1", ("terminal_pass",)),
    "build_verify": ("gamma.enwiki9.safe-mix-independent-build-verification.v1", ("terminal_pass",)),
    "transactional_controls": ("gamma.enwiki9.safe-mix-negative-controls-execution-receipt.v1", ("terminal_pass",)),
    "oracle_suite": ("gamma.enwiki9.safe-mix-oracle-suite-receipt.v1", ("all_populations_pass",)),
}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def bytes_digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def regular(path: Path, label: str) -> Path:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"unsafe {label}")
    return path.resolve(strict=True)


def load(path: Path, label: str) -> tuple[Path, dict[str, Any]]:
    path = regular(path, label)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"non-object {label}")
    return path, value


def binding(record: Any, label: str) -> Path:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise RuntimeError(f"bad {label} binding")
    declared = Path(record["path"])
    path = regular(declared if declared.is_absolute() else ROOT / declared, label)
    if path.stat().st_size != record["bytes"] or digest(path) != record["sha256"]:
        raise RuntimeError(f"changed {label}")
    return path


def need(value: bool, name: str, checks: dict[str, bool]) -> None:
    checks[name] = bool(value)
    if not value:
        raise RuntimeError(name)


def write_new(path: Path, value: dict[str, Any]) -> None:
    raw = canonical(value)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        offset = 0
        while offset < len(raw):
            written = os.write(descriptor, raw[offset:])
            if written <= 0:
                raise OSError("short write")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def probe_tools(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    probes = {}
    for name, marker in (("compiler", b"clang"), ("linker", b"lld")):
        command = [str(binding(plan["activation"]["toolchain"][name], name)), "--version"]
        result = subprocess.run(command, env=ENV, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, close_fds=True)
        if result.returncode or marker not in (result.stdout + b"\n" + result.stderr).lower():
            raise RuntimeError(f"{name} probe")
        probes[name] = {
            "command": command,
            "command_sha256": bytes_digest(canonical(command)),
            "return_code": result.returncode,
            "stdout_sha256": bytes_digest(result.stdout),
            "stderr_sha256": bytes_digest(result.stderr),
            "family_marker_pass": True,
        }
    return probes


def child_pass(value: dict[str, Any], phase: str) -> bool:
    schema, fields = PHASES[phase]
    return bool(
        value.get("schema") == schema
        and value.get("candidate_id") == SUBJECT
        and all(value.get(field) is True for field in fields)
        and value.get("execution_authority") is False
        and value.get("archive_authority") is False
        and value.get("score_credit_bytes") == 0
    )


def guard_pass(value: dict[str, Any]) -> bool:
    guards = value.get("guards")
    return bool(
        value.get("schema") == "gamma.enwiki9.resource-guard-receipt.v3"
        and value.get("status") == "complete"
        and value.get("returncode") == 0
        and isinstance(guards, dict)
        and guards
        and not any(guards.values())
    )


def verify(receipt_file: Path) -> tuple[dict[str, Any], bool]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    phase = receipt_sha = plan_sha = child_sha = guard_sha = None
    try:
        receipt_file, receipt = load(receipt_file, "activation receipt")
        receipt_sha = digest(receipt_file)
        receipt_schema_path, receipt_schema = load(RECEIPT_SCHEMA, "receipt schema")
        output_schema_path, output_schema = load(OUTPUT_SCHEMA, "verification schema")
        _, plan_schema = load(PLAN_SCHEMA, "plan schema")
        for schema in (receipt_schema, output_schema, plan_schema):
            jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(receipt_schema).validate(receipt)
        phase = receipt["phase"]
        need(receipt["terminal_pass"] is True, "receipt_terminal", checks)
        plan_path = binding(receipt["activation_plan"], "plan")
        need(plan_path == PLAN.resolve(strict=True), "plan_path", checks)
        _, plan = load(plan_path, "plan")
        jsonschema.Draft202012Validator(plan_schema).validate(plan)
        plan_sha = digest(plan_path)
        need(plan["revision"] >= 2 and plan["execution_authorized"] is True, "plan_active", checks)
        command = receipt["command"]
        need(plan["phases"][phase]["argv"] == command, "phase_command", checks)
        need(bytes_digest(canonical(command)) == receipt["command_sha256"], "command_digest", checks)
        need(bytes_digest(canonical(plan["source_bindings"])) == receipt["source_bindings_sha256"], "source_aggregate", checks)
        need(bytes_digest(canonical(plan["activation"]["toolchain"])) == receipt["toolchain_bindings_sha256"], "toolchain_aggregate", checks)

        expected = {
            "activation_gate": ROOT / "programs/gamma_safe_mix_v2/activation_gate.py",
            "activation_verifier": Path(__file__).resolve(strict=True),
            "plan_schema": PLAN_SCHEMA,
            "activation_receipt_schema": receipt_schema_path,
            "activation_verification_schema": output_schema_path,
            "v1_program_lock": ROOT / "programs/gamma_safe_mix_v1/program-lock.json",
            "v1_program_lock_verification": ROOT / "results/gamma_safe_mix_v1/01_program_lock/program-lock-verification.json",
            "activation_audit": ROOT / "operations/planning/gamma_safe_mix_v1_activation_audit_q0_v1.json",
            "lease_schema": ROOT / "operations/runtime/exclusive_full1g.schema.json",
            "owned_cleanup_manager": ROOT / "programs/gamma_managed_exclusive_lease_owned_cleanup_q0_v1/managed_exclusive_lease.py",
            "resource_guard": ROOT / "tools/run_with_resource_guard_v3.py",
            "resource_guard_schema": ROOT / "contracts/research/v1/resource-guard-receipt.v3.schema.json",
            "python_runtime": PYTHON,
        }
        need(set(plan["source_bindings"]) == set(expected), "source_set", checks)
        for name, path in expected.items():
            need(binding(plan["source_bindings"][name], name) == path.resolve(strict=True), f"source_{name}", checks)

        terminal_path = binding(receipt["qm8_terminal_receipt"], "qm8 terminal")
        classification_path = binding(receipt["qm8_terminal_classification"], "qm8 classification")
        need(receipt["qm8_terminal_receipt"] == plan["activation"]["qm8_terminal_receipt"], "qm8_terminal_binding", checks)
        need(receipt["qm8_terminal_classification"] == plan["activation"]["qm8_terminal_classification"], "qm8_classification_binding", checks)
        terminal = json.loads(terminal_path.read_text())
        classification = json.loads(classification_path.read_text())
        class_schema = "gamma.enwiki9.cmix-filebacked-fxcm-full-soft-high-verification.v1" if terminal.get("terminal_pass") is True else "gamma.enwiki9.cmix-filebacked-fxcm-full-qm8-failure-verification.v1"
        need(
            terminal.get("schema") == "gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1"
            and terminal.get("candidate_id") == "cmix_obias_memory_safe_parent_filebacked_q1_v1"
            and terminal.get("arm") == "a"
            and isinstance(terminal.get("terminal_pass"), bool)
            and classification.get("schema") == class_schema
            and classification.get("verification_pass") is True
            and classification.get("gamma_score_credit_bytes") == 0,
            "qm8_evidence", checks,
        )

        lease_path = binding(receipt["managed_lease_verification"], "lease verification")
        manager = binding(receipt["canonical_lease_manager"], "canonical manager")
        need(receipt["managed_lease_verification"] == plan["activation"]["managed_lease_verification"], "lease_binding", checks)
        need(receipt["canonical_lease_manager"] == plan["activation"]["canonical_lease_manager"], "manager_binding", checks)
        lease = json.loads(lease_path.read_text())
        need(
            lease.get("schema") == "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-verification.v1"
            and lease.get("candidate_id") == "gamma_managed_exclusive_lease_owned_cleanup_q0_v1"
            and lease.get("verified") is True
            and lease.get("canonical_migration_authorized") is True
            and lease.get("execution_authority") is False
            and lease.get("archive_authority") is False
            and lease.get("gamma_compression_credit_bytes") == 0
            and lease.get("gamma_score_credit_bytes") == 0
            and manager == CANONICAL_MANAGER.resolve(strict=True)
            and digest(manager) == digest(expected["owned_cleanup_manager"]),
            "lease_migration", checks,
        )

        need(probe_tools(plan) == receipt["toolchain_probes"], "toolchain_probes", checks)
        child_path = binding(receipt["child_receipt"], "child receipt")
        guard_path = binding(receipt["guard_receipt"], "guard receipt")
        child_sha, guard_sha = digest(child_path), digest(guard_path)
        _, child = load(child_path, "child receipt")
        _, guard = load(guard_path, "guard receipt")
        _, child_schema = load(binding(plan["phases"][phase]["child_receipt_schema"], "child schema"), "child schema")
        _, guard_schema = load(expected["resource_guard_schema"], "guard schema")
        for schema, value in ((child_schema, child), (guard_schema, guard)):
            jsonschema.Draft202012Validator.check_schema(schema)
            jsonschema.Draft202012Validator(schema).validate(value)
        need(child_pass(child, phase), "child_pass", checks)
        need(guard_pass(guard), "guard_pass", checks)
        need(command.count("--") == 1 and guard["command"] == command[command.index("--") + 1 :], "guard_command", checks)
        need(not any(path.exists() or path.is_symlink() for path in (LEASE, LOCK)), "namespace_free", checks)
        need(
            receipt["execution_authority"] is False
            and receipt["archive_authority"] is False
            and receipt["gamma_compression_credit_bytes"] == 0
            and receipt["gamma_score_credit_bytes"] == 0,
            "zero_authority", checks,
        )
        verified = all(checks.values())
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
        verified = False
    output = {
        "schema": "gamma.enwiki9.safe-mix-v2-activation-verification.v1",
        "candidate_id": CID,
        "subject_candidate_id": SUBJECT,
        "phase": phase,
        "verified": verified,
        "receipt_sha256": receipt_sha,
        "plan_sha256": plan_sha,
        "child_receipt_sha256": child_sha,
        "guard_receipt_sha256": guard_sha,
        "checks": checks,
        "errors": errors,
        "claim_authority": "proof_phase_execution_only" if verified else "none",
        "execution_authority": False,
        "archive_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    return output, verified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output, verified = verify(args.receipt)
    _, schema = load(OUTPUT_SCHEMA, "verification schema")
    jsonschema.Draft202012Validator(schema).validate(output)
    write_new(args.output, output)
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
