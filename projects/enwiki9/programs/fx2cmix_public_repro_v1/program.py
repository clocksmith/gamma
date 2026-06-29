"""Full-enwik9 wrapper for the published fx2-cmix archive9 path.

This is deliberately not a prefix-test wrapper. Upstream fx2-cmix `-e` uses
fixed split/reorder constants for enwik9 and emits a self-extracting `archive9`
binary. The normal project driver can import this module, but a streaming
full-corpus runner is preferred for Lane 0 because it avoids holding enwik9 in
Python memory.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import tempfile


FULL_ENWIK9_BYTES = 1_000_000_000
_HERE = pathlib.Path(__file__).resolve().parent
_BIN = _HERE / "cmix"


def _require_full(data: bytes) -> None:
    if len(data) != FULL_ENWIK9_BYTES:
        raise ValueError(
            "fx2cmix_public_repro_v1 only supports the full enwik9 corpus; "
            "prefix gates are invalid for the upstream -e/archive9 path"
        )


def _stage_binary(root: pathlib.Path) -> pathlib.Path:
    if not _BIN.exists():
        raise FileNotFoundError(
            f"missing {_BIN}; run fx2_public_repro_queue.py --prepare after "
            "building external/fx2-cmix/run/cmix"
        )
    staged = root / "cmix"
    shutil.copy2(_BIN, staged)
    os.chmod(staged, 0o755)
    return staged


def compress(data: bytes) -> bytes:
    _require_full(data)
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        _stage_binary(root)
        source = root / "enwik9"
        source.write_bytes(data)
        subprocess.run(
            ["./cmix", "-e", "enwik9", "enwik9.comp"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return (root / "archive9").read_bytes()


def decompress(blob: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        archive = root / "archive9"
        archive.write_bytes(blob)
        os.chmod(archive, 0o755)
        subprocess.run(
            ["./archive9"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return (root / "enwik9_uncompressed").read_bytes()
