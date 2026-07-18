#!/usr/bin/env python3
"""Score a causal WRT title-token endpoint against compact FX2 probabilities.

The compact trace contains only FX2's pre-bit probability and the true bit.
This tool reconstructs the exact WRT byte stream, tokenizes it with the same
dictionary code contract, rebuilds current and previous page titles, and
scores title-token predictions without rewriting the stream.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Iterable, Iterator, Sequence

from wrt_exact import (
    ParsedStore,
    TEXT_SEGMENT,
    WrtEvent,
    parse_store,
    read_dictionary_words,
    token_index,
    wrt_byte_transform,
)


TRACE_MAGIC = b"FX2PT01\n"
TRACE_RECORD = struct.Struct("<HB")
TOTAL = 1 << 16
MAX_CODE = (1 << 32) - 1
TITLE_CONTEXTS = (1, 2, 3, 4, 6, 8)
BLENDS_PPM = (10_000, 25_000, 50_000, 100_000, 200_000)
EXPERT_ONE = 63_488
EXPERT_ZERO = TOTAL - EXPERT_ONE
BLOCK_BYTES = 65_536


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


char_swap = wrt_byte_transform
load_dictionary = read_dictionary_words


@dataclass(frozen=True)
class TraceByte:
    value: int
    probabilities: tuple[int, ...]
    bits: tuple[int, ...]


def iter_trace_bytes(path: Path) -> Iterator[TraceByte]:
    with path.open("rb") as handle:
        if handle.read(len(TRACE_MAGIC)) != TRACE_MAGIC:
            raise ValueError("invalid compact FX2 trace header")
        while True:
            chunk = handle.read(8 * TRACE_RECORD.size)
            if not chunk:
                break
            if len(chunk) != 8 * TRACE_RECORD.size:
                raise ValueError("compact trace ends inside a WRT byte")
            probabilities: list[int] = []
            bits: list[int] = []
            value = 0
            for p1, bit in TRACE_RECORD.iter_unpack(chunk):
                if not 1 <= p1 < TOTAL or bit not in (0, 1):
                    raise ValueError("invalid compact trace record")
                probabilities.append(p1)
                bits.append(bit)
                value = (value << 1) | bit
            yield TraceByte(value, tuple(probabilities), tuple(bits))


@dataclass(frozen=True)
class WrtUnit:
    signature: int
    encoded: bytes
    decoded: bytes


def unit_from_event(event: WrtEvent) -> WrtUnit:
    logical = bytes(wrt_byte_transform(value) for value in event.encoded)
    if event.kind == "token":
        signature = token_index(logical)
    elif event.kind == "escaped_literal":
        if len(logical) != 2:
            raise ValueError("invalid escaped WRT event")
        signature = 0x30000 + logical[1]
    elif event.kind == "control":
        if len(logical) != 1:
            raise ValueError("invalid WRT control event")
        signature = 0x20000 + logical[0]
    elif event.kind == "literal":
        if len(logical) != 1:
            raise ValueError("invalid WRT literal event")
        signature = 0x10000 + logical[0]
    else:
        raise ValueError(f"unsupported WRT event kind: {event.kind}")
    return WrtUnit(signature, event.encoded, event.decoded)


class WikiState:
    def __init__(self) -> None:
        self.in_tag = False
        self.tag_closing = False
        self.tag_name_done = False
        self.tag = bytearray()
        self.previous = 0
        self.page_mode = False
        self.title_mode = False
        self.prose_mode = False
        self.page_boundary = 0

    def _finish_tag(self, self_closing: bool) -> None:
        tag = bytes(self.tag).lower()
        closing = self.tag_closing
        if tag == b"page":
            self.page_boundary = 2 if closing else 1
            self.page_mode = not closing
        elif tag == b"title":
            self.title_mode = not closing
        elif tag == b"text":
            self.prose_mode = not closing
        self.tag.clear()
        self.tag_closing = False
        self.tag_name_done = False

    def feed(self, data: bytes) -> None:
        self.page_boundary = 0
        for value in data:
            if value == ord("<"):
                self.in_tag = True
                self.tag.clear()
                self.tag_closing = False
                self.tag_name_done = False
            elif self.in_tag:
                if not self.tag and not self.tag_name_done and value == ord("/"):
                    self.tag_closing = True
                elif not self.tag_name_done and (
                    ord("A") <= value <= ord("Z")
                    or ord("a") <= value <= ord("z")
                    or ord("0") <= value <= ord("9")
                ):
                    if len(self.tag) < 24:
                        self.tag.append(value)
                elif self.tag and value != ord("/"):
                    self.tag_name_done = True
                if value == ord(">"):
                    self._finish_tag(self.previous == ord("/"))
                    self.in_tag = False
            self.previous = value


@dataclass(frozen=True)
class Rule:
    encoded: bytes
    best_count: int
    total: int


@dataclass(frozen=True)
class Endpoint:
    expected_byte: int
    match_tokens: int
    best_count: int
    total: int


class TitleTokenModel:
    def __init__(self, max_context: int = max(TITLE_CONTEXTS)) -> None:
        self.max_context = max_context
        self.rules: dict[tuple[int, ...], Rule] = {}
        self.recent: list[int] = []
        self.expected = b""
        self.expected_index = 0
        self.expected_rule: Rule | None = None
        self.expected_match = 0

    def build(self, units: Sequence[WrtUnit]) -> None:
        histograms: dict[tuple[int, ...], Counter[bytes]] = {}
        signatures = [unit.signature for unit in units]
        for next_index in range(1, len(units)):
            for length in range(1, min(self.max_context, next_index) + 1):
                context = tuple(signatures[next_index - length : next_index])
                histograms.setdefault(context, Counter())[units[next_index].encoded] += 1
        self.rules.clear()
        for context, counts in histograms.items():
            encoded, best_count = min(
                counts.items(), key=lambda item: (-item[1], item[0])
            )
            self.rules[context] = Rule(encoded, best_count, sum(counts.values()))
        self.reset_recent()

    def reset_recent(self) -> None:
        self.recent.clear()
        self.expected = b""
        self.expected_index = 0
        self.expected_rule = None
        self.expected_match = 0

    def endpoint(self) -> Endpoint | None:
        if self.expected_rule is None or self.expected_index >= len(self.expected):
            return None
        return Endpoint(
            self.expected[self.expected_index],
            self.expected_match,
            self.expected_rule.best_count,
            self.expected_rule.total,
        )

    def observe_stream_byte(self, value: int) -> None:
        if self.expected_rule is None or self.expected_index >= len(self.expected):
            return
        if value != self.expected[self.expected_index]:
            self.expected = b""
            self.expected_index = 0
            self.expected_rule = None
            self.expected_match = 0
            return
        self.expected_index += 1

    def observe_unit(self, signature: int) -> None:
        self.recent.append(signature)
        if len(self.recent) > self.max_context:
            del self.recent[0]
        self.expected = b""
        self.expected_index = 0
        self.expected_rule = None
        self.expected_match = 0
        for length in range(min(self.max_context, len(self.recent)), 0, -1):
            rule = self.rules.get(tuple(self.recent[-length:]))
            if rule is not None:
                self.expected = rule.encoded
                self.expected_rule = rule
                self.expected_match = length
                return


class TitleEndpointState:
    def __init__(self) -> None:
        self.wiki = WikiState()
        self.current_units: list[WrtUnit] = []
        self.current = TitleTokenModel()
        self.previous = TitleTokenModel()
        self.pages = 0
        self.titles = 0
        self.title_units = 0
        self.decoded_sha256 = hashlib.sha256()
        self.decoded_bytes = 0

    def endpoints(self) -> tuple[Endpoint | None, Endpoint | None]:
        return self.current.endpoint(), self.previous.endpoint()

    def observe_stream_byte(self, encoded: int) -> None:
        self.current.observe_stream_byte(encoded)
        self.previous.observe_stream_byte(encoded)

    def observe_event(self, event: WrtEvent) -> None:
        unit = unit_from_event(event)
        title_before = self.wiki.title_mode
        prose_before = self.wiki.prose_mode
        in_tag_before = self.wiki.in_tag
        self.decoded_sha256.update(unit.decoded)
        self.decoded_bytes += len(unit.decoded)
        self.wiki.feed(unit.decoded)

        if self.wiki.page_boundary == 1:
            self.previous.build(self.current_units)
            self.current_units = []
            self.current.build(())
            self.pages += 1

        begins_tag = unit.decoded.startswith(b"<")
        if title_before and not in_tag_before and not begins_tag:
            self.current_units.append(unit)
            self.title_units += 1
        if title_before and not self.wiki.title_mode:
            self.current.build(self.current_units)
            self.titles += 1

        body_unit = prose_before and not in_tag_before and not begins_tag
        if body_unit:
            self.current.observe_unit(unit.signature)
            self.previous.observe_unit(unit.signature)
        else:
            self.current.reset_recent()
            self.previous.reset_recent()


LOSS_QBITS = tuple(
    0 if probability == 0 else int(round(-math.log2(probability / TOTAL) * 256))
    for probability in range(TOTAL + 1)
)


def loss_qbits(bit: int, p1: int) -> int:
    return LOSS_QBITS[p1 if bit else TOTAL - p1]


def blend_probability(base_p1: int, expert_p1: int, blend_ppm: int) -> int:
    mixed = (base_p1 * (1_000_000 - blend_ppm) + expert_p1 * blend_ppm + 500_000) // 1_000_000
    return max(1, min(TOTAL - 1, mixed))


def decay_toward_zero(value: int, shift: int = 12) -> int:
    amount = abs(value) >> shift
    return value - amount if value > 0 else value + amount


@dataclass(frozen=True)
class VariantSpec:
    source: str
    min_context: int
    blend_ppm: int
    strict: bool
    router: str

    @property
    def variant_id(self) -> str:
        strict = "strict" if self.strict else "majority"
        return f"{self.source}_m{self.min_context}_b{self.blend_ppm}_{strict}_{self.router}"


@dataclass
class VariantStats:
    spec: VariantSpec
    eligible_bits: int = 0
    applied_bits: int = 0
    qbits_saved: int = 0
    counterfactual_qbits: int = 0
    regret_qbits: int = 0
    block_qbits: dict[int, int] = field(default_factory=dict)
    eligible_byte_events: int = 0
    positive_byte_events: int = 0
    regressing_byte_events: int = 0
    flat_byte_events: int = 0
    positive_byte_oracle_qbits: int = 0
    negative_byte_qbits: int = 0

    def probability(self, endpoint: Endpoint, bit_pos: int, prefix: int, base_p1: int) -> tuple[int, int] | None:
        if endpoint.match_tokens < self.spec.min_context:
            return None
        if self.spec.strict and endpoint.best_count != endpoint.total:
            return None
        if bit_pos and endpoint.expected_byte >> (8 - bit_pos) != prefix:
            return None
        expected_bit = (endpoint.expected_byte >> (7 - bit_pos)) & 1
        expert_p1 = EXPERT_ONE if expected_bit else EXPERT_ZERO
        return blend_probability(base_p1, expert_p1, self.spec.blend_ppm), expected_bit


def all_specs() -> list[VariantSpec]:
    return [
        VariantSpec(source, context, blend, strict, router)
        for source in ("current", "previous")
        for context in TITLE_CONTEXTS
        for blend in BLENDS_PPM
        for strict in (True, False)
        for router in ("always", "regret12")
    ]


class Fx2RangeCounter:
    def __init__(self) -> None:
        self.x1 = 0
        self.x2 = MAX_CODE
        self.bytes = 0

    def encode(self, bit: int, p1: int) -> None:
        delta = self.x2 - self.x1
        midpoint = self.x1 + (delta >> 16) * p1 + ((delta & 0xFFFF) * p1 >> 16)
        if bit:
            self.x2 = midpoint
        else:
            self.x1 = midpoint + 1
        while ((self.x1 ^ self.x2) & 0xFF000000) == 0:
            self.bytes += 1
            self.x1 = (self.x1 << 8) & MAX_CODE
            self.x2 = ((self.x2 << 8) & MAX_CODE) + 255

    def finish(self) -> None:
        while ((self.x1 ^ self.x2) & 0xFF000000) == 0:
            self.bytes += 1
            self.x1 = (self.x1 << 8) & MAX_CODE
            self.x2 = ((self.x2 << 8) & MAX_CODE) + 255
        self.bytes += 1


def score_trace(
    trace: Path,
    parsed: ParsedStore,
    specs: Sequence[VariantSpec],
    exact_ids: set[str] | None = None,
) -> tuple[dict[str, VariantStats], dict[str, object]]:
    states = {spec.variant_id: VariantStats(spec) for spec in specs}
    states_by_source = {
        source: [
            (variant_id, state)
            for variant_id, state in states.items()
            if state.spec.source == source
        ]
        for source in ("current", "previous")
    }
    endpoint_state = TitleEndpointState()
    events_by_end = {event.end: event for event in parsed.events}
    if len(events_by_end) != len(parsed.events):
        raise ValueError("multiple WRT events end at one stream offset")
    expected_start = 6
    for event in parsed.events:
        if event.start != expected_start or event.end <= event.start:
            raise ValueError("WRT events do not form a contiguous causal stream")
        expected_start = event.end
    if expected_start != len(parsed.stream):
        raise ValueError("WRT events do not cover the complete text segment")
    exact_ids = exact_ids or set()
    exact = {variant_id: Fx2RangeCounter() for variant_id in exact_ids}
    baseline = Fx2RangeCounter() if exact_ids else None
    wrt_digest = hashlib.sha256()
    wrt_bytes = 0

    for byte_pos, trace_byte in enumerate(iter_trace_bytes(trace)):
        if byte_pos >= len(parsed.stream) or trace_byte.value != parsed.stream[byte_pos]:
            raise ValueError("compact trace truth bytes differ from the exact WRT store")
        current, previous = endpoint_state.endpoints()
        endpoints = {"current": current, "previous": previous}
        prefix = 0
        event_deltas: dict[str, int] = {}
        wrt_digest.update(bytes((trace_byte.value,)))
        wrt_bytes += 1
        for bit_pos, (p1, bit) in enumerate(zip(trace_byte.probabilities, trace_byte.bits)):
            if baseline is not None:
                baseline.encode(bit, p1)
            for source, source_states in states_by_source.items():
                endpoint = endpoints[source]
                # Discovery has no exact coders to advance. Avoid visiting every
                # variant on the overwhelmingly common rows where its source has
                # no prediction. Exact replay still feeds the base probability to
                # every frozen coder on those rows.
                if endpoint is None and not exact:
                    continue
                for variant_id, state in source_states:
                    candidate: tuple[int, int] | None = None
                    if endpoint is not None:
                        candidate = state.probability(endpoint, bit_pos, prefix, p1)
                    chosen = p1
                    if candidate is not None:
                        candidate_p1, _ = candidate
                        delta = loss_qbits(bit, p1) - loss_qbits(bit, candidate_p1)
                        state.eligible_bits += 1
                        state.counterfactual_qbits += delta
                        event_deltas[variant_id] = event_deltas.get(variant_id, 0) + delta
                        apply = state.spec.router == "always" or state.regret_qbits > 0
                        if apply:
                            chosen = candidate_p1
                            state.applied_bits += 1
                            state.qbits_saved += delta
                            block = byte_pos // BLOCK_BYTES
                            state.block_qbits[block] = state.block_qbits.get(block, 0) + delta
                        if state.spec.router == "regret12":
                            state.regret_qbits = max(
                                -(1 << 24),
                                min(1 << 24, decay_toward_zero(state.regret_qbits) + delta),
                            )
                    if variant_id in exact:
                        exact[variant_id].encode(bit, chosen)
            prefix = (prefix << 1) | bit
        for variant_id, delta in event_deltas.items():
            state = states[variant_id]
            state.eligible_byte_events += 1
            if delta > 0:
                state.positive_byte_events += 1
                state.positive_byte_oracle_qbits += delta
            elif delta < 0:
                state.regressing_byte_events += 1
                state.negative_byte_qbits += delta
            else:
                state.flat_byte_events += 1
        endpoint_state.observe_stream_byte(trace_byte.value)
        event = events_by_end.get(byte_pos + 1)
        if event is not None:
            endpoint_state.observe_event(event)

    if wrt_bytes != len(parsed.stream):
        raise ValueError("compact trace length differs from the exact WRT stream")
    decoded_sha256 = endpoint_state.decoded_sha256.hexdigest()
    expected_decoded_sha256 = hashlib.sha256(parsed.decoded).hexdigest()
    if endpoint_state.decoded_bytes != parsed.raw_length:
        raise ValueError("causal event replay did not reconstruct the declared raw length")
    if decoded_sha256 != expected_decoded_sha256:
        raise ValueError("causal event replay differs from the exact WRT decode")

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
    diagnostics = {
        "wrt_bytes": wrt_bytes,
        "wrt_sha256": wrt_digest.hexdigest(),
        "decoded_bytes": endpoint_state.decoded_bytes,
        "decoded_sha256": decoded_sha256,
        "exact_store_raw_bytes": parsed.raw_length,
        "exact_store_events": len(parsed.events),
        "exact_store_event_kinds": parsed.kind_counts,
        "events_released_after_completion": True,
        "pages": endpoint_state.pages,
        "titles": endpoint_state.titles,
        "title_units": endpoint_state.title_units,
        "exact": exact_rows,
    }
    return states, diagnostics


def row_for(stats: VariantStats, scope_bytes: int) -> dict[str, object]:
    blocks = list(stats.block_qbits.values())
    return {
        "variant_id": stats.spec.variant_id,
        "source": stats.spec.source,
        "min_context_tokens": stats.spec.min_context,
        "blend_ppm": stats.spec.blend_ppm,
        "strict_next_token": stats.spec.strict,
        "router": stats.spec.router,
        "eligible_bits": stats.eligible_bits,
        "applied_bits": stats.applied_bits,
        "qbits_saved": stats.qbits_saved,
        "qbit_saved_bytes": stats.qbits_saved / 2048.0,
        "qbit_gain_bytes_per_million": stats.qbits_saved / 2048.0 * 1_000_000 / scope_bytes,
        "counterfactual_qbits": stats.counterfactual_qbits,
        "eligible_byte_events": stats.eligible_byte_events,
        "positive_byte_events": stats.positive_byte_events,
        "regressing_byte_events": stats.regressing_byte_events,
        "flat_byte_events": stats.flat_byte_events,
        "positive_byte_oracle_qbits": stats.positive_byte_oracle_qbits,
        "positive_byte_oracle_bytes": stats.positive_byte_oracle_qbits / 2048.0,
        "positive_byte_oracle_bytes_per_million": (
            stats.positive_byte_oracle_qbits / 2048.0 * 1_000_000 / scope_bytes
        ),
        "negative_byte_qbits": stats.negative_byte_qbits,
        "positive_blocks": sum(value > 0 for value in blocks),
        "regressing_blocks": sum(value < 0 for value in blocks),
        "flat_blocks": sum(value == 0 for value in blocks),
        "worst_block_qbit_bytes": min(blocks, default=0) / 2048.0,
    }


def archive_payload_bytes(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(5)
    if len(header) != 5:
        raise ValueError("truncated FX2 archive")
    wrt_bytes = header[0] & 0x7F
    for value in header[1:]:
        wrt_bytes = (wrt_bytes << 8) | value
    header_bytes = 5 if wrt_bytes < 10_000 else 37
    return path.stat().st_size - header_bytes, wrt_bytes


def parse_variant_id(value: str, specs: Sequence[VariantSpec]) -> VariantSpec:
    matches = [spec for spec in specs if spec.variant_id == value]
    if len(matches) != 1:
        raise ValueError(f"unknown variant id: {value}")
    return matches[0]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--phase", choices=("selection", "confirmation"), required=True)
    parser.add_argument("--variant-id")
    parser.add_argument("--exact-top", type=int, default=8)
    parser.add_argument("--substrate-id", default="raw_fx2")
    parser.add_argument("--state-contract", default="cold_reset_random_window")
    parser.add_argument("--substrate-receipt", type=Path)
    parser.add_argument("--gross-floor-bpm", type=float, default=700.0)
    parser.add_argument("--target-gap-bytes", type=int)
    parser.add_argument("--incremental-program-bytes", type=int, default=0)
    parser.add_argument("--full-scope-bytes", type=int, default=1_000_000_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.scope_bytes <= 0 or args.exact_top <= 0:
        raise SystemExit("scope and exact-top must be positive")
    if args.gross_floor_bpm < 0 or args.incremental_program_bytes < 0:
        raise SystemExit("economic byte counts and rates cannot be negative")
    if args.target_gap_bytes is not None and args.target_gap_bytes < 0:
        raise SystemExit("target gap cannot be negative")
    if args.full_scope_bytes <= 0:
        raise SystemExit("full-scope-bytes must be positive")
    for path in (args.trace, args.dictionary, args.wrt_store, args.raw_input):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    if args.substrate_receipt and not args.substrate_receipt.is_file():
        raise SystemExit(f"missing substrate receipt: {args.substrate_receipt}")
    if args.payload and not args.payload.is_file():
        raise SystemExit(f"missing arithmetic payload: {args.payload}")

    specs = all_specs()
    if args.variant_id:
        selected = parse_variant_id(args.variant_id, specs)
        first_specs = [selected]
    else:
        first_specs = specs
    dictionary = load_dictionary(args.dictionary)
    parsed = parse_store(args.wrt_store, args.dictionary)
    raw_input = args.raw_input.read_bytes()
    if raw_input != parsed.decoded:
        raise SystemExit("exact WRT decode differs from --raw-input")
    if args.scope_bytes != parsed.raw_length:
        raise SystemExit("--scope-bytes differs from the exact WRT raw length")
    first, diagnostics = score_trace(args.trace, parsed, first_specs)
    rows = [row_for(stats, args.scope_bytes) for stats in first.values()]
    rows.sort(
        key=lambda row: (
            -float(row["qbit_gain_bytes_per_million"]),
            int(row["regressing_blocks"]),
            str(row["variant_id"]),
        )
    )
    candidate_rows = [row for row in rows if row["source"] == "current"]
    control_rows = [row for row in rows if row["source"] == "previous"]
    oracle_candidate_rows = sorted(
        candidate_rows,
        key=lambda row: (
            -float(row["positive_byte_oracle_bytes_per_million"]),
            str(row["variant_id"]),
        ),
    )
    oracle_control_rows = sorted(
        control_rows,
        key=lambda row: (
            -float(row["positive_byte_oracle_bytes_per_million"]),
            str(row["variant_id"]),
        ),
    )
    exact_ids = {
        str(row["variant_id"])
        for row in candidate_rows[: args.exact_top]
        + control_rows[: min(4, args.exact_top)]
    }
    exact_specs = [parse_variant_id(value, specs) for value in exact_ids]
    _, exact_diagnostics = score_trace(args.trace, parsed, exact_specs, exact_ids)
    exact = exact_diagnostics["exact"]
    for row in rows:
        row["exact"] = exact.get(str(row["variant_id"]))

    validations: dict[str, object] = {}
    baseline_values = {
        int(value["baseline_payload_bytes"])
        for value in exact.values()
    }
    if args.archive:
        payload_bytes, archive_wrt_bytes = archive_payload_bytes(args.archive)
        validations["archive"] = {
            "path": str(args.archive),
            "sha256": sha256_file(args.archive),
            "payload_bytes": payload_bytes,
            "wrt_bytes": archive_wrt_bytes,
            "trace_wrt_bytes_match": archive_wrt_bytes == diagnostics["wrt_bytes"],
            "baseline_range_match": baseline_values == {payload_bytes},
        }
    if args.payload:
        validations["payload"] = {
            "path": str(args.payload),
            "sha256": sha256_file(args.payload),
            "bytes": args.payload.stat().st_size,
            "baseline_range_match": baseline_values == {args.payload.stat().st_size},
        }
    validations["wrt_store"] = {
        "path": str(args.wrt_store),
        "sha256": sha256_file(args.wrt_store),
        "storage_header_bytes": parsed.storage_header_bytes,
        "stream_bytes": len(parsed.stream),
        "stream_sha256": hashlib.sha256(parsed.stream).hexdigest(),
        "trace_matches_store": diagnostics["wrt_sha256"]
        == hashlib.sha256(parsed.stream).hexdigest(),
        "raw_length": parsed.raw_length,
        "decoded_sha256": hashlib.sha256(parsed.decoded).hexdigest(),
        "event_count": len(parsed.events),
        "event_kind_counts": parsed.kind_counts,
    }
    validations["raw_input"] = {
        "path": str(args.raw_input),
        "bytes": args.raw_input.stat().st_size,
        "sha256": sha256_file(args.raw_input),
        "matches_exact_wrt_decode": True,
    }

    tool = Path(__file__).resolve()
    substrate_receipt = None
    if args.substrate_receipt:
        substrate_receipt = {
            "path": str(args.substrate_receipt),
            "bytes": args.substrate_receipt.stat().st_size,
            "sha256": sha256_file(args.substrate_receipt),
        }
    required_gain_bpm = None
    if args.target_gap_bytes is not None:
        required_gain_bpm = (
            (args.target_gap_bytes + args.incremental_program_bytes)
            * 1_000_000
            / args.full_scope_bytes
        )
    payload = {
        "schema_version": 1,
        "receipt_type": "wrt_title_token_automaton_shadow",
        "evidence_level": "compact_exact_probability_trace_shadow",
        "claim_boundary": (
            "This is a causal shadow replay on an arbitrary random window. "
            "It is not integrated source, a native candidate archive, a prefix score, "
            "or a 10.95% proof."
        ),
        "window_id": args.window_id,
        "phase": args.phase,
        "scope_bytes": args.scope_bytes,
        "substrate": {
            "id": args.substrate_id,
            "state_contract": args.state_contract,
            "receipt": substrate_receipt,
        },
        "economics": {
            "gross_screen_bytes_per_million": args.gross_floor_bpm,
            "target_gap_bytes": args.target_gap_bytes,
            "incremental_program_bytes": args.incremental_program_bytes,
            "full_scope_bytes": args.full_scope_bytes,
            "required_gain_bytes_per_million": required_gain_bpm,
        },
        "trace": {
            "path": str(args.trace),
            "bytes": args.trace.stat().st_size,
            "sha256": sha256_file(args.trace),
            "record_format": "8-byte FX2PT01 header then little-endian uint16 p1 and uint8 truth bit",
        },
        "dictionary": {
            "path": str(args.dictionary),
            "bytes": args.dictionary.stat().st_size,
            "sha256": sha256_file(args.dictionary),
            "words": len(dictionary),
        },
        "tool": {"path": str(tool), "sha256": sha256_file(tool)},
        "contract": {
            "sources": ["current", "previous"],
            "title_context_tokens": list(TITLE_CONTEXTS),
            "blend_ppm": list(BLENDS_PPM),
            "strict_modes": [True, False],
            "routers": ["always", "regret12"],
            "expert_probability_one": EXPERT_ONE,
            "block_bytes": BLOCK_BYTES,
            "target_gross_bytes_per_million": args.gross_floor_bpm,
            "oracle_definition": (
                "Future-label abstention independently chooses each eligible WRT "
                "byte event after summing that event's causal-prefix bit deltas."
            ),
        },
        "diagnostics": diagnostics,
        "validations": validations,
        "rows": rows,
        "best": candidate_rows[0] if candidate_rows else None,
        "best_control": control_rows[0] if control_rows else None,
        "best_positive_byte_oracle": (
            oracle_candidate_rows[0] if oracle_candidate_rows else None
        ),
        "best_control_positive_byte_oracle": (
            oracle_control_rows[0] if oracle_control_rows else None
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["best"], indent=2, sort_keys=True))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
