"""purple_parrot_title_table_cmix_v1 — online wikilink back-reference
preprocessor on top of cmix as the back-end.

Layer 1: identical to title_table_v1's bug-fixed encoder. Scans for
`[[Title]]` and `[[Title|Alt]]`, replaces each with NEW_TITLE (literal +
add to vocab) on first occurrence or REF_TITLE (varint index) on later
occurrences. ESC byte is 0x10. 0x10 in payload is escape-doubled.

Layer 2: cmix as the back-end via subprocess to system cmix on PATH.

Architecture test: title_table_v1 lost +0.28% under lzma at full corpus
because lzma's match finder already extracted that redundancy. cmix's
match model is weaker than its mixer; an explicit typed-link channel may
compose. This program's S vs cmix_wrapped's S on the same scope answers
that.

Score-honesty caveat: cmix binary is NOT inlined here (PATH-resolved per
the schema_cmix / title_table_cmix convention). For a leaderboard-eligible
row, inline as in cmix_wrapped/program.py.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile

LINK_RE = re.compile(rb"\[\[([^\]\[\|\n]{1,200})(\|([^\]\[\n]{0,200}))?\]\]")

ESC = 0x10
TAG_LITERAL_ESC = 0x00
TAG_NEW = 0x01
TAG_REF = 0x02
TAG_REF_ALT = 0x03

_CMIX = shutil.which("cmix")


def _require_cmix() -> str:
    if _CMIX is None:
        raise RuntimeError(
            "cmix not on PATH; install from https://github.com/byronknoll/cmix"
        )
    return _CMIX


def _cmix(flag: str, data: bytes) -> bytes:
    binary = _require_cmix()
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        with open(src, "wb") as f:
            f.write(data)
        subprocess.run(
            [binary, flag, src, dst],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with open(dst, "rb") as f:
            return f.read()


def _varint(n: int) -> bytes:
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n & 0x7F)
    return bytes(out)


def _read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    shift = 0
    n = 0
    while True:
        b = buf[pos]
        pos += 1
        n |= (b & 0x7F) << shift
        if not (b & 0x80):
            return n, pos
        shift += 7


def _double_esc(chunk: bytes) -> bytes:
    return chunk.replace(bytes([ESC]), bytes([ESC, TAG_LITERAL_ESC]))


def _encode(data: bytes) -> bytes:
    out: list[bytes] = []
    vocab: dict[bytes, int] = {}
    pos = 0
    for m in LINK_RE.finditer(data):
        out.append(_double_esc(data[pos : m.start()]))
        title = m.group(1)
        alt = m.group(3)
        idx = vocab.get(title)
        if idx is None:
            vocab[title] = len(vocab)
            out.append(bytes([ESC, TAG_NEW]) + _varint(len(title)) + title)
            if alt is None:
                out.append(b"\x00")
            else:
                out.append(b"\x01" + _varint(len(alt)) + alt)
        else:
            if alt is None:
                out.append(bytes([ESC, TAG_REF]) + _varint(idx))
            else:
                out.append(
                    bytes([ESC, TAG_REF_ALT]) + _varint(idx) + _varint(len(alt)) + alt
                )
        pos = m.end()
    out.append(_double_esc(data[pos:]))
    return b"".join(out)


def _decode(stream: bytes) -> bytes:
    out: list[bytes] = []
    vocab: list[bytes] = []
    pos = 0
    n = len(stream)
    while pos < n:
        i = stream.find(bytes([ESC]), pos)
        if i < 0:
            out.append(stream[pos:])
            break
        out.append(stream[pos:i])
        pos = i + 1
        if pos >= n:
            raise ValueError("trailing ESC with no tag")
        tag = stream[pos]
        pos += 1
        if tag == TAG_LITERAL_ESC:
            out.append(bytes([ESC]))
        elif tag == TAG_NEW:
            ln, pos = _read_varint(stream, pos)
            title = stream[pos : pos + ln]
            pos += ln
            vocab.append(title)
            has_alt = stream[pos]
            pos += 1
            if has_alt == 0:
                out.append(b"[[" + title + b"]]")
            elif has_alt == 1:
                ln2, pos = _read_varint(stream, pos)
                alt = stream[pos : pos + ln2]
                pos += ln2
                out.append(b"[[" + title + b"|" + alt + b"]]")
            else:
                raise ValueError(f"bad has_alt {has_alt:#x}")
        elif tag == TAG_REF:
            idx, pos = _read_varint(stream, pos)
            out.append(b"[[" + vocab[idx] + b"]]")
        elif tag == TAG_REF_ALT:
            idx, pos = _read_varint(stream, pos)
            ln2, pos = _read_varint(stream, pos)
            alt = stream[pos : pos + ln2]
            pos += ln2
            out.append(b"[[" + vocab[idx] + b"|" + alt + b"]]")
        else:
            raise ValueError(f"bad tag {tag:#x}")
    return b"".join(out)


def compress(data: bytes) -> bytes:
    return _cmix("-c", _encode(data))


def decompress(data: bytes) -> bytes:
    return _decode(_cmix("-d", data))
