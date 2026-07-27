#!/usr/bin/env python3
"""Screen scalar NNCP branch-frequency centroids against hard-label controls."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import lzma
import math
from pathlib import Path
import struct


HEADER = struct.Struct("<8sQQ")
ROW = struct.Struct("<QQQHHB")
BRANCH = struct.Struct("<HB")
MAGIC = b"NNQBR1\0\0"
TOTAL = 32768


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> list[tuple[int, list[tuple[int, int, int, int]]]]:
    raw = path.read_bytes()
    magic, count, _branches = HEADER.unpack_from(raw)
    if magic != MAGIC:
        raise ValueError("invalid branch trace")
    offset = HEADER.size
    rows: list[tuple[int, list[tuple[int, int, int, int]]]] = []
    for _ in range(count):
        _execution, _before, _after, symbol, vocabulary, branch_count = (
            ROW.unpack_from(raw, offset)
        )
        offset += ROW.size
        start, active = 0, vocabulary
        branches: list[tuple[int, int, int, int]] = []
        for _branch in range(branch_count):
            probability, bit = BRANCH.unpack_from(raw, offset)
            offset += BRANCH.size
            branches.append((start, active, probability, bit))
            left = active >> 1
            if bit:
                start += left
                active -= left
            else:
                active = left
        rows.append((symbol, branches))
    if offset != len(raw):
        raise ValueError("trailing trace bytes")
    return rows


def q_soft(accumulator: list[int]) -> int:
    return max(1, min(TOTAL - 1, round(accumulator[0] / accumulator[1])))


def q_hard(accumulator: list[int]) -> int:
    zeros, ones = accumulator
    return max(1, min(TOTAL - 1, round((zeros + 0.5) * TOTAL / (zeros + ones + 1))))


def loss(probability: int, bit: int) -> float:
    mass = probability if bit == 0 else TOTAL - probability
    return -math.log2(mass / TOTAL)


def serialize(
    tables: dict[tuple[int, ...], int],
    depth: int,
) -> bytes:
    output = bytearray(struct.pack("<BI", depth, len(tables)))
    for key in sorted(tables):
        output.extend(struct.pack("<B", len(key)))
        for value in key:
            output.extend(struct.pack("<h", value))
        output.extend(struct.pack("<H", tables[key]))
    return bytes(output)


def evaluate(
    rows: list[tuple[int, list[tuple[int, int, int, int]]]],
    train_rows: int,
    depth: int,
    minimum_count: int,
) -> dict[str, object]:
    counts: Counter[tuple[int, ...]] = Counter()
    soft = defaultdict(lambda: [0, 0])
    hard = defaultdict(lambda: [0, 0])
    fallback_soft = defaultdict(lambda: [0, 0])
    fallback_hard = defaultdict(lambda: [0, 0])
    active_soft = defaultdict(lambda: [0, 0])
    active_hard = defaultdict(lambda: [0, 0])
    global_soft = [0, 0]
    global_hard = [0, 0]

    for index, (_symbol, branches) in enumerate(rows[:train_rows]):
        history = (
            tuple(row[0] for row in rows[max(0, index - depth) : index])
            if depth
            else ()
        )
        for start, active, probability, bit in branches:
            key = (*history, start, active)
            counts[key] += 1
            soft[key][0] += probability
            soft[key][1] += 1
            hard[key][bit] += 1
            split = (start, active)
            fallback_soft[split][0] += probability
            fallback_soft[split][1] += 1
            fallback_hard[split][bit] += 1
            active_key = (active,)
            active_soft[active_key][0] += probability
            active_soft[active_key][1] += 1
            active_hard[active_key][bit] += 1
            global_soft[0] += probability
            global_soft[1] += 1
            global_hard[bit] += 1

    retained = {key for key, count in counts.items() if count >= minimum_count}
    soft_tables = {key: q_soft(soft[key]) for key in retained}
    hard_tables = {key: q_hard(hard[key]) for key in retained}
    for key, accumulator in fallback_soft.items():
        soft_tables[(-1, *key)] = q_soft(accumulator)
        hard_tables[(-1, *key)] = q_hard(fallback_hard[key])
    for key, accumulator in active_soft.items():
        soft_tables[(-2, *key)] = q_soft(accumulator)
        hard_tables[(-2, *key)] = q_hard(active_hard[key])
    soft_tables[(-3,)] = q_soft(global_soft)
    hard_tables[(-3,)] = q_hard(global_hard)

    losses = {"teacher": 0.0, "soft": 0.0, "hard": 0.0}
    for index, (_symbol, branches) in enumerate(rows[train_rows:], train_rows):
        history = (
            tuple(row[0] for row in rows[max(0, index - depth) : index])
            if depth
            else ()
        )
        for start, active, probability, bit in branches:
            key = (*history, start, active)
            if key in retained:
                soft_probability = q_soft(soft[key])
                hard_probability = q_hard(hard[key])
            elif fallback_soft[(start, active)][1]:
                soft_probability = q_soft(fallback_soft[(start, active)])
                hard_probability = q_hard(fallback_hard[(start, active)])
            elif active_soft[(active,)][1]:
                soft_probability = q_soft(active_soft[(active,)])
                hard_probability = q_hard(active_hard[(active,)])
            else:
                soft_probability = q_soft(global_soft)
                hard_probability = q_hard(global_hard)
            losses["teacher"] += loss(probability, bit)
            losses["soft"] += loss(soft_probability, bit)
            losses["hard"] += loss(hard_probability, bit)

    soft_model = serialize(soft_tables, depth)
    hard_model = serialize(hard_tables, depth)
    soft_lzma = lzma.compress(
        soft_model, format=lzma.FORMAT_ALONE, preset=9 | lzma.PRESET_EXTREME
    )
    hard_lzma = lzma.compress(
        hard_model, format=lzma.FORMAT_ALONE, preset=9 | lzma.PRESET_EXTREME
    )
    return {
        "depth": depth,
        "hard_ideal_bits": losses["hard"],
        "hard_model_lzma_bytes": len(hard_lzma),
        "hard_model_lzma_sha256": sha256(hard_lzma),
        "hard_two_part_proxy_bytes": math.ceil(losses["hard"] / 8) + len(hard_lzma),
        "minimum_count": minimum_count,
        "retained_contexts": len(retained),
        "soft_ideal_bits": losses["soft"],
        "soft_minus_hard_ideal_bits": losses["soft"] - losses["hard"],
        "soft_model_lzma_bytes": len(soft_lzma),
        "soft_model_lzma_sha256": sha256(soft_lzma),
        "soft_two_part_proxy_bytes": math.ceil(losses["soft"] / 8) + len(soft_lzma),
        "teacher_ideal_bits": losses["teacher"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--train-rows", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = load(args.trace)
    if not 0 < args.train_rows < len(rows):
        raise ValueError("invalid train-row split")
    evaluations = [
        evaluate(rows, args.train_rows, depth, minimum_count)
        for depth in (0, 1, 2)
        for minimum_count in (2, 4, 8, 16)
    ]
    all_soft_worse = all(
        float(row["soft_ideal_bits"]) > float(row["hard_ideal_bits"])
        for row in evaluations
    )
    decision = {
        "claim_boundary": (
            "Startup branch-centroid representation screen. Ideal loss and "
            "two-part proxies are not native Hutter score evidence."
        ),
        "evaluations": evaluations,
        "generated_from_trace_sha256": sha256(args.trace.read_bytes()),
        "holdout_rows": len(rows) - args.train_rows,
        "schema": "nncp_branch_centroid_screen_v1",
        "score_credit_bytes": 0,
        "soft_loses_every_configuration": all_soft_worse,
        "status": (
            "terminal_startup_negative" if all_soft_worse else "requires_native_gate"
        ),
        "train_rows": args.train_rows,
    }
    args.output.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "soft_loses_every_configuration": all_soft_worse,
                "status": decision["status"],
                "worst_soft_minus_hard_ideal_bits": max(
                    float(row["soft_minus_hard_ideal_bits"])
                    for row in evaluations
                ),
                "best_soft_minus_hard_ideal_bits": min(
                    float(row["soft_minus_hard_ideal_bits"])
                    for row in evaluations
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
