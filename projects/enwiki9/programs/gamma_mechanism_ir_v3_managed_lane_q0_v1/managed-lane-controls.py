#!/usr/bin/env python3
"""Exercise frozen local controls for the managed-lane ownership primitive."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Callable

from managed_lane import LaneError, OwnedNamespaceLock, load_tool, require_clear


CANDIDATE_ID = "gamma_mechanism_ir_v3_managed_lane_q0_v1"
SCHEMA = "gamma.enwiki9.mechanism-ir-managed-lane-controls.v1"
PROJECT = Path(__file__).resolve().parents[2]


def write_new(path: Path, raw: bytes) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
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


def reject(operation: Callable[[], object]) -> bool:
    try:
        operation()
    except LaneError:
        return True
    return False


def namespace(root: Path, name: str) -> tuple[Path, Path, Path]:
    directory = root / name
    directory.mkdir()
    lease = directory / "exclusive.json"
    lock = directory / "exclusive.json.lock"
    return directory, lease, lock


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exclusive-lease", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    if args.work_root.exists() or args.work_root.is_symlink():
        raise SystemExit("work root already exists")
    if args.receipt.exists() or args.receipt.is_symlink():
        raise SystemExit("receipt already exists")
    require_clear(args.exclusive_lease)
    args.work_root.mkdir(parents=True)
    controls: dict[str, bool] = {}

    with OwnedNamespaceLock.acquire(args.exclusive_lease):
        _, lease, lock = namespace(args.work_root, "released")
        guard = OwnedNamespaceLock.acquire(lease)
        guard.assert_owned(lease)
        guard.release()
        controls["released_state_accepts"] = not lease.exists() and not lock.exists()

        _, lease, lock = namespace(args.work_root, "live-lease")
        write_new(lease, b"{}\n")
        controls["live_lease_rejected"] = reject(lambda: OwnedNamespaceLock.acquire(lease)) and not lock.exists()
        lease.unlink()

        _, lease, lock = namespace(args.work_root, "orphan-lock")
        write_new(lock, b"orphan\n")
        controls["orphan_lock_rejected"] = reject(lambda: OwnedNamespaceLock.acquire(lease)) and not lease.exists()
        lock.unlink()

        directory, lease, lock = namespace(args.work_root, "lease-symlink")
        target = directory / "target"
        lease.symlink_to(target)
        controls["lease_symlink_rejected"] = reject(lambda: OwnedNamespaceLock.acquire(lease)) and lease.is_symlink()
        lease.unlink()

        directory, lease, lock = namespace(args.work_root, "lock-symlink")
        target = directory / "target"
        lock.symlink_to(target)
        controls["lock_symlink_rejected"] = reject(lambda: OwnedNamespaceLock.acquire(lease)) and lock.is_symlink()
        lock.unlink()

        _, lease, lock = namespace(args.work_root, "post-acquire-lease")
        guard = OwnedNamespaceLock.acquire(lease)
        write_new(lease, b"appeared\n")
        controls["post_acquire_lease_rejected"] = reject(guard.release) and not lock.exists()
        lease.unlink()

        directory, lease, lock = namespace(args.work_root, "inode-substitution")
        guard = OwnedNamespaceLock.acquire(lease)
        saved = directory / "owned.saved"
        lock.rename(saved)
        write_new(lock, b"replacement\n")
        controls["lock_inode_substitution_rejected"] = reject(guard.release) and lock.read_bytes() == b"replacement\n"
        lock.unlink()
        saved.unlink()

        _, lease, lock = namespace(args.work_root, "token-substitution")
        guard = OwnedNamespaceLock.acquire(lease)
        descriptor = os.open(lock, os.O_WRONLY | os.O_TRUNC | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            os.write(descriptor, b"changed\n")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        controls["lock_token_substitution_rejected"] = reject(guard.release) and lock.read_bytes() == b"changed\n"
        lock.unlink()

        directory, lease, lock = namespace(args.work_root, "hardlink-substitution")
        guard = OwnedNamespaceLock.acquire(lease)
        hardlink = directory / "owned.link"
        os.link(lock, hardlink, follow_symlinks=False)
        controls["lock_hardlink_rejected"] = reject(guard.release) and lock.samefile(hardlink)
        lock.unlink()
        hardlink.unlink()

        directory, lease, lock = namespace(args.work_root, "canonical-manager-collision")
        transition = directory / "transitions.json"
        guard = OwnedNamespaceLock.acquire(lease)
        manager = load_tool(
            PROJECT,
            "managed_exclusive_lease.py",
            "managed_exclusive_lease_frozen_collision_control",
        )
        collision_rejected = False
        try:
            manager.ManagedExclusiveLease.acquire(
                lease_path=lease,
                transition_path=transition,
                candidate_id="foreign-lock-collision-control",
                command_sha256="0" * 64,
                runner_sha256="1" * 64,
                guard_path="control/guard.json",
                result_path="control/result.json",
                scratch_path="control/scratch",
                claim_boundary="must not delete a foreign acquisition lock",
            )
        except Exception:
            collision_rejected = True
        lock_preserved = lock.exists() and not lock.is_symlink()
        controls["canonical_manager_foreign_lock_preserved"] = (
            collision_rejected and lock_preserved
        )
        if lock_preserved:
            guard.release()
        else:
            reject(guard.release)

        _, lease, lock = namespace(args.work_root, "wrapped-failure")
        guard = OwnedNamespaceLock.acquire(lease)
        wrapped_failed = False
        try:
            raise RuntimeError("frozen wrapped-operation failure control")
        except RuntimeError:
            wrapped_failed = True
        finally:
            guard.release()
        controls["wrapped_failure_cleanup_pass"] = wrapped_failed and not lease.exists() and not lock.exists()

    require_clear(args.exclusive_lease)
    all_pass = len(controls) == 11 and all(controls.values())
    output = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "controls": controls,
        "all_controls_pass": all_pass,
        "canonical_namespace_clean_after_pass": True,
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
