"""sidecar_mix_cmix_v1.

Modified fx2-cmix with deterministic MediaWiki sidecar contexts wired into
the live mixer path only. The sibling cmix.bin.gz is counted by the local
harness.
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
_extracted: pathlib.Path | None = None


def _binary() -> pathlib.Path:
    global _extracted
    if _extracted is not None and _extracted.exists():
        return _extracted
    fd, path = tempfile.mkstemp(prefix="sidecar-mix-cmix-", suffix=".bin")
    os.close(fd)
    p = pathlib.Path(path)
    with gzip.open(_BIN_GZ, "rb") as src:
        p.write_bytes(src.read())
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    _extracted = p
    return p


def _run(flag: str, data: bytes) -> bytes:
    binary = _binary()
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        with open(src, "wb") as f:
            f.write(data)
        subprocess.run(
            [str(binary), flag, src, dst],
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
