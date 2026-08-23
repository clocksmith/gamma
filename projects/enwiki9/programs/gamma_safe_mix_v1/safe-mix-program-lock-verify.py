#!/usr/bin/env python3
"""Verify a materialized SAFE-MIX program lock against current files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any


SCHEMA = "gamma.enwiki9.safe-mix-program-lock-verification.v1"
CANDIDATE_ID = "gamma_safe_mix_v1"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def existing_regular(path: Path, label: str) -> Path:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"{label} must be a non-symlink regular file")
    return path.resolve(strict=True)


def open_parent(path: Path) -> int:
    if path.name in {"", ".", ".."}:
        raise ValueError("output must name one new verification file")
    parts = path.parent.parts
    if path.is_absolute():
        directory = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        parts = parts[1:]
    else:
        directory = os.open(".", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in parts:
            if part in {"", "."}:
                continue
            if part == "..":
                raise ValueError("parent traversal is forbidden")
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=directory,
            )
            os.close(directory)
            directory = child
        return directory
    except BaseException:
        os.close(directory)
        raise


def write_new(path: Path, value: dict[str, Any]) -> None:
    data = canonical(value)
    parent = open_parent(path)
    try:
        descriptor = os.open(
            path.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent,
        )
        try:
            cursor = 0
            while cursor < len(data):
                written = os.write(descriptor, data[cursor:])
                if written <= 0:
                    raise OSError("short program-lock verification write")
                cursor += written
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.fsync(parent)
    finally:
        os.close(parent)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program-lock", type=Path, required=True)
    parser.add_argument("--pending-lock", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    lock_path = existing_regular(args.program_lock, "materialized program lock")
    pending_path = existing_regular(args.pending_lock, "pending program lock")
    verifier = existing_regular(Path(__file__).resolve(strict=True), "program-lock verifier")
    python = existing_regular(Path(sys.executable).resolve(strict=True), "resolved Python executable")
    lock = json.loads(lock_path.read_text(encoding="ascii"))
    pending = json.loads(pending_path.read_text(encoding="ascii"))
    if (
        lock.get("schema") != "gamma.enwiki9.safe-mix-program-lock.v1"
        or lock.get("candidate_id") != CANDIDATE_ID
        or lock.get("hash_status") != "content_addressed"
        or lock.get("pending_lock_sha256") != sha256(pending_path)
        or lock.get("all_files_regular_no_symlink_pass") is not True
        or lock.get("all_file_digests_materialized_pass") is not True
        or lock.get("execution_authority") is not False
        or lock.get("archive_authority") is not False
    ):
        raise RuntimeError("materialized program-lock identity or terminal state is invalid")
    if (
        pending.get("candidate_id") != CANDIDATE_ID
        or not isinstance(pending.get("files"), list)
        or not isinstance(lock.get("files"), list)
        or lock.get("declared_file_count") != len(lock["files"])
        or len(pending["files"]) != len(lock["files"])
    ):
        raise RuntimeError("pending/materialized declaration cardinality mismatch")

    pending_names = []
    locked_names = []
    current_manifest = []
    for pending_entry, locked_entry in zip(pending["files"], lock["files"]):
        if (
            not isinstance(pending_entry, dict)
            or set(pending_entry) != {"path", "sha256"}
            or pending_entry.get("sha256") is not None
            or not isinstance(locked_entry, dict)
            or set(locked_entry) != {"path", "sha256"}
            or pending_entry.get("path") != locked_entry.get("path")
        ):
            raise RuntimeError("pending/materialized file declaration mismatch")
        name = locked_entry["path"]
        if name in locked_names:
            raise RuntimeError("program-lock file path is duplicated")
        selected = existing_regular(lock_path.parent / name, f"locked file {name}")
        digest = sha256(selected)
        if digest != locked_entry.get("sha256"):
            raise RuntimeError(f"program lock is stale for {name}")
        pending_names.append(pending_entry["path"])
        locked_names.append(name)
        current_manifest.append({"path": name, "sha256": digest})
    if lock_path.name in locked_names:
        raise RuntimeError("materialized lock may not hash itself")
    materializer_entry = next(
        (entry for entry in current_manifest if entry["path"] == "safe-mix-program-lock-materialize.py"),
        None,
    )
    if materializer_entry is None or materializer_entry["sha256"] != lock.get("materializer_sha256"):
        raise RuntimeError("materializer identity mismatch")

    output = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "program_lock_sha256": sha256(lock_path),
        "pending_lock_sha256": sha256(pending_path),
        "verifier_sha256": sha256(verifier),
        "python_executable_sha256": sha256(python),
        "declared_file_count": len(current_manifest),
        "current_manifest_sha256": hashlib.sha256(canonical(current_manifest)).hexdigest(),
        "pending_declaration_identity_pass": pending_names == locked_names,
        "all_current_file_digests_pass": True,
        "non_circular_lock_pass": True,
        "materializer_identity_pass": True,
        "terminal_pass": True,
        "execution_authority": False,
        "archive_authority": False,
        "score_credit_bytes": 0,
    }
    write_new(args.receipt, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
