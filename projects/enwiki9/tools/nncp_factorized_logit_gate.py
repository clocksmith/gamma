#!/usr/bin/env python3
"""Test a factored int8 logit student against a matched hard control."""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import lzma
import math
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from projects.enwiki9.tools.nncp_soft_quotient_gate import (  # noqa: E402
    BitReader,
    BitWriter,
    HALF,
    MASK,
    QUARTER,
    STATE_BITS,
    THREE_QUARTERS,
    cumulative,
    load_symbols,
    load_trace,
)


MODEL_MAGIC = b"FLPM1\0"
ARCHIVE_MAGIC = b"FLPA1\0"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def feature_ids(
    history: list[int], lags: tuple[int, ...], buckets: int
) -> tuple[int, ...]:
    result = [0]
    width = buckets + 1
    for slot, lag in enumerate(lags):
        bucket = history[-lag] % buckets if len(history) >= lag else buckets
        result.append(1 + slot * width + bucket)
    return tuple(result)


def softmax(logits: list[float]) -> list[float]:
    maximum = max(logits)
    values = [math.exp(value - maximum) for value in logits]
    total = math.fsum(values)
    return [value / total for value in values]


def train(
    symbols: list[int],
    targets: list[tuple[float, ...]] | None,
    train_rows: int,
    lags: tuple[int, ...],
    buckets: int,
    epochs: int,
    learning_rate: float,
    vocab: int,
) -> list[list[float]]:
    table_count = 1 + len(lags) * (buckets + 1)
    weights = [[0.0] * vocab for _ in range(table_count)]
    active_rows = [
        feature_ids(symbols[:index], lags, buckets) for index in range(train_rows)
    ]
    for _epoch in range(epochs):
        for index, active in enumerate(active_rows):
            logits = [
                math.fsum(weights[feature][symbol] for feature in active)
                for symbol in range(vocab)
            ]
            predicted = softmax(logits)
            scale = learning_rate / len(active)
            true_symbol = symbols[index]
            for symbol in range(vocab):
                target = (
                    targets[index][symbol]
                    if targets is not None
                    else (1.0 if symbol == true_symbol else 0.0)
                )
                update = scale * (target - predicted[symbol])
                for feature in active:
                    weights[feature][symbol] += update
    return weights


def quantize_weights(
    weights: list[list[float]], scale: int
) -> tuple[list[tuple[int, ...]], int]:
    result: list[tuple[int, ...]] = []
    clipped = 0
    factor = scale / math.log(2.0)
    for row in weights:
        quantized: list[int] = []
        for value in row:
            integer = round(value * factor)
            if integer < -127:
                integer = -127
                clipped += 1
            elif integer > 127:
                integer = 127
                clipped += 1
            quantized.append(integer)
        result.append(tuple(quantized))
    return result, clipped


def exp2_table(scale: int) -> tuple[int, ...]:
    return tuple(round((1 << 24) * (2.0 ** (-remainder / scale))) for remainder in range(scale))


def counts_from_logits(
    logits: list[int], total: int, scale: int, exp_table: tuple[int, ...]
) -> tuple[int, ...]:
    vocab = len(logits)
    if total < vocab:
        raise ValueError("probability total is below vocabulary")
    maximum = max(logits)
    scores: list[int] = []
    for value in logits:
        distance = maximum - value
        whole, remainder = divmod(distance, scale)
        score = exp_table[remainder] >> min(whole, 63)
        scores.append(max(1, score))
    available = total - vocab
    score_total = sum(scores)
    allocations = [available * score // score_total for score in scores]
    counts = [1 + allocation for allocation in allocations]
    missing = total - sum(counts)
    order = sorted(
        range(vocab),
        key=lambda symbol: (
            -(available * scores[symbol] % score_total),
            symbol,
        ),
    )
    for symbol in order[:missing]:
        counts[symbol] += 1
    if sum(counts) != total or min(counts) < 1:
        raise AssertionError("invalid dynamic probability table")
    return tuple(counts)


def predict_counts(
    history: list[int],
    weights: list[tuple[int, ...]],
    lags: tuple[int, ...],
    buckets: int,
    total: int,
    scale: int,
    exp_table: tuple[int, ...],
) -> tuple[int, ...]:
    active = feature_ids(history, lags, buckets)
    vocab = len(weights[0])
    logits = [
        sum(weights[feature][symbol] for feature in active)
        for symbol in range(vocab)
    ]
    return counts_from_logits(logits, total, scale, exp_table)


def encode(
    symbols: list[int],
    seed: list[int],
    weights: list[tuple[int, ...]],
    lags: tuple[int, ...],
    buckets: int,
    total: int,
    scale: int,
    exp_table: tuple[int, ...],
) -> tuple[bytes, int]:
    writer = BitWriter()
    low, high, pending = 0, MASK, 0
    history = seed.copy()

    def emit(bit: int) -> None:
        nonlocal pending
        writer.write(bit)
        for _ in range(pending):
            writer.write(1 - bit)
        pending = 0

    for symbol in symbols:
        counts = predict_counts(
            history, weights, lags, buckets, total, scale, exp_table
        )
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
    return writer.finish(), len(writer.bits)


def decode(
    payload: bytes,
    length: int,
    seed: list[int],
    weights: list[tuple[int, ...]],
    lags: tuple[int, ...],
    buckets: int,
    total: int,
    scale: int,
    exp_table: tuple[int, ...],
) -> list[int]:
    reader = BitReader(payload)
    low, high, code = 0, MASK, 0
    for _ in range(STATE_BITS):
        code = ((code << 1) | reader.read()) & MASK
    history = seed.copy()
    output: list[int] = []
    for _ in range(length):
        counts = predict_counts(
            history, weights, lags, buckets, total, scale, exp_table
        )
        cumul = cumulative(counts)
        width = high - low + 1
        value = ((code - low + 1) * total - 1) // width
        symbol = bisect.bisect_right(cumul, value) - 1
        if symbol < 0 or symbol >= len(counts):
            raise ValueError("invalid arithmetic symbol")
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
        history.append(symbol)
    return output


def serialize_model(
    weights: list[tuple[int, ...]],
    lags: tuple[int, ...],
    buckets: int,
    total: int,
    scale: int,
    exp_table: tuple[int, ...],
) -> bytes:
    vocab = len(weights[0])
    result = bytearray(MODEL_MAGIC)
    result += struct.pack(
        "<HHHBBH", vocab, len(weights), total, scale, len(lags), buckets
    )
    result += bytes(lags)
    result += struct.pack(f"<{len(exp_table)}I", *exp_table)
    for row in weights:
        result += struct.pack(f"<{vocab}b", *row)
    return bytes(result)


def evaluate(
    name: str,
    symbols: list[int],
    seed: list[int],
    weights: list[tuple[int, ...]],
    lags: tuple[int, ...],
    buckets: int,
    total: int,
    scale: int,
    exp_table: tuple[int, ...],
    output_dir: Path,
) -> dict[str, object]:
    payload, bits = encode(
        symbols, seed, weights, lags, buckets, total, scale, exp_table
    )
    decoded = decode(
        payload,
        len(symbols),
        seed,
        weights,
        lags,
        buckets,
        total,
        scale,
        exp_table,
    )
    if decoded != symbols:
        raise ValueError(f"{name} roundtrip failed")
    model_raw = serialize_model(
        weights, lags, buckets, total, scale, exp_table
    )
    model_lzma = lzma.compress(
        model_raw,
        format=lzma.FORMAT_ALONE,
        preset=9 | lzma.PRESET_EXTREME,
    )
    seed_bytes = struct.pack(f"<{len(seed)}H", *seed)
    archive = (
        ARCHIVE_MAGIC
        + struct.pack("<QH", len(symbols), len(seed))
        + seed_bytes
        + payload
    )
    (output_dir / f"{name}.model.lzma").write_bytes(model_lzma)
    (output_dir / f"{name}.archive").write_bytes(archive)
    return {
        "roundtrip_ok": True,
        "arithmetic_bits": bits,
        "seed_bytes": len(seed_bytes),
        "archive_bytes": len(archive),
        "archive_sha256": sha256(archive),
        "model_raw_bytes": len(model_raw),
        "model_lzma_bytes": len(model_lzma),
        "model_lzma_sha256": sha256(model_lzma),
        "two_part_bytes": len(archive) + len(model_lzma),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--symbols", type=Path, required=True)
    parser.add_argument("--train-rows", type=int, required=True)
    parser.add_argument("--lags", default="1,2,4,8")
    parser.add_argument("--buckets", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=0.5)
    parser.add_argument("--logit-scale", type=int, default=16)
    parser.add_argument("--total", type=int, default=4096)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    args = parser.parse_args()

    symbols = load_symbols(args.symbols)
    trace_symbols, distributions = load_trace(args.trace)
    if symbols != trace_symbols:
        raise ValueError("trace and symbol stream differ")
    if not 1 < args.train_rows < len(symbols):
        raise ValueError("invalid train split")
    lags = tuple(int(value) for value in args.lags.split(","))
    if not lags or min(lags) < 1 or max(lags) > 255:
        raise ValueError("invalid lags")
    vocab = len(distributions[0])
    soft_real = train(
        symbols,
        distributions,
        args.train_rows,
        lags,
        args.buckets,
        args.epochs,
        args.learning_rate,
        vocab,
    )
    hard_real = train(
        symbols,
        None,
        args.train_rows,
        lags,
        args.buckets,
        args.epochs,
        args.learning_rate,
        vocab,
    )
    soft_weights, soft_clipped = quantize_weights(
        soft_real, args.logit_scale
    )
    hard_weights, hard_clipped = quantize_weights(
        hard_real, args.logit_scale
    )
    exponentials = exp2_table(args.logit_scale)
    holdout = symbols[args.train_rows :]
    seed = symbols[max(0, args.train_rows - max(lags)) : args.train_rows]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    soft = evaluate(
        "soft",
        holdout,
        seed,
        soft_weights,
        lags,
        args.buckets,
        args.total,
        args.logit_scale,
        exponentials,
        args.output_dir,
    )
    hard = evaluate(
        "hard",
        holdout,
        seed,
        hard_weights,
        lags,
        args.buckets,
        args.total,
        args.logit_scale,
        exponentials,
        args.output_dir,
    )
    teacher_bits = sum(
        -math.log2(distributions[index][symbols[index]])
        for index in range(args.train_rows, len(symbols))
    )
    delta = int(soft["two_part_bytes"]) - int(hard["two_part_bytes"])
    decision = {
        "schema": "nncp_factorized_logit_gate_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "candidate_positive" if delta < 0 else "terminal_startup_negative",
        "score_credit_bytes": 0,
        "rows": len(symbols),
        "train_rows": args.train_rows,
        "holdout_rows": len(holdout),
        "lags": list(lags),
        "buckets": args.buckets,
        "epochs": args.epochs,
        "learning_rate": args.learning_rate,
        "logit_scale": args.logit_scale,
        "probability_total": args.total,
        "teacher_holdout_ideal_bits_oracle": teacher_bits,
        "soft_clipped_weights": soft_clipped,
        "hard_clipped_weights": hard_clipped,
        "soft": soft,
        "hard": hard,
        "soft_minus_hard_payload_bytes": int(soft["archive_bytes"])
        - int(hard["archive_bytes"]),
        "soft_minus_hard_two_part_bytes": delta,
        "trace_sha256": sha256(args.trace.read_bytes()),
        "symbols_sha256": sha256(args.symbols.read_bytes()),
        "claim_boundary": (
            "Bounded same-domain factored-logit student only. Teacher loss is "
            "oracle evidence; no native score or Hutter credit."
        ),
        "next_gate": (
            "Require disjoint transfer before native integration."
            if delta < 0
            else "Retire this lag-feature logit projection without a width or epoch ladder."
        ),
    }
    args.decision.parent.mkdir(parents=True, exist_ok=True)
    args.decision.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
