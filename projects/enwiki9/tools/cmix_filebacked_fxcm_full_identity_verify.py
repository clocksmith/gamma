#!/usr/bin/env python3
"""Independently rederive q1 full probability and sparse-state identity."""

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

import cmix_filebacked_fxcm_100m_identity_resource_verify as proof100
import cmix_filebacked_fxcm_100m_observer_calibration_verify as calibration_verify
import cmix_filebacked_fxcm_full_soft_high_verify as full_arm_verify
import enwiki9_python_source_closure as python_source


PROJECT = Path(__file__).resolve().parents[1]
CONTRACTS = PROJECT / "contracts/research/v1"
SOURCE_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-full-identity.schema.json"
ARM_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-full-identity-arm.schema.json"
OUTPUT_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-full-identity-verification.schema.json"
BUILD_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-100m-observer-build.schema.json"
CALIBRATION_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-100m-observer-calibration.schema.json"
CALIBRATION_VERIFICATION_SCHEMA = (
    CONTRACTS / "cmix-filebacked-fxcm-100m-observer-calibration-verification.schema.json"
)
OPENING_100M_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-100m-identity-resource.schema.json"
OPENING_100M_VERIFICATION_SCHEMA = (
    CONTRACTS / "cmix-filebacked-fxcm-100m-identity-resource-verification.schema.json"
)
SOURCE_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-full-identity.v1"
ARM_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-full-identity-arm.v1"
OUTPUT_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-full-identity-verification.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
CANONICAL_BYTES = 1_000_000_000
CANONICAL_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
PAYLOAD_BYTES = 107_730_531
PAYLOAD_SHA256 = "889aa8074e0a84eb89997986899f1ef9f7cc0e52e87d1d36f86899fc679f5490"
FIXED_MODELED_CHECKPOINTS = (
    16_777_216,
    33_554_432,
    50_331_648,
    100_000_000,
    500_000_000,
)
EXPECTED_RANGES = 26
MINIMUM_RANGE_BYTES = 64 * 1024 * 1024
CALIBRATION = {
    "opening_10m": (
        0,
        "d651255043d85fa2f9bb6076a145710edd1366cf3e634033d2b2dadcff54e97a",
        46_128_408,
    ),
    "distant_10m": (
        500_000_000,
        "4ab13c5d455f591fa2f27e8e234833f65ebbacc5e2ef4101fbd547f85aa4ec59",
        48_103_592,
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(16 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


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
    resolved = absolute.resolve(strict=True)
    if PROJECT != resolved and PROJECT not in resolved.parents:
        raise ValueError(f"{label}: path escapes project root")
    return resolved


def artifact(path: Path) -> dict[str, Any]:
    path = regular_file(path, "artifact")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def artifact_path(record: Any, label: str) -> Path:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise ValueError(f"{label}: malformed artifact record")
    path = regular_file(Path(record["path"]), label)
    if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
        raise ValueError(f"{label}: artifact identity mismatch")
    return path


def load_json_artifact(record: Any, label: str) -> tuple[Path, dict[str, Any]]:
    path = artifact_path(record, label)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label}: JSON root is not an object")
    return path, value


def same_file_value(left: Any, right: Any) -> bool:
    return bool(
        isinstance(left, dict)
        and isinstance(right, dict)
        and left.get("bytes") == right.get("bytes")
        and left.get("sha256") == right.get("sha256")
    )


def python_source_closure_rows(entries: tuple[Path, ...]) -> list[dict[str, str]]:
    return [
        {
            "path": path.relative_to(PROJECT).as_posix(),
            "sha256": f"sha256:{sha256_file(path)}",
        }
        for path in python_source.local_source_closure(entries)
    ]


def diagnostic_guard_pass(value: dict[str, Any], role: str, arm: dict[str, Any]) -> bool:
    objective = value.get("objective", {})
    selected_cpu = arm.get("selected_logical_cpu")
    sample_cpu_pass = all(
        isinstance(value.get(name), dict)
        and value[name].get("allowed_cpu_union") == [selected_cpu]
        for name in ("peak_sample", "peak_tree_sample", "latest_sample")
    )
    return bool(
        value.get("schema") == "gamma.enwiki9.resource-guard-receipt.v2"
        and value.get("status") == "complete"
        and value.get("returncode") == 0
        and value.get("command") == ["./cmix", "-e", "enwik9", "out.cmix"]
        and value.get("label") == f"{CANDIDATE_ID}-full-identity-{role}"
        and value.get("phase") == "diagnostic"
        and value.get("sample_interval_seconds") == 0.25
        and value.get("limit_kib") == 11_500_000
        and value.get("limit_mode") == "tree"
        and value.get("official_decimal_limit_kib") is None
        and value.get("official_decimal_over_limit_kib") is None
        and value.get("scratch_paths") == [arm.get("scratch_root")]
        and value.get("temporary_disk_limit_bytes") == 100_000_000_000
        and value.get("temporary_disk_measurement_complete") is True
        and value.get("max_logical_cpus") == 1
        and value.get("affinity_measurement_complete") is True
        and value.get("max_sampled_allowed_cpu_count") == 1
        and sample_cpu_pass
        and objective.get("objectiveId") == "gamma-enwik9-hutter-105m-v1"
        and objective.get("targetScoreBytes") == 105_000_000
        and objective.get("corpusBytes") == CANONICAL_BYTES
        and objective.get("corpusSha256") == CANONICAL_SHA256
        and value.get("wall_time_measurement_complete") is True
        and value.get("wall_time_exceeded") is False
        and value.get("rss_guard_exceeded") is False
        and value.get("official_decimal_memory_exceeded") is False
        and value.get("temporary_disk_guard_exceeded") is False
        and value.get("logical_cpu_guard_exceeded") is False
    )


def load_contract(path: Path, schema_path: Path, schema_id: str) -> dict[str, Any]:
    value = json.loads(regular_file(path, schema_id).read_text(encoding="utf-8"))
    schema = json.loads(regular_file(schema_path, f"{schema_id} schema").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(value, schema)
    if value.get("schema") != schema_id:
        raise ValueError(f"{path}: schema identity mismatch")
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


def json_lines(path: Path, label: str) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{label} line {line_number} is not an object")
        values.append(value)
    return values


def valid_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        return False
    try:
        bytes.fromhex(value)
    except ValueError:
        return False
    return True


def parse_observer(arm: dict[str, Any]) -> dict[str, Any]:
    probability_path = artifact_path(
        arm["observer_outputs"]["probability_manifest"], "probability manifest"
    )
    coder_path = artifact_path(
        arm["observer_outputs"]["coder_manifest"], "coder manifest"
    )
    state_path = artifact_path(
        arm["observer_outputs"]["state_manifest"], "state manifest"
    )
    probability = json.loads(probability_path.read_text(encoding="ascii"))
    modeled_bytes = probability.get("completed_coded_bytes")
    probability_sha256 = probability.get("post_head_probability_sha256")
    if (
        set(probability)
        != {"coded_bits", "completed_coded_bytes", "post_head_probability_sha256"}
        or not isinstance(modeled_bytes, int)
        or modeled_bytes <= FIXED_MODELED_CHECKPOINTS[-1]
        or probability.get("coded_bits") != modeled_bytes * 8
        or not valid_sha256(probability_sha256)
    ):
        raise ValueError("probability manifest geometry mismatch")
    checkpoints = (0, *FIXED_MODELED_CHECKPOINTS, modeled_bytes)
    kinds = ("start", *("fixed" for _ in FIXED_MODELED_CHECKPOINTS), "terminal")
    coder_records = json_lines(coder_path, "coder manifest")
    if len(coder_records) != len(checkpoints):
        raise ValueError("coder checkpoint count mismatch")
    coder_summary: list[dict[str, Any]] = []
    for index, (record, checkpoint, kind) in enumerate(
        zip(coder_records, checkpoints, kinds)
    ):
        if (
            set(record)
            != {
                "coded_bits", "completed_coded_bytes", "high", "kind", "low",
                "payload_bytes", "probability_sha256",
            }
            or record.get("completed_coded_bytes") != checkpoint
            or record.get("kind") != kind
            or record.get("coded_bits") != checkpoint * 8
            or not valid_sha256(record.get("probability_sha256"))
            or not all(
                isinstance(record.get(name), int) and 0 <= record[name] <= 0xFFFFFFFF
                for name in ("low", "high")
            )
            or not isinstance(record.get("payload_bytes"), int)
            or record["payload_bytes"] < 0
        ):
            raise ValueError(f"coder checkpoint {index} mismatch")
        coder_summary.append(
            {
                "modeled_bytes": checkpoint,
                "kind": kind,
                "coded_bits": record["coded_bits"],
                "low": record["low"],
                "high": record["high"],
                "payload_bytes": record["payload_bytes"],
                "probability_sha256": record["probability_sha256"],
            }
        )
    if coder_summary[-1]["probability_sha256"] != probability_sha256:
        raise ValueError("terminal probability digest mismatch")

    state_records = json_lines(state_path, "state manifest")
    records_per_checkpoint = EXPECTED_RANGES + 1
    if len(state_records) != len(checkpoints) * records_per_checkpoint:
        raise ValueError("state checkpoint record count mismatch")
    geometry_reference: tuple[tuple[int, int], ...] | None = None
    state_summary: list[dict[str, Any]] = []
    for checkpoint_index, (checkpoint, kind) in enumerate(zip(checkpoints, kinds)):
        begin = checkpoint_index * records_per_checkpoint
        chunk = state_records[begin : begin + records_per_checkpoint]
        ranges = chunk[:-1]
        manifest = chunk[-1]
        geometry: list[tuple[int, int]] = []
        aggregate = hashlib.sha256()
        for ordinal, record in enumerate(ranges):
            byte_count = record.get("bytes")
            alignment = record.get("alignment")
            digest = record.get("sha256")
            if (
                set(record)
                != {"alignment", "bytes", "checkpoint", "kind", "ordinal", "sha256"}
                or record.get("checkpoint") != checkpoint
                or record.get("kind") != kind
                or record.get("ordinal") != ordinal
                or not isinstance(byte_count, int)
                or byte_count < MINIMUM_RANGE_BYTES
                or not isinstance(alignment, int)
                or alignment <= 0
                or alignment & (alignment - 1)
                or not valid_sha256(digest)
            ):
                raise ValueError(
                    f"state checkpoint {checkpoint_index} range {ordinal} mismatch"
                )
            geometry.append((byte_count, alignment))
            aggregate.update(struct.pack("<Q", ordinal))
            aggregate.update(struct.pack("<Q", byte_count))
            aggregate.update(struct.pack("<Q", alignment))
            aggregate.update(bytes.fromhex(digest))
        frozen_geometry = tuple(geometry)
        if geometry_reference is None:
            geometry_reference = frozen_geometry
        elif frozen_geometry != geometry_reference:
            raise ValueError("semantic allocation geometry changed")
        if (
            set(manifest)
            != {"allocation_count", "checkpoint", "kind", "manifest_sha256"}
            or manifest.get("allocation_count") != EXPECTED_RANGES
            or manifest.get("checkpoint") != checkpoint
            or manifest.get("kind") != kind
            or manifest.get("manifest_sha256") != aggregate.hexdigest()
        ):
            raise ValueError(f"state checkpoint {checkpoint_index} manifest mismatch")
        state_summary.append(
            {
                "modeled_bytes": checkpoint,
                "kind": kind,
                "allocation_count": EXPECTED_RANGES,
                "manifest_sha256": aggregate.hexdigest(),
            }
        )
    return {
        "modeled_bytes": modeled_bytes,
        "coded_bits": modeled_bytes * 8,
        "probability_sha256": probability_sha256,
        "coder_checkpoints": coder_summary,
        "state_checkpoints": state_summary,
    }


def negative_checkpoint_controls(arm: dict[str, Any]) -> bool:
    expected_prefix = (0, *FIXED_MODELED_CHECKPOINTS)

    def valid(coder: Any, state: Any) -> bool:
        if not isinstance(coder, list) or not isinstance(state, list) or len(coder) != 7 or len(state) != 7:
            return False
        coder_positions = tuple(item.get("modeled_bytes") for item in coder)
        state_positions = tuple(item.get("modeled_bytes") for item in state)
        kinds = ("start", *("fixed" for _ in FIXED_MODELED_CHECKPOINTS), "terminal")
        return bool(
            coder_positions == state_positions
            and coder_positions[:-1] == expected_prefix
            and coder_positions[-1] == arm["modeled_stream"]["bytes"]
            and tuple(item.get("kind") for item in coder) == kinds
            and tuple(item.get("kind") for item in state) == kinds
            and all(item.get("coded_bits") == item.get("modeled_bytes") * 8 for item in coder)
        )

    coder = arm["coder_checkpoints"]
    state = arm["state_checkpoints"]
    if not valid(coder, state):
        return False
    wrong_count = json.loads(json.dumps(coder))
    wrong_count[3]["coded_bits"] += 8
    wrong_terminal = json.loads(json.dumps(state))
    wrong_terminal[-1]["modeled_bytes"] -= 1
    mutations = (
        (coder[:-1], state),
        ([coder[0], *coder], state),
        ([coder[1], coder[0], *coder[2:]], state),
        (wrong_count, state),
        (coder, state[:-1]),
        (coder, wrong_terminal),
    )
    return all(not valid(candidate_coder, candidate_state) for candidate_coder, candidate_state in mutations)


def calibration_evidence(
    receipt: dict[str, Any],
    verification: dict[str, Any],
) -> tuple[bool, list[dict[str, Any]], dict[str, str], dict[str, Any]]:
    input_schema, output_schema = calibration_verify.schemas()
    jsonschema.validate(receipt, input_schema)
    jsonschema.validate(verification, output_schema)
    checks, derived, errors = calibration_verify.derive(receipt)
    independently_passed = bool(
        not errors
        and checks == verification["artifact_checks"]
        and derived == verification["derived_comparisons"]
        and verification["verified"] is True
        and verification["passed"] is True
        and verification["errors"] == []
        and receipt["terminal_pass"] is True
    )
    by_key = {(run["offset"], run["arm"]): run for run in receipt["runs"]}
    rows: list[dict[str, Any]] = []
    for name, (offset, expected_digest, expected_bits) in CALIBRATION.items():
        run = by_key[(offset, "I-P")]
        probability_path = artifact_path(
            run["probability_summary"], f"{name} probability summary"
        )
        probability = json.loads(probability_path.read_text(encoding="ascii"))
        rows.append(
            {
                "population": name,
                "expected_probability_sha256": expected_digest,
                "observed_probability_sha256": run["probability_sha256"],
                "expected_coded_bits": expected_bits,
                "observed_coded_bits": probability["coded_bits"],
            }
        )
    opening_parent = by_key[(0, "I-P")]
    opening_negative = by_key[(0, "N-P")]
    controls = {
        "observer_off_payload_sha256": opening_parent["reference_payload"]["sha256"],
        "observer_on_payload_sha256": opening_parent["arithmetic_payload"]["sha256"],
        "post_head_probability_sha256": opening_parent["probability_sha256"],
        "pre_head_probability_sha256": opening_negative["probability_sha256"],
    }
    _, build = load_json_artifact(receipt["antecedents"]["observer_build"], "observer build")
    build_schema_path = artifact_path(
        receipt["antecedents"]["observer_build_schema"], "observer build schema"
    )
    build_schema = json.loads(build_schema_path.read_text())
    jsonschema.Draft202012Validator.check_schema(build_schema)
    jsonschema.validate(build, build_schema)
    return independently_passed, rows, controls, build


def opening_100m_pass(receipt: dict[str, Any], verification: dict[str, Any]) -> bool:
    input_schema, output_schema = proof100.validate_schema_hashes()
    jsonschema.validate(receipt, input_schema)
    jsonschema.validate(verification, output_schema)
    artifacts, comparisons, resources, decisions, errors = proof100.derive(receipt)
    return bool(
        errors == []
        and verification["errors"] == []
        and verification["verified"] is True
        and verification["passed"] is True
        and verification["artifact_checks"] == artifacts
        and verification["derived_comparisons"] == comparisons
        and verification["derived_resources"] == resources
        and verification["derived_decisions"] == decisions
        and decisions["opening_100m_gate_pass"] is True
    )


def verify(receipt_path: Path) -> tuple[dict[str, Any], bool]:
    source = load_contract(receipt_path, SOURCE_SCHEMA, SOURCE_SCHEMA_ID)
    checks: dict[str, bool] = {}
    errors: list[str] = []
    checks["population_artifact_exact"] = (
        source["population"]["bytes"] == CANONICAL_BYTES
        and source["population"]["sha256"] == CANONICAL_SHA256
        and artifact_path(source["population"], "population").stat().st_size == CANONICAL_BYTES
    )

    artifact_records: list[tuple[str, dict[str, Any]]] = [
        ("planning contract", source["planning_contract"]),
        ("coordinator", source["coordinator"]),
        ("arm runner", source["arm_runner"]),
        ("arm schema", source["arm_schema"]),
        ("Python source closure", source["python_source_closure"]),
    ]
    artifact_records.extend((f"activation {name}", value) for name, value in source["activation"].items())
    artifact_records.extend(
        (f"observer antecedent {name}", value)
        for name, value in source["observer_antecedents"].items()
    )
    for role, summary in source["arms"].items():
        artifact_records.extend(
            (f"{role} {name}", summary[name])
            for name in (
                "observer_receipt", "binary", "modeled_stream", "payload",
                "self_extracting_archive",
            )
        )
    artifact_checks = []
    for label, record in artifact_records:
        try:
            artifact_path(record, label)
            artifact_checks.append(True)
        except (OSError, ValueError) as error:
            artifact_checks.append(False)
            errors.append(str(error))
    checks["artifact_closure_exact"] = all(artifact_checks)

    plan_path, plan = load_json_artifact(source["planning_contract"], "planning contract")
    plan_schema_path = regular_file(
        PROJECT / "operations/planning" / plan.get("$schema", ""),
        "full identity planning schema",
    )
    plan_schema = json.loads(plan_schema_path.read_text())
    jsonschema.Draft202012Validator.check_schema(plan_schema)
    jsonschema.validate(plan, plan_schema)
    checks["planning_schema_binding"] = (
        plan.get("planning_schema_sha256") == sha256_file(plan_schema_path)
    )
    implementation = plan.get("implementation", {})
    expected_bindings = {
        "coordinator": source["coordinator"],
        "arm_runner": source["arm_runner"],
        "arm_schema": source["arm_schema"],
        "joint_schema": artifact(SOURCE_SCHEMA),
        "verifier": artifact(Path(__file__).resolve()),
        "verification_schema": artifact(OUTPUT_SCHEMA),
        "python_source_closure": source["python_source_closure"],
    }
    checks["plan_implementation_binding"] = bool(
        plan.get("artifact_id") == "cmix_filebacked_fxcm_full_probability_state_identity_q0_v1"
        and plan.get("candidate_id") == CANDIDATE_ID
        and all(
            implementation.get(name, {}).get("path")
            == str(Path(record["path"]).relative_to(PROJECT))
            and implementation.get(name, {}).get("sha256") == record["sha256"]
            for name, record in expected_bindings.items()
        )
    )
    checks["plan_proof_artifact_binding"] = all(
        plan.get("proof_artifacts", {}).get(name) == expected
        for name, expected in {
            "arm_receipt_schema": {
                "path": str(ARM_SCHEMA.relative_to(PROJECT)),
                "sha256": sha256_file(ARM_SCHEMA),
            },
            "joint_receipt_schema": {
                "path": str(SOURCE_SCHEMA.relative_to(PROJECT)),
                "sha256": sha256_file(SOURCE_SCHEMA),
            },
            "verification_schema": {
                "path": str(OUTPUT_SCHEMA.relative_to(PROJECT)),
                "sha256": sha256_file(OUTPUT_SCHEMA),
            },
            "verifier": {
                "path": str(Path(__file__).resolve().relative_to(PROJECT)),
                "sha256": sha256_file(Path(__file__).resolve()),
            },
        }.items()
    )
    source_closure_path = artifact_path(
        source["python_source_closure"], "Python source closure"
    )
    source_closure = json.loads(source_closure_path.read_text(encoding="ascii"))
    expected_source_closure = python_source_closure_rows(
        (
            artifact_path(source["coordinator"], "coordinator"),
            artifact_path(source["arm_runner"], "arm runner"),
            Path(__file__).resolve(strict=True),
        )
    )
    checks["python_source_closure_exact"] = source_closure == expected_source_closure

    activation_values: dict[str, dict[str, Any]] = {}
    activation_paths: dict[str, Path] = {}
    for name, record in source["activation"].items():
        activation_paths[name], activation_values[name] = load_json_artifact(
            record, f"activation {name}"
        )
    full_arms_pass = True
    for arm in ("a", "b"):
        recomputed, passed = full_arm_verify.verify(
            activation_paths[f"full_roundtrip_{arm}"]
        )
        full_arms_pass &= bool(
            passed
            and activation_values[f"full_roundtrip_{arm}_verification"] == recomputed
        )
    arm_a = activation_values["full_roundtrip_a"]
    arm_b = activation_values["full_roundtrip_b"]
    full_arms_pass &= all(
        same_file_value(arm_a["outputs"][name], arm_b["outputs"][name])
        for name in ("payload", "archive", "restored")
    )
    opening_pass = opening_100m_pass(
        activation_values["opening_100m_receipt"],
        activation_values["opening_100m_verification"],
    ) and (
        activation_values["opening_100m_verification"].get("receipt_sha256")
        == source["activation"]["opening_100m_receipt"]["sha256"]
    )
    activation_pass = full_arms_pass and opening_pass
    checks["activation_evidence_rederived"] = activation_pass

    _, calibration_receipt = load_json_artifact(
        source["observer_antecedents"]["calibration_receipt"],
        "calibration receipt",
    )
    _, calibration_verification = load_json_artifact(
        source["observer_antecedents"]["calibration_verification"],
        "calibration verification",
    )
    calibration_pass, calibration_rows, calibration_controls, build = calibration_evidence(
        calibration_receipt, calibration_verification
    )
    calibration_pass &= (
        calibration_verification.get("receipt_sha256")
        == source["observer_antecedents"]["calibration_receipt"]["sha256"]
    )
    checks["observer_calibration_rederived"] = calibration_pass
    checks["calibration_summary_exact"] = source["calibration"] == calibration_rows
    build_record = source["observer_antecedents"]["build_receipt"]
    calibration_build_record = calibration_receipt["antecedents"]["observer_build"]
    checks["observer_build_binding_exact"] = (
        build_record == calibration_build_record
        and source["observer_antecedents"]["build_schema"]
        == calibration_receipt["antecedents"]["observer_build_schema"]
        and build.get("decisions", {}).get("observer_build_pass") is True
    )

    package_by_role = {
        package["arm"]: package for package in build["packages"]
    }
    raw_arms: dict[str, dict[str, Any]] = {}
    parsed_arms: dict[str, dict[str, Any]] = {}
    arm_pass = True
    guard_pass = True
    for role in ("parent", "q1"):
        arm_path = artifact_path(source["arms"][role]["observer_receipt"], f"{role} arm receipt")
        arm = load_contract(arm_path, ARM_SCHEMA, ARM_SCHEMA_ID)
        raw_arms[role] = arm
        parsed = parse_observer(arm)
        parsed_arms[role] = parsed
        expected_summary = {
            "observer_receipt": source["arms"][role]["observer_receipt"],
            "binary": arm["binary"],
            "return_code": arm["return_code"],
            "modeled_stream": arm["modeled_stream"],
            "coded_bits": arm["coded_bits"],
            "probability_sha256": arm["probability_sha256"],
            "coder_checkpoints": arm["coder_checkpoints"],
            "state_checkpoints": arm["state_checkpoints"],
            "payload": arm["payload"],
            "self_extracting_archive": arm["self_extracting_archive"],
        }
        arm_pass &= bool(
            arm["role"] == role
            and arm["runner"] == source["arm_runner"]
            and arm["receipt_schema"] == source["arm_schema"]
            and arm["population"] == source["population"]
            and arm["observer_build_receipt"]
            == source["observer_antecedents"]["build_receipt"]
            and arm["observer_build_schema"]
            == source["observer_antecedents"]["build_schema"]
            and same_file_value(
                arm["binary"],
                package_by_role["parent" if role == "parent" else "candidate"][
                    "packaged_binary"
                ],
            )
            and same_file_value(arm["head"], build["head_blob"])
            and source["arms"][role] == expected_summary
            and arm["coded_bits"] == parsed["coded_bits"]
            and arm["probability_sha256"] == parsed["probability_sha256"]
            and arm["coder_checkpoints"] == parsed["coder_checkpoints"]
            and arm["state_checkpoints"] == parsed["state_checkpoints"]
            and arm["modeled_stream"]["bytes"] == parsed["modeled_bytes"]
            and arm["return_code"] == 0
            and arm["arm_pass"] is True
            and arm["backing_cleanup_pass"] is True
        )
        for name, record in (
            ("binary", arm["binary"]),
            ("head", arm["head"]),
            ("modeled stream", arm["modeled_stream"]),
            ("payload", arm["payload"]),
            ("archive", arm["self_extracting_archive"]),
            ("resource guard", arm["resource_guard"]),
        ):
            artifact_path(record, f"{role} {name}")
        guard_path, guard = load_json_artifact(arm["resource_guard"], f"{role} resource guard")
        del guard_path
        guard_pass &= diagnostic_guard_pass(guard, role, arm)
    checks["arm_receipts_and_observer_outputs_rederived"] = arm_pass
    checks["diagnostic_guards_rederived"] = guard_pass

    parent = raw_arms["parent"]
    q1 = raw_arms["q1"]
    probability_identity = bool(
        parent["coded_bits"] == q1["coded_bits"]
        and parent["probability_sha256"] == q1["probability_sha256"]
    )
    coder_identity = parent["coder_checkpoints"] == q1["coder_checkpoints"]
    state_identity = parent["state_checkpoints"] == q1["state_checkpoints"]
    modeled_identity = bool(
        parent["modeled_stream"]["bytes"] == q1["modeled_stream"]["bytes"]
        and parent["modeled_stream"]["sha256"] == q1["modeled_stream"]["sha256"]
    )
    payload_identity = bool(
        parent["payload"]["bytes"] == q1["payload"]["bytes"] == PAYLOAD_BYTES
        and parent["payload"]["sha256"] == q1["payload"]["sha256"] == PAYLOAD_SHA256
    )
    mutation = build["state_mutation_control"]
    expected_controls = {
        **calibration_controls,
        "unmutated_state_sha256": mutation["start_manifest_sha256"],
        "single_byte_mutated_state_sha256": mutation["mutation_manifest_sha256"],
        "checkpoint_negative_controls_rejected": (
            negative_checkpoint_controls(parent) and negative_checkpoint_controls(q1)
        ),
    }
    controls_exact = source["controls"] == expected_controls
    controls_pass = bool(
        controls_exact
        and expected_controls["observer_off_payload_sha256"]
        == expected_controls["observer_on_payload_sha256"]
        and expected_controls["post_head_probability_sha256"]
        != expected_controls["pre_head_probability_sha256"]
        and expected_controls["unmutated_state_sha256"]
        != expected_controls["single_byte_mutated_state_sha256"]
        and expected_controls["checkpoint_negative_controls_rejected"] is True
    )
    checks["controls_rederived"] = controls_pass

    derived = {
        "activation_pass": activation_pass,
        "calibration_pass": calibration_pass and source["calibration"] == calibration_rows,
        "probability_identity_pass": probability_identity,
        "coder_checkpoint_identity_pass": coder_identity,
        "state_checkpoint_identity_pass": state_identity,
        "modeled_stream_identity_pass": modeled_identity,
        "payload_identity_pass": payload_identity,
        "controls_pass": controls_pass,
        "full_identity_pass": False,
    }
    derived["full_identity_pass"] = all(
        value for name, value in derived.items() if name != "full_identity_pass"
    ) and all(checks.values())
    checks["declared_decisions_exact"] = source["decisions"] == derived
    if not checks["declared_decisions_exact"]:
        errors.append("declared decisions differ from independent rederivation")
    if source["terminal_pass"] is not (derived["full_identity_pass"] and source["errors"] == []):
        errors.append("terminal decision differs from independent rederivation")
    if source["errors"]:
        errors.extend(f"source receipt: {message}" for message in source["errors"])
    errors.extend(f"check failed: {name}" for name, value in checks.items() if not value)

    verification_pass = not errors and all(checks.values()) and derived["full_identity_pass"]
    output = {
        "schema": OUTPUT_SCHEMA_ID,
        "candidate_id": CANDIDATE_ID,
        "source_receipt": artifact(receipt_path),
        "checks": checks,
        "derived": derived,
        "errors": errors,
        "verification_pass": verification_pass,
        "claim_boundary": (
            "Independent full post-head probability-stream and seven-checkpoint "
            "mutation-scoped state identity only; no resource or score authority."
        ),
        "gamma_score_credit_bytes": 0,
    }
    output_schema = json.loads(OUTPUT_SCHEMA.read_text())
    jsonschema.Draft202012Validator.check_schema(output_schema)
    jsonschema.validate(output, output_schema)
    return output, verification_pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt_path = regular_file(args.receipt, "full identity receipt")
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit("output already exists")
    output, passed = verify(receipt_path)
    write_new(args.output, output)
    print(json.dumps(output, sort_keys=True, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
