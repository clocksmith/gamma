#!/usr/bin/env python3
"""Run the frozen WIKI-PDA v2 ceiling only under active q1-v3 authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import cmix_memory_safe_parent_qualification_verify_v3 as parent_v3
import wiki_pda_structural_replay_ceiling_q0_v2 as legacy


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = legacy.CANDIDATE_ID
RESULT = legacy.RESULT
SOURCE = legacy.SOURCE
INTERFACE = legacy.INTERFACE
SCAN_SCHEMA = legacy.SCAN_SCHEMA
EXPERIMENT = legacy.EXPERIMENT
PROPOSAL = legacy.PROPOSAL
CANDIDATE_REVISION = legacy.CANDIDATE_REVISION
PLAN = (
    PROJECT
    / "operations/planning/"
    "wiki_pda_structural_replay_ceiling_q0_v2_execution_v2.json"
)
PLAN_SCHEMA = (
    PROJECT / "operations/planning/wiki-pda-ceiling-execution-plan-v2.schema.json"
)
DECISION_SCHEMA = (
    PROJECT / "operations/planning/wiki-pda-ceiling-decision-v2.schema.json"
)
RESOURCE_SCHEMA = legacy.RESOURCE_SCHEMA
MANIFEST_SCHEMA = legacy.MANIFEST_SCHEMA
VERIFICATION_SCHEMA = legacy.VERIFICATION_SCHEMA
SHARED_HELPER = legacy.SHARED_HELPER
LEGACY_RUNNER = Path(legacy.__file__).resolve(strict=True)
VERIFIER = (
    PROJECT
    / "tools/wiki_pda_structural_replay_ceiling_q0_v2_authority_v3_verify.py"
)
LEGACY_VERIFIER = (
    PROJECT / "tools/wiki_pda_structural_replay_ceiling_q0_v2_verify.py"
)

PARENT_DESIGN_POLICY = (
    PROJECT
    / "operations/planning/"
    "cmix_obias_memory_safe_parent_filebacked_q1_qualification_policy_v6.json"
)
PARENT_POLICY_SCHEMA = parent_v3.POLICY_SCHEMA
PARENT_RECEIPT_SCHEMA = parent_v3.SOURCE_SCHEMA
PARENT_VERIFICATION_SCHEMA = parent_v3.OUTPUT_SCHEMA
PARENT_VERIFIER = Path(parent_v3.__file__).resolve(strict=True)
PARENT_SOURCE_CLOSURE = parent_v3.SOURCE_CLOSURE

RESOURCE_GUARD = legacy.RESOURCE_GUARD
RESOURCE_GUARD_SCHEMA = legacy.RESOURCE_GUARD_SCHEMA
LEASE_IMPLEMENTATION = legacy.LEASE_IMPLEMENTATION
LEASE_VERIFIER = legacy.LEASE_VERIFIER
LEASE_SCHEMA = legacy.LEASE_SCHEMA
LEASE = legacy.LEASE
LEASE_LOCK = legacy.LEASE_LOCK
INPUT = legacy.INPUT
COMPILER = legacy.COMPILER
LOADER_LIBRARY = legacy.LOADER_LIBRARY
LD_LIBRARY_PATH = legacy.LD_LIBRARY_PATH
TASKSET = legacy.TASKSET
CGROUP_A = legacy.CGROUP_A
CGROUP_B = legacy.CGROUP_B

INPUT_BYTES = legacy.INPUT_BYTES
INPUT_SHA256 = legacy.INPUT_SHA256
REQUIRED_CORRECT_BYTES = legacy.REQUIRED_CORRECT_BYTES
TREE_LIMIT_KIB = legacy.TREE_LIMIT_KIB
CGROUP_LIMIT_BYTES = legacy.CGROUP_LIMIT_BYTES
SCRATCH_LIMIT_BYTES = legacy.SCRATCH_LIMIT_BYTES
CANDIDATE_TREE_SHA256 = legacy.CANDIDATE_TREE_SHA256
COMPILE_FLAGS = legacy.COMPILE_FLAGS
BASE_ENVIRONMENT = legacy.BASE_ENVIRONMENT
COMPILE_ENVIRONMENT = legacy.COMPILE_ENVIRONMENT
CLAIM_BOUNDARY = legacy.CLAIM_BOUNDARY
shared = legacy.shared

sha256 = legacy.sha256
display_path = legacy.display_path
canonical_sha256 = legacy.canonical_sha256
artifact = legacy.artifact
write_bytes_exclusive = legacy.write_bytes_exclusive
write_json_exclusive = legacy.write_json_exclusive
validate_with_schema = legacy.validate_with_schema
assert_regular_no_symlink = legacy.assert_regular_no_symlink
resolve_project_path = legacy.resolve_project_path
verify_reference = legacy.verify_reference
hash_population = legacy.hash_population
scan_command = legacy.scan_command
semantic_scan_checks = legacy.semantic_scan_checks
validate_guard = legacy.validate_guard
resource_summary = legacy.resource_summary
derive_measurements = legacy.derive_measurements
derive_gates = legacy.derive_gates
empty_scan = legacy.empty_scan
empty_gates = legacy.empty_gates
result_manifest = legacy.result_manifest


def load_object(path: Path, label: str) -> dict[str, Any]:
    assert_regular_no_symlink(path, one_link=True)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return value


def project_evidence(path: Path, label: str) -> Path:
    path = path.absolute()
    assert_regular_no_symlink(path, one_link=True)
    resolved = path.resolve(strict=True)
    if PROJECT not in resolved.parents:
        raise RuntimeError(f"{label} escapes the project: {path}")
    return resolved


def validate_parent(
    receipt_path: Path,
    verification_path: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    bytes,
    dict[str, Any],
    Path,
]:
    receipt_path = project_evidence(receipt_path, "q1-v3 qualification receipt")
    verification_path = project_evidence(
        verification_path, "q1-v3 qualification verification"
    )
    receipt = load_object(receipt_path, "q1-v3 qualification receipt")
    verification = load_object(
        verification_path, "q1-v3 qualification verification"
    )
    validate_with_schema(receipt, PARENT_RECEIPT_SCHEMA)
    validate_with_schema(verification, PARENT_VERIFICATION_SCHEMA)
    receipt_digest = sha256(receipt_path)
    authority = verification.get("authority", {})
    active_policy_record = authority.get("authority_policy")
    if not isinstance(active_policy_record, dict):
        raise RuntimeError("q1-v3 verification lacks active policy binding")
    active_policy_path = resolve_project_path(active_policy_record["path"])
    verify_reference(active_policy_record, active_policy_path)
    policy = load_object(active_policy_path, "active q1 authority policy")
    parent_v3.validate_policy(policy)
    checks = verification.get("checks", {})
    evidence_checks = verification.get("evidence_checks", {})
    if (
        verification.get("verified") is not True
        or verification.get("qualified") is not True
        or verification.get("errors") != []
        or verification.get("qualification_failures") != []
        or verification.get("receipt_sha256") != receipt_digest
        or not isinstance(checks, dict)
        or not checks
        or not all(checks.values())
        or not isinstance(evidence_checks, dict)
        or not evidence_checks
        or not all(evidence_checks.values())
        or verification.get("claim_authority")
        != "memory_safe_external_parent_only"
        or verification.get("promotion_authority") is not True
        or authority.get("policy_revision", 0) < 7
        or verification.get("gamma_compression_credit_bytes") != 0
        or verification.get("gamma_score_credit_bytes") != 0
        or receipt.get("authority_policy") != active_policy_record
    ):
        raise RuntimeError("q1-v3 parent qualification is not fully positive")
    if LEASE.exists() or LEASE.is_symlink() or LEASE_LOCK.exists() or LEASE_LOCK.is_symlink():
        raise RuntimeError("exclusive full-1G namespace is occupied")
    fresh, verified = parent_v3.verify(receipt_path, active_policy_path, LEASE)
    if not verified or fresh != verification:
        raise RuntimeError("fresh q1-v3 verification differs from stored authority")
    reverified_raw = (
        json.dumps(fresh, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    )
    return (
        artifact(receipt_path, receipt_digest),
        artifact(verification_path),
        reverified_raw,
        artifact(active_policy_path),
        active_policy_path,
    )


def validate_plan(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    validate_with_schema(plan, PLAN_SCHEMA)
    expected_implementation = {
        "source": SOURCE,
        "interface": INTERFACE,
        "scan_schema": SCAN_SCHEMA,
        "runner": Path(__file__).resolve(strict=True),
        "verifier": VERIFIER,
        "shared_helper": SHARED_HELPER,
        "legacy_runner": LEGACY_RUNNER,
        "legacy_verifier": LEGACY_VERIFIER,
    }
    bindings: dict[str, dict[str, Any]] = {}
    for key, expected in expected_implementation.items():
        record = {
            "path": plan["implementation"][key],
            "sha256": plan["implementation"][f"{key}_sha256"],
        }
        bindings[key] = verify_reference(record, expected)
    bindings["candidate_revision"] = verify_reference(
        plan["candidate_revision"], CANDIDATE_REVISION
    )
    revision = load_object(CANDIDATE_REVISION, "candidate revision")
    if (
        revision["candidateId"] != CANDIDATE_ID
        or revision["candidateTreeSha256"]
        != f"sha256:{plan['candidate_revision']['candidate_tree_sha256']}"
        or plan["candidate_revision"]["candidate_tree_sha256"]
        != CANDIDATE_TREE_SHA256
    ):
        raise RuntimeError("candidate revision identity mismatch")
    bindings["experiment"] = verify_reference(plan["experiment"], EXPERIMENT)
    bindings["proposal"] = verify_reference(plan["proposal"], PROPOSAL)
    expected_schemas = {
        "plan": PLAN_SCHEMA,
        "decision": DECISION_SCHEMA,
        "resource_summary": RESOURCE_SCHEMA,
        "output_manifest": MANIFEST_SCHEMA,
        "verification": VERIFICATION_SCHEMA,
    }
    if set(plan["schemas"]) != set(expected_schemas):
        raise RuntimeError("execution schema role set mismatch")
    for key, expected in expected_schemas.items():
        bindings[f"schema_{key}"] = verify_reference(
            plan["schemas"][key], expected
        )
    parent_expected = {
        "design_policy": PARENT_DESIGN_POLICY,
        "authority_policy_schema": PARENT_POLICY_SCHEMA,
        "receipt_schema": PARENT_RECEIPT_SCHEMA,
        "verification_schema": PARENT_VERIFICATION_SCHEMA,
        "verifier": PARENT_VERIFIER,
        "python_source_closure": PARENT_SOURCE_CLOSURE,
    }
    if set(plan["parent_qualification"]) != set(parent_expected):
        raise RuntimeError("parent qualification role set mismatch")
    for key, expected in parent_expected.items():
        bindings[f"parent_{key}"] = verify_reference(
            plan["parent_qualification"][key], expected
        )
    for key, expected in (
        ("lease_implementation", LEASE_IMPLEMENTATION),
        ("lease_schema", LEASE_SCHEMA),
        ("lease_verifier", LEASE_VERIFIER),
    ):
        plan_key = key.removeprefix("lease_")
        bindings[key] = verify_reference(
            plan["exclusive_lane"][plan_key], expected
        )
    bindings["resource_guard"] = verify_reference(
        plan["resource_guard"]["implementation"], RESOURCE_GUARD
    )
    bindings["resource_guard_schema"] = verify_reference(
        plan["resource_guard"]["receipt_schema"], RESOURCE_GUARD_SCHEMA
    )
    for key, expected in (
        ("compiler", COMPILER),
        ("loader_library", LOADER_LIBRARY),
        ("taskset", TASKSET),
    ):
        path = Path(plan["toolchain"][key])
        assert_regular_no_symlink(path)
        digest = sha256(path)
        if path != expected or digest != plan["toolchain"][f"{key}_sha256"]:
            raise RuntimeError(f"toolchain binding mismatch: {key}")
        bindings[key] = artifact(path, digest)
    expected_outputs = [
        f"results/{CANDIDATE_ID}/lease-evidence.json",
        f"results/{CANDIDATE_ID}/lease-transitions.json",
        f"results/{CANDIDATE_ID}/scan-a.json",
        f"results/{CANDIDATE_ID}/scan-b.json",
        f"results/{CANDIDATE_ID}/resource-guard.json",
        f"results/{CANDIDATE_ID}/decision.json",
        f"results/{CANDIDATE_ID}/output-manifest.json",
    ]
    expected_command = [
        "python3",
        "tools/wiki_pda_structural_replay_ceiling_q0_v2_authority_v3.py",
        "--parent-qualification-receipt",
        "<schema-valid-active-policy-v7+-q1-v3-qualification-receipt>",
        "--parent-qualification-verification",
        "<schema-valid-independent-q1-v3-verification>",
    ]
    if (
        plan["toolchain"]["ld_library_path"] != str(LD_LIBRARY_PATH)
        or plan["toolchain"]["compile_flags"] != COMPILE_FLAGS
        or plan["population"]
        != {"path": str(INPUT), "bytes": INPUT_BYTES, "sha256": INPUT_SHA256}
        or plan["resource_guard"]["limit_kib"] != TREE_LIMIT_KIB
        or plan["resource_guard"]["cgroup_memory_max_bytes"]
        != CGROUP_LIMIT_BYTES
        or plan["resource_guard"]["scratch_limit_bytes"]
        != SCRATCH_LIMIT_BYTES
        or plan["resource_guard"]["max_logical_cpus"] != 1
        or plan["resource_guard"]["cpu"] != 0
        or plan["resource_guard"]["cgroup_a"] != str(CGROUP_A)
        or plan["resource_guard"]["cgroup_b"] != str(CGROUP_B)
        or plan["exclusive_lane"]["lease"] != display_path(LEASE)
        or plan["exclusive_lane"]["lock"] != display_path(LEASE_LOCK)
        or plan["command_template"] != expected_command
        or plan["outputs"] != expected_outputs
    ):
        raise RuntimeError("execution plan constants mismatch")
    bindings["execution_plan"] = artifact(PLAN)
    bindings["execution_plan_schema"] = artifact(PLAN_SCHEMA)
    return bindings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-qualification-receipt", required=True, type=Path)
    parser.add_argument(
        "--parent-qualification-verification", required=True, type=Path
    )
    args = parser.parse_args()
    receipt_path = (
        args.parent_qualification_receipt
        if args.parent_qualification_receipt.is_absolute()
        else PROJECT / args.parent_qualification_receipt
    )
    verification_path = (
        args.parent_qualification_verification
        if args.parent_qualification_verification.is_absolute()
        else PROJECT / args.parent_qualification_verification
    )
    if RESULT.exists() or RESULT.is_symlink():
        raise FileExistsError(f"refusing to overwrite result root: {RESULT}")
    for path in (CGROUP_A, CGROUP_B, LEASE, LEASE_LOCK):
        if path.exists() or path.is_symlink():
            raise RuntimeError(f"exclusive execution namespace occupied: {path}")
    plan = load_object(PLAN, "WIKI-PDA v3-authority execution plan")
    bindings = validate_plan(plan)
    (
        parent_receipt,
        parent_verification,
        parent_reverification,
        active_policy,
        active_policy_path,
    ) = validate_parent(receipt_path, verification_path)
    preflight_hashes = {
        path: sha256(path)
        for path in (
            PLAN,
            SOURCE,
            INTERFACE,
            SCAN_SCHEMA,
            EXPERIMENT,
            PROPOSAL,
            CANDIDATE_REVISION,
            SHARED_HELPER,
            LEGACY_RUNNER,
            VERIFIER,
            LEGACY_VERIFIER,
            PARENT_DESIGN_POLICY,
            PARENT_POLICY_SCHEMA,
            PARENT_RECEIPT_SCHEMA,
            PARENT_VERIFICATION_SCHEMA,
            PARENT_VERIFIER,
            PARENT_SOURCE_CLOSURE,
            active_policy_path,
            receipt_path,
            verification_path,
        )
    }
    RESULT.mkdir(mode=0o700, parents=True)
    invocation = {
        "argv": [str(Path(__file__).resolve()), *sys.argv[1:]],
        "cwd": str(PROJECT),
        "environment": BASE_ENVIRONMENT,
    }
    from managed_exclusive_lease import ManagedExclusiveLease

    try:
        lease = ManagedExclusiveLease.acquire(
            lease_path=LEASE,
            transition_path=RESULT / "lease-transitions.json",
            candidate_id=CANDIDATE_ID,
            command_sha256=canonical_sha256(invocation),
            runner_sha256=bindings["runner"]["sha256"],
            guard_path=str(RESULT),
            result_path=str(RESULT),
            scratch_path=str(RESULT),
            claim_boundary=(
                "Managed exclusive lane for two zero-credit WIKI-PDA scans; "
                "no signal authority."
            ),
        )
    except Exception:
        RESULT.rmdir()
        raise
    write_bytes_exclusive(
        RESULT / "parent-reverification.json", parent_reverification
    )
    decision: dict[str, Any] = {
        "schema": "gamma.enwiki9.wiki-pda-ceiling-decision.v2",
        "candidate_id": CANDIDATE_ID,
        "operational_status": "terminal_infrastructure_failure",
        "claim_boundary": CLAIM_BOUNDARY,
        "claim_authority": "causal_shadow_opportunity_screen_only",
        "bindings": bindings,
        "parent_qualification": {
            "receipt": parent_receipt,
            "verification": parent_verification,
            "independent_reverification": artifact(
                RESULT / "parent-reverification.json"
            ),
            "active_policy": active_policy,
            "authority_design_policy": artifact(PARENT_DESIGN_POLICY),
            "fully_positive": True,
        },
        "population": {
            "path": str(INPUT),
            "bytes": INPUT_BYTES,
            "sha256": INPUT_SHA256,
            "verified": False,
        },
        "exclusive_lease": {
            "lease_id": lease.record["lease_id"],
            "release_pass": False,
            "evidence": None,
            "transitions": None,
        },
        "compile": None,
        "scans": {"a": empty_scan(), "b": empty_scan()},
        "resource_summary": None,
        "measurements": None,
        "gates": empty_gates(),
        "scientific_verdict": "none_infrastructure_failure",
        "promotion_authorized": False,
        "next_authority": "one_correction_only_runner_successor",
        "archive_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
        "error": None,
    }
    try:
        decision["population"]["verified"] = hash_population() == INPUT_SHA256
        lease.heartbeat()
        binary = RESULT / "wiki-pda-ceiling-scan"
        compile_record, _, _ = shared.run_command(
            step_id="compile",
            argv=[str(COMPILER), *COMPILE_FLAGS, str(SOURCE), "-o", str(binary)],
            environment=COMPILE_ENVIRONMENT,
            stdout_path=RESULT / "compile.stdout",
            stderr_path=RESULT / "compile.stderr",
            lease=lease,
        )
        decision["compile"] = compile_record
        if compile_record["returncode"] != 0:
            raise RuntimeError("scanner compilation failed")
        scans: dict[str, dict[str, Any]] = {}
        guards: dict[str, dict[str, Any]] = {}
        for arm, cgroup in (("a", CGROUP_A), ("b", CGROUP_B)):
            receipt = RESULT / f"scan-{arm}.json"
            guard_path = RESULT / f"guard-{arm}.json"
            command, current_peak, file_peak = shared.run_command(
                step_id=f"scan_{arm}",
                argv=scan_command(binary, receipt, guard_path, cgroup, arm),
                environment=BASE_ENVIRONMENT,
                stdout_path=RESULT / f"scan-{arm}.stdout",
                stderr_path=RESULT / f"scan-{arm}.stderr",
                lease=lease,
                cgroup_path=cgroup,
            )
            if (
                command["returncode"] != 0
                or not receipt.is_file()
                or not guard_path.is_file()
            ):
                raise RuntimeError(f"scanner arm {arm} failed")
            scan = load_object(receipt, f"scanner arm {arm}")
            guard = load_object(guard_path, f"resource guard {arm}")
            validate_with_schema(scan, SCAN_SCHEMA)
            semantic_scan_checks(scan)
            validate_guard(guard)
            if cgroup.exists():
                raise RuntimeError(f"scanner cgroup {arm} was not cleaned")
            scans[arm] = {
                "command": command,
                "receipt": artifact(receipt),
                "guard": artifact(guard_path),
                "sampled_cgroup_file_peak_bytes": file_peak,
                "sampled_cgroup_current_peak_bytes": current_peak,
            }
            guards[arm] = guard
            decision["scans"][arm] = scans[arm]
            lease.heartbeat()
        scan_a_path = RESULT / "scan-a.json"
        scan_b_path = RESULT / "scan-b.json"
        scan_a = load_object(scan_a_path, "scanner arm a")
        scan_b = load_object(scan_b_path, "scanner arm b")
        repeat = (
            scan_a_path.read_bytes() == scan_b_path.read_bytes()
            and scan_a == scan_b
        )
        resources = resource_summary(guards, scans)
        write_json_exclusive(RESULT / "resource-guard.json", resources)
        decision["resource_summary"] = artifact(RESULT / "resource-guard.json")
        measurements = derive_measurements(scan_a, resources, repeat)
        gates = derive_gates(scan_a, measurements, resources, repeat)
        decision["measurements"] = measurements
        decision["gates"] = gates
        for path, digest in preflight_hashes.items():
            if sha256(path) != digest:
                raise RuntimeError(
                    f"source or antecedent drifted during execution: {path}"
                )
        passed = gates["all_promotion_predicates_pass"]
        decision.update(
            {
                "operational_status": "terminal",
                "scientific_verdict": (
                    "authorize_retained_parent_donor_surprise_trace_zero_credit"
                    if passed
                    else "retire_exact_wiki_pda_information_source"
                ),
                "promotion_authorized": passed,
                "next_authority": (
                    "retained_parent_donor_surprise_trace_only"
                    if passed
                    else "one_materially_different_information_source"
                ),
            }
        )
    except Exception as error:
        decision["error"] = f"{type(error).__name__}: {error}"
    finally:
        try:
            lease.heartbeat()
            lease.release(evidence_path=RESULT / "lease-evidence.json")
            decision["exclusive_lease"] = {
                "lease_id": lease.record["lease_id"],
                "release_pass": True,
                "evidence": artifact(RESULT / "lease-evidence.json"),
                "transitions": artifact(RESULT / "lease-transitions.json"),
            }
        except Exception as lease_error:
            message = (
                "lease release failure: "
                f"{type(lease_error).__name__}: {lease_error}"
            )
            decision["error"] = (
                message
                if decision["error"] is None
                else f"{decision['error']}; {message}"
            )
            decision.update(
                {
                    "operational_status": "terminal_infrastructure_failure",
                    "scientific_verdict": "none_infrastructure_failure",
                    "promotion_authorized": False,
                    "next_authority": "one_correction_only_runner_successor",
                }
            )
    validate_with_schema(decision, DECISION_SCHEMA)
    write_json_exclusive(RESULT / "decision.json", decision)
    write_json_exclusive(
        RESULT / "output-manifest.json",
        result_manifest(decision["operational_status"] == "terminal"),
    )
    return 0 if decision["operational_status"] == "terminal" else 1


if __name__ == "__main__":
    raise SystemExit(main())
