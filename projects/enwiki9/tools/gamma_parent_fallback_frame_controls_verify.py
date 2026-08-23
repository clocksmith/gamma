#!/usr/bin/env python3
"""Verify retained negative-control evidence for the native GAFS framer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


SCHEMA = "gamma-parent-fallback-frame-control-verification.v1"
PROGRAM_ID = "gamma_parent_fallback_archive_select_q0_v1"
MAGIC = b"GAFS"
VERSION = 1
HEADER_BYTES = 14
CHUNK_BYTES = 1024 * 1024
MALFORMED_CONTROLS = (
    "bad_magic",
    "bad_version",
    "bad_mode",
    "short_header",
    "short_payload",
    "trailing_bytes",
)
ALL_CONTROLS = MALFORMED_CONTROLS + (
    "existing_output",
    "symlink_input",
    "nonregular_input",
)


class VerificationError(Exception):
    pass


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"JSON root is not an object: {path}")
    return value, raw


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


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def object_field(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} is not an object")
        return {}
    return value


def verify_stream(path: Path, receipt: dict[str, Any], name: str, errors: list[str]) -> None:
    size, digest = file_identity(path)
    require(receipt.get("bytes") == size, f"{name} byte count mismatch", errors)
    require(receipt.get("sha256") == digest, f"{name} SHA-256 mismatch", errors)


def valid_frame(raw: bytes) -> bool:
    if len(raw) < HEADER_BYTES or raw[:4] != MAGIC or raw[4] != VERSION or raw[5] > 1:
        return False
    payload_bytes = int.from_bytes(raw[6:14], "little")
    return payload_bytes == len(raw) - HEADER_BYTES


def malformed_as_declared(name: str, raw: bytes) -> bool:
    if name == "bad_magic":
        return len(raw) >= HEADER_BYTES and raw[:4] != MAGIC
    if name == "bad_version":
        return len(raw) >= HEADER_BYTES and raw[:4] == MAGIC and raw[4] != VERSION
    if name == "bad_mode":
        return len(raw) >= HEADER_BYTES and raw[:4] == MAGIC and raw[4] == VERSION and raw[5] > 1
    if name == "short_header":
        return len(raw) < HEADER_BYTES
    if len(raw) < HEADER_BYTES or raw[:4] != MAGIC or raw[4] != VERSION or raw[5] > 1:
        return False
    declared = int.from_bytes(raw[6:14], "little")
    actual = len(raw) - HEADER_BYTES
    if name == "short_payload":
        return declared > actual
    if name == "trailing_bytes":
        return declared < actual
    return False


def verify(args: argparse.Namespace) -> tuple[dict[str, Any], bool]:
    errors: list[str] = []
    manifest, manifest_raw = load_json(args.manifest)
    require(manifest.get("schema_version") == "gamma-parent-fallback-frame-control-evidence.v1", "control manifest schema mismatch", errors)
    require(manifest.get("program_id") == PROGRAM_ID, "control manifest program_id mismatch", errors)
    _, binary_sha256 = file_identity(args.binary)
    require(manifest.get("binary_sha256") == binary_sha256, "control binary SHA-256 mismatch", errors)
    controls = object_field(manifest.get("controls"), "manifest.controls", errors)

    for name in ALL_CONTROLS:
        directory = args.controls_root / name
        record = object_field(controls.get(name), f"manifest.controls.{name}", errors)
        require(record.get("return_code") not in (None, 0), f"{name} did not retain a nonzero return code", errors)
        verify_stream(directory / "stdout.bin", object_field(record.get("stdout"), f"{name}.stdout", errors), f"{name} stdout", errors)
        verify_stream(directory / "stderr.bin", object_field(record.get("stderr"), f"{name}.stderr", errors), f"{name} stderr", errors)

    for name in MALFORMED_CONTROLS:
        directory = args.controls_root / name
        record = object_field(controls.get(name), f"manifest.controls.{name}", errors)
        archive_path = directory / "archive.gafs"
        archive_raw = archive_path.read_bytes()
        require(record.get("input_sha256") == hashlib.sha256(archive_raw).hexdigest(), f"{name} input SHA-256 mismatch", errors)
        require(malformed_as_declared(name, archive_raw), f"{name} input does not realize its declared mutation", errors)
        require(record.get("output_exists") is False, f"{name} claims an output", errors)
        require(not (directory / "output.bin").exists(), f"{name} output path exists", errors)

    existing_directory = args.controls_root / "existing_output"
    existing_record = object_field(controls.get("existing_output"), "manifest.controls.existing_output", errors)
    existing_archive = (existing_directory / "archive.gafs").read_bytes()
    require(valid_frame(existing_archive), "existing_output archive is not valid", errors)
    require(existing_record.get("input_sha256") == hashlib.sha256(existing_archive).hexdigest(), "existing_output archive hash mismatch", errors)
    _, before_sha256 = file_identity(existing_directory / "output-before.bin")
    _, after_sha256 = file_identity(existing_directory / "output-after.bin")
    require(existing_record.get("output_before_sha256") == before_sha256, "existing_output before hash mismatch", errors)
    require(existing_record.get("output_after_sha256") == after_sha256, "existing_output after hash mismatch", errors)
    require(before_sha256 == after_sha256, "existing output was modified", errors)
    require(existing_record.get("output_exists") is True, "existing_output does not retain output existence", errors)

    symlink_directory = args.controls_root / "symlink_input"
    symlink_record = object_field(controls.get("symlink_input"), "manifest.controls.symlink_input", errors)
    link_path = symlink_directory / "input-link"
    require(link_path.is_symlink(), "symlink_input is not a symlink", errors)
    if link_path.is_symlink():
        link_target = os.readlink(link_path)
        require(symlink_record.get("link_target") == link_target, "symlink target mismatch", errors)
    require(symlink_record.get("output_exists") is False, "symlink_input claims an output", errors)
    require(not (symlink_directory / "output.bin").exists(), "symlink_input output exists", errors)

    nonregular_directory = args.controls_root / "nonregular_input"
    nonregular_record = object_field(controls.get("nonregular_input"), "manifest.controls.nonregular_input", errors)
    require((nonregular_directory / "input-directory").is_dir(), "nonregular_input is not a directory", errors)
    require(nonregular_record.get("output_exists") is False, "nonregular_input claims an output", errors)
    require(not (nonregular_directory / "output.bin").exists(), "nonregular_input output exists", errors)

    verified = not errors
    output = {
        "schema_version": SCHEMA,
        "program_id": PROGRAM_ID,
        "verified": verified,
        "computed": {
            "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "binary_sha256": binary_sha256,
            "controls": list(ALL_CONTROLS),
        },
        "errors": errors,
    }
    return output, verified


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--controls-root", required=True, type=Path)
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
