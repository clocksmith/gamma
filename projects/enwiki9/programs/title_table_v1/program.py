"""title_table_v1 — online-learned [[Title]] / [[Title|Alt]] back-reference
table, then lzma --extreme -9.

Encoder scans for `[[Title]]` and `[[Title|Alt]]` patterns and replaces each
with either a "new title" record (literal title bytes appended) or a
back-reference to a vocab index. Decoder rebuilds the vocab in the same
order from the same byte stream.

Frame format (before lzma) uses 0x10 as the escape byte:
    0x10 0x00            literal 0x10 byte
    0x10 0x01 <varint(L)> <L bytes title> <0x00 | 0x01 <varint(L2)> <L2 bytes alt>>
                         new title; either no alt (0x00) or alt text (0x01...)
    0x10 0x02 <varint(idx)>
                         back-reference to existing title, no alt
    0x10 0x03 <varint(idx)> <varint(L)> <L bytes alt>
                         back-reference to existing title, with alt text

Escape doubling: any 0x10 byte in non-link payload is replaced with 0x10 0x00
on encode. Decoder undoes this. Random-data safe.

Note: the title vocabulary never ships in program_size — it is rebuilt at
decode time from the back-references themselves.
"""

from __future__ import annotations

import lzma
import re

PRESET = 9 | lzma.PRESET_EXTREME

LINK_RE = re.compile(rb"\[\[([^\]\[\|\n]{1,200})(\|([^\]\[\n]{0,200}))?\]\]")

ESC = 0x10
TAG_LITERAL_ESC = 0x00
TAG_NEW = 0x01
TAG_REF = 0x02
TAG_REF_ALT = 0x03


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
    return lzma.compress(_encode(data), preset=PRESET)


def decompress(data: bytes) -> bytes:
    return _decode(lzma.decompress(data))
