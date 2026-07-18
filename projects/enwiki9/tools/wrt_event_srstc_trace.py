#!/usr/bin/env python3
"""Emit a causal semantic-retrieval endpoint over exact WRT events.

Each completed WRT event is indexed under a compact sketch of the raw bytes and
Wiki state that preceded it.  At a later event, an identical decoder-rebuilt
sketch retrieves prior encoded continuations.  The candidate probability uses
only their already-decoded prefixes and is paired with the frozen endpoint428
probability stream for exact downstream replay.
"""

from __future__ import annotations

import argparse
from collections import Counter, deque
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import struct
from typing import Any, Iterable

import numpy as np

from causal_state_screen import WikiState
from fx2_shadow_residual_coder import TOTAL, clamp_p1
from streaming_retrieval_shadow import fnv64_bytes, fnv64_ints, simhash16
from wrt_entity_trie_fx2_shadow import P1Trace, event_prefix
from wrt_exact import ParsedStore, WrtEvent, parse_store


PAIR_MAGIC = b"CMXAUX1\0"
PAIR_HEADER_BYTES = 16


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


def probability_bucket(p1: int, buckets: int) -> int:
    return min(buckets - 1, int(p1) * buckets // TOTAL)


@dataclass(frozen=True)
class SemanticFeatures:
    field: int
    mode: int
    slot: int
    schema_hash: int
    suffix_hash: int
    simhash: int

    def keys(self) -> tuple[tuple[Any, ...], ...]:
        return (
            ("suffix", self.suffix_hash),
            ("sim0", self.simhash & 0xFF),
            ("sim1", (self.simhash >> 8) & 0xFF),
            ("schema", self.schema_hash),
            ("hybrid", self.field, self.mode, self.simhash & 0xFF),
        )


@dataclass
class RawSemanticState:
    suffix_len: int
    sketch_len: int
    wiki: WikiState = field(default_factory=WikiState)
    tail: bytearray = field(default_factory=bytearray)

    def features(self) -> SemanticFeatures:
        tail = bytes(self.tail)
        wiki = self.wiki.features()
        field = int(wiki.get("field", 0))
        mode = int(wiki.get("mode", 0))
        slot = int(wiki.get("slot", 0))
        column = int(wiki.get("column_bucket", 0))
        word_sig = wiki.get("word_sig", (0, 0))
        if not isinstance(word_sig, tuple):
            word_sig = (0, 0)
        suffix_hash = fnv64_bytes(tail[-self.suffix_len :]) & 0xFFFF
        schema_hash = fnv64_ints(
            (field, mode, slot, column, int(word_sig[0]), int(word_sig[1]))
        ) & 0xFFFF
        return SemanticFeatures(
            field=field,
            mode=mode,
            slot=slot,
            schema_hash=schema_hash,
            suffix_hash=suffix_hash,
            simhash=simhash16(tail[-self.sketch_len :]),
        )

    def observe(self, decoded: bytes) -> None:
        for byte in decoded:
            self.wiki.update(byte)
            self.tail.append(byte)
        keep = max(self.suffix_len, self.sketch_len)
        if len(self.tail) > keep:
            del self.tail[: len(self.tail) - keep]


@dataclass
class EventContinuationTable:
    max_keys: int
    codes_per_key: int
    counts: dict[tuple[Any, ...], Counter[bytes]] = field(default_factory=dict)
    order: deque[tuple[Any, ...]] = field(default_factory=deque)
    evicted_keys: int = 0
    rejected_codes: int = 0

    def update(self, keys: Iterable[tuple[Any, ...]], code: bytes) -> None:
        for key in keys:
            counter = self.counts.get(key)
            if counter is None:
                if len(self.counts) >= self.max_keys:
                    old = self.order.popleft()
                    del self.counts[old]
                    self.evicted_keys += 1
                counter = Counter()
                self.counts[key] = counter
                self.order.append(key)
            if code not in counter and len(counter) >= self.codes_per_key:
                self.rejected_codes += 1
                continue
            counter[code] += 1

    def candidate(
        self,
        keys: Iterable[tuple[Any, ...]],
        relative_bit: int,
        prefix: int,
        alpha2: int,
        min_support: int,
    ) -> tuple[int | None, int, int]:
        zeros = 0
        ones = 0
        support = 0
        for key in keys:
            counter = self.counts.get(key)
            if counter is None:
                continue
            for code, count in counter.items():
                code_bits = 8 * len(code)
                if relative_bit >= code_bits:
                    continue
                if relative_bit:
                    prior = int.from_bytes(code, "big") >> (code_bits - relative_bit)
                    if prior != prefix:
                        continue
                bit = (code[relative_bit // 8] >> (7 - (relative_bit & 7))) & 1
                zeros += count * int(bit == 0)
                ones += count * int(bit == 1)
                support += count
        if support < min_support:
            return None, 0, 0
        probability = ((2 * ones + alpha2) * TOTAL) // (2 * support + 2 * alpha2)
        return clamp_p1(probability), support, zeros + ones

    def state_bytes_estimate(self) -> int:
        return sum(
            32 + sum(8 + len(code) for code in counter)
            for counter in self.counts.values()
        )


def validate_event_cover(parsed: ParsedStore) -> None:
    expected = 6
    for event in parsed.events:
        if event.start != expected or event.end <= event.start:
            raise ValueError("WRT events do not form a contiguous causal stream")
        expected = event.end
    if expected != len(parsed.stream):
        raise ValueError("WRT events do not cover the complete text segment")


def run(
    *,
    store: Path,
    dictionary: Path,
    raw_input: Path,
    base_p1: Path,
    output_trace: Path,
    suffix_len: int,
    sketch_len: int,
    max_keys: int,
    codes_per_key: int,
    min_support: int,
    alpha2: int,
) -> dict[str, Any]:
    parsed = parse_store(store, dictionary)
    raw = raw_input.read_bytes()
    if raw != parsed.decoded:
        raise ValueError("exact WRT decode differs from raw input")
    validate_event_cover(parsed)
    rows = len(parsed.stream) * 8
    trace = P1Trace(base_p1)
    if trace.rows != rows:
        trace.close()
        raise ValueError("WRT stream and base P1 rows differ")

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

    semantic = RawSemanticState(suffix_len=suffix_len, sketch_len=sketch_len)
    table = EventContinuationTable(
        max_keys=max_keys, codes_per_key=codes_per_key
    )
    event_index = 0
    current_event: WrtEvent | None = None
    current_features: SemanticFeatures | None = None
    events = parsed.events
    row = 0
    active_rows = 0
    support_total = 0
    for position, byte in enumerate(parsed.stream):
        if position >= 6 and current_event is None:
            if event_index >= len(events) or events[event_index].start != position:
                raise ValueError("missing WRT event at stream position")
            current_event = events[event_index]
            current_features = semantic.features()
        for bit_position in range(8):
            bit = (byte >> (7 - bit_position)) & 1
            base_value = trace.p1(row)
            pair[row, 0] = base_value
            endpoint_value = base_value
            if current_event is not None and current_features is not None:
                relative_bit = (position - current_event.start) * 8 + bit_position
                current_prefix = event_prefix(current_event.encoded, relative_bit)
                retrieved, support, _hits = table.candidate(
                    current_features.keys(),
                    relative_bit,
                    current_prefix,
                    alpha2,
                    min_support,
                )
                if retrieved is not None:
                    endpoint_value = retrieved
                    active_rows += 1
                    support_total += support
            pair[row, 1] = endpoint_value
            row += 1
        if current_event is not None and position + 1 == current_event.end:
            assert current_features is not None
            table.update(current_features.keys(), current_event.encoded)
            semantic.observe(current_event.decoded)
            event_index += 1
            current_event = None
            current_features = None

    if event_index != len(events) or row != rows:
        raise ValueError("semantic retrieval replay did not consume exact stream")
    pair.flush()
    del pair
    trace.close()
    return {
        "schema": "wrt_event_srstc_trace_v1",
        "evidence_level": "causal_bounded_discovery_probability_trace",
        "claim_boundary": (
            "Retrieval endpoint trace only. Exact held-out blend replay, source "
            "cost, native integration, roundtrip, resources, and full-corpus "
            "official accounting remain required."
        ),
        "promotion_authorized": False,
        "inputs": {
            "store": artifact(store),
            "dictionary": artifact(dictionary),
            "raw_input": artifact(raw_input),
            "base_p1": artifact(base_p1),
        },
        "scope": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(parsed.stream),
            "rows": rows,
            "events": len(events),
        },
        "identity": {
            "raw_matches_exact_wrt_decode": True,
            "base_rows_copied_from_frozen_p1": True,
            "semantic_state_updates_after_completed_event": True,
            "continuations_insert_after_completed_event": True,
            "current_prefix_uses_prior_bits_only": True,
            "total_event_length_never_exposed": True,
        },
        "model": {
            "raw_context_suffix_bytes": suffix_len,
            "raw_context_sketch_bytes": sketch_len,
            "max_table_keys": max_keys,
            "codes_per_key": codes_per_key,
            "minimum_support": min_support,
            "active_rows": active_rows,
            "mean_active_support": support_total / active_rows if active_rows else 0.0,
            "table_keys": len(table.counts),
            "evicted_keys": table.evicted_keys,
            "rejected_codes": table.rejected_codes,
            "estimated_state_bytes": table.state_bytes_estimate(),
        },
        "output": artifact(output_trace),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit a causal WRT event SRSTC retrieval trace."
    )
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--base-p1", type=Path, required=True)
    parser.add_argument("--output-trace", type=Path, required=True)
    parser.add_argument("--output-receipt", type=Path, required=True)
    parser.add_argument("--suffix-len", type=int, default=32)
    parser.add_argument("--sketch-len", type=int, default=96)
    parser.add_argument("--max-keys", type=int, default=50_000)
    parser.add_argument("--codes-per-key", type=int, default=32)
    parser.add_argument("--min-support", type=int, default=4)
    parser.add_argument("--alpha2", type=int, default=1)
    args = parser.parse_args()
    receipt = run(
        store=args.store,
        dictionary=args.dictionary,
        raw_input=args.raw_input,
        base_p1=args.base_p1,
        output_trace=args.output_trace,
        suffix_len=args.suffix_len,
        sketch_len=args.sketch_len,
        max_keys=args.max_keys,
        codes_per_key=args.codes_per_key,
        min_support=args.min_support,
        alpha2=args.alpha2,
    )
    args.output_receipt.parent.mkdir(parents=True, exist_ok=True)
    args.output_receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
