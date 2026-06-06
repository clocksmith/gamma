"""purple_parrot_ultimate_cmix_v1 — stacked preprocessing pipeline:
numeric date encoding -> wikilink back-reference table -> markup opcode
substitution -> cmix back-end.

This is the maximum-stacking variant of the locked plan's "structural
normalization" idea, layered onto a context-mixer back-end. It is NOT the
full cmix-sidecar architecture (which would require modifying cmix's C++
mixer to add zero-archive-cost context families); this is the pure-
preprocessor approximation, with all preprocessing costs paid in
program_size.

Layer escape bytes (chosen to be mutually disjoint so layers nest cleanly):
  numeric:        ESC = 0x11 (DC1)
  title_table:    ESC = 0x10 (DLE)
  markup_opcode:  ESC = 0x00 (NUL)

Encode order (innermost → outermost): numeric_encode -> title_table_encode
-> markup_opcode_encode -> cmix_compress. Decode reverses.

Layer interaction: title_table consumes some patterns markup_opcode would
otherwise catch (`[[Category:`, `[[`, `]]`). Net effect is empirically
unknown; the combined ΔS vs cmix_wrapped is the test.

Score-honesty caveat: cmix binary is NOT inlined here.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import shutil
import subprocess
import tempfile

# ---------- markup_opcode layer (ESC=0x00) ----------

OP_ESC = 0
OP_LIT_ESC = 255

OP_TOKENS = [
    b'<text xml:space="preserve">',
    b"</text>",
    b"<page>",
    b"</page>",
    b"<revision>",
    b"</revision>",
    b"<contributor>",
    b"</contributor>",
    b"<timestamp>",
    b"</timestamp>",
    b"<username>",
    b"</username>",
    b"<comment>",
    b"</comment>",
    b"<title>",
    b"</title>",
    b"<id>",
    b"</id>",
    b"<minor />",
    b"{{",
    b"}}",
    b"[[Category:",
    b"[[Image:",
    b"[[",
    b"]]",
    b"&quot;",
    b"&lt;",
    b"&gt;",
    b"&amp;",
    b"http://",
    b"https://",
    b"<ref",
    b"</ref>",
    b"|thumb",
    b"|right",
    b"|left",
    b"Category:",
    b"File:",
    b"Image:",
]

OP_TOKENS_BY_LEN = sorted(enumerate(OP_TOKENS, 1), key=lambda x: len(x[1]), reverse=True)
OP_DECODE = {i: token for i, token in enumerate(OP_TOKENS, 1)}


def _op_encode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        if data[i] == OP_ESC:
            out.extend((OP_ESC, OP_LIT_ESC))
            i += 1
            continue
        for code, token in OP_TOKENS_BY_LEN:
            if data.startswith(token, i):
                out.extend((OP_ESC, code))
                i += len(token)
                break
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def _op_decode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b != OP_ESC:
            out.append(b)
            i += 1
            continue
        if i + 1 >= n:
            raise ValueError("truncated opcode escape")
        code = data[i + 1]
        if code == OP_LIT_ESC:
            out.append(OP_ESC)
        else:
            out.extend(OP_DECODE[code])
        i += 2
    return bytes(out)


# ---------- title_table layer (ESC=0x10) ----------

LINK_RE = re.compile(rb"\[\[([^\]\[\|\n]{1,200})(\|([^\]\[\n]{0,200}))?\]\]")

TT_ESC = 0x10
TT_LITERAL_ESC = 0x00
TT_NEW = 0x01
TT_REF = 0x02
TT_REF_ALT = 0x03


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


def _tt_double_esc(chunk: bytes) -> bytes:
    return chunk.replace(bytes([TT_ESC]), bytes([TT_ESC, TT_LITERAL_ESC]))


def _tt_encode(data: bytes) -> bytes:
    out: list[bytes] = []
    vocab: dict[bytes, int] = {}
    pos = 0
    for m in LINK_RE.finditer(data):
        out.append(_tt_double_esc(data[pos : m.start()]))
        title = m.group(1)
        alt = m.group(3)
        idx = vocab.get(title)
        if idx is None:
            vocab[title] = len(vocab)
            out.append(bytes([TT_ESC, TT_NEW]) + _varint(len(title)) + title)
            if alt is None:
                out.append(b"\x00")
            else:
                out.append(b"\x01" + _varint(len(alt)) + alt)
        else:
            if alt is None:
                out.append(bytes([TT_ESC, TT_REF]) + _varint(idx))
            else:
                out.append(
                    bytes([TT_ESC, TT_REF_ALT]) + _varint(idx) + _varint(len(alt)) + alt
                )
        pos = m.end()
    out.append(_tt_double_esc(data[pos:]))
    return b"".join(out)


def _tt_decode(stream: bytes) -> bytes:
    out: list[bytes] = []
    vocab: list[bytes] = []
    pos = 0
    n = len(stream)
    while pos < n:
        i = stream.find(bytes([TT_ESC]), pos)
        if i < 0:
            out.append(stream[pos:])
            break
        out.append(stream[pos:i])
        pos = i + 1
        if pos >= n:
            raise ValueError("trailing TT_ESC with no tag")
        tag = stream[pos]
        pos += 1
        if tag == TT_LITERAL_ESC:
            out.append(bytes([TT_ESC]))
        elif tag == TT_NEW:
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
        elif tag == TT_REF:
            idx, pos = _read_varint(stream, pos)
            out.append(b"[[" + vocab[idx] + b"]]")
        elif tag == TT_REF_ALT:
            idx, pos = _read_varint(stream, pos)
            ln2, pos = _read_varint(stream, pos)
            alt = stream[pos : pos + ln2]
            pos += ln2
            out.append(b"[[" + vocab[idx] + b"|" + alt + b"]]")
        else:
            raise ValueError(f"bad TT tag {tag:#x}")
    return b"".join(out)


# ---------- numeric layer (ESC=0x11) ----------

ISO_DATE_RE = re.compile(
    rb"(?<![0-9])((?:1[5-9]|20|21)[0-9]{2})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])(?![0-9])"
)

NUM_ESC = 0x11
NUM_DATE_TAG = 0xFF
NUM_EPOCH = _dt.date(1500, 1, 1)


def _num_encode_date(y: int, m: int, d: int) -> bytes | None:
    try:
        delta = (_dt.date(y, m, d) - NUM_EPOCH).days
    except ValueError:
        return None
    if delta < 0 or delta >= (1 << 24):
        return None
    return delta.to_bytes(3, "big")


def _num_double_esc(chunk: bytes) -> bytes:
    return chunk.replace(bytes([NUM_ESC]), bytes([NUM_ESC, 0x00]))


def _num_encode(data: bytes) -> bytes:
    parts: list[bytes] = []
    pos = 0
    for m in ISO_DATE_RE.finditer(data):
        parts.append(_num_double_esc(data[pos : m.start()]))
        y = int(m.group(1))
        mo = int(m.group(2))
        d = int(m.group(3))
        encoded = _num_encode_date(y, mo, d)
        if encoded is None:
            parts.append(_num_double_esc(m.group(0)))
        else:
            parts.append(bytes([NUM_ESC, NUM_DATE_TAG]) + encoded)
        pos = m.end()
    parts.append(_num_double_esc(data[pos:]))
    return b"".join(parts)


def _num_decode(stream: bytes) -> bytes:
    out: list[bytes] = []
    pos = 0
    n = len(stream)
    while pos < n:
        i = stream.find(bytes([NUM_ESC]), pos)
        if i < 0:
            out.append(stream[pos:])
            break
        out.append(stream[pos:i])
        pos = i + 1
        if pos >= n:
            raise ValueError("trailing NUM_ESC with no marker")
        tag = stream[pos]
        pos += 1
        if tag == 0x00:
            out.append(bytes([NUM_ESC]))
        elif tag == NUM_DATE_TAG:
            days = int.from_bytes(stream[pos : pos + 3], "big")
            pos += 3
            date = NUM_EPOCH + _dt.timedelta(days=days)
            out.append(
                f"{date.year:04d}-{date.month:02d}-{date.day:02d}".encode("ascii")
            )
        else:
            raise ValueError(f"bad NUM marker {tag:#x}")
    return b"".join(out)


# ---------- cmix back-end ----------

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


# ---------- pipeline ----------


def compress(data: bytes) -> bytes:
    stage1 = _num_encode(data)
    stage2 = _tt_encode(stage1)
    stage3 = _op_encode(stage2)
    return _cmix("-c", stage3)


def decompress(data: bytes) -> bytes:
    stage3 = _cmix("-d", data)
    stage2 = _op_decode(stage3)
    stage1 = _tt_decode(stage2)
    return _num_decode(stage1)
