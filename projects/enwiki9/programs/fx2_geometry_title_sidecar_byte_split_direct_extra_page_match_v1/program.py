"""Rate-ledger selector over raw vs geometry/title FX2-SC backend paths."""

from __future__ import annotations

import gzip
import os
import pathlib
import re
import stat
import subprocess
import tempfile

_DIR = pathlib.Path(__file__).resolve().parent
_BIN_GZ = _DIR / "cmix.bin.gz"
_DICT_GZ = _DIR / "english.dic.gz"
_OPEN = b"  <page>\n"
_CLOSE = b"  </page>\n"
_binary_path: pathlib.Path | None = None
_dict_path: pathlib.Path | None = None


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
    global _binary_path
    if _binary_path is None or not _binary_path.exists():
        _binary_path = _extract(_BIN_GZ, "fx2-geom-title-sidecar-cmix-", True)
    return _binary_path


def _dictionary() -> pathlib.Path:
    global _dict_path
    if _dict_path is None or not _dict_path.exists():
        _dict_path = _extract(_DICT_GZ, "fx2-geom-title-sidecar-dict-", False)
    return _dict_path


def _run_backend(flag: str, data: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        with open(src, "wb") as fh:
            fh.write(data)
        subprocess.run(
            [str(_binary()), flag, str(_dictionary()), src, dst],
            cwd=td,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with open(dst, "rb") as fh:
            return fh.read()


def _first(page: bytes, pattern: bytes) -> bytes:
    match = re.search(pattern, page, re.S | re.I)
    return match.group(1) if match else b""


def _pages(data: bytes, allow_unsorted: bool = False):
    start = data.find(_OPEN)
    if start < 0:
        return None
    pages: list[bytes] = []
    offset = start
    while True:
        head = data.find(_OPEN, offset)
        tail = data.find(_CLOSE, head)
        if head < 0 or tail < 0:
            break
        tail += len(_CLOSE)
        pages.append(data[head:tail])
        offset = tail
    ids = [int(_first(page, rb"<id>(\d+)</id>") or 10**30) for page in pages]
    if len(pages) > 1 and len(ids) == len(set(ids)) and (
        allow_unsorted or ids == sorted(ids)
    ):
        return data[:start], pages, data[offset:], ids
    return None


def _norm(value: bytes) -> bytes:
    return re.sub(rb"[^a-z0-9]+", b" ", value.lower()).strip()[:240]


def _geometry_key(page: bytes) -> bytes:
    title = _first(page, rb"<title>(.*?)</title>")
    redirect = _first(page, rb"#redirect\s*\[\[([^\]\|\n]{1,140})")
    if redirect:
        return _norm(b"z " + redirect)
    categories = re.findall(rb"\[\[Category:([^\]\|\n]{1,100})", page, re.I)
    if categories:
        return _norm(b"c " + b" ".join(sorted(categories)) + b" t " + title[:80])
    infobox = _first(page, rb"\{\{\s*(infobox[^\|\}\n]{0,80})")
    if infobox:
        return _norm(b"i " + infobox + b" t " + title)
    template = _first(page, rb"\{\{([^\|\}\n]{1,80})")
    return _norm(b"x " + (template or title) + b" t " + title)


def _reorder(data: bytes) -> bytes | None:
    split = _pages(data)
    if not split:
        return None
    head, pages, tail, ids = split
    order = sorted(range(len(pages)), key=lambda i: (_geometry_key(pages[i]), ids[i]))
    if order == list(range(len(pages))):
        return None
    return head + b"".join(pages[i] for i in order) + tail


def _restore(data: bytes) -> bytes:
    split = _pages(data, allow_unsorted=True)
    if not split:
        return data
    head, pages, tail, ids = split
    return head + b"".join(pages[i] for i in sorted(range(len(pages)), key=lambda i: ids[i])) + tail


def compress(data: bytes) -> bytes:
    raw = _run_backend("-c", data)
    reordered = _reorder(data)
    if reordered is None:
        return b"R" + raw
    geometry = _run_backend("-c", reordered)
    if len(geometry) < len(raw):
        return b"G" + geometry
    return b"R" + raw


def decompress(data: bytes) -> bytes:
    decoded = _run_backend("-d", data[1:])
    if data[:1] == b"G":
        return _restore(decoded)
    return decoded
