#!/usr/bin/env python3
"""Recompute and cross-bind all WIKI-PDA arm output evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


CANDIDATE_ID = "wiki_pda_structural_replay_q0_v2"
AUTHORITY_SCHEMA = "gamma.enwiki9.wiki-pda-output-authority-manifest.v1"
RECEIPT_SCHEMA = "gamma.enwiki9.wiki-pda-structural-replay-receipt.v3"
ARM_MANIFEST_SCHEMA = "gamma.enwiki9.wiki-pda-arm-output-manifest.v1"
ARM_VERIFICATION_SCHEMA = "gamma.enwiki9.wiki-pda-arm-output-verification.v1"
OUTPUT_SCHEMA = "gamma.enwiki9.wiki-pda-output-authority-verification.v1"
ARMS = ("P", "K", "D", "R", "S")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_bytes(data: bytes, label: str) -> dict[str, Any]:
    value = json.loads(data.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label}: expected JSON object")
    return value


def canonical_relative(raw: Any) -> PurePosixPath | None:
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        return None
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != raw:
        return None
    return path


def bound_path(root: Path, raw: Any, want_directory: bool, errors: list[str], label: str) -> Path | None:
    relative = canonical_relative(raw)
    if relative is None:
        errors.append(f"{label}: unsafe or non-canonical path")
        return None
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            errors.append(f"{label}: cannot lstat {relative}: {exc}")
            return None
        if stat.S_ISLNK(metadata.st_mode):
            errors.append(f"{label}: symlink component forbidden: {relative}")
            return None
    try:
        metadata = current.stat()
    except OSError as exc:
        errors.append(f"{label}: cannot stat {relative}: {exc}")
        return None
    if want_directory:
        if not stat.S_ISDIR(metadata.st_mode):
            errors.append(f"{label}: expected directory: {relative}")
            return None
    else:
        if not stat.S_ISREG(metadata.st_mode):
            errors.append(f"{label}: expected regular file: {relative}")
            return None
        if metadata.st_nlink != 1:
            errors.append(f"{label}: hard-linked metadata file forbidden: {relative}")
            return None
    return current


def artifact_by_role(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        if isinstance(artifact, dict) and isinstance(artifact.get("role"), str):
            result[artifact["role"]] = artifact
    return result


def compare(errors: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        errors.append(f"{label}: expected {expected!r}, got {actual!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-manifest", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    authority_hash = "0" * 64
    authority: dict[str, Any] = {}
    if not args.authority_manifest.is_file() or args.authority_manifest.is_symlink():
        errors.append("authority manifest must be a non-symlink regular file")
    else:
        authority_hash = sha256_file(args.authority_manifest)
        try:
            authority = load_json_bytes(args.authority_manifest.read_bytes(), "authority manifest")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(str(exc))

    if not args.evidence_root.is_dir() or args.evidence_root.is_symlink():
        errors.append("evidence root must be a non-symlink directory")

    receipt_hash = "0" * 64
    verifier_hash = "0" * 64
    receipt: dict[str, Any] = {}
    verifier_path: Path | None = None
    if authority:
        compare(errors, "authority schema", authority.get("schema"), AUTHORITY_SCHEMA)
        compare(errors, "authority candidate_id", authority.get("candidate_id"), CANDIDATE_ID)
        receipt_path = bound_path(args.evidence_root, authority.get("receipt_path"), False, errors, "receipt")
        verifier_path = bound_path(
            args.evidence_root,
            authority.get("arm_output_verifier_path"),
            False,
            errors,
            "arm output verifier",
        )
        if receipt_path:
            receipt_hash = sha256_file(receipt_path)
            compare(errors, "authority receipt_sha256", authority.get("receipt_sha256"), receipt_hash)
            try:
                receipt = load_json_bytes(receipt_path.read_bytes(), "receipt")
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                errors.append(str(exc))
        if verifier_path:
            verifier_hash = sha256_file(verifier_path)
            compare(errors, "authority arm_output_verifier_sha256", authority.get("arm_output_verifier_sha256"), verifier_hash)

    if receipt:
        compare(errors, "receipt schema", receipt.get("schema"), RECEIPT_SCHEMA)
        compare(errors, "receipt candidate_id", receipt.get("candidate_id"), CANDIDATE_ID)

    input_lock = receipt.get("input_lock") if isinstance(receipt.get("input_lock"), dict) else {}
    receipt_arms = receipt.get("arms") if isinstance(receipt.get("arms"), dict) else {}
    authority_arms = authority.get("arms") if isinstance(authority.get("arms"), dict) else {}
    computed_arms: dict[str, dict[str, str]] = {}

    for arm in ARMS:
        entry = authority_arms.get(arm)
        receipt_arm = receipt_arms.get(arm)
        if not isinstance(entry, dict):
            errors.append(f"{arm}: missing authority arm entry")
            computed_arms[arm] = {"output_manifest_sha256": "0" * 64, "output_verification_sha256": "0" * 64}
            continue
        if not isinstance(receipt_arm, dict):
            errors.append(f"{arm}: missing receipt arm")
            receipt_arm = {}

        manifest_path = bound_path(args.evidence_root, entry.get("output_manifest_path"), False, errors, f"{arm} manifest")
        artifacts_root = bound_path(args.evidence_root, entry.get("artifacts_root"), True, errors, f"{arm} artifacts root")
        verification_path = bound_path(
            args.evidence_root,
            entry.get("output_verification_path"),
            False,
            errors,
            f"{arm} verification",
        )
        manifest_hash = sha256_file(manifest_path) if manifest_path else "0" * 64
        verification_hash = sha256_file(verification_path) if verification_path else "0" * 64
        computed_arms[arm] = {
            "output_manifest_sha256": manifest_hash,
            "output_verification_sha256": verification_hash,
        }
        compare(errors, f"{arm} authority manifest hash", entry.get("output_manifest_sha256"), manifest_hash)
        compare(errors, f"{arm} authority verification hash", entry.get("output_verification_sha256"), verification_hash)
        compare(errors, f"{arm} receipt manifest hash", receipt_arm.get("output_manifest_sha256"), manifest_hash)
        compare(errors, f"{arm} receipt verification hash", receipt_arm.get("output_verification_sha256"), verification_hash)
        compare(errors, f"{arm} receipt output_verification_pass", receipt_arm.get("output_verification_pass"), True)

        manifest: dict[str, Any] = {}
        recorded_verification = b""
        if manifest_path:
            try:
                manifest = load_json_bytes(manifest_path.read_bytes(), f"{arm} output manifest")
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                errors.append(str(exc))
        if verification_path:
            try:
                recorded_verification = verification_path.read_bytes()
                verification = load_json_bytes(recorded_verification, f"{arm} output verification")
                compare(errors, f"{arm} verification schema", verification.get("schema"), ARM_VERIFICATION_SCHEMA)
                compare(errors, f"{arm} verification candidate_id", verification.get("candidate_id"), CANDIDATE_ID)
                compare(errors, f"{arm} verification arm", verification.get("arm"), arm)
                compare(errors, f"{arm} verification verified", verification.get("verified"), True)
                compare(errors, f"{arm} verification errors", verification.get("errors"), [])
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                errors.append(str(exc))

        if verifier_path and manifest_path and artifacts_root:
            completed = subprocess.run(
                [
                    sys.executable,
                    os.fspath(verifier_path),
                    "--manifest",
                    os.fspath(manifest_path),
                    "--artifacts-root",
                    os.fspath(artifacts_root),
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if completed.returncode != 0:
                errors.append(f"{arm}: arm verifier returned {completed.returncode}: {completed.stderr.decode('utf-8', 'replace')}")
            if completed.stdout != recorded_verification:
                errors.append(f"{arm}: freshly recomputed verification differs bytewise from recorded verification")

        if manifest:
            compare(errors, f"{arm} manifest schema", manifest.get("schema"), ARM_MANIFEST_SCHEMA)
            compare(errors, f"{arm} manifest candidate_id", manifest.get("candidate_id"), CANDIDATE_ID)
            compare(errors, f"{arm} manifest arm", manifest.get("arm"), arm)
            compare(errors, f"{arm} manifest binary", manifest.get("binary_sha256"), input_lock.get("binary_sha256"))
            compare(
                errors,
                f"{arm} manifest population",
                manifest.get("population_manifest_sha256"),
                input_lock.get("population_manifest_sha256"),
            )
            compare(errors, f"{arm} command", manifest.get("command_sha256"), receipt_arm.get("command_sha256"))
            compare(errors, f"{arm} return codes", manifest.get("return_codes"), receipt_arm.get("return_codes"))
            artifacts = artifact_by_role(manifest)
            role_bindings = {
                "integer_probability_stream": "integer_probability_stream_sha256",
                "coder_state_manifest": "coder_state_manifest_sha256",
                "parent_persistent_state_manifest": "parent_persistent_state_manifest_sha256",
                "wiki_pda_state_manifest": "wiki_pda_state_manifest_sha256",
                "resource_receipt": "resource_receipt_sha256",
                "dependency_closure_receipt": "dependency_closure_receipt_sha256",
            }
            for role, receipt_key in role_bindings.items():
                artifact = artifacts.get(role)
                if artifact is not None:
                    compare(errors, f"{arm} {role} hash", artifact.get("sha256"), receipt_arm.get(receipt_key))
            archive = artifacts.get("archive")
            if archive is not None:
                compare(errors, f"{arm} archive bytes", archive.get("bytes"), receipt_arm.get("archive_size_bytes"))
                compare(errors, f"{arm} archive hash", archive.get("sha256"), receipt_arm.get("archive_sha256"))
            decoded_stream = artifacts.get("decoded_stream")
            if decoded_stream is not None:
                compare(errors, f"{arm} decoded stream bytes", decoded_stream.get("bytes"), receipt_arm.get("decoded_size_bytes"))
                compare(errors, f"{arm} decoded stream hash", decoded_stream.get("sha256"), receipt_arm.get("decoded_sha256"))
            raw_inverse = artifacts.get("raw_inverse")
            expected_raw = manifest.get("expected_raw") if isinstance(manifest.get("expected_raw"), dict) else {}
            if raw_inverse is not None:
                compare(errors, f"{arm} raw inverse receipt bytes", raw_inverse.get("bytes"), receipt_arm.get("raw_inverse_size_bytes"))
                compare(errors, f"{arm} raw inverse receipt hash", raw_inverse.get("sha256"), receipt_arm.get("raw_inverse_sha256"))
                compare(errors, f"{arm} raw inverse expected bytes", raw_inverse.get("bytes"), expected_raw.get("bytes"))
                compare(errors, f"{arm} raw inverse expected hash", raw_inverse.get("sha256"), expected_raw.get("sha256"))
                compare(errors, f"{arm} raw inverse corpus hash", raw_inverse.get("sha256"), input_lock.get("corpus_sha256"))
            if manifest.get("phase_status") == "complete":
                compare(errors, f"{arm} raw_inverse_pass", receipt_arm.get("raw_inverse_pass"), True)

    comparisons = receipt.get("comparisons") if isinstance(receipt.get("comparisons"), dict) else {}
    compare(errors, "receipt all_arm_output_manifests_pass", comparisons.get("all_arm_output_manifests_pass"), True)

    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "verified": not errors,
        "errors": errors,
        "computed": {
            "authority_manifest_sha256": authority_hash,
            "receipt_sha256": receipt_hash,
            "arm_output_verifier_sha256": verifier_hash,
            "arms": computed_arms,
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
