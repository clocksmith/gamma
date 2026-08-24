#!/usr/bin/env python3
"""Execute two guarded zero-credit WIKI-PDA v2 causal ceiling scans."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any

import fxcm_fossil_match_q0_v3 as shared


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "wiki_pda_structural_replay_ceiling_q0_v2"
RESULT = PROJECT / "results" / CANDIDATE_ID
SOURCE = PROJECT / "programs/wiki_pda_structural_replay_ceiling_q0_v2/wiki-pda-ceiling-scan.cpp"
INTERFACE = PROJECT / "programs/wiki_pda_structural_replay_ceiling_q0_v2/interface-contract.json"
SCAN_SCHEMA = PROJECT / "programs/wiki_pda_structural_replay_ceiling_q0_v2/scan-receipt.schema.json"
EXPERIMENT = PROJECT / "operations/adaptive/experiments/wiki_pda_structural_replay_ceiling_q0_v2.json"
PROPOSAL = PROJECT / "operations/adaptive/proposals/developed/000_wiki_pda_structural_replay_ceiling_q0_v2.json"
CANDIDATE_REVISION = PROJECT / "operations/adaptive/candidate-revisions/wiki_pda_structural_replay_ceiling_q0_v2/20260824T074003807866Z_8f674767ceb8.json"
PLAN = PROJECT / "operations/planning/wiki_pda_structural_replay_ceiling_q0_v2_execution.json"
PLAN_SCHEMA = PROJECT / "operations/planning/wiki-pda-ceiling-execution-plan.schema.json"
DECISION_SCHEMA = PROJECT / "operations/planning/wiki-pda-ceiling-decision.schema.json"
RESOURCE_SCHEMA = PROJECT / "operations/planning/wiki-pda-ceiling-resource-summary.schema.json"
MANIFEST_SCHEMA = PROJECT / "operations/planning/wiki-pda-ceiling-output-manifest.schema.json"
VERIFICATION_SCHEMA = PROJECT / "operations/planning/wiki-pda-ceiling-verification.schema.json"
SHARED_HELPER = PROJECT / "tools/fxcm_fossil_match_q0_v3.py"

PARENT_POLICY = shared.PARENT_POLICY
PARENT_RECEIPT_SCHEMA = shared.PARENT_RECEIPT_SCHEMA
PARENT_VERIFICATION_SCHEMA = shared.PARENT_VERIFICATION_SCHEMA
PARENT_VERIFIER = shared.PARENT_VERIFIER
RESOURCE_GUARD = shared.RESOURCE_GUARD
RESOURCE_GUARD_SCHEMA = shared.RESOURCE_GUARD_SCHEMA
LEASE_IMPLEMENTATION = shared.LEASE_IMPLEMENTATION
LEASE_VERIFIER = shared.LEASE_VERIFIER
LEASE_SCHEMA = shared.LEASE_SCHEMA
LEASE = shared.LEASE
LEASE_LOCK = shared.LEASE_LOCK
INPUT = shared.INPUT
COMPILER = shared.COMPILER
LOADER_LIBRARY = shared.LOADER_LIBRARY
LD_LIBRARY_PATH = shared.LD_LIBRARY_PATH
TASKSET = shared.TASKSET
CGROUP_A = Path("/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/gamma-wiki-pda-ceiling-v2-a")
CGROUP_B = Path("/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/gamma-wiki-pda-ceiling-v2-b")

INPUT_BYTES = 587_138_826
INPUT_SHA256 = "7826ff63dedd526c119dda08e6e044be8fa8f6e89a55f3d6b1f3447cdfc5c1ce"
REQUIRED_CORRECT_BYTES = 4_079_243
TREE_LIMIT_KIB = 65_536
CGROUP_LIMIT_BYTES = 256_000_000
SCRATCH_LIMIT_BYTES = 100_000_000
CANDIDATE_TREE_SHA256 = "8f674767ceb8f452f24f2167460f89519957652624340ef3ecdcd1dfa2302419"
COMPILE_FLAGS = [
    "--driver-mode=g++", "-std=c++17", "-O2", "-Wall", "-Wextra",
    "-Werror", "-pedantic", "-fno-fast-math", "-ffp-contract=off",
    "-march=x86-64", "-mtune=generic", "-Wl,--build-id=none",
]
BASE_ENVIRONMENT = shared.BASE_ENVIRONMENT
COMPILE_ENVIRONMENT = {**BASE_ENVIRONMENT, "LD_LIBRARY_PATH": str(LD_LIBRARY_PATH)}
CLAIM_BOUNDARY = (
    "Two guarded scans measure only a causal optimistic correct-byte ceiling "
    "and matched-control association. They prove no probability gain, "
    "arithmetic archive gain, inverse, package score, or prize qualification."
)


sha256 = shared.sha256
display_path = shared.display_path
canonical_sha256 = shared.canonical_sha256
artifact = shared.artifact
write_bytes_exclusive = shared.write_bytes_exclusive
write_json_exclusive = shared.write_json_exclusive
validate_with_schema = shared.validate_with_schema
assert_regular_no_symlink = shared.assert_regular_no_symlink
resolve_project_path = shared.resolve_project_path
verify_reference = shared.verify_reference


def validate_parent(receipt: Path, verification: Path) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    return shared.validate_parent(receipt, verification)


def validate_plan(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    validate_with_schema(plan, PLAN_SCHEMA)
    expected_implementation = {
        "source": SOURCE,
        "interface": INTERFACE,
        "scan_schema": SCAN_SCHEMA,
        "runner": Path(__file__).resolve(),
        "verifier": PROJECT / "tools/wiki_pda_structural_replay_ceiling_q0_v2_verify.py",
        "shared_helper": SHARED_HELPER,
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
    revision = json.loads(CANDIDATE_REVISION.read_text(encoding="utf-8"))
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
        bindings[f"schema_{key}"] = verify_reference(plan["schemas"][key], expected)

    parent_expected = {
        "policy": PARENT_POLICY,
        "receipt_schema": PARENT_RECEIPT_SCHEMA,
        "verification_schema": PARENT_VERIFICATION_SCHEMA,
        "verifier": PARENT_VERIFIER,
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
        bindings[key] = verify_reference(plan["exclusive_lane"][plan_key], expected)
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
        "python3", "tools/wiki_pda_structural_replay_ceiling_q0_v2.py",
        "--parent-qualification-receipt",
        "<schema-valid-policy-v4-q1-qualification-receipt>",
        "--parent-qualification-verification",
        "<schema-valid-independent-policy-v4-q1-verification>",
    ]
    if (
        plan["toolchain"]["ld_library_path"] != str(LD_LIBRARY_PATH)
        or plan["toolchain"]["compile_flags"] != COMPILE_FLAGS
        or plan["population"]
        != {"path": str(INPUT), "bytes": INPUT_BYTES, "sha256": INPUT_SHA256}
        or plan["resource_guard"]["limit_kib"] != TREE_LIMIT_KIB
        or plan["resource_guard"]["cgroup_memory_max_bytes"] != CGROUP_LIMIT_BYTES
        or plan["resource_guard"]["scratch_limit_bytes"] != SCRATCH_LIMIT_BYTES
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


def hash_population() -> str:
    assert_regular_no_symlink(INPUT, one_link=True)
    if INPUT.stat().st_size != INPUT_BYTES:
        raise RuntimeError("transformed population size mismatch")
    descriptor = os.open(INPUT, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    digest = hashlib.sha256()
    offset = 0
    try:
        while True:
            block = os.read(descriptor, 8 << 20)
            if not block:
                break
            digest.update(block)
            block_start = offset
            offset += len(block)
            if hasattr(os, "posix_fadvise"):
                os.posix_fadvise(
                    descriptor, block_start, len(block), os.POSIX_FADV_DONTNEED
                )
    finally:
        os.close(descriptor)
    if offset != INPUT_BYTES or digest.hexdigest() != INPUT_SHA256:
        raise RuntimeError("transformed population digest mismatch")
    return digest.hexdigest()


def scan_command(binary: Path, output: Path, guard: Path, cgroup: Path, arm: str) -> list[str]:
    return [
        "/usr/bin/python3", str(RESOURCE_GUARD),
        "--limit-kib", str(TREE_LIMIT_KIB),
        "--limit-mode", "tree",
        "--official-decimal-limit-kib", "9765625",
        "--cgroup-path", str(cgroup),
        "--cgroup-memory-max-bytes", str(CGROUP_LIMIT_BYTES),
        "--scratch-path", str(RESULT),
        "--temporary-disk-limit-bytes", str(SCRATCH_LIMIT_BYTES),
        "--max-logical-cpus", "1",
        "--guard-json", str(guard),
        "--label", f"wiki-pda-ceiling-v2-{arm}",
        "--phase", "diagnostic", "--",
        str(TASKSET), "--cpu-list", "0", str(binary), str(INPUT), str(output),
    ]


def semantic_scan_checks(scan: dict[str, Any]) -> None:
    if (
        scan["population_bytes"] != INPUT_BYTES
        or scan["required_correct_bytes"] != REQUIRED_CORRECT_BYTES
        or scan["transition_offset_zero_predictions"] != 0
        or scan["closing_before_offset_two_predictions"] != 0
        or scan["treatment_k_state_identity_pass"] is not True
        or scan["k_transition_fnv1a64"] != scan["d_transition_fnv1a64"]
        or scan["control_outcomes_feed_state"] is not False
        or scan["promotion_authorized"] is not False
        or scan["gamma_compression_credit_bytes"] != 0
        or scan["gamma_score_credit_bytes"] != 0
        or scan["table_lookups"] != scan["events_started"]
    ):
        raise RuntimeError("scanner causal constants failed")
    arms = scan["arms"]
    d_active = arms["D"]["active"]
    if any(arms[key]["active"] != d_active for key in ("R", "S", "N")):
        raise RuntimeError("matched control opportunity set failed")
    if d_active > arms["C"]["active"] + arms["T"]["active"]:
        raise RuntimeError("D union attribution exceeds source opportunities")
    for key, arm in arms.items():
        if (
            arm["correct"] > arm["active"]
            or sum(row["active"] for row in arm["thirds"]) != arm["active"]
            or sum(row["correct"] for row in arm["thirds"]) != arm["correct"]
        ):
            raise RuntimeError(f"arm partition failed: {key}")
    margins = []
    for third in range(3):
        control = max(arms[key]["thirds"][third]["correct"] for key in ("R", "S", "N"))
        margins.append(arms["D"]["thirds"][third]["correct"] - control)
        active = arms["D"]["thirds"][third]["active"]
        if any(arms[key]["thirds"][third]["active"] != active for key in ("R", "S", "N")):
            raise RuntimeError("thirdwise matched opportunity set failed")
    target = arms["D"]["correct"] >= REQUIRED_CORRECT_BYTES
    thirds = min(margins) > 0
    causal = scan["causal_and_verification_pass"] is True
    if (
        scan["minimum_third_treatment_minus_max_control_correct_bytes"] != min(margins)
        or scan["target_scale_correct_ceiling_pass"] is not target
        or scan["all_thirds_beat_controls_pass"] is not thirds
        or scan["absolute_ceiling_pass"] is not (target and thirds and causal)
    ):
        raise RuntimeError("scanner derived predicates failed")


def validate_guard(guard: dict[str, Any]) -> None:
    validate_with_schema(guard, RESOURCE_GUARD_SCHEMA)
    if (
        guard["schema"] != "gamma.enwiki9.resource-guard-receipt.v3"
        or guard["status"] != "complete"
        or guard["returncode"] != 0
        or any(guard["guards"].values())
        or not all(guard["measurements"].values())
        or guard["peaks"]["max_sampled_tree_rss_kib"] > TREE_LIMIT_KIB
        or guard["peaks"]["max_observed_process_vmhwm_kib"] > TREE_LIMIT_KIB
        or guard["peaks"]["cgroup_memory_peak_bytes"] > CGROUP_LIMIT_BYTES
        or guard["peaks"]["max_sampled_scratch_logical_bytes"] > SCRATCH_LIMIT_BYTES
        or guard["cgroup_events"]["delta"]["max"] != 0
        or guard["cgroup_events"]["delta"]["oom"] != 0
        or guard["cgroup_events"]["delta"]["oom_kill"] != 0
    ):
        raise RuntimeError("scanner resource guard did not pass")


def resource_summary(guards: dict[str, dict[str, Any]], scans: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = list(guards.values())
    result = {
        "schema": "gamma.enwiki9.wiki-pda-ceiling-resource-summary.v1",
        "candidate_id": CANDIDATE_ID,
        "arms": {arm: scans[arm]["guard"] for arm in ("a", "b")},
        "maximum_tree_rss_kib": max(g["peaks"]["max_sampled_tree_rss_kib"] for g in values),
        "maximum_process_vmhwm_kib": max(g["peaks"]["max_observed_process_vmhwm_kib"] for g in values),
        "maximum_cgroup_memory_bytes": max(g["peaks"]["cgroup_memory_peak_bytes"] for g in values),
        "maximum_sampled_cgroup_file_bytes": max(scans[a]["sampled_cgroup_file_peak_bytes"] for a in ("a", "b")),
        "maximum_scratch_logical_bytes": max(g["peaks"]["max_sampled_scratch_logical_bytes"] for g in values),
        "maximum_scratch_allocated_bytes": max(g["peaks"]["max_sampled_scratch_allocated_bytes"] for g in values),
        "cgroup_max_events": sum(g["cgroup_events"]["delta"]["max"] for g in values),
        "cgroup_oom_events": sum(g["cgroup_events"]["delta"]["oom"] for g in values),
        "cgroup_oom_kill_events": sum(g["cgroup_events"]["delta"]["oom_kill"] for g in values),
        "all_resource_predicates_pass": False,
    }
    result["all_resource_predicates_pass"] = (
        result["maximum_tree_rss_kib"] <= TREE_LIMIT_KIB
        and result["maximum_process_vmhwm_kib"] <= TREE_LIMIT_KIB
        and result["maximum_cgroup_memory_bytes"] <= CGROUP_LIMIT_BYTES
        and result["maximum_scratch_logical_bytes"] <= SCRATCH_LIMIT_BYTES
        and result["cgroup_max_events"] == 0
        and result["cgroup_oom_events"] == 0
        and result["cgroup_oom_kill_events"] == 0
    )
    validate_with_schema(result, RESOURCE_SCHEMA)
    return result


def derive_measurements(scan: dict[str, Any], resources: dict[str, Any], repeat: bool) -> dict[str, Any]:
    arms = scan["arms"]
    return {
        "scanned_bytes": scan["population_bytes"],
        "treatment_active_bytes": arms["D"]["active"],
        "treatment_correct_bytes": arms["D"]["correct"],
        "random_correct_bytes": arms["R"]["correct"],
        "shifted_correct_bytes": arms["S"]["correct"],
        "negated_correct_bytes": arms["N"]["correct"],
        "transition_offset_zero_predictions": scan["transition_offset_zero_predictions"],
        "closing_before_offset_two_predictions": scan["closing_before_offset_two_predictions"],
        "minimum_third_treatment_minus_max_control_correct_bytes": scan["minimum_third_treatment_minus_max_control_correct_bytes"],
        "opportunity_fnv1a64": scan["opportunity_fnv1a64"],
        "repeat_identity_pass": repeat,
        "maximum_tree_rss_kib": resources["maximum_tree_rss_kib"],
        "maximum_cgroup_memory_bytes": resources["maximum_cgroup_memory_bytes"],
        "maximum_sampled_cgroup_file_bytes": resources["maximum_sampled_cgroup_file_bytes"],
    }


def derive_gates(scan: dict[str, Any], measurements: dict[str, Any], resources: dict[str, Any], repeat: bool) -> dict[str, bool]:
    gates = {
        "full_population_pass": measurements["scanned_bytes"] == INPUT_BYTES,
        "target_scale_correct_ceiling_pass": measurements["treatment_correct_bytes"] >= REQUIRED_CORRECT_BYTES,
        "no_seen_opener_credit_pass": measurements["transition_offset_zero_predictions"] == 0,
        "no_early_closing_credit_pass": measurements["closing_before_offset_two_predictions"] == 0,
        "all_thirds_beat_controls_pass": measurements["minimum_third_treatment_minus_max_control_correct_bytes"] > 0,
        "repeat_identity_pass": repeat,
        "causal_verification_pass": scan["causal_and_verification_pass"] is True,
        "resource_pass": resources["all_resource_predicates_pass"] is True,
        "all_promotion_predicates_pass": False,
    }
    gates["all_promotion_predicates_pass"] = all(v for k, v in gates.items() if k != "all_promotion_predicates_pass")
    return gates


def empty_scan() -> dict[str, Any]:
    return {"command": None, "receipt": None, "guard": None, "sampled_cgroup_file_peak_bytes": None, "sampled_cgroup_current_peak_bytes": None}


def empty_gates() -> dict[str, None]:
    return {key: None for key in (
        "full_population_pass", "target_scale_correct_ceiling_pass",
        "no_seen_opener_credit_pass", "no_early_closing_credit_pass",
        "all_thirds_beat_controls_pass", "repeat_identity_pass",
        "causal_verification_pass", "resource_pass",
        "all_promotion_predicates_pass",
    )}


def result_manifest(complete: bool) -> dict[str, Any]:
    roles = [
        ("lease_evidence", "lease-evidence.json"),
        ("lease_transitions", "lease-transitions.json"),
        ("parent_reverification", "parent-reverification.json"),
        ("compile_stdout", "compile.stdout"), ("compile_stderr", "compile.stderr"),
        ("scanner_binary", "wiki-pda-ceiling-scan"),
        ("scan_a_receipt", "scan-a.json"), ("scan_a_guard", "guard-a.json"),
        ("scan_a_stdout", "scan-a.stdout"), ("scan_a_stderr", "scan-a.stderr"),
        ("scan_b_receipt", "scan-b.json"), ("scan_b_guard", "guard-b.json"),
        ("scan_b_stdout", "scan-b.stdout"), ("scan_b_stderr", "scan-b.stderr"),
        ("resource_summary", "resource-guard.json"), ("decision", "decision.json"),
    ]
    artifacts = []
    for role, relative in roles:
        path = RESULT / relative
        if path.is_file():
            record = artifact(path)
            record.update({"role": role, "path": relative})
            artifacts.append(record)
    observed = sorted(path.name for path in RESULT.iterdir())
    expected = {relative for _, relative in roles}
    exact = set(observed) == expected and all(path.is_file() and not path.is_symlink() for path in RESULT.iterdir())
    manifest = {
        "schema": "gamma.enwiki9.wiki-pda-ceiling-output-manifest.v1",
        "candidate_id": CANDIDATE_ID,
        "result_root": f"results/{CANDIDATE_ID}",
        "pre_manifest_exact_file_set_pass": exact,
        "unexpected_pre_manifest_entries": sorted(set(observed) - expected),
        "complete_result_artifacts_pass": complete and exact and len(artifacts) == len(roles),
        "artifacts": artifacts,
    }
    validate_with_schema(manifest, MANIFEST_SCHEMA)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-qualification-receipt", required=True, type=Path)
    parser.add_argument("--parent-qualification-verification", required=True, type=Path)
    args = parser.parse_args()
    receipt_path = args.parent_qualification_receipt if args.parent_qualification_receipt.is_absolute() else PROJECT / args.parent_qualification_receipt
    verification_path = args.parent_qualification_verification if args.parent_qualification_verification.is_absolute() else PROJECT / args.parent_qualification_verification

    if RESULT.exists() or RESULT.is_symlink():
        raise FileExistsError(f"refusing to overwrite result root: {RESULT}")
    for path in (CGROUP_A, CGROUP_B, LEASE, LEASE_LOCK):
        if path.exists() or path.is_symlink():
            raise RuntimeError(f"exclusive execution namespace occupied: {path}")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    bindings = validate_plan(plan)
    parent_receipt, parent_verification, parent_reverification = validate_parent(receipt_path, verification_path)
    preflight_hashes = {path: sha256(path) for path in (
        PLAN, SOURCE, INTERFACE, SCAN_SCHEMA, EXPERIMENT, PROPOSAL,
        CANDIDATE_REVISION, SHARED_HELPER, PARENT_POLICY, receipt_path,
        verification_path,
    )}

    RESULT.mkdir(mode=0o700, parents=True)
    invocation = {"argv": [str(Path(__file__).resolve()), *sys.argv[1:]], "cwd": str(PROJECT), "environment": BASE_ENVIRONMENT}
    from managed_exclusive_lease import ManagedExclusiveLease

    try:
        lease = ManagedExclusiveLease.acquire(
            lease_path=LEASE,
            transition_path=RESULT / "lease-transitions.json",
            candidate_id=CANDIDATE_ID,
            command_sha256=canonical_sha256(invocation),
            runner_sha256=bindings["runner"]["sha256"],
            guard_path=str(RESULT), result_path=str(RESULT), scratch_path=str(RESULT),
            claim_boundary="Managed exclusive lane for two zero-credit WIKI-PDA scans; no signal authority.",
        )
    except Exception:
        RESULT.rmdir()
        raise

    write_bytes_exclusive(RESULT / "parent-reverification.json", parent_reverification)
    decision: dict[str, Any] = {
        "schema": "gamma.enwiki9.wiki-pda-ceiling-decision.v1",
        "candidate_id": CANDIDATE_ID,
        "operational_status": "terminal_infrastructure_failure",
        "claim_boundary": CLAIM_BOUNDARY,
        "claim_authority": "causal_shadow_opportunity_screen_only",
        "bindings": bindings,
        "parent_qualification": {
            "receipt": parent_receipt, "verification": parent_verification,
            "independent_reverification": artifact(RESULT / "parent-reverification.json"),
            "policy_v4": artifact(PARENT_POLICY), "fully_positive": True,
        },
        "population": {"path": str(INPUT), "bytes": INPUT_BYTES, "sha256": INPUT_SHA256, "verified": False},
        "exclusive_lease": {"lease_id": lease.record["lease_id"], "release_pass": False, "evidence": None, "transitions": None},
        "compile": None, "scans": {"a": empty_scan(), "b": empty_scan()},
        "resource_summary": None, "measurements": None, "gates": empty_gates(),
        "scientific_verdict": "none_infrastructure_failure",
        "promotion_authorized": False,
        "next_authority": "one_correction_only_runner_successor",
        "archive_authority": False, "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0, "error": None,
    }
    try:
        decision["population"]["verified"] = hash_population() == INPUT_SHA256
        lease.heartbeat()
        binary = RESULT / "wiki-pda-ceiling-scan"
        compile_record, _, _ = shared.run_command(
            step_id="compile",
            argv=[str(COMPILER), *COMPILE_FLAGS, str(SOURCE), "-o", str(binary)],
            environment=COMPILE_ENVIRONMENT,
            stdout_path=RESULT / "compile.stdout", stderr_path=RESULT / "compile.stderr",
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
                lease=lease, cgroup_path=cgroup,
            )
            if command["returncode"] != 0 or not receipt.is_file() or not guard_path.is_file():
                raise RuntimeError(f"scanner arm {arm} failed")
            scan = json.loads(receipt.read_text(encoding="utf-8"))
            guard = json.loads(guard_path.read_text(encoding="utf-8"))
            validate_with_schema(scan, SCAN_SCHEMA)
            semantic_scan_checks(scan)
            validate_guard(guard)
            if cgroup.exists():
                raise RuntimeError(f"scanner cgroup {arm} was not cleaned")
            scans[arm] = {
                "command": command, "receipt": artifact(receipt), "guard": artifact(guard_path),
                "sampled_cgroup_file_peak_bytes": file_peak,
                "sampled_cgroup_current_peak_bytes": current_peak,
            }
            guards[arm] = guard
            decision["scans"][arm] = scans[arm]
            lease.heartbeat()

        scan_a_path = RESULT / "scan-a.json"
        scan_b_path = RESULT / "scan-b.json"
        scan_a = json.loads(scan_a_path.read_text(encoding="utf-8"))
        scan_b = json.loads(scan_b_path.read_text(encoding="utf-8"))
        repeat = scan_a_path.read_bytes() == scan_b_path.read_bytes() and scan_a == scan_b
        resources = resource_summary(guards, scans)
        write_json_exclusive(RESULT / "resource-guard.json", resources)
        decision["resource_summary"] = artifact(RESULT / "resource-guard.json")
        measurements = derive_measurements(scan_a, resources, repeat)
        gates = derive_gates(scan_a, measurements, resources, repeat)
        decision["measurements"] = measurements
        decision["gates"] = gates
        for path, digest in preflight_hashes.items():
            if sha256(path) != digest:
                raise RuntimeError(f"source or antecedent drifted during execution: {path}")
        passed = gates["all_promotion_predicates_pass"]
        decision.update({
            "operational_status": "terminal",
            "scientific_verdict": (
                "authorize_retained_parent_donor_surprise_trace_zero_credit"
                if passed else "retire_exact_wiki_pda_information_source"
            ),
            "promotion_authorized": passed,
            "next_authority": (
                "retained_parent_donor_surprise_trace_only"
                if passed else "one_materially_different_information_source"
            ),
        })
    except Exception as error:
        decision["error"] = f"{type(error).__name__}: {error}"
    finally:
        try:
            lease.heartbeat()
            lease.release(evidence_path=RESULT / "lease-evidence.json")
            decision["exclusive_lease"] = {
                "lease_id": lease.record["lease_id"], "release_pass": True,
                "evidence": artifact(RESULT / "lease-evidence.json"),
                "transitions": artifact(RESULT / "lease-transitions.json"),
            }
        except Exception as lease_error:
            message = f"lease release failure: {type(lease_error).__name__}: {lease_error}"
            decision["error"] = message if decision["error"] is None else f"{decision['error']}; {message}"
            decision.update({
                "operational_status": "terminal_infrastructure_failure",
                "scientific_verdict": "none_infrastructure_failure",
                "promotion_authorized": False,
                "next_authority": "one_correction_only_runner_successor",
            })

    validate_with_schema(decision, DECISION_SCHEMA)
    write_json_exclusive(RESULT / "decision.json", decision)
    write_json_exclusive(
        RESULT / "output-manifest.json",
        result_manifest(decision["operational_status"] == "terminal"),
    )
    return 0 if decision["operational_status"] == "terminal" else 1


if __name__ == "__main__":
    raise SystemExit(main())
