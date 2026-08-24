#!/usr/bin/env python3
"""Independently rederive CMIX midpoint persistence attribution v2."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "research" / "v1"
RECEIPT_SCHEMA_PATH = CONTRACTS / "cmix-midpoint-persistence-attribution-receipt-v2.schema.json"
OUTPUT_SCHEMA_PATH = CONTRACTS / "cmix-midpoint-persistence-attribution-verification-v2.schema.json"
Q1_SCHEMA_PATH = CONTRACTS / "cmix-memory-safe-parent-qualification-verification-v2.schema.json"
ORACLE_SCHEMA_PATH = CONTRACTS / "cmix-shadow-midpoint-oracle-authority.schema.json"

CANDIDATE_ID = "cmix_obias_midpoint_persistence_attribution64_q0_v2"
RECEIPT_SCHEMA = "gamma.enwiki9.cmix-midpoint-persistence-attribution-receipt.v2"
OUTPUT_SCHEMA = "gamma.enwiki9.cmix-midpoint-persistence-attribution-verification.v2"
Q1_SCHEMA = "gamma.enwiki9.cmix-memory-safe-parent-qualification-verification.v2"
ORACLE_SCHEMA = "gamma.enwiki9.cmix-shadow-midpoint-oracle-authority.v1"
EXPECTED_EVIDENCE_ROLES = {
    "planning_contract",
    "experiment_contract",
    "receipt_schema",
    "verifier",
    "q1_policy",
    "q1_qualification_verification",
    "oracle_contract",
    "oracle_authority_verification",
    "source_tree_manifest",
    "build_receipt",
    "binary",
    "population_manifest",
    "package_manifest",
}
REJOIN_PREDICATES = (
    "P_J_parent_branch_identity_pass",
    "F_J_adapted_trajectory_identity_pass",
    "identical_truth_stream_pass",
    "parent_native_cadence_pass",
    "coder_not_forked_or_rewound_pass",
    "truth_only_shared_state_audit_pass",
    "no_writable_alias_pass",
    "no_adapted_persistent_write_survived_pass",
    "live_negative_mutation_control_pass",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def load_schema(path: Path) -> dict[str, Any]:
    value = load_json(path)
    jsonschema.Draft202012Validator.check_schema(value)
    return value


def resolve_regular(root: Path, reference: Any, label: str, errors: list[str]) -> Path | None:
    if not isinstance(reference, dict):
        errors.append(f"{label}: reference must be an object")
        return None
    raw = reference.get("path")
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        errors.append(f"{label}: path must be a nonempty string")
        return None
    relative = PurePosixPath(raw)
    if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != raw:
        errors.append(f"{label}: unsafe or noncanonical path")
        return None
    current = root
    try:
        for part in relative.parts:
            current = current / part
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                errors.append(f"{label}: symlink component forbidden")
                return None
        metadata = current.stat()
    except OSError as exc:
        errors.append(f"{label}: cannot inspect path: {exc}")
        return None
    if not stat.S_ISREG(metadata.st_mode):
        errors.append(f"{label}: expected a regular file")
        return None
    if metadata.st_nlink != 1:
        errors.append(f"{label}: hard-linked evidence forbidden")
        return None
    if reference.get("bytes") != metadata.st_size:
        errors.append(f"{label}: byte count mismatch")
    digest = sha256_file(current)
    if reference.get("sha256") != digest:
        errors.append(f"{label}: SHA-256 mismatch")
    return current


def require_document(
    role: str,
    paths: dict[str, Path],
    errors: list[str],
) -> dict[str, Any]:
    path = paths.get(role)
    if path is None:
        return {}
    try:
        return load_json(path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"{role}: {exc}")
        return {}


def derive_decision(
    *,
    scope_bytes: int,
    prerequisites_pass: bool,
    exactness_pass: bool,
    rejoin_pass: bool,
    resources_pass: bool,
    F_gain: int,
    F_beats_S: bool,
    retention_pass: bool,
) -> dict[str, str]:
    if not prerequisites_pass:
        return {
            "terminal_classification": "invalid_receipt",
            "scientific_verdict": "invalid",
            "authorized_successor": "none",
        }
    if not exactness_pass or not resources_pass:
        return {
            "terminal_classification": "fail_exactness_resource_or_package",
            "scientific_verdict": "none",
            "authorized_successor": "none",
        }
    if not rejoin_pass:
        return {
            "terminal_classification": "fail_rejoin_identity",
            "scientific_verdict": "none",
            "authorized_successor": "one_correction_only_rejoin_implementation_successor",
        }
    required_gain = {250000: 0, 1000000: 4080, 10000000: 40793}.get(scope_bytes)
    if required_gain is None:
        return {
            "terminal_classification": "invalid_receipt",
            "scientific_verdict": "invalid",
            "authorized_successor": "none",
        }
    if scope_bytes == 250000:
        return {
            "terminal_classification": "pass_250k_exactness_authorize_1m",
            "scientific_verdict": "none",
            "authorized_successor": "same_candidate_1m_calibration",
        }
    if F_gain < required_gain:
        return {
            "terminal_classification": "fail_full_oracle_subscale",
            "scientific_verdict": "fail",
            "authorized_successor": "none_retire_cmix_midpoint_family",
        }
    if not F_beats_S:
        return {
            "terminal_classification": "fail_causal_control",
            "scientific_verdict": "fail",
            "authorized_successor": "none_retire_cmix_midpoint_family",
        }
    if scope_bytes == 1000000:
        return {
            "terminal_classification": "pass_1m_target_scale_authorize_10m",
            "scientific_verdict": "none",
            "authorized_successor": "same_candidate_10m_attribution",
        }
    if retention_pass:
        return {
            "terminal_classification": "pass_local_fork_retains_at_least_0_8",
            "scientific_verdict": "pass",
            "authorized_successor": "cmix_obias_safe_fork_midas64_q0_v2",
        }
    return {
        "terminal_classification": "pass_persistent_effect_requires_functional_jvp",
        "scientific_verdict": "pass",
        "authorized_successor": "cmix_obias_functional_jvp_persistence_attribution_q0_v1",
    }


def verify(receipt_path: Path, evidence_root: Path) -> tuple[dict[str, Any], bool]:
    errors: list[str] = []
    receipt_hash = "0" * 64
    receipt: dict[str, Any] = {}
    try:
        if receipt_path.is_symlink() or not receipt_path.is_file():
            raise ValueError("receipt must be a non-symlink regular file")
        if receipt_path.stat().st_nlink != 1:
            raise ValueError("receipt must not be hard linked")
        receipt_hash = sha256_file(receipt_path)
        receipt = load_json(receipt_path)
        jsonschema.Draft202012Validator(load_schema(RECEIPT_SCHEMA_PATH)).validate(receipt)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, jsonschema.ValidationError, jsonschema.SchemaError) as exc:
        errors.append(f"receipt: {exc}")

    if not evidence_root.is_dir() or evidence_root.is_symlink():
        errors.append("evidence root must be a non-symlink directory")
    evidence = receipt.get("evidence") if isinstance(receipt.get("evidence"), dict) else {}
    if set(evidence) != EXPECTED_EVIDENCE_ROLES:
        errors.append("evidence roles differ from the exact frozen set")
    paths: dict[str, Path] = {}
    evidence_hashes: dict[str, str] = {}
    for role in sorted(EXPECTED_EVIDENCE_ROLES):
        path = resolve_regular(evidence_root, evidence.get(role), role, errors)
        if path is not None:
            paths[role] = path
            evidence_hashes[role] = sha256_file(path)

    if evidence_hashes.get("receipt_schema") != sha256_file(RECEIPT_SCHEMA_PATH):
        errors.append("receipt_schema does not bind the verifier's exact schema")
    if evidence_hashes.get("verifier") != sha256_file(Path(__file__).resolve()):
        errors.append("verifier evidence does not bind the executing verifier")

    planning = require_document("planning_contract", paths, errors)
    experiment = require_document("experiment_contract", paths, errors)
    q1_policy = require_document("q1_policy", paths, errors)
    q1 = require_document("q1_qualification_verification", paths, errors)
    oracle_contract = require_document("oracle_contract", paths, errors)
    oracle = require_document("oracle_authority_verification", paths, errors)
    if planning.get("artifact_id") != CANDIDATE_ID:
        errors.append("planning contract identity mismatch")
    if experiment.get("experimentId") != CANDIDATE_ID or experiment.get("proposalId") != CANDIDATE_ID:
        errors.append("experiment identity mismatch")
    if q1_policy.get("artifact_id") != "cmix_obias_memory_safe_parent_filebacked_q1_qualification_policy_v4":
        errors.append("q1 policy identity mismatch")
    if oracle_contract.get("candidate_id") != "cmix_obias_shadow_midpoint_oracle64_q0_v2":
        errors.append("oracle contract identity mismatch")

    try:
        jsonschema.Draft202012Validator(load_schema(Q1_SCHEMA_PATH)).validate(q1)
    except (jsonschema.ValidationError, jsonschema.SchemaError, ValueError) as exc:
        errors.append(f"q1 qualification verification: {exc}")
    try:
        jsonschema.Draft202012Validator(load_schema(ORACLE_SCHEMA_PATH)).validate(oracle)
    except (jsonschema.ValidationError, jsonschema.SchemaError, ValueError) as exc:
        errors.append(f"oracle authority verification: {exc}")
    q1_pass = (
        q1.get("schema") == Q1_SCHEMA
        and q1.get("verified") is True
        and q1.get("qualified") is True
        and isinstance(q1.get("checks"), dict)
        and bool(q1["checks"])
        and all(value is True for value in q1["checks"].values())
        and q1.get("errors") == []
        and q1.get("qualification_failures") == []
        and q1.get("promotion_authority") is True
        and q1.get("claim_authority") == "memory_safe_external_parent_only"
        and q1.get("gamma_score_credit_bytes") == 0
    )
    oracle_pass = (
        oracle.get("schema") == ORACLE_SCHEMA
        and oracle.get("verified") is True
        and oracle.get("scientific_verdict") == "pass"
        and oracle.get("persistence_attribution_activation_authority") is True
        and oracle.get("score_credit_bytes") == 0
    )
    prerequisites_pass = q1_pass and oracle_pass
    if not q1_pass:
        errors.append("q1 terminal qualification authority is absent")
    if not oracle_pass:
        errors.append("shadow midpoint oracle terminal authority is absent")

    arms = receipt.get("arms") if isinstance(receipt.get("arms"), dict) else {}
    scope = receipt.get("scope") if isinstance(receipt.get("scope"), dict) else {}
    scope_bytes = scope.get("raw_bytes")
    required_gain = {250000: 0, 1000000: 4080, 10000000: 40793}.get(scope_bytes)
    if scope.get("required_F_gain_bytes") != required_gain:
        errors.append("scope required F gain differs from the frozen ladder")
    exactness_pass = scope.get("complete_population_pass") is True
    for name in ("P", "F", "J", "S"):
        arm = arms.get(name) if isinstance(arms.get(name), dict) else {}
        exactness_pass = exactness_pass and all(
            arm.get(field) == 0
            for field in ("encode_return_code", "decode_return_code", "raw_inverse_return_code")
        )
        exactness_pass = exactness_pass and all(
            arm.get(field) is True
            for field in ("raw_inverse_pass", "repeat_identity_pass", "resource_pass", "dependency_closure_pass")
        )
        exactness_pass = exactness_pass and arm.get("archive_sha256") == arm.get("repeat_archive_sha256")

    rejoin = receipt.get("rejoin") if isinstance(receipt.get("rejoin"), dict) else {}
    rejoin_pass = all(rejoin.get(field) is True for field in REJOIN_PREDICATES)
    rejoin_pass = rejoin_pass and rejoin.get("P_join_state_stream_sha256") == rejoin.get("J_parent_join_state_stream_sha256")
    rejoin_pass = rejoin_pass and rejoin.get("F_adapted_second_half_stream_sha256") == rejoin.get("J_adapted_second_half_stream_sha256")

    resources = receipt.get("resources") if isinstance(receipt.get("resources"), dict) else {}
    resources_pass = all(
        resources.get(field) is True
        for field in ("all_arm_resource_pass", "dependency_closure_pass", "package_pass")
    )
    rss = resources.get("maximum_process_tree_rss_kib")
    cgroup = resources.get("maximum_cgroup_memory_bytes")
    package = resources.get("incremental_package_bytes")
    resources_pass = resources_pass and isinstance(rss, int) and rss <= 9765625
    resources_pass = resources_pass and isinstance(cgroup, int) and cgroup < 10000000000
    resources_pass = resources_pass and isinstance(package, int) and package <= 65536

    P_bytes = arms.get("P", {}).get("archive_bytes")
    F_bytes = arms.get("F", {}).get("archive_bytes")
    J_bytes = arms.get("J", {}).get("archive_bytes")
    S_bytes = arms.get("S", {}).get("archive_bytes")
    if not all(isinstance(value, int) for value in (P_bytes, F_bytes, J_bytes, S_bytes)):
        errors.append("arm archive byte counts are incomplete")
        P_bytes = F_bytes = J_bytes = S_bytes = 0
    F_gain = P_bytes - F_bytes
    J_gain = P_bytes - J_bytes
    S_gain = P_bytes - S_bytes
    F_beats_S = F_bytes < S_bytes
    retention_pass = F_gain > 0 and 5 * J_gain >= 4 * F_gain
    reported = receipt.get("reported") if isinstance(receipt.get("reported"), dict) else {}
    expected_reported = {
        "F_gain_bytes": F_gain,
        "J_gain_bytes": J_gain,
        "S_gain_bytes": S_gain,
        "F_beats_S_pass": F_beats_S,
        "retention_numerator_bytes": J_gain,
        "retention_denominator_bytes": F_gain,
        "retention_threshold_numerator": 4,
        "retention_threshold_denominator": 5,
        "fork_retention_pass": retention_pass,
    }
    if reported != expected_reported:
        errors.append("reported comparison values differ from exact archive arithmetic")

    decision = derive_decision(
        scope_bytes=scope_bytes if isinstance(scope_bytes, int) else 0,
        prerequisites_pass=prerequisites_pass,
        exactness_pass=exactness_pass,
        rejoin_pass=rejoin_pass,
        resources_pass=resources_pass,
        F_gain=F_gain,
        F_beats_S=F_beats_S,
        retention_pass=retention_pass,
    )
    if receipt.get("decision") != decision:
        errors.append("reported terminal decision differs from independent derivation")

    verified = not errors
    successor_authority = verified and decision["authorized_successor"] not in {
        "none",
        "none_retire_cmix_midpoint_family",
    }
    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "verified": verified,
        "errors": errors,
        "receipt_sha256": receipt_hash,
        "evidence_sha256": evidence_hashes,
        "computed": {
            "F_gain_bytes": F_gain,
            "J_gain_bytes": J_gain,
            "S_gain_bytes": S_gain,
            "F_beats_S_pass": F_beats_S,
            "retention_numerator_bytes": J_gain,
            "retention_denominator_bytes": F_gain,
            "fork_retention_pass": retention_pass,
            "exactness_pass": exactness_pass,
            "rejoin_pass": rejoin_pass,
            "resources_pass": resources_pass,
        },
        "decision": decision,
        "successor_activation_authority": successor_authority,
        "compression_credit_bytes": 0,
        "score_credit_bytes": 0,
    }
    jsonschema.Draft202012Validator(load_schema(OUTPUT_SCHEMA_PATH)).validate(output)
    return output, verified


def write_new(path: Path, value: dict[str, Any]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit("verification output already exists")
    output, verified = verify(args.receipt, args.evidence_root)
    write_new(args.output, output)
    print(json.dumps(output, sort_keys=True, indent=2))
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
