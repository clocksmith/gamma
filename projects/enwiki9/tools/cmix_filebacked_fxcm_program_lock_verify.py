#!/usr/bin/env python3
"""Independently verify the q1 source-program lock against live files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
LOCK_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-program-lock.v1"
OUTPUT_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-program-lock-verification.v1"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def regular(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label} has a symlink component: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label} must be a single-link regular file")
    return absolute.resolve(strict=True)


def safe_project_file(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value or not value.isascii():
        raise RuntimeError(f"{label} path is invalid")
    relative = PurePosixPath(value)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise RuntimeError(f"{label} path is unsafe")
    return regular(PROJECT.joinpath(*relative.parts), label)


def write_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    path.parent.resolve(strict=True)
    data = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        if os.write(descriptor, data) != len(data):
            raise OSError("short program-lock verification write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program-lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock_path = regular(args.program_lock, "program lock")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    checks = {
        "identity_pass": True,
        "pending_identity_pass": True,
        "file_set_pass": True,
        "file_identity_pass": True,
        "manifest_digest_pass": True,
    }
    if (
        not isinstance(lock, dict)
        or lock.get("schema") != LOCK_SCHEMA
        or lock.get("candidate_id") != CANDIDATE_ID
        or lock.get("operational_status") != "frozen"
        or lock.get("source_implementation_frozen") is not True
        or lock.get("claim_authority") != "source_implementation_only"
        or lock.get("execution_authority") is not False
    ):
        errors.append("program-lock identity or governance mismatch")
        checks["identity_pass"] = False
    pending = lock.get("pending_declaration")
    pending_value: dict[str, Any] = {}
    try:
        if not isinstance(pending, dict) or set(pending) != {"path", "bytes", "sha256"}:
            raise RuntimeError("pending record has an invalid field set")
        pending_path = safe_project_file(pending["path"], "pending declaration")
        if pending_path.stat().st_size != pending["bytes"] or sha256_file(pending_path) != pending["sha256"]:
            raise RuntimeError("pending declaration identity mismatch")
        pending_value = json.loads(pending_path.read_text(encoding="utf-8"))
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        errors.append(str(error))
        checks["pending_identity_pass"] = False
    expected_paths: list[str] = []
    if pending_value:
        program_dir = pending_path.parent
        for index, record in enumerate(pending_value.get("files", [])):
            try:
                relative = PurePosixPath(record["path"])
                resolved = program_dir.joinpath(*relative.parts).resolve(strict=True)
                expected_paths.append(resolved.relative_to(PROJECT).as_posix())
            except (KeyError, OSError, ValueError, TypeError):
                errors.append(f"pending file {index} cannot be resolved")
                checks["file_set_pass"] = False
    files = lock.get("files")
    observed_paths: list[str] = []
    if not isinstance(files, list) or not files:
        errors.append("program-lock file manifest is empty")
        checks["file_set_pass"] = False
        files = []
    for index, record in enumerate(files):
        try:
            if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
                raise RuntimeError("record has an invalid field set")
            path = safe_project_file(record["path"], f"program-lock file {index}")
            observed_paths.append(record["path"])
            if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
                raise RuntimeError("identity mismatch")
        except (OSError, RuntimeError) as error:
            errors.append(f"program-lock file {index}: {error}")
            checks["file_identity_pass"] = False
    if observed_paths != expected_paths or len(observed_paths) != len(set(observed_paths)):
        errors.append("program-lock file set or ordering differs from the pending declaration")
        checks["file_set_pass"] = False
    if lock.get("file_manifest_sha256") != hashlib.sha256(canonical(files)).hexdigest():
        errors.append("program-lock file-manifest digest mismatch")
        checks["manifest_digest_pass"] = False
    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "verified": not errors,
        "errors": errors,
        "program_lock_sha256": sha256_file(lock_path),
        "checks": checks,
        "claim_authority": "source_implementation_only",
        "execution_authority": False,
    }
    write_new(args.output, output)
    return 0 if output["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
