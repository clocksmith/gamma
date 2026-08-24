#!/usr/bin/env python3
"""Coordinate sealed parent/q1 full-corpus probability and state identity arms."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

import jsonschema

import cmix_filebacked_fxcm_100m_identity_resource_verify as proof
import cmix_filebacked_fxcm_100m_observer_calibration_verify as calibration_verify
import cmix_filebacked_fxcm_full_identity_arm as arm_tool
import cmix_filebacked_fxcm_full_soft_high_verify as full_arm_verify
import cmix_filebacked_fxcm_scope_identity as scope
import enwiki9_python_source_closure as python_source


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-identity.v1"
ARM_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-identity-arm.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
PARENT_ID = "cmix_obias_source_full1g_roundtrip_a_qm0_v1"
PLAN_ID = "cmix_filebacked_fxcm_full_probability_state_identity_q0_v1"
PARENT_PAYLOAD_BYTES = 107_730_531
PARENT_PAYLOAD_SHA256 = "889aa8074e0a84eb89997986899f1ef9f7cc0e52e87d1d36f86899fc679f5490"
CALIBRATION = {
    "opening_10m": (
        0,
        "d651255043d85fa2f9bb6076a145710edd1366cf3e634033d2b2dadcff54e97a",
        46_128_408,
    ),
    "distant_10m": (
        500_000_000,
        "4ab13c5d455f591fa2f27e8e234833f65ebbacc5e2ef4101fbd547f85aa4ec59",
        48_103_592,
    ),
}


def artifact(path: Path) -> dict[str, Any]:
    return scope.artifact(path)


def load_json(path: Path, label: str) -> tuple[Path, dict[str, Any]]:
    return scope.load_json(path, label)


def verification_matches(
    receipt_path: Path,
    verification: dict[str, Any],
    verifier: Callable[[Path], tuple[dict[str, Any], bool]],
) -> bool:
    recomputed, passed = verifier(receipt_path)
    return passed and verification == recomputed


def same_file_value(left: Any, right: Any) -> bool:
    return bool(
        isinstance(left, dict)
        and isinstance(right, dict)
        and left.get("bytes") == right.get("bytes")
        and left.get("sha256") == right.get("sha256")
    )


def opening_100m_verification_matches(
    receipt: dict[str, Any], verification: dict[str, Any]
) -> bool:
    input_schema, output_schema = proof.validate_schema_hashes()
    jsonschema.validate(receipt, input_schema)
    jsonschema.validate(verification, output_schema)
    artifacts, comparisons, resources, decisions, errors = proof.derive(receipt)
    return bool(
        errors == []
        and verification.get("errors") == []
        and verification.get("verified") is True
        and verification.get("passed") is True
        and verification.get("artifact_checks") == artifacts
        and verification.get("derived_comparisons") == comparisons
        and verification.get("derived_resources") == resources
        and verification.get("derived_decisions") == decisions
        and decisions.get("opening_100m_gate_pass") is True
    )


def calibration_verification_matches(
    receipt: dict[str, Any], verification: dict[str, Any]
) -> bool:
    input_schema, output_schema = calibration_verify.schemas()
    jsonschema.validate(receipt, input_schema)
    jsonschema.validate(verification, output_schema)
    checks, derived, errors = calibration_verify.derive(receipt)
    return bool(
        errors == []
        and verification.get("errors") == []
        and verification.get("verified") is True
        and verification.get("passed") is True
        and verification.get("artifact_checks") == checks
        and verification.get("derived_comparisons") == derived
        and receipt.get("terminal_pass") is True
    )


def checkpoint_geometry_pass(receipt: dict[str, Any]) -> bool:
    expected_prefix = (0, *arm_tool.FIXED_MODELED_CHECKPOINTS)
    coder = receipt.get("coder_checkpoints")
    state = receipt.get("state_checkpoints")
    if not isinstance(coder, list) or not isinstance(state, list) or len(coder) != 7 or len(state) != 7:
        return False
    coder_positions = tuple(item.get("modeled_bytes") for item in coder)
    state_positions = tuple(item.get("modeled_bytes") for item in state)
    kinds = ("start", *("fixed" for _ in arm_tool.FIXED_MODELED_CHECKPOINTS), "terminal")
    return bool(
        coder_positions == state_positions
        and coder_positions[:-1] == expected_prefix
        and coder_positions[-1] == receipt.get("modeled_stream", {}).get("bytes")
        and tuple(item.get("kind") for item in coder) == kinds
        and tuple(item.get("kind") for item in state) == kinds
        and all(item.get("coded_bits") == item.get("modeled_bytes") * 8 for item in coder)
    )


def python_source_closure_rows(entries: tuple[Path, ...]) -> list[dict[str, str]]:
    return [
        {
            "path": path.relative_to(proof.PROJECT).as_posix(),
            "sha256": f"sha256:{scope.sha256_file(path)}",
        }
        for path in python_source.local_source_closure(entries)
    ]


def checkpoint_negative_controls_rejected(receipt: dict[str, Any]) -> bool:
    if not checkpoint_geometry_pass(receipt):
        return False
    coder = receipt["coder_checkpoints"]
    state = receipt["state_checkpoints"]
    mutations: list[dict[str, Any]] = []
    mutations.append({**receipt, "coder_checkpoints": coder[:-1]})
    mutations.append({**receipt, "coder_checkpoints": [coder[0], *coder]})
    mutations.append({**receipt, "coder_checkpoints": [coder[1], coder[0], *coder[2:]]})
    wrong_count = json.loads(json.dumps(coder))
    wrong_count[3]["coded_bits"] += 8
    mutations.append({**receipt, "coder_checkpoints": wrong_count})
    mutations.append({**receipt, "state_checkpoints": state[:-1]})
    wrong_terminal = json.loads(json.dumps(state))
    wrong_terminal[-1]["modeled_bytes"] -= 1
    mutations.append({**receipt, "state_checkpoints": wrong_terminal})
    return all(not checkpoint_geometry_pass(value) for value in mutations)


def calibration_rows(calibration: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_key = {
        (run["offset"], run["arm"]): run
        for run in calibration.get("runs", [])
        if isinstance(run, dict)
    }
    rows: list[dict[str, Any]] = []
    for name, (offset, expected_digest, expected_bits) in CALIBRATION.items():
        run = by_key[(offset, "I-P")]
        probability_path = scope.verify_artifact_record(
            run["probability_summary"], f"{name} probability summary"
        )
        probability = json.loads(probability_path.read_text(encoding="ascii"))
        rows.append(
            {
                "population": name,
                "expected_probability_sha256": expected_digest,
                "observed_probability_sha256": run["probability_sha256"],
                "expected_coded_bits": expected_bits,
                "observed_coded_bits": probability["coded_bits"],
            }
        )
    opening_parent = by_key[(0, "I-P")]
    opening_negative = by_key[(0, "N-P")]
    controls = {
        "observer_off_payload_sha256": opening_parent["reference_payload"]["sha256"],
        "observer_on_payload_sha256": opening_parent["arithmetic_payload"]["sha256"],
        "post_head_probability_sha256": opening_parent["probability_sha256"],
        "pre_head_probability_sha256": opening_negative["probability_sha256"],
    }
    return rows, controls


def run_arm(
    *,
    role: str,
    arm_runner: Path,
    corpus: Path,
    build_receipt: Path,
    build_schema: Path,
    resource_guard: Path,
    exclusive_lease: Path,
    arm_schema: Path,
    result_root: Path,
    scratch_root: Path,
    cpu: int,
) -> tuple[Path, dict[str, Any]]:
    command = [
        sys.executable,
        str(arm_runner),
        "--role",
        role,
        "--corpus",
        str(corpus),
        "--observer-build-receipt",
        str(build_receipt),
        "--observer-build-schema",
        str(build_schema),
        "--resource-guard",
        str(resource_guard),
        "--exclusive-lease",
        str(exclusive_lease),
        "--receipt-schema",
        str(arm_schema),
        "--result-root",
        str(result_root / role),
        "--scratch-root",
        str(scratch_root / role),
        "--cpu",
        str(cpu),
    ]
    with (result_root / f"{role}.runner.stdout").open("xb") as stdout, (
        result_root / f"{role}.runner.stderr"
    ).open("xb") as stderr:
        completed = subprocess.run(command, stdout=stdout, stderr=stderr, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"full identity {role} arm failed with {completed.returncode}")
    receipt_path, receipt = load_json(
        result_root / role / "full-identity-arm-receipt.json",
        f"full identity {role} arm receipt",
    )
    return receipt_path, receipt


def arm_summary(receipt_path: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "observer_receipt": artifact(receipt_path),
        "binary": receipt["binary"],
        "return_code": receipt["return_code"],
        "modeled_stream": receipt["modeled_stream"],
        "coded_bits": receipt["coded_bits"],
        "probability_sha256": receipt["probability_sha256"],
        "coder_checkpoints": receipt["coder_checkpoints"],
        "state_checkpoints": receipt["state_checkpoints"],
        "payload": receipt["payload"],
        "self_extracting_archive": receipt["self_extracting_archive"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--full-roundtrip-a", type=Path, required=True)
    parser.add_argument("--full-roundtrip-a-verification", type=Path, required=True)
    parser.add_argument("--full-roundtrip-b", type=Path, required=True)
    parser.add_argument("--full-roundtrip-b-verification", type=Path, required=True)
    parser.add_argument("--opening-100m-receipt", type=Path, required=True)
    parser.add_argument("--opening-100m-verification", type=Path, required=True)
    parser.add_argument("--observer-build-receipt", type=Path, required=True)
    parser.add_argument("--observer-build-schema", type=Path, required=True)
    parser.add_argument("--observer-calibration-receipt", type=Path, required=True)
    parser.add_argument("--observer-calibration-verification", type=Path, required=True)
    parser.add_argument("--arm-runner", type=Path, required=True)
    parser.add_argument("--arm-schema", type=Path, required=True)
    parser.add_argument("--receipt-schema", type=Path, required=True)
    parser.add_argument("--resource-guard", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--cpu", type=int, required=True)
    args = parser.parse_args()

    proof.require_released_lease(args.exclusive_lease)
    plan_path, plan = load_json(args.plan, "full identity plan")
    if (
        plan.get("artifact_id") != PLAN_ID
        or plan.get("candidate_id") != CANDIDATE_ID
        or plan.get("execution_authorized") is not False
    ):
        raise RuntimeError("full identity planning contract mismatch")
    plan_schema_path, plan_schema = load_json(
        proof.PROJECT / "operations" / "planning" / plan.get("$schema", ""),
        "full identity planning schema",
    )
    jsonschema.Draft202012Validator.check_schema(plan_schema)
    jsonschema.validate(plan, plan_schema)
    if plan.get("planning_schema_sha256") != scope.sha256_file(plan_schema_path):
        raise RuntimeError("full identity planning schema binding mismatch")
    corpus = scope.existing_regular(args.corpus, "canonical full corpus")
    if corpus.stat().st_size != scope.CANONICAL_BYTES or scope.sha256_file(corpus) != scope.CANONICAL_SHA256:
        raise RuntimeError("canonical full corpus identity mismatch")
    arm_runner = scope.existing_regular(args.arm_runner, "full identity arm runner")
    arm_schema_path, arm_schema = load_json(args.arm_schema, "full identity arm schema")
    receipt_schema_path, receipt_schema = load_json(
        args.receipt_schema, "full identity receipt schema"
    )
    resource_guard = scope.existing_regular(args.resource_guard, "diagnostic resource guard")
    jsonschema.Draft202012Validator.check_schema(arm_schema)
    jsonschema.Draft202012Validator.check_schema(receipt_schema)
    implementation = plan.get("implementation", {})
    coordinator_path = Path(__file__).resolve(strict=True)
    verifier_record = implementation.get("verifier", {})
    verifier_path = scope.existing_regular(
        proof.PROJECT / verifier_record.get("path", ""),
        "full identity independent verifier",
    )
    source_closure_record = implementation.get("python_source_closure", {})
    source_closure_path = scope.existing_regular(
        proof.PROJECT / source_closure_record.get("path", ""),
        "full identity Python source closure",
    )
    for name, path in (
        ("coordinator", coordinator_path),
        ("arm_runner", arm_runner),
        ("arm_schema", arm_schema_path),
        ("joint_schema", receipt_schema_path),
        ("verifier", verifier_path),
        ("resource_guard", resource_guard),
        ("python_source_closure", source_closure_path),
    ):
        record = implementation.get(name, {})
        if (
            record.get("path") != str(path.relative_to(proof.PROJECT))
            or record.get("sha256") != scope.sha256_file(path)
        ):
            raise RuntimeError(f"full identity plan {name} binding mismatch")
    source_closure = json.loads(source_closure_path.read_text(encoding="ascii"))
    expected_source_closure = python_source_closure_rows(
        (coordinator_path, arm_runner, verifier_path)
    )
    if source_closure != expected_source_closure:
        raise RuntimeError("full identity Python source closure mismatch")

    activation_paths: dict[str, Path] = {}
    activation_values: dict[str, dict[str, Any]] = {}
    for name, raw_path in (
        ("full_roundtrip_a", args.full_roundtrip_a),
        ("full_roundtrip_a_verification", args.full_roundtrip_a_verification),
        ("full_roundtrip_b", args.full_roundtrip_b),
        ("full_roundtrip_b_verification", args.full_roundtrip_b_verification),
        ("opening_100m_receipt", args.opening_100m_receipt),
        ("opening_100m_verification", args.opening_100m_verification),
    ):
        activation_paths[name], activation_values[name] = load_json(raw_path, name)
    full_roundtrip_pass = all(
        (
            verification_matches(
                activation_paths[f"full_roundtrip_{arm}"],
                activation_values[f"full_roundtrip_{arm}_verification"],
                full_arm_verify.verify,
            )
            for arm in ("a", "b")
        )
    )
    arm_a = activation_values["full_roundtrip_a"]
    arm_b = activation_values["full_roundtrip_b"]
    full_roundtrip_pass = full_roundtrip_pass and all(
        same_file_value(arm_a["outputs"][name], arm_b["outputs"][name])
        for name in ("payload", "archive", "restored")
    )
    opening_100m_pass = bool(
        opening_100m_verification_matches(
            activation_values["opening_100m_receipt"],
            activation_values["opening_100m_verification"],
        )
        and activation_values["opening_100m_verification"].get("receipt_sha256")
        == scope.sha256_file(activation_paths["opening_100m_receipt"])
    )
    activation_pass = full_roundtrip_pass and opening_100m_pass
    if not activation_pass:
        raise RuntimeError("full identity activation evidence did not pass")

    build_path, build = load_json(args.observer_build_receipt, "observer build")
    build_schema_path, build_schema = load_json(args.observer_build_schema, "observer build schema")
    calibration_path, calibration = load_json(
        args.observer_calibration_receipt, "observer calibration"
    )
    calibration_verification_path, calibration_verification = load_json(
        args.observer_calibration_verification, "observer calibration verification"
    )
    jsonschema.Draft202012Validator.check_schema(build_schema)
    jsonschema.validate(build, build_schema)
    calibration_pass = bool(
        build.get("decisions", {}).get("observer_build_pass") is True
        and calibration_verification_matches(calibration, calibration_verification)
        and calibration_verification.get("receipt_sha256") == scope.sha256_file(calibration_path)
        and calibration.get("antecedents", {}).get("observer_build")
        == artifact(build_path)
        and calibration.get("antecedents", {}).get("observer_build_schema")
        == artifact(build_schema_path)
    )
    if not calibration_pass:
        raise RuntimeError("observer build or calibration evidence did not pass")

    result_root, _ = scope.absent_root(args.result_root, "full identity result root")
    scratch_root, _ = scope.absent_root(args.scratch_root, "full identity scratch root")
    if result_root == scratch_root or result_root in scratch_root.parents or scratch_root in result_root.parents:
        raise RuntimeError("full identity result and scratch roots must be disjoint")
    result_root.mkdir(mode=0o700)
    scratch_root.mkdir(mode=0o700)
    arm_receipts: dict[str, tuple[Path, dict[str, Any]]] = {}
    for role in ("parent", "q1"):
        arm_receipts[role] = run_arm(
            role=role,
            arm_runner=arm_runner,
            corpus=corpus,
            build_receipt=build_path,
            build_schema=build_schema_path,
            resource_guard=resource_guard,
            exclusive_lease=args.exclusive_lease,
            arm_schema=arm_schema_path,
            result_root=result_root,
            scratch_root=scratch_root,
            cpu=args.cpu,
        )
        jsonschema.validate(arm_receipts[role][1], arm_schema)
    if next(scratch_root.iterdir(), None) is not None:
        raise RuntimeError("full identity coordinator scratch residue survived")
    scratch_root.rmdir()

    parent = arm_receipts["parent"][1]
    q1 = arm_receipts["q1"][1]
    calibration_summary, controls = calibration_rows(calibration)
    mutation = build["state_mutation_control"]
    controls.update(
        {
            "unmutated_state_sha256": mutation["start_manifest_sha256"],
            "single_byte_mutated_state_sha256": mutation["mutation_manifest_sha256"],
            "checkpoint_negative_controls_rejected": (
                checkpoint_negative_controls_rejected(parent)
                and checkpoint_negative_controls_rejected(q1)
            ),
        }
    )
    probability_identity = bool(
        parent["coded_bits"] == q1["coded_bits"]
        and parent["probability_sha256"] == q1["probability_sha256"]
    )
    coder_identity = parent["coder_checkpoints"] == q1["coder_checkpoints"]
    state_identity = parent["state_checkpoints"] == q1["state_checkpoints"]
    modeled_identity = bool(
        parent["modeled_stream"]["bytes"] == q1["modeled_stream"]["bytes"]
        and parent["modeled_stream"]["sha256"] == q1["modeled_stream"]["sha256"]
    )
    payload_identity = bool(
        parent["payload"]["bytes"] == q1["payload"]["bytes"] == PARENT_PAYLOAD_BYTES
        and parent["payload"]["sha256"] == q1["payload"]["sha256"] == PARENT_PAYLOAD_SHA256
    )
    controls_pass = bool(
        controls["observer_off_payload_sha256"] == controls["observer_on_payload_sha256"]
        and controls["post_head_probability_sha256"] != controls["pre_head_probability_sha256"]
        and controls["unmutated_state_sha256"] != controls["single_byte_mutated_state_sha256"]
        and controls["checkpoint_negative_controls_rejected"] is True
    )
    decisions = {
        "activation_pass": activation_pass,
        "calibration_pass": calibration_pass,
        "probability_identity_pass": probability_identity,
        "coder_checkpoint_identity_pass": coder_identity,
        "state_checkpoint_identity_pass": state_identity,
        "modeled_stream_identity_pass": modeled_identity,
        "payload_identity_pass": payload_identity,
        "controls_pass": controls_pass,
        "full_identity_pass": False,
    }
    decisions["full_identity_pass"] = all(
        value for name, value in decisions.items() if name != "full_identity_pass"
    )
    errors = [f"decision failed: {name}" for name, value in decisions.items() if not value]
    receipt = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "authoritative_parent_id": PARENT_ID,
        "planning_contract": artifact(plan_path),
        "coordinator": artifact(coordinator_path),
        "arm_runner": artifact(arm_runner),
        "arm_schema": artifact(arm_schema_path),
        "python_source_closure": artifact(source_closure_path),
        "population": artifact(corpus),
        "activation": {name: artifact(path) for name, path in activation_paths.items()},
        "observer_antecedents": {
            "build_receipt": artifact(build_path),
            "build_schema": artifact(build_schema_path),
            "calibration_receipt": artifact(calibration_path),
            "calibration_verification": artifact(calibration_verification_path),
        },
        "calibration": calibration_summary,
        "arms": {
            role: arm_summary(*arm_receipts[role]) for role in ("parent", "q1")
        },
        "controls": controls,
        "decisions": decisions,
        "errors": errors,
        "terminal_pass": decisions["full_identity_pass"] and not errors,
        "claim_boundary": (
            "Full post-head probability-stream and seven-checkpoint mutation-scoped "
            "state identity only; no compression, resource, runtime, or score credit."
        ),
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.validate(receipt, receipt_schema)
    scope.write_new(result_root / "full-identity-receipt.json", receipt)
    return 0 if receipt["terminal_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
