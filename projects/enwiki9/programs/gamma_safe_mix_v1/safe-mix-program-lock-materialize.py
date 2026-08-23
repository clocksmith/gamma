#!/usr/bin/env python3
"""Materialize a non-circular content-addressed SAFE-MIX program lock."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any


SCHEMA = "gamma.enwiki9.safe-mix-program-lock.v1"
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
        raise ValueError("output must name one new lock file")
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
                    raise OSError("short program-lock write")
                cursor += written
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.fsync(parent)
    finally:
        os.close(parent)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pending-lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pending_path = existing_regular(args.pending_lock, "pending program lock")
    materializer = existing_regular(Path(__file__).resolve(strict=True), "program-lock materializer")
    if args.output.resolve(strict=False) == pending_path:
        raise RuntimeError("materialized output must not replace the pending declaration")
    pending = json.loads(pending_path.read_text(encoding="ascii"))
    if (
        pending.get("candidate_id") != CANDIDATE_ID
        or pending.get("hash_status") not in {"pending_materialization", "requires_static_patch_review_and_terminal_attribution"}
        or not isinstance(pending.get("files"), list)
        or not pending["files"]
    ):
        raise RuntimeError("pending program-lock identity or state is invalid")

    files: list[dict[str, Any]] = []
    names: set[str] = set()
    for entry in pending["files"]:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"path", "sha256"}
            or not isinstance(entry["path"], str)
            or entry["sha256"] is not None
            or entry["path"] in names
        ):
            raise RuntimeError("pending file declaration is malformed, prehashed, or duplicated")
        selected = existing_regular(
            pending_path.parent / entry["path"],
            f"declared program file {entry['path']}",
        )
        files.append({"path": entry["path"], "sha256": sha256(selected)})
        names.add(entry["path"])

    required = {
        "program-lock.pending.json",
        "safe-mix-program-lock-materialize.py",
        "../../contracts/research/v1/safe-mix-program-lock.schema.json",
    }
    if not required.issubset(names):
        raise RuntimeError("pending declaration omits lock materialization inputs")
    materializer_entry = next(
        item for item in files if item["path"] == "safe-mix-program-lock-materialize.py"
    )
    if materializer_entry["sha256"] != sha256(materializer):
        raise RuntimeError("pending declaration does not bind the selected materializer")

    output = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "operational_status": "dormant_dependency",
        "hash_status": "content_addressed",
        "pending_lock_sha256": sha256(pending_path),
        "materializer_sha256": sha256(materializer),
        "declared_file_count": len(files),
        "files": files,
        "all_files_regular_no_symlink_pass": True,
        "all_file_digests_materialized_pass": True,
        "execution_authority": False,
        "archive_authority": False,
        "score_credit_bytes": 0,
    }
    write_new(args.output, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
