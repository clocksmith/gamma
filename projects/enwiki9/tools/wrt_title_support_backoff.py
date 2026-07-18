#!/usr/bin/env python3
"""Score a support-backed, contrastive WRT title endpoint.

The current page title and previous page title each define a hierarchy of
token-transition distributions.  The endpoint interpolates those distributions
from short to long contexts, then either applies the current distribution or
its contrast against the previous-title control.  All state is rebuilt from
completed WRT events and all arithmetic affecting probabilities is integer.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Sequence

from wrt_exact import (
    ParsedStore,
    TEXT_SEGMENT,
    WrtEvent,
    parse_store,
    read_dictionary_words,
    wrt_byte_transform,
)
from wrt_title_token_automaton import (
    BLOCK_BYTES,
    TRACE_MAGIC,
    TOTAL,
    Fx2RangeCounter,
    WikiState,
    WrtUnit,
    archive_payload_bytes,
    iter_trace_bytes,
    loss_qbits,
    sha256_file,
    unit_from_event,
)


MAX_CONTEXTS = (2, 4, 8)
BACKOFF_COUNTS = (4, 16, 64)
SCALES_PPM = (100_000, 250_000, 500_000, 1_000_000)
MODES = ("current", "previous", "contrast")


def scaled_delta(value: int, scale_ppm: int) -> int:
    magnitude = (abs(value) * scale_ppm + 500_000) // 1_000_000
    return magnitude if value >= 0 else -magnitude


@dataclass(frozen=True)
class ActiveNode:
    context_length: int
    counts: Counter[bytes]


class SupportTitleModel:
    def __init__(self, max_context: int = max(MAX_CONTEXTS)) -> None:
        self.max_context = max_context
        self.rules: dict[tuple[int, ...], Counter[bytes]] = {}
        self.recent: list[int] = []
        self.active_nodes: list[ActiveNode] = []
        self.observed = b""

    def build(self, units: Sequence[WrtUnit]) -> None:
        histograms: dict[tuple[int, ...], Counter[bytes]] = {}
        signatures = [unit.signature for unit in units]
        for next_index in range(1, len(units)):
            for length in range(1, min(self.max_context, next_index) + 1):
                context = tuple(signatures[next_index - length : next_index])
                histograms.setdefault(context, Counter())[units[next_index].encoded] += 1
        self.rules = histograms
        self.reset_recent()

    def reset_recent(self) -> None:
        self.recent.clear()
        self.active_nodes.clear()
        self.observed = b""

    def observe_stream_byte(self, value: int) -> None:
        if not self.active_nodes:
            return
        observed = self.observed + bytes((value,))
        self.active_nodes = [
            node
            for node in self.active_nodes
            if any(code.startswith(observed) for code in node.counts)
        ]
        self.observed = observed if self.active_nodes else b""

    def observe_unit(self, signature: int) -> None:
        self.recent.append(signature)
        if len(self.recent) > self.max_context:
            del self.recent[0]
        self.observed = b""
        self.active_nodes = []
        for length in range(1, min(self.max_context, len(self.recent)) + 1):
            counts = self.rules.get(tuple(self.recent[-length:]))
            if counts:
                self.active_nodes.append(ActiveNode(length, counts))

    def probability(
        self,
        max_context: int,
        backoff_count: int,
        bit_pos: int,
        prefix: int,
    ) -> tuple[int, int, int] | None:
        byte_index = len(self.observed)
        probability = TOTAL // 2
        longest = 0
        longest_support = 0
        matched = False
        for node in self.active_nodes:
            if node.context_length > max_context:
                continue
            zeros = 0
            ones = 0
            for code, count in node.counts.items():
                if len(code) <= byte_index or code[:byte_index] != self.observed:
                    continue
                value = code[byte_index]
                if bit_pos and value >> (8 - bit_pos) != prefix:
                    continue
                if (value >> (7 - bit_pos)) & 1:
                    ones += count
                else:
                    zeros += count
            support = zeros + ones
            if support == 0:
                continue
            matched = True
            denominator = support + backoff_count
            probability = (
                ones * TOTAL + backoff_count * probability + denominator // 2
            ) // denominator
            longest = node.context_length
            longest_support = support
        if not matched:
            return None
        return max(1, min(TOTAL - 1, probability)), longest, longest_support


class SupportEndpointState:
    def __init__(self) -> None:
        self.wiki = WikiState()
        self.current_units: list[WrtUnit] = []
        self.current = SupportTitleModel()
        self.previous = SupportTitleModel()
        self.pages = 0
        self.titles = 0
        self.title_units = 0
        self.decoded_sha256 = hashlib.sha256()
        self.decoded_bytes = 0

    def observe_stream_byte(self, value: int) -> None:
        self.current.observe_stream_byte(value)
        self.previous.observe_stream_byte(value)

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

        if prose_before and not in_tag_before and not begins_tag:
            self.current.observe_unit(unit.signature)
            self.previous.observe_unit(unit.signature)
        else:
            self.current.reset_recent()
            self.previous.reset_recent()


@dataclass(frozen=True)
class SupportSpec:
    mode: str
    max_context: int
    backoff_count: int
    scale_ppm: int

    @property
    def variant_id(self) -> str:
        return (
            f"{self.mode}_m{self.max_context}_k{self.backoff_count}"
            f"_s{self.scale_ppm}"
        )


@dataclass
class SupportStats:
    spec: SupportSpec
    eligible_bits: int = 0
    qbits_saved: int = 0
    block_qbits: dict[int, int] = field(default_factory=dict)
    eligible_stream_bytes: int = 0
    positive_stream_bytes: int = 0
    regressing_stream_bytes: int = 0
    flat_stream_bytes: int = 0
    positive_byte_oracle_qbits: int = 0
    negative_byte_qbits: int = 0
    maximum_context_seen: int = 0
    maximum_support_seen: int = 0


def all_specs() -> list[SupportSpec]:
    return [
        SupportSpec(mode, context, backoff, scale)
        for mode in MODES
        for context in MAX_CONTEXTS
        for backoff in BACKOFF_COUNTS
        for scale in SCALES_PPM
    ]


def candidate_probability(
    spec: SupportSpec,
    base_p1: int,
    current: tuple[int, int, int] | None,
    previous: tuple[int, int, int] | None,
) -> tuple[int, int, int] | None:
    if spec.mode == "current":
        if current is None:
            return None
        signal = current[0] - TOTAL // 2
        context, support = current[1], current[2]
    elif spec.mode == "previous":
        if previous is None:
            return None
        signal = previous[0] - TOTAL // 2
        context, support = previous[1], previous[2]
    else:
        if current is None:
            return None
        signal = current[0] - (previous[0] if previous is not None else TOTAL // 2)
        context, support = current[1], current[2]
    candidate = max(1, min(TOTAL - 1, base_p1 + scaled_delta(signal, spec.scale_ppm)))
    if candidate == base_p1:
        return None
    return candidate, context, support


def score_trace(
    trace: Path,
    parsed: ParsedStore,
    specs: Sequence[SupportSpec],
    exact_ids: set[str] | None = None,
) -> tuple[dict[str, SupportStats], dict[str, object]]:
    states = {spec.variant_id: SupportStats(spec) for spec in specs}
    endpoint = SupportEndpointState()
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
    baseline = Fx2RangeCounter() if exact else None
    parameter_pairs = sorted({(spec.max_context, spec.backoff_count) for spec in specs})
    wrt_digest = hashlib.sha256()
    wrt_bytes = 0

    for byte_pos, trace_byte in enumerate(iter_trace_bytes(trace)):
        if byte_pos >= len(parsed.stream) or trace_byte.value != parsed.stream[byte_pos]:
            raise ValueError("compact trace truth bytes differ from the exact WRT store")
        wrt_digest.update(bytes((trace_byte.value,)))
        wrt_bytes += 1
        prefix = 0
        byte_deltas: dict[str, int] = {}
        for bit_pos, (base_p1, bit) in enumerate(
            zip(trace_byte.probabilities, trace_byte.bits)
        ):
            if baseline is not None:
                baseline.encode(bit, base_p1)
            if not endpoint.current.active_nodes and not endpoint.previous.active_nodes:
                for coder in exact.values():
                    coder.encode(bit, base_p1)
                prefix = (prefix << 1) | bit
                continue
            probabilities: dict[tuple[str, int, int], tuple[int, int, int] | None] = {}
            for context, backoff in parameter_pairs:
                probabilities[("current", context, backoff)] = endpoint.current.probability(
                    context, backoff, bit_pos, prefix
                )
                probabilities[("previous", context, backoff)] = endpoint.previous.probability(
                    context, backoff, bit_pos, prefix
                )
            for variant_id, state in states.items():
                key = (state.spec.max_context, state.spec.backoff_count)
                candidate = candidate_probability(
                    state.spec,
                    base_p1,
                    probabilities[("current", *key)],
                    probabilities[("previous", *key)],
                )
                chosen = base_p1
                if candidate is not None:
                    chosen, context, support = candidate
                    delta = loss_qbits(bit, base_p1) - loss_qbits(bit, chosen)
                    state.eligible_bits += 1
                    state.qbits_saved += delta
                    state.maximum_context_seen = max(state.maximum_context_seen, context)
                    state.maximum_support_seen = max(state.maximum_support_seen, support)
                    state.block_qbits[byte_pos // BLOCK_BYTES] = (
                        state.block_qbits.get(byte_pos // BLOCK_BYTES, 0) + delta
                    )
                    byte_deltas[variant_id] = byte_deltas.get(variant_id, 0) + delta
                if variant_id in exact:
                    exact[variant_id].encode(bit, chosen)
            prefix = (prefix << 1) | bit
        for variant_id, delta in byte_deltas.items():
            state = states[variant_id]
            state.eligible_stream_bytes += 1
            if delta > 0:
                state.positive_stream_bytes += 1
                state.positive_byte_oracle_qbits += delta
            elif delta < 0:
                state.regressing_stream_bytes += 1
                state.negative_byte_qbits += delta
            else:
                state.flat_stream_bytes += 1
        endpoint.observe_stream_byte(trace_byte.value)
        event = events_by_end.get(byte_pos + 1)
        if event is not None:
            endpoint.observe_event(event)

    if wrt_bytes != len(parsed.stream):
        raise ValueError("compact trace length differs from the exact WRT stream")
    decoded_sha256 = endpoint.decoded_sha256.hexdigest()
    if endpoint.decoded_bytes != parsed.raw_length:
        raise ValueError("causal event replay did not reconstruct the raw length")
    if decoded_sha256 != hashlib.sha256(parsed.decoded).hexdigest():
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
    return states, {
        "wrt_bytes": wrt_bytes,
        "wrt_sha256": wrt_digest.hexdigest(),
        "decoded_bytes": endpoint.decoded_bytes,
        "decoded_sha256": decoded_sha256,
        "events": len(parsed.events),
        "events_released_after_completion": True,
        "pages": endpoint.pages,
        "titles": endpoint.titles,
        "title_units": endpoint.title_units,
        "exact": exact_rows,
    }


def row_for(stats: SupportStats, scope_bytes: int) -> dict[str, object]:
    blocks = list(stats.block_qbits.values())
    return {
        "variant_id": stats.spec.variant_id,
        "mode": stats.spec.mode,
        "max_context_tokens": stats.spec.max_context,
        "backoff_count": stats.spec.backoff_count,
        "scale_ppm": stats.spec.scale_ppm,
        "eligible_bits": stats.eligible_bits,
        "qbits_saved": stats.qbits_saved,
        "qbit_saved_bytes": stats.qbits_saved / 2048.0,
        "qbit_gain_bytes_per_million": (
            stats.qbits_saved / 2048.0 * 1_000_000 / scope_bytes
        ),
        "eligible_stream_bytes": stats.eligible_stream_bytes,
        "positive_stream_bytes": stats.positive_stream_bytes,
        "regressing_stream_bytes": stats.regressing_stream_bytes,
        "flat_stream_bytes": stats.flat_stream_bytes,
        "positive_byte_oracle_qbits": stats.positive_byte_oracle_qbits,
        "positive_byte_oracle_bytes_per_million": (
            stats.positive_byte_oracle_qbits / 2048.0 * 1_000_000 / scope_bytes
        ),
        "negative_byte_qbits": stats.negative_byte_qbits,
        "maximum_context_seen": stats.maximum_context_seen,
        "maximum_support_seen": stats.maximum_support_seen,
        "positive_blocks": sum(value > 0 for value in blocks),
        "regressing_blocks": sum(value < 0 for value in blocks),
        "flat_blocks": sum(value == 0 for value in blocks),
        "worst_block_qbit_bytes": min(blocks, default=0) / 2048.0,
    }


def parse_variant_id(value: str, specs: Sequence[SupportSpec]) -> SupportSpec:
    matches = [spec for spec in specs if spec.variant_id == value]
    if len(matches) != 1:
        raise ValueError(f"unknown variant id: {value}")
    return matches[0]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--variant-id")
    parser.add_argument("--exact-top", type=int, default=8)
    parser.add_argument("--target-gap-bytes", type=int, default=57_404)
    parser.add_argument("--incremental-program-bytes", type=int, default=12_000)
    parser.add_argument("--full-scope-bytes", type=int, default=1_000_000_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.scope_bytes <= 0 or args.exact_top <= 0 or args.full_scope_bytes <= 0:
        raise SystemExit("scope values and exact-top must be positive")
    if args.target_gap_bytes < 0 or args.incremental_program_bytes < 0:
        raise SystemExit("economic byte counts cannot be negative")
    for path in (
        args.trace,
        args.dictionary,
        args.wrt_store,
        args.raw_input,
        args.archive,
    ):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")

    dictionary = read_dictionary_words(args.dictionary)
    parsed = parse_store(args.wrt_store, args.dictionary)
    raw_input = args.raw_input.read_bytes()
    if raw_input != parsed.decoded:
        raise SystemExit("exact WRT decode differs from --raw-input")
    if args.scope_bytes != parsed.raw_length:
        raise SystemExit("--scope-bytes differs from the exact WRT raw length")

    specs = all_specs()
    selected_specs = (
        [parse_variant_id(args.variant_id, specs)] if args.variant_id else specs
    )
    first, diagnostics = score_trace(args.trace, parsed, selected_specs)
    rows = [row_for(stats, args.scope_bytes) for stats in first.values()]
    rows.sort(
        key=lambda row: (
            -float(row["qbit_gain_bytes_per_million"]),
            int(row["regressing_blocks"]),
            str(row["variant_id"]),
        )
    )
    exact_ids = {str(row["variant_id"]) for row in rows[: args.exact_top]}
    exact_specs = [parse_variant_id(value, specs) for value in exact_ids]
    _, exact_diagnostics = score_trace(args.trace, parsed, exact_specs, exact_ids)
    for row in rows:
        row["exact"] = exact_diagnostics["exact"].get(str(row["variant_id"]))

    payload_bytes, archive_wrt_bytes = archive_payload_bytes(args.archive)
    baseline_values = {
        int(value["baseline_payload_bytes"])
        for value in exact_diagnostics["exact"].values()
    }
    stream_sha256 = hashlib.sha256(parsed.stream).hexdigest()
    tool = Path(__file__).resolve()
    payload = {
        "schema_version": 1,
        "receipt_type": "wrt_title_support_backoff_shadow",
        "evidence_level": "causal_exact_probability_trace_shadow",
        "claim_boundary": (
            "This is exact arithmetic replay on a constructive endpoint428 prefix "
            "trace, not integrated source or a full-corpus Hutter score."
        ),
        "window_id": args.window_id,
        "scope_bytes": args.scope_bytes,
        "economics": {
            "target_gap_bytes": args.target_gap_bytes,
            "incremental_program_bytes": args.incremental_program_bytes,
            "required_gain_bytes_per_million": (
                (args.target_gap_bytes + args.incremental_program_bytes)
                * 1_000_000
                / args.full_scope_bytes
            ),
        },
        "contract": {
            "modes": list(MODES),
            "max_contexts": list(MAX_CONTEXTS),
            "backoff_counts": list(BACKOFF_COUNTS),
            "scales_ppm": list(SCALES_PPM),
            "contrast": "current_title_probability - previous_title_probability",
            "probability_arithmetic": "Q16 integer hierarchical interpolation",
            "event_release": "after final encoded byte only",
        },
        "artifacts": {
            "trace": {
                "path": str(args.trace),
                "bytes": args.trace.stat().st_size,
                "sha256": sha256_file(args.trace),
            },
            "archive": {
                "path": str(args.archive),
                "bytes": args.archive.stat().st_size,
                "sha256": sha256_file(args.archive),
                "payload_bytes": payload_bytes,
            },
            "wrt_store": {
                "path": str(args.wrt_store),
                "bytes": args.wrt_store.stat().st_size,
                "sha256": sha256_file(args.wrt_store),
                "stream_bytes": len(parsed.stream),
                "stream_sha256": stream_sha256,
            },
            "raw_input": {
                "path": str(args.raw_input),
                "bytes": args.raw_input.stat().st_size,
                "sha256": sha256_file(args.raw_input),
            },
            "dictionary": {
                "path": str(args.dictionary),
                "bytes": args.dictionary.stat().st_size,
                "sha256": sha256_file(args.dictionary),
                "words": len(dictionary),
            },
            "tool": {"path": str(tool), "sha256": sha256_file(tool)},
        },
        "validations": {
            "trace_matches_store": diagnostics["wrt_sha256"] == stream_sha256,
            "raw_matches_exact_decode": diagnostics["decoded_sha256"]
            == hashlib.sha256(raw_input).hexdigest(),
            "archive_wrt_bytes_match": archive_wrt_bytes == len(parsed.stream),
            "baseline_range_match": baseline_values == {payload_bytes},
            "events_released_after_completion": diagnostics[
                "events_released_after_completion"
            ],
        },
        "diagnostics": diagnostics,
        "rows": rows,
        "best": rows[0] if rows else None,
    }
    if not all(payload["validations"].values()):
        raise SystemExit("one or more exact substrate validations failed")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["best"], indent=2, sort_keys=True))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
