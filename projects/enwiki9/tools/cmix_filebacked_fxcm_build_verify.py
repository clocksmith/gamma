#!/usr/bin/env python3
"""Compare two independent q1 builds without granting execution authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any


CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
BUILD_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-build-receipt.v1"
OUTPUT_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-build-verification.v1"
BUILD_FIELDS = {
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


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def regular_no_links(path: Path, label: str) -> Path:
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


def directory_no_links(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current = current / component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"{label} has an invalid component: {current}")
    return absolute.resolve(strict=True)


def load_build(path: Path, role: str, label: str) -> tuple[Path, dict[str, Any]]:
    resolved = regular_no_links(path, label)
    value = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != BUILD_FIELDS:
        raise RuntimeError(f"{label} has an invalid field set")
    if value["schema"] != BUILD_SCHEMA or value["candidate_id"] != CANDIDATE_ID:
        raise RuntimeError(f"{label} identity mismatch")
    if value["build_role"] != role:
        raise RuntimeError(f"{label} role mismatch")
    if value["source_closure_sha256"] != canonical_sha256(value["source_closure"]):
        raise RuntimeError(f"{label} source closure digest mismatch")
    header_entries = [
        entry for entry in value["source_closure"]
        if isinstance(entry, dict) and entry.get("role") == "shared_allocator_header"
    ]
    if len(header_entries) != 1 or header_entries[0].get("sha256") != value["shared_allocator_header_sha256"]:
        raise RuntimeError(f"{label} does not uniquely bind its allocator header")
    definitions = value["compile_definitions"]
    if not isinstance(definitions, list) or not all(isinstance(item, str) for item in definitions):
        raise RuntimeError(f"{label} compile definitions are invalid")
    if len(definitions) != len(set(definitions)):
        raise RuntimeError(f"{label} compile definitions are duplicated")
    production = "GAMMA_FILEBACKED_FXCM=1" in definitions
    testing = "GAMMA_FILEBACKED_FXCM_TESTING=1" in definitions
    if not production or testing != (role == "harness"):
        raise RuntimeError(f"{label} violates the release/harness macro boundary")
    if (
        value["compile_return_code"] != 0
        or value["prepare_return_code"] != 0
        or value["link_return_code"] != 0
        or value["clean_build_root_pass"] is not True
        or value["build_succeeded"] is not True
        or value["macro_boundary_trace_pass"] is not True
    ):
        raise RuntimeError(f"{label} is not a successful clean build")
    return resolved, value


def write_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    output_parent = directory_no_links(path.parent, "output parent")
    data = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("ascii")
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
                raise OSError("short verification write")
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
    parser.add_argument("--build-a-receipt", type=Path, required=True)
    parser.add_argument("--build-b-receipt", type=Path, required=True)
    parser.add_argument("--binary-a", type=Path, required=True)
    parser.add_argument("--binary-b", type=Path, required=True)
    parser.add_argument("--shared-header", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    receipt_a_path, build_a = load_build(args.build_a_receipt, args.role, "build A receipt")
    receipt_b_path, build_b = load_build(args.build_b_receipt, args.role, "build B receipt")
    binary_a = regular_no_links(args.binary_a, "build A binary")
    binary_b = regular_no_links(args.binary_b, "build B binary")
    shared_header = regular_no_links(args.shared_header, "shared allocator header")
    binary_a_sha256 = sha256_file(binary_a)
    binary_b_sha256 = sha256_file(binary_b)
    header_sha256 = sha256_file(shared_header)
    if build_a["binary_sha256"] != binary_a_sha256 or build_b["binary_sha256"] != binary_b_sha256:
        raise RuntimeError("a build receipt does not bind its supplied binary")
    if build_a["shared_allocator_header_sha256"] != header_sha256 or build_b["shared_allocator_header_sha256"] != header_sha256:
        raise RuntimeError("build receipts do not bind the supplied allocator header")

    checks = {
        "build_id_distinct_pass": build_a["build_id"] != build_b["build_id"],
        "build_root_identity_distinct_pass": build_a["build_root_identity_sha256"] != build_b["build_root_identity_sha256"],
        "source_closure_identity_pass": build_a["source_closure"] == build_b["source_closure"],
        "toolchain_identity_pass": (
            build_a["compiler_binary_sha256"] == build_b["compiler_binary_sha256"]
            and build_a["linker_binary_sha256"] == build_b["linker_binary_sha256"]
            and build_a["capture_tool_sha256"] == build_b["capture_tool_sha256"]
            and build_a["compiler_proxy_sha256"] == build_b["compiler_proxy_sha256"]
            and build_a["stage_executable_manifest_sha256"] == build_b["stage_executable_manifest_sha256"]
        ),
        "command_identity_pass": (
            build_a["prepare_argv"] == build_b["prepare_argv"]
            and build_a["compile_argv"] == build_b["compile_argv"]
            and build_a["link_argv"] == build_b["link_argv"]
            and build_a["command_manifest_sha256"] == build_b["command_manifest_sha256"]
        ),
        "environment_identity_pass": build_a["environment_sha256"] == build_b["environment_sha256"],
        "shared_allocator_identity_pass": build_a["shared_allocator_header_sha256"] == build_b["shared_allocator_header_sha256"] == header_sha256,
        "macro_boundary_pass": build_a["compile_definitions"] == build_b["compile_definitions"],
        "compiler_invocation_identity_pass": (
            build_a["compiler_invocation_manifest_sha256"]
            == build_b["compiler_invocation_manifest_sha256"]
            and build_a["compiler_invocation_count"] == build_b["compiler_invocation_count"]
        ),
        "binary_identity_pass": binary_a_sha256 == binary_b_sha256,
    }
    if not all(checks.values()):
        failed = sorted(name for name, passed in checks.items() if not passed)
        raise RuntimeError(f"independent build comparison failed: {failed}")
    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "build_role": args.role,
        "build_a_receipt_sha256": sha256_file(receipt_a_path),
        "build_b_receipt_sha256": sha256_file(receipt_b_path),
        "build_a_binary_sha256": binary_a_sha256,
        "build_b_binary_sha256": binary_b_sha256,
        "shared_allocator_header_sha256": header_sha256,
        "source_closure_sha256": build_a["source_closure_sha256"],
        "capture_tool_sha256": build_a["capture_tool_sha256"],
        "compiler_proxy_sha256": build_a["compiler_proxy_sha256"],
        "command_manifest_sha256": build_a["command_manifest_sha256"],
        "stage_executable_manifest_sha256": build_a["stage_executable_manifest_sha256"],
        "compiler_invocation_manifest_sha256": build_a["compiler_invocation_manifest_sha256"],
        "compiler_invocation_count": build_a["compiler_invocation_count"],
        "compiler_binary_sha256": build_a["compiler_binary_sha256"],
        "linker_binary_sha256": build_a["linker_binary_sha256"],
        **checks,
        "independent_build_pass": True,
        "authority": "build_identity_only",
        "execution_authority": False,
    }
    write_new(args.output, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
