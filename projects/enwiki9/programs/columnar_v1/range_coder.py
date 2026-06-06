"""range_coder — pure-Python 32-bit Witten-Neal-Cleary range coder.

32-bit precision, byte-aligned bit I/O. Encoder/decoder lockstep: both
sides must call encode/update with identical (cum_low, cum_high, total)
tuples for each symbol — this is the contract that the model layer
above maintains by running identical online updates.

Renormalization: standard E1 (output 0 when high < HALF), E2 (output 1
when low >= HALF), E3 (track pending bits when range straddles HALF
without crossing it). On finish, output `pending+1` bits to disambiguate
the final code.

Output: bytes. Decoder reads bytes back, primes 32 bits of code, then
issues query/update pairs symmetric to encoder.

Cross-host determinism: integer arithmetic only. No floating point. All
integer ops are arbitrary-precision Python ints, so identical bytes-out
on every host with the same Python implementation.
"""

from __future__ import annotations

TOP = 1 << 32
HALF = 1 << 31
QUARTER = 1 << 30
THREE_QUARTER = 3 << 30
MASK = TOP - 1


class _BitWriter:
    __slots__ = ("buf", "cur", "cnt")

    def __init__(self) -> None:
        self.buf = bytearray()
        self.cur = 0
        self.cnt = 0

    def write_bit(self, b: int) -> None:
        self.cur = (self.cur << 1) | (b & 1)
        self.cnt += 1
        if self.cnt == 8:
            self.buf.append(self.cur)
            self.cur = 0
            self.cnt = 0

    def finish(self) -> bytes:
        if self.cnt > 0:
            self.cur <<= 8 - self.cnt
            self.buf.append(self.cur)
            self.cur = 0
            self.cnt = 0
        return bytes(self.buf)


class _BitReader:
    __slots__ = ("data", "pos", "cur", "cnt")

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0
        self.cur = 0
        self.cnt = 0

    def read_bit(self) -> int:
        if self.cnt == 0:
            if self.pos < len(self.data):
                self.cur = self.data[self.pos]
                self.pos += 1
            else:
                self.cur = 0
            self.cnt = 8
        b = (self.cur >> 7) & 1
        self.cur = (self.cur << 1) & 0xFF
        self.cnt -= 1
        return b


class RangeEncoder:
    __slots__ = ("low", "high", "pending", "bw")

    def __init__(self) -> None:
        self.low = 0
        self.high = MASK
        self.pending = 0
        self.bw = _BitWriter()

    def _emit_pending(self, b: int) -> None:
        self.bw.write_bit(b)
        nb = 1 - b
        for _ in range(self.pending):
            self.bw.write_bit(nb)
        self.pending = 0

    def encode(self, cum_low: int, cum_high: int, total: int) -> None:
        rng = self.high - self.low + 1
        self.high = self.low + (rng * cum_high) // total - 1
        self.low = self.low + (rng * cum_low) // total

        while True:
            if self.high < HALF:
                self._emit_pending(0)
            elif self.low >= HALF:
                self._emit_pending(1)
                self.low -= HALF
                self.high -= HALF
            elif self.low >= QUARTER and self.high < THREE_QUARTER:
                self.pending += 1
                self.low -= QUARTER
                self.high -= QUARTER
            else:
                break
            self.low = (self.low << 1) & MASK
            self.high = ((self.high << 1) | 1) & MASK

    def finish(self) -> bytes:
        self.pending += 1
        if self.low < QUARTER:
            self._emit_pending(0)
        else:
            self._emit_pending(1)
        return self.bw.finish()


class RangeDecoder:
    __slots__ = ("low", "high", "code", "br")

    def __init__(self, data: bytes) -> None:
        self.low = 0
        self.high = MASK
        self.code = 0
        self.br = _BitReader(data)
        for _ in range(32):
            self.code = (self.code << 1) | self.br.read_bit()

    def query(self, total: int) -> int:
        rng = self.high - self.low + 1
        return ((self.code - self.low + 1) * total - 1) // rng

    def update(self, cum_low: int, cum_high: int, total: int) -> None:
        rng = self.high - self.low + 1
        self.high = self.low + (rng * cum_high) // total - 1
        self.low = self.low + (rng * cum_low) // total

        while True:
            if self.high < HALF:
                pass
            elif self.low >= HALF:
                self.code -= HALF
                self.low -= HALF
                self.high -= HALF
            elif self.low >= QUARTER and self.high < THREE_QUARTER:
                self.code -= QUARTER
                self.low -= QUARTER
                self.high -= QUARTER
            else:
                break
            self.low = (self.low << 1) & MASK
            self.high = ((self.high << 1) | 1) & MASK
            self.code = ((self.code << 1) | self.br.read_bit()) & MASK
