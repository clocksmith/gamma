from __future__ import annotations

import re
import subprocess

XZ = ["xz", "-q", "-c", "-T1", "--check=crc32", "--lzma2=preset=9e,dict=1024MiB"]
UNXZ = ["xz", "-q", "-d", "-c", "--memlimit-decompress=0"]

OPEN_RE = re.compile(
    rb"<title>|<id>|<timestamp>|<username>|<comment>|<text xml:space=\"preserve\">"
)
FIELDS = {
    b"<title>": (1, b"</title>"),
    b"<id>": (2, b"</id>"),
    b"<timestamp>": (3, b"</timestamp>"),
    b"<username>": (4, b"</username>"),
    b"<comment>": (5, b"</comment>"),
    b'<text xml:space="preserve">': (6, b"</text>"),
}
WORD_RE = re.compile(rb"[A-Za-z]{3,32}")
ESC = 2
BASE = 128
MAX_WORDS = 128


def _xz(data: bytes) -> bytes:
    return subprocess.run(XZ, input=data, stdout=subprocess.PIPE, check=True).stdout


def _unxz(data: bytes) -> bytes:
    return subprocess.run(UNXZ, input=data, stdout=subprocess.PIPE, check=True).stdout


def _putv(out: bytearray, n: int) -> None:
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)


def _getv(data: bytes, pos: int) -> tuple[int, int]:
    shift = 0
    n = 0
    while True:
        b = data[pos]
        pos += 1
        n |= (b & 127) << shift
        if b < 128:
            return n, pos
        shift += 7


def _emit_skel(out: bytearray, chunk: bytes) -> None:
    if 0 not in chunk:
        out.extend(chunk)
        return
    for b in chunk:
        if b == 0:
            out.extend((0, 0))
        else:
            out.append(b)


def _pack_graph(data: bytes) -> bytes:
    skel = bytearray()
    channels: list[list[bytes]] = [[] for _ in range(7)]
    pos = 0
    for m in OPEN_RE.finditer(data):
        if m.start() < pos:
            continue
        code, close = FIELDS[m.group(0)]
        end = data.find(close, m.end())
        if end < 0:
            continue
        _emit_skel(skel, data[pos : m.end()])
        skel.extend((0, code))
        channels[code].append(data[m.end() : end])
        pos = end
    _emit_skel(skel, data[pos:])

    out = bytearray(b"GF1")
    _putv(out, len(skel))
    out.extend(skel)
    for code in range(1, 7):
        _putv(out, len(channels[code]))
        for item in channels[code]:
            _putv(out, len(item))
            out.extend(item)
    return bytes(out)


def _unpack_graph(data: bytes) -> bytes:
    if data[:3] != b"GF1":
        raise ValueError("bad graph pack")
    pos = 3
    skel_len, pos = _getv(data, pos)
    skel = data[pos : pos + skel_len]
    pos += skel_len
    channels: list[list[bytes]] = [[] for _ in range(7)]
    for code in range(1, 7):
        n, pos = _getv(data, pos)
        for _ in range(n):
            size, pos = _getv(data, pos)
            channels[code].append(data[pos : pos + size])
            pos += size

    idx = [0] * 7
    out = bytearray()
    i = 0
    while i < len(skel):
        b = skel[i]
        if b:
            out.append(b)
            i += 1
            continue
        code = skel[i + 1]
        i += 2
        if code == 0:
            out.append(0)
        else:
            j = idx[code]
            out.extend(channels[code][j])
            idx[code] = j + 1
    return bytes(out)


def _pick_words(data: bytes) -> list[bytes]:
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
    return [w for _, w in scored[:MAX_WORDS]]


def _esc(data: bytes) -> bytes:
    if not any(b == ESC or b >= BASE for b in data):
        return data
    out = bytearray()
    for b in data:
        if b == ESC or b >= BASE:
            out.append(ESC)
        out.append(b)
    return bytes(out)


def _pack_words(data: bytes) -> bytes:
    words = _pick_words(data)
    out = bytearray(b"WD1")
    _putv(out, len(words))
    for w in words:
        _putv(out, len(w))
        out.extend(w)
    if not words:
        out.extend(_esc(data))
        return bytes(out)
    code = {w: bytes([BASE + i]) for i, w in enumerate(words)}
    pat = re.compile(b"|".join(re.escape(w) for w in words))
    pos = 0
    for m in pat.finditer(data):
        out.extend(_esc(data[pos : m.start()]))
        out.extend(code[m.group(0)])
        pos = m.end()
    out.extend(_esc(data[pos:]))
    return bytes(out)


def _unpack_words(data: bytes) -> bytes:
    if data[:3] != b"WD1":
        raise ValueError("bad word pack")
    pos = 3
    n, pos = _getv(data, pos)
    words = []
    for _ in range(n):
        size, pos = _getv(data, pos)
        words.append(data[pos : pos + size])
        pos += size
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
    raw = b"R" + _xz(data)
    packed = _pack_words(_pack_graph(data))
    graph = b"F" + _xz(packed)
    return graph if len(graph) < len(raw) else raw


def decompress(data: bytes) -> bytes:
    mode = data[:1]
    inner = _unxz(data[1:])
    if mode == b"R":
        return inner
    if mode == b"F":
        return _unpack_graph(_unpack_words(inner))
    raise ValueError("bad graph_fim_xz_selector mode")
