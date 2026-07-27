#!/usr/bin/env python3
"""Compile and test a decoder-visible automaton from NNCP teacher states."""

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

from projects.enwiki9.tools.nncp_soft_quotient_gate import (
    BitReader,
    BitWriter,
    FULL,
    HALF,
    MASK,
    QUARTER,
    STATE_BITS,
    THREE_QUARTERS,
    cumulative,
    load_symbols,
    load_trace,
    quantize_mass,
)


MODEL_MAGIC = b"DTAM1\0"
ARCHIVE_MAGIC = b"DTAA1\0"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def squared_distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return math.fsum((a - b) * (a - b) for a, b in zip(left, right))


def canonical_kmeans(
    rows: list[tuple[float, ...]], states: int, iterations: int
) -> tuple[list[int], list[tuple[float, ...]]]:
    if not 1 <= states <= len(rows):
        raise ValueError("invalid automaton state count")
    centroids = [rows[0]]
    while len(centroids) < states:
        best_index = max(
            range(len(rows)),
            key=lambda index: (
                min(squared_distance(rows[index], center) for center in centroids),
                -index,
            ),
        )
        centroids.append(rows[best_index])

    assignments = [0] * len(rows)
    for _ in range(iterations):
        new_assignments = [
            min(
                range(states),
                key=lambda state: (squared_distance(row, centroids[state]), state),
            )
            for row in rows
        ]
        sums = [[0.0] * len(rows[0]) for _ in range(states)]
        counts = [0] * states
        for assignment, row in zip(new_assignments, rows):
            counts[assignment] += 1
            for symbol, probability in enumerate(row):
                sums[assignment][symbol] += probability
        new_centroids: list[tuple[float, ...]] = []
        for state in range(states):
            if counts[state] == 0:
                new_centroids.append(centroids[state])
            else:
                inverse = 1.0 / counts[state]
                new_centroids.append(
                    tuple(value * inverse for value in sums[state])
                )
        assignments = new_assignments
        if new_centroids == centroids:
            break
        centroids = new_centroids
    return assignments, centroids


def learn_transition(
    symbols: list[int], labels: list[int], states: int, vocab: int
) -> tuple[list[list[int]], int]:
    counts = [[{} for _ in range(vocab)] for _ in range(states)]
    for index in range(len(labels) - 1):
        source = labels[index]
        symbol = symbols[index]
        target = labels[index + 1]
        cell = counts[source][symbol]
        cell[target] = cell.get(target, 0) + 1
    transition = [[state] * vocab for state in range(states)]
    for state in range(states):
        for symbol in range(vocab):
            cell = counts[state][symbol]
            if cell:
                transition[state][symbol] = min(
                    cell, key=lambda target: (-cell[target], target)
                )
    disagreements = sum(
        transition[labels[index]][symbols[index]] != labels[index + 1]
        for index in range(len(labels) - 1)
    )
    return transition, disagreements


def closed_loop_states(
    symbols: list[int], transition: list[list[int]], initial: int
) -> tuple[list[int], int]:
    state = initial
    path: list[int] = []
    for symbol in symbols:
        path.append(state)
        state = transition[state][symbol]
    return path, state


def output_tables(
    symbols: list[int],
    distributions: list[tuple[float, ...]],
    path: list[int],
    states: int,
    total: int,
) -> tuple[list[tuple[int, ...]], list[tuple[int, ...]]]:
    vocab = len(distributions[0])
    global_soft = [0.0] * vocab
    global_hard = [0.0] * vocab
    soft = [[0.0] * vocab for _ in range(states)]
    hard = [[0.0] * vocab for _ in range(states)]
    visits = [0] * states
    for symbol, distribution, state in zip(symbols, distributions, path):
        visits[state] += 1
        for candidate, probability in enumerate(distribution):
            soft[state][candidate] += probability
            global_soft[candidate] += probability
        hard[state][symbol] += 1.0
        global_hard[symbol] += 1.0
    for state in range(states):
        if visits[state] == 0:
            soft[state] = global_soft.copy()
            hard[state] = global_hard.copy()
    return (
        [quantize_mass(mass, total) for mass in soft],
        [quantize_mass(mass, total) for mass in hard],
    )


def encode(
    symbols: list[int],
    transition: list[list[int]],
    outputs: list[tuple[int, ...]],
    initial: int,
    total: int,
) -> tuple[bytes, int, int]:
    writer = BitWriter()
    low, high, pending = 0, MASK, 0
    state = initial

    def emit(bit: int) -> None:
        nonlocal pending
        writer.write(bit)
        for _ in range(pending):
            writer.write(1 - bit)
        pending = 0

    for symbol in symbols:
        cumul = cumulative(outputs[state])
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
        state = transition[state][symbol]
    pending += 1
    emit(0 if low < QUARTER else 1)
    bit_count = len(writer.bits)
    return writer.finish(), bit_count, state


def decode(
    payload: bytes,
    length: int,
    transition: list[list[int]],
    outputs: list[tuple[int, ...]],
    initial: int,
    total: int,
) -> tuple[list[int], int]:
    reader = BitReader(payload)
    low, high, code = 0, MASK, 0
    for _ in range(STATE_BITS):
        code = ((code << 1) | reader.read()) & MASK
    state = initial
    decoded: list[int] = []
    for _ in range(length):
        cumul = cumulative(outputs[state])
        width = high - low + 1
        value = ((code - low + 1) * total - 1) // width
        symbol = bisect.bisect_right(cumul, value) - 1
        if symbol < 0 or symbol >= len(outputs[state]):
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
        decoded.append(symbol)
        state = transition[state][symbol]
    return decoded, state


def serialize_model(
    transition: list[list[int]],
    outputs: list[tuple[int, ...]],
    initial: int,
    total: int,
) -> bytes:
    states = len(transition)
    vocab = len(transition[0])
    if states > 256 or max(max(row) for row in transition) > 255:
        raise ValueError("v1 transition serialization requires at most 256 states")
    result = bytearray(MODEL_MAGIC)
    result += struct.pack("<BHI B", states, vocab, total, initial)
    for row in transition:
        result += bytes(row)
    for row in outputs:
        result += struct.pack(f"<{vocab}H", *row)
    return bytes(result)


def evaluate(
    name: str,
    symbols: list[int],
    transition: list[list[int]],
    outputs: list[tuple[int, ...]],
    initial: int,
    total: int,
    output_dir: Path,
) -> dict[str, object]:
    payload, bits, final_state = encode(
        symbols, transition, outputs, initial, total
    )
    decoded, decoded_final = decode(
        payload, len(symbols), transition, outputs, initial, total
    )
    if decoded != symbols or decoded_final != final_state:
        raise ValueError(f"{name} roundtrip or state agreement failed")
    model_raw = serialize_model(transition, outputs, initial, total)
    model_lzma = lzma.compress(
        model_raw,
        format=lzma.FORMAT_ALONE,
        preset=9 | lzma.PRESET_EXTREME,
    )
    archive = ARCHIVE_MAGIC + struct.pack("<QB", len(symbols), initial) + payload
    (output_dir / f"{name}.model.lzma").write_bytes(model_lzma)
    (output_dir / f"{name}.archive").write_bytes(archive)
    return {
        "roundtrip_ok": True,
        "final_state_agreement": True,
        "arithmetic_bits": bits,
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
    parser.add_argument("--states", type=int, default=8)
    parser.add_argument("--iterations", type=int, default=8)
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
    train_symbols = symbols[: args.train_rows]
    train_distributions = distributions[: args.train_rows]
    vocab = len(train_distributions[0])
    labels, _centroids = canonical_kmeans(
        train_distributions, args.states, args.iterations
    )
    transition, disagreements = learn_transition(
        train_symbols, labels, args.states, vocab
    )
    initial = labels[0]
    path, holdout_initial = closed_loop_states(
        train_symbols, transition, initial
    )
    soft_outputs, hard_outputs = output_tables(
        train_symbols,
        train_distributions,
        path,
        args.states,
        args.total,
    )
    closed_loop_agreement = sum(a == b for a, b in zip(path, labels))
    holdout = symbols[args.train_rows :]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    soft = evaluate(
        "soft",
        holdout,
        transition,
        soft_outputs,
        holdout_initial,
        args.total,
        args.output_dir,
    )
    hard = evaluate(
        "hard",
        holdout,
        transition,
        hard_outputs,
        holdout_initial,
        args.total,
        args.output_dir,
    )
    teacher_bits = sum(
        -math.log2(distributions[index][symbols[index]])
        for index in range(args.train_rows, len(symbols))
    )
    soft_two_part_delta = int(soft["two_part_bytes"]) - int(
        hard["two_part_bytes"]
    )
    decision = {
        "schema": "nncp_teacher_automaton_gate_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "candidate_positive"
            if soft_two_part_delta < 0
            else "terminal_startup_negative"
        ),
        "score_credit_bytes": 0,
        "rows": len(symbols),
        "train_rows": args.train_rows,
        "holdout_rows": len(holdout),
        "states": args.states,
        "iterations": args.iterations,
        "vocabulary": vocab,
        "probability_total": args.total,
        "transition_disagreements": disagreements,
        "transition_rows": max(0, args.train_rows - 1),
        "closed_loop_teacher_state_agreements": closed_loop_agreement,
        "teacher_holdout_ideal_bits_oracle": teacher_bits,
        "soft": soft,
        "hard": hard,
        "soft_minus_hard_payload_bytes": int(soft["archive_bytes"])
        - int(hard["archive_bytes"]),
        "soft_minus_hard_two_part_bytes": soft_two_part_delta,
        "trace_sha256": sha256(args.trace.read_bytes()),
        "symbols_sha256": sha256(args.symbols.read_bytes()),
        "claim_boundary": (
            "Bounded same-domain deterministic automaton test only. Teacher "
            "states and ideal loss are oracle evidence; no Hutter credit."
        ),
        "next_gate": (
            "Require a disjoint trace before native integration."
            if soft_two_part_delta < 0
            else "Retire this teacher-cluster automaton without a state-count ladder."
        ),
    }
    args.decision.parent.mkdir(parents=True, exist_ok=True)
    args.decision.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
