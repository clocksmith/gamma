"""typed_flip_rehydration_v1.

Prototype of the typed stochastic rehydration idea:

  bytes -> typed wiki clock state -> adaptive probability model -> residual bits

The decoder does not store a transformed byte stream. It replays the same
typed XML/wiki state machine and adaptive probability process, then arithmetic
decodes the exact byte at each clock tick. The stochastic part is represented
by online frequency estimates P(byte | typed_context); the compressed stream is
the correction signal that selects the true branch at every step.
"""

from __future__ import annotations

import struct

STATE_BITS = 32
FULL = 1 << STATE_BITS
HALF = FULL >> 1
QUARTER = HALF >> 1
THREE_QUARTER = QUARTER * 3
MAX_TOTAL = 2048
MAX_MODELS = 32768
MIN_TRAINED = 24
MAGIC = b"TFR1"


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


class Enc:
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


class NibbleModel:
    def __init__(self) -> None:
        self.c = [1] * 16
        self.total = 16

    def encode(self, enc: Enc, sym: int) -> None:
        cum = 0
        for i in range(sym):
            cum += self.c[i]
        enc.sym(cum, self.c[sym], self.total)

    def decode(self, dec: Dec) -> int:
        target = dec.target(self.total)
        cum = 0
        for sym, freq in enumerate(self.c):
            if target < cum + freq:
                dec.sym(cum, freq, self.total)
                return sym
            cum += freq
        raise ValueError("arithmetic target out of range")

    def update(self, sym: int) -> None:
        self.c[sym] += 1
        self.total += 1
        if self.total >= MAX_TOTAL:
            self.c = [(x + 1) >> 1 for x in self.c]
            self.total = sum(self.c)


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


class WikiClock:
    OUT = 0
    TEXT = 1
    TITLE = 2
    ID = 3
    TIMESTAMP = 4
    USERNAME = 5
    COMMENT = 6

    def __init__(self) -> None:
        self.field = self.OUT
        self.wiki = 0
        self.prev = 0
        self.prev2 = 0
        self.prev_class = 0
        self.run_class = 0
        self.run_len = 0
        self.line_col = 0
        self.page_phase = 0
        self.pos = 0
        self.tail = bytearray()

    def coarse_key(self, phase: int, hi: int = 0) -> int:
        return (
            0x100000
            ^ (phase << 18)
            ^ (self.field << 12)
            ^ (self.wiki << 8)
            ^ (self.prev_class << 4)
            ^ hi
        )

    def medium_key(self, phase: int, hi: int = 0) -> int:
        return (
            0x200000
            ^ (phase << 20)
            ^ (self.field << 16)
            ^ (self.wiki << 12)
            ^ (self.prev_class << 8)
            ^ (self.run_class << 4)
            ^ hi
        )

    def exact_key(self, phase: int, hi: int = 0) -> int:
        clock = (self.pos >> 10) & 7
        return (
            0x300000
            ^ (phase << 24)
            ^ (self.field << 21)
            ^ (self.wiki << 17)
            ^ (self.page_phase << 13)
            ^ (clock << 10)
            ^ (self.prev << 2)
            ^ (hi << 1)
            ^ (_byte_class(self.prev2) & 1)
        )

    def column_key(self, phase: int, hi: int = 0) -> int:
        return (
            0x400000
            ^ (phase << 16)
            ^ (self.field << 12)
            ^ (min(self.line_col >> 3, 15) << 8)
            ^ (self.prev_class << 4)
            ^ min(self.line_col >> 3, 15)
            ^ hi
        )

    def _set_field_from_tail(self) -> None:
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
        cls = _byte_class(b)
        if cls == self.run_class:
            self.run_len = min(self.run_len + 1, 15)
        else:
            self.run_class = cls
            self.run_len = 1

        if self.prev == 91 and b == 91:
            self.wiki = 1
        elif self.prev == 93 and b == 93:
            self.wiki = 0 if self.field == self.TEXT else self.wiki
        elif self.prev == 123 and b == 123:
            self.wiki = 2
        elif self.prev == 125 and b == 125:
            self.wiki = 0 if self.field == self.TEXT else self.wiki
        elif self.prev == 60 and b in (114, 82):  # <r...
            self.wiki = 3
        elif self.tail.endswith(b"</ref") and b == 62:
            self.wiki = 0

        if b == 10:
            self.line_col = 0
        else:
            self.line_col = min(self.line_col + 1, 255)

        self.tail.append(b)
        if len(self.tail) > 48:
            del self.tail[0]
        self._set_field_from_tail()

        self.prev2 = self.prev
        self.prev = b
        self.prev_class = cls
        self.pos += 1


class Process:
    def __init__(self) -> None:
        self.models: dict[int, NibbleModel] = {0: NibbleModel(), 1: NibbleModel()}
        self.clock = WikiClock()

    def model(self, key: int, fallback: NibbleModel) -> NibbleModel:
        found = self.models.get(key)
        if found is not None:
            return found
        if len(self.models) >= MAX_MODELS:
            return fallback
        found = NibbleModel()
        self.models[key] = found
        return found

    def chain(self, phase: int, hi: int = 0) -> tuple[NibbleModel, NibbleModel, NibbleModel, NibbleModel, NibbleModel]:
        base = self.models[phase]
        return (
            base,
            self.model(self.clock.coarse_key(phase, hi), base),
            self.model(self.clock.column_key(phase, hi), base),
            self.model(self.clock.medium_key(phase, hi), base),
            self.model(self.clock.exact_key(phase, hi), base),
        )

    @staticmethod
    def counts(chain: tuple[NibbleModel, NibbleModel, NibbleModel, NibbleModel, NibbleModel]) -> list[int]:
        counts = chain[0].c[:]
        for model, weight, threshold in (
            (chain[1], 3, MIN_TRAINED),
            (chain[2], 2, MIN_TRAINED),
            (chain[3], 3, MIN_TRAINED * 2),
            (chain[4], 1, MIN_TRAINED * 4),
        ):
            if model.total >= 16 + threshold:
                for i, value in enumerate(model.c):
                    counts[i] += value * weight
        return counts

    @staticmethod
    def interval(counts: list[int], sym: int) -> tuple[int, int, int]:
        cum = 0
        total = sum(counts)
        for i, freq in enumerate(counts):
            if i == sym:
                return cum, freq, total
            cum += freq
        raise ValueError("nibble out of range")

    @staticmethod
    def symbol_at(counts: list[int], target: int) -> tuple[int, int, int, int]:
        cum = 0
        total = sum(counts)
        for sym, freq in enumerate(counts):
            if target < cum + freq:
                return sym, cum, freq, total
            cum += freq
        raise ValueError("arithmetic target out of range")

    def update_models(self, chain: tuple[NibbleModel, NibbleModel, NibbleModel, NibbleModel, NibbleModel], sym: int) -> None:
        seen: set[int] = set()
        for model in chain:
            marker = id(model)
            if marker not in seen:
                model.update(sym)
                seen.add(marker)


def compress(data: bytes) -> bytes:
    proc = Process()
    enc = Enc()
    for b in data:
        hi = b >> 4
        lo = b & 15
        chain = proc.chain(0)
        counts = proc.counts(chain)
        cum, freq, total = proc.interval(counts, hi)
        enc.sym(cum, freq, total)
        proc.update_models(chain, hi)
        chain = proc.chain(1, hi)
        counts = proc.counts(chain)
        cum, freq, total = proc.interval(counts, lo)
        enc.sym(cum, freq, total)
        proc.update_models(chain, lo)
        proc.clock.update(b)
    body = enc.finish()
    return MAGIC + struct.pack(">Q", len(data)) + body


def decompress(data: bytes) -> bytes:
    if data[:4] != MAGIC:
        raise ValueError("bad typed rehydration stream")
    (n,) = struct.unpack(">Q", data[4:12])
    dec = Dec(data[12:])
    proc = Process()
    out = bytearray()
    for _ in range(n):
        chain = proc.chain(0)
        counts = proc.counts(chain)
        hi, cum, freq, total = proc.symbol_at(counts, dec.target(sum(counts)))
        dec.sym(cum, freq, total)
        proc.update_models(chain, hi)
        chain = proc.chain(1, hi)
        counts = proc.counts(chain)
        lo, cum, freq, total = proc.symbol_at(counts, dec.target(sum(counts)))
        dec.sym(cum, freq, total)
        proc.update_models(chain, lo)
        b = (hi << 4) | lo
        out.append(b)
        proc.clock.update(b)
    return bytes(out)
