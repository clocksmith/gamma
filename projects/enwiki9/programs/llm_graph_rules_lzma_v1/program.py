"""llm_graph_rules_lzma_v1.

The live LLM is used only to author the deterministic reduction rule. Runtime
compression is model-free: pre-scan wiki links, admit only high-support targets
as graph nodes, encode later occurrences as node references, then apply the
same compact MediaWiki/XML opcode idea used by the strong LZMA baselines.
"""

from __future__ import annotations

import lzma
import re

ESC = 0
LIT_ESC = 255
TAG_LINK_NEW = 64
TAG_LINK_REF = 65
TAG_LINK_REF_ALT = 66
LINK_THRESHOLD = 20
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
    b"<title>",
    b"</title>",
]

TOKENS_BY_LEN = sorted(enumerate(TOKENS, 1), key=lambda x: len(x[1]), reverse=True)
DECODE = dict(enumerate(TOKENS, 1))
LINK_RE = re.compile(rb"\[\[([^\]\[\|\n]{1,240})(\|([^\]\[\n]{0,240}))?\]\]")
LAST_STATS: dict[str, int] = {}


def _varint(n: int) -> bytes:
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)
    return bytes(out)


def _read_varint(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 0
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


def _link_candidates(data: bytes) -> set[bytes]:
    counts: dict[bytes, int] = {}
    for match in LINK_RE.finditer(data):
        title = match.group(1)
        counts[title] = counts.get(title, 0) + 1
    return {
        title
        for title, count in counts.items()
        if count >= LINK_THRESHOLD and len(title) >= 2
    }


def _emit_escaped(out: bytearray, b: int) -> None:
    if b == ESC:
        out.extend((ESC, LIT_ESC))
    else:
        out.append(b)


def _encode(data: bytes) -> bytes:
    candidates = _link_candidates(data)
    nodes: list[bytes] = []
    node_index: dict[bytes, int] = {}
    out = bytearray()
    i = 0
    n = len(data)
    link_new = link_ref = link_alt = token_count = token_bytes = 0

    while i < n:
        if data[i] == ESC:
            out.extend((ESC, LIT_ESC))
            i += 1
            continue

        match = LINK_RE.match(data, i)
        if match is not None:
            title = match.group(1)
            alt = match.group(3)
            idx = node_index.get(title)
            if idx is not None:
                if alt is None:
                    out.extend((ESC, TAG_LINK_REF))
                    out.extend(_varint(idx))
                else:
                    out.extend((ESC, TAG_LINK_REF_ALT))
                    out.extend(_varint(idx))
                    out.extend(_varint(len(alt)))
                    out.extend(alt)
                    link_alt += 1
                link_ref += 1
                i = match.end()
                continue
            if title in candidates:
                node_index[title] = len(nodes)
                nodes.append(title)
                out.extend((ESC, TAG_LINK_NEW))
                out.extend(_varint(len(title)))
                out.extend(title)
                if alt is None:
                    out.append(0)
                else:
                    out.append(1)
                    out.extend(_varint(len(alt)))
                    out.extend(alt)
                    link_alt += 1
                link_new += 1
                i = match.end()
                continue

        for code, token in TOKENS_BY_LEN:
            if data.startswith(token, i):
                out.extend((ESC, code))
                i += len(token)
                token_count += 1
                token_bytes += len(token)
                break
        else:
            _emit_escaped(out, data[i])
            i += 1

    LAST_STATS.clear()
    LAST_STATS.update(
        {
            "source_len": len(data),
            "transformed_size": len(out),
            "link_candidate_count": len(candidates),
            "link_new_count": link_new,
            "link_ref_count": link_ref,
            "link_alt_count": link_alt,
            "fixed_token_count": token_count,
            "fixed_token_source_bytes": token_bytes,
        }
    )
    return bytes(out)


def _decode(stream: bytes) -> bytes:
    out = bytearray()
    nodes: list[bytes] = []
    i = 0
    n = len(stream)
    while i < n:
        b = stream[i]
        if b != ESC:
            out.append(b)
            i += 1
            continue
        if i + 1 >= n:
            raise ValueError("truncated escape")
        tag = stream[i + 1]
        i += 2
        if tag == LIT_ESC:
            out.append(ESC)
        elif 1 <= tag <= len(TOKENS):
            out.extend(DECODE[tag])
        elif tag == TAG_LINK_NEW:
            ln, i = _read_varint(stream, i)
            title = stream[i : i + ln]
            if len(title) != ln:
                raise ValueError("truncated link title")
            i += ln
            nodes.append(title)
            if i >= n:
                raise ValueError("truncated link alt flag")
            flag = stream[i]
            i += 1
            if flag == 0:
                out.extend(b"[[" + title + b"]]")
            elif flag == 1:
                ln2, i = _read_varint(stream, i)
                alt = stream[i : i + ln2]
                if len(alt) != ln2:
                    raise ValueError("truncated link alt")
                i += ln2
                out.extend(b"[[" + title + b"|" + alt + b"]]")
            else:
                raise ValueError(f"bad link alt flag {flag:#x}")
        elif tag == TAG_LINK_REF:
            idx, i = _read_varint(stream, i)
            out.extend(b"[[" + nodes[idx] + b"]]")
        elif tag == TAG_LINK_REF_ALT:
            idx, i = _read_varint(stream, i)
            ln2, i = _read_varint(stream, i)
            alt = stream[i : i + ln2]
            if len(alt) != ln2:
                raise ValueError("truncated link ref alt")
            i += ln2
            out.extend(b"[[" + nodes[idx] + b"|" + alt + b"]]")
        else:
            raise ValueError(f"bad tag {tag:#x}")
    return bytes(out)


def compress(data: bytes) -> bytes:
    return lzma.compress(_encode(data), preset=PRESET)


def decompress(data: bytes) -> bytes:
    return _decode(lzma.decompress(data))


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
