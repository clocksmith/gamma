"""Exact zero-cost residual primitives for the LOGOS lexical-frame ceiling.

The Q0 frame descriptions are deliberately supplied out of band.  This module
therefore proves only an information ceiling: fixed anchor bytes are generated
without consuming arithmetic truth bits, while literal-hole bytes are decoded
against their original receipt-bound P1 rows.  A passing Q0 must earn a
separate finite paid control format.
"""

from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Iterator, Sequence
import zlib


MASK32 = (1 << 32) - 1
FALLBACK_MAGIC = b"M2LFC0\0\0"
FALLBACK_HEADER = struct.Struct("<8sQ")


@dataclass(frozen=True)
class FrameRule:
    left: bytes
    right: bytes


@dataclass(frozen=True)
class FrameInvocation:
    target_start: int
    hole_length: int
    rule_id: int


def invocation_end(rule: FrameRule, invocation: FrameInvocation) -> int:
    return (
        invocation.target_start
        + len(rule.left)
        + invocation.hole_length
        + len(rule.right)
    )


def fixed_intervals(
    rules: Sequence[FrameRule],
    invocations: Sequence[FrameInvocation],
) -> Iterator[tuple[int, int, bytes]]:
    for invocation in invocations:
        rule = rules[invocation.rule_id]
        left_start = invocation.target_start
        left_end = left_start + len(rule.left)
        right_start = left_end + invocation.hole_length
        right_end = right_start + len(rule.right)
        yield left_start, left_end, rule.left
        yield right_start, right_end, rule.right


def validate_plan(
    rules: Sequence[FrameRule],
    invocations: Sequence[FrameInvocation],
    wrt_size: int,
    original: bytes | None = None,
) -> None:
    if len(set(rules)) != len(rules):
        raise ValueError("duplicate frame rules")
    if any(not rule.left or not rule.right for rule in rules):
        raise ValueError("frame anchors must be nonempty")
    previous_end = 0
    for invocation in invocations:
        if not 0 <= invocation.rule_id < len(rules):
            raise ValueError("invocation references an unknown rule")
        if invocation.hole_length < 0:
            raise ValueError("frame hole length is negative")
        end = invocation_end(rules[invocation.rule_id], invocation)
        if not 0 <= previous_end <= invocation.target_start < end <= wrt_size:
            raise ValueError("frame invocations overlap or exceed the WRT stream")
        previous_end = end
    if original is not None:
        for start, end, anchor in fixed_intervals(rules, invocations):
            if original[start:end] != anchor:
                raise ValueError("frame anchor differs from target WRT bytes")


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
    rules: Sequence[FrameRule],
    invocations: Sequence[FrameInvocation],
) -> Iterator[int]:
    cursor = 0
    for start, end, _anchor in fixed_intervals(rules, invocations):
        yield from range(cursor, start)
        cursor = end
    yield from range(cursor, wrt_size)


def encode_residual(
    data: bytes,
    probabilities: Sequence[int],
    rules: Sequence[FrameRule],
    invocations: Sequence[FrameInvocation],
) -> tuple[bytes, int]:
    if len(probabilities) != len(data) * 8:
        raise ValueError("probability rows do not match byte stream")
    validate_plan(rules, invocations, len(data), data)
    encoder = RangeEncoder()
    literal_bits = 0
    for byte_index in literal_byte_indices(len(data), rules, invocations):
        value = data[byte_index]
        row = byte_index * 8
        for bit_index, shift in enumerate(range(7, -1, -1)):
            encoder.encode(probabilities[row + bit_index], (value >> shift) & 1)
            literal_bits += 1
    return encoder.finish(), literal_bits


def decode_residual(
    wrt_size: int,
    probabilities: Sequence[int],
    payload: bytes,
    rules: Sequence[FrameRule],
    invocations: Sequence[FrameInvocation],
) -> tuple[bytes, int]:
    if len(probabilities) != wrt_size * 8:
        raise ValueError("probability rows do not match byte stream")
    validate_plan(rules, invocations, wrt_size)
    decoder = RangeDecoder(payload)
    output = bytearray(wrt_size)
    literal_bits = 0

    def decode_byte(position: int) -> None:
        nonlocal literal_bits
        value = 0
        row = position * 8
        for bit_index in range(8):
            value = (value << 1) | decoder.decode(probabilities[row + bit_index])
            literal_bits += 1
        output[position] = value

    position = 0
    for invocation in invocations:
        while position < invocation.target_start:
            decode_byte(position)
            position += 1
        rule = rules[invocation.rule_id]
        output[position : position + len(rule.left)] = rule.left
        position += len(rule.left)
        hole_end = position + invocation.hole_length
        while position < hole_end:
            decode_byte(position)
            position += 1
        output[position : position + len(rule.right)] = rule.right
        position += len(rule.right)
    while position < wrt_size:
        decode_byte(position)
        position += 1
    result = bytes(output)
    validate_plan(rules, invocations, wrt_size, result)
    return result, literal_bits


def compress(data: bytes) -> bytes:
    """Deterministic fallback; the Q0 evidence uses ``encode_residual``."""

    payload = zlib.compress(data, level=9)
    return FALLBACK_HEADER.pack(FALLBACK_MAGIC, len(data)) + payload


def decompress(archive: bytes) -> bytes:
    if len(archive) < FALLBACK_HEADER.size:
        raise ValueError("fallback archive is truncated")
    magic, length = FALLBACK_HEADER.unpack_from(archive)
    if magic != FALLBACK_MAGIC:
        raise ValueError("invalid fallback archive")
    data = zlib.decompress(archive[FALLBACK_HEADER.size :])
    if len(data) != length:
        raise ValueError("fallback decoded length differs")
    return data
