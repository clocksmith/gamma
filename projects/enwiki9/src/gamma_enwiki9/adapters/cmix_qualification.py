"""CMIX qualification semantics, called by the research application."""
from typing import Any
import pathlib
import json
import jsonschema


def load_json(path):
    return json.loads(path.read_bytes())


def verify_activation(
    requirement: dict[str, Any],
    evidence_set: set[str],
    *, verifier, lease_path, project_file, bound_project_file, artifact_record_matches, file_sha256,
) -> dict[str, Any]:
    candidate_id = requirement.get("candidate_id")
    verification_text = requirement.get("verification_path")
    receipt_text = requirement.get("qualification_receipt_path")
    schema_text = requirement.get("verification_schema_path")
    schema_sha256 = requirement.get("verification_schema_sha256")
    verifier_text = requirement.get("verifier_path")
    verifier_sha256 = requirement.get("verifier_sha256")
    expected_claim = requirement.get("expected_claim_authority")
    minimum_revision = requirement.get("minimum_policy_revision")
    if (
        not isinstance(candidate_id, str)
        or not isinstance(verification_text, str)
        or not isinstance(receipt_text, str)
        or not isinstance(schema_text, str)
        or not isinstance(schema_sha256, str)
        or not isinstance(verifier_text, str)
        or not isinstance(verifier_sha256, str)
        or not isinstance(expected_claim, str)
        or not isinstance(minimum_revision, int)
        or minimum_revision < 7
    ):
        raise ValueError("malformed v3 parent-qualification activation requirement")
    missing = sorted({verification_text, receipt_text} - evidence_set)
    if missing:
        raise ValueError(
            "activation evidence must include required v3 parent qualification "
            f"artifacts: {', '.join(missing)}"
        )

    verification_path = project_file(
        verification_text, "v3 parent-qualification verification"
    )
    receipt_path = project_file(
        receipt_text, "v3 parent-qualification receipt"
    )
    schema_path = bound_project_file(
        schema_text, schema_sha256, "v3 parent-qualification verification schema"
    )
    verifier_path = bound_project_file(
        verifier_text, verifier_sha256, "v3 parent-qualification verifier"
    )
    if verifier_path != pathlib.Path(verifier.__file__).resolve():
        raise ValueError("bound v3 parent-qualification verifier is not the loaded verifier")

    verification = load_json(verification_path)
    schema = load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(verification)
    authority = verification.get("authority")
    checks = verification.get("checks")
    evidence_checks = verification.get("evidence_checks")
    if not isinstance(authority, dict):
        raise ValueError("v3 parent-qualification authority is malformed")
    policy_path = artifact_record_matches(
        authority.get("authority_policy"), "v3 parent-qualification policy"
    )
    plan_path = artifact_record_matches(
        authority.get("activated_full_identity_plan"),
        "v3 activated full-identity plan",
    )
    artifact_sha256 = verification.get("artifact_sha256")
    if not isinstance(artifact_sha256, dict):
        raise ValueError("v3 parent-qualification artifact digests are malformed")
    if (
        artifact_sha256.get("authority_policy") != file_sha256(policy_path)
        or artifact_sha256.get("activated_full_identity_plan")
        != file_sha256(plan_path)
        or verification.get("receipt_sha256") != file_sha256(receipt_path)
    ):
        raise ValueError("v3 parent-qualification embedded artifact digest differs")

    regenerated, regenerated_verified = verifier.verify(
        receipt_path,
        policy_path,
        lease_path,
    )
    if not regenerated_verified or regenerated != verification:
        raise ValueError(
            "v3 parent-qualification verification does not equal an exact fresh replay"
        )
    if (
        verification.get("candidate_id") != candidate_id
        or verification.get("verified") is not True
        or verification.get("qualified") is not True
        or verification.get("errors") != []
        or verification.get("qualification_failures") != []
        or not isinstance(checks, dict)
        or not checks
        or any(value is not True for value in checks.values())
        or not isinstance(evidence_checks, dict)
        or not evidence_checks
        or any(value is not True for value in evidence_checks.values())
        or verification.get("claim_authority") != expected_claim
        or verification.get("promotion_authority") is not True
        or verification.get("gamma_compression_credit_bytes") != 0
        or verification.get("gamma_score_credit_bytes") != 0
        or authority.get("policy_revision", 0) < minimum_revision
    ):
        raise ValueError("v3 parent qualification does not grant the required authority")
    return {
        "kind": "terminal_verifier",
        "candidate_id": candidate_id,
        "qualification_receipt_path": receipt_text,
        "qualification_receipt_sha256": file_sha256(receipt_path),
        "verification_path": verification_text,
        "verification_sha256": file_sha256(verification_path),
        "policy_revision": authority["policy_revision"],
        "claim_authority": verification["claim_authority"],
        "qualified": True,
    }
