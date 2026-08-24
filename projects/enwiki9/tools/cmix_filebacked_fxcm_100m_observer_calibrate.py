#!/usr/bin/env python3
"""Calibrate the sealed 100M observer on retained opening/distant 10M scopes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any

import jsonschema

import cmix_filebacked_fxcm_build_capture as capture
import cmix_filebacked_fxcm_scope_identity as scope


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-100m-observer-calibration.v1"
BUILD_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-100m-observer-build.v1"
TRANSFER_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-transfer-10m.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
PLAN_ARTIFACT_ID = "cmix_filebacked_fxcm_100m_identity_resource_q0_v1"
CALIBRATION_SCHEMA_SHA256 = "009de365b89e83bc395d2f55332bc5b4f39de4ff0f0ddcb2727d6f1bba45c18a"
RUN_SPECS = (
    (0, "I-P", "parent", "post_head", True),
    (0, "I-Q", "candidate", "post_head", True),
    (0, "N-P", "negative", "pre_head", True),
    (500_000_000, "I-P", "parent", "post_head", False),
    (500_000_000, "I-Q", "candidate", "post_head", False),
)


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": scope.sha256_file(path),
    }


def verify_artifact(record: Any, label: str) -> Path:
    return scope.verify_artifact_record(record, label)


def packages_from_build(build: dict[str, Any]) -> tuple[dict[str, Path], Path]:
    if (
        build.get("schema") != BUILD_SCHEMA
        or build.get("candidate_id") != CANDIDATE_ID
        or build.get("decisions", {}).get("observer_build_pass") is not True
        or build.get("decisions", {}).get("state_mutation_control_pass") is not True
        or build.get("state_mutation_control", {}).get("pass") is not True
    ):
        raise RuntimeError("observer build receipt did not pass")
    packages: dict[str, Path] = {}
    for record in build.get("packages", []):
        arm = record.get("arm") if isinstance(record, dict) else None
        if arm not in {"parent", "candidate", "negative"} or arm in packages:
            raise RuntimeError("observer package arm set is invalid")
        packages[arm] = verify_artifact(record.get("packaged_binary"), f"{arm} package")
    if set(packages) != {"parent", "candidate", "negative"}:
        raise RuntimeError("observer build did not bind all three packages")
    return packages, verify_artifact(build.get("head_blob"), "observer head blob")


def transfer_scopes(transfer: dict[str, Any]) -> dict[int, dict[str, Any]]:
    if (
        transfer.get("schema") != TRANSFER_SCHEMA
        or transfer.get("candidate_id") != CANDIDATE_ID
        or transfer.get("terminal_pass") is not True
    ):
        raise RuntimeError("retained opening/distant 10M receipt did not pass")
    values: dict[int, dict[str, Any]] = {}
    for item in transfer.get("scopes", []):
        offset = item.get("offset") if isinstance(item, dict) else None
        if (
            offset not in {0, 500_000_000}
            or offset in values
            or item.get("bytes") != 10_000_000
            or item.get("scope_pass") is not True
        ):
            raise RuntimeError("retained transfer scope set is invalid")
        arms = {arm["arm"]: arm for arm in item.get("arms", [])}
        if set(arms) != {"parent", "candidate"}:
            raise RuntimeError("retained transfer arm set is invalid")
        parent_probability = arms["parent"]["trace"][
            "integer_probability_stream_sha256"
        ]
        candidate_probability = arms["candidate"]["trace"][
            "integer_probability_stream_sha256"
        ]
        if parent_probability != candidate_probability:
            raise RuntimeError("retained transfer probability identity drift")
        values[offset] = {
            "offset": offset,
            "bytes": item["bytes"],
            "slice_sha256": item["slice_sha256"],
            "probability_sha256": parent_probability,
            "payloads": {
                name: verify_artifact(arm["payload"], f"retained {offset} {name} payload")
                for name, arm in arms.items()
            },
        }
    if set(values) != {0, 500_000_000}:
        raise RuntimeError("retained transfer scopes are incomplete")
    return values


def observer_outputs(observer_root: Path, transformed_bytes: int) -> dict[str, Any]:
    probability_path = scope.existing_regular(
        observer_root / "probability.json", "observer probability summary"
    )
    coder_path = scope.existing_regular(
        observer_root / "coder-checkpoints.jsonl", "observer coder checkpoints"
    )
    state_path = scope.existing_regular(
        observer_root / "persistent-state.jsonl", "observer persistent state"
    )
    probability = json.loads(probability_path.read_text(encoding="ascii"))
    coder = [
        json.loads(line)
        for line in coder_path.read_text(encoding="ascii").splitlines()
    ]
    state = [
        json.loads(line)
        for line in state_path.read_text(encoding="ascii").splitlines()
    ]
    expected_bits = transformed_bytes * 8
    probability_sha256 = probability.get("post_head_probability_sha256")
    coder_geometry = (
        probability.get("completed_coded_bytes") == transformed_bytes
        and probability.get("coded_bits") == expected_bits
        and isinstance(probability_sha256, str)
        and len(probability_sha256) == 64
        and len(coder) == 2
        and [record.get("kind") for record in coder] == ["start", "terminal"]
        and coder[0].get("completed_coded_bytes") == 0
        and coder[0].get("coded_bits") == 0
        and coder[-1].get("completed_coded_bytes") == transformed_bytes
        and coder[-1].get("coded_bits") == expected_bits
        and coder[-1].get("probability_sha256") == probability_sha256
    )
    ranges = [record for record in state if "ordinal" in record]
    manifests = [record for record in state if "manifest_sha256" in record]
    state_geometry = (
        len(state) == 54
        and len(ranges) == 52
        and len(manifests) == 2
        and {record.get("kind") for record in ranges} == {"start", "terminal"}
        and all(
            {record.get("ordinal") for record in ranges if record.get("kind") == kind}
            == set(range(26))
            for kind in ("start", "terminal")
        )
        and all(
            isinstance(record.get("bytes"), int)
            and record["bytes"] >= 64 * 1024 * 1024
            and isinstance(record.get("alignment"), int)
            and record["alignment"] > 0
            and record["alignment"] & (record["alignment"] - 1) == 0
            for record in ranges
        )
        and [record.get("kind") for record in manifests] == ["start", "terminal"]
        and all(record.get("allocation_count") == 26 for record in manifests)
        and manifests[0].get("checkpoint") == 0
        and manifests[1].get("checkpoint") == transformed_bytes
    )
    if not coder_geometry or not state_geometry:
        raise RuntimeError("observer output geometry mismatch")
    return {
        "probability_sha256": probability_sha256,
        "probability_summary": artifact(probability_path),
        "coder_checkpoints": artifact(coder_path),
        "persistent_state": artifact(state_path),
        "geometry_pass": True,
    }


def run_one(
    *,
    arm: str,
    probability_tap: str,
    decode_required: bool,
    population: dict[str, Any],
    package: Path,
    reference_payload: Path,
    head_blob: Path,
    corpus: Path,
    guard_tool: Path,
    result_root: Path,
    scratch_root: Path,
    cpu: int,
) -> dict[str, Any]:
    offset = population["offset"]
    run_name = f"scope-{offset:09d}-{arm.lower()}"
    run_root = result_root / run_name
    run_root.mkdir(mode=0o700)
    encode_root = scratch_root / f"{run_name}-encode"
    encode_root.mkdir(mode=0o700)
    local_cmix = encode_root / "cmix"
    local_head = encode_root / "head.blob"
    shutil.copyfile(package, local_cmix)
    shutil.copyfile(head_blob, local_head)
    local_cmix.chmod(0o755)
    slice_sha256 = scope.copy_slice(
        corpus, encode_root / "enwik9", offset, population["bytes"]
    )
    if slice_sha256 != population["slice_sha256"]:
        raise RuntimeError(f"{run_name} population identity mismatch")
    observer_root = run_root / "observer"
    observer_root.mkdir(mode=0o700)
    transformed_input = run_root / "transformed-input"
    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "TZ": "UTC",
        "KH_BITLSTM32": str(local_head),
        "GAMMA_FULL_IDENTITY_DIR": str(observer_root),
        "GAMMA_FULL_IDENTITY_TRANSFORMED_INPUT": str(transformed_input),
    }
    encode_backing: Path | None = None
    if arm == "I-Q":
        encode_backing = scratch_root / f"{run_name}-encode-backing"
        encode_backing.mkdir(mode=0o700)
        environment["GAMMA_FXCM_BACKING_DIR"] = str(encode_backing)
    encode_guard_path = run_root / "encode-guard.json"
    encode_return, encode_guard = scope.run_guarded(
        ["./cmix", "-e", "enwik9", "out.cmix"],
        encode_root,
        environment,
        guard_tool,
        encode_guard_path,
        run_root / "encode.stdout",
        run_root / "encode.stderr",
        scratch_root,
        f"{CANDIDATE_ID}-{run_name}-encode",
        cpu,
    )
    encode_pass = encode_return == 0 and scope.guard_pass(encode_guard)
    if not encode_pass:
        raise RuntimeError(f"{run_name} encode or guard failed")
    payload_source = scope.existing_regular(encode_root / "out.cmix", "encoded payload")
    archive_source = scope.existing_regular(encode_root / "archive9", "encoded archive")
    payload_path = run_root / "out.cmix"
    archive_path = run_root / "archive9"
    os.replace(payload_source, payload_path)
    os.replace(archive_source, archive_path)
    transformed_input = scope.existing_regular(
        transformed_input, f"{run_name} transformed input"
    )
    observed = observer_outputs(observer_root, transformed_input.stat().st_size)
    payload_identity = (
        payload_path.stat().st_size == reference_payload.stat().st_size
        and scope.sha256_file(payload_path) == scope.sha256_file(reference_payload)
    )
    encode_cleanup = encode_backing is None or scope.directory_empty(encode_backing)
    if not encode_cleanup:
        raise RuntimeError(f"{run_name} left encode backing files")
    if encode_backing is not None:
        encode_backing.rmdir()
    shutil.rmtree(encode_root)

    decode_return: int | None = None
    decode_guard_record: dict[str, Any] | None = None
    decode_guard_pass: bool | None = None
    decoded_transformed_record: dict[str, Any] | None = None
    raw_inverse_record: dict[str, Any] | None = None
    transformed_inverse_pass: bool | None = None
    raw_inverse_pass: bool | None = None
    decode_cleanup = True
    if decode_required:
        decode_root = scratch_root / f"{run_name}-decode"
        decode_root.mkdir(mode=0o700)
        local_archive = decode_root / "archive9"
        shutil.copyfile(archive_path, local_archive)
        local_archive.chmod(0o755)
        decoded_transformed = run_root / "decoded-transformed"
        decode_environment = {
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
            "TZ": "UTC",
            "GAMMA_FULL_IDENTITY_TRANSFORMED_OUTPUT": str(decoded_transformed),
        }
        decode_backing: Path | None = None
        if arm == "I-Q":
            decode_backing = scratch_root / f"{run_name}-decode-backing"
            decode_backing.mkdir(mode=0o700)
            decode_environment["GAMMA_FXCM_BACKING_DIR"] = str(decode_backing)
        decode_guard_path = run_root / "decode-guard.json"
        decode_return, decode_guard = scope.run_guarded(
            ["./archive9"],
            decode_root,
            decode_environment,
            guard_tool,
            decode_guard_path,
            run_root / "decode.stdout",
            run_root / "decode.stderr",
            scratch_root,
            f"{CANDIDATE_ID}-{run_name}-decode",
            cpu,
        )
        decode_guard_pass = decode_return == 0 and scope.guard_pass(decode_guard)
        if not decode_guard_pass:
            raise RuntimeError(f"{run_name} decode or guard failed")
        decoded_transformed = scope.existing_regular(
            decoded_transformed, f"{run_name} decoded transformed stream"
        )
        restored = scope.existing_regular(
            decode_root / "enwik9_uncompressed", f"{run_name} raw inverse"
        )
        raw_inverse_path = run_root / "enwik9_uncompressed"
        os.replace(restored, raw_inverse_path)
        transformed_inverse_pass = (
            decoded_transformed.stat().st_size == transformed_input.stat().st_size
            and scope.sha256_file(decoded_transformed) == scope.sha256_file(transformed_input)
        )
        raw_inverse_pass = (
            raw_inverse_path.stat().st_size == population["bytes"]
            and scope.sha256_file(raw_inverse_path) == slice_sha256
        )
        decode_cleanup = decode_backing is None or scope.directory_empty(decode_backing)
        if not decode_cleanup:
            raise RuntimeError(f"{run_name} left decode backing files")
        if decode_backing is not None:
            decode_backing.rmdir()
        shutil.rmtree(decode_root)
        decode_guard_record = artifact(decode_guard_path)
        decoded_transformed_record = artifact(decoded_transformed)
        raw_inverse_record = artifact(raw_inverse_path)

    return {
        "arm": arm,
        "offset": offset,
        "bytes": population["bytes"],
        "slice_sha256": slice_sha256,
        "probability_tap": probability_tap,
        "package": artifact(package),
        "reference_payload": artifact(reference_payload),
        "encode_return_code": encode_return,
        "encode_guard": artifact(encode_guard_path),
        "encode_guard_pass": encode_pass,
        "probability_sha256": observed["probability_sha256"],
        "probability_summary": observed["probability_summary"],
        "coder_checkpoints": observed["coder_checkpoints"],
        "persistent_state": observed["persistent_state"],
        "transformed_input": artifact(transformed_input),
        "arithmetic_payload": artifact(payload_path),
        "self_extracting_archive": artifact(archive_path),
        "payload_reference_identity_pass": payload_identity,
        "observer_geometry_pass": observed["geometry_pass"],
        "decode_required": decode_required,
        "decode_return_code": decode_return,
        "decode_guard": decode_guard_record,
        "decode_guard_pass": decode_guard_pass,
        "decoded_transformed": decoded_transformed_record,
        "raw_inverse": raw_inverse_record,
        "transformed_inverse_pass": transformed_inverse_pass,
        "raw_inverse_pass": raw_inverse_pass,
        "backing_cleanup_pass": encode_cleanup and decode_cleanup,
    }


def comparisons(
    runs: list[dict[str, Any]],
    populations: dict[int, dict[str, Any]],
    state_mutation_pass: bool,
) -> dict[str, bool]:
    expected_keys = {(offset, arm) for offset, arm, _, _, _ in RUN_SPECS}
    by_key = {(run["offset"], run["arm"]): run for run in runs}
    complete = len(runs) == len(RUN_SPECS) and set(by_key) == expected_keys

    def available(offset: int, arm: str) -> dict[str, Any] | None:
        return by_key.get((offset, arm))

    opening_parent = available(0, "I-P")
    opening_q1 = available(0, "I-Q")
    opening_negative = available(0, "N-P")
    distant_parent = available(500_000_000, "I-P")
    distant_q1 = available(500_000_000, "I-Q")
    opening_reference = complete and all(
        run["probability_sha256"] == populations[0]["probability_sha256"]
        for run in (opening_parent, opening_q1)
        if run is not None
    )
    distant_reference = complete and all(
        run["probability_sha256"]
        == populations[500_000_000]["probability_sha256"]
        for run in (distant_parent, distant_q1)
        if run is not None
    )
    probability_identity = complete and all(
        available(offset, "I-P")["probability_sha256"]
        == available(offset, "I-Q")["probability_sha256"]
        for offset in (0, 500_000_000)
    )
    coder_identity = complete and all(
        available(offset, "I-P")["coder_checkpoints"]["sha256"]
        == available(offset, "I-Q")["coder_checkpoints"]["sha256"]
        for offset in (0, 500_000_000)
    )
    state_identity = complete and all(
        available(offset, "I-P")["persistent_state"]["sha256"]
        == available(offset, "I-Q")["persistent_state"]["sha256"]
        for offset in (0, 500_000_000)
    )
    negative_probability = (
        complete
        and opening_negative["probability_sha256"]
        != opening_parent["probability_sha256"]
    )
    negative_payload = (
        complete
        and opening_negative["arithmetic_payload"]["sha256"]
        == opening_parent["arithmetic_payload"]["sha256"]
    )
    negative_state = (
        complete
        and opening_negative["persistent_state"]["sha256"]
        == opening_parent["persistent_state"]["sha256"]
    )
    payload_reference = complete and all(
        run["payload_reference_identity_pass"] is True for run in runs
    )
    opening_inverse = complete and all(
        run["raw_inverse_pass"] is True
        for run in runs
        if run["offset"] == 0
    )
    transformed_inverse = complete and all(
        run["transformed_inverse_pass"] is True
        for run in runs
        if run["offset"] == 0
    )
    values = {
        "all_runs_complete": complete,
        "opening_post_head_reference_pass": opening_reference,
        "distant_post_head_reference_pass": distant_reference,
        "parent_q1_probability_identity_pass": probability_identity,
        "parent_q1_coder_identity_pass": coder_identity,
        "parent_q1_state_identity_pass": state_identity,
        "pre_head_probability_negative_control_pass": negative_probability,
        "pre_head_payload_identity_pass": negative_payload,
        "pre_head_state_identity_pass": negative_state,
        "all_payload_reference_identity_pass": payload_reference,
        "opening_all_raw_inverses_pass": opening_inverse,
        "opening_all_transformed_inverses_pass": transformed_inverse,
        "state_mutation_control_pass": state_mutation_pass,
    }
    values["observer_calibration_pass"] = all(values.values())
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--observer-build-receipt", type=Path, required=True)
    parser.add_argument("--observer-build-schema", type=Path, required=True)
    parser.add_argument("--transfer-receipt", type=Path, required=True)
    parser.add_argument("--transfer-verification", type=Path, required=True)
    parser.add_argument("--receipt-schema", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--resource-guard", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    args = parser.parse_args()

    lease_lock = Path(str(capture.LEASE) + ".lock")
    if lease_lock.exists() or lease_lock.is_symlink():
        raise RuntimeError(f"exclusive full-1G lease lock exists: {lease_lock}")
    capture.require_lease_released()
    plan_path, plan = scope.load_json(args.plan, "100M planning contract")
    build_path, build = scope.load_json(
        args.observer_build_receipt, "observer build receipt"
    )
    build_schema_path, build_schema = scope.load_json(
        args.observer_build_schema, "observer build schema"
    )
    transfer_path, transfer = scope.load_json(
        args.transfer_receipt, "opening/distant 10M receipt"
    )
    transfer_verification_path, transfer_verification = scope.load_json(
        args.transfer_verification, "opening/distant 10M verification"
    )
    receipt_schema_path, receipt_schema = scope.load_json(
        args.receipt_schema, "observer calibration receipt schema"
    )
    corpus = scope.existing_regular(args.corpus, "canonical corpus")
    guard_tool = scope.existing_regular(args.resource_guard, "resource guard")
    if corpus.stat().st_size != scope.CANONICAL_BYTES:
        raise RuntimeError("canonical corpus byte count mismatch")
    if (
        plan.get("artifact_id") != PLAN_ARTIFACT_ID
        or plan.get("candidate_id") != CANDIDATE_ID
        or plan.get("execution_authorized") is not False
    ):
        raise RuntimeError("100M planning contract identity mismatch")
    calibration_contract = plan.get("observer_calibration", {})
    runner_path = Path(__file__).resolve()
    if (
        calibration_contract.get("runner")
        != str(runner_path.relative_to(capture.PROJECT))
        or calibration_contract.get("runner_sha256") != scope.sha256_file(runner_path)
        or calibration_contract.get("receipt_schema")
        != str(receipt_schema_path.relative_to(capture.PROJECT))
        or calibration_contract.get("receipt_schema_sha256")
        != CALIBRATION_SCHEMA_SHA256
    ):
        raise RuntimeError("planning contract calibration binding mismatch")
    if scope.sha256_file(receipt_schema_path) != CALIBRATION_SCHEMA_SHA256:
        raise RuntimeError("calibration receipt schema digest mismatch")
    build_contract = plan.get("observer_build", {})
    if (
        build_contract.get("receipt_schema")
        != str(build_schema_path.relative_to(capture.PROJECT))
        or build_contract.get("receipt_schema_sha256")
        != scope.sha256_file(build_schema_path)
    ):
        raise RuntimeError("planning contract observer build schema drift")
    jsonschema.Draft202012Validator.check_schema(build_schema)
    jsonschema.validate(build, build_schema)
    jsonschema.Draft202012Validator.check_schema(receipt_schema)
    build_plan = verify_artifact(build.get("planning_contract"), "build planning contract")
    if build_plan != plan_path or scope.sha256_file(build_plan) != scope.sha256_file(plan_path):
        raise RuntimeError("observer build used a different planning contract")
    if (
        transfer_verification.get("verification_pass") is not True
        or transfer_verification.get("candidate_id") != CANDIDATE_ID
        or transfer_verification.get("source_receipt", {}).get("sha256")
        != scope.sha256_file(transfer_path)
    ):
        raise RuntimeError("opening/distant transfer verification did not pass")
    packages, head_blob = packages_from_build(build)
    populations = transfer_scopes(transfer)
    result_root, _ = scope.absent_root(args.result_root, "calibration result root")
    scratch_root, _ = scope.absent_root(args.scratch_root, "calibration scratch root")
    if (
        result_root == scratch_root
        or result_root in scratch_root.parents
        or scratch_root in result_root.parents
    ):
        raise RuntimeError("calibration result and scratch roots must be disjoint")
    result_root.mkdir(mode=0o700)
    scratch_root.mkdir(mode=0o700)
    runs: list[dict[str, Any]] = []
    errors: list[str] = []
    cpu = min(os.sched_getaffinity(0))
    try:
        for offset, arm, package_role, tap, decode_required in RUN_SPECS:
            reference_role = "candidate" if arm == "I-Q" else "parent"
            runs.append(
                run_one(
                    arm=arm,
                    probability_tap=tap,
                    decode_required=decode_required,
                    population=populations[offset],
                    package=packages[package_role],
                    reference_payload=populations[offset]["payloads"][reference_role],
                    head_blob=head_blob,
                    corpus=corpus,
                    guard_tool=guard_tool,
                    result_root=result_root,
                    scratch_root=scratch_root,
                    cpu=cpu,
                )
            )
        if next(scratch_root.iterdir(), None) is not None:
            raise RuntimeError("calibration scratch root is not empty")
        scratch_root.rmdir()
    except Exception as error:
        errors.append(f"{type(error).__name__}: {error}")

    derived = comparisons(
        runs,
        populations,
        build["state_mutation_control"]["pass"] is True,
    )
    terminal_pass = not errors and derived["observer_calibration_pass"]
    receipt = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "antecedents": {
            "planning_contract": artifact(plan_path),
            "observer_build": artifact(build_path),
            "observer_build_schema": artifact(build_schema_path),
            "opening_distant_10m_receipt": artifact(transfer_path),
            "opening_distant_10m_verification": artifact(transfer_verification_path),
        },
        "fixed_scopes": [
            {
                "offset": populations[offset]["offset"],
                "bytes": populations[offset]["bytes"],
                "slice_sha256": populations[offset]["slice_sha256"],
            }
            for offset in (0, 500_000_000)
        ],
        "runs": runs,
        "comparisons": derived,
        "errors": errors,
        "terminal_pass": terminal_pass,
        "claim_authority": (
            "observer_calibration_on_retained_opening_and_distant_10m_only"
        ),
        "execution_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.validate(receipt, receipt_schema)
    scope.write_new(result_root / "observer-calibration-receipt.json", receipt)
    return 0 if terminal_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
