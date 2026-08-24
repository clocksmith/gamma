#!/usr/bin/env python3
"""Freeze the exact q1 source implementation and its proof harnesses."""

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
PENDING_SCHEMA = "gamma.enwiki9.pending-program-lock.v1"
OUTPUT_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-program-lock.v1"
REQUIRED_BASENAMES = {
    "gamma-filebacked-fxcm.h",
    "integration-v2.patch",
    "apply-filebacked-fxcm-v2.sh",
    "allocator-negative-control-harness.cpp",
    "release-build-command.json",
    "harness-build-command.json",
    "cmix_filebacked_fxcm_source_materialize.py",
    "cmix_filebacked_fxcm_build_stage.py",
    "cmix_filebacked_fxcm_build_capture.py",
    "cmix_filebacked_fxcm_compiler_proxy.py",
    "cmix_filebacked_fxcm_program_lock_materialize.py",
    "cmix_filebacked_fxcm_program_lock_verify.py",
}


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


def safe_declared_path(value: Any, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or not value.isascii():
        raise RuntimeError(f"{label} must be nonempty ASCII")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", "."} for part in path.parts):
        raise RuntimeError(f"{label} is not a normalized relative path")
    return path


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(PROJECT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    parent = path.parent.resolve(strict=True)
    if not parent.is_dir() or parent.is_symlink():
        raise RuntimeError("program-lock output parent is invalid")
    data = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        offset = 0
        while offset < len(data):
            written = os.write(descriptor, data[offset:])
            if written <= 0:
                raise OSError("short program-lock write")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pending", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pending_path = regular(args.pending, "pending declaration")
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    if (
        not isinstance(pending, dict)
        or pending.get("schema") != PENDING_SCHEMA
        or pending.get("candidate_id") != CANDIDATE_ID
        or pending.get("execution_authority") is not False
    ):
        raise RuntimeError("pending declaration identity mismatch")
    declared = pending.get("files")
    if not isinstance(declared, list) or not declared:
        raise RuntimeError("pending declaration has no files")
    pending_dir = pending_path.parent
    paths: list[Path] = []
    seen: set[Path] = set()
    for index, record in enumerate(declared):
        if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
            raise RuntimeError(f"pending file {index} has an invalid field set")
        if record["sha256"] is not None:
            raise RuntimeError(f"pending file {index} is unexpectedly pre-hashed")
        relative = safe_declared_path(record["path"], f"pending file {index}")
        path = regular(pending_dir.joinpath(*relative.parts), f"pending file {index}")
        try:
            path.relative_to(PROJECT)
        except ValueError as error:
            raise RuntimeError(f"pending file {index} escapes the project") from error
        if path in seen:
            raise RuntimeError(f"pending file {index} is duplicated")
        seen.add(path)
        paths.append(path)
    missing = sorted(REQUIRED_BASENAMES - {path.name for path in paths})
    if missing:
        raise RuntimeError(f"pending declaration omits required files: {missing}")
    files = [artifact(path) for path in paths]
    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "operational_status": "frozen",
        "pending_declaration": artifact(pending_path),
        "files": files,
        "file_manifest_sha256": hashlib.sha256(canonical(files)).hexdigest(),
        "source_implementation_frozen": True,
        "claim_authority": "source_implementation_only",
        "execution_authority": False,
    }
    write_new(args.output, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
