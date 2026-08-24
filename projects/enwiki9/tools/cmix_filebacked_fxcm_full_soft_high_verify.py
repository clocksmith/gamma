#!/usr/bin/env python3
"""Independently verify a passing soft-pressure q1 full-corpus arm."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType
from typing import Any

import jsonschema
import research_contracts


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-soft-high-verification.v1"
PROJECT = Path(__file__).resolve().parents[1]
RESULT = PROJECT / "results/cmix_filebacked_fxcm_full_a_qm8_v1"
SCRATCH = PROJECT / "scratch/cmix_filebacked_fxcm_full_a_qm8_v1"
CGROUP = Path(
    "/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/"
    "app.slice/gamma-q1-full-a-qm8-v1"
)
LEASE = PROJECT / "operations/runtime/exclusive_full1g.json"
LOCK = PROJECT / "operations/runtime/exclusive_full1g.json.lock"
LEASE_VERIFIER = PROJECT / "tools/managed_exclusive_lease_verify.py"
SCHEMA_PATH = PROJECT / "contracts/research/v1/cmix-filebacked-fxcm-full-soft-high-verification.schema.json"
PLAN = (
    PROJECT
    / "operations/planning/"
    "cmix_filebacked_fxcm_full_a_qm8_soft_high_verification_v1.json"
)
PLAN_SCHEMA = PROJECT / "operations/planning/campaign-static-contract.schema.json"
SOURCE_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1"
STAGE_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-stage.v1"
GUARD_SCHEMA = "gamma.enwiki9.resource-guard-receipt.v3"
SOFT_HIGH_SCHEMA = "gamma.enwiki9.resource-guard-soft-high.v1"
CANONICAL_BYTES = 1_000_000_000
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
PARENT_PAYLOAD_BYTES = 107_730_531
PARENT_PAYLOAD_SHA256 = "889aa8074e0a84eb89997986899f1ef9f7cc0e52e87d1d36f86899fc679f5490"
HARD_MEMORY_MAX_BYTES = 9_999_998_976
SOFT_MEMORY_HIGH_BYTES = 8_999_997_440
MEMORY_LIMIT_KIB = 9_765_625
PYTHON = "/usr/bin/python3"
EXPECTED_WRAPPER_SHA256 = "d2838c816bf17c5108fd0cf7170180ea8d47decbd3009f26ddf6bb7a02d05bae"
EXPECTED_GUARD_SHA256 = "044147f7ffe6922ea8dafd52fc3d4426077b20958adbcd421245ad41adcfc1e4"
EXPECTED_ROUNDTRIP_SHA256 = "b196cddcef51e890794fa3877e5763b13c695ddd3ad1e1065eb9a584fce2f20b"
EXPECTED_STAGE_SHA256 = "e8aed4cbe68ba162a1d30a66bdf3243c70226268a9f23dbdb4bc4bef31354741"
ANTECEDENT_SCHEMAS = {
    "build_receipt": "gamma.enwiki9.cmix-filebacked-fxcm-build-receipt.v1",
    "build_verification": "gamma.enwiki9.cmix-filebacked-fxcm-build-verification.v1",
    "scope_build_receipt": "gamma.enwiki9.cmix-filebacked-fxcm-scope-build.v1",
    "program_lock_verification": "gamma.enwiki9.cmix-filebacked-fxcm-program-lock-verification.v1",
    "transfer_receipt": "gamma.enwiki9.cmix-filebacked-fxcm-transfer-10m.v1",
    "transfer_verification": "gamma.enwiki9.cmix-filebacked-fxcm-identity-verification.v1",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(16 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def regular(path: Path, label: str) -> Path:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label} has a symlink component: {current}")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label} is not a single-link regular file: {path}")
    return path.resolve(strict=True)


def artifact(path: Path) -> dict[str, Any]:
    path = regular(path, "artifact")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def artifact_matches(record: dict[str, Any] | None) -> bool:
    if not isinstance(record, dict):
        return False
    path = Path(record.get("path", ""))
    try:
        path = regular(path, "artifact record")
    except (OSError, RuntimeError):
        return False
    return bool(
        path.stat().st_size == record.get("bytes")
        and sha256_file(path) == record.get("sha256")
    )


def artifact_at(record: dict[str, Any] | None, expected: Path) -> bool:
    if not artifact_matches(record):
        return False
    try:
        return Path(record["path"]).resolve(strict=True) == expected.resolve(strict=True)
    except OSError:
        return False


def command_sha256(argv: list[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(item) for item in argv)).hexdigest()


def expected_stage_command(phase: str, source: dict[str, Any]) -> list[str]:
    command = [
        PYTHON,
        str(PROJECT / "tools/cmix_filebacked_fxcm_full_stage.py"),
        "--mode",
        phase,
        "--corpus",
        source["population"]["path"],
        "--work-root",
        str(SCRATCH / phase),
        "--result-root",
        str(RESULT / phase),
        "--receipt",
        str(RESULT / phase / "stage-receipt.json"),
    ]
    if phase == "encode":
        command.extend(
            [
                "--package",
                source["package"]["packaged_compressor"]["path"],
                "--head",
                source["package"]["head"]["path"],
            ]
        )
    else:
        command.extend(["--archive", source["outputs"]["archive"]["path"]])
    return command


def expected_guard_command(
    phase: str, source: dict[str, Any], stage_command: list[str]
) -> list[str]:
    return [
        "/usr/bin/taskset",
        "--cpu-list",
        str(source["selected_logical_cpu"]),
        PYTHON,
        str(PROJECT / "tools/run_with_resource_guard_v3_soft_high.py"),
        "--limit-kib",
        "9765625",
        "--limit-mode",
        "tree",
        "--official-decimal-limit-kib",
        "9765625",
        "--cgroup-path",
        str(CGROUP),
        "--cgroup-memory-max-bytes",
        "10000000000",
        "--scratch-path",
        str(SCRATCH),
        "--scratch-path",
        str(RESULT),
        "--temporary-disk-limit-bytes",
        "100000000000",
        "--phase-marker-path",
        str(RESULT / phase / "phase-markers.jsonl"),
        "--max-logical-cpus",
        "1",
        "--guard-json",
        str(RESULT / phase / "guard.json"),
        "--label",
        f"q1-full-{phase}",
        "--phase",
        "diagnostic",
        "--",
        *stage_command,
    ]


def load_module(path: Path, name: str) -> ModuleType:
    path = regular(path, name)
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    if Path(str(module.__file__)).resolve(strict=True) != path:
        raise RuntimeError(f"loaded {name} from wrong source")
    return module


def plan_binding(record: Any, expected: Path, label: str) -> None:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise RuntimeError(f"{label} plan binding malformed")
    declared = Path(record["path"])
    path = declared if declared.is_absolute() else PROJECT / declared
    path = regular(path, label)
    if path != expected.resolve(strict=True):
        raise RuntimeError(f"{label} plan path mismatch")
    if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
        raise RuntimeError(f"{label} plan identity mismatch")


def live_qm8_processes() -> list[int]:
    ancestors: set[int] = set()
    cursor = os.getpid()
    while cursor > 1 and cursor not in ancestors:
        ancestors.add(cursor)
        try:
            suffix = (Path("/proc") / str(cursor) / "stat").read_text(
                encoding="ascii"
            ).rsplit(")", 1)[1]
            cursor = int(suffix.split()[1])
        except (OSError, IndexError, ValueError):
            break
    found: list[int] = []
    for path in Path("/proc").iterdir():
        if not path.name.isdigit() or int(path.name) in ancestors:
            continue
        try:
            command = (path / "cmdline").read_bytes().replace(b"\0", b" ")
        except OSError:
            continue
        if b"cmix_filebacked_fxcm_full_a_qm8_v1" in command:
            found.append(int(path.name))
    return sorted(found)


def validate_activation(receipt_path: Path) -> None:
    plan_path = regular(PLAN, "qm8 success-verification plan")
    plan_schema_path = regular(PLAN_SCHEMA, "campaign static-contract schema")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan_schema = json.loads(plan_schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(plan_schema)
    jsonschema.Draft202012Validator(plan_schema).validate(plan)
    contract = plan.get("contract", {})
    activation = contract.get("activation", {})
    source = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        plan.get("artifact_id")
        != "cmix_filebacked_fxcm_full_a_qm8_soft_high_verification_v1"
        or plan.get("revision", 0) < 2
        or plan.get("claim_authority") != "none"
        or contract.get("candidate_id") != "cmix_filebacked_fxcm_full_a_qm8_v1"
        or contract.get("source_receipt") != str(receipt_path)
        or contract.get("output") != str(RESULT / "full-soft-high-verification.json")
        or activation.get("status") != "activated_after_terminal_passing_qm8"
        or activation.get("execution_authorized") is not True
        or activation.get("terminal_receipt_sha256") != sha256_file(receipt_path)
        or source.get("schema") != SOURCE_SCHEMA
        or source.get("candidate_id")
        != "cmix_obias_memory_safe_parent_filebacked_q1_v1"
        or source.get("arm") != "a"
        or source.get("terminal_pass") is not True
        or live_qm8_processes()
        or contract.get("promotion_authority") is not False
        or contract.get("memory_safe_parent_qualification_authority") is not False
        or contract.get("gamma_compression_credit_bytes") != 0
        or contract.get("gamma_score_credit_bytes") != 0
    ):
        raise RuntimeError("qm8 success-verification plan is not receipt-bound revision 2")
    expected_bindings = {
        "verifier": PROJECT / "tools/cmix_filebacked_fxcm_full_soft_high_verify.py",
        "verification_schema": SCHEMA_PATH,
        "research_contracts": PROJECT / "tools/research_contracts.py",
        "lease_verifier": LEASE_VERIFIER,
        "plan_schema": PLAN_SCHEMA,
        "python_runtime": Path("/usr/bin/python3.14"),
        "full_roundtrip_schema": PROJECT / "contracts/research/v1/cmix-filebacked-fxcm-full-roundtrip.schema.json",
        "stage_schema": PROJECT / "contracts/research/v1/cmix-filebacked-fxcm-full-stage.schema.json",
        "guard_schema": PROJECT / "contracts/research/v1/resource-guard-receipt.v3.schema.json",
        "soft_high_schema": PROJECT / "contracts/research/v1/resource-guard-soft-high.schema.json",
        "roundtrip_runner": PROJECT / "tools/cmix_filebacked_fxcm_full_roundtrip.py",
        "stage_runner": PROJECT / "tools/cmix_filebacked_fxcm_full_stage.py",
        "soft_high_wrapper": PROJECT / "tools/run_with_resource_guard_v3_soft_high.py",
        "resource_guard": PROJECT / "tools/run_with_resource_guard_v3.py",
    }
    bindings = contract.get("bindings", {})
    for name, expected in expected_bindings.items():
        plan_binding(bindings.get(name), expected, name)
    expected_command = [
        "/usr/bin/python3.14",
        "tools/cmix_filebacked_fxcm_full_soft_high_verify.py",
        "--receipt",
        "results/cmix_filebacked_fxcm_full_a_qm8_v1/full-roundtrip-receipt.json",
        "--output",
        "results/cmix_filebacked_fxcm_full_a_qm8_v1/full-soft-high-verification.json",
    ]
    if contract.get("command") != expected_command:
        raise RuntimeError("qm8 success-verification command mismatch")


def validate_output(value: dict[str, Any]) -> None:
    schema_path = regular(SCHEMA_PATH, "qm8 success-verification schema")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)


def write_new(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600
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


def validate_contract(path: Path, schema: str) -> dict[str, Any]:
    value = json.loads(path.read_text())
    research_contracts.validate_artifact(path)
    if value.get("schema") != schema:
        raise RuntimeError(f"{path}: expected schema {schema}")
    return value


def stage_checks(
    *,
    phase: str,
    source: dict[str, Any],
    result_root: Path,
    checks: dict[str, bool],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    summary = source["stages"][phase]
    guard_path = Path(summary["guard_receipt"]["path"])
    stage_path = Path(summary["stage_receipt"]["path"])
    soft_path = guard_path.with_name("soft-high-receipt.json")
    guard = validate_contract(guard_path, GUARD_SCHEMA)
    stage = validate_contract(stage_path, STAGE_SCHEMA)
    soft = validate_contract(soft_path, SOFT_HIGH_SCHEMA)
    events = guard["cgroup_events"]["delta"]
    stage_command = expected_stage_command(phase, source)
    checks[f"{phase}_summary_artifacts_match"] = (
        artifact_at(summary["guard_receipt"], result_root / phase / "guard.json")
        and artifact_at(
            summary["stage_receipt"], result_root / phase / "stage-receipt.json"
        )
        and artifact_at(
            summary["guard_stdout"], result_root / phase / "guard.stdout"
        )
        and artifact_at(
            summary["guard_stderr"], result_root / phase / "guard.stderr"
        )
        and soft_path.resolve(strict=True)
        == (result_root / phase / "soft-high-receipt.json").resolve(strict=True)
    )
    checks[f"{phase}_command_binding"] = (
        guard["command"] == stage_command
        and guard["command_sha256"] == command_sha256(stage_command)
        and summary["stage_command_sha256"] == guard["command_sha256"]
        and summary["guard_command_sha256"]
        == command_sha256(expected_guard_command(phase, source, stage_command))
    )
    checks[f"{phase}_guard_complete"] = (
        guard["status"] == "complete"
        and guard["returncode"] == 0
        and summary["outer_return_code"] == 0
        and summary["guard_status"] == guard["status"]
        and summary["guard_return_code"] == guard["returncode"]
        and not any(guard["guards"].values())
        and all(guard["measurements"].values())
    )
    checks[f"{phase}_hard_memory_clean"] = (
        guard["cgroup"]["memory_max_bytes"] == HARD_MEMORY_MAX_BYTES
        and guard["peaks"]["cgroup_memory_peak_bytes"] <= HARD_MEMORY_MAX_BYTES
        and events.get("max", 0) == 0
        and events.get("oom", 0) == 0
        and events.get("oom_kill", 0) == 0
        and events.get("oom_group_kill", 0) == 0
    )
    checks[f"{phase}_guard_contract"] = (
        guard["phase"] == "diagnostic"
        and guard["label"] == f"q1-full-{phase}"
        and guard["limit_mode"] == "tree"
        and guard["limit_kib"] == MEMORY_LIMIT_KIB
        and guard["official_decimal_limit_kib"] == MEMORY_LIMIT_KIB
        and guard["temporary_disk_limit_bytes"] == 100_000_000_000
        and guard["max_logical_cpus"] == 1
        and guard["scratch_paths"] == [str(SCRATCH), str(RESULT)]
        and guard["phase_marker_path"]
        == str(result_root / phase / "phase-markers.jsonl")
        and guard["cgroup"]["path"] == str(CGROUP)
        and guard["cgroup"]["requested_memory_max_bytes"] == 10_000_000_000
        and guard["cgroup"]["memory_max_bytes"] == HARD_MEMORY_MAX_BYTES
    )
    checks[f"{phase}_rss_cpu_disk_clean"] = (
        guard["peaks"]["max_sampled_tree_rss_kib"] < MEMORY_LIMIT_KIB
        and guard["peaks"]["max_observed_process_vmhwm_kib"] < MEMORY_LIMIT_KIB
        and guard["peaks"]["max_sampled_allowed_cpu_count"] == 1
        and max(
            guard["peaks"]["max_sampled_scratch_logical_bytes"],
            guard["peaks"]["max_sampled_scratch_allocated_bytes"],
        ) < guard["temporary_disk_limit_bytes"]
    )
    checks[f"{phase}_summary_measurements"] = (
        summary["maximum_tree_rss_kib"]
        == guard["peaks"]["max_sampled_tree_rss_kib"]
        and summary["cgroup_memory_peak_bytes"]
        == guard["peaks"]["cgroup_memory_peak_bytes"]
        and summary["maximum_temporary_disk_bytes"]
        == max(
            guard["peaks"]["max_sampled_scratch_logical_bytes"],
            guard["peaks"]["max_sampled_scratch_allocated_bytes"],
        )
        and summary["maximum_allowed_cpu_count"]
        == guard["peaks"]["max_sampled_allowed_cpu_count"]
        and summary["stage_return_code"] == stage["return_code"]
        and summary["backing_cleanup_pass"] == stage["backing_cleanup_pass"]
        and summary["exact_raw_inverse_pass"] == stage["exact_raw_inverse_pass"]
        and summary["cgroup_cleanup_pass"] is True
        and summary["errors"] == []
        and summary["stage_and_guard_pass"] is True
    )
    checks[f"{phase}_stage_complete"] = (
        stage["mode"] == phase
        and stage["return_code"] == 0
        and stage["stage_pass"] is True
        and stage["backing_cleanup_pass"] is True
    )
    checks[f"{phase}_stage_provenance"] = (
        artifact_at(stage["corpus"], Path(source["population"]["path"]))
        and stage["corpus"] == source["population"]
        and artifact_at(
            stage["stage_runner"],
            PROJECT / "tools/cmix_filebacked_fxcm_full_stage.py",
        )
        and stage["stage_runner"]["sha256"] == EXPECTED_STAGE_SHA256
        and artifact_at(
            stage["phase_marker"], result_root / phase / "phase-markers.jsonl"
        )
        and stage["work_root"] == str(SCRATCH / phase)
        and stage["result_root"] == str(result_root / phase)
        and stage["command"]
        == (
            ["./cmix", "-e", source["population"]["path"], "out.cmix"]
            if phase == "encode"
            else ["./archive9"]
        )
        and all(
            artifact_matches(record)
            for group in (stage["inputs"], stage["outputs"])
            for record in group.values()
        )
        and stage["inputs"]
        == (
            {
                "package": source["package"]["packaged_compressor"],
                "head": source["package"]["head"],
            }
            if phase == "encode"
            else {"archive": source["outputs"]["archive"]}
        )
        and stage["outputs"]
        == (
            {
                "payload": source["outputs"]["payload"],
                "archive": source["outputs"]["archive"],
            }
            if phase == "encode"
            else {"restored": source["outputs"]["restored"]}
        )
        and stage["execution_authority"] is False
        and stage["gamma_compression_credit_bytes"] == 0
        and stage["gamma_score_credit_bytes"] == 0
    )
    checks[f"{phase}_soft_pressure_bound"] = (
        soft["wrapper_pass"] is True
        and soft["effective_memory_high_bytes"] == SOFT_MEMORY_HIGH_BYTES
        and soft["memory_high_restore_pass"] is True
        and soft["guard_return_code"] == 0
        and soft["guard_status"] == "complete"
        and artifact_matches(soft["underlying_guard"])
        and soft["underlying_guard"]["sha256"] == EXPECTED_GUARD_SHA256
        and Path(soft["underlying_guard"]["path"]).resolve(strict=True)
        == (PROJECT / "tools/run_with_resource_guard_v3.py").resolve(strict=True)
        and artifact_matches(soft["guard_receipt"])
        and Path(soft["guard_receipt"]["path"]).resolve() == guard_path.resolve()
        and not Path(soft["cgroup_path"]).exists()
        and soft["cgroup_path"] == str(CGROUP)
        and soft["high_event_count"] == events["high"]
    )
    checks[f"{phase}_soft_pressure_observed"] = isinstance(soft["high_event_count"], int) and soft["high_event_count"] >= 0
    checks[f"{phase}_result_ownership"] = (
        guard_path.parent == result_root / phase
        and stage_path.parent == result_root / phase
    )
    return guard, stage, soft


def verify(receipt_path: Path) -> tuple[dict[str, Any], bool]:
    source = validate_contract(receipt_path, SOURCE_SCHEMA)
    result_root = receipt_path.parent
    arm = source["arm"]
    antecedents = source["antecedents"]
    checks: dict[str, bool] = {
        "source_terminal_pass": source["terminal_pass"] is True,
        "source_arm_supported": arm in {"a", "b"},
        "source_zero_credit_boundary": source["memory_safe_parent_qualified"] is False
        and source["promotion_authorized"] is False
        and source["gamma_compression_credit_bytes"] == 0
        and source["gamma_score_credit_bytes"] == 0,
        "population_exact": source["population"]["bytes"] == CANONICAL_BYTES
        and source["population"]["sha256"] == CANONICAL_SHA256
        and artifact_matches(source["population"]),
        "resource_wrapper_exact": artifact_at(
            source["resource_guard"],
            PROJECT / "tools/run_with_resource_guard_v3_soft_high.py",
        )
        and source["resource_guard"]["sha256"] == EXPECTED_WRAPPER_SHA256,
        "roundtrip_runner_exact": artifact_at(
            source["runner"], PROJECT / "tools/cmix_filebacked_fxcm_full_roundtrip.py"
        )
        and source["runner"]["sha256"] == EXPECTED_ROUNDTRIP_SHA256,
        "stage_runner_exact": artifact_at(
            source["stage_runner"], PROJECT / "tools/cmix_filebacked_fxcm_full_stage.py"
        )
        and source["stage_runner"]["sha256"] == EXPECTED_STAGE_SHA256,
        "antecedent_artifacts_match": all(
            artifact_matches(record)
            for record in antecedents.values()
            if record is not None
        ),
    }
    for name, schema in ANTECEDENT_SCHEMAS.items():
        validate_contract(Path(antecedents[name]["path"]), schema)
    checks["antecedent_contracts_valid"] = True
    encode_guard, encode_stage, encode_soft = stage_checks(
        phase="encode", source=source, result_root=result_root, checks=checks
    )
    decode_guard, decode_stage, decode_soft = stage_checks(
        phase="decode", source=source, result_root=result_root, checks=checks
    )
    package = source["package"]
    package_parts = [
        Path(package[name]["path"])
        for name in ("raw_binary", "dictionary_payload", "article_order_payload", "header")
    ]
    packaged_path = Path(package["packaged_compressor"]["path"])
    digest = hashlib.sha256()
    concatenated_bytes = 0
    for part in package_parts:
        with part.open("rb") as stream:
            for block in iter(lambda: stream.read(16 << 20), b""):
                digest.update(block)
                concatenated_bytes += len(block)
    checks["package_artifacts_match"] = all(
        artifact_matches(package[name])
        for name in (
            "raw_binary",
            "dictionary_payload",
            "article_order_payload",
            "header",
            "packaged_compressor",
            "head",
            "build_verification",
        )
    )
    checks["package_result_ownership"] = (
        Path(package["packaged_compressor"]["path"]).resolve(strict=True)
        == (result_root / "package/cmix").resolve(strict=True)
        and Path(package["head"]["path"]).resolve(strict=True)
        == (result_root / "package/head.blob").resolve(strict=True)
        and package["arm"] == "a"
    )
    checks["package_mechanical_concatenation"] = (
        concatenated_bytes == packaged_path.stat().st_size
        and digest.hexdigest() == sha256_file(packaged_path)
        and package["mechanical_concatenation_pass"] is True
    )
    checks["program_bytes_rederived"] = (
        package["program_bytes"]
        == package["packaged_compressor"]["bytes"] + package["head"]["bytes"]
        == packaged_path.stat().st_size + Path(package["head"]["path"]).stat().st_size
    )
    outputs = source["outputs"]
    checks["payload_exact_parent"] = (
        artifact_at(outputs["payload"], result_root / "encode/out.cmix")
        and outputs["payload"]["bytes"] == PARENT_PAYLOAD_BYTES
        and outputs["payload"]["sha256"] == PARENT_PAYLOAD_SHA256
        and encode_stage["outputs"]["payload"] == outputs["payload"]
    )
    checks["archive_exactly_bound"] = (
        artifact_at(outputs["archive"], result_root / "encode/archive9")
        and encode_stage["outputs"]["archive"] == outputs["archive"]
    )
    checks["restored_exact_canonical"] = (
        artifact_at(outputs["restored"], result_root / "decode/enwik9-restored")
        and outputs["restored"]["bytes"] == CANONICAL_BYTES
        and outputs["restored"]["sha256"] == CANONICAL_SHA256
        and decode_stage["outputs"]["restored"] == outputs["restored"]
        and decode_stage["exact_raw_inverse_pass"] is True
        and source["identity"]["exact_raw_inverse_pass"] is True
    )
    counted_score = outputs["archive"]["bytes"] + package["program_bytes"]
    checks["accounting_rederived"] = (
        source["accounting"]["archive_bytes"] == outputs["archive"]["bytes"]
        and source["accounting"]["program_bytes"] == package["program_bytes"]
        and source["accounting"]["counted_score_bytes"] == counted_score
        and source["accounting"]["target_bytes"] == 105_000_000
        and source["accounting"]["target_pass"]
        is (counted_score <= 105_000_000)
        and source["accounting"]["score_credit_bytes"] == 0
    )
    checks["resources_rederived"] = (
        source["resources"]["guard_count"] == 2
        and source["resources"]["maximum_tree_rss_kib"]
        == max(
            encode_guard["peaks"]["max_sampled_tree_rss_kib"],
            decode_guard["peaks"]["max_sampled_tree_rss_kib"],
        )
        and source["resources"]["maximum_cgroup_memory_peak_bytes"]
        == max(
            encode_guard["peaks"]["cgroup_memory_peak_bytes"],
            decode_guard["peaks"]["cgroup_memory_peak_bytes"],
        )
        and source["resources"]["maximum_temporary_disk_bytes"]
        == max(
            encode_guard["peaks"]["max_sampled_scratch_logical_bytes"],
            encode_guard["peaks"]["max_sampled_scratch_allocated_bytes"],
            decode_guard["peaks"]["max_sampled_scratch_logical_bytes"],
            decode_guard["peaks"]["max_sampled_scratch_allocated_bytes"],
        )
        and source["resources"]["maximum_allowed_cpu_count"] == 1
        and source["resources"]["all_guards_pass"] is True
        and source["resources"]["diagnostic_timing_only"] is True
        and source["resources"]["geekbench5_single_core_score"] is None
        and source["resources"]["runtime_eligibility_established"] is False
    )
    checks["cleanup_complete"] = (
        source["cleanup"]["scratch_removed_on_success_pass"] is True
        and source["cleanup"]["scratch_preserved_on_failure"] is False
        and source["cleanup"]["cgroup_removed_pass"] is True
        and source["cleanup"]["lease_removed_pass"] is True
        and source["cleanup"]["lease_release_pass"] is True
        and source["cleanup"]["scratch_root"] == str(SCRATCH)
        and not SCRATCH.exists()
        and not LEASE.exists()
        and not LOCK.exists()
        and not CGROUP.exists()
    )
    checks["lease_artifacts_match"] = artifact_matches(
        source["lease"]["evidence"]
    ) and artifact_matches(source["lease"]["transitions"])
    if checks["lease_artifacts_match"]:
        lease_module = load_module(LEASE_VERIFIER, "qm8_success_lease_verifier")
        lease_result, lease_verified = lease_module.verify(
            argparse.Namespace(
                transition_log=Path(source["lease"]["transitions"]["path"]),
                terminal_lease=Path(source["lease"]["evidence"]["path"]),
            )
        )
        checks["lease_transition_semantics"] = bool(
            lease_verified
            and lease_result.get("verified") is True
            and lease_result.get("candidate_id")
            == "cmix_obias_memory_safe_parent_filebacked_q1_v1-full-a"
        )
    else:
        checks["lease_transition_semantics"] = False
    checks["arm_a_reference_consistent"] = (
        arm == "a"
        and antecedents["arm_a_reference"] is None
        and all(value is None for value in source["identity"]["arm_a"].values())
    ) or (
        arm == "b"
        and artifact_matches(antecedents["arm_a_reference"])
        and all(value is True for value in source["identity"]["arm_a"].values())
    )
    if arm == "b":
        validate_contract(Path(antecedents["arm_a_reference"]["path"]), SOURCE_SCHEMA)
    checks["encode_pressure_was_active"] = (
        encode_soft["high_event_count"]
        == encode_guard["cgroup_events"]["delta"]["high"]
        > 0
    )
    checks["decode_soft_receipt_consistent"] = decode_soft["high_event_count"] == decode_guard["cgroup_events"]["delta"]["high"]
    errors = [f"check failed: {name}" for name, passed in checks.items() if not passed]
    output = {
        "schema": SCHEMA,
        "candidate_id": receipt_path.parent.name,
        "arm": arm,
        "source_receipt": artifact(receipt_path),
        "evidence": {
            "encode_guard": artifact(Path(source["stages"]["encode"]["guard_receipt"]["path"])),
            "encode_stage": artifact(Path(source["stages"]["encode"]["stage_receipt"]["path"])),
            "encode_soft_high": artifact(Path(source["stages"]["encode"]["guard_receipt"]["path"]).with_name("soft-high-receipt.json")),
            "decode_guard": artifact(Path(source["stages"]["decode"]["guard_receipt"]["path"])),
            "decode_stage": artifact(Path(source["stages"]["decode"]["stage_receipt"]["path"])),
            "decode_soft_high": artifact(Path(source["stages"]["decode"]["guard_receipt"]["path"]).with_name("soft-high-receipt.json")),
            "roundtrip_runner": artifact(Path(source["runner"]["path"])),
            "stage_runner": artifact(Path(source["stage_runner"]["path"])),
            "resource_guard_wrapper": artifact(Path(source["resource_guard"]["path"])),
            "verifier": artifact(Path(__file__).resolve(strict=True)),
            "verification_schema": artifact(SCHEMA_PATH.resolve(strict=True)),
        },
        "observed": {
            "payload_bytes": outputs["payload"]["bytes"],
            "archive_bytes": outputs["archive"]["bytes"],
            "program_bytes": package["program_bytes"],
            "counted_score_bytes": counted_score,
            "encode_cgroup_peak_bytes": encode_guard["peaks"]["cgroup_memory_peak_bytes"],
            "decode_cgroup_peak_bytes": decode_guard["peaks"]["cgroup_memory_peak_bytes"],
            "encode_tree_peak_rss_kib": encode_guard["peaks"]["max_sampled_tree_rss_kib"],
            "decode_tree_peak_rss_kib": decode_guard["peaks"]["max_sampled_tree_rss_kib"],
            "encode_high_events": encode_soft["high_event_count"],
            "decode_high_events": decode_soft["high_event_count"],
        },
        "checks": checks,
        "errors": errors,
        "verification_pass": not errors,
        "claim_boundary": (
            "Independent verification of one passing diagnostic full-corpus arm. "
            "It does not establish two-arm determinism, full probability-stream identity, "
            "runtime eligibility, memory-safe-parent qualification, or Gamma score credit."
        ),
        "gamma_score_credit_bytes": 0,
    }
    return output, not errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (
        args.output.absolute() != RESULT / "full-soft-high-verification.json"
        or args.output.parent.resolve(strict=True) != RESULT
        or args.output.exists()
        or args.output.is_symlink()
    ):
        raise SystemExit("output must be the new canonical qm8 success verification")
    receipt_path = regular(args.receipt, "qm8 terminal receipt")
    if receipt_path != RESULT / "full-roundtrip-receipt.json":
        raise SystemExit("qm8 terminal receipt path mismatch")
    validate_activation(receipt_path)
    try:
        output, passed = verify(receipt_path)
    except Exception as exc:
        output = {
            "schema": SCHEMA,
            "candidate_id": args.receipt.parent.name,
            "arm": None,
            "source_receipt": None,
            "evidence": None,
            "observed": None,
            "checks": {},
            "errors": [f"{type(exc).__name__}: {exc}"],
            "verification_pass": False,
            "claim_boundary": "Independent verification failed before the source arm could be established.",
            "gamma_score_credit_bytes": 0,
        }
        passed = False
    validate_output(output)
    write_new(args.output, output)
    sys.stdout.write(json.dumps(output, sort_keys=True, indent=2) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
