#!/usr/bin/env python3
"""Local deterministic controls for exact-ownership managed lease cleanup."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import managed_exclusive_lease as candidate


CANDIDATE_ID = "gamma_managed_exclusive_lease_owned_cleanup_q0_v1"
SCHEMA = "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-controls.v1"
PROJECT = Path(__file__).resolve().parents[2]


def load_module(path: Path, name: str) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    if Path(str(module.__file__)).resolve(strict=True) != path.resolve(strict=True):
        raise RuntimeError(f"loaded module differs: {path}")
    return module


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def identity(path: Path) -> dict[str, Any]:
    metadata = path.lstat()
    raw = path.read_bytes()
    return {
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "links": metadata.st_nlink,
    }


def unchanged(path: Path, expected: dict[str, Any]) -> bool:
    try:
        return identity(path) == expected
    except OSError:
        return False


def reject(operation: Callable[[], object]) -> bool:
    try:
        operation()
    except Exception:
        return True
    return False


def write_new(path: Path, raw: bytes, mode: int = 0o600) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        mode,
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


def acquire(lease: Path, transition: Path, label: str) -> candidate.ManagedExclusiveLease:
    return candidate.ManagedExclusiveLease.acquire(
        lease_path=lease,
        transition_path=transition,
        candidate_id=f"{CANDIDATE_ID}-{label}",
        command_sha256="0" * 64,
        runner_sha256="1" * 64,
        guard_path=f"{label}/guard.json",
        result_path=f"{label}/result.json",
        scratch_path=f"{label}/scratch",
        claim_boundary="local ownership control only",
    )


def lifecycle(root: Path, name: str, verifier: ModuleType) -> dict[str, Any]:
    directory = root / name
    directory.mkdir()
    lease = directory / "exclusive.json"
    lock = directory / "exclusive.json.lock"
    transition = directory / "transitions.json"
    terminal = directory / "terminal.json"
    manager = acquire(lease, transition, name)
    manager.heartbeat()
    manager.release(evidence_path=terminal)
    verification, verified = verifier.verify(
        argparse.Namespace(transition_log=transition, terminal_lease=terminal)
    )
    return {
        "released": not lease.exists() and not lock.exists(),
        "verified": verified,
        "events": [entry["event"] for entry in json.loads(transition.read_text())["entries"]],
        "terminal_keys": sorted(json.loads(terminal.read_text())),
        "transition_schema": json.loads(transition.read_text())["schema_version"],
        "verification": verification,
    }


def normalized_lifecycle(value: dict[str, Any]) -> dict[str, Any]:
    verification = value["verification"]
    computed = verification["computed"]
    return {
        "released": value["released"],
        "verified": value["verified"],
        "events": value["events"],
        "terminal_keys": value["terminal_keys"],
        "transition_schema": value["transition_schema"],
        "verification_shape": {
            "schema_version": verification["schema_version"],
            "verified": verification["verified"],
            "errors": verification["errors"],
            "entries": computed["entries"],
            "activations": computed["activations"],
            "deauthorizations": computed["deauthorizations"],
            "terminal_events": computed["terminal_events"],
            "terminal_signal_authority": computed["terminal_signal_authority"],
        },
    }


def cleanup_manager(manager: candidate.ManagedExclusiveLease) -> None:
    manager.owned_lock.detach_without_unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    if args.work_root.exists() or args.work_root.is_symlink():
        raise SystemExit("work root already exists")
    if args.receipt.exists() or args.receipt.is_symlink():
        raise SystemExit("receipt already exists")
    args.work_root.mkdir(parents=True)
    verifier = load_module(
        PROJECT / "tools/managed_exclusive_lease_verify.py",
        "managed_exclusive_lease_verify_frozen",
    )
    controls: dict[str, bool] = {}

    normal_a = lifecycle(args.work_root, "normal-a", verifier)
    normal_b = lifecycle(args.work_root, "normal-b", verifier)
    normalized_a = normalized_lifecycle(normal_a)
    normalized_b = normalized_lifecycle(normal_b)
    controls["normal_lifecycle_pass"] = normal_a["released"] and normal_a["verified"]
    controls["reacquire_pass"] = normal_b["released"] and normal_b["verified"]
    controls["normalized_repeat_pass"] = normalized_a == normalized_b
    controls["schema_transition_identity_pass"] = (
        normal_a["transition_schema"] == "managed-exclusive-lease-transition-log.v1"
        and normal_b["transition_schema"] == "managed-exclusive-lease-transition-log.v1"
        and normal_a["verification"]["schema_version"]
        == "managed-exclusive-lease-verification.v1"
        and normal_b["verification"]["schema_version"]
        == "managed-exclusive-lease-verification.v1"
    )

    directory = args.work_root / "foreign-lock"
    directory.mkdir()
    lease = directory / "exclusive.json"
    lock = directory / "exclusive.json.lock"
    transition = directory / "transitions.json"
    write_new(lock, b"foreign-lock\n")
    before = identity(lock)
    collision = reject(lambda: acquire(lease, transition, "foreign-lock"))
    controls["foreign_lock_collision_preserved"] = collision and unchanged(lock, before)
    lock.unlink()

    directory = args.work_root / "manager-collision"
    directory.mkdir()
    lease = directory / "exclusive.json"
    lock = directory / "exclusive.json.lock"
    transition_a = directory / "transitions-a.json"
    transition_b = directory / "transitions-b.json"
    terminal = directory / "terminal.json"
    first = acquire(lease, transition_a, "manager-first")
    lease_before = identity(lease)
    lock_before = identity(lock)
    collision = reject(lambda: acquire(lease, transition_b, "manager-second"))
    controls["manager_collision_preserved"] = (
        collision and unchanged(lease, lease_before) and unchanged(lock, lock_before)
    )
    first.release(evidence_path=terminal)

    directory = args.work_root / "lease-symlink"
    directory.mkdir()
    lease = directory / "exclusive.json"
    transition = directory / "transitions.json"
    lease.symlink_to(directory / "missing-target")
    controls["lease_symlink_rejected"] = reject(
        lambda: acquire(lease, transition, "lease-symlink")
    ) and lease.is_symlink()
    lease.unlink()

    directory = args.work_root / "lock-symlink"
    directory.mkdir()
    lease = directory / "exclusive.json"
    lock = directory / "exclusive.json.lock"
    transition = directory / "transitions.json"
    lock.symlink_to(directory / "missing-target")
    controls["lock_symlink_rejected"] = reject(
        lambda: acquire(lease, transition, "lock-symlink")
    ) and lock.is_symlink()
    lock.unlink()

    directory = args.work_root / "post-acquire-lease"
    directory.mkdir()
    lease = directory / "exclusive.json"
    lock = directory / "exclusive.json.lock"
    owned = candidate._OwnedLock.acquire(lease)
    write_new(lease, b"foreign-lease\n")
    rejected = reject(lambda: owned.publish_lease(b"candidate-lease\n"))
    owned.unlink_owned_lock()
    controls["post_acquire_lease_preserved"] = (
        rejected and lease.read_bytes() == b"foreign-lease\n" and not lock.exists()
    )
    lease.unlink()

    directory = args.work_root / "inode-substitution"
    directory.mkdir()
    lease = directory / "exclusive.json"
    lock = directory / "exclusive.json.lock"
    transition = directory / "transitions.json"
    terminal = directory / "terminal.json"
    manager = acquire(lease, transition, "inode-substitution")
    saved = directory / "owned.saved"
    lock.rename(saved)
    write_new(lock, b"replacement\n")
    controls["inode_substitution_rejected"] = reject(
        lambda: manager.release(evidence_path=terminal)
    ) and lock.read_bytes() == b"replacement\n"
    cleanup_manager(manager)
    lock.unlink()
    saved.unlink()
    lease.unlink()

    directory = args.work_root / "hardlink-substitution"
    directory.mkdir()
    lease = directory / "exclusive.json"
    lock = directory / "exclusive.json.lock"
    transition = directory / "transitions.json"
    terminal = directory / "terminal.json"
    manager = acquire(lease, transition, "hardlink-substitution")
    hardlink = directory / "owned.link"
    os.link(lock, hardlink, follow_symlinks=False)
    controls["hardlink_substitution_rejected"] = reject(
        lambda: manager.release(evidence_path=terminal)
    ) and lock.samefile(hardlink)
    cleanup_manager(manager)
    lock.unlink()
    hardlink.unlink()
    lease.unlink()

    directory = args.work_root / "token-substitution"
    directory.mkdir()
    lease = directory / "exclusive.json"
    lock = directory / "exclusive.json.lock"
    transition = directory / "transitions.json"
    terminal = directory / "terminal.json"
    manager = acquire(lease, transition, "token-substitution")
    descriptor = os.open(lock, os.O_WRONLY | os.O_TRUNC | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        os.write(descriptor, b"changed\n")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    controls["token_substitution_rejected"] = reject(
        lambda: manager.release(evidence_path=terminal)
    ) and lock.read_bytes() == b"changed\n"
    cleanup_manager(manager)
    lock.unlink()
    lease.unlink()

    directory = args.work_root / "partial-publication"
    directory.mkdir()
    lease = directory / "exclusive.json"
    lock = directory / "exclusive.json.lock"
    blocker = directory / "not-a-directory"
    write_new(blocker, b"blocker\n")
    transition = blocker / "transitions.json"
    failed = reject(lambda: acquire(lease, transition, "partial-publication"))
    controls["partial_failure_remains_occupied"] = failed and lease.exists() and lock.exists()
    lease.unlink()
    lock.unlink()

    all_pass = len(controls) == 13 and all(controls.values())
    output = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "controls": controls,
        "normal_a": normalized_a,
        "normal_b": normalized_b,
        "all_controls_pass": all_pass,
        "claim_authority": "infrastructure_only",
        "execution_authority": False,
        "promotion_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    raw = (json.dumps(output, sort_keys=True, indent=2) + "\n").encode("ascii")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    write_new(args.receipt, raw)
    print(json.dumps(output, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
