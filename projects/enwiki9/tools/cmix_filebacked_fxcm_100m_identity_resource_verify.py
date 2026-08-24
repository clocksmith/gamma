#!/usr/bin/env python3
"""Independently rederive the sealed q1 opening-100M identity/resource gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any

import jsonschema


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
INPUT_SCHEMA_SHA256 = "0bf3d6bc4716b369ff7d8d7b6dd9cf89545a07c8a35918f7d5e004c018eef321"
OUTPUT_SCHEMA_SHA256 = "43991c9ec64fdf787e0ba15e5e2491ccbc7e9542df066c5d12e9bb933f263c3f"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
PREFIX_BYTES = 100_000_000
PREFIX_SHA256 = "2b49720ec4d78c3c9fabaee6e4179a5e997302b3a70029f30f2d582218c024a8"
PHASES = {
    "package_helper_construction",
    "frontend_preprocessing",
    "model_pretraining",
    "arithmetic_payload_encode",
    "archive_assembly",
    "archive_decode",
    "frontend_inverse",
    "cleanup",
}


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


def false_comparisons() -> dict[str, bool]:
    return {
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
            "guard_receipt",
        ):
            record = arm[field]
            if record is not None:
                artifact_records.append((f"arm {arm_name} {field}", record))
    required_artifacts = len(artifact_records)
    for label, record in artifact_records:
        try:
            resolve_artifact(record, label)
            verified_artifacts += 1
        except (OSError, RuntimeError, ValueError) as error:
            errors.append(str(error))
    all_artifacts = verified_artifacts == required_artifacts

    arms = receipt["arms"]
    parent = arms["I-P"]
    q1_identity = arms["I-Q"]
    q1_release = arms["R-Q"]
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
    engineering = (
        resource["process_tree_peak_rss_kib"] <= 9_000_000
        and resource["largest_process_vmhwm_kib"] <= 9_000_000
        and resource["cgroup_memory_peak_bytes"] <= 10_000_000_000
        and resource["memory_events_max"] == 0
        and resource["memory_events_oom"] == 0
        and resource["memory_events_oom_kill"] == 0
    )
    official = (
        resource["process_tree_peak_rss_kib"] <= 9_765_625
        and resource["largest_process_vmhwm_kib"] <= 9_765_625
        and resource["cgroup_memory_peak_bytes"] <= 10_000_000_000
        and resource["memory_events_max"] == 0
        and resource["memory_events_oom"] == 0
        and resource["memory_events_oom_kill"] == 0
    )
    temporary_disk = (
        resource["scratch_allocated_peak_bytes"] <= 100_000_000_000
        and resource["scratch_after_cleanup_bytes"] == 0
    )
    cpu = resource["maximum_logical_cpus"] == 1
    phases = resource["phase_measurements"]
    phase_names = [phase["phase"] for phase in phases]
    phase_pass = (
        len(phase_names) == len(PHASES)
        and set(phase_names) == PHASES
        and all(phase["observed"] is True for phase in phases)
        and resource["process_tree_peak_rss_kib"]
        >= max(phase["tree_rss_peak_kib"] for phase in phases)
        and resource["largest_process_vmhwm_kib"]
        >= max(phase["largest_process_vmhwm_kib"] for phase in phases)
        and resource["cgroup_memory_peak_bytes"]
        >= max(phase["cgroup_peak_bytes"] for phase in phases)
        and resource["scratch_logical_peak_bytes"]
        >= max(phase["scratch_logical_bytes"] for phase in phases)
        and resource["scratch_allocated_peak_bytes"]
        >= max(phase["scratch_allocated_bytes"] for phase in phases)
    )
    cleanup = resource["scratch_after_cleanup_bytes"] == 0 and all(
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
