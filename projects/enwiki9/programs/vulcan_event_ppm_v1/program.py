"""VULCAN V0 adaptive categorical coder for exact WRT event bytes."""

from __future__ import annotations

import struct
from collections import OrderedDict


MAGIC = b"VULCAN0\0"
HALF = 1 << 31
QUARTER = 1 << 30
THREE_QUARTERS = 3 << 30
MASK32 = (1 << 32) - 1
MAX_TOTAL = 1 << 15
MAX_EVENT_CONTEXTS = 50_000
EVENTS_PER_CONTEXT = 32
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


class SparseEventModel:
    def __init__(self) -> None:
        self.symbols: list[int] = []
        self.counts: dict[int, int] = {}
        self.escape = 1
        self.total = 1

    def contains(self, symbol: int) -> bool:
        return symbol in self.counts

    def interval(self, symbol: int | None) -> tuple[int, int, int]:
        cumulative = 0
        if symbol is None:
            for known in self.symbols:
                cumulative += self.counts[known]
            return cumulative, cumulative + self.escape, self.total
        for known in self.symbols:
            count = self.counts[known]
            if known == symbol:
                return cumulative, cumulative + count, self.total
            cumulative += count
        raise KeyError(symbol)

    def symbol(self, target: int) -> int | None:
        cumulative = 0
        for symbol in self.symbols:
            cumulative += self.counts[symbol]
            if target < cumulative:
                return symbol
        if target < self.total:
            return None
        raise ValueError("event target outside model")

    def observe_escape(self) -> None:
        self.escape += 1
        self.total += 1
        self._rescale()

    def observe(self, symbol: int) -> None:
        if symbol not in self.counts:
            if len(self.symbols) >= EVENTS_PER_CONTEXT:
                return
            self.symbols.append(symbol)
            self.counts[symbol] = 0
        self.counts[symbol] += 1
        self.total += 1
        self._rescale()

    def _rescale(self) -> None:
        if self.total < MAX_TOTAL:
            return
        self.escape = max(1, (self.escape + 1) >> 1)
        self.total = self.escape
        for symbol in self.symbols:
            self.counts[symbol] = max(1, (self.counts[symbol] + 1) >> 1)
            self.total += self.counts[symbol]


class EventPPM:
    def __init__(self) -> None:
        self.models: OrderedDict[tuple[int, ...], SparseEventModel] = OrderedDict()

    def contexts(self, history: list[int]) -> tuple[tuple[int, ...], ...]:
        rows = []
        if len(history) >= 2:
            rows.append((history[-2], history[-1]))
        if history:
            rows.append((history[-1],))
        rows.append(())
        return tuple(rows)

    def get(self, context: tuple[int, ...]) -> SparseEventModel | None:
        model = self.models.get(context)
        if model is not None:
            self.models.move_to_end(context)
        return model

    def update(self, contexts: tuple[tuple[int, ...], ...], symbol: int) -> None:
        for context in contexts:
            model = self.models.get(context)
            if model is None:
                if len(self.models) >= MAX_EVENT_CONTEXTS:
                    self.models.popitem(last=False)
                model = SparseEventModel()
                self.models[context] = model
            else:
                self.models.move_to_end(context)
            model.observe(symbol)

    def entries(self) -> int:
        return sum(len(model.symbols) for model in self.models.values())


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
    ppm = EventPPM()
    event_ids: dict[bytes, int] = {}
    history: list[int] = []
    position = 0
    events = 0
    decisions = 0
    previous_kind = 3
    previous_bucket = 0
    while position < len(data):
        length = event_length(data, position)
        kind = length - 1
        event = data[position : position + length]
        event_id = event_ids.get(event)
        contexts = ppm.contexts(history)
        matched = False
        if event_id is not None:
            for context in contexts:
                model = ppm.get(context)
                if model is None:
                    continue
                if model.contains(event_id):
                    coder.encode(*model.interval(event_id))
                    decisions += 1
                    matched = True
                    break
                coder.encode(*model.interval(None))
                model.observe_escape()
                decisions += 1
        else:
            for context in contexts:
                model = ppm.get(context)
                if model is None:
                    continue
                coder.encode(*model.interval(None))
                model.observe_escape()
                decisions += 1
        if not matched:
            _encode_symbol(coder, models.kind_model(previous_kind), kind)
            decisions += 1
            for offset in range(length):
                value = event[offset]
                model = models.byte_model(
                    previous_kind, kind, offset, previous_bucket
                )
                _encode_symbol(coder, model, value)
                decisions += 1
            if event_id is None:
                event_id = len(event_ids)
                event_ids[event] = event_id
        assert event_id is not None
        ppm.update(contexts, event_id)
        history.append(event_id)
        if len(history) > 2:
            del history[0]
        previous_kind = kind
        previous_bucket = event[-1] >> 4
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
        "event_contexts": len(ppm.models),
        "event_context_entries": ppm.entries(),
        "event_vocabulary": len(event_ids),
        "payload_bytes": len(payload),
    }
    return MAGIC + struct.pack("<Q", len(data)) + payload


def decompress(archive: bytes) -> bytes:
    if len(archive) < 16 or archive[:8] != MAGIC:
        raise ValueError("invalid VULCAN V0 archive")
    size = struct.unpack_from("<Q", archive, 8)[0]
    coder = ArithmeticDecoder(archive[16:])
    models = ModelBank()
    ppm = EventPPM()
    events: list[bytes] = []
    event_to_id: dict[bytes, int] = {}
    history: list[int] = []
    output = bytearray()
    previous_kind = 3
    previous_bucket = 0
    while len(output) < size:
        contexts = ppm.contexts(history)
        event_id = None
        for context in contexts:
            model = ppm.get(context)
            if model is None:
                continue
            target = coder.target(model.total)
            candidate = model.symbol(target)
            coder.update(*model.interval(candidate))
            if candidate is None:
                model.observe_escape()
                continue
            event_id = candidate
            break
        if event_id is None:
            kind_model = models.kind_model(previous_kind)
            kind = _decode_symbol(coder, kind_model)
            length = kind + 1
            if len(output) + length > size:
                raise ValueError("event exceeds declared stream length")
            event_bytes = bytearray()
            for offset in range(length):
                model = models.byte_model(
                    previous_kind, kind, offset, previous_bucket
                )
                event_bytes.append(_decode_symbol(coder, model))
            event = bytes(event_bytes)
            event_id = event_to_id.get(event)
            if event_id is None:
                event_id = len(events)
                events.append(event)
                event_to_id[event] = event_id
        else:
            if event_id >= len(events):
                raise ValueError("event id outside vocabulary")
            event = events[event_id]
            kind = len(event) - 1
            if len(output) + len(event) > size:
                raise ValueError("event exceeds declared stream length")
        ppm.update(contexts, event_id)
        history.append(event_id)
        if len(history) > 2:
            del history[0]
        output.extend(event)
        previous_kind = kind
        previous_bucket = output[-1] >> 4
    return bytes(output)


def stats() -> dict[str, int | float]:
    return dict(_LAST_STATS)
