#!/usr/bin/env python3
"""Verify q1 exact commands, static inputs, generated-input DAG, and outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any


INPUT_SCHEMA = "gamma.enwiki9.cmix-memory-safe-parent-command-manifest.v1"
OUTPUT_SCHEMA = "gamma.enwiki9.cmix-memory-safe-parent-command-manifest-verification.v1"
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
OUTPUT_PREFIX = {
    "source_closure": "01_source_closure/",
    "program_lock": "01_source_closure/",
    "build_a": "02_build_a/",
    "build_b": "03_build_b/",
    "build_verification": "04_build_verification/",
    "compiler_trace_controls": "05_controls/",
    "allocator_controls": "05_controls/",
    "scope_probability_identity": "06_scope_identity/",
    "full_roundtrip_a": "07_full_roundtrip_a/",
    "full_roundtrip_b": "08_full_roundtrip_b/",
    "qualification_receipt": "09_qualification/",
    "qualification_verification": "09_qualification/",
}
REQUIRED_ENVIRONMENT = {"LANG": "C", "LC_ALL": "C", "PYTHONHASHSEED": "0", "TZ": "UTC"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def pretty_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def require_clear_lease(path: Path) -> None:
    lock_path = path.with_name(f"{path.name}.lock")
    if path.exists() or path.is_symlink() or lock_path.exists() or lock_path.is_symlink():
        raise SystemExit("exclusive lease namespace is occupied")


def safe_relative(value: Any) -> str | None:
    if not isinstance(value, str) or not value or not value.isascii() or "\0" in value or "\n" in value or "\r" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    args = parser.parse_args()
    require_clear_lease(args.exclusive_lease)
    manifest_path = regular_file(args.manifest, "command manifest")
    if args.verification.exists() or args.verification.is_symlink():
        raise SystemExit("verification path already exists")
    raw = manifest_path.read_bytes()
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"manifest parse failure: {exc}") from exc
    if not isinstance(manifest, dict):
        raise SystemExit("manifest must be a JSON object")
    errors: list[str] = []
    checks = {
        "identity_pass": True,
        "step_set_pass": True,
        "ordinal_pass": True,
        "argv_environment_pass": True,
        "static_input_identity_pass": True,
        "generated_input_dag_pass": True,
        "output_isolation_pass": True,
        "command_digest_pass": True,
    }
    result_root = safe_relative(manifest.get("result_root"))
    if (
        manifest.get("schema") != INPUT_SCHEMA
        or manifest.get("candidate_id") != CANDIDATE_ID
        or manifest.get("workspace_root") != WORKSPACE_ROOT
        or result_root is None
        or manifest.get("step_command_sha256_rule") != "SHA-256 of canonical compact ASCII JSON for the complete step object with command_sha256 omitted"
        or manifest.get("manifest_sha256_rule") != "SHA-256 of canonical ASCII JSON with this field present and command_manifest_sha256 absent"
        or manifest.get("claim_authority") != "none"
        or manifest.get("execution_authority") is not False
    ):
        errors.append("manifest identity or governance mismatch")
        checks["identity_pass"] = False
    values = manifest.get("steps")
    steps: dict[str, dict[str, Any]] = {}
    if isinstance(values, list):
        for value in values:
            if isinstance(value, dict) and isinstance(value.get("id"), str) and value["id"] not in steps:
                steps[value["id"]] = value
    if set(steps) != set(STEP_IDS) or not isinstance(values, list) or len(values) != len(STEP_IDS):
        errors.append("manifest step set is not exact")
        checks["step_set_pass"] = False
    if isinstance(values, list):
        ordinals = [value.get("ordinal") if isinstance(value, dict) else None for value in values]
        ids = [value.get("id") if isinstance(value, dict) else None for value in values]
        if ordinals != list(range(len(STEP_IDS))) or ids != STEP_IDS:
            errors.append("manifest steps are not in frozen ordinal order")
            checks["ordinal_pass"] = False

    declared_outputs: dict[str, str] = {}
    static_input_paths: set[str] = set()
    for ordinal, step_id in enumerate(STEP_IDS):
        step = steps.get(step_id)
        if step is None:
            continue
        argv = step.get("argv")
        environment = step.get("environment")
        executable = step.get("executable")
        argv_pass = (
            step.get("cwd") == WORKSPACE_ROOT
            and isinstance(argv, list)
            and len(argv) >= 2
            and all(isinstance(value, str) and value and value.isascii() and not any(character in value for character in ("\0", "\n", "\r")) for value in argv)
            and isinstance(environment, dict)
            and all(isinstance(key, str) and key.isascii() and isinstance(value, str) and value.isascii() for key, value in environment.items())
            and all(environment.get(key) == value for key, value in REQUIRED_ENVIRONMENT.items())
            and isinstance(executable, dict)
            and isinstance(executable.get("path"), str)
            and isinstance(executable.get("bytes"), int)
            and executable["bytes"] > 0
            and isinstance(executable.get("sha256"), str)
            and SHA256_RE.fullmatch(executable["sha256"]) is not None
        )
        if not argv_pass:
            errors.append(f"step {step_id} has invalid argv, environment, cwd, or executable identity")
            checks["argv_environment_pass"] = False
        inputs = step.get("inputs")
        if not isinstance(inputs, list):
            errors.append(f"step {step_id} static inputs are not an array")
            checks["static_input_identity_pass"] = False
        else:
            local_paths: set[str] = set()
            for item in inputs:
                if not isinstance(item, dict):
                    errors.append(f"step {step_id} has malformed static input")
                    checks["static_input_identity_pass"] = False
                    continue
                path_value = item.get("path")
                safe_path = safe_relative(path_value)
                if safe_path is None or safe_path in local_paths or not isinstance(item.get("bytes"), int) or item["bytes"] <= 0 or not isinstance(item.get("sha256"), str) or SHA256_RE.fullmatch(item["sha256"]) is None:
                    errors.append(f"step {step_id} has invalid or duplicate static input")
                    checks["static_input_identity_pass"] = False
                    continue
                local_paths.add(safe_path)
                static_input_paths.add(safe_path)
                try:
                    actual = regular_file(Path(WORKSPACE_ROOT) / safe_path, f"static input {safe_path}")
                except (OSError, SystemExit) as exc:
                    errors.append(f"step {step_id} static input is unavailable or unsafe: {exc}")
                    checks["static_input_identity_pass"] = False
                    continue
                if actual.stat().st_size != item["bytes"] or sha256_file(actual) != item["sha256"]:
                    errors.append(f"step {step_id} static input identity mismatch: {safe_path}")
                    checks["static_input_identity_pass"] = False
        outputs = step.get("declared_outputs")
        if not isinstance(outputs, list) or not outputs:
            errors.append(f"step {step_id} lacks declared outputs")
            checks["output_isolation_pass"] = False
        else:
            for output in outputs:
                safe_output = safe_relative(output)
                expected_prefix = OUTPUT_PREFIX[step_id]
                if safe_output is None or not safe_output.startswith(expected_prefix) or safe_output in declared_outputs:
                    errors.append(f"step {step_id} has unsafe, cross-phase, or duplicate output {output}")
                    checks["output_isolation_pass"] = False
                    continue
                declared_outputs[safe_output] = step_id
        refs = step.get("generated_input_refs")
        if not isinstance(refs, list):
            errors.append(f"step {step_id} generated_input_refs is not an array")
            checks["generated_input_dag_pass"] = False
        else:
            local_refs: set[tuple[str, str]] = set()
            for ref in refs:
                if not isinstance(ref, dict):
                    errors.append(f"step {step_id} has malformed generated input ref")
                    checks["generated_input_dag_pass"] = False
                    continue
                producer = ref.get("producer_step")
                path_value = safe_relative(ref.get("path"))
                pair = (producer, path_value)
                if (
                    producer not in STEP_IDS
                    or STEP_IDS.index(producer) >= ordinal
                    or path_value is None
                    or declared_outputs.get(path_value) != producer
                    or pair in local_refs
                ):
                    errors.append(f"step {step_id} has invalid or forward generated-input reference")
                    checks["generated_input_dag_pass"] = False
                    continue
                local_refs.add(pair)
        command_hash = step.get("command_sha256")
        hash_subject = dict(step)
        hash_subject.pop("command_sha256", None)
        expected_hash = sha256_bytes(canonical_json(hash_subject))
        if command_hash != expected_hash:
            errors.append(f"step {step_id} command digest mismatch")
            checks["command_digest_pass"] = False

    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "verified": not errors,
        "errors": errors,
        "manifest_sha256": sha256_bytes(raw),
        "checks": checks,
        "claim_authority": "none",
        "execution_authority": False,
        "promotion_authority": False,
    }
    args.verification.parent.mkdir(parents=True, exist_ok=True)
    with args.verification.open("xb") as stream:
        stream.write(pretty_json(output))
        stream.flush()
        os.fsync(stream.fileno())
    return 0 if output["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
