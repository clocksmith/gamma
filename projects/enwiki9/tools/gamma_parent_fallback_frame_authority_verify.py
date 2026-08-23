#!/usr/bin/env python3
"""Fail-closed composition verifier for native framing and negative controls."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PROGRAM_ID = "gamma_parent_fallback_archive_select_q0_v1"
MANIFEST_SCHEMA = "gamma-parent-fallback-frame-authority-manifest.v1"
NATIVE_VERIFICATION_SCHEMA = "gamma-parent-fallback-frame-native-verification.v1"
CONTROL_VERIFICATION_SCHEMA = "gamma-parent-fallback-frame-control-verification.v1"
OUTPUT_SCHEMA = "gamma-parent-fallback-frame-authority-verification.v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def named_values(value: Any, key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, dict):
        for current_key, current_value in value.items():
            if current_key == key:
                found.append(current_value)
            found.extend(named_values(current_value, key))
    elif isinstance(value, list):
        for item in value:
            found.extend(named_values(item, key))
    return found


def require_equal(errors: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        errors.append(f"{label}: expected {expected!r}, got {actual!r}")


def require_bound_hash(
    errors: list[str], document: dict[str, Any], key: str, expected: str, label: str
) -> None:
    values = named_values(document, key)
    if expected not in values:
        errors.append(f"{label}: no {key} field binds {expected}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-manifest", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--native-receipt", type=Path, required=True)
    parser.add_argument("--native-verification", type=Path, required=True)
    parser.add_argument("--control-evidence-manifest", type=Path, required=True)
    parser.add_argument("--control-verification", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    paths = {
        "authority_manifest": args.authority_manifest,
        "binary": args.binary,
        "native_receipt": args.native_receipt,
        "native_verification": args.native_verification,
        "control_evidence_manifest": args.control_evidence_manifest,
        "control_verification": args.control_verification,
    }
    for label, path in paths.items():
        if not path.is_file():
            errors.append(f"{label}: missing regular file: {path}")

    computed = {f"{label}_sha256": sha256_file(path) for label, path in paths.items() if path.is_file()}

    manifest: dict[str, Any] = {}
    native_receipt: dict[str, Any] = {}
    native_verification: dict[str, Any] = {}
    control_manifest: dict[str, Any] = {}
    control_verification: dict[str, Any] = {}
    for label, path in (
        ("authority_manifest", args.authority_manifest),
        ("native_receipt", args.native_receipt),
        ("native_verification", args.native_verification),
        ("control_evidence_manifest", args.control_evidence_manifest),
        ("control_verification", args.control_verification),
    ):
        if not path.is_file():
            continue
        try:
            document = load_json(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{label}: {exc}")
            continue
        if label == "authority_manifest":
            manifest = document
        elif label == "native_receipt":
            native_receipt = document
        elif label == "native_verification":
            native_verification = document
        elif label == "control_evidence_manifest":
            control_manifest = document
        else:
            control_verification = document

    if manifest:
        require_equal(errors, "manifest schema", manifest.get("schema"), MANIFEST_SCHEMA)
        require_equal(errors, "manifest program_id", manifest.get("program_id"), PROGRAM_ID)
        for key in (
            "binary_sha256",
            "native_receipt_sha256",
            "native_verification_sha256",
            "control_evidence_manifest_sha256",
            "control_verification_sha256",
        ):
            require_equal(errors, f"manifest {key}", manifest.get(key), computed.get(key))
        require_equal(errors, "manifest native_verification_pass", manifest.get("native_verification_pass"), True)
        require_equal(errors, "manifest control_verification_pass", manifest.get("control_verification_pass"), True)
        require_equal(errors, "manifest execution_authority", manifest.get("execution_authority"), True)

    if native_receipt:
        require_equal(errors, "native receipt program_id", native_receipt.get("program_id"), PROGRAM_ID)
        require_bound_hash(errors, native_receipt, "binary_sha256", computed.get("binary_sha256", ""), "native receipt")

    if native_verification:
        require_equal(errors, "native verification schema", native_verification.get("schema"), NATIVE_VERIFICATION_SCHEMA)
        require_equal(errors, "native verification program_id", native_verification.get("program_id"), PROGRAM_ID)
        require_equal(errors, "native verification verified", native_verification.get("verified"), True)
        require_equal(errors, "native verification errors", native_verification.get("errors"), [])
        require_bound_hash(errors, native_verification, "receipt_sha256", computed.get("native_receipt_sha256", ""), "native verification")
        require_bound_hash(errors, native_verification, "binary_sha256", computed.get("binary_sha256", ""), "native verification")

    if control_manifest:
        require_equal(errors, "control manifest program_id", control_manifest.get("program_id"), PROGRAM_ID)
        require_bound_hash(errors, control_manifest, "binary_sha256", computed.get("binary_sha256", ""), "control manifest")

    if control_verification:
        require_equal(errors, "control verification schema", control_verification.get("schema"), CONTROL_VERIFICATION_SCHEMA)
        require_equal(errors, "control verification program_id", control_verification.get("program_id"), PROGRAM_ID)
        require_equal(errors, "control verification verified", control_verification.get("verified"), True)
        require_equal(errors, "control verification errors", control_verification.get("errors"), [])
        require_bound_hash(
            errors,
            control_verification,
            "manifest_sha256",
            computed.get("control_evidence_manifest_sha256", ""),
            "control verification",
        )
        require_bound_hash(errors, control_verification, "binary_sha256", computed.get("binary_sha256", ""), "control verification")

    output = {
        "schema": OUTPUT_SCHEMA,
        "program_id": PROGRAM_ID,
        "verified": not errors,
        "errors": errors,
        "computed": {
            "authority_manifest_sha256": computed.get("authority_manifest_sha256", "0" * 64),
            "binary_sha256": computed.get("binary_sha256", "0" * 64),
            "native_receipt_sha256": computed.get("native_receipt_sha256", "0" * 64),
            "native_verification_sha256": computed.get("native_verification_sha256", "0" * 64),
            "control_evidence_manifest_sha256": computed.get("control_evidence_manifest_sha256", "0" * 64),
            "control_verification_sha256": computed.get("control_verification_sha256", "0" * 64),
        },
    }
    rendered = json.dumps(output, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if output["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
