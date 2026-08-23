#!/usr/bin/env python3
"""Derive SAFE-FORK memory admission from q1 qualification and allocation evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any


INPUT_SCHEMA = "gamma.enwiki9.cmix-safe-fork-memory-admission-receipt.v1"
OUTPUT_SCHEMA = "gamma.enwiki9.cmix-safe-fork-memory-admission-verification.v1"
CANDIDATE_ID = "cmix_obias_safe_fork_midas64_q0_v1"
PARENT_CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
PARENT_TARGET_BYTES = 9_216_000_000
HARD_BYTES = 10_000_000_000
RESERVE_BYTES = 128_000_000
STATIC_MAX_INCREMENTAL_BYTES = 656_000_000
PHASES = ["before_fork", "midpoint", "second_half_peak", "after_rejoin", "terminal"]
ALLOCATION_FIELDS = ["recurrent_state_bytes", "selected_parameters_optimizer_bytes", "midpoint_scratch_bytes", "safe_mix_state_bytes", "audit_state_bytes"]
FORBIDDEN_FIELDS = ["context_tables", "dictionary_order", "unproved_contexts", "coder_state", "input_archive_buffers", "complete_process_image", "unbounded_traces"]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def load(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"{label} parse failure: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{label} must be a JSON object")
    return value, raw


def nonnegative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-receipt", type=Path, required=True)
    parser.add_argument("--parent-verification", type=Path, required=True)
    parser.add_argument("--admission-receipt", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    args = parser.parse_args()
    require_clear_lease(args.exclusive_lease)
    parent_receipt_path = regular_file(args.parent_receipt, "parent receipt")
    parent_verification_path = regular_file(args.parent_verification, "parent verification")
    admission_path = regular_file(args.admission_receipt, "admission receipt")
    if args.verification.exists() or args.verification.is_symlink():
        raise SystemExit("verification path already exists")
    parent_receipt, parent_raw = load(parent_receipt_path, "parent receipt")
    parent_verification, parent_verification_raw = load(parent_verification_path, "parent verification")
    admission, admission_raw = load(admission_path, "admission receipt")
    errors: list[str] = []
    failures: list[str] = []
    if (
        parent_verification.get("schema") != "gamma.enwiki9.cmix-memory-safe-parent-qualification-verification.v1"
        or parent_verification.get("candidate_id") != PARENT_CANDIDATE_ID
        or parent_verification.get("verified") is not True
        or parent_verification.get("qualified") is not True
        or parent_verification.get("errors") != []
        or parent_verification.get("receipt_sha256") != sha256_bytes(parent_raw)
    ):
        errors.append("parent verification is not a positive decision bound to the supplied q1 receipt")
    parent_resources = parent_receipt.get("resources") if isinstance(parent_receipt.get("resources"), dict) else {}
    parent_peak_kib = parent_resources.get("process_tree_peak_rss_kib")
    parent_peak_bytes = parent_peak_kib * 1024 if nonnegative_integer(parent_peak_kib) else -1
    parent = admission.get("parent") if isinstance(admission.get("parent"), dict) else {}
    if (
        admission.get("schema") != INPUT_SCHEMA
        or admission.get("candidate_id") != CANDIDATE_ID
        or admission.get("claim_authority") != "none"
        or admission.get("execution_authority") is not False
        or parent.get("qualification_receipt_sha256") != sha256_bytes(parent_raw)
        or parent.get("qualification_verification_sha256") != sha256_bytes(parent_verification_raw)
        or parent.get("process_tree_peak_bytes") != parent_peak_bytes
    ):
        errors.append("admission identity or parent binding is malformed")
    parent_below_target = 0 <= parent_peak_bytes <= PARENT_TARGET_BYTES
    if not parent_below_target:
        failures.append("qualified parent is above the SAFE-FORK engineering target")
    dynamic_limit = max(0, min(STATIC_MAX_INCREMENTAL_BYTES, HARD_BYTES - max(parent_peak_bytes, 0) - RESERVE_BYTES))

    phase_values = admission.get("phase_allocations")
    phases: dict[str, dict[str, Any]] = {}
    if isinstance(phase_values, list):
        for value in phase_values:
            if isinstance(value, dict) and value.get("phase") in PHASES and value["phase"] not in phases:
                phases[value["phase"]] = value
    allocation_arithmetic = isinstance(phase_values, list) and len(phase_values) == len(PHASES) and set(phases) == set(PHASES)
    phase_totals: list[int] = []
    if allocation_arithmetic:
        for phase in PHASES:
            value = phases[phase]
            fields_valid = all(nonnegative_integer(value.get(field)) for field in ALLOCATION_FIELDS)
            total = sum(value[field] for field in ALLOCATION_FIELDS) if fields_valid else -1
            if not fields_valid or value.get("total_incremental_bytes") != total:
                allocation_arithmetic = False
            phase_totals.append(max(total, 0))
    if allocation_arithmetic and (
        phases["after_rejoin"]["recurrent_state_bytes"] != 0
        or phases["after_rejoin"]["selected_parameters_optimizer_bytes"] != 0
        or phases["after_rejoin"]["midpoint_scratch_bytes"] != 0
        or phases["terminal"]["recurrent_state_bytes"] != 0
        or phases["terminal"]["selected_parameters_optimizer_bytes"] != 0
        or phases["terminal"]["midpoint_scratch_bytes"] != 0
    ):
        allocation_arithmetic = False
    if not allocation_arithmetic:
        errors.append("phase allocation arithmetic, closure, or post-rejoin release is malformed")
    measured_incremental_peak = max(phase_totals, default=0)

    arm_hashes = admission.get("arm_capacity_sha256") if isinstance(admission.get("arm_capacity_sha256"), dict) else {}
    arm_capacity_structure = (
        set(arm_hashes) == {"K", "D", "M", "R", "S"}
        and all(isinstance(value, str) and SHA256_RE.fullmatch(value) is not None for value in arm_hashes.values())
    )
    arm_capacity_identity = arm_capacity_structure and len(set(arm_hashes.values())) == 1
    if not arm_capacity_structure:
        errors.append("arm-capacity digest set is malformed")
    elif not arm_capacity_identity:
        failures.append("K/D/M/R/S allocation capacities are not byte-identical")
    forbidden = admission.get("forbidden_duplication_bytes") if isinstance(admission.get("forbidden_duplication_bytes"), dict) else {}
    forbidden_structure = set(forbidden) == set(FORBIDDEN_FIELDS) and all(nonnegative_integer(forbidden.get(field)) for field in FORBIDDEN_FIELDS)
    forbidden_absent = forbidden_structure and all(forbidden[field] == 0 for field in FORBIDDEN_FIELDS)
    if not forbidden_structure:
        errors.append("forbidden-duplication accounting is malformed")
    elif not forbidden_absent:
        failures.append("one or more forbidden duplication classes are nonzero")
    incremental_budget_pass = allocation_arithmetic and measured_incremental_peak <= dynamic_limit
    if allocation_arithmetic and not incremental_budget_pass:
        failures.append("measured fork increment exceeds dynamic headroom")

    measurements = admission.get("measurements") if isinstance(admission.get("measurements"), dict) else {}
    measurement_integer_fields = ["process_tree_peak_bytes", "largest_process_vmhwm_bytes", "cgroup_memory_peak_bytes", "memory_events_oom", "memory_events_oom_kill"]
    measurement_structure = all(nonnegative_integer(measurements.get(field)) for field in measurement_integer_fields) and isinstance(measurements.get("p_k_probability_identity_pass"), bool) and isinstance(measurements.get("p_k_state_identity_pass"), bool)
    resource_guard_pass = (
        measurement_structure
        and measurements["process_tree_peak_bytes"] <= HARD_BYTES
        and measurements["largest_process_vmhwm_bytes"] <= HARD_BYTES
        and measurements["cgroup_memory_peak_bytes"] <= HARD_BYTES
        and measurements["memory_events_oom"] == 0
        and measurements["memory_events_oom_kill"] == 0
    )
    if not measurement_structure:
        errors.append("resource measurements are malformed")
    elif not resource_guard_pass:
        failures.append("SAFE-FORK resource guard did not pass")
    p_k_identity = measurement_structure and measurements.get("p_k_probability_identity_pass") is True and measurements.get("p_k_state_identity_pass") is True
    if measurement_structure and not p_k_identity:
        failures.append("P/K probability or state identity did not pass")
    admitted = parent_below_target and allocation_arithmetic and arm_capacity_identity and forbidden_absent and incremental_budget_pass and resource_guard_pass and p_k_identity
    derived = {
        "parent_below_engineering_target": parent_below_target,
        "allocation_arithmetic_pass": allocation_arithmetic,
        "arm_capacity_identity_pass": arm_capacity_identity,
        "forbidden_duplication_absent": forbidden_absent,
        "incremental_budget_pass": incremental_budget_pass,
        "resource_guard_pass": resource_guard_pass,
        "p_k_identity_pass": p_k_identity,
        "memory_admission_pass": admitted,
    }
    declared = admission.get("declared_decisions") if isinstance(admission.get("declared_decisions"), dict) else {}
    if declared != derived:
        errors.append("declared admission decisions differ from mechanically derived decisions")
    verified = not errors
    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "verified": verified,
        "admitted": admitted if verified else False,
        "errors": errors,
        "admission_failures": failures,
        "receipt_sha256": sha256_bytes(admission_raw),
        "parent_receipt_sha256": sha256_bytes(parent_raw),
        "parent_verification_sha256": sha256_bytes(parent_verification_raw),
        "dynamic_incremental_limit_bytes": dynamic_limit,
        "measured_incremental_peak_bytes": measured_incremental_peak,
        "derived_decisions": derived,
        "claim_authority": "none",
        "promotion_authority": False,
    }
    args.verification.parent.mkdir(parents=True, exist_ok=True)
    with args.verification.open("xb") as stream:
        stream.write(json_bytes(output))
        stream.flush()
        os.fsync(stream.fileno())
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
