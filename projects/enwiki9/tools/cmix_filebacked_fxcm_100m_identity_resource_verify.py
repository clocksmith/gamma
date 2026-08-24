#!/usr/bin/env python3
"""Independently rederive the sealed q1 opening-100M identity/resource gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
from typing import Any

import jsonschema

import cmix_filebacked_fxcm_scope_identity as scope


PROJECT = Path(__file__).resolve().parents[1]
INPUT_SCHEMA = (
    PROJECT
    / "contracts/research/v1/cmix-filebacked-fxcm-100m-identity-resource.schema.json"
)
OUTPUT_SCHEMA = (
    PROJECT
    / "contracts/research/v1/"
    "cmix-filebacked-fxcm-100m-identity-resource-verification.schema.json"
)
INPUT_SCHEMA_SHA256 = "e7b9d8a9f37f8479e8ea057871e1510df5e4fdbf62a7d36bc31a5efa617389a8"
OUTPUT_SCHEMA_SHA256 = "f6ed6d489141687b7599497a53c5d5162c0c352f54d2db07b26ca99c4cfc6802"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
CALIBRATION_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-100m-observer-calibration.v1"
CALIBRATION_VERIFICATION_SCHEMA = (
    "gamma.enwiki9.cmix-filebacked-fxcm-100m-observer-calibration-verification.v1"
)
RELEASE_STAGE_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-100m-release-stage.v1"
IDENTITY_ARM_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-100m-identity-arm.v1"
GUARD_SCHEMA = "gamma.enwiki9.resource-guard-receipt.v3"
SOFT_HIGH_SCHEMA = "gamma.enwiki9.resource-guard-soft-high.v1"
PREFIX_BYTES = 100_000_000
PREFIX_SHA256 = "2b49720ec4d78c3c9fabaee6e4179a5e997302b3a70029f30f2d582218c024a8"
PHASES = (
    "package_helper_construction",
    "frontend_preprocessing",
    "model_pretraining",
    "arithmetic_payload_encode",
    "archive_assembly",
    "archive_decode",
    "frontend_inverse",
    "cleanup",
)
FIXED_OBSERVER_CHECKPOINTS = (16_777_216, 33_554_432, 50_331_648)
EXPECTED_OBSERVER_RANGES = 26


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def digest_prefix(path: Path, byte_count: int) -> str:
    remaining = byte_count
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while remaining:
            block = stream.read(min(8 << 20, remaining))
            if not block:
                raise RuntimeError("population ended before the frozen prefix boundary")
            digest.update(block)
            remaining -= len(block)
    return digest.hexdigest()


def digest_concatenation(paths: list[Path]) -> tuple[int, str]:
    digest = hashlib.sha256()
    total = 0
    for path in paths:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(8 << 20), b""):
                digest.update(block)
                total += len(block)
    return total, digest.hexdigest()


def regular_file(raw_path: Path, label: str, project_only: bool = False) -> Path:
    path = raw_path if raw_path.is_absolute() else PROJECT / raw_path
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label}: symlink component forbidden: {current}")
    resolved = absolute.resolve(strict=True)
    metadata = resolved.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label}: expected one-link regular file: {resolved}")
    if project_only and PROJECT not in resolved.parents:
        raise RuntimeError(f"{label}: artifact escapes project: {resolved}")
    return resolved


def proc_start_ticks(pid: int) -> int | None:
    try:
        return int(Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split()[21])
    except (FileNotFoundError, IndexError, ValueError):
        return None


def require_released_lease(path: Path) -> None:
    lease_path = path if path.is_absolute() else PROJECT / path
    lease_lock = Path(str(lease_path) + ".lock")
    if lease_lock.exists() or lease_lock.is_symlink():
        raise RuntimeError(f"exclusive full-1G lease lock exists: {lease_lock}")
    if not lease_path.exists():
        return
    lease_path = regular_file(lease_path, "exclusive lease")
    lease = json.loads(lease_path.read_text(encoding="utf-8"))
    pid = lease.get("pid")
    start_ticks = lease.get("proc_start_ticks")
    if isinstance(pid, int) and proc_start_ticks(pid) == start_ticks:
        raise RuntimeError(f"exclusive full-1G lease remains active for PID {pid}")
    codec_pid = lease.get("codec_pid")
    if isinstance(codec_pid, int) and Path(f"/proc/{codec_pid}").exists():
        raise RuntimeError(f"exclusive full-1G codec PID remains active: {codec_pid}")


def validate_schema_hashes() -> tuple[dict[str, Any], dict[str, Any]]:
    if digest_file(INPUT_SCHEMA) != INPUT_SCHEMA_SHA256:
        raise RuntimeError("input receipt schema hash drift")
    if digest_file(OUTPUT_SCHEMA) != OUTPUT_SCHEMA_SHA256:
        raise RuntimeError("verification schema hash drift")
    input_schema = json.loads(INPUT_SCHEMA.read_text(encoding="utf-8"))
    output_schema = json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(input_schema)
    jsonschema.Draft202012Validator.check_schema(output_schema)
    return input_schema, output_schema


def resolve_artifact(record: dict[str, Any], label: str) -> Path:
    path = regular_file(Path(record["path"]), label, project_only=True)
    if path.stat().st_size != record["bytes"]:
        raise RuntimeError(f"{label}: byte count mismatch: {path}")
    if digest_file(path) != record["sha256"]:
        raise RuntimeError(f"{label}: SHA-256 mismatch: {path}")
    return path


def nullable_artifact_hash(record: dict[str, Any] | None) -> str | None:
    return None if record is None else record["sha256"]


def project_relative_artifact_path(record: dict[str, Any]) -> str:
    raw = Path(record["path"])
    path = raw if raw.is_absolute() else PROJECT / raw
    return str(path.resolve(strict=True).relative_to(PROJECT))


def valid_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        bytes.fromhex(value)
    except ValueError:
        return False
    return value == value.lower()


def json_lines(path: Path, label: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"{label} line {line_number}: {error}") from error
        if not isinstance(value, dict):
            raise RuntimeError(f"{label} line {line_number} is not an object")
        records.append(value)
    return records


def identity_observer_geometry(execution: dict[str, Any]) -> bool:
    probability_path = resolve_artifact(
        execution["probability_summary"], "identity probability summary"
    )
    coder_path = resolve_artifact(
        execution["coder_checkpoints"], "identity coder checkpoints"
    )
    state_path = resolve_artifact(
        execution["persistent_state"], "identity persistent state"
    )
    probability = json.loads(probability_path.read_text(encoding="ascii"))
    if not isinstance(probability, dict):
        return False
    transformed_bytes = execution["transformed_input"]["bytes"]
    if transformed_bytes <= FIXED_OBSERVER_CHECKPOINTS[-1]:
        return False
    probability_sha256 = probability.get("post_head_probability_sha256")
    checkpoints = (0, *FIXED_OBSERVER_CHECKPOINTS, transformed_bytes)
    kinds = ("start", "fixed", "fixed", "fixed", "terminal")
    if (
        set(probability)
        != {"coded_bits", "completed_coded_bytes", "post_head_probability_sha256"}
        or probability.get("coded_bits") != transformed_bytes * 8
        or probability.get("completed_coded_bytes") != transformed_bytes
        or probability_sha256 != execution.get("probability_sha256")
        or not valid_sha256(probability_sha256)
    ):
        return False
    coder = json_lines(coder_path, "identity coder checkpoints")
    if len(coder) != len(checkpoints):
        return False
    for record, checkpoint, kind in zip(coder, checkpoints, kinds):
        if (
            set(record)
            != {
                "coded_bits",
                "completed_coded_bytes",
                "high",
                "kind",
                "low",
                "payload_bytes",
                "probability_sha256",
            }
            or record.get("kind") != kind
            or record.get("completed_coded_bytes") != checkpoint
            or record.get("coded_bits") != checkpoint * 8
            or not valid_sha256(record.get("probability_sha256"))
            or not all(
                isinstance(record.get(name), int) and 0 <= record[name] <= 0xFFFFFFFF
                for name in ("low", "high")
            )
            or not isinstance(record.get("payload_bytes"), int)
            or record["payload_bytes"] < 0
        ):
            return False
    if coder[-1]["probability_sha256"] != probability_sha256:
        return False

    state = json_lines(state_path, "identity persistent state")
    stride = EXPECTED_OBSERVER_RANGES + 1
    if len(state) != len(checkpoints) * stride:
        return False
    frozen_geometry: tuple[tuple[int, int], ...] | None = None
    for index, (checkpoint, kind) in enumerate(zip(checkpoints, kinds)):
        records = state[index * stride : (index + 1) * stride]
        ranges = records[:-1]
        manifest = records[-1]
        geometry: list[tuple[int, int]] = []
        aggregate = hashlib.sha256()
        for ordinal, record in enumerate(ranges):
            byte_count = record.get("bytes")
            alignment = record.get("alignment")
            range_sha256 = record.get("sha256")
            if (
                set(record)
                != {"alignment", "bytes", "checkpoint", "kind", "ordinal", "sha256"}
                or record.get("checkpoint") != checkpoint
                or record.get("kind") != kind
                or record.get("ordinal") != ordinal
                or not isinstance(byte_count, int)
                or byte_count < 64 * 1024 * 1024
                or not isinstance(alignment, int)
                or alignment <= 0
                or alignment & (alignment - 1)
                or not valid_sha256(range_sha256)
            ):
                return False
            geometry.append((byte_count, alignment))
            aggregate.update(struct.pack("<Q", ordinal))
            aggregate.update(struct.pack("<Q", byte_count))
            aggregate.update(struct.pack("<Q", alignment))
            aggregate.update(bytes.fromhex(range_sha256))
        geometry_tuple = tuple(geometry)
        if frozen_geometry is None:
            frozen_geometry = geometry_tuple
        elif geometry_tuple != frozen_geometry:
            return False
        if (
            set(manifest)
            != {"allocation_count", "checkpoint", "kind", "manifest_sha256"}
            or manifest.get("allocation_count") != EXPECTED_OBSERVER_RANGES
            or manifest.get("checkpoint") != checkpoint
            or manifest.get("kind") != kind
            or manifest.get("manifest_sha256") != aggregate.hexdigest()
        ):
            return False
    return True


def false_comparisons() -> dict[str, bool]:
    return {
        "observer_calibration_antecedent_pass": False,
        "post_head_probability_identity_pass": False,
        "coder_checkpoint_identity_pass": False,
        "persistent_state_checkpoint_identity_pass": False,
        "arithmetic_payload_identity_pass": False,
        "decoded_transformed_identity_pass": False,
        "all_raw_inverses_pass": False,
        "parent_q1_self_extracting_archive_identity_expected": False,
        "identity_gate_pass": False,
    }


def false_resources() -> dict[str, bool]:
    return {
        "engineering_headroom_pass": False,
        "official_memory_pass": False,
        "temporary_disk_pass": False,
        "cpu_pass": False,
        "phase_measurement_pass": False,
        "cleanup_pass": False,
        "resource_gate_pass": False,
    }


def decisions(population: bool, identity: bool, resource: bool) -> dict[str, Any]:
    passed = population and identity and resource
    return {
        "population_identity_pass": population,
        "identity_gate_pass": identity,
        "resource_gate_pass": resource,
        "opening_100m_gate_pass": passed,
        "authorize_unchanged_full1g_q1": passed,
        "memory_safe_parent_qualified": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }


def derive(receipt: dict[str, Any]) -> tuple[
    dict[str, Any], dict[str, bool], dict[str, bool], dict[str, Any], list[str]
]:
    errors: list[str] = []
    verified_artifacts = 0
    required_artifacts = 0

    population = receipt["population"]
    try:
        population_path = regular_file(Path(population["path"]), "population")
        population_pass = (
            population_path.stat().st_size >= PREFIX_BYTES
            and digest_prefix(population_path, PREFIX_BYTES) == PREFIX_SHA256
        )
    except (OSError, RuntimeError, ValueError) as error:
        population_pass = False
        errors.append(f"population: {error}")

    artifact_records: list[tuple[str, dict[str, Any]]] = []
    artifact_records.extend(
        (f"antecedent {name}", record) for name, record in receipt["antecedents"].items()
    )
    for arm_name, arm in receipt["arms"].items():
        for field in (
            "binary",
            "coder_checkpoint_manifest",
            "persistent_state_manifest",
            "arithmetic_payload",
            "self_extracting_archive",
            "decoded_transformed",
            "raw_inverse",
            "execution_receipt",
        ):
            record = arm[field]
            if record is not None:
                artifact_records.append((f"arm {arm_name} {field}", record))
    artifact_records.extend(
        (
            ("resource phase measurement receipt", receipt["resources"]["phase_measurement_receipt"]),
            ("resource guard receipt", receipt["resources"]["resource_guard_receipt"]),
            ("resource memory.high receipt", receipt["resources"]["memory_high_receipt"]),
        )
    )
    required_artifacts = len(artifact_records)
    for label, record in artifact_records:
        try:
            resolve_artifact(record, label)
            verified_artifacts += 1
        except (OSError, RuntimeError, ValueError) as error:
            errors.append(str(error))
    all_artifacts = verified_artifacts == required_artifacts

    calibration_pass = False
    plan_binding_pass = False
    try:
        plan_path = resolve_artifact(
            receipt["antecedents"]["planning_contract"], "planning contract antecedent"
        )
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        coordinator = plan.get("coordinator", {})
        frozen = plan.get("frozen_parent_and_candidate", {})
        frozen_path_pass = all(
            frozen.get(plan_name) == project_relative_artifact_path(record)
            for plan_name, record in (
                ("q1_source_closure", receipt["antecedents"]["source_closure"]),
                ("q1_program_lock", receipt["antecedents"]["program_lock_verification"]),
                ("q1_release_build_a", receipt["antecedents"]["q1_release_build_a"]),
                ("q1_release_build_b", receipt["antecedents"]["q1_release_build_b"]),
                ("build_verification", receipt["antecedents"]["build_verification"]),
                ("q1_scope_build", receipt["antecedents"]["scope_build_receipt"]),
                ("opening_distant_10m_receipt", receipt["antecedents"]["opening_distant_10m_receipt"]),
                (
                    "opening_distant_10m_verification",
                    receipt["antecedents"]["opening_distant_10m_verification"],
                ),
            )
        )
        plan_binding_pass = (
            plan.get("artifact_id")
            == "cmix_filebacked_fxcm_100m_identity_resource_q0_v1"
            and plan.get("candidate_id") == CANDIDATE_ID
            and frozen_path_pass
            and plan.get("receipt_schema", {}).get("sha256") == INPUT_SCHEMA_SHA256
            and plan.get("independent_verification", {}).get("verifier")
            == str(Path(__file__).resolve().relative_to(PROJECT))
            and plan.get("independent_verification", {}).get("verifier_sha256")
            == digest_file(Path(__file__).resolve())
            and coordinator.get("runner")
            == "tools/cmix_filebacked_fxcm_100m_identity_resource.py"
            and coordinator.get("identity_arm_runner")
            == "tools/cmix_filebacked_fxcm_100m_identity_arm.py"
            and coordinator.get("identity_arm_schema")
            == "contracts/research/v1/"
            "cmix-filebacked-fxcm-100m-identity-arm.schema.json"
            and coordinator.get("release_stage_runner")
            == "tools/cmix_filebacked_fxcm_100m_release_stage.py"
            and coordinator.get("release_stage_schema")
            == "contracts/research/v1/"
            "cmix-filebacked-fxcm-100m-release-stage.schema.json"
            and coordinator.get("identity_resource_guard")
            == "tools/run_with_rss_guard.py"
            and coordinator.get("release_soft_high_guard")
            == "tools/run_with_resource_guard_v3_soft_high.py"
            and coordinator.get("release_resource_guard")
            == "tools/run_with_resource_guard_v3.py"
            and all(
                coordinator.get(hash_field) == digest_file(PROJECT / path_field)
                for path_field, hash_field in (
                    (coordinator["runner"], "runner_sha256"),
                    (coordinator["identity_arm_runner"], "identity_arm_runner_sha256"),
                    (coordinator["identity_arm_schema"], "identity_arm_schema_sha256"),
                    (coordinator["release_stage_runner"], "release_stage_runner_sha256"),
                    (coordinator["release_stage_schema"], "release_stage_schema_sha256"),
                    (coordinator["identity_resource_guard"], "identity_resource_guard_sha256"),
                    (coordinator["release_soft_high_guard"], "release_soft_high_guard_sha256"),
                    (coordinator["release_resource_guard"], "release_resource_guard_sha256"),
                )
            )
        )
        if not plan_binding_pass:
            errors.append("planning contract execution binding failed")
        calibration_path = resolve_artifact(
            receipt["antecedents"]["observer_calibration"],
            "observer calibration antecedent",
        )
        calibration_verification_path = resolve_artifact(
            receipt["antecedents"]["observer_calibration_verification"],
            "observer calibration verification antecedent",
        )
        calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
        calibration_verification = json.loads(
            calibration_verification_path.read_text(encoding="utf-8")
        )
        calibration_pass = (
            calibration.get("schema") == CALIBRATION_SCHEMA
            and calibration.get("candidate_id") == CANDIDATE_ID
            and calibration.get("terminal_pass") is True
            and calibration.get("comparisons", {}).get("observer_calibration_pass")
            is True
            and calibration_verification.get("schema")
            == CALIBRATION_VERIFICATION_SCHEMA
            and calibration_verification.get("candidate_id") == CANDIDATE_ID
            and calibration_verification.get("verified") is True
            and calibration_verification.get("passed") is True
            and calibration_verification.get("receipt_sha256")
            == receipt["antecedents"]["observer_calibration"]["sha256"]
            and calibration.get("antecedents", {}).get("planning_contract")
            == receipt["antecedents"]["planning_contract"]
            and calibration.get("antecedents", {}).get("observer_build")
            == receipt["antecedents"]["observer_build"]
        )
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
        errors.append(f"observer calibration antecedent: {error}")

    arms = receipt["arms"]
    parent = arms["I-P"]
    q1_identity = arms["I-Q"]
    q1_release = arms["R-Q"]
    observer_build_binding_pass = False
    try:
        observer_build_path = resolve_artifact(
            receipt["antecedents"]["observer_build"], "observer build antecedent"
        )
        observer_schema_path = resolve_artifact(
            receipt["antecedents"]["observer_build_schema"],
            "observer build schema antecedent",
        )
        observer_build = json.loads(observer_build_path.read_text(encoding="utf-8"))
        observer_schema = json.loads(observer_schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(observer_schema)
        jsonschema.validate(observer_build, observer_schema)
        observer_packages = {
            value["arm"]: value["packaged_binary"]
            for value in observer_build.get("packages", [])
        }
        observer_build_binding_pass = (
            observer_build.get("candidate_id") == CANDIDATE_ID
            and observer_build.get("decisions", {}).get("observer_build_pass") is True
            and set(observer_packages) == {"parent", "candidate", "negative"}
            and observer_packages["parent"] == parent["binary"]
            and observer_packages["candidate"] == q1_identity["binary"]
        )
        if not observer_build_binding_pass:
            errors.append("observer build does not bind the two identity packages")
    except (
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        jsonschema.ValidationError,
        jsonschema.SchemaError,
    ) as error:
        errors.append(f"observer build antecedent: {error}")

    identity_execution_pass = plan_binding_pass and observer_build_binding_pass
    for arm_name, arm in (("I-P", parent), ("I-Q", q1_identity)):
        try:
            execution_path = resolve_artifact(
                arm["execution_receipt"], f"{arm_name} execution receipt"
            )
            execution = json.loads(execution_path.read_text(encoding="utf-8"))
            identity_schema = json.loads(
                (
                    PROJECT
                    / "contracts/research/v1/"
                    "cmix-filebacked-fxcm-100m-identity-arm.schema.json"
                ).read_text(encoding="utf-8")
            )
            jsonschema.validate(execution, identity_schema)
            for field in (
                "runner",
                "receipt_schema",
                "encode_guard",
                "decode_guard",
                "probability_summary",
                "transformed_input",
            ):
                required_artifacts += 1
                try:
                    resolve_artifact(
                        execution[field], f"{arm_name} execution {field}"
                    )
                    verified_artifacts += 1
                except (OSError, RuntimeError, ValueError) as error:
                    errors.append(str(error))
            encode_guard_path = resolve_artifact(
                execution["encode_guard"], f"{arm_name} encode guard"
            )
            decode_guard_path = resolve_artifact(
                execution["decode_guard"], f"{arm_name} decode guard"
            )
            encode_guard = json.loads(encode_guard_path.read_text(encoding="utf-8"))
            decode_guard = json.loads(decode_guard_path.read_text(encoding="utf-8"))
            execution_pass = (
                execution.get("schema") == IDENTITY_ARM_SCHEMA
                and execution.get("candidate_id") == CANDIDATE_ID
                and execution.get("arm") == arm_name
                and execution.get("arm_pass") is True
                and execution.get("errors") == []
                and execution.get("command_sha256") == arm["command_sha256"]
                and execution.get("runner", {}).get("path")
                == str(PROJECT / "tools/cmix_filebacked_fxcm_100m_identity_arm.py")
                and execution.get("receipt_schema", {}).get("path")
                == str(
                    PROJECT
                    / "contracts/research/v1/"
                    "cmix-filebacked-fxcm-100m-identity-arm.schema.json"
                )
                and execution.get("receipt_schema", {}).get("sha256")
                == digest_file(
                    PROJECT
                    / "contracts/research/v1/"
                    "cmix-filebacked-fxcm-100m-identity-arm.schema.json"
                )
                and execution.get("population", {}).get("path")
                == receipt["population"]["path"]
                and execution.get("population", {}).get("bytes") == PREFIX_BYTES
                and execution.get("population", {}).get("sha256") == PREFIX_SHA256
                and execution.get("package") == arm["binary"]
                and execution.get("return_codes") == arm["return_codes"]
                and execution.get("probability_sha256")
                == arm["post_head_probability_sha256"]
                and execution.get("coder_checkpoints")
                == arm["coder_checkpoint_manifest"]
                and execution.get("persistent_state")
                == arm["persistent_state_manifest"]
                and execution.get("arithmetic_payload")
                == arm["arithmetic_payload"]
                and execution.get("self_extracting_archive")
                == arm["self_extracting_archive"]
                and execution.get("decoded_transformed")
                == arm["decoded_transformed"]
                and execution.get("raw_inverse") == arm["raw_inverse"]
                and execution.get("raw_inverse_pass") is True
                and execution.get("transformed_inverse_pass") is True
                and execution.get("observer_geometry_pass") is True
                and identity_observer_geometry(execution)
                and execution.get("backing_cleanup_pass")
                == arm["backing_cleanup_pass"]
                and scope.guard_pass(encode_guard)
                and scope.guard_pass(decode_guard)
            )
            identity_execution_pass &= execution_pass
            if not execution_pass:
                errors.append(f"{arm_name} execution receipt contract failed")
        except (
            OSError,
            RuntimeError,
            TypeError,
            ValueError,
            KeyError,
            json.JSONDecodeError,
            jsonschema.ValidationError,
        ) as error:
            identity_execution_pass = False
            errors.append(f"{arm_name} execution receipt: {error}")
    all_artifacts = verified_artifacts == required_artifacts
    instrument_contract = (
        parent["instrumented"] is True
        and q1_identity["instrumented"] is True
        and q1_release["instrumented"] is False
        and parent["resource_authority"] is False
        and q1_identity["resource_authority"] is False
        and q1_release["resource_authority"] is True
        and q1_release["post_head_probability_sha256"] is None
        and q1_release["coder_checkpoint_manifest"] is None
        and q1_release["persistent_state_manifest"] is None
    )
    if not instrument_contract:
        errors.append("instrumented/release arm separation differs from the frozen contract")

    probability_identity = (
        isinstance(parent["post_head_probability_sha256"], str)
        and parent["post_head_probability_sha256"]
        == q1_identity["post_head_probability_sha256"]
    )
    coder_identity = (
        nullable_artifact_hash(parent["coder_checkpoint_manifest"]) is not None
        and nullable_artifact_hash(parent["coder_checkpoint_manifest"])
        == nullable_artifact_hash(q1_identity["coder_checkpoint_manifest"])
    )
    state_identity = (
        nullable_artifact_hash(parent["persistent_state_manifest"]) is not None
        and nullable_artifact_hash(parent["persistent_state_manifest"])
        == nullable_artifact_hash(q1_identity["persistent_state_manifest"])
    )

    payload_records = [arm["arithmetic_payload"] for arm in arms.values()]
    payload_identity = all(record is not None for record in payload_records) and len(
        {(record["bytes"], record["sha256"]) for record in payload_records if record}
    ) == 1
    decoded_records = [parent["decoded_transformed"], q1_identity["decoded_transformed"]]
    decoded_identity = all(record is not None for record in decoded_records) and len(
        {(record["bytes"], record["sha256"]) for record in decoded_records if record}
    ) == 1
    raw_records = [arm["raw_inverse"] for arm in arms.values()]
    all_raw_inverses = all(
        arm["raw_inverse_pass"] is True
        and arm["return_codes"] == {"encode": 0, "decode": 0, "raw_inverse": 0}
        and record is not None
        and record["bytes"] == PREFIX_BYTES
        and record["sha256"] == PREFIX_SHA256
        for arm, record in zip(arms.values(), raw_records)
    )
    comparison = {
        "observer_calibration_antecedent_pass": calibration_pass,
        "post_head_probability_identity_pass": probability_identity,
        "coder_checkpoint_identity_pass": coder_identity,
        "persistent_state_checkpoint_identity_pass": state_identity,
        "arithmetic_payload_identity_pass": payload_identity,
        "decoded_transformed_identity_pass": decoded_identity,
        "all_raw_inverses_pass": all_raw_inverses,
        "parent_q1_self_extracting_archive_identity_expected": False,
        "identity_gate_pass": all(
            (
                instrument_contract,
                identity_execution_pass,
                calibration_pass,
                all_artifacts,
                probability_identity,
                coder_identity,
                state_identity,
                payload_identity,
                decoded_identity,
                all_raw_inverses,
            )
        ),
    }

    resource = receipt["resources"]
    resource_evidence_pass = False
    guard: dict[str, Any] = {}
    release_stage: dict[str, Any] = {}
    soft_high: dict[str, Any] = {}
    try:
        guard_path = resolve_artifact(
            resource["resource_guard_receipt"], "R-Q resource guard receipt"
        )
        phase_path = resolve_artifact(
            resource["phase_measurement_receipt"], "phase measurement receipt"
        )
        soft_high_path = resolve_artifact(
            resource["memory_high_receipt"], "memory.high receipt"
        )
        guard = json.loads(guard_path.read_text(encoding="utf-8"))
        release_stage = json.loads(phase_path.read_text(encoding="utf-8"))
        soft_high = json.loads(soft_high_path.read_text(encoding="utf-8"))
        guard_schema = json.loads(
            (PROJECT / "contracts/research/v1/resource-guard-receipt.v3.schema.json").read_text(
                encoding="utf-8"
            )
        )
        soft_schema = json.loads(
            (PROJECT / "contracts/research/v1/resource-guard-soft-high.schema.json").read_text(
                encoding="utf-8"
            )
        )
        release_schema = json.loads(
            (
                PROJECT
                / "contracts/research/v1/"
                "cmix-filebacked-fxcm-100m-release-stage.schema.json"
            ).read_text(encoding="utf-8")
        )
        jsonschema.validate(guard, guard_schema)
        jsonschema.validate(soft_high, soft_schema)
        jsonschema.validate(release_stage, release_schema)
        stage_outputs = release_stage.get("outputs", {})
        release_nested_artifacts_pass = True
        for field, record in (
            ("runner", release_stage.get("runner")),
            ("receipt schema", release_stage.get("receipt_schema")),
            *(
                (f"input {name}", value)
                for name, value in release_stage.get("inputs", {}).items()
            ),
        ):
            required_artifacts += 1
            try:
                resolve_artifact(record, f"release stage {field}")
                verified_artifacts += 1
            except (OSError, RuntimeError, TypeError, ValueError) as error:
                release_nested_artifacts_pass = False
                errors.append(str(error))
        build_verification_path = resolve_artifact(
            receipt["antecedents"]["build_verification"],
            "release build verification antecedent",
        )
        scope_build_path = resolve_artifact(
            receipt["antecedents"]["scope_build_receipt"],
            "scope-build antecedent",
        )
        build_verification = json.loads(
            build_verification_path.read_text(encoding="utf-8")
        )
        scope_build = json.loads(scope_build_path.read_text(encoding="utf-8"))
        scope_candidate = next(
            (
                value
                for value in scope_build.get("packages", [])
                if isinstance(value, dict) and value.get("arm") == "candidate"
            ),
            None,
        )
        stage_inputs = release_stage.get("inputs", {})
        input_paths = [
            resolve_artifact(stage_inputs[name], f"release stage input {name}")
            for name in (
                "raw_binary",
                "dictionary_payload",
                "article_order_payload",
                "package_header",
            )
        ]
        package_bytes, package_sha256 = digest_concatenation(input_paths)
        packaged_record = stage_outputs.get("packaged_compressor", {})
        release_build_binding_pass = (
            build_verification.get("candidate_id") == CANDIDATE_ID
            and build_verification.get("build_role") == "release"
            and build_verification.get("independent_build_pass") is True
            and receipt["antecedents"]["q1_release_build_a"]["sha256"]
            == build_verification.get("build_a_receipt_sha256")
            and receipt["antecedents"]["q1_release_build_b"]["sha256"]
            == build_verification.get("build_b_receipt_sha256")
            and stage_inputs.get("raw_binary", {}).get("sha256")
            == build_verification.get("build_a_binary_sha256")
            and scope_build.get("candidate_id") == CANDIDATE_ID
            and scope_build.get("package_asset_identity_pass") is True
            and scope_candidate is not None
            and stage_inputs.get("dictionary_payload")
            == scope_candidate.get("dictionary_payload")
            and stage_inputs.get("article_order_payload")
            == scope_candidate.get("article_order_payload")
            and stage_inputs.get("package_header") == scope_candidate.get("header")
            and stage_inputs.get("head_blob") == scope_build.get("head_blob")
            and packaged_record.get("bytes") == package_bytes
            and packaged_record.get("sha256") == package_sha256
        )
        resource_evidence_pass = (
            release_nested_artifacts_pass
            and release_build_binding_pass
            and plan_binding_pass
            and guard.get("schema") == GUARD_SCHEMA
            and guard.get("status") == "complete"
            and guard.get("returncode") == 0
            and guard.get("limit_mode") == "tree"
            and guard.get("limit_kib") == 9_765_625
            and guard.get("official_decimal_limit_kib") == 9_765_625
            and guard.get("cgroup", {}).get("requested_memory_max_bytes")
            == 10_000_000_000
            and guard.get("cgroup", {}).get("memory_max_bytes", 10_000_000_001)
            <= 10_000_000_000
            and all(guard.get("measurements", {}).values())
            and not any(guard.get("guards", {}).values())
            and release_stage.get("schema") == RELEASE_STAGE_SCHEMA
            and release_stage.get("candidate_id") == CANDIDATE_ID
            and release_stage.get("stage_pass") is True
            and release_stage.get("command_sha256") == q1_release["command_sha256"]
            and release_stage.get("runner", {}).get("path")
            == str(PROJECT / "tools/cmix_filebacked_fxcm_100m_release_stage.py")
            and release_stage.get("receipt_schema", {}).get("path")
            == str(
                PROJECT
                / "contracts/research/v1/"
                "cmix-filebacked-fxcm-100m-release-stage.schema.json"
            )
            and release_stage.get("receipt_schema", {}).get("sha256")
            == digest_file(
                PROJECT
                / "contracts/research/v1/"
                "cmix-filebacked-fxcm-100m-release-stage.schema.json"
            )
            and release_stage.get("population", {}).get("path")
            == receipt["population"]["path"]
            and release_stage.get("population", {}).get("bytes") == PREFIX_BYTES
            and release_stage.get("population", {}).get("sha256") == PREFIX_SHA256
            and release_stage.get("exact_raw_inverse_pass") is True
            and release_stage.get("backing_cleanup_pass") is True
            and stage_outputs.get("packaged_compressor") == q1_release["binary"]
            and stage_outputs.get("arithmetic_payload") == q1_release["arithmetic_payload"]
            and stage_outputs.get("self_extracting_archive")
            == q1_release["self_extracting_archive"]
            and stage_outputs.get("raw_inverse") == q1_release["raw_inverse"]
            and release_stage.get("return_codes") == q1_release["return_codes"]
            and q1_release.get("execution_receipt")
            == resource.get("phase_measurement_receipt")
            and soft_high.get("schema") == SOFT_HIGH_SCHEMA
            and soft_high.get("wrapper_pass") is True
            and soft_high.get("guard_return_code") == 0
            and soft_high.get("guard_status") == "complete"
            and soft_high.get("errors") == []
            and soft_high.get("requested_memory_high_bytes") == 9_000_000_000
            and soft_high.get("effective_memory_high_bytes", 9_000_000_001)
            <= 9_000_000_000
            and soft_high.get("memory_high_restore_pass") is True
            and soft_high.get("guard_receipt", {}).get("sha256")
            == resource["resource_guard_receipt"]["sha256"]
            and soft_high.get("guard_receipt") == resource["resource_guard_receipt"]
        )
    except (
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        jsonschema.ValidationError,
    ) as error:
        errors.append(f"resource evidence: {error}")

    phases = release_stage.get("phase_measurements", [])
    guard_peaks = guard.get("peaks", {})
    guard_events = guard.get("cgroup_events", {}).get("delta", {})
    process_tree_peak = max(
        [guard_peaks.get("max_sampled_tree_rss_kib", 0)]
        + [phase.get("tree_rss_peak_kib", 0) for phase in phases]
    )
    process_vmhwm_peak = max(
        [guard_peaks.get("max_observed_process_vmhwm_kib", 0)]
        + [phase.get("largest_process_vmhwm_kib", 0) for phase in phases]
    )
    cgroup_peak = max(
        [guard_peaks.get("cgroup_memory_peak_bytes", 0)]
        + [phase.get("cgroup_peak_bytes", 0) for phase in phases]
    )
    scratch_logical_peak = max(
        [guard_peaks.get("max_sampled_scratch_logical_bytes", 0)]
        + [phase.get("scratch_logical_bytes", 0) for phase in phases]
    )
    scratch_allocated_peak = max(
        [guard_peaks.get("max_sampled_scratch_allocated_bytes", 0)]
        + [phase.get("scratch_allocated_bytes", 0) for phase in phases]
    )
    observed_resource_values = {
        "process_tree_peak_rss_kib": process_tree_peak,
        "largest_process_vmhwm_kib": process_vmhwm_peak,
        "cgroup_memory_peak_bytes": cgroup_peak,
        "memory_events_high": guard_events.get("high", 0),
        "memory_events_max": guard_events.get("max", 0),
        "memory_events_oom": guard_events.get("oom", 0),
        "memory_events_oom_kill": guard_events.get("oom_kill", 0),
        "maximum_logical_cpus": guard_peaks.get("max_sampled_allowed_cpu_count", 0),
        "scratch_logical_peak_bytes": scratch_logical_peak,
        "scratch_allocated_peak_bytes": scratch_allocated_peak,
        "scratch_after_cleanup_bytes": release_stage.get(
            "scratch_after_cleanup_bytes", -1
        ),
        "phase_measurements": phases,
    }
    for name, observed in observed_resource_values.items():
        if resource.get(name) != observed:
            errors.append(f"resource value differs from measured evidence: {name}")
    engineering = (
        resource_evidence_pass
        and process_tree_peak <= 9_000_000
        and process_vmhwm_peak <= 9_000_000
        and cgroup_peak <= 10_000_000_000
        and guard_events.get("max", 0) == 0
        and guard_events.get("oom", 0) == 0
        and guard_events.get("oom_kill", 0) == 0
    )
    official = (
        resource_evidence_pass
        and process_tree_peak <= 9_765_625
        and process_vmhwm_peak <= 9_765_625
        and cgroup_peak <= 10_000_000_000
        and guard_events.get("max", 0) == 0
        and guard_events.get("oom", 0) == 0
        and guard_events.get("oom_kill", 0) == 0
    )
    temporary_disk = (
        scratch_allocated_peak <= 100_000_000_000
        and release_stage.get("scratch_after_cleanup_bytes") == 0
    )
    cpu = guard_peaks.get("max_sampled_allowed_cpu_count") == 1
    phase_names = [phase["phase"] for phase in phases]
    phase_pass = (
        len(phase_names) == len(PHASES)
        and tuple(phase_names) == PHASES
        and all(phase["observed"] is True for phase in phases)
        and process_tree_peak
        >= max(phase["tree_rss_peak_kib"] for phase in phases)
        and process_vmhwm_peak
        >= max(phase["largest_process_vmhwm_kib"] for phase in phases)
        and cgroup_peak
        >= max(phase["cgroup_peak_bytes"] for phase in phases)
        and scratch_logical_peak
        >= max(phase["scratch_logical_bytes"] for phase in phases)
        and scratch_allocated_peak
        >= max(phase["scratch_allocated_bytes"] for phase in phases)
    )
    cleanup = release_stage.get("scratch_after_cleanup_bytes") == 0 and all(
        arm["backing_cleanup_pass"] is True for arm in arms.values()
    )
    resource_derived = {
        "engineering_headroom_pass": engineering,
        "official_memory_pass": official,
        "temporary_disk_pass": temporary_disk,
        "cpu_pass": cpu,
        "phase_measurement_pass": phase_pass,
        "cleanup_pass": cleanup,
        "resource_gate_pass": all(
            (engineering, official, temporary_disk, cpu, phase_pass, cleanup)
        ),
    }
    derived_decisions = decisions(
        population_pass,
        comparison["identity_gate_pass"],
        resource_derived["resource_gate_pass"],
    )

    if receipt["comparisons"] != comparison:
        errors.append("declared comparisons differ from independent derivation")
    for key, value in resource_derived.items():
        if resource[key] != value:
            errors.append(f"declared resource decision differs: {key}")
    if receipt["decisions"] != derived_decisions:
        errors.append("declared decisions differ from independent derivation")
    if receipt["terminal_pass"] is not derived_decisions["opening_100m_gate_pass"]:
        errors.append("terminal_pass differs from the complete derived gate")
    if receipt["errors"] != [] and receipt["terminal_pass"] is True:
        errors.append("passing receipt contains source errors")

    all_artifacts = verified_artifacts == required_artifacts
    artifact_checks = {
        "population_prefix_identity_pass": population_pass,
        "required_artifact_count": required_artifacts,
        "verified_artifact_count": verified_artifacts,
        "all_artifacts_pass": all_artifacts,
    }
    return artifact_checks, comparison, resource_derived, derived_decisions, errors


def write_json_exclusive(path: Path, value: dict[str, Any]) -> None:
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short verification write")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def new_output_path(raw_path: Path) -> Path:
    path = raw_path if raw_path.is_absolute() else PROJECT / raw_path
    absolute = path.absolute()
    parent = absolute.parent
    current = Path(parent.anchor)
    for component in parent.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"verification parent has symlink component: {current}")
    if not parent.is_dir():
        raise RuntimeError("verification parent must be an existing directory")
    resolved_parent = parent.resolve(strict=True)
    if PROJECT != resolved_parent and PROJECT not in resolved_parent.parents:
        raise RuntimeError("verification output must remain inside the project")
    resolved_output = resolved_parent / absolute.name
    if resolved_output.exists() or resolved_output.is_symlink():
        raise FileExistsError(f"refusing to overwrite verification: {resolved_output}")
    return resolved_output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    args = parser.parse_args()

    require_released_lease(args.exclusive_lease)
    input_schema, output_schema = validate_schema_hashes()
    receipt_path = regular_file(args.receipt, "100M receipt", project_only=True)
    output_path = new_output_path(args.verification)

    raw = receipt_path.read_bytes()
    receipt = json.loads(raw.decode("utf-8"))
    validation_errors: list[str] = []
    try:
        jsonschema.Draft202012Validator(input_schema).validate(receipt)
    except jsonschema.ValidationError as error:
        validation_errors.append(f"receipt schema: {error.message}")

    if validation_errors:
        artifact_checks = {
            "population_prefix_identity_pass": False,
            "required_artifact_count": 0,
            "verified_artifact_count": 0,
            "all_artifacts_pass": False,
        }
        comparison = false_comparisons()
        resource = false_resources()
        derived = decisions(False, False, False)
        errors = validation_errors
    else:
        artifact_checks, comparison, resource, derived, errors = derive(receipt)

    verified = not errors
    passed = verified and derived["opening_100m_gate_pass"]
    output = {
        "schema": (
            "gamma.enwiki9.cmix-filebacked-fxcm-100m-identity-resource-"
            "verification.v1"
        ),
        "candidate_id": CANDIDATE_ID,
        "verified": verified,
        "passed": passed,
        "errors": errors,
        "receipt_sha256": digest_bytes(raw),
        "artifact_checks": artifact_checks,
        "derived_comparisons": comparison,
        "derived_resources": resource,
        "derived_decisions": derived,
        "claim_authority": "none",
        "promotion_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.Draft202012Validator(output_schema).validate(output)
    write_json_exclusive(output_path, output)
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
