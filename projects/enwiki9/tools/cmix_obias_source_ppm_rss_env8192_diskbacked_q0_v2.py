#!/usr/bin/env python3
"""Disk-backed exact 1M/100M envelope for CMIX_PPM_RSS_MB=8192."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
from types import ModuleType
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v2"
FROZEN_PATCHED_SUCCESSOR = "cmix_obias_memory_safe_parent_q0_v1"
SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-diskbacked.v2"
STAGE_SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-diskbacked-stage.v1"
GUARD_SCHEMA = "gamma.enwiki9.resource-guard-receipt.v3"
WITNESS_SCHEMA = "gamma.enwiki9.cmix-obias-probability-state-witness.v1"
CANONICAL_BYTES = 1_000_000_000
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
GATES = {
    1_000_000: "369b688978f649681136198fb96db14c1616756260c55fb4b65e9bc049552cad",
    100_000_000: "2b49720ec4d78c3c9fabaee6e4179a5e997302b3a70029f30f2d582218c024a8",
}
MEMORY_LIMIT_KIB = 9_765_625
MEMORY_MAX_BYTES = 10_000_000_000
DISK_LIMIT_BYTES = 100_000_000_000
WALL_TIME_NUMERATOR = 252_000_000
OPTION_TEXT = b"CMIX_PPM_RSS_MB=8192"
COUNTED_COMPRESS_COMMAND = (
    "CMIX_PPM_RSS_MB=8192 KH_BITLSTM32=head.blob ./cmix -e enwik9 out.cmix"
)
COUNTED_DECOMPRESS_COMMAND = "CMIX_PPM_RSS_MB=8192 ./archive9"
RUNTIME_PROJECTION_RESERVE_RATIO = 1.25
EXPECTED = {
    "original_1m_receipt": (
        "results/cmix_obias_source_1m_roundtrip_qm3_v1/decision.json",
        45242,
        "c7c70a8349f42169fd07d782a9439cedc512a3b687aae2518bb982496079d312",
    ),
    "original_package": (
        "results/cmix_obias_source_1m_roundtrip_qm3_v1/cmix",
        468481,
        "4ba53d3652c4e6de4126b4c03006e45a5f7e0511abd5d9661bf8132236ef1d2a",
    ),
    "head": (
        "results/cmix_obias_source_1m_roundtrip_qm3_v1/head.blob",
        23002,
        "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078",
    ),
    "source_archive": (
        "results/cmix_obias_memory_safe_parent_build_a_q0_v1/source.tar",
        2611200,
        "656a3100b7c4580658080fb0eda221a28b2f982f798f0b7ddc13409f2ce9c249",
    ),
    "ppmd_source": (
        "results/cmix_obias_memory_safe_parent_build_a_q0_v1/source-inputs/src/models/ppmd.cpp",
        37033,
        "d54d27616f756efa1fd5d08aaec85fe4688004b5dcd49f411caba92812cbb7e1",
    ),
    "managed_lease": (
        "programs/gamma_managed_exclusive_lease_owned_cleanup_q0_v1/managed_exclusive_lease.py",
        26066,
        "df96b87efb30e2c172f1d5182c7a81ef2b7bde6b7454c0181f2ac5cf39c20acb",
    ),
    "managed_lease_verifier": (
        "tools/managed_exclusive_lease_verify.py",
        9081,
        "68ab6f91181e616c7e4991d3c6c76979e06aa4936add62e23c96d92e8bbb29d1",
    ),
    "resource_guard": (
        "tools/run_with_resource_guard_v3.py",
        31807,
        "044147f7ffe6922ea8dafd52fc3d4426077b20958adbcd421245ad41adcfc1e4",
    ),
    "stage_runner": (
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v1_stage.py",
        19246,
        "955dfddcc740116359d7edbc530de416499eb5d68a55f8c236767045b253ebd3",
    ),
}
SCORE_RE = re.compile(r"Single[- ]Core\s+Score\s*:?\s*([0-9][0-9,]*)", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if not resolved.is_file() or resolved.is_symlink():
        raise RuntimeError(f"not a regular artifact: {resolved}")
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def verify_record(path: Path, expected: dict[str, Any], label: str) -> Path:
    if not isinstance(expected, dict) or set(expected) != {"path", "bytes", "sha256"}:
        raise RuntimeError(f"{label} artifact record is malformed")
    resolved = path.resolve(strict=True)
    value = artifact(resolved)
    if value["bytes"] != expected["bytes"] or value["sha256"] != expected["sha256"]:
        raise RuntimeError(f"{label} artifact identity mismatch")
    return resolved


def same_artifact(left: Any, right: Any) -> bool:
    return bool(
        isinstance(left, dict)
        and isinstance(right, dict)
        and left.get("bytes") == right.get("bytes")
        and left.get("sha256") == right.get("sha256")
    )


def write_new(path: Path, raw: bytes, mode: int = 0o600) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        mode,
    )
    try:
        cursor = 0
        while cursor < len(raw):
            written = os.write(descriptor, raw[cursor:])
            if written <= 0:
                raise OSError(f"short write: {path}")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_json_new(path: Path, value: dict[str, Any]) -> None:
    write_new(path, json.dumps(value, indent=2, sort_keys=True).encode("ascii") + b"\n")


def command_sha256(argv: list[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(value) for value in argv)).hexdigest()


def load_module(path: Path, name: str) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    if Path(module.__file__).resolve(strict=True) != path.resolve(strict=True):
        raise RuntimeError(f"loaded module differs from {path}")
    return module


def filesystem_type(path: Path) -> str:
    completed = subprocess.run(
        ["/usr/bin/stat", "--file-system", "--format=%T", str(path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def existing_dependencies() -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for name, (relative, expected_bytes, expected_sha256) in EXPECTED.items():
        path = (PROJECT / relative).resolve(strict=True)
        observed = artifact(path)
        if observed["bytes"] != expected_bytes or observed["sha256"] != expected_sha256:
            raise RuntimeError(f"frozen dependency drift: {name}")
        resolved[name] = path
    ppmd = resolved["ppmd_source"].read_text(encoding="utf-8")
    required_fragments = (
        'getenv("CMIX_PPM_RSS_MB")',
        "strtoull(env, &end, 10)",
        "DropPpmHeapResidency(ppmd_model_.get())",
    )
    if any(fragment not in ppmd for fragment in required_fragments):
        raise RuntimeError("bound original source lacks the runtime PPM-RSS control")
    return resolved


def active_horizon_jobs() -> list[str]:
    running = PROJECT / "operations/adaptive/running"
    found: list[str] = []
    for path in sorted(running.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            found.append(path.name)
            continue
        if value.get("candidate_id") == "endpoint428_horizon_retained_parent_trace_q0_v1":
            found.append(value.get("job_id", path.stem))
    return found


def parse_score(path: Path) -> tuple[int, dict[str, Any]]:
    record = artifact(path)
    matches = SCORE_RE.findall(path.read_text(errors="replace"))
    values = {int(value.replace(",", "")) for value in matches}
    if len(values) != 1 or next(iter(values)) <= 0:
        raise RuntimeError("Geekbench 5 report must contain one positive Single-Core Score")
    return next(iter(values)), record


def load_json_artifact(path: Path, label: str) -> tuple[dict[str, Any], dict[str, Any]]:
    record = artifact(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} root is not an object")
    return value, record


def managed_lease_verification(path: Path) -> dict[str, Any]:
    value, record = load_json_artifact(path, "managed lease verification")
    checks = value.get("checks")
    if not (
        value.get("schema")
        == "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-verification.v1"
        and value.get("candidate_id") == "gamma_managed_exclusive_lease_owned_cleanup_q0_v1"
        and value.get("verified") is True
        and isinstance(checks, dict)
        and checks
        and all(item is True for item in checks.values())
        and value.get("errors") == []
        and value.get("canonical_migration_authorized") is True
    ):
        raise RuntimeError("managed lease owned-cleanup verification is not authoritative")
    return record


def identity_witness(path: Path, role: str, gate_size: int) -> tuple[dict[str, Any], dict[str, Any]]:
    value, record = load_json_artifact(path, f"{role} identity witness")
    required = {
        "schema",
        "role",
        "gate_size",
        "population_sha256",
        "release_package_sha256",
        "producer",
        "coded_bits",
        "probability_sha256",
        "state_checkpoints",
        "payload",
        "witness_pass",
    }
    if set(value) != required or value.get("schema") != WITNESS_SCHEMA:
        raise RuntimeError(f"{role} identity witness shape or schema mismatch")
    if (
        value.get("role") != role
        or value.get("gate_size") != gate_size
        or value.get("population_sha256") != GATES[gate_size]
        or value.get("release_package_sha256") != EXPECTED["original_package"][2]
        or value.get("witness_pass") is not True
        or not isinstance(value.get("coded_bits"), int)
        or value["coded_bits"] <= 0
        or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("probability_sha256")))
        or not isinstance(value.get("state_checkpoints"), list)
        or not value["state_checkpoints"]
    ):
        raise RuntimeError(f"{role} identity witness binding failed")
    verify_record(Path(value["producer"]["path"]), value["producer"], f"{role} witness producer")
    return value, record


def witness_identity(control: dict[str, Any], treatment: dict[str, Any]) -> bool:
    return bool(
        control["coded_bits"] == treatment["coded_bits"]
        and control["probability_sha256"] == treatment["probability_sha256"]
        and control["state_checkpoints"] == treatment["state_checkpoints"]
        and control["payload"]["bytes"] == treatment["payload"]["bytes"]
        and control["payload"]["sha256"] == treatment["payload"]["sha256"]
    )


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


def guard_pass(value: dict[str, Any], phase: str, score: int) -> bool:
    peaks = value.get("peaks", {})
    events = value.get("cgroup_events", {}).get("delta", {})
    return bool(
        value.get("schema") == GUARD_SCHEMA
        and value.get("phase") == phase
        and value.get("status") == "complete"
        and value.get("returncode") == 0
        and math.isclose(value.get("geekbench5_single_core_score", 0), score)
        and math.isclose(
            value.get("wall_time_limit_seconds", 0), WALL_TIME_NUMERATOR / score, abs_tol=1e-6
        )
        and value.get("limit_mode") == "tree"
        and value.get("official_decimal_limit_kib") == MEMORY_LIMIT_KIB
        and value.get("cgroup", {}).get("requested_memory_max_bytes") == MEMORY_MAX_BYTES
        and value.get("cgroup", {}).get("memory_max_bytes", MEMORY_MAX_BYTES + 1) <= MEMORY_MAX_BYTES
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
    )


def run_stage(
    *,
    label: str,
    mode: str,
    ppm_rss_mb: str,
    input_record: dict[str, Any] | None,
    package_record: dict[str, Any] | None,
    head_record: dict[str, Any] | None,
    archive_record: dict[str, Any] | None,
    result_root: Path,
    scratch_root: Path,
    cgroup_base: Path,
    lease_path: Path,
    cpu: int,
    score: int,
    dependencies: dict[str, Path],
    lease_module: ModuleType,
) -> dict[str, Any]:
    phase = "compression" if mode == "encode" else "decompression"
    phase_result = result_root / label
    phase_work = scratch_root / label
    phase_result.mkdir(mode=0o700)
    marker = phase_result / "phase-markers.jsonl"
    write_new(marker, b"")
    stage_receipt = phase_result / "stage.json"
    stage_argv = [
        "/usr/bin/python3",
        str(dependencies["stage_runner"]),
        "--mode",
        mode,
        "--ppm-rss-mb",
        ppm_rss_mb,
        "--work-root",
        str(phase_work),
        "--result-root",
        str(phase_result),
        "--receipt",
        str(stage_receipt),
    ]
    if mode == "encode":
        assert input_record is not None and package_record is not None and head_record is not None
        for option, record in (
            ("input", input_record),
            ("package", package_record),
            ("head", head_record),
        ):
            stage_argv.extend(
                [
                    f"--{option}",
                    str(record["path"]),
                    f"--{option}-bytes",
                    str(record["bytes"]),
                    f"--{option}-sha256",
                    str(record["sha256"]),
                ]
            )
    else:
        assert archive_record is not None
        stage_argv.extend(
            [
                "--archive",
                str(archive_record["path"]),
                "--archive-bytes",
                str(archive_record["bytes"]),
                "--archive-sha256",
                str(archive_record["sha256"]),
            ]
        )
    guard_receipt = phase_result / "guard.json"
    cgroup_path = cgroup_base.with_name(f"{cgroup_base.name}-{label}")
    if cgroup_path.exists() or cgroup_path.is_symlink():
        raise RuntimeError(f"stage cgroup already exists: {cgroup_path}")
    cgroup_path.mkdir(mode=0o700)
    guard_argv = [
        "/usr/bin/taskset",
        "--cpu-list",
        str(cpu),
        "/usr/bin/python3",
        str(dependencies["resource_guard"]),
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
        f"{CANDIDATE_ID}-{label}",
        "--phase",
        phase,
        "--geekbench5-single-core-score",
        str(score),
        "--",
        *stage_argv,
    ]
    transition = phase_result / "lease-transitions.json"
    evidence = phase_result / "lease-evidence.json"
    lease = lease_module.ManagedExclusiveLease.acquire(
        lease_path=lease_path,
        transition_path=transition,
        candidate_id=f"{CANDIDATE_ID}-{label}",
        command_sha256=command_sha256(guard_argv),
        runner_sha256=sha256_file(Path(__file__).resolve(strict=True)),
        guard_path=str(guard_receipt),
        result_path=str(phase_result),
        scratch_path=str(phase_work),
        claim_boundary="one exact env-only CMIX encode/decode stage; zero Gamma score credit",
    )
    process: subprocess.Popen[Any] | None = None
    outer_returncode: int | None = None
    errors: list[str] = []
    try:
        with (phase_result / "guard.stdout").open("xb") as stdout, (
            phase_result / "guard.stderr"
        ).open("xb") as stderr:
            process = subprocess.Popen(
                guard_argv,
                cwd=PROJECT,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
            start_ticks = lease_module.proc_identity(process.pid)[1]
            lease.activate_codec(
                codec_pid=process.pid,
                codec_proc_start_ticks=start_ticks,
                codec_command_sha256=command_sha256(guard_argv),
            )
            while (outer_returncode := process.poll()) is None:
                lease.heartbeat()
                time.sleep(5)
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    finally:
        if process is not None:
            terminate_group(process)
            outer_returncode = process.wait()
        try:
            lease.deauthorize_signals()
            lease.release(evidence_path=evidence)
        except Exception as exc:
            errors.append(f"lease_release: {type(exc).__name__}: {exc}")
        if not remove_empty_cgroup(cgroup_path):
            errors.append("cgroup_cleanup_failed")
    guard: dict[str, Any] | None = None
    stage: dict[str, Any] | None = None
    if guard_receipt.is_file():
        guard, _ = load_json_artifact(guard_receipt, f"{label} guard")
    else:
        errors.append("guard_receipt_missing")
    if stage_receipt.is_file():
        stage, _ = load_json_artifact(stage_receipt, f"{label} stage")
    else:
        errors.append("stage_receipt_missing")
    passed = bool(
        not errors
        and outer_returncode == 0
        and guard is not None
        and guard_pass(guard, phase, score)
        and stage is not None
        and stage.get("schema") == STAGE_SCHEMA
        and stage.get("mode") == mode
        and stage.get("ppm_rss_environment")
        == ({} if ppm_rss_mb == "default" else {"CMIX_PPM_RSS_MB": "8192"})
        and stage.get("execution", {}).get("measurement_complete") is True
        and stage.get("stage_pass") is True
        and not lease_path.exists()
        and not lease_path.with_name(f"{lease_path.name}.lock").exists()
    )
    if not passed and not errors:
        errors.append("guard_stage_or_lease_contract_failed")
    return {
        "label": label,
        "mode": mode,
        "ppm_rss_mb": ppm_rss_mb,
        "stage_argv": stage_argv,
        "guard_argv": guard_argv,
        "outer_returncode": outer_returncode,
        "guard": guard,
        "stage": stage,
        "lease_evidence": artifact(evidence) if evidence.is_file() else None,
        "lease_transitions": artifact(transition) if transition.is_file() else None,
        "errors": errors,
        "pass": passed,
    }


def copy_prefix(corpus: Path, destination: Path, gate_size: int) -> dict[str, Any]:
    descriptor = os.open(
        destination,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        with corpus.open("rb") as source:
            remaining = gate_size
            while remaining:
                chunk = source.read(min(8 << 20, remaining))
                if not chunk:
                    raise RuntimeError("canonical corpus ended before exact gate")
                cursor = 0
                while cursor < len(chunk):
                    written = os.write(descriptor, chunk[cursor:])
                    if written <= 0:
                        raise OSError("short gate-population write")
                    cursor += written
                remaining -= len(chunk)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    value = artifact(destination)
    if value["bytes"] != gate_size or value["sha256"] != GATES[gate_size]:
        raise RuntimeError("exact gate population identity mismatch")
    return value


def preflight(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Path]]:
    dependencies = existing_dependencies()
    blockers: list[str] = []
    horizon = active_horizon_jobs()
    if horizon:
        blockers.append(f"active HORIZON job owns the corpus-heavy lane: {horizon}")
    if args.gate_size not in GATES:
        blockers.append("gate size must be exactly 1000000 or 100000000")
    corpus = args.corpus.resolve()
    if not corpus.is_file() or corpus.is_symlink() or corpus.stat().st_size != CANONICAL_BYTES:
        blockers.append("canonical 1G corpus path or size is invalid")
    if args.geekbench5_report is None:
        blockers.append("an isolated Geekbench 5 report is required")
    else:
        try:
            parse_score(args.geekbench5_report.resolve(strict=True))
        except Exception as exc:
            blockers.append(f"Geekbench 5 receipt: {exc}")
    if args.managed_lease_verification is None:
        blockers.append("owned-cleanup managed lease verification is required")
    else:
        try:
            managed_lease_verification(args.managed_lease_verification.resolve(strict=True))
        except Exception as exc:
            blockers.append(f"managed lease verification: {exc}")
    if (args.control_witness is None) != (args.treatment_witness is None):
        blockers.append("control and treatment witnesses must be supplied together")
    for role, path in (("control", args.control_witness), ("treatment", args.treatment_witness)):
        if path is not None:
            try:
                identity_witness(path.resolve(strict=True), role, args.gate_size)
            except Exception as exc:
                blockers.append(f"{role} witness: {exc}")
    if args.result_root is None or args.scratch_root is None or args.cgroup_path is None:
        blockers.append("result, scratch, and cgroup roots are required for execution")
    else:
        scratch_parent = args.scratch_root.resolve().parent
        if not scratch_parent.is_dir():
            blockers.append("scratch parent is missing")
        else:
            scratch_fs = filesystem_type(scratch_parent)
            if scratch_fs in {"tmpfs", "ramfs"} or Path("/dev/shm") in args.scratch_root.resolve().parents:
                blockers.append(f"scratch must be disk-backed, observed filesystem={scratch_fs}")
        if args.result_root.exists() or args.result_root.is_symlink():
            if not args.precreated_empty_result_root:
                blockers.append("result root exists without --precreated-empty-result-root")
            elif not args.result_root.is_dir() or next(args.result_root.iterdir(), None) is not None:
                blockers.append("precreated result root is not an empty directory")
        if args.scratch_root.exists() or args.scratch_root.is_symlink():
            blockers.append("scratch root must be absent")
        if args.cgroup_path.exists() or args.cgroup_path.is_symlink():
            blockers.append("cgroup base path must be absent")
        if not args.cgroup_path.parent.is_dir():
            blockers.append("cgroup parent is missing")
    if args.cpu not in os.sched_getaffinity(0):
        blockers.append("selected CPU is outside coordinator affinity")
    lease = args.exclusive_lease.resolve()
    if lease.exists() or lease.is_symlink() or lease.with_name(f"{lease.name}.lock").exists():
        blockers.append("managed exclusive lease namespace is occupied")
    report = {
        "schema": "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-preflight.v1",
        "candidate_id": CANDIDATE_ID,
        "first_runnable_gate_bytes": 1_000_000,
        "selected_gate_bytes": args.gate_size,
        "frozen_original_package": artifact(dependencies["original_package"]),
        "env_only_treatment": {"CMIX_PPM_RSS_MB": "8192"},
        "patched_q0_status": "conditional_successor_only",
        "patched_q0_candidate_id": FROZEN_PATCHED_SUCCESSOR,
        "dependencies": {name: artifact(path) for name, path in dependencies.items()},
        "population_hash_recomputed": False,
        "blockers": blockers,
        "execution_ready": not blockers,
        "claim_boundary": "Read-only preflight; no corpus gate, lease, cgroup, result, or score authority.",
    }
    return report, dependencies


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation-only", action="store_true")
    parser.add_argument("--gate-size", type=int, choices=tuple(GATES), default=1_000_000)
    parser.add_argument("--corpus", type=Path, default=PROJECT / "data/enwik9")
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--precreated-empty-result-root", action="store_true")
    parser.add_argument("--scratch-root", type=Path)
    parser.add_argument("--cgroup-path", type=Path)
    parser.add_argument(
        "--exclusive-lease",
        type=Path,
        default=PROJECT / "operations/runtime/exclusive_full1g.json",
    )
    parser.add_argument("--managed-lease-verification", type=Path)
    parser.add_argument("--geekbench5-report", type=Path)
    parser.add_argument("--control-witness", type=Path)
    parser.add_argument("--treatment-witness", type=Path)
    parser.add_argument("--cpu", type=int, default=min(os.sched_getaffinity(0)))
    args = parser.parse_args()

    if Path.cwd().resolve(strict=True) != PROJECT:
        raise RuntimeError(f"runner must execute from {PROJECT}")
    report, dependencies = preflight(args)
    if args.validation_only:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if not report["execution_ready"]:
        raise RuntimeError("execution preflight failed: " + "; ".join(report["blockers"]))

    assert args.result_root is not None and args.scratch_root is not None
    assert args.cgroup_path is not None and args.geekbench5_report is not None
    assert args.managed_lease_verification is not None
    result_root = args.result_root.resolve()
    scratch_root = args.scratch_root.resolve()
    if not result_root.exists():
        result_root.mkdir(mode=0o700)
    scratch_root.mkdir(mode=0o700)
    population_record = copy_prefix(args.corpus.resolve(strict=True), scratch_root / "population.bin", args.gate_size)
    score, score_record = parse_score(args.geekbench5_report.resolve(strict=True))
    lease_verification_record = managed_lease_verification(
        args.managed_lease_verification.resolve(strict=True)
    )
    control_witness: dict[str, Any] | None = None
    treatment_witness: dict[str, Any] | None = None
    control_witness_record: dict[str, Any] | None = None
    treatment_witness_record: dict[str, Any] | None = None
    if args.control_witness is not None and args.treatment_witness is not None:
        control_witness, control_witness_record = identity_witness(
            args.control_witness.resolve(strict=True), "control", args.gate_size
        )
        treatment_witness, treatment_witness_record = identity_witness(
            args.treatment_witness.resolve(strict=True), "treatment", args.gate_size
        )
        if not witness_identity(control_witness, treatment_witness):
            raise RuntimeError("optional control/treatment probability or state witness mismatch")
    package_record = artifact(dependencies["original_package"])
    head_record = artifact(dependencies["head"])
    lease_module = load_module(dependencies["managed_lease"], "q0_owned_managed_lease")
    stages: dict[str, Any] = {}
    errors: list[str] = []
    try:
        for label, ppm in (
            ("control-encode", "default"),
            ("treatment-a-encode", "8192"),
            ("treatment-b-encode", "8192"),
        ):
            stages[label] = run_stage(
                label=label,
                mode="encode",
                ppm_rss_mb=ppm,
                input_record=population_record,
                package_record=package_record,
                head_record=head_record,
                archive_record=None,
                result_root=result_root,
                scratch_root=scratch_root,
                cgroup_base=args.cgroup_path,
                lease_path=args.exclusive_lease.resolve(),
                cpu=args.cpu,
                score=score,
                dependencies=dependencies,
                lease_module=lease_module,
            )
            if not stages[label]["pass"]:
                raise RuntimeError(f"{label} failed")
        treatment_archive = stages["treatment-a-encode"]["stage"]["outputs"]["archive"]
        stages["treatment-decode"] = run_stage(
            label="treatment-decode",
            mode="decode",
            ppm_rss_mb="8192",
            input_record=None,
            package_record=None,
            head_record=None,
            archive_record=treatment_archive,
            result_root=result_root,
            scratch_root=scratch_root,
            cgroup_base=args.cgroup_path,
            lease_path=args.exclusive_lease.resolve(),
            cpu=args.cpu,
            score=score,
            dependencies=dependencies,
            lease_module=lease_module,
        )
        if not stages["treatment-decode"]["pass"]:
            raise RuntimeError("treatment-decode failed")
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    def output(label: str, name: str) -> dict[str, Any] | None:
        stage = stages.get(label, {}).get("stage")
        return stage.get("outputs", {}).get(name) if isinstance(stage, dict) else None

    control_payload = output("control-encode", "payload")
    control_archive = output("control-encode", "archive")
    treatment_a_payload = output("treatment-a-encode", "payload")
    treatment_b_payload = output("treatment-b-encode", "payload")
    treatment_a_archive = output("treatment-a-encode", "archive")
    treatment_b_archive = output("treatment-b-encode", "archive")
    restored = output("treatment-decode", "restored")
    optional_witness_pass = (
        witness_identity(control_witness, treatment_witness)
        if control_witness is not None and treatment_witness is not None
        else None
    )
    identity = {
        "same_original_package_source_contract_pass": all(
            stages.get(label, {}).get("stage", {}).get("inputs", {}).get("package", {}).get("sha256")
            == EXPECTED["original_package"][2]
            for label in ("control-encode", "treatment-a-encode", "treatment-b-encode")
        ),
        "control_treatment_payload_identity_pass": same_artifact(
            control_payload, treatment_a_payload
        ),
        "control_treatment_archive_identity_pass": same_artifact(
            control_archive, treatment_a_archive
        ),
        "treatment_payload_repeat_pass": same_artifact(
            treatment_a_payload, treatment_b_payload
        ),
        "treatment_archive_repeat_pass": same_artifact(
            treatment_a_archive, treatment_b_archive
        ),
        "exact_inverse_pass": same_artifact(restored, population_record),
    }
    for name, passed in identity.items():
        if not passed:
            errors.append(f"identity_failed: {name}")
    command_blob = (
        COUNTED_COMPRESS_COMMAND.encode("ascii")
        + COUNTED_DECOMPRESS_COMMAND.encode("ascii")
    )
    control_execution = (
        stages.get("control-encode", {}).get("stage", {}).get("execution", {})
    )
    treatment_execution = (
        stages.get("treatment-a-encode", {}).get("stage", {}).get("execution", {})
    )
    control_ppm = control_execution.get("ppm_residency", {})
    treatment_ppm = (
        stages.get("treatment-a-encode", {})
        .get("stage", {})
        .get("execution", {})
        .get("ppm_residency", {})
    )
    control_tree_peak = (
        stages.get("control-encode", {})
        .get("guard", {})
        .get("peaks", {})
        .get("max_sampled_tree_rss_kib")
    )
    treatment_tree_peak = (
        stages.get("treatment-a-encode", {})
        .get("guard", {})
        .get("peaks", {})
        .get("max_sampled_tree_rss_kib")
    )
    control_totals = control_execution.get("process_tree_totals", {})
    treatment_totals = treatment_execution.get("process_tree_totals", {})
    comparison_values = (
        control_tree_peak,
        treatment_tree_peak,
        control_totals.get("minor_faults"),
        treatment_totals.get("minor_faults"),
        control_totals.get("major_faults"),
        treatment_totals.get("major_faults"),
        control_totals.get("read_bytes"),
        treatment_totals.get("read_bytes"),
        control_totals.get("write_bytes"),
        treatment_totals.get("write_bytes"),
    )
    comparative_telemetry_complete = all(
        isinstance(value, int) for value in comparison_values
    )
    control_ppm_max = control_ppm.get("maximum_rss_kib")
    treatment_ppm_max = treatment_ppm.get("maximum_rss_kib")
    comparative_effect_observed = bool(
        comparative_telemetry_complete
        and (
            (
                isinstance(control_ppm_max, int)
                and isinstance(treatment_ppm_max, int)
                and treatment_ppm_max < control_ppm_max
            )
            or treatment_tree_peak < control_tree_peak
        )
    )
    ppm_resource_identity = {
        "required_for_gate": args.gate_size == 100_000_000,
        "trigger_total_rss_kib": 8_192 * 1_024,
        "engineering_maximum_tree_rss_kib": 9_000_000,
        "strict_official_maximum_tree_rss_kib": MEMORY_LIMIT_KIB,
        "control_tree_rss_peak_kib": control_tree_peak,
        "treatment_tree_rss_peak_kib": treatment_tree_peak,
        "control_ppm_maximum_rss_kib": control_ppm_max,
        "treatment_ppm_maximum_rss_kib": treatment_ppm_max,
        "control_ppm_observation_count": control_ppm.get("observation_count"),
        "treatment_ppm_observation_count": treatment_ppm.get("observation_count"),
        "control_process_tree_totals": control_totals,
        "treatment_process_tree_totals": treatment_totals,
        "process_tree_total_deltas_treatment_minus_control": {
            name: treatment_totals.get(name) - control_totals.get(name)
            if isinstance(treatment_totals.get(name), int)
            and isinstance(control_totals.get(name), int)
            else None
            for name in ("minor_faults", "major_faults", "read_bytes", "write_bytes")
        },
        "comparative_residency_and_fault_telemetry_complete": (
            comparative_telemetry_complete
        ),
        "comparative_residency_effect_observed": comparative_effect_observed,
        "comparative_residency_effect_status": (
            "observed"
            if comparative_effect_observed
            else "not_observed_inconclusive"
        ),
        "observed_drop_count": treatment_ppm.get("observed_drop_count", 0),
        "observed_refault_growth_count": treatment_ppm.get(
            "observed_refault_growth_count", 0
        ),
        "events_truncated": treatment_ppm.get("events_truncated"),
        "opening_100m_engineering_peak_pass": (
            True
            if args.gate_size == 1_000_000
            else bool(isinstance(treatment_tree_peak, int) and treatment_tree_peak < 9_000_000)
        ),
        "direct_purge_call_instrumentation_available": False,
        "observed_drop_absence_status": "inconclusive_not_falsification",
        "claim_boundary": (
            "Control and treatment residency, faults, IO, and tree peaks are compared. "
            "Bounded smaps drop/regrowth events are diagnostic only: the existing "
            "5000-byte purge cadence can evade external sampling, so zero observed "
            "events is inconclusive and is not algorithmic falsification."
        ),
    }
    ppm_resource_identity["external_total_rss_trigger_crossed"] = bool(
        isinstance(treatment_tree_peak, int)
        and treatment_tree_peak >= ppm_resource_identity["trigger_total_rss_kib"]
    )
    if not comparative_telemetry_complete:
        errors.append("comparative_residency_fault_io_telemetry_incomplete")
    if not ppm_resource_identity["opening_100m_engineering_peak_pass"]:
        errors.append("opening_100m_engineering_peak_at_or_above_9000000_kib")
    source_entries = {
        name: artifact(path)
        for name, path in dependencies.items()
        if name
        in {
            "source_archive",
            "managed_lease",
            "managed_lease_verifier",
            "resource_guard",
            "stage_runner",
        }
    }
    evidence_bundle_entries = {
        **{name: value["bytes"] for name, value in source_entries.items()},
        "coordinator_source": Path(__file__).stat().st_size,
    }
    official_entries = {
        "original_compressor": package_record["bytes"],
        "neural_head": head_record["bytes"],
        "self_extracting_archive": (
            treatment_a_archive["bytes"] if treatment_a_archive is not None else 0
        ),
        "compression_command_bytes": len(COUNTED_COMPRESS_COMMAND.encode("ascii")),
        "decompression_command_bytes": len(COUNTED_DECOMPRESS_COMMAND.encode("ascii")),
    }
    accounting = {
        "official_score_entries": official_entries,
        "official_complete_counted_bytes": sum(official_entries.values()),
        "evidence_bundle_entries_zero_score": evidence_bundle_entries,
        "evidence_bundle_bytes_zero_score": sum(evidence_bundle_entries.values()),
        "option_text_ascii": OPTION_TEXT.decode("ascii"),
        "normalized_compression_command": COUNTED_COMPRESS_COMMAND,
        "normalized_decompression_command": COUNTED_DECOMPRESS_COMMAND,
        "command_blob_sha256": hashlib.sha256(command_blob).hexdigest(),
        "source_and_dependencies": source_entries,
        "complete_package_accounting_pass": bool(
            len(COUNTED_COMPRESS_COMMAND.encode("ascii")) == 69
            and len(COUNTED_DECOMPRESS_COMMAND.encode("ascii")) == 31
            and all(value > 0 for value in official_entries.values())
            and all(value > 0 for value in evidence_bundle_entries.values())
        ),
        "claim_boundary": (
            "Official score accounting is archive plus compressor plus head plus the exact "
            "69-byte compression and 31-byte decompression commands. Source, guard, lease, "
            "runner, and receipts are separately counted zero-score evidence-bundle bytes."
        ),
    }
    if not accounting["complete_package_accounting_pass"]:
        errors.append("package_accounting_incomplete")
    def stage_elapsed(label: str) -> float | None:
        value = stages.get(label, {}).get("guard", {}).get("elapsed_s")
        return float(value) if isinstance(value, (int, float)) else None

    treatment_encode_elapsed = stage_elapsed("treatment-a-encode")
    treatment_decode_elapsed = stage_elapsed("treatment-decode")
    control_encode_elapsed = stage_elapsed("control-encode")
    projection_factor = CANONICAL_BYTES / args.gate_size
    runtime_projection = {
        "reject_only": args.gate_size == 100_000_000,
        "reserve_ratio": RUNTIME_PROJECTION_RESERVE_RATIO,
        "scale_factor": projection_factor,
        "control_encode_elapsed_seconds": control_encode_elapsed,
        "treatment_encode_elapsed_seconds": treatment_encode_elapsed,
        "treatment_decode_elapsed_seconds": treatment_decode_elapsed,
        "measured_treatment_control_encode_ratio": (
            treatment_encode_elapsed / control_encode_elapsed
            if treatment_encode_elapsed is not None
            and control_encode_elapsed is not None
            and control_encode_elapsed > 0
            else None
        ),
        "reserved_full_encode_projection_seconds": (
            treatment_encode_elapsed * projection_factor * RUNTIME_PROJECTION_RESERVE_RATIO
            if treatment_encode_elapsed is not None
            else None
        ),
        "reserved_full_decode_projection_seconds": (
            treatment_decode_elapsed * projection_factor * RUNTIME_PROJECTION_RESERVE_RATIO
            if treatment_decode_elapsed is not None
            else None
        ),
        "official_phase_limit_seconds": WALL_TIME_NUMERATOR / score,
        "opening_100m_projection_pass": True,
        "claim_boundary": (
            "A 100M projection plus frozen reserve can reject a runtime path but cannot "
            "qualify either full-corpus program."
        ),
    }
    if args.gate_size == 100_000_000:
        projections = (
            runtime_projection["reserved_full_encode_projection_seconds"],
            runtime_projection["reserved_full_decode_projection_seconds"],
        )
        runtime_projection["opening_100m_projection_pass"] = bool(
            all(isinstance(value, float) for value in projections)
            and all(
                value < runtime_projection["official_phase_limit_seconds"]
                for value in projections
            )
        )
        if not runtime_projection["opening_100m_projection_pass"]:
            errors.append("opening_100m_reserved_runtime_projection_failed")
    stage_pass = bool(stages and all(value.get("pass") is True for value in stages.values()))
    pre_cleanup_pass = bool(
        not errors
        and stage_pass
        and all(identity.values())
        and ppm_resource_identity[
            "comparative_residency_and_fault_telemetry_complete"
        ]
        and ppm_resource_identity["opening_100m_engineering_peak_pass"]
        and runtime_projection["opening_100m_projection_pass"]
    )
    if pre_cleanup_pass:
        shutil.rmtree(scratch_root)
    cleanup_pass = not scratch_root.exists() if pre_cleanup_pass else scratch_root.exists()
    if not cleanup_pass:
        errors.append("scratch_cleanup_contract_failed")
    terminal_pass = bool(pre_cleanup_pass and cleanup_pass and not errors)
    decision = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "mechanism": {"type": "environment_only", "CMIX_PPM_RSS_MB": "8192"},
        "patched_q0": {
            "candidate_id": FROZEN_PATCHED_SUCCESSOR,
            "status": "conditional_successor_only",
            "compression_credit_bytes": 0,
        },
        "gate_size": args.gate_size,
        "population": population_record,
        "preflight": report,
        "geekbench5": {"single_core_score": score, "report": score_record},
        "managed_lease_verification": lease_verification_record,
        "identity_witnesses": {
            "control": control_witness_record,
            "treatment": treatment_witness_record,
            "optional_identity_pass": optional_witness_pass,
            "claim_boundary": (
                "Optional corroboration only; gate authority comes from the exact same "
                "source/package contract, exact payload/archive repeats, and inverse."
            ),
        },
        "stages": stages,
        "identity": identity,
        "ppm_resource_identity": ppm_resource_identity,
        "runtime_projection": runtime_projection,
        "package_accounting": accounting,
        "cleanup": {
            "scratch_removed_on_pass": terminal_pass and not scratch_root.exists(),
            "scratch_preserved_on_failure": not terminal_pass and scratch_root.exists(),
            "lease_namespace_clear": not args.exclusive_lease.exists()
            and not args.exclusive_lease.with_name(f"{args.exclusive_lease.name}.lock").exists(),
        },
        "errors": list(dict.fromkeys(errors)),
        "terminal_pass": terminal_pass,
        "promotion_authorized": terminal_pass and args.gate_size == 1_000_000,
        "opening_100m_reject_only": args.gate_size == 100_000_000,
        "next_gate_bytes": 100_000_000 if terminal_pass and args.gate_size == 1_000_000 else None,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
        "claim_boundary": (
            "Exact bounded env-only identity/resource evidence for an external-derived "
            "experimental parent; never a Gamma-authored objective result."
        ),
    }
    write_json_new(result_root / "decision.json", decision)
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0 if terminal_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
