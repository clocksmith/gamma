#!/usr/bin/env python3
"""Independently rehash and compare two SAFE-MIX proof builds."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any


SCHEMA = "gamma.enwiki9.safe-mix-independent-build-verification.v1"
CANDIDATE_ID = "gamma_safe_mix_v1"
ARTIFACTS = {
    "safe_mix_object": "safe-mix.o",
    "trace_object": "safe-mix-trace.o",
    "negative_controls_object": "safe-mix-negative-controls.o",
    "native_trace_binary": "safe-mix-trace",
    "negative_controls_binary": "safe-mix-negative-controls",
}


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


def existing_directory(path: Path, label: str) -> Path:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise RuntimeError(f"{label} must be a non-symlink directory")
    return path.resolve(strict=True)


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def open_parent(path: Path) -> int:
    if path.name in {"", ".", ".."}:
        raise ValueError("output must name one leaf")
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
                    raise OSError("short verification write")
                cursor += written
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.fsync(parent)
    finally:
        os.close(parent)


def load_build(receipt_path: Path, root: Path, role: str) -> tuple[dict[str, Any], dict[str, str]]:
    receipt = json.loads(receipt_path.read_text(encoding="ascii"))
    if (
        receipt.get("schema") != "gamma.enwiki9.safe-mix-build-receipt.v1"
        or receipt.get("candidate_id") != CANDIDATE_ID
        or receipt.get("build_role") != role
        or receipt.get("terminal_pass") is not True
        or receipt.get("all_commands_pass") is not True
        or receipt.get("live_path_absent_pass") is not True
        or receipt.get("execution_authority") is not False
        or receipt.get("archive_authority") is not False
    ):
        raise RuntimeError(f"build {role} receipt is not terminal-pass evidence")
    hashes: dict[str, str] = {}
    for name, filename in ARTIFACTS.items():
        value = receipt.get("artifacts", {}).get(name)
        path = existing_regular(root / filename, f"build {role} artifact {name}")
        digest = sha256(path)
        if (
            not isinstance(value, dict)
            or value.get("path") != f"{{BUILD_ROOT}}/{filename}"
            or value.get("bytes") != path.stat().st_size
            or value.get("sha256") != digest
        ):
            raise RuntimeError(f"build {role} artifact receipt mismatch for {name}")
        hashes[name] = digest
    return receipt, hashes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-a-receipt", type=Path, required=True)
    parser.add_argument("--build-a-root", type=Path, required=True)
    parser.add_argument("--build-b-receipt", type=Path, required=True)
    parser.add_argument("--build-b-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    receipt_a_path = existing_regular(args.build_a_receipt, "build A receipt")
    receipt_b_path = existing_regular(args.build_b_receipt, "build B receipt")
    root_a = existing_directory(args.build_a_root, "build A root")
    root_b = existing_directory(args.build_b_root, "build B root")
    if root_a == root_b or is_within(root_a, root_b) or is_within(root_b, root_a):
        raise RuntimeError("independent build roots must be disjoint")
    verifier = existing_regular(Path(__file__), "independent-build verifier")
    python = existing_regular(
        Path(sys.executable).resolve(strict=True),
        "resolved Python executable",
    )
    receipt_a, hashes_a = load_build(receipt_a_path, root_a, "A")
    receipt_b, hashes_b = load_build(receipt_b_path, root_b, "B")

    input_lock_identity = receipt_a.get("input_lock") == receipt_b.get("input_lock")
    environment_identity = receipt_a.get("environment_sha256") == receipt_b.get("environment_sha256")
    source_identity = receipt_a.get("sources") == receipt_b.get("sources")
    probe_identity = receipt_a.get("tool_probes") == receipt_b.get("tool_probes")
    command_identity = receipt_a.get("commands") == receipt_b.get("commands")
    artifact_identity = {name: hashes_a[name] == hashes_b[name] for name in ARTIFACTS}
    terminal = all((
        input_lock_identity,
        environment_identity,
        source_identity,
        probe_identity,
        command_identity,
        all(artifact_identity.values()),
    ))
    if not terminal:
        raise RuntimeError("independent SAFE-MIX builds are not byte-identical")

    output = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "build_a_receipt_sha256": sha256(receipt_a_path),
        "build_b_receipt_sha256": sha256(receipt_b_path),
        "verifier_sha256": sha256(verifier),
        "python_executable_sha256": sha256(python),
        "input_lock_identity_pass": input_lock_identity,
        "environment_identity_pass": environment_identity,
        "source_identity_pass": source_identity,
        "tool_probe_identity_pass": probe_identity,
        "command_receipt_identity_pass": command_identity,
        "artifact_identity": artifact_identity,
        "all_artifacts_byte_identity_pass": all(artifact_identity.values()),
        "terminal_pass": terminal,
        "execution_authority": False,
        "archive_authority": False,
        "score_credit_bytes": 0,
    }
    write_new(args.receipt, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
