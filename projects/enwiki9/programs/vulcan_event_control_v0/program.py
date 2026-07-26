"""VULCAN V0 adaptive categorical coder for exact WRT event bytes."""

from __future__ import annotations

import struct


MAGIC = b"VULCAN0\0"
HALF = 1 << 31
QUARTER = 1 << 30
THREE_QUARTERS = 3 << 30
MASK32 = (1 << 32) - 1
MAX_TOTAL = 1 << 15
_LAST_STATS: dict[str, int | float] = {}


class BitWriter:
    def __init__(self) -> None:
        self.output = bytearray()
        self.value = 0
        self.used = 0

    def write(self, bit: int) -> None:
        self.value = (self.value << 1) | bit
        self.used += 1
        if self.used == 8:
            self.output.append(self.value)
            self.value = 0
            self.used = 0

    def finish(self) -> bytes:
        if self.used:
            self.output.append(self.value << (8 - self.used))
        return bytes(self.output)


class BitReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.position = 0

    def read(self) -> int:
        byte = self.position >> 3
        if byte >= len(self.data):
            self.position += 1
            return 0
        bit = (self.data[byte] >> (7 - (self.position & 7))) & 1
        self.position += 1
        return bit


class ArithmeticEncoder:
    def __init__(self) -> None:
        self.low = 0
        self.high = MASK32
        self.pending = 0
        self.writer = BitWriter()

    def _emit(self, bit: int) -> None:
        self.writer.write(bit)
        inverse = bit ^ 1
        while self.pending:
            self.writer.write(inverse)
            self.pending -= 1

    def encode(self, low_count: int, high_count: int, total: int) -> None:
        width = self.high - self.low + 1
        self.high = self.low + (width * high_count // total) - 1
        self.low = self.low + (width * low_count // total)
        while True:
            if self.high < HALF:
                self._emit(0)
            elif self.low >= HALF:
                self._emit(1)
                self.low -= HALF
                self.high -= HALF
            elif self.low >= QUARTER and self.high < THREE_QUARTERS:
                self.pending += 1
                self.low -= QUARTER
                self.high -= QUARTER
            else:
                break
            self.low = (self.low << 1) & MASK32
            self.high = ((self.high << 1) | 1) & MASK32

    def finish(self) -> bytes:
        self.pending += 1
        self._emit(0 if self.low < QUARTER else 1)
        return self.writer.finish()


class ArithmeticDecoder:
    def __init__(self, data: bytes) -> None:
        self.reader = BitReader(data)
        self.low = 0
        self.high = MASK32
        self.code = 0
        for _ in range(32):
            self.code = ((self.code << 1) | self.reader.read()) & MASK32

    def target(self, total: int) -> int:
        width = self.high - self.low + 1
        return ((self.code - self.low + 1) * total - 1) // width

    def update(self, low_count: int, high_count: int, total: int) -> None:
        width = self.high - self.low + 1
        self.high = self.low + (width * high_count // total) - 1
        self.low = self.low + (width * low_count // total)
        while True:
            if self.high < HALF:
                pass
            elif self.low >= HALF:
                self.low -= HALF
                self.high -= HALF
                self.code -= HALF
            elif self.low >= QUARTER and self.high < THREE_QUARTERS:
                self.low -= QUARTER
                self.high -= QUARTER
                self.code -= QUARTER
            else:
                break
            self.low = (self.low << 1) & MASK32
            self.high = ((self.high << 1) | 1) & MASK32
            self.code = ((self.code << 1) | self.reader.read()) & MASK32


class AdaptiveModel:
    def __init__(self, symbols: int) -> None:
        self.symbols = symbols
        self.counts = [1] * symbols
        self.tree = [0] * (symbols + 1)
        self.total = symbols
        self._rebuild()

    def _rebuild(self) -> None:
        self.tree = [0] * (self.symbols + 1)
        for symbol, count in enumerate(self.counts):
            self._add(symbol, count)
        self.total = sum(self.counts)

    def _add(self, symbol: int, delta: int) -> None:
        index = symbol + 1
        while index <= self.symbols:
            self.tree[index] += delta
            index += index & -index

    def prefix(self, symbol: int) -> int:
        value = 0
        index = symbol
        while index:
            value += self.tree[index]
            index -= index & -index
        return value

    def interval(self, symbol: int) -> tuple[int, int, int]:
        low = self.prefix(symbol)
        return low, low + self.counts[symbol], self.total

    def symbol(self, target: int) -> int:
        index = 0
        accumulated = 0
        step = 1 << (self.symbols.bit_length() - 1)
        while step:
            candidate = index + step
            if candidate <= self.symbols and accumulated + self.tree[candidate] <= target:
                index = candidate
                accumulated += self.tree[candidate]
            step >>= 1
        if index >= self.symbols:
            raise ValueError("arithmetic target outside model")
        return index

    def update(self, symbol: int) -> None:
        self.counts[symbol] += 1
        self._add(symbol, 1)
        self.total += 1
        if self.total >= MAX_TOTAL:
            self.counts = [max(1, (count + 1) >> 1) for count in self.counts]
            self._rebuild()


class ModelBank:
    def __init__(self) -> None:
        self.kind = [AdaptiveModel(3) for _ in range(4)]
        self.byte: dict[tuple[int, int, int, int], AdaptiveModel] = {}

    def kind_model(self, previous_kind: int) -> AdaptiveModel:
        return self.kind[previous_kind]

    def byte_model(
        self,
        previous_kind: int,
        kind: int,
        position: int,
        previous_bucket: int,
    ) -> AdaptiveModel:
        key = (previous_kind, kind, position, previous_bucket)
        model = self.byte.get(key)
        if model is None:
            model = AdaptiveModel(256)
            self.byte[key] = model
        return model


def wrt_transform(value: int) -> int:
    if ord("{") <= value < 127:
        value += ord("P") - ord("{")
    elif ord("P") <= value < ord("T"):
        value -= ord("P") - ord("{")
    elif ord(":") <= value <= ord("?") or ord("J") <= value <= ord("O"):
        value ^= 0x70
    if value in (ord("X"), ord("`")):
        value ^= ord("X") ^ ord("`")
    return value


def event_length(data: bytes, position: int) -> int:
    first = wrt_transform(data[position])
    length = 2 if first == 0x0C or first > 0xCF else 1
    if length == 2 and first > 0xCF and position + 1 < len(data):
        if wrt_transform(data[position + 1]) > 0xCF:
            length = 3
    if position + length > len(data):
        return 1
    return length


def _encode_symbol(coder: ArithmeticEncoder, model: AdaptiveModel, symbol: int) -> None:
    coder.encode(*model.interval(symbol))
    model.update(symbol)


def _decode_symbol(coder: ArithmeticDecoder, model: AdaptiveModel) -> int:
    target = coder.target(model.total)
    symbol = model.symbol(target)
    coder.update(*model.interval(symbol))
    model.update(symbol)
    return symbol


def compress(data: bytes) -> bytes:
    coder = ArithmeticEncoder()
    models = ModelBank()
    position = 0
    events = 0
    decisions = 0
    previous_kind = 3
    previous_bucket = 0
    while position < len(data):
        length = event_length(data, position)
        kind = length - 1
        _encode_symbol(coder, models.kind_model(previous_kind), kind)
        decisions += 1
        for offset in range(length):
            value = data[position + offset]
            model = models.byte_model(
                previous_kind, kind, offset, previous_bucket
            )
            _encode_symbol(coder, model, value)
            decisions += 1
        previous_kind = kind
        previous_bucket = data[position + length - 1] >> 4
        position += length
        events += 1
    payload = coder.finish()
    global _LAST_STATS
    raw_bit_decisions = len(data) * 8
    _LAST_STATS = {
        "events": events,
        "categorical_decisions": decisions,
        "raw_bit_decisions": raw_bit_decisions,
        "decision_reduction": 0.0
        if raw_bit_decisions == 0
        else 1.0 - decisions / raw_bit_decisions,
        "model_tables": len(models.byte) + len(models.kind),
        "payload_bytes": len(payload),
    }
    return MAGIC + struct.pack("<Q", len(data)) + payload


def decompress(archive: bytes) -> bytes:
    if len(archive) < 16 or archive[:8] != MAGIC:
        raise ValueError("invalid VULCAN V0 archive")
    size = struct.unpack_from("<Q", archive, 8)[0]
    coder = ArithmeticDecoder(archive[16:])
    models = ModelBank()
    output = bytearray()
    previous_kind = 3
    previous_bucket = 0
    while len(output) < size:
        kind_model = models.kind_model(previous_kind)
        kind = _decode_symbol(coder, kind_model)
        length = kind + 1
        if len(output) + length > size:
            raise ValueError("event exceeds declared stream length")
        for offset in range(length):
            model = models.byte_model(
                previous_kind, kind, offset, previous_bucket
            )
            output.append(_decode_symbol(coder, model))
        previous_kind = kind
        previous_bucket = output[-1] >> 4
    return bytes(output)


def stats() -> dict[str, int | float]:
    return dict(_LAST_STATS)
