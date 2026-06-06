from __future__ import annotations

import heapq
import subprocess


ESC = 0
LIT_ESC = 255

MAC = 254
MAC_LIT = 0
MAC_DEF = 1
MAC_REF = 2
SPAN = 16
MIN_COUNT = 3
MAX_RULES = 8192
MAX_CANDIDATES = MAX_RULES * 8

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


def _encode_opcode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
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
                break
        else:
            out.append(data[i])
            i += 1
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


LAST_STATS: dict[str, int] = {}


def _literal_stream_cost(chunk: bytes) -> int:
    """Bytes needed to emit chunk literally in the macro layer."""
    return len(chunk) + chunk.count(MAC)


def _mine_rules(data: bytes) -> set[bytes]:
    n = len(data) - SPAN + 1
    if n <= 0:
        return set()

    counters: dict[bytes, tuple[int, int]] = {}
    heap: list[tuple[int, int, bytes]] = []
    serial = 0
    total_spans = 0
    # First pass: deterministic corpus-wide Space-Saving heavy hitters.
    # Stride is 1, so unaligned repeats are visible, while the candidate table
    # stays bounded instead of filling from the first prefix.
    for i in range(n):
        span = data[i : i + SPAN]
        total_spans += 1
        if span in counters:
            count, err = counters[span]
            count += 1
            counters[span] = (count, err)
            heapq.heappush(heap, (count, serial, span))
            serial += 1
            continue
        if len(counters) < MAX_CANDIDATES:
            counters[span] = (1, 0)
            heapq.heappush(heap, (1, serial, span))
            serial += 1
            continue
        while heap:
            count, _, old = heapq.heappop(heap)
            current = counters.get(old)
            if current is not None and current[0] == count:
                break
        else:
            raise RuntimeError("heavy-hitter heap exhausted")
        del counters[old]
        counters[span] = (count + 1, count)
        heapq.heappush(heap, (count + 1, serial, span))
        serial += 1

    candidates = set(counters)
    if not candidates:
        LAST_STATS.clear()
        LAST_STATS.update(
            {
                "total_spans": total_spans,
                "candidate_count": 0,
                "rule_count": 0,
            }
        )
        return set()

    counts = {span: 0 for span in candidates}
    first_pos = {span: n for span in candidates}
    # Second pass: exact counts and first positions for heavy-hitter
    # candidates across the full corpus.
    for i in range(n):
        span = data[i : i + SPAN]
        if span in counts:
            counts[span] += 1
            if first_pos[span] == n:
                first_pos[span] = i

    rough: list[tuple[int, bytes]] = []
    best_ref_cost = 2 + len(_uvarint(0))
    def_overhead = 2 + len(_uvarint(SPAN))
    for span, count in counts.items():
        if count < MIN_COUNT:
            continue
        literal = _literal_stream_cost(span)
        savings = (count - 1) * (literal - best_ref_cost) - def_overhead
        if savings > 0:
            rough.append((savings, span))

    rough.sort(reverse=True)
    pool = [span for _, span in rough[: MAX_RULES * 2]]
    ranked_by_first_use = {
        span: idx for idx, span in enumerate(sorted(pool, key=lambda s: first_pos[s]))
    }
    scored: list[tuple[int, bytes]] = []
    for span in pool:
        literal = _literal_stream_cost(span)
        ref_cost = 2 + len(_uvarint(ranked_by_first_use[span]))
        savings = (counts[span] - 1) * (literal - ref_cost) - def_overhead
        if savings > 0:
            scored.append((savings, span))

    scored.sort(reverse=True)
    rules = {span for _, span in scored[:MAX_RULES]}
    LAST_STATS.clear()
    LAST_STATS.update(
        {
            "total_spans": total_spans,
            "candidate_count": len(candidates),
            "rule_count": len(rules),
            "admissible_rule_count": len(scored),
        }
    )
    return rules


def _emit_literal(out: bytearray, b: int) -> None:
    if b == MAC:
        out.extend((MAC, MAC_LIT))
    else:
        out.append(b)


def _encode_macros(data: bytes) -> bytes:
    rules = _mine_rules(data)
    source_len = len(data)
    ref_source_bytes = 0
    ref_encoded_bytes = 0
    def_source_bytes = 0
    def_encoded_bytes = 0
    literal_source_bytes = 0
    literal_encoded_bytes = 0
    if not rules:
        out = bytearray()
        for b in data:
            before = len(out)
            _emit_literal(out, b)
            literal_source_bytes += 1
            literal_encoded_bytes += len(out) - before
        LAST_STATS.update(
            {
                "source_len": source_len,
                "macro_encoded_len": len(out),
                "macro_definitions": 0,
                "macro_references": 0,
                "macro_reference_source_bytes": 0,
                "macro_reference_encoded_bytes": 0,
                "macro_definition_source_bytes": 0,
                "macro_definition_encoded_bytes": 0,
                "macro_literal_source_bytes": literal_source_bytes,
                "macro_literal_encoded_bytes": literal_encoded_bytes,
                "macro_reference_coverage_ppm": 0,
            }
        )
        return bytes(out)

    defined: dict[bytes, int] = {}
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        span = data[i : i + SPAN]
        if len(span) == SPAN and span in rules:
            idx = defined.get(span)
            if idx is None:
                idx = len(defined)
                defined[span] = idx
                out.extend((MAC, MAC_DEF))
                size = _uvarint(len(span))
                out.extend(size)
                out.extend(span)
                def_source_bytes += SPAN
                def_encoded_bytes += 2 + len(size) + SPAN
            else:
                out.extend((MAC, MAC_REF))
                ref = _uvarint(idx)
                out.extend(ref)
                ref_source_bytes += SPAN
                ref_encoded_bytes += 2 + len(ref)
            i += SPAN
        else:
            before = len(out)
            _emit_literal(out, data[i])
            literal_source_bytes += 1
            literal_encoded_bytes += len(out) - before
            i += 1
    LAST_STATS.update(
        {
            "source_len": source_len,
            "macro_encoded_len": len(out),
            "macro_definitions": len(defined),
            "macro_references": ref_source_bytes // SPAN,
            "macro_reference_source_bytes": ref_source_bytes,
            "macro_reference_encoded_bytes": ref_encoded_bytes,
            "macro_definition_source_bytes": def_source_bytes,
            "macro_definition_encoded_bytes": def_encoded_bytes,
            "macro_literal_source_bytes": literal_source_bytes,
            "macro_literal_encoded_bytes": literal_encoded_bytes,
            "macro_reference_coverage_ppm": int(
                ref_source_bytes * 1_000_000 / source_len
            )
            if source_len
            else 0,
        }
    )
    return bytes(out)


def _decode_macros(data: bytes) -> bytes:
    rules: list[bytes] = []
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b != MAC:
            out.append(b)
            i += 1
            continue
        if i + 1 >= n:
            raise ValueError("truncated macro escape")
        tag = data[i + 1]
        i += 2
        if tag == MAC_LIT:
            out.append(MAC)
        elif tag == MAC_DEF:
            size, i = _read_uvarint(data, i)
            span = data[i : i + size]
            if len(span) != size:
                raise ValueError("truncated macro definition")
            i += size
            rules.append(span)
            out.extend(span)
        elif tag == MAC_REF:
            idx, i = _read_uvarint(data, i)
            out.extend(rules[idx])
        else:
            raise ValueError(f"bad macro tag {tag}")
    return bytes(out)


def compress(data: bytes) -> bytes:
    encoded = _encode_macros(_encode_opcode(data))
    # The macro layer runs before opcode decode. It may emit ESC (0x00) bytes
    # inside macro definitions, but _decode_macros fully reconstructs the
    # original opcode stream before _decode_opcode sees it.
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
    return _decode_opcode(_decode_macros(encoded))


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
