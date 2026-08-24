#!/usr/bin/env python3
"""Run guard v3 with a verified cgroup memory.high pressure boundary."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


SCHEMA = "gamma.enwiki9.resource-guard-soft-high.v1"
REQUESTED_MEMORY_HIGH_BYTES = 9_000_000_000
EXPECTED_GUARD_SHA256 = "044147f7ffe6922ea8dafd52fc3d4426077b20958adbcd421245ad41adcfc1e4"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def option_value(arguments: list[str], option: str) -> str:
    positions = [index for index, value in enumerate(arguments) if value == option]
    if len(positions) != 1 or positions[0] + 1 >= len(arguments):
        raise RuntimeError(f"expected exactly one {option}")
    return arguments[positions[0] + 1]


def write_new(path: Path, value: dict[str, Any]) -> None:
    data = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600
    )
    try:
        cursor = 0
        while cursor < len(data):
            written = os.write(descriptor, data[cursor:])
            if written <= 0:
                raise OSError(f"short write: {path}")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    arguments = sys.argv[1:]
    cgroup = Path(option_value(arguments, "--cgroup-path")).resolve(strict=True)
    guard_json_argument = Path(option_value(arguments, "--guard-json")).absolute()
    if not guard_json_argument.parent.resolve(strict=True).is_dir():
        raise RuntimeError("guard receipt parent must exist")
    sidecar = guard_json_argument.with_name("soft-high-receipt.json")
    if sidecar.exists() or sidecar.is_symlink():
        raise RuntimeError(f"soft-high sidecar must be absent: {sidecar}")
    if any(cgroup.joinpath(name).read_text().strip() for name in ("cgroup.procs",)):
        raise RuntimeError("dedicated cgroup must be empty before soft-high setup")
    memory_high_path = cgroup / "memory.high"
    if not memory_high_path.is_file():
        raise RuntimeError(f"memory.high is unavailable: {memory_high_path}")
    underlying = Path(__file__).with_name("run_with_resource_guard_v3.py").resolve(strict=True)
    if sha256_file(underlying) != EXPECTED_GUARD_SHA256:
        raise RuntimeError("underlying resource guard v3 identity drift")

    previous_memory_high = memory_high_path.read_text().strip()
    guard_return_code: int | None = None
    restore_pass = False
    error: str | None = None
    effective_memory_high = 0
    try:
        memory_high_path.write_text(f"{REQUESTED_MEMORY_HIGH_BYTES}\n")
        effective_memory_high = int(memory_high_path.read_text().strip())
        page_size = os.sysconf("SC_PAGE_SIZE")
        rounding = REQUESTED_MEMORY_HIGH_BYTES - effective_memory_high
        if rounding < 0 or rounding >= page_size:
            raise RuntimeError(
                "memory.high did not bind to a page-rounded safe boundary: "
                f"requested={REQUESTED_MEMORY_HIGH_BYTES} effective={effective_memory_high}"
            )
        completed = subprocess.run(
            ["/usr/bin/python3", str(underlying), *arguments], check=False
        )
        guard_return_code = completed.returncode
    except (OSError, RuntimeError, ValueError) as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            memory_high_path.write_text(f"{previous_memory_high}\n")
            restore_pass = memory_high_path.read_text().strip() == previous_memory_high
        except OSError as exc:
            restore_pass = False
            if error is None:
                error = f"{type(exc).__name__}: restore memory.high: {exc}"

    guard_record: dict[str, Any] | None = None
    guard_status: str | None = None
    high_event_count: int | None = None
    if guard_json_argument.is_file():
        guard_record = artifact(guard_json_argument)
        guard = json.loads(guard_json_argument.read_text())
        guard_status = guard.get("status")
        high_event_count = guard.get("cgroup_events", {}).get("delta", {}).get("high")
    rounding = (
        REQUESTED_MEMORY_HIGH_BYTES - effective_memory_high
        if effective_memory_high > 0
        else None
    )
    wrapper_pass = (
        error is None
        and guard_return_code is not None
        and guard_record is not None
        and restore_pass
        and effective_memory_high > 0
    )
    receipt = {
        "schema": SCHEMA,
        "underlying_guard": artifact(underlying),
        "cgroup_path": str(cgroup),
        "cgroup_inode": cgroup.stat().st_ino,
        "previous_memory_high": previous_memory_high,
        "requested_memory_high_bytes": REQUESTED_MEMORY_HIGH_BYTES,
        "effective_memory_high_bytes": effective_memory_high or None,
        "memory_high_rounding_bytes": rounding,
        "memory_high_restore_pass": restore_pass,
        "guard_return_code": guard_return_code,
        "guard_receipt": guard_record,
        "guard_status": guard_status,
        "high_event_count": high_event_count,
        "errors": [] if error is None else [error],
        "wrapper_pass": wrapper_pass,
        "claim_boundary": (
            "Resource-pressure control only. memory.high may trigger reclaim or throttling, "
            "but it does not change codec inputs, outputs, probability arithmetic, or the "
            "unchanged 10,000,000,000-byte hard memory.max boundary."
        ),
    }
    write_new(sidecar, receipt)
    if not wrapper_pass:
        return 76
    return int(guard_return_code)


if __name__ == "__main__":
    raise SystemExit(main())
