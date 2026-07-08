import struct
from dataclasses import dataclass, field
from typing import Any

TOTAL = 1 << 16
STATE_BITS = 32
FULL = 1 << STATE_BITS
HALF = FULL >> 1
QUARTER = HALF >> 1
THREE_QUARTER = QUARTER * 3
FNV_OFFSET = 1469598103934665603
FNV_PRIME = 1099511628211

BASE_ORDER = 2
BASE_TABLE_CAP = 200_000
RETRIEVAL_TABLE_CAP = 200_000
SUFFIX_LEN = 32
SKETCH_LEN = 96
P_BUCKETS = 32
MIN_SUPPORT = 8
BLEND_PPM = 640_000
ALPHA2 = 1
TYPED_KEY_PROFILE = "rich"

LAST_STATS: dict[str, int | float] = {}


def clamp_p1(p1: int) -> int:
    return max(1, min(TOTAL - 1, int(p1)))


def prob_bucket(p1: int, buckets: int) -> int:
    if buckets <= 1:
        return 0
    return min(buckets - 1, (clamp_p1(p1) * buckets) >> 16)


def fnv64_bytes(data: bytes) -> int:
    h = FNV_OFFSET
    for byte in data:
        h ^= byte
        h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


def fnv64_ints(values: tuple[int, ...]) -> int:
    h = FNV_OFFSET
    for value in values:
        h ^= value & 0xFFFFFFFFFFFFFFFF
        h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


def simhash16(data: bytes, ngram: int = 3) -> int:
    if not data:
        return 0
    if len(data) < ngram:
        return fnv64_bytes(data) & 0xFFFF
    acc = [0] * 16
    for i in range(0, len(data) - ngram + 1):
        h = fnv64_bytes(data[i : i + ngram])
        for bit in range(16):
            acc[bit] += 1 if (h >> bit) & 1 else -1
    out = 0
    for bit, value in enumerate(acc):
        if value >= 0:
            out |= 1 << bit
    return out


def bucket(value: int, cuts: tuple[int, ...]) -> int:
    for index, cut in enumerate(cuts):
        if value <= cut:
            return index
    return len(cuts)


def char_class(byte: int) -> int:
    if 65 <= byte <= 90:
        return 1
    if 97 <= byte <= 122:
        return 2
    if 48 <= byte <= 57:
        return 3
    if byte in (9, 10, 13, 32):
        return 4
    if byte in (60, 62, 47, 34, 38, 59, 61):
        return 5
    if byte in (91, 93, 123, 124, 125):
        return 6
    if byte >= 128:
        return 7
    return 0


class BitsOut:
    def __init__(self) -> None:
        self.out = bytearray()
        self.cur = 0
        self.n = 0

    def bit(self, value: int) -> None:
        self.cur = (self.cur << 1) | (value & 1)
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


class BinaryArithmeticEncoder:
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

    def bit(self, bit: int, p1: int) -> None:
        p1 = clamp_p1(p1)
        zeros = TOTAL - p1
        span = self.high - self.low + 1
        split = self.low + (span * zeros) // TOTAL
        if bit:
            self.low = split
        else:
            self.high = split - 1
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


class BinaryArithmeticDecoder:
    def __init__(self, data: bytes) -> None:
        self.low = 0
        self.high = FULL - 1
        self.bits = BitsIn(data)
        self.code = 0
        for _ in range(STATE_BITS):
            self.code = (self.code << 1) | self.bits.bit()

    def bit(self, p1: int) -> int:
        p1 = clamp_p1(p1)
        zeros = TOTAL - p1
        span = self.high - self.low + 1
        split = self.low + (span * zeros) // TOTAL
        target = ((self.code - self.low + 1) * TOTAL - 1) // span
        if target < zeros:
            bit = 0
            self.high = split - 1
        else:
            bit = 1
            self.low = split
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
        return bit


@dataclass
class BitCounts:
    zeros: int = 0
    ones: int = 0

    @property
    def total(self) -> int:
        return self.zeros + self.ones

    def update(self, bit: int) -> None:
        if bit:
            self.ones += 1
        else:
            self.zeros += 1


class BoundedCounterTable:
    def __init__(self, cap_entries: int) -> None:
        self.cap_entries = cap_entries
        self.counters: dict[tuple[Any, ...], BitCounts] = {}
        self.order: list[tuple[Any, ...]] = []
        self.cursor = 0

    def get(self, key: tuple[Any, ...]) -> BitCounts | None:
        return self.counters.get(key)

    def update(self, key: tuple[Any, ...], bit: int) -> None:
        counter = self.counters.get(key)
        if counter is None:
            if self.cap_entries > 0 and len(self.counters) >= self.cap_entries:
                while self.cursor < len(self.order):
                    old = self.order[self.cursor]
                    self.cursor += 1
                    if old in self.counters:
                        del self.counters[old]
                        break
                if self.cursor > 4096 and self.cursor * 2 > len(self.order):
                    self.order = self.order[self.cursor :]
                    self.cursor = 0
            counter = BitCounts()
            self.counters[key] = counter
            self.order.append(key)
        counter.update(bit)


@dataclass
class WikiState:
    field_id: int = 0
    mode: int = 0
    slot: int = 0
    page_kind: int = 0
    link_depth: int = 0
    template_depth: int = 0
    table_depth: int = 0
    tag_depth: int = 0
    ref_depth: int = 0
    column: int = 0
    line_start: bool = True
    prev1: int = 0
    prev2: int = 0
    prev3: int = 0
    prev_class: int = 0
    word_len: int = 0
    word_class: int = 0
    title_seen: bool = False
    tail: bytearray = field(default_factory=bytearray)

    def features(self) -> dict[str, Any]:
        return {
            "field": self.field_id,
            "mode": self.mode,
            "slot": self.slot,
            "column": bucket(self.column, (0, 4, 16, 48, 96)),
            "word_len_bucket": bucket(self.word_len, (0, 1, 3, 7, 15)),
            "word_class": self.word_class,
        }

    def update(self, byte: int) -> None:
        self.tail.append(byte)
        if len(self.tail) > 160:
            del self.tail[:64]
        tail = bytes(self.tail)
        lower = tail.lower()
        if byte == 10:
            self.column = 0
            self.line_start = True
        else:
            self.column = min(255, self.column + 1)
            if byte not in (9, 13, 32):
                self.line_start = False
        if self.prev1 == 91 and byte == 91:
            self.link_depth = min(7, self.link_depth + 1)
            self.mode = 1
        elif self.prev1 == 93 and byte == 93:
            self.link_depth = max(0, self.link_depth - 1)
            if self.link_depth == 0 and self.mode == 1:
                self.mode = 0
                if self.slot in (1, 2):
                    self.slot = 0
        elif self.prev1 == 123 and byte == 123:
            self.template_depth = min(7, self.template_depth + 1)
            self.mode = 2
        elif self.prev1 == 125 and byte == 125:
            self.template_depth = max(0, self.template_depth - 1)
            if self.template_depth == 0 and self.mode == 2:
                self.mode = 0
                if self.slot in (3, 4, 7, 8):
                    self.slot = 0
        elif self.prev1 == 123 and byte == 124:
            self.table_depth = min(3, self.table_depth + 1)
            self.mode = 4
        elif self.prev1 == 124 and byte == 125:
            self.table_depth = max(0, self.table_depth - 1)
            if self.table_depth == 0 and self.mode == 4:
                self.mode = 0
        elif self.prev1 == 60:
            self.tag_depth = min(3, self.tag_depth + 1)
            self.mode = 3
        elif byte == 62 and self.tag_depth:
            self.tag_depth = max(0, self.tag_depth - 1)
            if self.tag_depth == 0 and self.mode == 3 and self.ref_depth == 0:
                self.mode = 0
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
            self.mode = 3
        elif lower.endswith(b'name="') or lower.endswith(b"name='"):
            if self.slot == 5:
                self.slot = 6
        elif self.mode == 2 and lower.endswith(b"url="):
            self.slot = 7
        elif self.mode == 2 and lower.endswith(b"title="):
            self.slot = 8
        elif lower.endswith(b"==references=="):
            self.slot = 9
        elif lower.endswith(b"</ref>"):
            self.ref_depth = max(0, self.ref_depth - 1)
            if self.ref_depth == 0:
                self.slot = 0
                if self.mode == 3:
                    self.mode = 0
        if tail.endswith(b"<title>"):
            self.field_id = 1
            self.title_seen = False
        elif tail.endswith(b"</title>"):
            title_tail = lower[-120:]
            if b"list of" in title_tail:
                self.page_kind = 2
            elif b"disambiguation" in title_tail:
                self.page_kind = 3
            else:
                self.page_kind = 4
            self.field_id = 0
            self.title_seen = True
        elif tail.endswith(b"<id>"):
            self.field_id = 2
        elif tail.endswith(b"</id>"):
            self.field_id = 0
        elif tail.endswith(b"<timestamp>"):
            self.field_id = 3
        elif tail.endswith(b"</timestamp>"):
            self.field_id = 0
        elif tail.endswith(b"<username>"):
            self.field_id = 4
        elif tail.endswith(b"</username>"):
            self.field_id = 0
        elif tail.endswith(b"<comment>"):
            self.field_id = 5
        elif tail.endswith(b"</comment>"):
            self.field_id = 0
        elif tail.endswith(b'<text xml:space="preserve">'):
            self.field_id = 6
            self.slot = 0
            self.mode = 0
        elif tail.endswith(b"</text>"):
            self.field_id = 0
            self.slot = 0
            self.mode = 0
            self.link_depth = 0
            self.template_depth = 0
            self.table_depth = 0
            self.ref_depth = 0
        cls = char_class(byte)
        if cls in (1, 2):
            self.word_len = min(31, self.word_len + 1)
            self.word_class = cls
        elif cls == 3:
            self.word_len = min(31, self.word_len + 1)
            self.word_class = 3
        else:
            self.word_len = 0
            self.word_class = cls
        self.prev3 = self.prev2
        self.prev2 = self.prev1
        self.prev1 = byte
        self.prev_class = cls


class CausalState:
    def __init__(self) -> None:
        self.wiki = WikiState()
        self.tail = bytearray()
        self.cached: dict[str, Any] | None = None

    def observe_byte(self, byte: int) -> None:
        self.wiki.update(byte)
        self.tail.append(byte)
        keep = max(SUFFIX_LEN, SKETCH_LEN, 192)
        if len(self.tail) > keep * 2:
            del self.tail[: len(self.tail) - keep]
        self.cached = None

    def features(self) -> dict[str, Any]:
        if self.cached is not None:
            return self.cached
        tail = bytes(self.tail)
        wiki = self.wiki.features()
        field_id = int(wiki["field"])
        mode = int(wiki["mode"])
        slot = int(wiki["slot"])
        column = int(wiki["column"])
        word_len_bucket = int(wiki["word_len_bucket"])
        word_class = int(wiki["word_class"])
        sim = simhash16(tail[-SKETCH_LEN:])
        suffix_hash = fnv64_bytes(tail[-SUFFIX_LEN:]) & 0xFFFF
        schema_hash = fnv64_ints(
            (field_id, mode, slot, column, word_len_bucket, word_class)
        ) & 0xFFFF
        self.cached = {
            "field": field_id,
            "mode": mode,
            "slot": slot,
            "column": column,
            "word_len_bucket": word_len_bucket,
            "word_class": word_class,
            "suffix_hash": suffix_hash,
            "sim_band0": sim & 0xFF,
            "sim_band1": (sim >> 8) & 0xFF,
            "schema_hash": schema_hash,
        }
        return self.cached


@dataclass
class PartialByteState:
    prefix: int = 0
    length: int = 0

    def current(self) -> tuple[int, int]:
        return self.length, self.prefix

    def observe(self, bit: int) -> int | None:
        self.prefix = ((self.prefix << 1) | int(bit)) & 0xFF
        self.length += 1
        if self.length == 8:
            byte = self.prefix
            self.prefix = 0
            self.length = 0
            return byte
        return None


class RawBaseModel:
    def __init__(self) -> None:
        self.table = BoundedCounterTable(BASE_TABLE_CAP)

    def key(
        self,
        history: bytes,
        bit_pos: int,
        partial_len: int,
        partial_prefix: int,
    ) -> tuple[Any, ...]:
        suffix = tuple(history[-BASE_ORDER:]) if BASE_ORDER > 0 else ()
        return ("raw_base", bit_pos, partial_len, partial_prefix, suffix)

    def predict(
        self,
        history: bytes,
        bit_pos: int,
        partial_len: int,
        partial_prefix: int,
    ) -> int:
        counter = self.table.get(self.key(history, bit_pos, partial_len, partial_prefix))
        if counter is None:
            return TOTAL // 2
        total = counter.total
        denom = 2 * total + 2 * ALPHA2
        numer = (2 * counter.ones + ALPHA2) * TOTAL
        return clamp_p1(numer // denom)

    def update(
        self,
        history: bytes,
        bit_pos: int,
        partial_len: int,
        partial_prefix: int,
        bit: int,
    ) -> None:
        self.table.update(self.key(history, bit_pos, partial_len, partial_prefix), bit)


def make_keys(
    features: dict[str, Any],
    bit_pos: int,
    base_p1: int,
    partial_len: int,
    partial_prefix: int,
) -> list[tuple[Any, ...]]:
    pbin = prob_bucket(base_p1, P_BUCKETS)
    keys: list[tuple[Any, ...]] = [
        ("suffix", bit_pos, pbin, features["suffix_hash"]),
        ("sim0", bit_pos, pbin, features["sim_band0"]),
        ("sim1", bit_pos, pbin, features["sim_band1"]),
        ("schema", bit_pos, pbin, features["schema_hash"]),
        ("hybrid", bit_pos, pbin, features["field"], features["mode"], features["sim_band0"]),
    ]
    if TYPED_KEY_PROFILE == "rich":
        keys.extend(
            [
                (
                    "schema_slot",
                    bit_pos,
                    pbin,
                    features["field"],
                    features["mode"],
                    features["slot"],
                ),
                (
                    "schema_column",
                    bit_pos,
                    pbin,
                    features["field"],
                    features["mode"],
                    features["column"],
                ),
                (
                    "schema_word",
                    bit_pos,
                    pbin,
                    features["schema_hash"],
                    features["word_len_bucket"],
                    features["word_class"],
                ),
                (
                    "sim_schema",
                    bit_pos,
                    pbin,
                    features["sim_band0"],
                    features["schema_hash"],
                ),
                (
                    "suffix_schema",
                    bit_pos,
                    pbin,
                    features["suffix_hash"],
                    features["schema_hash"],
                ),
            ]
        )
    if partial_len > 0:
        partial_bucket = fnv64_ints((partial_len, partial_prefix, bit_pos)) & 0xFFFF
        keys.extend(
            [
                ("partial_suffix", bit_pos, partial_len, partial_prefix, pbin, features["suffix_hash"]),
                ("partial_sim0", bit_pos, partial_len, partial_prefix, pbin, features["sim_band0"]),
                ("partial_schema", bit_pos, partial_len, partial_prefix, pbin, features["schema_hash"]),
                (
                    "partial_hybrid",
                    bit_pos,
                    pbin,
                    partial_bucket,
                    features["field"],
                    features["mode"],
                    features["sim_band0"],
                ),
            ]
        )
    return keys


def retrieval_p1(table: BoundedCounterTable, keys: list[tuple[Any, ...]]) -> tuple[int | None, int]:
    zeros = 0
    ones = 0
    hits = 0
    for key in keys:
        counter = table.get(key)
        if counter is None:
            continue
        zeros += counter.zeros
        ones += counter.ones
        hits += counter.total
    total = zeros + ones
    if total < MIN_SUPPORT:
        return None, hits
    denom = 2 * total + 2 * ALPHA2
    numer = (2 * ones + ALPHA2) * TOTAL
    return clamp_p1(numer // denom), hits


def blend_probability(base_p1: int, prior_p1: int | None) -> int:
    if prior_p1 is None:
        return base_p1
    mixed = (base_p1 * (1_000_000 - BLEND_PPM) + prior_p1 * BLEND_PPM) // 1_000_000
    return clamp_p1(mixed)


class Predictor:
    def __init__(self) -> None:
        self.state = CausalState()
        self.partial = PartialByteState()
        self.base = RawBaseModel()
        self.retrieval = BoundedCounterTable(RETRIEVAL_TABLE_CAP)
        self.rows = 0
        self.retrieval_rows = 0
        self.retrieval_hits = 0

    def p1(self, bit_pos: int) -> tuple[int, bytes, int, int, list[tuple[Any, ...]]]:
        partial_len, partial_prefix = self.partial.current()
        history = bytes(self.state.tail)
        base_p1 = self.base.predict(history, bit_pos, partial_len, partial_prefix)
        keys = make_keys(self.state.features(), bit_pos, base_p1, partial_len, partial_prefix)
        prior_p1, hits = retrieval_p1(self.retrieval, keys)
        corrected = blend_probability(base_p1, prior_p1)
        if prior_p1 is not None:
            self.retrieval_rows += 1
            self.retrieval_hits += hits
        return corrected, history, partial_len, partial_prefix, keys

    def update(
        self,
        bit: int,
        bit_pos: int,
        history: bytes,
        partial_len: int,
        partial_prefix: int,
        keys: list[tuple[Any, ...]],
    ) -> None:
        self.base.update(history, bit_pos, partial_len, partial_prefix, bit)
        for key in keys:
            self.retrieval.update(key, bit)
        self.rows += 1
        byte = self.partial.observe(bit)
        if byte is not None:
            self.state.observe_byte(byte)


def compress(data: bytes) -> bytes:
    pred = Predictor()
    enc = BinaryArithmeticEncoder()
    for byte in data:
        for bit_pos in range(8):
            bit = (byte >> (7 - bit_pos)) & 1
            p1, history, partial_len, partial_prefix, keys = pred.p1(bit_pos)
            enc.bit(bit, p1)
            pred.update(bit, bit_pos, history, partial_len, partial_prefix, keys)
    body = enc.finish()
    LAST_STATS.clear()
    LAST_STATS.update(
        {
            "rows": pred.rows,
            "retrieval_rows": pred.retrieval_rows,
            "retrieval_mean_hits": pred.retrieval_hits / pred.retrieval_rows
            if pred.retrieval_rows
            else 0.0,
            "base_contexts": len(pred.base.table.counters),
            "retrieval_contexts": len(pred.retrieval.counters),
        }
    )
    return struct.pack(">I", len(data)) + body


def decompress(blob: bytes) -> bytes:
    if len(blob) < 4:
        raise ValueError("truncated SRSTC archive")
    size = struct.unpack(">I", blob[:4])[0]
    pred = Predictor()
    dec = BinaryArithmeticDecoder(blob[4:])
    out = bytearray()
    for _ in range(size):
        byte = 0
        for bit_pos in range(8):
            p1, history, partial_len, partial_prefix, keys = pred.p1(bit_pos)
            bit = dec.bit(p1)
            byte = (byte << 1) | bit
            pred.update(bit, bit_pos, history, partial_len, partial_prefix, keys)
        out.append(byte)
    return bytes(out)


def stats() -> dict[str, int | float]:
    return dict(LAST_STATS)
