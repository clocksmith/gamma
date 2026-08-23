#!/usr/bin/env python3
"""Materialize exact q1 executable, static-input, environment, and command identities."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any


INPUT_SCHEMA = "gamma.enwiki9.cmix-memory-safe-parent-command-draft.v1"
OUTPUT_SCHEMA = "gamma.enwiki9.cmix-memory-safe-parent-command-manifest.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
WORKSPACE_ROOT = "/home/x/deco/gamma"
STEP_IDS = [
    "source_closure",
    "program_lock",
    "build_a",
    "build_b",
    "build_verification",
    "compiler_trace_controls",
    "allocator_controls",
    "scope_probability_identity",
    "full_roundtrip_a",
    "full_roundtrip_b",
    "qualification_receipt",
    "qualification_verification",
]
STEP_HASH_RULE = "SHA-256 of canonical compact ASCII JSON for the complete step object with command_sha256 omitted"
MANIFEST_HASH_RULE = "SHA-256 of canonical ASCII JSON with this field present and command_manifest_sha256 absent"


def pretty_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def sha256_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def regular_file(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise SystemExit(f"{label}: symlink component forbidden: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise SystemExit(f"{label}: expected single-link regular file")
    return absolute.resolve(strict=True)


def regular_directory(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise SystemExit(f"{label}: symlink component forbidden: {current}")
    if not stat.S_ISDIR(absolute.stat().st_mode):
        raise SystemExit(f"{label}: expected directory")
    return absolute.resolve(strict=True)


def require_output_parent(path: Path) -> None:
    regular_directory(path.parent, "manifest parent")
    if path.exists() or path.is_symlink():
        raise SystemExit("manifest path already exists")


def require_clear_lease(path: Path) -> None:
    lease = json.loads(regular_file(path, "exclusive lease").read_text(encoding="utf-8"))
    if not isinstance(lease, dict) or lease.get("active") is not False:
        raise SystemExit("exclusive lease is active or lacks an explicit inactive decision")


def safe_relative(value: Any) -> str:
    if not isinstance(value, str) or not value or not value.isascii() or any(character in value for character in ("\0", "\n", "\r")):
        raise SystemExit("path must be nonempty single-line ASCII")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise SystemExit(f"unsafe workspace-relative path: {value}")
    return path.as_posix()


def identity(path: Path, display: str) -> dict[str, Any]:
    return {"path": display, "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    require_clear_lease(args.exclusive_lease)
    workspace = regular_directory(Path(WORKSPACE_ROOT), "workspace root")
    draft_path = regular_file(args.draft, "command draft")
    require_output_parent(args.manifest)
    raw = draft_path.read_bytes()
    try:
        draft = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"draft parse failure: {exc}") from exc
    if not isinstance(draft, dict):
        raise SystemExit("draft must be a JSON object")
    values = draft.get("steps")
    if (
        draft.get("schema") != INPUT_SCHEMA
        or draft.get("candidate_id") != CANDIDATE_ID
        or draft.get("workspace_root") != WORKSPACE_ROOT
        or draft.get("claim_authority") != "none"
        or draft.get("execution_authority") is not False
        or not isinstance(values, list)
        or len(values) != len(STEP_IDS)
    ):
        raise SystemExit("unexpected draft identity, governance, or step count")
    steps: list[dict[str, Any]] = []
    for ordinal, value in enumerate(values):
        if not isinstance(value, dict) or value.get("ordinal") != ordinal or value.get("id") != STEP_IDS[ordinal]:
            raise SystemExit("draft steps are not in exact frozen order")
        executable_display = value.get("executable_path")
        if not isinstance(executable_display, str) or not executable_display:
            raise SystemExit(f"step {STEP_IDS[ordinal]} lacks executable_path")
        executable_path = regular_file(Path(executable_display), f"step {STEP_IDS[ordinal]} executable")
        input_values = value.get("input_paths")
        if not isinstance(input_values, list):
            raise SystemExit(f"step {STEP_IDS[ordinal]} input_paths is not an array")
        input_paths = [safe_relative(item) for item in input_values]
        if len(input_paths) != len(set(input_paths)):
            raise SystemExit(f"step {STEP_IDS[ordinal]} has duplicate static inputs")
        inputs: list[dict[str, Any]] = []
        for relative in input_paths:
            source = regular_file(workspace / relative, f"step {STEP_IDS[ordinal]} input {relative}")
            try:
                source.relative_to(workspace)
            except ValueError as exc:
                raise SystemExit(f"step input escapes workspace: {relative}") from exc
            inputs.append(identity(source, relative))
        step = {
            "ordinal": ordinal,
            "id": STEP_IDS[ordinal],
            "cwd": value.get("cwd"),
            "argv": value.get("argv"),
            "environment": value.get("environment"),
            "executable": identity(executable_path, executable_display),
            "inputs": inputs,
            "generated_input_refs": value.get("generated_input_refs"),
            "declared_outputs": value.get("declared_outputs"),
        }
        step["command_sha256"] = hashlib.sha256(canonical_json(step)).hexdigest()
        steps.append(step)
    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "workspace_root": WORKSPACE_ROOT,
        "result_root": draft.get("result_root"),
        "steps": steps,
        "step_command_sha256_rule": STEP_HASH_RULE,
        "manifest_sha256_rule": MANIFEST_HASH_RULE,
        "claim_authority": "none",
        "execution_authority": False,
    }
    with args.manifest.open("xb") as stream:
        stream.write(pretty_json(output))
        stream.flush()
        os.fsync(stream.fileno())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
