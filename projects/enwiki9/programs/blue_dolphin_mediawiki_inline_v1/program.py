"""blue_dolphin_mediawiki_inline_v1 — Phase 4 typed inline channels.

Reversible MediaWiki parser. The byte stream stays in original order; structural
state transitions are emitted as inline marker bytes (not split streams). The
back-end coder sees: original bytes interleaved with type boundary markers, in
the natural enwik9 byte order.

Why inline (not split): splitting destroys cross-stream mutual information
(e.g., article title predicts prose vocabulary). Inline tagging exposes the
type boundary to the back-end while keeping local byte context intact.

Determinism: integer-only byte ops, no regex, no locale, no float.

Reversibility: every byte either appears verbatim or is escaped; markers are
distinguishable by a unique escape prefix.

Back-end: lzma --extreme -9.
"""

from __future__ import annotations

import lzma

PRESET = 9 | lzma.PRESET_EXTREME

ESC = 0x01
LIT_ESC = 0xFF

# State codes — small integer alphabet so markers compress well
S_OUTSIDE = 1
S_TEXT = 2
S_TEMPLATE = 3
S_WIKILINK = 4
S_REF = 5
S_TABLE = 6


def _looks_like(data: bytes, i: int, prefix: bytes) -> bool:
    return data.startswith(prefix, i)


def _emit_marker(out: bytearray, state: int) -> None:
    out.append(ESC)
    out.append(state)


def _emit_byte(out: bytearray, b: int) -> None:
    if b == ESC:
        out.append(ESC)
        out.append(LIT_ESC)
    else:
        out.append(b)


def encode(data: bytes) -> bytes:
    out = bytearray()
    n = len(data)
    state_stack = [S_OUTSIDE]
    last_emitted_state = S_OUTSIDE
    i = 0

    def cur_state() -> int:
        return state_stack[-1]

    while i < n:
        b = data[i]

        push = None
        pop = False

        if cur_state() != S_TEXT and _looks_like(data, i, b'<text'):
            push = S_TEXT
        elif cur_state() == S_TEXT and _looks_like(data, i, b'</text>'):
            pop = True
        elif _looks_like(data, i, b'{{'):
            push = S_TEMPLATE
        elif cur_state() == S_TEMPLATE and _looks_like(data, i, b'}}'):
            pop = True
        elif _looks_like(data, i, b'[['):
            push = S_WIKILINK
        elif cur_state() == S_WIKILINK and _looks_like(data, i, b']]'):
            pop = True
        elif cur_state() != S_REF and _looks_like(data, i, b'<ref'):
            push = S_REF
        elif cur_state() == S_REF and _looks_like(data, i, b'</ref>'):
            pop = True
        elif _looks_like(data, i, b'{|'):
            push = S_TABLE
        elif cur_state() == S_TABLE and _looks_like(data, i, b'|}'):
            pop = True

        if push is not None:
            state_stack.append(push)
            if cur_state() != last_emitted_state:
                _emit_marker(out, cur_state())
                last_emitted_state = cur_state()

        _emit_byte(out, b)
        i += 1

        if pop and len(state_stack) > 1:
            state_stack.pop()
            if cur_state() != last_emitted_state:
                _emit_marker(out, cur_state())
                last_emitted_state = cur_state()

    return bytes(out)


def decode(stream: bytes) -> bytes:
    out = bytearray()
    n = len(stream)
    i = 0
    while i < n:
        b = stream[i]
        if b != ESC:
            out.append(b)
            i += 1
            continue
        if i + 1 >= n:
            raise ValueError("truncated escape at end of stream")
        nxt = stream[i + 1]
        if nxt == LIT_ESC:
            out.append(ESC)
            i += 2
        else:
            i += 2
    return bytes(out)


def compress(data: bytes) -> bytes:
    return lzma.compress(encode(data), preset=PRESET)


def decompress(data: bytes) -> bytes:
    return decode(lzma.decompress(data))
