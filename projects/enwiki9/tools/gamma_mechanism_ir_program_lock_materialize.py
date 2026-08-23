#!/usr/bin/env python3
"""Materialize the exact source closure for Gamma Mechanism IR v3."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any


OUTPUT_SCHEMA = "gamma.enwiki9.gamma-mechanism-ir-program-lock.v1"


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    metadata = absolute.stat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise SystemExit(f"{label}: expected directory")
    return absolute.resolve(strict=True)


def require_clear_lease(path: Path) -> None:
    lease = json.loads(regular_file(path, "exclusive lease").read_text(encoding="utf-8"))
    if not isinstance(lease, dict) or lease.get("active") is not False:
        raise SystemExit("exclusive lease is active or lacks an explicit inactive decision")


def safe_relative(value: Any) -> str:
    if not isinstance(value, str) or not value or not value.isascii():
        raise SystemExit("source path must be nonempty ASCII")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise SystemExit(f"unsafe source path: {value}")
    return path.as_posix()


def set_hash(files: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for value in sorted(files, key=lambda item: item["path"]):
        digest.update(value["path"].encode("ascii"))
        digest.update(b"\0")
        digest.update(str(value["bytes"]).encode("ascii"))
        digest.update(b"\0")
        digest.update(value["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require_clear_lease(args.exclusive_lease)
    root = regular_directory(args.root, "root")
    contract = regular_file(args.contract, "source contract")
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit("output already exists")
    raw_contract = contract.read_bytes()
    document = json.loads(raw_contract.decode("utf-8"))
    if not isinstance(document, dict) or document.get("program_id") != "gamma_mechanism_ir_v3":
        raise SystemExit("unexpected source contract")
    values = document.get("files")
    if not isinstance(values, list):
        raise SystemExit("source contract files must be an array")
    paths = [safe_relative(value) for value in values]
    if len(set(paths)) != len(paths) or paths != sorted(paths):
        raise SystemExit("source paths must be unique and sorted")
    files: list[dict[str, Any]] = []
    for relative in paths:
        source = regular_file(root / relative, f"source {relative}")
        try:
            source.relative_to(root)
        except ValueError as exc:
            raise SystemExit(f"source escapes root: {relative}") from exc
        files.append({"path": relative, "bytes": source.stat().st_size, "sha256": sha256_file(source)})
    output = {
        "schema": OUTPUT_SCHEMA,
        "program_id": "gamma_mechanism_ir_v3",
        "source_contract": {
            "path": os.fspath(args.contract),
            "bytes": len(raw_contract),
            "sha256": hashlib.sha256(raw_contract).hexdigest(),
        },
        "files": files,
        "artifact_set_sha256": set_hash(files),
        "claim_authority": "none",
        "execution_authority": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(json_bytes(output))
        stream.flush()
        os.fsync(stream.fileno())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
