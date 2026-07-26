#!/usr/bin/env python3
"""Score causal target-conditioned Wiki link surfaces over an exact P1 trace."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import gzip
import json
import os
from pathlib import Path
from typing import Any, Iterable

from fx2_shadow_residual_coder import BinaryArithmeticEncoder, TOTAL, clamp_p1
from streaming_retrieval_shadow import blend_probability
from wrt_entity_trie_fx2_shadow import (
    P1Trace,
    artifact,
    event_bit,
    fast_qbits,
    sha256_bytes,
)
from wrt_exact import ParsedStore, WrtEvent, parse_store


LINK_OPEN = b"[["
LINK_CLOSE = b"]]"
TAIL_BYTES = 4


def split_for(position: int, stream_bytes: int) -> str:
    if position < stream_bytes // 3:
        return "train"
    if position < 2 * stream_bytes // 3:
        return "development"
    return "holdout"


def actual_path(
    counter: Counter[bytes], encoded: bytes
) -> list[tuple[int, int] | None]:
    active = list(counter.items())
    path: list[tuple[int, int] | None] = []
    for bit_index in range(8 * len(encoded)):
        zeros = 0
        ones = 0
        compatible: list[tuple[bytes, int]] = []
        truth = event_bit(encoded, bit_index)
        for code, count in active:
            if bit_index >= 8 * len(code):
                continue
            bit = event_bit(code, bit_index)
            if bit:
                ones += count
            else:
                zeros += count
            if bit == truth:
                compatible.append((code, count))
        support = zeros + ones
        if support:
            p1 = ((2 * ones + 1) * TOTAL) // (2 * support + 2)
            path.append((clamp_p1(p1), support))
        else:
            path.append(None)
        active = compatible
    return path


@dataclass
class SurfaceObserver:
    mode: str = "none"
    target: list[WrtEvent] = field(default_factory=list)
    surface: list[WrtEvent] = field(default_factory=list)
    active_target: tuple[bytes, ...] = ()
    tail: bytearray = field(default_factory=bytearray)
    piped_links: int = 0
    completed_surfaces: int = 0
    unpiped_links: int = 0
    discarded_boundaries: int = 0

    @property
    def in_surface(self) -> bool:
        return self.mode == "surface" and bool(self.active_target)

    @property
    def surface_prefix(self) -> tuple[bytes, ...]:
        return tuple(event.encoded for event in self.surface)

    @staticmethod
    def strip_suffix(
        events: list[WrtEvent], byte_count: int
    ) -> tuple[bytes, ...] | None:
        kept = list(events)
        remaining = byte_count
        while remaining > 0 and kept:
            event = kept.pop()
            if not event.decoded:
                continue
            if len(event.decoded) > remaining:
                return None
            remaining -= len(event.decoded)
        if remaining:
            return None
        return tuple(event.encoded for event in kept)

    def reset(self) -> None:
        self.mode = "none"
        self.target.clear()
        self.surface.clear()
        self.active_target = ()

    def observe(
        self, event: WrtEvent
    ) -> tuple[tuple[bytes, ...], tuple[bytes, ...]] | None:
        if self.mode == "target":
            self.target.append(event)
        elif self.mode == "surface":
            self.surface.append(event)

        self.tail.extend(event.decoded)
        if len(self.tail) > TAIL_BYTES:
            del self.tail[: len(self.tail) - TAIL_BYTES]
        tail = bytes(self.tail)

        if self.mode == "target":
            if tail.endswith(b"|"):
                target = self.strip_suffix(self.target, 1)
                if target:
                    self.active_target = target
                    self.surface.clear()
                    self.mode = "surface"
                    self.piped_links += 1
                else:
                    self.discarded_boundaries += 1
                    self.reset()
            elif tail.endswith(LINK_CLOSE):
                self.unpiped_links += 1
                self.reset()
            return None

        if self.mode == "surface" and tail.endswith(LINK_CLOSE):
            surface = self.strip_suffix(self.surface, len(LINK_CLOSE))
            target = self.active_target
            self.reset()
            if target and surface:
                self.completed_surfaces += 1
                return target, surface
            if surface is None:
                self.discarded_boundaries += 1
            return None

        if self.mode == "none" and tail.endswith(LINK_OPEN):
            self.mode = "target"
            self.target.clear()
            self.surface.clear()
            self.active_target = ()
        return None

    def receipt(self) -> dict[str, int]:
        return {
            "piped_links": self.piped_links,
            "completed_surfaces": self.completed_surfaces,
            "unpiped_links": self.unpiped_links,
            "discarded_non_event_aligned_boundaries": self.discarded_boundaries,
        }


@dataclass
class SurfaceTable:
    counts: dict[
        tuple[bytes, ...], dict[tuple[bytes, ...], Counter[bytes]]
    ] = field(default_factory=lambda: defaultdict(lambda: defaultdict(Counter)))
    target_observations: Counter[tuple[bytes, ...]] = field(default_factory=Counter)
    inserted_surfaces: int = 0

    def observe(
        self, target: tuple[bytes, ...], surface: tuple[bytes, ...]
    ) -> None:
        contexts = self.counts[target]
        for index, code in enumerate(surface):
            contexts[surface[:index]][code] += 1
        self.target_observations[target] += 1
        self.inserted_surfaces += 1

    def candidates(
        self, target: tuple[bytes, ...], prefix: tuple[bytes, ...]
    ) -> Counter[bytes] | None:
        contexts = self.counts.get(target)
        if contexts is None:
            return None
        counter = contexts.get(prefix)
        return counter if counter else None

    def state_bytes_estimate(self) -> int:
        total = 0
        for target, contexts in self.counts.items():
            total += 16 + sum(len(code) for code in target)
            for prefix, counter in contexts.items():
                total += 12 + sum(len(code) for code in prefix)
                total += sum(8 + len(code) for code in counter)
        return total

    def receipt(self) -> dict[str, int]:
        return {
            "targets": len(self.counts),
            "inserted_surfaces": self.inserted_surfaces,
            "contexts": sum(len(contexts) for contexts in self.counts.values()),
            "continuation_edges": sum(
                len(counter)
                for contexts in self.counts.values()
                for counter in contexts.values()
            ),
            "state_bytes_estimate": self.state_bytes_estimate(),
        }


@dataclass(frozen=True)
class Spec:
    minimum_target_observations: int
    minimum_support: int
    blend_ppm: int
    gate: str

    @property
    def name(self) -> str:
        return (
            f"surface_o{self.minimum_target_observations}_"
            f"s{self.minimum_support}_b{self.blend_ppm}_{self.gate}"
        )


@dataclass
class Stats:
    gains: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    active_rows: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    eligible_rows: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    target_bank: dict[tuple[bytes, ...], int] = field(default_factory=dict)
    current_event_gain: int = 0


def iter_positions(
    parsed: ParsedStore,
) -> Iterable[tuple[int, WrtEvent | None, bool]]:
    event_index = 0
    active_start: int | None = None
    for position in range(len(parsed.stream)):
        while (
            event_index < len(parsed.events)
            and position >= parsed.events[event_index].end
        ):
            event_index += 1
        event = (
            parsed.events[event_index]
            if event_index < len(parsed.events)
            and parsed.events[event_index].start <= position < parsed.events[event_index].end
            else None
        )
        is_new = event is not None and event.start != active_start
        if is_new:
            active_start = event.start
        yield position, event, is_new


def score_grid(
    parsed: ParsedStore, trace: P1Trace, specs: list[Spec]
) -> tuple[dict[str, Stats], SurfaceTable, SurfaceObserver]:
    states = {spec.name: Stats() for spec in specs}
    table = SurfaceTable()
    observer = SurfaceObserver()
    path: list[tuple[int, int] | None] = []
    path_target: tuple[bytes, ...] = ()
    for position, event, is_new in iter_positions(parsed):
        if is_new and event is not None:
            path_target = observer.active_target if observer.in_surface else ()
            counter = (
                table.candidates(path_target, observer.surface_prefix)
                if path_target
                else None
            )
            path = actual_path(counter, event.encoded) if counter else []
            for state in states.values():
                state.current_event_gain = 0
        partition = split_for(position, len(parsed.stream))
        for bit_position in range(8):
            bit = (parsed.stream[position] >> (7 - bit_position)) & 1
            base_p1 = trace.p1(position * 8 + bit_position)
            endpoint = None
            if event is not None and path:
                relative_bit = (position - event.start) * 8 + bit_position
                if relative_bit < len(path):
                    endpoint = path[relative_bit]
            if endpoint is None:
                continue
            endpoint_p1, support = endpoint
            observations = table.target_observations[path_target]
            base_qbits = fast_qbits(bit, base_p1)
            for spec in specs:
                state = states[spec.name]
                if (
                    observations < spec.minimum_target_observations
                    or support < spec.minimum_support
                ):
                    continue
                state.eligible_rows[partition] += 1
                state.eligible_rows["all"] += 1
                candidate_p1 = blend_probability(
                    base_p1, endpoint_p1, spec.blend_ppm
                )
                gain = base_qbits - fast_qbits(bit, candidate_p1)
                state.current_event_gain += gain
                active = (
                    spec.gate == "always"
                    or state.target_bank.get(path_target, 0) >= 0
                )
                if active:
                    state.gains[partition] += gain
                    state.gains["all"] += gain
                    state.active_rows[partition] += 1
                    state.active_rows["all"] += 1
        if event is not None and position == event.end - 1:
            if path_target and path:
                for state in states.values():
                    bank = state.target_bank.get(path_target, 0)
                    state.target_bank[path_target] = max(
                        -(1 << 24),
                        min(1 << 24, bank + state.current_event_gain),
                    )
            completed = observer.observe(event)
            if completed is not None:
                table.observe(*completed)
    return states, table, observer


def exact_replay(
    parsed: ParsedStore,
    trace: P1Trace,
    spec: Spec,
    block_bytes: int,
) -> dict[str, Any]:
    table = SurfaceTable()
    observer = SurfaceObserver()
    target_bank: dict[tuple[bytes, ...], int] = {}
    encoders = {
        name: (BinaryArithmeticEncoder(), BinaryArithmeticEncoder())
        for name in ("all", "train", "development", "holdout")
    }
    qbits: dict[str, int] = defaultdict(int)
    active_rows: dict[str, int] = defaultdict(int)
    eligible_rows: dict[str, int] = defaultdict(int)
    block_qbits: dict[int, int] = defaultdict(int)
    path: list[tuple[int, int] | None] = []
    path_target: tuple[bytes, ...] = ()
    current_event_gain = 0
    for position, event, is_new in iter_positions(parsed):
        if is_new and event is not None:
            path_target = observer.active_target if observer.in_surface else ()
            counter = (
                table.candidates(path_target, observer.surface_prefix)
                if path_target
                else None
            )
            path = actual_path(counter, event.encoded) if counter else []
            current_event_gain = 0
        partition = split_for(position, len(parsed.stream))
        for bit_position in range(8):
            bit = (parsed.stream[position] >> (7 - bit_position)) & 1
            base_p1 = trace.p1(position * 8 + bit_position)
            endpoint = None
            if event is not None and path:
                relative_bit = (position - event.start) * 8 + bit_position
                if relative_bit < len(path):
                    endpoint = path[relative_bit]
            candidate_p1 = base_p1
            if endpoint is not None:
                endpoint_p1, support = endpoint
                observations = table.target_observations[path_target]
                if (
                    observations >= spec.minimum_target_observations
                    and support >= spec.minimum_support
                ):
                    eligible_rows[partition] += 1
                    eligible_rows["all"] += 1
                    proposed = blend_probability(
                        base_p1, endpoint_p1, spec.blend_ppm
                    )
                    gain = fast_qbits(bit, base_p1) - fast_qbits(bit, proposed)
                    current_event_gain += gain
                    active = (
                        spec.gate == "always"
                        or target_bank.get(path_target, 0) >= 0
                    )
                    if active:
                        candidate_p1 = proposed
                        qbits[partition] += gain
                        qbits["all"] += gain
                        active_rows[partition] += 1
                        active_rows["all"] += 1
                        if partition == "holdout":
                            block_qbits[position // block_bytes] += gain
            for name in ("all", partition):
                encoders[name][0].encode(bit, base_p1)
                encoders[name][1].encode(bit, candidate_p1)
        if event is not None and position == event.end - 1:
            if path_target and path:
                target_bank[path_target] = max(
                    -(1 << 24),
                    min(
                        1 << 24,
                        target_bank.get(path_target, 0) + current_event_gain,
                    ),
                )
            completed = observer.observe(event)
            if completed is not None:
                table.observe(*completed)
    exact: dict[str, dict[str, int]] = {}
    for name, (baseline, candidate) in encoders.items():
        baseline.finish()
        candidate.finish()
        exact[name] = {
            "baseline_bytes": baseline.byte_count,
            "candidate_bytes": candidate.byte_count,
            "saved_bytes": baseline.byte_count - candidate.byte_count,
        }
    blocks = [
        {"block_id": block, "gain_bytes": gain / 2048.0}
        for block, gain in sorted(block_qbits.items())
    ]
    return {
        "exact_arithmetic": exact,
        "qbit_gain": dict(qbits),
        "active_rows": dict(active_rows),
        "eligible_rows": dict(eligible_rows),
        "block_rows": blocks,
        "positive_blocks": sum(row["gain_bytes"] > 0 for row in blocks),
        "regressing_blocks": sum(row["gain_bytes"] < 0 for row in blocks),
        "largest_block_regression_bytes": max(
            (-row["gain_bytes"] for row in blocks if row["gain_bytes"] < 0),
            default=0.0,
        ),
        "table": table.receipt(),
        "observer": observer.receipt(),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    parsed = parse_store(args.store, args.dictionary)
    with args.raw.open("rb") as source:
        raw = source.read(parsed.raw_length)
    if raw != parsed.decoded:
        raise RuntimeError("WRT store does not reconstruct the declared raw prefix")
    trace = P1Trace(args.base_p1)
    try:
        if trace.rows != len(parsed.stream) * 8:
            raise RuntimeError("base probability trace does not cover the WRT stream")
        blends = tuple(int(value) for value in args.blends.split(",") if value)
        observations = tuple(
            int(value) for value in args.minimum_target_observations.split(",") if value
        )
        supports = tuple(
            int(value) for value in args.minimum_supports.split(",") if value
        )
        gates = tuple(value for value in args.gates.split(",") if value)
        specs = [
            Spec(observation, support, blend, gate)
            for observation in observations
            for support in supports
            for blend in blends
            for gate in gates
        ]
        states, discovery_table, discovery_observer = score_grid(
            parsed, trace, specs
        )
        ranked = sorted(
            specs,
            key=lambda spec: (
                -states[spec.name].gains["development"],
                spec.minimum_target_observations,
                spec.minimum_support,
                spec.blend_ppm,
                spec.gate,
            ),
        )
        selected = ranked[0]
        replay = exact_replay(parsed, trace, selected, args.block_bytes)
        source_gzip_bytes = len(gzip.compress(Path(__file__).read_bytes(), compresslevel=9))
        holdout_stream_bytes = len(parsed.stream) - 2 * (len(parsed.stream) // 3)
        holdout_raw_estimate = (
            parsed.raw_length * holdout_stream_bytes / len(parsed.stream)
        )
        heldout_saved = replay["exact_arithmetic"]["holdout"]["saved_bytes"]
        gross_per_1m = (
            heldout_saved * 1_000_000 / holdout_raw_estimate
            if holdout_raw_estimate
            else 0.0
        )
        required_per_1m = (
            args.minimum_research_bytes_per_1m + source_gzip_bytes / 1000.0
        )
        candidate_rows = []
        for spec in ranked:
            stats = states[spec.name]
            candidate_rows.append(
                {
                    "candidate": spec.name,
                    "minimum_target_observations": spec.minimum_target_observations,
                    "minimum_support": spec.minimum_support,
                    "blend_ppm": spec.blend_ppm,
                    "gate": spec.gate,
                    "train_gain_bytes": stats.gains["train"] / 2048.0,
                    "development_gain_bytes": stats.gains["development"] / 2048.0,
                    "holdout_gain_bytes": stats.gains["holdout"] / 2048.0,
                    "development_active_rows": stats.active_rows["development"],
                    "holdout_active_rows": stats.active_rows["holdout"],
                }
            )
        verdict = (
            "viable_for_disjoint_confirmation"
            if gross_per_1m >= required_per_1m
            and heldout_saved > 0
            and replay["largest_block_regression_bytes"]
            <= args.maximum_block_regression_bytes
            else "positive_but_below_research_gate"
            if heldout_saved > 0
            else "retire_exact_target_surface_mechanism"
        )
        return {
            "schema": "wrt_link_surface_cmem_shadow_v1",
            "evidence_level": "causal_shadow",
            "claim_boundary": (
                "Exact endpoint428 arithmetic shadow only. Native integration, "
                "counted package composition, disjoint transfer, roundtrip, RSS, "
                "runtime replacement value, and full-corpus proof remain required."
            ),
            "inputs": {
                "store": artifact(args.store),
                "raw_corpus": artifact(args.raw),
                "raw_scope_sha256": sha256_bytes(raw),
                "dictionary": artifact(args.dictionary),
                "base_p1": artifact(args.base_p1),
            },
            "scope": {
                "raw_bytes": parsed.raw_length,
                "wrt_stream_bytes": len(parsed.stream),
                "rows": len(parsed.stream) * 8,
                "events": len(parsed.events),
                "split_policy": "chronological_stream_thirds_v1",
                "holdout_raw_bytes_estimate_by_stream_fraction": holdout_raw_estimate,
            },
            "selection": {
                "rule": "maximum development qbit gain; holdout excluded from ranking",
                "selected_candidate": selected.name,
                "candidates": candidate_rows,
            },
            "exact_replay": replay,
            "discovery_state": {
                "table": discovery_table.receipt(),
                "observer": discovery_observer.receipt(),
            },
            "economics": {
                "heldout_gross_saved_bytes_per_1m_raw_estimate": gross_per_1m,
                "minimum_research_bytes_per_1m": args.minimum_research_bytes_per_1m,
                "source_gzip9_bytes": source_gzip_bytes,
                "source_cost_bytes_per_1m_at_1g": source_gzip_bytes / 1000.0,
                "required_gross_bytes_per_1m": required_per_1m,
                "forecast_margin_bytes": args.forecast_margin_bytes,
                "packed_state_bytes_estimate": replay["table"]["state_bytes_estimate"],
            },
            "identity": {
                "raw_roundtrip_ok": True,
                "base_trace_full_stream_coverage": True,
                "target_known_before_surface_prediction": True,
                "updates_after_completed_surface": True,
                "selection_reads_holdout": False,
                "static_alias_payload_bytes": 0,
                "decoder_replayable_state": True,
            },
            "verdict": verdict,
            "promotion_authorized": verdict == "viable_for_disjoint_confirmation",
        }
    finally:
        trace.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--base-p1", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-target-observations", default="1,2")
    parser.add_argument("--minimum-supports", default="1,2")
    parser.add_argument("--blends", default="10000,25000,50000,100000,250000")
    parser.add_argument("--gates", default="always,target_positive")
    parser.add_argument("--block-bytes", type=int, default=16_384)
    parser.add_argument("--minimum-research-bytes-per-1m", type=float, default=200.0)
    parser.add_argument("--maximum-block-regression-bytes", type=float, default=8.0)
    parser.add_argument("--forecast-margin-bytes", type=int, default=110_677)
    args = parser.parse_args()
    for path in (args.store, args.raw, args.dictionary, args.base_p1):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    if any(gate not in ("always", "target_positive") for gate in args.gates.split(",")):
        raise SystemExit("gates must be always or target_positive")
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(
        json.dumps(
            {
                "selected": receipt["selection"]["selected_candidate"],
                "heldout_saved_bytes": receipt["exact_replay"]["exact_arithmetic"][
                    "holdout"
                ]["saved_bytes"],
                "gross_per_1m": receipt["economics"][
                    "heldout_gross_saved_bytes_per_1m_raw_estimate"
                ],
                "required_per_1m": receipt["economics"][
                    "required_gross_bytes_per_1m"
                ],
                "verdict": receipt["verdict"],
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
