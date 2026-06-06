"""yellow_tucan_schema_opcode_lzma_v1.

No-cmix composition of the two no-cmix wins under investigation:
split XML skeleton from <text> payloads, opcode-compress the XML stream, then
compress both streams with Python stdlib LZMA extreme mode.
"""

from __future__ import annotations

import lzma
import struct

ESC = 0
LIT_ESC = 255
SENTINEL = b"\x00\x00\xfe\xff"
TEXT_OPEN = b'<text xml:space="preserve">'
TEXT_CLOSE = b"</text>"
PRESET = 9 | lzma.PRESET_EXTREME

TOKENS = [
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

TOKENS_BY_LEN = sorted(enumerate(TOKENS, 1), key=lambda x: len(x[1]), reverse=True)
DECODE = {i: token for i, token in enumerate(TOKENS, 1)}
LAST_STATS: dict[str, int] = {}


def _split(data: bytes) -> tuple[bytes, bytes]:
    if SENTINEL in data:
        return data, b""
    xml_parts: list[bytes] = []
    text_parts: list[bytes] = []
    pos = 0
    while True:
        i = data.find(TEXT_OPEN, pos)
        if i < 0:
            xml_parts.append(data[pos:])
            break
        xml_parts.append(data[pos : i + len(TEXT_OPEN)])
        j = data.find(TEXT_CLOSE, i + len(TEXT_OPEN))
        if j < 0:
            xml_parts.append(data[i + len(TEXT_OPEN) :])
            break
        text_parts.append(data[i + len(TEXT_OPEN) : j])
        xml_parts.append(SENTINEL)
        xml_parts.append(TEXT_CLOSE)
        pos = j + len(TEXT_CLOSE)
    return b"".join(xml_parts), SENTINEL.join(text_parts)


def _merge(xml_stream: bytes, text_stream: bytes) -> bytes:
    if SENTINEL not in xml_stream:
        return xml_stream
    blobs = text_stream.split(SENTINEL) if text_stream else []
    out: list[bytes] = []
    pos = 0
    bi = 0
    while True:
        i = xml_stream.find(SENTINEL, pos)
        if i < 0:
            out.append(xml_stream[pos:])
            break
        out.append(xml_stream[pos:i])
        out.append(blobs[bi])
        bi += 1
        pos = i + len(SENTINEL)
    return b"".join(out)


def _encode_opcode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    token_count = 0
    matched_bytes = 0
    n = len(data)
    while i < n:
        if data[i] == ESC:
            out.extend((ESC, LIT_ESC))
            i += 1
            continue
        for code, token in TOKENS_BY_LEN:
            if data.startswith(token, i):
                out.extend((ESC, code))
                i += len(token)
                token_count += 1
                matched_bytes += len(token)
                break
        else:
            out.append(data[i])
            i += 1
    LAST_STATS.update(
        {
            "opcode_token_count": token_count,
            "syntax_matched_bytes": matched_bytes,
            "syntax_deleted_bytes": max(0, matched_bytes - 2 * token_count),
            "xml_transformed_size": len(out),
        }
    )
    return bytes(out)


def _decode_opcode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b != ESC:
            out.append(b)
            i += 1
            continue
        if i + 1 >= n:
            raise ValueError("truncated opcode escape")
        code = data[i + 1]
        if code == LIT_ESC:
            out.append(ESC)
        else:
            out.extend(DECODE[code])
        i += 2
    return bytes(out)


def compress(data: bytes) -> bytes:
    xml_s, text_s = _split(data)
    LAST_STATS.clear()
    LAST_STATS.update(
        {
            "source_len": len(data),
            "xml_source_size": len(xml_s),
            "text_source_size": len(text_s),
        }
    )
    xml_c = lzma.compress(_encode_opcode(xml_s), preset=PRESET)
    text_c = lzma.compress(text_s, preset=PRESET) if text_s else b""
    return struct.pack(">QQ", len(xml_c), len(text_c)) + xml_c + text_c


def decompress(data: bytes) -> bytes:
    xml_len, text_len = struct.unpack(">QQ", data[:16])
    xml_c = data[16 : 16 + xml_len]
    text_c = data[16 + xml_len : 16 + xml_len + text_len]
    xml_s = _decode_opcode(lzma.decompress(xml_c))
    text_s = lzma.decompress(text_c) if text_c else b""
    return _merge(xml_s, text_s)


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
