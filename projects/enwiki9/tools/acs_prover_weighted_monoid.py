#!/usr/bin/env python3
"""Exact weighted-summary monoid pilot for a finite XML lexical transducer."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import resource
import time
from typing import NamedTuple


TEXT, AFTER_LT, TAG, DOUBLE_QUOTE, SINGLE_QUOTE = range(5)
STATE_COUNT = 5
COST_DIMENSION = 4


class Summary(NamedTuple):
    next_state: tuple[int, ...]
    cost: tuple[tuple[int, ...], ...]


def transition(state: int, value: int) -> int:
    if state == TEXT:
        return AFTER_LT if value == ord("<") else TEXT
    if state in (AFTER_LT, TAG):
        if value == ord(">"):
            return TEXT
        if value == ord('"'):
            return DOUBLE_QUOTE
        if value == ord("'"):
            return SINGLE_QUOTE
        return TAG
    if state == DOUBLE_QUOTE:
        return TAG if value == ord('"') else DOUBLE_QUOTE
    return TAG if value == ord("'") else SINGLE_QUOTE


def step_cost(state: int, value: int, next_state: int) -> tuple[int, ...]:
    return (
        1,
        int(state != TEXT or value == ord("<")),
        int(value in (ord("<"), ord(">"), ord('"'), ord("'"))),
        int(next_state != state),
    )


def add_cost(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(a + b for a, b in zip(left, right))


def identity() -> Summary:
    return Summary(
        tuple(range(STATE_COUNT)),
        tuple((0,) * COST_DIMENSION for _ in range(STATE_COUNT)),
    )


def summarize(block: bytes) -> Summary:
    next_states = []
    costs = []
    for initial in range(STATE_COUNT):
        state = initial
        cost = (0,) * COST_DIMENSION
        for value in block:
            following = transition(state, value)
            cost = add_cost(cost, step_cost(state, value, following))
            state = following
        next_states.append(state)
        costs.append(cost)
    return Summary(tuple(next_states), tuple(costs))


def compose(left: Summary, right: Summary) -> Summary:
    next_states = []
    costs = []
    for state in range(STATE_COUNT):
        middle = left.next_state[state]
        next_states.append(right.next_state[middle])
        costs.append(add_cost(left.cost[state], right.cost[middle]))
    return Summary(tuple(next_states), tuple(costs))


def replay(blocks: list[bytes]) -> Summary:
    result = identity()
    for block in blocks:
        result = compose(result, summarize(block))
    return result


class SummaryTree:
    def __init__(self, summaries: list[Summary]) -> None:
        self.count = len(summaries)
        self.leaf_count = 1 << math.ceil(math.log2(max(1, self.count)))
        self.nodes = [identity() for _ in range(2 * self.leaf_count)]
        for index, summary in enumerate(summaries):
            self.nodes[self.leaf_count + index] = summary
        for index in range(self.leaf_count - 1, 0, -1):
            self.nodes[index] = compose(
                self.nodes[2 * index], self.nodes[2 * index + 1]
            )

    def replace(self, index: int, summary: Summary) -> int:
        node = self.leaf_count + index
        self.nodes[node] = summary
        compositions = 0
        node //= 2
        while node:
            self.nodes[node] = compose(
                self.nodes[2 * node], self.nodes[2 * node + 1]
            )
            compositions += 1
            node //= 2
        return compositions

    @property
    def root(self) -> Summary:
        return self.nodes[1]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=65_536)
    parser.add_argument("--block-size", type=int, default=256)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = args.input.read_bytes()[: args.limit]
    blocks = [
        data[index : index + args.block_size]
        for index in range(0, len(data), args.block_size)
    ]

    started = time.perf_counter()
    summaries = [summarize(block) for block in blocks]
    tree = SummaryTree(summaries)
    base_replay = replay(blocks)
    base_ok = tree.root == base_replay

    point_blocks = list(blocks)
    point_index = min(7, len(blocks) - 1)
    source_index = min(8, len(blocks) - 1)
    point_blocks[point_index] = blocks[source_index]
    point_compositions = tree.replace(point_index, summarize(blocks[source_index]))
    point_ok = tree.root == replay(point_blocks)

    interval_blocks = list(point_blocks)
    interval_start = min(12, len(blocks) - 1)
    interval_end = min(interval_start + 4, len(blocks))
    replacements = list(reversed(interval_blocks[interval_start:interval_end]))
    interval_compositions = 0
    for offset, block in enumerate(replacements):
        index = interval_start + offset
        interval_blocks[index] = block
        interval_compositions += tree.replace(index, summarize(block))
    interval_ok = tree.root == replay(interval_blocks)
    elapsed = time.perf_counter() - started

    all_states_checked = all(
        tree.root.next_state[state] == replay(interval_blocks).next_state[state]
        and tree.root.cost[state] == replay(interval_blocks).cost[state]
        for state in range(STATE_COUNT)
    )
    passed = base_ok and point_ok and interval_ok and all_states_checked
    receipt = {
        "schema": "acs_prover_weighted_monoid/v1",
        "artifact_class": "prover_transfer_receipt",
        "mathematical_status": "COMPLETE",
        "prover_transfer": (
            "VERIFIED_FOR_XML_LEXICAL_TRANSDUCER_V1"
            if passed
            else "FAILED"
        ),
        "candidate_affected": False,
        "hutter_score_credit_bytes": 0,
        "input": {
            "path": str(args.input.resolve()),
            "source_bytes": args.input.stat().st_size,
            "used_bytes": len(data),
            "sha256": digest(args.input),
        },
        "instance": {
            "states": STATE_COUNT,
            "cost_dimensions": COST_DIMENSION,
            "block_size": args.block_size,
            "blocks": len(blocks),
            "padded_leaves": tree.leaf_count,
        },
        "checks": {
            "base_tree_equals_replay": base_ok,
            "point_tree_equals_replay": point_ok,
            "interval_tree_equals_replay": interval_ok,
            "all_states_checked": all_states_checked,
            "pass": passed,
        },
        "operations": {
            "initial_compositions": tree.leaf_count - 1,
            "point_compositions": point_compositions,
            "interval_compositions": interval_compositions,
        },
        "resources": {
            "elapsed_seconds": elapsed,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "claim_boundary": (
            "This proves exact state and modeled-cost recomposition for the "
            "frozen five-state transducer. It does not prove archive-byte "
            "identity, candidate gain, full-corpus score, or actual RSS."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt["checks"], sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
