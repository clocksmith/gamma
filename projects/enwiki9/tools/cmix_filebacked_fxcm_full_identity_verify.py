#!/usr/bin/env python3
"""Independently rederive q1 byte-zero probability and state identity."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any

import jsonschema


PROJECT = Path(__file__).resolve().parents[1]
CONTRACTS = PROJECT / "contracts/research/v1"
SOURCE_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-full-identity.schema.json"
ARM_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-full-identity-arm.schema.json"
OUTPUT_SCHEMA = CONTRACTS / "cmix-filebacked-fxcm-full-identity-verification.schema.json"
SOURCE_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-full-identity.v1"
ARM_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-full-identity-arm.v1"
OUTPUT_SCHEMA_ID = "gamma.enwiki9.cmix-filebacked-fxcm-full-identity-verification.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
CHECKPOINTS = [0, 100_000_000, 500_000_000, 1_000_000_000]
CALIBRATION = {
    "opening_10m": (
        "d651255043d85fa2f9bb6076a145710edd1366cf3e634033d2b2dadcff54e97a",
        46_128_408,
    ),
    "distant_10m": (
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
    absolute = path if path.is_absolute() else Path.cwd() / path
    absolute = absolute.absolute()
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


def artifact_matches(record: Any, label: str) -> bool:
    if not isinstance(record, dict):
        return False
    try:
        path = regular_file(Path(record["path"]), label)
    except (KeyError, OSError, ValueError):
        return False
    return path.stat().st_size == record.get("bytes") and sha256_file(path) == record.get("sha256")


def load_contract(path: Path, schema_path: Path, schema_id: str) -> dict[str, Any]:
    value = json.loads(regular_file(path, schema_id).read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8"))).validate(value)
    if value.get("schema") != schema_id:
        raise ValueError(f"{path}: schema identity mismatch")
    return value


def write_new(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
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


def ordered_checkpoints(values: Any) -> bool:
    return isinstance(values, list) and [value.get("coded_bytes") for value in values if isinstance(value, dict)] == CHECKPOINTS


def verify(receipt_path: Path) -> tuple[dict[str, Any], bool]:
    source = load_contract(receipt_path, SOURCE_SCHEMA, SOURCE_SCHEMA_ID)
    checks: dict[str, bool] = {}
    checks["population_artifact_exact"] = artifact_matches(source["population"], "population")

    calibration = {
        value["population"]: value
        for value in source["calibration"]
        if isinstance(value, dict) and value.get("population") in CALIBRATION
    }
    checks["calibration_population_exact"] = set(calibration) == set(CALIBRATION)
    checks["calibration_values_exact"] = checks["calibration_population_exact"] and all(
        row["expected_probability_sha256"] == expected_digest
        and row["observed_probability_sha256"] == expected_digest
        and row["expected_coded_bits"] == expected_bits
        and row["observed_coded_bits"] == expected_bits
        for name, (expected_digest, expected_bits) in CALIBRATION.items()
        for row in [calibration[name]]
    )

    raw_arms: dict[str, dict[str, Any]] = {}
    arm_receipt_match = True
    arm_summary_match = True
    arm_output_match = True
    for role in ("parent", "q1"):
        summary = source["arms"][role]
        arm_path = Path(summary["observer_receipt"]["path"])
        arm_receipt_match = arm_receipt_match and artifact_matches(summary["observer_receipt"], f"{role} observer receipt")
        arm = load_contract(arm_path, ARM_SCHEMA, ARM_SCHEMA_ID)
        raw_arms[role] = arm
        arm_summary_match = arm_summary_match and arm["role"] == role and all(
            arm[key] == summary[key]
            for key in (
                "binary", "return_code", "coded_bits", "probability_sha256",
                "coder_checkpoints", "state_checkpoints", "payload",
            )
        )
        arm_output_match = arm_output_match and artifact_matches(arm["binary"], f"{role} binary")
        arm_output_match = arm_output_match and artifact_matches(arm["payload"], f"{role} payload")
        arm_output_match = arm_output_match and all(
            artifact_matches(record, f"{role} {name}")
            for name, record in arm["observer_outputs"].items()
        )
    checks["observer_arm_receipts_match"] = arm_receipt_match
    checks["observer_arm_summaries_rederived"] = arm_summary_match
    checks["observer_output_artifacts_match"] = arm_output_match

    parent = raw_arms["parent"]
    q1 = raw_arms["q1"]
    checks["return_codes_zero"] = parent["return_code"] == q1["return_code"] == 0
    checks["checkpoint_population_exact"] = all(
        ordered_checkpoints(arm[kind])
        for arm in (parent, q1)
        for kind in ("coder_checkpoints", "state_checkpoints")
    )
    probability_identity = (
        parent["coded_bits"] == q1["coded_bits"]
        and parent["probability_sha256"] == q1["probability_sha256"]
    )
    coder_identity = parent["coder_checkpoints"] == q1["coder_checkpoints"]
    state_identity = parent["state_checkpoints"] == q1["state_checkpoints"]
    payload_identity = (
        parent["payload"]["bytes"] == q1["payload"]["bytes"] == 107_730_531
        and parent["payload"]["sha256"] == q1["payload"]["sha256"]
        == "889aa8074e0a84eb89997986899f1ef9f7cc0e52e87d1d36f86899fc679f5490"
    )
    checks["probability_identity"] = probability_identity
    checks["coder_checkpoint_identity"] = coder_identity
    checks["state_checkpoint_identity"] = state_identity
    checks["payload_identity"] = payload_identity

    controls = source["controls"]
    controls_pass = (
        controls["observer_off_payload_sha256"] == controls["observer_on_payload_sha256"]
        and controls["post_head_probability_sha256"] != controls["pre_head_probability_sha256"]
        and controls["unmutated_state_sha256"] != controls["single_byte_mutated_state_sha256"]
        and controls["checkpoint_negative_controls_rejected"] is True
    )
    checks["negative_controls_exact"] = controls_pass
    evidence_match = all(artifact_matches(record, "retained evidence") for record in source["evidence"])
    evidence_hashes = {record["sha256"] for record in source["evidence"]}
    required_hashes = {
        source["arms"][role][name]["sha256"]
        for role in ("parent", "q1")
        for name in ("observer_receipt", "binary", "payload")
    }
    checks["evidence_closure"] = evidence_match and required_hashes <= evidence_hashes

    calibration_pass = checks["calibration_population_exact"] and checks["calibration_values_exact"]
    full_identity = all(checks.values())
    derived = {
        "calibration_pass": calibration_pass,
        "probability_identity_pass": probability_identity,
        "coder_checkpoint_identity_pass": coder_identity,
        "state_checkpoint_identity_pass": state_identity,
        "payload_identity_pass": payload_identity,
        "controls_pass": controls_pass,
        "full_identity_pass": full_identity,
    }
    errors = [f"check failed: {name}" for name, passed in checks.items() if not passed]
    output = {
        "schema": OUTPUT_SCHEMA_ID,
        "candidate_id": CANDIDATE_ID,
        "source_receipt": artifact(receipt_path),
        "checks": checks,
        "derived": derived,
        "errors": errors,
        "verification_pass": not errors,
        "claim_boundary": (
            "Independent byte-zero post-head probability, coder-checkpoint, and "
            "mutation-scoped persistent-state checkpoint identity only. Sparse "
            "checkpoints are not a claim of continuously observed state equality."
        ),
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.Draft202012Validator(json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))).validate(output)
    return output, not errors


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
