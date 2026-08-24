#!/usr/bin/env python3
"""Independently classify any terminally failed q1 qm8 full-corpus Arm A."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
from types import ModuleType
from typing import Any

import jsonschema
import research_contracts


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-qm8-failure-verification.v1"
SOURCE_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1"
STAGE_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-stage.v1"
GUARD_SCHEMA = "gamma.enwiki9.resource-guard-receipt.v3"
SOFT_SCHEMA = "gamma.enwiki9.resource-guard-soft-high.v1"
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
PLAN = (
    PROJECT
    / "operations/planning/"
    "cmix_filebacked_fxcm_full_a_qm8_failure_verification_v1.json"
)
PLAN_SCHEMA = PROJECT / "operations/planning/campaign-static-contract.schema.json"
SCHEMA_PATH = (
    PROJECT
    / "contracts/research/v1/"
    "cmix-filebacked-fxcm-full-qm8-failure-verification.schema.json"
)
CANONICAL_BYTES = 1_000_000_000
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
PARENT_PAYLOAD_BYTES = 107_730_531
PARENT_PAYLOAD_SHA256 = "889aa8074e0a84eb89997986899f1ef9f7cc0e52e87d1d36f86899fc679f5490"
EXPECTED = {
    "runner": "b196cddcef51e890794fa3877e5763b13c695ddd3ad1e1065eb9a584fce2f20b",
    "stage_runner": "e8aed4cbe68ba162a1d30a66bdf3243c70226268a9f23dbdb4bc4bef31354741",
    "resource_guard": "d2838c816bf17c5108fd0cf7170180ea8d47decbd3009f26ddf6bb7a02d05bae",
}
PYTHON = "/usr/bin/python3"
ANTECEDENT_SCHEMAS = {
    "build_receipt": "gamma.enwiki9.cmix-filebacked-fxcm-build-receipt.v1",
    "build_verification": "gamma.enwiki9.cmix-filebacked-fxcm-build-verification.v1",
    "scope_build_receipt": "gamma.enwiki9.cmix-filebacked-fxcm-scope-build.v1",
    "program_lock_verification": (
        "gamma.enwiki9.cmix-filebacked-fxcm-program-lock-verification.v1"
    ),
    "transfer_receipt": "gamma.enwiki9.cmix-filebacked-fxcm-transfer-10m.v1",
    "transfer_verification": (
        "gamma.enwiki9.cmix-filebacked-fxcm-identity-verification.v1"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(16 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def regular(path: Path, label: str, *, one_link: bool = True) -> Path:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label} has a symlink component: {current}")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"{label} is not regular: {path}")
    if one_link and metadata.st_nlink != 1:
        raise RuntimeError(f"{label} is not single-link: {path}")
    return path.resolve(strict=True)


def artifact(path: Path) -> dict[str, Any]:
    path = regular(path, "artifact")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def artifact_matches(record: Any, label: str) -> bool:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        return False
    try:
        path = regular(Path(record["path"]), label)
    except (OSError, RuntimeError):
        return False
    return path.stat().st_size == record["bytes"] and sha256(path) == record["sha256"]


def artifact_at(record: Any, expected: Path, label: str) -> bool:
    if not artifact_matches(record, label):
        return False
    try:
        return Path(record["path"]).resolve(strict=True) == expected.resolve(strict=True)
    except OSError:
        return False


def load_contract(path: Path, schema: str, label: str) -> dict[str, Any]:
    path = regular(path, label)
    value = json.loads(path.read_text(encoding="utf-8"))
    research_contracts.validate_artifact(path)
    if value.get("schema") != schema:
        raise RuntimeError(f"{label} schema mismatch")
    return value


def plan_binding(record: Any, expected: Path, label: str) -> None:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise RuntimeError(f"{label} plan binding malformed")
    declared = Path(record["path"])
    path = declared if declared.is_absolute() else PROJECT / declared
    path = regular(path, label)
    if path != expected.resolve(strict=True):
        raise RuntimeError(f"{label} plan path mismatch")
    if path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
        raise RuntimeError(f"{label} plan identity mismatch")


def validate_plan(receipt_path: Path) -> None:
    plan_path = regular(PLAN, "qm8 failure-verification plan")
    schema_path = regular(PLAN_SCHEMA, "campaign static-contract schema")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(plan)
    contract = plan.get("contract", {})
    activation = contract.get("activation", {})
    source = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        plan.get("artifact_id")
        != "cmix_filebacked_fxcm_full_a_qm8_failure_verification_v1"
        or plan.get("revision", 0) < 2
        or plan.get("claim_authority") != "none"
        or contract.get("candidate_id") != "cmix_filebacked_fxcm_full_a_qm8_v1"
        or contract.get("source_receipt") != str(receipt_path)
        or contract.get("output")
        != str(RESULT / "full-terminal-failure-verification.json")
        or activation.get("status") != "activated_after_terminal_failed_qm8"
        or activation.get("execution_authorized") is not True
        or activation.get("terminal_receipt_sha256") != sha256(receipt_path)
        or source.get("schema") != SOURCE_SCHEMA
        or source.get("candidate_id")
        != "cmix_obias_memory_safe_parent_filebacked_q1_v1"
        or source.get("arm") != "a"
        or source.get("terminal_pass") is not False
        or live_qm8_processes()
        or contract.get("promotion_authority") is not False
        or contract.get("memory_safe_parent_qualification_authority") is not False
        or contract.get("archive_authority") is not False
        or contract.get("gamma_compression_credit_bytes") != 0
        or contract.get("gamma_score_credit_bytes") != 0
    ):
        raise RuntimeError("qm8 failure-verification plan is not receipt-bound revision 2")
    expected_bindings = {
        "verifier": PROJECT / "tools/cmix_filebacked_fxcm_full_qm8_failure_verify.py",
        "verification_schema": SCHEMA_PATH,
        "research_contracts": PROJECT / "tools/research_contracts.py",
        "lease_verifier": LEASE_VERIFIER,
        "plan_schema": PLAN_SCHEMA,
        "python_runtime": Path("/usr/bin/python3.14"),
    }
    implementation = contract.get("implementation", {})
    for name, expected in expected_bindings.items():
        plan_binding(implementation.get(name), expected, name)
    source_bindings = {
        "full_roundtrip_schema": (
            PROJECT
            / "contracts/research/v1/cmix-filebacked-fxcm-full-roundtrip.schema.json"
        ),
        "stage_schema": (
            PROJECT / "contracts/research/v1/cmix-filebacked-fxcm-full-stage.schema.json"
        ),
        "guard_schema": (
            PROJECT / "contracts/research/v1/resource-guard-receipt.v3.schema.json"
        ),
        "soft_high_schema": (
            PROJECT / "contracts/research/v1/resource-guard-soft-high.schema.json"
        ),
        "roundtrip_runner": PROJECT / "tools/cmix_filebacked_fxcm_full_roundtrip.py",
        "stage_runner": PROJECT / "tools/cmix_filebacked_fxcm_full_stage.py",
        "soft_high_wrapper": PROJECT / "tools/run_with_resource_guard_v3_soft_high.py",
        "resource_guard": PROJECT / "tools/run_with_resource_guard_v3.py",
    }
    for name, expected in source_bindings.items():
        plan_binding(contract.get("source_bindings", {}).get(name), expected, name)
    expected_command = [
        "/usr/bin/python3.14",
        "tools/cmix_filebacked_fxcm_full_qm8_failure_verify.py",
        "--receipt",
        "results/cmix_filebacked_fxcm_full_a_qm8_v1/full-roundtrip-receipt.json",
        "--output",
        "results/cmix_filebacked_fxcm_full_a_qm8_v1/"
        "full-terminal-failure-verification.json",
    ]
    if contract.get("command") != expected_command:
        raise RuntimeError("qm8 failure-verification command mismatch")


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


def write_new(path: Path, value: dict[str, Any]) -> None:
    raw = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
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


def validate_output(value: dict[str, Any]) -> None:
    schema_path = regular(SCHEMA_PATH, "qm8 failure-verification schema")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)


def command_sha256(argv: list[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(item) for item in argv)).hexdigest()


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


def latest_progress(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        return {"phase": None, "percent": None}
    text = path.read_bytes().decode("utf-8", errors="replace").replace("\r", "\n")
    phase: str | None = None
    percent: float | None = None
    for line in text.splitlines():
        match = re.search(r"\b(progress|pretraining): ([0-9]+(?:\.[0-9]+)?)%", line)
        if match:
            phase = match.group(1)
            percent = float(match.group(2))
    return {"phase": phase, "percent": percent}


def expected_stage_command(phase: str, source: dict[str, Any]) -> list[str] | None:
    command = [
        PYTHON,
        str(PROJECT / "tools/cmix_filebacked_fxcm_full_stage.py"),
        "--mode",
        phase,
        "--corpus",
        source.get("population", {}).get("path", ""),
        "--work-root",
        str(SCRATCH / phase),
        "--result-root",
        str(RESULT / phase),
        "--receipt",
        str(RESULT / phase / "stage-receipt.json"),
    ]
    if phase == "encode":
        package = source.get("package")
        if not isinstance(package, dict):
            return None
        command.extend(
            [
                "--package",
                package.get("packaged_compressor", {}).get("path", ""),
                "--head",
                package.get("head", {}).get("path", ""),
            ]
        )
    else:
        archive = source.get("outputs", {}).get("archive")
        if not isinstance(archive, dict):
            return None
        command.extend(["--archive", archive.get("path", "")])
    return command


def expected_guard_command(
    phase: str, source: dict[str, Any], stage_command: list[str]
) -> list[str]:
    marker = RESULT / phase / "phase-markers.jsonl"
    return [
        "/usr/bin/taskset",
        "--cpu-list",
        str(source.get("selected_logical_cpu")),
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
        str(marker),
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


def inspect_stage(
    phase: str,
    summary: Any,
    source: dict[str, Any],
    evidence_checks: dict[str, bool],
) -> dict[str, Any]:
    if summary is None:
        return {
            "present": False,
            "summary_pass": False,
            "guard_status": None,
            "guard_returncode": None,
            "guard_present": False,
            "guard_flags": {},
            "events": {},
            "peaks": {},
            "stage_returncode": None,
            "stage_pass": None,
            "exact_inverse": None,
            "inputs": {},
            "outputs": {},
            "progress": {"phase": None, "percent": None},
        }
    if not isinstance(summary, dict) or summary.get("mode") != phase:
        raise RuntimeError(f"{phase} stage summary malformed")
    phase_root = RESULT / phase
    for role in ("guard_stdout", "guard_stderr"):
        expected = phase_root / role.replace("_", ".")
        evidence_checks[f"{phase}_{role}_artifact"] = artifact_at(
            summary.get(role), expected, f"{phase} {role}"
        )
    guard: dict[str, Any] | None = None
    stage: dict[str, Any] | None = None
    guard_record = summary.get("guard_receipt")
    stage_record = summary.get("stage_receipt")
    stage_command = expected_stage_command(phase, source)
    evidence_checks[f"{phase}_outer_guard_command_hash"] = bool(
        stage_command is not None
        and summary.get("guard_command_sha256")
        == command_sha256(expected_guard_command(phase, source, stage_command))
    )
    if guard_record is not None:
        evidence_checks[f"{phase}_guard_artifact"] = artifact_at(
            guard_record, phase_root / "guard.json", f"{phase} guard"
        )
        if evidence_checks[f"{phase}_guard_artifact"]:
            guard_path = Path(guard_record["path"])
            guard = load_contract(guard_path, GUARD_SCHEMA, f"{phase} guard")
            evidence_checks[f"{phase}_guard_command_hash"] = (
                guard.get("command_sha256") == command_sha256(guard.get("command", []))
                and summary.get("stage_command_sha256")
                == guard.get("command_sha256")
                and stage_command is not None
                and guard.get("command") == stage_command
                and summary.get("guard_return_code") == guard.get("returncode")
                and summary.get("guard_status") == guard.get("status")
            )
            evidence_checks[f"{phase}_guard_contract"] = (
                guard.get("phase") == "diagnostic"
                and guard.get("limit_mode") == "tree"
                and guard.get("limit_kib") == 9_765_625
                and guard.get("official_decimal_limit_kib") == 9_765_625
                and guard.get("temporary_disk_limit_bytes") == 100_000_000_000
                and guard.get("max_logical_cpus") == 1
                and guard.get("label") == f"q1-full-{phase}"
                and guard.get("scratch_paths") == [str(SCRATCH), str(RESULT)]
                and guard.get("phase_marker_path")
                == str(phase_root / "phase-markers.jsonl")
                and guard.get("cgroup", {}).get("path") == str(CGROUP)
                and guard.get("cgroup", {}).get("requested_memory_max_bytes")
                == 10_000_000_000
                and guard.get("cgroup", {}).get("memory_max_bytes")
                == 9_999_998_976
            )
            evidence_checks[f"{phase}_guard_summary_measurements"] = (
                summary.get("maximum_tree_rss_kib")
                == guard.get("peaks", {}).get("max_sampled_tree_rss_kib")
                and summary.get("cgroup_memory_peak_bytes")
                == guard.get("peaks", {}).get("cgroup_memory_peak_bytes")
                and summary.get("maximum_temporary_disk_bytes")
                == max(
                    guard.get("peaks", {}).get(
                        "max_sampled_scratch_logical_bytes", 0
                    ),
                    guard.get("peaks", {}).get(
                        "max_sampled_scratch_allocated_bytes", 0
                    ),
                )
                and summary.get("maximum_allowed_cpu_count")
                == guard.get("peaks", {}).get("max_sampled_allowed_cpu_count")
            )
            soft_path = guard_path.with_name("soft-high-receipt.json")
            if soft_path.is_file() and not soft_path.is_symlink():
                soft = load_contract(soft_path, SOFT_SCHEMA, f"{phase} soft-high")
                evidence_checks[f"{phase}_soft_high_binding"] = (
                    soft_path.resolve(strict=True)
                    == (phase_root / "soft-high-receipt.json").resolve(strict=True)
                    and artifact_at(
                        soft.get("underlying_guard"),
                        PROJECT / "tools/run_with_resource_guard_v3.py",
                        f"{phase} underlying guard",
                    )
                    and soft.get("underlying_guard", {}).get("sha256")
                    == "044147f7ffe6922ea8dafd52fc3d4426077b20958adbcd421245ad41adcfc1e4"
                    and soft.get("guard_receipt") is not None
                    and artifact_matches(soft["guard_receipt"], f"{phase} soft guard")
                    and Path(soft["guard_receipt"]["path"]).resolve(strict=True)
                    == guard_path.resolve(strict=True)
                    and soft.get("guard_status") == guard.get("status")
                    and soft.get("guard_return_code") == guard.get("returncode")
                    and soft.get("cgroup_path") == str(CGROUP)
                    and soft.get("high_event_count")
                    == guard.get("cgroup_events", {}).get("delta", {}).get("high")
                    and (
                        (
                            soft.get("effective_memory_high_bytes") == 8_999_997_440
                            and soft.get("memory_high_restore_pass") is True
                            and soft.get("errors") == []
                        )
                        if soft.get("wrapper_pass") is True
                        else bool(soft.get("errors"))
                    )
                    and (
                        summary.get("outer_return_code") == soft.get("guard_return_code")
                        if soft.get("wrapper_pass") is True
                        else summary.get("outer_return_code") == 76
                    )
                )
            else:
                evidence_checks[f"{phase}_soft_high_absence_observed"] = True
    else:
        evidence_checks[f"{phase}_guard_absence_truthful"] = (
            summary.get("guard_status") is None
            and summary.get("guard_return_code") is None
        )
        soft_path = phase_root / "soft-high-receipt.json"
        if soft_path.is_file() and not soft_path.is_symlink():
            soft = load_contract(soft_path, SOFT_SCHEMA, f"{phase} soft-high")
            evidence_checks[f"{phase}_soft_high_without_guard"] = (
                artifact_at(
                    soft.get("underlying_guard"),
                    PROJECT / "tools/run_with_resource_guard_v3.py",
                    f"{phase} underlying guard",
                )
                and soft.get("underlying_guard", {}).get("sha256")
                == "044147f7ffe6922ea8dafd52fc3d4426077b20958adbcd421245ad41adcfc1e4"
                and soft.get("cgroup_path") == str(CGROUP)
                and soft.get("guard_receipt") is None
                and soft.get("wrapper_pass") is False
                and bool(soft.get("errors"))
                and summary.get("outer_return_code") == 76
            )
        else:
            evidence_checks[f"{phase}_soft_high_absence_observed"] = True
    if stage_record is not None:
        evidence_checks[f"{phase}_stage_artifact"] = artifact_at(
            stage_record, phase_root / "stage-receipt.json", f"{phase} stage"
        )
        if evidence_checks[f"{phase}_stage_artifact"]:
            stage = load_contract(Path(stage_record["path"]), STAGE_SCHEMA, f"{phase} stage")
            evidence_checks[f"{phase}_stage_provenance"] = (
                stage.get("candidate_id")
                == "cmix_obias_memory_safe_parent_filebacked_q1_v1"
                and stage.get("corpus", {}).get("bytes") == CANONICAL_BYTES
                and stage.get("corpus", {}).get("sha256") == CANONICAL_SHA256
                and artifact_matches(stage.get("corpus"), f"{phase} stage corpus")
                and artifact_at(
                    stage.get("stage_runner"),
                    PROJECT / "tools/cmix_filebacked_fxcm_full_stage.py",
                    f"{phase} stage runner",
                )
                and stage.get("stage_runner", {}).get("sha256")
                == EXPECTED["stage_runner"]
                and artifact_at(
                    stage.get("phase_marker"),
                    phase_root / "phase-markers.jsonl",
                    f"{phase} phase marker",
                )
                and stage.get("result_root") == str(phase_root)
                and stage.get("work_root") == str(SCRATCH / phase)
                and stage.get("command")
                == (
                    ["./cmix", "-e", source["population"]["path"], "out.cmix"]
                    if phase == "encode"
                    else ["./archive9"]
                )
                and stage.get("execution_authority") is False
                and stage.get("gamma_compression_credit_bytes") == 0
                and stage.get("gamma_score_credit_bytes") == 0
            )
            evidence_checks[f"{phase}_stage_io_artifacts"] = all(
                artifact_matches(record, f"{phase} stage {kind} {name}")
                for kind in ("inputs", "outputs")
                for name, record in stage.get(kind, {}).items()
            )
            evidence_checks[f"{phase}_stage_summary_binding"] = (
                stage.get("mode") == phase
                and summary.get("stage_return_code") == stage.get("return_code")
                and (
                    summary.get("stage_and_guard_pass") is False
                    or (
                        summary.get("outer_return_code") == 0
                        and summary.get("cgroup_cleanup_pass") is True
                        and summary.get("errors") == []
                        and stage.get("stage_pass") is True
                        and guard is not None
                        and guard.get("status") == "complete"
                        and guard.get("returncode") == 0
                        and not any(guard.get("guards", {}).values())
                    )
                )
            )
    else:
        evidence_checks[f"{phase}_stage_absence_truthful"] = (
            summary.get("stage_return_code") is None
            and summary.get("backing_cleanup_pass") is None
        )
    return {
        "present": True,
        "summary_pass": summary.get("stage_and_guard_pass") is True,
        "guard_status": guard.get("status") if guard else summary.get("guard_status"),
        "guard_returncode": guard.get("returncode") if guard else summary.get("guard_return_code"),
        "guard_present": guard is not None,
        "guard_flags": guard.get("guards", {}) if guard else {},
        "events": guard.get("cgroup_events", {}).get("delta", {}) if guard else {},
        "peaks": guard.get("peaks", {}) if guard else {},
        "stage_returncode": stage.get("return_code") if stage else summary.get("stage_return_code"),
        "stage_pass": stage.get("stage_pass") if stage else None,
        "exact_inverse": stage.get("exact_raw_inverse_pass") if stage else None,
        "inputs": stage.get("inputs", {}) if stage else {},
        "outputs": stage.get("outputs", {}) if stage else {},
        "progress": latest_progress(RESULT / phase / f"{phase}.codec.stderr"),
    }


def package_checks(package: Any, checks: dict[str, bool]) -> None:
    if package is None:
        checks["package_absence_allowed_on_failure"] = True
        return
    names = (
        "raw_binary",
        "dictionary_payload",
        "article_order_payload",
        "header",
        "packaged_compressor",
        "head",
        "build_verification",
    )
    checks["package_artifacts"] = all(
        artifact_matches(package.get(name), f"package {name}") for name in names
    )
    if not checks["package_artifacts"]:
        return
    checks["package_result_ownership"] = (
        Path(package["packaged_compressor"]["path"]).resolve(strict=True)
        == (RESULT / "package/cmix").resolve(strict=True)
        and Path(package["head"]["path"]).resolve(strict=True)
        == (RESULT / "package/head.blob").resolve(strict=True)
        and package.get("arm") == "a"
    )
    digest = hashlib.sha256()
    size = 0
    for name in ("raw_binary", "dictionary_payload", "article_order_payload", "header"):
        with Path(package[name]["path"]).open("rb") as stream:
            for block in iter(lambda: stream.read(16 << 20), b""):
                digest.update(block)
                size += len(block)
    packaged = Path(package["packaged_compressor"]["path"])
    checks["package_concatenation"] = (
        size == packaged.stat().st_size
        and digest.hexdigest() == sha256(packaged)
        and package.get("program_bytes")
        == packaged.stat().st_size + Path(package["head"]["path"]).stat().st_size
    )


def verify(receipt_path: Path) -> tuple[dict[str, Any], bool]:
    receipt_path = regular(receipt_path, "qm8 terminal receipt")
    if receipt_path != RESULT / "full-roundtrip-receipt.json":
        raise RuntimeError("qm8 terminal receipt path mismatch")
    validate_plan(receipt_path)
    source = load_contract(receipt_path, SOURCE_SCHEMA, "qm8 terminal receipt")
    evidence_checks: dict[str, bool] = {
        "source_is_failed_qm8_arm_a": source.get("arm") == "a"
        and source.get("terminal_pass") is False
        and source.get("candidate_id") == "cmix_obias_memory_safe_parent_filebacked_q1_v1",
        "source_zero_credit": source.get("memory_safe_parent_qualified") is False
        and source.get("promotion_authorized") is False
        and source.get("execution_authority") is False
        and source.get("accounting", {}).get("score_credit_bytes") == 0
        and source.get("gamma_compression_credit_bytes") == 0
        and source.get("gamma_score_credit_bytes") == 0,
        "source_errors_nonempty": bool(source.get("errors")),
        "qm8_process_closed": live_qm8_processes() == [],
        "population_artifact": artifact_matches(source.get("population"), "population")
        and source["population"]["bytes"] == CANONICAL_BYTES
        and source["population"]["sha256"] == CANONICAL_SHA256,
    }
    evidence_checks["scratch_root_exact"] = (
        source.get("cleanup", {}).get("scratch_root") == str(SCRATCH)
    )
    for role, digest in EXPECTED.items():
        record = source.get(role)
        expected_path = {
            "runner": PROJECT / "tools/cmix_filebacked_fxcm_full_roundtrip.py",
            "stage_runner": PROJECT / "tools/cmix_filebacked_fxcm_full_stage.py",
            "resource_guard": PROJECT / "tools/run_with_resource_guard_v3_soft_high.py",
        }[role]
        evidence_checks[f"{role}_exact"] = (
            artifact_at(record, expected_path, role)
            and record["sha256"] == digest
        )
    evidence_checks["antecedent_artifacts"] = all(
        artifact_matches(record, f"antecedent {name}")
        for name, record in source.get("antecedents", {}).items()
        if record is not None
    )
    for name, schema in ANTECEDENT_SCHEMAS.items():
        record = source.get("antecedents", {}).get(name)
        if artifact_matches(record, f"antecedent {name}"):
            load_contract(Path(record["path"]), schema, f"antecedent {name}")
            evidence_checks[f"antecedent_{name}_contract"] = True
        else:
            evidence_checks[f"antecedent_{name}_contract"] = False
    package_checks(source.get("package"), evidence_checks)
    encode = inspect_stage(
        "encode", source.get("stages", {}).get("encode"), source, evidence_checks
    )
    decode = inspect_stage(
        "decode", source.get("stages", {}).get("decode"), source, evidence_checks
    )

    outputs = source.get("outputs", {})
    for name in ("payload", "archive", "restored"):
        record = outputs.get(name)
        evidence_checks[f"output_{name}_artifact"] = (
            record is None or artifact_matches(record, f"output {name}")
        )
    if encode["present"] and encode["inputs"]:
        evidence_checks["encode_stage_input_binding"] = bool(
            source.get("package") is not None
            and encode["inputs"].get("package")
            == source["package"].get("packaged_compressor")
            and encode["inputs"].get("head") == source["package"].get("head")
        )
        evidence_checks["encode_stage_output_binding"] = all(
            encode["outputs"].get(name) == outputs.get(name)
            for name in encode["outputs"]
        )
    if decode["present"] and decode["inputs"]:
        evidence_checks["decode_stage_input_binding"] = (
            decode["inputs"].get("archive") == outputs.get("archive")
        )
        evidence_checks["decode_stage_output_binding"] = all(
            decode["outputs"].get(name) == outputs.get(name)
            for name in decode["outputs"]
        )
    if outputs.get("payload") is not None:
        evidence_checks["payload_identity_truthful"] = (
            source["identity"]["authoritative_parent_payload_identity_pass"]
            is (
                outputs["payload"]["bytes"] == PARENT_PAYLOAD_BYTES
                and outputs["payload"]["sha256"] == PARENT_PAYLOAD_SHA256
            )
        )
    if outputs.get("restored") is not None:
        evidence_checks["inverse_identity_truthful"] = (
            source["identity"]["exact_raw_inverse_pass"]
            is (
                outputs["restored"]["bytes"] == CANONICAL_BYTES
                and outputs["restored"]["sha256"] == CANONICAL_SHA256
            )
        )

    package = source.get("package")
    archive_bytes = (
        outputs["archive"]["bytes"] if outputs.get("archive") is not None else None
    )
    program_bytes = package.get("program_bytes") if isinstance(package, dict) else None
    counted_score = (
        archive_bytes + program_bytes
        if archive_bytes is not None and program_bytes is not None
        else None
    )
    accounting = source.get("accounting", {})
    evidence_checks["accounting_rederived"] = (
        accounting.get("archive_bytes") == archive_bytes
        and accounting.get("program_bytes") == program_bytes
        and accounting.get("counted_score_bytes") == counted_score
        and accounting.get("target_bytes") == 105_000_000
        and accounting.get("target_pass")
        is (counted_score is not None and counted_score <= 105_000_000)
        and accounting.get("score_credit_bytes") == 0
    )

    guarded_stages = [stage for stage in (encode, decode) if stage["guard_present"]]
    resources = source.get("resources", {})
    evidence_checks["resources_rederived"] = (
        resources.get("guard_count") == len(guarded_stages)
        and resources.get("maximum_tree_rss_kib")
        == max(
            (stage["peaks"].get("max_sampled_tree_rss_kib", 0) for stage in guarded_stages),
            default=0,
        )
        and resources.get("maximum_cgroup_memory_peak_bytes")
        == max(
            (stage["peaks"].get("cgroup_memory_peak_bytes", 0) for stage in guarded_stages),
            default=0,
        )
        and resources.get("maximum_temporary_disk_bytes")
        == max(
            (
                max(
                    stage["peaks"].get("max_sampled_scratch_logical_bytes", 0),
                    stage["peaks"].get("max_sampled_scratch_allocated_bytes", 0),
                )
                for stage in guarded_stages
            ),
            default=0,
        )
        and resources.get("maximum_allowed_cpu_count")
        == max(
            (stage["peaks"].get("max_sampled_allowed_cpu_count", 0) for stage in guarded_stages),
            default=0,
        )
        and resources.get("all_guards_pass")
        is (
            len(guarded_stages) == 2
            and encode["summary_pass"]
            and decode["summary_pass"]
        )
        and resources.get("diagnostic_timing_only") is True
        and resources.get("geekbench5_single_core_score") is None
        and resources.get("runtime_eligibility_established") is False
    )

    lease_evidence = source.get("lease", {}).get("evidence")
    lease_transitions = source.get("lease", {}).get("transitions")
    evidence_checks["lease_artifact_pairing"] = (
        (lease_evidence is None and lease_transitions is None)
        or (lease_evidence is not None and lease_transitions is not None)
    )
    lease_verified = False
    if lease_evidence is not None and lease_transitions is not None:
        evidence_checks["lease_artifacts"] = artifact_matches(
            lease_evidence, "lease evidence"
        ) and artifact_matches(lease_transitions, "lease transitions")
        if evidence_checks["lease_artifacts"]:
            module = load_module(LEASE_VERIFIER, "qm8_failure_lease_verifier")
            lease_result, lease_verified = module.verify(
                argparse.Namespace(
                    transition_log=Path(lease_transitions["path"]),
                    terminal_lease=Path(lease_evidence["path"]),
                )
            )
            evidence_checks["lease_transition_semantics"] = bool(
                lease_verified
                and lease_result.get("verified") is True
                and lease_result.get("candidate_id")
                == "cmix_obias_memory_safe_parent_filebacked_q1_v1-full-a"
            )
    else:
        evidence_checks["lease_artifact_absence_truthful"] = (
            source.get("cleanup", {}).get("lease_release_pass") is False
        )

    cleanup = source.get("cleanup", {})
    evidence_checks["cleanup_observation_truthful"] = (
        cleanup.get("scratch_removed_on_success_pass") is False
        and cleanup.get("scratch_preserved_on_failure")
        is Path(cleanup.get("scratch_root", "/nonexistent")).is_dir()
        and cleanup.get("cgroup_removed_pass")
        is (not CGROUP.exists())
        and cleanup.get("lease_removed_pass") is (not LEASE.exists() and not LOCK.exists())
    )

    stages = (encode, decode)
    resource_hard = any(
        stage["guard_flags"].get("cgroup_memory_guard_exceeded", False)
        or stage["events"].get("max", 0) > 0
        or stage["events"].get("oom", 0) > 0
        or stage["events"].get("oom_kill", 0) > 0
        for stage in stages
    )
    resource_rss = any(
        stage["guard_flags"].get("rss_guard_exceeded", False)
        or stage["guard_flags"].get("official_decimal_memory_exceeded", False)
        for stage in stages
    )
    resource_other = any(
        stage["guard_flags"].get(name, False)
        for stage in stages
        for name in (
            "temporary_disk_guard_exceeded",
            "logical_cpu_guard_exceeded",
            "wall_time_guard_exceeded",
        )
    )
    encode_failed = not encode["summary_pass"]
    payload_failed = outputs.get("payload") is not None and not source["identity"][
        "authoritative_parent_payload_identity_pass"
    ]
    decode_failed = encode["summary_pass"] and (
        not decode["summary_pass"] or not source["identity"]["exact_raw_inverse_pass"]
    )
    cleanup_failed = not all(
        cleanup.get(name) is True
        for name in ("cgroup_removed_pass", "lease_removed_pass", "lease_release_pass")
    )
    failure_predicates = {
        "resource_hard_cap_or_oom": resource_hard,
        "resource_rss_or_decimal_limit": resource_rss,
        "resource_disk_cpu_or_runtime": resource_other,
        "encode_codec_or_stage": encode_failed,
        "payload_or_parent_identity": payload_failed,
        "decode_codec_or_inverse": decode_failed,
        "cleanup_or_lease": cleanup_failed,
        "infrastructure_unclassified": False,
    }
    order = (
        "resource_hard_cap_or_oom",
        "resource_rss_or_decimal_limit",
        "resource_disk_cpu_or_runtime",
        "payload_or_parent_identity",
        "decode_codec_or_inverse",
        "cleanup_or_lease",
        "encode_codec_or_stage",
    )
    primary = next((name for name in order if failure_predicates[name]), None)
    if primary is None:
        primary = "infrastructure_unclassified"
        failure_predicates[primary] = True
    successor = {
        "resource_hard_cap_or_oom": "one_phase_specific_memory_successor",
        "resource_rss_or_decimal_limit": "one_phase_specific_memory_successor",
        "resource_disk_cpu_or_runtime": "one_resource_correction_successor",
        "payload_or_parent_identity": "first_divergence_localization_only",
        "decode_codec_or_inverse": "one_decode_or_inverse_correction_successor",
        "cleanup_or_lease": "one_cleanup_transaction_correction_successor",
        "encode_codec_or_stage": "one_encode_infrastructure_correction_successor",
        "infrastructure_unclassified": "one_receipt_bound_infrastructure_diagnostic",
    }[primary]
    evidence_errors = [name for name, passed in evidence_checks.items() if not passed]
    verified = not evidence_errors
    reported_primary = primary if verified else "verification_failure"
    reported_successor = successor if verified else "none_until_verifier_correction"
    reported_authority = (
        "independent_terminal_failure_classification_only"
        if verified
        else "none_verification_failure"
    )
    output = {
        "schema": SCHEMA,
        "candidate_id": "cmix_filebacked_fxcm_full_a_qm8_v1",
        "source_receipt": artifact(receipt_path),
        "source_terminal_pass": False,
        "evidence_checks": evidence_checks,
        "failure_predicates": failure_predicates,
        "primary_failure_class": reported_primary,
        "authorized_successor": reported_successor,
        "observed": {
            "source_errors": source.get("errors", []),
            "encode": encode,
            "decode": decode,
            "scratch_present": Path(cleanup.get("scratch_root", "/nonexistent")).is_dir(),
            "lease_present": LEASE.exists(),
            "lock_present": LOCK.exists(),
            "lease_transition_verified": lease_verified,
        },
        "errors": [f"evidence check failed: {name}" for name in evidence_errors],
        "verification_pass": verified,
        "promotion_authorized": False,
        "memory_safe_parent_qualified": False,
        "archive_authority": False,
        "claim_authority": reported_authority,
        "claim_boundary": (
            (
                "Independent classification of one terminally failed qm8 Arm A. "
                "It grants no parent qualification, archive, inverse, runtime, "
                "compression, authorship, or objective credit."
            )
            if verified
            else "The qm8 terminal failure could not be independently classified."
        ),
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    return output, verified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if (
        args.output.absolute()
        != RESULT / "full-terminal-failure-verification.json"
        or args.output.parent.resolve(strict=True) != RESULT
        or args.output.exists()
        or args.output.is_symlink()
    ):
        raise SystemExit("output must be the new canonical qm8 failure verification")
    preflight_receipt = regular(args.receipt, "qm8 terminal receipt")
    if preflight_receipt != RESULT / "full-roundtrip-receipt.json":
        raise SystemExit("qm8 terminal receipt path mismatch")
    validate_plan(preflight_receipt)
    try:
        output, passed = verify(preflight_receipt)
    except Exception as exc:
        output = {
            "schema": SCHEMA,
            "candidate_id": "cmix_filebacked_fxcm_full_a_qm8_v1",
            "source_receipt": None,
            "source_terminal_pass": False,
            "evidence_checks": {},
            "failure_predicates": {
                "resource_hard_cap_or_oom": False,
                "resource_rss_or_decimal_limit": False,
                "resource_disk_cpu_or_runtime": False,
                "encode_codec_or_stage": False,
                "payload_or_parent_identity": False,
                "decode_codec_or_inverse": False,
                "cleanup_or_lease": False,
                "infrastructure_unclassified": False,
            },
            "primary_failure_class": "verification_failure",
            "authorized_successor": "none_until_verifier_correction",
            "observed": None,
            "errors": [f"{type(exc).__name__}: {exc}"],
            "verification_pass": False,
            "promotion_authorized": False,
            "memory_safe_parent_qualified": False,
            "archive_authority": False,
            "claim_authority": "none_verification_failure",
            "claim_boundary": "The qm8 terminal failure could not be independently classified.",
            "gamma_compression_credit_bytes": 0,
            "gamma_score_credit_bytes": 0,
        }
        passed = False
    validate_output(output)
    write_new(args.output, output)
    sys.stdout.write(json.dumps(output, sort_keys=True, indent=2) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
