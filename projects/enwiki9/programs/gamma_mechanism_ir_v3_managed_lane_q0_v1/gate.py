#!/usr/bin/env python3
"""Bind truthful wrapper provenance through the unchanged v3 static gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any

from managed_lane import OwnedNamespaceLock, load_tool


PROJECT = Path(__file__).resolve().parents[2]
CANDIDATE_ID = "gamma_mechanism_ir_v3_managed_lane_q0_v1"
SCHEMA = "gamma.enwiki9.mechanism-ir-managed-lane-gate.v1"
WRAPPER_COMPILER = Path(__file__).with_name("compile.py")
UPSTREAM_COMPILER = PROJECT / "tools/gamma_mechanism_ir_compile_v2.py"


def sha256(path: Path) -> str:
    raw, _ = read_artifact(path)
    return hashlib.sha256(raw).hexdigest()


def absolute(path: Path) -> Path:
    return path if path.is_absolute() else Path.cwd() / path


def open_parent(path: Path) -> tuple[Path, int]:
    resolved = absolute(path)
    current = Path(resolved.anchor)
    for component in resolved.parent.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"unsafe artifact parent component: {current}")
    descriptor = os.open(
        resolved.parent,
        os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
    )
    observed = os.fstat(descriptor)
    current_metadata = os.stat(resolved.parent, follow_symlinks=False)
    if (
        not stat.S_ISDIR(observed.st_mode)
        or observed.st_dev != current_metadata.st_dev
        or observed.st_ino != current_metadata.st_ino
    ):
        os.close(descriptor)
        raise RuntimeError(f"artifact parent identity changed: {resolved.parent}")
    return resolved, descriptor


def read_artifact(path: Path) -> tuple[bytes, dict[str, Any]]:
    resolved, parent_descriptor = open_parent(path)
    try:
        descriptor = os.open(
            resolved.name,
            os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
            dir_fd=parent_descriptor,
        )
        try:
            before = os.fstat(descriptor)
            named = os.stat(
                resolved.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_dev != named.st_dev
                or before.st_ino != named.st_ino
            ):
                raise RuntimeError(f"single-link regular artifact required: {path}")
            blocks: list[bytes] = []
            while True:
                block = os.read(descriptor, 1 << 20)
                if not block:
                    break
                blocks.append(block)
            after = os.fstat(descriptor)
            if (
                before.st_dev != after.st_dev
                or before.st_ino != after.st_ino
                or before.st_size != after.st_size
                or before.st_mtime_ns != after.st_mtime_ns
                or before.st_ctime_ns != after.st_ctime_ns
            ):
                raise RuntimeError(f"artifact changed while read: {path}")
            raw = b"".join(blocks)
            if len(raw) != after.st_size:
                raise RuntimeError(f"artifact length changed while read: {path}")
        finally:
            os.close(descriptor)
    finally:
        os.close(parent_descriptor)
    return raw, {
        "path": os.fspath(path),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def write_new(path: Path, value: dict[str, Any]) -> None:
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("ascii")
    resolved, parent_descriptor = open_parent(path)
    try:
        descriptor = os.open(
            resolved.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent_descriptor,
        )
        try:
            offset = 0
            while offset < len(raw):
                written = os.write(descriptor, raw[offset:])
                if written <= 0:
                    raise RuntimeError(f"short write: {path}")
                offset += written
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.fsync(parent_descriptor)
    finally:
        os.close(parent_descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program-lock", required=True, type=Path)
    parser.add_argument("--program-lock-verification", required=True, type=Path)
    parser.add_argument("--compilation-verification", required=True, type=Path)
    parser.add_argument("--exclusive-lease", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    compatibility_path = args.receipt.with_name(f"{args.receipt.stem}.v3-compat.json")
    upstream_gate_path = args.receipt.with_name(f"{args.receipt.stem}.v3-upstream.json")
    with OwnedNamespaceLock.acquire(args.exclusive_lease) as guard:
        guard.assert_owned(args.exclusive_lease)
        for path in (args.receipt, compatibility_path, upstream_gate_path):
            if path.exists() or path.is_symlink():
                raise SystemExit(f"output already exists: {path}")
        actual_raw, actual_artifact = read_artifact(args.compilation_verification)
        wrapper_raw, wrapper_artifact = read_artifact(WRAPPER_COMPILER)
        upstream_raw, upstream_artifact = read_artifact(UPSTREAM_COMPILER)
        actual = json.loads(actual_raw.decode("utf-8"))
        wrapper_hash = hashlib.sha256(wrapper_raw).hexdigest()
        upstream_hash = hashlib.sha256(upstream_raw).hexdigest()
        if (
            not isinstance(actual, dict)
            or actual.get("schema")
            != "gamma.enwiki9.gamma-mechanism-ir-compilation-verification.v2"
            or actual.get("verified") is not True
            or actual.get("errors") != []
            or actual.get("compiler_sha256") != wrapper_hash
        ):
            raise SystemExit(
                "actual compilation verification is not a positive wrapper-bound receipt"
            )
        compatibility = dict(actual)
        compatibility["compiler_sha256"] = upstream_hash
        differing = {
            key
            for key in set(actual) | set(compatibility)
            if actual.get(key) != compatibility.get(key)
        }
        if differing != {"compiler_sha256"}:
            raise SystemExit(
                "v3 compatibility projection changed more than compiler identity"
            )
        write_new(compatibility_path, compatibility)
        tool = load_tool(
            PROJECT,
            "gamma_mechanism_ir_v3_gate.py",
            "gamma_ir_v3_gate_frozen",
        )
        tool.require_clear_lease = guard.assert_owned
        original_argv = sys.argv
        sys.argv = [
            str(PROJECT / "tools/gamma_mechanism_ir_v3_gate.py"),
            "--program-lock", str(args.program_lock),
            "--program-lock-verification", str(args.program_lock_verification),
            "--compilation-verification", str(compatibility_path),
            "--exclusive-lease", str(args.exclusive_lease),
            "--receipt", str(upstream_gate_path),
        ]
        try:
            return_code = int(tool.main())
        finally:
            sys.argv = original_argv
        guard.assert_owned(args.exclusive_lease)
        upstream_gate_raw, upstream_gate_artifact = read_artifact(upstream_gate_path)
        upstream_gate = json.loads(upstream_gate_raw.decode("utf-8"))
        stable_actual_raw, stable_actual_artifact = read_artifact(
            args.compilation_verification
        )
        stable_wrapper_raw, stable_wrapper_artifact = read_artifact(WRAPPER_COMPILER)
        stable_upstream_raw, stable_upstream_artifact = read_artifact(UPSTREAM_COMPILER)
        if (
            stable_actual_raw != actual_raw
            or stable_wrapper_raw != wrapper_raw
            or stable_upstream_raw != upstream_raw
        ):
            raise SystemExit("gate input changed during provenance projection")
        _, compatibility_artifact = read_artifact(compatibility_path)
        checks = {
            "actual_wrapper_verification_pass": True,
            "wrapper_compiler_identity_pass": actual["compiler_sha256"] == wrapper_hash,
            "compatibility_projection_exact_pass": differing == {"compiler_sha256"},
            "upstream_compiler_identity_pass": compatibility["compiler_sha256"] == upstream_hash,
            "unchanged_v3_gate_pass": (
                return_code == 0
                and upstream_gate.get("verified") is True
                and upstream_gate.get("errors") == []
            ),
        }
        verified = all(checks.values())
        output = {
            "schema": SCHEMA,
            "candidate_id": CANDIDATE_ID,
            "verified": verified,
            "errors": [] if verified else ["managed-lane final gate predicate failed"],
            "actual_compilation_verification": stable_actual_artifact,
            "compatibility_projection": compatibility_artifact,
            "upstream_v3_gate": upstream_gate_artifact,
            "wrapper_compiler": stable_wrapper_artifact,
            "upstream_compiler": stable_upstream_artifact,
            "checks": checks,
            "claim_authority": "infrastructure_only",
            "execution_authority": False,
            "promotion_authority": False,
            "gamma_compression_credit_bytes": 0,
            "gamma_score_credit_bytes": 0,
        }
        write_new(args.receipt, output)
        guard.assert_owned(args.exclusive_lease)
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
