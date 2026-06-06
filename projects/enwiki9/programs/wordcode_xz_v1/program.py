from __future__ import annotations

import re
import struct
import subprocess

ESC = 2
BASE = 128
MAX_K = 128
WORD_RE = re.compile(rb"[A-Za-z]{3,32}")
XZ = ["xz", "-q", "-c", "-T1", "--check=crc32", "--lzma2=preset=9e,dict=1024MiB"]


def _pick(data: bytes) -> list[bytes]:
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
    return [w for _, w in scored[:MAX_K]]


def _esc(data: bytes) -> bytes:
    if not any(b == ESC or b >= BASE for b in data):
        return data
    out = bytearray()
    for b in data:
        if b == ESC or b >= BASE:
            out.append(ESC)
        out.append(b)
    return bytes(out)


def _sub(data: bytes, words: list[bytes]) -> bytes:
    if not words:
        return _esc(data)
    code = {w: bytes([BASE + i]) for i, w in enumerate(words)}
    pat = re.compile(b"|".join(re.escape(w) for w in words))
    out = []
    pos = 0
    for m in pat.finditer(data):
        out.append(_esc(data[pos : m.start()]))
        out.append(code[m.group(0)])
        pos = m.end()
    out.append(_esc(data[pos:]))
    return b"".join(out)


def _expand(data: bytes, words: list[bytes]) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        b = data[i]
        if b == ESC:
            i += 1
            out.append(data[i])
        elif b >= BASE:
            out.extend(words[b - BASE])
        else:
            out.append(b)
        i += 1
    return bytes(out)


def compress(data: bytes) -> bytes:
    words = _pick(data)
    hdr = bytearray([len(words)])
    for w in words:
        hdr.append(len(w))
        hdr.extend(w)
    inner = struct.pack(">I", len(hdr)) + hdr + _sub(data, words)
    return subprocess.run(XZ, input=inner, stdout=subprocess.PIPE, check=True).stdout


def decompress(data: bytes) -> bytes:
    inner = subprocess.run(
        ["xz", "-q", "-d", "-c", "--memlimit-decompress=0"],
        input=data,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    (hlen,) = struct.unpack(">I", inner[:4])
    hdr = inner[4 : 4 + hlen]
    pos = 1
    words = []
    for _ in range(hdr[0]):
        n = hdr[pos]
        pos += 1
        words.append(hdr[pos : pos + n])
        pos += n
    return _expand(inner[4 + hlen :], words)
