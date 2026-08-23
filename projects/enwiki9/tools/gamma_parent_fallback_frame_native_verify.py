#!/usr/bin/env python3
"""Offline verifier for native GAFS frame qualification evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, BinaryIO


SCHEMA = "gamma-parent-fallback-frame-native-verification.v1"
PROGRAM_ID = "gamma_parent_fallback_archive_select_q0_v1"
MAGIC = b"GAFS"
VERSION = 1
HEADER_BYTES = 14
CHUNK_BYTES = 1024 * 1024
FIXTURES = {
    "parent_smaller": "P",
    "candidate_smaller": "C",
    "equal_size_parent_tie": "P",
}


class VerificationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"JSON root is not an object: {path}")
    return value


def file_identity(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return size, digest.hexdigest()


def streams_equal(left: BinaryIO, right: BinaryIO, bytes_to_compare: int | None = None) -> bool:
    remaining = bytes_to_compare
    while remaining is None or remaining > 0:
        request = CHUNK_BYTES if remaining is None else min(CHUNK_BYTES, remaining)
        left_chunk = left.read(request)
        right_chunk = right.read(request)
        if left_chunk != right_chunk:
            return False
        if not left_chunk:
            return remaining in (None, 0)
        if remaining is not None:
            remaining -= len(left_chunk)
    return True


def files_equal(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as left_handle, right.open("rb") as right_handle:
        return streams_equal(left_handle, right_handle)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def object_field(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} is not an object")
        return {}
    return value


def verify_fixture(name: str, directory: Path, receipt: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    parent_path = directory / "parent.bin"
    candidate_path = directory / "candidate.bin"
    archive_path = directory / "archive.gafs"
    repeat_path = directory / "archive-repeat.gafs"
    extracted_path = directory / "extracted.bin"
    create_stdout_path = directory / "create.stdout"
    extract_stdout_path = directory / "extract.stdout"
    parent_bytes, parent_sha256 = file_identity(parent_path)
    candidate_bytes, candidate_sha256 = file_identity(candidate_path)
    archive_bytes, archive_sha256 = file_identity(archive_path)
    repeat_bytes, repeat_sha256 = file_identity(repeat_path)
    extracted_bytes, extracted_sha256 = file_identity(extracted_path)
    _, create_stdout_sha256 = file_identity(create_stdout_path)
    _, extract_stdout_sha256 = file_identity(extract_stdout_path)

    expected_mode = "P" if parent_bytes <= candidate_bytes else "C"
    declared_role = FIXTURES[name]
    require(expected_mode == declared_role, f"{name} does not realize its declared size relation", errors)
    if name == "parent_smaller":
        require(parent_bytes < candidate_bytes, "parent_smaller fixture is not strict", errors)
    elif name == "candidate_smaller":
        require(candidate_bytes < parent_bytes, "candidate_smaller fixture is not strict", errors)
    else:
        require(parent_bytes == candidate_bytes, "equal_size_parent_tie fixture is not equal", errors)
    selected_path = parent_path if expected_mode == "P" else candidate_path
    selected_bytes = parent_bytes if expected_mode == "P" else candidate_bytes
    selected_sha256 = parent_sha256 if expected_mode == "P" else candidate_sha256

    require(archive_bytes >= HEADER_BYTES, f"{name} archive is shorter than header", errors)
    parsed_mode: str | None = None
    payload_bytes = -1
    if archive_bytes >= HEADER_BYTES:
        with archive_path.open("rb") as archive:
            header = archive.read(HEADER_BYTES)
            require(header[:4] == MAGIC, f"{name} magic mismatch", errors)
            require(header[4] == VERSION, f"{name} version mismatch", errors)
            if header[5] == 0:
                parsed_mode = "P"
            elif header[5] == 1:
                parsed_mode = "C"
            else:
                errors.append(f"{name} mode byte is invalid")
            payload_bytes = int.from_bytes(header[6:14], "little")
            require(payload_bytes == archive_bytes - HEADER_BYTES, f"{name} payload length mismatch", errors)
            with selected_path.open("rb") as selected:
                require(streams_equal(archive, selected, max(payload_bytes, 0)), f"{name} framed payload mismatch", errors)
                require(archive.read(1) == b"", f"{name} archive has trailing bytes", errors)
                require(selected.read(1) == b"", f"{name} selected payload has uncopied bytes", errors)
    require(parsed_mode == expected_mode, f"{name} selected mode mismatch", errors)
    require(archive_bytes == HEADER_BYTES + selected_bytes, f"{name} archive size arithmetic mismatch", errors)
    require(repeat_bytes == archive_bytes and repeat_sha256 == archive_sha256, f"{name} repeat archive digest mismatch", errors)
    require(files_equal(archive_path, repeat_path), f"{name} repeat archive byte mismatch", errors)
    require(extracted_bytes == selected_bytes and extracted_sha256 == selected_sha256, f"{name} extracted payload digest mismatch", errors)
    require(files_equal(extracted_path, selected_path), f"{name} extracted payload byte mismatch", errors)
    expected_stdout = (expected_mode + "\n").encode("ascii")
    require(create_stdout_path.read_bytes() == expected_stdout, f"{name} create stdout mismatch", errors)
    require(extract_stdout_path.read_bytes() == expected_stdout, f"{name} extract stdout mismatch", errors)

    expected_receipt = {
        "parent_bytes": parent_bytes,
        "candidate_bytes": candidate_bytes,
        "expected_mode": expected_mode,
        "create_return_code": 0,
        "create_stdout_sha256": create_stdout_sha256,
        "archive_bytes": archive_bytes,
        "archive_sha256": archive_sha256,
        "extract_return_code": 0,
        "extract_stdout_sha256": extract_stdout_sha256,
        "extracted_bytes": extracted_bytes,
        "extracted_sha256": extracted_sha256,
        "selected_payload_sha256": selected_sha256,
        "payload_identity": True,
    }
    for field, expected in expected_receipt.items():
        require(receipt.get(field) == expected, f"{name} receipt {field} mismatch", errors)
    return {
        "mode": expected_mode,
        "archive_bytes": archive_bytes,
        "archive_sha256": archive_sha256,
        "selected_payload_sha256": selected_sha256,
    }


def verify(args: argparse.Namespace) -> tuple[dict[str, Any], bool]:
    errors: list[str] = []
    receipt = load_json(args.receipt)
    require(receipt.get("schema_version") == "gamma-parent-fallback-frame-native-receipt.v1", "receipt schema mismatch", errors)
    require(receipt.get("program_id") == PROGRAM_ID, "receipt program_id mismatch", errors)
    identity = object_field(receipt.get("identity"), "receipt.identity", errors)
    package = object_field(receipt.get("package"), "receipt.package", errors)
    controls = object_field(receipt.get("controls"), "receipt.controls", errors)
    decision = object_field(receipt.get("decision"), "receipt.decision", errors)
    fixtures = object_field(receipt.get("fixtures"), "receipt.fixtures", errors)

    identity_inputs = {
        "interface_contract_sha256": args.interface_contract,
        "program_lock_sha256": args.program_lock,
        "source_sha256": args.source,
        "compiler_sha256": args.compiler,
        "build_command_sha256": args.build_command,
        "build_environment_sha256": args.build_environment,
        "build_log_sha256": args.build_log,
        "binary_sha256": args.binary,
    }
    computed_hashes: dict[str, str] = {}
    for field, path in identity_inputs.items():
        _, digest = file_identity(path)
        computed_hashes[field] = digest
        require(identity.get(field) == digest, f"identity {field} mismatch", errors)
    binary_bytes = args.binary.stat().st_size
    require(package.get("binary_bytes") == binary_bytes, "package binary_bytes mismatch", errors)
    _, dependency_closure_sha256 = file_identity(args.dependency_closure)
    require(package.get("dependency_closure_sha256") == dependency_closure_sha256, "dependency closure SHA-256 mismatch", errors)
    require(package.get("included_in_union_package") is True, "binary is not included in union package", errors)
    added_package_bytes = package.get("added_package_bytes")
    require(
        isinstance(added_package_bytes, int)
        and not isinstance(added_package_bytes, bool)
        and binary_bytes <= added_package_bytes <= 65536,
        "added package bytes are invalid",
        errors,
    )

    fixture_directories = {
        "parent_smaller": args.parent_smaller,
        "candidate_smaller": args.candidate_smaller,
        "equal_size_parent_tie": args.equal_size_parent_tie,
    }
    computed_fixtures: dict[str, Any] = {}
    for name, directory in fixture_directories.items():
        fixture_receipt = object_field(fixtures.get(name), f"receipt.fixtures.{name}", errors)
        computed_fixtures[name] = verify_fixture(name, directory, fixture_receipt, errors)

    required_controls = (
        "bad_magic_rejected",
        "bad_version_rejected",
        "bad_mode_rejected",
        "short_header_rejected",
        "short_payload_rejected",
        "trailing_bytes_rejected",
        "existing_output_preserved",
        "symlink_input_rejected",
        "nonregular_input_rejected",
        "repeat_archive_identity",
    )
    for control in required_controls:
        require(controls.get(control) is True, f"control {control} did not pass", errors)
    require(decision.get("native_frame_authority") is True, "native frame authority is false", errors)
    require(decision.get("compression_authority") is False, "receipt overclaims compression authority", errors)
    require(decision.get("status") == "pass", "native frame decision is not pass", errors)

    verified = not errors
    output = {
        "schema_version": SCHEMA,
        "program_id": PROGRAM_ID,
        "verified": verified,
        "computed": {
            "identity": computed_hashes,
            "fixtures": computed_fixtures,
            "binary_bytes": binary_bytes,
            "dependency_closure_sha256": dependency_closure_sha256,
        },
        "errors": errors,
    }
    return output, verified


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--interface-contract", required=True, type=Path)
    parser.add_argument("--program-lock", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--compiler", required=True, type=Path)
    parser.add_argument("--build-command", required=True, type=Path)
    parser.add_argument("--build-environment", required=True, type=Path)
    parser.add_argument("--build-log", required=True, type=Path)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--dependency-closure", required=True, type=Path)
    parser.add_argument("--parent-smaller", required=True, type=Path)
    parser.add_argument("--candidate-smaller", required=True, type=Path)
    parser.add_argument("--equal-size-parent-tie", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        output, verified = verify(args)
    except (OSError, VerificationError) as exc:
        output = {
            "schema_version": SCHEMA,
            "program_id": PROGRAM_ID,
            "verified": False,
            "computed": None,
            "errors": [str(exc)],
        }
        verified = False
    encoded = json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n"
    if args.output is None:
        sys.stdout.write(encoded)
    else:
        args.output.write_text(encoded, encoding="utf-8")
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
