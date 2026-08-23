#!/usr/bin/env python3
"""Materialize an explicit q1 source closure without recursive discovery."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat


CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-source-closure.v1"
ROLES = {"shared_allocator_header", "source", "build_input"}
MAX_ENTRIES = 16384
MAX_TOTAL_BYTES = 8 * 1024 * 1024 * 1024


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def existing_regular(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current = current / component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label} has symlink component: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label} must be a single-link regular file")
    return absolute.resolve(strict=True)


def existing_directory(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current = current / component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"{label} has an invalid component: {current}")
    return absolute.resolve(strict=True)


def normalized_relative(value: str, line_number: int) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise RuntimeError(f"entry list line {line_number} has an unsafe path")
    if path.as_posix() != value:
        raise RuntimeError(f"entry list line {line_number} is not normalized")
    return path


def write_new(path: Path, value: dict[str, object]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    output_parent = existing_directory(path.parent, "output parent")
    data = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        cursor = 0
        while cursor < len(data):
            written = os.write(descriptor, data[cursor:])
            if written <= 0:
                raise OSError("short source-closure write")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    directory = os.open(output_parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--entry-list", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_root = existing_directory(args.source_root, "source root")
    entry_list = existing_regular(args.entry_list, "entry list")
    raw = entry_list.read_bytes()
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise RuntimeError("entry list must be ASCII") from error
    entries: list[dict[str, object]] = []
    seen: set[str] = set()
    total_bytes = 0
    header_count = 0
    lines = text.splitlines()
    if not lines or len(lines) > MAX_ENTRIES:
        raise RuntimeError("entry list is empty or exceeds its entry ceiling")
    for line_number, line in enumerate(lines, 1):
        if not line or line.count("\t") != 1:
            raise RuntimeError(f"entry list line {line_number} must be ROLE<TAB>PATH")
        role, raw_path = line.split("\t")
        if role not in ROLES:
            raise RuntimeError(f"entry list line {line_number} has an invalid role")
        relative = normalized_relative(raw_path, line_number)
        normalized = relative.as_posix()
        if normalized in seen:
            raise RuntimeError(f"entry list line {line_number} duplicates {normalized}")
        seen.add(normalized)
        path = existing_regular(source_root.joinpath(*relative.parts), f"entry list line {line_number}")
        size = path.stat().st_size
        total_bytes += size
        if total_bytes > MAX_TOTAL_BYTES:
            raise RuntimeError("source closure exceeds its byte ceiling")
        if role == "shared_allocator_header":
            header_count += 1
        entries.append({
            "path": normalized,
            "bytes": size,
            "sha256": sha256_file(path),
            "role": role,
        })
    if header_count != 1:
        raise RuntimeError("source closure requires exactly one shared allocator header")
    metadata = source_root.stat()
    root_identity = {
        "path": str(source_root),
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
    }
    output = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "entry_list_sha256": hashlib.sha256(raw).hexdigest(),
        "source_root_identity_sha256": hashlib.sha256(canonical(root_identity)).hexdigest(),
        "entries": entries,
    }
    write_new(args.output, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
