#!/usr/bin/env python3
"""Restricted GSRT2-to-HARM callback adapter and bounded shadow replay.

Only the fields enumerated by ``pretruth_view`` reach prediction.  In
particular, the tape's posttruth raw span is parsed for ABI validation but is
never exposed to HARM-Delta.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import struct
from types import MappingProxyType
from typing import Callable, Iterable, Iterator, Mapping

from core import (
    HarmDelta,
    MODE_ORDER,
    PROBABILITY_SCALE,
    PROJECTED_FULL_SHADOW_STATE_BOUND_BYTES,
    PROJECTED_NATIVE_TREATMENT_STATE_BOUND_BYTES,
    RouteId,
)


TAPE_HEADER_BYTES = 192
TAPE_RECORD_BYTES = 88
TAPE_RECORD = struct.Struct("<10QI4B")
EVENT_TEMPLATE_ENTER = 1
EVENT_EXPLICIT_FIELD_ENTRY = 2
EVENT_FIELD_VALUE_BYTE = 3
EVENT_DEFERRED_VALUE_UPDATE = 4
EVENT_FIELD_EXIT = 5
EVENT_POSITIONAL_FIELD_EXIT_AUDIT = 6
EVENT_TEMPLATE_EXIT = 7
EVENT_OVERFLOW_ENTER = 8
EVENT_OVERFLOW_EXIT = 9
FLAG_PREDICTIVE = 2
WRT_OPEN = ord("P")
WRT_FIELD = ord("Q")
WRT_CLOSE = ord("R")
HORIZON_KEY_BYTES = 16
HORIZON_MINIMUM_AGE = 100_000_000
HORIZON_HASH_BASE = 0x9E3779B185EBCA87

EXPECTED_FLAGS = {
    EVENT_TEMPLATE_ENTER: 128,
    EVENT_EXPLICIT_FIELD_ENTRY: 137,
    EVENT_FIELD_VALUE_BYTE: 11,
    EVENT_DEFERRED_VALUE_UPDATE: 77,
    EVENT_FIELD_EXIT: 137,
    EVENT_POSITIONAL_FIELD_EXIT_AUDIT: 144,
    EVENT_TEMPLATE_EXIT: 128,
    EVENT_OVERFLOW_ENTER: 160,
    EVENT_OVERFLOW_EXIT: 160,
}
EXPECTED_KEY_IDENTITY = {
    EVENT_TEMPLATE_ENTER: 0,
    EVENT_EXPLICIT_FIELD_ENTRY: 1,
    EVENT_FIELD_VALUE_BYTE: 1,
    EVENT_DEFERRED_VALUE_UPDATE: 1,
    EVENT_FIELD_EXIT: 1,
    EVENT_POSITIONAL_FIELD_EXIT_AUDIT: 2,
    EVENT_TEMPLATE_EXIT: 0,
    EVENT_OVERFLOW_ENTER: 0,
    EVENT_OVERFLOW_EXIT: 0,
}


@dataclass(frozen=True)
class TapeRow:
    source: int
    availability: int
    first_bit: int
    raw_before: int
    raw_after: int
    route_lo: int
    route_hi: int
    witness_lo: int
    witness_hi: int
    virtual_ordinal: int
    field_ordinal: int
    event_type: int
    flags: int
    depth: int
    key_identity: int

    def route(self) -> RouteId:
        return RouteId(
            self.route_lo, self.route_hi, self.witness_lo, self.witness_hi
        )

    def occurrence_id(self) -> tuple[int, ...]:
        return (
            self.depth,
            self.route_lo,
            self.route_hi,
            self.witness_lo,
            self.witness_hi,
            self.field_ordinal,
        )

    def pretruth_view(self) -> tuple[int, ...]:
        if self.event_type != EVENT_FIELD_VALUE_BYTE:
            raise ValueError("pretruth view requested for nonprediction")
        return (
            self.source,
            self.first_bit,
            self.route_lo,
            self.route_hi,
            self.witness_lo,
            self.witness_hi,
            self.virtual_ordinal,
            self.field_ordinal,
            self.depth,
            self.key_identity,
        )


@dataclass(frozen=True)
class PhysicalSeed:
    target_coordinate: int
    source_coordinate: int
    context_hash: int
    anchor_transition_hash: int


@dataclass(frozen=True)
class PhysicalSeedTape:
    observer_sha256: str
    repeat_observer_sha256: str
    seed_payload_sha256: str
    repeat_seed_payload_sha256: str
    terminal_anchor_transition_hash: int
    repeat_terminal_anchor_transition_hash: int
    seeds: Mapping[int, PhysicalSeed]

    def __post_init__(self) -> None:
        digests = (
            self.observer_sha256,
            self.repeat_observer_sha256,
            self.seed_payload_sha256,
            self.repeat_seed_payload_sha256,
        )
        if any(
            len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            for digest in digests
        ):
            raise ValueError("physical seed observer digest is malformed")
        if self.observer_sha256 != self.repeat_observer_sha256:
            raise ValueError("physical seed observer lacks exact repeat identity")
        if self.seed_payload_sha256 != self.repeat_seed_payload_sha256:
            raise ValueError("physical seed payload lacks exact repeat identity")
        if (
            self.terminal_anchor_transition_hash
            != self.repeat_terminal_anchor_transition_hash
            or not 0 <= self.terminal_anchor_transition_hash < 1 << 64
        ):
            raise ValueError("physical anchor state lacks exact repeat identity")
        payload = bytearray()
        for target, seed in sorted(self.seeds.items()):
            if target != seed.target_coordinate:
                raise ValueError("physical seed dictionary target mismatch")
            payload.extend(struct.pack(
                "<4Q", seed.target_coordinate, seed.source_coordinate,
                seed.context_hash, seed.anchor_transition_hash,
            ))
        if hashlib.sha256(payload).hexdigest() != self.seed_payload_sha256:
            raise ValueError("physical seed payload digest mismatch")
        object.__setattr__(self, "seeds", MappingProxyType(dict(self.seeds)))

    def get(self, coordinate: int) -> PhysicalSeed | None:
        return self.seeds.get(coordinate)


def _u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")


def _u64(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 8], "little")


def horizon_context_hash(context: bytes) -> int:
    if len(context) != HORIZON_KEY_BYTES:
        raise ValueError("invalid physical HORIZON context")
    value = 0
    for byte in context:
        value = (value * HORIZON_HASH_BASE + byte) & ((1 << 64) - 1)
    return value


def _priority(event_type: int) -> int:
    if event_type == EVENT_DEFERRED_VALUE_UPDATE:
        return 0
    if event_type == EVENT_FIELD_VALUE_BYTE:
        return 2
    return 1


def validate_tape_row(
    row: TapeRow, wrt_bytes: int, raw_bytes: int | None = None
) -> None:
    if not 0 <= row.source < wrt_bytes:
        raise ValueError("GSRT2 source outside population")
    if row.first_bit != row.availability * 8:
        raise ValueError("GSRT2 first-bit arithmetic mismatch")
    if row.event_type not in EXPECTED_FLAGS:
        raise ValueError("invalid GSRT2 event")
    if row.flags != EXPECTED_FLAGS[row.event_type]:
        raise ValueError("GSRT2 event/flag mismatch")
    if row.key_identity != EXPECTED_KEY_IDENTITY[row.event_type]:
        raise ValueError("GSRT2 event/key mismatch")
    if row.event_type == EVENT_FIELD_VALUE_BYTE:
        if row.availability != row.source:
            raise ValueError("GSRT2 prediction delta mismatch")
    elif row.event_type == EVENT_DEFERRED_VALUE_UPDATE:
        ordinary = row.availability == row.source + 2
        terminal = row.source + 1 == wrt_bytes and row.availability == wrt_bytes
        if not (ordinary or terminal):
            raise ValueError("GSRT2 deferred delta mismatch")
    elif row.availability != row.source + 1:
        raise ValueError("GSRT2 structural delta mismatch")
    if row.event_type in (
        EVENT_EXPLICIT_FIELD_ENTRY,
        EVENT_FIELD_VALUE_BYTE,
        EVENT_DEFERRED_VALUE_UPDATE,
        EVENT_FIELD_EXIT,
    ) and row.depth == 0:
        raise ValueError("GSRT2 routed event has zero depth")
    if row.depth > 16:
        raise ValueError("GSRT2 template depth exceeds frozen bound")
    routed = bool(row.flags & 1)
    route_zero = (row.route_lo, row.route_hi) == (0, 0)
    witness_zero = (row.witness_lo, row.witness_hi) == (0, 0)
    if routed:
        if route_zero or witness_zero:
            raise ValueError("GSRT2 routed event has zero identity")
    elif not route_zero or not witness_zero or row.virtual_ordinal != 0:
        raise ValueError("GSRT2 plain event carries routed state")
    if raw_bytes is not None and not (
        0 <= row.raw_before <= row.raw_after <= raw_bytes
    ):
        raise ValueError("GSRT2 raw frontier mismatch")


@dataclass(frozen=True)
class TapeBinding:
    tape_sha256: str
    repeat_tape_sha256: str
    fixture_flags: int
    store_bytes: int
    wrt_bytes: int
    raw_bytes: int
    dictionary_bytes: int
    record_count: int
    descriptor_count: int
    event_counts: tuple[int, ...]
    deferred_updates: int
    positional_predictive_events: int
    parser_digest: int
    raw_digest: int
    wrt_digest: int


def iter_tape(path: Path, binding: TapeBinding) -> Iterator[TapeRow]:
    if (
        len(binding.tape_sha256) != 64
        or binding.tape_sha256 != binding.repeat_tape_sha256
        or any(
            character not in "0123456789abcdef"
            for character in binding.tape_sha256
        )
    ):
        raise ValueError("GSRT2 tape lacks exact repeat identity")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    if digest.hexdigest() != binding.tape_sha256:
        raise ValueError("GSRT2 tape content binding mismatch")
    if len(binding.event_counts) != 9:
        raise ValueError("GSRT2 event-count geometry mismatch")
    if binding.fixture_flags not in (0, 1):
        raise ValueError("GSRT2 reserved fixture flags are set")
    if binding.positional_predictive_events != 0:
        raise ValueError("HARM v1 forbids positional predictive events")
    with path.open("rb") as stream:
        header = stream.read(TAPE_HEADER_BYTES)
        if len(header) != TAPE_HEADER_BYTES or header[:8] != b"GSRT2\0\0\0":
            raise ValueError("invalid GSRT2 header")
        if _u32(header, 8) != 2 or _u32(header, 12) != TAPE_HEADER_BYTES:
            raise ValueError("invalid GSRT2 version/header geometry")
        if _u32(header, 16) != TAPE_RECORD_BYTES:
            raise ValueError("invalid GSRT2 record geometry")
        expected_header = {
            20: (4, binding.fixture_flags, "fixture flags"),
            24: (8, binding.store_bytes, "store bytes"),
            32: (8, binding.wrt_bytes, "WRT bytes"),
            40: (8, binding.raw_bytes, "raw bytes"),
            48: (8, binding.dictionary_bytes, "dictionary bytes"),
            56: (8, binding.record_count, "record count"),
            64: (8, binding.descriptor_count, "descriptor count"),
            168: (8, binding.parser_digest, "parser digest"),
            176: (8, binding.raw_digest, "raw digest"),
            184: (8, binding.wrt_digest, "WRT digest"),
        }
        for offset, (width, expected, label) in expected_header.items():
            observed = _u32(header, offset) if width == 4 else _u64(header, offset)
            if observed != expected:
                raise ValueError(f"GSRT2 {label} mismatch")
        if _u64(header, 160) != 0:
            raise ValueError("GSRT2 reports pretruth violations")
        observed_counts = tuple(_u64(header, 72 + 8 * index) for index in range(9))
        if (
            observed_counts != binding.event_counts
            or sum(observed_counts) != binding.record_count
            or _u64(header, 144) != binding.deferred_updates
            or _u64(header, 152) != binding.positional_predictive_events
            or observed_counts[EVENT_DEFERRED_VALUE_UPDATE - 1]
            != binding.deferred_updates
        ):
            raise ValueError("GSRT2 event accounting mismatch")
        previous_order: tuple[int, int, int] | None = None
        body_counts = [0] * 9
        for _ in range(binding.record_count):
            payload = stream.read(TAPE_RECORD_BYTES)
            if len(payload) != TAPE_RECORD_BYTES:
                raise ValueError("short GSRT2 record")
            row = TapeRow(*TAPE_RECORD.unpack(payload))
            validate_tape_row(row, binding.wrt_bytes, binding.raw_bytes)
            order = (row.availability, _priority(row.event_type), row.source)
            if previous_order is not None and order < previous_order:
                raise ValueError("GSRT2 callback order regression")
            previous_order = order
            body_counts[row.event_type - 1] += 1
            yield row
        if tuple(body_counts) != binding.event_counts:
            raise ValueError("GSRT2 body/header event-count mismatch")
        if stream.read(1):
            raise ValueError("trailing GSRT2 bytes")


def _truth_count(p1: int, truth_bit: int) -> int:
    return p1 if truth_bit else PROBABILITY_SCALE - p1


class ReplayMetrics:
    def __init__(
        self,
        measure_start: int,
        measure_end: int,
        measure_raw_start: int | None = None,
        measure_raw_end: int | None = None,
    ) -> None:
        if not 0 <= measure_start < measure_end:
            raise ValueError("invalid measurement scope")
        if (measure_raw_start is None) != (measure_raw_end is None):
            raise ValueError("raw measurement bounds must be supplied together")
        if (
            measure_raw_start is not None
            and not 0 <= measure_raw_start < measure_raw_end
        ):
            raise ValueError("invalid raw measurement scope")
        self.measure_start = measure_start
        self.measure_end = measure_end
        self.measure_bytes = measure_end - measure_start
        self.measure_raw_start = measure_raw_start
        self.measure_raw_end = measure_raw_end
        self.active_bytes = 0
        self.arm_awake_bytes = {arm: 0 for arm in HarmDelta.ARMS}
        self.parent_truth_bits = 0.0
        self.candidate_gain_bits = {arm: 0.0 for arm in HarmDelta.ARMS}
        self.candidate_gain_by_third = {
            arm: [0.0, 0.0, 0.0] for arm in HarmDelta.ARMS
        }
        self.gain_bits = {arm: 0.0 for arm in HarmDelta.ARMS}
        self.gain_by_third = {arm: [0.0, 0.0, 0.0] for arm in HarmDelta.ARMS}
        self.positive_opportunity_bytes = {arm: 0 for arm in HarmDelta.ARMS}
        self.top_emitting_mode = {mode: 0 for mode in ("M", "X", "I")}
        self.top_edit_drift = {offset: 0 for offset in range(-8, 9)}
        self.e_gain_by_top_emitting_mode = {
            mode: 0.0 for mode in ("M", "X", "I")
        }
        self.e_gain_by_top_edit_drift = {offset: 0.0 for offset in range(-8, 9)}
        self.e_positive_gain_bins = {
            "(0,0.25]": [0, 0.0],
            "(0.25,0.5]": [0, 0.0],
            "(0.5,1]": [0, 0.0],
            "(1,2]": [0, 0.0],
            "(2,4]": [0, 0.0],
            "(4,8]": [0, 0.0],
            "(8,+inf)": [0, 0.0],
        }
        self.digest = hashlib.sha256()

    def observe(
        self,
        coordinate: int,
        raw_coordinate: int,
        truth: int,
        rows: dict[str, tuple[int, ...]],
        awake: dict[str, bool],
        edit_state: tuple[int, str] | None,
    ) -> None:
        self.active_bytes += 1
        if self.measure_raw_start is None:
            third = min(
                2, (coordinate - self.measure_start) * 3 // self.measure_bytes
            )
        else:
            third = min(2, (
                (raw_coordinate - self.measure_raw_start) * 3
                // (self.measure_raw_end - self.measure_raw_start)
            ))
        byte_gains = {arm: 0.0 for arm in HarmDelta.ARMS}
        self.digest.update(coordinate.to_bytes(8, "little"))
        self.digest.update(truth.to_bytes(1, "little"))
        for bit_index, parent in enumerate(rows["P"]):
            truth_bit = (truth >> (7 - bit_index)) & 1
            parent_truth = _truth_count(parent, truth_bit)
            self.parent_truth_bits -= math.log2(parent_truth / PROBABILITY_SCALE)
            for arm in HarmDelta.ARMS:
                candidate = rows[f"candidate_{arm}"][bit_index]
                mixed = rows[f"mixture_{arm}"][bit_index]
                candidate_gain = math.log2(
                    _truth_count(candidate, truth_bit) / parent_truth
                )
                gain = math.log2(_truth_count(mixed, truth_bit) / parent_truth)
                self.candidate_gain_bits[arm] += candidate_gain
                self.candidate_gain_by_third[arm][third] += candidate_gain
                self.gain_bits[arm] += gain
                self.gain_by_third[arm][third] += gain
                byte_gains[arm] += gain
                self.digest.update(arm.encode("ascii"))
                self.digest.update(coordinate.to_bytes(8, "little"))
                self.digest.update(bit_index.to_bytes(1, "little"))
                self.digest.update(parent.to_bytes(2, "little"))
                self.digest.update(candidate.to_bytes(2, "little"))
                self.digest.update(mixed.to_bytes(2, "little"))
        for arm in HarmDelta.ARMS:
            self.digest.update(bytes((1 if awake[arm] else 0,)))
            if awake[arm]:
                self.arm_awake_bytes[arm] += 1
            if byte_gains[arm] > 0:
                self.positive_opportunity_bytes[arm] += 1
        e_gain = byte_gains["E"]
        if e_gain > 0:
            if e_gain <= 0.25:
                label = "(0,0.25]"
            elif e_gain <= 0.5:
                label = "(0.25,0.5]"
            elif e_gain <= 1:
                label = "(0.5,1]"
            elif e_gain <= 2:
                label = "(1,2]"
            elif e_gain <= 4:
                label = "(2,4]"
            elif e_gain <= 8:
                label = "(4,8]"
            else:
                label = "(8,+inf)"
            self.e_positive_gain_bins[label][0] += 1
            self.e_positive_gain_bins[label][1] += e_gain
        if edit_state is not None:
            drift, mode = edit_state
            self.top_edit_drift[drift] += 1
            self.top_emitting_mode[mode] += 1
            self.e_gain_by_top_edit_drift[drift] += byte_gains["E"]
            self.e_gain_by_top_emitting_mode[mode] += byte_gains["E"]

    def result(self, state_digest: str) -> dict[str, object]:
        return {
            "measure_start_wrt": self.measure_start,
            "measure_end_wrt": self.measure_end,
            "measure_start_raw": self.measure_raw_start,
            "measure_end_raw": self.measure_raw_end,
            "chronological_third_coordinate_system": (
                "wrt" if self.measure_raw_start is None else "canonical_raw"
            ),
            "active_bytes": self.active_bytes,
            "arm_awake_bytes": self.arm_awake_bytes,
            "parent_truth_bits": self.parent_truth_bits,
            "raw_candidate_gain_bits": self.candidate_gain_bits,
            "raw_candidate_gain_bits_by_third": self.candidate_gain_by_third,
            "mixture_gain_bits": self.gain_bits,
            "mixture_gain_bits_by_third": self.gain_by_third,
            "positive_opportunity_bytes": self.positive_opportunity_bytes,
            "top_emitting_mode_bytes": self.top_emitting_mode,
            "e_mixture_gain_bits_by_top_emitting_mode": (
                self.e_gain_by_top_emitting_mode
            ),
            "top_edit_drift_bytes": {
                str(key): value for key, value in self.top_edit_drift.items()
            },
            "e_mixture_gain_bits_by_top_edit_drift": {
                str(key): value
                for key, value in self.e_gain_by_top_edit_drift.items()
            },
            "route_class": "explicit_template_field",
            "e_mixture_gain_bits_by_route_class": {
                "explicit_template_field": self.gain_bits["E"]
            },
            "e_positive_byte_gain_distribution": {
                label: {"bytes": values[0], "gain_bits": values[1]}
                for label, values in self.e_positive_gain_bins.items()
            },
            "projected_native_treatment_serialized_state_bound_bytes": (
                PROJECTED_NATIVE_TREATMENT_STATE_BOUND_BYTES
            ),
            "projected_full_shadow_serialized_state_bound_bytes": (
                PROJECTED_FULL_SHADOW_STATE_BOUND_BYTES
            ),
            "probability_sha256": self.digest.hexdigest(),
            "terminal_state_sha256": state_digest,
        }


ParentProvider = Callable[[int], tuple[int, ...]]
def _physical_donor(
    stream: bytes, target: int, seed_tape: PhysicalSeedTape | None
) -> bytes | None:
    if seed_tape is None:
        return None
    seed = seed_tape.get(target)
    if seed is None:
        return None
    if seed.target_coordinate != target:
        raise ValueError("physical seed target mismatch")
    source = seed.source_coordinate
    if (
        target < HORIZON_KEY_BYTES
        or source < HORIZON_KEY_BYTES
        or target - source <= HORIZON_MINIMUM_AGE
        or source + 512 > target
    ):
        raise ValueError("physical seed is not causally old")
    target_context = stream[target - HORIZON_KEY_BYTES : target]
    source_context = stream[source - HORIZON_KEY_BYTES : source]
    if target_context != source_context:
        raise ValueError("physical seed context mismatch")
    if horizon_context_hash(target_context) != seed.context_hash:
        raise ValueError("physical seed context hash mismatch")
    if not 0 <= seed.anchor_transition_hash < 1 << 64:
        raise ValueError("physical seed transition witness mismatch")
    return stream[source : source + 512]


def replay(
    stream: bytes,
    tape_rows: Iterable[TapeRow],
    parent_provider: ParentProvider,
    physical_seed_tape: PhysicalSeedTape | None = None,
    expected_physical_observer_sha256: str | None = None,
    measure_start: int = 0,
    measure_end: int | None = None,
    measure_raw_start: int | None = None,
    measure_raw_end: int | None = None,
) -> dict[str, object]:
    """Replay one already frozen bounded population.

    A physical seed tape is intentionally absent from the GSRT2 ABI.  When one
    is supplied, the caller must independently bind its prospectively frozen
    observer digest; otherwise the G comparator is rejected rather than used.
    """

    if measure_end is None:
        measure_end = len(stream)
    if not 0 <= measure_start < measure_end <= len(stream):
        raise ValueError("measurement scope is outside replay prefix")
    if physical_seed_tape is not None and (
        expected_physical_observer_sha256 is None
        or physical_seed_tape.observer_sha256
        != expected_physical_observer_sha256
    ):
        raise ValueError("physical observer identity is not prospectively bound")
    model = HarmDelta()
    metrics = ReplayMetrics(
        measure_start, measure_end, measure_raw_start, measure_raw_end
    )
    def validated_rows() -> Iterator[TapeRow]:
        previous: tuple[int, int, int] | None = None
        for row in tape_rows:
            validate_tape_row(row, len(stream))
            order = (row.availability, _priority(row.event_type), row.source)
            if previous is not None and order < previous:
                raise ValueError("GSRT2 callback priority regression")
            previous = order
            yield row

    iterator = iter(validated_rows())
    next_row = next(iterator, None)
    scheduled: dict[
        int, list[tuple[int, tuple[int, ...], RouteId, int]]
    ] = {}
    ambiguous: dict[int, tuple[int, ...]] = {}
    literal_expected: dict[int, int] = {}
    pending_marker: tuple[int, int, tuple[int, ...]] | None = None
    entry_ordinals: dict[tuple[int, ...], int] = {}
    route_ordinals: dict[RouteId, int] = {}

    for coordinate in range(len(stream) + 1):
        if coordinate == len(stream) and pending_marker is not None:
            source, _, _ = pending_marker
            literal_expected[source] = coordinate
            pending_marker = None
        group: list[TapeRow] = []
        while next_row is not None and next_row.availability == coordinate:
            group.append(next_row)
            next_row = next(iterator, None)
        if next_row is not None and next_row.availability < coordinate:
            raise ValueError("late tape callback")

        deferred_sources: set[int] = set()
        for row in group:
            if row.event_type != EVENT_DEFERRED_VALUE_UPDATE:
                continue
            if row.source in deferred_sources:
                raise ValueError("duplicate deferred literal callback")
            occurrence_id = ambiguous.get(row.source)
            if occurrence_id is None:
                raise ValueError("deferred update lacks ambiguous prediction")
            occurrence = model.occurrences.get(occurrence_id)
            if occurrence is None or occurrence.route != row.route():
                raise ValueError("deferred update route mismatch")
            if route_ordinals.get(row.route(), row.virtual_ordinal) != row.virtual_ordinal:
                raise ValueError("deferred update virtual ordinal mismatch")
            model.commit_byte(occurrence_id, stream[row.source])
            route_ordinals[row.route()] = row.virtual_ordinal + 1
            deferred_sources.add(row.source)

        missing_deferred = {
            source for source, availability in literal_expected.items()
            if availability == coordinate and source not in deferred_sources
        }
        if missing_deferred:
            raise ValueError("missing deferred literal callback")
        for source in deferred_sources:
            if literal_expected.get(source) != coordinate:
                raise ValueError("unexpected deferred literal callback")
            literal_expected.pop(source)

        for _, occurrence_id, route, truth in sorted(scheduled.pop(coordinate, [])):
            model.commit_byte(occurrence_id, truth)
            route_ordinals[route] = route_ordinals.get(route, 0) + 1

        prediction: TapeRow | None = None
        for row in group:
            if row.event_type == EVENT_DEFERRED_VALUE_UPDATE:
                continue
            if row.event_type == EVENT_EXPLICIT_FIELD_ENTRY:
                occurrence_id = row.occurrence_id()
                if row.key_identity != 1:
                    raise ValueError("non-explicit route entered HARM v1")
                route = row.route()
                if route in route_ordinals and route_ordinals[route] != row.virtual_ordinal:
                    raise ValueError("route entry virtual ordinal mismatch")
                route_ordinals.setdefault(route, row.virtual_ordinal)
                physical = _physical_donor(
                    stream, row.availability, physical_seed_tape
                )
                model.enter(
                    occurrence_id,
                    route,
                    occurrence_seed=row.source ^ row.virtual_ordinal,
                    physical_donor=physical,
                )
                entry_ordinals[occurrence_id] = row.virtual_ordinal
            elif row.event_type == EVENT_FIELD_EXIT:
                occurrence_id = row.occurrence_id()
                if occurrence_id not in entry_ordinals:
                    raise ValueError("field exit lacks route entry")
                if route_ordinals.get(row.route()) != row.virtual_ordinal:
                    raise ValueError("field exit virtual ordinal mismatch")
                model.exit(
                    occurrence_id,
                    expected_commits=row.virtual_ordinal - entry_ordinals.pop(
                        occurrence_id
                    ),
                )
            elif row.event_type == EVENT_FIELD_VALUE_BYTE:
                if prediction is not None or row.source != coordinate:
                    raise ValueError("invalid predictive callback multiplicity")
                if not (row.flags & FLAG_PREDICTIVE) or row.key_identity != 1:
                    raise ValueError("invalid HARM predictive callback")
                row.pretruth_view()
                if route_ordinals.get(row.route()) != row.virtual_ordinal:
                    raise ValueError("prediction virtual ordinal mismatch")
                prediction = row
            elif row.event_type not in (
                EVENT_TEMPLATE_ENTER,
                EVENT_POSITIONAL_FIELD_EXIT_AUDIT,
                EVENT_TEMPLATE_EXIT,
                EVENT_OVERFLOW_ENTER,
                EVENT_OVERFLOW_EXIT,
            ):
                raise ValueError("unsupported semantic callback")

        for source in deferred_sources:
            ambiguous.pop(source, None)

        if coordinate == len(stream):
            break
        truth = stream[coordinate]
        paired_current = False
        if pending_marker is not None:
            pending_source, pending_truth, _ = pending_marker
            if truth == pending_truth:
                ambiguous.pop(pending_source, None)
                paired_current = True
            else:
                literal_expected[pending_source] = coordinate + 1
            pending_marker = None
        if prediction is None:
            continue
        occurrence_id = prediction.occurrence_id()
        if occurrence_id not in model.occurrences:
            raise ValueError("prediction lacks active occurrence")
        histograms = model.candidate_histograms(occurrence_id)
        occurrence = model.occurrences[occurrence_id]
        edit = occurrence.transducers.get("E")
        edit_state: tuple[int, str] | None = None
        if edit is not None and hasattr(edit, "weights") and edit.weights:
            edit_state = max(
                edit.weights,
                key=lambda key: (
                    edit.weights[key], -abs(key[0]), -key[0],
                    -MODE_ORDER[key[1]],
                ),
            )
        rows = model.score_byte(
            occurrence_id, parent_provider(coordinate), truth
        )
        if rows["P"] != rows["K"]:
            raise AssertionError("P/K probability identity failure")
        in_wrt_scope = measure_start <= coordinate < measure_end
        in_raw_scope = (
            measure_raw_start is None
            or measure_raw_start <= prediction.raw_before < measure_raw_end
        )
        if in_wrt_scope and in_raw_scope:
            metrics.observe(
                coordinate,
                prediction.raw_before,
                truth,
                rows,
                {arm: histograms[arm] is not None for arm in HarmDelta.ARMS},
                edit_state,
            )

        if truth in (WRT_OPEN, WRT_CLOSE) and not paired_current:
            ambiguous[coordinate] = occurrence_id
            pending_marker = (coordinate, truth, occurrence_id)
        elif truth != WRT_FIELD:
            scheduled.setdefault(coordinate + 1, []).append(
                (coordinate, occurrence_id, prediction.route(), truth)
            )

    if next_row is not None:
        raise ValueError("tape callbacks extend beyond WRT population")
    if scheduled:
        raise ValueError("ordinary commits extend beyond WRT population")
    if ambiguous or literal_expected or pending_marker is not None:
        raise ValueError("unresolved semantic literal lifecycle")
    result = metrics.result(model.state_digest())
    result["p_k_probability_identity_pass"] = True
    result["physical_g_comparator_admissible"] = bool(
        physical_seed_tape is not None
        and physical_seed_tape.seeds
        and result["arm_awake_bytes"]["G"] > 0
    )
    result["physical_seed_observer_sha256"] = (
        None if physical_seed_tape is None else physical_seed_tape.observer_sha256
    )
    result["physical_seed_payload_sha256"] = (
        None if physical_seed_tape is None
        else physical_seed_tape.seed_payload_sha256
    )
    return result
