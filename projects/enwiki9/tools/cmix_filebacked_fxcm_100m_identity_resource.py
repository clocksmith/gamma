#!/usr/bin/env python3
"""Coordinate the sealed q1 opening-100M identity and resource gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from typing import Any

import jsonschema

import cmix_filebacked_fxcm_100m_identity_resource_verify as proof
import cmix_filebacked_fxcm_scope_identity as scope
import research_contracts


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-100m-identity-resource.v1"
PLAN_ID = "cmix_filebacked_fxcm_100m_identity_resource_q0_v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
PARENT_ID = "cmix_obias_source_full1g_roundtrip_a_qm0_v1"
PREFIX_BYTES = 100_000_000
PREFIX_SHA256 = "2b49720ec4d78c3c9fabaee6e4179a5e997302b3a70029f30f2d582218c024a8"
MEMORY_LIMIT_KIB = 9_765_625
MEMORY_MAX_BYTES = 10_000_000_000
ENGINEERING_LIMIT_KIB = 9_000_000
MEMORY_HIGH_BYTES = 9_000_000_000
DISK_LIMIT_BYTES = 100_000_000_000
PHASES = proof.PHASES
PLAN_SCHEMA = (
    proof.PROJECT
    / "operations/planning/"
    "cmix-filebacked-fxcm-100m-identity-resource-plan.schema.json"
)
PLAN_SCHEMA_SHA256 = "eb8970b91fbf809c93f8a876c316883bb39d03aac1b96d6b0f1a1dcec0e656bc"


def artifact(path: Path) -> dict[str, Any]:
    return scope.artifact(path)


def command_sha256(argv: list[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(value) for value in argv)).hexdigest()


def run_logged(
    command: list[str], stdout: Any, stderr: Any, environment: dict[str, str] | None = None
) -> int:
    process = subprocess.Popen(
        command,
        env=environment,
        stdout=stdout,
        stderr=stderr,
        start_new_session=True,
    )
    try:
        return process.wait()
    except BaseException:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
        raise


def load_contract(path: Path, expected_schema: str, label: str) -> tuple[Path, dict[str, Any]]:
    resolved, value = scope.load_json(path, label)
    research_contracts.validate_artifact(resolved)
    if value.get("schema") != expected_schema:
        raise RuntimeError(f"{label} schema mismatch")
    return resolved, value


def copy_prefix(corpus: Path, destination: Path) -> None:
    observed = scope.copy_slice(corpus, destination, 0, PREFIX_BYTES)
    if observed != PREFIX_SHA256:
        raise RuntimeError("retained opening-100M prefix identity mismatch")


def observer_packages(build: dict[str, Any]) -> tuple[dict[str, Path], Path]:
    if (
        build.get("candidate_id") != CANDIDATE_ID
        or build.get("decisions", {}).get("observer_build_pass") is not True
        or build.get("state_mutation_control", {}).get("pass") is not True
    ):
        raise RuntimeError("observer build receipt did not pass")
    packages: dict[str, Path] = {}
    for value in build.get("packages", []):
        role = value.get("arm") if isinstance(value, dict) else None
        if role not in {"parent", "candidate", "negative"} or role in packages:
            raise RuntimeError("observer package set is invalid")
        packages[role] = scope.verify_artifact_record(
            value.get("packaged_binary"), f"observer {role} package"
        )
    if set(packages) != {"parent", "candidate", "negative"}:
        raise RuntimeError("observer package set is incomplete")
    return packages, scope.verify_artifact_record(build.get("head_blob"), "observer head")


def q1_release_inputs(
    *,
    build_a_path: Path,
    build_a: dict[str, Any],
    build_b_path: Path,
    build_b: dict[str, Any],
    build_verification: dict[str, Any],
    raw_a: Path,
    raw_b: Path,
    scope_build: dict[str, Any],
) -> dict[str, Path]:
    for arm, path, build, raw in (
        ("a", build_a_path, build_a, raw_a),
        ("b", build_b_path, build_b, raw_b),
    ):
        expected_receipt = build_verification.get(f"build_{arm}_receipt_sha256")
        expected_binary = build_verification.get(f"build_{arm}_binary_sha256")
        if (
            build.get("candidate_id") != CANDIDATE_ID
            or build.get("build_role") != "release"
            or build.get("build_succeeded") is not True
            or build.get("clean_build_root_pass") is not True
            or scope.sha256_file(path) != expected_receipt
            or scope.sha256_file(raw) != expected_binary
            or build.get("binary_sha256") != expected_binary
        ):
            raise RuntimeError(f"q1 release build {arm.upper()} binding failed")
    if (
        build_verification.get("candidate_id") != CANDIDATE_ID
        or build_verification.get("build_role") != "release"
        or build_verification.get("independent_build_pass") is not True
        or scope.sha256_file(raw_a) != scope.sha256_file(raw_b)
    ):
        raise RuntimeError("independent q1 release-build identity failed")
    packages = scope_build.get("packages")
    candidate = next(
        (
            value
            for value in packages or []
            if isinstance(value, dict) and value.get("arm") == "candidate"
        ),
        None,
    )
    if candidate is None or scope_build.get("package_asset_identity_pass") is not True:
        raise RuntimeError("q1 scope-build package assets are unavailable")
    return {
        "raw_binary": raw_a,
        "dictionary_payload": scope.verify_artifact_record(
            candidate.get("dictionary_payload"), "release dictionary"
        ),
        "article_order_payload": scope.verify_artifact_record(
            candidate.get("article_order_payload"), "release article order"
        ),
        "package_header": scope.verify_artifact_record(
            candidate.get("header"), "release package header"
        ),
        "head_blob": scope.verify_artifact_record(scope_build.get("head_blob"), "release head"),
    }


def run_identity_arm(
    *,
    arm: str,
    population: Path,
    package: Path,
    head_blob: Path,
    identity_runner: Path,
    identity_schema: Path,
    resource_guard: Path,
    lease: Path,
    result_root: Path,
    scratch_root: Path,
    cpu: int,
) -> tuple[dict[str, Any], str]:
    command = [
        sys.executable,
        str(identity_runner),
        "--arm",
        arm,
        "--population",
        str(population),
        "--package",
        str(package),
        "--head-blob",
        str(head_blob),
        "--resource-guard",
        str(resource_guard),
        "--exclusive-lease",
        str(lease),
        "--receipt-schema",
        str(identity_schema),
        "--result-root",
        str(result_root),
        "--scratch-root",
        str(scratch_root),
        "--cpu",
        str(cpu),
    ]
    log_root = result_root.parent / f"{arm}-invocation"
    log_root.mkdir(mode=0o700)
    with (log_root / "stdout").open("xb") as stdout, (log_root / "stderr").open("xb") as stderr:
        return_code = run_logged(command, stdout, stderr)
    receipt_path, receipt = load_contract(
        result_root / "identity-arm-receipt.json",
        "gamma.enwiki9.cmix-filebacked-fxcm-100m-identity-arm.v1",
        f"{arm} identity receipt",
    )
    expected_command = command_sha256(command)
    if (
        return_code != 0
        or receipt.get("arm") != arm
        or receipt.get("arm_pass") is not True
        or receipt.get("command_sha256") != expected_command
        or receipt.get("errors") != []
    ):
        raise RuntimeError(f"{arm} identity arm failed")
    receipt["_receipt_path"] = receipt_path
    return receipt, expected_command


def remove_empty_cgroup(path: Path) -> bool:
    try:
        if (path / "cgroup.procs").read_text(encoding="ascii").split():
            return False
        path.rmdir()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return not path.exists()


def run_release_arm(
    *,
    population: Path,
    release_inputs: dict[str, Path],
    soft_guard: Path,
    stage_runner: Path,
    stage_schema: Path,
    result_root: Path,
    work_root: Path,
    global_result_root: Path,
    global_scratch_root: Path,
    cgroup_path: Path,
    cpu: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    result_root.mkdir(mode=0o700)
    work_root.mkdir(mode=0o700)
    marker = result_root / "phase-markers.jsonl"
    marker.touch(mode=0o600, exist_ok=False)
    guard_path = result_root / "guard.json"
    stage_receipt = result_root / "release-stage-receipt.json"
    stage_command = [
        sys.executable,
        str(stage_runner),
        "--population",
        str(population),
        "--raw-binary",
        str(release_inputs["raw_binary"]),
        "--dictionary-payload",
        str(release_inputs["dictionary_payload"]),
        "--article-order-payload",
        str(release_inputs["article_order_payload"]),
        "--package-header",
        str(release_inputs["package_header"]),
        "--head-blob",
        str(release_inputs["head_blob"]),
        "--work-root",
        str(work_root),
        "--result-root",
        str(result_root),
        "--receipt-schema",
        str(stage_schema),
        "--receipt",
        str(stage_receipt),
    ]
    cgroup_path.mkdir(mode=0o700)
    guard_command = [
        "/usr/bin/taskset",
        "--cpu-list",
        str(cpu),
        sys.executable,
        str(soft_guard),
        "--limit-kib",
        str(MEMORY_LIMIT_KIB),
        "--limit-mode",
        "tree",
        "--official-decimal-limit-kib",
        str(MEMORY_LIMIT_KIB),
        "--cgroup-path",
        str(cgroup_path),
        "--cgroup-memory-max-bytes",
        str(MEMORY_MAX_BYTES),
        "--scratch-path",
        str(global_scratch_root),
        "--scratch-path",
        str(global_result_root),
        "--temporary-disk-limit-bytes",
        str(DISK_LIMIT_BYTES),
        "--phase-marker-path",
        str(marker),
        "--max-logical-cpus",
        "1",
        "--guard-json",
        str(guard_path),
        "--label",
        "q1-opening-100m-release",
        "--phase",
        "diagnostic",
        "--",
        *stage_command,
    ]
    environment = {
        "GAMMA_PHASE_CGROUP_PATH": str(cgroup_path),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "TZ": "UTC",
    }
    try:
        with (result_root / "guard.stdout").open("xb") as stdout, (
            result_root / "guard.stderr"
        ).open("xb") as stderr:
            return_code = run_logged(
                guard_command,
                stdout,
                stderr,
                environment,
            )
    finally:
        cgroup_cleanup = remove_empty_cgroup(cgroup_path)
    if not cgroup_cleanup:
        raise RuntimeError("release cgroup cleanup failed")
    guard_path, guard = load_contract(
        guard_path, "gamma.enwiki9.resource-guard-receipt.v3", "release guard"
    )
    stage_path, stage = load_contract(
        stage_receipt,
        "gamma.enwiki9.cmix-filebacked-fxcm-100m-release-stage.v1",
        "release stage",
    )
    soft_path, soft = load_contract(
        result_root / "soft-high-receipt.json",
        "gamma.enwiki9.resource-guard-soft-high.v1",
        "release memory.high receipt",
    )
    expected_stage_command = command_sha256(stage_command)
    if (
        return_code != 0
        or stage.get("stage_pass") is not True
        or stage.get("command_sha256") != expected_stage_command
        or guard.get("status") != "complete"
        or guard.get("returncode") != 0
        or any(guard.get("guards", {}).values())
        or soft.get("wrapper_pass") is not True
        or soft.get("requested_memory_high_bytes") != MEMORY_HIGH_BYTES
    ):
        raise RuntimeError("release arm stage, guard, or memory.high wrapper failed")
    if next(work_root.iterdir(), None) is not None:
        raise RuntimeError("release work root retained scratch content")
    work_root.rmdir()
    stage["_receipt_path"] = stage_path
    guard["_receipt_path"] = guard_path
    soft["_receipt_path"] = soft_path
    return stage, guard, soft, expected_stage_command


def identity_arm_summary(receipt: dict[str, Any], command_digest: str) -> dict[str, Any]:
    return {
        "arm": receipt["arm"],
        "instrumented": True,
        "resource_authority": False,
        "binary": receipt["package"],
        "command_sha256": command_digest,
        "return_codes": receipt["return_codes"],
        "post_head_probability_sha256": receipt["probability_sha256"],
        "coder_checkpoint_manifest": receipt["coder_checkpoints"],
        "persistent_state_manifest": receipt["persistent_state"],
        "arithmetic_payload": receipt["arithmetic_payload"],
        "self_extracting_archive": receipt["self_extracting_archive"],
        "decoded_transformed": receipt["decoded_transformed"],
        "raw_inverse": receipt["raw_inverse"],
        "raw_inverse_pass": receipt["raw_inverse_pass"],
        "execution_receipt": artifact(receipt["_receipt_path"]),
        "backing_cleanup_pass": receipt["backing_cleanup_pass"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--observer-build", type=Path, required=True)
    parser.add_argument("--observer-build-schema", type=Path, required=True)
    parser.add_argument("--observer-calibration", type=Path, required=True)
    parser.add_argument("--observer-calibration-verification", type=Path, required=True)
    parser.add_argument("--source-closure", type=Path, required=True)
    parser.add_argument("--program-lock-verification", type=Path, required=True)
    parser.add_argument("--q1-release-build-a", type=Path, required=True)
    parser.add_argument("--q1-release-build-b", type=Path, required=True)
    parser.add_argument("--q1-release-binary-a", type=Path, required=True)
    parser.add_argument("--q1-release-binary-b", type=Path, required=True)
    parser.add_argument("--build-verification", type=Path, required=True)
    parser.add_argument("--scope-build-receipt", type=Path, required=True)
    parser.add_argument("--opening-distant-10m", type=Path, required=True)
    parser.add_argument("--opening-distant-10m-verification", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--identity-arm-runner", type=Path, required=True)
    parser.add_argument("--identity-arm-schema", type=Path, required=True)
    parser.add_argument("--identity-resource-schema", type=Path, required=True)
    parser.add_argument("--identity-resource-guard", type=Path, required=True)
    parser.add_argument("--release-soft-guard", type=Path, required=True)
    parser.add_argument("--release-stage-runner", type=Path, required=True)
    parser.add_argument("--release-stage-schema", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--cgroup-path", type=Path, required=True)
    parser.add_argument("--cpu", type=int)
    args = parser.parse_args()

    proof.require_released_lease(args.exclusive_lease)
    plan_path, plan = scope.load_json(args.plan, "100M planning contract")
    if scope.sha256_file(PLAN_SCHEMA) != PLAN_SCHEMA_SHA256:
        raise RuntimeError("100M planning schema hash drift")
    plan_schema = json.loads(PLAN_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(plan_schema)
    jsonschema.validate(plan, plan_schema)
    if (
        plan.get("artifact_id") != PLAN_ID
        or plan.get("candidate_id") != CANDIDATE_ID
        or plan.get("planning_schema_sha256") != PLAN_SCHEMA_SHA256
    ):
        raise RuntimeError("100M planning contract identity mismatch")
    observer_build_path, observer_build = load_contract(
        args.observer_build,
        "gamma.enwiki9.cmix-filebacked-fxcm-100m-observer-build.v1",
        "observer build",
    )
    observer_build_schema_path, observer_build_schema = scope.load_json(
        args.observer_build_schema, "observer build schema"
    )
    jsonschema.Draft202012Validator.check_schema(observer_build_schema)
    jsonschema.validate(observer_build, observer_build_schema)
    calibration_path, calibration = load_contract(
        args.observer_calibration,
        "gamma.enwiki9.cmix-filebacked-fxcm-100m-observer-calibration.v1",
        "observer calibration",
    )
    calibration_verification_path, calibration_verification = load_contract(
        args.observer_calibration_verification,
        "gamma.enwiki9.cmix-filebacked-fxcm-100m-observer-calibration-verification.v1",
        "observer calibration verification",
    )
    source_closure_path, _ = load_contract(
        args.source_closure,
        "gamma.enwiki9.cmix-filebacked-fxcm-source-closure.v1",
        "q1 source closure",
    )
    lock_path, lock = load_contract(
        args.program_lock_verification,
        "gamma.enwiki9.cmix-filebacked-fxcm-program-lock-verification.v1",
        "q1 program lock verification",
    )
    build_a_path, build_a = load_contract(
        args.q1_release_build_a,
        "gamma.enwiki9.cmix-filebacked-fxcm-build-receipt.v1",
        "q1 release build A",
    )
    build_b_path, build_b = load_contract(
        args.q1_release_build_b,
        "gamma.enwiki9.cmix-filebacked-fxcm-build-receipt.v1",
        "q1 release build B",
    )
    build_verification_path, build_verification = load_contract(
        args.build_verification,
        "gamma.enwiki9.cmix-filebacked-fxcm-build-verification.v1",
        "q1 release build verification",
    )
    scope_build_path, scope_build = load_contract(
        args.scope_build_receipt,
        "gamma.enwiki9.cmix-filebacked-fxcm-scope-build.v1",
        "q1 scope build",
    )
    transfer_path, transfer = load_contract(
        args.opening_distant_10m,
        "gamma.enwiki9.cmix-filebacked-fxcm-transfer-10m.v1",
        "opening/distant 10M receipt",
    )
    transfer_verification_path, transfer_verification = load_contract(
        args.opening_distant_10m_verification,
        "gamma.enwiki9.cmix-filebacked-fxcm-identity-verification.v1",
        "opening/distant 10M verification",
    )
    frozen = plan.get("frozen_parent_and_candidate", {})
    frozen_paths = {
        "q1_source_closure": source_closure_path,
        "q1_program_lock": lock_path,
        "q1_release_build_a": build_a_path,
        "q1_release_build_b": build_b_path,
        "build_verification": build_verification_path,
        "q1_scope_build": scope_build_path,
        "opening_distant_10m_receipt": transfer_path,
        "opening_distant_10m_verification": transfer_verification_path,
    }
    if any(
        frozen.get(name) != str(path.relative_to(proof.PROJECT))
        for name, path in frozen_paths.items()
    ):
        raise RuntimeError("frozen q1 antecedent path binding failed")
    calibration_contract = plan.get("observer_calibration", {})
    if (
        calibration.get("terminal_pass") is not True
        or calibration_verification.get("passed") is not True
        or calibration_verification.get("receipt_sha256") != scope.sha256_file(calibration_path)
        or calibration_verification.get("verifier", {}).get("path")
        != str(proof.PROJECT / calibration_contract.get("independent_verifier", ""))
        or calibration_verification.get("verifier", {}).get("sha256")
        != calibration_contract.get("independent_verifier_sha256")
        or calibration_verification.get("input_schema", {}).get("sha256")
        != calibration_contract.get("receipt_schema_sha256")
        or calibration_verification.get("output_schema", {}).get("sha256")
        != calibration_contract.get("verification_schema_sha256")
        or calibration_verification.get("planning_contract")
        != calibration.get("antecedents", {}).get("planning_contract")
        or calibration.get("antecedents", {}).get("planning_contract", {}).get("sha256")
        != scope.sha256_file(plan_path)
        or calibration.get("antecedents", {}).get("observer_build", {}).get("sha256")
        != scope.sha256_file(observer_build_path)
        or lock.get("verified") is not True
        or transfer.get("terminal_pass") is not True
        or transfer_verification.get("verification_pass") is not True
        or transfer_verification.get("source_receipt", {}).get("sha256")
        != scope.sha256_file(transfer_path)
    ):
        raise RuntimeError("100M antecedent verification failed")

    corpus = scope.existing_regular(args.corpus, "canonical enwik9 corpus")
    identity_runner = scope.existing_regular(args.identity_arm_runner, "identity arm runner")
    identity_schema_path, identity_schema = scope.load_json(
        args.identity_arm_schema, "identity arm schema"
    )
    del identity_schema
    receipt_schema_path, receipt_schema = scope.load_json(
        args.identity_resource_schema, "identity/resource schema"
    )
    identity_guard = scope.existing_regular(args.identity_resource_guard, "identity guard v2")
    identity_guard_schema_path, identity_guard_schema = scope.load_json(
        proof.PROJECT / "contracts/research/v1/resource-guard-receipt.schema.json",
        "identity guard v2 schema",
    )
    jsonschema.Draft202012Validator.check_schema(identity_guard_schema)
    soft_guard = scope.existing_regular(args.release_soft_guard, "release soft-high guard")
    release_guard = scope.existing_regular(
        soft_guard.with_name("run_with_resource_guard_v3.py"), "release resource guard v3"
    )
    stage_runner = scope.existing_regular(args.release_stage_runner, "release stage runner")
    stage_schema_path, stage_schema = scope.load_json(
        args.release_stage_schema, "release stage schema"
    )
    del stage_schema
    runner_path = Path(__file__).resolve(strict=True)
    coordinator = plan.get("coordinator", {})
    if (
        coordinator.get("runner") != str(runner_path.relative_to(proof.PROJECT))
        or coordinator.get("runner_sha256") != scope.sha256_file(runner_path)
        or coordinator.get("identity_arm_runner")
        != str(identity_runner.relative_to(proof.PROJECT))
        or coordinator.get("identity_arm_runner_sha256") != scope.sha256_file(identity_runner)
        or coordinator.get("identity_arm_schema")
        != str(identity_schema_path.relative_to(proof.PROJECT))
        or coordinator.get("identity_arm_schema_sha256") != scope.sha256_file(identity_schema_path)
        or coordinator.get("release_stage_runner")
        != str(stage_runner.relative_to(proof.PROJECT))
        or coordinator.get("release_stage_runner_sha256") != scope.sha256_file(stage_runner)
        or coordinator.get("release_stage_schema")
        != str(stage_schema_path.relative_to(proof.PROJECT))
        or coordinator.get("release_stage_schema_sha256") != scope.sha256_file(stage_schema_path)
        or coordinator.get("identity_resource_guard")
        != str(identity_guard.relative_to(proof.PROJECT))
        or coordinator.get("identity_resource_guard_sha256") != scope.sha256_file(identity_guard)
        or coordinator.get("identity_resource_guard_schema")
        != str(identity_guard_schema_path.relative_to(proof.PROJECT))
        or coordinator.get("identity_resource_guard_schema_sha256")
        != scope.sha256_file(identity_guard_schema_path)
        or coordinator.get("release_soft_high_guard")
        != str(soft_guard.relative_to(proof.PROJECT))
        or coordinator.get("release_soft_high_guard_sha256") != scope.sha256_file(soft_guard)
        or coordinator.get("release_resource_guard")
        != str(release_guard.relative_to(proof.PROJECT))
        or coordinator.get("release_resource_guard_sha256") != scope.sha256_file(release_guard)
        or plan.get("receipt_schema", {}).get("sha256") != scope.sha256_file(receipt_schema_path)
    ):
        raise RuntimeError("planning contract coordinator binding mismatch")

    if corpus.stat().st_size < PREFIX_BYTES or proof.digest_prefix(corpus, PREFIX_BYTES) != PREFIX_SHA256:
        raise RuntimeError("canonical opening-100M population identity mismatch")
    result_root, _ = scope.absent_root(args.result_root, "100M result root")
    scratch_root, _ = scope.absent_root(args.scratch_root, "100M scratch root")
    if result_root == scratch_root or result_root in scratch_root.parents or scratch_root in result_root.parents:
        raise RuntimeError("100M result and scratch roots must be disjoint")
    cgroup_path = args.cgroup_path
    if not cgroup_path.is_absolute() or cgroup_path.exists() or cgroup_path.is_symlink():
        raise RuntimeError("100M cgroup path must be absent and absolute")
    cgroup_parent = scope.existing_directory(cgroup_path.parent, "100M cgroup parent")
    cgroup_path = cgroup_parent / cgroup_path.name
    cpu = min(os.sched_getaffinity(0)) if args.cpu is None else args.cpu
    if cpu not in os.sched_getaffinity(0):
        raise RuntimeError("selected 100M CPU is outside coordinator affinity")

    observer_package, observer_head = observer_packages(observer_build)
    raw_a = scope.existing_regular(args.q1_release_binary_a, "q1 release binary A")
    raw_b = scope.existing_regular(args.q1_release_binary_b, "q1 release binary B")
    release_inputs = q1_release_inputs(
        build_a_path=build_a_path,
        build_a=build_a,
        build_b_path=build_b_path,
        build_b=build_b,
        build_verification=build_verification,
        raw_a=raw_a,
        raw_b=raw_b,
        scope_build=scope_build,
    )

    result_root.mkdir(mode=0o700)
    scratch_root.mkdir(mode=0o700)
    population_root = result_root / "population"
    population_root.mkdir(mode=0o700)
    population = population_root / "enwik9-opening-100m"
    copy_prefix(corpus, population)
    identity_values: dict[str, tuple[dict[str, Any], str]] = {}
    for arm, role in (("I-P", "parent"), ("I-Q", "candidate")):
        identity_values[arm] = run_identity_arm(
            arm=arm,
            population=population,
            package=observer_package[role],
            head_blob=observer_head,
            identity_runner=identity_runner,
            identity_schema=identity_schema_path,
            resource_guard=identity_guard,
            lease=args.exclusive_lease,
            result_root=result_root / arm,
            scratch_root=scratch_root / arm,
            cpu=cpu,
        )
    stage, guard, soft, release_command = run_release_arm(
        population=population,
        release_inputs=release_inputs,
        soft_guard=soft_guard,
        stage_runner=stage_runner,
        stage_schema=stage_schema_path,
        result_root=result_root / "R-Q",
        work_root=scratch_root / "R-Q",
        global_result_root=result_root,
        global_scratch_root=scratch_root,
        cgroup_path=cgroup_path,
        cpu=cpu,
    )
    if next(scratch_root.iterdir(), None) is not None:
        raise RuntimeError("100M coordinator scratch residue survived")
    scratch_root.rmdir()

    arms = {
        name: identity_arm_summary(*identity_values[name]) for name in ("I-P", "I-Q")
    }
    stage_outputs = stage["outputs"]
    arms["R-Q"] = {
        "arm": "R-Q",
        "instrumented": False,
        "resource_authority": True,
        "binary": stage_outputs["packaged_compressor"],
        "command_sha256": release_command,
        "return_codes": stage["return_codes"],
        "post_head_probability_sha256": None,
        "coder_checkpoint_manifest": None,
        "persistent_state_manifest": None,
        "arithmetic_payload": stage_outputs["arithmetic_payload"],
        "self_extracting_archive": stage_outputs["self_extracting_archive"],
        "decoded_transformed": None,
        "raw_inverse": stage_outputs["raw_inverse"],
        "raw_inverse_pass": stage["exact_raw_inverse_pass"],
        "execution_receipt": artifact(stage["_receipt_path"]),
        "backing_cleanup_pass": stage["backing_cleanup_pass"],
    }
    parent = arms["I-P"]
    candidate = arms["I-Q"]
    payload_keys = {
        (value["arithmetic_payload"]["bytes"], value["arithmetic_payload"]["sha256"])
        for value in arms.values()
    }
    raw_pass = all(
        value["raw_inverse_pass"] is True
        and value["raw_inverse"]["bytes"] == PREFIX_BYTES
        and value["raw_inverse"]["sha256"] == PREFIX_SHA256
        for value in arms.values()
    )
    comparisons = {
        "observer_calibration_antecedent_pass": True,
        "post_head_probability_identity_pass": parent["post_head_probability_sha256"]
        == candidate["post_head_probability_sha256"],
        "coder_checkpoint_identity_pass": parent["coder_checkpoint_manifest"]["sha256"]
        == candidate["coder_checkpoint_manifest"]["sha256"],
        "persistent_state_checkpoint_identity_pass": parent["persistent_state_manifest"]["sha256"]
        == candidate["persistent_state_manifest"]["sha256"],
        "arithmetic_payload_identity_pass": len(payload_keys) == 1,
        "decoded_transformed_identity_pass": (
            parent["decoded_transformed"]["bytes"], parent["decoded_transformed"]["sha256"]
        )
        == (
            candidate["decoded_transformed"]["bytes"],
            candidate["decoded_transformed"]["sha256"],
        ),
        "all_raw_inverses_pass": raw_pass,
        "parent_q1_self_extracting_archive_identity_expected": False,
        "identity_gate_pass": False,
    }
    comparisons["identity_gate_pass"] = all(
        value for key, value in comparisons.items() if key != "parent_q1_self_extracting_archive_identity_expected"
    )

    phases = stage["phase_measurements"]
    peaks = guard["peaks"]
    events = guard["cgroup_events"]["delta"]
    tree_peak = max(
        [peaks["max_sampled_tree_rss_kib"]]
        + [value["tree_rss_peak_kib"] for value in phases]
    )
    vmhwm_peak = max(
        [peaks["max_observed_process_vmhwm_kib"]]
        + [value["largest_process_vmhwm_kib"] for value in phases]
    )
    cgroup_peak = max(
        [peaks["cgroup_memory_peak_bytes"]]
        + [value["cgroup_peak_bytes"] for value in phases]
    )
    scratch_logical_peak = max(
        [peaks["max_sampled_scratch_logical_bytes"]]
        + [value["scratch_logical_bytes"] for value in phases]
    )
    scratch_allocated_peak = max(
        [peaks["max_sampled_scratch_allocated_bytes"]]
        + [value["scratch_allocated_bytes"] for value in phases]
    )
    phase_pass = (
        tuple(value["phase"] for value in phases) == PHASES
        and all(value["observed"] is True for value in phases)
    )
    engineering = (
        tree_peak <= ENGINEERING_LIMIT_KIB
        and vmhwm_peak <= ENGINEERING_LIMIT_KIB
        and cgroup_peak <= MEMORY_MAX_BYTES
        and events.get("max", 0) == 0
        and events.get("oom", 0) == 0
        and events.get("oom_kill", 0) == 0
    )
    official = (
        tree_peak <= MEMORY_LIMIT_KIB
        and vmhwm_peak <= MEMORY_LIMIT_KIB
        and cgroup_peak <= MEMORY_MAX_BYTES
        and events.get("max", 0) == 0
        and events.get("oom", 0) == 0
        and events.get("oom_kill", 0) == 0
    )
    temporary_disk = scratch_allocated_peak <= DISK_LIMIT_BYTES and stage["scratch_after_cleanup_bytes"] == 0
    cpu_pass = peaks["max_sampled_allowed_cpu_count"] == 1
    cleanup = stage["scratch_after_cleanup_bytes"] == 0 and all(
        value["backing_cleanup_pass"] is True for value in arms.values()
    )
    resource_gate = all((engineering, official, temporary_disk, cpu_pass, phase_pass, cleanup))
    resources = {
        "authoritative_arm": "R-Q",
        "process_tree_peak_rss_kib": tree_peak,
        "largest_process_vmhwm_kib": vmhwm_peak,
        "cgroup_memory_peak_bytes": cgroup_peak,
        "memory_events_high": events.get("high", 0),
        "memory_events_max": events.get("max", 0),
        "memory_events_oom": events.get("oom", 0),
        "memory_events_oom_kill": events.get("oom_kill", 0),
        "maximum_logical_cpus": peaks["max_sampled_allowed_cpu_count"],
        "scratch_logical_peak_bytes": scratch_logical_peak,
        "scratch_allocated_peak_bytes": scratch_allocated_peak,
        "scratch_after_cleanup_bytes": stage["scratch_after_cleanup_bytes"],
        "resource_guard_receipt": artifact(guard["_receipt_path"]),
        "phase_measurement_receipt": artifact(stage["_receipt_path"]),
        "memory_high_receipt": artifact(soft["_receipt_path"]),
        "phase_measurements": phases,
        "engineering_headroom_pass": engineering,
        "official_memory_pass": official,
        "temporary_disk_pass": temporary_disk,
        "cpu_pass": cpu_pass,
        "phase_measurement_pass": phase_pass,
        "cleanup_pass": cleanup,
        "resource_gate_pass": resource_gate,
    }
    gate_pass = comparisons["identity_gate_pass"] and resource_gate
    decisions = {
        "population_identity_pass": True,
        "identity_gate_pass": comparisons["identity_gate_pass"],
        "resource_gate_pass": resource_gate,
        "opening_100m_gate_pass": gate_pass,
        "authorize_unchanged_full1g_q1": gate_pass,
        "memory_safe_parent_qualified": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    receipt = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "authoritative_parent_id": PARENT_ID,
        "population": {
            "path": str(population),
            "offset": 0,
            "bytes": PREFIX_BYTES,
            "sha256": PREFIX_SHA256,
            "canonical_opening_prefix": True,
        },
        "antecedents": {
            "planning_contract": artifact(plan_path),
            "observer_build": artifact(observer_build_path),
            "observer_build_schema": artifact(observer_build_schema_path),
            "observer_calibration": artifact(calibration_path),
            "observer_calibration_verification": artifact(calibration_verification_path),
            "source_closure": artifact(source_closure_path),
            "program_lock_verification": artifact(lock_path),
            "q1_release_build_a": artifact(build_a_path),
            "q1_release_build_b": artifact(build_b_path),
            "build_verification": artifact(build_verification_path),
            "scope_build_receipt": artifact(scope_build_path),
            "opening_distant_10m_receipt": artifact(transfer_path),
            "opening_distant_10m_verification": artifact(transfer_verification_path),
        },
        "arms": arms,
        "comparisons": comparisons,
        "resources": resources,
        "decisions": decisions,
        "errors": [],
        "terminal_pass": gate_pass,
        "claim_authority": "opening_100m_parent_preservation_and_headroom_only",
        "claim_boundary": (
            "One opening-100M population only; no full-1G qualification, deterministic "
            "repeat, runtime eligibility, compression improvement, authorship, or score credit."
        ),
        "execution_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.validate(receipt, receipt_schema)
    receipt_path = result_root / "identity-resource-receipt.json"
    scope.write_new(receipt_path, receipt)
    return 0 if gate_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
