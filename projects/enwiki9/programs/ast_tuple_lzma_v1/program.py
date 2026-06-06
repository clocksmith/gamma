from __future__ import annotations

import subprocess


RAW = 1
XML_TAG = 2
TEMPLATE_OPEN = 3
TEMPLATE_CLOSE = 4
LINK_OPEN = 5
LINK_CLOSE = 6
TABLE_OPEN = 7
TABLE_CLOSE = 8
REF_CLOSE = 9

FIXED = {
    TEMPLATE_OPEN: b"{{",
    TEMPLATE_CLOSE: b"}}",
    LINK_OPEN: b"[[",
    LINK_CLOSE: b"]]",
    TABLE_OPEN: b"{|",
    TABLE_CLOSE: b"|}",
    REF_CLOSE: b"</ref>",
}

XZ_ARGS = [
    "xz",
    "-q",
    "-c",
    "-T1",
    "--check=crc32",
    "--lzma2=preset=9e,dict=1024MiB",
]


def _uvarint(n: int) -> bytes:
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)
    return bytes(out)


def _read_uvarint(data: bytes, pos: int) -> tuple[int, int]:
    shift = 0
    value = 0
    while True:
        if pos >= len(data):
            raise ValueError("truncated varint")
        b = data[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        if b < 0x80:
            return value, pos
        shift += 7
        if shift > 63:
            raise ValueError("varint too large")


def _emit(out: bytearray, typ: int, payload: bytes = b"") -> None:
    out.append(typ)
    if typ not in FIXED:
        out.extend(_uvarint(len(payload)))
        out.extend(payload)


def _looks_like_xml_tag(data: bytes, pos: int) -> int:
    if data[pos] != 60:
        return -1
    if pos + 1 >= len(data):
        return -1
    nxt = data[pos + 1]
    if not (nxt == 47 or nxt == 33 or nxt == 63 or 65 <= nxt <= 90 or 97 <= nxt <= 122):
        return -1
    end = data.find(b">", pos + 1, min(len(data), pos + 512))
    return end if end >= 0 else -1


def _next_marker(data: bytes, pos: int) -> tuple[int, int, int] | None:
    candidates: list[tuple[int, int, int]] = []
    xml_end = _looks_like_xml_tag(data, pos)
    if xml_end >= 0:
        candidates.append((pos, XML_TAG, xml_end + 1))
    for typ, lit in FIXED.items():
        if data.startswith(lit, pos):
            candidates.append((pos, typ, pos + len(lit)))
    return min(candidates, default=None)


def _encode(data: bytes) -> bytes:
    out = bytearray()
    raw = bytearray()
    pos = 0
    while pos < len(data):
        marker = _next_marker(data, pos)
        if marker is None:
            raw.append(data[pos])
            pos += 1
            continue
        _, typ, end = marker
        if raw:
            _emit(out, RAW, bytes(raw))
            raw.clear()
        payload = data[pos:end] if typ == XML_TAG else b""
        _emit(out, typ, payload)
        pos = end
    if raw:
        _emit(out, RAW, bytes(raw))
    return bytes(out)


def _decode(data: bytes) -> bytes:
    out = bytearray()
    pos = 0
    while pos < len(data):
        typ = data[pos]
        pos += 1
        fixed = FIXED.get(typ)
        if fixed is not None:
            out.extend(fixed)
            continue
        size, pos = _read_uvarint(data, pos)
        payload = data[pos : pos + size]
        if len(payload) != size:
            raise ValueError("truncated payload")
        pos += size
        if typ not in (RAW, XML_TAG):
            raise ValueError(f"unknown token type {typ}")
        out.extend(payload)
    return bytes(out)


def compress(data: bytes) -> bytes:
    encoded = _encode(data)
    return subprocess.run(
        XZ_ARGS,
        input=encoded,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout


def decompress(data: bytes) -> bytes:
    encoded = subprocess.run(
        ["xz", "-q", "-d", "-c", "--memlimit-decompress=0"],
        input=data,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    return _decode(encoded)
