#!/usr/bin/env python3
"""Bind delegated CMIX runs to a receiptable disk-backed scratch root."""

from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile as standard_tempfile
from typing import Any


MEMORY_FILESYSTEMS = {"tmpfs", "ramfs"}
DEFAULT_ROOT = Path(
    os.environ.get("GAMMA_ENWIK9_DISK_SCRATCH", "/home/x/enwiki9-scratch")
)


def _unescape_mount(value: str) -> str:
    return re.sub(
        r"\\([0-7]{3})",
        lambda match: chr(int(match.group(1), 8)),
        value,
    )


def mount_manifest(root: Path) -> dict[str, object]:
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    resolved = root.resolve(strict=True)
    candidates: list[tuple[int, Path, str, str, str]] = []
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        left, separator, right = line.partition(" - ")
        if not separator:
            continue
        left_fields = left.split()
        right_fields = right.split()
        if len(left_fields) < 6 or len(right_fields) < 2:
            continue
        mount_point = Path(_unescape_mount(left_fields[4]))
        try:
            resolved.relative_to(mount_point)
        except ValueError:
            continue
        candidates.append(
            (
                len(str(mount_point)),
                mount_point,
                right_fields[0],
                _unescape_mount(right_fields[1]),
                left_fields[5],
            )
        )
    if not candidates:
        raise RuntimeError(f"no mountinfo entry contains scratch root {resolved}")
    _, mount_point, filesystem, source, options = max(candidates)
    if filesystem in MEMORY_FILESYSTEMS:
        raise RuntimeError(
            f"scratch root {resolved} is on forbidden memory filesystem {filesystem}"
        )
    stat = os.statvfs(resolved)
    return {
        "root": str(resolved),
        "mount_point": str(mount_point),
        "source": source,
        "filesystem": filesystem,
        "mount_options": options,
        "memory_backed": False,
        "available_bytes_before": stat.f_bavail * stat.f_frsize,
    }


def bind_qm0(qm0: Any, root: Path = DEFAULT_ROOT) -> dict[str, object]:
    manifest = mount_manifest(root)
    resolved = Path(str(manifest["root"]))
    original_temporary_directory = qm0.tempfile.TemporaryDirectory

    class DiskTempfileProxy:
        @staticmethod
        def TemporaryDirectory(*args: object, **kwargs: object) -> object:
            adjusted = dict(kwargs)
            adjusted["dir"] = str(resolved)
            return original_temporary_directory(*args, **adjusted)

    qm0.tempfile = DiskTempfileProxy()
    standard_tempfile.tempdir = str(resolved)
    os.environ["TMPDIR"] = str(resolved)
    return manifest
