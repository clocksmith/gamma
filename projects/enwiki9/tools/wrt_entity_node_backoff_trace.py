#!/usr/bin/env python3
"""Emit an endpoint428-relative WRT entity-node backoff trace.

The existing entity trie supplies a decoder-rebuilt semantic coordinate: the
node reached by the already completed events of the current link target. Its
raw next-event probability loses against endpoint428. This probe instead
learns bounded hierarchical residual calibration from prior occurrences of
the same node, support, and base-probability regime.

Only completed WRT events enter the trie. The current bit is predicted before
its truth updates any counter. No eventual WRT event length is exposed.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import struct
from typing import Any, Sequence

import numpy as np

from fx2_shadow_residual_coder import TOTAL, clamp_p1
from wrt_entity_trie_fx2_shadow import (
    EntityObserver,
    EntityTrie,
    P1Trace,
    event_prefix,
)
from wrt_exact import ParsedStore, WrtEvent, parse_store


PAIR_MAGIC = b"CMXAUX1\0"
PAIR_HEADER_BYTES = 16
Q24 = 1 << 24
PROFILES = ("global", "node")


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
    return min(buckets - 1, (int(p1) * buckets) // TOTAL)


def support_bucket(support: int) -> int:
    if support < 1:
        return 0
    return min(15, support.bit_length() - 1)


@dataclass
class BoundedCounts:
    cap: int
    counts: dict[tuple[Any, ...], list[int]] = field(default_factory=dict)
    blocked: int = 0

    def predict(
        self,
        keys: Sequence[tuple[Any, ...]],
        prior_q24: int,
        prior_strength: int,
    ) -> tuple[int, int]:
        probability = prior_q24
        matches = 0
        for key in keys:
            counts = self.counts.get(key)
            if counts is None:
                continue
            zero, one = counts
            total = zero + one
            probability = (
                one * Q24
                + prior_strength * probability
                + (total + prior_strength) // 2
            ) // (total + prior_strength)
            probability = min(Q24 - 1, max(1, probability))
            matches += 1
        return probability, matches

    def update(self, keys: Sequence[tuple[Any, ...]], bit: int) -> None:
        for key in keys:
            counts = self.counts.get(key)
            if counts is None:
                if len(self.counts) >= self.cap:
                    self.blocked += 1
                    continue
                counts = [0, 0]
                self.counts[key] = counts
            counts[bit] += 1


@dataclass
class EntityNodeBackoff:
    profile: str
    max_contexts: int
    base_buckets: int
    retrieval_buckets: int
    prior_strength: int
    table: BoundedCounts = field(init=False)
    active_rows: int = 0
    maximum_matches: int = 0

    def __post_init__(self) -> None:
        if self.profile not in PROFILES:
            raise ValueError(f"unsupported profile: {self.profile}")
        if self.max_contexts < 1 or self.prior_strength < 1:
            raise ValueError("invalid backoff bounds")
        self.table = BoundedCounts(self.max_contexts)

    def keys(
        self,
        *,
        node: int,
        relative_bit: int,
        base_p1: int,
        retrieval_p1: int,
        support: int,
    ) -> list[tuple[Any, ...]]:
        base_bucket = probability_bucket(base_p1, self.base_buckets)
        retrieval_bucket = probability_bucket(
            retrieval_p1, self.retrieval_buckets
        )
        support_class = support_bucket(support)
        bit_in_byte = relative_bit & 7
        keys: list[tuple[Any, ...]] = [
            (
                "map",
                bit_in_byte,
                base_bucket,
                retrieval_bucket,
                support_class,
            ),
            (
                "position",
                relative_bit,
                base_bucket,
                retrieval_bucket,
                support_class,
            ),
        ]
        if self.profile == "node":
            keys.extend(
                [
                    (
                        "node_coarse",
                        node,
                        bit_in_byte,
                        base_bucket // 4,
                        retrieval_bucket // 2,
                        support_class,
                    ),
                    (
                        "node_exact",
                        node,
                        relative_bit,
                        base_bucket,
                        retrieval_bucket,
                        support_class,
                    ),
                ]
            )
        return keys

    def predict_then_update(
        self,
        *,
        node: int,
        relative_bit: int,
        base_p1: int,
        retrieval_p1: int,
        support: int,
        bit: int,
    ) -> int:
        keys = self.keys(
            node=node,
            relative_bit=relative_bit,
            base_p1=base_p1,
            retrieval_p1=retrieval_p1,
            support=support,
        )
        prior_q24 = (int(base_p1) * Q24 + TOTAL // 2) // TOTAL
        probability, matches = self.table.predict(
            keys, prior_q24, self.prior_strength
        )
        self.table.update(keys, bit)
        if matches:
            self.active_rows += 1
            self.maximum_matches = max(self.maximum_matches, matches)
        endpoint_p1 = (probability * TOTAL + Q24 // 2) // Q24
        return clamp_p1(endpoint_p1)


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
    profile: str,
    cap_nodes: int,
    max_contexts: int,
    min_support: int,
    alpha2: int,
    minimum_entity_events: int,
    maximum_entity_events: int,
    base_buckets: int,
    retrieval_buckets: int,
    prior_strength: int,
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

    trie = EntityTrie(cap_nodes=cap_nodes)
    observer = EntityObserver()
    model = EntityNodeBackoff(
        profile=profile,
        max_contexts=max_contexts,
        base_buckets=base_buckets,
        retrieval_buckets=retrieval_buckets,
        prior_strength=prior_strength,
    )
    event_index = 0
    current_event: WrtEvent | None = None
    eligible_rows = 0
    events = parsed.events
    row = 0
    for position, byte in enumerate(parsed.stream):
        if position >= 6 and current_event is None:
            if event_index >= len(events) or events[event_index].start != position:
                raise ValueError("missing WRT event at stream position")
            current_event = events[event_index]

        for bit_position in range(8):
            bit = (byte >> (7 - bit_position)) & 1
            base_value = trace.p1(row)
            pair[row, 0] = base_value
            endpoint_value = base_value
            if current_event is not None and observer.in_link:
                node = trie.follow(observer.link_prefix)
                if node is not None:
                    relative_bit = (
                        (position - current_event.start) * 8 + bit_position
                    )
                    current_prefix = event_prefix(
                        current_event.encoded, relative_bit
                    )
                    retrieval_value, support = trie.predict(
                        node,
                        relative_bit,
                        current_prefix,
                        min_support,
                        alpha2,
                    )
                    if retrieval_value is not None:
                        eligible_rows += 1
                        endpoint_value = model.predict_then_update(
                            node=node,
                            relative_bit=relative_bit,
                            base_p1=base_value,
                            retrieval_p1=retrieval_value,
                            support=support,
                            bit=bit,
                        )
            pair[row, 1] = endpoint_value
            row += 1

        if current_event is not None and position + 1 == current_event.end:
            completed = observer.observe(current_event)
            if completed is not None:
                _kind, sequence = completed
                if minimum_entity_events <= len(sequence) <= maximum_entity_events:
                    trie.insert(sequence)
            event_index += 1
            current_event = None

    if event_index != len(events) or row != rows:
        raise ValueError("entity-node replay did not consume the exact stream")
    pair.flush()
    del pair
    trace.close()
    return {
        "schema": "wrt_entity_node_backoff_trace_v1",
        "evidence_level": "causal_bounded_discovery_probability_trace",
        "claim_boundary": (
            "Endpoint trace only. Exact held-out blend replay, incremental "
            "source cost, native integration, roundtrip, resources, and full "
            "corpus official accounting remain."
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
            "trie_contains_completed_entities_only": True,
            "current_event_prefix_uses_prior_bits_only": True,
            "current_truth_updates_backoff_after_prediction": True,
            "total_event_length_never_exposed": True,
        },
        "model": {
            "profile": profile,
            "eligible_rows": eligible_rows,
            "active_rows_with_prior_counts": model.active_rows,
            "maximum_hierarchical_matches": model.maximum_matches,
            "contexts_used": len(model.table.counts),
            "context_insertions_blocked": model.table.blocked,
            "estimated_context_state_bytes_at_24_per_context": (
                len(model.table.counts) * 24
            ),
            "base_probability_buckets": base_buckets,
            "retrieval_probability_buckets": retrieval_buckets,
            "prior_strength": prior_strength,
            "minimum_retrieval_support": min_support,
            "trie": trie.receipt(),
            "observer": observer.receipt(),
        },
        "output": artifact(output_trace),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit a causal WRT entity-node residual backoff trace."
    )
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--base-p1", type=Path, required=True)
    parser.add_argument("--output-trace", type=Path, required=True)
    parser.add_argument("--output-receipt", type=Path, required=True)
    parser.add_argument("--profile", choices=PROFILES, default="node")
    parser.add_argument("--cap-nodes", type=int, default=100_000)
    parser.add_argument("--max-contexts", type=int, default=200_000)
    parser.add_argument("--min-support", type=int, default=1)
    parser.add_argument("--alpha2", type=int, default=1)
    parser.add_argument("--minimum-entity-events", type=int, default=1)
    parser.add_argument("--maximum-entity-events", type=int, default=64)
    parser.add_argument("--base-buckets", type=int, default=32)
    parser.add_argument("--retrieval-buckets", type=int, default=16)
    parser.add_argument("--prior-strength", type=int, default=8)
    args = parser.parse_args()
    receipt = run(
        store=args.store,
        dictionary=args.dictionary,
        raw_input=args.raw_input,
        base_p1=args.base_p1,
        output_trace=args.output_trace,
        profile=args.profile,
        cap_nodes=args.cap_nodes,
        max_contexts=args.max_contexts,
        min_support=args.min_support,
        alpha2=args.alpha2,
        minimum_entity_events=args.minimum_entity_events,
        maximum_entity_events=args.maximum_entity_events,
        base_buckets=args.base_buckets,
        retrieval_buckets=args.retrieval_buckets,
        prior_strength=args.prior_strength,
    )
    args.output_receipt.parent.mkdir(parents=True, exist_ok=True)
    args.output_receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
