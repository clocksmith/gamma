"""Fast-search suffix page ordering over the compact fx2 backend.

This package uses a gzip-decoded dictionary to avoid measuring candidate keys
through a slow self-compressed dictionary decode. It is a search lane, not the
minimum counted package for a final score.
"""

from __future__ import annotations

import gzip
import lzma
import os
import pathlib
import re
import stat
import subprocess
import tempfile

_DIR = pathlib.Path(__file__).resolve().parent
_OPEN = b"  <page>\n"
_CLOSE = b"  </page>\n"
_binary_path: pathlib.Path | None = None
_dict_path: pathlib.Path | None = None
_LAST_STATS: dict = {}


def _extract(src: pathlib.Path, prefix: str, executable: bool, codec: str) -> pathlib.Path:
    fd, name = tempfile.mkstemp(prefix=prefix)
    os.close(fd)
    out = pathlib.Path(name)
    if codec == "xz":
        out.write_bytes(lzma.open(src).read())
    elif codec == "gz":
        out.write_bytes(gzip.open(src, "rb").read())
    else:
        raise ValueError(codec)
    if executable:
        out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return out


def _binary() -> pathlib.Path:
    global _binary_path
    if _binary_path is None or not _binary_path.exists():
        _binary_path = _extract(_DIR / "cmix.xz", "fx2-gzsuf-cmix-", True, "xz")
    return _binary_path


def _dictionary() -> pathlib.Path:
    global _dict_path
    if _dict_path is None or not _dict_path.exists():
        _dict_path = _extract(_DIR / "english.dic.gz", "fx2-gzsuf-dic-", False, "gz")
    return _dict_path


def _run(flag: str, data: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        pathlib.Path(src).write_bytes(data)
        subprocess.run(
            [str(_binary()), flag, str(_dictionary()), src, dst],
            cwd=td,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return pathlib.Path(dst).read_bytes()


def _first(page: bytes, pattern: bytes) -> bytes:
    match = re.search(pattern, page, re.S | re.I)
    return match.group(1) if match else b""


def _split(data: bytes, allow_unsorted: bool = False):
    start = data.find(_OPEN)
    if start < 0:
        return None
    pages: list[bytes] = []
    pos = start
    while True:
        head = data.find(_OPEN, pos)
        tail = data.find(_CLOSE, head)
        if head < 0 or tail < 0:
            break
        tail += len(_CLOSE)
        pages.append(data[head:tail])
        pos = tail
    ids = [int(_first(page, rb"<id>(\d+)</id>") or 10**30) for page in pages]
    if len(pages) > 1 and len(ids) == len(set(ids)) and (
        allow_unsorted or ids == sorted(ids)
    ):
        return data[:start], pages, data[pos:], ids
    return None


def _norm(value: bytes) -> bytes:
    return re.sub(rb"[^a-z0-9]+", b" ", value.lower()).strip()[:240]


def _key(page: bytes, pid: int) -> tuple[bytes, int]:
    title = _first(page, rb"<title>(.*?)</title>")
    redirect = _first(page, rb"#redirect\s*\[\[([^\]\|\n]{1,140})")
    if redirect:
        return _norm(b"z " + redirect), pid
    suffix = title[-30:]
    cats = re.findall(rb"\[\[Category:([^\]\|\n]{1,100})", page, re.I)
    if cats:
        return _norm(b"c " + b" ".join(sorted(cats)) + b" s " + suffix), pid
    infobox = _first(page, rb"\{\{\s*(infobox[^\|\}\n]{0,80})")
    if infobox:
        return _norm(b"i " + infobox + b" s " + suffix), pid
    template = _first(page, rb"\{\{([^\|\}\n]{1,80})")
    return _norm(b"x " + (template or title) + b" s " + suffix), pid


def _order(data: bytes) -> bytes | None:
    split = _split(data)
    if split is None:
        return None
    head, pages, tail, ids = split
    order = sorted(range(len(pages)), key=lambda i: _key(pages[i], ids[i]))
    if order == list(range(len(pages))):
        return None
    return head + b"".join(pages[i] for i in order) + tail


def _restore(data: bytes) -> bytes:
    split = _split(data, allow_unsorted=True)
    if split is None:
        return data
    head, pages, tail, ids = split
    return head + b"".join(pages[i] for i in sorted(range(len(pages)), key=lambda i: ids[i])) + tail


def compress(data: bytes) -> bytes:
    global _LAST_STATS
    ordered = _order(data)
    if ordered is None:
        payload = _run("-c", data)
        _LAST_STATS = {"mode": "raw", "payload_size": len(payload)}
        return b"R" + payload
    payload = _run("-c", ordered)
    _LAST_STATS = {"mode": "geometry_suffix", "payload_size": len(payload)}
    return b"G" + payload


def decompress(data: bytes) -> bytes:
    decoded = _run("-d", data[1:])
    return decoded if data[:1] == b"R" else _restore(decoded)


def stats() -> dict:
    return dict(_LAST_STATS)
