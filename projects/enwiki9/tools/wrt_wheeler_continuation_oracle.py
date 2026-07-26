#!/usr/bin/env python3
"""Truth-aware exact WRT continuation ceiling for the Wheeler research lane.

The oracle indexes exact suffixes of completed WRT emission groups under causal
Wiki roles.  At each target event it evaluates continuation distributions for
several exact suffix depths, then uses the known target only to select the best
depth and to keep positive event gain.  This is a zero-credit feasibility bound,
not a legal predictor or a Wheeler/wavelet index implementation.
"""

from __future__ import annotations

import argparse
from collections import Counter, deque
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from causal_state_screen import WikiState
from fx2_shadow_residual_coder import TOTAL, clamp_p1
from wrt_entity_trie_fx2_shadow import P1Trace
from wrt_exact import ParsedStore, parse_store


@dataclass(frozen=True)
class ScopeSpec:
    name: str
    store: Path
    dictionary: Path
    raw: Path
    base_p1: Path


@dataclass(frozen=True)
class EmissionGroup:
    start: int
    end: int
    encoded: bytes
    decoded: bytes


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
    }


def emission_groups(parsed: ParsedStore) -> tuple[EmissionGroup, ...]:
    groups: list[EmissionGroup] = []
    pending = []
    for event in parsed.events:
        pending.append(event)
        if event.decoded:
            groups.append(
                EmissionGroup(
                    start=pending[0].start,
                    end=event.end,
                    encoded=b"".join(item.encoded for item in pending),
                    decoded=b"".join(item.decoded for item in pending),
                )
            )
            pending.clear()
    if pending:
        if not groups:
            groups.append(
                EmissionGroup(
                    pending[0].start,
                    pending[-1].end,
                    b"".join(item.encoded for item in pending),
                    b"",
                )
            )
        else:
            previous = groups[-1]
            groups[-1] = EmissionGroup(
                previous.start,
                pending[-1].end,
                previous.encoded + b"".join(item.encoded for item in pending),
                previous.decoded,
            )
    expected = 6
    for group in groups:
        if group.start != expected or group.end <= group.start:
            raise ValueError("emission groups do not exactly cover the WRT event stream")
        expected = group.end
    if expected != len(parsed.stream):
        raise ValueError("emission groups leave uncovered WRT bytes")
    return tuple(groups)


def role(wiki: WikiState) -> tuple[int, int, int, int]:
    features = wiki.features()
    return (
        int(features.get("field", 0)),
        int(features.get("mode", 0)),
        int(features.get("slot", 0)),
        int(features.get("column_bucket", 0)),
    )


@dataclass
class ExactContinuationTable:
    max_keys: int
    codes_per_key: int
    counts: dict[tuple[Any, ...], Counter[bytes]] = field(default_factory=dict)
    order: deque[tuple[Any, ...]] = field(default_factory=deque)
    evicted_keys: int = 0
    rejected_codes: int = 0

    def get(self, key: tuple[Any, ...]) -> Counter[bytes] | None:
        return self.counts.get(key)

    def update(self, key: tuple[Any, ...], code: bytes) -> None:
        counter = self.counts.get(key)
        if counter is None:
            if len(self.counts) >= self.max_keys:
                old = self.order.popleft()
                del self.counts[old]
                self.evicted_keys += 1
            counter = Counter()
            self.counts[key] = counter
            self.order.append(key)
        if code not in counter and len(counter) >= self.codes_per_key:
            self.rejected_codes += 1
            return
        counter[code] += 1

    def estimated_state_bytes(self) -> int:
        return sum(
            48 + sum(12 + len(code) for code in counter)
            for counter in self.counts.values()
        )


def bit_loss(bit: int, p1: int) -> float:
    numerator = p1 if bit else TOTAL - p1
    return -math.log2(max(1, numerator) / TOTAL)


def event_base_loss(group: EmissionGroup, trace: P1Trace) -> float:
    loss = 0.0
    relative = 0
    for value in group.encoded:
        for bit_position in range(8):
            bit = (value >> (7 - bit_position)) & 1
            row = group.start * 8 + relative
            loss += bit_loss(bit, trace.p1(row))
            relative += 1
    return loss


def distribution_loss(
    group: EmissionGroup,
    counter: Counter[bytes],
    trace: P1Trace,
    min_support: int,
    alpha2: int,
) -> tuple[float, int]:
    loss = 0.0
    prefix = 0
    prefix_length = 0
    active_bits = 0
    for value in group.encoded:
        for bit_position in range(8):
            bit = (value >> (7 - bit_position)) & 1
            row = group.start * 8 + prefix_length
            zeros = 0
            ones = 0
            for code, count in counter.items():
                code_bits = len(code) * 8
                if code_bits <= prefix_length:
                    continue
                code_value = int.from_bytes(code, "big")
                if prefix_length and code_value >> (code_bits - prefix_length) != prefix:
                    continue
                next_bit = (code_value >> (code_bits - prefix_length - 1)) & 1
                if next_bit:
                    ones += count
                else:
                    zeros += count
            support = zeros + ones
            if support >= min_support:
                p1 = clamp_p1(
                    ((2 * ones + alpha2) * TOTAL)
                    // (2 * support + 2 * alpha2)
                )
                active_bits += 1
            else:
                p1 = trace.p1(row)
            loss += bit_loss(bit, p1)
            prefix = (prefix << 1) | bit
            prefix_length += 1
    return loss, active_bits


def partition(index: int, count: int) -> str:
    fraction = index / max(1, count)
    if fraction < 0.6:
        return "train"
    if fraction < 0.8:
        return "development"
    return "holdout"


def run_scope(
    spec: ScopeSpec,
    depths: tuple[int, ...],
    max_keys: int,
    codes_per_key: int,
    min_support: int,
    alpha2: int,
) -> dict[str, Any]:
    parsed = parse_store(spec.store, spec.dictionary)
    raw = spec.raw.read_bytes()
    if raw != parsed.decoded:
        raise ValueError(f"{spec.name}: raw input does not match exact WRT decode")
    groups = emission_groups(parsed)
    trace = P1Trace(spec.base_p1)
    expected_rows = len(parsed.stream) * 8
    if trace.rows != expected_rows:
        trace.close()
        raise ValueError(
            f"{spec.name}: base P1 rows {trace.rows} != WRT rows {expected_rows}"
        )

    wiki = WikiState()
    history: deque[bytes] = deque(maxlen=max(depths))
    table = ExactContinuationTable(max_keys=max_keys, codes_per_key=codes_per_key)
    stats: dict[str, Counter[str]] = {
        name: Counter() for name in ("train", "development", "holdout")
    }
    by_role: dict[str, Counter[str]] = {}
    selected_depths: Counter[int] = Counter()

    for index, group in enumerate(groups):
        split = partition(index, len(groups))
        split_stats = stats[split]
        current_role = role(wiki)
        role_name = ":".join(map(str, current_role[:3]))
        role_stats = by_role.setdefault(role_name, Counter())
        base_loss = event_base_loss(group, trace)
        best_loss = base_loss
        best_depth = 0
        best_active_bits = 0
        keys: list[tuple[int, tuple[Any, ...]]] = []
        history_tuple = tuple(history)
        for depth in depths:
            if len(history_tuple) < depth:
                continue
            key = ("exact_wrt_suffix", current_role, depth, history_tuple[-depth:])
            keys.append((depth, key))
            counter = table.get(key)
            if counter is None:
                continue
            candidate_loss, active_bits = distribution_loss(
                group, counter, trace, min_support, alpha2
            )
            if candidate_loss < best_loss:
                best_loss = candidate_loss
                best_depth = depth
                best_active_bits = active_bits
        gain_bits = max(0.0, base_loss - best_loss)
        decoded_bytes = len(group.decoded)
        split_stats["events"] += 1
        split_stats["raw_bytes"] += decoded_bytes
        split_stats["wrt_bytes"] += len(group.encoded)
        split_stats["base_millibits"] += round(base_loss * 1000)
        split_stats["oracle_gain_millibits"] += round(gain_bits * 1000)
        split_stats["selected_events"] += int(best_depth > 0)
        split_stats["active_bits"] += best_active_bits
        role_stats["events"] += 1
        role_stats["raw_bytes"] += decoded_bytes
        role_stats["oracle_gain_millibits"] += round(gain_bits * 1000)
        if best_depth:
            selected_depths[best_depth] += 1
        for _depth, key in keys:
            table.update(key, group.encoded)
        history.append(group.encoded)
        for value in group.decoded:
            wiki.update(value)

    trace.close()

    def summarize(counter: Counter[str]) -> dict[str, Any]:
        raw_bytes = int(counter["raw_bytes"])
        gain_bits = counter["oracle_gain_millibits"] / 1000
        return {
            "events": int(counter["events"]),
            "raw_bytes": raw_bytes,
            "wrt_bytes": int(counter["wrt_bytes"]),
            "base_ideal_bits": counter["base_millibits"] / 1000,
            "truth_aware_positive_gain_bits": gain_bits,
            "truth_aware_positive_gain_bytes": gain_bits / 8,
            "truth_aware_positive_gain_bytes_per_m": (
                gain_bits / 8 * 1_000_000 / raw_bytes if raw_bytes else 0.0
            ),
            "selected_events": int(counter["selected_events"]),
            "active_bits": int(counter["active_bits"]),
        }

    role_rows = []
    for name, counter in by_role.items():
        raw_bytes = int(counter["raw_bytes"])
        gain_bytes = counter["oracle_gain_millibits"] / 8000
        role_rows.append(
            {
                "role": name,
                "events": int(counter["events"]),
                "raw_bytes": raw_bytes,
                "gain_bytes": gain_bytes,
                "gain_bytes_per_m": (
                    gain_bytes * 1_000_000 / raw_bytes if raw_bytes else 0.0
                ),
            }
        )
    role_rows.sort(key=lambda row: float(row["gain_bytes"]), reverse=True)
    return {
        "name": spec.name,
        "inputs": {
            "store": artifact(spec.store),
            "dictionary": artifact(spec.dictionary),
            "raw": artifact(spec.raw),
            "base_p1": artifact(spec.base_p1),
        },
        "scope": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(parsed.stream),
            "emission_groups": len(groups),
            "base_rows": expected_rows,
        },
        "partitions": {name: summarize(stats[name]) for name in stats},
        "selected_suffix_depths": {
            str(depth): selected_depths[depth] for depth in sorted(selected_depths)
        },
        "top_roles": role_rows[:24],
        "table": {
            "keys": len(table.counts),
            "evicted_keys": table.evicted_keys,
            "rejected_codes": table.rejected_codes,
            "estimated_state_bytes": table.estimated_state_bytes(),
        },
    }


def parse_scope(value: str) -> ScopeSpec:
    parts = value.split(":", 4)
    if len(parts) != 5:
        raise argparse.ArgumentTypeError(
            "--scope requires NAME:STORE:DICTIONARY:RAW:BASE_P1"
        )
    return ScopeSpec(parts[0], *(Path(part) for part in parts[1:]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", action="append", type=parse_scope, required=True)
    parser.add_argument("--depth", action="append", type=int, default=[])
    parser.add_argument("--max-keys", type=int, default=250_000)
    parser.add_argument("--codes-per-key", type=int, default=64)
    parser.add_argument("--min-support", type=int, default=2)
    parser.add_argument("--alpha2", type=int, default=1)
    parser.add_argument("--feasibility-b-per-m", type=float, default=1500.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    depths = tuple(sorted(set(args.depth or [1, 2, 4, 8])))
    if not depths or depths[0] <= 0:
        raise SystemExit("suffix depths must be positive")
    scopes = [
        run_scope(
            spec,
            depths,
            args.max_keys,
            args.codes_per_key,
            args.min_support,
            args.alpha2,
        )
        for spec in args.scope
    ]
    holdout_rates = {
        row["name"]: row["partitions"]["holdout"][
            "truth_aware_positive_gain_bytes_per_m"
        ]
        for row in scopes
    }
    pass_gate = all(
        rate >= args.feasibility_b_per_m for rate in holdout_rates.values()
    )
    receipt = {
        "schema": "wrt_wheeler_truth_aware_continuation_oracle_v1",
        "evidence_level": "zero_credit_truth_aware_feasibility_ceiling",
        "promotion_authorized": False,
        "claim_boundary": (
            "The true target selects the best exact suffix depth per completed "
            "emission group and negative events are suppressed. This is not a "
            "causal predictor, archive, Wheeler index, or score claim."
        ),
        "model": {
            "exact_suffix_depths": list(depths),
            "structural_role": ["field", "mode", "slot", "column_bucket"],
            "zero_output_controls_grouped_with_next_output_event": True,
            "updates_after_completed_emission_group": True,
            "max_keys": args.max_keys,
            "codes_per_key": args.codes_per_key,
            "minimum_support": args.min_support,
            "alpha2": args.alpha2,
        },
        "gate": {
            "required_holdout_bytes_per_m_each_scope": args.feasibility_b_per_m,
            "holdout_bytes_per_m": holdout_rates,
            "pass": pass_gate,
            "decision": (
                "authorize_frozen_causal_shadow"
                if pass_gate
                else "retire_wheeler_before_causal_shadow_and_index"
            ),
        },
        "scopes": scopes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt["gate"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
