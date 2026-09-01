#!/usr/bin/env python3
"""Corrected exact opening-1M env-only envelope with pinned CPU and authority."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v10"
SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-opening1m-decision.v10"
CLOSURE_SCHEMA = "gamma.enwiki9.adaptive-source-closure.v1"
V3_PATH = PROJECT / "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3.py"
STAGE_PATH = PROJECT / "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3_stage.py"
SOURCE_CLOSURE = PROJECT / f"operations/adaptive/source-closures/{CANDIDATE_ID}.json"
LEASE_PATH = PROJECT / "operations/runtime/exclusive_full1g.json"
LEASE_LOCK_PATH = PROJECT / "operations/runtime/exclusive_full1g.json.lock"
RESULT_ROOT = PROJECT / f"results/{CANDIDATE_ID}"
SCRATCH_ROOT = PROJECT / f"scratch/{CANDIDATE_ID}"
CGROUP_BASE = Path("/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/gamma-cmix-obias-env8192-opening1m-q0-v10")
PYTHON_RUNTIME_CLOSURE = PROJECT / f"operations/adaptive/python-runtime-closures/{CANDIDATE_ID}.json"
STDLIB_RESOURCE_GUARD = PROJECT / "tools/run_with_resource_guard_q0_v10.py"
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
MEASUREMENT_IDS = (
    "packageSourceIdentityPass", "knownBaselinePayloadPass", "knownBaselineArchivePass",
    "freshArmIdentityPass", "exactDecodePass", "guardContractPass",
    "leaseEvidencePass", "outputManifestCompletePass", "officialCompletePackageBytes",
    "memoryEligibilityAtOpening1m", "runtimeEligibilityAtOpening1m",
    "ppmTriggerEligibilityAtOpening1m", "optionalWitnessIdentityPass",
)
PROMOTION_PREDICATES = (
    ("package-source-identity", "packageSourceIdentityPass", "eq", True),
    ("known-payload", "knownBaselinePayloadPass", "eq", True),
    ("known-archive", "knownBaselineArchivePass", "eq", True),
    ("fresh-arms", "freshArmIdentityPass", "eq", True),
    ("exact-decode", "exactDecodePass", "eq", True),
    ("strict-guards", "guardContractPass", "eq", True),
    ("lease-evidence", "leaseEvidencePass", "eq", True),
    ("complete-manifest", "outputManifestCompletePass", "eq", True),
    ("official-accounting", "officialCompletePackageBytes", "eq", 955_881),
)
KILL_PREDICATES = (
    ("package-source-drift", "packageSourceIdentityPass", "eq", False),
    ("known-payload-mismatch", "knownBaselinePayloadPass", "eq", False),
    ("known-archive-mismatch", "knownBaselineArchivePass", "eq", False),
    ("fresh-arm-mismatch", "freshArmIdentityPass", "eq", False),
    ("decode-mismatch", "exactDecodePass", "eq", False),
    ("guard-failure", "guardContractPass", "eq", False),
    ("lease-failure", "leaseEvidencePass", "eq", False),
    ("manifest-failure", "outputManifestCompletePass", "eq", False),
)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V3 = load_module(V3_PATH, "cmix_q0_v10_v3_helpers")
BASE = V3.BASE


def verify_record(record: Any, label: str) -> tuple[Path, dict[str, Any]]:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise RuntimeError(f"{label} artifact record is malformed")
    path = Path(record["path"]).resolve(strict=True)
    observed = BASE.artifact(path)
    if observed != record:
        raise RuntimeError(f"{label} artifact identity mismatch")
    return path, observed


def verify_source_closure(expected_sha256: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    record = BASE.artifact(SOURCE_CLOSURE.resolve(strict=True))
    if expected_sha256 is not None and record["sha256"] != expected_sha256:
        raise RuntimeError("future adaptive job source-closure SHA-256 mismatch")
    value = json.loads(SOURCE_CLOSURE.read_text())
    if value.get("schema") != CLOSURE_SCHEMA or value.get("candidate_id") != CANDIDATE_ID:
        raise RuntimeError("source closure identity mismatch")
    artifacts = value.get("artifacts")
    required = {
        "experiment", "proposal", "candidate_revision", "coordinator", "stage",
        "v3_helpers", "stage_base", "coordinator_base",
        "python_runtime_closure",
        "original_receipt", "original_package", "original_head", "baseline_payload",
        "baseline_archive", "source_archive", "runtime_option_source", "managed_lease",
        "managed_lease_verifier", "resource_guard",
    }
    if not isinstance(artifacts, dict) or set(artifacts) != required:
        raise RuntimeError("source closure artifact set is incomplete")
    for name, bound in artifacts.items():
        if not isinstance(bound, dict) or set(bound) != {"path", "bytes", "sha256"}:
            raise RuntimeError(f"source closure record malformed: {name}")
        observed = BASE.artifact((PROJECT / bound["path"]).resolve(strict=True))
        if observed["bytes"] != bound["bytes"] or observed["sha256"] != bound["sha256"]:
            raise RuntimeError(f"source closure drift: {name}")
    if Path(artifacts["coordinator"]["path"]).name != Path(__file__).name:
        raise RuntimeError("source closure does not bind this coordinator")
    return value, record


def affinity_samples_pass(guard: dict[str, Any], cpu: int, mode: str) -> bool:
    samples = [guard.get(name) for name in ("peak_sample", "peak_tree_sample", "latest_sample")]
    process_rows: list[dict[str, Any]] = []
    for sample in samples:
        if not isinstance(sample, dict) or sample.get("allowed_cpu_union") != [cpu]:
            return False
        rows = sample.get("processes")
        if not isinstance(rows, list) or not rows:
            return False
        process_rows.extend(row for row in rows if isinstance(row, dict))
    if not process_rows or any(row.get("allowed_cpus") != [cpu] for row in process_rows):
        return False
    codec_names = {"archive9"} if mode == "decode" else {"cmix"}
    return any(row.get("comm") in codec_names for row in process_rows)


def run_stage(
    *, arm: str, result_root: Path, scratch_root: Path, cgroup_base: Path,
    population: dict[str, Any], package: dict[str, Any], head: dict[str, Any],
    archive: dict[str, Any] | None, guard_path: Path, lease: Any, cpu: int,
) -> dict[str, Any]:
    if os.sched_getaffinity(0) != {cpu}:
        raise RuntimeError("coordinator affinity drifted before stage")
    slug = arm.lower().replace("-", "_")
    phase_result, phase_work = result_root / slug, scratch_root / slug
    phase_result.mkdir(mode=0o700)
    marker = phase_result / "phase-markers.jsonl"
    BASE.write_new(marker, b"")
    mode, ppm, command = V3.stage_argv(arm, phase_result, phase_work, population, package, head, archive)
    phase = "identity"
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
        "--", *command,
    ]
    process: subprocess.Popen[Any] | None = None
    returncode = None
    guard_affinity = None
    errors: list[str] = []
    try:
        with (phase_result / "guard.stdout").open("xb") as stdout, (phase_result / "guard.stderr").open("xb") as stderr:
            process = subprocess.Popen(guard_argv, cwd=PROJECT, stdout=stdout, stderr=stderr, start_new_session=True)
            guard_affinity = sorted(os.sched_getaffinity(process.pid))
            if guard_affinity != [cpu]:
                raise RuntimeError("guard did not inherit singleton selected-CPU affinity")
            while (returncode := process.poll()) is None:
                if os.sched_getaffinity(0) != {cpu} or os.sched_getaffinity(process.pid) != {cpu}:
                    raise RuntimeError("coordinator or guard affinity drifted during stage")
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
        passed, guard_errors = V3.strict_guard_pass(
            guard, label=label, phase=phase, command=command, cgroup=cgroup,
            scratch=scratch_root, result=result_root, marker=marker, score=None,
        )
        if not passed:
            errors.extend(f"guard:{item}" for item in guard_errors)
        if not affinity_samples_pass(guard, cpu, mode):
            errors.append("guard-stage-codec-singleton-affinity")
    else:
        errors.append("guard-receipt-missing")
    stage_receipt = phase_result / "stage.json"
    if stage_receipt.is_file():
        stage, _ = BASE.load_json_artifact(stage_receipt, f"{arm} stage")
        if (
            stage.get("schema") != V3.STAGE_SCHEMA or stage.get("scope_bytes") != POPULATION_BYTES
            or stage.get("arm") != arm or stage.get("mode") != mode
            or stage.get("ppm_rss_environment") != ({} if ppm == "default" else {"CMIX_PPM_RSS_MB": "8192"})
            or stage.get("stage_pass") is not True
        ):
            errors.append("stage-contract")
    else:
        errors.append("stage-receipt-missing")
    if not BASE.remove_empty_cgroup(cgroup):
        errors.append("cgroup-cleanup")
    if os.sched_getaffinity(0) != {cpu}:
        errors.append("coordinator-affinity-after-stage")
    return {
        "arm": arm, "mode": mode, "selected_cpu": cpu,
        "coordinator_affinity": sorted(os.sched_getaffinity(0)),
        "guard_initial_affinity": guard_affinity, "command": command,
        "guard_argv": guard_argv, "returncode": returncode, "guard": guard,
        "stage": stage, "errors": errors, "pass": not errors and returncode == 0,
    }


def evaluate(rows: tuple[tuple[str, str, str, Any], ...], measurements: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for predicate_id, measurement_id, operator, threshold in rows:
        observed = measurements[measurement_id]
        passed = observed == threshold
        result.append({
            "predicateId": predicate_id, "measurementId": measurement_id,
            "operator": operator, "threshold": threshold, "applicability": "APPLICABLE",
            "observed": observed, "result": "PASS" if passed else "FAIL",
        })
    return result


def inapplicable_evaluations(measurements: dict[str, Any], witness_supplied: bool) -> list[dict[str, Any]]:
    rows = []
    for predicate_id, measurement_id in (
        ("memory-eligibility", "memoryEligibilityAtOpening1m"),
        ("runtime-eligibility", "runtimeEligibilityAtOpening1m"),
        ("ppm-trigger-eligibility", "ppmTriggerEligibilityAtOpening1m"),
    ):
        rows.append({"predicateId": predicate_id, "measurementId": measurement_id, "applicability": "N_A", "observed": measurements[measurement_id], "result": "N_A"})
    rows.append({
        "predicateId": "optional-witness", "measurementId": "optionalWitnessIdentityPass",
        "applicability": "APPLICABLE" if witness_supplied else "N_A",
        "observed": measurements["optionalWitnessIdentityPass"],
        "result": ("PASS" if measurements["optionalWitnessIdentityPass"] is True else "FAIL") if witness_supplied else "N_A",
    })
    return rows


def preflight(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Path]]:
    dependencies = BASE.existing_dependencies()
    dependencies.update({
        "coordinator": Path(__file__).resolve(), "v3_helpers": V3_PATH.resolve(strict=True),
        "stage_v3": STAGE_PATH.resolve(strict=True),
        "python_runtime_closure": PYTHON_RUNTIME_CLOSURE.resolve(strict=True),
    })
    dependencies["resource_guard"] = STDLIB_RESOURCE_GUARD.resolve(strict=True)
    blockers: list[str] = []
    if args.result_root.resolve() != RESULT_ROOT or args.scratch_root.resolve() != SCRATCH_ROOT or args.cgroup_path != CGROUP_BASE:
        blockers.append("caller runtime-path override is forbidden")
    if (args.control_witness is None) != (args.treatment_witness is None):
        blockers.append("XOR witness presence is forbidden")
    if args.cpu is None:
        blockers.append("future adaptive job must explicitly select --cpu")
    elif os.sched_getaffinity(0) != {args.cpu}:
        blockers.append("coordinator is not pinned to the selected singleton CPU")
    closure_value = closure_record = None
    if not SOURCE_CLOSURE.is_file():
        blockers.append("sealed v10 source closure is missing")
    else:
        try:
            closure_value, closure_record = verify_source_closure(args.source_closure_sha256)
        except Exception as exc:
            blockers.append(f"source closure: {exc}")
    if not args.validation_only and args.source_closure_sha256 is None:
        blockers.append("future adaptive job must bind --source-closure-sha256")
    if not args.validation_only:
        corpus = args.corpus.resolve()
        if not corpus.is_file() or corpus.stat().st_size != 1_000_000_000:
            blockers.append("canonical 1G source corpus path or size is invalid")
    if args.result_root is None or args.scratch_root is None or args.cgroup_path is None:
        blockers.append("result, scratch, and cgroup roots are required")
    else:
        result, scratch = args.result_root.resolve(), args.scratch_root.resolve()
        if result == scratch or result in scratch.parents or scratch in result.parents:
            blockers.append("result and scratch roots must be distinct and disjoint")
        for role, path in (("result", args.result_root), ("scratch", args.scratch_root)):
            disk_ok, fs_type = V3.disk_backed_parent(path)
            if not disk_ok:
                blockers.append(f"{role} root must be disk-backed, observed {fs_type}")
            if path.exists() or path.is_symlink():
                blockers.append(f"{role} root must be absent")
        if not args.validation_only and (args.cgroup_path.exists() or args.cgroup_path.is_symlink() or not args.cgroup_path.parent.is_dir()):
            blockers.append("absent cgroup base with existing parent is required")
        if not args.validation_only:
            parent=args.cgroup_path.parent; st=parent.stat(); controllers=set((parent/"cgroup.controllers").read_text().split()); occupants=(parent/"cgroup.procs").read_text().split()
            if (str(parent.resolve(strict=True)),st.st_ino,st.st_uid,st.st_gid)!=(str(CGROUP_BASE.parent),8608,1000,1000) or not {"memory","pids"}.issubset(controllers) or occupants:
                blockers.append("current delegated cgroup parent identity/controllers/direct occupants mismatch")
    if not args.validation_only and (LEASE_PATH.exists() or LEASE_PATH.is_symlink() or LEASE_LOCK_PATH.exists() or LEASE_LOCK_PATH.is_symlink()):
        blockers.append("pinned canonical managed exclusive lease namespace is occupied")
    report = {
        "schema": "gamma.enwiki9.cmix-obias-opening1m-preflight.v10",
        "candidate_id": CANDIDATE_ID, "scope_bytes": POPULATION_BYTES,
        "larger_gates_supported": [], "selected_cpu": args.cpu,
        "coordinator_affinity": sorted(os.sched_getaffinity(0)),
        "exclusive_lease_path": str(LEASE_PATH), "exclusive_lease_lock_path": str(LEASE_LOCK_PATH),
        "caller_lease_override_supported": False,
        "source_closure": closure_record, "source_closure_value": closure_value,
        "runtime_eligibility": None, "memory_eligibility": None,
        "ppm_trigger_eligibility": None,
        "blockers": blockers, "execution_ready": not blockers,
        "dependencies": {name: BASE.artifact(path) for name, path in dependencies.items()},
        "claim_boundary": "Read-only validation or exact opening-1M identity execution only; no larger gate authority.",
    }
    return report, dependencies


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation-only", action="store_true")
    parser.add_argument("--cpu", type=int)
    parser.add_argument("--corpus", type=Path, default=PROJECT / "data/enwik9")
    parser.add_argument("--result-root", type=Path, default=RESULT_ROOT)
    parser.add_argument("--scratch-root", type=Path, default=SCRATCH_ROOT)
    parser.add_argument("--cgroup-path", type=Path, default=CGROUP_BASE)
    parser.add_argument("--control-witness", type=Path)
    parser.add_argument("--treatment-witness", type=Path)
    parser.add_argument("--source-closure-sha256")
    args = parser.parse_args()
    if Path.cwd().resolve(strict=True) != PROJECT:
        raise RuntimeError(f"runner must execute from {PROJECT}")
    initial_affinity = set(os.sched_getaffinity(0))
    if args.cpu is not None:
        if args.cpu not in initial_affinity:
            raise RuntimeError("selected CPU is outside initial coordinator affinity")
        os.sched_setaffinity(0, {args.cpu})
        if os.sched_getaffinity(0) != {args.cpu}:
            raise RuntimeError("failed to pin coordinator to selected CPU")
    report, dependencies = preflight(args)
    if args.validation_only:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if not report["execution_ready"]:
        raise RuntimeError("execution preflight failed: " + "; ".join(report["blockers"]))
    assert args.cpu is not None
    assert args.result_root is not None and args.scratch_root is not None and args.cgroup_path is not None
    result_root, scratch_root, cgroup_base = args.result_root.resolve(), args.scratch_root.resolve(), args.cgroup_path.resolve()
    result_root.mkdir(mode=0o700)
    transition = result_root / "experiment-lease-transitions.json"
    evidence = result_root / "experiment-lease-evidence.json"
    verification_path = result_root / "experiment-lease-verification.json"
    lease_module = load_module(dependencies["managed_lease"], "cmix_q0_v10_outer_lease")
    verifier_module = load_module(dependencies["managed_lease_verifier"], "cmix_q0_v10_lease_verifier")
    sequence_sha = hashlib.sha256(V3.canonical_json({"candidate_id": CANDIDATE_ID, "arms": ["P", "E-A", "E-B", "E-decode"], "scope_bytes": POPULATION_BYTES, "selected_cpu": args.cpu})).hexdigest()
    lease = None
    errors: list[str] = []
    stages: dict[str, Any] = {}
    lease_verification_value = None
    try:
        lease = lease_module.ManagedExclusiveLease.acquire(
            lease_path=LEASE_PATH, transition_path=transition, candidate_id=CANDIDATE_ID,
            command_sha256=sequence_sha, runner_sha256=BASE.sha256_file(Path(__file__).resolve(strict=True)),
            guard_path=str(dependencies["resource_guard"]), result_path=str(result_root), scratch_path=str(scratch_root),
            claim_boundary="one pinned-CPU outer lease across exact opening-1M P/E-A/E-B/decode arms",
        )
        scratch_root.mkdir(mode=0o700)
        population = BASE.copy_prefix(args.corpus.resolve(strict=True), scratch_root / "population.bin", POPULATION_BYTES)
        package, head = BASE.artifact(dependencies["original_package"]), BASE.artifact(dependencies["head"])
        for arm in ("P", "E-A", "E-B"):
            stages[arm] = run_stage(
                arm=arm, result_root=result_root, scratch_root=scratch_root, cgroup_base=cgroup_base,
                population=population, package=package, head=head, archive=None,
                guard_path=dependencies["resource_guard"], lease=lease, cpu=args.cpu,
            )
            if stages[arm]["pass"] is not True:
                raise RuntimeError(f"stage failed: {arm}")
        archive = stages["E-A"]["stage"]["outputs"]["archive"]
        stages["E-decode"] = run_stage(
            arm="E-decode", result_root=result_root, scratch_root=scratch_root, cgroup_base=cgroup_base,
            population=population, package=package, head=head, archive=archive,
            guard_path=dependencies["resource_guard"], lease=lease, cpu=args.cpu,
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
        BASE.write_json_new(verification_path, lease_verification_value)
        terminal = json.loads(evidence.read_text())
        terminal_pass = bool(
            verified and lease_verification_value.get("candidate_id") == CANDIDATE_ID
            and terminal.get("candidate_id") == CANDIDATE_ID and terminal.get("command_sha256") == sequence_sha
            and terminal.get("runner_sha256") == BASE.sha256_file(Path(__file__).resolve(strict=True))
            and terminal.get("guard_path") == str(dependencies["resource_guard"])
            and terminal.get("result_path") == str(result_root) and terminal.get("scratch_path") == str(scratch_root)
            and terminal.get("signal_authority") is False
            and lease_verification_value.get("computed", {}).get("terminal_events") == 1
            and lease_verification_value.get("computed", {}).get("activations") == 0
        )
        if not terminal_pass:
            errors.append("outer_lease_evidence_verification_failed")
    else:
        errors.append("outer_lease_evidence_incomplete")
    if LEASE_PATH.exists() or LEASE_LOCK_PATH.exists():
        errors.append("pinned_outer_lease_namespace_not_clean")

    def output(arm: str, name: str) -> Any:
        stage = stages.get(arm, {}).get("stage")
        return stage.get("outputs", {}).get(name) if isinstance(stage, dict) else None

    payloads = [output(arm, "payload") for arm in ("P", "E-A", "E-B")]
    archives = [output(arm, "archive") for arm in ("P", "E-A", "E-B")]
    restored = output("E-decode", "restored")
    known_payload = all(V3.artifact_matches(item, PAYLOAD_BYTES, PAYLOAD_SHA256) for item in payloads)
    known_archive = all(V3.artifact_matches(item, ARCHIVE_BYTES, ARCHIVE_SHA256) for item in archives)
    fresh_identity = bool(known_payload and known_archive and all(BASE.same_artifact(payloads[0], item) for item in payloads[1:]) and all(BASE.same_artifact(archives[0], item) for item in archives[1:]))
    exact_decode = V3.artifact_matches(restored, POPULATION_BYTES, POPULATION_SHA256)
    guard_pass = len(stages) == 4 and all(value.get("pass") is True for value in stages.values())
    lease_pass = bool(lease_verification_value and lease_verification_value.get("verified") is True and not LEASE_PATH.exists() and not LEASE_LOCK_PATH.exists())
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
    manifest, manifest_pass = V3.result_manifest(result_root)
    source_identity = bool(report["source_closure"] and BASE.artifact(dependencies["source_archive"])["sha256"] == BASE.EXPECTED["source_archive"][2])
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
    if tuple(measurements) != MEASUREMENT_IDS:
        errors.append("flat_measurement_map_drift")
    promotion_evaluations = evaluate(PROMOTION_PREDICATES, measurements)
    kill_evaluations = evaluate(KILL_PREDICATES, measurements)
    applicability_evaluations = inapplicable_evaluations(measurements, witness_supplied)
    promotion_pass = all(row["result"] == "PASS" for row in promotion_evaluations)
    kill_pass = any(row["result"] == "PASS" for row in kill_evaluations)
    optional_pass = all(row["result"] in {"PASS", "N_A"} for row in applicability_evaluations)
    pass_before_cleanup = not errors and promotion_pass and not kill_pass and optional_pass
    if pass_before_cleanup:
        shutil.rmtree(scratch_root)
    cleanup_pass = (not scratch_root.exists()) if pass_before_cleanup else scratch_root.exists()
    if not cleanup_pass:
        errors.append("scratch_cleanup_contract_failed")
    terminal_pass = pass_before_cleanup and cleanup_pass and not errors
    decision = {
        "schema": SCHEMA, "candidate_id": CANDIDATE_ID, "scope_bytes": POPULATION_BYTES,
        "selected_cpu": args.cpu, "coordinator_affinity": sorted(os.sched_getaffinity(0)),
        "exclusive_lease_path": str(LEASE_PATH), "caller_lease_override_supported": False,
        "larger_gate_authorized": False, "next_gate_bytes": None,
        "separately_frozen_100m_experiment_required": True,
        "preflight": report, "stages": stages,
        "flat_measurements": measurements,
        "promotion_predicate_evaluations": promotion_evaluations,
        "kill_predicate_evaluations": kill_evaluations,
        "applicability_evaluations": applicability_evaluations,
        "predicate_summary": {"promotion_pass": promotion_pass, "kill_pass": kill_pass},
        "known_baseline": {"payload": {"bytes": PAYLOAD_BYTES, "sha256": PAYLOAD_SHA256}, "archive": {"bytes": ARCHIVE_BYTES, "sha256": ARCHIVE_SHA256}},
        "package_accounting": {
            "official_score_entries": {"compressor": 468_481, "head": 23_002, "archive": ARCHIVE_BYTES, "compression_command_bytes": 69, "decompression_command_bytes": 31},
            "official_complete_counted_bytes": official_bytes, "added_command_bytes": 100,
            "compression_command": COUNTED_COMPRESS_COMMAND, "decompression_command": COUNTED_DECOMPRESS_COMMAND,
            "evidence_bundle_score_bytes": 0,
        },
        "outer_lease_verification": lease_verification_value,
        "output_manifest": {"policy": "complete-result-artifacts-v1", "decision_self_excluded": True, "artifacts": manifest, "complete": manifest_pass},
        "cleanup": {"scratch_removed_on_pass": terminal_pass and not scratch_root.exists(), "scratch_preserved_on_failure": not terminal_pass and scratch_root.exists()},
        "errors": list(dict.fromkeys(errors)), "terminal_pass": terminal_pass,
        "promotion_authorized": False, "gamma_compression_credit_bytes": 0, "gamma_score_credit_bytes": 0,
        "claim_boundary": "Exact opening-1M output-neutral identity only; memory/runtime/trigger are null N/A and no larger gate is authorized.",
    }
    BASE.write_json_new(result_root / "decision.json", decision)
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0 if terminal_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
