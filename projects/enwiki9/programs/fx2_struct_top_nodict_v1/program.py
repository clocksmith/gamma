"""fx2_struct_top_nodict_v1.

Score-honest wrapper around the context-6 LTO fx2-cmix build, using native
no-dictionary mode to avoid shipping the 175 KB WRT dictionary.
"""

from __future__ import annotations

import gzip
import os
import pathlib
import stat
import subprocess
import tempfile

_DIR = pathlib.Path(__file__).resolve().parent
_BIN_GZ = _DIR / "cmix.bin.gz"
_extracted_bin: pathlib.Path | None = None


def _extract_binary() -> pathlib.Path:
    global _extracted_bin
    if _extracted_bin is not None and _extracted_bin.exists():
        return _extracted_bin
    fd, path = tempfile.mkstemp(prefix="fx2-struct-top-nodict-cmix-")
    os.close(fd)
    p = pathlib.Path(path)
    with gzip.open(_BIN_GZ, "rb") as inp:
        p.write_bytes(inp.read())
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    _extracted_bin = p
    return p


def _run(flag: str, data: bytes) -> bytes:
    binary = _extract_binary()
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        with open(src, "wb") as f:
            f.write(data)
        subprocess.run(
            [str(binary), flag, src, dst],
            cwd=td,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with open(dst, "rb") as f:
            return f.read()


def compress(data: bytes) -> bytes:
    return _run("-c", data)


def decompress(data: bytes) -> bytes:
    return _run("-d", data)
