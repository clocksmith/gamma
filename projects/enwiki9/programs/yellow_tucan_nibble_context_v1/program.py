from __future__ import annotations

import struct

STATE_BITS = 32
FULL = 1 << STATE_BITS
HALF = FULL >> 1
QUARTER = HALF >> 1
THREE_QUARTER = QUARTER * 3
MAX_TOTAL = 2048
MAX_CTX = 8192
MIN_TRAINED = 24

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
        self.c = [1] * 16
        self.t = 16

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
        self.prev = 0
        self.prev_class = 0
        self.run_class = 0
        self.run_len = 0

    @staticmethod
    def byte_class(b: int) -> int:
        if 65 <= b <= 90 or 97 <= b <= 122:
            return 1
        if 48 <= b <= 57:
            return 2
        if b in (9, 10, 13, 32):
            return 3
        if b in (34, 38, 39, 47, 60, 61, 62, 91, 93, 123, 124, 125):
            return 4
        if b < 32 or b >= 128:
            return 5
        return 6

    def key(self, phase: int, hi: int = 0) -> int:
        return (
            (phase << 22)
            ^ (self.mode << 18)
            ^ (self.bracket << 16)
            ^ (self.brace << 14)
            ^ (self.prev_class << 10)
            ^ (self.run_class << 6)
            ^ (self.run_len << 4)
            ^ hi
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
        elif b == 123:
            self.mode = 3
        elif self.mode == 3 and b == 125:
            self.mode = 0
        elif b == 91:
            self.mode = 4
        elif self.mode == 4 and b == 93:
            self.mode = 0

        if b == 91:
            self.bracket = min(3, self.bracket + 1)
        elif b == 93:
            self.bracket = max(0, self.bracket - 1)
        if b == 123:
            self.brace = min(3, self.brace + 1)
        elif b == 125:
            self.brace = max(0, self.brace - 1)

        cls = self.byte_class(b)
        self.run_len = min(3, self.run_len + 1) if cls == self.run_class else 1
        self.run_class = cls
        self.prev_class = cls
        self.prev = b


class Predictor:
    def __init__(self) -> None:
        self.global_hi = Model()
        self.global_lo = Model()
        self.prev_hi: dict[int, Model] = {}
        self.prev_lo: dict[int, Model] = {}
        self.struct_hi: dict[int, Model] = {}
        self.struct_lo: dict[int, Model] = {}
        self.st = State()

    def _ctx(self, phase: int, hi: int, create: bool) -> tuple[Model, Model | None, Model | None]:
        base = self.global_hi if phase == 0 else self.global_lo
        prev_key = (phase << 12) ^ (self.st.prev << 4) ^ hi
        struct_key = self.st.key(phase, hi)
        prev_map = self.prev_hi if phase == 0 else self.prev_lo
        struct_map = self.struct_hi if phase == 0 else self.struct_lo

        prev = prev_map.get(prev_key)
        if prev is None and create and len(prev_map) < MAX_CTX:
            prev = Model()
            prev_map[prev_key] = prev

        struct = struct_map.get(struct_key)
        if struct is None and create and len(struct_map) < MAX_CTX:
            struct = Model()
            struct_map[struct_key] = struct

        return base, prev, struct

    def counts(self, phase: int, hi: int = 0) -> list[int]:
        base, prev, struct = self._ctx(phase, hi, False)
        counts = [1 + x for x in base.c]
        if prev is not None and prev.t >= MIN_TRAINED:
            for i, x in enumerate(prev.c):
                counts[i] += 5 * x
        if struct is not None and struct.t >= MIN_TRAINED:
            for i, x in enumerate(struct.c):
                counts[i] += 4 * x
        return counts

    def update_symbol(self, phase: int, sym: int, hi: int = 0) -> None:
        base, prev, struct = self._ctx(phase, hi, True)
        base.upd(sym)
        if prev is not None:
            prev.upd(sym)
        if struct is not None:
            struct.upd(sym)

    def update_byte(self, b: int) -> None:
        self.st.update(b)

    def stat_dict(self) -> dict[str, int]:
        return {
            "prev_hi": len(self.prev_hi),
            "prev_lo": len(self.prev_lo),
            "struct_hi": len(self.struct_hi),
            "struct_lo": len(self.struct_lo),
        }


def _cf(counts: list[int], sym: int) -> tuple[int, int, int]:
    cum = 0
    for i, freq in enumerate(counts):
        if i == sym:
            return cum, freq, sum(counts)
        cum += freq
    raise ValueError("bad symbol")


def _find(counts: list[int], target: int) -> tuple[int, int, int, int]:
    cum = 0
    total = sum(counts)
    for sym, freq in enumerate(counts):
        if target < cum + freq:
            return sym, cum, freq, total
        cum += freq
    raise ValueError("bad arithmetic target")


def compress(data: bytes) -> bytes:
    p = Predictor()
    e = Enc()
    for b in data:
        hi = b >> 4
        lo = b & 15
        c, f, t = _cf(p.counts(0), hi)
        e.sym(c, f, t)
        p.update_symbol(0, hi)
        c, f, t = _cf(p.counts(1, hi), lo)
        e.sym(c, f, t)
        p.update_symbol(1, lo, hi)
        p.update_byte(b)
    LAST_STATS.clear()
    LAST_STATS.update(p.stat_dict())
    return struct.pack(">I", len(data)) + e.finish()


def decompress(data: bytes) -> bytes:
    n = struct.unpack(">I", data[:4])[0]
    p = Predictor()
    d = Dec(data[4:])
    out = bytearray()
    for _ in range(n):
        counts = p.counts(0)
        hi, c, f, t = _find(counts, d.target(sum(counts)))
        d.sym(c, f, t)
        p.update_symbol(0, hi)
        counts = p.counts(1, hi)
        lo, c, f, t = _find(counts, d.target(sum(counts)))
        d.sym(c, f, t)
        p.update_symbol(1, lo, hi)
        b = (hi << 4) | lo
        out.append(b)
        p.update_byte(b)
    return bytes(out)


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
