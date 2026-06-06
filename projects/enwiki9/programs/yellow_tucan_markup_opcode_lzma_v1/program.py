"""yellow_tucan_markup_opcode_lzma_v1.

No-cmix architecture test: reversible MediaWiki/XML opcode substitution
followed by Python stdlib LZMA extreme mode. No external binary is used.
"""

from __future__ import annotations

import lzma

ESC = 0
LIT_ESC = 255
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


def _encode(data: bytes) -> bytes:
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
    LAST_STATS.clear()
    LAST_STATS.update(
        {
            "source_len": len(data),
            "transformed_size": len(out),
            "opcode_token_count": token_count,
            "syntax_matched_bytes": matched_bytes,
            "syntax_deleted_bytes": max(0, matched_bytes - 2 * token_count),
        }
    )
    return bytes(out)


def _decode(data: bytes) -> bytes:
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
    return lzma.compress(_encode(data), preset=PRESET)


def decompress(data: bytes) -> bytes:
    return _decode(lzma.decompress(data))


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
