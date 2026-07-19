#!/usr/bin/env python3
"""Emit a causal normalized WRT phrase endpoint paired with exact FX2 P1."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from typing import Sequence

import numpy as np

from wrt_exact import parse_store
from wrt_normalized_phrase_copy_shadow import (
    PhraseTable,
    actual_path_endpoints,
    validate_event_cover,
)
from wrt_title_token_automaton import iter_trace_bytes, sha256_file


PAIR_MAGIC = b"CMXAUX1\0"
P1_MAGIC = b"CMX21P1\0"
HEADER_BYTES = 16


def initialize_trace(path: Path, magic: bytes, rows: int, columns: int) -> np.memmap:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        stream.write(magic)
        stream.write(struct.pack("<Q", rows))
        stream.truncate(HEADER_BYTES + rows * columns * 2)
    shape = (rows, columns) if columns > 1 else (rows,)
    return np.memmap(path, dtype="<u2", mode="r+", offset=HEADER_BYTES, shape=shape)


def run(args: argparse.Namespace) -> dict[str, object]:
    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if raw != parsed.decoded or len(raw) != args.scope_bytes:
        raise ValueError("raw input does not match exact WRT decode and scope")
    validate_event_cover(parsed)
    rows = len(parsed.stream) * 8
    pair = initialize_trace(args.output_pair, PAIR_MAGIC, rows, 2)
    base = initialize_trace(args.output_base_p1, P1_MAGIC, rows, 1)
    table = PhraseTable("normalized")
    events = parsed.events
    event_index = 0
    current_event = None
    path: list[tuple[int, int] | None] = []
    row = 0
    active_rows = 0
    support_sum = 0
    trace_digest = hashlib.sha256()

    for byte_position, trace_byte in enumerate(iter_trace_bytes(args.trace)):
        if byte_position >= len(parsed.stream) or trace_byte.value != parsed.stream[byte_position]:
            raise ValueError("trace truth differs from exact WRT store")
        if byte_position >= 6 and current_event is None:
            if event_index >= len(events) or events[event_index].start != byte_position:
                raise ValueError("missing WRT event at stream position")
            current_event = events[event_index]
            candidate = table.candidates().get(args.context_length)
            path = (
                actual_path_endpoints(candidate, current_event.encoded)
                if candidate is not None
                else [None] * current_event.bit_length
            )
        trace_digest.update(bytes((trace_byte.value,)))
        for bit_position, base_p1 in enumerate(trace_byte.probabilities):
            endpoint_p1 = base_p1
            if current_event is not None:
                relative_bit = (byte_position - current_event.start) * 8 + bit_position
                endpoint = path[relative_bit]
                if endpoint is not None:
                    endpoint_p1, support = endpoint
                    active_rows += 1
                    support_sum += support
            base[row] = base_p1
            pair[row, 0] = base_p1
            pair[row, 1] = endpoint_p1
            row += 1
        if current_event is not None and byte_position + 1 == current_event.end:
            table.observe(current_event)
            event_index += 1
            current_event = None
            path = []

    if row != rows or event_index != len(events):
        raise ValueError("endpoint trace did not consume the exact WRT stream")
    pair.flush()
    base.flush()
    del pair
    del base
    receipt = {
        "schema_version": 1,
        "receipt_type": "wrt_normalized_phrase_endpoint_trace",
        "evidence_level": "causal_exact_fx2_paired_probability_trace",
        "claim_boundary": (
            "Endpoint trace only. Frozen calibration, exact replay, native "
            "integration, source cost, and full-corpus proof remain required."
        ),
        "scope_bytes": args.scope_bytes,
        "window_id": args.window_id,
        "model": {
            "signature_mode": "normalized",
            "context_length": args.context_length,
            "active_rows": active_rows,
            "mean_support": support_sum / active_rows if active_rows else 0.0,
            "events": event_index,
            "estimated_state_bytes": table.estimated_state_bytes(),
        },
        "identity": {
            "raw_matches_exact_wrt_decode": True,
            "events_update_after_completion": True,
            "current_event_path_uses_only_prior_truth_bits": True,
            "future_event_length_exposed_to_endpoint": False,
            "trace_matches_wrt_store": trace_digest.hexdigest()
            == hashlib.sha256(parsed.stream).hexdigest(),
            "base_column_copied_from_exact_fx2_trace": True,
        },
        "inputs": {
            "trace": {"bytes": args.trace.stat().st_size, "sha256": sha256_file(args.trace)},
            "wrt_store": {"bytes": args.wrt_store.stat().st_size, "sha256": sha256_file(args.wrt_store)},
            "raw_input": {"bytes": args.raw_input.stat().st_size, "sha256": sha256_file(args.raw_input)},
            "dictionary": {"bytes": args.dictionary.stat().st_size, "sha256": sha256_file(args.dictionary)},
        },
        "outputs": {
            "pair_trace": {"bytes": args.output_pair.stat().st_size, "sha256": sha256_file(args.output_pair)},
            "base_p1": {"bytes": args.output_base_p1.stat().st_size, "sha256": sha256_file(args.output_base_p1)},
        },
    }
    args.output_receipt.parent.mkdir(parents=True, exist_ok=True)
    args.output_receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--context-length", type=int, default=12)
    parser.add_argument("--output-pair", type=Path, required=True)
    parser.add_argument("--output-base-p1", type=Path, required=True)
    parser.add_argument("--output-receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    for path in (args.trace, args.wrt_store, args.dictionary, args.raw_input):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    if args.context_length not in (1, 2, 4, 8, 12):
        raise SystemExit("context length must be one of 1,2,4,8,12")
    receipt = run(args)
    print(json.dumps(receipt["model"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
