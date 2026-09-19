#!/usr/bin/env python3
"""Independently verify the source-bound q1 Geekbench runtime qualification."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import stat
from typing import Any

import jsonschema

import enwiki9_python_source_closure as python_source
import research_contracts


PROJECT = Path(__file__).resolve().parents[1]
CONTRACTS = PROJECT / "contracts/research/v1"
SOURCE_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-runtime-qualification.schema.json"
OUTPUT_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-runtime-qualification-verification.schema.json"
PLAN_SCHEMA = PROJECT / "operations/planning/cmix-filebacked-fxcm-runtime-plan.schema.json"
HOST_SCHEMA = CONTRACTS / "cmix-runtime-host-fingerprint.schema.json"
STAGE_SCHEMA_PATH = CONTRACTS / "cmix-filebacked-fxcm-runtime-stage.schema.json"
SOURCE_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-runtime-qualification.v1"
OUTPUT_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-runtime-qualification-verification.v1"
PLAN_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-runtime-plan.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
ARM_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1"
ARM_VERIFICATION_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-soft-high-verification.v1"
GUARD_SCHEMA = "gamma.enwiki9.resource-guard-receipt.v3"
STAGE_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-runtime-stage.v1"
WALL_TIME_NUMERATOR = 252_000_000
RSS_LIMIT_KIB = 9_765_625
CGROUP_LIMIT_BYTES = 10_000_000_000
DISK_LIMIT_BYTES = 100_000_000_000
PYTHON = "/usr/bin/python3"
TASKSET = "/usr/bin/taskset"
SCORE_RE = re.compile(r"Single[- ]Core\s+Score\s*:?\s*([0-9][0-9,]*)", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"^\$\{[A-Z0-9_]+\}$")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(16 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def command_sha256(argv: list[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(part) for part in argv)).hexdigest()


def instantiate_plan_command(plan: dict[str, Any], replacements: dict[str, str]) -> list[str]:
    command = [replacements.get(token, token) for token in plan["command"]]
    if any(PLACEHOLDER_RE.fullmatch(token) for token in command):
        raise ValueError("runtime command retains an unresolved placeholder")
    return command


def regular_file(path: Path, label: str) -> Path:
    absolute = (path if path.is_absolute() else Path.cwd() / path).absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"{label}: symlink component forbidden: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise ValueError(f"{label}: expected single-link regular file")
    return absolute.resolve(strict=True)


def artifact(path: Path) -> dict[str, Any]:
    path = regular_file(path, "artifact")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def artifact_matches(record: Any, label: str, allow_empty: bool = False) -> bool:
    if not isinstance(record, dict):
        return False
    try:
        path = regular_file(Path(record["path"]), label)
    except (KeyError, OSError, ValueError):
        return False
    return bool(
        (allow_empty or path.stat().st_size > 0)
        and path.stat().st_size == record.get("bytes")
        and sha256_file(path) == record.get("sha256")
    )


def same_record(left: Any, right: Any) -> bool:
    return bool(
        isinstance(left, dict)
        and isinstance(right, dict)
        and left.get("bytes") == right.get("bytes")
        and left.get("sha256") == right.get("sha256")
    )


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(regular_file(path, "JSON artifact").read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def write_new(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
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


def parse_geekbench5_score(path: Path) -> int:
    text = regular_file(path, "Geekbench report").read_bytes().decode("utf-8", errors="replace")
    if re.search(r"Geekbench\s+5(?:\.|\s|$)", text, re.IGNORECASE) is None:
        raise ValueError("raw report does not identify Geekbench 5")
    scores = [int(value.replace(",", "")) for value in SCORE_RE.findall(text)]
    if len(scores) != 1 or scores[0] <= 0:
        raise ValueError("raw report does not contain exactly one positive single-core score")
    return scores[0]


def current_host_fingerprint() -> dict[str, Any]:
    machine_id = regular_file(Path("/etc/machine-id"), "machine id").read_bytes()
    model_names = sorted(
        {
            line.split(":", 1)[1].strip()
            for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines()
            if line.lower().startswith("model name") and ":" in line
        }
    )
    if not model_names:
        raise ValueError("current host exposes no CPU model name")
    return {
        "schema": "gamma.enwiki9.cmix-runtime-host-fingerprint.v1",
        "machine_id_sha256": hashlib.sha256(machine_id).hexdigest(),
        "uname_machine": platform.machine(),
        "cpu_model_names": model_names,
    }


def closure_rows(entries: tuple[Path, ...]) -> list[dict[str, str]]:
    return [
        {
            "path": path.relative_to(PROJECT).as_posix(),
            "sha256": f"sha256:{sha256_file(path)}",
        }
        for path in python_source.local_source_closure(entries)
    ]


def load_contract(path: Path, schema: str, label: str) -> dict[str, Any]:
    value = load_json(path)
    research_contracts.validate_artifact(path)
    if value.get("schema") != schema:
        raise ValueError(f"{label} schema mismatch")
    return value


def load_direct_contract(
    path: Path, schema_path: Path, schema: str, label: str
) -> dict[str, Any]:
    value = load_json(path)
    jsonschema.Draft202012Validator(
        json.loads(schema_path.read_text(encoding="ascii"))
    ).validate(value)
    if value.get("schema") != schema:
        raise ValueError(f"{label} schema mismatch")
    return value


def bound_plan_file(record: Any, label: str) -> Path:
    if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
        raise ValueError(f"{label} plan binding is malformed")
    path = regular_file(PROJECT / record["path"], label)
    if sha256_file(path) != record["sha256"]:
        raise ValueError(f"{label} plan binding mismatch")
    return path


def expected_stage_argv(
    source: dict[str, Any], phase: str, mode: str, archive: str | None
) -> list[str]:
    execution = source["execution"][phase]
    stage_runner = source["implementation"]["stage_runner"]["path"]
    argv = [
        PYTHON,
        stage_runner,
        "--mode",
        mode,
        "--work-root",
        execution["work_root"],
        "--result-root",
        execution["result_root"],
        "--receipt",
        source["stage_receipts"][phase]["path"],
    ]
    if mode == "encode":
        argv.extend(
            [
                "--corpus",
                source["population"]["path"],
                "--package",
                source["package"]["packaged_compressor"]["path"],
                "--head",
                source["package"]["head"]["path"],
            ]
        )
    else:
        if archive is None:
            raise ValueError("decompression archive is absent")
        argv.extend(["--archive", archive])
    return argv


def expected_guard_argv(
    source: dict[str, Any], phase: str, score: int, stage_argv: list[str]
) -> list[str]:
    execution = source["execution"][phase]
    return [
        TASKSET,
        "--cpu-list",
        str(source["execution"]["selected_logical_cpu"]),
        PYTHON,
        source["implementation"]["resource_guard"]["path"],
        "--limit-kib",
        str(RSS_LIMIT_KIB),
        "--limit-mode",
        "tree",
        "--official-decimal-limit-kib",
        str(RSS_LIMIT_KIB),
        "--sample-interval",
        "0.5",
        "--cgroup-path",
        execution["cgroup_path"],
        "--cgroup-memory-max-bytes",
        str(CGROUP_LIMIT_BYTES),
        "--scratch-path",
        source["execution"]["scratch_root"],
        "--scratch-path",
        source["execution"]["result_root"],
        "--temporary-disk-limit-bytes",
        str(DISK_LIMIT_BYTES),
        "--phase-marker-path",
        execution["phase_marker"],
        "--max-logical-cpus",
        "1",
        "--guard-json",
        source["guards"][phase]["path"],
        "--label",
        f"q1-runtime-{phase}",
        "--phase",
        phase,
        "--geekbench5-single-core-score",
        str(score),
        "--",
        *stage_argv,
    ]


def guard_pass(
    guard: dict[str, Any], phase: str, score: int, stage_argv: list[str]
) -> bool:
    expected_limit = WALL_TIME_NUMERATOR / score
    events = guard["cgroup_events"]["delta"]
    peaks = guard["peaks"]
    return bool(
        guard["schema"] == GUARD_SCHEMA
        and guard["phase"] == phase
        and guard["status"] == "complete"
        and guard["returncode"] == 0
        and guard["command"] == stage_argv
        and guard["command_sha256"] == command_sha256(stage_argv)
        and math.isclose(guard["geekbench5_single_core_score"], score, rel_tol=0.0, abs_tol=1e-9)
        and math.isclose(guard["wall_time_limit_seconds"], expected_limit, rel_tol=0.0, abs_tol=1e-6)
        and guard["elapsed_s"] < expected_limit
        and guard["limit_mode"] == "tree"
        and guard["limit_kib"] == RSS_LIMIT_KIB
        and guard["official_decimal_limit_kib"] == RSS_LIMIT_KIB
        and guard["cgroup"]["requested_memory_max_bytes"] == CGROUP_LIMIT_BYTES
        and guard["cgroup"]["memory_max_bytes"] <= CGROUP_LIMIT_BYTES
        and guard["cgroup"]["joined_before_exec"] is True
        and peaks["max_sampled_tree_rss_kib"] < RSS_LIMIT_KIB
        and peaks["max_observed_process_vmhwm_kib"] < RSS_LIMIT_KIB
        and peaks["cgroup_memory_peak_bytes"] < CGROUP_LIMIT_BYTES
        and peaks["max_sampled_scratch_logical_bytes"] < DISK_LIMIT_BYTES
        and peaks["max_sampled_scratch_allocated_bytes"] < DISK_LIMIT_BYTES
        and peaks["max_sampled_allowed_cpu_count"] <= 1
        and events.get("max", 0) == 0
        and events.get("oom", 0) == 0
        and events.get("oom_kill", 0) == 0
        and events.get("oom_group_kill", 0) == 0
        and all(guard["measurements"].values())
        and not any(guard["guards"].values())
    )


def verify_lease(source: dict[str, Any]) -> bool:
    cleanup = source["cleanup"]
    evidence_record = cleanup["lease_evidence"]
    transition_record = cleanup["lease_transitions"]
    if not artifact_matches(evidence_record, "lease evidence") or not artifact_matches(
        transition_record, "lease transitions"
    ):
        return False
    evidence_path = regular_file(Path(evidence_record["path"]), "lease evidence")
    evidence = load_json(evidence_path)
    transitions = load_json(Path(transition_record["path"]))
    coordinator = source["implementation"]["coordinator"]
    execution = source["execution"]
    if not (
        evidence.get("schema") == "gamma.enwiki9.exclusive-full1g-lease.v1"
        and evidence.get("candidate_id") == f"{CANDIDATE_ID}-runtime"
        and evidence.get("runner_sha256") == coordinator["sha256"]
        and evidence.get("command_sha256") == execution["coordinator_command_sha256"]
        and evidence.get("result_path") == source["execution"]["result_root"]
        and evidence.get("scratch_path") == source["execution"]["scratch_root"]
        and evidence.get("signal_authority") is False
        and transitions.get("schema_version") == "managed-exclusive-lease-transition-log.v1"
        and transitions.get("candidate_id") == f"{CANDIDATE_ID}-runtime"
        and transitions.get("lease_id") == evidence.get("lease_id")
        and isinstance(transitions.get("entries"), list)
        and transitions["entries"]
    ):
        return False
    previous = "0" * 64
    for index, entry in enumerate(transitions["entries"]):
        payload = dict(entry)
        entry_digest = payload.pop("entry_sha256", None)
        if not (
            entry.get("sequence") == index
            and entry.get("previous_entry_sha256") == previous
            and entry.get("lease_sha256") == hashlib.sha256(canonical(entry.get("lease"))).hexdigest()
            and entry_digest == hashlib.sha256(canonical(payload)).hexdigest()
        ):
            return False
        previous = entry_digest
    return bool(
        transitions["entries"][0].get("event") == "lease_acquired"
        and transitions["entries"][-1].get("event") == "terminal_evidence_frozen"
        and transitions["entries"][-1].get("terminal_evidence_sha256") == sha256_file(evidence_path)
        and not Path(cleanup["lease_path"]).exists()
    )


def verify(receipt_path: Path) -> tuple[dict[str, Any], bool]:
    source = load_json(receipt_path)
    jsonschema.Draft202012Validator(json.loads(SOURCE_SCHEMA.read_text(encoding="ascii"))).validate(source)
    if source.get("schema") != SOURCE_SCHEMA_ID or source.get("contract_revision") != 2:
        raise ValueError("runtime receipt identity mismatch")
    checks: dict[str, bool] = {}
    checks["source_terminal_pass"] = source["terminal_pass"] is True and source["runtime_eligible"] is True and source["errors"] == []
    checks["objective_binding_pass"] = source["objective"] == research_contracts.objective_binding()
    checks["source_artifacts_match"] = all(
        artifact_matches(record, label)
        for label, record in (
            ("plan", source["antecedents"]["plan"]),
            ("Python source closure", source["antecedents"]["python_source_closure"]),
            ("Arm A receipt", source["antecedents"]["arm_a_receipt"]),
            ("Arm A verification", source["antecedents"]["arm_a_verification"]),
            ("Arm B receipt", source["antecedents"]["arm_b_receipt"]),
            ("Arm B verification", source["antecedents"]["arm_b_verification"]),
            ("population", source["population"]),
            ("benchmark report", source["benchmark"]["raw_report"]),
            ("host fingerprint", source["benchmark"]["host_fingerprint"]),
            ("packaged compressor", source["package"]["packaged_compressor"]),
            ("head", source["package"]["head"]),
            ("reference archive", source["package"]["archive"]),
            ("compression guard", source["guards"]["compression"]),
            ("decompression guard", source["guards"]["decompression"]),
            ("compression stage", source["stage_receipts"]["compression"]),
            ("decompression stage", source["stage_receipts"]["decompression"]),
            ("output payload", source["outputs"]["payload"]),
            ("output archive", source["outputs"]["archive"]),
            ("restored corpus", source["outputs"]["restored"]),
        )
    ) and all(
        artifact_matches(record, f"implementation {name}")
        for name, record in source["implementation"].items()
    )

    plan_path = Path(source["antecedents"]["plan"]["path"])
    plan = load_json(plan_path)
    jsonschema.Draft202012Validator(json.loads(PLAN_SCHEMA.read_text(encoding="ascii"))).validate(plan)
    checks["plan_contract_pass"] = bool(
        plan.get("$schema") == PLAN_SCHEMA_ID
        and plan.get("execution_authorized") is True
        and plan.get("working_directory") == str(PROJECT)
        and source["execution"]["working_directory"] == str(PROJECT)
    )
    current_implementation = {
        name: artifact(bound_plan_file(record, f"plan implementation {name}"))
        for name, record in plan["implementation"].items()
        if name != "python_source_closure"
    }
    checks["implementation_exact"] = current_implementation == source["implementation"]
    closure_path = bound_plan_file(plan["implementation"]["python_source_closure"], "runtime source closure")
    roots = tuple(
        regular_file(PROJECT / value, f"runtime closure root {index}")
        for index, value in enumerate(plan["source_closure_roots"])
    )
    checks["python_source_closure_exact"] = (
        artifact(closure_path) == source["antecedents"]["python_source_closure"]
        and json.loads(closure_path.read_text(encoding="ascii")) == closure_rows(roots)
    )

    arm_a_path = Path(source["antecedents"]["arm_a_receipt"]["path"])
    arm_b_path = Path(source["antecedents"]["arm_b_receipt"]["path"])
    arm_a = load_contract(arm_a_path, ARM_SCHEMA, "Arm A")
    arm_b = load_contract(arm_b_path, ARM_SCHEMA, "Arm B")
    verification_a = load_contract(
        Path(source["antecedents"]["arm_a_verification"]["path"]),
        ARM_VERIFICATION_SCHEMA,
        "Arm A verification",
    )
    verification_b = load_contract(
        Path(source["antecedents"]["arm_b_verification"]["path"]),
        ARM_VERIFICATION_SCHEMA,
        "Arm B verification",
    )
    checks["independent_full_arms_pass"] = bool(
        arm_a["arm"] == "a"
        and arm_b["arm"] == "b"
        and arm_a["terminal_pass"] is True
        and arm_b["terminal_pass"] is True
        and verification_a["verification_pass"] is True
        and verification_b["verification_pass"] is True
        and verification_a["source_receipt"] == artifact(arm_a_path)
        and verification_b["source_receipt"] == artifact(arm_b_path)
        and all(verification_a["checks"].values())
        and all(verification_b["checks"].values())
        and all(value is True for value in arm_b["identity"]["arm_a"].values())
    )
    checks["arm_a_b_artifact_identity"] = all(
        same_record(arm_a[left][name], arm_b[left][name])
        for left, names in (
            ("package", ("packaged_compressor", "head")),
            ("outputs", ("payload", "archive", "restored")),
        )
        for name in names
    )
    checks["exact_arm_a_package_bound"] = bool(
        source["package"]["packaged_compressor"] == arm_a["package"]["packaged_compressor"]
        and source["package"]["head"] == arm_a["package"]["head"]
        and source["package"]["archive"] == arm_a["outputs"]["archive"]
    )

    parsed_score = parse_geekbench5_score(Path(source["benchmark"]["raw_report"]["path"]))
    score = source["benchmark"]["single_core_score"]
    checks["geekbench5_report_rederived"] = parsed_score == score
    fingerprint = load_json(Path(source["benchmark"]["host_fingerprint"]["path"]))
    jsonschema.Draft202012Validator(json.loads(HOST_SCHEMA.read_text(encoding="ascii"))).validate(fingerprint)
    checks["current_host_fingerprint_exact"] = fingerprint == current_host_fingerprint()

    guards = {
        phase: load_contract(Path(source["guards"][phase]["path"]), GUARD_SCHEMA, f"{phase} guard")
        for phase in ("compression", "decompression")
    }
    stages = {
        phase: load_direct_contract(
            Path(source["stage_receipts"][phase]["path"]),
            STAGE_SCHEMA_PATH,
            STAGE_SCHEMA,
            f"{phase} stage",
        )
        for phase in ("compression", "decompression")
    }
    compression_stage_argv = expected_stage_argv(source, "compression", "encode", None)
    decompression_stage_argv = expected_stage_argv(
        source, "decompression", "decode", source["outputs"]["archive"]["path"]
    )
    command_pairs = {
        "compression": (compression_stage_argv, expected_guard_argv(source, "compression", score, compression_stage_argv)),
        "decompression": (decompression_stage_argv, expected_guard_argv(source, "decompression", score, decompression_stage_argv)),
    }
    checks["exact_command_contract"] = all(
        source["execution"][phase]["stage_argv"] == stage_argv
        and source["execution"][phase]["guard_argv"] == guard_argv
        and source["execution"][phase]["stage_command_sha256"] == command_sha256(stage_argv)
        and source["execution"][phase]["guard_command_sha256"] == command_sha256(guard_argv)
        for phase, (stage_argv, guard_argv) in command_pairs.items()
    )
    checks["compression_guard_pass"] = guard_pass(guards["compression"], "compression", score, compression_stage_argv)
    checks["decompression_guard_pass"] = guard_pass(guards["decompression"], "decompression", score, decompression_stage_argv)
    encode = stages["compression"]
    decode = stages["decompression"]
    checks["stages_pass"] = bool(
        encode["mode"] == "encode"
        and decode["mode"] == "decode"
        and encode["return_code"] == decode["return_code"] == 0
        and encode["stage_pass"] is True
        and decode["stage_pass"] is True
        and encode["backing_cleanup_pass"] is True
        and decode["backing_cleanup_pass"] is True
        and decode["exact_raw_inverse_pass"] is True
        and encode["stage_runner"] == source["implementation"]["stage_runner"]
        and decode["stage_runner"] == source["implementation"]["stage_runner"]
    )
    checks["stage_inputs_exact"] = bool(
        encode["inputs"]["package"] == source["package"]["packaged_compressor"]
        and encode["inputs"]["head"] == source["package"]["head"]
        and encode["inputs"]["corpus"] == source["population"]
        and decode["inputs"]["archive"] == source["outputs"]["archive"]
        and encode["population"]
        == {"bytes": source["population"]["bytes"], "sha256": source["population"]["sha256"]}
        and decode["population"] == encode["population"]
        and "corpus" not in decode["inputs"]
        and same_record(decode["outputs"]["restored"], source["population"])
    )
    checks["codec_commands_corpus_independent"] = bool(
        encode["command"] == ["./cmix", "-e", encode["inputs"]["corpus"]["path"], "out.cmix"]
        and decode["command"] == ["./archive9"]
        and source["population"]["path"] not in decompression_stage_argv
    )
    checks["archive_and_inverse_bound"] = bool(
        encode["outputs"]["payload"] == source["outputs"]["payload"]
        and encode["outputs"]["archive"] == source["outputs"]["archive"]
        and decode["outputs"]["restored"] == source["outputs"]["restored"]
        and same_record(source["outputs"]["payload"], arm_a["outputs"]["payload"])
        and same_record(source["outputs"]["archive"], arm_a["outputs"]["archive"])
        and same_record(source["outputs"]["restored"], arm_a["outputs"]["restored"])
        and all(source["identities"].values())
    )
    cleanup = source["cleanup"]
    checks["cleanup_complete"] = bool(
        cleanup["scratch_removed_on_success_pass"] is True
        and cleanup["scratch_preserved_on_failure"] is False
        and cleanup["cgroup_removed_pass"] is True
        and cleanup["lease_removed_pass"] is True
        and cleanup["lease_release_pass"] is True
        and not Path(cleanup["scratch_root"]).exists()
        and not Path(cleanup["cgroup_path"]).exists()
        and not Path(cleanup["lease_path"]).exists()
        and not Path(cleanup["lease_path"]).with_name(Path(cleanup["lease_path"]).name + ".lock").exists()
        and cleanup["scratch_root"] == source["execution"]["scratch_root"]
    )
    checks["managed_lease_chain_pass"] = verify_lease(source)
    expected_coordinator_argv = instantiate_plan_command(
        plan,
        {
            "${ARM_A_RECEIPT}": source["antecedents"]["arm_a_receipt"]["path"],
            "${ARM_A_VERIFICATION}": source["antecedents"]["arm_a_verification"]["path"],
            "${ARM_B_RECEIPT}": source["antecedents"]["arm_b_receipt"]["path"],
            "${ARM_B_VERIFICATION}": source["antecedents"]["arm_b_verification"]["path"],
            "${GEEKBENCH5_REPORT}": source["benchmark"]["raw_report"]["path"],
            "${RESULT_ROOT}": source["execution"]["result_root"],
            "${SCRATCH_ROOT}": source["execution"]["scratch_root"],
            "${CGROUP_PATH}": cleanup["cgroup_path"],
            "${LEASE_TRANSITION}": cleanup["lease_transitions"]["path"],
            "${CPU}": str(source["execution"]["selected_logical_cpu"]),
        },
    )
    checks["coordinator_command_bound"] = bool(
        source["execution"]["coordinator_argv"] == expected_coordinator_argv
        and source["execution"]["coordinator_command_sha256"]
        == command_sha256(expected_coordinator_argv)
    )

    expected_limit = WALL_TIME_NUMERATOR / score
    runtime_eligible = all(checks.values())
    derived = {
        "geekbench5_single_core_score": score,
        "wall_time_limit_seconds": expected_limit,
        "compression_elapsed_seconds": guards["compression"]["elapsed_s"],
        "decompression_elapsed_seconds": guards["decompression"]["elapsed_s"],
        "compression_runtime_pass": checks["compression_guard_pass"],
        "decompression_runtime_pass": checks["decompression_guard_pass"],
        "runtime_eligible": runtime_eligible,
    }
    errors = [f"check failed: {name}" for name, passed in checks.items() if not passed]
    output = {
        "schema": OUTPUT_SCHEMA_ID,
        "contract_revision": 2,
        "candidate_id": CANDIDATE_ID,
        "source_receipt": artifact(receipt_path),
        "evidence": {
            "plan": artifact(plan_path),
            "python_source_closure": artifact(closure_path),
            "coordinator": artifact(Path(source["implementation"]["coordinator"]["path"])),
            "verifier": artifact(Path(__file__).resolve(strict=True)),
            "source_schema": artifact(SOURCE_SCHEMA),
            "verification_schema": artifact(OUTPUT_SCHEMA),
        },
        "checks": checks,
        "derived": derived,
        "errors": errors,
        "verification_pass": not errors,
        "claim_boundary": (
            "Independent exact-package runtime verification on the Geekbench-5-measured host only; "
            "no compression or score credit."
        ),
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.Draft202012Validator(json.loads(OUTPUT_SCHEMA.read_text(encoding="ascii"))).validate(output)
    return output, not errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt_path = regular_file(args.receipt, "runtime receipt")
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit("output already exists")
    output, passed = verify(receipt_path)
    write_new(args.output, output)
    print(json.dumps(output, sort_keys=True, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
