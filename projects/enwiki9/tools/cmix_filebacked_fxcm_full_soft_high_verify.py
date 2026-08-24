#!/usr/bin/env python3
"""Independently verify a passing soft-pressure q1 full-corpus arm."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

import research_contracts


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-soft-high-verification.v1"
PROJECT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT / "contracts/research/v1/cmix-filebacked-fxcm-full-soft-high-verification.schema.json"
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


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def artifact_matches(record: dict[str, Any] | None) -> bool:
    if not isinstance(record, dict):
        return False
    path = Path(record.get("path", ""))
    return bool(
        path.is_file()
        and path.stat().st_size == record.get("bytes")
        and sha256_file(path) == record.get("sha256")
    )


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
    checks[f"{phase}_summary_artifacts_match"] = artifact_matches(summary["guard_receipt"]) and artifact_matches(summary["stage_receipt"])
    checks[f"{phase}_guard_complete"] = (
        guard["status"] == "complete"
        and guard["returncode"] == 0
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
    checks[f"{phase}_rss_cpu_disk_clean"] = (
        guard["peaks"]["max_sampled_tree_rss_kib"] < MEMORY_LIMIT_KIB
        and guard["peaks"]["max_observed_process_vmhwm_kib"] < MEMORY_LIMIT_KIB
        and guard["peaks"]["max_sampled_allowed_cpu_count"] == 1
        and max(
            guard["peaks"]["max_sampled_scratch_logical_bytes"],
            guard["peaks"]["max_sampled_scratch_allocated_bytes"],
        ) < guard["temporary_disk_limit_bytes"]
    )
    checks[f"{phase}_stage_complete"] = (
        stage["mode"] == phase
        and stage["return_code"] == 0
        and stage["stage_pass"] is True
        and stage["backing_cleanup_pass"] is True
    )
    checks[f"{phase}_soft_pressure_bound"] = (
        soft["wrapper_pass"] is True
        and soft["effective_memory_high_bytes"] == SOFT_MEMORY_HIGH_BYTES
        and soft["memory_high_restore_pass"] is True
        and soft["guard_return_code"] == 0
        and soft["guard_status"] == "complete"
        and artifact_matches(soft["underlying_guard"])
        and soft["underlying_guard"]["sha256"] == EXPECTED_GUARD_SHA256
        and artifact_matches(soft["guard_receipt"])
        and Path(soft["guard_receipt"]["path"]).resolve() == guard_path.resolve()
        and not Path(soft["cgroup_path"]).exists()
    )
    checks[f"{phase}_soft_pressure_observed"] = isinstance(soft["high_event_count"], int) and soft["high_event_count"] >= 0
    checks[f"{phase}_result_ownership"] = guard_path.parent == result_root / phase and stage_path.parent == result_root / phase
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
        "resource_wrapper_exact": artifact_matches(source["resource_guard"])
        and source["resource_guard"]["sha256"] == EXPECTED_WRAPPER_SHA256,
        "roundtrip_runner_exact": artifact_matches(source["runner"])
        and source["runner"]["sha256"] == EXPECTED_ROUNDTRIP_SHA256,
        "stage_runner_exact": artifact_matches(source["stage_runner"])
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
        artifact_matches(outputs["payload"])
        and outputs["payload"]["bytes"] == PARENT_PAYLOAD_BYTES
        and outputs["payload"]["sha256"] == PARENT_PAYLOAD_SHA256
        and encode_stage["outputs"]["payload"] == outputs["payload"]
    )
    checks["archive_exactly_bound"] = artifact_matches(outputs["archive"]) and encode_stage["outputs"]["archive"] == outputs["archive"]
    checks["restored_exact_canonical"] = (
        artifact_matches(outputs["restored"])
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
        and source["accounting"]["score_credit_bytes"] == 0
    )
    checks["cleanup_complete"] = (
        source["cleanup"]["scratch_removed_on_success_pass"] is True
        and source["cleanup"]["scratch_preserved_on_failure"] is False
        and source["cleanup"]["cgroup_removed_pass"] is True
        and source["cleanup"]["lease_removed_pass"] is True
        and source["cleanup"]["lease_release_pass"] is True
        and not Path(source["cleanup"]["scratch_root"]).exists()
        and not (result_root.parents[1] / "operations/runtime/exclusive_full1g.json").exists()
    )
    checks["lease_artifacts_match"] = artifact_matches(source["lease"]["evidence"]) and artifact_matches(source["lease"]["transitions"])
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
    try:
        output, passed = verify(args.receipt.resolve(strict=True))
    except (OSError, KeyError, TypeError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
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
    write_new(args.output, output)
    sys.stdout.write(json.dumps(output, sort_keys=True, indent=2) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
