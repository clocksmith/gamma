#!/usr/bin/env python3
"""Capture one frozen SAFE-MIX proof build; never grants archive authority."""

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


SCHEMA = "gamma.enwiki9.safe-mix-build-receipt.v1"
CANDIDATE_ID = "gamma_safe_mix_v1"
SOURCE_FILES = (
    "safe-mix.h",
    "safe-mix.cpp",
    "safe-mix-trace.cpp",
    "safe-mix-negative-controls.cpp",
)
ARTIFACTS = {
    "safe_mix_object": "safe-mix.o",
    "trace_object": "safe-mix-trace.o",
    "negative_controls_object": "safe-mix-negative-controls.o",
    "native_trace_binary": "safe-mix-trace",
    "negative_controls_binary": "safe-mix-negative-controls",
}
PLACEHOLDERS = ("{COMPILER}", "{LINKER}", "{SOURCE_ROOT}", "{BUILD_ROOT}")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def existing_regular(path: Path, label: str, executable: bool = False) -> Path:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"{label} must be a non-symlink regular file")
    resolved = path.resolve(strict=True)
    if executable and not os.access(resolved, os.X_OK):
        raise RuntimeError(f"{label} is not executable")
    return resolved


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
                    raise OSError("short receipt write")
                cursor += written
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.fsync(parent)
    finally:
        os.close(parent)


def run(command: list[str], stdout_path: Path, stderr_path: Path, environment: dict[str, str]) -> int:
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        completed = subprocess.run(
            command,
            cwd=stdout_path.parent,
            env=environment,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
        stdout.flush()
        stderr.flush()
        os.fsync(stdout.fileno())
        os.fsync(stderr.fileno())
    return completed.returncode


def artifact(path: Path, normalized_path: str) -> dict[str, Any]:
    regular = existing_regular(path, normalized_path)
    return {"path": normalized_path, "bytes": regular.stat().st_size, "sha256": sha256(regular)}


def substitute(argument: str, replacements: dict[str, str]) -> str:
    output = argument
    for placeholder, value in replacements.items():
        output = output.replace(placeholder, value)
    if any(placeholder in output for placeholder in PLACEHOLDERS):
        raise RuntimeError(f"unresolved build placeholder in {argument!r}")
    return output


def require_program_lock(path: Path) -> dict[str, str]:
    value = json.loads(path.read_text(encoding="ascii"))
    if (
        value.get("schema") != "gamma.enwiki9.safe-mix-program-lock.v1"
        or value.get("candidate_id") != CANDIDATE_ID
        or value.get("operational_status") != "dormant_dependency"
        or value.get("hash_status") != "content_addressed"
        or not isinstance(value.get("files"), list)
        or not value["files"]
        or value.get("declared_file_count") != len(value["files"])
        or value.get("all_files_regular_no_symlink_pass") is not True
        or value.get("all_file_digests_materialized_pass") is not True
        or value.get("execution_authority") is not False
        or value.get("archive_authority") is not False
        or value.get("score_credit_bytes") != 0
    ):
        raise RuntimeError("program lock is pending, foreign, or incomplete")
    observed: dict[str, str] = {}
    for entry in value["files"]:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"path", "sha256"}
            or not isinstance(entry["path"], str)
            or not isinstance(entry["sha256"], str)
            or len(entry["sha256"]) != 64
            or entry["path"] in observed
        ):
            raise RuntimeError("program lock file entry is invalid or duplicated")
        locked = existing_regular(path.parent / entry["path"], f"locked file {entry['path']}")
        if sha256(locked) != entry["sha256"]:
            raise RuntimeError(f"program lock digest mismatch for {entry['path']}")
        observed[entry["path"]] = entry["sha256"]
    if path.name in observed:
        raise RuntimeError("program lock may not hash itself")
    if (
        observed.get("program-lock.pending.json") != value.get("pending_lock_sha256")
        or observed.get("safe-mix-program-lock-materialize.py") != value.get("materializer_sha256")
    ):
        raise RuntimeError("program lock does not bind its pending declaration and materializer")
    for required in (
        *SOURCE_FILES,
        "program-lock.pending.json",
        "safe-mix-program-lock-materialize.py",
        "safe-mix-build-contract.json",
        "safe-mix-build-capture.py",
    ):
        if required not in observed:
            raise RuntimeError(f"program lock omits {required}")
    return observed


def contains_live_path(path: Path, needles: tuple[bytes, ...]) -> bool:
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            if any(needle and needle in block for needle in needles):
                return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--build-contract", type=Path, required=True)
    parser.add_argument("--program-lock", type=Path, required=True)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--linker", type=Path, required=True)
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--build-role", choices=("A", "B"), required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if active_lease(args.exclusive_lease):
        raise RuntimeError("active exclusive lease forbids SAFE-MIX build capture")

    source_root = existing_directory(args.source_root, "source root")
    contract_path = existing_regular(args.build_contract, "build contract")
    program_lock = existing_regular(args.program_lock, "program lock")
    compiler = existing_regular(args.compiler, "compiler", executable=True)
    linker = existing_regular(args.linker, "linker", executable=True)
    builder = existing_regular(Path(__file__), "builder")
    python = existing_regular(
        Path(sys.executable).resolve(strict=True),
        "resolved Python executable",
        executable=True,
    )
    locked_files = require_program_lock(program_lock)
    if (
        locked_files["safe-mix-build-contract.json"] != sha256(contract_path)
        or locked_files["safe-mix-build-capture.py"] != sha256(builder)
    ):
        raise RuntimeError("program lock does not bind the selected builder and contract")
    build_root = create_directory(args.build_root)
    if is_within(build_root, source_root) or is_within(source_root, build_root):
        raise RuntimeError("source and build roots must be disjoint")

    contract = json.loads(contract_path.read_text(encoding="ascii"))
    if (
        contract.get("schema") != "gamma.enwiki9.safe-mix-build-contract.v1"
        or contract.get("candidate_id") != CANDIDATE_ID
        or tuple(contract.get("source_files", [])) != SOURCE_FILES
        or not isinstance(contract.get("environment"), dict)
        or len(contract.get("commands", [])) != 5
        or contract.get("identity_probes") != {
            "compiler": ["{COMPILER}", "--version"],
            "linker": ["{LINKER}", "--version"],
        }
    ):
        raise RuntimeError("build contract identity or shape mismatch")
    environment = {str(key): str(value) for key, value in contract["environment"].items()}
    environment_sha256 = sha256_bytes(canonical(environment))
    replacements = {
        "{COMPILER}": str(compiler),
        "{LINKER}": str(linker),
        "{SOURCE_ROOT}": str(source_root),
        "{BUILD_ROOT}": str(build_root),
    }

    sources = []
    for name in SOURCE_FILES:
        path = existing_regular(source_root / name, f"source {name}")
        digest = sha256(path)
        if locked_files[name] != digest:
            raise RuntimeError(f"selected source root differs from the locked {name}")
        sources.append({"path": name, "bytes": path.stat().st_size, "sha256": digest})

    old_umask = os.umask(0o077)
    try:
        probes: dict[str, Any] = {}
        for name, tool in (("compiler", compiler), ("linker", linker)):
            normalized_command = contract["identity_probes"][name]
            command = [substitute(item, replacements) for item in normalized_command]
            stdout_path = build_root / f"{name}-identity.stdout"
            stderr_path = build_root / f"{name}-identity.stderr"
            return_code = run(command, stdout_path, stderr_path, environment)
            if return_code != 0:
                raise RuntimeError(f"{name} identity probe failed")
            probes[name] = {
                "command_sha256": sha256_bytes(canonical(normalized_command)),
                "return_code": return_code,
                "stdout_sha256": sha256(stdout_path),
                "stderr_sha256": sha256(stderr_path),
            }

        command_receipts = []
        for expected_sequence, command_specification in enumerate(contract["commands"], 1):
            if (
                not isinstance(command_specification, dict)
                or command_specification.get("sequence") != expected_sequence
                or command_specification.get("phase") not in {"compile", "link"}
                or not isinstance(command_specification.get("argv"), list)
                or not all(isinstance(item, str) for item in command_specification["argv"])
            ):
                raise RuntimeError(f"build command {expected_sequence} violates the contract shape")
            normalized_argv = command_specification["argv"]
            actual_argv = [substitute(item, replacements) for item in normalized_argv]
            stdout_path = build_root / f"command-{expected_sequence:02d}.stdout"
            stderr_path = build_root / f"command-{expected_sequence:02d}.stderr"
            return_code = run(actual_argv, stdout_path, stderr_path, environment)
            if return_code != 0:
                raise RuntimeError(f"build command {expected_sequence} failed")
            command_receipts.append({
                "sequence": expected_sequence,
                "phase": command_specification["phase"],
                "normalized_argv": normalized_argv,
                "command_sha256": sha256_bytes(canonical(normalized_argv)),
                "return_code": return_code,
                "stdout_sha256": sha256(stdout_path),
                "stderr_sha256": sha256(stderr_path),
            })
    finally:
        os.umask(old_umask)

    artifacts = {
        name: artifact(build_root / filename, f"{{BUILD_ROOT}}/{filename}")
        for name, filename in ARTIFACTS.items()
    }
    retained = [
        entry for entry in build_root.iterdir()
        if entry.is_file() and not entry.is_symlink()
    ]
    live_needles = (str(source_root).encode(), str(build_root).encode())
    live_path_absent = not any(contains_live_path(path, live_needles) for path in retained)
    if not live_path_absent:
        raise RuntimeError("build artifact or log retained a live source/build path")

    receipt = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "build_id": args.build_id,
        "build_role": args.build_role,
        "input_lock": {
            "build_contract_sha256": sha256(contract_path),
            "program_lock_sha256": sha256(program_lock),
            "builder_sha256": sha256(builder),
            "python_executable_sha256": sha256(python),
            "compiler_sha256": sha256(compiler),
            "linker_sha256": sha256(linker),
        },
        "environment_sha256": environment_sha256,
        "tool_probes": probes,
        "sources": sources,
        "commands": command_receipts,
        "artifacts": artifacts,
        "exclusive_lease_absent_pass": True,
        "all_commands_pass": True,
        "live_path_absent_pass": True,
        "terminal_pass": True,
        "execution_authority": False,
        "archive_authority": False,
        "score_credit_bytes": 0,
    }
    write_new(args.receipt, receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
