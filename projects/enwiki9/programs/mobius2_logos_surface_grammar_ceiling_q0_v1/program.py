"""Exact state-preserving surface-grammar archive primitives for LOGOS Q0.

The module implements the decoder-visible part of the certificate: finite WRT
rule definitions, ordered invocations with literal holes, and an actual
literal-only range payload over receipt-bound parent probabilities. Grammar
discovery remains an encoder-side operation in the gate.
"""

from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Iterator, Sequence


MASK32 = (1 << 32) - 1
MAGIC = b"M2LOGS1\0"
LITERAL_MAGIC = b"M2LIT1\0\0"
HEADER = struct.Struct("<8sB7xQQQQQ")
LITERAL_HEADER = struct.Struct("<8sQ")
COUNT = struct.Struct("<I")
MODE_FORCED_LITERAL = 0
MODE_GENERATE = 1


@dataclass(frozen=True)
class Rule:
    segments: tuple[bytes, ...]


@dataclass(frozen=True)
class Invocation:
    target_start: int
    rule_id: int
    hole_lengths: tuple[int, ...]


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


def rule_definition_bytes(rule: Rule) -> int:
    return uleb_size(len(rule.segments)) + sum(
        uleb_size(len(segment)) + len(segment) for segment in rule.segments
    )


def invocation_bytes(invocation: Invocation) -> int:
    return (
        uleb_size(invocation.target_start)
        + uleb_size(invocation.rule_id)
        + sum(uleb_size(length) for length in invocation.hole_lengths)
    )


def invocation_end(rule: Rule, invocation: Invocation) -> int:
    return invocation.target_start + sum(map(len, rule.segments)) + sum(
        invocation.hole_lengths
    )


def fixed_intervals(
    rules: Sequence[Rule], invocations: Sequence[Invocation]
) -> Iterator[tuple[int, int, bytes]]:
    for invocation in invocations:
        rule = rules[invocation.rule_id]
        cursor = invocation.target_start
        for index, segment in enumerate(rule.segments):
            if segment:
                yield cursor, cursor + len(segment), segment
            cursor += len(segment)
            if index < len(invocation.hole_lengths):
                cursor += invocation.hole_lengths[index]


def validate_control(
    rules: Sequence[Rule],
    invocations: Sequence[Invocation],
    wrt_size: int,
    original: bytes | None = None,
) -> None:
    if len(rules) > 0xFFFFFFFF or len(invocations) > 0xFFFFFFFF:
        raise ValueError("control count exceeds u32")
    if len(set(rules)) != len(rules):
        raise ValueError("duplicate rule definitions")
    for rule in rules:
        if len(rule.segments) < 2:
            raise ValueError("a rule needs at least two fixed segments")
        if any(not isinstance(segment, bytes) or not segment for segment in rule.segments):
            raise ValueError("rule fixed segments must be nonempty bytes")

    previous_end = 0
    for invocation in invocations:
        if not 0 <= invocation.rule_id < len(rules):
            raise ValueError("invocation references an unknown rule")
        rule = rules[invocation.rule_id]
        if len(invocation.hole_lengths) != len(rule.segments) - 1:
            raise ValueError("invocation hole arity differs from its rule")
        if any(length < 0 for length in invocation.hole_lengths):
            raise ValueError("hole length is negative")
        end = invocation_end(rule, invocation)
        if not 0 <= previous_end <= invocation.target_start < end <= wrt_size:
            raise ValueError("invocations overlap or exceed the WRT stream")
        previous_end = end

    if original is not None:
        for start, end, segment in fixed_intervals(rules, invocations):
            if original[start:end] != segment:
                raise ValueError("rule segment differs from exact target WRT bytes")


def encode_control(
    rules: Sequence[Rule],
    invocations: Sequence[Invocation],
    wrt_size: int,
) -> bytes:
    rules = tuple(rules)
    invocations = tuple(invocations)
    validate_control(rules, invocations, wrt_size)
    output = bytearray(COUNT.pack(len(rules)))
    for rule in rules:
        output += encode_uleb(len(rule.segments))
        for segment in rule.segments:
            output += encode_uleb(len(segment))
            output += segment
    output += COUNT.pack(len(invocations))
    for invocation in invocations:
        output += encode_uleb(invocation.target_start)
        output += encode_uleb(invocation.rule_id)
        for length in invocation.hole_lengths:
            output += encode_uleb(length)
    return bytes(output)


def decode_control(
    data: bytes, wrt_size: int
) -> tuple[tuple[Rule, ...], tuple[Invocation, ...]]:
    if len(data) < 2 * COUNT.size:
        raise ValueError("control stream is truncated")
    rule_count = COUNT.unpack_from(data)[0]
    cursor = COUNT.size
    rules: list[Rule] = []
    for _ in range(rule_count):
        segment_count, cursor = decode_uleb(data, cursor)
        if segment_count < 2:
            raise ValueError("invalid rule segment count")
        segments: list[bytes] = []
        for _ in range(segment_count):
            length, cursor = decode_uleb(data, cursor)
            end = cursor + length
            if length == 0 or end > len(data):
                raise ValueError("truncated or empty rule segment")
            segments.append(data[cursor:end])
            cursor = end
        rules.append(Rule(tuple(segments)))
    if cursor + COUNT.size > len(data):
        raise ValueError("missing invocation count")
    invocation_count = COUNT.unpack_from(data, cursor)[0]
    cursor += COUNT.size
    invocations: list[Invocation] = []
    for _ in range(invocation_count):
        target_start, cursor = decode_uleb(data, cursor)
        rule_id, cursor = decode_uleb(data, cursor)
        if rule_id >= len(rules):
            raise ValueError("invocation references an unknown rule")
        holes: list[int] = []
        for _ in range(len(rules[rule_id].segments) - 1):
            length, cursor = decode_uleb(data, cursor)
            holes.append(length)
        invocations.append(Invocation(target_start, rule_id, tuple(holes)))
    if cursor != len(data):
        raise ValueError("control stream has trailing bytes")
    result_rules = tuple(rules)
    result_invocations = tuple(invocations)
    validate_control(result_rules, result_invocations, wrt_size)
    return result_rules, result_invocations


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


def literal_byte_indices(
    wrt_size: int,
    rules: Sequence[Rule],
    invocations: Sequence[Invocation],
    generate: bool,
) -> Iterator[int]:
    if not generate:
        yield from range(wrt_size)
        return
    cursor = 0
    for start, end, _segment in fixed_intervals(rules, invocations):
        yield from range(cursor, start)
        cursor = end
    yield from range(cursor, wrt_size)


def encode_literal_payload(
    data: bytes,
    probabilities: Sequence[int],
    rules: Sequence[Rule],
    invocations: Sequence[Invocation],
    generate: bool,
) -> tuple[bytes, int]:
    if len(probabilities) != len(data) * 8:
        raise ValueError("probability rows do not match byte stream")
    validate_control(rules, invocations, len(data), data)
    encoder = RangeEncoder()
    literal_bits = 0
    for byte_index in literal_byte_indices(
        len(data), rules, invocations, generate
    ):
        value = data[byte_index]
        row = byte_index * 8
        for bit_index, shift in enumerate(range(7, -1, -1)):
            encoder.encode(probabilities[row + bit_index], (value >> shift) & 1)
            literal_bits += 1
    return encoder.finish(), literal_bits


def range_encode(data: bytes, probabilities: Sequence[int]) -> bytes:
    payload, _bits = encode_literal_payload(data, probabilities, (), (), False)
    return payload


def build_archive(
    data: bytes,
    probabilities: Sequence[int],
    rules: Sequence[Rule],
    invocations: Sequence[Invocation],
    generate: bool,
) -> bytes:
    rules = tuple(rules)
    invocations = tuple(invocations)
    validate_control(rules, invocations, len(data), data)
    control = encode_control(rules, invocations, len(data))
    payload, literal_bits = encode_literal_payload(
        data, probabilities, rules, invocations, generate
    )
    mode = MODE_GENERATE if generate else MODE_FORCED_LITERAL
    return (
        HEADER.pack(
            MAGIC,
            mode,
            len(data),
            len(probabilities),
            len(control),
            literal_bits,
            len(payload),
        )
        + control
        + payload
    )


def decode_archive(
    archive: bytes, probabilities: Sequence[int]
) -> tuple[bytes, tuple[Rule, ...], tuple[Invocation, ...]]:
    if len(archive) < HEADER.size:
        raise ValueError("grammar archive is truncated")
    magic, mode, wrt_size, rows, control_bytes, literal_bits, payload_bytes = (
        HEADER.unpack_from(archive)
    )
    if magic != MAGIC or mode not in (MODE_FORCED_LITERAL, MODE_GENERATE):
        raise ValueError("invalid grammar archive header")
    if rows != len(probabilities) or rows != wrt_size * 8:
        raise ValueError("archive probability-row contract differs")
    if len(archive) != HEADER.size + control_bytes + payload_bytes:
        raise ValueError("grammar archive length differs from frame")
    control_end = HEADER.size + control_bytes
    rules, invocations = decode_control(archive[HEADER.size:control_end], wrt_size)
    decoder = RangeDecoder(archive[control_end:])
    output = bytearray(wrt_size)
    decoded_literal_bits = 0

    def decode_byte(position: int) -> None:
        nonlocal decoded_literal_bits
        value = 0
        row = position * 8
        for bit_index in range(8):
            value = (value << 1) | decoder.decode(probabilities[row + bit_index])
            decoded_literal_bits += 1
        output[position] = value

    position = 0
    if mode == MODE_FORCED_LITERAL:
        while position < wrt_size:
            decode_byte(position)
            position += 1
    else:
        for invocation in invocations:
            while position < invocation.target_start:
                decode_byte(position)
                position += 1
            rule = rules[invocation.rule_id]
            for index, segment in enumerate(rule.segments):
                output[position : position + len(segment)] = segment
                position += len(segment)
                if index < len(invocation.hole_lengths):
                    hole_end = position + invocation.hole_lengths[index]
                    while position < hole_end:
                        decode_byte(position)
                        position += 1
        while position < wrt_size:
            decode_byte(position)
            position += 1

    if decoded_literal_bits != literal_bits:
        raise ValueError("decoded literal-bit count differs from frame")
    result = bytes(output)
    validate_control(rules, invocations, wrt_size, result)
    if encode_control(rules, invocations, wrt_size) != archive[HEADER.size:control_end]:
        raise ValueError("control stream is not byte-canonical")
    return result, rules, invocations


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
