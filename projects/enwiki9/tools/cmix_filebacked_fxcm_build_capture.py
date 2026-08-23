#!/usr/bin/env python3
"""Capture one clean q1 build from a normalized command manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "projects/enwiki9"
LEASE = PROJECT / "operations/runtime/exclusive_full1g.json"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
COMMAND_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-build-command.v1"
CLOSURE_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-source-closure.v1"
RECEIPT_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-build-receipt.v1"
COMMAND_FIELDS = {
    "schema", "candidate_id", "build_role", "prepare_argv", "compile_argv",
    "link_argv", "compile_definitions", "environment", "compiler_trace_relative_path",
    "binary_relative_path",
}
TRACE_FIELDS = {
    "schema", "candidate_id", "sequence", "build_role", "proxy_sha256",
    "python_executable_sha256", "compiler_sha256", "cwd", "argv", "definitions",
    "linker_sha256",
    "compile_event", "response_file_absent_pass", "return_code",
}
TRACE_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-compiler-invocation.v1"
PRODUCTION_DEFINITION = "-DGAMMA_FILEBACKED_FXCM=1"
TESTING_DEFINITION = "-DGAMMA_FILEBACKED_FXCM_TESTING=1"
RESERVED_PROXY_ENVIRONMENT = {
    "GAMMA_FXCM_REAL_COMPILER",
    "GAMMA_FXCM_REAL_LINKER",
    "GAMMA_FXCM_COMPILER_TRACE_DIR",
    "GAMMA_FXCM_SOURCE_ROOT",
    "GAMMA_FXCM_BUILD_ROOT",
    "GAMMA_FXCM_BUILD_ROLE",
}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def proc_start_ticks(pid: int) -> int | None:
    try:
        return int(Path(f"/proc/{pid}/stat").read_text(encoding="ascii").split()[21])
    except (FileNotFoundError, IndexError, ValueError):
        return None


def require_lease_released() -> None:
    if not LEASE.is_file():
        return
    lease = json.loads(LEASE.read_text(encoding="utf-8"))
    for pid_key, start_key in (("pid", "proc_start_ticks"), ("codec_pid", "codec_proc_start_ticks")):
        pid = lease.get(pid_key)
        start = lease.get(start_key)
        if isinstance(pid, int) and Path(f"/proc/{pid}").exists():
            if start is None or proc_start_ticks(pid) == start:
                raise RuntimeError(f"exclusive lease remains active for {pid_key}={pid}")


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


def safe_relative(value: str, label: str) -> PurePosixPath:
    relative = PurePosixPath(value)
    if relative.is_absolute() or not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise RuntimeError(f"{label} must be a normalized relative path")
    return relative


def is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def load_json(path: Path, label: str) -> tuple[Path, dict[str, Any]]:
    resolved = existing_regular(path, label)
    value = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must contain an object")
    return resolved, value


def source_entries(source_root: Path, manifest: dict[str, Any], header_sha256: str) -> list[dict[str, Any]]:
    if set(manifest) != {"schema", "candidate_id", "entry_list_sha256", "source_root_identity_sha256", "entries"}:
        raise RuntimeError("source closure manifest has an invalid field set")
    if manifest["schema"] != CLOSURE_SCHEMA or manifest["candidate_id"] != CANDIDATE_ID:
        raise RuntimeError("source closure manifest identity mismatch")
    root_metadata = source_root.stat()
    observed_root_identity = sha256_bytes(canonical({
        "path": str(source_root),
        "device": root_metadata.st_dev,
        "inode": root_metadata.st_ino,
    }))
    if manifest["source_root_identity_sha256"] != observed_root_identity:
        raise RuntimeError("source closure manifest does not bind the supplied source root")
    entries = manifest["entries"]
    if not isinstance(entries, list) or not entries:
        raise RuntimeError("source closure is empty")
    observed_paths: set[str] = set()
    header_count = 0
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != {"path", "bytes", "sha256", "role"}:
            raise RuntimeError(f"source closure entry {index} is invalid")
        relative = safe_relative(entry["path"], f"source closure entry {index}")
        normalized = relative.as_posix()
        if normalized in observed_paths:
            raise RuntimeError(f"duplicate source closure path: {normalized}")
        observed_paths.add(normalized)
        path = existing_regular(source_root.joinpath(*relative.parts), f"source closure entry {index}")
        if path.stat().st_size != entry["bytes"] or sha256_file(path) != entry["sha256"]:
            raise RuntimeError(f"source closure entry {index} identity mismatch")
        if entry["role"] == "shared_allocator_header":
            header_count += 1
            if entry["sha256"] != header_sha256:
                raise RuntimeError("source closure allocator header digest mismatch")
    if header_count != 1:
        raise RuntimeError("source closure must contain exactly one allocator header")
    return entries


def expand(value: str, bindings: dict[str, str]) -> str:
    result = value
    for token, replacement in bindings.items():
        result = result.replace(token, replacement)
    if any(token in result for token in ("{SOURCE_ROOT}", "{BUILD_ROOT}", "{COMPILER}", "{COMPILER_PROXY}", "{LINKER}")):
        raise RuntimeError(f"unresolved build placeholder: {value}")
    return result


def run_stage(
    name: str,
    template: list[str] | None,
    bindings: dict[str, str],
    build_root: Path,
    environment: dict[str, str],
    log: bytearray,
) -> tuple[int, str | None]:
    if template is None:
        return 0, None
    argv = [expand(item, bindings) for item in template]
    executable_path = Path(argv[0])
    if not executable_path.is_absolute():
        raise RuntimeError(f"{name} executable must be an absolute path")
    executable = existing_regular(executable_path, f"{name} executable")
    executable_sha256 = sha256_file(executable)
    completed = subprocess.run(
        argv,
        cwd=build_root,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    header = canonical({
        "phase": name,
        "argv": argv,
        "return_code": completed.returncode,
        "stdout_bytes": len(completed.stdout),
        "stderr_bytes": len(completed.stderr),
    })
    log.extend(len(header).to_bytes(8, "little"))
    log.extend(header)
    log.extend(len(completed.stdout).to_bytes(8, "little"))
    log.extend(completed.stdout)
    log.extend(len(completed.stderr).to_bytes(8, "little"))
    log.extend(completed.stderr)
    return completed.returncode, executable_sha256


def compiler_trace_manifest(
    trace_directory: Path,
    role: str,
    proxy_sha256: str,
    compiler_sha256: str,
    linker_sha256: str,
    source_root: Path,
    build_root: Path,
) -> tuple[str, int, bool]:
    sequence_path = existing_regular(trace_directory / ".sequence", "compiler trace sequence")
    raw_sequence = sequence_path.read_text(encoding="ascii")
    if not raw_sequence or not raw_sequence.isdigit():
        raise RuntimeError("compiler trace sequence is invalid")
    count = int(raw_sequence)
    if count < 1 or count > 65536:
        raise RuntimeError("compiler invocation count is outside its ceiling")
    observed_names = {entry.name for entry in os.scandir(trace_directory)}
    expected_names = {".sequence"} | {
        f"invocation-{sequence:08d}.json" for sequence in range(1, count + 1)
    }
    if observed_names != expected_names:
        raise RuntimeError("compiler trace directory is incomplete or contains foreign entries")
    normalized_records: list[dict[str, Any]] = []
    compile_count = 0
    link_count = 0
    forbidden_roots = (str(source_root), str(build_root))
    for sequence in range(1, count + 1):
        path = existing_regular(
            trace_directory / f"invocation-{sequence:08d}.json",
            f"compiler invocation {sequence}",
        )
        value = json.loads(path.read_text(encoding="ascii"))
        if not isinstance(value, dict) or set(value) != TRACE_FIELDS:
            raise RuntimeError(f"compiler invocation {sequence} has an invalid field set")
        if (
            value["schema"] != TRACE_SCHEMA
            or value["candidate_id"] != CANDIDATE_ID
            or value["sequence"] != sequence
            or value["build_role"] != role
            or value["proxy_sha256"] != proxy_sha256
            or value["compiler_sha256"] != compiler_sha256
            or value["linker_sha256"] != linker_sha256
            or value["response_file_absent_pass"] is not True
            or value["return_code"] != 0
        ):
            raise RuntimeError(f"compiler invocation {sequence} failed identity or terminal checks")
        rendered = canonical(value).decode("ascii")
        if any(root in rendered for root in forbidden_roots):
            raise RuntimeError(f"compiler invocation {sequence} retained a live root path")
        argv = value["argv"]
        definitions = value["definitions"]
        if not isinstance(argv, list) or not argv or argv[0] != "{REAL_COMPILER}":
            raise RuntimeError(f"compiler invocation {sequence} has invalid argv")
        extracted = sorted(
            item for item in argv[1:]
            if isinstance(item, str) and item.startswith("-D")
        )
        if not isinstance(definitions, list) or definitions != extracted:
            raise RuntimeError(f"compiler invocation {sequence} definition extraction mismatch")
        if (
            "-D" in argv
            or any(isinstance(item, str) and item.startswith("@") for item in argv)
            or any(
                isinstance(item, str) and item.startswith("-UGAMMA_FILEBACKED_FXCM")
                for item in argv
            )
        ):
            raise RuntimeError(f"compiler invocation {sequence} contains hidden or negating definition syntax")
        if any(flag in argv[1:] for flag in ("-E", "-S", "-M", "-MM", "-fsyntax-only")):
            raise RuntimeError(f"compiler invocation {sequence} is not a production compile or link event")
        observed_compile_event = "-c" in argv[1:]
        if value["compile_event"] is not observed_compile_event:
            raise RuntimeError(f"compiler invocation {sequence} compile-event classification mismatch")
        if observed_compile_event:
            if argv[1:].count("-c") != 1:
                raise RuntimeError(f"compiler invocation {sequence} has an ambiguous compile boundary")
            compile_count += 1
            production_variants = [
                item for item in definitions
                if item.startswith("-DGAMMA_FILEBACKED_FXCM")
                and not item.startswith("-DGAMMA_FILEBACKED_FXCM_TESTING")
            ]
            testing_variants = [
                item for item in definitions
                if item.startswith("-DGAMMA_FILEBACKED_FXCM_TESTING")
            ]
            if production_variants != [PRODUCTION_DEFINITION]:
                raise RuntimeError(f"compiler invocation {sequence} lacks one exact production definition")
            expected_testing = [TESTING_DEFINITION] if role == "harness" else []
            if testing_variants != expected_testing:
                raise RuntimeError(f"compiler invocation {sequence} violates the testing macro boundary")
        else:
            link_count += 1
            linker_selections = [
                item for item in argv[1:]
                if isinstance(item, str) and item.startswith("--ld-path=")
            ]
            if linker_selections != ["--ld-path={REAL_LINKER}"]:
                raise RuntimeError(f"compiler invocation {sequence} does not select the bound linker")
            if any(
                isinstance(item, str)
                and (item == "{SOURCE_ROOT}" or item.startswith("{SOURCE_ROOT}/"))
                for item in argv[1:]
            ):
                raise RuntimeError(f"compiler invocation {sequence} link event contains source input")
        normalized = dict(value)
        normalized.pop("sequence")
        normalized_records.append(normalized)
    if compile_count < 1 or link_count < 1:
        raise RuntimeError("compiler trace lacks a compile or link event")
    return sha256_bytes(canonical(normalized_records)), count, True


def write_new(path: Path, data: bytes) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    output_parent = existing_directory(path.parent, "output parent")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        cursor = 0
        while cursor < len(data):
            written = os.write(descriptor, data[cursor:])
            if written <= 0:
                raise OSError("short evidence write")
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
    parser.add_argument("--role", choices=("release", "harness"), required=True)
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-closure", type=Path, required=True)
    parser.add_argument("--shared-header", type=Path, required=True)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--compiler-proxy", type=Path, required=True)
    parser.add_argument("--linker", type=Path, required=True)
    parser.add_argument("--command-manifest", type=Path, required=True)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--build-log", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    require_lease_released()
    if not args.build_id or not args.build_id.isascii() or any(character.isspace() for character in args.build_id):
        raise RuntimeError("build id must be nonempty ASCII without whitespace")
    source_root = existing_directory(args.source_root, "source root")
    shared_header = existing_regular(args.shared_header, "shared allocator header")
    compiler = existing_regular(args.compiler, "compiler")
    compiler_proxy = existing_regular(args.compiler_proxy, "compiler proxy")
    linker = existing_regular(args.linker, "linker")
    closure_path, closure = load_json(args.source_closure, "source closure")
    command_path, command = load_json(args.command_manifest, "command manifest")
    if set(command) != COMMAND_FIELDS or command["schema"] != COMMAND_SCHEMA or command["candidate_id"] != CANDIDATE_ID or command["build_role"] != args.role:
        raise RuntimeError("build command manifest identity mismatch")
    definitions = command["compile_definitions"]
    if not isinstance(definitions, list) or not all(isinstance(item, str) for item in definitions) or len(definitions) != len(set(definitions)):
        raise RuntimeError("compile definitions are invalid")
    if "GAMMA_FILEBACKED_FXCM=1" not in definitions or ("GAMMA_FILEBACKED_FXCM_TESTING=1" in definitions) != (args.role == "harness"):
        raise RuntimeError("release/harness macro boundary mismatch")
    for field in ("compile_argv", "link_argv"):
        if not isinstance(command[field], list) or not command[field] or not all(isinstance(item, str) for item in command[field]):
            raise RuntimeError(f"{field} must be a nonempty string array")
    if command["prepare_argv"] is not None and (not isinstance(command["prepare_argv"], list) or not command["prepare_argv"] or not all(isinstance(item, str) for item in command["prepare_argv"])):
        raise RuntimeError("prepare_argv must be null or a nonempty string array")
    if not isinstance(command["environment"], dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in command["environment"].items()):
        raise RuntimeError("build environment must be a string map")
    if RESERVED_PROXY_ENVIRONMENT & set(command["environment"]):
        raise RuntimeError("command manifest may not override compiler proxy environment")
    compiler_trace_relative = safe_relative(
        command["compiler_trace_relative_path"],
        "compiler_trace_relative_path",
    )
    binary_relative = safe_relative(command["binary_relative_path"], "binary_relative_path")

    header_sha256 = sha256_file(shared_header)
    entries = source_entries(source_root, closure, header_sha256)
    build_root = args.build_root
    if not build_root.is_absolute() or build_root.exists() or build_root.is_symlink():
        raise RuntimeError("build root must be an absent absolute path")
    build_root_parent = existing_directory(build_root.parent, "build root parent")
    build_root = build_root_parent / build_root.name
    build_log_parent = existing_directory(args.build_log.parent, "build log parent")
    receipt_parent = existing_directory(args.receipt.parent, "receipt parent")
    build_log = build_log_parent / args.build_log.name
    receipt_path = receipt_parent / args.receipt.name
    if build_log == receipt_path:
        raise RuntimeError("build log and receipt paths must differ")
    if is_within(build_root, source_root) or is_within(source_root, build_root):
        raise RuntimeError("source and build roots must be disjoint")
    for output_path, label in ((build_log, "build log"), (receipt_path, "receipt")):
        if is_within(output_path, source_root) or is_within(output_path, build_root):
            raise RuntimeError(f"{label} must be outside source and build roots")
        if output_path.exists() or output_path.is_symlink():
            raise FileExistsError(output_path)
    build_root.mkdir(mode=0o700)
    build_root_parent_descriptor = os.open(
        build_root.parent,
        os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
    )
    try:
        os.fsync(build_root_parent_descriptor)
    finally:
        os.close(build_root_parent_descriptor)
    root_metadata = build_root.stat()
    root_identity = {
        "path": str(build_root.resolve(strict=True)),
        "device": root_metadata.st_dev,
        "inode": root_metadata.st_ino,
    }
    bindings = {
        "{SOURCE_ROOT}": str(source_root),
        "{BUILD_ROOT}": str(build_root),
        "{COMPILER}": str(compiler),
        "{COMPILER_PROXY}": str(compiler_proxy),
        "{LINKER}": str(linker),
    }
    trace_directory = build_root.joinpath(*compiler_trace_relative.parts)
    trace_directory.mkdir(mode=0o700)
    build_root_descriptor = os.open(
        build_root,
        os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
    )
    try:
        os.fsync(build_root_descriptor)
    finally:
        os.close(build_root_descriptor)
    effective_environment_template = dict(command["environment"])
    effective_environment_template.update({
        "GAMMA_FXCM_REAL_COMPILER": "{COMPILER}",
        "GAMMA_FXCM_REAL_LINKER": "{LINKER}",
        "GAMMA_FXCM_COMPILER_TRACE_DIR": "{BUILD_ROOT}/" + compiler_trace_relative.as_posix(),
        "GAMMA_FXCM_SOURCE_ROOT": "{SOURCE_ROOT}",
        "GAMMA_FXCM_BUILD_ROOT": "{BUILD_ROOT}",
        "GAMMA_FXCM_BUILD_ROLE": args.role,
    })
    environment = {
        key: expand(value, bindings)
        for key, value in effective_environment_template.items()
    }
    log = bytearray(b"GAMMA_FXCM_BUILD_LOG_V1\n")
    prepare_rc, prepare_executable_sha256 = run_stage(
        "prepare", command["prepare_argv"], bindings, build_root, environment, log
    )
    if prepare_rc == 0:
        compile_rc, compile_executable_sha256 = run_stage(
            "compile", command["compile_argv"], bindings, build_root, environment, log
        )
    else:
        compile_rc, compile_executable_sha256 = 125, None
    if compile_rc == 0:
        link_rc, link_executable_sha256 = run_stage(
            "link", command["link_argv"], bindings, build_root, environment, log
        )
    else:
        link_rc, link_executable_sha256 = 125, None
    write_new(build_log, bytes(log))
    if prepare_rc != 0 or compile_rc != 0 or link_rc != 0:
        return 2
    compiler_sha256 = sha256_file(compiler)
    linker_sha256 = sha256_file(linker)
    compiler_proxy_sha256 = sha256_file(compiler_proxy)
    invocation_manifest_sha256, invocation_count, macro_boundary_trace_pass = compiler_trace_manifest(
        trace_directory,
        args.role,
        compiler_proxy_sha256,
        compiler_sha256,
        linker_sha256,
        source_root,
        build_root,
    )
    binary = existing_regular(build_root.joinpath(*binary_relative.parts), "built binary")
    capture_tool = Path(__file__).resolve(strict=True)
    stage_executables = {
        "prepare": prepare_executable_sha256,
        "compile": compile_executable_sha256,
        "link": link_executable_sha256,
    }
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "build_role": args.role,
        "build_id": args.build_id,
        "build_root_identity_sha256": sha256_bytes(canonical(root_identity)),
        "capture_tool_sha256": sha256_file(capture_tool),
        "compiler_proxy_sha256": compiler_proxy_sha256,
        "command_manifest_sha256": sha256_file(command_path),
        "stage_executable_manifest_sha256": sha256_bytes(canonical(stage_executables)),
        "compiler_invocation_manifest_sha256": invocation_manifest_sha256,
        "compiler_invocation_count": invocation_count,
        "macro_boundary_trace_pass": macro_boundary_trace_pass,
        "binary_sha256": sha256_file(binary),
        "shared_allocator_header_sha256": header_sha256,
        "source_closure_sha256": sha256_bytes(canonical(entries)),
        "source_closure": entries,
        "compiler_binary_sha256": compiler_sha256,
        "linker_binary_sha256": linker_sha256,
        "prepare_argv": command["prepare_argv"],
        "compile_argv": command["compile_argv"],
        "link_argv": command["link_argv"],
        "compile_definitions": definitions,
        "environment_sha256": sha256_bytes(canonical(effective_environment_template)),
        "build_log_sha256": sha256_file(build_log),
        "prepare_return_code": prepare_rc,
        "compile_return_code": compile_rc,
        "link_return_code": link_rc,
        "clean_build_root_pass": True,
        "build_succeeded": True,
    }
    write_new(receipt_path, json.dumps(receipt, sort_keys=True, indent=2).encode("ascii") + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
