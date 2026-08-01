"""Exact primitives for the Route D timestamp-microblock Q0 diagnostic.

The score-bearing mechanism under study is an energy-ordered XOR residual
around the previous decoder-visible timestamp microblock.  This module exposes
exact rank/unrank, deterministic nested parity rows, bounded first-hit search,
an explicit byte-edit control, and a matched causal arithmetic control.

``compress`` and ``decompress`` deliberately implement only a literal framed
fallback.  The candidate receives no compression credit unless the separate
receipt-bound diagnostic proves that the rank/parity representation pays.
"""

from __future__ import annotations

from functools import lru_cache
import hashlib
import itertools
import math
from typing import Iterable


MAGIC = b"RDTQ0L1\0"
TOTAL = 4096
MAX_CODE = (1 << 32) - 1
HALF = 1 << 31
FIRST_QTR = 1 << 30
THIRD_QTR = FIRST_QTR * 3
CAUSAL_ORDER = 8


def compress(data: bytes) -> bytes:
    """Return an exact literal container; it is a non-scoring fallback only."""

    return MAGIC + len(data).to_bytes(8, "big") + data


def decompress(archive: bytes) -> bytes:
    if len(archive) < len(MAGIC) + 8 or not archive.startswith(MAGIC):
        raise ValueError("invalid Route D Q0 literal container")
    size = int.from_bytes(archive[len(MAGIC) : len(MAGIC) + 8], "big")
    data = archive[len(MAGIC) + 8 :]
    if len(data) != size:
        raise ValueError("Route D Q0 literal container length mismatch")
    return data


def ceil_log2(value: int) -> int:
    if value <= 0:
        raise ValueError("ceil_log2 requires a positive integer")
    return (value - 1).bit_length()


def elias_delta_length(value: int) -> int:
    if value <= 0:
        raise ValueError("Elias-delta values must be positive")
    width = value.bit_length()
    return width + 2 * (width.bit_length() - 1)


def residual_mask(prototype: bytes, target: bytes) -> int:
    if len(prototype) != len(target) or not target:
        raise ValueError("prototype and target must have equal positive length")
    return int.from_bytes(prototype, "big") ^ int.from_bytes(target, "big")


def apply_residual(prototype: bytes, residual: int) -> bytes:
    width_bits = len(prototype) * 8
    if residual < 0 or residual >= (1 << width_bits):
        raise ValueError("residual does not fit prototype width")
    value = int.from_bytes(prototype, "big") ^ residual
    return value.to_bytes(len(prototype), "big")


def combination_lex_rank(width: int, positions: tuple[int, ...]) -> int:
    """Rank an ascending position tuple in itertools.combinations order."""

    rank = 0
    previous = -1
    count = len(positions)
    for index, position in enumerate(positions):
        if position <= previous or position >= width:
            raise ValueError("positions must be strictly increasing and in range")
        remaining = count - index - 1
        for skipped in range(previous + 1, position):
            rank += math.comb(width - skipped - 1, remaining)
        previous = position
    return rank


def combination_lex_unrank(width: int, count: int, rank: int) -> tuple[int, ...]:
    population = math.comb(width, count)
    if rank < 0 or rank >= population:
        raise ValueError("combination rank out of range")
    positions: list[int] = []
    start = 0
    remaining_rank = rank
    for index in range(count):
        remaining = count - index - 1
        for position in range(start, width):
            suffixes = math.comb(width - position - 1, remaining)
            if remaining_rank < suffixes:
                positions.append(position)
                start = position + 1
                break
            remaining_rank -= suffixes
    return tuple(positions)


def energy_rank(width: int, mask: int) -> int:
    if width <= 0 or mask < 0 or mask >= (1 << width):
        raise ValueError("mask does not fit energy width")
    weight = mask.bit_count()
    before_weight = sum(math.comb(width, value) for value in range(weight))
    positions = tuple(index for index in range(width) if (mask >> index) & 1)
    return before_weight + combination_lex_rank(width, positions)


def energy_unrank(width: int, rank: int) -> int:
    if width <= 0 or rank < 0 or rank >= (1 << width):
        raise ValueError("energy rank out of range")
    remaining = rank
    for weight in range(width + 1):
        population = math.comb(width, weight)
        if remaining < population:
            mask = 0
            for position in combination_lex_unrank(width, weight, remaining):
                mask |= 1 << position
            return mask
        remaining -= population
    raise AssertionError("unreachable energy rank")


def iter_energy_masks(width: int, stop_rank: int) -> Iterable[tuple[int, int]]:
    """Yield canonical masks from rank zero through ``stop_rank`` inclusive."""

    if stop_rank < 0:
        return
    rank = 0
    for weight in range(width + 1):
        for positions in itertools.combinations(range(width), weight):
            mask = 0
            for position in positions:
                mask |= 1 << position
            yield rank, mask
            if rank == stop_rank:
                return
            rank += 1


def _hash_row(width: int, counter: int) -> int:
    needed = (width + 7) // 8
    payload = bytearray()
    block = 0
    while len(payload) < needed:
        payload.extend(
            hashlib.sha256(
                f"seal2-route-d:{width}:{counter}:{block}".encode("ascii")
            ).digest()
        )
        block += 1
    return int.from_bytes(payload[:needed], "big") & ((1 << width) - 1)


@lru_cache(maxsize=None)
def deterministic_parity_rows(width: int) -> tuple[int, ...]:
    """Return a deterministic full-rank nested binary parity matrix."""

    if width <= 0:
        raise ValueError("parity width must be positive")
    basis: dict[int, int] = {}
    rows: list[int] = []
    counter = 0
    while len(rows) < width:
        row = _hash_row(width, counter)
        counter += 1
        reduced = row
        for pivot in sorted(basis, reverse=True):
            if (reduced >> pivot) & 1:
                reduced ^= basis[pivot]
        if reduced == 0:
            continue
        basis[reduced.bit_length() - 1] = reduced
        rows.append(row)
    return tuple(rows)


def parity_signature(mask: int, rows: tuple[int, ...], depth: int) -> int:
    if depth < 0 or depth > len(rows):
        raise ValueError("parity depth out of range")
    signature = 0
    for row in rows[:depth]:
        signature = (signature << 1) | ((mask & row).bit_count() & 1)
    return signature


@lru_cache(maxsize=8192)
def bounded_parity_certificate(
    width: int,
    true_mask: int,
    max_expansions: int,
) -> dict[str, int | bool | None]:
    """Prove a minimum nested depth and replay the exact first-hit search."""

    rank = energy_rank(width, true_mask)
    expansions = rank + 1
    if expansions > max_expansions:
        return {
            "rank": rank,
            "expansions": expansions,
            "within_budget": False,
            "depth": None,
            "roundtrip_ok": False,
        }

    rows = deterministic_parity_rows(width)
    required_depth = 0
    for candidate_rank, candidate in iter_energy_masks(width, rank):
        if candidate_rank == rank:
            if candidate != true_mask:
                raise AssertionError("energy enumeration disagrees with rank")
            break
        difference = candidate ^ true_mask
        separating_depth = next(
            index
            for index, row in enumerate(rows, start=1)
            if (difference & row).bit_count() & 1
        )
        required_depth = max(required_depth, separating_depth)

    syndrome = parity_signature(true_mask, rows, required_depth)
    recovered = None
    observed_expansions = 0
    for _candidate_rank, candidate in iter_energy_masks(width, rank):
        observed_expansions += 1
        if parity_signature(candidate, rows, required_depth) == syndrome:
            recovered = candidate
            break
    return {
        "rank": rank,
        "expansions": observed_expansions,
        "within_budget": True,
        "depth": required_depth,
        "roundtrip_ok": recovered == true_mask,
    }


def byte_edit_bits(prototype: bytes, target: bytes) -> int:
    if len(prototype) != len(target) or not target:
        raise ValueError("byte-edit inputs must have equal positive length")
    changed = [index for index, pair in enumerate(zip(prototype, target)) if pair[0] != pair[1]]
    position_bits = ceil_log2(math.comb(len(target), len(changed)))
    count_bits = ceil_log2(len(target) + 1)
    return count_bits + position_bits + 8 * len(changed)


class BitWriter:
    def __init__(self) -> None:
        self.output = bytearray()
        self.current = 0
        self.used = 0
        self.bits = 0

    def write(self, bit: int) -> None:
        self.current = (self.current << 1) | (bit & 1)
        self.used += 1
        self.bits += 1
        if self.used == 8:
            self.output.append(self.current)
            self.current = 0
            self.used = 0

    def finish(self) -> bytes:
        if self.used:
            self.output.append(self.current << (8 - self.used))
            self.current = 0
            self.used = 0
        return bytes(self.output)


class BitReader:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.position = 0

    def read(self) -> int:
        if self.position >= len(self.payload) * 8:
            self.position += 1
            return 0
        value = (self.payload[self.position >> 3] >> (7 - (self.position & 7))) & 1
        self.position += 1
        return value


class ArithmeticEncoder:
    def __init__(self) -> None:
        self.low = 0
        self.high = MAX_CODE
        self.pending = 0
        self.writer = BitWriter()

    def _emit(self, bit: int) -> None:
        self.writer.write(bit)
        while self.pending:
            self.writer.write(1 - bit)
            self.pending -= 1

    def encode(self, bit: int, p1: int) -> None:
        p1 = max(1, min(TOTAL - 1, p1))
        span = self.high - self.low + 1
        split = self.low + (span * (TOTAL - p1)) // TOTAL
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
            elif self.low >= FIRST_QTR and self.high < THIRD_QTR:
                self.pending += 1
                self.low -= FIRST_QTR
                self.high -= FIRST_QTR
            else:
                break
            self.low = (self.low << 1) & MAX_CODE
            self.high = ((self.high << 1) & MAX_CODE) | 1

    def finish(self) -> tuple[bytes, int]:
        self.pending += 1
        self._emit(0 if self.low < FIRST_QTR else 1)
        bits = self.writer.bits
        return self.writer.finish(), bits


class ArithmeticDecoder:
    def __init__(self, payload: bytes) -> None:
        self.reader = BitReader(payload)
        self.low = 0
        self.high = MAX_CODE
        self.code = 0
        for _ in range(32):
            self.code = ((self.code << 1) | self.reader.read()) & MAX_CODE

    def decode(self, p1: int) -> int:
        p1 = max(1, min(TOTAL - 1, p1))
        span = self.high - self.low + 1
        split = self.low + (span * (TOTAL - p1)) // TOTAL
        if self.code < split:
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
            elif self.low >= FIRST_QTR and self.high < THIRD_QTR:
                self.low -= FIRST_QTR
                self.high -= FIRST_QTR
                self.code -= FIRST_QTR
            else:
                break
            self.low = (self.low << 1) & MAX_CODE
            self.high = ((self.high << 1) & MAX_CODE) | 1
            self.code = ((self.code << 1) & MAX_CODE) | self.reader.read()
        return bit


class AdaptiveCausalModel:
    def __init__(self) -> None:
        self.counts: dict[tuple[int, int], list[int]] = {}
        self.context = 0
        self.available = 0

    def _key(self) -> tuple[int, int]:
        order = min(CAUSAL_ORDER, self.available)
        return order, self.context & ((1 << order) - 1)

    def p1(self) -> int:
        zeros, ones = self.counts.get(self._key(), [1, 1])
        return max(1, min(TOTAL - 1, (ones * TOTAL) // (zeros + ones)))

    def update(self, bit: int) -> None:
        key = self._key()
        pair = self.counts.setdefault(key, [1, 1])
        pair[bit] += 1
        if pair[0] + pair[1] >= 255:
            pair[0] = (pair[0] + 1) >> 1
            pair[1] = (pair[1] + 1) >> 1
        self.context = ((self.context << 1) | bit) & ((1 << CAUSAL_ORDER) - 1)
        self.available = min(CAUSAL_ORDER, self.available + 1)


def _bits(value: int, width: int) -> Iterable[int]:
    for position in range(width - 1, -1, -1):
        yield (value >> position) & 1


def causal_roundtrip(values: list[int], width: int) -> dict[str, int | str | bool]:
    """Encode and decode residual masks with one matched causal arithmetic model."""

    encoder = ArithmeticEncoder()
    model = AdaptiveCausalModel()
    for value in values:
        if value < 0 or value >= (1 << width):
            raise ValueError("causal value does not fit width")
        for bit in _bits(value, width):
            encoder.encode(bit, model.p1())
            model.update(bit)
    payload, payload_bits = encoder.finish()

    decoder = ArithmeticDecoder(payload)
    model = AdaptiveCausalModel()
    decoded: list[int] = []
    for _ in values:
        value = 0
        for _position in range(width):
            bit = decoder.decode(model.p1())
            model.update(bit)
            value = (value << 1) | bit
        decoded.append(value)
    return {
        "payload_bits": payload_bits,
        "payload_bytes": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "roundtrip_ok": decoded == values,
    }
