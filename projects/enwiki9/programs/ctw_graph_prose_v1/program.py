from __future__ import annotations

import bz2
import lzma
import re
import struct

P = 9 | lzma.PRESET_EXTREME
STATE_BITS = 32
FULL = 1 << STATE_BITS
HALF = FULL >> 1
QUARTER = HALF >> 1
THREE_QUARTER = QUARTER * 3
SCALE = 4096
MAX_CTX = 1 << 18
MAGIC = b"CGP1"
ESC = 2
BASE = 128
MAX_WORDS = 128

OPEN_RE = re.compile(rb"<title>|<id>|<timestamp>|<username>|<comment>|<text xml:space=\"preserve\">")
FIELDS = {
    b"<title>": (1, b"</title>"),
    b"<id>": (2, b"</id>"),
    b"<timestamp>": (3, b"</timestamp>"),
    b"<username>": (4, b"</username>"),
    b"<comment>": (5, b"</comment>"),
    b'<text xml:space="preserve">': (6, b"</text>"),
}
WORD_RE = re.compile(rb"[A-Za-z]{3,32}")
TOKENS = sorted(
    b"""<text xml:space="preserve">
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
Image:
|title=
|date=
|accessdate=
|publisher=
|author=
|first=
|last=
== References ==
== External links ==
== See also ==""".splitlines(),
    key=len,
    reverse=True,
)

LAST_STATS: dict[str, int | str] = {}


def pv(out: bytearray, n: int) -> None:
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)


def gv(data: bytes, pos: int) -> tuple[int, int]:
    n = 0
    shift = 0
    while True:
        b = data[pos]
        pos += 1
        n |= (b & 127) << shift
        if b < 128:
            return n, pos
        shift += 7


def emit_skel(out: bytearray, chunk: bytes) -> None:
    if 0 not in chunk:
        out.extend(chunk)
        return
    for b in chunk:
        out.extend((0, 0)) if b == 0 else out.append(b)


def graph_pack(data: bytes) -> bytes:
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
        emit_skel(skel, data[pos:m.end()])
        skel.extend((0, code))
        channels[code].append(data[m.end():end])
        pos = end
    emit_skel(skel, data[pos:])
    out = bytearray(b"GF1")
    pv(out, len(skel))
    out.extend(skel)
    for code in range(1, 7):
        pv(out, len(channels[code]))
        for item in channels[code]:
            pv(out, len(item))
            out.extend(item)
    return bytes(out)


def graph_unpack(data: bytes) -> bytes:
    if data[:3] != b"GF1":
        raise ValueError("bad graph payload")
    pos = 3
    size, pos = gv(data, pos)
    skel = data[pos:pos + size]
    pos += size
    channels: list[list[bytes]] = [[] for _ in range(7)]
    for code in range(1, 7):
        n, pos = gv(data, pos)
        for _ in range(n):
            size, pos = gv(data, pos)
            channels[code].append(data[pos:pos + size])
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


def token_pack(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        if data[i] == 0:
            out.extend((0, 255))
            i += 1
            continue
        for n, tok in enumerate(TOKENS, 1):
            if data.startswith(tok, i):
                out.extend((0, n))
                i += len(tok)
                break
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def token_unpack(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        b = data[i]
        if b:
            out.append(b)
            i += 1
            continue
        n = data[i + 1]
        i += 2
        if n == 255:
            out.append(0)
        elif 0 < n <= len(TOKENS):
            out.extend(TOKENS[n - 1])
        else:
            raise ValueError("bad token code")
    return bytes(out)


def esc(data: bytes) -> bytes:
    if not any(b == ESC or b >= BASE for b in data):
        return data
    out = bytearray()
    for b in data:
        if b == ESC or b >= BASE:
            out.append(ESC)
        out.append(b)
    return bytes(out)


def pick_words(data: bytes) -> list[bytes]:
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


def word_pack(data: bytes) -> bytes:
    words = pick_words(data)
    out = bytearray(b"WD1")
    pv(out, len(words))
    for w in words:
        pv(out, len(w))
        out.extend(w)
    if not words:
        out.extend(esc(data))
        return bytes(out)
    code = {w: bytes([BASE + i]) for i, w in enumerate(words)}
    pat = re.compile(b"|".join(re.escape(w) for w in words))
    pos = 0
    for m in pat.finditer(data):
        out.extend(esc(data[pos:m.start()]))
        out.extend(code[m.group(0)])
        pos = m.end()
    out.extend(esc(data[pos:]))
    return bytes(out)


def word_unpack(data: bytes) -> bytes:
    if data[:3] != b"WD1":
        raise ValueError("bad word payload")
    pos = 3
    n, pos = gv(data, pos)
    words = []
    for _ in range(n):
        size, pos = gv(data, pos)
        words.append(data[pos:pos + size])
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


def transform(data: bytes) -> bytes:
    return word_pack(token_pack(graph_pack(data)))


def untransform(data: bytes) -> bytes:
    return graph_unpack(token_unpack(word_unpack(data)))


class BitsOut:
    def __init__(self) -> None:
        self.out = bytearray()
        self.cur = 0
        self.n = 0

    def bit(self, b: int) -> None:
        self.cur = (self.cur << 1) | b
        self.n += 1
        if self.n == 8:
            self.out.append(self.cur)
            self.cur = 0
            self.n = 0

    def finish(self) -> bytes:
        if self.n:
            self.out.append(self.cur << (8 - self.n))
        return bytes(self.out)


class BitsIn:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.i = 0
        self.cur = 0
        self.n = 0

    def bit(self) -> int:
        if self.n == 0:
            self.cur = self.data[self.i] if self.i < len(self.data) else 0
            self.i += 1
            self.n = 8
        self.n -= 1
        return (self.cur >> self.n) & 1


class Enc:
    def __init__(self) -> None:
        self.low = 0
        self.high = FULL - 1
        self.pending = 0
        self.bits = BitsOut()

    def emit(self, b: int) -> None:
        self.bits.bit(b)
        while self.pending:
            self.bits.bit(1 - b)
            self.pending -= 1

    def sym(self, cum: int, freq: int, total: int) -> None:
        span = self.high - self.low + 1
        self.high = self.low + (span * (cum + freq) // total) - 1
        self.low = self.low + (span * cum // total)
        while True:
            if self.high < HALF:
                self.emit(0)
            elif self.low >= HALF:
                self.emit(1)
                self.low -= HALF
                self.high -= HALF
            elif self.low >= QUARTER and self.high < THREE_QUARTER:
                self.pending += 1
                self.low -= QUARTER
                self.high -= QUARTER
            else:
                break
            self.low <<= 1
            self.high = (self.high << 1) | 1

    def finish(self) -> bytes:
        self.pending += 1
        self.emit(0 if self.low < QUARTER else 1)
        return self.bits.finish()


class Dec:
    def __init__(self, data: bytes) -> None:
        self.low = 0
        self.high = FULL - 1
        self.bits = BitsIn(data)
        self.code = 0
        for _ in range(STATE_BITS):
            self.code = (self.code << 1) | self.bits.bit()

    def target(self, total: int) -> int:
        span = self.high - self.low + 1
        return ((self.code - self.low + 1) * total - 1) // span

    def sym(self, cum: int, freq: int, total: int) -> None:
        span = self.high - self.low + 1
        self.high = self.low + (span * (cum + freq) // total) - 1
        self.low = self.low + (span * cum // total)
        while True:
            if self.high < HALF:
                pass
            elif self.low >= HALF:
                self.low -= HALF
                self.high -= HALF
                self.code -= HALF
            elif self.low >= QUARTER and self.high < THREE_QUARTER:
                self.low -= QUARTER
                self.high -= QUARTER
                self.code -= QUARTER
            else:
                break
            self.low <<= 1
            self.high = (self.high << 1) | 1
            self.code = (self.code << 1) | self.bits.bit()


class Node:
    __slots__ = ("z", "o")

    def __init__(self) -> None:
        self.z = 1
        self.o = 1

    def update(self, b: int) -> None:
        if b:
            self.o += 1
        else:
            self.z += 1
        if self.z + self.o >= 2048:
            self.z = (self.z + 1) >> 1
            self.o = (self.o + 1) >> 1


class Clock:
    def __init__(self) -> None:
        self.prev = 0
        self.prev2 = 0
        self.cls = 0
        self.run = 0
        self.mode = 0
        self.pos = 0
        self.tail = bytearray()

    def update(self, b: int) -> None:
        if 65 <= b <= 90:
            cls = 1
        elif 97 <= b <= 122:
            cls = 2
        elif 48 <= b <= 57:
            cls = 3
        elif b in (9, 10, 13, 32):
            cls = 4
        elif b >= BASE:
            cls = 5
        elif b in (60, 62, 91, 93, 123, 124, 125):
            cls = 6
        else:
            cls = 7
        self.run = min(self.run + 1, 15) if cls == self.cls else 1
        self.cls = cls
        self.tail.append(b)
        if len(self.tail) > 32:
            del self.tail[0]
        t = bytes(self.tail)
        if t.endswith(b"<text"):
            self.mode = 1
        elif t.endswith(b"</text>"):
            self.mode = 0
        elif t.endswith(b"{{"):
            self.mode = 2
        elif t.endswith(b"}}"):
            self.mode = 1
        elif t.endswith(b"[["):
            self.mode = 3
        elif t.endswith(b"]]"):
            self.mode = 1
        self.prev2 = self.prev
        self.prev = b
        self.pos += 1


class Mix:
    def __init__(self) -> None:
        self.nodes: dict[int, Node] = {}
        self.clock = Clock()
        self.bits = 1

    def keys(self, bitpos: int) -> tuple[int, ...]:
        c = self.clock
        lb = self.bits & 65535
        return (
            bitpos,
            0x10000 ^ (bitpos << 8) ^ c.prev,
            0x20000 ^ (bitpos << 16) ^ (c.prev2 << 8) ^ c.prev,
            0x30000 ^ (bitpos << 12) ^ (c.mode << 8) ^ (c.cls << 4) ^ c.run,
            0x40000 ^ (bitpos << 20) ^ (c.mode << 16) ^ lb,
            0x50000 ^ (bitpos << 19) ^ ((c.pos >> 6) & 31) ^ (c.prev << 5) ^ c.cls,
        )

    def p1(self, bitpos: int) -> int:
        p = 0.5
        mass = 1.0
        for key in self.keys(bitpos):
            node = self.nodes.get(key)
            if node is None:
                continue
            total = node.z + node.o
            q = node.o / total
            w = 1.0 + min(128, total)
            p = (p * mass + q * w) / (mass + w)
            mass += w
        freq = int(p * SCALE)
        if freq <= 0:
            return 1
        if freq >= SCALE:
            return SCALE - 1
        return freq

    def update_bit(self, bitpos: int, bit: int) -> None:
        for key in self.keys(bitpos):
            node = self.nodes.get(key)
            if node is None:
                if len(self.nodes) >= MAX_CTX:
                    continue
                node = Node()
                self.nodes[key] = node
            node.update(bit)
        self.bits = ((self.bits << 1) | bit) & 131071

    def update_byte(self, b: int) -> None:
        self.clock.update(b)


def ctw_encode(data: bytes) -> bytes:
    mix = Mix()
    enc = Enc()
    for b in data:
        for bitpos in range(8):
            bit = (b >> (7 - bitpos)) & 1
            f1 = mix.p1(bitpos)
            f0 = SCALE - f1
            enc.sym(f0 if bit else 0, f1 if bit else f0, SCALE)
            mix.update_bit(bitpos, bit)
        mix.update_byte(b)
    body = enc.finish()
    LAST_STATS["ctw_contexts"] = len(mix.nodes)
    return struct.pack(">Q", len(data)) + body


def ctw_decode(data: bytes) -> bytes:
    (n,) = struct.unpack(">Q", data[:8])
    dec = Dec(data[8:])
    mix = Mix()
    out = bytearray()
    for _ in range(n):
        b = 0
        for bitpos in range(8):
            f1 = mix.p1(bitpos)
            f0 = SCALE - f1
            target = dec.target(SCALE)
            if target < f0:
                bit = 0
                dec.sym(0, f0, SCALE)
            else:
                bit = 1
                dec.sym(f0, f1, SCALE)
            b = (b << 1) | bit
            mix.update_bit(bitpos, bit)
        out.append(b)
        mix.update_byte(b)
    return bytes(out)


def xz(data: bytes) -> bytes:
    return lzma.compress(data, preset=P, check=0)


def uxz(data: bytes) -> bytes:
    return lzma.decompress(data)


def compress(data: bytes) -> bytes:
    packed = transform(data)
    choices = [
        (b"r", bz2.compress(data, 9)),
        (b"x", xz(data)),
        (b"g", xz(packed)),
        (b"b", bz2.compress(packed, 9)),
        (b"c", ctw_encode(packed)),
    ]
    mode, body = min(choices, key=lambda x: len(x[1]))
    LAST_STATS["mode"] = mode.decode()
    LAST_STATS["packed_size"] = len(packed)
    LAST_STATS["archive_body_size"] = len(body)
    return MAGIC + mode + body


def decompress(data: bytes) -> bytes:
    if data[:4] != MAGIC:
        raise ValueError("bad ctw graph prose archive")
    mode = data[4:5]
    body = data[5:]
    if mode == b"r":
        return bz2.decompress(body)
    if mode == b"x":
        return uxz(body)
    if mode == b"g":
        return untransform(uxz(body))
    if mode == b"b":
        return untransform(bz2.decompress(body))
    if mode == b"c":
        return untransform(ctw_decode(body))
    raise ValueError("bad ctw graph prose mode")


def stats() -> dict[str, int | str]:
    return dict(LAST_STATS)
