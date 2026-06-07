"""Wrapper for the counted morphic integer online context arithmetic prototype."""

from __future__ import annotations

import lzma
import os
import pathlib
import subprocess
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
_BIN_XZ = _HERE / "qm.xz"
_CACHE = pathlib.Path(tempfile.gettempdir()) / f"qmctx3-{os.getpid()}"
_BIN = _CACHE / "qm"


def _binary() -> pathlib.Path:
    _CACHE.mkdir(exist_ok=True)
    if not _BIN.exists():
        _BIN.write_bytes(lzma.decompress(_BIN_XZ.read_bytes()))
        _BIN.chmod(0o755)
    return _BIN


def _run(flag: str, data: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        src = root / "in"
        dst = root / "out"
        src.write_bytes(data)
        subprocess.run(
            [str(_binary()), flag, str(src), str(dst)],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return dst.read_bytes()


def compress(data: bytes) -> bytes:
    return _run("-c", data)


def decompress(blob: bytes) -> bytes:
    return _run("-d", blob)
