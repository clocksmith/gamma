from __future__ import annotations

import struct

STATE_BITS = 32
FULL = 1 << STATE_BITS
HALF = FULL >> 1
QUARTER = HALF >> 1
THREE_QUARTER = QUARTER * 3
MAX_TOTAL = 8192
MAX_DIST = 32768
MAX_MODELS = 70000
MAGIC = b"GUR1"

LAST_STATS: dict[str, int] = {}


class BitsOut:
    def __init__(self) -> None:
        self.out = bytearray()
        self.cur = 0
        self.n = 0

    def bit(self, bit: int) -> None:
        self.cur = (self.cur << 1) | bit
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


class Encoder:
    def __init__(self) -> None:
        self.low = 0
        self.high = FULL - 1
        self.pending = 0
        self.bits = BitsOut()

    def _emit(self, bit: int) -> None:
        self.bits.bit(bit)
        while self.pending:
            self.bits.bit(1 - bit)
            self.pending -= 1

    def sym(self, cum: int, freq: int, total: int) -> None:
        span = self.high - self.low + 1
        self.high = self.low + (span * (cum + freq) // total) - 1
        self.low = self.low + (span * cum // total)
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


class Decoder:
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


class Model:
    def __init__(self) -> None:
        self.c = [1] * 256
        self.t = 256

    def update(self, sym: int) -> None:
        self.c[sym] += 1
        self.t += 1
        if self.t >= MAX_TOTAL:
            self.c = [(v + 1) >> 1 for v in self.c]
            self.t = sum(self.c)


def _byte_class(b: int) -> int:
    if 65 <= b <= 90:
        return 1
    if 97 <= b <= 122:
        return 2
    if 48 <= b <= 57:
        return 3
    if b in (9, 10, 13, 32):
        return 4
    if b in (34, 38, 39, 47, 60, 61, 62):
        return 5
    if b in (91, 93, 123, 124, 125):
        return 6
    if b < 32 or b >= 128:
        return 7
    return 8


class Clock:
    OUT = 0
    TITLE = 1
    ID = 2
    TIMESTAMP = 3
    USERNAME = 4
    COMMENT = 5
    TEXT = 6

    def __init__(self) -> None:
        self.field = self.OUT
        self.wiki = 0
        self.prev = 0
        self.prev2 = 0
        self.prev_class = 0
        self.line_col = 0
        self.page_phase = 0
        self.pos = 0
        self.tail = bytearray()

    def keys(self) -> list[int]:
        band = min(self.line_col >> 3, 31)
        clock = (self.pos >> 10) & 7
        return [
            0,
            0x10000 | self.prev,
            0x200000 | (self.prev2 << 8) | self.prev,
            0x300000 | (self.field << 12) | (self.wiki << 8) | self.prev_class,
            0x400000 | (self.field << 16) | (self.wiki << 12) | self.prev,
            0x500000 | (band << 8) | self.prev_class,
            0x600000 | (self.page_phase << 12) | (clock << 8) | self.prev_class,
        ]

    def _set_field(self) -> None:
        t = bytes(self.tail)
        if t.endswith(b"<title>"):
            self.field = self.TITLE
        elif t.endswith(b"</title>"):
            self.field = self.OUT
        elif t.endswith(b"<id>"):
            self.field = self.ID
        elif t.endswith(b"</id>"):
            self.field = self.OUT
        elif t.endswith(b"<timestamp>"):
            self.field = self.TIMESTAMP
        elif t.endswith(b"</timestamp>"):
            self.field = self.OUT
        elif t.endswith(b"<username>"):
            self.field = self.USERNAME
        elif t.endswith(b"</username>"):
            self.field = self.OUT
        elif t.endswith(b"<comment>"):
            self.field = self.COMMENT
        elif t.endswith(b"</comment>"):
            self.field = self.OUT
        elif t.endswith(b'<text xml:space="preserve">'):
            self.field = self.TEXT
        elif t.endswith(b"</text>"):
            self.field = self.OUT
        elif t.endswith(b"</page>"):
            self.page_phase = (self.page_phase + 1) & 15

    def update(self, b: int) -> None:
        if self.prev == 91 and b == 91:
            self.wiki = 1
        elif self.prev == 93 and b == 93 and self.field == self.TEXT:
            self.wiki = 0
        elif self.prev == 123 and b == 123:
            self.wiki = 2
        elif self.prev == 125 and b == 125 and self.field == self.TEXT:
            self.wiki = 0
        elif self.prev == 60 and b in (82, 114):
            self.wiki = 3
        elif self.tail.endswith(b"</ref") and b == 62:
            self.wiki = 0

        self.line_col = 0 if b == 10 else min(self.line_col + 1, 255)
        self.tail.append(b)
        if len(self.tail) > 48:
            del self.tail[0]
        self._set_field()
        self.prev2 = self.prev
        self.prev = b
        self.prev_class = _byte_class(b)
        self.pos += 1


class Process:
    def __init__(self) -> None:
        self.models: dict[int, Model] = {0: Model()}
        self.clock = Clock()

    def chain(self) -> list[Model]:
        out = []
        for key in self.clock.keys():
            model = self.models.get(key)
            if model is None:
                if len(self.models) >= MAX_MODELS:
                    continue
                model = Model()
                self.models[key] = model
            out.append(model)
        return out

    @staticmethod
    def counts(chain: list[Model]) -> tuple[list[int], int]:
        counts = chain[0].c[:]
        for model, weight, threshold in zip(
            chain[1:],
            (5, 4, 3, 3, 2, 1),
            (256, 512, 512, 512, 768, 384),
        ):
            if model.t >= threshold:
                for i, value in enumerate(model.c):
                    counts[i] += value * weight
        total = sum(counts)
        while total > MAX_DIST:
            counts = [(v + 1) >> 1 for v in counts]
            total = sum(counts)
        return counts, total

    @staticmethod
    def interval(counts: list[int], sym: int) -> tuple[int, int]:
        return sum(counts[:sym]), counts[sym]

    @staticmethod
    def symbol_at(counts: list[int], target: int) -> tuple[int, int, int]:
        cum = 0
        for sym, freq in enumerate(counts):
            if target < cum + freq:
                return sym, cum, freq
            cum += freq
        raise ValueError("arithmetic target out of range")

    def update(self, chain: list[Model], sym: int) -> None:
        seen: set[int] = set()
        for model in chain:
            marker = id(model)
            if marker not in seen:
                model.update(sym)
                seen.add(marker)
        self.clock.update(sym)


def compress(data: bytes) -> bytes:
    proc = Process()
    enc = Encoder()
    for b in data:
        chain = proc.chain()
        counts, total = proc.counts(chain)
        cum, freq = proc.interval(counts, b)
        enc.sym(cum, freq, total)
        proc.update(chain, b)
    body = enc.finish()
    LAST_STATS.clear()
    LAST_STATS.update({"models": len(proc.models)})
    return MAGIC + struct.pack(">Q", len(data)) + body


def decompress(data: bytes) -> bytes:
    if data[:4] != MAGIC:
        raise ValueError("bad graph union range stream")
    n = struct.unpack(">Q", data[4:12])[0]
    proc = Process()
    dec = Decoder(data[12:])
    out = bytearray()
    for _ in range(n):
        chain = proc.chain()
        counts, total = proc.counts(chain)
        sym, cum, freq = proc.symbol_at(counts, dec.target(total))
        dec.sym(cum, freq, total)
        out.append(sym)
        proc.update(chain, sym)
    return bytes(out)


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
