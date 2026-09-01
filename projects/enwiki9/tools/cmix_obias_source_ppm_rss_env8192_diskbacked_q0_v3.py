#!/usr/bin/env python3
"""Fail-closed disk-backed execution envelope for the exact opening 1M only."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3"
SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-opening1m-decision.v3"
STAGE_SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-opening1m-stage.v3"
HOST_SCHEMA = "gamma.enwiki9.geekbench5-current-host-binding.v1"
CLOSURE_SCHEMA = "gamma.enwiki9.adaptive-source-closure.v1"
BASE_PATH = PROJECT / "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v2.py"
STAGE_PATH = PROJECT / "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3_stage.py"
SOURCE_CLOSURE = PROJECT / f"operations/adaptive/source-closures/{CANDIDATE_ID}.json"
POPULATION_BYTES = 1_000_000
POPULATION_SHA256 = "369b688978f649681136198fb96db14c1616756260c55fb4b65e9bc049552cad"
PAYLOAD_BYTES = 172_605
PAYLOAD_SHA256 = "a723ca62ae2237354888dc23c3e2bb08eb166276719a011eb95bf52774d70db7"
ARCHIVE_BYTES = 464_298
ARCHIVE_SHA256 = "9065eaf54f81e441598fd53c39f909db49d6a9627ae0456eabb8c77099b8ccc4"
MEMORY_LIMIT_KIB = 9_765_625
MEMORY_MAX_BYTES = 10_000_000_000
DISK_LIMIT_BYTES = 100_000_000_000
COUNTED_COMPRESS_COMMAND = "CMIX_PPM_RSS_MB=8192 KH_BITLSTM32=head.blob ./cmix -e enwik9 out.cmix"
COUNTED_DECOMPRESS_COMMAND = "CMIX_PPM_RSS_MB=8192 ./archive9"
EXPERIMENT_MEASUREMENTS = (
    "packageSourceIdentityPass",
    "knownBaselinePayloadPass",
    "knownBaselineArchivePass",
    "freshArmIdentityPass",
    "exactDecodePass",
    "guardContractPass",
    "leaseEvidencePass",
    "outputManifestCompletePass",
    "officialCompletePackageBytes",
    "memoryEligibilityAtOpening1m",
    "runtimeEligibilityAtOpening1m",
    "ppmTriggerEligibilityAtOpening1m",
    "optionalWitnessIdentityPass",
)
PREDICATES = (
    ("package-source-identity", "packageSourceIdentityPass", "eq", True, True),
    ("known-payload", "knownBaselinePayloadPass", "eq", True, True),
    ("known-archive", "knownBaselineArchivePass", "eq", True, True),
    ("fresh-arms", "freshArmIdentityPass", "eq", True, True),
    ("exact-decode", "exactDecodePass", "eq", True, True),
    ("strict-guards", "guardContractPass", "eq", True, True),
    ("lease-evidence", "leaseEvidencePass", "eq", True, True),
    ("complete-manifest", "outputManifestCompletePass", "eq", True, True),
    ("official-accounting", "officialCompletePackageBytes", "eq", 955_881, True),
    ("memory-eligibility", "memoryEligibilityAtOpening1m", "eq", True, False),
    ("runtime-eligibility", "runtimeEligibilityAtOpening1m", "eq", True, False),
    ("ppm-trigger-eligibility", "ppmTriggerEligibilityAtOpening1m", "eq", True, False),
    ("optional-witness", "optionalWitnessIdentityPass", "eq", True, None),
)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_module(BASE_PATH, "cmix_q0_v3_coordinator_base")


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def artifact_matches(record: Any, size: int, digest: str) -> bool:
    return isinstance(record, dict) and record.get("bytes") == size and record.get("sha256") == digest


def current_host_fingerprint() -> dict[str, Any]:
    cpu_model = None
    for line in Path("/proc/cpuinfo").read_text(errors="replace").splitlines():
        if line.startswith("model name") and ":" in line:
            cpu_model = line.split(":", 1)[1].strip()
            break
    machine_id = Path("/etc/machine-id").read_bytes().strip()
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    uname = platform.uname()
    return {
        "hostname": uname.node,
        "system": uname.system,
        "release": uname.release,
        "version": uname.version,
        "machine": uname.machine,
        "cpu_model": cpu_model,
        "machine_id_sha256": hashlib.sha256(machine_id).hexdigest(),
        "boot_id": boot_id,
        "logical_cpu_count": os.cpu_count(),
        "coordinator_affinity": sorted(os.sched_getaffinity(0)),
    }


def verify_host_receipt(path: Path, geekbench: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    value, record = BASE.load_json_artifact(path.resolve(strict=True), "host fingerprint")
    expected_report = BASE.artifact(geekbench.resolve(strict=True))
    host = current_host_fingerprint()
    expected_host_digest = hashlib.sha256(canonical_json(host)).hexdigest()
    if (
        value.get("schema") != HOST_SCHEMA
        or value.get("isolated_geekbench5") is not True
        or value.get("geekbench5_report") != expected_report
        or value.get("current_host") != host
        or value.get("current_host_sha256") != expected_host_digest
    ):
        raise RuntimeError("Geekbench 5 report is not bound to the current isolated host")
    return value, record


def verify_source_closure(path: Path, expected_sha256: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    record = BASE.artifact(path.resolve(strict=True))
    if expected_sha256 is not None and record["sha256"] != expected_sha256:
        raise RuntimeError("source closure digest differs from adaptive job binding")
    value = json.loads(path.read_text())
    if value.get("schema") != CLOSURE_SCHEMA or value.get("candidate_id") != CANDIDATE_ID:
        raise RuntimeError("source closure schema or candidate mismatch")
    required = {
        "experiment", "proposal", "candidate_revision", "coordinator", "stage",
        "stage_base", "coordinator_base", "original_receipt", "original_package",
        "original_head", "baseline_payload", "baseline_archive", "source_archive",
        "runtime_option_source", "managed_lease", "managed_lease_verifier", "resource_guard",
    }
    artifacts = value.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != required:
        raise RuntimeError("source closure artifact set is incomplete")
    for name, bound in artifacts.items():
        if not isinstance(bound, dict) or set(bound) != {"path", "bytes", "sha256"}:
            raise RuntimeError(f"source closure record malformed: {name}")
        resolved = (PROJECT / bound["path"]).resolve(strict=True)
        observed = BASE.artifact(resolved)
        if observed["bytes"] != bound["bytes"] or observed["sha256"] != bound["sha256"]:
            raise RuntimeError(f"source closure artifact drift: {name}")
    if Path(artifacts["coordinator"]["path"]).name != Path(__file__).name:
        raise RuntimeError("source closure does not bind this coordinator")
    if Path(artifacts["stage"]["path"]).name != STAGE_PATH.name:
        raise RuntimeError("source closure does not bind the v3 stage")
    return value, record


def disk_backed_parent(path: Path) -> tuple[bool, str]:
    parent = path.resolve().parent
    if not parent.is_dir():
        return False, "missing-parent"
    fs_type = BASE.filesystem_type(parent)
    in_shm = path.resolve() == Path("/dev/shm") or Path("/dev/shm") in path.resolve().parents
    return fs_type not in {"tmpfs", "ramfs"} and not in_shm, fs_type


def strict_guard_pass(
    value: dict[str, Any], *, label: str, phase: str, command: list[str], cgroup: Path,
    scratch: Path, result: Path, marker: Path, score: float,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    require = lambda condition, message: errors.append(message) if not condition else None
    require(value.get("schema") == BASE.GUARD_SCHEMA, "schema")
    require(value.get("status") == "complete" and value.get("returncode") == 0, "terminal-status")
    require(value.get("label") == label and value.get("phase") == phase, "label-phase")
    require(value.get("command") == command, "command")
    require(value.get("command_sha256") == BASE.command_sha256(command), "command-sha256")
    require(value.get("limit_kib") == MEMORY_LIMIT_KIB, "limit-kib")
    require(value.get("limit_mode") == "tree", "limit-mode")
    require(value.get("official_decimal_limit_kib") == MEMORY_LIMIT_KIB, "official-limit")
    require(value.get("temporary_disk_limit_bytes") == DISK_LIMIT_BYTES, "disk-limit")
    require(value.get("max_logical_cpus") == 1, "cpu-limit")
    require(value.get("geekbench5_single_core_score") == score, "geekbench-score")
    require(value.get("scratch_paths") == [str(scratch), str(result)], "scratch-paths")
    require(value.get("phase_marker_path") == str(marker), "phase-marker-path")
    cgroup_value = value.get("cgroup", {})
    require(cgroup_value.get("path") == str(cgroup), "cgroup-path")
    require(cgroup_value.get("joined_before_exec") is True, "cgroup-join")
    require(cgroup_value.get("requested_memory_max_bytes") == MEMORY_MAX_BYTES, "cgroup-request")
    require(isinstance(cgroup_value.get("memory_max_bytes"), int) and cgroup_value["memory_max_bytes"] <= MEMORY_MAX_BYTES, "cgroup-effective")
    measurements = value.get("measurements")
    guards = value.get("guards")
    events = value.get("cgroup_events")
    require(isinstance(measurements, dict) and bool(measurements) and all(item is True for item in measurements.values()), "measurements")
    require(isinstance(guards, dict) and bool(guards) and all(item is False for item in guards.values()), "guards")
    require(isinstance(events, dict) and all(isinstance(events.get(key), dict) and bool(events[key]) for key in ("baseline", "final", "delta")), "events")
    require(isinstance(value.get("phase_markers"), list) and bool(value["phase_markers"]), "phase-markers")
    expected_marker_phase = "opening1m_" + label.rsplit("-", 1)[-1]
    marker_pairs = [
        (item.get("phase"), item.get("event"))
        for item in value.get("phase_markers", [])
        if isinstance(item, dict)
    ]
    require(
        (expected_marker_phase, "start") in marker_pairs
        and (expected_marker_phase, "end") in marker_pairs,
        "phase-marker-start-end",
    )
    require(isinstance(value.get("sample_count"), int) and value["sample_count"] > 0, "samples")
    require(isinstance(value.get("smaps_rollup_checkpoints"), list) and bool(value["smaps_rollup_checkpoints"]), "smaps")
    peaks = value.get("peaks", {})
    require(isinstance(peaks, dict) and bool(peaks), "peaks")
    require(peaks.get("max_sampled_tree_rss_kib", MEMORY_LIMIT_KIB) < MEMORY_LIMIT_KIB, "tree-rss")
    require(peaks.get("max_observed_process_vmhwm_kib", MEMORY_LIMIT_KIB) < MEMORY_LIMIT_KIB, "vmhwm")
    require(peaks.get("cgroup_memory_peak_bytes", MEMORY_MAX_BYTES) < MEMORY_MAX_BYTES, "cgroup-peak")
    return not errors, errors


def stage_argv(
    arm: str, phase_result: Path, phase_work: Path, population: dict[str, Any],
    package: dict[str, Any], head: dict[str, Any], archive: dict[str, Any] | None,
) -> tuple[str, str, list[str]]:
    mode = "decode" if arm == "E-decode" else "encode"
    ppm = "default" if arm == "P" else "8192"
    argv = [
        sys.executable, str(STAGE_PATH), "--mode", mode, "--arm", arm,
        "--work-root", str(phase_work), "--result-root", str(phase_result),
        "--receipt", str(phase_result / "stage.json"), "--ppm-rss-mb", ppm,
    ]
    if mode == "encode":
        argv += ["--input", population["path"], "--package", package["path"], "--head", head["path"]]
    else:
        assert archive is not None
        argv += ["--archive", archive["path"]]
    return mode, ppm, argv


def run_stage(
    *, arm: str, result_root: Path, scratch_root: Path, cgroup_base: Path,
    population: dict[str, Any], package: dict[str, Any], head: dict[str, Any],
    archive: dict[str, Any] | None, score: float, guard_path: Path, lease: Any,
) -> dict[str, Any]:
    slug = arm.lower().replace("-", "_")
    phase_result = result_root / slug
    phase_work = scratch_root / slug
    phase_result.mkdir(mode=0o700)
    marker = phase_result / "phase-markers.jsonl"
    BASE.write_new(marker, b"")
    mode, ppm, command = stage_argv(arm, phase_result, phase_work, population, package, head, archive)
    phase = "decompression" if mode == "decode" else "compression"
    label = f"{CANDIDATE_ID}-{slug}"
    cgroup = cgroup_base.with_name(f"{cgroup_base.name}-{slug}")
    if cgroup.exists() or cgroup.is_symlink():
        raise RuntimeError(f"stage cgroup exists: {cgroup}")
    cgroup.mkdir(mode=0o700)
    guard_receipt = phase_result / "guard.json"
    guard_argv = [
        sys.executable, str(guard_path), "--limit-kib", str(MEMORY_LIMIT_KIB),
        "--limit-mode", "tree", "--official-decimal-limit-kib", str(MEMORY_LIMIT_KIB),
        "--sample-interval", "0.5", "--cgroup-path", str(cgroup),
        "--cgroup-memory-max-bytes", str(MEMORY_MAX_BYTES),
        "--scratch-path", str(scratch_root), "--scratch-path", str(result_root),
        "--temporary-disk-limit-bytes", str(DISK_LIMIT_BYTES),
        "--phase-marker-path", str(marker), "--max-logical-cpus", "1",
        "--guard-json", str(guard_receipt), "--label", label, "--phase", phase,
        "--geekbench5-single-core-score", str(score), "--", *command,
    ]
    process: subprocess.Popen[Any] | None = None
    returncode: int | None = None
    errors: list[str] = []
    try:
        with (phase_result / "guard.stdout").open("xb") as stdout, (phase_result / "guard.stderr").open("xb") as stderr:
            process = subprocess.Popen(guard_argv, cwd=PROJECT, stdout=stdout, stderr=stderr, start_new_session=True)
            while (returncode := process.poll()) is None:
                lease.heartbeat()
                time.sleep(5)
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    finally:
        if process is not None:
            BASE.terminate_group(process)
            returncode = process.wait()
    guard = stage = None
    if guard_receipt.is_file():
        guard, _ = BASE.load_json_artifact(guard_receipt, f"{arm} guard")
        passed, guard_errors = strict_guard_pass(
            guard, label=label, phase=phase, command=command, cgroup=cgroup,
            scratch=scratch_root, result=result_root, marker=marker, score=score,
        )
        if not passed:
            errors.extend(f"guard:{item}" for item in guard_errors)
    else:
        errors.append("guard-receipt-missing")
    stage_receipt = phase_result / "stage.json"
    if stage_receipt.is_file():
        stage, _ = BASE.load_json_artifact(stage_receipt, f"{arm} stage")
        if (
            stage.get("schema") != STAGE_SCHEMA or stage.get("scope_bytes") != POPULATION_BYTES
            or stage.get("arm") != arm or stage.get("mode") != mode
            or stage.get("ppm_rss_environment") != ({} if ppm == "default" else {"CMIX_PPM_RSS_MB": "8192"})
            or stage.get("stage_pass") is not True
        ):
            errors.append("stage-contract")
    else:
        errors.append("stage-receipt-missing")
    if not BASE.remove_empty_cgroup(cgroup):
        errors.append("cgroup-cleanup")
    return {
        "arm": arm, "mode": mode, "ppm_rss_mb": ppm, "command": command,
        "guard_argv": guard_argv, "returncode": returncode, "guard": guard,
        "stage": stage, "errors": errors, "pass": not errors and returncode == 0,
    }


def expected_result_paths() -> set[str]:
    common = {"codec.stdout", "codec.stderr", "guard.stdout", "guard.stderr", "guard.json", "phase-markers.jsonl", "stage.json"}
    paths: set[str] = set()
    for slug in ("p", "e_a", "e_b"):
        paths.update(f"{slug}/{name}" for name in common | {"out.cmix", "archive9"})
    paths.update(f"e_decode/{name}" for name in common | {"enwik9_uncompressed"})
    paths.update({"experiment-lease-transitions.json", "experiment-lease-evidence.json", "experiment-lease-verification.json"})
    return paths


def result_manifest(result_root: Path) -> tuple[list[dict[str, Any]], bool]:
    records = []
    for path in sorted(result_root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"result symlink forbidden: {path}")
        if path.is_file() and path.name != "decision.json":
            record = BASE.artifact(path)
            record["path"] = path.relative_to(result_root).as_posix()
            records.append(record)
    return records, {item["path"] for item in records} == expected_result_paths()


def predicate_evaluations(measurements: dict[str, Any], witness_supplied: bool) -> list[dict[str, Any]]:
    rows = []
    for predicate_id, measurement_id, operator, threshold, applicability in PREDICATES:
        applies = witness_supplied if applicability is None else applicability
        observed = measurements[measurement_id]
        if not applies:
            result = "N_A"
        elif operator == "eq":
            result = "PASS" if observed == threshold else "FAIL"
        else:
            raise RuntimeError("unsupported predicate operator")
        rows.append({
            "predicateId": predicate_id, "measurementId": measurement_id,
            "operator": operator, "threshold": threshold, "applicability": "APPLICABLE" if applies else "N_A",
            "observed": observed, "result": result,
        })
    return rows


def preflight(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Path]]:
    dependencies = BASE.existing_dependencies()
    dependencies.update({"coordinator": Path(__file__).resolve(), "stage_v3": STAGE_PATH.resolve(strict=True), "coordinator_base": BASE_PATH.resolve(strict=True)})
    blockers: list[str] = []
    horizon = BASE.active_horizon_jobs()
    if horizon:
        blockers.append(f"active HORIZON job owns the corpus-heavy lane: {horizon}")
    corpus = args.corpus.resolve()
    if not corpus.is_file() or corpus.stat().st_size != 1_000_000_000:
        blockers.append("canonical 1G source corpus path or size is invalid")
    closure_value = closure_record = None
    if not args.source_closure.is_file():
        blockers.append("sealed v3 adaptive source closure is missing")
    else:
        try:
            closure_value, closure_record = verify_source_closure(args.source_closure, args.source_closure_sha256)
        except Exception as exc:
            blockers.append(f"source closure: {exc}")
    if not args.validation_only and args.source_closure_sha256 is None:
        blockers.append("adaptive job must bind --source-closure-sha256")
    score = score_record = host_record = None
    if args.geekbench5_report is None or args.host_fingerprint_receipt is None:
        blockers.append("isolated Geekbench 5 report and current-host binding are required")
    else:
        try:
            score, score_record = BASE.parse_score(args.geekbench5_report.resolve(strict=True))
            _, host_record = verify_host_receipt(args.host_fingerprint_receipt, args.geekbench5_report)
        except Exception as exc:
            blockers.append(f"Geekbench/current-host binding: {exc}")
    lease_verification = None
    if args.managed_lease_verification is None:
        blockers.append("authoritative owned-cleanup managed-lease verification is required")
    else:
        try:
            lease_verification = BASE.managed_lease_verification(args.managed_lease_verification.resolve(strict=True))
        except Exception as exc:
            blockers.append(f"managed lease verification: {exc}")
    if (args.control_witness is None) != (args.treatment_witness is None):
        blockers.append("optional control/treatment witnesses must be supplied together")
    if args.result_root is None or args.scratch_root is None or args.cgroup_path is None:
        blockers.append("result, scratch, and cgroup roots are required")
    else:
        for role, path in (("result", args.result_root), ("scratch", args.scratch_root)):
            disk_ok, fs_type = disk_backed_parent(path)
            if not disk_ok:
                blockers.append(f"{role} root must be disk-backed, observed {fs_type}")
        if args.result_root.exists() or args.result_root.is_symlink():
            blockers.append("result root must be absent")
        if args.scratch_root.exists() or args.scratch_root.is_symlink():
            blockers.append("scratch root must be absent")
        if args.cgroup_path.exists() or args.cgroup_path.is_symlink() or not args.cgroup_path.parent.is_dir():
            blockers.append("absent cgroup base with an existing parent is required")
    lease_path = args.exclusive_lease.resolve()
    if lease_path.exists() or lease_path.is_symlink() or lease_path.with_name(f"{lease_path.name}.lock").exists():
        blockers.append("managed exclusive lease namespace is occupied")
    source_text = dependencies["ppmd_source"].read_text(errors="replace")
    for fragment in ('getenv("CMIX_PPM_RSS_MB")', "strtoull", "DropPpmHeapResidency"):
        if fragment not in source_text:
            blockers.append(f"runtime option source audit missing: {fragment}")
    report = {
        "schema": "gamma.enwiki9.cmix-obias-opening1m-preflight.v3",
        "candidate_id": CANDIDATE_ID, "scope_bytes": POPULATION_BYTES,
        "larger_gates_supported": [], "execution_ready": not blockers, "blockers": blockers,
        "source_closure": closure_record, "source_closure_value": closure_value,
        "geekbench5_score": score, "geekbench5_report": score_record,
        "host_fingerprint_receipt": host_record, "lease_implementation_verification": lease_verification,
        "dependencies": {name: BASE.artifact(path) for name, path in dependencies.items()},
        "claim_boundary": "Read-only validation or exact opening-1M execution only; no 100M/full authorization.",
    }
    return report, dependencies


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation-only", action="store_true")
    parser.add_argument("--corpus", type=Path, default=PROJECT / "data/enwik9")
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--scratch-root", type=Path)
    parser.add_argument("--cgroup-path", type=Path)
    parser.add_argument("--exclusive-lease", type=Path, default=PROJECT / "operations/runtime/exclusive_full1g.json")
    parser.add_argument("--managed-lease-verification", type=Path)
    parser.add_argument("--geekbench5-report", type=Path)
    parser.add_argument("--host-fingerprint-receipt", type=Path)
    parser.add_argument("--control-witness", type=Path)
    parser.add_argument("--treatment-witness", type=Path)
    parser.add_argument("--source-closure", type=Path, default=SOURCE_CLOSURE)
    parser.add_argument("--source-closure-sha256")
    args = parser.parse_args()
    if Path.cwd().resolve(strict=True) != PROJECT:
        raise RuntimeError(f"runner must execute from {PROJECT}")
    report, dependencies = preflight(args)
    if args.validation_only:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if not report["execution_ready"]:
        raise RuntimeError("execution preflight failed: " + "; ".join(report["blockers"]))
    assert args.result_root is not None and args.scratch_root is not None and args.cgroup_path is not None
    assert args.geekbench5_report is not None and args.host_fingerprint_receipt is not None
    result_root, scratch_root = args.result_root.resolve(), args.scratch_root.resolve()
    result_root.mkdir(mode=0o700)
    transition = result_root / "experiment-lease-transitions.json"
    evidence = result_root / "experiment-lease-evidence.json"
    verification = result_root / "experiment-lease-verification.json"
    lease_module = load_module(dependencies["managed_lease"], "cmix_q0_v3_outer_lease")
    verifier_module = load_module(dependencies["managed_lease_verifier"], "cmix_q0_v3_lease_verifier")
    sequence_sha = hashlib.sha256(canonical_json({"candidate_id": CANDIDATE_ID, "arms": ["P", "E-A", "E-B", "E-decode"], "scope_bytes": POPULATION_BYTES})).hexdigest()
    lease = None
    errors: list[str] = []
    stages: dict[str, Any] = {}
    lease_verification_value = None
    try:
        lease = lease_module.ManagedExclusiveLease.acquire(
            lease_path=args.exclusive_lease.resolve(), transition_path=transition,
            candidate_id=CANDIDATE_ID, command_sha256=sequence_sha,
            runner_sha256=BASE.sha256_file(Path(__file__).resolve(strict=True)),
            guard_path=str(dependencies["resource_guard"]), result_path=str(result_root),
            scratch_path=str(scratch_root),
            claim_boundary="one outer lease across matched exact opening-1M P/E-A/E-B/decode arms",
        )
        scratch_root.mkdir(mode=0o700)
        population = BASE.copy_prefix(args.corpus.resolve(strict=True), scratch_root / "population.bin", POPULATION_BYTES)
        package = BASE.artifact(dependencies["original_package"])
        head = BASE.artifact(dependencies["head"])
        score, _ = BASE.parse_score(args.geekbench5_report.resolve(strict=True))
        for arm in ("P", "E-A", "E-B"):
            stages[arm] = run_stage(
                arm=arm, result_root=result_root, scratch_root=scratch_root,
                cgroup_base=args.cgroup_path, population=population, package=package,
                head=head, archive=None, score=score,
                guard_path=dependencies["resource_guard"], lease=lease,
            )
            if stages[arm]["pass"] is not True:
                raise RuntimeError(f"stage failed: {arm}")
        archive = stages["E-A"]["stage"]["outputs"]["archive"]
        stages["E-decode"] = run_stage(
            arm="E-decode", result_root=result_root, scratch_root=scratch_root,
            cgroup_base=args.cgroup_path, population=population, package=package,
            head=head, archive=archive, score=score,
            guard_path=dependencies["resource_guard"], lease=lease,
        )
        if stages["E-decode"]["pass"] is not True:
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
        verify_args = argparse.Namespace(transition_log=transition, terminal_lease=evidence, output=None)
        lease_verification_value, verified = verifier_module.verify(verify_args)
        BASE.write_json_new(verification, lease_verification_value)
        terminal_lease = json.loads(evidence.read_text())
        terminal_contract_pass = bool(
            terminal_lease.get("candidate_id") == CANDIDATE_ID
            and terminal_lease.get("command_sha256") == sequence_sha
            and terminal_lease.get("runner_sha256")
            == BASE.sha256_file(Path(__file__).resolve(strict=True))
            and terminal_lease.get("guard_path") == str(dependencies["resource_guard"])
            and terminal_lease.get("result_path") == str(result_root)
            and terminal_lease.get("scratch_path") == str(scratch_root)
            and terminal_lease.get("signal_authority") is False
            and lease_verification_value.get("computed", {}).get("terminal_events") == 1
            and lease_verification_value.get("computed", {}).get("activations") == 0
        )
        if (
            not verified
            or lease_verification_value.get("candidate_id") != CANDIDATE_ID
            or not terminal_contract_pass
        ):
            errors.append("outer_lease_evidence_verification_failed")
    else:
        errors.append("outer_lease_evidence_incomplete")
    if args.exclusive_lease.exists() or args.exclusive_lease.with_name(f"{args.exclusive_lease.name}.lock").exists():
        errors.append("outer_lease_namespace_not_clean")

    def output(arm: str, name: str) -> Any:
        stage = stages.get(arm, {}).get("stage")
        return stage.get("outputs", {}).get(name) if isinstance(stage, dict) else None

    payloads = [output(arm, "payload") for arm in ("P", "E-A", "E-B")]
    archives = [output(arm, "archive") for arm in ("P", "E-A", "E-B")]
    restored = output("E-decode", "restored")
    source_identity = bool(
        report["source_closure"] and BASE.artifact(dependencies["original_package"])["sha256"] == BASE.EXPECTED["original_package"][2]
        and BASE.artifact(dependencies["ppmd_source"])["sha256"] == BASE.EXPECTED["ppmd_source"][2]
    )
    known_payload = all(artifact_matches(item, PAYLOAD_BYTES, PAYLOAD_SHA256) for item in payloads)
    known_archive = all(artifact_matches(item, ARCHIVE_BYTES, ARCHIVE_SHA256) for item in archives)
    fresh_identity = bool(known_payload and known_archive and all(BASE.same_artifact(payloads[0], item) for item in payloads[1:]) and all(BASE.same_artifact(archives[0], item) for item in archives[1:]))
    exact_decode = artifact_matches(restored, POPULATION_BYTES, POPULATION_SHA256)
    guard_pass = len(stages) == 4 and all(value.get("pass") is True for value in stages.values())
    lease_pass = bool(lease_verification_value and lease_verification_value.get("verified") is True and not args.exclusive_lease.exists())
    witness_supplied = args.control_witness is not None and args.treatment_witness is not None
    witness_pass = None
    if witness_supplied:
        try:
            control, _ = BASE.identity_witness(args.control_witness.resolve(strict=True), "control", POPULATION_BYTES)
            treatment, _ = BASE.identity_witness(args.treatment_witness.resolve(strict=True), "treatment", POPULATION_BYTES)
            witness_pass = BASE.witness_identity(control, treatment)
        except Exception as exc:
            errors.append(f"optional_witness:{exc}")
            witness_pass = False
    official_bytes = 468_481 + 23_002 + ARCHIVE_BYTES + len(COUNTED_COMPRESS_COMMAND.encode()) + len(COUNTED_DECOMPRESS_COMMAND.encode())
    manifest, manifest_pass = result_manifest(result_root)
    measurements = {
        "packageSourceIdentityPass": source_identity,
        "knownBaselinePayloadPass": known_payload,
        "knownBaselineArchivePass": known_archive,
        "freshArmIdentityPass": fresh_identity,
        "exactDecodePass": exact_decode,
        "guardContractPass": guard_pass,
        "leaseEvidencePass": lease_pass,
        "outputManifestCompletePass": manifest_pass,
        "officialCompletePackageBytes": official_bytes,
        "memoryEligibilityAtOpening1m": None,
        "runtimeEligibilityAtOpening1m": None,
        "ppmTriggerEligibilityAtOpening1m": None,
        "optionalWitnessIdentityPass": witness_pass,
    }
    if tuple(measurements) != EXPERIMENT_MEASUREMENTS:
        errors.append("flat_measurement_map_drift")
    evaluations = predicate_evaluations(measurements, witness_supplied)
    applicable_pass = all(row["result"] == "PASS" for row in evaluations if row["applicability"] == "APPLICABLE")
    terminal_pass = not errors and applicable_pass
    if terminal_pass:
        shutil.rmtree(scratch_root)
    cleanup_pass = (not scratch_root.exists()) if terminal_pass else scratch_root.exists()
    if not cleanup_pass:
        errors.append("scratch_cleanup_contract_failed")
        terminal_pass = False
    decision = {
        "schema": SCHEMA, "candidate_id": CANDIDATE_ID, "scope_bytes": POPULATION_BYTES,
        "larger_gate_authorized": False, "next_gate_bytes": None,
        "separately_frozen_100m_experiment_required": True,
        "preflight": report, "stages": stages,
        "flat_measurements": measurements, "predicate_evaluations": evaluations,
        "known_baseline": {
            "payload": {"bytes": PAYLOAD_BYTES, "sha256": PAYLOAD_SHA256},
            "archive": {"bytes": ARCHIVE_BYTES, "sha256": ARCHIVE_SHA256},
        },
        "package_accounting": {
            "official_score_entries": {"compressor": 468_481, "head": 23_002, "archive": ARCHIVE_BYTES, "compression_command_bytes": 69, "decompression_command_bytes": 31},
            "official_complete_counted_bytes": official_bytes,
            "added_command_bytes": 100,
            "compression_command": COUNTED_COMPRESS_COMMAND,
            "decompression_command": COUNTED_DECOMPRESS_COMMAND,
            "evidence_bundle_score_bytes": 0,
        },
        "outer_lease_verification": lease_verification_value,
        "output_manifest": {"policy": "complete-result-artifacts-v1", "decision_self_excluded": True, "artifacts": manifest, "complete": manifest_pass},
        "cleanup": {"scratch_removed_on_pass": terminal_pass and not scratch_root.exists(), "scratch_preserved_on_failure": not terminal_pass and scratch_root.exists()},
        "errors": list(dict.fromkeys(errors)), "terminal_pass": terminal_pass,
        "promotion_authorized": False, "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
        "claim_boundary": "Exact opening-1M output-neutral identity authority only; memory/runtime/trigger are N/A and no larger gate is authorized.",
    }
    BASE.write_json_new(result_root / "decision.json", decision)
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0 if terminal_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
