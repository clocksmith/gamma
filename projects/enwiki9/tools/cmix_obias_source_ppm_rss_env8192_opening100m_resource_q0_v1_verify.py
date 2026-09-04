#!/usr/bin/env python3
"""Independently verify the opening-100M CMIX env8192 resource gate."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import stat
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
PLAN_SCHEMA = "gamma.enwiki9.cmix-env8192-opening100m-resource-plan.v1"
DECISION_SCHEMA = "gamma.enwiki9.cmix-env8192-opening100m-resource-decision.v1"
VERIFY_SCHEMA = "gamma.enwiki9.cmix-env8192-opening100m-resource-verification.v1"
CANDIDATE = "cmix_obias_source_ppm_rss_env8192_opening100m_resource_q0_v1"
STAGE_SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-opening100m-stage.resource-q0-v1"
GUARD_SCHEMA = "gamma.enwiki9.resource-guard-receipt.v3"
CALIBRATION_SCHEMA = "gamma.enwiki9.geekbench5-tryout-calibration.v1"
CALIBRATION_VERIFY_SCHEMA = "gamma.enwiki9.geekbench5-tryout-calibration-verification.v1"
POPULATION_BYTES = 100_000_000
POPULATION_SHA256 = "2b49720ec4d78c3c9fabaee6e4179a5e997302b3a70029f30f2d582218c024a8"
MEMORY_LIMIT_KIB = 9_765_625
MEMORY_MAX_BYTES = 10_000_000_000
ENGINEERING_TREE_RSS_KIB = 9_000_000
PPM_TRIGGER_KIB = 8_388_608
DISK_LIMIT_BYTES = 100_000_000_000
WALL_TIME_NUMERATOR = 252_000_000
RUNTIME_RESERVE = 1.25
COUNTED_COMPRESS_COMMAND = (
    "CMIX_PPM_RSS_MB=8192 KH_BITLSTM32=head.blob ./cmix -e enwik9 out.cmix"
)
COUNTED_DECOMPRESS_COMMAND = "CMIX_PPM_RSS_MB=8192 ./archive9"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(16 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


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
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


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
    if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
        raise RuntimeError(f"{label}: binding mismatch")
    return path


def write_new(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        cursor = 0
        while cursor < len(payload):
            written = os.write(descriptor, payload[cursor:])
            if written <= 0:
                raise OSError(f"short write: {path}")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def same_artifact(left: Any, right: Any) -> bool:
    return bool(
        isinstance(left, dict)
        and isinstance(right, dict)
        and left.get("bytes") == right.get("bytes")
        and left.get("sha256") == right.get("sha256")
    )


def command_sha256(command: list[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(item) for item in command)).hexdigest()


def json_lines(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="ascii").splitlines():
        value = json.loads(line)
        if not isinstance(value, dict):
            raise RuntimeError(f"non-object JSON line: {path}")
        records.append(value)
    return records


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


def stage_contract_pass(
    *,
    plan: dict[str, Any],
    files: dict[str, Path],
    result_root: Path,
    arm: str,
    row: Any,
    population: Any,
    treatment_archive: Any,
) -> bool:
    """Recompute a stage contract without trusting coordinator pass flags."""
    try:
        if not isinstance(row, dict):
            return False
        slug = arm.lower().replace("-", "_")
        mode = "decode" if arm == "E-decode" else "encode"
        ppm = "default" if arm == "P" else "8192"
        cpu = int(plan["selected_cpu"])
        stage_result = result_root / slug
        stage_work = Path(plan["paths"]["scratch_root"]) / slug
        marker = stage_result / "phase-markers.jsonl"
        cgroup_base = Path(plan["paths"]["cgroup_base"])
        cgroup = cgroup_base.with_name(f"{cgroup_base.name}-{slug}")
        stage_command = [
            str(files["python"]),
            str(files["stage"]),
            "--mode",
            mode,
            "--arm",
            arm,
            "--work-root",
            str(stage_work),
            "--result-root",
            str(stage_result),
            "--receipt",
            str(stage_result / "stage.json"),
            "--ppm-rss-mb",
            ppm,
        ]
        if mode == "encode":
            stage_command.extend(
                [
                    "--input",
                    str(Path(plan["paths"]["scratch_root"]) / "population.bin"),
                    "--package",
                    str(files["original_package"]),
                    "--head",
                    str(files["head"]),
                ]
            )
        else:
            stage_command.extend(
                [
                    "--archive",
                    str(result_root / "e_a/archive9"),
                    "--archive-bytes",
                    str(treatment_archive["bytes"]),
                    "--archive-sha256",
                    treatment_archive["sha256"],
                ]
            )
        guard_command = [
            str(files["python"]),
            str(files["resource_guard"]),
            "--limit-kib",
            str(MEMORY_LIMIT_KIB),
            "--limit-mode",
            "tree",
            "--official-decimal-limit-kib",
            str(MEMORY_LIMIT_KIB),
            "--sample-interval",
            "0.5",
            "--cgroup-path",
            str(cgroup),
            "--cgroup-memory-max-bytes",
            str(MEMORY_MAX_BYTES),
            "--scratch-path",
            str(Path(plan["paths"]["scratch_root"])),
            "--scratch-path",
            str(result_root),
            "--temporary-disk-limit-bytes",
            str(DISK_LIMIT_BYTES),
            "--phase-marker-path",
            str(marker),
            "--max-logical-cpus",
            "1",
            "--guard-json",
            str(stage_result / "guard.json"),
            "--label",
            f"{CANDIDATE}-{slug}",
            "--phase",
            "identity",
            "--",
            *stage_command,
        ]
        if not (
            row.get("arm") == arm
            and row.get("mode") == mode
            and row.get("selected_cpu") == cpu
            and row.get("coordinator_affinity") == [cpu]
            and row.get("guard_initial_affinity") == [cpu]
            and row.get("command") == stage_command
            and row.get("guard_argv") == guard_command
            and row.get("returncode") == 0
            and row.get("errors") == []
            and row.get("pass") is True
        ):
            return False

        guard = row.get("guard")
        stage = row.get("stage")
        if not isinstance(guard, dict) or not isinstance(stage, dict):
            return False
        cgroup_value = guard.get("cgroup", {})
        measurements = guard.get("measurements", {})
        guards = guard.get("guards", {})
        event_delta = guard.get("cgroup_events", {}).get("delta", {})
        peaks = guard.get("peaks", {})
        marker_source = json_lines(marker)
        marker_pairs = [(item.get("phase"), item.get("event")) for item in marker_source]
        expected_phase = f"opening100m_{slug}"
        retained_pairs = [
            (item.get("phase"), item.get("event"))
            for item in guard.get("phase_markers", [])
            if isinstance(item, dict)
        ]
        if not (
            guard.get("schema") == GUARD_SCHEMA
            and guard.get("status") == "complete"
            and guard.get("returncode") == 0
            and guard.get("label") == f"{CANDIDATE}-{slug}"
            and guard.get("phase") == "identity"
            and guard.get("command") == stage_command
            and guard.get("command_sha256") == command_sha256(stage_command)
            and guard.get("limit_kib") == MEMORY_LIMIT_KIB
            and guard.get("limit_mode") == "tree"
            and guard.get("official_decimal_limit_kib") == MEMORY_LIMIT_KIB
            and guard.get("temporary_disk_limit_bytes") == DISK_LIMIT_BYTES
            and guard.get("max_logical_cpus") == 1
            and guard.get("wall_time_limit_seconds") is None
            and guard.get("geekbench5_single_core_score") is None
            and guard.get("scratch_paths")
            == [str(Path(plan["paths"]["scratch_root"])), str(result_root)]
            and guard.get("phase_marker_path") == str(marker)
            and isinstance(measurements, dict)
            and bool(measurements)
            and all(value is True for value in measurements.values())
            and isinstance(guards, dict)
            and bool(guards)
            and all(value is False for value in guards.values())
            and event_delta.get("max", 0) == 0
            and event_delta.get("oom", 0) == 0
            and event_delta.get("oom_kill", 0) == 0
            and marker_pairs == [(expected_phase, "start"), (expected_phase, "end")]
            and retained_pairs == marker_pairs
            and cgroup_value.get("path") == str(cgroup)
            and cgroup_value.get("joined_before_exec") is True
            and cgroup_value.get("requested_memory_max_bytes") == MEMORY_MAX_BYTES
            and cgroup_value.get("memory_swap_max_bytes") == 0
            and isinstance(cgroup_value.get("memory_max_bytes"), int)
            and cgroup_value["memory_max_bytes"] <= MEMORY_MAX_BYTES
            and isinstance(peaks.get("max_sampled_tree_rss_kib"), int)
            and peaks["max_sampled_tree_rss_kib"] < MEMORY_LIMIT_KIB
            and isinstance(peaks.get("max_observed_process_vmhwm_kib"), int)
            and peaks["max_observed_process_vmhwm_kib"] < MEMORY_LIMIT_KIB
            and isinstance(peaks.get("cgroup_memory_peak_bytes"), int)
            and peaks["cgroup_memory_peak_bytes"] < MEMORY_MAX_BYTES
            and peaks.get("max_sampled_scratch_logical_bytes", DISK_LIMIT_BYTES)
            < DISK_LIMIT_BYTES
            and peaks.get("max_sampled_scratch_allocated_bytes", DISK_LIMIT_BYTES)
            < DISK_LIMIT_BYTES
            and peaks.get("max_sampled_allowed_cpu_count") == 1
            and affinity_samples_pass(guard, cpu, mode)
            and not cgroup.exists()
            and not cgroup.is_symlink()
        ):
            return False

        execution = stage.get("execution")
        if not isinstance(execution, dict):
            return False
        local_environment = {
            "PATH": "/usr/bin:/bin",
            "GAMMA_RESOURCE_PHASE_MARKERS": str(marker),
        }
        if mode == "encode":
            local_environment["KH_BITLSTM32"] = str(stage_work / "head.blob")
        if ppm == "8192":
            local_environment["CMIX_PPM_RSS_MB"] = "8192"
        expected_execution_argv = (
            [str(stage_work / "archive9")]
            if mode == "decode"
            else [
                str(stage_work / "cmix"),
                "-e",
                str(Path(plan["paths"]["scratch_root"]) / "population.bin"),
                "out.cmix",
            ]
        )
        expected_inputs = (
            {"archive": treatment_archive}
            if mode == "decode"
            else {
                "population": population,
                "package": artifact(files["original_package"]),
                "head": artifact(files["head"]),
            }
        )
        expected_outputs = (
            {"restored": artifact(stage_result / "enwik9_uncompressed")}
            if mode == "decode"
            else {
                "payload": artifact(stage_result / "out.cmix"),
                "archive": artifact(stage_result / "archive9"),
            }
        )
        totals = execution.get("process_tree_totals", {})
        raw_io = execution.get("raw_sum_of_sampled_process_io_counters", {})
        ppm_observation = execution.get("ppm_residency", {})
        if not (
            stage.get("schema") == STAGE_SCHEMA
            and stage.get("scope_bytes") == POPULATION_BYTES
            and stage.get("arm") == arm
            and stage.get("mode") == mode
            and stage.get("ppm_rss_environment")
            == ({} if ppm == "default" else {"CMIX_PPM_RSS_MB": "8192"})
            and stage.get("clean_codec_environment") == local_environment
            and stage.get("inputs") == expected_inputs
            and stage.get("outputs") == expected_outputs
            and stage.get("execution_artifact") == artifact(stage_result / "execution.json")
            and stage.get("exact_decode_filename")
            == ("enwik9_uncompressed" if mode == "decode" else None)
            and stage.get("phase_marker_path") == str(marker)
            and stage.get("stage_pass") is True
            and execution.get("argv") == expected_execution_argv
            and execution.get("returncode") == 0
            and execution.get("measurement_complete") is True
            and execution.get("measurement_errors") == []
            and execution.get("identity_errors") == []
            and isinstance(execution.get("sample_count"), int)
            and execution["sample_count"] > 0
            and isinstance(execution.get("processes"), list)
            and bool(execution["processes"])
            and all(isinstance(totals.get(name), int) for name in ("minor_faults", "major_faults"))
            and all(isinstance(raw_io.get(name), int) for name in ("read_bytes", "write_bytes"))
            and isinstance(ppm_observation.get("observation_count"), int)
            and execution.get("stdout") == artifact(stage_result / "codec.stdout")
            and execution.get("stderr") == artifact(stage_result / "codec.stderr")
        ):
            return False
        return True
    except (KeyError, OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError):
        return False


def check(condition: bool, name: str, checks: dict[str, bool], errors: list[str]) -> None:
    checks[name] = bool(condition)
    if not condition:
        errors.append(name)


def output(stages: dict[str, Any], arm: str, name: str) -> Any:
    stage = stages.get(arm, {}).get("stage")
    return stage.get("outputs", {}).get(name) if isinstance(stage, dict) else None


def expected_paths() -> set[str]:
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
    paths.update(f"e_decode/{name}" for name in common | {"enwik9_uncompressed"})
    paths.update(
        {
            "experiment-lease-transitions.json",
            "experiment-lease-evidence.json",
            "experiment-lease-verification.json",
        }
    )
    return paths


def actual_manifest(result_root: Path, output_path: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(result_root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"result symlink forbidden: {path}")
        if path.is_file() and path.name != "decision.json" and path != output_path:
            record = artifact(path)
            record["path"] = path.relative_to(result_root).as_posix()
            records.append(record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    plan_path, plan = load_json(
        args.plan if args.plan.is_absolute() else PROJECT / args.plan, "100M plan"
    )
    if sha256_file(plan_path) != args.plan_sha256:
        raise RuntimeError("100M plan SHA-256 mismatch")
    if (
        plan.get("$schema") != PLAN_SCHEMA
        or plan.get("candidate_id") != CANDIDATE
        or plan.get("status") != "frozen_blocked_dependencies"
        or plan.get("execution_authorized") is not True
        or plan.get("claim_authority") != "none_until_terminal"
        or plan.get("objective_credit_bytes") != 0
        or plan.get("external_derived_lane") is not True
        or plan.get("scope_bytes") != POPULATION_BYTES
        or plan.get("scope_sha256") != POPULATION_SHA256
        or plan.get("selected_cpu") != 2
    ):
        raise RuntimeError("100M plan identity mismatch")
    expected_artifact_names = {
        "coordinator",
        "verifier",
        "stage",
        "objective",
        "identity_decision",
        "original_package",
        "head",
        "source_archive",
        "ppmd_source",
        "calibration_plan",
        "zombie_safe_telemetry",
        "coordinator_v10",
        "helpers_v3",
        "coordinator_v2",
        "resource_guard",
        "resource_guard_v12",
        "resource_guard_v11",
        "resource_guard_v10",
        "resource_guard_v3",
        "managed_lease",
        "managed_lease_verifier",
        "python",
    }
    if set(plan.get("artifacts", {})) != expected_artifact_names:
        raise RuntimeError("100M plan artifact closure mismatch")
    files = {
        name: verify_binding(record, f"plan artifact {name}")
        for name, record in plan["artifacts"].items()
    }
    if files.get("verifier") != Path(__file__).resolve(strict=True):
        raise RuntimeError("plan does not bind this verifier")
    decision_path, decision = load_json(args.decision, "100M decision")
    if (
        decision.get("$schema") != DECISION_SCHEMA
        or decision.get("candidate_id") != CANDIDATE
    ):
        raise RuntimeError("100M decision identity mismatch")
    result_root = Path(plan["paths"]["result_root"]).resolve(strict=True)
    if decision_path != result_root / "decision.json":
        raise RuntimeError("100M decision is not the frozen result-root decision")
    output_path = args.output.absolute()
    if output_path.parent != result_root or output_path.exists() or output_path.is_symlink():
        raise RuntimeError("verification output must be a new direct result-root child")

    checks: dict[str, bool] = {}
    errors: list[str] = []
    check(decision.get("plan") == artifact(plan_path), "decision_plan_binding", checks, errors)
    check(
        decision.get("terminal") is True
        and decision.get("objective_credit_bytes") == 0
        and decision.get("gamma_score_credit_bytes") == 0
        and decision.get("external_derived_lane") is True
        and decision.get("promotion_authorized") is False,
        "decision_claim_boundary",
        checks,
        errors,
    )
    cpu = int(plan["selected_cpu"])
    check(
        decision.get("selected_cpu") == cpu
        and decision.get("coordinator_affinity") == [cpu],
        "decision_cpu_binding",
        checks,
        errors,
    )
    preflight = decision.get("preflight", {})
    post_pin = decision.get("post_pin_preflight", {})
    preflight_pass = bool(
        isinstance(preflight, dict)
        and isinstance(post_pin, dict)
        and preflight.get("execution_ready") is True
        and post_pin.get("execution_ready") is True
        and preflight.get("blockers") == []
        and post_pin.get("blockers") == []
        and preflight.get("adaptive_running") == []
        and post_pin.get("adaptive_running") == []
        and preflight.get("selected_cpu") == cpu
        and post_pin.get("selected_cpu") == cpu
        and cpu in preflight.get("caller_affinity", [])
        and post_pin.get("caller_affinity") == [cpu]
        and preflight.get("bound_artifact_count") == len(files)
        and post_pin.get("bound_artifact_count") == len(files)
        and preflight.get("runtime_authority") == decision.get("runtime_authority")
        and post_pin.get("runtime_authority") == decision.get("runtime_authority")
    )
    check(preflight_pass, "retained_preflights", checks, errors)
    check(decision.get("scope_bytes") == POPULATION_BYTES, "scope_bytes", checks, errors)
    population = decision.get("population", {})
    check(
        population.get("bytes") == POPULATION_BYTES
        and population.get("sha256") == POPULATION_SHA256,
        "population_identity",
        checks,
        errors,
    )

    stages = decision.get("stages")
    check(
        isinstance(stages, dict) and set(stages) == {"P", "E-A", "E-B", "E-decode"},
        "stage_set",
        checks,
        errors,
    )
    if not isinstance(stages, dict):
        stages = {}
    all_stage_files_match = True
    for arm, slug in (("P", "p"), ("E-A", "e_a"), ("E-B", "e_b"), ("E-decode", "e_decode")):
        stage_row = stages.get(arm, {})
        for name in ("guard", "stage"):
            expected_path = result_root / slug / f"{name}.json"
            try:
                _, retained = load_json(expected_path, f"{arm} {name}")
                all_stage_files_match = all_stage_files_match and retained == stage_row.get(name)
            except Exception:
                all_stage_files_match = False
        stage = stage_row.get("stage", {})
        execution = stage.get("execution", {}) if isinstance(stage, dict) else {}
        try:
            _, retained_execution = load_json(
                result_root / slug / "execution.json", f"{arm} execution"
            )
            all_stage_files_match = all_stage_files_match and retained_execution == execution
            all_stage_files_match = all_stage_files_match and stage.get(
                "execution_artifact"
            ) == artifact(result_root / slug / "execution.json")
            verify_binding(execution.get("stdout"), f"{arm} codec stdout")
            verify_binding(execution.get("stderr"), f"{arm} codec stderr")
        except Exception:
            all_stage_files_match = False
    check(all_stage_files_match, "retained_stage_guard_execution_files", checks, errors)

    payloads = [output(stages, arm, "payload") for arm in ("P", "E-A", "E-B")]
    archives = [output(stages, arm, "archive") for arm in ("P", "E-A", "E-B")]
    restored = output(stages, "E-decode", "restored")
    outputs_match_files = True
    for index, arm in enumerate(("P", "E-A", "E-B")):
        slug = arm.lower().replace("-", "_")
        try:
            outputs_match_files = outputs_match_files and payloads[index] == artifact(
                result_root / slug / "out.cmix"
            )
            outputs_match_files = outputs_match_files and archives[index] == artifact(
                result_root / slug / "archive9"
            )
        except Exception:
            outputs_match_files = False
    try:
        outputs_match_files = outputs_match_files and restored == artifact(
            result_root / "e_decode/enwik9_uncompressed"
        )
    except Exception:
        outputs_match_files = False
    check(outputs_match_files, "retained_codec_outputs", checks, errors)
    stage_contracts = {
        arm: stage_contract_pass(
            plan=plan,
            files=files,
            result_root=result_root,
            arm=arm,
            row=stages.get(arm),
            population=population,
            treatment_archive=archives[1],
        )
        for arm in ("P", "E-A", "E-B", "E-decode")
    }
    check(all(stage_contracts.values()), "independent_stage_contracts", checks, errors)
    recomputed_identity = {
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
        "exact_inverse": bool(
            isinstance(restored, dict)
            and restored.get("bytes") == POPULATION_BYTES
            and restored.get("sha256") == POPULATION_SHA256
        ),
    }
    check(decision.get("identity") == recomputed_identity, "identity_recomputed", checks, errors)
    check(all(recomputed_identity.values()), "identity_pass", checks, errors)

    guard_peaks = {
        arm: stages.get(arm, {}).get("guard", {}).get("peaks", {})
        for arm in ("P", "E-A", "E-B", "E-decode")
    }
    strict_resource = bool(
        all(stages.get(arm, {}).get("pass") is True for arm in guard_peaks)
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
    engineering = all(
        guard_peaks[arm].get("max_sampled_tree_rss_kib", ENGINEERING_TREE_RSS_KIB)
        < ENGINEERING_TREE_RSS_KIB
        for arm in ("E-A", "E-B")
    )
    trigger = all(
        guard_peaks[arm].get("max_observed_process_vmhwm_kib", 0) >= PPM_TRIGGER_KIB
        for arm in ("E-A", "E-B")
    )
    resource = decision.get("resources", {})
    check(resource.get("guard_peaks") == guard_peaks, "resource_peak_binding", checks, errors)
    check(resource.get("strict_resource_pass") is strict_resource, "strict_resource", checks, errors)
    check(
        resource.get("treatment_engineering_peak_pass") is engineering,
        "engineering_headroom",
        checks,
        errors,
    )
    check(
        resource.get("engineering_tree_rss_limit_kib") == ENGINEERING_TREE_RSS_KIB
        and resource.get("official_tree_rss_limit_kib") == MEMORY_LIMIT_KIB
        and resource.get("hard_cgroup_limit_bytes") == MEMORY_MAX_BYTES
        and resource.get("zero_swap_required") is True,
        "resource_threshold_binding",
        checks,
        errors,
    )
    check(
        resource.get("ppm_trigger_crossed_both_treatment_repeats") is trigger,
        "ppm_trigger",
        checks,
        errors,
    )
    comparative_rows: dict[str, dict[str, Any]] = {}
    comparative_complete = True
    for arm in ("P", "E-A", "E-B"):
        execution = stages.get(arm, {}).get("stage", {}).get("execution", {})
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
    residency_effect = bool(
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
    expected_comparative = {
        "complete": comparative_complete,
        "rows": comparative_rows,
        "residency_effect_observed": residency_effect,
        "residency_effect_status": (
            "observed" if residency_effect else "not_observed_inconclusive"
        ),
        "observed_drop_absence_status": "inconclusive_not_falsification",
        "io_counter_scope": "Raw sampled per-process counter sums are diagnostic and may overlap; they are not unique physical IO totals.",
    }
    check(
        comparative_complete and decision.get("comparative_telemetry") == expected_comparative,
        "comparative_telemetry",
        checks,
        errors,
    )

    runtime_path, runtime_receipt = load_json(
        Path(plan["runtime_authority"]["producer_receipt_path"]), "runtime authority"
    )
    verification_path, runtime_verification = load_json(
        Path(plan["runtime_authority"]["verification_path"]), "runtime verification"
    )
    score = runtime_receipt.get("selected_single_core_score")
    runtime_authority_pass = bool(
        runtime_receipt.get("$schema") == CALIBRATION_SCHEMA
        and runtime_receipt.get("candidate_id")
        == plan["runtime_authority"]["candidate_id"]
        and runtime_receipt.get("terminal_authority") is True
        and runtime_receipt.get("plan") == artifact(files["calibration_plan"])
        and isinstance(score, int)
        and score > 0
        and runtime_verification.get("$schema") == CALIBRATION_VERIFY_SCHEMA
        and runtime_verification.get("candidate_id")
        == plan["runtime_authority"]["candidate_id"]
        and runtime_verification.get("authority_verified") is True
        and runtime_verification.get("evidence_valid") is True
        and runtime_verification.get("errors") == []
        and runtime_verification.get("source_receipt") == artifact(runtime_path)
        and runtime_verification.get("selected_single_core_score") == score
        and decision.get("runtime_authority", {}).get("producer_receipt")
        == artifact(runtime_path)
        and decision.get("runtime_authority", {}).get("independent_verification")
        == artifact(verification_path)
        and decision.get("runtime_authority", {}).get("single_core_score") == score
    )
    check(runtime_authority_pass, "runtime_authority", checks, errors)
    elapsed = {
        arm: stages.get(arm, {}).get("guard", {}).get("elapsed_s")
        for arm in ("P", "E-A", "E-B", "E-decode")
    }
    treatment_elapsed = (
        max(elapsed["E-A"], elapsed["E-B"])
        if isinstance(elapsed["E-A"], (int, float))
        and isinstance(elapsed["E-B"], (int, float))
        else None
    )
    encode_projection = treatment_elapsed * 10 * RUNTIME_RESERVE if treatment_elapsed else None
    decode_projection = (
        elapsed["E-decode"] * 10 * RUNTIME_RESERVE
        if isinstance(elapsed["E-decode"], (int, float))
        else None
    )
    phase_limit = WALL_TIME_NUMERATOR / score if isinstance(score, int) and score > 0 else None
    projection_pass = bool(
        phase_limit is not None
        and encode_projection is not None
        and decode_projection is not None
        and encode_projection < phase_limit
        and decode_projection < phase_limit
    )
    runtime = decision.get("runtime_projection", {})
    check(runtime.get("elapsed_seconds") == elapsed, "runtime_elapsed", checks, errors)
    check(
        runtime.get("conservative_treatment_encode_elapsed_seconds") == treatment_elapsed,
        "runtime_encode_selection",
        checks,
        errors,
    )
    numeric_projection_binding = bool(
        isinstance(phase_limit, (int, float))
        and isinstance(runtime.get("phase_limit_seconds"), (int, float))
        and math.isclose(runtime["phase_limit_seconds"], phase_limit)
        and isinstance(encode_projection, (int, float))
        and isinstance(runtime.get("reserved_full_encode_projection_seconds"), (int, float))
        and math.isclose(
            runtime["reserved_full_encode_projection_seconds"], encode_projection
        )
        and isinstance(decode_projection, (int, float))
        and isinstance(runtime.get("reserved_full_decode_projection_seconds"), (int, float))
        and math.isclose(
            runtime["reserved_full_decode_projection_seconds"], decode_projection
        )
    )
    check(numeric_projection_binding, "runtime_numeric_projection", checks, errors)
    check(
        runtime.get("single_core_score") == score
        and runtime.get("reserve_ratio") == RUNTIME_RESERVE
        and runtime.get("scale_factor") == 10.0
        and runtime.get("reject_only") is True
        and runtime.get("full_corpus_runtime_qualified") is False
        and runtime.get("pass") is projection_pass,
        "runtime_projection",
        checks,
        errors,
    )

    package = decision.get("package_accounting", {})
    entries = package.get("entries", {})
    expected_archive_bytes = archives[1].get("bytes", 0) if isinstance(archives[1], dict) else 0
    package_pass = bool(
        entries.get("original_compressor") == files["original_package"].stat().st_size
        and entries.get("neural_head") == files["head"].stat().st_size
        and entries.get("opening100m_archive_diagnostic") == expected_archive_bytes
        and entries.get("compression_command_bytes")
        == len(COUNTED_COMPRESS_COMMAND.encode("ascii"))
        and entries.get("decompression_command_bytes")
        == len(COUNTED_DECOMPRESS_COMMAND.encode("ascii"))
        and all(isinstance(value, int) and value > 0 for value in entries.values())
        and package.get("opening100m_diagnostic_counted_bytes")
        == sum(value for value in entries.values() if isinstance(value, int))
        and package.get("full_corpus_score_authority") is False
    )
    check(package_pass and package.get("pass") is True, "package_accounting", checks, errors)

    manifest = actual_manifest(result_root, output_path)
    manifest_paths = {record["path"] for record in manifest}
    check(manifest_paths == expected_paths(), "actual_manifest_paths", checks, errors)
    check(
        decision.get("output_manifest", {}).get("artifacts") == manifest
        and decision.get("output_manifest", {}).get("complete") is True,
        "decision_manifest_binding",
        checks,
        errors,
    )

    lease_verifier_path = files["managed_lease_verifier"]
    specification = importlib.util.spec_from_file_location(
        "opening100m_independent_lease_verifier", lease_verifier_path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load bound managed lease verifier")
    lease_verifier = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(lease_verifier)
    transition = result_root / "experiment-lease-transitions.json"
    terminal_lease = result_root / "experiment-lease-evidence.json"
    lease_args = argparse.Namespace(
        transition_log=transition, terminal_lease=terminal_lease, output=None
    )
    independent_lease, lease_ok = lease_verifier.verify(lease_args)
    _, stored_lease = load_json(
        result_root / "experiment-lease-verification.json", "stored lease verification"
    )
    check(
        lease_ok
        and independent_lease == stored_lease
        and decision.get("outer_lease_verification") == stored_lease,
        "outer_lease_verification",
        checks,
        errors,
    )
    check(
        stored_lease.get("verified") is True
        and stored_lease.get("errors") == []
        and stored_lease.get("candidate_id") == CANDIDATE
        and stored_lease.get("computed", {}).get("terminal_events") == 1
        and stored_lease.get("computed", {}).get("activations") == 0
        and stored_lease.get("computed", {}).get("terminal_signal_authority") is False,
        "outer_lease_terminal_semantics",
        checks,
        errors,
    )
    lease_path = Path(plan["paths"]["lease"])
    check(
        not lease_path.exists() and not lease_path.with_name(f"{lease_path.name}.lock").exists(),
        "lease_namespace_released",
        checks,
        errors,
    )
    check(not Path(plan["paths"]["scratch_root"]).exists(), "scratch_removed", checks, errors)
    cleanup = decision.get("cleanup", {})
    check(
        cleanup.get("scratch_removed_on_pass") is True
        and cleanup.get("scratch_preserved_on_failure") is False
        and cleanup.get("lease_namespace_clear") is True,
        "decision_cleanup_binding",
        checks,
        errors,
    )

    authority = bool(
        not errors
        and all(recomputed_identity.values())
        and strict_resource
        and engineering
        and trigger
        and runtime_authority_pass
        and projection_pass
        and package_pass
        and lease_ok
    )
    check(decision.get("errors") == [], "decision_errors_empty", checks, errors)
    check(decision.get("terminal_pass") is authority, "terminal_pass_consistency", checks, errors)
    check(
        decision.get("full1g_resource_successor_authorized") is authority,
        "full1g_successor_consistency",
        checks,
        errors,
    )
    verification = {
        "$schema": VERIFY_SCHEMA,
        "candidate_id": CANDIDATE,
        "source_decision": artifact(decision_path),
        "plan": artifact(plan_path),
        "checks": checks,
        "errors": errors,
        "evidence_valid": not errors,
        "authority_verified": authority and not errors,
        "full1g_resource_successor_authorized": authority and not errors,
        "objective_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
        "claim_boundary": "Independent opening-100M external-derived identity and reject-only resource verification; no full-corpus qualification or Gamma-authored score credit.",
    }
    write_new(output_path, verification)
    print(json.dumps(artifact(output_path), sort_keys=True))
    return 0 if verification["authority_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
