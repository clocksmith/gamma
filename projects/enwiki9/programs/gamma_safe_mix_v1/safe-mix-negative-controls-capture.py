#!/usr/bin/env python3
"""Bind one SAFE-MIX transactional-control execution to its build chain."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


SCHEMA = "gamma.enwiki9.safe-mix-negative-controls-execution-receipt.v1"
CANDIDATE_ID = "gamma_safe_mix_v1"
FROZEN_ENVIRONMENT = {"LANG": "C", "LC_ALL": "C", "TZ": "UTC"}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def existing_regular(path: Path, label: str, executable: bool = False) -> Path:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"{label} must be a non-symlink regular file")
    resolved = path.resolve(strict=True)
    if executable and not os.access(resolved, os.X_OK):
        raise RuntimeError(f"{label} is not executable")
    return resolved


def active_lease(path: Path) -> bool:
    if not path.exists() and not path.is_symlink():
        return False
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError("exclusive lease must be a non-symlink regular file")
    value = json.loads(path.read_text(encoding="ascii"))
    pid = value.get("pid")
    if value.get("active") is not True or not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def open_parent(path: Path) -> int:
    if path.name in {"", ".", ".."}:
        raise ValueError("output must name one new file")
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


def create_directory(path: Path) -> Path:
    parent = open_parent(path)
    try:
        os.mkdir(path.name, mode=0o700, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)
    return path.resolve(strict=True)


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
                    raise OSError("short execution-receipt write")
                cursor += written
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.fsync(parent)
    finally:
        os.close(parent)


def require_subject(value: Any) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or value.get("schema") != "gamma.enwiki9.safe-mix-negative-controls-receipt.v1"
        or value.get("candidate_id") != CANDIDATE_ID
        or value.get("all_controls_pass") is not True
        or value.get("pending_state_digest_pass") is not True
        or value.get("identity_control_pass") is not True
        or value.get("execution_authority") is not False
        or value.get("archive_authority") is not False
        or value.get("score_credit_bytes") != 0
    ):
        raise RuntimeError("native transactional-control subject is not terminal-pass evidence")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--build-receipt", type=Path, required=True)
    parser.add_argument("--independent-build-verification", type=Path, required=True)
    parser.add_argument("--program-lock", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if active_lease(args.exclusive_lease):
        raise RuntimeError("active exclusive lease forbids transactional controls")
    binary = existing_regular(args.binary, "negative-controls binary", executable=True)
    build_receipt_path = existing_regular(args.build_receipt, "build receipt")
    verification_path = existing_regular(
        args.independent_build_verification, "independent-build verification"
    )
    program_lock = existing_regular(args.program_lock, "program lock")
    capture = existing_regular(Path(__file__).resolve(strict=True), "execution capture")
    python = existing_regular(Path(sys.executable).resolve(strict=True), "resolved Python executable")
    build = json.loads(build_receipt_path.read_text(encoding="ascii"))
    verification = json.loads(verification_path.read_text(encoding="ascii"))
    locked = json.loads(program_lock.read_text(encoding="ascii"))
    binary_artifact = build.get("artifacts", {}).get("negative_controls_binary", {})
    if (
        build.get("schema") != "gamma.enwiki9.safe-mix-build-receipt.v1"
        or build.get("candidate_id") != CANDIDATE_ID
        or build.get("terminal_pass") is not True
        or build.get("input_lock", {}).get("program_lock_sha256") != sha256(program_lock)
        or binary_artifact.get("sha256") != sha256(binary)
        or binary_artifact.get("bytes") != binary.stat().st_size
    ):
        raise RuntimeError("selected binary is not bound by the terminal build receipt")
    if (
        verification.get("schema") != "gamma.enwiki9.safe-mix-independent-build-verification.v1"
        or verification.get("candidate_id") != CANDIDATE_ID
        or verification.get("terminal_pass") is not True
        or sha256(build_receipt_path) not in {
            verification.get("build_a_receipt_sha256"),
            verification.get("build_b_receipt_sha256"),
        }
        or verification.get("artifact_identity", {}).get("negative_controls_binary") is not True
    ):
        raise RuntimeError("independent-build verification does not authorize the selected binary")
    if (
        locked.get("schema") != "gamma.enwiki9.safe-mix-program-lock.v1"
        or locked.get("hash_status") != "content_addressed"
    ):
        raise RuntimeError("program lock is not materialized")

    root = create_directory(args.work_root)
    stdout_path = root / "subject.stdout"
    stderr_path = root / "subject.stderr"
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        completed = subprocess.run(
            [str(binary)],
            env=FROZEN_ENVIRONMENT,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
        stdout.flush()
        stderr.flush()
        os.fsync(stdout.fileno())
        os.fsync(stderr.fileno())
    if completed.returncode != 0:
        raise RuntimeError("native transactional controls failed")
    raw_subject = stdout_path.read_bytes()
    if not raw_subject.endswith(b"\n") or raw_subject.count(b"\n") != 1:
        raise RuntimeError("native subject must be exactly one newline-terminated JSON object")
    subject = require_subject(json.loads(raw_subject.decode("ascii")))
    normalized_command = ["{NEGATIVE_CONTROLS_BINARY}"]
    output = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "input_lock": {
            "program_lock_sha256": sha256(program_lock),
            "build_receipt_sha256": sha256(build_receipt_path),
            "independent_build_verification_sha256": sha256(verification_path),
            "binary_sha256": sha256(binary),
            "capture_sha256": sha256(capture),
            "python_executable_sha256": sha256(python),
        },
        "normalized_argv": normalized_command,
        "command_sha256": hashlib.sha256(canonical(normalized_command)).hexdigest(),
        "environment_sha256": hashlib.sha256(canonical(FROZEN_ENVIRONMENT)).hexdigest(),
        "return_code": completed.returncode,
        "stdout_bytes": stdout_path.stat().st_size,
        "stdout_sha256": sha256(stdout_path),
        "stderr_bytes": stderr_path.stat().st_size,
        "stderr_sha256": sha256(stderr_path),
        "subject_canonical_sha256": hashlib.sha256(canonical(subject)).hexdigest(),
        "subject": subject,
        "exclusive_lease_absent_pass": True,
        "terminal_pass": True,
        "execution_authority": False,
        "archive_authority": False,
        "score_credit_bytes": 0,
    }
    write_new(args.receipt, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
