"""cmix21 with decoder-built wiki sidecar direct and page-match contexts.

The cmix binary and dictionary are stored gzip-compressed beside this file and
counted by the harness. This build keeps cmix21's byte stream unchanged and
adds semantic direct models plus page/shape sidecar match contexts.
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
_DICT_GZ = _DIR / "english.dic.gz"
_extracted_bin: pathlib.Path | None = None
_extracted_dict: pathlib.Path | None = None


def _extract(src: pathlib.Path, prefix: str, executable: bool) -> pathlib.Path:
    fd, path = tempfile.mkstemp(prefix=prefix)
    os.close(fd)
    out = pathlib.Path(path)
    with gzip.open(src, "rb") as inp:
        out.write_bytes(inp.read())
    if executable:
        out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return out


def _binary() -> pathlib.Path:
    global _extracted_bin
    if _extracted_bin is None or not _extracted_bin.exists():
        _extracted_bin = _extract(_BIN_GZ, "cmix21-sidecar-bin-", True)
    return _extracted_bin


def _dictionary() -> pathlib.Path:
    global _extracted_dict
    if _extracted_dict is None or not _extracted_dict.exists():
        _extracted_dict = _extract(_DICT_GZ, "cmix21-sidecar-dict-", False)
    return _extracted_dict


def _run(flag: str, data: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        with open(src, "wb") as f:
            f.write(data)
        subprocess.run(
            [str(_binary()), flag, str(_dictionary()), src, dst],
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
