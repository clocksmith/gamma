#!/usr/bin/env python3
"""Emit a causal WRT token-suffix Sequence Memoizer probability trace.

The model is a bounded binary hierarchical Pitman-Yor approximation.  Every
bit context combines the already completed WRT token suffix with the current
token byte phase and current byte-bit prefix.  Counts update only after the
true bit.  The resulting endpoint is submission-compatible in mechanism: no
trained weights or future state are required, although this Python trace is
discovery evidence rather than native integration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np


P1_MAGIC = b"CMX21P1\0"
P1_HEADER_BYTES = 16
PAIR_MAGIC = b"CMXAUX1\0"
PAIR_HEADER_BYTES = 16
PROBABILITY_TOTAL = 65_536
Q24 = 1 << 24


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


def read_p1_rows(path: Path) -> int:
    with path.open("rb") as stream:
        header = stream.read(P1_HEADER_BYTES)
    if len(header) != P1_HEADER_BYTES or header[:8] != P1_MAGIC:
        raise ValueError("invalid CMIX21 P1 header")
    rows = struct.unpack_from("<Q", header, 8)[0]
    if rows < 1 or path.stat().st_size != P1_HEADER_BYTES + 2 * rows:
        raise ValueError("CMIX21 P1 length mismatch")
    return rows


def token_length(first_byte: int) -> int:
    if first_byte == 0x0C:
        return 2
    if 0xD0 <= first_byte <= 0xEF:
        return 2
    if first_byte >= 0xF0:
        return 3
    return 1


def token_id(token: bytes) -> int:
    if not 1 <= len(token) <= 3:
        raise ValueError("WRT token must contain one to three bytes")
    value = len(token) << 24
    for byte in token:
        value = (value << 8) | byte
    return value


class SequenceMemoizer:
    """Bounded Q24 binary HPYP over completed-token suffix contexts."""

    def __init__(self, max_order: int, max_contexts: int) -> None:
        if max_order < 0 or max_contexts < 1:
            raise ValueError("invalid Sequence Memoizer bounds")
        self.max_order = max_order
        self.max_contexts = max_contexts
        self.tables: list[dict[tuple[Any, ...], list[int]]] = [
            {} for _ in range(max_order + 1)
        ]
        self.contexts = 0
        self.context_insertions_blocked = 0
        self.recent_tokens: deque[int] = deque(maxlen=max_order)
        self.token_buffer = bytearray()
        self.expected_token_bytes = 0
        self.tokens_completed = 0

    def _suffixes(self) -> list[tuple[int, ...]]:
        recent = tuple(self.recent_tokens)
        return [
            recent[len(recent) - depth :] if depth else ()
            for depth in range(min(self.max_order, len(recent)) + 1)
        ]

    def _keys(
        self,
        suffixes: list[tuple[int, ...]],
        phase: int,
        bit_position: int,
        prefix: int,
    ) -> list[tuple[Any, ...]]:
        return [
            (phase, bit_position, prefix, suffix)
            for suffix in suffixes
        ]

    def predict_q24(self, keys: list[tuple[Any, ...]]) -> int:
        probability = Q24 // 2
        for depth, key in enumerate(keys):
            counts = self.tables[depth].get(key)
            if counts is None:
                continue
            zero, one = counts
            total = zero + one
            distinct = int(zero > 0) + int(one > 0)
            adjusted_one_twice = max(2 * one - 1, 0)
            denominator_twice = 2 * total + 2
            numerator = (
                adjusted_one_twice * Q24
                + (2 + distinct) * probability
            )
            probability = (numerator + denominator_twice // 2) // denominator_twice
        return min(Q24 - 1, max(1, probability))

    def update(self, keys: list[tuple[Any, ...]], bit: int) -> None:
        for depth, key in enumerate(keys):
            table = self.tables[depth]
            counts = table.get(key)
            if counts is None:
                if self.contexts >= self.max_contexts:
                    self.context_insertions_blocked += 1
                    continue
                counts = [0, 0]
                table[key] = counts
                self.contexts += 1
            counts[bit] += 1

    def phase(self) -> int:
        if not self.token_buffer:
            return 0
        return self.expected_token_bytes * 4 + len(self.token_buffer)

    def observe_byte(self, byte: int) -> None:
        if not self.token_buffer:
            self.expected_token_bytes = token_length(byte)
        self.token_buffer.append(byte)
        if len(self.token_buffer) == self.expected_token_bytes:
            self.recent_tokens.append(token_id(bytes(self.token_buffer)))
            self.token_buffer.clear()
            self.expected_token_bytes = 0
            self.tokens_completed += 1

    def predict_and_observe_byte(self, byte: int) -> list[int]:
        suffixes = self._suffixes()
        phase = self.phase()
        probabilities: list[int] = []
        prefix = 0
        for bit_position in range(8):
            bit = (byte >> (7 - bit_position)) & 1
            keys = self._keys(suffixes, phase, bit_position, prefix)
            q24 = self.predict_q24(keys)
            p1 = (q24 * PROBABILITY_TOTAL + Q24 // 2) // Q24
            probabilities.append(min(PROBABILITY_TOTAL - 1, max(1, p1)))
            self.update(keys, bit)
            prefix = (prefix << 1) | bit
        self.observe_byte(byte)
        return probabilities


def run(
    *,
    store: Path,
    store_offset: int,
    base_p1: Path,
    output_trace: Path,
    max_order: int,
    max_contexts: int,
) -> dict[str, Any]:
    if store_offset < 0 or store_offset >= store.stat().st_size:
        raise ValueError("invalid WRT store offset")
    data = store.read_bytes()[store_offset:]
    rows = len(data) * 8
    if read_p1_rows(base_p1) != rows:
        raise ValueError("WRT store and base P1 rows differ")
    base = np.memmap(
        base_p1,
        dtype="<u2",
        mode="r",
        offset=P1_HEADER_BYTES,
        shape=(rows,),
    )
    output_trace.parent.mkdir(parents=True, exist_ok=True)
    with output_trace.open("wb") as stream:
        stream.write(PAIR_MAGIC)
        stream.write(struct.pack("<Q", rows))
        stream.truncate(PAIR_HEADER_BYTES + rows * 4)
    pair = np.memmap(
        output_trace,
        dtype="<u2",
        mode="r+",
        offset=PAIR_HEADER_BYTES,
        shape=(rows, 2),
    )
    model = SequenceMemoizer(max_order=max_order, max_contexts=max_contexts)
    row = 0
    for byte in data:
        probabilities = model.predict_and_observe_byte(byte)
        end = row + 8
        pair[row:end, 0] = base[row:end]
        pair[row:end, 1] = probabilities
        row = end
    pair.flush()
    del pair
    estimated_native_state_bytes = model.contexts * 24
    return {
        "schema": "wrt_sequence_memoizer_trace_v1",
        "evidence_level": "causal_bounded_discovery_probability_trace",
        "inputs": {
            "store": artifact(store),
            "store_offset_bytes": store_offset,
            "base_p1": artifact(base_p1),
        },
        "output": artifact(output_trace),
        "scope": {
            "wrt_bytes": len(data),
            "rows": rows,
        },
        "model": {
            "max_token_order": max_order,
            "max_contexts": max_contexts,
            "contexts_used": model.contexts,
            "context_insertions_blocked": model.context_insertions_blocked,
            "tokens_completed": model.tokens_completed,
            "estimated_native_state_bytes_at_24_per_context": (
                estimated_native_state_bytes
            ),
            "discount": "1/2",
            "strength": 1,
            "probability_math": "deterministic_integer_Q24",
        },
        "identity": {
            "base_rows_copied_from_frozen_p1": True,
            "updates_after_current_true_bit": True,
            "uses_only_completed_token_suffix_and_current_byte_prefix": True,
        },
        "promotion_authorized": False,
        "claim_boundary": (
            "Causal endpoint trace only. Exact blend replay, held-out economics, "
            "native state layout, source cost, roundtrip, and full-corpus proof remain."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--store-offset", type=int, default=5)
    parser.add_argument("--base-p1", type=Path, required=True)
    parser.add_argument("--output-trace", type=Path, required=True)
    parser.add_argument("--output-receipt", type=Path, required=True)
    parser.add_argument("--max-order", type=int, default=3)
    parser.add_argument("--max-contexts", type=int, default=500_000)
    args = parser.parse_args()
    receipt = run(
        store=args.store,
        store_offset=args.store_offset,
        base_p1=args.base_p1,
        output_trace=args.output_trace,
        max_order=args.max_order,
        max_contexts=args.max_contexts,
    )
    args.output_receipt.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output_receipt.with_suffix(args.output_receipt.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output_receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
