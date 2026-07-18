#!/usr/bin/env python3
"""Test a causal contextual mixer over WRT entity-trie residuals.

The entity tries contain only completed title and link-target WRT sequences.
For each eligible bit, signed residual experts move the endpoint428
probability toward or away from the trie prediction.  A deterministic online
mixer chooses an expert from prior loss in decoder-visible context buckets,
then updates every expert after the true bit is decoded.

All configurations stop at the sealed holdout boundary.  Development gain
selects one configuration, which is replayed from the corpus start with actual
CMIX range coding.  The other configurations never read holdout truth.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import struct
from typing import Any, Iterable

from fx2_attribution_external_base_screen import CmixRangeEncoder
from fx2_shadow_residual_coder import TOTAL, clamp_p1
from wrt_entity_trie_fx2_shadow import (
    EntityObserver,
    EntityTrie,
    P1Trace,
    ParsedStore,
    WrtEvent,
    artifact,
    event_bit,
    event_prefix,
    fast_qbits,
    make_tries,
    observe_and_insert,
    parse_store,
    sha256_bytes,
)


PPM = 1_000_000
QBITS_PER_BYTE = 2048
P1_MAGIC = b"CMX21P1\0"
FEATURE_SCHEMES = ("global", "support", "disagreement")
DEFAULT_SIGNED_BLENDS = (
    -100_000,
    -50_000,
    -25_000,
    -10_000,
    -5_000,
    0,
    5_000,
    10_000,
    25_000,
    50_000,
    100_000,
)
ENTITY_TRIE_TOOL = Path(__file__).with_name("wrt_entity_trie_fx2_shadow.py")


@dataclass(frozen=True)
class EndpointStats:
    p1: int
    support: int
    branches: int
    zeros: int
    ones: int


def endpoint_stats(
    trie: EntityTrie,
    node: int | None,
    bit_index: int,
    prefix: int,
    min_support: int,
    alpha2: int,
) -> EndpointStats | None:
    """Return a trie probability and causal support diagnostics."""

    if node is None:
        return None
    zeros = 0
    ones = 0
    support = 0
    branches = 0
    for code, edge in trie.nodes[node].items():
        code_bits = 8 * len(code)
        if bit_index >= code_bits:
            continue
        if bit_index:
            code_prefix = int.from_bytes(code, "big") >> (code_bits - bit_index)
            if code_prefix != prefix:
                continue
        branches += 1
        if event_bit(code, bit_index):
            ones += edge.count
        else:
            zeros += edge.count
        support += edge.count
    if support < min_support:
        return None
    probability = ((2 * ones + alpha2) * TOTAL) // (
        2 * support + 2 * alpha2
    )
    return EndpointStats(
        p1=clamp_p1(probability),
        support=support,
        branches=branches,
        zeros=zeros,
        ones=ones,
    )


def signed_blend_probability(base_p1: int, endpoint_p1: int, weight_ppm: int) -> int:
    """Interpolate or extrapolate from base toward an endpoint."""

    if not -PPM <= weight_ppm <= PPM:
        raise ValueError("signed blend weight must be within -1000000..1000000")
    delta = endpoint_p1 - base_p1
    product = delta * weight_ppm
    correction = (
        (product + PPM // 2) // PPM
        if product >= 0
        else -((-product + PPM // 2) // PPM)
    )
    return clamp_p1(base_p1 + correction)


def decay_toward_zero(value: int, shift: int) -> int:
    if shift <= 0:
        return value
    amount = abs(value) >> shift
    return value - amount if value >= 0 else value + amount


def log_bucket(value: int, cap: int) -> int:
    if value <= 0:
        return 0
    return min(cap, value.bit_length() - 1)


def confidence_bucket(p1: int) -> int:
    return min(7, log_bucket(abs(p1 - TOTAL // 2), 15) // 2)


def prefix_signature(relative_bit: int, prefix: int) -> int:
    """Encode at most the first four already-decoded bits of this WRT event."""

    known = min(relative_bit, 4)
    if known == 0:
        return 0
    first = prefix >> max(0, relative_bit - known)
    return (1 << known) | first


def causal_feature_keys(
    scheme: str,
    *,
    path_depth: int,
    relative_bit: int,
    prefix: int,
    base_p1: int,
    endpoint: EndpointStats,
) -> tuple[tuple[int, ...], ...]:
    """Build hierarchical keys without the current truth bit or future bytes."""

    if scheme not in FEATURE_SCHEMES:
        raise ValueError(f"unknown feature scheme: {scheme}")
    keys: list[tuple[int, ...]] = [(0,)]
    if scheme == "global":
        return tuple(keys)

    byte_phase = min(relative_bit // 8, 2)
    bit_position = relative_bit & 7
    depth = min(path_depth, 6)
    support = log_bucket(endpoint.support, 12)
    branches = log_bucket(endpoint.branches, 6)
    support_key = (1, depth, byte_phase, bit_position, support, branches)
    keys.append(support_key)
    if scheme == "support":
        return tuple(keys)

    delta = endpoint.p1 - base_p1
    base_side = int(base_p1 >= TOTAL // 2)
    endpoint_side = int(endpoint.p1 >= TOTAL // 2)
    detail_key = (
        2,
        depth,
        byte_phase,
        bit_position,
        support,
        branches,
        prefix_signature(relative_bit, prefix),
        base_side,
        endpoint_side,
        confidence_bucket(base_p1),
        confidence_bucket(endpoint.p1),
        int(delta > 0) - int(delta < 0),
        min(7, log_bucket(abs(delta), 15) // 2),
    )
    keys.append(detail_key)
    return tuple(keys)


@dataclass
class MixerBucket:
    observations: int
    gains_qbits: list[int]


@dataclass(frozen=True)
class MixerDecision:
    expert_index: int
    level: int
    gain_qbits: int


@dataclass
class ContextMixer:
    blends_ppm: tuple[int, ...]
    minimum_observations: int
    margin_qbits: int
    decay_shift: int
    states: dict[tuple[int, ...], MixerBucket] = field(default_factory=dict)
    choices: Counter[int] = field(default_factory=Counter)
    levels: Counter[int] = field(default_factory=Counter)

    def __post_init__(self) -> None:
        if 0 not in self.blends_ppm:
            raise ValueError("blend expert universe must contain zero")
        if self.minimum_observations < 0 or self.margin_qbits < 0:
            raise ValueError("observation and margin floors must be nonnegative")
        self.zero_index = self.blends_ppm.index(0)

    def choose(self, keys: tuple[tuple[int, ...], ...]) -> tuple[int, int]:
        """Choose from prior state only, backing off to the base expert."""

        for level in range(len(keys) - 1, -1, -1):
            state = self.states.get(keys[level])
            if state is None or state.observations < self.minimum_observations:
                continue
            best = self.zero_index
            for index, score in enumerate(state.gains_qbits):
                if score > state.gains_qbits[best]:
                    best = index
                elif score == state.gains_qbits[best] and (
                    abs(self.blends_ppm[index]), self.blends_ppm[index]
                ) < (
                    abs(self.blends_ppm[best]), self.blends_ppm[best]
                ):
                    best = index
            if (
                best != self.zero_index
                and state.gains_qbits[best] > self.margin_qbits
            ):
                return best, level
        return self.zero_index, -1

    def update(
        self,
        keys: tuple[tuple[int, ...], ...],
        expert_gains_qbits: tuple[int, ...],
    ) -> None:
        if len(expert_gains_qbits) != len(self.blends_ppm):
            raise ValueError("expert gain vector length mismatch")
        for key in keys:
            state = self.states.get(key)
            if state is None:
                state = MixerBucket(
                    observations=0,
                    gains_qbits=[0] * len(self.blends_ppm),
                )
                self.states[key] = state
            if self.decay_shift:
                for index, value in enumerate(state.gains_qbits):
                    state.gains_qbits[index] = decay_toward_zero(
                        value, self.decay_shift
                    )
            for index, gain in enumerate(expert_gains_qbits):
                state.gains_qbits[index] += gain
            state.observations += 1

    def decide_then_learn(
        self,
        keys: tuple[tuple[int, ...], ...],
        expert_gains_qbits: tuple[int, ...],
    ) -> MixerDecision:
        expert, level = self.choose(keys)
        gain = expert_gains_qbits[expert]
        self.choices[self.blends_ppm[expert]] += 1
        self.levels[level] += 1
        self.update(keys, expert_gains_qbits)
        return MixerDecision(expert, level, gain)

    @property
    def state_bytes_estimate(self) -> int:
        return sum(
            32 + 4 * len(key) + 8 * len(state.gains_qbits)
            for key, state in self.states.items()
        )

    def receipt(self) -> dict[str, Any]:
        observations = [state.observations for state in self.states.values()]
        return {
            "context_states": len(self.states),
            "maximum_context_observations": max(observations, default=0),
            "state_bytes_estimate": self.state_bytes_estimate,
            "choice_rows_by_blend_ppm": {
                str(key): value for key, value in sorted(self.choices.items())
            },
            "choice_rows_by_level": {
                str(key): value for key, value in sorted(self.levels.items())
            },
        }


@dataclass(frozen=True)
class MixerSpec:
    trie_name: str
    scheme: str
    decay_shift: int

    @property
    def name(self) -> str:
        return f"{self.trie_name}_{self.scheme}_d{self.decay_shift}"


@dataclass
class SplitTotals:
    rows: int = 0
    active_rows: int = 0
    gain_qbits: int = 0

    def receipt(self, proportional_raw_bytes: float) -> dict[str, float | int]:
        gain_bytes = self.gain_qbits / QBITS_PER_BYTE
        return {
            "eligible_rows": self.rows,
            "active_rows": self.active_rows,
            "gain_qbits": self.gain_qbits,
            "gain_bytes": gain_bytes,
            "gain_bytes_per_proportional_1m_raw": (
                gain_bytes * 1_000_000 / proportional_raw_bytes
                if proportional_raw_bytes > 0
                else 0.0
            ),
        }


@dataclass
class CandidateRun:
    spec: MixerSpec
    mixer: ContextMixer
    train: SplitTotals = field(default_factory=SplitTotals)
    dev: SplitTotals = field(default_factory=SplitTotals)

    def add(
        self,
        split: str,
        keys: tuple[tuple[int, ...], ...],
        expert_gains_qbits: tuple[int, ...],
    ) -> None:
        decision = self.mixer.decide_then_learn(keys, expert_gains_qbits)
        totals = self.train if split == "train" else self.dev
        totals.rows += 1
        totals.active_rows += int(
            self.mixer.blends_ppm[decision.expert_index] != 0
        )
        totals.gain_qbits += decision.gain_qbits


def parse_ints(values: str) -> tuple[int, ...]:
    return tuple(int(value) for value in values.split(",") if value)


def make_specs(args: argparse.Namespace) -> list[MixerSpec]:
    tries = tuple(value for value in args.tries.split(",") if value)
    schemes = tuple(value for value in args.schemes.split(",") if value)
    decays = parse_ints(args.decay_shifts)
    invalid_tries = sorted(set(tries) - {"title", "link", "combined"})
    invalid_schemes = sorted(set(schemes) - set(FEATURE_SCHEMES))
    if invalid_tries:
        raise ValueError(f"unknown tries: {','.join(invalid_tries)}")
    if invalid_schemes:
        raise ValueError(f"unknown schemes: {','.join(invalid_schemes)}")
    if any(decay < 0 for decay in decays):
        raise ValueError("decay shifts must be nonnegative")
    specs = [
        MixerSpec(trie_name=trie, scheme=scheme, decay_shift=decay)
        for trie in tries
        for scheme in schemes
        for decay in decays
    ]
    if not specs:
        raise ValueError("context-mixer candidate universe is empty")
    return specs


def make_runs(
    specs: Iterable[MixerSpec],
    blends_ppm: tuple[int, ...],
    minimum_observations: int,
    margin_qbits: int,
) -> dict[str, CandidateRun]:
    return {
        spec.name: CandidateRun(
            spec=spec,
            mixer=ContextMixer(
                blends_ppm=blends_ppm,
                minimum_observations=minimum_observations,
                margin_qbits=margin_qbits,
                decay_shift=spec.decay_shift,
            ),
        )
        for spec in specs
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


def expert_rows(
    bit: int,
    base_p1: int,
    endpoint_p1: int,
    blends_ppm: tuple[int, ...],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    probabilities = tuple(
        signed_blend_probability(base_p1, endpoint_p1, blend)
        for blend in blends_ppm
    )
    base_loss = fast_qbits(bit, base_p1)
    gains = tuple(base_loss - fast_qbits(bit, p1) for p1 in probabilities)
    return probabilities, gains


def discovery_scan(
    parsed: ParsedStore,
    trace: P1Trace,
    specs: list[MixerSpec],
    *,
    blends_ppm: tuple[int, ...],
    dev_start_row: int,
    holdout_start_row: int,
    cap_nodes: int,
    min_support: int,
    alpha2: int,
    minimum_entity_events: int,
    maximum_entity_events: int,
    minimum_observations: int,
    margin_qbits: int,
) -> tuple[dict[str, CandidateRun], dict[str, EntityTrie], EntityObserver]:
    runs = make_runs(specs, blends_ppm, minimum_observations, margin_qbits)
    by_trie: dict[str, list[CandidateRun]] = {name: [] for name in make_tries(1)}
    for run in runs.values():
        by_trie[run.spec.trie_name].append(run)

    tries = make_tries(cap_nodes)
    observer = EntityObserver()
    events = parsed.events
    event_index = 0
    active_event_start: int | None = None
    nodes = {name: None for name in tries}
    path_depth = 0

    for position in range(len(parsed.stream)):
        event_index, event = event_at(events, event_index, position)
        if event is not None and event.start != active_event_start:
            active_event_start = event.start
            path = observer.link_prefix if observer.in_link else ()
            path_depth = len(path)
            nodes = {
                name: trie.follow(path) if observer.in_link else None
                for name, trie in tries.items()
            }
        complete_byte = True
        for bit_position in range(8):
            row = position * 8 + bit_position
            if row >= holdout_start_row:
                complete_byte = False
                break
            bit = (parsed.stream[position] >> (7 - bit_position)) & 1
            base_p1 = trace.p1(row)
            if event is None or not observer.in_link:
                continue
            relative_bit = (position - event.start) * 8 + bit_position
            prefix = event_prefix(event.encoded, relative_bit)
            split = "train" if row < dev_start_row else "dev"
            for trie_name, candidate_runs in by_trie.items():
                if not candidate_runs:
                    continue
                endpoint = endpoint_stats(
                    tries[trie_name],
                    nodes[trie_name],
                    relative_bit,
                    prefix,
                    min_support,
                    alpha2,
                )
                if endpoint is None:
                    continue
                _, gains = expert_rows(
                    bit, base_p1, endpoint.p1, blends_ppm
                )
                for run in candidate_runs:
                    keys = causal_feature_keys(
                        run.spec.scheme,
                        path_depth=path_depth,
                        relative_bit=relative_bit,
                        prefix=prefix,
                        base_p1=base_p1,
                        endpoint=endpoint,
                    )
                    run.add(split, keys, gains)
        if not complete_byte:
            break
        if event is not None and position == event.end - 1:
            observe_and_insert(
                observer,
                tries,
                event,
                minimum_entity_events,
                maximum_entity_events,
            )
    return runs, tries, observer


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def replay_selected(
    parsed: ParsedStore,
    trace: P1Trace,
    spec: MixerSpec,
    *,
    blends_ppm: tuple[int, ...],
    dev_start_row: int,
    holdout_start_row: int,
    cap_nodes: int,
    min_support: int,
    alpha2: int,
    minimum_entity_events: int,
    maximum_entity_events: int,
    minimum_observations: int,
    margin_qbits: int,
    holdout_blocks: int,
    baseline_payload: bytes,
    candidate_payload_path: Path | None,
    candidate_p1_path: Path | None,
) -> dict[str, Any]:
    mixer = ContextMixer(
        blends_ppm=blends_ppm,
        minimum_observations=minimum_observations,
        margin_qbits=margin_qbits,
        decay_shift=spec.decay_shift,
    )
    tries = make_tries(cap_nodes)
    observer = EntityObserver()
    full_base = CmixRangeEncoder()
    full_candidate = CmixRangeEncoder()
    heldout_base = CmixRangeEncoder()
    heldout_candidate = CmixRangeEncoder()
    block_base = [CmixRangeEncoder() for _ in range(holdout_blocks)]
    block_candidate = [CmixRangeEncoder() for _ in range(holdout_blocks)]
    rows = trace.rows
    heldout_rows = rows - holdout_start_row
    split_totals = {
        "train": SplitTotals(),
        "dev": SplitTotals(),
        "holdout": SplitTotals(),
    }
    events = parsed.events
    event_index = 0
    active_event_start: int | None = None
    node: int | None = None
    path_depth = 0
    event_heldout_expert_gains = [0] * len(blends_ppm)
    event_has_heldout_endpoint = False
    heldout_positive_event_oracle_qbits = 0
    heldout_positive_bit_oracle_qbits = 0
    p1_output = bytearray(P1_MAGIC + struct.pack("<Q", rows)) if candidate_p1_path else None

    for position in range(len(parsed.stream)):
        event_index, event = event_at(events, event_index, position)
        if event is not None and event.start != active_event_start:
            active_event_start = event.start
            path = observer.link_prefix if observer.in_link else ()
            path_depth = len(path)
            node = (
                tries[spec.trie_name].follow(path) if observer.in_link else None
            )
            event_heldout_expert_gains = [0] * len(blends_ppm)
            event_has_heldout_endpoint = False

        for bit_position in range(8):
            row = position * 8 + bit_position
            bit = (parsed.stream[position] >> (7 - bit_position)) & 1
            base_p1 = trace.p1(row)
            candidate_p1 = base_p1
            selected_gain = 0
            active = False
            eligible = False
            if event is not None and observer.in_link:
                relative_bit = (position - event.start) * 8 + bit_position
                prefix = event_prefix(event.encoded, relative_bit)
                endpoint = endpoint_stats(
                    tries[spec.trie_name],
                    node,
                    relative_bit,
                    prefix,
                    min_support,
                    alpha2,
                )
                if endpoint is not None:
                    eligible = True
                    probabilities, gains = expert_rows(
                        bit, base_p1, endpoint.p1, blends_ppm
                    )
                    keys = causal_feature_keys(
                        spec.scheme,
                        path_depth=path_depth,
                        relative_bit=relative_bit,
                        prefix=prefix,
                        base_p1=base_p1,
                        endpoint=endpoint,
                    )
                    expert, level = mixer.choose(keys)
                    candidate_p1 = probabilities[expert]
                    selected_gain = gains[expert]
                    active = blends_ppm[expert] != 0
                    mixer.choices[blends_ppm[expert]] += 1
                    mixer.levels[level] += 1
                    mixer.update(keys, gains)
                    if row >= holdout_start_row:
                        event_has_heldout_endpoint = True
                        heldout_positive_bit_oracle_qbits += max(0, max(gains))
                        for index, gain in enumerate(gains):
                            event_heldout_expert_gains[index] += gain

            if row < dev_start_row:
                split = "train"
            elif row < holdout_start_row:
                split = "dev"
            else:
                split = "holdout"
            if eligible:
                split_totals[split].rows += 1
            split_totals[split].active_rows += int(active)
            split_totals[split].gain_qbits += selected_gain

            full_base.encode(bit, base_p1)
            full_candidate.encode(bit, candidate_p1)
            if row >= holdout_start_row:
                heldout_base.encode(bit, base_p1)
                heldout_candidate.encode(bit, candidate_p1)
                block = min(
                    holdout_blocks - 1,
                    (row - holdout_start_row) * holdout_blocks // heldout_rows,
                )
                block_base[block].encode(bit, base_p1)
                block_candidate[block].encode(bit, candidate_p1)
            if p1_output is not None:
                p1_output.extend(struct.pack("<H", candidate_p1))

        if event is not None and position == event.end - 1:
            if event_has_heldout_endpoint:
                heldout_positive_event_oracle_qbits += max(
                    0, max(event_heldout_expert_gains)
                )
            observe_and_insert(
                observer,
                tries,
                event,
                minimum_entity_events,
                maximum_entity_events,
            )

    full_base_payload = full_base.finish()
    full_candidate_payload = full_candidate.finish()
    heldout_base_payload = heldout_base.finish()
    heldout_candidate_payload = heldout_candidate.finish()
    if full_base_payload != baseline_payload:
        raise RuntimeError("base P1 replay is not byte-identical to baseline payload")
    if candidate_payload_path is not None:
        atomic_write(candidate_payload_path, full_candidate_payload)
    if candidate_p1_path is not None:
        assert p1_output is not None
        atomic_write(candidate_p1_path, bytes(p1_output))

    block_rows: list[dict[str, int]] = []
    for block, (base_coder, candidate_coder) in enumerate(
        zip(block_base, block_candidate, strict=True)
    ):
        start = holdout_start_row + heldout_rows * block // holdout_blocks
        end = holdout_start_row + heldout_rows * (block + 1) // holdout_blocks
        base_bytes = len(base_coder.finish())
        candidate_bytes = len(candidate_coder.finish())
        block_rows.append(
            {
                "block": block,
                "start_row": start,
                "end_row": end,
                "base_payload_bytes": base_bytes,
                "candidate_payload_bytes": candidate_bytes,
                "saved_bytes": base_bytes - candidate_bytes,
            }
        )
    regressions = [-row["saved_bytes"] for row in block_rows if row["saved_bytes"] < 0]
    return {
        "selected_candidate": spec.name,
        "full": {
            "rows": rows,
            "base_payload_bytes": len(full_base_payload),
            "candidate_payload_bytes": len(full_candidate_payload),
            "saved_bytes": len(full_base_payload) - len(full_candidate_payload),
            "base_payload_sha256": sha256_bytes(full_base_payload),
            "candidate_payload_sha256": sha256_bytes(full_candidate_payload),
        },
        "holdout": {
            "rows": heldout_rows,
            "base_payload_bytes": len(heldout_base_payload),
            "candidate_payload_bytes": len(heldout_candidate_payload),
            "saved_bytes": len(heldout_base_payload) - len(heldout_candidate_payload),
            "base_payload_sha256": sha256_bytes(heldout_base_payload),
            "candidate_payload_sha256": sha256_bytes(heldout_candidate_payload),
        },
        "split_qbits": {
            name: totals.gain_qbits for name, totals in split_totals.items()
        },
        "split_totals": {
            name: {
                "eligible_rows": totals.rows,
                "active_rows": totals.active_rows,
                "gain_qbits": totals.gain_qbits,
                "gain_bytes": totals.gain_qbits / QBITS_PER_BYTE,
            }
            for name, totals in split_totals.items()
        },
        "heldout_positive_event_oracle_bytes": (
            heldout_positive_event_oracle_qbits / QBITS_PER_BYTE
        ),
        "heldout_positive_bit_oracle_bytes": (
            heldout_positive_bit_oracle_qbits / QBITS_PER_BYTE
        ),
        "holdout_block_audit": {
            "blocks": holdout_blocks,
            "regressing_blocks": len(regressions),
            "largest_regression_bytes": max(regressions, default=0),
            "total_regression_bytes": sum(regressions),
            "rows": block_rows,
        },
        "mixer": mixer.receipt(),
        "tries": {name: trie.receipt() for name, trie in tries.items()},
        "observer": observer.receipt(),
        "candidate_payload_artifact": (
            artifact(candidate_payload_path)
            if candidate_payload_path is not None
            else None
        ),
        "candidate_p1_artifact": (
            artifact(candidate_p1_path) if candidate_p1_path is not None else None
        ),
    }


def candidate_receipt(
    run: CandidateRun,
    *,
    train_raw_bytes: float,
    dev_raw_bytes: float,
) -> dict[str, Any]:
    return {
        "candidate": run.spec.name,
        "trie": run.spec.trie_name,
        "feature_scheme": run.spec.scheme,
        "decay_shift": run.spec.decay_shift,
        "train": run.train.receipt(train_raw_bytes),
        "dev": run.dev.receipt(dev_raw_bytes),
        "mixer": run.mixer.receipt(),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    parsed = parse_store(args.store, args.dictionary)
    raw = args.raw.read_bytes()[: parsed.raw_length]
    if len(raw) != parsed.raw_length:
        raise RuntimeError("raw corpus is shorter than the WRT-declared scope")
    if raw != parsed.decoded:
        raise RuntimeError("WRT store does not reconstruct the raw scope")
    baseline_payload = args.baseline_payload.read_bytes()
    blends_ppm = tuple(sorted(set(parse_ints(args.signed_blends))))
    if 0 not in blends_ppm or any(not -PPM <= value <= PPM for value in blends_ppm):
        raise ValueError("signed blends must contain zero and stay within +/-1000000")

    trace = P1Trace(args.base_p1)
    try:
        if trace.rows != len(parsed.stream) * 8:
            raise RuntimeError("base trace does not cover the exact WRT stream")
        if not 0 < args.dev_start_row < args.holdout_start_row < trace.rows:
            raise ValueError("row split boundaries must be ordered inside the trace")
        if not 1 <= args.holdout_blocks <= trace.rows - args.holdout_start_row:
            raise ValueError("invalid holdout block count")

        specs = make_specs(args)
        discovery, discovery_tries, discovery_observer = discovery_scan(
            parsed,
            trace,
            specs,
            blends_ppm=blends_ppm,
            dev_start_row=args.dev_start_row,
            holdout_start_row=args.holdout_start_row,
            cap_nodes=args.cap_nodes,
            min_support=args.min_support,
            alpha2=args.alpha2,
            minimum_entity_events=args.minimum_entity_events,
            maximum_entity_events=args.maximum_entity_events,
            minimum_observations=args.minimum_observations,
            margin_qbits=args.margin_qbits,
        )
        ranked_runs = sorted(
            discovery.values(),
            key=lambda item: (
                -item.dev.gain_qbits,
                -item.train.gain_qbits,
                item.mixer.state_bytes_estimate,
                item.spec.name,
            ),
        )
        selected_run = ranked_runs[0]
        replay = replay_selected(
            parsed,
            trace,
            selected_run.spec,
            blends_ppm=blends_ppm,
            dev_start_row=args.dev_start_row,
            holdout_start_row=args.holdout_start_row,
            cap_nodes=args.cap_nodes,
            min_support=args.min_support,
            alpha2=args.alpha2,
            minimum_entity_events=args.minimum_entity_events,
            maximum_entity_events=args.maximum_entity_events,
            minimum_observations=args.minimum_observations,
            margin_qbits=args.margin_qbits,
            holdout_blocks=args.holdout_blocks,
            baseline_payload=baseline_payload,
            candidate_payload_path=args.candidate_payload,
            candidate_p1_path=args.candidate_p1,
        )
        if replay["split_qbits"]["train"] != selected_run.train.gain_qbits:
            raise RuntimeError("selected training replay differs from discovery")
        if replay["split_qbits"]["dev"] != selected_run.dev.gain_qbits:
            raise RuntimeError("selected development replay differs from discovery")

        rows = trace.rows
        train_raw = parsed.raw_length * args.dev_start_row / rows
        dev_raw = (
            parsed.raw_length
            * (args.holdout_start_row - args.dev_start_row)
            / rows
        )
        holdout_raw = parsed.raw_length * (rows - args.holdout_start_row) / rows
        full_rate = replay["full"]["saved_bytes"] * 1_000_000 / parsed.raw_length
        holdout_rate = (
            replay["holdout"]["saved_bytes"] * 1_000_000 / holdout_raw
        )
        qbit_holdout_rate = (
            replay["split_qbits"]["holdout"]
            / QBITS_PER_BYTE
            * 1_000_000
            / holdout_raw
        )
        required_zero_code = args.forecast_gap_bytes / 1000.0
        provisional_code_rate = args.provisional_integration_code_bytes / 1000.0
        required_with_provisional_code = required_zero_code + provisional_code_rate
        payable_code_bytes = max(
            0.0, (min(full_rate, holdout_rate) - required_zero_code) * 1000.0
        )
        candidates = [
            candidate_receipt(
                candidate,
                train_raw_bytes=train_raw,
                dev_raw_bytes=dev_raw,
            )
            for candidate in ranked_runs
        ]
        economics_pass = (
            full_rate >= required_with_provisional_code
            and holdout_rate >= required_with_provisional_code
        )
        verdict = (
            "positive_shadow_requires_native_integration_and_disjoint_scale"
            if economics_pass
            else "positive_but_insufficient_counted_margin"
            if replay["holdout"]["saved_bytes"] > 0
            else "negative_or_flat_retire_contextual_entity_mixer_shape"
        )
        max_state = (
            sum(row["state_bytes_estimate"] for row in replay["tries"].values())
            + replay["mixer"]["state_bytes_estimate"]
        )
        return {
            "schema": "wrt_entity_context_mixer_shadow_v1",
            "hypothesis": (
                "A signed hierarchical online mixer can retain entity-trie "
                "residual information that fixed positive blends and node-local "
                "event regret discard over endpoint428."
            ),
            "evidence_level": (
                "development_selected_exact_heldout_cmix_range_replay"
            ),
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
                "baseline_payload": artifact(args.baseline_payload),
            },
            "scope": {
                "raw_bytes": parsed.raw_length,
                "wrt_stream_bytes": len(parsed.stream),
                "rows": rows,
                "events": len(parsed.events),
                "event_kind_counts": parsed.kind_counts,
                "dev_start_row": args.dev_start_row,
                "holdout_start_row": args.holdout_start_row,
                "train_raw_bytes_proportional": train_raw,
                "dev_raw_bytes_proportional": dev_raw,
                "holdout_raw_bytes_proportional": holdout_raw,
                "selection_reads_holdout": False,
            },
            "parameters": {
                "tries": args.tries.split(","),
                "feature_schemes": args.schemes.split(","),
                "decay_shifts": list(parse_ints(args.decay_shifts)),
                "signed_blends_ppm": list(blends_ppm),
                "minimum_observations": args.minimum_observations,
                "margin_qbits": args.margin_qbits,
                "cap_nodes_per_trie": args.cap_nodes,
                "minimum_support": args.min_support,
                "alpha2": args.alpha2,
                "minimum_entity_events": args.minimum_entity_events,
                "maximum_entity_events": args.maximum_entity_events,
                "holdout_blocks": args.holdout_blocks,
                "update_contract": (
                    "choose from prior bucket gains, code truth, decay and update "
                    "all signed experts"
                ),
            },
            "selection": {
                "rule": (
                    "maximum development qbit gain; ties prefer training gain, "
                    "smaller state, then lexical identity"
                ),
                "selected_candidate": selected_run.spec.name,
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
                "target_gap_bytes": args.forecast_gap_bytes,
                "zero_code_required_bytes_per_1m": required_zero_code,
                "provisional_integration_code_bytes": (
                    args.provisional_integration_code_bytes
                ),
                "provisional_code_cost_bytes_per_1m_at_1g": provisional_code_rate,
                "required_with_provisional_code_bytes_per_1m": (
                    required_with_provisional_code
                ),
                "full_exact_saved_bytes_per_1m": full_rate,
                "holdout_exact_saved_bytes_per_proportional_1m": holdout_rate,
                "holdout_qbit_gain_bytes_per_proportional_1m": qbit_holdout_rate,
                "maximum_payable_integration_code_bytes_from_lower_rate": (
                    payable_code_bytes
                ),
                "max_incremental_state_bytes_estimate": max_state,
                "economics_pass_with_provisional_code": economics_pass,
            },
            "identity": {
                "raw_roundtrip_ok": True,
                "base_trace_full_stream_coverage": True,
                "baseline_payload_byte_identical": True,
                "route_selected_before_current_truth": True,
                "mixer_updated_after_current_truth": True,
                "trie_updated_after_completed_event": True,
                "features_use_decoded_prefix_only": True,
                "static_entity_payload_bytes": 0,
                "decoder_replayable_state": True,
                "selection_reads_holdout": False,
            },
            "verdict": verdict,
            "promotion_authorized": False,
            "claim_boundary": (
                "This is exact arithmetic shadow evidence over a hash-pinned "
                "endpoint428 probability stream. It does not change a native "
                "archive. Native integration, compressed source accounting, "
                "roundtrip, determinism, RSS, broader transfer, and official "
                "1G proof remain required."
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
    parser.add_argument("--baseline-payload", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-payload", type=Path)
    parser.add_argument("--candidate-p1", type=Path)
    parser.add_argument("--dev-start-row", type=int, required=True)
    parser.add_argument("--holdout-start-row", type=int, required=True)
    parser.add_argument("--cap-nodes", type=int, default=500_000)
    parser.add_argument("--min-support", type=int, default=1)
    parser.add_argument("--alpha2", type=int, default=1)
    parser.add_argument("--minimum-entity-events", type=int, default=1)
    parser.add_argument("--maximum-entity-events", type=int, default=64)
    parser.add_argument("--tries", default="title,link,combined")
    parser.add_argument("--schemes", default=",".join(FEATURE_SCHEMES))
    parser.add_argument("--decay-shifts", default="0,10,14")
    parser.add_argument(
        "--signed-blends",
        default=",".join(str(value) for value in DEFAULT_SIGNED_BLENDS),
    )
    parser.add_argument("--minimum-observations", type=int, default=8)
    parser.add_argument("--margin-qbits", type=int, default=0)
    parser.add_argument("--holdout-blocks", type=int, default=16)
    parser.add_argument("--forecast-gap-bytes", type=int, default=57_404)
    parser.add_argument(
        "--provisional-integration-code-bytes", type=int, default=12_000
    )
    args = parser.parse_args()
    for path in (
        args.store,
        args.raw,
        args.dictionary,
        args.base_p1,
        args.baseline_payload,
    ):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(
        json.dumps(
            {
                "selected": receipt["selection"]["selected_candidate"],
                "dev_gain_bytes": receipt["selection"]["candidates"][0]["dev"][
                    "gain_bytes"
                ],
                "heldout_saved_bytes": receipt["exact_replay"]["holdout"][
                    "saved_bytes"
                ],
                "heldout_rate": receipt["economics"][
                    "holdout_exact_saved_bytes_per_proportional_1m"
                ],
                "required_rate": receipt["economics"][
                    "required_with_provisional_code_bytes_per_1m"
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
