"""Score-honest wrapper around the recovered fx2-cmix source build."""

from __future__ import annotations

import os
import pathlib
import subprocess
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
_BIN = _HERE / "cmix"
_DICT = _HERE / "english.dic"


def _run(args: list[str], cwd: pathlib.Path) -> None:
    subprocess.run(
        args,
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )


def _cmix(flag: str, data: bytes) -> bytes:
    os.chmod(_BIN, 0o755)
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        src = root / "in"
        dst = root / "out"
        src.write_bytes(data)
        _run([str(_BIN), flag, str(_DICT), str(src), str(dst)], root)
        return dst.read_bytes()


def compress(data: bytes) -> bytes:
    return _cmix("-c", data)


def decompress(blob: bytes) -> bytes:
    return _cmix("-d", blob)
