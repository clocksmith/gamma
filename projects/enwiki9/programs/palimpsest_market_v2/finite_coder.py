#!/usr/bin/env python3
"""Exact finite binary arithmetic coder used by PALIMPSEST shadow arms."""

from __future__ import annotations

import hashlib
import struct
from typing import Iterable, Mapping

from core import ARMS, CODED_ARMS, PROBABILITY_SCALE


MAGIC = b"PMKTAR2\0"
STATE_BITS = 32
FULL = 1 << STATE_BITS
MASK = FULL - 1
HALF = FULL >> 1
QUARTER = HALF >> 1
THREE_QUARTERS = QUARTER * 3


class _BitWriter:
    def __init__(self) -> None:
        self.bits: list[int] = []

    def write(self, value: int) -> None:
        if value not in (0, 1):
            raise ValueError("arithmetic output is not a bit")
        self.bits.append(value)

    def bytes(self) -> bytes:
        result = bytearray((len(self.bits) + 7) // 8)
        for index, value in enumerate(self.bits):
            result[index // 8] |= value << (7 - index % 8)
        return bytes(result)


class ArithmeticEncoder:
    def __init__(self) -> None:
        self.low = 0
        self.high = MASK
        self.pending = 0
        self.writer = _BitWriter()
        self.finished = False

    def _emit(self, bit: int) -> None:
        self.writer.write(bit)
        for _ in range(self.pending):
            self.writer.write(bit ^ 1)
        self.pending = 0

    def write(self, probability_one: int, truth_bit: int) -> None:
        if self.finished:
            raise ValueError("arithmetic encoder is already terminated")
        if not 0 < probability_one < PROBABILITY_SCALE:
            raise ValueError("invalid Q16 probability")
        if truth_bit not in (0, 1):
            raise ValueError("truth is not a bit")
        width = self.high - self.low + 1
        zero_count = PROBABILITY_SCALE - probability_one
        split = self.low + (width * zero_count // PROBABILITY_SCALE) - 1
        if not self.low <= split < self.high:
            raise AssertionError("finite arithmetic interval collapsed")
        if truth_bit:
            self.low = split + 1
        else:
            self.high = split
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
            self.low = (self.low << 1) & MASK
            self.high = ((self.high << 1) & MASK) | 1

    def finish(self) -> bytes:
        if not self.finished:
            self.pending += 1
            self._emit(0 if self.low < QUARTER else 1)
            self.finished = True
        return self.writer.bytes()


class _BitReader:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.position = 0

    def read(self) -> int:
        if self.position >= len(self.payload) * 8:
            self.position += 1
            return 0
        result = (
            self.payload[self.position // 8] >> (7 - self.position % 8)
        ) & 1
        self.position += 1
        return result


class ArithmeticDecoder:
    def __init__(self, payload: bytes):
        self.low = 0
        self.high = MASK
        self.reader = _BitReader(payload)
        self.code = 0
        for _ in range(STATE_BITS):
            self.code = ((self.code << 1) & MASK) | self.reader.read()

    def read(self, probability_one: int) -> int:
        if not 0 < probability_one < PROBABILITY_SCALE:
            raise ValueError("invalid Q16 probability")
        width = self.high - self.low + 1
        zero_count = PROBABILITY_SCALE - probability_one
        split = self.low + (width * zero_count // PROBABILITY_SCALE) - 1
        if self.code <= split:
            truth = 0
            self.high = split
        else:
            truth = 1
            self.low = split + 1
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
            self.low = (self.low << 1) & MASK
            self.high = ((self.high << 1) & MASK) | 1
            self.code = ((self.code << 1) & MASK) | self.reader.read()
        return truth


def frame(bit_count: int, coder_payload: bytes) -> bytes:
    if bit_count < 0:
        raise ValueError("negative truth-bit count")
    return MAGIC + struct.pack("<Q", bit_count) + coder_payload


def parse_frame(archive: bytes) -> tuple[int, bytes]:
    if len(archive) < 16 or archive[:8] != MAGIC:
        raise ValueError("invalid PALIMPSEST finite archive")
    return struct.unpack_from("<Q", archive, 8)[0], archive[16:]


def encode_schedule(probabilities: Iterable[int], truths: Iterable[int]) -> bytes:
    encoder = ArithmeticEncoder()
    count = 0
    for probability, truth in zip(probabilities, truths, strict=True):
        encoder.write(probability, truth)
        count += 1
    return frame(count, encoder.finish())


def decode_schedule(archive: bytes, probabilities: Iterable[int]) -> tuple[int, ...]:
    bit_count, payload = parse_frame(archive)
    iterator = iter(probabilities)
    decoder = ArithmeticDecoder(payload)
    truths = []
    for _ in range(bit_count):
        try:
            probability = next(iterator)
        except StopIteration as error:
            raise ValueError("probability schedule ended before archive") from error
        truths.append(decoder.read(probability))
    try:
        next(iterator)
    except StopIteration:
        return tuple(truths)
    raise ValueError("probability schedule extends beyond archive")


class CounterfactualReplay:
    """Independent finite coders over one shared pretruth row stream."""

    def __init__(self) -> None:
        self.encoders = {arm: ArithmeticEncoder() for arm in CODED_ARMS}
        self.probabilities = {arm: [] for arm in CODED_ARMS}
        self.truths: list[int] = []
        self.interval_digest = {arm: hashlib.sha256() for arm in CODED_ARMS}

    def observe_byte(
        self, rows: Mapping[str, tuple[int, ...]], truth: int
    ) -> None:
        schedules = {
            "P": rows["P"],
            "K": rows["K"],
            **{arm: rows[f"mixture_{arm}"] for arm in ARMS},
        }
        for bit_index in range(8):
            truth_bit = (truth >> (7 - bit_index)) & 1
            self.truths.append(truth_bit)
            for arm in CODED_ARMS:
                probability = schedules[arm][bit_index]
                encoder = self.encoders[arm]
                encoder.write(probability, truth_bit)
                self.probabilities[arm].append(probability)
                self.interval_digest[arm].update(
                    struct.pack(
                        "<HBIIQ",
                        probability,
                        truth_bit,
                        encoder.low,
                        encoder.high,
                        encoder.pending,
                    )
                )

    def finish(self) -> dict[str, object]:
        archives = {
            arm: frame(len(self.truths), encoder.finish())
            for arm, encoder in self.encoders.items()
        }
        roundtrip = {
            arm: decode_schedule(archives[arm], self.probabilities[arm])
            == tuple(self.truths)
            for arm in CODED_ARMS
        }
        return {
            "archives": archives,
            "archive_bytes": {arm: len(value) for arm, value in archives.items()},
            "archive_sha256": {
                arm: hashlib.sha256(value).hexdigest()
                for arm, value in archives.items()
            },
            "interval_sha256": {
                arm: digest.hexdigest()
                for arm, digest in self.interval_digest.items()
            },
            "roundtrip": roundtrip,
            "bit_count": len(self.truths),
        }
