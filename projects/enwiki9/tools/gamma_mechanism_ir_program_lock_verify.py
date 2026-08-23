#!/usr/bin/env python3
"""Independently verify a Gamma Mechanism IR v3 source program lock."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any


OUTPUT_SCHEMA = "gamma.enwiki9.gamma-mechanism-ir-program-lock-verification.v1"


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def safe_paths(values: Any) -> list[str]:
    if not isinstance(values, list):
        raise SystemExit("contract file list must be an array")
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value or not value.isascii():
            raise SystemExit("source path must be nonempty ASCII")
        path = PurePosixPath(value)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise SystemExit(f"unsafe source path: {value}")
        result.append(path.as_posix())
    if result != sorted(result) or len(result) != len(set(result)):
        raise SystemExit("source paths must be unique and sorted")
    return result


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
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    require_clear_lease(args.exclusive_lease)
    root = regular_directory(args.root, "root")
    contract = regular_file(args.contract, "source contract")
    lock = regular_file(args.lock, "program lock")
    if args.receipt.exists() or args.receipt.is_symlink():
        raise SystemExit("receipt already exists")
    raw_contract = contract.read_bytes()
    raw_lock = lock.read_bytes()
    contract_document = json.loads(raw_contract.decode("utf-8"))
    lock_document = json.loads(raw_lock.decode("utf-8"))
    if not isinstance(contract_document, dict) or not isinstance(lock_document, dict):
        raise SystemExit("contract and lock must be JSON objects")
    errors: list[str] = []
    checks = {
        "contract_identity_pass": True,
        "path_closure_pass": True,
        "file_identity_pass": True,
        "artifact_set_pass": True,
        "filesystem_safety_pass": True,
    }
    if lock_document.get("schema") != "gamma.enwiki9.gamma-mechanism-ir-program-lock.v1" or lock_document.get("program_id") != "gamma_mechanism_ir_v3":
        errors.append("unexpected program-lock identity")
        checks["contract_identity_pass"] = False
    declared_contract = lock_document.get("source_contract")
    if not isinstance(declared_contract, dict) or declared_contract.get("bytes") != len(raw_contract) or declared_contract.get("sha256") != sha256_bytes(raw_contract):
        errors.append("program lock does not bind the supplied source contract")
        checks["contract_identity_pass"] = False
    paths = safe_paths(contract_document.get("files"))
    declared_values = lock_document.get("files")
    declared: dict[str, dict[str, Any]] = {}
    if not isinstance(declared_values, list):
        errors.append("program lock files must be an array")
        checks["path_closure_pass"] = False
    else:
        for value in declared_values:
            if not isinstance(value, dict) or not isinstance(value.get("path"), str) or value["path"] in declared:
                errors.append("program lock contains malformed or duplicate file entries")
                checks["path_closure_pass"] = False
                continue
            declared[value["path"]] = value
    if set(declared) != set(paths):
        errors.append("program-lock path set differs from source contract")
        checks["path_closure_pass"] = False
    recomputed: list[dict[str, Any]] = []
    for relative in paths:
        try:
            source = regular_file(root / relative, f"source {relative}")
            source.relative_to(root)
        except (OSError, ValueError, SystemExit) as exc:
            errors.append(f"unsafe source {relative}: {exc}")
            checks["filesystem_safety_pass"] = False
            continue
        actual = {"path": relative, "bytes": source.stat().st_size, "sha256": sha256_file(source)}
        recomputed.append(actual)
        if declared.get(relative) != actual:
            errors.append(f"file identity mismatch: {relative}")
            checks["file_identity_pass"] = False
    recomputed_hash = set_hash(recomputed)
    if lock_document.get("artifact_set_sha256") != recomputed_hash:
        errors.append("artifact-set digest mismatch")
        checks["artifact_set_pass"] = False
    output = {
        "schema": OUTPUT_SCHEMA,
        "program_id": "gamma_mechanism_ir_v3",
        "verified": not errors,
        "errors": errors,
        "source_contract_sha256": sha256_bytes(raw_contract),
        "program_lock_sha256": sha256_bytes(raw_lock),
        "recomputed_artifact_set_sha256": recomputed_hash,
        "checks": checks,
        "claim_authority": "none",
        "execution_authority": False,
        "promotion_authority": False,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("xb") as stream:
        stream.write(json_bytes(output))
        stream.flush()
        os.fsync(stream.fileno())
    return 0 if output["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
