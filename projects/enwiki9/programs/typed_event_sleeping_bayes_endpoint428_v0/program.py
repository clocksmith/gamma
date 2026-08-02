"""TESBE-Raw: exact typed-event sleeping prefix-trie selector.

All profiles code the same raw byte sequence with the same adaptive order-1
literal model. Event profiles add point-mass continuations learned only after
their complete 32-byte spans have been decoded. The literal branch is exactly
the baseline distribution, so the event expert sleeps when no completed-history
candidate is eligible.
"""

from dataclasses import dataclass, field
import struct


MAGIC = b"TESBER1\0"
STATE_BITS = 32
FULL = 1 << STATE_BITS
HALF = FULL >> 1
QUARTER = HALF >> 1
THREE_QUARTERS = QUARTER * 3
MAX_TOTAL = 1 << 14
CONTINUATION_BYTES = 32
MAX_KEYS = 8192
MAX_CANDIDATES = 8
MIN_CANDIDATES = 2
LITERAL_PRIOR = 12
WEIGHT_TOTAL = 1 << 24
MIN_LITERAL_WEIGHT = WEIGHT_TOTAL >> 8
PROFILES = ("B0", "C0", "E0", "E1")
TRIGGERS = (
    b"<timestamp>",
    b"<title>",
    b"[[",
    b"{{",
    b"\n",
    b"|",
    b"=",
)

_LAST_STATS: dict[str, object] = {}


class BitsOut:
    def __init__(self) -> None:
        self.data = bytearray()
        self.value = 0
        self.used = 0

    def bit(self, value: int) -> None:
        self.value = (self.value << 1) | (value & 1)
        self.used += 1
        if self.used == 8:
            self.data.append(self.value)
            self.value = 0
            self.used = 0

    def finish(self) -> bytes:
        if self.used:
            self.data.append(self.value << (8 - self.used))
        return bytes(self.data)


class BitsIn:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.position = 0

    def bit(self) -> int:
        byte = self.position >> 3
        if byte >= len(self.data):
            self.position += 1
            return 0
        value = (self.data[byte] >> (7 - (self.position & 7))) & 1
        self.position += 1
        return value


class ArithmeticEncoder:
    def __init__(self) -> None:
        self.low = 0
        self.high = FULL - 1
        self.pending = 0
        self.bits = BitsOut()

    def _emit(self, bit: int) -> None:
        self.bits.bit(bit)
        inverse = bit ^ 1
        while self.pending:
            self.bits.bit(inverse)
            self.pending -= 1

    def encode(self, low_count: int, high_count: int, total: int) -> None:
        if not 0 <= low_count < high_count <= total:
            raise ValueError("invalid arithmetic interval")
        width = self.high - self.low + 1
        next_high = self.low + width * high_count // total - 1
        next_low = self.low + width * low_count // total
        if next_low > next_high:
            raise ArithmeticError("arithmetic interval collapsed")
        self.low, self.high = next_low, next_high
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
            self.low <<= 1
            self.high = (self.high << 1) | 1

    def finish(self) -> bytes:
        self.pending += 1
        self._emit(0 if self.low < QUARTER else 1)
        return self.bits.finish()


class ArithmeticDecoder:
    def __init__(self, data: bytes) -> None:
        self.low = 0
        self.high = FULL - 1
        self.bits = BitsIn(data)
        self.code = 0
        for _ in range(STATE_BITS):
            self.code = (self.code << 1) | self.bits.bit()

    def target(self, total: int) -> int:
        width = self.high - self.low + 1
        return ((self.code - self.low + 1) * total - 1) // width

    def update(self, low_count: int, high_count: int, total: int) -> None:
        width = self.high - self.low + 1
        self.high = self.low + width * high_count // total - 1
        self.low = self.low + width * low_count // total
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
            self.low <<= 1
            self.high = (self.high << 1) | 1
            self.code = (self.code << 1) | self.bits.bit()


class AdaptiveByteModel:
    def __init__(self) -> None:
        self.counts = [1] * 256
        self.tree = [0] * 257
        self.total = 256
        self._rebuild()

    def _add(self, symbol: int, delta: int) -> None:
        index = symbol + 1
        while index <= 256:
            self.tree[index] += delta
            index += index & -index

    def _rebuild(self) -> None:
        self.tree = [0] * 257
        for symbol, count in enumerate(self.counts):
            self._add(symbol, count)
        self.total = sum(self.counts)

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
        step = 256
        while step:
            candidate = index + step
            if candidate <= 256 and accumulated + self.tree[candidate] <= target:
                index = candidate
                accumulated += self.tree[candidate]
            step >>= 1
        if index >= 256:
            raise ValueError("arithmetic target outside byte model")
        return index

    def update(self, symbol: int) -> None:
        self.counts[symbol] += 1
        self._add(symbol, 1)
        self.total += 1
        if self.total >= MAX_TOTAL:
            self.counts = [max(1, (count + 1) >> 1) for count in self.counts]
            self._rebuild()


class LiteralBank:
    def __init__(self) -> None:
        self.models = [AdaptiveByteModel() for _ in range(257)]
        self.previous = 256

    @property
    def model(self) -> AdaptiveByteModel:
        return self.models[self.previous]

    def update(self, symbol: int) -> None:
        self.model.update(symbol)
        self.previous = symbol


def _hash_word(data: bytes) -> int:
    value = 2166136261
    for byte in data:
        if 65 <= byte <= 90:
            byte += 32
        value ^= byte
        value = (value * 16777619) & 0xFFFFFFFF
    return value


def _char_class(byte: int) -> int:
    if 65 <= byte <= 90 or 97 <= byte <= 122:
        return 1
    if 48 <= byte <= 57:
        return 2
    if byte in (9, 10, 13, 32):
        return 3
    if byte in (60, 62, 47, 34, 38, 59, 61):
        return 4
    if byte in (91, 93, 123, 124, 125):
        return 5
    if byte >= 128:
        return 6
    return 0


@dataclass
class WikiState:
    field_id: int = 0
    mode: int = 0
    slot: int = 0
    column: int = 0
    link_depth: int = 0
    template_depth: int = 0
    ref_depth: int = 0
    tail: bytearray = field(default_factory=bytearray)

    def update(self, byte: int) -> None:
        self.tail.append(byte)
        if len(self.tail) > 192:
            del self.tail[:64]
        lower = bytes(self.tail).lower()
        self.column = 0 if byte == 10 else min(255, self.column + 1)
        if lower.endswith(b"<title>"):
            self.field_id = 1
        elif lower.endswith(b"</title>"):
            self.field_id = 0
        elif lower.endswith(b"<timestamp>"):
            self.field_id = 2
        elif lower.endswith(b"</timestamp>"):
            self.field_id = 0
        elif lower.endswith(b'<text xml:space="preserve">'):
            self.field_id = 3
            self.slot = 0
            self.mode = 0
        elif lower.endswith(b"</text>"):
            self.field_id = 0
            self.slot = 0
            self.mode = 0
            self.link_depth = 0
            self.template_depth = 0
            self.ref_depth = 0
        if lower.endswith(b"[["):
            self.link_depth = min(7, self.link_depth + 1)
            self.mode = 1
        elif lower.endswith(b"]]"):
            self.link_depth = max(0, self.link_depth - 1)
            if self.link_depth == 0 and self.mode == 1:
                self.mode = 0
                self.slot = 0
        elif lower.endswith(b"{{"):
            self.template_depth = min(7, self.template_depth + 1)
            self.mode = 2
        elif lower.endswith(b"}}"):
            self.template_depth = max(0, self.template_depth - 1)
            if self.template_depth == 0 and self.mode == 2:
                self.mode = 0
                self.slot = 0
        if lower.endswith(b"[[category:"):
            self.slot = 1
        elif lower.endswith(b"[[image:") or lower.endswith(b"[[file:"):
            self.slot = 2
        elif lower.endswith(b"{{cite"):
            self.slot = 3
        elif lower.endswith(b"{{infobox"):
            self.slot = 4
        elif lower.endswith(b"<ref"):
            self.slot = 5
            self.ref_depth = min(3, self.ref_depth + 1)
        elif self.mode == 2 and lower.endswith(b"url="):
            self.slot = 6
        elif self.mode == 2 and lower.endswith(b"title="):
            self.slot = 7
        elif lower.endswith(b"</ref>"):
            self.ref_depth = max(0, self.ref_depth - 1)
            if self.ref_depth == 0 and self.slot == 5:
                self.slot = 0


def _previous_word(history: bytes) -> bytes:
    position = len(history) - 1
    while position >= 0 and not (
        48 <= history[position] <= 57
        or 65 <= history[position] <= 90
        or 97 <= history[position] <= 122
    ):
        position -= 1
    end = position + 1
    while position >= 0 and (
        48 <= history[position] <= 57
        or 65 <= history[position] <= 90
        or 97 <= history[position] <= 122
    ):
        position -= 1
    return history[position + 1 : end][-24:]


def _normalized_suffix(data: bytes) -> bytes:
    return bytes(byte + 32 if 65 <= byte <= 90 else byte for byte in data[-4:])


class ReceiptMemory:
    def __init__(self) -> None:
        self.rows: dict[tuple[object, ...], list[bytes]] = {}
        self.order: list[tuple[object, ...]] = []
        self.cursor = 0

    def get(self, key: tuple[object, ...]) -> tuple[bytes, ...]:
        return tuple(self.rows.get(key, ()))

    def add(self, key: tuple[object, ...], continuation: bytes) -> None:
        row = self.rows.get(key)
        if row is None:
            if len(self.rows) >= MAX_KEYS:
                while self.cursor < len(self.order):
                    old = self.order[self.cursor]
                    self.cursor += 1
                    if old in self.rows:
                        del self.rows[old]
                        break
                if self.cursor > 4096 and self.cursor * 2 > len(self.order):
                    self.order = self.order[self.cursor :]
                    self.cursor = 0
            row = []
            self.rows[key] = row
            self.order.append(key)
        row.append(continuation)
        if len(row) > MAX_CANDIDATES:
            del row[0]


@dataclass
class Opportunity:
    key: tuple[object, ...]
    candidates: list[tuple[bytes, int]]
    literal_weight: int
    buffer: bytearray = field(default_factory=bytearray)

    @property
    def offset(self) -> int:
        return len(self.buffer)


class Distribution:
    def __init__(self, model: AdaptiveByteModel, opportunity: Opportunity | None) -> None:
        self.model = model
        self.opportunity = opportunity
        self.base_total = model.total
        self.candidate_mass = [0] * 256
        if opportunity is not None:
            offset = opportunity.offset
            for continuation, weight in opportunity.candidates:
                self.candidate_mass[continuation[offset]] += weight
        self.candidate_total = sum(self.candidate_mass)
        self.literal_weight = (
            opportunity.literal_weight
            if opportunity is not None and self.candidate_total
            else WEIGHT_TOTAL
        )
        self.total = self.base_total * (self.literal_weight + self.candidate_total)

    def prefix(self, symbol: int) -> int:
        return (
            self.literal_weight * self.model.prefix(symbol)
            + self.base_total * sum(self.candidate_mass[:symbol])
        )

    def interval(self, symbol: int) -> tuple[int, int, int]:
        low = self.prefix(symbol)
        count = (
            self.literal_weight * self.model.counts[symbol]
            + self.base_total * self.candidate_mass[symbol]
        )
        return low, low + count, self.total

    def symbol(self, target: int) -> int:
        low = 0
        high = 256
        while low + 1 < high:
            middle = (low + high) // 2
            if self.prefix(middle) <= target:
                low = middle
            else:
                high = middle
        start, end, _total = self.interval(low)
        if not start <= target < end:
            raise ValueError("mixed arithmetic target outside distribution")
        return low


class Predictor:
    def __init__(self, profile: str, size: int) -> None:
        self.profile = profile
        self.size = size
        self.processed = 0
        self.literal = LiteralBank()
        self.wiki = WikiState()
        self.memory = ReceiptMemory()
        self.active: Opportunity | None = None
        self.opportunities = 0
        self.wakes = 0
        self.candidate_symbols = 0
        self.surviving_symbols = 0

    def distribution(self) -> Distribution:
        return Distribution(self.literal.model, self.active)

    def _key(self, trigger_id: int, marker: bytes) -> tuple[object, ...]:
        history = bytes(self.wiki.tail)
        before = history[: -len(marker)]
        if self.profile == "C0":
            return (trigger_id,)
        if self.profile == "E0":
            return (trigger_id, _normalized_suffix(before))
        word = _previous_word(before)
        return (
            trigger_id,
            self.wiki.field_id,
            self.wiki.mode,
            self.wiki.slot,
            min(7, self.wiki.column >> 4),
            _hash_word(word) & 63,
            tuple(_char_class(byte) for byte in before[-3:]),
        )

    def _trigger(self) -> tuple[int, bytes] | None:
        tail = bytes(self.wiki.tail)
        for trigger_id, marker in enumerate(TRIGGERS):
            if tail.endswith(marker):
                return trigger_id, marker
        return None

    def _launch(self) -> None:
        if self.profile == "B0" or self.processed + CONTINUATION_BYTES > self.size:
            return
        trigger = self._trigger()
        if trigger is None:
            return
        key = self._key(*trigger)
        prior = self.memory.get(key)
        candidates: list[tuple[bytes, int]] = []
        literal_weight = WEIGHT_TOTAL
        if len(prior) >= MIN_CANDIDATES:
            unit = WEIGHT_TOTAL // (LITERAL_PRIOR + len(prior))
            candidates = [(continuation, unit) for continuation in prior]
            literal_weight = WEIGHT_TOTAL - unit * len(candidates)
            self.wakes += 1
        self.active = Opportunity(key, candidates, literal_weight)
        self.opportunities += 1

    def update(self, symbol: int, distribution: Distribution) -> None:
        active = self.active
        if active is not None and active.candidates:
            offset = active.offset
            base_count = distribution.model.counts[symbol]
            base_total = distribution.base_total
            survivors = [
                (continuation, weight)
                for continuation, weight in active.candidates
                if continuation[offset] == symbol
            ]
            candidate_mass = sum(weight for _continuation, weight in survivors)
            literal_numerator = active.literal_weight * base_count
            denominator = literal_numerator + candidate_mass * base_total
            self.candidate_symbols += 1
            if survivors and denominator:
                new_literal = max(
                    MIN_LITERAL_WEIGHT,
                    WEIGHT_TOTAL * literal_numerator // denominator,
                )
                candidate_budget = WEIGHT_TOTAL - new_literal
                old_total = sum(weight for _continuation, weight in survivors)
                weighted = [
                    [continuation, candidate_budget * weight // old_total]
                    for continuation, weight in survivors
                ]
                weighted[0][1] += candidate_budget - sum(
                    weight for _continuation, weight in weighted
                )
                active.candidates = [
                    (continuation, int(weight)) for continuation, weight in weighted
                ]
                active.literal_weight = new_literal
                self.surviving_symbols += 1
            else:
                active.candidates = []
                active.literal_weight = WEIGHT_TOTAL

        self.literal.update(symbol)
        self.wiki.update(symbol)
        self.processed += 1
        if active is not None:
            active.buffer.append(symbol)
            if len(active.buffer) == CONTINUATION_BYTES:
                self.memory.add(active.key, bytes(active.buffer))
                self.active = None
        if self.active is None:
            self._launch()

    def stats(self) -> dict[str, int]:
        return {
            "opportunities": self.opportunities,
            "wakes": self.wakes,
            "candidate_symbols": self.candidate_symbols,
            "surviving_symbols": self.surviving_symbols,
            "memory_keys": len(self.memory.rows),
        }


def _encode(data: bytes, profile: str) -> tuple[bytes, dict[str, int]]:
    predictor = Predictor(profile, len(data))
    coder = ArithmeticEncoder()
    for symbol in data:
        distribution = predictor.distribution()
        coder.encode(*distribution.interval(symbol))
        predictor.update(symbol, distribution)
    return coder.finish(), predictor.stats()


def _decode(payload: bytes, size: int, profile: str) -> bytes:
    predictor = Predictor(profile, size)
    coder = ArithmeticDecoder(payload)
    output = bytearray()
    for _ in range(size):
        distribution = predictor.distribution()
        target = coder.target(distribution.total)
        symbol = distribution.symbol(target)
        coder.update(*distribution.interval(symbol))
        output.append(symbol)
        predictor.update(symbol, distribution)
    return bytes(output)


def compress(data: bytes) -> bytes:
    payloads: dict[str, bytes] = {}
    profile_stats: dict[str, dict[str, int]] = {}
    control_roundtrip: dict[str, bool] = {}
    for profile in PROFILES:
        payload, profile_stat = _encode(data, profile)
        payloads[profile] = payload
        profile_stats[profile] = profile_stat
        control_roundtrip[profile] = _decode(payload, len(data), profile) == data
        if not control_roundtrip[profile]:
            raise RuntimeError(f"{profile} control failed roundtrip")
    selected = min(PROFILES, key=lambda name: (len(payloads[name]), PROFILES.index(name)))
    mode = PROFILES.index(selected)
    _LAST_STATS.clear()
    _LAST_STATS.update(
        {
            "selected": selected,
            "payload_bytes": {name: len(payloads[name]) for name in PROFILES},
            "gain_vs_b0_bytes": {
                name: len(payloads["B0"]) - len(payloads[name]) for name in PROFILES
            },
            "profile_stats": profile_stats,
            "control_roundtrip": control_roundtrip,
            "continuation_bytes": CONTINUATION_BYTES,
            "max_candidates": MAX_CANDIDATES,
            "max_keys": MAX_KEYS,
        }
    )
    return MAGIC + struct.pack(">IB", len(data), mode) + payloads[selected]


def decompress(archive: bytes) -> bytes:
    if len(archive) < 13 or archive[:8] != MAGIC:
        raise ValueError("invalid TESBE-Raw archive")
    size, mode = struct.unpack_from(">IB", archive, 8)
    if mode >= len(PROFILES):
        raise ValueError("invalid TESBE-Raw selector mode")
    return _decode(archive[13:], size, PROFILES[mode])


def stats() -> dict[str, object]:
    return dict(_LAST_STATS)
