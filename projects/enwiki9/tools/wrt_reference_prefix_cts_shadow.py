#!/usr/bin/env python3
"""Score a causal prior-reference continuation model against exact FX2.

The model is active only inside legacy escaped Wikipedia reference bodies. It
indexes WRT-event continuations only after a reference has closed, so every
prediction is rebuildable from the decoded prefix. Contexts use normalized
completed WRT events and candidate event codes are filtered by the bits already
decoded from the current event. No current-reference length or future skeleton
is exposed.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence

from wrt_exact import ParsedStore, WrtEvent, parse_store, wrt_byte_transform
from wrt_title_token_automaton import (
    BLOCK_BYTES,
    Fx2RangeCounter,
    TOTAL,
    archive_payload_bytes,
    blend_probability,
    iter_trace_bytes,
    loss_qbits,
    sha256_file,
)


OPEN = b"&lt;ref"
TAG_END = b"&gt;"
CLOSE = b"&lt;/ref&gt;"
CONTEXT_LENGTHS = (0, 1, 2, 4, 8, 12)
MIN_SUPPORTS = (1, 2, 4)
BLENDS_PPM = (10_000, 25_000, 50_000, 100_000, 200_000)


def normalized_event_signature(event: WrtEvent) -> bytes:
    """Return a small causal signature while preserving structural tokens."""
    decoded = event.decoded.lower()
    if not decoded:
        logical = bytes(wrt_byte_transform(value) for value in event.encoded)
        return b"C" + logical
    output = bytearray()
    previous_class = -1
    for value in decoded:
        if ord("0") <= value <= ord("9"):
            current_class = 1
            normalized = ord("#")
        elif value in b" \t\r\n":
            current_class = 2
            normalized = ord(" ")
        else:
            current_class = 0
            normalized = value
        if current_class in (1, 2) and current_class == previous_class:
            continue
        output.append(normalized)
        previous_class = current_class
    return b"D" + bytes(output)


@dataclass
class ReferenceScanner:
    """Causal escaped-reference recognizer updated after completed events."""

    opening: bool = False
    in_body: bool = False
    tail: bytearray = field(default_factory=bytearray)
    opening_bytes: bytearray = field(default_factory=bytearray)
    current_events: list[WrtEvent] = field(default_factory=list)
    completed_references: int = 0
    self_closing_references: int = 0

    def _append_tail(self, value: int) -> None:
        self.tail.append(value)
        if len(self.tail) > len(CLOSE):
            del self.tail[: len(self.tail) - len(CLOSE)]

    def observe_event(self, event: WrtEvent) -> tuple[WrtEvent, ...] | None:
        was_in_body = self.in_body
        if was_in_body:
            self.current_events.append(event)
        closed = False
        for raw_value in event.decoded:
            value = raw_value + 32 if ord("A") <= raw_value <= ord("Z") else raw_value
            self._append_tail(value)
            if self.in_body:
                if bytes(self.tail).endswith(CLOSE):
                    self.in_body = False
                    closed = True
                continue
            if self.opening:
                self.opening_bytes.append(value)
                if bytes(self.opening_bytes).endswith(TAG_END):
                    stripped = bytes(self.opening_bytes).rstrip()
                    if stripped.endswith(b"/&gt;"):
                        self.self_closing_references += 1
                    else:
                        self.in_body = True
                        self.current_events.clear()
                    self.opening = False
                    self.opening_bytes.clear()
                continue
            if bytes(self.tail).endswith(OPEN):
                self.opening = True
                self.opening_bytes = bytearray(OPEN)
        if closed:
            completed = tuple(self.current_events)
            self.current_events.clear()
            self.completed_references += 1
            return completed
        return None


@dataclass
class ContinuationTable:
    counts: dict[int, dict[tuple[bytes, ...], Counter[bytes]]] = field(
        default_factory=lambda: {length: defaultdict(Counter) for length in CONTEXT_LENGTHS}
    )
    inserted_references: int = 0
    inserted_events: int = 0

    def add_transition(
        self, prior_events: Sequence[WrtEvent], event: WrtEvent
    ) -> None:
        signatures = [normalized_event_signature(item) for item in prior_events]
        for length in CONTEXT_LENGTHS:
            if length > len(signatures):
                continue
            context = tuple(signatures[-length:]) if length else ()
            self.counts[length][context][event.encoded] += 1
        self.inserted_events += 1

    def add_reference(self, events: Sequence[WrtEvent]) -> None:
        signatures = [normalized_event_signature(event) for event in events]
        for index, event in enumerate(events):
            for length in CONTEXT_LENGTHS:
                if length <= index:
                    context = tuple(signatures[index - length : index]) if length else ()
                    self.counts[length][context][event.encoded] += 1
        self.inserted_references += 1
        self.inserted_events += len(events)

    def candidates(
        self, current_events: Sequence[WrtEvent]
    ) -> dict[int, Counter[bytes]]:
        signatures = [normalized_event_signature(event) for event in current_events]
        result: dict[int, Counter[bytes]] = {}
        for length in CONTEXT_LENGTHS:
            if length > len(signatures):
                continue
            context = tuple(signatures[-length:]) if length else ()
            counter = self.counts[length].get(context)
            if counter:
                result[length] = counter
        return result

    def estimated_state_bytes(self) -> int:
        total = 0
        for contexts in self.counts.values():
            for context, counter in contexts.items():
                total += 24 + sum(len(value) + 8 for value in context)
                total += sum(len(code) + 8 for code in counter)
        return total


@dataclass(frozen=True)
class Variant:
    context_length: int
    min_support: int
    blend_ppm: int

    @property
    def variant_id(self) -> str:
        return f"refcts_k{self.context_length}_s{self.min_support}_b{self.blend_ppm}"


def variants() -> list[Variant]:
    return [
        Variant(context_length, min_support, blend_ppm)
        for context_length in CONTEXT_LENGTHS
        for min_support in MIN_SUPPORTS
        for blend_ppm in BLENDS_PPM
    ]


def candidate_probability(
    counter: Counter[bytes],
    relative_bit: int,
    prefix: int,
    base_p1: int,
    variant: Variant,
) -> tuple[int, int] | None:
    zeros = 0
    ones = 0
    for code, count in counter.items():
        code_bits = 8 * len(code)
        if relative_bit >= code_bits:
            continue
        if relative_bit:
            prior = int.from_bytes(code, "big") >> (code_bits - relative_bit)
            if prior != prefix:
                continue
        bit = (code[relative_bit // 8] >> (7 - (relative_bit & 7))) & 1
        if bit:
            ones += count
        else:
            zeros += count
    support = zeros + ones
    if support < variant.min_support:
        return None
    endpoint_p1 = ((2 * ones + 1) * TOTAL) // (2 * support + 2)
    endpoint_p1 = max(1, min(TOTAL - 1, endpoint_p1))
    return blend_probability(base_p1, endpoint_p1, variant.blend_ppm), support


@dataclass
class VariantStats:
    variant: Variant
    qbits: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    eligible_bits: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    active_references: set[int] = field(default_factory=set)
    block_qbits: dict[int, int] = field(default_factory=lambda: defaultdict(int))
    support_sum: int = 0
    positive_event_oracle_qbits: dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    negative_event_qbits: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    positive_events: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    regressing_events: dict[str, int] = field(default_factory=lambda: defaultdict(int))


def partition_for(reference_ordinal: int, total_references: int) -> str:
    if total_references <= 2:
        return "all"
    first = total_references // 3
    second = (2 * total_references) // 3
    if reference_ordinal < first:
        return "train"
    if reference_ordinal < second:
        return "development"
    return "holdout"


def validate_event_cover(parsed: ParsedStore) -> None:
    expected = 6
    for event in parsed.events:
        if event.start != expected or event.end <= event.start:
            raise ValueError("WRT events do not form a contiguous causal stream")
        expected = event.end
    if expected != len(parsed.stream):
        raise ValueError("WRT events do not cover the complete text segment")


def count_reference_bodies(raw: bytes) -> int:
    lower = raw.lower()
    count = 0
    cursor = 0
    while True:
        start = lower.find(OPEN, cursor)
        if start < 0:
            return count
        tag_end = lower.find(TAG_END, start + len(OPEN))
        if tag_end < 0:
            return count
        tag = lower[start : tag_end + len(TAG_END)]
        cursor = tag_end + len(TAG_END)
        if tag.rstrip().endswith(b"/&gt;"):
            continue
        close = lower.find(CLOSE, cursor)
        if close < 0:
            continue
        count += 1
        cursor = close + len(CLOSE)


def score(
    trace: Path,
    parsed: ParsedStore,
    candidate_variants: Sequence[Variant],
    total_references: int,
    exact_ids: set[str] | None = None,
) -> tuple[dict[str, VariantStats], dict[str, object]]:
    stats = {variant.variant_id: VariantStats(variant) for variant in candidate_variants}
    exact_ids = exact_ids or set()
    exact = {variant_id: Fx2RangeCounter() for variant_id in exact_ids}
    baseline = Fx2RangeCounter() if exact_ids else None
    scanner = ReferenceScanner()
    table = ContinuationTable()
    events = parsed.events
    event_index = 0
    current_event: WrtEvent | None = None
    current_candidates: dict[int, Counter[bytes]] = {}
    reference_ordinal: int | None = None
    event_partition = "outside"
    event_deltas: dict[str, int] = defaultdict(int)
    trace_bytes = 0
    trace_sha = hashlib.sha256()

    for byte_position, trace_byte in enumerate(iter_trace_bytes(trace)):
        if byte_position >= len(parsed.stream) or trace_byte.value != parsed.stream[byte_position]:
            raise ValueError("trace truth differs from exact WRT store")
        if byte_position >= 6 and current_event is None:
            if event_index >= len(events) or events[event_index].start != byte_position:
                raise ValueError("missing WRT event at stream position")
            current_event = events[event_index]
            if scanner.in_body:
                current_candidates = table.candidates(scanner.current_events)
                reference_ordinal = scanner.completed_references
                event_partition = partition_for(reference_ordinal, total_references)
            else:
                current_candidates = {}
                reference_ordinal = None
                event_partition = "outside"
            event_deltas.clear()
        trace_sha.update(bytes((trace_byte.value,)))
        trace_bytes += 1
        prefix = 0
        for bit_position, (base_p1, bit) in enumerate(
            zip(trace_byte.probabilities, trace_byte.bits)
        ):
            if baseline is not None:
                baseline.encode(bit, base_p1)
            relative_bit = 0
            if current_event is not None:
                relative_bit = (byte_position - current_event.start) * 8 + bit_position
            partition = (
                partition_for(reference_ordinal, total_references)
                if reference_ordinal is not None
                else "outside"
            )
            if not current_candidates and not exact:
                prefix = (prefix << 1) | bit
                continue
            for variant_id, state in stats.items():
                chosen = base_p1
                counter = current_candidates.get(state.variant.context_length)
                candidate = None
                if counter is not None and current_event is not None:
                    candidate = candidate_probability(
                        counter, relative_bit, prefix, base_p1, state.variant
                    )
                if candidate is not None:
                    chosen, support = candidate
                    delta = loss_qbits(bit, base_p1) - loss_qbits(bit, chosen)
                    state.qbits[partition] += delta
                    state.qbits["all"] += delta
                    state.eligible_bits[partition] += 1
                    state.eligible_bits["all"] += 1
                    state.support_sum += support
                    assert reference_ordinal is not None
                    state.active_references.add(reference_ordinal)
                    state.block_qbits[byte_position // BLOCK_BYTES] += delta
                    event_deltas[variant_id] += delta
                if variant_id in exact:
                    exact[variant_id].encode(bit, chosen)
            prefix = (prefix << 1) | bit
        if current_event is not None and byte_position + 1 == current_event.end:
            for variant_id, delta in event_deltas.items():
                state = stats[variant_id]
                if delta > 0:
                    state.positive_event_oracle_qbits[event_partition] += delta
                    state.positive_event_oracle_qbits["all"] += delta
                    state.positive_events[event_partition] += 1
                    state.positive_events["all"] += 1
                elif delta < 0:
                    state.negative_event_qbits[event_partition] += delta
                    state.negative_event_qbits["all"] += delta
                    state.regressing_events[event_partition] += 1
                    state.regressing_events["all"] += 1
            completed = scanner.observe_event(current_event)
            if completed is not None:
                table.add_reference(completed)
            event_index += 1
            current_event = None
            current_candidates = {}
            reference_ordinal = None

    if trace_bytes != len(parsed.stream) or event_index != len(events):
        raise ValueError("trace replay did not consume the complete WRT stream")
    if scanner.in_body:
        raise ValueError("trace ended inside a reference body")
    if scanner.completed_references != total_references:
        raise ValueError(
            "causal reference scanner disagrees with the raw reference census: "
            f"{scanner.completed_references} != {total_references}"
        )
    exact_rows: dict[str, object] = {}
    if baseline is not None:
        baseline.finish()
        for variant_id, coder in exact.items():
            coder.finish()
            exact_rows[variant_id] = {
                "baseline_payload_bytes": baseline.bytes,
                "candidate_payload_bytes": coder.bytes,
                "saved_bytes": baseline.bytes - coder.bytes,
            }
    return stats, {
        "trace_bytes": trace_bytes,
        "trace_sha256": trace_sha.hexdigest(),
        "completed_references": scanner.completed_references,
        "self_closing_references": scanner.self_closing_references,
        "inserted_references": table.inserted_references,
        "inserted_events": table.inserted_events,
        "estimated_state_bytes": table.estimated_state_bytes(),
        "exact": exact_rows,
    }


def row_for(state: VariantStats, scope_bytes: int) -> dict[str, object]:
    partitions = {}
    for partition in ("train", "development", "holdout", "all"):
        qbits = state.qbits.get(partition, 0)
        partitions[partition] = {
            "qbits_saved": qbits,
            "saved_bytes": qbits / 2048.0,
            "bytes_per_million": qbits / 2048.0 * 1_000_000 / scope_bytes,
            "eligible_bits": state.eligible_bits.get(partition, 0),
            "positive_event_oracle_saved_bytes": (
                state.positive_event_oracle_qbits.get(partition, 0) / 2048.0
            ),
            "negative_event_saved_bytes": (
                state.negative_event_qbits.get(partition, 0) / 2048.0
            ),
            "positive_events": state.positive_events.get(partition, 0),
            "regressing_events": state.regressing_events.get(partition, 0),
        }
    blocks = list(state.block_qbits.values())
    return {
        "variant_id": state.variant.variant_id,
        "context_length": state.variant.context_length,
        "minimum_support": state.variant.min_support,
        "blend_ppm": state.variant.blend_ppm,
        "partitions": partitions,
        "active_references": len(state.active_references),
        "mean_support": (
            state.support_sum / state.eligible_bits.get("all", 1)
            if state.eligible_bits.get("all", 0)
            else 0.0
        ),
        "positive_blocks": sum(value > 0 for value in blocks),
        "regressing_blocks": sum(value < 0 for value in blocks),
        "worst_block_saved_bytes": min(blocks, default=0) / 2048.0,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--trace-guard", type=Path)
    parser.add_argument("--trace-binary", type=Path)
    parser.add_argument("--trace-source-commit")
    parser.add_argument("--trace-source-patch", type=Path)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--phase", choices=("selection", "confirmation"), required=True)
    parser.add_argument("--variant-id")
    parser.add_argument("--exact-top", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    for path in (args.trace, args.wrt_store, args.dictionary, args.raw_input):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    if args.archive and not args.archive.is_file():
        raise SystemExit(f"missing archive: {args.archive}")
    for path in (args.trace_guard, args.trace_binary, args.trace_source_patch):
        if path and not path.is_file():
            raise SystemExit(f"missing trace provenance input: {path}")
    if args.scope_bytes <= 0 or args.exact_top <= 0:
        raise SystemExit("scope and exact-top must be positive")

    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if raw != parsed.decoded or len(raw) != args.scope_bytes:
        raise SystemExit("raw input does not match the exact WRT decode and scope")
    validate_event_cover(parsed)
    total_references = count_reference_bodies(raw)
    grid = variants()
    if args.variant_id:
        grid = [variant for variant in grid if variant.variant_id == args.variant_id]
        if len(grid) != 1:
            raise SystemExit(f"unknown variant: {args.variant_id}")
    first, diagnostics = score(args.trace, parsed, grid, total_references)
    rows = [row_for(state, args.scope_bytes) for state in first.values()]
    rows.sort(
        key=lambda row: (
            -float(row["partitions"]["development"]["saved_bytes"]),
            -float(row["partitions"]["holdout"]["saved_bytes"]),
            str(row["variant_id"]),
        )
    )
    exact_ids = {str(row["variant_id"]) for row in rows[: args.exact_top]}
    exact_grid = [variant for variant in grid if variant.variant_id in exact_ids]
    _, exact_diagnostics = score(
        args.trace, parsed, exact_grid, total_references, exact_ids
    )
    exact = exact_diagnostics["exact"]
    for row in rows:
        row["exact"] = exact.get(str(row["variant_id"]))

    validations: dict[str, object] = {
        "raw_matches_exact_wrt_decode": True,
        "trace_matches_wrt_store": diagnostics["trace_sha256"]
        == hashlib.sha256(parsed.stream).hexdigest(),
        "events_released_after_completion": True,
        "reference_inserted_only_after_close": True,
        "current_event_prefix_uses_prior_bits_only": True,
        "future_reference_length_exposed": False,
    }
    if args.archive:
        payload_bytes, archive_wrt_bytes = archive_payload_bytes(args.archive)
        baseline_values = {
            int(value["baseline_payload_bytes"]) for value in exact.values()
        }
        validations["archive"] = {
            "bytes": args.archive.stat().st_size,
            "sha256": sha256_file(args.archive),
            "payload_bytes": payload_bytes,
            "wrt_bytes": archive_wrt_bytes,
            "baseline_range_match": baseline_values == {payload_bytes},
            "trace_wrt_bytes_match": archive_wrt_bytes == diagnostics["trace_bytes"],
        }
    best = rows[0] if rows else None
    best_holdout = (
        max(
            rows,
            key=lambda row: float(row["partitions"]["holdout"]["saved_bytes"]),
        )
        if rows
        else None
    )
    trace_generation = None
    if args.trace_guard or args.trace_binary or args.trace_source_commit or args.trace_source_patch:
        trace_generation = {
            "source_commit": args.trace_source_commit,
            "source_patch": (
                {
                    "sha256": sha256_file(args.trace_source_patch),
                    "bytes": args.trace_source_patch.stat().st_size,
                }
                if args.trace_source_patch
                else None
            ),
            "binary": (
                {
                    "sha256": sha256_file(args.trace_binary),
                    "bytes": args.trace_binary.stat().st_size,
                }
                if args.trace_binary
                else None
            ),
            "guard": json.loads(args.trace_guard.read_text()) if args.trace_guard else None,
        }
    output = {
        "schema_version": 1,
        "receipt_type": "wrt_reference_prefix_cts_shadow",
        "evidence_level": "causal_exact_fx2_probability_trace_shadow",
        "claim_boundary": (
            "Selection-window causal shadow only. This is not integrated source, "
            "a native candidate archive, a full-corpus score, or a 10.80% proof."
        ),
        "window_id": args.window_id,
        "phase": args.phase,
        "scope_bytes": args.scope_bytes,
        "substrate": "raw_fx2",
        "inputs": {
            "trace": {"sha256": sha256_file(args.trace), "bytes": args.trace.stat().st_size},
            "wrt_store": {"sha256": sha256_file(args.wrt_store), "bytes": args.wrt_store.stat().st_size},
            "raw_input": {"sha256": sha256_file(args.raw_input), "bytes": args.raw_input.stat().st_size},
            "dictionary": {"sha256": sha256_file(args.dictionary), "bytes": args.dictionary.stat().st_size},
        },
        "trace_generation": trace_generation,
        "model": {
            "reference_syntax": "legacy escaped &lt;ref ...&gt; ... &lt;/ref&gt;",
            "contexts": list(CONTEXT_LENGTHS),
            "minimum_supports": list(MIN_SUPPORTS),
            "blend_ppm": list(BLENDS_PPM),
            "normalization": "lowercase decoded WRT event; collapse digit and whitespace runs",
            **{key: value for key, value in diagnostics.items() if key != "exact"},
        },
        "economics": {
            "target_gap_bytes": 57_404,
            "required_gain_bytes_per_million_before_program_cost": 57.404,
            "program_cost_counted": False,
        },
        "validations": validations,
        "selection_rule": "maximize development qbit savings, break ties by holdout then id",
        "best_by_selection_rule": best,
        "best_holdout_diagnostic": best_holdout,
        "rows": rows,
        "verdict": (
            "freeze_variant_and_run_disjoint_confirmation"
            if best
            and float(best["partitions"]["development"]["saved_bytes"]) > 0
            and float(best["partitions"]["holdout"]["saved_bytes"]) > 0
            and int((best.get("exact") or {}).get("saved_bytes", 0)) > 0
            else "retire_unchanged_or_redesign_endpoint"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"best": best, "verdict": output["verdict"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
