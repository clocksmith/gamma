#!/usr/bin/env python3
"""Grant q1 parent authority only through an exact active policy and plan binding."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

import jsonschema

import cmix_memory_safe_parent_qualification_verify_v2 as evidence_v2
from enwiki9_python_source_closure import local_source_closure


PROJECT = Path(__file__).resolve().parents[1]
CONTRACTS = PROJECT / "contracts/research/v1"
OBJECTIVE = CONTRACTS / "objective-contract.json"
SOURCE_SCHEMA = CONTRACTS / "cmix-memory-safe-parent-qualification-receipt-v3.schema.json"
OUTPUT_SCHEMA = CONTRACTS / "cmix-memory-safe-parent-qualification-verification-v3.schema.json"
EVIDENCE_SCHEMA = CONTRACTS / "cmix-memory-safe-parent-qualification-receipt-v2.schema.json"
POLICY_SCHEMA = (
    PROJECT
    / "operations/planning/cmix-memory-safe-parent-qualification-authority-policy.schema.json"
)
SOURCE_CLOSURE = (
    PROJECT
    / "operations/planning/cmix_memory_safe_parent_qualification_v3_python_source_closure_q0_v1.json"
)
SOURCE_SCHEMA_ID = "gamma.enwiki9.cmix-memory-safe-parent-qualification-receipt.v3"
OUTPUT_SCHEMA_ID = "gamma.enwiki9.cmix-memory-safe-parent-qualification-verification.v3"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
PARENT_ID = "cmix_obias_source_full1g_roundtrip_a_qm0_v1"
ACTIVE_STATUS = "active_qualification_authority"
ACTIVE_CLAIM = "memory_safe_external_parent_only"
EXPECTED_REVOKED_AUTHORITIES = {
    "qualification_v1",
    "qualification_v2_unbound_policy",
    "qualification_policy_v1",
    "qualification_policy_v2",
    "qualification_policy_v3",
    "qualification_policy_v4",
    "qualification_policy_v5",
    "qualification_policy_v6_design_only",
}


artifact = evidence_v2.artifact
artifact_matches = evidence_v2.artifact_matches
load_json = evidence_v2.load_json
regular_file = evidence_v2.regular_file
sha256_file = evidence_v2.sha256_file
validate_direct = evidence_v2.validate_direct
write_new = evidence_v2.write_new


def validate_policy(value: dict[str, Any]) -> None:
    schema = json.loads(POLICY_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)
    if value.get("$schema") != POLICY_SCHEMA.name:
        raise ValueError("authority policy schema identity mismatch")


def objective_record() -> dict[str, Any]:
    value = json.loads(OBJECTIVE.read_text(encoding="utf-8"))
    return {
        "id": value["objectiveId"],
        "sha256": sha256_file(OBJECTIVE),
        "corpus_bytes": value["corpus"]["bytes"],
        "corpus_sha256": value["corpus"]["sha256"],
        "target_score_bytes": value["score"]["targetBytes"],
    }


def policy_revision_matches(policy: dict[str, Any]) -> bool:
    match = re.fullmatch(
        r"cmix_obias_memory_safe_parent_filebacked_q1_qualification_policy_v([0-9]+)",
        str(policy.get("artifact_id", "")),
    )
    return bool(match and int(match.group(1)) == policy.get("revision"))


def expected_source_closure() -> list[dict[str, str]]:
    return [
        {
            "path": path.relative_to(PROJECT).as_posix(),
            "sha256": f"sha256:{sha256_file(path)}",
        }
        for path in local_source_closure((Path(__file__).resolve(),))
    ]


def verify(
    receipt_path: Path,
    policy_path: Path,
    exclusive_lease: Path,
) -> tuple[dict[str, Any], bool]:
    router = load_json(receipt_path)
    validate_direct(router, SOURCE_SCHEMA, SOURCE_SCHEMA_ID)
    policy_path = regular_file(policy_path, "active qualification policy")
    evidence_path = regular_file(
        Path(router["evidence_router"]["path"]), "v2 evidence router"
    )
    plan_path: Path

    checks = {
        "router_schema_pass": True,
        "objective_binding_pass": router["objective"] == objective_record(),
        "artifact_closure_pass": (
            artifact_matches(router["evidence_router"], "v2 evidence router")
            and artifact_matches(router["authority_policy"], "authority policy")
            and Path(router["authority_policy"]["path"]).resolve(strict=True)
            == policy_path
        ),
        "v2_evidence_reopened_pass": False,
        "policy_schema_pass": False,
        "policy_activation_pass": False,
        "policy_evidence_binding_pass": False,
        "policy_source_binding_pass": False,
        "authority_source_closure_pass": False,
        "activated_plan_binding_pass": False,
        "exclusive_namespace_pass": False,
    }

    evidence_router = load_json(evidence_path)
    validate_direct(
        evidence_router,
        EVIDENCE_SCHEMA,
        evidence_v2.SOURCE_SCHEMA_ID,
    )
    evidence_verification, evidence_verified = evidence_v2.verify(evidence_path)
    checks["v2_evidence_reopened_pass"] = bool(
        evidence_verified
        and evidence_verification["verified"] is True
        and evidence_verification["qualified"] is False
        and evidence_verification["promotion_authority"] is False
        and evidence_verification["claim_authority"] == "none"
        and evidence_verification["errors"] == []
        and evidence_verification["qualification_failures"]
        == [evidence_v2.AUTHORITY_REVOKED_REASON]
        and all(evidence_verification["checks"].values())
    )

    full_identity_path = regular_file(
        Path(evidence_router["artifacts"]["full_identity_receipt"]["path"]),
        "full identity receipt",
    )
    full_identity = load_json(full_identity_path)
    activated_plan_record = full_identity["planning_contract"]
    plan_path = regular_file(
        Path(activated_plan_record["path"]), "activated full identity plan"
    )
    activated_plan = load_json(plan_path)

    policy = load_json(policy_path)
    validate_policy(policy)
    checks["policy_schema_pass"] = True
    checks["policy_activation_pass"] = bool(
        policy_revision_matches(policy)
        and policy["revision"] >= 7
        and policy["operational_status"] == ACTIVE_STATUS
        and policy["candidate_id"] == CANDIDATE_ID
        and policy["authoritative_parent_id"] == PARENT_ID
        and policy["claim_authority"] == ACTIVE_CLAIM
        and policy["objective"] == objective_record()
        and set(policy["revoked_authorities"]) == EXPECTED_REVOKED_AUTHORITIES
    )
    checks["policy_evidence_binding_pass"] = bool(
        policy["bindings"]["evidence_router"] == router["evidence_router"]
        and policy["bindings"]["activated_full_identity_plan"]
        == activated_plan_record
    )
    expected_source_bindings = {
        "evidence_router_schema": artifact(EVIDENCE_SCHEMA),
        "evidence_verification_schema": artifact(evidence_v2.OUTPUT_SCHEMA),
        "evidence_verifier": artifact(Path(evidence_v2.__file__).resolve()),
        "authority_router_schema": artifact(SOURCE_SCHEMA),
        "authority_verification_schema": artifact(OUTPUT_SCHEMA),
        "authority_verifier": artifact(Path(__file__).resolve()),
        "authority_python_source_closure": artifact(SOURCE_CLOSURE),
    }
    checks["policy_source_binding_pass"] = all(
        policy["bindings"][role] == record
        for role, record in expected_source_bindings.items()
    )
    source_closure = json.loads(SOURCE_CLOSURE.read_text(encoding="ascii"))
    checks["authority_source_closure_pass"] = (
        source_closure == expected_source_closure()
    )
    checks["activated_plan_binding_pass"] = bool(
        artifact_matches(activated_plan_record, "activated full identity plan")
        and policy["bindings"]["activated_full_identity_plan"]
        == artifact(plan_path)
        and activated_plan.get("artifact_id")
        == "cmix_filebacked_fxcm_full_probability_state_identity_q0_v1"
        and activated_plan.get("revision", 0) >= 7
        and activated_plan.get("operational_status")
        == "activated_owned_lane_after_all_dependencies"
        and activated_plan.get("execution_authorized") is True
    )

    expected_lease = PROJECT / policy["exclusive_namespace"]["lease"]
    expected_lock = PROJECT / policy["exclusive_namespace"]["lock"]
    supplied_lease = exclusive_lease.absolute()
    checks["exclusive_namespace_pass"] = bool(
        supplied_lease == expected_lease.absolute()
        and expected_lock == supplied_lease.with_name(f"{supplied_lease.name}.lock")
        and policy["exclusive_namespace"]["required_absent"] is True
        and not supplied_lease.exists()
        and not supplied_lease.is_symlink()
        and not expected_lock.exists()
        and not expected_lock.is_symlink()
    )

    errors: list[str] = []
    failures = [
        f"qualification predicate failed: {name}"
        for name, passed in checks.items()
        if not passed
    ]
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
        "artifact_sha256": {
            "evidence_router": sha256_file(evidence_path),
            "authority_policy": sha256_file(policy_path),
            "activated_full_identity_plan": sha256_file(plan_path),
        },
        "checks": checks,
        "evidence_checks": evidence_verification["checks"],
        "derived": evidence_verification["derived"],
        "authority": {
            "policy_artifact_id": policy["artifact_id"],
            "policy_revision": policy["revision"],
            "authority_policy": artifact(policy_path),
            "activated_full_identity_plan": artifact(plan_path),
        },
        "claim_authority": ACTIVE_CLAIM if qualified else "none",
        "promotion_authority": qualified,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.Draft202012Validator(
        json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))
    ).validate(output)
    return output, verified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--exclusive-lease", required=True, type=Path)
    parser.add_argument("--verification", required=True, type=Path)
    args = parser.parse_args()
    lease = args.exclusive_lease.absolute()
    lock = lease.with_name(f"{lease.name}.lock")
    if lease.exists() or lease.is_symlink() or lock.exists() or lock.is_symlink():
        raise SystemExit("exclusive full-1G lease namespace is occupied")
    receipt_path = regular_file(args.receipt, "qualification authority router")
    if args.verification.exists() or args.verification.is_symlink():
        raise SystemExit("verification output already exists")
    output, verified = verify(receipt_path, args.policy, lease)
    if not verified or output["qualified"] is not True:
        print(json.dumps(output, sort_keys=True, indent=2))
        return 1
    write_new(args.verification, output)
    print(json.dumps(output, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
