"""fx2_topic_sort_match_v1.

Score-honest wrapper around the structural fx2-cmix build. The encoder may sort
complete MediaWiki pages by a deterministic topic key before compression; the
decoder restores the original enwik9 order by page id.
"""

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
_RAW = b"R"
_TOPIC = b"T"
_PAGE_OPEN = b"  <page>\n"
_PAGE_CLOSE = b"  </page>\n"
_extracted_bin: pathlib.Path | None = None
_extracted_dict: pathlib.Path | None = None


def _extract(src: pathlib.Path, prefix: str, executable: bool) -> pathlib.Path:
    fd, path = tempfile.mkstemp(prefix=prefix)
    os.close(fd)
    p = pathlib.Path(path)
    with gzip.open(src, "rb") as inp:
        p.write_bytes(inp.read())
    if executable:
        p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return p


def _binary() -> pathlib.Path:
    global _extracted_bin
    if _extracted_bin is None or not _extracted_bin.exists():
        _extracted_bin = _extract(_BIN_GZ, "fx2-topic-sort-match-cmix-", True)
    return _extracted_bin


def _dictionary() -> pathlib.Path:
    global _extracted_dict
    if _extracted_dict is None or not _extracted_dict.exists():
        _extracted_dict = _extract(_DICT_GZ, "fx2-topic-sort-match-dict-", False)
    return _extracted_dict


def _run(flag: str, data: bytes) -> bytes:
    binary = _binary()
    dictionary = _dictionary()
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        with open(src, "wb") as f:
            f.write(data)
        subprocess.run(
            [str(binary), flag, str(dictionary), src, dst],
            cwd=td,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with open(dst, "rb") as f:
            return f.read()


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


def _split_pages(data: bytes) -> tuple[bytes, list[bytes], bytes, list[int]] | None:
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
    if len(pages) < 2 or ids != sorted(ids) or len(ids) != len(set(ids)):
        return None
    return data[:first], pages, data[pos:], ids


def _topic_order(data: bytes) -> bytes | None:
    parts = _split_pages(data)
    if parts is None:
        return None
    head, pages, tail, ids = parts
    order = sorted(range(len(pages)), key=lambda i: (_topic_key(pages[i]), ids[i]))
    if order == list(range(len(pages))):
        return None
    return head + b"".join(pages[i] for i in order) + tail


def _restore_id_order(data: bytes) -> bytes:
    parts = _split_pages(data)
    if parts is None:
        return data
    head, pages, tail, ids = parts
    order = sorted(range(len(pages)), key=lambda i: ids[i])
    return head + b"".join(pages[i] for i in order) + tail


def compress(data: bytes) -> bytes:
    raw = _run("-c", data)
    ordered = _topic_order(data)
    if ordered is None:
        return _RAW + raw
    topic = _run("-c", ordered)
    if len(topic) < len(raw):
        return _TOPIC + topic
    return _RAW + raw


def decompress(data: bytes) -> bytes:
    mode, body = data[:1], data[1:]
    out = _run("-d", body)
    if mode == _RAW:
        return out
    if mode == _TOPIC:
        return _restore_id_order(out)
    raise ValueError("unknown archive mode")
