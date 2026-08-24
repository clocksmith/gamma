#!/usr/bin/env python3
"""Exercise SAFE-MIX v2 activation primitives in a synthetic namespace."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any, Callable

import activation_gate as gate


CANDIDATE_ID = "gamma_safe_mix_v2"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rejected(operation: Callable[[], Any]) -> bool:
    try:
        operation()
    except Exception:
        return True
    return False


def write_new(path: Path, value: dict[str, Any]) -> None:
    raw = canonical(value)
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
                raise OSError("short activation-controls receipt write")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_fake_process(proc_root: Path, pid: int, command: bytes) -> None:
    process = proc_root / str(pid)
    process.mkdir(mode=0o700)
    fields = ["S", "1", *("0" for _ in range(17)), "12345"]
    (process / "stat").write_text(
        f"{pid} (synthetic) {' '.join(fields)}\n",
        encoding="ascii",
    )
    (process / "cmdline").write_bytes(command)


def unlink_if_present(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    if args.root.exists() or args.root.is_symlink():
        raise FileExistsError(args.root)
    args.root.mkdir(mode=0o700)
    root = args.root.resolve(strict=True)
    receipt = Path(os.path.abspath(args.receipt))
    try:
        receipt.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("activation-controls receipt must be outside the scratch root")
    controls: dict[str, bool] = {}

    controls["dormant_plan_rejected"] = rejected(gate.validate_plan)

    namespace = root / "namespace"
    namespace.mkdir(mode=0o700)
    absent = namespace / "absent"
    gate.require_absent(absent, "synthetic absent path")
    controls["absent_path_accepted"] = True
    regular_path = namespace / "regular"
    regular_path.write_bytes(b"occupied\n")
    controls["regular_path_rejected"] = rejected(
        lambda: gate.require_absent(regular_path, "synthetic regular path")
    )
    directory_path = namespace / "directory"
    directory_path.mkdir(mode=0o700)
    controls["directory_path_rejected"] = rejected(
        lambda: gate.require_absent(directory_path, "synthetic directory path")
    )
    symlink_path = namespace / "symlink"
    symlink_path.symlink_to(namespace / "missing-target")
    controls["dangling_symlink_rejected"] = rejected(
        lambda: gate.require_absent(symlink_path, "synthetic symlink path")
    )

    normal_path = namespace / "normal.lock"
    normal = gate.OwnedLock.acquire(normal_path)
    normal_witness = normal.witness()
    controls["second_owner_collision_rejected"] = rejected(
        lambda: gate.OwnedLock.acquire(normal_path)
    )
    normal.release()
    controls["normal_owned_release_pass"] = (
        not normal_path.exists()
        and not normal_path.is_symlink()
        and normal_witness["payload_bytes"] > 0
    )

    replacement_path = namespace / "replacement.lock"
    displaced_path = namespace / "displaced.lock"
    replacement = gate.OwnedLock.acquire(replacement_path)
    replacement_path.rename(displaced_path)
    replacement_path.write_bytes(b"foreign replacement\n")
    replacement_metadata = replacement_path.stat()
    controls["replacement_release_rejected"] = rejected(replacement.release)
    controls["replacement_preserved"] = (
        replacement_path.read_bytes() == b"foreign replacement\n"
        and replacement_path.stat().st_ino == replacement_metadata.st_ino
        and displaced_path.is_file()
    )
    unlink_if_present(replacement_path)
    unlink_if_present(displaced_path)

    token_path = namespace / "token.lock"
    token = gate.OwnedLock.acquire(token_path)
    os.pwrite(token.lock_descriptor, b"X", 0)
    controls["token_mutation_release_rejected"] = rejected(token.release)
    controls["token_mutation_preserved"] = token_path.is_file()
    unlink_if_present(token_path)

    hardlink_path = namespace / "hardlink.lock"
    hardlink_alias = namespace / "hardlink.alias"
    hardlink = gate.OwnedLock.acquire(hardlink_path)
    os.link(hardlink_path, hardlink_alias)
    controls["hardlink_release_rejected"] = rejected(hardlink.release)
    controls["hardlink_population_preserved"] = (
        hardlink_path.is_file()
        and hardlink_alias.is_file()
        and hardlink_path.stat().st_nlink == 2
    )
    unlink_if_present(hardlink_alias)
    unlink_if_present(hardlink_path)

    fake_proc = root / "proc"
    fake_proc.mkdir(mode=0o700)
    write_fake_process(
        fake_proc,
        101,
        b"python3\0tools/cmix_filebacked_fxcm_full_roundtrip.py\0"
        b"--result-root\0results/cmix_filebacked_fxcm_full_a_qm8_v1\0",
    )
    write_fake_process(fake_proc, 102, b"python3\0unrelated.py\0")
    observed = gate.live_qm8_processes(fake_proc)
    controls["live_qm8_detected"] = (
        len(observed) == 1
        and observed[0]["pid"] == 101
        and observed[0]["start_ticks"] == 12345
    )
    (fake_proc / "101/cmdline").write_bytes(b"python3\0unrelated.py\0")
    controls["unrelated_process_ignored"] = gate.live_qm8_processes(fake_proc) == []

    binding_root = root / "bindings"
    binding_root.mkdir(mode=0o700)
    bound = binding_root / "bound.json"
    bound.write_bytes(b"{}\n")
    record = {
        "path": str(bound),
        "bytes": bound.stat().st_size,
        "sha256": sha256(bound),
    }
    controls["exact_binding_pass"] = gate.resolve_binding(record, "synthetic binding") == bound
    changed = dict(record)
    changed["sha256"] = "0" * 64
    controls["hash_drift_rejected"] = rejected(
        lambda: gate.resolve_binding(changed, "synthetic hash drift")
    )
    alias = binding_root / "alias.json"
    alias.symlink_to(bound)
    aliased = dict(record)
    aliased["path"] = str(alias)
    controls["binding_symlink_rejected"] = rejected(
        lambda: gate.resolve_binding(aliased, "synthetic symlink binding")
    )

    all_pass = all(controls.values())
    output = {
        "schema": "gamma.enwiki9.safe-mix-v2-activation-controls.v1",
        "candidate_id": CANDIDATE_ID,
        "input_lock": {
            "activation_gate_sha256": sha256(Path(gate.__file__).resolve(strict=True)),
            "controls_sha256": sha256(Path(__file__).resolve(strict=True)),
            "python_executable_sha256": sha256(Path(sys.executable).resolve(strict=True)),
        },
        "controls": controls,
        "all_controls_pass": all_pass,
        "execution_authority": False,
        "archive_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    write_new(receipt, output)
    shutil.rmtree(root)
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
