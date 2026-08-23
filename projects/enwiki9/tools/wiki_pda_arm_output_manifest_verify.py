#!/usr/bin/env python3
"""Verify a WIKI-PDA arm's output directory as an exact closed artifact set."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any


MANIFEST_SCHEMA = "gamma.enwiki9.wiki-pda-arm-output-manifest.v1"
OUTPUT_SCHEMA = "gamma.enwiki9.wiki-pda-arm-output-verification.v1"
CANDIDATE_ID = "wiki_pda_structural_replay_q0_v2"
KNOWN_ROLES = {
    "command_manifest",
    "stdout",
    "stderr",
    "archive",
    "decoded_stream",
    "raw_inverse",
    "integer_probability_stream",
    "coder_state_manifest",
    "parent_persistent_state_manifest",
    "wiki_pda_state_manifest",
    "resource_receipt",
    "dependency_closure_receipt",
}
ALWAYS_REQUIRED = {"command_manifest", "stdout", "stderr", "resource_receipt"}
ENCODE_SUCCESS_REQUIRED = {
    "archive",
    "integer_probability_stream",
    "coder_state_manifest",
    "parent_persistent_state_manifest",
    "wiki_pda_state_manifest",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative_path(raw: Any) -> str | None:
    if not isinstance(raw, str) or not raw:
        return None
    if "\x00" in raw:
        return None
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != raw:
        return None
    return path.as_posix()


def scan_root(root: Path, errors: list[str]) -> tuple[dict[str, os.stat_result], int]:
    observed: dict[str, os.stat_result] = {}
    total_bytes = 0

    def visit(directory: Path, relative: PurePosixPath) -> None:
        nonlocal total_bytes
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name)
        except OSError as exc:
            errors.append(f"cannot scan {directory}: {exc}")
            return
        for entry in entries:
            child_relative = relative / entry.name
            child_name = child_relative.as_posix()
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as exc:
                errors.append(f"cannot stat {child_name}: {exc}")
                continue
            mode = metadata.st_mode
            if stat.S_ISLNK(mode):
                errors.append(f"symlink forbidden: {child_name}")
            elif stat.S_ISDIR(mode):
                visit(Path(entry.path), child_relative)
            elif stat.S_ISREG(mode):
                if metadata.st_nlink != 1:
                    errors.append(f"hard-linked artifact forbidden: {child_name} has nlink={metadata.st_nlink}")
                observed[child_name] = metadata
                total_bytes += metadata.st_size
            else:
                errors.append(f"special filesystem entry forbidden: {child_name}")

    visit(root, PurePosixPath())
    return observed, total_bytes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--artifacts-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    manifest_sha256 = "0" * 64
    manifest: dict[str, Any] = {}
    if not args.manifest.is_file():
        errors.append(f"manifest is not a regular file: {args.manifest}")
    else:
        manifest_sha256 = sha256_file(args.manifest)
        try:
            loaded = json.loads(args.manifest.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("manifest must be a JSON object")
            manifest = loaded
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"manifest parse failure: {exc}")

    if not args.artifacts_root.is_dir() or args.artifacts_root.is_symlink():
        errors.append(f"artifacts root must be a non-symlink directory: {args.artifacts_root}")
        observed: dict[str, os.stat_result] = {}
        observed_bytes = 0
    else:
        observed, observed_bytes = scan_root(args.artifacts_root, errors)

    if manifest:
        if manifest.get("schema") != MANIFEST_SCHEMA:
            errors.append("unexpected manifest schema")
        if manifest.get("candidate_id") != CANDIDATE_ID:
            errors.append("unexpected candidate_id")

        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, list):
            errors.append("artifacts must be an array")
            artifacts = []
        declared_paths: dict[str, str] = {}
        declared_roles: dict[str, str] = {}
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"artifacts[{index}] must be an object")
                continue
            role = artifact.get("role")
            relative = safe_relative_path(artifact.get("path"))
            if role not in KNOWN_ROLES:
                errors.append(f"artifacts[{index}] has unknown role {role!r}")
            elif role in declared_roles:
                errors.append(f"duplicate artifact role: {role}")
            if relative is None:
                errors.append(f"artifacts[{index}] has unsafe path")
                continue
            if relative in declared_paths:
                errors.append(f"duplicate artifact path: {relative}")
                continue
            declared_paths[relative] = str(role)
            if role in KNOWN_ROLES:
                declared_roles[str(role)] = relative
            metadata = observed.get(relative)
            if metadata is None:
                errors.append(f"declared artifact missing: {relative}")
                continue
            if artifact.get("bytes") != metadata.st_size:
                errors.append(f"size mismatch: {relative}")
            actual_sha256 = sha256_file(args.artifacts_root / relative)
            if artifact.get("sha256") != actual_sha256:
                errors.append(f"SHA-256 mismatch: {relative}")

        undeclared = sorted(set(observed) - set(declared_paths))
        missing = sorted(set(declared_paths) - set(observed))
        if undeclared:
            errors.append("undeclared regular files: " + ", ".join(undeclared))
        if missing:
            errors.append("missing declared regular files: " + ", ".join(missing))

        absent_always = sorted(ALWAYS_REQUIRED - set(declared_roles))
        if absent_always:
            errors.append("missing always-required roles: " + ", ".join(absent_always))

        return_codes = manifest.get("return_codes")
        if not isinstance(return_codes, dict):
            errors.append("return_codes must be an object")
            return_codes = {}
        phase_status = manifest.get("phase_status")
        encode = return_codes.get("encode")
        decode = return_codes.get("decode")
        raw_inverse = return_codes.get("raw_inverse")
        if encode == 0:
            absent = sorted(ENCODE_SUCCESS_REQUIRED - set(declared_roles))
            if absent:
                errors.append("successful encode missing roles: " + ", ".join(absent))
        if decode == 0 and "decoded_stream" not in declared_roles:
            errors.append("successful decode missing decoded_stream")
        if raw_inverse == 0 and "raw_inverse" not in declared_roles:
            errors.append("successful raw inverse missing raw_inverse")
        if phase_status == "complete":
            if (encode, decode, raw_inverse) != (0, 0, 0):
                errors.append("complete phase requires three zero return codes")
            if "dependency_closure_receipt" not in declared_roles:
                errors.append("complete phase missing dependency_closure_receipt")
            raw_path = declared_roles.get("raw_inverse")
            expected_raw = manifest.get("expected_raw")
            if raw_path and isinstance(expected_raw, dict) and raw_path in observed:
                raw_file = args.artifacts_root / raw_path
                if expected_raw.get("bytes") != observed[raw_path].st_size:
                    errors.append("raw inverse size does not match expected_raw")
                if expected_raw.get("sha256") != sha256_file(raw_file):
                    errors.append("raw inverse SHA-256 does not match expected_raw")

    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "run_id": str(manifest.get("run_id", "invalid")),
        "arm": manifest.get("arm", "P") if manifest.get("arm") in {"P", "K", "D", "R", "S"} else "P",
        "verified": not errors,
        "errors": errors,
        "computed": {
            "manifest_sha256": manifest_sha256,
            "observed_regular_files": len(observed),
            "observed_regular_bytes": observed_bytes,
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
