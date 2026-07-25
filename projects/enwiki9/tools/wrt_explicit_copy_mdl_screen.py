#!/usr/bin/env python3
"""Upper-bound MDL screen for causal explicit copies in an exact WRT stream."""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
from dataclasses import dataclass
import gzip
import hashlib
import json
from pathlib import Path

from wrt_exact import parse_store
from wrt_title_token_automaton import iter_trace_bytes, loss_qbits


MASK64 = (1 << 64) - 1
BASE1 = 0x9E3779B185EBCA87
BASE2 = 0xC2B2AE3D27D4EB4F
QBITS_PER_BIT = 256
QBITS_PER_BYTE = 2048


@dataclass(frozen=True)
class Copy:
    source: int
    length: int
    distance: int
    displaced_qbits: int
    command_bits: int
    net_qbits: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def gamma_bits(value: int) -> int:
    if value < 1:
        raise ValueError("gamma code requires a positive integer")
    return 2 * (value.bit_length() - 1) + 1


def rolling(values: list[int], base: int) -> tuple[list[int], list[int]]:
    prefix = [0] * (len(values) + 1)
    powers = [1] * (len(values) + 1)
    for index, value in enumerate(values):
        prefix[index + 1] = (prefix[index] * base + value + 1) & MASK64
        powers[index + 1] = (powers[index] * base) & MASK64
    return prefix, powers


def span_hash(prefix: list[int], powers: list[int], start: int, length: int) -> int:
    return (prefix[start + length] - prefix[start] * powers[length]) & MASK64


def partition(position: int, stream_bytes: int) -> str:
    if position < stream_bytes // 3:
        return "train"
    if position < 2 * stream_bytes // 3:
        return "development"
    return "holdout"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-events", type=int, default=2)
    parser.add_argument("--max-events", type=int, default=256)
    parser.add_argument("--max-candidates", type=int, default=8)
    args = parser.parse_args()

    for path in (args.trace, args.wrt_store, args.dictionary, args.raw_input):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    if args.min_events < 2 or args.max_events < args.min_events:
        raise SystemExit("invalid event-length bounds")
    if args.max_candidates < 1:
        raise SystemExit("max-candidates must be positive")

    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if raw != parsed.decoded:
        raise SystemExit("raw input does not match exact WRT decode")

    byte_cost_qbits: list[int] = []
    trace_truth = hashlib.sha256()
    for position, trace_byte in enumerate(iter_trace_bytes(args.trace)):
        if position >= len(parsed.stream) or trace_byte.value != parsed.stream[position]:
            raise SystemExit("trace truth differs from exact WRT stream")
        trace_truth.update(bytes((trace_byte.value,)))
        byte_cost_qbits.append(
            sum(
                loss_qbits(bit, probability)
                for probability, bit in zip(trace_byte.probabilities, trace_byte.bits)
            )
        )
    if len(byte_cost_qbits) != len(parsed.stream):
        raise SystemExit("trace length differs from exact WRT stream")

    byte_prefix = [0]
    for cost in byte_cost_qbits:
        byte_prefix.append(byte_prefix[-1] + cost)
    event_costs = [
        byte_prefix[event.end] - byte_prefix[event.start] for event in parsed.events
    ]
    event_prefix = [0]
    for cost in event_costs:
        event_prefix.append(event_prefix[-1] + cost)

    symbol_ids: dict[bytes, int] = {}
    symbols: list[int] = []
    for event in parsed.events:
        symbols.append(symbol_ids.setdefault(event.encoded, len(symbol_ids)))
    prefix1, powers1 = rolling(symbols, BASE1)
    prefix2, powers2 = rolling(symbols, BASE2)

    def same(left: int, right: int, length: int) -> bool:
        return (
            span_hash(prefix1, powers1, left, length)
            == span_hash(prefix1, powers1, right, length)
            and span_hash(prefix2, powers2, left, length)
            == span_hash(prefix2, powers2, right, length)
        )

    count = len(symbols)
    candidates: dict[tuple[int, int], deque[int]] = defaultdict(
        lambda: deque(maxlen=args.max_candidates)
    )
    best: list[Copy | None] = [None] * count
    match_starts = 0
    evaluated_sources = 0
    for index in range(count):
        completed = index - args.min_events
        if completed >= 0:
            key = (
                span_hash(prefix1, powers1, completed, args.min_events),
                span_hash(prefix2, powers2, completed, args.min_events),
            )
            candidates[key].append(completed)
        if index + args.min_events > count:
            continue
        key = (
            span_hash(prefix1, powers1, index, args.min_events),
            span_hash(prefix2, powers2, index, args.min_events),
        )
        prior_positions = candidates.get(key)
        if not prior_positions:
            continue
        match_starts += 1
        for source in reversed(prior_positions):
            evaluated_sources += 1
            maximum = min(args.max_events, count - index, index - source)
            if maximum < args.min_events:
                continue
            low = args.min_events
            high = maximum
            while low < high:
                middle = (low + high + 1) // 2
                if same(source, index, middle):
                    low = middle
                else:
                    high = middle - 1
            longest = low
            lengths = {args.min_events, longest}
            for boundary in (3, 7, 15, 31, 63, 127, 255):
                if args.min_events <= boundary <= longest:
                    lengths.add(boundary)
            for length in lengths:
                displaced = event_prefix[index + length] - event_prefix[index]
                distance = index - source
                command_bits = 1 + gamma_bits(distance) + gamma_bits(length)
                net = displaced - command_bits * QBITS_PER_BIT
                current = best[index]
                if net > 0 and (current is None or net > current.net_qbits):
                    best[index] = Copy(
                        source=source,
                        length=length,
                        distance=distance,
                        displaced_qbits=displaced,
                        command_bits=command_bits,
                        net_qbits=net,
                    )

    optimum = [0] * (count + 1)
    take = [False] * count
    for index in range(count - 1, -1, -1):
        optimum[index] = optimum[index + 1]
        copy = best[index]
        if copy is not None:
            value = copy.net_qbits + optimum[index + copy.length]
            if value > optimum[index]:
                optimum[index] = value
                take[index] = True

    selected: list[tuple[int, Copy]] = []
    index = 0
    while index < count:
        copy = best[index]
        if take[index] and copy is not None:
            if symbols[copy.source : copy.source + copy.length] != symbols[
                index : index + copy.length
            ]:
                raise SystemExit("selected rolling-hash match failed exact verification")
            selected.append((index, copy))
            index += copy.length
        else:
            index += 1

    by_partition: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    copied_events = 0
    copied_wrt_bytes = 0
    displaced_qbits = 0
    command_bits = 0
    for start, copy in selected:
        name = partition(parsed.events[start].start, len(parsed.stream))
        event_end = start + copy.length
        wrt_bytes = parsed.events[event_end - 1].end - parsed.events[start].start
        copied_events += copy.length
        copied_wrt_bytes += wrt_bytes
        displaced_qbits += copy.displaced_qbits
        command_bits += copy.command_bits
        row = by_partition[name]
        row["commands"] += 1
        row["copied_events"] += copy.length
        row["copied_wrt_bytes"] += wrt_bytes
        row["displaced_qbits"] += copy.displaced_qbits
        row["command_bits"] += copy.command_bits
        row["net_qbits"] += copy.net_qbits

    source_gzip9_bytes = len(gzip.compress(Path(__file__).read_bytes(), compresslevel=9))
    net_bytes = optimum[0] / QBITS_PER_BYTE
    projected_full_gain = net_bytes * 1000 - source_gzip9_bytes
    receipt = {
        "schema_version": 1,
        "receipt_type": "wrt_explicit_copy_mdl_upper_bound",
        "evidence_level": "causal_exact_event_match_optimistic_target_trace_mdl",
        "claim_boundary": (
            "Discovery upper bound only. It ignores literal/copy mode-stream cost, "
            "backend-state changes after removing WRT bytes, native integration, "
            "roundtrip, and full-corpus transfer."
        ),
        "inputs": {
            "trace": {
                "path": str(args.trace),
                "bytes": args.trace.stat().st_size,
                "sha256": sha256_file(args.trace),
            },
            "wrt_store": {
                "path": str(args.wrt_store),
                "bytes": args.wrt_store.stat().st_size,
                "sha256": sha256_file(args.wrt_store),
            },
            "dictionary": {
                "path": str(args.dictionary),
                "bytes": args.dictionary.stat().st_size,
                "sha256": sha256_file(args.dictionary),
            },
            "raw_input": {
                "path": str(args.raw_input),
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            },
        },
        "validations": {
            "raw_matches_exact_wrt_decode": True,
            "trace_matches_exact_wrt_stream": (
                trace_truth.hexdigest() == hashlib.sha256(parsed.stream).hexdigest()
            ),
            "references_are_prior_and_non_overlapping": all(
                copy.source + copy.length <= start for start, copy in selected
            ),
            "selected_matches_exactly_verified": True,
        },
        "model": {
            "events": count,
            "unique_encoded_events": len(symbol_ids),
            "minimum_copy_events": args.min_events,
            "maximum_copy_events": args.max_events,
            "candidate_sources_per_prefix": args.max_candidates,
            "match_starts": match_starts,
            "evaluated_sources": evaluated_sources,
            "distance_code": "Elias gamma over prior-event distance",
            "length_code": "Elias gamma over copied-event length",
            "opcode_bits_per_copy": 1,
            "literal_mode_stream_bits": 0,
        },
        "selection": {
            "method": "exact non-overlapping dynamic program over best copy per event",
            "commands": len(selected),
            "copied_events": copied_events,
            "copied_wrt_bytes": copied_wrt_bytes,
            "displaced_trace_bytes": displaced_qbits / QBITS_PER_BYTE,
            "command_bytes": command_bits / 8.0,
            "net_upper_bound_bytes": net_bytes,
            "net_upper_bound_bytes_per_million_raw": net_bytes * 1_000_000 / len(raw),
            "partitions": {
                name: {
                    **values,
                    "displaced_trace_bytes": values["displaced_qbits"] / QBITS_PER_BYTE,
                    "command_bytes": values["command_bits"] / 8.0,
                    "net_upper_bound_bytes": values["net_qbits"] / QBITS_PER_BYTE,
                }
                for name, values in sorted(by_partition.items())
            },
        },
        "economics": {
            "screen_source_gzip9_bytes": source_gzip9_bytes,
            "projected_full_gain_before_source_bytes": net_bytes * 1000,
            "projected_full_gain_after_screen_source_bytes": projected_full_gain,
            "target_debt_bytes_per_million": 57.404,
            "passes_debt_before_omitted_costs": (
                net_bytes * 1_000_000 / len(raw) > 57.404
            ),
        },
        "verdict": (
            "construct_exact_transform_and_measure_target_backend"
            if projected_full_gain > 57_404
            else "retire_explicit_copy_shape_by_optimistic_upper_bound"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "net_upper_bound_bytes": net_bytes,
                "commands": len(selected),
                "source_gzip9_bytes": source_gzip9_bytes,
                "projected_full_gain_after_screen_source_bytes": projected_full_gain,
                "verdict": receipt["verdict"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
