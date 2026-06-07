"""Recovered fx2-cmix GCC build with xz-packed executable and dictionary."""

from __future__ import annotations

import lzma
import os
import pathlib
import subprocess
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
_BIN_XZ = _HERE / "cmix.xz"
_DICT_XZ = _HERE / "english.dic.xz"
_CACHE = pathlib.Path(tempfile.gettempdir()) / f"fx2rec-{os.getpid()}"
_BIN = _CACHE / "cmix"
_DICT = _CACHE / "english.dic"


def _ensure() -> tuple[pathlib.Path, pathlib.Path]:
    _CACHE.mkdir(exist_ok=True)
    if not _BIN.exists():
        _BIN.write_bytes(lzma.decompress(_BIN_XZ.read_bytes()))
        _BIN.chmod(0o755)
    if not _DICT.exists():
        _DICT.write_bytes(lzma.decompress(_DICT_XZ.read_bytes()))
    return _BIN, _DICT


def _run(flag: str, data: bytes) -> bytes:
    binary, dictionary = _ensure()
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        src = root / "in"
        dst = root / "out"
        src.write_bytes(data)
        subprocess.run(
            [str(binary), flag, str(dictionary), str(src), str(dst)],
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
