#!/usr/bin/env python3
"""Emit a causal typed Skip-CTS endpoint over an exact WRT stream.

The endpoint maintains suffix histories separately for decoder-rebuilt Wiki
regimes, thereby skipping intervening events from unrelated regimes.  Binary
contexts also include a coarse bucket of the exact base probability, making
the model a residual calibrator rather than a standalone language model.
"""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import struct
from typing import Any, Sequence

import numpy as np

from causal_state_screen import WikiState
from wrt_exact import (
    ParsedStore,
    TEXT_SEGMENT,
    WrtEvent,
    parse_store,
    wrt_byte_transform,
)
from wrt_title_token_automaton import unit_from_event


P1_MAGIC = b"CMX21P1\0"
P1_HEADER_BYTES = 16
PAIR_MAGIC = b"CMXAUX1\0"
PAIR_HEADER_BYTES = 16
TOTAL = 65_536
Q24 = 1 << 24
PROFILES = ("plain", "phase", "global", "field", "mode", "slot", "page_slot")


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


def probability_bucket(p1: int, buckets: int) -> int:
    return min(buckets - 1, (int(p1) * buckets) // TOTAL)


def causal_event_prefix(event: WrtEvent, event_phase: int) -> int:
    if not 0 <= event_phase < len(event.encoded):
        raise ValueError("event phase is outside the encoded WRT event")
    if event_phase == 0:
        return 0
    value = 1
    for encoded in event.encoded[:event_phase]:
        value = (value << 8) | int(encoded)
    return value


def suffixes(history: deque[int], max_order: int) -> list[tuple[int, ...]]:
    recent = tuple(history)
    return [
        recent[len(recent) - depth :] if depth else ()
        for depth in range(min(max_order, len(recent)) + 1)
    ]


def regime_keys(state: WikiState, profile: str) -> tuple[tuple[Any, ...], ...]:
    if profile in {"plain", "phase", "global"}:
        return ()
    field_id = state.field_id
    mode = state.mode
    slot = state.slot
    page_kind = state.page_kind
    keys: list[tuple[Any, ...]] = [("field", field_id)]
    if profile in {"mode", "slot", "page_slot"}:
        keys.append(("field_mode", field_id, mode))
    if profile in {"slot", "page_slot"}:
        keys.append(("field_mode_slot", field_id, mode, slot))
    if profile == "page_slot":
        keys.append(("page_field_mode_slot", page_kind, field_id, mode, slot))
    return tuple(keys)


@dataclass
class ContextBudget:
    cap: int
    used: int = 0
    blocked: int = 0

    def claim(self) -> bool:
        if self.used >= self.cap:
            self.blocked += 1
            return False
        self.used += 1
        return True


@dataclass
class CountTable:
    budget: ContextBudget
    counts: dict[tuple[Any, ...], list[int]] = field(default_factory=dict)

    def predict_q24(
        self,
        keys: Sequence[tuple[Any, ...]],
        prior_q24: int,
    ) -> tuple[int, int]:
        probability = prior_q24
        matches = 0
        for key in keys:
            counts = self.counts.get(key)
            if counts is None:
                continue
            zero, one = counts
            total = zero + one
            distinct = int(zero > 0) + int(one > 0)
            adjusted_one_twice = max(2 * one - 1, 0)
            denominator_twice = 2 * total + 2
            probability = (
                adjusted_one_twice * Q24
                + (2 + distinct) * probability
                + denominator_twice // 2
            ) // denominator_twice
            probability = min(Q24 - 1, max(1, probability))
            matches += 1
        return probability, matches

    def update(self, keys: Sequence[tuple[Any, ...]], bit: int) -> None:
        for key in keys:
            counts = self.counts.get(key)
            if counts is None:
                if not self.budget.claim():
                    continue
                counts = [0, 0]
                self.counts[key] = counts
            counts[bit] += 1


class TypedSkipCTS:
    def __init__(
        self,
        *,
        max_order: int,
        max_contexts: int,
        p_buckets: int,
        profile: str,
    ) -> None:
        if max_order < 0 or max_contexts < 1 or p_buckets < 2:
            raise ValueError("invalid typed Skip-CTS bounds")
        if profile not in PROFILES:
            raise ValueError(f"unsupported typed profile: {profile}")
        self.max_order = max_order
        self.p_buckets = p_buckets
        self.profile = profile
        self.budget = ContextBudget(max_contexts)
        self.table = CountTable(self.budget)
        self.global_history: deque[int] = deque(maxlen=max_order)
        self.typed_histories: dict[tuple[Any, ...], deque[int]] = {}
        self.events_completed = 0
        self.active_rows = 0
        self.maximum_matches = 0

    def _history(self, regime: tuple[Any, ...]) -> deque[int]:
        history = self.typed_histories.get(regime)
        if history is None:
            history = deque(maxlen=self.max_order)
            self.typed_histories[regime] = history
        return history

    def _keys(
        self,
        *,
        regimes: Sequence[tuple[Any, ...]],
        event_prefix_key: int,
        event_phase: int,
        bit_position: int,
        prefix: int,
        p_bucket: int,
    ) -> list[tuple[Any, ...]]:
        common = (event_prefix_key, event_phase, bit_position, prefix, p_bucket)
        keys = [
            (("global",), *common, suffix)
            for suffix in suffixes(self.global_history, self.max_order)
        ]
        for regime in regimes:
            keys.extend(
                (regime, *common, suffix)
                for suffix in suffixes(self._history(regime), self.max_order)
            )
        return keys

    def predict_then_update(
        self,
        *,
        regimes: Sequence[tuple[Any, ...]],
        event_prefix_key: int,
        event_phase: int,
        bit_position: int,
        prefix: int,
        base_p1: int,
        bit: int,
    ) -> int:
        keys = self._keys(
            regimes=regimes,
            event_prefix_key=event_prefix_key,
            event_phase=event_phase,
            bit_position=bit_position,
            prefix=prefix,
            p_bucket=probability_bucket(base_p1, self.p_buckets),
        )
        prior_q24 = (int(base_p1) * Q24 + TOTAL // 2) // TOTAL
        probability, matches = self.table.predict_q24(keys, prior_q24)
        self.table.update(keys, bit)
        if matches:
            self.active_rows += 1
            self.maximum_matches = max(self.maximum_matches, matches)
        endpoint_p1 = (probability * TOTAL + Q24 // 2) // Q24
        return min(TOTAL - 1, max(1, endpoint_p1))

    def observe_event(
        self,
        event: WrtEvent,
        regimes: Sequence[tuple[Any, ...]],
    ) -> None:
        signature = unit_from_event(event).signature
        self.global_history.append(signature)
        for regime in regimes:
            self._history(regime).append(signature)
        self.events_completed += 1


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
    max_order: int,
    max_contexts: int,
    p_buckets: int,
    profile: str,
) -> dict[str, Any]:
    parsed = parse_store(store, dictionary)
    raw = raw_input.read_bytes()
    if raw != parsed.decoded:
        raise ValueError("exact WRT decode differs from raw input")
    validate_event_cover(parsed)
    rows = len(parsed.stream) * 8
    if read_p1_rows(base_p1) != rows:
        raise ValueError("WRT stream and base P1 rows differ")
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

    model = TypedSkipCTS(
        max_order=max_order,
        max_contexts=max_contexts,
        p_buckets=p_buckets,
        profile=profile,
    )
    wiki = WikiState()
    event_index = 0
    current_event: WrtEvent | None = None
    current_regimes: tuple[tuple[Any, ...], ...] = ()
    row = 0
    for byte_position, byte in enumerate(parsed.stream):
        if byte_position < 6:
            event_prefix_key = 0
            event_phase = byte_position
            current_event = None
            current_regimes = ()
        else:
            if current_event is None:
                if event_index >= len(parsed.events):
                    raise ValueError("missing WRT event for stream position")
                current_event = parsed.events[event_index]
                if current_event.start != byte_position:
                    raise ValueError("WRT event starts at an unexpected position")
                current_regimes = regime_keys(wiki, profile)
            event_phase = byte_position - current_event.start
            # Only already completed bytes of the current WRT event enter the
            # key.  Total event length is never exposed: for F0-FF prefixes it
            # is not known until the second encoded byte itself is decoded.
            event_prefix_key = causal_event_prefix(current_event, event_phase)
            if profile == "plain":
                event_prefix_key = 0
                event_phase = 0
            elif profile == "phase":
                event_prefix_key = 0

        prefix = 0
        for bit_position in range(8):
            bit = (byte >> (7 - bit_position)) & 1
            base_value = int(base[row])
            pair[row, 0] = base_value
            if current_event is None:
                endpoint_value = base_value
            else:
                endpoint_value = model.predict_then_update(
                    regimes=current_regimes,
                    event_prefix_key=event_prefix_key,
                    event_phase=event_phase,
                    bit_position=bit_position,
                    prefix=prefix,
                    base_p1=base_value,
                    bit=bit,
                )
            pair[row, 1] = endpoint_value
            prefix = (prefix << 1) | bit
            row += 1

        if current_event is not None and byte_position + 1 == current_event.end:
            model.observe_event(current_event, current_regimes)
            for decoded_byte in current_event.decoded:
                wiki.update(decoded_byte)
            event_index += 1
            current_event = None
            current_regimes = ()

    if event_index != len(parsed.events) or row != rows:
        raise ValueError("typed Skip-CTS replay did not consume the exact stream")
    pair.flush()
    del pair
    del base
    estimated_state_bytes = model.budget.used * 24
    return {
        "schema": "wrt_typed_skip_cts_trace_v1",
        "evidence_level": "causal_bounded_discovery_probability_trace",
        "inputs": {
            "store": artifact(store),
            "dictionary": artifact(dictionary),
            "raw_input": artifact(raw_input),
            "base_p1": artifact(base_p1),
        },
        "output": artifact(output_trace),
        "scope": {
            "raw_bytes": parsed.raw_length,
            "wrt_bytes": len(parsed.stream),
            "rows": rows,
            "events": len(parsed.events),
        },
        "model": {
            "profile": profile,
            "max_token_order": max_order,
            "probability_buckets": p_buckets,
            "max_contexts": max_contexts,
            "contexts_used": model.budget.used,
            "context_insertions_blocked": model.budget.blocked,
            "typed_histories": len(model.typed_histories),
            "events_completed": model.events_completed,
            "active_rows": model.active_rows,
            "maximum_hierarchical_matches": model.maximum_matches,
            "estimated_native_state_bytes_at_24_per_context": estimated_state_bytes,
            "probability_math": "deterministic_integer_Q24_HPYP_backoff",
        },
        "identity": {
            "raw_matches_exact_wrt_decode": True,
            "base_rows_copied_from_frozen_p1": True,
            "updates_after_current_true_bit": True,
            "events_released_after_final_encoded_byte": True,
            "total_event_length_never_exposed": True,
            "current_event_key_uses_completed_bytes_only": True,
            "typed_histories_skip_intervening_regimes": True,
            "base_probability_bucket_is_decoder_available": True,
        },
        "promotion_authorized": False,
        "claim_boundary": (
            "Causal endpoint trace only. Exact blend replay, held-out economics, "
            "native source/state cost, roundtrip, and full-corpus proof remain."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--base-p1", type=Path, required=True)
    parser.add_argument("--output-trace", type=Path, required=True)
    parser.add_argument("--output-receipt", type=Path, required=True)
    parser.add_argument("--profile", choices=PROFILES, default="slot")
    parser.add_argument("--max-order", type=int, default=3)
    parser.add_argument("--max-contexts", type=int, default=500_000)
    parser.add_argument("--p-buckets", type=int, default=16)
    args = parser.parse_args(argv)
    receipt = run(
        store=args.store,
        dictionary=args.dictionary,
        raw_input=args.raw_input,
        base_p1=args.base_p1,
        output_trace=args.output_trace,
        max_order=args.max_order,
        max_contexts=args.max_contexts,
        p_buckets=args.p_buckets,
        profile=args.profile,
    )
    args.output_receipt.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output_receipt.with_suffix(args.output_receipt.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output_receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
