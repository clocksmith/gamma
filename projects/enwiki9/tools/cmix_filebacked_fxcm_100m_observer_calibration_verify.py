#!/usr/bin/env python3
"""Independently verify the sealed q1 observer calibration receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import jsonschema

import cmix_filebacked_fxcm_100m_identity_resource_verify as proof
import cmix_filebacked_fxcm_scope_identity as scope


INPUT_SCHEMA = (
    proof.PROJECT
    / "contracts/research/v1/"
    "cmix-filebacked-fxcm-100m-observer-calibration.schema.json"
)
OUTPUT_SCHEMA = (
    proof.PROJECT
    / "contracts/research/v1/"
    "cmix-filebacked-fxcm-100m-observer-calibration-verification.schema.json"
)
INPUT_SCHEMA_SHA256 = "009de365b89e83bc395d2f55332bc5b4f39de4ff0f0ddcb2727d6f1bba45c18a"
OUTPUT_SCHEMA_SHA256 = "d107e2bb9949c138c71a281a566a8c04318bdae3e345be1b5c0e1edde9a42cd3"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
RUN_CONTRACT = (
    (0, "I-P", "post_head", True),
    (0, "I-Q", "post_head", True),
    (0, "N-P", "pre_head", True),
    (500_000_000, "I-P", "post_head", False),
    (500_000_000, "I-Q", "post_head", False),
)
FIXED_SCOPES = {
    0: (10_000_000, "5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97"),
    500_000_000: (
        10_000_000,
        "17dfa1d4d228170583555711d5aab51a740475da194657f3db272a0b31a0d7af",
    ),
}


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": proof.digest_file(path),
    }


def false_comparisons() -> dict[str, bool]:
    return {
        "all_runs_complete": False,
        "opening_post_head_reference_pass": False,
        "distant_post_head_reference_pass": False,
        "parent_q1_probability_identity_pass": False,
        "parent_q1_coder_identity_pass": False,
        "parent_q1_state_identity_pass": False,
        "pre_head_probability_negative_control_pass": False,
        "pre_head_payload_identity_pass": False,
        "pre_head_state_identity_pass": False,
        "all_payload_reference_identity_pass": False,
        "opening_all_raw_inverses_pass": False,
        "opening_all_transformed_inverses_pass": False,
        "state_mutation_control_pass": False,
        "observer_calibration_pass": False,
    }


def load_json_artifact(record: dict[str, Any], label: str) -> tuple[Path, dict[str, Any]]:
    path = proof.resolve_artifact(record, label)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return path, value


def observer_geometry(run: dict[str, Any]) -> bool:
    _, probability = load_json_artifact(
        run["probability_summary"], "probability summary"
    )
    coder_path = proof.resolve_artifact(run["coder_checkpoints"], "coder checkpoints")
    state_path = proof.resolve_artifact(run["persistent_state"], "persistent state")
    coder = [json.loads(line) for line in coder_path.read_text().splitlines()]
    state = [json.loads(line) for line in state_path.read_text().splitlines()]
    transformed_bytes = run["transformed_input"]["bytes"]
    probability_sha256 = probability.get("post_head_probability_sha256")
    ranges = [record for record in state if "ordinal" in record]
    manifests = [record for record in state if "manifest_sha256" in record]
    return (
        probability_sha256 == run["probability_sha256"]
        and probability.get("completed_coded_bytes") == transformed_bytes
        and probability.get("coded_bits") == transformed_bytes * 8
        and len(coder) == 2
        and [record.get("kind") for record in coder] == ["start", "terminal"]
        and coder[0].get("completed_coded_bytes") == 0
        and coder[0].get("coded_bits") == 0
        and coder[-1].get("completed_coded_bytes") == transformed_bytes
        and coder[-1].get("coded_bits") == transformed_bytes * 8
        and coder[-1].get("probability_sha256") == probability_sha256
        and len(state) == 54
        and len(ranges) == 52
        and len(manifests) == 2
        and {record.get("kind") for record in ranges} == {"start", "terminal"}
        and all(
            {record.get("ordinal") for record in ranges if record.get("kind") == kind}
            == set(range(26))
            for kind in ("start", "terminal")
        )
        and all(
            isinstance(record.get("bytes"), int)
            and record["bytes"] >= 64 * 1024 * 1024
            and isinstance(record.get("alignment"), int)
            and record["alignment"] > 0
            and record["alignment"] & (record["alignment"] - 1) == 0
            for record in ranges
        )
        and [record.get("kind") for record in manifests] == ["start", "terminal"]
        and all(record.get("allocation_count") == 26 for record in manifests)
        and manifests[0].get("checkpoint") == 0
        and manifests[1].get("checkpoint") == transformed_bytes
    )


def transfer_expectations(transfer: dict[str, Any]) -> dict[int, dict[str, Any]]:
    values: dict[int, dict[str, Any]] = {}
    for item in transfer["scopes"]:
        offset = item["offset"]
        if offset not in FIXED_SCOPES or offset in values:
            raise RuntimeError("transfer scope set differs from calibration contract")
        arms = {arm["arm"]: arm for arm in item["arms"]}
        if set(arms) != {"parent", "candidate"}:
            raise RuntimeError("transfer arm set differs from calibration contract")
        parent_probability = arms["parent"]["trace"][
            "integer_probability_stream_sha256"
        ]
        candidate_probability = arms["candidate"]["trace"][
            "integer_probability_stream_sha256"
        ]
        if parent_probability != candidate_probability:
            raise RuntimeError("transfer probability identity failed")
        values[offset] = {
            "probability_sha256": parent_probability,
            "payload": {
                name: arm["payload"] for name, arm in arms.items()
            },
        }
    if set(values) != set(FIXED_SCOPES):
        raise RuntimeError("transfer scopes are incomplete")
    return values


def derive(receipt: dict[str, Any]) -> tuple[dict[str, Any], dict[str, bool], list[str]]:
    errors: list[str] = []
    records: list[tuple[str, dict[str, Any]]] = [
        (f"antecedent {name}", record)
        for name, record in receipt["antecedents"].items()
    ]
    artifact_fields = (
        "package",
        "reference_payload",
        "encode_guard",
        "probability_summary",
        "coder_checkpoints",
        "persistent_state",
        "transformed_input",
        "arithmetic_payload",
        "self_extracting_archive",
        "decode_guard",
        "decoded_transformed",
        "raw_inverse",
    )
    for index, run in enumerate(receipt["runs"]):
        for field in artifact_fields:
            record = run[field]
            if record is not None:
                records.append((f"run {index} {field}", record))
    _, plan = load_json_artifact(
        receipt["antecedents"]["planning_contract"], "planning contract"
    )
    proof.validate_planning_contract(plan)
    calibration_contract = plan.get("observer_calibration", {})
    joint_verification_contract = plan.get("independent_verification", {})
    verifier_path = Path(__file__).resolve()
    proof_path = Path(proof.__file__).resolve()
    plan_binding = (
        plan.get("candidate_id") == CANDIDATE_ID
        and calibration_contract.get("independent_verifier")
        == str(verifier_path.relative_to(proof.PROJECT))
        and calibration_contract.get("independent_verifier_sha256")
        == proof.digest_file(verifier_path)
        and calibration_contract.get("receipt_schema_sha256")
        == INPUT_SCHEMA_SHA256
        and calibration_contract.get("verification_schema_sha256")
        == OUTPUT_SCHEMA_SHA256
        and joint_verification_contract.get("verifier")
        == str(proof_path.relative_to(proof.PROJECT))
        and joint_verification_contract.get("verifier_sha256")
        == proof.digest_file(proof_path)
    )
    if not plan_binding:
        errors.append("planning contract verifier binding failed")
    _, build = load_json_artifact(
        receipt["antecedents"]["observer_build"], "observer build"
    )
    _, build_schema = load_json_artifact(
        receipt["antecedents"]["observer_build_schema"], "observer build schema"
    )
    jsonschema.Draft202012Validator.check_schema(build_schema)
    jsonschema.validate(build, build_schema)
    mutation_control = build["state_mutation_control"]
    for field in (
        "source",
        "binary",
        "persistent_state",
        "coder_checkpoints",
        "probability_summary",
    ):
        records.append((f"state mutation control {field}", mutation_control[field]))
    verified_count = 0
    for label, record in records:
        try:
            proof.resolve_artifact(record, label)
            verified_count += 1
        except (OSError, RuntimeError, ValueError) as error:
            errors.append(str(error))
    all_artifacts = verified_count == len(records)

    fixed_scopes = {
        item["offset"]: (item["bytes"], item["slice_sha256"])
        for item in receipt["fixed_scopes"]
    }
    run_shape = tuple(
        (run["offset"], run["arm"], run["probability_tap"], run["decode_required"])
        for run in receipt["runs"]
    )
    fixed_run_contract = (
        plan_binding and fixed_scopes == FIXED_SCOPES and run_shape == RUN_CONTRACT
    )

    geometry_results: list[bool] = []
    for index, run in enumerate(receipt["runs"]):
        try:
            geometry_results.append(observer_geometry(run))
            guard_path, guard = load_json_artifact(run["encode_guard"], "encode guard")
            del guard_path
            if run["encode_return_code"] != 0 or not scope.guard_pass(guard):
                errors.append(f"run {index} encode guard does not pass")
            if run["decode_required"]:
                _, decode_guard = load_json_artifact(run["decode_guard"], "decode guard")
                if run["decode_return_code"] != 0 or not scope.guard_pass(decode_guard):
                    errors.append(f"run {index} decode guard does not pass")
            elif any(
                run[field] is not None
                for field in (
                    "decode_return_code",
                    "decode_guard",
                    "decode_guard_pass",
                    "decoded_transformed",
                    "raw_inverse",
                    "transformed_inverse_pass",
                    "raw_inverse_pass",
                )
            ):
                errors.append(f"run {index} has forbidden distant decode evidence")
        except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
            geometry_results.append(False)
            errors.append(f"run {index} geometry: {error}")
    geometry_pass = (
        len(geometry_results) == len(RUN_CONTRACT)
        and all(geometry_results)
        and all(run["observer_geometry_pass"] is True for run in receipt["runs"])
    )

    transfer_path, transfer = load_json_artifact(
        receipt["antecedents"]["opening_distant_10m_receipt"],
        "opening/distant receipt",
    )
    _, transfer_verification = load_json_artifact(
        receipt["antecedents"]["opening_distant_10m_verification"],
        "opening/distant verification",
    )
    if (
        transfer_verification.get("verification_pass") is not True
        or transfer_verification.get("source_receipt", {}).get("sha256")
        != proof.digest_file(transfer_path)
    ):
        errors.append("opening/distant verification binding failed")
    expected = transfer_expectations(transfer)
    by_key = {(run["offset"], run["arm"]): run for run in receipt["runs"]}
    complete = fixed_run_contract and len(by_key) == len(RUN_CONTRACT)

    def run(offset: int, arm: str) -> dict[str, Any]:
        return by_key[(offset, arm)]

    reference_probability: dict[int, bool] = {}
    for offset in FIXED_SCOPES:
        reference_probability[offset] = complete and all(
            run(offset, arm)["probability_sha256"]
            == expected[offset]["probability_sha256"]
            for arm in ("I-P", "I-Q")
        )
    probability_identity = complete and all(
        run(offset, "I-P")["probability_sha256"]
        == run(offset, "I-Q")["probability_sha256"]
        for offset in FIXED_SCOPES
    )
    coder_identity = complete and all(
        run(offset, "I-P")["coder_checkpoints"]["sha256"]
        == run(offset, "I-Q")["coder_checkpoints"]["sha256"]
        for offset in FIXED_SCOPES
    )
    state_identity = complete and all(
        run(offset, "I-P")["persistent_state"]["sha256"]
        == run(offset, "I-Q")["persistent_state"]["sha256"]
        for offset in FIXED_SCOPES
    )
    negative_probability = complete and (
        run(0, "N-P")["probability_sha256"]
        != run(0, "I-P")["probability_sha256"]
    )
    negative_payload = complete and (
        run(0, "N-P")["arithmetic_payload"]["sha256"]
        == run(0, "I-P")["arithmetic_payload"]["sha256"]
    )
    negative_state = complete and (
        run(0, "N-P")["persistent_state"]["sha256"]
        == run(0, "I-P")["persistent_state"]["sha256"]
    )
    payload_reference = complete
    for item in receipt["runs"]:
        reference_role = "candidate" if item["arm"] == "I-Q" else "parent"
        expected_record = expected[item["offset"]]["payload"][reference_role]
        payload_reference &= (
            item["reference_payload"]["bytes"] == expected_record["bytes"]
            and item["reference_payload"]["sha256"] == expected_record["sha256"]
            and item["arithmetic_payload"]["bytes"] == expected_record["bytes"]
            and item["arithmetic_payload"]["sha256"] == expected_record["sha256"]
            and item["payload_reference_identity_pass"] is True
        )
    opening_inverse = complete and all(
        item["raw_inverse"] is not None
        and item["raw_inverse"]["bytes"] == FIXED_SCOPES[0][0]
        and item["raw_inverse"]["sha256"] == FIXED_SCOPES[0][1]
        and item["raw_inverse_pass"] is True
        for item in receipt["runs"]
        if item["offset"] == 0
    )
    transformed_inverse = complete and all(
        item["decoded_transformed"] is not None
        and item["decoded_transformed"]["bytes"] == item["transformed_input"]["bytes"]
        and item["decoded_transformed"]["sha256"] == item["transformed_input"]["sha256"]
        and item["transformed_inverse_pass"] is True
        for item in receipt["runs"]
        if item["offset"] == 0
    )
    mutation = (
        build.get("decisions", {}).get("state_mutation_control_pass") is True
        and build.get("state_mutation_control", {}).get("pass") is True
        and build["state_mutation_control"].get("range_digest_changed") is True
        and build["state_mutation_control"].get("aggregate_digest_changed") is True
        and build["state_mutation_control"].get("terminal_matches_mutation") is True
    )
    derived = {
        "all_runs_complete": complete,
        "opening_post_head_reference_pass": reference_probability.get(0, False),
        "distant_post_head_reference_pass": reference_probability.get(500_000_000, False),
        "parent_q1_probability_identity_pass": probability_identity,
        "parent_q1_coder_identity_pass": coder_identity,
        "parent_q1_state_identity_pass": state_identity,
        "pre_head_probability_negative_control_pass": negative_probability,
        "pre_head_payload_identity_pass": negative_payload,
        "pre_head_state_identity_pass": negative_state,
        "all_payload_reference_identity_pass": bool(payload_reference),
        "opening_all_raw_inverses_pass": opening_inverse,
        "opening_all_transformed_inverses_pass": transformed_inverse,
        "state_mutation_control_pass": mutation,
    }
    derived["observer_calibration_pass"] = all(derived.values()) and geometry_pass
    if receipt["comparisons"] != derived:
        errors.append("declared calibration comparisons differ from rederivation")
    if receipt["terminal_pass"] is not (
        derived["observer_calibration_pass"] and receipt["errors"] == []
    ):
        errors.append("terminal calibration decision differs from rederivation")
    checks = {
        "required_artifact_count": len(records),
        "verified_artifact_count": verified_count,
        "all_artifacts_pass": all_artifacts,
        "fixed_run_contract_pass": fixed_run_contract,
        "observer_geometry_pass": geometry_pass,
    }
    return checks, derived, errors


def schemas() -> tuple[dict[str, Any], dict[str, Any]]:
    if proof.digest_file(INPUT_SCHEMA) != INPUT_SCHEMA_SHA256:
        raise RuntimeError("calibration input schema hash drift")
    if proof.digest_file(OUTPUT_SCHEMA) != OUTPUT_SCHEMA_SHA256:
        raise RuntimeError("calibration verification schema hash drift")
    input_schema = json.loads(INPUT_SCHEMA.read_text())
    output_schema = json.loads(OUTPUT_SCHEMA.read_text())
    jsonschema.Draft202012Validator.check_schema(input_schema)
    jsonschema.Draft202012Validator.check_schema(output_schema)
    return input_schema, output_schema


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    args = parser.parse_args()

    proof.require_released_lease(args.exclusive_lease)
    input_schema, output_schema = schemas()
    receipt_path = proof.regular_file(args.receipt, "calibration receipt", project_only=True)
    output_path = proof.new_output_path(args.verification)
    receipt_raw = receipt_path.read_bytes()
    receipt = json.loads(receipt_raw)
    planning_contract = proof.resolve_artifact(
        receipt["antecedents"]["planning_contract"], "planning contract"
    )
    errors: list[str] = []
    schema_valid = True
    try:
        jsonschema.validate(receipt, input_schema)
    except jsonschema.ValidationError as error:
        schema_valid = False
        errors.append(f"receipt schema: {error.message}")
    checks = {
        "required_artifact_count": 0,
        "verified_artifact_count": 0,
        "all_artifacts_pass": False,
        "fixed_run_contract_pass": False,
        "observer_geometry_pass": False,
    }
    derived = false_comparisons()
    if schema_valid:
        try:
            checks, derived, derived_errors = derive(receipt)
            errors.extend(derived_errors)
        except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
            errors.append(f"rederivation: {error}")
    verified = (
        schema_valid
        and checks["all_artifacts_pass"]
        and checks["fixed_run_contract_pass"]
        and checks["observer_geometry_pass"]
        and not errors
    )
    passed = (
        verified
        and derived["observer_calibration_pass"]
        and receipt.get("terminal_pass") is True
        and receipt.get("errors") == []
    )
    output = {
        "schema": (
            "gamma.enwiki9.cmix-filebacked-fxcm-100m-"
            "observer-calibration-verification.v1"
        ),
        "candidate_id": CANDIDATE_ID,
        "verifier": artifact(Path(__file__).resolve()),
        "input_schema": artifact(INPUT_SCHEMA),
        "output_schema": artifact(OUTPUT_SCHEMA),
        "planning_contract": artifact(planning_contract),
        "verified": verified,
        "passed": passed,
        "errors": errors,
        "receipt_sha256": proof.digest_bytes(receipt_raw),
        "artifact_checks": checks,
        "derived_comparisons": derived,
        "claim_authority": "none",
        "promotion_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.validate(output, output_schema)
    proof.write_json_exclusive(output_path, output)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
