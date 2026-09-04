#!/usr/bin/env python3
"""Guarded opening-100M original-CMIX env8192 resource successor."""

import hashlib
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_ppm_rss_env8192_opening100m_resource_q0_v1"
PREIMPORT_DEPENDENCIES = (
    (
        "coordinator_v10",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v10.py",
        29442,
        "7044081f6fa4e31ee4ce6d9895e124fd6dc9d16a99f85830f46a0cc7807c597f",
    ),
    (
        "helpers_v3",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3.py",
        33567,
        "f7092b45762ac01027098256a4e041c2ebe0d252eea5a813401d38f525ac29e7",
    ),
    (
        "coordinator_v2",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v2.py",
        45710,
        "c4f370e178c782001cc18bd77cb8e8699ad2505ccf2fb9a99fc87ae047a81639",
    ),
)


def _sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_preimport_dependencies():
    observed = {}
    for name, relative, expected_bytes, expected_sha256 in PREIMPORT_DEPENDENCIES:
        unresolved = PROJECT / relative
        if unresolved.is_symlink() or unresolved.resolve(strict=True) != unresolved.absolute():
            raise RuntimeError(f"pre-import dependency path invalid: {name}")
        if unresolved.stat().st_size != expected_bytes or _sha256_file(unresolved) != expected_sha256:
            raise RuntimeError(f"pre-import dependency drift: {name}")
        observed[name] = {
            "path": relative,
            "bytes": expected_bytes,
            "sha256": expected_sha256,
        }
    return observed


PREIMPORT_REPORT = _verify_preimport_dependencies()

# No inherited project code is imported above this boundary.
import argparse
import importlib.util
import json
import math
import os
import shutil
import stat
import sys
import time
from typing import Any


PLAN_SCHEMA = "gamma.enwiki9.cmix-env8192-opening100m-resource-plan.v1"
DECISION_SCHEMA = "gamma.enwiki9.cmix-env8192-opening100m-resource-decision.v1"
STAGE_SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-opening100m-stage.resource-q0-v1"
CALIBRATION_SCHEMA = "gamma.enwiki9.geekbench5-tryout-calibration.v1"
CALIBRATION_VERIFY_SCHEMA = "gamma.enwiki9.geekbench5-tryout-calibration-verification.v1"
POPULATION_BYTES = 100_000_000
POPULATION_SHA256 = "2b49720ec4d78c3c9fabaee6e4179a5e997302b3a70029f30f2d582218c024a8"
CANONICAL_BYTES = 1_000_000_000
MEMORY_LIMIT_KIB = 9_765_625
MEMORY_MAX_BYTES = 10_000_000_000
ENGINEERING_TREE_RSS_KIB = 9_000_000
PPM_TRIGGER_KIB = 8_192 * 1_024
DISK_LIMIT_BYTES = 100_000_000_000
WALL_TIME_NUMERATOR = 252_000_000
RUNTIME_RESERVE = 1.25
COUNTED_COMPRESS_COMMAND = (
    "CMIX_PPM_RSS_MB=8192 KH_BITLSTM32=head.blob ./cmix -e enwik9 out.cmix"
)
COUNTED_DECOMPRESS_COMMAND = "CMIX_PPM_RSS_MB=8192 ./archive9"


def load_module(path: Path, name: str) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


V10 = load_module(
    PROJECT / "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v10.py",
    "cmix_opening100m_v10_base",
)
V3 = V10.V3
BASE = V10.BASE


def regular_file(path: Path, label: str) -> Path:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label}: symlink component forbidden: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label}: expected single-link regular file")
    return absolute.resolve(strict=True)


def artifact(path: Path) -> dict[str, Any]:
    path = regular_file(path, "artifact")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": _sha256_file(path)}


def load_json(path: Path, label: str) -> tuple[Path, dict[str, Any]]:
    path = regular_file(path, label)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{label}: expected JSON object")
    return path, value


def verify_binding(record: Any, label: str) -> Path:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise RuntimeError(f"{label}: malformed binding")
    path = Path(str(record["path"]))
    if not path.is_absolute():
        path = PROJECT / path
    path = regular_file(path, label)
    if path.stat().st_size != record["bytes"] or _sha256_file(path) != record["sha256"]:
        raise RuntimeError(f"{label}: binding mismatch")
    return path


def write_json_new(path: Path, value: dict[str, Any]) -> None:
    BASE.write_json_new(path, value)


def same_artifact(left: Any, right: Any) -> bool:
    return bool(
        isinstance(left, dict)
        and isinstance(right, dict)
        and left.get("bytes") == right.get("bytes")
        and left.get("sha256") == right.get("sha256")
    )


def stage_argv(
    arm: str,
    phase_result: Path,
    phase_work: Path,
    population: dict[str, Any],
    package: dict[str, Any],
    head: dict[str, Any],
    archive: dict[str, Any] | None,
) -> tuple[str, str, list[str]]:
    mode = "decode" if arm == "E-decode" else "encode"
    ppm = "default" if arm == "P" else "8192"
    argv = [
        sys.executable,
        str(V3.STAGE_PATH),
        "--mode",
        mode,
        "--arm",
        arm,
        "--work-root",
        str(phase_work),
        "--result-root",
        str(phase_result),
        "--receipt",
        str(phase_result / "stage.json"),
        "--ppm-rss-mb",
        ppm,
    ]
    if mode == "encode":
        argv.extend(
            [
                "--input",
                population["path"],
                "--package",
                package["path"],
                "--head",
                head["path"],
            ]
        )
    else:
        if not isinstance(archive, dict):
            raise RuntimeError("decode archive record is absent")
        argv.extend(
            [
                "--archive",
                archive["path"],
                "--archive-bytes",
                str(archive["bytes"]),
                "--archive-sha256",
                archive["sha256"],
            ]
        )
    return mode, ppm, argv


def strict_guard_pass(
    value: dict[str, Any],
    *,
    label: str,
    phase: str,
    command: list[str],
    cgroup: Path,
    scratch: Path,
    result: Path,
    marker: Path,
    score: Any,
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(value.get("schema") == BASE.GUARD_SCHEMA, "schema")
    require(value.get("status") == "complete" and value.get("returncode") == 0, "terminal")
    require(value.get("label") == label and value.get("phase") == phase == "identity", "label-phase")
    require(value.get("command") == command, "command")
    require(value.get("command_sha256") == BASE.command_sha256(command), "command-digest")
    require(value.get("limit_kib") == MEMORY_LIMIT_KIB, "memory-limit")
    require(value.get("official_decimal_limit_kib") == MEMORY_LIMIT_KIB, "official-memory-limit")
    require(value.get("temporary_disk_limit_bytes") == DISK_LIMIT_BYTES, "disk-limit")
    require(value.get("max_logical_cpus") == 1, "cpu-limit")
    require(value.get("wall_time_limit_seconds") is None, "diagnostic-wall-limit")
    require(value.get("scratch_paths") == [str(scratch), str(result)], "scratch-paths")
    require(value.get("phase_marker_path") == str(marker), "phase-marker-path")
    cgroup_value = value.get("cgroup", {})
    require(cgroup_value.get("path") == str(cgroup), "cgroup-path")
    require(cgroup_value.get("joined_before_exec") is True, "cgroup-join")
    require(cgroup_value.get("requested_memory_max_bytes") == MEMORY_MAX_BYTES, "cgroup-request")
    require(cgroup_value.get("memory_swap_max_bytes") == 0, "zero-swap")
    require(
        isinstance(cgroup_value.get("memory_max_bytes"), int)
        and cgroup_value["memory_max_bytes"] <= MEMORY_MAX_BYTES,
        "cgroup-effective-limit",
    )
    measurements = value.get("measurements", {})
    guards = value.get("guards", {})
    require(bool(measurements) and all(item is True for item in measurements.values()), "measurements")
    require(bool(guards) and all(item is False for item in guards.values()), "guards")
    event_delta = value.get("cgroup_events", {}).get("delta", {})
    require(
        event_delta.get("max", 0) == 0
        and event_delta.get("oom", 0) == 0
        and event_delta.get("oom_kill", 0) == 0,
        "cgroup-events",
    )
    expected_marker_phase = "opening100m_" + label.rsplit("-", 1)[-1]
    marker_pairs = {
        (item.get("phase"), item.get("event"))
        for item in value.get("phase_markers", [])
        if isinstance(item, dict)
    }
    require(
        (expected_marker_phase, "start") in marker_pairs
        and (expected_marker_phase, "end") in marker_pairs,
        "phase-markers",
    )
    peaks = value.get("peaks", {})
    require(peaks.get("max_sampled_tree_rss_kib", MEMORY_LIMIT_KIB) < MEMORY_LIMIT_KIB, "tree-rss")
    require(peaks.get("max_observed_process_vmhwm_kib", MEMORY_LIMIT_KIB) < MEMORY_LIMIT_KIB, "vmhwm")
    require(peaks.get("cgroup_memory_peak_bytes", MEMORY_MAX_BYTES) < MEMORY_MAX_BYTES, "cgroup-peak")
    require(peaks.get("max_sampled_scratch_logical_bytes", DISK_LIMIT_BYTES) < DISK_LIMIT_BYTES, "logical-disk")
    require(peaks.get("max_sampled_scratch_allocated_bytes", DISK_LIMIT_BYTES) < DISK_LIMIT_BYTES, "allocated-disk")
    return not errors, errors


def affinity_samples_pass(guard: dict[str, Any], cpu: int, mode: str) -> bool:
    observed: list[dict[str, Any]] = []
    for name in ("peak_sample", "peak_tree_sample", "latest_sample"):
        sample = guard.get(name)
        if not isinstance(sample, dict) or not isinstance(sample.get("processes"), list):
            return False
        rows = sample["processes"]
        if not rows:
            if not (
                name == "latest_sample"
                and sample.get("allowed_cpu_union") == []
                and sample.get("tree_rss_kib") == 0
                and sample.get("tree_live_threads") == 0
                and guard.get("status") == "complete"
                and guard.get("returncode") == 0
                and guard.get("measurements", {}).get("affinity_complete") is True
                and guard.get("measurements", {}).get("process_tree_rss_complete") is True
                and guard.get("guards", {}).get("measurement_incomplete") is False
                and guard.get("peaks", {}).get("max_sampled_allowed_cpu_count") == 1
            ):
                return False
            continue
        if sample.get("allowed_cpu_union") != [cpu]:
            return False
        if any(not isinstance(row, dict) or row.get("allowed_cpus") != [cpu] for row in rows):
            return False
        observed.extend(rows)
    expected = {"archive9"} if mode == "decode" else {"cmix"}
    return bool(observed) and any(row.get("comm") in expected for row in observed)


def expected_result_paths() -> set[str]:
    common = {
        "codec.stdout",
        "codec.stderr",
        "execution.json",
        "guard.stdout",
        "guard.stderr",
        "guard.json",
        "phase-markers.jsonl",
        "stage.json",
    }
    paths: set[str] = set()
    for slug in ("p", "e_a", "e_b"):
        paths.update(f"{slug}/{name}" for name in common | {"out.cmix", "archive9"})
    paths.update(
        f"e_decode/{name}" for name in common | {"enwik9_uncompressed"}
    )
    paths.update(
        {
            "experiment-lease-transitions.json",
            "experiment-lease-evidence.json",
            "experiment-lease-verification.json",
        }
    )
    return paths


def result_manifest(result_root: Path) -> tuple[list[dict[str, Any]], bool]:
    records = []
    for path in sorted(result_root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"result symlink forbidden: {path}")
        if path.is_file() and path.name != "decision.json":
            record = artifact(path)
            record["path"] = path.relative_to(result_root).as_posix()
            records.append(record)
    return records, {record["path"] for record in records} == expected_result_paths()


def runtime_authority(plan: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    runtime = plan["runtime_authority"]
    receipt_path, receipt = load_json(Path(runtime["producer_receipt_path"]), "calibration receipt")
    verification_path, verification = load_json(
        Path(runtime["verification_path"]), "calibration verification"
    )
    calibration_plan = verify_binding(plan["artifacts"]["calibration_plan"], "calibration plan")
    score = receipt.get("selected_single_core_score")
    if not (
        receipt.get("$schema") == CALIBRATION_SCHEMA
        and receipt.get("candidate_id") == runtime["candidate_id"]
        and receipt.get("terminal_authority") is True
        and receipt.get("plan") == artifact(calibration_plan)
        and isinstance(score, int)
        and score > 0
        and verification.get("$schema") == CALIBRATION_VERIFY_SCHEMA
        and verification.get("candidate_id") == runtime["candidate_id"]
        and verification.get("source_receipt") == artifact(receipt_path)
        and verification.get("authority_verified") is True
        and verification.get("evidence_valid") is True
        and verification.get("errors") == []
        and verification.get("selected_single_core_score") == score
    ):
        raise RuntimeError("current-host Geekbench 5 authority is absent or invalid")
    return score, {
        "producer_receipt": artifact(receipt_path),
        "independent_verification": artifact(verification_path),
        "single_core_score": score,
    }


def static_plan(plan_path: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    _, plan = load_json(plan_path, "100M plan")
    if (
        plan.get("$schema") != PLAN_SCHEMA
        or plan.get("candidate_id") != CANDIDATE_ID
        or plan.get("execution_authorized") is not True
        or plan.get("objective_credit_bytes") != 0
    ):
        raise RuntimeError("100M plan identity or authority mismatch")
    paths = {
        name: verify_binding(record, f"plan artifact {name}")
        for name, record in plan["artifacts"].items()
    }
    if paths["coordinator"] != Path(__file__).resolve(strict=True):
        raise RuntimeError("plan does not bind this coordinator")
    if paths["stage"] != Path(plan["stage_path"]).resolve(strict=True):
        raise RuntimeError("plan stage binding mismatch")
    identity_decision = json.loads(paths["identity_decision"].read_text(encoding="utf-8"))
    if not (
        identity_decision.get("candidate_id")
        == "cmix_obias_source_ppm_rss_env8192_zombiefix_q0_v1"
        and identity_decision.get("terminal_pass") is True
        and identity_decision.get("promotion_authorized") is False
        and identity_decision.get("separately_frozen_100m_experiment_required") is True
    ):
        raise RuntimeError("opening-1M identity antecedent is not a terminal pass")
    ppmd = paths["ppmd_source"].read_text(encoding="utf-8")
    if any(
        fragment not in ppmd
        for fragment in (
            'getenv("CMIX_PPM_RSS_MB")',
            "strtoull(env, &end, 10)",
            "DropPpmHeapResidency(ppmd_model_.get())",
        )
    ):
        raise RuntimeError("original CMIX source lacks the bound PPM residency seam")
    return plan, paths


def dynamic_preflight(plan: dict[str, Any], files: dict[str, Path]) -> dict[str, Any]:
    blockers: list[str] = []
    runtime: dict[str, Any] | None = None
    score: int | None = None
    try:
        score, runtime = runtime_authority(plan)
    except Exception as exc:
        blockers.append(f"runtime authority: {exc}")
    running = sorted(
        str(path) for path in (PROJECT / "operations/adaptive/running").glob("*.json")
    )
    if running:
        blockers.append("adaptive running directory is not empty")
    if Path(sys.executable).resolve(strict=True) != files["python"]:
        blockers.append("executing Python does not match the frozen interpreter")
    for role in ("result_root", "scratch_root", "cgroup_base"):
        path = Path(plan["paths"][role])
        if path.exists() or path.is_symlink():
            blockers.append(f"{role} is occupied")
    lease = Path(plan["paths"]["lease"])
    if lease.exists() or lease.is_symlink() or lease.with_name(f"{lease.name}.lock").exists():
        blockers.append("canonical managed lease namespace is occupied")
    corpus = Path(plan["paths"]["corpus"])
    if not corpus.is_file() or corpus.stat().st_size != CANONICAL_BYTES:
        blockers.append("canonical corpus size or path mismatch")
    selected_cpu = int(plan["selected_cpu"])
    if selected_cpu not in os.sched_getaffinity(0):
        blockers.append("selected CPU is outside caller affinity")
    parent = Path(plan["paths"]["cgroup_parent"])
    parent_stat = parent.stat()
    controllers = set((parent / "cgroup.controllers").read_text(encoding="ascii").split())
    direct = (parent / "cgroup.procs").read_text(encoding="ascii").split()
    expected_parent = plan["cgroup_parent_identity"]
    if (
        parent_stat.st_ino != expected_parent["inode"]
        or parent_stat.st_uid != expected_parent["uid"]
        or parent_stat.st_gid != expected_parent["gid"]
        or not {"memory", "pids"}.issubset(controllers)
        or direct
        or not os.access(parent, os.W_OK)
    ):
        blockers.append("delegated cgroup parent contract failed")
    return {
        "execution_ready": not blockers,
        "blockers": blockers,
        "runtime_authority": runtime,
        "single_core_score": score,
        "adaptive_running": running,
        "selected_cpu": selected_cpu,
        "caller_affinity": sorted(os.sched_getaffinity(0)),
        "preimport_dependencies": PREIMPORT_REPORT,
        "bound_artifact_count": len(files),
        "cgroup_parent": {
            "path": str(parent),
            "inode": parent_stat.st_ino,
            "uid": parent_stat.st_uid,
            "gid": parent_stat.st_gid,
            "controllers": sorted(controllers),
            "direct_procs": direct,
        },
    }


def output(stages: dict[str, Any], arm: str, name: str) -> Any:
    stage = stages.get(arm, {}).get("stage")
    return stage.get("outputs", {}).get(name) if isinstance(stage, dict) else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--plan-sha256")
    parser.add_argument("--validation-only", action="store_true")
    args = parser.parse_args()
    if Path.cwd().resolve(strict=True) != PROJECT:
        raise RuntimeError(f"runner must execute from {PROJECT}")
    plan_path = args.plan if args.plan.is_absolute() else PROJECT / args.plan
    observed_plan_sha256 = _sha256_file(plan_path)
    if args.plan_sha256 is not None and args.plan_sha256 != observed_plan_sha256:
        raise RuntimeError("100M plan SHA-256 mismatch")
    plan, files = static_plan(plan_path)

    stage_path = files["stage"]
    V10.CANDIDATE_ID = CANDIDATE_ID
    V10.POPULATION_BYTES = POPULATION_BYTES
    V10.POPULATION_SHA256 = POPULATION_SHA256
    V3.CANDIDATE_ID = CANDIDATE_ID
    V3.STAGE_PATH = stage_path
    V3.STAGE_SCHEMA = STAGE_SCHEMA
    V3.stage_argv = stage_argv
    V3.strict_guard_pass = strict_guard_pass
    V10.affinity_samples_pass = affinity_samples_pass

    preflight = dynamic_preflight(plan, files)
    if args.validation_only:
        print(json.dumps(preflight, indent=2, sort_keys=True))
        return 0
    if args.plan_sha256 is None:
        raise RuntimeError("execution requires an explicit frozen --plan-sha256")
    if not preflight["execution_ready"]:
        raise RuntimeError("100M execution preflight failed: " + "; ".join(preflight["blockers"]))

    cpu = int(plan["selected_cpu"])
    os.sched_setaffinity(0, {cpu})
    if os.sched_getaffinity(0) != {cpu}:
        raise RuntimeError("failed to pin 100M coordinator")
    second_preflight = dynamic_preflight(plan, files)
    if second_preflight["blockers"]:
        raise RuntimeError("100M preflight changed after coordinator pin")
    score = int(second_preflight["single_core_score"])

    result_root = Path(plan["paths"]["result_root"])
    scratch_root = Path(plan["paths"]["scratch_root"])
    cgroup_base = Path(plan["paths"]["cgroup_base"])
    lease_path = Path(plan["paths"]["lease"])
    result_root.mkdir(mode=0o700)
    scratch_root.mkdir(mode=0o700)
    transition = result_root / "experiment-lease-transitions.json"
    evidence = result_root / "experiment-lease-evidence.json"
    lease_verification_path = result_root / "experiment-lease-verification.json"
    lease_module = V10.load_module(files["managed_lease"], "cmix_opening100m_managed_lease")
    verifier_module = V10.load_module(
        files["managed_lease_verifier"], "cmix_opening100m_lease_verifier"
    )
    sequence = {
        "candidate_id": CANDIDATE_ID,
        "arms": ["P", "E-A", "E-B", "E-decode"],
        "scope_bytes": POPULATION_BYTES,
        "selected_cpu": cpu,
        "single_core_score": score,
    }
    sequence_sha = hashlib.sha256(V3.canonical_json(sequence)).hexdigest()
    lease = None
    errors: list[str] = []
    stages: dict[str, Any] = {}
    lease_verification: dict[str, Any] | None = None
    population: dict[str, Any] | None = None
    try:
        lease = lease_module.ManagedExclusiveLease.acquire(
            lease_path=lease_path,
            transition_path=transition,
            candidate_id=CANDIDATE_ID,
            command_sha256=sequence_sha,
            runner_sha256=_sha256_file(Path(__file__).resolve(strict=True)),
            guard_path=str(files["resource_guard"]),
            result_path=str(result_root),
            scratch_path=str(scratch_root),
            claim_boundary="opening-100M original-CMIX env8192 reject-only resource gate",
        )
        population = BASE.copy_prefix(
            Path(plan["paths"]["corpus"]).resolve(strict=True),
            scratch_root / "population.bin",
            POPULATION_BYTES,
        )
        if population["sha256"] != POPULATION_SHA256:
            raise RuntimeError("opening-100M population hash mismatch")
        package = artifact(files["original_package"])
        head = artifact(files["head"])
        for arm in ("P", "E-A", "E-B"):
            stages[arm] = V10.run_stage(
                arm=arm,
                result_root=result_root,
                scratch_root=scratch_root,
                cgroup_base=cgroup_base,
                population=population,
                package=package,
                head=head,
                archive=None,
                guard_path=files["resource_guard"],
                lease=lease,
                cpu=cpu,
            )
            if stages[arm].get("pass") is not True:
                raise RuntimeError(f"stage failed: {arm}")
        treatment_archive = stages["E-A"]["stage"]["outputs"]["archive"]
        stages["E-decode"] = V10.run_stage(
            arm="E-decode",
            result_root=result_root,
            scratch_root=scratch_root,
            cgroup_base=cgroup_base,
            population=population,
            package=package,
            head=head,
            archive=treatment_archive,
            guard_path=files["resource_guard"],
            lease=lease,
            cpu=cpu,
        )
        if stages["E-decode"].get("pass") is not True:
            raise RuntimeError("stage failed: E-decode")
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    finally:
        if lease is not None:
            try:
                lease.release(evidence_path=evidence)
            except Exception as exc:
                errors.append(f"lease_release:{type(exc).__name__}:{exc}")

    if transition.is_file() and evidence.is_file():
        verify_args = argparse.Namespace(
            transition_log=transition, terminal_lease=evidence, output=None
        )
        lease_verification, lease_verified = verifier_module.verify(verify_args)
        write_json_new(lease_verification_path, lease_verification)
        terminal_lease = json.loads(evidence.read_text(encoding="utf-8"))
        if not (
            lease_verified
            and lease_verification.get("candidate_id") == CANDIDATE_ID
            and lease_verification.get("computed", {}).get("terminal_events") == 1
            and lease_verification.get("computed", {}).get("activations") == 0
            and terminal_lease.get("command_sha256") == sequence_sha
            and terminal_lease.get("runner_sha256") == _sha256_file(Path(__file__))
            and terminal_lease.get("signal_authority") is False
        ):
            errors.append("outer_lease_evidence_verification_failed")
    else:
        errors.append("outer_lease_evidence_incomplete")
    if lease_path.exists() or lease_path.with_name(f"{lease_path.name}.lock").exists():
        errors.append("outer_lease_namespace_not_clean")

    payloads = [output(stages, arm, "payload") for arm in ("P", "E-A", "E-B")]
    archives = [output(stages, arm, "archive") for arm in ("P", "E-A", "E-B")]
    restored = output(stages, "E-decode", "restored")
    identity = {
        "three_payloads_present": all(
            isinstance(item, dict) and item.get("bytes", 0) > 0 for item in payloads
        ),
        "three_archives_present": all(
            isinstance(item, dict) and item.get("bytes", 0) > 0 for item in archives
        ),
        "control_treatment_payload_identity": all(
            same_artifact(payloads[0], item) for item in payloads[1:]
        ),
        "control_treatment_archive_identity": all(
            same_artifact(archives[0], item) for item in archives[1:]
        ),
        "treatment_repeat_payload_identity": same_artifact(payloads[1], payloads[2]),
        "treatment_repeat_archive_identity": same_artifact(archives[1], archives[2]),
        "exact_inverse": same_artifact(restored, population),
    }
    if not all(identity.values()):
        errors.append("archive_or_inverse_identity_failed")

    guard_peaks = {
        arm: stages.get(arm, {}).get("guard", {}).get("peaks", {})
        for arm in ("P", "E-A", "E-B", "E-decode")
    }
    strict_resource_pass = bool(
        len(stages) == 4
        and all(stage.get("pass") is True for stage in stages.values())
        and all(
            isinstance(peaks.get("max_sampled_tree_rss_kib"), int)
            and peaks["max_sampled_tree_rss_kib"] < MEMORY_LIMIT_KIB
            and isinstance(peaks.get("cgroup_memory_peak_bytes"), int)
            and peaks["cgroup_memory_peak_bytes"] < MEMORY_MAX_BYTES
            and peaks.get("max_sampled_scratch_logical_bytes", DISK_LIMIT_BYTES)
            < DISK_LIMIT_BYTES
            and peaks.get("max_sampled_scratch_allocated_bytes", DISK_LIMIT_BYTES)
            < DISK_LIMIT_BYTES
            for peaks in guard_peaks.values()
        )
    )
    treatment_engineering_pass = all(
        guard_peaks[arm].get("max_sampled_tree_rss_kib", ENGINEERING_TREE_RSS_KIB)
        < ENGINEERING_TREE_RSS_KIB
        for arm in ("E-A", "E-B")
    )
    trigger_crossed = all(
        guard_peaks[arm].get("max_observed_process_vmhwm_kib", 0) >= PPM_TRIGGER_KIB
        for arm in ("E-A", "E-B")
    )
    if not strict_resource_pass:
        errors.append("strict_resource_gate_failed")
    if not treatment_engineering_pass:
        errors.append("treatment_engineering_headroom_failed")
    if not trigger_crossed:
        errors.append("ppm_trigger_not_observed_at_opening100m")

    executions = {
        arm: stages.get(arm, {}).get("stage", {}).get("execution", {})
        for arm in ("P", "E-A", "E-B", "E-decode")
    }
    comparative_rows = {}
    comparative_complete = True
    for arm in ("P", "E-A", "E-B"):
        execution = executions[arm]
        totals = execution.get("process_tree_totals", {})
        raw_io = execution.get("raw_sum_of_sampled_process_io_counters", {})
        ppm = execution.get("ppm_residency", {})
        row = {
            "tree_rss_peak_kib": guard_peaks[arm].get("max_sampled_tree_rss_kib"),
            "cgroup_peak_bytes": guard_peaks[arm].get("cgroup_memory_peak_bytes"),
            "minor_faults_sampled": totals.get("minor_faults"),
            "major_faults_sampled": totals.get("major_faults"),
            "raw_read_bytes_counter_sum": raw_io.get("read_bytes"),
            "raw_write_bytes_counter_sum": raw_io.get("write_bytes"),
            "ppm_observation_count": ppm.get("observation_count"),
            "ppm_minimum_rss_kib": ppm.get("minimum_rss_kib"),
            "ppm_maximum_rss_kib": ppm.get("maximum_rss_kib"),
            "ppm_observed_drop_count": ppm.get("observed_drop_count"),
            "ppm_observed_refault_growth_count": ppm.get("observed_refault_growth_count"),
            "ppm_events_truncated": ppm.get("events_truncated"),
        }
        comparative_rows[arm] = row
        comparative_complete = comparative_complete and all(
            isinstance(row[name], int)
            for name in (
                "tree_rss_peak_kib",
                "cgroup_peak_bytes",
                "minor_faults_sampled",
                "major_faults_sampled",
                "raw_read_bytes_counter_sum",
                "raw_write_bytes_counter_sum",
                "ppm_observation_count",
            )
        )
    if not comparative_complete:
        errors.append("comparative_residency_fault_io_telemetry_incomplete")
    residency_effect_observed = bool(
        comparative_complete
        and (
            comparative_rows["E-A"]["tree_rss_peak_kib"]
            < comparative_rows["P"]["tree_rss_peak_kib"]
            or (
                isinstance(comparative_rows["E-A"]["ppm_maximum_rss_kib"], int)
                and isinstance(comparative_rows["P"]["ppm_maximum_rss_kib"], int)
                and comparative_rows["E-A"]["ppm_maximum_rss_kib"]
                < comparative_rows["P"]["ppm_maximum_rss_kib"]
            )
        )
    )

    elapsed = {
        arm: stages.get(arm, {}).get("guard", {}).get("elapsed_s")
        for arm in ("P", "E-A", "E-B", "E-decode")
    }
    treatment_encode_elapsed = (
        max(elapsed["E-A"], elapsed["E-B"])
        if isinstance(elapsed["E-A"], (int, float))
        and isinstance(elapsed["E-B"], (int, float))
        else None
    )
    decode_elapsed = elapsed["E-decode"]
    scale = CANONICAL_BYTES / POPULATION_BYTES
    encode_projection = (
        treatment_encode_elapsed * scale * RUNTIME_RESERVE
        if treatment_encode_elapsed is not None
        else None
    )
    decode_projection = (
        decode_elapsed * scale * RUNTIME_RESERVE
        if isinstance(decode_elapsed, (int, float))
        else None
    )
    phase_limit = WALL_TIME_NUMERATOR / score
    runtime_projection_pass = bool(
        isinstance(encode_projection, float)
        and isinstance(decode_projection, float)
        and encode_projection < phase_limit
        and decode_projection < phase_limit
    )
    if not runtime_projection_pass:
        errors.append("reserved_runtime_projection_failed")

    archive_bytes = archives[1].get("bytes", 0) if isinstance(archives[1], dict) else 0
    package_entries = {
        "original_compressor": files["original_package"].stat().st_size,
        "neural_head": files["head"].stat().st_size,
        "opening100m_archive_diagnostic": archive_bytes,
        "compression_command_bytes": len(COUNTED_COMPRESS_COMMAND.encode("ascii")),
        "decompression_command_bytes": len(COUNTED_DECOMPRESS_COMMAND.encode("ascii")),
    }
    package_accounting_pass = bool(
        package_entries["compression_command_bytes"] == 69
        and package_entries["decompression_command_bytes"] == 31
        and all(value > 0 for value in package_entries.values())
    )
    if not package_accounting_pass:
        errors.append("package_accounting_failed")

    manifest, manifest_pass = result_manifest(result_root)
    if not manifest_pass:
        errors.append("output_manifest_incomplete")
    pre_cleanup_pass = not errors
    if pre_cleanup_pass:
        shutil.rmtree(scratch_root)
    cleanup_pass = not scratch_root.exists() if pre_cleanup_pass else scratch_root.exists()
    if not cleanup_pass:
        errors.append("scratch_cleanup_contract_failed")
    terminal_pass = bool(pre_cleanup_pass and cleanup_pass and not errors)
    decision = {
        "$schema": DECISION_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "terminal": True,
        "terminal_pass": terminal_pass,
        "claim_authority": "opening100m_reject_only_resource" if terminal_pass else "none",
        "objective_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
        "external_derived_lane": True,
        "plan": artifact(plan_path),
        "scope_bytes": POPULATION_BYTES,
        "population": population,
        "selected_cpu": cpu,
        "coordinator_affinity": sorted(os.sched_getaffinity(0)),
        "runtime_authority": second_preflight["runtime_authority"],
        "preflight": preflight,
        "post_pin_preflight": second_preflight,
        "identity": identity,
        "stages": stages,
        "resources": {
            "strict_resource_pass": strict_resource_pass,
            "treatment_engineering_peak_pass": treatment_engineering_pass,
            "ppm_trigger_crossed_both_treatment_repeats": trigger_crossed,
            "engineering_tree_rss_limit_kib": ENGINEERING_TREE_RSS_KIB,
            "official_tree_rss_limit_kib": MEMORY_LIMIT_KIB,
            "hard_cgroup_limit_bytes": MEMORY_MAX_BYTES,
            "zero_swap_required": True,
            "guard_peaks": guard_peaks,
        },
        "comparative_telemetry": {
            "complete": comparative_complete,
            "rows": comparative_rows,
            "residency_effect_observed": residency_effect_observed,
            "residency_effect_status": (
                "observed" if residency_effect_observed else "not_observed_inconclusive"
            ),
            "observed_drop_absence_status": "inconclusive_not_falsification",
            "io_counter_scope": "Raw sampled per-process counter sums are diagnostic and may overlap; they are not unique physical IO totals.",
        },
        "runtime_projection": {
            "reject_only": True,
            "single_core_score": score,
            "phase_limit_seconds": phase_limit,
            "reserve_ratio": RUNTIME_RESERVE,
            "scale_factor": scale,
            "elapsed_seconds": elapsed,
            "conservative_treatment_encode_elapsed_seconds": treatment_encode_elapsed,
            "reserved_full_encode_projection_seconds": encode_projection,
            "reserved_full_decode_projection_seconds": decode_projection,
            "pass": runtime_projection_pass,
            "full_corpus_runtime_qualified": False,
        },
        "package_accounting": {
            "entries": package_entries,
            "opening100m_diagnostic_counted_bytes": sum(package_entries.values()),
            "pass": package_accounting_pass,
            "full_corpus_score_authority": False,
        },
        "outer_lease_verification": lease_verification,
        "output_manifest": {
            "policy": "complete-result-artifacts-decision-self-excluded-v1",
            "artifacts": manifest,
            "complete": manifest_pass,
        },
        "cleanup": {
            "scratch_removed_on_pass": terminal_pass and not scratch_root.exists(),
            "scratch_preserved_on_failure": not terminal_pass and scratch_root.exists(),
            "lease_namespace_clear": not lease_path.exists()
            and not lease_path.with_name(f"{lease_path.name}.lock").exists(),
        },
        "errors": list(dict.fromkeys(errors)),
        "promotion_authorized": False,
        "full1g_resource_successor_authorized": terminal_pass,
        "claim_boundary": "Exact opening-100M identity and reject-only resource evidence for an external-derived original-CMIX env override; never Gamma-authored score credit or full-corpus qualification.",
    }
    write_json_new(result_root / "decision.json", decision)
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0 if terminal_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
