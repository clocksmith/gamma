from __future__ import annotations

import bz2
import re

E = 0
ESC = 1
LIT0 = 255
BASE = 128
WORD_RE = re.compile(rb"[A-Za-z]{3,32}")
KS = (0, 4, 8, 12, 16, 20, 24, 32, 48, 64)
T = b"""<text xml:space="preserve">
</text>
<page>
</page>
<revision>
</revision>
<contributor>
</contributor>
<timestamp>
</timestamp>
<username>
</username>
<comment>
</comment>
<title>
</title>
<id>
</id>
<minor />
{{
}}
[[Category:
[[Image:
[[
]]
&quot;
&lt;
&gt;
&amp;
http://
https://
<ref
</ref>
|thumb
|right
|left
Category:
File:
Image:""".splitlines()
S = sorted(enumerate(T, 1), key=lambda x: -len(x[1]))
D = dict(enumerate(T, 1))
LAST_STATS: dict[str, int | str] = {}


def tok(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        if data[i] == E:
            out.extend((E, LIT0))
            i += 1
            continue
        for c, t in S:
            if data.startswith(t, i):
                out.extend((E, c))
                i += len(t)
                break
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def untok(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        b = data[i]
        if b:
            out.append(b)
            i += 1
            continue
        c = data[i + 1]
        out.extend(b"\0" if c == LIT0 else D[c])
        i += 2
    return bytes(out)


def pick_words(data: bytes, k: int) -> list[bytes]:
    counts: dict[bytes, int] = {}
    for m in WORD_RE.finditer(data):
        w = m.group(0)
        counts[w] = counts.get(w, 0) + 1
    scored = []
    for w, f in counts.items():
        save = f * (len(w) - 1) - len(w) - 1
        if save > 0:
            scored.append((save, w))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [w for _, w in scored[:k]]


def esc(data: bytes) -> bytes:
    if not any(b == ESC or b >= BASE for b in data):
        return data
    out = bytearray()
    for b in data:
        if b == ESC or b >= BASE:
            out.append(ESC)
        out.append(b)
    return bytes(out)


def word_pack(data: bytes, words: list[bytes]) -> bytes:
    out = bytearray([len(words)])
    for w in words:
        out.append(len(w))
        out.extend(w)
    if not words:
        out.extend(esc(data))
        return bytes(out)
    mp = {w: bytes([BASE + i]) for i, w in enumerate(words)}
    pat = re.compile(b"|".join(re.escape(w) for w in words))
    pos = 0
    for m in pat.finditer(data):
        out.extend(esc(data[pos:m.start()]))
        out.extend(mp[m.group(0)])
        pos = m.end()
    out.extend(esc(data[pos:]))
    return bytes(out)


def word_unpack(data: bytes) -> bytes:
    k = data[0]
    pos = 1
    words = []
    for _ in range(k):
        n = data[pos]
        pos += 1
        words.append(data[pos:pos + n])
        pos += n
    out = bytearray()
    while pos < len(data):
        b = data[pos]
        pos += 1
        if b == ESC:
            out.append(data[pos])
            pos += 1
        elif b >= BASE:
            out.extend(words[b - BASE])
        else:
            out.append(b)
    return bytes(out)


def compress(data: bytes) -> bytes:
    raw = bz2.compress(data, 9)
    t = tok(data)
    best_k = 0
    best_body = bz2.compress(word_pack(t, []), 9)
    for k in KS[1:]:
        body = bz2.compress(word_pack(t, pick_words(t, k)), 9)
        if len(body) < len(best_body):
            best_body = body
            best_k = k
    LAST_STATS.clear()
    LAST_STATS.update({"best_k": best_k, "token_size": len(t), "word_body_size": len(best_body)})
    if len(raw) <= len(best_body):
        LAST_STATS["mode"] = "raw"
        return b"OWB1r" + raw
    LAST_STATS["mode"] = "opcode_word"
    return b"OWB1w" + best_body


def decompress(data: bytes) -> bytes:
    if data[:4] != b"OWB1":
        raise ValueError("bad opcode word bz2 archive")
    mode = data[4:5]
    body = bz2.decompress(data[5:])
    if mode == b"r":
        return body
    if mode == b"w":
        return untok(word_unpack(body))
    raise ValueError("bad opcode word bz2 mode")


def stats() -> dict[str, int | str]:
    return dict(LAST_STATS)
