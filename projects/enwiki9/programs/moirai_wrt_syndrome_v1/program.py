"""MOIRAI v1: exact rateless block reconstruction from syndrome prefixes.

This first constructive candidate deliberately uses tiny 12-bit blocks so the
decoder can exhaustively prove the minimum-energy member of each syndrome
coset.  Its model is learned only from previously reconstructed blocks.
"""

from __future__ import annotations

from collections import Counter
import math
from typing import Iterable


MAGIC = b"MOIRAI1\0"
CAUSAL_MAGIC = b"MOICSL1\0"
BLOCK_BITS = 12
MODEL_ORDER = 8
REVERSE_WEIGHT = 64
WEIGHT_SCALE = 256
TOTAL = 4096
MAX_CODE = (1 << 32) - 1
HALF = 1 << 31
FIRST_QTR = 1 << 30
THIRD_QTR = FIRST_QTR * 3


class BitWriter:
    def __init__(self) -> None:
        self.output = bytearray()
        self.current = 0
        self.used = 0
        self.bits = 0

    def write_bit(self, bit: int) -> None:
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
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.position = 0

    def read_bit(self) -> int:
        if self.position >= len(self.data) * 8:
            self.position += 1
            return 0
        byte = self.data[self.position >> 3]
        bit = (byte >> (7 - (self.position & 7))) & 1
        self.position += 1
        return bit


class ArithmeticEncoder:
    def __init__(self) -> None:
        self.low = 0
        self.high = MAX_CODE
        self.pending = 0
        self.writer = BitWriter()

    def _bit_plus_follow(self, bit: int) -> None:
        self.writer.write_bit(bit)
        while self.pending:
            self.writer.write_bit(1 - bit)
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
                self._bit_plus_follow(0)
            elif self.low >= HALF:
                self._bit_plus_follow(1)
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
        self._bit_plus_follow(0 if self.low < FIRST_QTR else 1)
        bits = self.writer.bits
        return self.writer.finish(), bits


class ArithmeticDecoder:
    def __init__(self, payload: bytes) -> None:
        self.reader = BitReader(payload)
        self.low = 0
        self.high = MAX_CODE
        self.code = 0
        for _ in range(32):
            self.code = ((self.code << 1) | self.reader.read_bit()) & MAX_CODE

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
            self.code = (
                ((self.code << 1) & MAX_CODE) | self.reader.read_bit()
            )
        return bit


def _kt_p1(zeros: int, ones: int) -> int:
    return max(
        1,
        min(
            TOTAL - 1,
            ((2 * ones + 1) * TOTAL) // (2 * (zeros + ones + 1)),
        ),
    )


def _update_pair(pair: list[int], bit: int) -> None:
    pair[bit] += 1
    if pair[0] + pair[1] >= 255:
        pair[0] = (pair[0] + 1) >> 1
        pair[1] = (pair[1] + 1) >> 1


class BlockEnergy:
    def __init__(self) -> None:
        self.forward = [
            [[0, 0] for _ in range(1 << order)]
            for order in range(MODEL_ORDER + 1)
        ]
        self.reverse = [
            [[0, 0] for _ in range(1 << order)]
            for order in range(MODEL_ORDER + 1)
        ]
        self.context = 0
        self.available = 0
        self.loss_cache: dict[tuple[int, int, int], int] = {}

    @staticmethod
    def _lookup(
        tables: list[list[list[int]]], context: int, available: int
    ) -> tuple[int, int]:
        for order in range(min(MODEL_ORDER, available), -1, -1):
            pair = tables[order][context & ((1 << order) - 1)]
            if order == 0 or pair[0] + pair[1] >= 2:
                return pair[0], pair[1]
        raise AssertionError("order-0 context missing")

    def _loss(self, zeros: int, ones: int, bit: int) -> int:
        key = (zeros, ones, bit)
        value = self.loss_cache.get(key)
        if value is None:
            count = ones if bit else zeros
            numerator = 2 * count + 1
            denominator = 2 * (zeros + ones + 1)
            value = int(
                -math.log2(numerator / denominator) * WEIGHT_SCALE + 0.5
            )
            self.loss_cache[key] = value
        return value

    def forward_probabilities(self, value: int, width: int) -> list[int]:
        context = self.context
        available = self.available
        probabilities: list[int] = []
        for position in range(width - 1, -1, -1):
            zeros, ones = self._lookup(self.forward, context, available)
            probabilities.append(_kt_p1(zeros, ones))
            bit = (value >> position) & 1
            context = ((context << 1) | bit) & ((1 << MODEL_ORDER) - 1)
            available = min(MODEL_ORDER, available + 1)
        return probabilities

    def score(self, value: int, width: int, reverse_weight: int) -> int:
        context = self.context
        available = self.available
        forward_score = 0
        for position in range(width - 1, -1, -1):
            bit = (value >> position) & 1
            zeros, ones = self._lookup(self.forward, context, available)
            forward_score += self._loss(zeros, ones, bit)
            context = ((context << 1) | bit) & ((1 << MODEL_ORDER) - 1)
            available = min(MODEL_ORDER, available + 1)

        reverse_score = 0
        context = 0
        available = 0
        for position in range(width):
            bit = (value >> position) & 1
            zeros, ones = self._lookup(self.reverse, context, available)
            reverse_score += self._loss(zeros, ones, bit)
            context = ((context << 1) | bit) & ((1 << MODEL_ORDER) - 1)
            available = min(MODEL_ORDER, available + 1)
        return forward_score * WEIGHT_SCALE + reverse_score * reverse_weight

    @staticmethod
    def _train_direction(
        tables: list[list[list[int]]],
        bits: Iterable[int],
        initial_context: int = 0,
        initial_available: int = 0,
    ) -> tuple[int, int]:
        context = initial_context
        available = initial_available
        for bit in bits:
            for order in range(min(MODEL_ORDER, available) + 1):
                pair = tables[order][context & ((1 << order) - 1)]
                _update_pair(pair, bit)
            context = ((context << 1) | bit) & ((1 << MODEL_ORDER) - 1)
            available = min(MODEL_ORDER, available + 1)
        return context, available

    def update(self, value: int, width: int) -> None:
        forward_bits = [
            (value >> position) & 1
            for position in range(width - 1, -1, -1)
        ]
        self.context, self.available = self._train_direction(
            self.forward,
            forward_bits,
            self.context,
            self.available,
        )
        self._train_direction(
            self.reverse,
            reversed(forward_bits),
        )

    def state_bytes_estimate(self) -> int:
        cells = 2 * sum(1 << order for order in range(MODEL_ORDER + 1))
        return cells * 2


class DepthModel:
    def __init__(self) -> None:
        self.counts: dict[tuple[int, int, int], list[int]] = {}

    @staticmethod
    def code_bits(width: int) -> int:
        return width.bit_length()

    def probability(self, width: int, position: int, prefix: int) -> int:
        pair = self.counts.get((width, position, prefix))
        return _kt_p1(*(pair or [0, 0]))

    def update(self, width: int, position: int, prefix: int, bit: int) -> None:
        pair = self.counts.setdefault((width, position, prefix), [0, 0])
        _update_pair(pair, bit)

    def encode(self, coder: ArithmeticEncoder, width: int, depth: int) -> None:
        prefix = 0
        bits = self.code_bits(width)
        for position in range(bits):
            bit = (depth >> (bits - position - 1)) & 1
            coder.encode(bit, self.probability(width, position, prefix))
            self.update(width, position, prefix, bit)
            prefix = (prefix << 1) | bit

    def decode(self, coder: ArithmeticDecoder, width: int) -> int:
        prefix = 0
        bits = self.code_bits(width)
        for position in range(bits):
            bit = coder.decode(self.probability(width, position, prefix))
            self.update(width, position, prefix, bit)
            prefix = (prefix << 1) | bit
        if prefix > width:
            raise ValueError("invalid syndrome depth")
        return prefix


def _gray(value: int) -> int:
    return value ^ (value >> 1)


def _prefix(value: int, width: int, depth: int) -> int:
    return 0 if depth == 0 else _gray(value) >> (width - depth)


def _lcp(left: int, right: int, width: int) -> int:
    difference = _gray(left) ^ _gray(right)
    return width if difference == 0 else width - difference.bit_length()


def _rank_key(
    model: BlockEnergy, value: int, width: int, reverse_weight: int
) -> tuple[int, int]:
    return model.score(value, width, reverse_weight), value


def _minimum_depth(
    model: BlockEnergy, truth: int, width: int, reverse_weight: int
) -> tuple[int, int]:
    truth_key = _rank_key(model, truth, width, reverse_weight)
    maximum_lcp = -1
    evaluations = 0
    for candidate in range(1 << width):
        evaluations += 1
        if candidate == truth:
            continue
        if _rank_key(model, candidate, width, reverse_weight) < truth_key:
            maximum_lcp = max(maximum_lcp, _lcp(truth, candidate, width))
    return min(width, maximum_lcp + 1), evaluations


def _decode_coset(
    model: BlockEnergy,
    width: int,
    depth: int,
    syndrome: int,
    reverse_weight: int,
) -> tuple[int, int]:
    best_value = 0
    best_key: tuple[int, int] | None = None
    evaluations = 0
    for candidate in range(1 << width):
        if _prefix(candidate, width, depth) != syndrome:
            continue
        evaluations += 1
        key = _rank_key(model, candidate, width, reverse_weight)
        if best_key is None or key < best_key:
            best_key = key
            best_value = candidate
    if best_key is None:
        raise ValueError("empty syndrome coset")
    return best_value, evaluations


def _chunks(data: bytes) -> Iterable[tuple[int, int]]:
    buffer = 0
    available = 0
    for byte in data:
        buffer = (buffer << 8) | byte
        available += 8
        while available >= BLOCK_BITS:
            available -= BLOCK_BITS
            yield (buffer >> available) & ((1 << BLOCK_BITS) - 1), BLOCK_BITS
            buffer &= (1 << available) - 1
    if available:
        yield buffer, available


def _block_widths(byte_length: int) -> Iterable[int]:
    bit_length = byte_length * 8
    full, tail = divmod(bit_length, BLOCK_BITS)
    for _ in range(full):
        yield BLOCK_BITS
    if tail:
        yield tail


def _pack_values(values: Iterable[tuple[int, int]], byte_length: int) -> bytes:
    writer = BitWriter()
    for value, width in values:
        for position in range(width - 1, -1, -1):
            writer.write_bit((value >> position) & 1)
    output = writer.finish()
    if len(output) != byte_length:
        raise ValueError("decoded bit length mismatch")
    return output


def _encode_archive(
    data: bytes, reverse_weight: int
) -> tuple[bytes, dict[str, object]]:
    coder = ArithmeticEncoder()
    depths = DepthModel()
    model = BlockEnergy()
    histogram: Counter[int] = Counter()
    evaluations = 0
    blocks = 0
    for value, width in _chunks(data):
        depth, work = _minimum_depth(model, value, width, reverse_weight)
        evaluations += work
        histogram[depth] += 1
        blocks += 1
        depths.encode(coder, width, depth)
        syndrome = _prefix(value, width, depth)
        for position in range(depth - 1, -1, -1):
            coder.encode((syndrome >> position) & 1, TOTAL // 2)
        model.update(value, width)
    payload, payload_bits = coder.finish()
    header = MAGIC + len(data).to_bytes(8, "big") + bytes((reverse_weight,))
    stats: dict[str, object] = {
        "archive_bytes": len(header) + len(payload),
        "header_bytes": len(header),
        "payload_bytes": len(payload),
        "payload_bits_before_padding": payload_bits,
        "blocks": blocks,
        "depth_histogram": dict(sorted(histogram.items())),
        "mean_depth": (
            sum(depth * count for depth, count in histogram.items()) / blocks
            if blocks
            else 0.0
        ),
        "full_depth_blocks": sum(
            count
            for depth, count in histogram.items()
            if depth == BLOCK_BITS
        ),
        "candidate_evaluations": evaluations,
        "model_state_bytes_estimate": model.state_bytes_estimate(),
        "reverse_weight": reverse_weight,
    }
    return header + payload, stats


def _decode_archive(archive: bytes) -> tuple[bytes, dict[str, int]]:
    if len(archive) < 17 or archive[:8] != MAGIC:
        raise ValueError("invalid MOIRAI archive")
    byte_length = int.from_bytes(archive[8:16], "big")
    reverse_weight = archive[16]
    coder = ArithmeticDecoder(archive[17:])
    depths = DepthModel()
    model = BlockEnergy()
    output: list[tuple[int, int]] = []
    evaluations = 0
    for width in _block_widths(byte_length):
        depth = depths.decode(coder, width)
        syndrome = 0
        for _ in range(depth):
            syndrome = (syndrome << 1) | coder.decode(TOTAL // 2)
        value, work = _decode_coset(
            model, width, depth, syndrome, reverse_weight
        )
        evaluations += work
        output.append((value, width))
        model.update(value, width)
    return _pack_values(output, byte_length), {
        "candidate_evaluations": evaluations,
        "reverse_weight": reverse_weight,
    }


def _encode_causal(data: bytes) -> tuple[bytes, dict[str, int]]:
    coder = ArithmeticEncoder()
    model = BlockEnergy()
    blocks = 0
    for value, width in _chunks(data):
        probabilities = model.forward_probabilities(value, width)
        for index, position in enumerate(range(width - 1, -1, -1)):
            coder.encode((value >> position) & 1, probabilities[index])
        model.update(value, width)
        blocks += 1
    payload, payload_bits = coder.finish()
    header = CAUSAL_MAGIC + len(data).to_bytes(8, "big")
    return header + payload, {
        "archive_bytes": len(header) + len(payload),
        "header_bytes": len(header),
        "payload_bytes": len(payload),
        "payload_bits_before_padding": payload_bits,
        "blocks": blocks,
    }


def _decode_causal(archive: bytes) -> bytes:
    if len(archive) < 16 or archive[:8] != CAUSAL_MAGIC:
        raise ValueError("invalid causal archive")
    byte_length = int.from_bytes(archive[8:16], "big")
    coder = ArithmeticDecoder(archive[16:])
    model = BlockEnergy()
    output: list[tuple[int, int]] = []
    for width in _block_widths(byte_length):
        value = 0
        context = model.context
        available = model.available
        for _ in range(width):
            zeros, ones = model._lookup(model.forward, context, available)
            bit = coder.decode(_kt_p1(zeros, ones))
            value = (value << 1) | bit
            context = ((context << 1) | bit) & ((1 << MODEL_ORDER) - 1)
            available = min(MODEL_ORDER, available + 1)
        output.append((value, width))
        model.update(value, width)
    return _pack_values(output, byte_length)


def analyze(data: bytes) -> dict[str, object]:
    forward_archive, forward_stats = _encode_archive(data, 0)
    reverse_archive, reverse_stats = _encode_archive(data, REVERSE_WEIGHT)
    causal_archive, causal_stats = _encode_causal(data)
    forward_decoded, forward_decode_stats = _decode_archive(forward_archive)
    reverse_decoded, reverse_decode_stats = _decode_archive(reverse_archive)
    causal_decoded = _decode_causal(causal_archive)
    return {
        "input_bytes": len(data),
        "literal_bytes": len(data),
        "causal": causal_stats,
        "syndrome_forward": forward_stats,
        "syndrome_bidirectional": reverse_stats,
        "roundtrip": {
            "causal": causal_decoded == data,
            "syndrome_forward": forward_decoded == data,
            "syndrome_bidirectional": reverse_decoded == data,
        },
        "decode_candidate_evaluations": {
            "syndrome_forward": forward_decode_stats["candidate_evaluations"],
            "syndrome_bidirectional": reverse_decode_stats[
                "candidate_evaluations"
            ],
        },
        "deltas": {
            "bidirectional_minus_forward_bytes": len(reverse_archive)
            - len(forward_archive),
            "bidirectional_minus_causal_bytes": len(reverse_archive)
            - len(causal_archive),
            "bidirectional_minus_literal_bytes": len(reverse_archive) - len(data),
        },
    }


def compress(data: bytes) -> bytes:
    return _encode_archive(data, REVERSE_WEIGHT)[0]


def decompress(archive: bytes) -> bytes:
    return _decode_archive(archive)[0]
