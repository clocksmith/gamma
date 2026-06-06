from __future__ import annotations

import lzma
import os
import pathlib
import re
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
_PAGE_OPEN = b"  <page>\n"
_PAGE_CLOSE = b"  </page>\n"


def _binary() -> pathlib.Path:
    global _bin_cache
    if _bin_cache is not None and _bin_cache.exists():
        return _bin_cache
    fd, path = tempfile.mkstemp(prefix="fx2-topic-cmix-", suffix=".bin")
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


def _page_id(page: bytes, fallback: int) -> int:
    m = re.search(rb"<id>(\d+)</id>", page)
    return int(m.group(1)) if m else 10**18 + fallback


def _field(page: bytes, pat: bytes) -> bytes:
    m = re.search(pat, page, re.S | re.I)
    return m.group(1) if m else b""


def _norm(v: bytes) -> bytes:
    return re.sub(rb"[^a-z0-9]+", b" ", v.lower()).strip()[:120]


def _topic_key(page: bytes) -> bytes:
    return _norm(
        _field(page, rb"\[\[Category:([^\]\|\n]{1,80})")
        or _field(page, rb"\{\{([^\|\}\n]{1,80})")
        or _field(page, rb"<title>(.*?)</title>")
    )


def _topic_order(data: bytes) -> bytes | None:
    first = data.find(_PAGE_OPEN)
    if first < 0:
        return None
    pages: list[bytes] = []
    pos = first
    while True:
        start = data.find(_PAGE_OPEN, pos)
        if start < 0:
            break
        end = data.find(_PAGE_CLOSE, start)
        if end < 0:
            break
        end += len(_PAGE_CLOSE)
        pages.append(data[start:end])
        pos = end
    ids = [_page_id(page, i) for i, page in enumerate(pages)]
    if not pages or ids != sorted(ids) or len(ids) != len(set(ids)):
        return None
    order = sorted(range(len(pages)), key=lambda i: (_topic_key(pages[i]), ids[i]))
    return data[:first] + b"".join(pages[i] for i in order) + data[pos:]


def _restore_id_order(data: bytes) -> bytes:
    first = data.find(_PAGE_OPEN)
    if first < 0:
        return data
    pages: list[bytes] = []
    pos = first
    while True:
        start = data.find(_PAGE_OPEN, pos)
        if start < 0:
            break
        end = data.find(_PAGE_CLOSE, start)
        if end < 0:
            break
        end += len(_PAGE_CLOSE)
        pages.append(data[start:end])
        pos = end
    ids = [_page_id(page, i) for i, page in enumerate(pages)]
    if not pages or len(ids) != len(set(ids)):
        return data
    order = sorted(range(len(pages)), key=lambda i: ids[i])
    return data[:first] + b"".join(pages[i] for i in order) + data[pos:]


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
        ordered = _topic_order(data)
        return _MODE_FX2 + _run_fx2(ordered if ordered is not None else data)
    return _MODE_CMIX + _run_cmix("-c", data)


def decompress(archive: bytes) -> bytes:
    mode = archive[:1]
    body = archive[1:]
    if mode == _MODE_FX2:
        return _restore_id_order(_decode_fx2(body))
    if mode == _MODE_CMIX:
        return _run_cmix("-d", body)
    raise ValueError("unknown archive mode")
