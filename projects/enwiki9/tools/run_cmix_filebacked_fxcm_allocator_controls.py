#!/usr/bin/env python3
"""Run q1 allocator fixtures sequentially after the exclusive host is released."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "projects/enwiki9"
LEASE = PROJECT / "operations/runtime/exclusive_full1g.json"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
MINIMUM_BACKED_BYTES = 64 * 1024 * 1024

EXPECTED_CODES = {
    "missing_environment": 64,
    "relative_path": 64,
    "dot_component": 65,
    "dotdot_component": 65,
    "repeated_separator": 65,
    "trailing_separator": 65,
    "symlink_component": 65,
    "nonempty_directory": 65,
    "filename_collision": 66,
    "reserve_failure": 66,
    "registry_overflow": 68,
    "interior_pointer_free": 69,
    "inode_replacement": 69,
    "pageout_failure": 70,
    "terminal_cleanup_failure": 71,
}

EXPECTED_RESIDUALS = {
    "missing_environment": set(),
    "relative_path": set(),
    "dot_component": set(),
    "dotdot_component": set(),
    "repeated_separator": set(),
    "trailing_separator": set(),
    "symlink_component": set(),
    "nonempty_directory": {"foreign-marker.bin"},
    "filename_collision": {"fxcm-0000.bin"},
    "reserve_failure": set(),
    "registry_overflow": set(),
    "interior_pointer_free": set(),
    "inode_replacement": {"fxcm-0000.bin", "retained-original.bin"},
    "pageout_failure": set(),
    "terminal_cleanup_failure": {"fxcm-0000.bin"},
}


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


def require_exclusive_host_released() -> None:
    if not LEASE.is_file():
        return
    lease = json.loads(LEASE.read_text(encoding="utf-8"))
    for pid_key, start_key in (("pid", "proc_start_ticks"), ("codec_pid", "codec_proc_start_ticks")):
        pid = lease.get(pid_key)
        start = lease.get(start_key)
        if isinstance(pid, int) and Path(f"/proc/{pid}").exists():
            if start is None or proc_start_ticks(pid) == start:
                raise RuntimeError(f"exclusive lease remains active for {pid_key}={pid}")


def require_regular_no_symlink(path: Path, label: str) -> Path:
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


def require_directory_no_symlink(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current = current / component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"{label} has an invalid component: {current}")
    return absolute.resolve(strict=True)


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def snapshot(directory: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for entry in sorted(os.scandir(directory), key=lambda value: value.name):
        metadata = entry.stat(follow_symlinks=False)
        if not stat.S_ISREG(metadata.st_mode):
            raise RuntimeError(f"unexpected nonregular scratch entry: {entry.path}")
        path = Path(entry.path)
        result[entry.name] = {
            "bytes": metadata.st_size,
            "allocated_bytes": metadata.st_blocks * 512,
            "device": metadata.st_dev,
            "inode": metadata.st_ino,
            "mode": stat.S_IMODE(metadata.st_mode),
            "sha256": sha256_file(path),
        }
    return result


def canonical_sha256(value: Any) -> str:
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")
    return sha256_bytes(rendered)


def write_json_fsynced(path: Path, value: Any) -> None:
    output_parent = require_directory_no_symlink(path.parent, "JSON output parent")
    data = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("ascii")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
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
    fsync_directory(output_parent)


def write_bytes_fsynced(path: Path, data: bytes) -> None:
    output_parent = require_directory_no_symlink(path.parent, "binary output parent")
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
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
    fsync_directory(output_parent)


def load_build_receipt(
    path: Path,
    role: str,
    binary_sha256: str,
    header_sha256: str,
) -> tuple[dict[str, Any], str]:
    receipt_path = require_regular_no_symlink(path, f"{role} build receipt")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    required = {
        "schema",
        "candidate_id",
        "build_role",
        "build_id",
        "build_root_identity_sha256",
        "capture_tool_sha256",
        "compiler_proxy_sha256",
        "command_manifest_sha256",
        "stage_executable_manifest_sha256",
        "compiler_invocation_manifest_sha256",
        "compiler_invocation_count",
        "macro_boundary_trace_pass",
        "binary_sha256",
        "shared_allocator_header_sha256",
        "source_closure_sha256",
        "source_closure",
        "compiler_binary_sha256",
        "linker_binary_sha256",
        "prepare_argv",
        "compile_argv",
        "link_argv",
        "compile_definitions",
        "environment_sha256",
        "build_log_sha256",
        "prepare_return_code",
        "compile_return_code",
        "link_return_code",
        "clean_build_root_pass",
        "build_succeeded",
    }
    if not isinstance(receipt, dict) or set(receipt) != required:
        raise RuntimeError(f"{role} build receipt has an invalid field set")
    if receipt["schema"] != "gamma.enwiki9.cmix-filebacked-fxcm-build-receipt.v1":
        raise RuntimeError(f"{role} build receipt schema mismatch")
    if receipt["candidate_id"] != CANDIDATE_ID or receipt["build_role"] != role:
        raise RuntimeError(f"{role} build receipt identity mismatch")
    if receipt["binary_sha256"] != binary_sha256:
        raise RuntimeError(f"{role} build receipt does not bind the supplied binary")
    if receipt["shared_allocator_header_sha256"] != header_sha256:
        raise RuntimeError(f"{role} build receipt does not bind the supplied allocator header")
    closure = receipt["source_closure"]
    if not isinstance(closure, list) or not closure:
        raise RuntimeError(f"{role} build receipt has no source closure")
    if receipt["source_closure_sha256"] != canonical_sha256(closure):
        raise RuntimeError(f"{role} source closure digest mismatch")
    header_entries = [
        entry
        for entry in closure
        if isinstance(entry, dict) and entry.get("role") == "shared_allocator_header"
    ]
    if len(header_entries) != 1 or header_entries[0].get("sha256") != header_sha256:
        raise RuntimeError(f"{role} source closure does not uniquely bind the allocator header")
    definitions = receipt["compile_definitions"]
    if not isinstance(definitions, list) or len(set(definitions)) != len(definitions):
        raise RuntimeError(f"{role} compile definitions are invalid")
    production = "GAMMA_FILEBACKED_FXCM=1" in definitions
    testing = "GAMMA_FILEBACKED_FXCM_TESTING=1" in definitions
    if not production or testing != (role == "harness"):
        raise RuntimeError(f"{role} build has an invalid allocator macro boundary")
    if (
        receipt["prepare_return_code"] != 0
        or receipt["compile_return_code"] != 0
        or receipt["link_return_code"] != 0
        or receipt["clean_build_root_pass"] is not True
        or receipt["build_succeeded"] is not True
        or receipt["macro_boundary_trace_pass"] is not True
    ):
        raise RuntimeError(f"{role} build receipt is not authority-bearing")
    return receipt, sha256_file(receipt_path)


def load_build_verification(
    path: Path,
    role: str,
    build_receipt_sha256: str,
    binary_sha256: str,
    header_sha256: str,
    source_closure_sha256: str,
    capture_tool_sha256: str,
    compiler_proxy_sha256: str,
    command_manifest_sha256: str,
    stage_executable_manifest_sha256: str,
    compiler_invocation_manifest_sha256: str,
    compiler_invocation_count: int,
    compiler_binary_sha256: str,
    linker_binary_sha256: str,
) -> str:
    verification_path = require_regular_no_symlink(path, f"{role} build verification")
    value = json.loads(verification_path.read_text(encoding="utf-8"))
    required = {
        "schema", "candidate_id", "build_role", "build_a_receipt_sha256",
        "build_b_receipt_sha256", "build_a_binary_sha256", "build_b_binary_sha256",
        "shared_allocator_header_sha256", "source_closure_sha256",
        "capture_tool_sha256", "compiler_proxy_sha256", "command_manifest_sha256",
        "stage_executable_manifest_sha256",
        "compiler_invocation_manifest_sha256", "compiler_invocation_count",
        "compiler_binary_sha256", "linker_binary_sha256", "build_id_distinct_pass",
        "build_root_identity_distinct_pass", "source_closure_identity_pass",
        "toolchain_identity_pass", "command_identity_pass", "environment_identity_pass",
        "shared_allocator_identity_pass", "macro_boundary_pass", "binary_identity_pass",
        "independent_build_pass", "authority", "execution_authority",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise RuntimeError(f"{role} build verification has an invalid field set")
    if (
        value["schema"] != "gamma.enwiki9.cmix-filebacked-fxcm-build-verification.v1"
        or value["candidate_id"] != CANDIDATE_ID
        or value["build_role"] != role
        or value["build_a_receipt_sha256"] != build_receipt_sha256
        or value["build_a_binary_sha256"] != binary_sha256
        or value["build_b_binary_sha256"] != binary_sha256
        or value["shared_allocator_header_sha256"] != header_sha256
        or value["source_closure_sha256"] != source_closure_sha256
        or value["capture_tool_sha256"] != capture_tool_sha256
        or value["compiler_proxy_sha256"] != compiler_proxy_sha256
        or value["command_manifest_sha256"] != command_manifest_sha256
        or value["stage_executable_manifest_sha256"] != stage_executable_manifest_sha256
        or value["compiler_invocation_manifest_sha256"] != compiler_invocation_manifest_sha256
        or value["compiler_invocation_count"] != compiler_invocation_count
        or value["compiler_binary_sha256"] != compiler_binary_sha256
        or value["linker_binary_sha256"] != linker_binary_sha256
        or value["authority"] != "build_identity_only"
        or value["execution_authority"] is not False
    ):
        raise RuntimeError(f"{role} build verification identity mismatch")
    pass_fields = [name for name in required if name.endswith("_pass")]
    if not pass_fields or any(value[name] is not True for name in pass_fields):
        raise RuntimeError(f"{role} independent build verification did not pass")
    return sha256_file(verification_path)


def residual_shape_pass(name: str, after: dict[str, dict[str, Any]]) -> bool:
    if set(after) != EXPECTED_RESIDUALS[name]:
        return False
    if any(entry["mode"] != 0o600 for entry in after.values()):
        return False
    if name == "filename_collision":
        return after["fxcm-0000.bin"]["bytes"] == 0
    if name == "inode_replacement":
        replacement = after["fxcm-0000.bin"]
        retained = after["retained-original.bin"]
        return (
            replacement["bytes"] == 0
            and retained["bytes"] >= MINIMUM_BACKED_BYTES
            and (replacement["device"], replacement["inode"])
            != (retained["device"], retained["inode"])
        )
    if name == "terminal_cleanup_failure":
        return after["fxcm-0000.bin"]["bytes"] >= MINIMUM_BACKED_BYTES
    return True


def prepare_scratch(name: str, scratch_parent: Path, control_root: Path) -> tuple[Path | None, str | None]:
    if name == "missing_environment":
        return None, None
    scratch = scratch_parent / name
    if name == "relative_path":
        relative = control_root / "relative-scratch"
        relative.mkdir()
        return relative, "relative-scratch"
    if name == "dot_component":
        parent = scratch_parent / "dot-component-parent"
        scratch = parent / "scratch"
        scratch.mkdir(parents=True)
        return scratch, f"{parent}/./scratch"
    if name == "dotdot_component":
        parent = scratch_parent / "dotdot-component-parent"
        (parent / "unused").mkdir(parents=True)
        scratch = parent / "scratch"
        scratch.mkdir()
        return scratch, f"{parent}/unused/../scratch"
    if name == "repeated_separator":
        scratch.mkdir()
        return scratch, f"{scratch_parent}//{name}"
    if name == "trailing_separator":
        scratch.mkdir()
        return scratch, f"{scratch}/"
    if name == "symlink_component":
        real_parent = scratch_parent / "symlink-real-parent"
        scratch = real_parent / "scratch"
        scratch.mkdir(parents=True)
        link = scratch_parent / "symlink-link"
        link.symlink_to(real_parent, target_is_directory=True)
        return scratch, f"{link}/scratch"
    scratch.mkdir()
    if name == "nonempty_directory":
        (scratch / "foreign-marker.bin").write_bytes(b"foreign-marker-v1\n")
    return scratch, str(scratch)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--harness", type=Path, required=True)
    parser.add_argument("--release-binary", type=Path, required=True)
    parser.add_argument("--shared-header", type=Path, required=True)
    parser.add_argument("--release-build-receipt", type=Path, required=True)
    parser.add_argument("--harness-build-receipt", type=Path, required=True)
    parser.add_argument("--release-build-verification", type=Path, required=True)
    parser.add_argument("--harness-build-verification", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--scratch-parent", type=Path, required=True)
    args = parser.parse_args()

    require_exclusive_host_released()
    harness = require_regular_no_symlink(args.harness, "harness")
    release_binary = require_regular_no_symlink(args.release_binary, "release binary")
    shared_header = require_regular_no_symlink(args.shared_header, "shared header")
    harness_sha256 = sha256_file(harness)
    release_binary_sha256 = sha256_file(release_binary)
    header_sha256 = sha256_file(shared_header)
    release_build, release_build_receipt_sha256 = load_build_receipt(
        args.release_build_receipt,
        "release",
        release_binary_sha256,
        header_sha256,
        release_build["source_closure_sha256"],
        release_build["capture_tool_sha256"],
        release_build["compiler_proxy_sha256"],
        release_build["command_manifest_sha256"],
        release_build["stage_executable_manifest_sha256"],
        release_build["compiler_invocation_manifest_sha256"],
        release_build["compiler_invocation_count"],
        release_build["compiler_binary_sha256"],
        release_build["linker_binary_sha256"],
    )
    harness_build, harness_build_receipt_sha256 = load_build_receipt(
        args.harness_build_receipt,
        "harness",
        harness_sha256,
        header_sha256,
        harness_build["source_closure_sha256"],
        harness_build["capture_tool_sha256"],
        harness_build["compiler_proxy_sha256"],
        harness_build["command_manifest_sha256"],
        harness_build["stage_executable_manifest_sha256"],
        harness_build["compiler_invocation_manifest_sha256"],
        harness_build["compiler_invocation_count"],
        harness_build["compiler_binary_sha256"],
        harness_build["linker_binary_sha256"],
    )
    shared_source_identity_pass = (
        release_build["shared_allocator_header_sha256"]
        == harness_build["shared_allocator_header_sha256"]
        == header_sha256
    )
    if not shared_source_identity_pass:
        raise RuntimeError("release and harness do not share one allocator source identity")
    release_build_verification_sha256 = load_build_verification(
        args.release_build_verification,
        "release",
        release_build_receipt_sha256,
        release_binary_sha256,
        header_sha256,
    )
    harness_build_verification_sha256 = load_build_verification(
        args.harness_build_verification,
        "harness",
        harness_build_receipt_sha256,
        harness_sha256,
        header_sha256,
    )
    if args.result_root.exists() or args.result_root.is_symlink():
        raise FileExistsError(args.result_root)
    result_parent = require_directory_no_symlink(args.result_root.parent, "result parent")
    scratch_parent = require_directory_no_symlink(args.scratch_parent, "scratch parent")
    if any(scratch_parent.iterdir()):
        raise RuntimeError("scratch parent must initially be empty")
    result_root = result_parent / args.result_root.name
    result_root.mkdir(mode=0o700)
    fsync_directory(result_parent)

    controls: dict[str, dict[str, Any]] = {}
    positive_receipt: dict[str, Any] | None = None
    for name in ("positive", *EXPECTED_CODES.keys()):
        control_root = result_root / name
        control_root.mkdir()
        scratch, raw_scratch = prepare_scratch(name, scratch_parent, control_root)
        before = snapshot(scratch) if scratch is not None else {}
        event_path = control_root / "events.bin"
        event_fd = os.open(event_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o600)
        argv = [str(harness), name]
        if raw_scratch is not None:
            argv.append(raw_scratch)
        environment = {
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": os.environ.get("PATH", os.defpath),
            "TZ": "UTC",
            "GAMMA_FXCM_EVENT_FD": str(event_fd),
        }
        if "LD_LIBRARY_PATH" in os.environ:
            environment["LD_LIBRARY_PATH"] = os.environ["LD_LIBRARY_PATH"]
        command = {
            "argv": argv,
            "cwd": str(control_root),
            "environment": environment,
        }
        completed = subprocess.run(
            argv,
            cwd=control_root,
            env=environment,
            pass_fds=(event_fd,),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        os.fsync(event_fd)
        os.close(event_fd)
        stdout_path = control_root / "stdout.bin"
        stderr_path = control_root / "stderr.bin"
        write_bytes_fsynced(stdout_path, completed.stdout)
        write_bytes_fsynced(stderr_path, completed.stderr)
        after = snapshot(scratch) if scratch is not None else {}
        write_json_fsynced(control_root / "command.json", command)
        write_json_fsynced(control_root / "scratch-before.json", before)
        write_json_fsynced(control_root / "scratch-after.json", after)

        if name == "positive":
            positive_receipt = {
                "return_code": completed.returncode,
                "stdout_sha256": sha256_bytes(completed.stdout),
                "stderr_sha256": sha256_bytes(completed.stderr),
                "event_stream_sha256": sha256_file(event_path),
                "scratch_before_sha256": canonical_sha256(before),
                "scratch_after_sha256": canonical_sha256(after),
                "pass": completed.returncode == 0 and not before and not after,
            }
            continue

        expected_code = EXPECTED_CODES[name]
        expected_residual = EXPECTED_RESIDUALS[name]
        residual_names = set(after)
        expected_residual_set_pass = residual_names == expected_residual
        preexisting_entries_unchanged = all(after.get(entry) == identity for entry, identity in before.items())
        expected_residual_shape_pass = residual_shape_pass(name, after)
        result = {
            "command_sha256": canonical_sha256(command),
            "return_code": completed.returncode,
            "stdout_bytes": len(completed.stdout),
            "stdout_sha256": sha256_bytes(completed.stdout),
            "stderr_bytes": len(completed.stderr),
            "stderr_sha256": sha256_bytes(completed.stderr),
            "scratch_before_sha256": canonical_sha256(before),
            "scratch_after_sha256": canonical_sha256(after),
            "expected_residual_names": sorted(expected_residual),
            "residual_manifest_sha256": canonical_sha256(after),
            "expected_failure_observed": completed.returncode == expected_code,
            "output_artifact_absent": not after,
            "expected_residual_set_pass": expected_residual_set_pass,
            "expected_residual_shape_pass": expected_residual_shape_pass,
            "preexisting_entries_unchanged": preexisting_entries_unchanged,
            "foreign_files_unchanged": preexisting_entries_unchanged,
        }
        if not all(
            (
                result["expected_failure_observed"],
                result["expected_residual_set_pass"],
                result["expected_residual_shape_pass"],
                result["preexisting_entries_unchanged"],
            )
        ):
            raise RuntimeError(
                f"control {name} failed: return={completed.returncode} residual={sorted(residual_names)}"
            )
        controls[name] = result

    if positive_receipt is None or not positive_receipt["pass"]:
        raise RuntimeError("positive allocator fixture failed")
    manifest = {
        "schema": "gamma.enwiki9.cmix-filebacked-fxcm-negative-controls.v2",
        "candidate_id": CANDIDATE_ID,
        "release_binary_sha256": release_binary_sha256,
        "harness_binary_sha256": harness_sha256,
        "shared_allocator_header_sha256": header_sha256,
        "release_build_receipt_sha256": release_build_receipt_sha256,
        "harness_build_receipt_sha256": harness_build_receipt_sha256,
        "release_build_verification_sha256": release_build_verification_sha256,
        "harness_build_verification_sha256": harness_build_verification_sha256,
        "release_source_closure_sha256": release_build["source_closure_sha256"],
        "harness_source_closure_sha256": harness_build["source_closure_sha256"],
        "shared_source_identity_pass": shared_source_identity_pass,
        "controls": controls,
    }
    write_json_fsynced(result_root / "positive-fixture.json", positive_receipt)
    write_json_fsynced(result_root / "negative-controls.json", manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
