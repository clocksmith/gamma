#!/usr/bin/env python3
"""Route WRT entity continuations with causal node-local reflected regret.

The underlying entity trie is rebuilt entirely from completed WRT title and
link events.  For each link-target event, the route decision is frozen before
the event's first bit.  After that event is decoded, its exact counterfactual
gain updates only the trie node that predicted it.  Selection stops at the
declared training boundary; only the selected configuration is replayed on the
heldout suffix with exact arithmetic coding.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Any

from fx2_shadow_residual_coder import BinaryArithmeticEncoder
from streaming_retrieval_shadow import blend_probability
from wrt_entity_trie_fx2_shadow import (
    EntityObserver,
    EntityTrie,
    P1Trace,
    ParsedStore,
    WrtEvent,
    artifact,
    event_prefix,
    fast_qbits,
    make_tries,
    observe_and_insert,
    parse_store,
    sha256_bytes,
)


ENTITY_TOOL = Path(__file__).with_name("wrt_entity_trie_fx2_shadow.py")


@dataclass
class NodeRegretState:
    observations: int = 0
    cumulative_gain_qbits: int = 0
    reflected_wealth_qbits: int = 0
    positive_events: int = 0
    negative_events: int = 0


@dataclass
class NodeRegretRouter:
    """A decoder-causal specialist with recoverable reflected wealth."""

    minimum_observations: int
    margin_qbits: int
    states: dict[int, NodeRegretState] = field(default_factory=dict)

    def active(self, node: int | None) -> bool:
        if node is None:
            return False
        state = self.states.get(node)
        return bool(
            state is not None
            and state.observations >= self.minimum_observations
            and state.reflected_wealth_qbits > self.margin_qbits
        )

    def update(self, node: int | None, gain_qbits: int, eligible_rows: int) -> None:
        if node is None or eligible_rows <= 0:
            return
        state = self.states.setdefault(node, NodeRegretState())
        state.observations += 1
        state.cumulative_gain_qbits += gain_qbits
        state.reflected_wealth_qbits = max(
            0, state.reflected_wealth_qbits + gain_qbits
        )
        state.positive_events += int(gain_qbits > 0)
        state.negative_events += int(gain_qbits < 0)

    @property
    def state_bytes_estimate(self) -> int:
        return len(self.states) * 32

    def receipt(self) -> dict[str, int]:
        rows = tuple(self.states.values())
        return {
            "node_states": len(rows),
            "observed_events": sum(row.observations for row in rows),
            "positive_events": sum(row.positive_events for row in rows),
            "negative_events": sum(row.negative_events for row in rows),
            "cumulative_gain_qbits": sum(
                row.cumulative_gain_qbits for row in rows
            ),
            "reflected_wealth_qbits": sum(
                row.reflected_wealth_qbits for row in rows
            ),
            "maximum_node_wealth_qbits": max(
                (row.reflected_wealth_qbits for row in rows), default=0
            ),
            "state_bytes_estimate": self.state_bytes_estimate,
        }


@dataclass(frozen=True)
class RouterSpec:
    trie_name: str
    minimum_prefix_events: int
    blend_ppm: int
    minimum_observations: int
    margin_qbits: int

    @property
    def name(self) -> str:
        return (
            f"{self.trie_name}_p{self.minimum_prefix_events}"
            f"_b{self.blend_ppm}_o{self.minimum_observations}"
            f"_m{self.margin_qbits}"
        )


@dataclass
class EventRouteState:
    node: int | None
    prefix_eligible: bool
    routed: bool
    eligible_rows: int = 0
    active_rows: int = 0
    heldout_active_rows: int = 0
    counterfactual_gain_qbits: int = 0
    heldout_counterfactual_gain_qbits: int = 0


@dataclass
class DiscoveryTotals:
    gain_qbits: int = 0
    active_rows: int = 0
    eligible_events: int = 0
    routed_events: int = 0
    counterfactual_gain_qbits: int = 0
    positive_event_oracle_qbits: int = 0

    def receipt(self) -> dict[str, float | int]:
        return {
            "gain_qbits": self.gain_qbits,
            "gain_bytes": self.gain_qbits / 2048.0,
            "active_rows": self.active_rows,
            "eligible_events": self.eligible_events,
            "routed_events": self.routed_events,
            "counterfactual_gain_bytes": self.counterfactual_gain_qbits / 2048.0,
            "positive_event_oracle_bytes": self.positive_event_oracle_qbits
            / 2048.0,
        }


def event_at(
    events: tuple[WrtEvent, ...], event_index: int, position: int
) -> tuple[int, WrtEvent | None]:
    while event_index < len(events) and position >= events[event_index].end:
        event_index += 1
    if (
        event_index < len(events)
        and events[event_index].start <= position < events[event_index].end
    ):
        return event_index, events[event_index]
    return event_index, None


def make_specs(args: argparse.Namespace) -> list[RouterSpec]:
    trie_names = tuple(value for value in args.tries.split(",") if value)
    invalid = sorted(set(trie_names) - {"title", "link", "combined"})
    if invalid:
        raise ValueError(f"unknown trie names: {','.join(invalid)}")
    prefix_floors = tuple(
        int(value) for value in args.minimum_prefix_events.split(",") if value
    )
    blends = tuple(int(value) for value in args.blends.split(",") if value)
    observation_floors = tuple(
        int(value) for value in args.router_minimum_observations.split(",") if value
    )
    margins = tuple(
        int(value) for value in args.router_margin_qbits.split(",") if value
    )
    specs = [
        RouterSpec(
            trie_name=trie_name,
            minimum_prefix_events=prefix_floor,
            blend_ppm=blend,
            minimum_observations=observation_floor,
            margin_qbits=margin,
        )
        for trie_name in trie_names
        for prefix_floor in prefix_floors
        for blend in blends
        for observation_floor in observation_floors
        for margin in margins
    ]
    if not specs:
        raise ValueError("router grid is empty")
    if any(not 0 < spec.blend_ppm <= 1_000_000 for spec in specs):
        raise ValueError("blend weights must be in 1..1000000")
    if any(spec.minimum_prefix_events < 0 for spec in specs):
        raise ValueError("prefix floors must be nonnegative")
    if any(spec.minimum_observations < 0 for spec in specs):
        raise ValueError("observation floors must be nonnegative")
    if any(spec.margin_qbits < 0 for spec in specs):
        raise ValueError("router margins must be nonnegative")
    return specs


def start_event_states(
    observer: EntityObserver,
    tries: dict[str, EntityTrie],
    specs: list[RouterSpec],
    routers: dict[str, NodeRegretRouter],
) -> tuple[dict[str, int | None], list[EventRouteState]]:
    path = observer.link_prefix if observer.in_link else ()
    nodes = {
        name: trie.follow(path) if observer.in_link else None
        for name, trie in tries.items()
    }
    states: list[EventRouteState] = []
    for spec in specs:
        node = nodes[spec.trie_name]
        prefix_eligible = (
            observer.in_link and len(path) >= spec.minimum_prefix_events
        )
        states.append(
            EventRouteState(
                node=node,
                prefix_eligible=prefix_eligible,
                routed=prefix_eligible and routers[spec.name].active(node),
            )
        )
    return nodes, states


def predict_by_trie(
    tries: dict[str, EntityTrie],
    nodes: dict[str, int | None],
    relative_bit: int,
    prefix: int,
    min_support: int,
    alpha2: int,
) -> dict[str, int | None]:
    return {
        name: trie.predict(
            nodes[name], relative_bit, prefix, min_support, alpha2
        )[0]
        for name, trie in tries.items()
    }


def finish_discovery_event(
    specs: list[RouterSpec],
    states: list[EventRouteState],
    routers: dict[str, NodeRegretRouter],
    totals: dict[str, DiscoveryTotals],
) -> None:
    for spec, state in zip(specs, states, strict=True):
        if state.eligible_rows <= 0:
            continue
        total = totals[spec.name]
        total.eligible_events += 1
        total.routed_events += int(state.routed and state.active_rows > 0)
        total.counterfactual_gain_qbits += state.counterfactual_gain_qbits
        total.positive_event_oracle_qbits += max(
            0, state.counterfactual_gain_qbits
        )
        routers[spec.name].update(
            state.node,
            state.counterfactual_gain_qbits,
            state.eligible_rows,
        )


def discover(
    parsed: ParsedStore,
    trace: P1Trace,
    specs: list[RouterSpec],
    *,
    train_stream_bytes: int,
    cap_nodes: int,
    min_support: int,
    alpha2: int,
    minimum_entity_events: int,
    maximum_entity_events: int,
) -> tuple[
    dict[str, DiscoveryTotals],
    dict[str, NodeRegretRouter],
    dict[str, EntityTrie],
    EntityObserver,
]:
    totals = {spec.name: DiscoveryTotals() for spec in specs}
    routers = {
        spec.name: NodeRegretRouter(
            minimum_observations=spec.minimum_observations,
            margin_qbits=spec.margin_qbits,
        )
        for spec in specs
    }
    tries = make_tries(cap_nodes)
    observer = EntityObserver()
    events = parsed.events
    event_index = 0
    active_event_start: int | None = None
    nodes = {name: None for name in tries}
    states: list[EventRouteState] = []
    limit = min(train_stream_bytes, len(parsed.stream))

    for position in range(limit):
        event_index, event = event_at(events, event_index, position)
        if event is not None and event.start != active_event_start:
            active_event_start = event.start
            nodes, states = start_event_states(observer, tries, specs, routers)
        for bit_position in range(8):
            bit = (parsed.stream[position] >> (7 - bit_position)) & 1
            base_p1 = trace.p1(position * 8 + bit_position)
            if event is None:
                continue
            relative_bit = (position - event.start) * 8 + bit_position
            prefix = event_prefix(event.encoded, relative_bit)
            endpoints = predict_by_trie(
                tries, nodes, relative_bit, prefix, min_support, alpha2
            )
            base_qbits = fast_qbits(bit, base_p1)
            for spec, state in zip(specs, states, strict=True):
                endpoint_p1 = endpoints[spec.trie_name]
                if not state.prefix_eligible or endpoint_p1 is None:
                    continue
                candidate_p1 = blend_probability(
                    base_p1, endpoint_p1, spec.blend_ppm
                )
                gain = base_qbits - fast_qbits(bit, candidate_p1)
                state.eligible_rows += 1
                state.counterfactual_gain_qbits += gain
                if state.routed:
                    state.active_rows += 1
                    totals[spec.name].active_rows += 1
                    totals[spec.name].gain_qbits += gain
        if event is not None and position == event.end - 1:
            finish_discovery_event(specs, states, routers, totals)
            observe_and_insert(
                observer,
                tries,
                event,
                minimum_entity_events,
                maximum_entity_events,
            )
    return totals, routers, tries, observer


def exact_replay(
    parsed: ParsedStore,
    trace: P1Trace,
    spec: RouterSpec,
    *,
    train_stream_bytes: int,
    cap_nodes: int,
    min_support: int,
    alpha2: int,
    minimum_entity_events: int,
    maximum_entity_events: int,
    block_bytes: int,
) -> dict[str, Any]:
    tries = make_tries(cap_nodes)
    observer = EntityObserver()
    router = NodeRegretRouter(
        minimum_observations=spec.minimum_observations,
        margin_qbits=spec.margin_qbits,
    )
    baseline = BinaryArithmeticEncoder()
    candidate = BinaryArithmeticEncoder()
    heldout_baseline = BinaryArithmeticEncoder()
    heldout_candidate = BinaryArithmeticEncoder()
    events = parsed.events
    event_index = 0
    active_event_start: int | None = None
    node: int | None = None
    state: EventRouteState | None = None
    block_qbits: dict[int, int] = {}
    train_gain_qbits = 0
    heldout_gain_qbits = 0
    active_rows = 0
    heldout_active_rows = 0
    eligible_events = 0
    routed_events = 0
    heldout_eligible_events = 0
    heldout_routed_events = 0
    heldout_positive_event_oracle_qbits = 0

    for position in range(len(parsed.stream)):
        event_index, event = event_at(events, event_index, position)
        if event is not None and event.start != active_event_start:
            active_event_start = event.start
            path = observer.link_prefix if observer.in_link else ()
            node = tries[spec.trie_name].follow(path) if observer.in_link else None
            prefix_eligible = (
                observer.in_link and len(path) >= spec.minimum_prefix_events
            )
            state = EventRouteState(
                node=node,
                prefix_eligible=prefix_eligible,
                routed=prefix_eligible and router.active(node),
            )
        for bit_position in range(8):
            bit = (parsed.stream[position] >> (7 - bit_position)) & 1
            base_p1 = trace.p1(position * 8 + bit_position)
            candidate_p1 = base_p1
            gain = 0
            if event is not None and state is not None and state.prefix_eligible:
                relative_bit = (position - event.start) * 8 + bit_position
                prefix = event_prefix(event.encoded, relative_bit)
                endpoint_p1 = tries[spec.trie_name].predict(
                    node,
                    relative_bit,
                    prefix,
                    min_support,
                    alpha2,
                )[0]
                if endpoint_p1 is not None:
                    mixed_p1 = blend_probability(
                        base_p1, endpoint_p1, spec.blend_ppm
                    )
                    counterfactual_gain = fast_qbits(
                        bit, base_p1
                    ) - fast_qbits(bit, mixed_p1)
                    state.eligible_rows += 1
                    state.counterfactual_gain_qbits += counterfactual_gain
                    if position >= train_stream_bytes:
                        state.heldout_counterfactual_gain_qbits += (
                            counterfactual_gain
                        )
                    if state.routed:
                        candidate_p1 = mixed_p1
                        gain = counterfactual_gain
                        state.active_rows += 1
                        active_rows += 1
                        if position >= train_stream_bytes:
                            state.heldout_active_rows += 1
                            heldout_active_rows += 1
            baseline.encode(bit, base_p1)
            candidate.encode(bit, candidate_p1)
            if position < train_stream_bytes:
                train_gain_qbits += gain
            else:
                heldout_baseline.encode(bit, base_p1)
                heldout_candidate.encode(bit, candidate_p1)
                heldout_gain_qbits += gain
                block = position // block_bytes
                block_qbits[block] = block_qbits.get(block, 0) + gain
        if event is not None and position == event.end - 1:
            assert state is not None
            if state.eligible_rows > 0:
                eligible_events += 1
                routed_events += int(state.routed and state.active_rows > 0)
                if event.end > train_stream_bytes:
                    heldout_eligible_events += int(
                        state.heldout_counterfactual_gain_qbits != 0
                        or state.heldout_active_rows > 0
                        or event.start >= train_stream_bytes
                    )
                    heldout_routed_events += int(state.heldout_active_rows > 0)
                    heldout_positive_event_oracle_qbits += max(
                        0, state.heldout_counterfactual_gain_qbits
                    )
                router.update(
                    state.node,
                    state.counterfactual_gain_qbits,
                    state.eligible_rows,
                )
            observe_and_insert(
                observer,
                tries,
                event,
                minimum_entity_events,
                maximum_entity_events,
            )

    baseline.finish()
    candidate.finish()
    heldout_baseline.finish()
    heldout_candidate.finish()
    blocks = [
        {"block_id": block, "gain_bytes": gain / 2048.0}
        for block, gain in sorted(block_qbits.items())
    ]
    return {
        "selected_candidate": spec.name,
        "baseline_bytes": baseline.byte_count,
        "candidate_bytes": candidate.byte_count,
        "saved_bytes": baseline.byte_count - candidate.byte_count,
        "heldout_baseline_bytes": heldout_baseline.byte_count,
        "heldout_candidate_bytes": heldout_candidate.byte_count,
        "heldout_saved_bytes": heldout_baseline.byte_count
        - heldout_candidate.byte_count,
        "train_gain_qbits": train_gain_qbits,
        "heldout_gain_qbits": heldout_gain_qbits,
        "active_rows": active_rows,
        "heldout_active_rows": heldout_active_rows,
        "eligible_events": eligible_events,
        "routed_events": routed_events,
        "heldout_eligible_events": heldout_eligible_events,
        "heldout_routed_events": heldout_routed_events,
        "heldout_positive_event_oracle_bytes": (
            heldout_positive_event_oracle_qbits / 2048.0
        ),
        "block_rows": blocks,
        "positive_blocks": sum(row["gain_bytes"] > 0 for row in blocks),
        "regressing_blocks": sum(row["gain_bytes"] < 0 for row in blocks),
        "largest_block_regression_bytes": max(
            (-row["gain_bytes"] for row in blocks if row["gain_bytes"] < 0),
            default=0.0,
        ),
        "router": router.receipt(),
        "tries": {name: trie.receipt() for name, trie in tries.items()},
        "observer": observer.receipt(),
    }


def spec_receipt(
    spec: RouterSpec,
    totals: DiscoveryTotals,
    router: NodeRegretRouter,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "candidate": spec.name,
        "trie": spec.trie_name,
        "minimum_prefix_events": spec.minimum_prefix_events,
        "blend_ppm": spec.blend_ppm,
        "router_minimum_observations": spec.minimum_observations,
        "router_margin_qbits": spec.margin_qbits,
    }
    row.update(totals.receipt())
    row["router"] = router.receipt()
    return row


def run(args: argparse.Namespace) -> dict[str, Any]:
    parsed = parse_store(args.store, args.dictionary)
    with args.raw.open("rb") as source:
        raw = source.read(parsed.raw_length)
    if len(raw) != parsed.raw_length:
        raise RuntimeError("raw corpus is shorter than the WRT-declared scope")
    if raw != parsed.decoded:
        raise RuntimeError("WRT store does not reconstruct the declared raw prefix")
    trace = P1Trace(args.base_p1)
    try:
        if trace.rows != len(parsed.stream) * 8:
            raise RuntimeError("base probability trace does not cover the exact WRT stream")
        specs = make_specs(args)
        totals, routers, discovery_tries, discovery_observer = discover(
            parsed,
            trace,
            specs,
            train_stream_bytes=args.train_stream_bytes,
            cap_nodes=args.cap_nodes,
            min_support=args.min_support,
            alpha2=args.alpha2,
            minimum_entity_events=args.minimum_entity_events,
            maximum_entity_events=args.maximum_entity_events,
        )
        ranked = sorted(
            specs,
            key=lambda spec: (
                -totals[spec.name].gain_qbits,
                totals[spec.name].active_rows,
                spec.minimum_observations,
                spec.margin_qbits,
                spec.blend_ppm,
                spec.minimum_prefix_events,
                spec.trie_name,
            ),
        )
        selected = ranked[0]
        replay = exact_replay(
            parsed,
            trace,
            selected,
            train_stream_bytes=args.train_stream_bytes,
            cap_nodes=args.cap_nodes,
            min_support=args.min_support,
            alpha2=args.alpha2,
            minimum_entity_events=args.minimum_entity_events,
            maximum_entity_events=args.maximum_entity_events,
            block_bytes=args.block_bytes,
        )
        if replay["train_gain_qbits"] != totals[selected.name].gain_qbits:
            raise RuntimeError("selected training replay differs from discovery")

        heldout_stream_fraction = (
            len(parsed.stream) - args.train_stream_bytes
        ) / len(parsed.stream)
        heldout_raw_bytes_estimate = parsed.raw_length * heldout_stream_fraction
        gross_per_1m = (
            replay["heldout_saved_bytes"] * 1_000_000 / heldout_raw_bytes_estimate
            if heldout_raw_bytes_estimate > 0
            else 0.0
        )
        code_rows = {
            "router_tool": Path(__file__).stat().st_size,
            "entity_trie_tool": ENTITY_TOOL.stat().st_size,
        }
        code_bytes = sum(code_rows.values())
        state_bytes = sum(
            row["state_bytes_estimate"] for row in replay["tries"].values()
        ) + replay["router"]["state_bytes_estimate"]
        required_per_1m = args.forecast_gap_bytes / 1000.0 + code_bytes / 1000.0
        candidates = [
            spec_receipt(spec, totals[spec.name], routers[spec.name])
            for spec in ranked
        ]
        verdict = (
            "positive_heldout_requires_disjoint_and_native_integration"
            if replay["heldout_saved_bytes"] > 0
            and gross_per_1m > required_per_1m
            else "insufficient_realizable_margin_preserve_typed_endpoint_direction"
            if replay["heldout_saved_bytes"] > 0
            else "negative_or_flat_retire_node_regret_entity_router"
        )
        return {
            "schema": "wrt_entity_regret_router_shadow_v1",
            "evidence_level": "train_only_selection_then_exact_heldout_arithmetic_replay",
            "inputs": {
                "store": artifact(args.store),
                "raw_corpus": {
                    "path": str(args.raw.resolve()),
                    "file_bytes": args.raw.stat().st_size,
                    "scoped_bytes": len(raw),
                    "scope_sha256": sha256_bytes(raw),
                },
                "dictionary": artifact(args.dictionary),
                "base_p1": artifact(args.base_p1),
                "base_p1_magic": trace.magic.decode("ascii", errors="replace"),
            },
            "scope": {
                "raw_bytes": parsed.raw_length,
                "wrt_stream_bytes": len(parsed.stream),
                "encoded_rows": len(parsed.stream) * 8,
                "events": len(parsed.events),
                "event_kind_counts": parsed.kind_counts,
                "train_stream_bytes": args.train_stream_bytes,
                "heldout_stream_bytes": len(parsed.stream)
                - args.train_stream_bytes,
                "heldout_raw_bytes_estimate_by_stream_fraction": (
                    heldout_raw_bytes_estimate
                ),
            },
            "parameters": {
                "tries": args.tries.split(","),
                "cap_nodes_per_trie": args.cap_nodes,
                "minimum_support": args.min_support,
                "alpha2": args.alpha2,
                "minimum_entity_events": args.minimum_entity_events,
                "maximum_entity_events": args.maximum_entity_events,
                "minimum_prefix_events": args.minimum_prefix_events,
                "blends_ppm": args.blends,
                "router_minimum_observations": (
                    args.router_minimum_observations
                ),
                "router_margin_qbits": args.router_margin_qbits,
                "block_bytes": args.block_bytes,
                "reflected_regret_update": "wealth=max(0,wealth+event_gain)",
            },
            "selection": {
                "rule": (
                    "maximum training-only causal qbit gain; heldout candidates "
                    "other than the selected row are never evaluated"
                ),
                "selected_candidate": selected.name,
                "selected_training_gain_bytes": totals[selected.name].gain_qbits
                / 2048.0,
                "candidate_count": len(candidates),
                "candidates": candidates,
            },
            "exact_replay": replay,
            "discovery_state": {
                "tries": {
                    name: trie.receipt() for name, trie in discovery_tries.items()
                },
                "observer": discovery_observer.receipt(),
            },
            "economics": {
                "heldout_gross_saved_bytes_per_1m_raw_estimate": gross_per_1m,
                "forecast_gap_bytes_per_1m": args.forecast_gap_bytes / 1000.0,
                "provisional_code_bytes": code_bytes,
                "provisional_code_byte_rows": code_rows,
                "provisional_code_cost_bytes_per_1m_at_1g": code_bytes / 1000.0,
                "required_gross_bytes_per_1m_before_integration_regressions": (
                    required_per_1m
                ),
                "max_incremental_state_bytes_estimate": state_bytes,
            },
            "identity": {
                "raw_roundtrip_ok": True,
                "base_trace_full_stream_coverage": True,
                "route_frozen_before_current_event": True,
                "regret_updated_after_completed_current_event": True,
                "selection_reads_heldout": False,
                "static_entity_payload_bytes": 0,
                "decoder_replayable_state": True,
            },
            "verdict": verdict,
            "promotion_authorized": False,
            "claim_boundary": (
                "This is exact arithmetic shadow evidence on a hash-pinned base "
                "trace. It does not change a constructive archive. Disjoint "
                "confirmation, native integration, source accounting, roundtrip, "
                "determinism, RSS, and official 1G proof remain required."
            ),
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
    parser.add_argument("--train-stream-bytes", type=int, default=100_000)
    parser.add_argument("--cap-nodes", type=int, default=500_000)
    parser.add_argument("--min-support", type=int, default=1)
    parser.add_argument("--alpha2", type=int, default=1)
    parser.add_argument("--minimum-entity-events", type=int, default=1)
    parser.add_argument("--maximum-entity-events", type=int, default=64)
    parser.add_argument("--tries", default="link,combined")
    parser.add_argument("--minimum-prefix-events", default="0,1,2,3,4")
    parser.add_argument("--blends", default="25000,50000,100000")
    parser.add_argument("--router-minimum-observations", default="1,2,4,8")
    parser.add_argument("--router-margin-qbits", default="0,256,1024,4096")
    parser.add_argument("--block-bytes", type=int, default=16_384)
    parser.add_argument("--forecast-gap-bytes", type=int, default=57_404)
    args = parser.parse_args()
    for path in (args.store, args.raw, args.dictionary, args.base_p1):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    if not 0 < args.train_stream_bytes < args.store.stat().st_size:
        raise SystemExit("training boundary must lie inside the stored stream")
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(
        json.dumps(
            {
                "selected": receipt["selection"]["selected_candidate"],
                "training_gain_bytes": receipt["selection"][
                    "selected_training_gain_bytes"
                ],
                "heldout_saved_bytes": receipt["exact_replay"][
                    "heldout_saved_bytes"
                ],
                "gross_per_1m": receipt["economics"][
                    "heldout_gross_saved_bytes_per_1m_raw_estimate"
                ],
                "required_per_1m": receipt["economics"][
                    "required_gross_bytes_per_1m_before_integration_regressions"
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
