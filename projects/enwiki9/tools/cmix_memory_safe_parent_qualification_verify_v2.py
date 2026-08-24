#!/usr/bin/env python3
"""Qualify q1 only by reopening every required independent evidence artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any

import jsonschema
import research_contracts
from cmix_filebacked_fxcm_full_identity_verify import verify as verify_full_identity
from cmix_filebacked_fxcm_full_soft_high_verify import verify as verify_full_arm
from cmix_filebacked_fxcm_runtime_qualification_verify import verify as verify_runtime


PROJECT = Path(__file__).resolve().parents[1]
CONTRACTS = PROJECT / "contracts/research/v1"
OBJECTIVE = CONTRACTS / "objective-contract.json"
SOURCE_SCHEMA = CONTRACTS / "cmix-memory-safe-parent-qualification-receipt-v2.schema.json"
OUTPUT_SCHEMA = CONTRACTS / "cmix-memory-safe-parent-qualification-verification-v2.schema.json"
FULL_IDENTITY_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-full-identity.schema.json"
FULL_IDENTITY_VERIFICATION_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-full-identity-verification.schema.json"
RUNTIME_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-runtime-qualification.schema.json"
RUNTIME_VERIFICATION_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-runtime-qualification-verification.schema.json"
SOURCE_SCHEMA_ID = "gamma.enwiki9.cmix-memory-safe-parent-qualification-receipt.v2"
OUTPUT_SCHEMA_ID = "gamma.enwiki9.cmix-memory-safe-parent-qualification-verification.v2"
ARM_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1"
ARM_VERIFICATION_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-full-soft-high-verification.v1"
FULL_IDENTITY_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-full-identity.v1"
FULL_IDENTITY_VERIFICATION_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-full-identity-verification.v1"
RUNTIME_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-runtime-qualification.v1"
RUNTIME_VERIFICATION_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-runtime-qualification-verification.v1"
DEPENDENCY_SCHEMA_ID = "gamma.enwiki9.dependency-closure.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
PARENT_ID = "cmix_obias_source_full1g_roundtrip_a_qm0_v1"
PARENT_PAYLOAD_BYTES = 107_730_531
PARENT_PAYLOAD_SHA256 = "889aa8074e0a84eb89997986899f1ef9f7cc0e52e87d1d36f86899fc679f5490"
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
ENGINEERING_RSS_KIB = 9_000_000
CGROUP_LIMIT_BYTES = 10_000_000_000
TARGET_BYTES = 105_000_000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(16 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def regular_file(path: Path, label: str) -> Path:
    absolute = (path if path.is_absolute() else Path.cwd() / path).absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"{label}: symlink component forbidden: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise ValueError(f"{label}: expected single-link regular file")
    resolved = absolute.resolve(strict=True)
    if PROJECT not in resolved.parents:
        raise ValueError(f"{label}: artifact escapes the project root")
    return resolved


def artifact(path: Path) -> dict[str, Any]:
    path = regular_file(path, "artifact")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def artifact_matches(record: Any, label: str) -> bool:
    if not isinstance(record, dict):
        return False
    try:
        path = regular_file(Path(record["path"]), label)
    except (KeyError, OSError, ValueError):
        return False
    return path.stat().st_size == record.get("bytes") and sha256_file(path) == record.get("sha256")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(regular_file(path, "JSON artifact").read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def validate_direct(value: dict[str, Any], schema_path: Path, schema_id: str) -> None:
    jsonschema.Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8"))).validate(value)
    if value.get("schema") != schema_id:
        raise ValueError(f"expected schema {schema_id}")


def same_file_value(left: Any, right: Any) -> bool:
    return isinstance(left, dict) and isinstance(right, dict) and (
        left.get("bytes"), left.get("sha256")
    ) == (right.get("bytes"), right.get("sha256"))


def independent_arm_pass(
    receipt: dict[str, Any],
    verification: dict[str, Any],
    arm: str,
    receipt_record: dict[str, Any],
) -> bool:
    return bool(
        receipt.get("schema") == ARM_SCHEMA_ID
        and receipt.get("candidate_id") == CANDIDATE_ID
        and receipt.get("authoritative_parent_id") == PARENT_ID
        and receipt.get("arm") == arm
        and receipt.get("terminal_pass") is True
        and receipt.get("errors") == []
        and receipt.get("memory_safe_parent_qualified") is False
        and receipt.get("promotion_authorized") is False
        and verification.get("schema") == ARM_VERIFICATION_SCHEMA_ID
        and verification.get("arm") == arm
        and verification.get("verification_pass") is True
        and verification.get("errors") == []
        and verification.get("source_receipt") == receipt_record
        and all(verification.get("checks", {}).values())
    )


def write_new(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        cursor = 0
        while cursor < len(payload):
            written = os.write(descriptor, payload[cursor:])
            if written <= 0:
                raise OSError(f"short write: {path}")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def verify(receipt_path: Path) -> tuple[dict[str, Any], bool]:
    router = load_json(receipt_path)
    validate_direct(router, SOURCE_SCHEMA, SOURCE_SCHEMA_ID)
    records = router["artifacts"]
    checks = {
        "router_schema_pass": True,
        "objective_binding_pass": False,
        "artifact_closure_pass": False,
        "arm_a_independent_pass": False,
        "arm_b_independent_pass": False,
        "two_arm_identity_pass": False,
        "full_probability_state_identity_pass": False,
        "runtime_pass": False,
        "resource_headroom_pass": False,
        "dependency_closure_pass": False,
        "license_closure_pass": False,
        "package_binding_pass": False,
    }
    objective_raw_sha256 = sha256_file(OBJECTIVE)
    objective = json.loads(OBJECTIVE.read_text(encoding="utf-8"))
    checks["objective_binding_pass"] = (
        router["objective"]["sha256"] == objective_raw_sha256
        and router["objective"]["id"] == objective["objectiveId"]
        and router["objective"]["corpus_bytes"] == objective["corpus"]["bytes"]
        and router["objective"]["corpus_sha256"] == objective["corpus"]["sha256"]
        and router["objective"]["target_score_bytes"] == objective["score"]["targetBytes"]
    )
    checks["artifact_closure_pass"] = all(
        artifact_matches(record, name) for name, record in records.items()
    )
    paths = {name: Path(record["path"]) for name, record in records.items()}
    values = {name: load_json(path) for name, path in paths.items()}

    for name in ("arm_a_receipt", "arm_a_verification", "arm_b_receipt", "arm_b_verification"):
        research_contracts.validate_artifact(paths[name])
    arm_a = values["arm_a_receipt"]
    arm_b = values["arm_b_receipt"]
    arm_a_verification = values["arm_a_verification"]
    arm_b_verification = values["arm_b_verification"]
    arm_a_recomputed, arm_a_recomputed_pass = verify_full_arm(paths["arm_a_receipt"])
    arm_b_recomputed, arm_b_recomputed_pass = verify_full_arm(paths["arm_b_receipt"])
    checks["arm_a_independent_pass"] = independent_arm_pass(
        arm_a, arm_a_verification, "a", records["arm_a_receipt"]
    ) and arm_a_recomputed_pass and arm_a_verification == arm_a_recomputed
    checks["arm_b_independent_pass"] = independent_arm_pass(
        arm_b, arm_b_verification, "b", records["arm_b_receipt"]
    ) and arm_b_recomputed_pass and arm_b_verification == arm_b_recomputed
    package_keys = (
        "raw_binary", "dictionary_payload", "article_order_payload", "header",
        "packaged_compressor", "head",
    )
    checks["two_arm_identity_pass"] = (
        checks["arm_a_independent_pass"]
        and checks["arm_b_independent_pass"]
        and all(same_file_value(arm_a["package"][key], arm_b["package"][key]) for key in package_keys)
        and arm_a["package"]["program_bytes"] == arm_b["package"]["program_bytes"]
        and all(same_file_value(arm_a["outputs"][key], arm_b["outputs"][key]) for key in ("payload", "archive", "restored"))
        and arm_a["outputs"]["payload"]["bytes"] == PARENT_PAYLOAD_BYTES
        and arm_a["outputs"]["payload"]["sha256"] == PARENT_PAYLOAD_SHA256
        and arm_a["outputs"]["restored"]["sha256"] == CANONICAL_SHA256
    )

    full_identity = values["full_identity_receipt"]
    full_identity_verification = values["full_identity_verification"]
    validate_direct(full_identity, FULL_IDENTITY_SCHEMA, FULL_IDENTITY_SCHEMA_ID)
    validate_direct(
        full_identity_verification,
        FULL_IDENTITY_VERIFICATION_SCHEMA,
        FULL_IDENTITY_VERIFICATION_SCHEMA_ID,
    )
    full_identity_recomputed, full_identity_recomputed_pass = verify_full_identity(
        paths["full_identity_receipt"]
    )
    checks["full_probability_state_identity_pass"] = (
        full_identity_verification["source_receipt"] == records["full_identity_receipt"]
        and full_identity_verification["verification_pass"] is True
        and full_identity_verification["errors"] == []
        and all(full_identity_verification["checks"].values())
        and all(full_identity_verification["derived"].values())
        and full_identity_recomputed_pass
        and full_identity_verification == full_identity_recomputed
        and same_file_value(full_identity["arms"]["q1"]["payload"], arm_a["outputs"]["payload"])
    )

    runtime = values["runtime_receipt"]
    runtime_verification = values["runtime_verification"]
    validate_direct(runtime, RUNTIME_SCHEMA, RUNTIME_SCHEMA_ID)
    validate_direct(
        runtime_verification,
        RUNTIME_VERIFICATION_SCHEMA,
        RUNTIME_VERIFICATION_SCHEMA_ID,
    )
    runtime_recomputed, runtime_recomputed_pass = verify_runtime(paths["runtime_receipt"])
    checks["runtime_pass"] = (
        runtime_verification["source_receipt"] == records["runtime_receipt"]
        and runtime_verification["verification_pass"] is True
        and runtime_verification["errors"] == []
        and all(runtime_verification["checks"].values())
        and runtime_verification["derived"]["runtime_eligible"] is True
        and runtime_recomputed_pass
        and runtime_verification == runtime_recomputed
        and same_file_value(runtime["package"]["packaged_compressor"], arm_a["package"]["packaged_compressor"])
        and same_file_value(runtime["package"]["head"], arm_a["package"]["head"])
        and same_file_value(runtime["package"]["archive"], arm_a["outputs"]["archive"])
    )

    maximum_tree_rss_kib = max(
        arm_a["resources"]["maximum_tree_rss_kib"],
        arm_b["resources"]["maximum_tree_rss_kib"],
    )
    maximum_cgroup_memory_bytes = max(
        arm_a["resources"]["maximum_cgroup_memory_peak_bytes"],
        arm_b["resources"]["maximum_cgroup_memory_peak_bytes"],
    )
    checks["resource_headroom_pass"] = (
        maximum_tree_rss_kib <= ENGINEERING_RSS_KIB
        and maximum_cgroup_memory_bytes < CGROUP_LIMIT_BYTES
        and arm_a["resources"]["all_guards_pass"] is True
        and arm_b["resources"]["all_guards_pass"] is True
    )

    dependency = values["dependency_closure"]
    dependency_result = research_contracts.validate_artifact(paths["dependency_closure"])
    license_audit = research_contracts.dependency_license_audit(dependency)
    checks["dependency_closure_pass"] = (
        dependency.get("schema") == DEPENDENCY_SCHEMA_ID
        and dependency.get("candidateId") == CANDIDATE_ID
        and dependency_result["complete"] is True
        and dependency_result["filesVerified"] is True
    )
    checks["license_closure_pass"] = license_audit["approved"] is True
    counted_pairs = {(record["bytes"], record["sha256"]) for record in dependency["countedFiles"]}
    required_package_pairs = {
        (arm_a["package"][name]["bytes"], arm_a["package"][name]["sha256"])
        for name in ("packaged_compressor", "head")
    }
    checks["package_binding_pass"] = (
        required_package_pairs <= counted_pairs
        and dependency["totalPackageBytes"] == arm_a["package"]["program_bytes"]
    )

    archive_bytes = arm_a["outputs"]["archive"]["bytes"]
    program_bytes = dependency["totalPackageBytes"]
    option_bytes = dependency["requiredOptionBytes"]
    complete_counted_bytes = archive_bytes + program_bytes + option_bytes
    score = runtime_verification["derived"]["geekbench5_single_core_score"]
    runtime_limit = runtime_verification["derived"]["wall_time_limit_seconds"]
    errors: list[str] = []
    failures = [f"qualification predicate failed: {name}" for name, passed in checks.items() if not passed]
    verified = not errors
    qualified = verified and not failures
    output = {
        "schema": OUTPUT_SCHEMA_ID,
        "candidate_id": CANDIDATE_ID,
        "verified": verified,
        "qualified": qualified,
        "errors": errors,
        "qualification_failures": failures,
        "receipt_sha256": sha256_file(receipt_path),
        "artifact_sha256": {name: sha256_file(path) for name, path in paths.items()},
        "checks": checks,
        "derived": {
            "payload_bytes": arm_a["outputs"]["payload"]["bytes"],
            "archive_bytes": archive_bytes,
            "program_bytes": program_bytes,
            "required_option_bytes": option_bytes,
            "complete_counted_bytes": complete_counted_bytes,
            "target_distance_bytes": complete_counted_bytes - TARGET_BYTES,
            "maximum_tree_rss_kib": maximum_tree_rss_kib,
            "maximum_cgroup_memory_bytes": maximum_cgroup_memory_bytes,
            "geekbench5_single_core_score": score,
            "runtime_limit_seconds": runtime_limit,
        },
        "claim_authority": "memory_safe_external_parent_only" if qualified else "none",
        "promotion_authority": qualified,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.Draft202012Validator(json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))).validate(output)
    return output, verified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--exclusive-lease", required=True, type=Path)
    parser.add_argument("--verification", required=True, type=Path)
    args = parser.parse_args()
    lease = args.exclusive_lease
    lock = lease.with_name(f"{lease.name}.lock")
    if lease.exists() or lease.is_symlink() or lock.exists() or lock.is_symlink():
        raise SystemExit("exclusive full-1G lease namespace is occupied")
    receipt_path = regular_file(args.receipt, "qualification router")
    if args.verification.exists() or args.verification.is_symlink():
        raise SystemExit("verification output already exists")
    output, verified = verify(receipt_path)
    write_new(args.verification, output)
    print(json.dumps(output, sort_keys=True, indent=2))
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
