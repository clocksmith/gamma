#!/usr/bin/env python3
"""Run one sealed instrumented opening-100M parent-preservation arm."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import sys
from typing import Any

import jsonschema

import cmix_filebacked_fxcm_100m_identity_resource_verify as proof
import cmix_filebacked_fxcm_scope_identity as scope


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-100m-identity-arm.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
PREFIX_BYTES = 100_000_000
PREFIX_SHA256 = "2b49720ec4d78c3c9fabaee6e4179a5e997302b3a70029f30f2d582218c024a8"
FIXED_CHECKPOINTS = (16_777_216, 33_554_432, 50_331_648)
EXPECTED_RANGES = 26
MINIMUM_RANGE_BYTES = 64 * 1024 * 1024


def artifact(path: Path) -> dict[str, Any]:
    return scope.artifact(path)


def command_sha256(argv: list[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(value) for value in argv)).hexdigest()


def load_json_lines(path: Path, label: str) -> list[dict[str, Any]]:
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


def valid_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        bytes.fromhex(value)
    except ValueError:
        return False
    return value == value.lower()


def observer_outputs(observer_root: Path, transformed_bytes: int) -> dict[str, Any]:
    if transformed_bytes <= FIXED_CHECKPOINTS[-1]:
        raise RuntimeError("transformed stream does not cross every frozen checkpoint")
    probability_path = scope.existing_regular(
        observer_root / "probability.json", "100M probability summary"
    )
    coder_path = scope.existing_regular(
        observer_root / "coder-checkpoints.jsonl", "100M coder checkpoints"
    )
    state_path = scope.existing_regular(
        observer_root / "persistent-state.jsonl", "100M persistent-state checkpoints"
    )
    probability = json.loads(probability_path.read_text(encoding="ascii"))
    if not isinstance(probability, dict):
        raise RuntimeError("100M probability summary is not an object")
    probability_sha256 = probability.get("post_head_probability_sha256")
    expected_checkpoints = (0, *FIXED_CHECKPOINTS, transformed_bytes)
    expected_kinds = ("start", "fixed", "fixed", "fixed", "terminal")
    expected_bits = transformed_bytes * 8
    if (
        set(probability) != {
            "coded_bits",
            "completed_coded_bytes",
            "post_head_probability_sha256",
        }
        or probability.get("completed_coded_bytes") != transformed_bytes
        or probability.get("coded_bits") != expected_bits
        or not valid_sha256(probability_sha256)
    ):
        raise RuntimeError("100M probability summary geometry mismatch")

    coder = load_json_lines(coder_path, "100M coder checkpoints")
    if len(coder) != len(expected_checkpoints):
        raise RuntimeError("100M coder checkpoint count mismatch")
    for index, (record, checkpoint, kind) in enumerate(
        zip(coder, expected_checkpoints, expected_kinds)
    ):
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
                isinstance(record.get(name), int) and record[name] >= 0
                for name in ("low", "high", "payload_bytes")
            )
            or record["low"] > 0xFFFFFFFF
            or record["high"] > 0xFFFFFFFF
        ):
            raise RuntimeError(f"100M coder checkpoint {index} geometry mismatch")
    if coder[-1]["probability_sha256"] != probability_sha256:
        raise RuntimeError("terminal coder probability digest mismatch")

    state = load_json_lines(state_path, "100M persistent state")
    records_per_checkpoint = EXPECTED_RANGES + 1
    if len(state) != len(expected_checkpoints) * records_per_checkpoint:
        raise RuntimeError("100M persistent-state record count mismatch")
    frozen_geometry: tuple[tuple[int, int], ...] | None = None
    for checkpoint_index, (checkpoint, kind) in enumerate(
        zip(expected_checkpoints, expected_kinds)
    ):
        begin = checkpoint_index * records_per_checkpoint
        chunk = state[begin : begin + records_per_checkpoint]
        ranges = chunk[:-1]
        manifest = chunk[-1]
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
                or byte_count < MINIMUM_RANGE_BYTES
                or not isinstance(alignment, int)
                or alignment <= 0
                or alignment & (alignment - 1)
                or not valid_sha256(range_sha256)
            ):
                raise RuntimeError(
                    f"100M state checkpoint {checkpoint_index} range {ordinal} mismatch"
                )
            geometry.append((byte_count, alignment))
            aggregate.update(struct.pack("<Q", ordinal))
            aggregate.update(struct.pack("<Q", byte_count))
            aggregate.update(struct.pack("<Q", alignment))
            aggregate.update(bytes.fromhex(range_sha256))
        geometry_tuple = tuple(geometry)
        if frozen_geometry is None:
            frozen_geometry = geometry_tuple
        elif geometry_tuple != frozen_geometry:
            raise RuntimeError("semantic range geometry changed between checkpoints")
        if (
            set(manifest)
            != {"allocation_count", "checkpoint", "kind", "manifest_sha256"}
            or manifest.get("allocation_count") != EXPECTED_RANGES
            or manifest.get("checkpoint") != checkpoint
            or manifest.get("kind") != kind
            or manifest.get("manifest_sha256") != aggregate.hexdigest()
        ):
            raise RuntimeError(
                f"100M state checkpoint {checkpoint_index} manifest mismatch"
            )
    return {
        "probability_sha256": probability_sha256,
        "probability_summary": artifact(probability_path),
        "coder_checkpoints": artifact(coder_path),
        "persistent_state": artifact(state_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=("I-P", "I-Q"), required=True)
    parser.add_argument("--population", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--head-blob", type=Path, required=True)
    parser.add_argument("--resource-guard", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--receipt-schema", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--cpu", type=int, required=True)
    args = parser.parse_args()

    proof.require_released_lease(args.exclusive_lease)
    population = scope.existing_regular(args.population, "opening-100M population")
    package = scope.existing_regular(args.package, f"{args.arm} observer package")
    head_blob = scope.existing_regular(args.head_blob, "observer head blob")
    guard_tool = scope.existing_regular(args.resource_guard, "resource guard v2")
    receipt_schema_path, receipt_schema = scope.load_json(
        args.receipt_schema, "100M identity-arm schema"
    )
    jsonschema.Draft202012Validator.check_schema(receipt_schema)
    if (
        population.stat().st_size != PREFIX_BYTES
        or scope.sha256_file(population) != PREFIX_SHA256
    ):
        raise RuntimeError("opening-100M population identity mismatch")
    if args.cpu not in os.sched_getaffinity(0):
        raise RuntimeError("selected CPU is outside identity-arm affinity")
    result_root, _ = scope.absent_root(args.result_root, "identity-arm result root")
    scratch_root, _ = scope.absent_root(args.scratch_root, "identity-arm scratch root")
    if (
        result_root == scratch_root
        or result_root in scratch_root.parents
        or scratch_root in result_root.parents
    ):
        raise RuntimeError("identity-arm result and scratch roots must be disjoint")
    result_root.mkdir(mode=0o700)
    scratch_root.mkdir(mode=0o700)

    encode_root = scratch_root / "encode"
    encode_root.mkdir(mode=0o700)
    local_cmix = encode_root / "cmix"
    local_head = encode_root / "head.blob"
    local_input = encode_root / "enwik9"
    shutil.copyfile(package, local_cmix)
    shutil.copyfile(head_blob, local_head)
    shutil.copyfile(population, local_input)
    local_cmix.chmod(0o700)
    observer_root = result_root / "observer"
    observer_root.mkdir(mode=0o700)
    transformed_input = result_root / "transformed-input"
    encode_environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "TZ": "UTC",
        "KH_BITLSTM32": str(local_head),
        "GAMMA_FULL_IDENTITY_DIR": str(observer_root),
        "GAMMA_FULL_IDENTITY_TRANSFORMED_INPUT": str(transformed_input),
    }
    encode_backing: Path | None = None
    if args.arm == "I-Q":
        encode_backing = scratch_root / "encode-backing"
        encode_backing.mkdir(mode=0o700)
        encode_environment["GAMMA_FXCM_BACKING_DIR"] = str(encode_backing)
    encode_guard_path = result_root / "encode-guard.json"
    encode_return, encode_guard = scope.run_guarded(
        ["./cmix", "-e", "enwik9", "out.cmix"],
        encode_root,
        encode_environment,
        guard_tool,
        encode_guard_path,
        result_root / "encode.stdout",
        result_root / "encode.stderr",
        scratch_root,
        f"{CANDIDATE_ID}-100m-{args.arm.lower()}-encode",
        args.cpu,
    )
    if encode_return != 0 or not scope.guard_pass(encode_guard):
        raise RuntimeError(f"{args.arm} encode or guard failed")
    payload_source = scope.existing_regular(encode_root / "out.cmix", "100M payload")
    archive_source = scope.existing_regular(encode_root / "archive9", "100M archive")
    payload_path = result_root / "out.cmix"
    archive_path = result_root / "archive9"
    os.replace(payload_source, payload_path)
    os.replace(archive_source, archive_path)
    transformed_input = scope.existing_regular(
        transformed_input, "100M transformed input"
    )
    observed = observer_outputs(observer_root, transformed_input.stat().st_size)
    encode_cleanup = encode_backing is None or scope.directory_empty(encode_backing)
    if not encode_cleanup:
        raise RuntimeError(f"{args.arm} encode backing files survived")
    if encode_backing is not None:
        encode_backing.rmdir()
    shutil.rmtree(encode_root)

    decode_root = scratch_root / "decode"
    decode_root.mkdir(mode=0o700)
    local_archive = decode_root / "archive9"
    shutil.copyfile(archive_path, local_archive)
    local_archive.chmod(0o700)
    decoded_transformed = result_root / "decoded-transformed"
    decode_environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "TZ": "UTC",
        "GAMMA_FULL_IDENTITY_TRANSFORMED_OUTPUT": str(decoded_transformed),
    }
    decode_backing: Path | None = None
    if args.arm == "I-Q":
        decode_backing = scratch_root / "decode-backing"
        decode_backing.mkdir(mode=0o700)
        decode_environment["GAMMA_FXCM_BACKING_DIR"] = str(decode_backing)
    decode_guard_path = result_root / "decode-guard.json"
    decode_return, decode_guard = scope.run_guarded(
        ["./archive9"],
        decode_root,
        decode_environment,
        guard_tool,
        decode_guard_path,
        result_root / "decode.stdout",
        result_root / "decode.stderr",
        scratch_root,
        f"{CANDIDATE_ID}-100m-{args.arm.lower()}-decode",
        args.cpu,
    )
    if decode_return != 0 or not scope.guard_pass(decode_guard):
        raise RuntimeError(f"{args.arm} decode or guard failed")
    decoded_transformed = scope.existing_regular(
        decoded_transformed, "100M decoded transformed stream"
    )
    raw_source = scope.existing_regular(
        decode_root / "enwik9_uncompressed", "100M raw inverse"
    )
    raw_inverse = result_root / "enwik9_uncompressed"
    os.replace(raw_source, raw_inverse)
    transformed_inverse_pass = (
        decoded_transformed.stat().st_size == transformed_input.stat().st_size
        and scope.sha256_file(decoded_transformed)
        == scope.sha256_file(transformed_input)
    )
    raw_inverse_pass = (
        raw_inverse.stat().st_size == PREFIX_BYTES
        and scope.sha256_file(raw_inverse) == PREFIX_SHA256
    )
    decode_cleanup = decode_backing is None or scope.directory_empty(decode_backing)
    if not decode_cleanup:
        raise RuntimeError(f"{args.arm} decode backing files survived")
    if decode_backing is not None:
        decode_backing.rmdir()
    shutil.rmtree(decode_root)
    if next(scratch_root.iterdir(), None) is not None:
        raise RuntimeError(f"{args.arm} scratch residue survived")
    scratch_root.rmdir()

    arm_pass = bool(
        transformed_inverse_pass
        and raw_inverse_pass
        and encode_cleanup
        and decode_cleanup
    )
    receipt = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "arm": args.arm,
        "runner": artifact(Path(__file__).resolve(strict=True)),
        "receipt_schema": artifact(receipt_schema_path),
        "command_sha256": command_sha256([sys.executable, *sys.argv]),
        "population": artifact(population),
        "package": artifact(package),
        "encode_guard": artifact(encode_guard_path),
        "decode_guard": artifact(decode_guard_path),
        "return_codes": {"encode": encode_return, "decode": decode_return, "raw_inverse": 0},
        "probability_sha256": observed["probability_sha256"],
        "probability_summary": observed["probability_summary"],
        "coder_checkpoints": observed["coder_checkpoints"],
        "persistent_state": observed["persistent_state"],
        "arithmetic_payload": artifact(payload_path),
        "self_extracting_archive": artifact(archive_path),
        "transformed_input": artifact(transformed_input),
        "decoded_transformed": artifact(decoded_transformed),
        "raw_inverse": artifact(raw_inverse),
        "observer_geometry_pass": True,
        "transformed_inverse_pass": transformed_inverse_pass,
        "raw_inverse_pass": raw_inverse_pass,
        "backing_cleanup_pass": encode_cleanup and decode_cleanup,
        "arm_pass": arm_pass,
        "errors": [] if arm_pass else ["identity-arm terminal predicate failed"],
        "claim_authority": "opening_100m_instrumented_identity_arm_only",
        "execution_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.validate(receipt, receipt_schema)
    scope.write_new(result_root / "identity-arm-receipt.json", receipt)
    return 0 if arm_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
