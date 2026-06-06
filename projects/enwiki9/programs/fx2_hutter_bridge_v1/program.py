from __future__ import annotations

import lzma
import os
import pathlib
import shutil
import stat
import subprocess
import tempfile

_DIR = pathlib.Path(__file__).resolve().parent
_BIN_XZ = _DIR / "cmix.bin.xz"
_FULL_ENWIK9_BYTES = 1_000_000_000
_MODE_CMIX = b"C"
_MODE_FX2 = b"F"
_bin_cache: pathlib.Path | None = None


def _binary() -> pathlib.Path:
    global _bin_cache
    if _bin_cache is not None and _bin_cache.exists():
        return _bin_cache
    fd, path = tempfile.mkstemp(prefix="fx2-hutter-cmix-", suffix=".bin")
    os.close(fd)
    p = pathlib.Path(path)
    p.write_bytes(lzma.decompress(_BIN_XZ.read_bytes()))
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    _bin_cache = p
    return p


def _run_cmix(flag: str, data: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        src = root / "in"
        dst = root / "out"
        src.write_bytes(data)
        subprocess.run(
            [str(_binary()), flag, str(src), str(dst)],
            cwd=root,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return dst.read_bytes()


def _run_fx2(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        cmix = root / "cmix"
        shutil.copy2(_binary(), cmix)
        cmix.chmod(cmix.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        src = root / "enwik9"
        src.write_bytes(data)
        subprocess.run(
            [str(cmix), "-e", str(src), "enwik9.comp"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return (root / "archive9").read_bytes()


def _decode_fx2(archive: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        arch = root / "archive9"
        arch.write_bytes(archive)
        arch.chmod(arch.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        subprocess.run(
            [str(arch)],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        out = root / "enwik9_uncompressed"
        if not out.exists():
            out = root / "enwik9_restored"
        return out.read_bytes()


def compress(data: bytes) -> bytes:
    if len(data) == _FULL_ENWIK9_BYTES:
        return _MODE_FX2 + _run_fx2(data)
    return _MODE_CMIX + _run_cmix("-c", data)


def decompress(archive: bytes) -> bytes:
    mode = archive[:1]
    body = archive[1:]
    if mode == _MODE_FX2:
        return _decode_fx2(body)
    if mode == _MODE_CMIX:
        return _run_cmix("-d", body)
    raise ValueError("unknown archive mode")
