"""Exact sentence edit-bypass primitives for the LOGOS semantic QH0 gate.

The encoder-side semantic retriever is deliberately outside this module.  A
decoder receives only canonical prior-span references, COPY intervals, and a
literal arithmetic stream.  The score-bearing native parent-state hook is not
claimed at QH0. ``compress`` and ``decompress`` remain literal-only fallbacks
for the repository program contract and receive no score credit.
"""

from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Iterable, Iterator, Sequence


MASK32 = (1 << 32) - 1
BYPASS_MAGIC = b"LGSEDBP1"
LITERAL_MAGIC = b"LGSLIT1\0"
BYPASS_HEADER = struct.Struct("<8sQQQQQ")
LITERAL_HEADER = struct.Struct("<8sQ")
COUNT = struct.Struct("<I")
MIN_COPY_BYTES = 8


@dataclass(frozen=True)
class CopySpan:
    target_offset: int
    source_offset: int
    length: int


@dataclass(frozen=True)
class PagePlan:
    target_start: int
    target_length: int
    prototype_start: int
    prototype_length: int
    copies: tuple[CopySpan, ...]


def encode_uleb(value: int) -> bytes:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("ULEB128 requires a nonnegative integer")
    output = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        output.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(output)


def uleb_size(value: int) -> int:
    return len(encode_uleb(value))


def decode_uleb(data: bytes, cursor: int) -> tuple[int, int]:
    start = cursor
    value = 0
    shift = 0
    while cursor < len(data):
        byte = data[cursor]
        cursor += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            if data[start:cursor] != encode_uleb(value):
                raise ValueError("noncanonical ULEB128")
            return value, cursor
        shift += 7
        if shift > 63:
            raise ValueError("ULEB128 exceeds 64 bits")
    raise ValueError("truncated ULEB128")


def validate_plans(
    plans: Sequence[PagePlan],
    wrt_size: int,
    original: bytes | None = None,
) -> None:
    previous_target_end = 0
    for plan in plans:
        target_end = plan.target_start + plan.target_length
        prototype_end = plan.prototype_start + plan.prototype_length
        if not 0 <= previous_target_end <= plan.target_start < target_end <= wrt_size:
            raise ValueError("target page plans overlap or exceed the WRT stream")
        if not 0 <= plan.prototype_start < prototype_end <= plan.target_start:
            raise ValueError("prototype page is not strictly prior")
        if not plan.copies:
            raise ValueError("active page plan has no copies")
        previous_copy_end = 0
        for copy in plan.copies:
            target_copy_end = copy.target_offset + copy.length
            source_copy_end = copy.source_offset + copy.length
            if copy.length < MIN_COPY_BYTES:
                raise ValueError("copy span is shorter than the frozen minimum")
            if not (
                0 <= previous_copy_end <= copy.target_offset
                and target_copy_end <= plan.target_length
                and 0 <= copy.source_offset
                and source_copy_end <= plan.prototype_length
            ):
                raise ValueError("copy span overlaps or exceeds a page")
            if original is not None:
                target = plan.target_start + copy.target_offset
                source = plan.prototype_start + copy.source_offset
                if original[target : target + copy.length] != original[
                    source : source + copy.length
                ]:
                    raise ValueError("copy span does not reproduce exact WRT bytes")
            previous_copy_end = target_copy_end
        previous_target_end = target_end


def encode_commands(plans: Sequence[PagePlan], wrt_size: int) -> bytes:
    ordered = tuple(sorted(plans, key=lambda plan: plan.target_start))
    validate_plans(ordered, wrt_size)
    output = bytearray(COUNT.pack(len(ordered)))
    for plan in ordered:
        output += encode_uleb(plan.target_start)
        output += encode_uleb(plan.target_length)
        output += encode_uleb(plan.prototype_start)
        output += encode_uleb(plan.prototype_length)
        output += COUNT.pack(len(plan.copies))
        for copy in plan.copies:
            output += encode_uleb(copy.target_offset)
            output += encode_uleb(copy.source_offset)
            output += encode_uleb(copy.length)
    return bytes(output)


def decode_commands(data: bytes, wrt_size: int) -> tuple[PagePlan, ...]:
    if len(data) < COUNT.size:
        raise ValueError("command stream is truncated")
    page_count = COUNT.unpack_from(data)[0]
    cursor = COUNT.size
    plans: list[PagePlan] = []
    for _ in range(page_count):
        target_start, cursor = decode_uleb(data, cursor)
        target_length, cursor = decode_uleb(data, cursor)
        prototype_start, cursor = decode_uleb(data, cursor)
        prototype_length, cursor = decode_uleb(data, cursor)
        if cursor + COUNT.size > len(data):
            raise ValueError("truncated copy count")
        copy_count = COUNT.unpack_from(data, cursor)[0]
        cursor += COUNT.size
        copies: list[CopySpan] = []
        for _ in range(copy_count):
            target_offset, cursor = decode_uleb(data, cursor)
            source_offset, cursor = decode_uleb(data, cursor)
            length, cursor = decode_uleb(data, cursor)
            copies.append(CopySpan(target_offset, source_offset, length))
        plans.append(
            PagePlan(
                target_start=target_start,
                target_length=target_length,
                prototype_start=prototype_start,
                prototype_length=prototype_length,
                copies=tuple(copies),
            )
        )
    if cursor != len(data):
        raise ValueError("command stream has trailing bytes")
    result = tuple(plans)
    validate_plans(result, wrt_size)
    return result


class RangeEncoder:
    def __init__(self) -> None:
        self.low = 0
        self.high = MASK32
        self.output = bytearray()

    def encode(self, probability_one: int, truth: int) -> None:
        probability_one = int(probability_one)
        if not 1 <= probability_one <= 65535:
            raise ValueError("P1 probability must be in [1, 65535]")
        delta = self.high - self.low
        midpoint = self.low + (delta >> 16) * probability_one + (
            (delta & 0xFFFF) * probability_one >> 16
        )
        if truth:
            self.high = midpoint
        else:
            self.low = midpoint + 1
        while ((self.low ^ self.high) & 0xFF000000) == 0:
            self.output.append((self.high >> 24) & 0xFF)
            self.low = (self.low << 8) & MASK32
            self.high = ((self.high << 8) & MASK32) + 255

    def finish(self) -> bytes:
        while ((self.low ^ self.high) & 0xFF000000) == 0:
            self.output.append((self.high >> 24) & 0xFF)
            self.low = (self.low << 8) & MASK32
            self.high = ((self.high << 8) & MASK32) + 255
        self.output.append((self.high >> 24) & 0xFF)
        return bytes(self.output)


class RangeDecoder:
    def __init__(self, payload: bytes) -> None:
        if not payload:
            raise ValueError("range payload is empty")
        self.payload = payload
        self.cursor = 4
        self.code = int.from_bytes(payload[:4].ljust(4, b"\0"), "big")
        self.low = 0
        self.high = MASK32

    def decode(self, probability_one: int) -> int:
        probability_one = int(probability_one)
        if not 1 <= probability_one <= 65535:
            raise ValueError("P1 probability must be in [1, 65535]")
        delta = self.high - self.low
        midpoint = self.low + (delta >> 16) * probability_one + (
            (delta & 0xFFFF) * probability_one >> 16
        )
        if self.code <= midpoint:
            truth = 1
            self.high = midpoint
        else:
            truth = 0
            self.low = midpoint + 1
        while ((self.low ^ self.high) & 0xFF000000) == 0:
            self.low = (self.low << 8) & MASK32
            self.high = ((self.high << 8) & MASK32) + 255
            byte = self.payload[self.cursor] if self.cursor < len(self.payload) else 0
            self.cursor += 1
            self.code = ((self.code << 8) & MASK32) + byte
        return truth


def copy_intervals(plans: Sequence[PagePlan]) -> Iterator[tuple[int, int, int]]:
    for plan in plans:
        for copy in plan.copies:
            yield (
                plan.target_start + copy.target_offset,
                plan.prototype_start + copy.source_offset,
                copy.length,
            )


def literal_byte_indices(wrt_size: int, plans: Sequence[PagePlan]) -> Iterator[int]:
    cursor = 0
    for target, _source, length in copy_intervals(plans):
        yield from range(cursor, target)
        cursor = target + length
    yield from range(cursor, wrt_size)


def range_encode(data: bytes, probabilities: Sequence[int]) -> bytes:
    if len(probabilities) != len(data) * 8:
        raise ValueError("probability rows do not match byte stream")
    encoder = RangeEncoder()
    row = 0
    for value in data:
        for shift in range(7, -1, -1):
            encoder.encode(probabilities[row], (value >> shift) & 1)
            row += 1
    return encoder.finish()


def build_bypass_archive(
    data: bytes,
    probabilities: Sequence[int],
    plans: Sequence[PagePlan],
) -> bytes:
    plans = tuple(sorted(plans, key=lambda plan: plan.target_start))
    validate_plans(plans, len(data), data)
    if len(probabilities) != len(data) * 8:
        raise ValueError("probability rows do not match byte stream")
    commands = encode_commands(plans, len(data))
    encoder = RangeEncoder()
    literal_bits = 0
    for byte_index in literal_byte_indices(len(data), plans):
        value = data[byte_index]
        row = byte_index * 8
        for bit_index, shift in enumerate(range(7, -1, -1)):
            encoder.encode(probabilities[row + bit_index], (value >> shift) & 1)
            literal_bits += 1
    payload = encoder.finish()
    return (
        BYPASS_HEADER.pack(
            BYPASS_MAGIC,
            len(data),
            len(probabilities),
            len(commands),
            literal_bits,
            len(payload),
        )
        + commands
        + payload
    )


def decode_bypass_archive(
    archive: bytes,
    probabilities: Sequence[int],
) -> tuple[bytes, tuple[PagePlan, ...]]:
    if len(archive) < BYPASS_HEADER.size:
        raise ValueError("bypass archive is truncated")
    magic, wrt_size, rows, command_bytes, literal_bits, payload_bytes = (
        BYPASS_HEADER.unpack_from(archive)
    )
    if magic != BYPASS_MAGIC:
        raise ValueError("invalid bypass archive magic")
    if rows != len(probabilities) or rows != wrt_size * 8:
        raise ValueError("archive probability-row contract differs")
    expected_size = BYPASS_HEADER.size + command_bytes + payload_bytes
    if len(archive) != expected_size:
        raise ValueError("bypass archive length differs from frame")
    command_start = BYPASS_HEADER.size
    command_end = command_start + command_bytes
    commands = archive[command_start:command_end]
    payload = archive[command_end:]
    plans = decode_commands(commands, wrt_size)
    intervals = iter(copy_intervals(plans))
    current_copy = next(intervals, None)
    decoder = RangeDecoder(payload)
    output = bytearray(wrt_size)
    decoded_literal_bits = 0
    position = 0
    while position < wrt_size:
        if current_copy is not None and position == current_copy[0]:
            _target, source, length = current_copy
            if source + length > position:
                raise ValueError("copy source is not fully decoder-visible")
            output[position : position + length] = output[source : source + length]
            position += length
            current_copy = next(intervals, None)
            continue
        value = 0
        row = position * 8
        for bit_index in range(8):
            value = (value << 1) | decoder.decode(probabilities[row + bit_index])
            decoded_literal_bits += 1
        output[position] = value
        position += 1
    if current_copy is not None:
        raise ValueError("unconsumed copy command")
    if decoded_literal_bits != literal_bits:
        raise ValueError("decoded literal-bit count differs from frame")
    result = bytes(output)
    validate_plans(plans, wrt_size, result)
    if encode_commands(plans, wrt_size) != commands:
        raise ValueError("command stream is not byte-canonical")
    return result, plans


def compress(data: bytes) -> bytes:
    """Literal-only zero-credit fallback for the repository program contract."""

    return LITERAL_HEADER.pack(LITERAL_MAGIC, len(data)) + data


def decompress(archive: bytes) -> bytes:
    if len(archive) < LITERAL_HEADER.size:
        raise ValueError("literal archive is truncated")
    magic, length = LITERAL_HEADER.unpack_from(archive)
    if magic != LITERAL_MAGIC or len(archive) != LITERAL_HEADER.size + length:
        raise ValueError("invalid literal archive")
    return archive[LITERAL_HEADER.size :]
