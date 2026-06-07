"""Lane B macro-residual XML scaffold transform with LZMA fallback."""

from __future__ import annotations

import lzma

ESC = 0
RAW = b"R"
TRANSFORMED = b"T"
PRESET = 9 | lzma.PRESET_EXTREME

TOKENS = [
    b'<text xml:space="preserve">',
    b'<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.3/"',
    b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
    b' xsi:schemaLocation="http://www.mediawiki.org/xml/export-0.3/',
    b' http://www.mediawiki.org/xml/export-0.3.xsd"',
    b' version="0.3" xml:lang="en">',
    b"  <siteinfo>\n",
    b"  </siteinfo>\n",
    b"    <namespaces>\n",
    b"    </namespaces>\n",
    b"  <page>\n",
    b"  </page>\n",
    b"    <title>",
    b"</title>\n",
    b"    <id>",
    b"</id>\n",
    b"    <revision>\n",
    b"    </revision>\n",
    b"      <id>",
    b"      <timestamp>",
    b"</timestamp>\n",
    b"      <contributor>\n",
    b"      </contributor>\n",
    b"        <username>",
    b"</username>\n",
    b"        <id>",
    b"      <minor />\n",
    b"      <comment>",
    b"</comment>\n",
    b"      <text xml:space=\"preserve\">",
    b"</text>\n",
    b"    <sitename>",
    b"</sitename>\n",
    b"    <base>",
    b"</base>\n",
    b"    <generator>",
    b"</generator>\n",
    b"    <case>",
    b"</case>\n",
    b"      <namespace key=\"0\" />\n",
    b"      <namespace key=\"",
    b"</namespace>\n",
    b"[[Category:",
    b"{{",
    b"}}",
    b"[[",
    b"]]",
    b"&quot;",
    b"&lt;",
    b"&gt;",
    b"&amp;",
]

TOKEN_PAIRS = sorted(enumerate(TOKENS, 1), key=lambda pair: len(pair[1]), reverse=True)
TOKEN_BY_CODE = {code: token for code, token in enumerate(TOKENS, 1)}
_STATS = {}


def _macro_encode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(data)
    hits = 0
    while i < n:
        if data[i] == ESC:
            out.extend((ESC, 0))
            i += 1
            continue
        for code, token in TOKEN_PAIRS:
            if data.startswith(token, i):
                out.extend((ESC, code))
                i += len(token)
                hits += 1
                break
        else:
            out.append(data[i])
            i += 1
    global _STATS
    _STATS = {
        "macro_hits": hits,
        "transformed_size": len(out),
        "raw_size": len(data),
    }
    return bytes(out)


def _macro_decode(data: bytes) -> bytes:
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
            raise ValueError("truncated macro escape")
        code = data[i + 1]
        if code == 0:
            out.append(ESC)
        else:
            try:
                out.extend(TOKEN_BY_CODE[code])
            except KeyError as exc:
                raise ValueError(f"unknown macro code {code}") from exc
        i += 2
    return bytes(out)


def compress(data: bytes) -> bytes:
    raw_archive = RAW + lzma.compress(data, preset=PRESET)
    transformed = _macro_encode(data)
    transformed_archive = TRANSFORMED + lzma.compress(transformed, preset=PRESET)
    if len(transformed_archive) < len(raw_archive):
        _STATS["selected_mode"] = "transformed"
        _STATS["raw_archive_size"] = len(raw_archive)
        _STATS["transformed_archive_size"] = len(transformed_archive)
        return transformed_archive
    _STATS["selected_mode"] = "raw"
    _STATS["raw_archive_size"] = len(raw_archive)
    _STATS["transformed_archive_size"] = len(transformed_archive)
    return raw_archive


def decompress(archive: bytes) -> bytes:
    if not archive:
        raise ValueError("empty archive")
    mode = archive[:1]
    payload = lzma.decompress(archive[1:])
    if mode == RAW:
        return payload
    if mode == TRANSFORMED:
        return _macro_decode(payload)
    raise ValueError(f"unknown archive mode {mode!r}")


def stats() -> dict:
    return dict(_STATS)
