#!/usr/bin/env python3
"""Independently rederive a FOSSIL-MATCH v3 causal-shadow decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import fxcm_fossil_match_q0_v3 as contract
import managed_exclusive_lease_verify


PROJECT = Path(__file__).resolve().parents[1]
RESULT = PROJECT / "results/fxcm_fossil_match_q0_v3"


def require(condition: bool, message: str, checks: dict[str, bool], key: str) -> None:
    checks[key] = bool(condition)
    if not condition:
        raise RuntimeError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON root is not an object: {path}")
    return value


def resolve_artifact(record: dict[str, Any]) -> Path:
    path = Path(record["path"])
    if not path.is_absolute():
        path = PROJECT / path
    contract.assert_regular_no_symlink(path)
    if path.stat().st_size != record["bytes"] or contract.sha256(path) != record["sha256"]:
        raise RuntimeError(f"artifact record mismatch: {path}")
    return path


def verify_manifest(manifest: dict[str, Any]) -> dict[str, Path]:
    contract.validate_with_schema(manifest, contract.MANIFEST_SCHEMA)
    if (
        manifest["pre_manifest_exact_file_set_pass"] is not True
        or manifest["unexpected_pre_manifest_entries"] != []
        or manifest["complete_result_artifacts_pass"] is not True
    ):
        raise RuntimeError("output manifest is not a complete exact file set")
    roles: dict[str, Path] = {}
    for record in manifest["artifacts"]:
        role = record["role"]
        if role in roles:
            raise RuntimeError(f"duplicate manifest role: {role}")
        path = RESULT / record["path"]
        contract.assert_regular_no_symlink(path)
        if (
            path.parent != RESULT
            or path.stat().st_size != record["bytes"]
            or contract.sha256(path) != record["sha256"]
        ):
            raise RuntimeError(f"manifest path mismatch: {record}")
        roles[role] = path
    expected_roles = {
        "lease_evidence",
        "lease_transitions",
        "parent_reverification",
        "compile_stdout",
        "compile_stderr",
        "scanner_binary",
        "scan_a_receipt",
        "scan_a_guard",
        "scan_a_stdout",
        "scan_a_stderr",
        "scan_b_receipt",
        "scan_b_guard",
        "scan_b_stdout",
        "scan_b_stderr",
        "resource_summary",
        "decision",
    }
    if set(roles) != expected_roles:
        raise RuntimeError("output manifest role set mismatch")
    expected_files = {path.name for path in roles.values()} | {"output-manifest.json"}
    observed_files = {path.name for path in RESULT.iterdir()}
    if observed_files != expected_files:
        raise RuntimeError("post-manifest result file set mismatch")
    return roles


def check_command(record: dict[str, Any], expected_argv: list[str], expected_env: dict[str, str]) -> None:
    expected = {
        "argv": expected_argv,
        "cwd": str(PROJECT),
        "environment": expected_env,
    }
    if (
        record["argv"] != expected_argv
        or record["cwd"] != str(PROJECT)
        or record["environment"] != expected_env
        or record["command_sha256"] != contract.canonical_sha256(expected)
        or record["returncode"] != 0
    ):
        raise RuntimeError(f"command reconstruction mismatch: {record.get('id')}")
    resolve_artifact(record["stdout"])
    resolve_artifact(record["stderr"])


def derive_resource_summary(
    guards: dict[str, dict[str, Any]], scans: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    values = list(guards.values())
    derived = {
        "schema": "gamma.enwiki9.fxcm-fossil-match-resource-summary.v1",
        "candidate_id": contract.CANDIDATE_ID,
        "arms": {arm: scans[arm]["guard"] for arm in ("a", "b")},
        "maximum_tree_rss_kib": max(
            guard["peaks"]["max_sampled_tree_rss_kib"] for guard in values
        ),
        "maximum_process_vmhwm_kib": max(
            guard["peaks"]["max_observed_process_vmhwm_kib"] for guard in values
        ),
        "maximum_cgroup_memory_bytes": max(
            guard["peaks"]["cgroup_memory_peak_bytes"] for guard in values
        ),
        "maximum_sampled_cgroup_file_bytes": max(
            scans[arm]["sampled_cgroup_file_peak_bytes"] for arm in ("a", "b")
        ),
        "maximum_scratch_logical_bytes": max(
            guard["peaks"]["max_sampled_scratch_logical_bytes"] for guard in values
        ),
        "maximum_scratch_allocated_bytes": max(
            guard["peaks"]["max_sampled_scratch_allocated_bytes"] for guard in values
        ),
        "cgroup_max_events": sum(
            guard["cgroup_events"]["delta"]["max"] for guard in values
        ),
        "cgroup_oom_events": sum(
            guard["cgroup_events"]["delta"]["oom"] for guard in values
        ),
        "cgroup_oom_kill_events": sum(
            guard["cgroup_events"]["delta"]["oom_kill"] for guard in values
        ),
        "all_resource_predicates_pass": False,
    }
    derived["all_resource_predicates_pass"] = (
        derived["maximum_tree_rss_kib"] <= contract.TREE_LIMIT_KIB
        and derived["maximum_process_vmhwm_kib"] <= contract.TREE_LIMIT_KIB
        and derived["maximum_cgroup_memory_bytes"] <= contract.CGROUP_LIMIT_BYTES
        and derived["maximum_scratch_logical_bytes"] <= contract.SCRATCH_LIMIT_BYTES
        and derived["cgroup_max_events"] == 0
        and derived["cgroup_oom_events"] == 0
        and derived["cgroup_oom_kill_events"] == 0
    )
    return derived


def derive_measurements(scan: dict[str, Any], resources: dict[str, Any], repeat: bool) -> dict[str, Any]:
    return {
        "scanned_bytes": scan["population_bytes"],
        "active_bytes": scan["active_bytes"],
        "treatment_correct_bytes": scan["treatment_correct_bytes"],
        "alias_correct_bytes": scan["alias_correct_bytes"],
        "random_correct_bytes": scan["random_correct_bytes"],
        "negated_correct_bytes": scan["negated_correct_bytes"],
        "minimum_third_treatment_minus_max_control_correct_bytes": scan[
            "minimum_third_treatment_minus_max_control_correct_bytes"
        ],
        "positive_distance_bucket_count": scan["positive_distance_bucket_count"],
        "opportunity_fnv1a64": scan["opportunity_fnv1a64"],
        "repeat_identity_pass": repeat,
        "maximum_tree_rss_kib": resources["maximum_tree_rss_kib"],
        "maximum_cgroup_memory_bytes": resources["maximum_cgroup_memory_bytes"],
        "maximum_sampled_cgroup_file_bytes": resources[
            "maximum_sampled_cgroup_file_bytes"
        ],
    }


def derive_gates(scan: dict[str, Any], measurements: dict[str, Any], resources: dict[str, Any], repeat: bool) -> dict[str, bool]:
    gates = {
        "full_population_pass": measurements["scanned_bytes"] == contract.INPUT_BYTES,
        "target_scale_envelope_pass": measurements["active_bytes"]
        >= contract.REQUIRED_ACTIVE_BYTES,
        "all_thirds_beat_controls_pass": measurements[
            "minimum_third_treatment_minus_max_control_correct_bytes"
        ]
        > 0,
        "distance_transfer_pass": measurements["positive_distance_bucket_count"] >= 2,
        "repeat_identity_pass": repeat,
        "causal_verification_pass": scan["causal_and_verification_pass"] is True,
        "resource_pass": resources["all_resource_predicates_pass"] is True,
        "all_promotion_predicates_pass": False,
    }
    gates["all_promotion_predicates_pass"] = all(
        value for key, value in gates.items() if key != "all_promotion_predicates_pass"
    )
    return gates


def verify(args: argparse.Namespace) -> tuple[dict[str, Any], bool]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    decision_path = args.decision.resolve(strict=True)
    manifest_path = args.manifest.resolve(strict=True)
    try:
        require(decision_path == RESULT / "decision.json", "decision path mismatch", checks, "decision_path_pass")
        require(manifest_path == RESULT / "output-manifest.json", "manifest path mismatch", checks, "manifest_path_pass")
        require(
            not contract.LEASE.exists()
            and not contract.LEASE_LOCK.exists()
            and not contract.CGROUP_A.exists()
            and not contract.CGROUP_B.exists(),
            "execution namespace was not cleaned",
            checks,
            "namespace_cleanup_pass",
        )
        decision = load_json(decision_path)
        manifest = load_json(manifest_path)
        contract.validate_with_schema(decision, contract.DECISION_SCHEMA)
        roles = verify_manifest(manifest)
        require(
            roles["decision"] == decision_path,
            "manifest does not bind decision",
            checks,
            "manifest_decision_binding_pass",
        )
        require(
            decision["operational_status"] == "terminal" and decision["error"] is None,
            "decision is not a clean terminal result",
            checks,
            "terminal_status_pass",
        )

        plan = load_json(contract.PLAN)
        bindings = contract.validate_plan(plan)
        require(
            decision["bindings"] == bindings,
            "decision implementation bindings differ",
            checks,
            "source_binding_pass",
        )
        receipt_path = args.parent_qualification_receipt
        if not receipt_path.is_absolute():
            receipt_path = PROJECT / receipt_path
        parent_verification_path = args.parent_qualification_verification
        if not parent_verification_path.is_absolute():
            parent_verification_path = PROJECT / parent_verification_path
        parent_receipt, parent_verification, reverified_raw = contract.validate_parent(
            receipt_path, parent_verification_path
        )
        require(
            decision["parent_qualification"]["receipt"] == parent_receipt
            and decision["parent_qualification"]["verification"]
            == parent_verification
            and roles["parent_reverification"].read_bytes() == reverified_raw
            and decision["parent_qualification"]["fully_positive"] is True,
            "parent qualification binding or reverification mismatch",
            checks,
            "parent_v4_qualification_pass",
        )
        require(
            decision["population"]
            == {
                "path": str(contract.INPUT),
                "bytes": contract.INPUT_BYTES,
                "sha256": contract.INPUT_SHA256,
                "verified": True,
            },
            "population binding mismatch",
            checks,
            "population_binding_pass",
        )

        compile_record = decision["compile"]
        if compile_record is None:
            raise RuntimeError("compile receipt is absent")
        binary = roles["scanner_binary"]
        check_command(
            compile_record,
            [
                str(contract.COMPILER),
                *contract.COMPILE_FLAGS,
                str(contract.SOURCE),
                "-o",
                str(binary),
            ],
            contract.COMPILE_ENVIRONMENT,
        )
        require(True, "", checks, "compile_command_pass")

        scan_values: dict[str, dict[str, Any]] = {}
        guard_values: dict[str, dict[str, Any]] = {}
        for arm, cgroup in (("a", contract.CGROUP_A), ("b", contract.CGROUP_B)):
            scan_record = decision["scans"][arm]
            command = scan_record["command"]
            if command is None:
                raise RuntimeError(f"scan command {arm} is absent")
            scan_path = roles[f"scan_{arm}_receipt"]
            guard_path = roles[f"scan_{arm}_guard"]
            check_command(
                command,
                contract.scan_command(binary, scan_path, guard_path, cgroup, arm),
                contract.BASE_ENVIRONMENT,
            )
            if (
                scan_record["receipt"] != contract.artifact(scan_path)
                or scan_record["guard"] != contract.artifact(guard_path)
                or scan_record["sampled_cgroup_file_peak_bytes"] is None
                or scan_record["sampled_cgroup_current_peak_bytes"] is None
                or scan_record["sampled_cgroup_current_peak_bytes"]
                > contract.CGROUP_LIMIT_BYTES
            ):
                raise RuntimeError(f"scan artifact or sampled resource mismatch: {arm}")
            scan = load_json(scan_path)
            guard = load_json(guard_path)
            contract.validate_with_schema(scan, contract.SCAN_SCHEMA)
            contract.semantic_scan_checks(scan)
            contract.validate_guard(guard)
            expected_child = [
                str(contract.TASKSET),
                "--cpu-list",
                "0",
                str(binary),
                str(contract.INPUT),
                str(scan_path),
            ]
            if (
                guard["command"] != expected_child
                or guard["cgroup"]["path"] != str(cgroup)
                or guard["max_logical_cpus"] != 1
                or guard["limit_kib"] != contract.TREE_LIMIT_KIB
            ):
                raise RuntimeError(f"guard reconstruction mismatch: {arm}")
            scan_values[arm] = scan
            guard_values[arm] = guard
        require(True, "", checks, "scan_and_guard_reconstruction_pass")

        repeat = (
            roles["scan_a_receipt"].read_bytes()
            == roles["scan_b_receipt"].read_bytes()
            and scan_values["a"] == scan_values["b"]
        )
        require(repeat, "scan repeat identity failed", checks, "repeat_identity_pass")
        resources = derive_resource_summary(guard_values, decision["scans"])
        contract.validate_with_schema(resources, contract.RESOURCE_SCHEMA)
        retained_resources = load_json(roles["resource_summary"])
        require(
            resources == retained_resources
            and decision["resource_summary"] == contract.artifact(roles["resource_summary"]),
            "resource summary rederivation mismatch",
            checks,
            "resource_rederivation_pass",
        )
        measurements = derive_measurements(scan_values["a"], resources, repeat)
        gates = derive_gates(scan_values["a"], measurements, resources, repeat)
        require(
            decision["measurements"] == measurements and decision["gates"] == gates,
            "measurement or gate rederivation mismatch",
            checks,
            "gate_rederivation_pass",
        )
        passed = gates["all_promotion_predicates_pass"]
        expected_verdict = (
            "authorize_retained_parent_surprisal_trace_zero_credit"
            if passed
            else "retire_exact_fossil_match_information_source"
        )
        require(
            decision["scientific_verdict"] == expected_verdict
            and decision["promotion_authorized"] is passed
            and decision["archive_authority"] is False
            and decision["gamma_compression_credit_bytes"] == 0
            and decision["gamma_score_credit_bytes"] == 0,
            "scientific verdict boundary mismatch",
            checks,
            "verdict_boundary_pass",
        )

        lease_args = argparse.Namespace(
            transition_log=roles["lease_transitions"],
            terminal_lease=roles["lease_evidence"],
            output=None,
        )
        lease_verification, lease_pass = managed_exclusive_lease_verify.verify(lease_args)
        require(
            lease_pass
            and lease_verification["verified"] is True
            and lease_verification["candidate_id"] == contract.CANDIDATE_ID
            and decision["exclusive_lease"]["release_pass"] is True
            and decision["exclusive_lease"]["lease_id"]
            == lease_verification["lease_id"],
            "managed lease evidence failed",
            checks,
            "lease_verification_pass",
        )
        verified = all(checks.values())
        scientific_verdict = decision["scientific_verdict"]
        promotion_authorized = decision["promotion_authorized"]
    except Exception as error:
        errors.append(f"{type(error).__name__}: {error}")
        verified = False
        scientific_verdict = "none_verification_failure"
        promotion_authorized = False

    output = {
        "schema": "gamma.enwiki9.fxcm-fossil-match-verification.v1",
        "candidate_id": contract.CANDIDATE_ID,
        "verified": verified,
        "decision_sha256": contract.sha256(args.decision),
        "manifest_sha256": contract.sha256(args.manifest),
        "checks": checks,
        "errors": errors,
        "scientific_verdict": scientific_verdict,
        "promotion_authorized": promotion_authorized,
        "archive_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    contract.validate_with_schema(output, contract.VERIFICATION_SCHEMA)
    return output, verified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--parent-qualification-receipt", required=True, type=Path)
    parser.add_argument("--parent-qualification-verification", required=True, type=Path)
    parser.add_argument("--verification", required=True, type=Path)
    args = parser.parse_args()
    if args.verification.exists() or args.verification.is_symlink():
        raise FileExistsError(f"refusing to overwrite verification: {args.verification}")
    try:
        if RESULT in args.verification.resolve().parents:
            raise RuntimeError("verification output must remain outside the sealed result root")
    except FileNotFoundError:
        if RESULT in args.verification.absolute().parents:
            raise RuntimeError("verification output must remain outside the sealed result root")
    output, verified = verify(args)
    contract.write_json_exclusive(args.verification, output)
    print(json.dumps(output, sort_keys=True, indent=2))
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
