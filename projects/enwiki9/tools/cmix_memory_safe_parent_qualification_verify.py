#!/usr/bin/env python3
"""Derive q1 memory-safe-parent qualification from a retained terminal receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any


OUTPUT_SCHEMA = "gamma.enwiki9.cmix-memory-safe-parent-qualification-verification.v1"
INPUT_SCHEMA = "gamma.enwiki9.cmix-memory-safe-parent-qualification-receipt.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
CANONICAL_BYTES = 1_000_000_000
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
RSS_LIMIT_KIB = 9_765_625
CGROUP_LIMIT_BYTES = 10_000_000_000
TEMPORARY_DISK_LIMIT_BYTES = 100_000_000_000
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


def object_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def integer_at_most(value: Any, maximum: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= maximum


def sha256_value(value: Any) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    args = parser.parse_args()
    require_clear_lease(args.exclusive_lease)
    receipt_path = regular_file(args.receipt, "qualification receipt")
    if args.verification.exists() or args.verification.is_symlink():
        raise SystemExit("verification path already exists")
    raw = receipt_path.read_bytes()
    try:
        receipt = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"qualification receipt parse failure: {exc}") from exc
    if not isinstance(receipt, dict):
        raise SystemExit("qualification receipt must be a JSON object")

    errors: list[str] = []
    qualification_failures: list[str] = []
    checks = {
        "identity_pass": True,
        "source_build_evidence_pass": True,
        "probability_identity_evidence_pass": True,
        "roundtrip_evidence_pass": True,
        "two_run_identity_evidence_pass": True,
        "resource_measurement_pass": True,
        "package_arithmetic_pass": True,
        "evidence_closure_pass": True,
        "decision_consistency_pass": True,
    }
    population = object_value(receipt.get("population"))
    if (
        receipt.get("schema") != INPUT_SCHEMA
        or receipt.get("candidate_id") != CANDIDATE_ID
        or population.get("bytes") != CANONICAL_BYTES
        or population.get("sha256") != CANONICAL_SHA256
        or population.get("canonical_enwik9") is not True
    ):
        errors.append("receipt identity or canonical population mismatch")
        checks["identity_pass"] = False

    source = object_value(receipt.get("source_and_build"))
    source_hash_fields = {
        "source_closure_sha256",
        "program_lock_sha256",
        "build_a_receipt_sha256",
        "build_b_receipt_sha256",
        "build_verification_sha256",
        "binary_a_sha256",
        "binary_b_sha256",
        "command_contract_sha256",
    }
    source_hashes_valid = all(sha256_value(source.get(field)) for field in source_hash_fields)
    build_identity = (
        source_hashes_valid
        and source.get("binary_identity_pass") is True
        and source.get("binary_a_sha256") == source.get("binary_b_sha256")
        and source.get("compiler_trace_controls_pass") is True
    )
    source_structure = (
        source_hashes_valid
        and isinstance(source.get("binary_identity_pass"), bool)
        and isinstance(source.get("compiler_trace_controls_pass"), bool)
    )
    if not source_structure:
        errors.append("source/build evidence is malformed")
    elif not build_identity:
        qualification_failures.append("source/build evidence does not establish independent binary identity")
    if not build_identity:
        checks["source_build_evidence_pass"] = False

    probability = object_value(receipt.get("probability_identity"))
    scopes = probability.get("scopes")
    scope_structure = isinstance(scopes, list) and len(scopes) >= 3
    scope_identity = scope_structure
    offsets: set[int] = set()
    if scope_structure:
        for scope in scopes:
            if not isinstance(scope, dict):
                scope_structure = False
                scope_identity = False
                continue
            offset = scope.get("offset")
            parent_hash = scope.get("parent_integer_probability_sha256")
            candidate_hash = scope.get("candidate_integer_probability_sha256")
            structurally_valid = (
                isinstance(offset, int)
                and not isinstance(offset, bool)
                and offset >= 0
                and offset not in offsets
                and isinstance(scope.get("bytes"), int)
                and not isinstance(scope.get("bytes"), bool)
                and scope["bytes"] > 0
                and offset + scope["bytes"] <= CANONICAL_BYTES
                and sha256_value(parent_hash)
                and sha256_value(candidate_hash)
                and isinstance(scope.get("identity_pass"), bool)
            )
            if not structurally_valid:
                scope_structure = False
                scope_identity = False
            else:
                hashes_equal = parent_hash == candidate_hash
                if scope.get("identity_pass") is not hashes_equal:
                    errors.append("scope identity decision contradicts its probability hashes")
                    scope_structure = False
                if not hashes_equal:
                    scope_identity = False
            if (
                not isinstance(offset, int)
                or isinstance(offset, bool)
                or offset < 0
                or offset in offsets
            ):
                scope_structure = False
                scope_identity = False
            offsets.add(offset) if isinstance(offset, int) and not isinstance(offset, bool) else None
    full_structure = (
        scope_structure
        and sha256_value(probability.get("full_stream_parent_sha256"))
        and sha256_value(probability.get("full_stream_candidate_sha256"))
        and isinstance(probability.get("full_stream_identity_pass"), bool)
        and isinstance(probability.get("persistent_state_identity_pass"), bool)
    )
    full_hashes_equal = (
        full_structure
        and probability.get("full_stream_parent_sha256") == probability.get("full_stream_candidate_sha256")
    )
    if full_structure and probability.get("full_stream_identity_pass") is not full_hashes_equal:
        errors.append("full-stream identity decision contradicts its probability hashes")
        full_structure = False
    full_probability_identity = (
        scope_identity
        and full_structure
        and full_hashes_equal
        and probability.get("full_stream_identity_pass") is True
        and probability.get("persistent_state_identity_pass") is True
    )
    if not full_structure:
        errors.append("probability or persistent-state evidence is malformed")
    elif not full_probability_identity:
        qualification_failures.append("probability or persistent-state identity did not pass")
    if not full_probability_identity:
        checks["probability_identity_evidence_pass"] = False

    values = receipt.get("roundtrips")
    roundtrips: dict[str, dict[str, Any]] = {}
    if isinstance(values, list):
        for value in values:
            if isinstance(value, dict) and value.get("arm") in {"A", "B"} and value["arm"] not in roundtrips:
                roundtrips[value["arm"]] = value
    roundtrip_structure = isinstance(values, list) and len(values) == 2 and len(roundtrips) == 2
    exact_inverse = roundtrip_structure
    cleanup_pass = roundtrip_structure
    if roundtrip_structure:
        for arm in ("A", "B"):
            value = roundtrips[arm]
            arm_structure = (
                isinstance(value.get("encode_return_code"), int)
                and not isinstance(value.get("encode_return_code"), bool)
                and isinstance(value.get("decode_return_code"), int)
                and not isinstance(value.get("decode_return_code"), bool)
                and isinstance(value.get("decoded_bytes"), int)
                and not isinstance(value.get("decoded_bytes"), bool)
                and sha256_value(value.get("decoded_sha256"))
                and isinstance(value.get("bytewise_inverse_pass"), bool)
                and isinstance(value.get("cleanup_pass"), bool)
                and isinstance(value.get("archive_bytes"), int)
                and not isinstance(value.get("archive_bytes"), bool)
                and value["archive_bytes"] > 0
                and sha256_value(value.get("archive_sha256"))
                and sha256_value(value.get("payload_sha256"))
            )
            if not arm_structure:
                roundtrip_structure = False
                exact_inverse = False
                continue
            derived_arm_inverse = (
                value.get("encode_return_code") == 0
                and value.get("decode_return_code") == 0
                and value.get("decoded_bytes") == CANONICAL_BYTES
                and value.get("decoded_sha256") == CANONICAL_SHA256
            )
            if value.get("bytewise_inverse_pass") is not derived_arm_inverse:
                errors.append(f"roundtrip {arm} inverse decision contradicts measured fields")
                roundtrip_structure = False
            exact_inverse = exact_inverse and derived_arm_inverse
            cleanup_pass = cleanup_pass and value.get("cleanup_pass") is True
    if not roundtrip_structure:
        errors.append("roundtrip evidence is malformed or internally contradictory")
    elif not exact_inverse:
        qualification_failures.append("two exact canonical roundtrips were not established")
    if roundtrip_structure and not cleanup_pass:
        qualification_failures.append("one or both roundtrip cleanup operations failed")
    if not (exact_inverse and cleanup_pass):
        checks["roundtrip_evidence_pass"] = False
    payload_identity = exact_inverse and roundtrips["A"]["payload_sha256"] == roundtrips["B"]["payload_sha256"]
    archive_identity = exact_inverse and (
        roundtrips["A"]["archive_bytes"] == roundtrips["B"]["archive_bytes"]
        and roundtrips["A"]["archive_sha256"] == roundtrips["B"]["archive_sha256"]
    )
    two_run_identity = build_identity and full_probability_identity and payload_identity and archive_identity and exact_inverse
    if roundtrip_structure and not two_run_identity:
        qualification_failures.append("A/B binary, probability, payload, archive, and inverse identity did not pass")
    if not two_run_identity:
        checks["two_run_identity_evidence_pass"] = False

    resources = object_value(receipt.get("resources"))
    resource_integer_fields = {
        "process_tree_peak_rss_kib",
        "largest_process_vmhwm_kib",
        "cgroup_memory_peak_bytes",
        "memory_events_oom",
        "memory_events_oom_kill",
        "maximum_logical_cpus",
        "scratch_logical_peak_bytes",
        "scratch_allocated_peak_bytes",
        "scratch_after_cleanup_bytes",
    }
    resource_boolean_fields = {"temporary_disk_pass", "memory_pass", "runtime_measured", "runtime_eligible"}
    resource_structure = (
        all(isinstance(resources.get(field), int) and not isinstance(resources.get(field), bool) and resources[field] >= 0 for field in resource_integer_fields)
        and all(isinstance(resources.get(field), bool) for field in resource_boolean_fields)
    )
    derived_memory_pass = (
        integer_at_most(resources.get("process_tree_peak_rss_kib"), RSS_LIMIT_KIB)
        and integer_at_most(resources.get("largest_process_vmhwm_kib"), RSS_LIMIT_KIB)
        and integer_at_most(resources.get("cgroup_memory_peak_bytes"), CGROUP_LIMIT_BYTES)
        and resources.get("memory_events_oom") == 0
        and resources.get("memory_events_oom_kill") == 0
        and resources.get("maximum_logical_cpus") == 1
    )
    derived_temporary_disk_pass = (
        integer_at_most(resources.get("scratch_logical_peak_bytes"), TEMPORARY_DISK_LIMIT_BYTES)
        and integer_at_most(resources.get("scratch_allocated_peak_bytes"), TEMPORARY_DISK_LIMIT_BYTES)
        and resources.get("scratch_after_cleanup_bytes") == 0
    )
    if resource_structure and resources.get("memory_pass") is not derived_memory_pass:
        errors.append("memory decision contradicts measured resource fields")
        resource_structure = False
    if resource_structure and resources.get("temporary_disk_pass") is not derived_temporary_disk_pass:
        errors.append("temporary-disk decision contradicts measured resource fields")
        resource_structure = False
    memory_pass = resource_structure and derived_memory_pass
    temporary_disk_pass = resource_structure and derived_temporary_disk_pass
    runtime_eligible = resources.get("runtime_measured") is True and resources.get("runtime_eligible") is True
    if resources.get("runtime_eligible") is True and resources.get("runtime_measured") is not True:
        errors.append("runtime eligibility is asserted without a measurement")
        resource_structure = False
        runtime_eligible = False
    if not resource_structure:
        errors.append("resource evidence is malformed or internally contradictory")
    elif not (memory_pass and temporary_disk_pass and runtime_eligible):
        qualification_failures.append("resource or runtime measurements did not qualify")
    if not (memory_pass and temporary_disk_pass and runtime_eligible):
        checks["resource_measurement_pass"] = False

    package = object_value(receipt.get("package"))
    components = [package.get("archive_bytes"), package.get("required_program_model_bytes"), package.get("other_counted_bytes")]
    package_structure = (
        all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in components)
        and isinstance(package.get("complete_counted_bytes"), int)
        and not isinstance(package.get("complete_counted_bytes"), bool)
        and isinstance(package.get("dependency_closure_pass"), bool)
        and isinstance(package.get("license_closure_pass"), bool)
    )
    package_sum_pass = package_structure and package.get("complete_counted_bytes") == sum(components)
    package_archive_pass = roundtrip_structure and package.get("archive_bytes") == roundtrips["A"]["archive_bytes"]
    if package_structure and not package_sum_pass:
        errors.append("complete counted package sum contradicts its components")
        package_structure = False
    if roundtrip_structure and not package_archive_pass:
        errors.append("package archive bytes contradict retained roundtrip archive bytes")
        package_structure = False
    package_arithmetic = (
        package_structure
        and package_sum_pass
        and package_archive_pass
        and package.get("dependency_closure_pass") is True
        and package.get("license_closure_pass") is True
    )
    if not package_structure:
        errors.append("complete package evidence is malformed or internally contradictory")
    elif not package_arithmetic:
        qualification_failures.append("dependency or license closure did not pass")
    if not package_arithmetic:
        checks["package_arithmetic_pass"] = False

    evidence = receipt.get("evidence")
    evidence_hashes: set[str] = set()
    evidence_paths: set[str] = set()
    evidence_pass = isinstance(evidence, list) and bool(evidence)
    if evidence_pass:
        for value in evidence:
            if (
                not isinstance(value, dict)
                or not isinstance(value.get("path"), str)
                or not value["path"]
                or value["path"] in evidence_paths
                or not isinstance(value.get("bytes"), int)
                or value["bytes"] <= 0
                or not sha256_value(value.get("sha256"))
            ):
                evidence_pass = False
                continue
            evidence_paths.add(value["path"])
            evidence_hashes.add(value["sha256"])
    required_source_evidence = {source.get(field) for field in source_hash_fields - {"binary_a_sha256", "binary_b_sha256"}}
    if not required_source_evidence <= evidence_hashes:
        evidence_pass = False
    if not evidence_pass:
        errors.append("retained evidence does not close the source/build authority chain")
        checks["evidence_closure_pass"] = False

    package_complete = package_arithmetic
    qualified = (
        two_run_identity
        and cleanup_pass
        and memory_pass
        and temporary_disk_pass
        and runtime_eligible
        and package_complete
        and evidence_pass
    )
    derived = {
        "build_identity_pass": build_identity,
        "probability_identity_pass": full_probability_identity,
        "payload_identity_pass": payload_identity,
        "archive_identity_pass": archive_identity,
        "two_run_determinism_pass": two_run_identity,
        "exact_inverse_pass": exact_inverse,
        "cleanup_pass": cleanup_pass,
        "memory_pass": memory_pass,
        "temporary_disk_pass": temporary_disk_pass,
        "package_accounting_complete": package_complete,
        "runtime_eligible": runtime_eligible,
        "memory_safe_parent_qualified": qualified,
    }
    decisions = object_value(receipt.get("decisions"))
    receipt_decision_keys = set(derived) - {"runtime_eligible", "cleanup_pass"}
    decision_subset = {key: decisions.get(key) for key in receipt_decision_keys}
    derived_subset = {key: derived[key] for key in receipt_decision_keys}
    decision_consistency = (
        decision_subset == derived_subset
        and decisions.get("officially_verified") is False
        and decisions.get("gamma_compression_credit_bytes") == 0
        and decisions.get("gamma_score_credit_bytes") == 0
    )
    if not decision_consistency:
        errors.append("self-reported decisions differ from mechanically derived decisions")
        checks["decision_consistency_pass"] = False

    verified = not errors
    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "verified": verified,
        "qualified": qualified if verified else False,
        "errors": errors,
        "qualification_failures": qualification_failures,
        "receipt_sha256": sha256_bytes(raw),
        "checks": checks,
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
