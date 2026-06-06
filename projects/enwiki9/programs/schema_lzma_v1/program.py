"""schema_lzma_v1 — split enwik9 into XML skeleton vs <text> content streams,
compress each with lzma --extreme -9 independently. Cheap-oracle test of
whether typed-stream architecture beats raw lzma on the same back-end.

Reversibility: the XML stream contains a 4-byte sentinel where each <text>
block's content was extracted; the text stream is the concatenation of the
extracted contents joined by the same sentinel. Decompress reverses the join.
"""

from __future__ import annotations

import lzma
import struct

SENTINEL = b"\x00\x00\xfe\xff"
TEXT_OPEN = b'<text xml:space="preserve">'
TEXT_CLOSE = b"</text>"
PRESET = 9 | lzma.PRESET_EXTREME


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
            xml_parts.append(data[i + len(TEXT_OPEN):])
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


def compress(data: bytes) -> bytes:
    xml_s, text_s = _split(data)
    xml_c = lzma.compress(xml_s, preset=PRESET)
    text_c = lzma.compress(text_s, preset=PRESET) if text_s else b""
    return struct.pack(">QQ", len(xml_c), len(text_c)) + xml_c + text_c


def decompress(data: bytes) -> bytes:
    xml_len, text_len = struct.unpack(">QQ", data[:16])
    xml_c = data[16 : 16 + xml_len]
    text_c = data[16 + xml_len : 16 + xml_len + text_len]
    xml_s = lzma.decompress(xml_c)
    text_s = lzma.decompress(text_c) if text_c else b""
    return _merge(xml_s, text_s)
