#!/usr/bin/env python3
"""Produce one source-bound Geekbench-5 runtime qualification receipt for q1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import time
from typing import Any

import jsonschema

import cmix_filebacked_fxcm_scope_identity as scope
import enwiki9_python_source_closure as python_source
import research_contracts
from managed_exclusive_lease import ManagedExclusiveLease, file_sha256


PROJECT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT / "contracts/research/v1/cmix-filebacked-fxcm-runtime-qualification.schema.json"
PLAN_SCHEMA_PATH = PROJECT / "operations/planning/cmix-filebacked-fxcm-runtime-plan.schema.json"
SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-runtime-qualification.v1"
PLAN_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-runtime-plan.v1"
ARM_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1"
ARM_VERIFICATION_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-soft-high-verification.v1"
GUARD_SCHEMA = "gamma.enwiki9.resource-guard-receipt.v3"
STAGE_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-runtime-stage.v1"
HOST_SCHEMA = "gamma.enwiki9.cmix-runtime-host-fingerprint.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
CANONICAL_BYTES = 1_000_000_000
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
MEMORY_LIMIT_KIB = 9_765_625
MEMORY_MAX_BYTES = 10_000_000_000
DISK_LIMIT_BYTES = 100_000_000_000
WALL_TIME_NUMERATOR = 252_000_000
PYTHON = Path("/usr/bin/python3")
TASKSET = Path("/usr/bin/taskset")
SCORE_RE = re.compile(r"Single[- ]Core\s+Score\s*:?\s*([0-9][0-9,]*)", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"^\$\{[A-Z0-9_]+\}$")


def command_sha256(argv: list[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(part) for part in argv)).hexdigest()


def current_process_argv() -> list[str]:
    raw = Path("/proc/self/cmdline").read_bytes()
    if not raw.endswith(b"\0"):
        raise RuntimeError("current process command line is not NUL terminated")
    argv = [os.fsdecode(token) for token in raw[:-1].split(b"\0")]
    if not argv or any(not token for token in argv):
        raise RuntimeError("current process command line is malformed")
    return argv


def instantiate_plan_command(plan: dict[str, Any], replacements: dict[str, str]) -> list[str]:
    command = [replacements.get(token, token) for token in plan["command"]]
    unresolved = [token for token in command if PLACEHOLDER_RE.fullmatch(token)]
    if unresolved:
        raise RuntimeError(f"unresolved runtime command placeholders: {unresolved}")
    return command


def same_record(left: Any, right: Any) -> bool:
    return bool(
        isinstance(left, dict)
        and isinstance(right, dict)
        and left.get("bytes") == right.get("bytes")
        and left.get("sha256") == right.get("sha256")
    )


def same_bytes(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as a, right.open("rb") as b:
        while True:
            aa = a.read(16 << 20)
            bb = b.read(16 << 20)
            if aa != bb:
                return False
            if not aa:
                return True


def write_new(path: Path, value: dict[str, Any]) -> None:
    data = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        cursor = 0
        while cursor < len(data):
            written = os.write(descriptor, data[cursor:])
            if written <= 0:
                raise OSError(f"short write: {path}")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def load_contract(path: Path, schema: str, label: str) -> tuple[Path, dict[str, Any]]:
    resolved, value = scope.load_json(path, label)
    research_contracts.validate_artifact(resolved)
    if value.get("schema") != schema:
        raise RuntimeError(f"{label} schema mismatch")
    return resolved, value


def bound_file(record: Any, label: str) -> Path:
    if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
        raise RuntimeError(f"{label} binding is malformed")
    path = scope.existing_regular(PROJECT / str(record["path"]), label)
    if scope.sha256_file(path) != record["sha256"]:
        raise RuntimeError(f"{label} binding mismatch")
    return path


def closure_rows(entries: tuple[Path, ...]) -> list[dict[str, str]]:
    return [
        {
            "path": path.relative_to(PROJECT).as_posix(),
            "sha256": f"sha256:{scope.sha256_file(path)}",
        }
        for path in python_source.local_source_closure(entries)
    ]


def validate_plan(path: Path) -> tuple[Path, dict[str, Any], Path, dict[str, Path]]:
    if not path.is_absolute():
        path = PROJECT / path
    plan_path, plan = scope.load_json(path, "runtime plan")
    jsonschema.Draft202012Validator(
        json.loads(PLAN_SCHEMA_PATH.read_text(encoding="ascii"))
    ).validate(plan)
    if plan.get("$schema") != PLAN_SCHEMA or plan.get("execution_authorized") is not True:
        raise RuntimeError("runtime plan identity or execution authority mismatch")
    implementation = {
        name: bound_file(record, f"runtime implementation {name}")
        for name, record in plan["implementation"].items()
        if name != "python_source_closure"
    }
    if implementation["coordinator"].resolve() != Path(__file__).resolve(strict=True):
        raise RuntimeError("runtime plan does not bind the selected coordinator")
    closure_path = bound_file(
        plan["implementation"]["python_source_closure"],
        "runtime Python source closure",
    )
    roots = tuple(
        scope.existing_regular(PROJECT / value, f"runtime closure root {index}")
        for index, value in enumerate(plan["source_closure_roots"])
    )
    observed = json.loads(closure_path.read_text(encoding="ascii"))
    if observed != closure_rows(roots):
        raise RuntimeError("runtime Python source closure mismatch")
    return plan_path, plan, closure_path, implementation


def load_arm(
    receipt_path: Path,
    verification_path: Path,
    expected_arm: str,
) -> tuple[Path, dict[str, Any], Path, dict[str, Any]]:
    receipt_path, receipt = load_contract(receipt_path, ARM_SCHEMA, f"Arm {expected_arm.upper()} receipt")
    verification_path, verification = load_contract(
        verification_path,
        ARM_VERIFICATION_SCHEMA,
        f"Arm {expected_arm.upper()} verification",
    )
    if (
        receipt.get("arm") != expected_arm
        or receipt.get("terminal_pass") is not True
        or receipt.get("memory_safe_parent_qualified") is not False
        or verification.get("arm") != expected_arm
        or verification.get("verification_pass") is not True
        or verification.get("errors") != []
        or not verification.get("checks")
        or not all(verification["checks"].values())
        or verification.get("source_receipt") != scope.artifact(receipt_path)
    ):
        raise RuntimeError(f"Arm {expected_arm.upper()} is not an independently verified terminal pass")
    return receipt_path, receipt, verification_path, verification


def parse_geekbench5_score(path: Path) -> int:
    raw = scope.existing_regular(path, "raw Geekbench 5 report").read_bytes()
    text = raw.decode("utf-8", errors="replace")
    if re.search(r"Geekbench\s+5(?:\.|\s|$)", text, re.IGNORECASE) is None:
        raise RuntimeError("raw report does not identify Geekbench 5")
    scores = [int(value.replace(",", "")) for value in SCORE_RE.findall(text)]
    if len(scores) != 1 or scores[0] <= 0:
        raise RuntimeError("raw report must contain exactly one positive single-core score")
    return scores[0]


def current_host_fingerprint() -> dict[str, Any]:
    machine_id = scope.existing_regular(Path("/etc/machine-id"), "machine id").read_bytes()
    model_names = sorted(
        {
            line.split(":", 1)[1].strip()
            for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines()
            if line.lower().startswith("model name") and ":" in line
        }
    )
    if not model_names:
        raise RuntimeError("current host exposes no CPU model name")
    return {
        "schema": HOST_SCHEMA,
        "machine_id_sha256": hashlib.sha256(machine_id).hexdigest(),
        "uname_machine": platform.machine(),
        "cpu_model_names": model_names,
    }


def terminate_group(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def remove_empty_cgroup(path: Path) -> bool:
    try:
        occupants = (path / "cgroup.procs").read_text(encoding="ascii").split()
    except FileNotFoundError:
        return True
    if occupants:
        return False
    try:
        path.rmdir()
    except OSError:
        return False
    return not path.exists()


def runtime_guard_pass(value: dict[str, Any], phase: str, score: int) -> bool:
    expected_wall = WALL_TIME_NUMERATOR / score
    events = value.get("cgroup_events", {}).get("delta", {})
    peaks = value.get("peaks", {})
    return bool(
        value.get("schema") == GUARD_SCHEMA
        and value.get("phase") == phase
        and value.get("status") == "complete"
        and value.get("returncode") == 0
        and math.isclose(value.get("geekbench5_single_core_score", 0), score, abs_tol=1e-9)
        and math.isclose(value.get("wall_time_limit_seconds", 0), expected_wall, abs_tol=1e-6)
        and value.get("elapsed_s", expected_wall) < expected_wall
        and value.get("limit_mode") == "tree"
        and value.get("limit_kib") == MEMORY_LIMIT_KIB
        and value.get("official_decimal_limit_kib") == MEMORY_LIMIT_KIB
        and value.get("cgroup", {}).get("requested_memory_max_bytes") == MEMORY_MAX_BYTES
        and value.get("cgroup", {}).get("memory_max_bytes", MEMORY_MAX_BYTES + 1) <= MEMORY_MAX_BYTES
        and value.get("cgroup", {}).get("joined_before_exec") is True
        and peaks.get("max_sampled_tree_rss_kib", MEMORY_LIMIT_KIB) < MEMORY_LIMIT_KIB
        and peaks.get("max_observed_process_vmhwm_kib", MEMORY_LIMIT_KIB) < MEMORY_LIMIT_KIB
        and peaks.get("cgroup_memory_peak_bytes", MEMORY_MAX_BYTES) < MEMORY_MAX_BYTES
        and peaks.get("max_sampled_scratch_logical_bytes", DISK_LIMIT_BYTES) < DISK_LIMIT_BYTES
        and peaks.get("max_sampled_scratch_allocated_bytes", DISK_LIMIT_BYTES) < DISK_LIMIT_BYTES
        and peaks.get("max_sampled_allowed_cpu_count", 2) <= 1
        and all(value.get("measurements", {}).values())
        and not any(value.get("guards", {}).values())
        and events.get("max", 0) == 0
        and events.get("oom", 0) == 0
        and events.get("oom_kill", 0) == 0
        and events.get("oom_group_kill", 0) == 0
    )


def run_stage(
    *,
    phase: str,
    mode: str,
    score: int,
    cpu: int,
    corpus: Path,
    package: Path,
    head: Path,
    archive: Path | None,
    result_root: Path,
    scratch_root: Path,
    cgroup_path: Path,
    guard: Path,
    stage_runner: Path,
    stage_schema: Path,
    lease: ManagedExclusiveLease,
) -> dict[str, Any]:
    phase_result = result_root / phase
    phase_work = scratch_root / phase
    phase_result.mkdir(mode=0o700)
    phase_work.mkdir(mode=0o700)
    marker = phase_result / "phase-markers.jsonl"
    marker.touch(mode=0o600, exist_ok=False)
    guard_receipt = phase_result / "guard.json"
    stage_receipt = phase_result / "stage-receipt.json"
    cgroup_path.mkdir(mode=0o700)

    stage_argv = [
        str(PYTHON),
        str(stage_runner),
        "--mode",
        mode,
        "--work-root",
        str(phase_work),
        "--result-root",
        str(phase_result),
        "--receipt",
        str(stage_receipt),
    ]
    if mode == "encode":
        stage_argv.extend(
            [
                "--corpus",
                str(corpus),
                "--package",
                str(package),
                "--head",
                str(head),
            ]
        )
    else:
        if archive is None:
            raise RuntimeError("decompression requires the runtime-produced archive")
        stage_argv.extend(["--archive", str(archive)])
    guard_argv = [
        str(TASKSET),
        "--cpu-list",
        str(cpu),
        str(PYTHON),
        str(guard),
        "--limit-kib",
        str(MEMORY_LIMIT_KIB),
        "--limit-mode",
        "tree",
        "--official-decimal-limit-kib",
        str(MEMORY_LIMIT_KIB),
        "--sample-interval",
        "0.5",
        "--cgroup-path",
        str(cgroup_path),
        "--cgroup-memory-max-bytes",
        str(MEMORY_MAX_BYTES),
        "--scratch-path",
        str(scratch_root),
        "--scratch-path",
        str(result_root),
        "--temporary-disk-limit-bytes",
        str(DISK_LIMIT_BYTES),
        "--phase-marker-path",
        str(marker),
        "--max-logical-cpus",
        "1",
        "--guard-json",
        str(guard_receipt),
        "--label",
        f"q1-runtime-{phase}",
        "--phase",
        phase,
        "--geekbench5-single-core-score",
        str(score),
        "--",
        *stage_argv,
    ]
    stdout_path = phase_result / "guard.stdout"
    stderr_path = phase_result / "guard.stderr"
    return_code: int | None = None
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(
            guard_argv,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
            env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin", "TZ": "UTC"},
        )
        try:
            while (return_code := process.poll()) is None:
                lease.heartbeat()
                time.sleep(5)
        finally:
            terminate_group(process)
            return_code = process.wait()

    cgroup_cleanup = remove_empty_cgroup(cgroup_path)
    errors: list[str] = []
    guard_value: dict[str, Any] | None = None
    stage_value: dict[str, Any] | None = None
    if guard_receipt.is_file():
        try:
            _, guard_value = load_contract(guard_receipt, GUARD_SCHEMA, f"{phase} guard")
        except Exception as exc:
            errors.append(f"guard_invalid: {type(exc).__name__}: {exc}")
    else:
        errors.append("guard_receipt_missing")
    if stage_receipt.is_file():
        try:
            _, stage_value = scope.load_json(stage_receipt, f"{phase} stage")
            jsonschema.Draft202012Validator(
                json.loads(stage_schema.read_text(encoding="ascii"))
            ).validate(stage_value)
            if stage_value.get("schema") != STAGE_SCHEMA:
                raise RuntimeError(f"{phase} stage schema identity mismatch")
        except Exception as exc:
            errors.append(f"stage_invalid: {type(exc).__name__}: {exc}")
    else:
        errors.append("stage_receipt_missing")
    if not cgroup_cleanup:
        errors.append("cgroup_cleanup_failed")
    passed = bool(
        not errors
        and return_code == 0
        and guard_value is not None
        and runtime_guard_pass(guard_value, phase, score)
        and stage_value is not None
        and stage_value.get("mode") == mode
        and stage_value.get("stage_pass") is True
    )
    if not passed and not errors:
        errors.append("stage_or_guard_runtime_contract_failed")
    return {
        "phase": phase,
        "mode": mode,
        "outer_return_code": return_code,
        "stage_argv": stage_argv,
        "guard_argv": guard_argv,
        "stage_command_sha256": command_sha256(stage_argv),
        "guard_command_sha256": command_sha256(guard_argv),
        "cgroup_path": str(cgroup_path),
        "work_root": str(phase_work),
        "result_root": str(phase_result),
        "phase_marker": str(marker),
        "guard_receipt": scope.artifact(guard_receipt) if guard_receipt.is_file() else None,
        "stage_receipt": scope.artifact(stage_receipt) if stage_receipt.is_file() else None,
        "guard_stdout": scope.artifact(stdout_path),
        "guard_stderr": scope.artifact(stderr_path),
        "guard": guard_value,
        "stage": stage_value,
        "cgroup_cleanup_pass": cgroup_cleanup,
        "errors": errors,
        "stage_and_guard_pass": passed,
    }


def execution_summary(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        key: value[key]
        for key in (
            "phase",
            "mode",
            "outer_return_code",
            "stage_argv",
            "guard_argv",
            "stage_command_sha256",
            "guard_command_sha256",
            "cgroup_path",
            "work_root",
            "result_root",
            "phase_marker",
            "guard_stdout",
            "guard_stderr",
            "cgroup_cleanup_pass",
            "errors",
            "stage_and_guard_pass",
        )
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--arm-a-receipt", type=Path, required=True)
    parser.add_argument("--arm-a-verification", type=Path, required=True)
    parser.add_argument("--arm-b-receipt", type=Path, required=True)
    parser.add_argument("--arm-b-verification", type=Path, required=True)
    parser.add_argument("--geekbench5-report", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--cgroup-path", type=Path, required=True)
    parser.add_argument("--lease-path", type=Path, required=True)
    parser.add_argument("--lease-transition", type=Path, required=True)
    parser.add_argument("--cpu", type=int, required=True)
    args = parser.parse_args()

    plan_path, plan, closure_path, implementation = validate_plan(args.plan)
    if Path.cwd().resolve(strict=True) != PROJECT or plan["working_directory"] != str(PROJECT):
        raise RuntimeError("runtime coordinator must execute from the plan-bound project directory")
    arm_a_path, arm_a, arm_a_verification_path, _ = load_arm(
        args.arm_a_receipt, args.arm_a_verification, "a"
    )
    arm_b_path, arm_b, arm_b_verification_path, _ = load_arm(
        args.arm_b_receipt, args.arm_b_verification, "b"
    )
    if not all(
        same_record(arm_a[left][name], arm_b[left][name])
        for left, names in (
            ("package", ("packaged_compressor", "head")),
            ("outputs", ("payload", "archive", "restored")),
        )
        for name in names
    ):
        raise RuntimeError("Arm A/B exact package or output identity mismatch")
    if not all(value is True for value in arm_b["identity"]["arm_a"].values()):
        raise RuntimeError("Arm B does not independently assert every Arm A identity")

    corpus = scope.existing_regular(args.corpus, "canonical enwik9")
    population_record = scope.artifact(corpus)
    if population_record["bytes"] != CANONICAL_BYTES or population_record["sha256"] != CANONICAL_SHA256:
        raise RuntimeError("canonical corpus identity mismatch")
    report = scope.existing_regular(args.geekbench5_report, "raw Geekbench 5 report")
    report_record = scope.artifact(report)
    score = parse_geekbench5_score(report)
    package = scope.verify_artifact_record(arm_a["package"]["packaged_compressor"], "Arm A package")
    head = scope.verify_artifact_record(arm_a["package"]["head"], "Arm A head")
    reference_archive = scope.verify_artifact_record(arm_a["outputs"]["archive"], "Arm A archive")
    stage_runner = implementation["stage_runner"]
    stage_schema = implementation["stage_schema"]
    guard = implementation["resource_guard"]
    if stage_runner != bound_file(plan["implementation"]["stage_runner"], "selected stage runner"):
        raise RuntimeError("selected stage runner changed")
    if guard != bound_file(plan["implementation"]["resource_guard"], "selected resource guard"):
        raise RuntimeError("selected resource guard changed")
    scope.existing_regular(PYTHON, "runtime Python")
    scope.existing_regular(TASKSET, "taskset")

    result_root, result_filesystem = scope.absent_root(args.result_root, "runtime result root")
    scratch_root, scratch_filesystem = scope.absent_root(args.scratch_root, "runtime scratch root")
    if result_root == scratch_root or result_root in scratch_root.parents or scratch_root in result_root.parents:
        raise RuntimeError("runtime result and scratch roots must be disjoint")
    cgroup_path = args.cgroup_path
    if not cgroup_path.is_absolute() or cgroup_path.exists() or cgroup_path.is_symlink():
        raise RuntimeError("runtime cgroup path must be an absent absolute path")
    scope.existing_directory(cgroup_path.parent, "runtime cgroup parent")
    lease_path = args.lease_path
    if not lease_path.is_absolute() or lease_path.exists() or lease_path.is_symlink():
        raise RuntimeError("exclusive full-1G lease must be absent")
    scope.existing_directory(lease_path.parent, "lease parent")
    lease_lock = lease_path.with_name(f"{lease_path.name}.lock")
    if lease_lock.exists() or lease_lock.is_symlink():
        raise RuntimeError("exclusive full-1G lease acquisition lock must be absent")
    transition_path = args.lease_transition
    if not transition_path.is_absolute() or transition_path.exists() or transition_path.is_symlink():
        raise RuntimeError("lease transition path must be absent")
    if transition_path.parent != result_root:
        raise RuntimeError("lease transition must be a direct child of runtime result root")
    cpu = args.cpu
    if cpu not in os.sched_getaffinity(0):
        raise RuntimeError("selected logical CPU is outside coordinator affinity")

    coordinator_argv = current_process_argv()
    expected_coordinator_argv = instantiate_plan_command(
        plan,
        {
            "${ARM_A_RECEIPT}": str(arm_a_path),
            "${ARM_A_VERIFICATION}": str(arm_a_verification_path),
            "${ARM_B_RECEIPT}": str(arm_b_path),
            "${ARM_B_VERIFICATION}": str(arm_b_verification_path),
            "${GEEKBENCH5_REPORT}": str(report),
            "${RESULT_ROOT}": str(result_root),
            "${SCRATCH_ROOT}": str(scratch_root),
            "${CGROUP_PATH}": str(cgroup_path),
            "${LEASE_TRANSITION}": str(transition_path),
            "${CPU}": str(cpu),
        },
    )
    if coordinator_argv != expected_coordinator_argv:
        raise RuntimeError("runtime coordinator argv differs from the exact plan command")

    objective = research_contracts.objective_binding()
    antecedent_records = {
        "plan": scope.artifact(plan_path),
        "python_source_closure": scope.artifact(closure_path),
        "arm_a_receipt": scope.artifact(arm_a_path),
        "arm_a_verification": scope.artifact(arm_a_verification_path),
        "arm_b_receipt": scope.artifact(arm_b_path),
        "arm_b_verification": scope.artifact(arm_b_verification_path),
    }
    implementation_records = {
        name: scope.artifact(path)
        for name, path in implementation.items()
    }
    drift_records = {
        **{f"antecedent_{name}": record for name, record in antecedent_records.items()},
        **{f"implementation_{name}": record for name, record in implementation_records.items()},
        "population": population_record,
        "geekbench5_report": report_record,
        "packaged_compressor": arm_a["package"]["packaged_compressor"],
        "head": arm_a["package"]["head"],
        "reference_archive": arm_a["outputs"]["archive"],
    }

    result_root.mkdir(mode=0o700)
    scratch_root.mkdir(mode=0o700)
    fingerprint_path = result_root / "host-fingerprint.json"
    fingerprint = current_host_fingerprint()
    jsonschema.Draft202012Validator(
        json.loads(implementation["host_fingerprint_schema"].read_text(encoding="ascii"))
    ).validate(fingerprint)
    write_new(fingerprint_path, fingerprint)

    errors: list[str] = []
    compression: dict[str, Any] | None = None
    decompression: dict[str, Any] | None = None
    lease: ManagedExclusiveLease | None = None
    lease_release_pass = False
    try:
        lease = ManagedExclusiveLease.acquire(
            lease_path=lease_path,
            transition_path=transition_path,
            candidate_id=f"{CANDIDATE_ID}-runtime",
            command_sha256=command_sha256(coordinator_argv),
            runner_sha256=file_sha256(Path(__file__).resolve(strict=True)),
            guard_path=str(result_root),
            result_path=str(result_root),
            scratch_path=str(scratch_root),
            claim_boundary="exact-package Geekbench-5 runtime qualification only; zero compression credit",
        )
        compression = run_stage(
            phase="compression",
            mode="encode",
            score=score,
            cpu=cpu,
            corpus=corpus,
            package=package,
            head=head,
            archive=None,
            result_root=result_root,
            scratch_root=scratch_root,
            cgroup_path=cgroup_path,
            guard=guard,
            stage_runner=stage_runner,
            stage_schema=stage_schema,
            lease=lease,
        )
        if not compression["stage_and_guard_pass"]:
            errors.extend(f"compression: {error}" for error in compression["errors"])
        else:
            runtime_archive = scope.verify_artifact_record(
                compression["stage"]["outputs"]["archive"], "runtime archive"
            )
            if not same_bytes(runtime_archive, reference_archive):
                errors.append("runtime compression archive differs from independently repeated Arm A/B archive")
            else:
                decompression = run_stage(
                    phase="decompression",
                    mode="decode",
                    score=score,
                    cpu=cpu,
                    corpus=corpus,
                    package=package,
                    head=head,
                    archive=runtime_archive,
                    result_root=result_root,
                    scratch_root=scratch_root,
                    cgroup_path=cgroup_path,
                    guard=guard,
                    stage_runner=stage_runner,
                    stage_schema=stage_schema,
                    lease=lease,
                )
                if not decompression["stage_and_guard_pass"]:
                    errors.extend(f"decompression: {error}" for error in decompression["errors"])
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    finally:
        if cgroup_path.exists() and not remove_empty_cgroup(cgroup_path):
            errors.append("terminal_cgroup_cleanup_failed")
        if lease is not None:
            try:
                lease.heartbeat()
                lease.release(evidence_path=result_root / "lease-evidence.json")
                lease_release_pass = True
            except Exception as exc:
                errors.append(f"lease_release_failed: {type(exc).__name__}: {exc}")

    outputs: dict[str, Any] = {"payload": None, "archive": None, "restored": None}
    if compression is not None and compression.get("stage"):
        outputs["payload"] = compression["stage"].get("outputs", {}).get("payload")
        outputs["archive"] = compression["stage"].get("outputs", {}).get("archive")
    if decompression is not None and decompression.get("stage"):
        outputs["restored"] = decompression["stage"].get("outputs", {}).get("restored")
    identities = {
        "arm_a_b_package_identity_pass": same_record(
            arm_a["package"]["packaged_compressor"], arm_b["package"]["packaged_compressor"]
        ),
        "arm_a_b_head_identity_pass": same_record(arm_a["package"]["head"], arm_b["package"]["head"]),
        "arm_a_b_payload_identity_pass": same_record(arm_a["outputs"]["payload"], arm_b["outputs"]["payload"]),
        "arm_a_b_archive_identity_pass": same_record(arm_a["outputs"]["archive"], arm_b["outputs"]["archive"]),
        "arm_a_b_restored_identity_pass": same_record(arm_a["outputs"]["restored"], arm_b["outputs"]["restored"]),
        "runtime_payload_identity_pass": same_record(outputs["payload"], arm_a["outputs"]["payload"]),
        "runtime_archive_identity_pass": same_record(outputs["archive"], arm_a["outputs"]["archive"]),
        "runtime_restored_identity_pass": same_record(outputs["restored"], arm_a["outputs"]["restored"]),
        "exact_raw_inverse_pass": bool(
            decompression is not None
            and decompression.get("stage", {}).get("exact_raw_inverse_pass") is True
        ),
    }
    for name, passed in identities.items():
        if not passed:
            errors.append(f"identity_failed: {name}")
    if research_contracts.objective_binding() != objective:
        errors.append("source_drift: objective_binding")
    for name, record in drift_records.items():
        try:
            scope.verify_artifact_record(record, f"terminal {name}")
        except Exception as exc:
            errors.append(f"source_drift: {name}: {type(exc).__name__}: {exc}")
    pre_cleanup_pass = bool(
        not errors
        and compression is not None
        and decompression is not None
        and compression["stage_and_guard_pass"]
        and decompression["stage_and_guard_pass"]
        and all(identities.values())
        and lease_release_pass
        and not lease_path.exists()
        and not lease_lock.exists()
        and not cgroup_path.exists()
    )
    if pre_cleanup_pass:
        try:
            shutil.rmtree(scratch_root)
        except Exception as exc:
            errors.append(f"successful_runtime_scratch_cleanup_failed: {type(exc).__name__}: {exc}")
    scratch_removed = not scratch_root.exists()
    if pre_cleanup_pass and not scratch_removed:
        errors.append("successful runtime scratch cleanup failed")
    terminal_pass = bool(pre_cleanup_pass and scratch_removed and not errors)

    receipt = {
        "schema": SCHEMA,
        "contract_revision": 2,
        "candidate_id": CANDIDATE_ID,
        "objective": objective,
        "antecedents": antecedent_records,
        "implementation": implementation_records,
        "population": population_record,
        "benchmark": {
            "version": 5,
            "single_core_score": score,
            "raw_report": report_record,
            "host_fingerprint": scope.artifact(fingerprint_path),
        },
        "package": {
            "packaged_compressor": arm_a["package"]["packaged_compressor"],
            "head": arm_a["package"]["head"],
            "archive": arm_a["outputs"]["archive"],
        },
        "execution": {
            "working_directory": str(PROJECT),
            "coordinator_argv": coordinator_argv,
            "coordinator_command_sha256": command_sha256(coordinator_argv),
            "selected_logical_cpu": cpu,
            "result_root": str(result_root),
            "scratch_root": str(scratch_root),
            "result_filesystem_type": result_filesystem,
            "scratch_filesystem_type": scratch_filesystem,
            "compression": execution_summary(compression),
            "decompression": execution_summary(decompression),
        },
        "guards": {
            "compression": compression["guard_receipt"] if compression is not None else None,
            "decompression": decompression["guard_receipt"] if decompression is not None else None,
        },
        "stage_receipts": {
            "compression": compression["stage_receipt"] if compression is not None else None,
            "decompression": decompression["stage_receipt"] if decompression is not None else None,
        },
        "outputs": outputs,
        "identities": identities,
        "cleanup": {
            "scratch_root": str(scratch_root),
            "scratch_removed_on_success_pass": terminal_pass and scratch_removed,
            "scratch_preserved_on_failure": not terminal_pass and scratch_root.exists(),
            "cgroup_path": str(cgroup_path),
            "cgroup_removed_pass": not cgroup_path.exists(),
            "lease_path": str(lease_path),
            "lease_removed_pass": not lease_path.exists() and not lease_lock.exists(),
            "lease_release_pass": lease_release_pass,
            "lease_evidence": (
                scope.artifact(result_root / "lease-evidence.json")
                if (result_root / "lease-evidence.json").is_file()
                else None
            ),
            "lease_transitions": (
                scope.artifact(transition_path) if transition_path.is_file() else None
            ),
        },
        "errors": list(dict.fromkeys(errors)),
        "terminal_pass": terminal_pass,
        "runtime_eligible": terminal_pass,
        "claim_boundary": (
            "Exact-package Geekbench-5 runtime qualification on this source-bound host only; "
            "no probability identity, compression improvement, authorship, or score credit."
        ),
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.Draft202012Validator(
        json.loads(SCHEMA_PATH.read_text(encoding="ascii"))
    ).validate(receipt)
    receipt_path = result_root / "runtime-qualification.json"
    write_new(receipt_path, receipt)
    return 0 if terminal_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
