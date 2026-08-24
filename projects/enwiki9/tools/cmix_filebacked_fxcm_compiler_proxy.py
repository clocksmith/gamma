#!/usr/bin/env python3
"""Execute and trace one real compiler invocation for q1 build evidence."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any


CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-compiler-invocation.v1"
REQUIRED_ENVIRONMENT = {
    "GAMMA_FXCM_REAL_COMPILER",
    "GAMMA_FXCM_REAL_LINKER",
    "GAMMA_FXCM_COMPILER_TRACE_DIR",
    "GAMMA_FXCM_SOURCE_ROOT",
    "GAMMA_FXCM_BUILD_ROOT",
    "GAMMA_FXCM_BUILD_ROLE",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def existing_regular(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise RuntimeError(f"{label} must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current = current / component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label} has symlink component: {current}")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label} must be a single-link regular file")
    return path.resolve(strict=True)


def existing_directory(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise RuntimeError(f"{label} must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current = current / component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"{label} has an invalid component: {current}")
    return path.resolve(strict=True)


def is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def normalize(
    value: str,
    source_root: Path,
    build_root: Path,
    compiler: Path,
    linker: Path,
) -> str:
    replacements = (
        (str(source_root), "{SOURCE_ROOT}"),
        (str(build_root), "{BUILD_ROOT}"),
        (str(compiler), "{REAL_COMPILER}"),
        (str(linker), "{REAL_LINKER}"),
    )
    result = value
    for prefix, token in replacements:
        if result == prefix:
            return token
        if result.startswith(prefix + "/"):
            return token + result[len(prefix):]
        for attached in ("-I", "-L"):
            attached_prefix = attached + prefix
            if result == attached_prefix:
                return attached + token
            if result.startswith(attached_prefix + "/"):
                return attached + token + result[len(attached_prefix):]
        option, separator, operand = result.partition("=")
        if separator:
            if operand == prefix:
                return option + separator + token
            if operand.startswith(prefix + "/"):
                return option + separator + token + operand[len(prefix):]
    return result


def next_sequence(trace_directory: Path) -> int:
    sequence_path = trace_directory / ".sequence"
    descriptor = os.open(
        sequence_path,
        os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise RuntimeError("compiler trace sequence must be a single-link regular file")
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        raw = os.read(descriptor, 64)
        previous = 0 if not raw else int(raw.decode("ascii"))
        sequence = previous + 1
        encoded = str(sequence).encode("ascii")
        os.lseek(descriptor, 0, os.SEEK_SET)
        os.ftruncate(descriptor, 0)
        if os.write(descriptor, encoded) != len(encoded):
            raise OSError("short compiler trace sequence write")
        os.fsync(descriptor)
        return sequence
    finally:
        os.close(descriptor)


def write_record(trace_directory: Path, sequence: int, value: dict[str, Any]) -> None:
    path = trace_directory / f"invocation-{sequence:08d}.json"
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        if os.write(descriptor, data) != len(data):
            raise OSError("short compiler invocation trace write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    directory = os.open(trace_directory, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def main() -> int:
    missing = sorted(name for name in REQUIRED_ENVIRONMENT if name not in os.environ)
    if missing:
        raise RuntimeError(f"missing compiler proxy environment: {missing}")
    role = os.environ["GAMMA_FXCM_BUILD_ROLE"]
    if role not in {"release", "harness"}:
        raise RuntimeError("invalid compiler proxy build role")
    compiler = existing_regular(Path(os.environ["GAMMA_FXCM_REAL_COMPILER"]), "real compiler")
    linker = existing_regular(Path(os.environ["GAMMA_FXCM_REAL_LINKER"]), "real linker")
    proxy = existing_regular(Path(__file__).resolve(strict=True), "compiler proxy")
    python_executable = existing_regular(
        Path(sys.executable).resolve(strict=True),
        "Python executable",
    )
    if compiler == proxy:
        raise RuntimeError("compiler proxy recursion is forbidden")
    source_root = existing_directory(Path(os.environ["GAMMA_FXCM_SOURCE_ROOT"]), "source root")
    build_root = existing_directory(Path(os.environ["GAMMA_FXCM_BUILD_ROOT"]), "build root")
    trace_directory = existing_directory(
        Path(os.environ["GAMMA_FXCM_COMPILER_TRACE_DIR"]),
        "compiler trace directory",
    )
    if not is_within(trace_directory, build_root):
        raise RuntimeError("compiler trace directory must be inside the build root")
    sequence = next_sequence(trace_directory)
    argv = [str(compiler), *sys.argv[1:]]
    response_file_absent_pass = not any(argument.startswith("@") for argument in sys.argv[1:])
    if response_file_absent_pass:
        try:
            completed = subprocess.run(argv, check=False)
            return_code = completed.returncode
        except OSError as error:
            os.write(2, f"compiler proxy execution failure: {error}\n".encode("utf-8", "replace"))
            return_code = 127
    else:
        os.write(2, b"compiler proxy rejected response-file argument\n")
        return_code = 64
    normalized_argv = [
        normalize(item, source_root, build_root, compiler, linker)
        for item in argv
    ]
    definitions = sorted(item for item in normalized_argv[1:] if item.startswith("-D"))
    record = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "sequence": sequence,
        "build_role": role,
        "proxy_sha256": sha256_file(proxy),
        "python_executable_sha256": sha256_file(python_executable),
        "compiler_sha256": sha256_file(compiler),
        "linker_sha256": sha256_file(linker),
        "cwd": normalize(
            str(Path.cwd().resolve(strict=True)),
            source_root,
            build_root,
            compiler,
            linker,
        ),
        "argv": normalized_argv,
        "definitions": definitions,
        "compile_event": "-c" in sys.argv[1:],
        "response_file_absent_pass": response_file_absent_pass,
        "return_code": return_code,
    }
    write_record(trace_directory, sequence, record)
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
