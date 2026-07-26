#!/usr/bin/env python3
"""Score causal long WRT phrase continuations against exact FX2 probabilities."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Sequence

from wrt_exact import ParsedStore, WrtEvent, parse_store
from wrt_reference_prefix_cts_shadow import (
    BLENDS_PPM,
    MIN_SUPPORTS,
    normalized_event_signature,
    validate_event_cover,
)
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


CONTEXT_LENGTHS = (1, 2, 4, 8, 12)
SIGNATURE_MODES = ("exact", "normalized")


def signature(event: WrtEvent, mode: str) -> bytes:
    if mode == "exact":
        return b"E" + event.encoded
    if mode == "normalized":
        return normalized_event_signature(event)
    raise ValueError(f"unsupported signature mode: {mode}")


@dataclass
class PhraseTable:
    mode: str
    counts: dict[int, dict[tuple[bytes, ...], Counter[bytes]]] = field(
        default_factory=lambda: {
            length: defaultdict(Counter) for length in CONTEXT_LENGTHS
        }
    )
    history: list[bytes] = field(default_factory=list)
    transitions: int = 0

    def candidates(self) -> dict[int, Counter[bytes]]:
        return {
            length: value[1] for length, value in self.candidate_entries().items()
        }

    def candidate_entries(
        self,
    ) -> dict[int, tuple[tuple[bytes, ...], Counter[bytes]]]:
        result: dict[int, tuple[tuple[bytes, ...], Counter[bytes]]] = {}
        for length in CONTEXT_LENGTHS:
            if length > len(self.history):
                continue
            context = tuple(self.history[-length:])
            counter = self.counts[length].get(context)
            if counter:
                result[length] = (context, counter)
        return result

    def observe(self, event: WrtEvent) -> None:
        for length in CONTEXT_LENGTHS:
            if length <= len(self.history):
                self.counts[length][tuple(self.history[-length:])][event.encoded] += 1
        self.history.append(signature(event, self.mode))
        self.transitions += 1

    def estimated_state_bytes(self) -> int:
        total = 0
        for contexts in self.counts.values():
            for context, counter in contexts.items():
                total += 24 + sum(len(value) + 8 for value in context)
                total += sum(len(code) + 8 for code in counter)
        return total


@dataclass(frozen=True)
class Spec:
    mode: str
    context_length: int
    min_support: int
    blend_ppm: int
    router: str = "always"

    @property
    def variant_id(self) -> str:
        suffix = "" if self.router == "always" else f"_{self.router}"
        return (
            f"phrase_{self.mode}_k{self.context_length}_"
            f"s{self.min_support}_b{self.blend_ppm}{suffix}"
        )

def specs(
    grid_mode: str = "full",
    router: str = "always",
    signature_modes: Sequence[str] = SIGNATURE_MODES,
) -> list[Spec]:
    supports = MIN_SUPPORTS if grid_mode == "full" else (1,)
    blends = BLENDS_PPM if grid_mode == "full" else (10_000, 50_000, 200_000)
    return [
        Spec(mode, context, support, blend, router)
        for mode in signature_modes
        for context in CONTEXT_LENGTHS
        for support in supports
        for blend in blends
    ]


@dataclass
class Stats:
    spec: Spec
    qbits: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    eligible_bits: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    event_delta: int = 0
    counterfactual_event_delta: int = 0
    positive_oracle: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    negative_event: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    positive_events: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    regressing_events: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    block_qbits: dict[int, int] = field(default_factory=lambda: defaultdict(int))
    support_sum: int = 0
    applied_bits: dict[str, int] = field(default_factory=lambda: defaultdict(int))


def continuation_endpoint(
    counter: Counter[bytes], relative_bit: int, prefix: int
) -> tuple[int, int] | None:
    """Uncached reference implementation used by focused tests."""
    zeros = 0
    ones = 0
    for code, count in counter.items():
        code_bits = 8 * len(code)
        if relative_bit < code_bits and (
            not relative_bit
            or int.from_bytes(code, "big") >> (code_bits - relative_bit) == prefix
        ):
            bit = (code[relative_bit // 8] >> (7 - (relative_bit & 7))) & 1
            if bit:
                ones += count
            else:
                zeros += count
    support = zeros + ones
    if not support:
        return None
    p1 = ((2 * ones + 1) * TOTAL) // (2 * support + 2)
    return max(1, min(TOTAL - 1, p1)), support


def actual_path_endpoints(
    counter: Counter[bytes], actual_code: bytes
) -> list[tuple[int, int] | None]:
    """Compute the same endpoints as prefix filtering along the observed path."""
    active = list(counter.items())
    endpoints: list[tuple[int, int] | None] = []
    for bit_index in range(8 * len(actual_code)):
        zeros = 0
        ones = 0
        compatible: list[tuple[bytes, int]] = []
        actual_bit = (actual_code[bit_index // 8] >> (7 - (bit_index & 7))) & 1
        for code, count in active:
            if bit_index >= 8 * len(code):
                continue
            bit = (code[bit_index // 8] >> (7 - (bit_index & 7))) & 1
            if bit:
                ones += count
            else:
                zeros += count
            if bit == actual_bit:
                compatible.append((code, count))
        support = zeros + ones
        if support:
            p1 = ((2 * ones + 1) * TOTAL) // (2 * support + 2)
            endpoints.append((max(1, min(TOTAL - 1, p1)), support))
        else:
            endpoints.append(None)
        active = compatible
    return endpoints


def partition(byte_position: int, stream_bytes: int) -> str:
    if byte_position < stream_bytes // 3:
        return "train"
    if byte_position < 2 * stream_bytes // 3:
        return "development"
    return "holdout"


def score(
    trace: Path,
    parsed: ParsedStore,
    grid: Sequence[Spec],
    exact_ids: set[str] | None = None,
) -> tuple[dict[str, Stats], dict[str, object]]:
    states = {spec.variant_id: Stats(spec) for spec in grid}
    active_modes = tuple(sorted({spec.mode for spec in grid}))
    by_key = {
        (mode, context): [
            state
            for state in states.values()
            if state.spec.mode == mode and state.spec.context_length == context
        ]
        for mode in active_modes
        for context in CONTEXT_LENGTHS
    }
    tables = {mode: PhraseTable(mode) for mode in active_modes}
    regrets: dict[str, dict[tuple[bytes, ...], int]] = {
        spec.variant_id: {} for spec in grid
    }
    exact_ids = exact_ids or set()
    exact = {variant_id: Fx2RangeCounter() for variant_id in exact_ids}
    baseline = Fx2RangeCounter() if exact_ids else None
    events = parsed.events
    event_index = 0
    current_event: WrtEvent | None = None
    candidate_paths: dict[str, dict[int, list[tuple[int, int] | None]]] = {}
    event_contexts: dict[str, dict[int, tuple[bytes, ...]]] = {}
    event_apply: dict[str, bool] = {}
    event_partition = "train"
    trace_digest = hashlib.sha256()
    trace_bytes = 0

    for byte_position, trace_byte in enumerate(iter_trace_bytes(trace)):
        if byte_position >= len(parsed.stream) or trace_byte.value != parsed.stream[byte_position]:
            raise ValueError("trace truth differs from exact WRT store")
        if byte_position >= 6 and current_event is None:
            if event_index >= len(events) or events[event_index].start != byte_position:
                raise ValueError("missing WRT event at stream position")
            current_event = events[event_index]
            entries = {
                mode: table.candidate_entries() for mode, table in tables.items()
            }
            event_contexts = {
                mode: {context: value[0] for context, value in values.items()}
                for mode, values in entries.items()
            }
            candidate_paths = {
                mode: {
                    context: actual_path_endpoints(value[1], current_event.encoded)
                    for context, value in values.items()
                }
                for mode, values in entries.items()
            }
            event_apply = {}
            for variant_id, state in states.items():
                context = event_contexts[state.spec.mode].get(state.spec.context_length)
                event_apply[variant_id] = (
                    state.spec.router == "always"
                    or (context is not None and regrets[variant_id].get(context, 0) > 0)
                )
            event_partition = partition(byte_position, len(parsed.stream))
            for state in states.values():
                state.event_delta = 0
                state.counterfactual_event_delta = 0
        trace_digest.update(bytes((trace_byte.value,)))
        trace_bytes += 1
        prefix = 0
        for bit_position, (base_p1, bit) in enumerate(
            zip(trace_byte.probabilities, trace_byte.bits)
        ):
            if baseline is not None:
                baseline.encode(bit, base_p1)
            if current_event is None:
                if exact:
                    for coder in exact.values():
                        coder.encode(bit, base_p1)
                prefix = (prefix << 1) | bit
                continue
            relative_bit = (byte_position - current_event.start) * 8 + bit_position
            exact_chosen = {variant_id: base_p1 for variant_id in exact}
            for mode in active_modes:
                mode_paths = candidate_paths[mode]
                for context, path in mode_paths.items():
                    endpoint = path[relative_bit]
                    if endpoint is None:
                        continue
                    endpoint_p1, support = endpoint
                    for state in by_key[(mode, context)]:
                        if support < state.spec.min_support:
                            continue
                        chosen = blend_probability(
                            base_p1, endpoint_p1, state.spec.blend_ppm
                        )
                        delta = loss_qbits(bit, base_p1) - loss_qbits(bit, chosen)
                        state.eligible_bits[event_partition] += 1
                        state.eligible_bits["all"] += 1
                        state.counterfactual_event_delta += delta
                        state.support_sum += support
                        if event_apply[state.spec.variant_id]:
                            state.qbits[event_partition] += delta
                            state.qbits["all"] += delta
                            state.event_delta += delta
                            state.applied_bits[event_partition] += 1
                            state.applied_bits["all"] += 1
                            state.block_qbits[byte_position // BLOCK_BYTES] += delta
                        else:
                            chosen = base_p1
                        if state.spec.variant_id in exact:
                            exact_chosen[state.spec.variant_id] = chosen
            for variant_id, coder in exact.items():
                coder.encode(bit, exact_chosen[variant_id])
            prefix = (prefix << 1) | bit
        if current_event is not None and byte_position + 1 == current_event.end:
            for state in states.values():
                counterfactual = state.counterfactual_event_delta
                if counterfactual > 0:
                    state.positive_oracle[event_partition] += counterfactual
                    state.positive_oracle["all"] += counterfactual
                    state.positive_events[event_partition] += 1
                    state.positive_events["all"] += 1
                elif counterfactual < 0:
                    state.negative_event[event_partition] += counterfactual
                    state.negative_event["all"] += counterfactual
                    state.regressing_events[event_partition] += 1
                    state.regressing_events["all"] += 1
                context = event_contexts[state.spec.mode].get(state.spec.context_length)
                if context is not None and counterfactual:
                    current = regrets[state.spec.variant_id].get(context, 0)
                    regrets[state.spec.variant_id][context] = max(
                        -(1 << 24), min(1 << 24, current + counterfactual)
                    )
            for table in tables.values():
                table.observe(current_event)
            event_index += 1
            current_event = None
            candidate_paths = {}
            event_contexts = {}
            event_apply = {}

    if trace_bytes != len(parsed.stream) or event_index != len(events):
        raise ValueError("trace replay did not consume the exact WRT stream")
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
        "trace_bytes": trace_bytes,
        "trace_sha256": trace_digest.hexdigest(),
        "events": event_index,
        "estimated_state_bytes": {
            mode: table.estimated_state_bytes() for mode, table in tables.items()
        },
        "exact": exact_rows,
    }


def row(state: Stats, scope_bytes: int) -> dict[str, object]:
    partitions = {}
    for name in ("train", "development", "holdout", "all"):
        qbits = state.qbits.get(name, 0)
        partitions[name] = {
            "saved_bytes": qbits / 2048.0,
            "bytes_per_million": qbits / 2048.0 * 1_000_000 / scope_bytes,
            "eligible_bits": state.eligible_bits.get(name, 0),
            "applied_bits": state.applied_bits.get(name, 0),
            "positive_event_oracle_saved_bytes": state.positive_oracle.get(name, 0) / 2048.0,
            "negative_event_saved_bytes": state.negative_event.get(name, 0) / 2048.0,
            "positive_events": state.positive_events.get(name, 0),
            "regressing_events": state.regressing_events.get(name, 0),
        }
    blocks = list(state.block_qbits.values())
    return {
        "variant_id": state.spec.variant_id,
        "signature_mode": state.spec.mode,
        "context_length": state.spec.context_length,
        "minimum_support": state.spec.min_support,
        "blend_ppm": state.spec.blend_ppm,
        "router": state.spec.router,
        "partitions": partitions,
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
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--grid-mode", choices=("coarse", "full"), default="coarse")
    parser.add_argument("--router", choices=("always", "context_regret"), default="always")
    parser.add_argument(
        "--signature-mode", choices=("both", "exact", "normalized"), default="both"
    )
    parser.add_argument("--exact-top", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    for path in (args.trace, args.wrt_store, args.dictionary, args.raw_input, args.archive):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if raw != parsed.decoded or len(raw) != args.scope_bytes:
        raise SystemExit("raw input does not match exact WRT decode and scope")
    validate_event_cover(parsed)
    signature_modes = (
        SIGNATURE_MODES if args.signature_mode == "both" else (args.signature_mode,)
    )
    grid = specs(args.grid_mode, args.router, signature_modes)
    first, diagnostics = score(args.trace, parsed, grid)
    rows = [row(state, args.scope_bytes) for state in first.values()]
    rows.sort(
        key=lambda item: (
            -float(item["partitions"]["development"]["saved_bytes"]),
            -float(item["partitions"]["holdout"]["saved_bytes"]),
            str(item["variant_id"]),
        )
    )
    exact_ids = {str(item["variant_id"]) for item in rows[: args.exact_top]}
    exact_grid = [spec for spec in grid if spec.variant_id in exact_ids]
    _, exact_diagnostics = score(args.trace, parsed, exact_grid, exact_ids)
    exact = exact_diagnostics["exact"]
    for item in rows:
        item["exact"] = exact.get(str(item["variant_id"]))
    payload_bytes, archive_wrt_bytes = archive_payload_bytes(args.archive)
    baseline_values = {int(item["baseline_payload_bytes"]) for item in exact.values()}
    best = rows[0]
    receipt = {
        "schema_version": 1,
        "receipt_type": "wrt_normalized_phrase_copy_shadow",
        "evidence_level": "causal_exact_fx2_probability_trace_shadow",
        "claim_boundary": (
            "Selection-window causal shadow only; not integrated source, a native "
            "candidate archive, a full-corpus score, or a 10.80% proof."
        ),
        "window_id": args.window_id,
        "scope_bytes": args.scope_bytes,
        "substrate": "raw_fx2",
        "inputs": {
            "trace": {"sha256": sha256_file(args.trace), "bytes": args.trace.stat().st_size},
            "wrt_store": {"sha256": sha256_file(args.wrt_store), "bytes": args.wrt_store.stat().st_size},
            "raw_input": {"sha256": sha256_file(args.raw_input), "bytes": args.raw_input.stat().st_size},
            "archive": {"sha256": sha256_file(args.archive), "bytes": args.archive.stat().st_size},
        },
        "model": {
            "grid_mode": args.grid_mode,
            "router": args.router,
            "signature_modes": list(signature_modes),
            "context_lengths": list(CONTEXT_LENGTHS),
            "minimum_supports": sorted({spec.min_support for spec in grid}),
            "blend_ppm": sorted({spec.blend_ppm for spec in grid}),
            **{key: value for key, value in diagnostics.items() if key != "exact"},
        },
        "economics": {
            "target_gap_bytes": 57_404,
            "required_gain_bytes_per_million_before_program_cost": 57.404,
            "program_cost_counted": False,
        },
        "validations": {
            "raw_matches_exact_wrt_decode": True,
            "trace_matches_wrt_store": diagnostics["trace_sha256"] == hashlib.sha256(parsed.stream).hexdigest(),
            "events_update_after_completion": True,
            "current_event_prefix_uses_prior_bits_only": True,
            "future_event_length_exposed": False,
            "archive_payload_bytes": payload_bytes,
            "archive_wrt_bytes": archive_wrt_bytes,
            "baseline_range_match": baseline_values == {payload_bytes},
            "trace_wrt_bytes_match": archive_wrt_bytes == diagnostics["trace_bytes"],
        },
        "selection_rule": "maximize development qbits, break ties by holdout then id",
        "best_by_selection_rule": best,
        "rows": rows,
        "verdict": (
            "freeze_variant_and_run_disjoint_confirmation"
            if float(best["partitions"]["development"]["saved_bytes"]) > 0
            and float(best["partitions"]["holdout"]["saved_bytes"]) > 0
            and int((best.get("exact") or {}).get("saved_bytes", 0)) > 0
            else "retire_unchanged_or_redesign_endpoint"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"best": best, "verdict": receipt["verdict"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
