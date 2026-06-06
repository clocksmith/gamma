"""yellow_tucan_structural_range_v1.

Custom no-cmix/no-lzma arithmetic coder with MediaWiki parser-state contexts.
Raw bytes are unchanged; parser state selects probability tables.
"""

from __future__ import annotations

import struct

STATE_BITS = 32
FULL = 1 << STATE_BITS
HALF = FULL >> 1
QUARTER = HALF >> 1
THREE_QUARTER = QUARTER * 3
MAX_TOTAL = 4096
MAX_CTX = 16384

LAST_STATS: dict[str, int] = {}


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

    def _emit(self, b: int) -> None:
        self.bits.bit(b)
        while self.pending:
            self.bits.bit(1 - b)
            self.pending -= 1

    def sym(self, cum: int, freq: int, total: int) -> None:
        r = self.high - self.low + 1
        self.high = self.low + (r * (cum + freq) // total) - 1
        self.low = self.low + (r * cum // total)
        while True:
            if self.high < HALF:
                self._emit(0)
            elif self.low >= HALF:
                self._emit(1)
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
        self._emit(0 if self.low < QUARTER else 1)
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
        r = self.high - self.low + 1
        return ((self.code - self.low + 1) * total - 1) // r

    def sym(self, cum: int, freq: int, total: int) -> None:
        r = self.high - self.low + 1
        self.high = self.low + (r * (cum + freq) // total) - 1
        self.low = self.low + (r * cum // total)
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


class Model:
    def __init__(self) -> None:
        self.c = [1] * 256
        self.t = 256

    def cf(self, s: int) -> tuple[int, int, int]:
        return sum(self.c[:s]), self.c[s], self.t

    def find(self, x: int) -> tuple[int, int, int]:
        c = 0
        for s, f in enumerate(self.c):
            if x < c + f:
                return s, c, f
            c += f
        raise ValueError("bad arithmetic target")

    def upd(self, s: int) -> None:
        self.c[s] += 1
        self.t += 1
        if self.t >= MAX_TOTAL:
            self.c = [(x + 1) >> 1 for x in self.c]
            self.t = sum(self.c)


class State:
    def __init__(self) -> None:
        self.mode = 0
        self.bracket = 0
        self.brace = 0
        self.digit = 0
        self.prev = 0

    def key(self) -> int:
        return (
            (self.mode << 24)
            ^ (self.bracket << 20)
            ^ (self.brace << 16)
            ^ (self.digit << 12)
            ^ self.prev
        )

    def update(self, b: int) -> None:
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
        self.prev = b


class Predictor:
    def __init__(self) -> None:
        self.o0 = Model()
        self.ctx: dict[int, Model] = {}
        self.st = State()

    def model(self) -> Model:
        k = self.st.key()
        m = self.ctx.get(k)
        if m is not None:
            return m
        if len(self.ctx) < MAX_CTX:
            m = Model()
            self.ctx[k] = m
            return m
        return self.o0

    def upd(self, s: int, m: Model) -> None:
        m.upd(s)
        if m is not self.o0:
            self.o0.upd(s)
        self.st.update(s)


def compress(data: bytes) -> bytes:
    p = Predictor()
    e = Enc()
    for b in data:
        m = p.model()
        c, f, t = m.cf(b)
        e.sym(c, f, t)
        p.upd(b, m)
    body = e.finish()
    LAST_STATS.clear()
    LAST_STATS.update({"contexts": len(p.ctx)})
    return struct.pack(">I", len(data)) + body


def decompress(data: bytes) -> bytes:
    n = struct.unpack(">I", data[:4])[0]
    p = Predictor()
    d = Dec(data[4:])
    out = bytearray()
    for _ in range(n):
        m = p.model()
        x = d.target(m.t)
        s, c, f = m.find(x)
        d.sym(c, f, m.t)
        out.append(s)
        p.upd(s, m)
    return bytes(out)


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
