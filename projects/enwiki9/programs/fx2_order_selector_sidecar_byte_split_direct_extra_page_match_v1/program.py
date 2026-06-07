"""Rate-ledger selector over raw and reversible page-order FX2-SC paths."""

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
_LAST_STATS: dict = {}

_MODES = (
    ("R", "raw"),
    ("G", "geometry"),
    ("S", "geometry_suffix"),
    ("C", "geometry_catonly"),
    ("V", "geometry_revtitle"),
    ("N", "geometry_ns"),
    ("T", "geometry_title"),
)


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
        _binary_path = _extract(_BIN_GZ, "fx2-order-selector-cmix-", True)
    return _binary_path


def _dictionary() -> pathlib.Path:
    global _dict_path
    if _dict_path is None or not _dict_path.exists():
        _dict_path = _extract(_DICT_GZ, "fx2-order-selector-dict-", False)
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


def _norm(value: bytes, limit: int = 240) -> bytes:
    return re.sub(rb"[^a-z0-9]+", b" ", value.lower()).strip()[:limit]


def _revnorm(value: bytes, limit: int = 120) -> bytes:
    parts = _norm(value, limit).split()
    return b" ".join(reversed(parts))


def _parts(page: bytes) -> tuple[bytes, bytes, list[bytes], bytes, bytes]:
    title = _first(page, rb"<title>(.*?)</title>")
    redirect = _first(page, rb"#redirect\s*\[\[([^\]\|\n]{1,140})")
    categories = re.findall(rb"\[\[Category:([^\]\|\n]{1,100})", page, re.I)
    infobox = _first(page, rb"\{\{\s*(infobox[^\|\}\n]{0,80})")
    template = _first(page, rb"\{\{([^\|\}\n]{1,80})")
    return title, redirect, categories, infobox, template


def _key(mode: str, page: bytes, pid: int) -> tuple:
    title, redirect, categories, infobox, template = _parts(page)
    ntitle = _norm(title)
    if mode == "geometry":
        if redirect:
            return (_norm(b"z " + redirect), pid)
        if categories:
            return (_norm(b"c " + b" ".join(sorted(categories)) + b" t " + title[:40]), pid)
        if infobox:
            return (_norm(b"i " + infobox), pid)
        return (_norm(b"x " + (template or title)), pid)
    if mode == "geometry_title":
        if redirect:
            return (_norm(b"z " + redirect), pid)
        if categories:
            return (_norm(b"c " + b" ".join(sorted(categories)) + b" t " + title[:80]), pid)
        if infobox:
            return (_norm(b"i " + infobox + b" t " + title), pid)
        return (_norm(b"x " + (template or title) + b" t " + title), pid)
    if mode == "geometry_suffix":
        if redirect:
            return (_norm(b"z " + redirect), pid)
        if categories:
            return (_norm(b"c " + b" ".join(sorted(categories)) + b" s " + title[-30:]), pid)
        if infobox:
            return (_norm(b"i " + infobox + b" s " + title[-30:]), pid)
        return (_norm(b"x " + (template or title) + b" s " + title[-30:]), pid)
    if mode == "geometry_catonly":
        if redirect:
            return (_norm(b"z " + redirect), pid)
        if categories:
            return (_norm(b"c " + b" ".join(sorted(categories))), pid)
        if infobox:
            return (_norm(b"i " + infobox), pid)
        return (_norm(b"x " + (template or title)), pid)
    if mode == "geometry_revtitle":
        if redirect:
            return (_norm(b"z " + redirect), pid)
        if categories:
            return (_norm(b"c " + b" ".join(sorted(categories))), _revnorm(title), pid)
        if infobox:
            return (_norm(b"i " + infobox), _revnorm(title), pid)
        return (_norm(b"x " + (template or title)), _revnorm(title), pid)
    if mode == "geometry_ns":
        namespace = ntitle.split(b" ", 1)[0] if b" " in ntitle else b""
        if redirect:
            return (b"z", _norm(redirect), pid)
        if ntitle.startswith(b"category "):
            return (b"c0", ntitle, pid)
        if categories:
            return (b"c1", _norm(b" ".join(sorted(categories))), ntitle[:80], pid)
        if infobox:
            return (b"i", _norm(infobox), ntitle[:80], pid)
        return (b"x", _norm(template or title), namespace, ntitle[:80], pid)
    raise ValueError(mode)


def _reorder(data: bytes, mode: str) -> bytes | None:
    split = _pages(data)
    if not split:
        return None
    head, pages, tail, ids = split
    order = sorted(range(len(pages)), key=lambda i: _key(mode, pages[i], ids[i]))
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
    global _LAST_STATS
    tried = []
    raw = _run_backend("-c", data)
    best_tag = "R"
    best_name = "raw"
    best_payload = raw
    tried.append({"mode": "raw", "archive": len(raw)})
    for tag, name in _MODES[1:]:
        ordered = _reorder(data, name)
        if ordered is None:
            tried.append({"mode": name, "archive": None})
            continue
        payload = _run_backend("-c", ordered)
        tried.append({"mode": name, "archive": len(payload)})
        if len(payload) < len(best_payload):
            best_tag = tag
            best_name = name
            best_payload = payload
    _LAST_STATS = {
        "selected_mode": best_name,
        "selected_payload_size": len(best_payload),
        "archive_includes_mode_tag": True,
        "tried_modes": tried,
    }
    return best_tag.encode("ascii") + best_payload


def decompress(data: bytes) -> bytes:
    decoded = _run_backend("-d", data[1:])
    return decoded if data[:1] == b"R" else _restore(decoded)


def stats() -> dict:
    return dict(_LAST_STATS)
