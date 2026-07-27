#!/usr/bin/env python3
"""Fit one frozen monotone q16 calibration table and replay exact holdout bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import mmap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAGIC = b"FX2PT01\n"
TOTAL = 1 << 16
MAX_CODE = (1 << 32) - 1
BIN_COUNT = 256
TARGET_BPM = 2000.0


@dataclass
class Block:
    first: int
    last: int
    zeros: int
    ones: int

    @property
    def total(self) -> int:
        return self.zeros + self.ones


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def trace_rows(path: Path) -> int:
    size = path.stat().st_size
    if size < len(MAGIC) or (size - len(MAGIC)) % 3:
        raise ValueError("invalid FX2PT trace size")
    with path.open("rb") as source:
        if source.read(len(MAGIC)) != MAGIC:
            raise ValueError("invalid FX2PT trace magic")
    return (size - len(MAGIC)) // 3


def pava(total: list[int], ones: list[int]) -> list[Block]:
    stack: list[Block] = []
    for index in range(BIN_COUNT):
        if total[index] == 0:
            continue
        block = Block(
            first=index,
            last=index,
            zeros=int(total[index] - ones[index]),
            ones=int(ones[index]),
        )
        stack.append(block)
        while len(stack) >= 2:
            left = stack[-2]
            right = stack[-1]
            if left.ones * right.total < right.ones * left.total:
                break
            stack[-2:] = [
                Block(
                    first=left.first,
                    last=right.last,
                    zeros=left.zeros + right.zeros,
                    ones=left.ones + right.ones,
                )
            ]
    return stack


def block_probability(block: Block) -> int:
    target = block.ones * TOTAL / block.total
    candidates = {
        max(1, min(TOTAL - 1, int(math.floor(target)))),
        max(1, min(TOTAL - 1, int(math.ceil(target)))),
    }

    def loss(q: int) -> float:
        p = q / TOTAL
        return -block.zeros * math.log2(1.0 - p) - block.ones * math.log2(p)

    return min(candidates, key=lambda q: (loss(q), q))


def table_from_blocks(blocks: list[Block]) -> tuple[list[int], list[dict[str, int]]]:
    table = [0] * BIN_COUNT
    encoded: list[dict[str, int]] = []
    previous_end = -1
    previous_q: int | None = None
    for index, block in enumerate(blocks):
        q = block_probability(block)
        end = block.last
        next_first = blocks[index + 1].first if index + 1 < len(blocks) else BIN_COUNT
        fill_first = previous_end + 1
        fill_last = next_first - 1
        if previous_q is None:
            for bin_index in range(fill_first, block.first):
                table[bin_index] = q
        for bin_index in range(block.first, fill_last + 1):
            table[bin_index] = q
        if encoded and encoded[-1]["q16"] == q:
            encoded[-1]["last_bin"] = fill_last
            encoded[-1]["zeros"] += block.zeros
            encoded[-1]["ones"] += block.ones
        else:
            encoded.append(
                {
                    "first_bin": fill_first,
                    "last_bin": fill_last,
                    "zeros": block.zeros,
                    "ones": block.ones,
                    "q16": q,
                }
            )
        previous_end = fill_last
        previous_q = q
    if previous_end < BIN_COUNT - 1:
        assert previous_q is not None
        for bin_index in range(previous_end + 1, BIN_COUNT):
            table[bin_index] = previous_q
        encoded[-1]["last_bin"] = BIN_COUNT - 1
    if any(table[index] < table[index - 1] for index in range(1, BIN_COUNT)):
        raise ValueError("quantized PAVA table is not monotone")
    return table, encoded


class RangeEncoder:
    def __init__(self) -> None:
        self.x1 = 0
        self.x2 = MAX_CODE
        self.output = bytearray()

    def update(self, p1: int, bit: int) -> None:
        delta = self.x2 - self.x1
        midpoint = self.x1 + (delta >> 16) * p1 + (
            (delta & 0xFFFF) * p1 >> 16
        )
        if bit:
            self.x2 = midpoint
        else:
            self.x1 = midpoint + 1
        while ((self.x1 ^ self.x2) & 0xFF000000) == 0:
            self.output.append((self.x2 >> 24) & 0xFF)
            self.x1 = (self.x1 << 8) & MAX_CODE
            self.x2 = ((self.x2 << 8) & MAX_CODE) + 255

    def finish(self) -> bytes:
        while ((self.x1 ^ self.x2) & 0xFF000000) == 0:
            self.output.append((self.x2 >> 24) & 0xFF)
            self.x1 = (self.x1 << 8) & MAX_CODE
            self.x2 = ((self.x2 << 8) & MAX_CODE) + 255
        self.output.append((self.x2 >> 24) & 0xFF)
        return bytes(self.output)


def run(args: argparse.Namespace) -> dict[str, Any]:
    rows = trace_rows(args.trace)
    split = rows // 2
    split -= split % 8
    total = [0] * BIN_COUNT
    ones = [0] * BIN_COUNT
    baseline_encoder = RangeEncoder()
    calibrated_encoder = RangeEncoder()
    with args.trace.open("rb") as source:
        mapped = mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ)
        for row in range(split):
            offset = len(MAGIC) + 3 * row
            p1 = mapped[offset] | (mapped[offset + 1] << 8)
            bit = mapped[offset + 2]
            if p1 == 0 or bit > 1:
                raise ValueError("invalid training trace row")
            bin_index = p1 >> 8
            total[bin_index] += 1
            ones[bin_index] += bit
        blocks = pava(total, ones)
        table, encoded = table_from_blocks(blocks)
        for row in range(split, rows):
            offset = len(MAGIC) + 3 * row
            p1 = mapped[offset] | (mapped[offset + 1] << 8)
            bit = mapped[offset + 2]
            if p1 == 0 or bit > 1:
                raise ValueError("invalid holdout trace row")
            baseline_encoder.update(p1, bit)
            calibrated_encoder.update(table[p1 >> 8], bit)
        mapped.close()
    baseline_payload = baseline_encoder.finish()
    calibrated_payload = calibrated_encoder.finish()
    gross_saved = len(baseline_payload) - len(calibrated_payload)
    table_bytes = 3 * len(encoded)
    net_saved = gross_saved - table_bytes
    holdout_rows = rows - split
    holdout_raw_bytes = args.raw_bytes * holdout_rows / rows
    net_bpm = net_saved * 1_000_000.0 / holdout_raw_bytes
    promoted = net_bpm >= TARGET_BPM
    result = {
        "schema": "finite_monotone_calibration_gate_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate": "finite_monotone_calibration_q16_v1",
        "input": {
            "trace": artifact(args.trace),
            "raw_scope_bytes": args.raw_bytes,
            "rows": rows,
            "train_rows": split,
            "holdout_rows": holdout_rows,
        },
        "construction": {
            "input_bins": BIN_COUNT,
            "pava_blocks": len(blocks),
            "quantized_blocks": len(encoded),
            "table_bytes": table_bytes,
            "table": encoded,
        },
        "holdout": {
            "baseline_payload_bytes": len(baseline_payload),
            "baseline_payload_sha256": hashlib.sha256(baseline_payload).hexdigest(),
            "calibrated_payload_bytes": len(calibrated_payload),
            "calibrated_payload_sha256": hashlib.sha256(calibrated_payload).hexdigest(),
            "gross_saved_bytes": gross_saved,
            "net_saved_bytes": net_saved,
            "net_saved_bpm": net_bpm,
        },
        "gate": {
            "required_net_saved_bpm": TARGET_BPM,
            "pass": promoted,
        },
        "decision": (
            "promote_monotone_calibration_to_distant_gate"
            if promoted
            else "retire_global_monotone_calibration"
        ),
        "claim_boundary": (
            "This is a chronological holdout shadow with exact q16 range replay "
            "and explicit table bytes. It has zero score credit until native "
            "integration, distant transfer, complete source accounting, and "
            "end-to-end replay pass."
        ),
        "score_credit_bytes": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--raw-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    result = run(parse_args())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
