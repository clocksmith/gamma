"""yellow_tucan_range_order_v1.

Custom no-cmix/no-lzma arithmetic coder with adaptive byte contexts.
This is a baseline for the new non-cmix predictor line: raw bytes are coded
by an integer arithmetic coder using online order-0/1/2 models.
"""

from __future__ import annotations

import struct

STATE_BITS = 32
FULL = 1 << STATE_BITS
HALF = FULL >> 1
QUARTER = HALF >> 1
THREE_QUARTER = QUARTER * 3
MAX_TOTAL = 4096
MAX_CTX2 = 8192

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


class Predictor:
    def __init__(self) -> None:
        self.o0 = Model()
        self.o1: dict[int, Model] = {}
        self.o2: dict[int, Model] = {}
        self.p1 = -1
        self.p2 = -1

    def _model(self) -> Model:
        if self.p2 >= 0:
            k = (self.p2 << 8) | self.p1
            m = self.o2.get(k)
            if m is not None:
                return m
            if len(self.o2) < MAX_CTX2:
                m = Model()
                self.o2[k] = m
                return m
        if self.p1 >= 0:
            return self.o1.setdefault(self.p1, Model())
        return self.o0

    def cf(self, s: int) -> tuple[Model, int, int, int]:
        m = self._model()
        c, f, t = m.cf(s)
        return m, c, f, t

    def find(self, target: int) -> tuple[Model, int, int, int, int]:
        m = self._model()
        s, c, f = m.find(target)
        return m, s, c, f, m.t

    def upd_all(self, s: int, chosen: Model) -> None:
        chosen.upd(s)
        if chosen is not self.o0:
            self.o0.upd(s)
        if self.p1 >= 0:
            m1 = self.o1.setdefault(self.p1, Model())
            if m1 is not chosen:
                m1.upd(s)
        self.p2, self.p1 = self.p1, s


def compress(data: bytes) -> bytes:
    p = Predictor()
    e = Enc()
    for b in data:
        m, c, f, t = p.cf(b)
        e.sym(c, f, t)
        p.upd_all(b, m)
    body = e.finish()
    LAST_STATS.clear()
    LAST_STATS.update({"ctx1": len(p.o1), "ctx2": len(p.o2)})
    return struct.pack(">I", len(data)) + body


def decompress(data: bytes) -> bytes:
    n = struct.unpack(">I", data[:4])[0]
    p = Predictor()
    d = Dec(data[4:])
    out = bytearray()
    for _ in range(n):
        m0 = p._model()
        x = d.target(m0.t)
        m, s, c, f, t = p.find(x)
        d.sym(c, f, t)
        out.append(s)
        p.upd_all(s, m)
    return bytes(out)


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
