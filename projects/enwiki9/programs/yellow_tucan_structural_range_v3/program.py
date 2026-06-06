"""yellow_tucan_structural_range_v3.

Custom no-cmix/no-lzma arithmetic coder. V3 uses an integer mixture of
global, previous-byte, and MediaWiki parser-state distributions instead of
selecting one context. Raw bytes are untouched.
"""

from __future__ import annotations

import struct

FULL = 1 << 32
HALF = FULL >> 1
QUARTER = HALF >> 1
THREE_QUARTER = QUARTER * 3
MAX_TOTAL = 4096
MAX_CTX = 16384
MIN_TRAINED = 288
LAST_STATS: dict[str, int] = {}


class BO:
    def __init__(self) -> None:
        self.o = bytearray()
        self.c = 0
        self.n = 0

    def b(self, x: int) -> None:
        self.c = (self.c << 1) | x
        self.n += 1
        if self.n == 8:
            self.o.append(self.c)
            self.c = self.n = 0

    def done(self) -> bytes:
        if self.n:
            self.o.append(self.c << (8 - self.n))
        return bytes(self.o)


class BI:
    def __init__(self, d: bytes) -> None:
        self.d = d
        self.i = self.c = self.n = 0

    def b(self) -> int:
        if not self.n:
            self.c = self.d[self.i] if self.i < len(self.d) else 0
            self.i += 1
            self.n = 8
        self.n -= 1
        return (self.c >> self.n) & 1


class AC:
    def __init__(self, d: bytes | None = None) -> None:
        self.lo = 0
        self.hi = FULL - 1
        self.p = 0
        if d is None:
            self.bo = BO()
            self.bi = None
            self.code = 0
        else:
            self.bo = None
            self.bi = BI(d)
            self.code = 0
            for _ in range(32):
                self.code = (self.code << 1) | self.bi.b()

    def emit(self, x: int) -> None:
        self.bo.b(x)
        while self.p:
            self.bo.b(1 - x)
            self.p -= 1

    def enc(self, c: int, f: int, t: int) -> None:
        r = self.hi - self.lo + 1
        self.hi = self.lo + (r * (c + f) // t) - 1
        self.lo += r * c // t
        while True:
            if self.hi < HALF:
                self.emit(0)
            elif self.lo >= HALF:
                self.emit(1)
                self.lo -= HALF
                self.hi -= HALF
            elif self.lo >= QUARTER and self.hi < THREE_QUARTER:
                self.p += 1
                self.lo -= QUARTER
                self.hi -= QUARTER
            else:
                break
            self.lo <<= 1
            self.hi = (self.hi << 1) | 1

    def val(self, t: int) -> int:
        r = self.hi - self.lo + 1
        return ((self.code - self.lo + 1) * t - 1) // r

    def dec(self, c: int, f: int, t: int) -> None:
        r = self.hi - self.lo + 1
        self.hi = self.lo + (r * (c + f) // t) - 1
        self.lo += r * c // t
        while True:
            if self.hi < HALF:
                pass
            elif self.lo >= HALF:
                self.lo -= HALF
                self.hi -= HALF
                self.code -= HALF
            elif self.lo >= QUARTER and self.hi < THREE_QUARTER:
                self.lo -= QUARTER
                self.hi -= QUARTER
                self.code -= QUARTER
            else:
                break
            self.lo <<= 1
            self.hi = (self.hi << 1) | 1
            self.code = (self.code << 1) | self.bi.b()

    def done(self) -> bytes:
        self.p += 1
        self.emit(0 if self.lo < QUARTER else 1)
        return self.bo.done()


class M:
    def __init__(self) -> None:
        self.c = [1] * 256
        self.t = 256

    def upd(self, s: int) -> None:
        self.c[s] += 1
        self.t += 1
        if self.t >= MAX_TOTAL:
            self.c = [(x + 1) >> 1 for x in self.c]
            self.t = sum(self.c)


class ST:
    def __init__(self) -> None:
        self.mode = self.bracket = self.brace = self.digit = self.p1 = self.p2 = 0

    def key(self) -> int:
        return (
            (self.mode << 24)
            ^ (self.bracket << 20)
            ^ (self.brace << 16)
            ^ (self.digit << 12)
            ^ (self.p2 << 8)
            ^ self.p1
        )

    def upd(self, b: int) -> None:
        if b == 60:
            self.mode = 1
        elif b == 62:
            self.mode = 0
        elif b == 38:
            self.mode = 2
        elif self.mode == 2 and b == 59:
            self.mode = 0
        if b == 91:
            self.bracket = min(3, self.bracket + 1)
        elif b == 93:
            self.bracket = max(0, self.bracket - 1)
        if b == 123:
            self.brace = min(3, self.brace + 1)
        elif b == 125:
            self.brace = max(0, self.brace - 1)
        self.digit = 1 if 48 <= b <= 57 else 0
        self.p2, self.p1 = self.p1, b


class P:
    def __init__(self) -> None:
        self.g = M()
        self.o1: dict[int, M] = {}
        self.sc: dict[int, M] = {}
        self.st = ST()

    def models(self, make: bool) -> list[tuple[M, int]]:
        out = [(self.g, 1)]
        m1 = self.o1.get(self.st.p1)
        if m1 is not None and m1.t >= MIN_TRAINED:
            out.append((m1, 4))
        k = self.st.key()
        ms = self.sc.get(k)
        if ms is not None and ms.t >= MIN_TRAINED:
            out.append((ms, 8))
        elif make and ms is None and len(self.sc) < MAX_CTX:
            self.sc[k] = M()
        return out

    def dist(self) -> tuple[list[int], int]:
        d = [0] * 256
        for m, w in self.models(True):
            c = m.c
            for i in range(256):
                d[i] += c[i] * w
        return d, sum(d)

    def upd(self, s: int) -> None:
        self.g.upd(s)
        self.o1.setdefault(self.st.p1, M()).upd(s)
        m = self.sc.get(self.st.key())
        if m is not None:
            m.upd(s)
        self.st.upd(s)


def _cf(d: list[int], s: int) -> tuple[int, int]:
    return sum(d[:s]), d[s]


def _find(d: list[int], x: int) -> tuple[int, int, int]:
    c = 0
    for s, f in enumerate(d):
        if x < c + f:
            return s, c, f
        c += f
    raise ValueError("bad target")


def compress(data: bytes) -> bytes:
    p = P()
    a = AC()
    for b in data:
        d, t = p.dist()
        c, f = _cf(d, b)
        a.enc(c, f, t)
        p.upd(b)
    LAST_STATS.clear()
    LAST_STATS.update({"ctx1": len(p.o1), "structural_contexts": len(p.sc)})
    return struct.pack(">I", len(data)) + a.done()


def decompress(data: bytes) -> bytes:
    n = struct.unpack(">I", data[:4])[0]
    p = P()
    a = AC(data[4:])
    out = bytearray()
    for _ in range(n):
        d, t = p.dist()
        s, c, f = _find(d, a.val(t))
        a.dec(c, f, t)
        out.append(s)
        p.upd(s)
    return bytes(out)


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
