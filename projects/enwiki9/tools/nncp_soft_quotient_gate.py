#!/usr/bin/env python3
"""Evaluate a quantized causal soft quotient against a hard-label control."""

from __future__ import annotations

import argparse
import bisect
import hashlib
import heapq
import json
import lzma
import math
import struct
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


TRACE_HEADER = struct.Struct("<8sQ")
TRACE_ROW = struct.Struct("<QQQQIHHI")
TRACE_MAGIC = b"NNTCHD2\0"
MODEL_MAGIC = b"QSPM1\0"
ARCHIVE_MAGIC = b"QSPA1\0"
STATE_BITS = 32
FULL = 1 << STATE_BITS
HALF = FULL >> 1
QUARTER = HALF >> 1
THREE_QUARTERS = QUARTER * 3
MASK = FULL - 1


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_symbols(path: Path) -> list[int]:
    raw = path.read_bytes()
    if len(raw) % 2:
        raise ValueError("u16be symbol stream has odd byte length")
    return [value[0] for value in struct.iter_unpack(">H", raw)]


def load_trace(path: Path) -> tuple[list[int], list[tuple[float, ...]]]:
    raw = path.read_bytes()
    if len(raw) < TRACE_HEADER.size:
        raise ValueError("truncated teacher trace")
    magic, count = TRACE_HEADER.unpack_from(raw, 0)
    if magic != TRACE_MAGIC or count <= 0:
        raise ValueError("invalid teacher trace")
    symbols: list[int] = []
    distributions: list[tuple[float, ...]] = []
    offset = TRACE_HEADER.size
    prior_after: int | None = None
    for index in range(count):
        if offset + TRACE_ROW.size > len(raw):
            raise ValueError("truncated teacher row")
        fixed = TRACE_ROW.unpack_from(raw, offset)
        offset += TRACE_ROW.size
        original, execution, before, after, _local, _stream, symbol, vocab = fixed
        if original != index or execution != index:
            raise ValueError("trace is not a sequential single stream")
        if prior_after is not None and before != prior_after:
            raise ValueError("coder counts are discontinuous")
        if after < before:
            raise ValueError("coder count decreased")
        size = 4 * vocab
        if offset + size > len(raw):
            raise ValueError("truncated teacher distribution")
        distribution = struct.unpack_from(f"<{vocab}f", raw, offset)
        offset += size
        if not all(math.isfinite(p) and p > 0 for p in distribution):
            raise ValueError("invalid teacher probability")
        if abs(math.fsum(distribution) - 1.0) > 2e-5:
            raise ValueError("teacher distribution is not normalized")
        symbols.append(symbol)
        distributions.append(distribution)
        prior_after = after
    if offset != len(raw):
        raise ValueError("trailing teacher trace bytes")
    return symbols, distributions


def quantize_mass(mass: list[float], total: int) -> tuple[int, ...]:
    vocab = len(mass)
    if total < vocab:
        raise ValueError("probability total is smaller than vocabulary")
    counts = [1] * vocab
    heap: list[tuple[float, int]] = []
    for symbol, weight in enumerate(mass):
        gain = weight * math.log(2.0)
        heapq.heappush(heap, (-gain, symbol))
    for _ in range(total - vocab):
        _negative_gain, symbol = heapq.heappop(heap)
        counts[symbol] += 1
        count = counts[symbol]
        gain = mass[symbol] * math.log((count + 1) / count)
        heapq.heappush(heap, (-gain, symbol))
    if sum(counts) != total or min(counts) < 1:
        raise AssertionError("invalid quantized table")
    return tuple(counts)


def context_key(symbols: list[int], index: int, depth: int) -> tuple[int, ...]:
    if depth == 0 or index < depth:
        return ()
    return tuple(symbols[index - depth : index])


def train_models(
    symbols: list[int],
    distributions: list[tuple[float, ...]],
    train_rows: int,
    depth: int,
    min_count: int,
    total: int,
) -> tuple[dict[tuple[int, ...], tuple[int, ...]], dict[tuple[int, ...], tuple[int, ...]]]:
    vocab = len(distributions[0])
    occurrences: Counter[tuple[int, ...]] = Counter()
    for index in range(train_rows):
        key = context_key(symbols, index, depth)
        if key:
            occurrences[key] += 1
    retained = {key for key, count in occurrences.items() if count >= min_count}
    soft: dict[tuple[int, ...], list[float]] = {
        (): [0.0] * vocab,
        **{key: [0.0] * vocab for key in retained},
    }
    hard: dict[tuple[int, ...], list[float]] = {
        (): [0.0] * vocab,
        **{key: [0.0] * vocab for key in retained},
    }
    for index in range(train_rows):
        distribution = distributions[index]
        symbol = symbols[index]
        keys = [()]
        key = context_key(symbols, index, depth)
        if key in retained:
            keys.append(key)
        for active in keys:
            for candidate, probability in enumerate(distribution):
                soft[active][candidate] += probability
            hard[active][symbol] += 1.0
    soft_model = {key: quantize_mass(mass, total) for key, mass in soft.items()}
    hard_model = {key: quantize_mass(mass, total) for key, mass in hard.items()}
    if soft_model.keys() != hard_model.keys():
        raise AssertionError("matched models use different context keys")
    return soft_model, hard_model


def cumulative(counts: tuple[int, ...]) -> list[int]:
    result = [0]
    for count in counts:
        result.append(result[-1] + count)
    return result


def select_counts(
    model: dict[tuple[int, ...], tuple[int, ...]],
    history: list[int],
    depth: int,
) -> tuple[int, ...]:
    key = tuple(history[-depth:]) if depth and len(history) >= depth else ()
    return model.get(key, model[()])


class BitWriter:
    def __init__(self) -> None:
        self.bits: list[int] = []

    def write(self, bit: int) -> None:
        self.bits.append(bit)

    def finish(self) -> bytes:
        padding = (-len(self.bits)) % 8
        bits = self.bits + [0] * padding
        output = bytearray()
        for offset in range(0, len(bits), 8):
            value = 0
            for bit in bits[offset : offset + 8]:
                value = (value << 1) | bit
            output.append(value)
        return bytes(output)


class BitReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.index = 0

    def read(self) -> int:
        if self.index >= 8 * len(self.data):
            self.index += 1
            return 0
        byte = self.data[self.index >> 3]
        bit = (byte >> (7 - (self.index & 7))) & 1
        self.index += 1
        return bit


def encode(
    symbols: list[int],
    model: dict[tuple[int, ...], tuple[int, ...]],
    depth: int,
    total: int,
) -> tuple[bytes, int]:
    writer = BitWriter()
    low, high, pending = 0, MASK, 0

    def emit(bit: int) -> None:
        nonlocal pending
        writer.write(bit)
        for _ in range(pending):
            writer.write(1 - bit)
        pending = 0

    history: list[int] = []
    for symbol in symbols:
        counts = select_counts(model, history, depth)
        cumul = cumulative(counts)
        width = high - low + 1
        high = low + (width * cumul[symbol + 1] // total) - 1
        low = low + (width * cumul[symbol] // total)
        while True:
            if high < HALF:
                emit(0)
            elif low >= HALF:
                emit(1)
                low -= HALF
                high -= HALF
            elif low >= QUARTER and high < THREE_QUARTERS:
                pending += 1
                low -= QUARTER
                high -= QUARTER
            else:
                break
            low = (low << 1) & MASK
            high = ((high << 1) & MASK) | 1
        history.append(symbol)
    pending += 1
    emit(0 if low < QUARTER else 1)
    bit_count = len(writer.bits)
    return writer.finish(), bit_count


def decode(
    payload: bytes,
    length: int,
    model: dict[tuple[int, ...], tuple[int, ...]],
    depth: int,
    total: int,
) -> list[int]:
    reader = BitReader(payload)
    low, high, code = 0, MASK, 0
    for _ in range(STATE_BITS):
        code = ((code << 1) | reader.read()) & MASK
    output: list[int] = []
    for _ in range(length):
        counts = select_counts(model, output, depth)
        cumul = cumulative(counts)
        width = high - low + 1
        value = ((code - low + 1) * total - 1) // width
        symbol = bisect.bisect_right(cumul, value) - 1
        if symbol < 0 or symbol >= len(counts):
            raise ValueError("arithmetic decoder selected invalid symbol")
        high = low + (width * cumul[symbol + 1] // total) - 1
        low = low + (width * cumul[symbol] // total)
        while True:
            if high < HALF:
                pass
            elif low >= HALF:
                low -= HALF
                high -= HALF
                code -= HALF
            elif low >= QUARTER and high < THREE_QUARTERS:
                low -= QUARTER
                high -= QUARTER
                code -= QUARTER
            else:
                break
            low = (low << 1) & MASK
            high = ((high << 1) & MASK) | 1
            code = ((code << 1) & MASK) | reader.read()
        output.append(symbol)
    return output


def serialize_model(
    model: dict[tuple[int, ...], tuple[int, ...]],
    depth: int,
    total: int,
) -> bytes:
    vocab = len(model[()])
    keys = sorted(key for key in model if key)
    output = bytearray(MODEL_MAGIC)
    output += struct.pack("<HIBI", vocab, total, depth, len(keys))
    output += struct.pack(f"<{vocab}H", *model[()])
    for key in keys:
        if len(key) != depth:
            raise ValueError("invalid context key depth")
        output += struct.pack(f"<{depth}H", *key)
        output += struct.pack(f"<{vocab}H", *model[key])
    return bytes(output)


def evaluate(
    name: str,
    symbols: list[int],
    model: dict[tuple[int, ...], tuple[int, ...]],
    depth: int,
    total: int,
    output_dir: Path,
) -> dict[str, object]:
    payload, bit_count = encode(symbols, model, depth, total)
    decoded = decode(payload, len(symbols), model, depth, total)
    if decoded != symbols:
        raise ValueError(f"{name} arithmetic roundtrip failed")
    model_raw = serialize_model(model, depth, total)
    model_lzma = lzma.compress(
        model_raw,
        format=lzma.FORMAT_ALONE,
        preset=9 | lzma.PRESET_EXTREME,
    )
    archive = ARCHIVE_MAGIC + struct.pack("<Q", len(symbols)) + payload
    (output_dir / f"{name}.model.lzma").write_bytes(model_lzma)
    (output_dir / f"{name}.archive").write_bytes(archive)
    ideal_bits = 0.0
    history: list[int] = []
    for symbol in symbols:
        counts = select_counts(model, history, depth)
        ideal_bits -= math.log2(counts[symbol] / total)
        history.append(symbol)
    return {
        "roundtrip_ok": True,
        "context_tables": len(model),
        "model_raw_bytes": len(model_raw),
        "model_lzma_bytes": len(model_lzma),
        "model_lzma_sha256": sha256(model_lzma),
        "arithmetic_bits": bit_count,
        "archive_bytes": len(archive),
        "archive_sha256": sha256(archive),
        "ideal_bits": ideal_bits,
        "two_part_bytes": len(model_lzma) + len(archive),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--symbols", type=Path, required=True)
    parser.add_argument("--train-rows", type=int, required=True)
    parser.add_argument("--depths", default="0,1,2")
    parser.add_argument("--min-count", type=int, default=2)
    parser.add_argument("--total", type=int, default=4096)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    args = parser.parse_args()

    symbols = load_symbols(args.symbols)
    trace_symbols, distributions = load_trace(args.trace)
    if trace_symbols != symbols:
        raise ValueError("trace symbols do not match supplied symbol stream")
    if not 0 < args.train_rows < len(symbols):
        raise ValueError("invalid chronological split")
    vocabularies = {len(distribution) for distribution in distributions}
    if len(vocabularies) != 1:
        raise ValueError("varying teacher vocabulary is unsupported")
    vocab = next(iter(vocabularies))
    if max(symbols) >= vocab:
        raise ValueError("symbol exceeds teacher vocabulary")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    holdout = symbols[args.train_rows :]
    teacher_bits = sum(
        -math.log2(distributions[index][symbols[index]])
        for index in range(args.train_rows, len(symbols))
    )
    rows: list[dict[str, object]] = []
    for depth in [int(value) for value in args.depths.split(",")]:
        soft, hard = train_models(
            symbols,
            distributions,
            args.train_rows,
            depth,
            args.min_count,
            args.total,
        )
        prefix = f"depth{depth}"
        soft_result = evaluate(
            f"{prefix}.soft", holdout, soft, depth, args.total, args.output_dir
        )
        hard_result = evaluate(
            f"{prefix}.hard", holdout, hard, depth, args.total, args.output_dir
        )
        rows.append(
            {
                "depth": depth,
                "soft": soft_result,
                "hard": hard_result,
                "soft_minus_hard_payload_bytes": (
                    int(soft_result["archive_bytes"])
                    - int(hard_result["archive_bytes"])
                ),
                "soft_minus_hard_two_part_bytes": (
                    int(soft_result["two_part_bytes"])
                    - int(hard_result["two_part_bytes"])
                ),
            }
        )
    soft_two_part_win = any(
        int(row["soft_minus_hard_two_part_bytes"]) < 0 for row in rows
    )
    status = (
        "mechanism_verified_candidate_positive"
        if soft_two_part_win
        else "terminal_startup_negative"
    )
    next_gate = (
        "Freeze the smallest positive depth and require transfer on a disjoint "
        "population before native integration."
        if soft_two_part_win
        else "Retire the suffix-centroid representation. Preserve the verified "
        "teacher trace for a student with a genuinely different causal state."
    )
    decision = {
        "schema": "nncp_quantized_soft_quotient_gate_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "score_credit_bytes": 0,
        "trace": str(args.trace.resolve()),
        "trace_sha256": sha256(args.trace.read_bytes()),
        "symbols": str(args.symbols.resolve()),
        "symbols_sha256": sha256(args.symbols.read_bytes()),
        "rows": len(symbols),
        "train_rows": args.train_rows,
        "holdout_rows": len(holdout),
        "vocabulary": vocab,
        "probability_total": args.total,
        "minimum_context_count": args.min_count,
        "teacher_holdout_ideal_bits_oracle": teacher_bits,
        "soft_two_part_win": soft_two_part_win,
        "evaluations": rows,
        "claim_boundary": (
            "Exact bounded same-domain student mechanics only. The teacher is "
            "an oracle, the scope is startup-sized, and no native full-corpus "
            "score, package, runtime, or Hutter credit is established."
        ),
        "next_gate": next_gate,
    }
    args.decision.parent.mkdir(parents=True, exist_ok=True)
    args.decision.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
