#!/usr/bin/env python3
"""Exact bounded core for the zero-credit HARM-Delta shadow.

The core operates on already decoded WRT bytes.  It never parses future field
content, selects a completed edit path, or writes an authoritative parent.
Population-specific parsing and Endpoint428 trace binding live outside this
module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import struct
from typing import Iterable


PROBABILITY_SCALE = 1 << 16
POSTERIOR_SCALE = 1 << 63
ALIGNMENT_SCALE = 1 << 30
MAX_VALUE_BYTES = 512
ROUTE_SLOTS = 4096
DRIFT = 8
MAX_ACTIVE_OCCURRENCES = 16
MASK64 = (1 << 64) - 1

# Fixed-width serialized-state projections for the declared mechanism.  These
# are design bounds, not Python RSS measurements or package accounting.
PROJECTED_NATIVE_TREATMENT_STATE_BOUND_BYTES = 2_266_801
PROJECTED_FULL_SHADOW_STATE_BOUND_BYTES = 4_565_073

MODES = ("M", "X", "I", "D")
MODE_ORDER = {mode: ordinal for ordinal, mode in enumerate(MODES)}
OFFSET_STEP = {"M": 0, "X": 0, "I": -1, "D": 1}

# Integer transition masses.  Rows are the previous edit mode and columns are
# the next mode.  They are constants, not trained or selected from corpus data.
TRANSITIONS = {
    "M": {"M": 224, "X": 16, "I": 8, "D": 8},
    "X": {"M": 128, "X": 96, "I": 16, "D": 16},
    "I": {"M": 96, "X": 16, "I": 136, "D": 8},
    "D": {"M": 96, "X": 16, "I": 8, "D": 136},
}

# (mass assigned to the donor byte, mass assigned to each other byte).
# Every row sums to 65536 over the byte alphabet.  D is a silent donor-only
# transition and consequently has no emission row.
EMISSIONS = {
    "M": (32896, 128),
    "X": (1, 257),
    "I": (256, 256),
}


def splitmix64(value: int) -> int:
    value = (value + 0x9E3779B97F4A7C15) & MASK64
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK64
    return (value ^ (value >> 31)) & MASK64


def round_half_up(numerator: int, denominator: int, scale: int) -> int:
    if numerator <= 0 or denominator <= 0 or numerator >= denominator:
        raise ValueError("invalid probability ratio")
    quotient, remainder = divmod(numerator * scale, denominator)
    if remainder * 2 >= denominator:
        quotient += 1
    return max(1, min(scale - 1, quotient))


def mixture_p1(parent_weight: int, parent_p1: int, candidate_p1: int) -> int:
    if not 0 < parent_weight < POSTERIOR_SCALE:
        raise ValueError("invalid parent weight")
    if not 0 < parent_p1 < PROBABILITY_SCALE:
        raise ValueError("invalid parent probability")
    if not 0 < candidate_p1 < PROBABILITY_SCALE:
        raise ValueError("invalid candidate probability")
    numerator = (
        parent_weight * parent_p1
        + (POSTERIOR_SCALE - parent_weight) * candidate_p1
    )
    quotient, remainder = divmod(numerator, POSTERIOR_SCALE)
    if remainder * 2 >= POSTERIOR_SCALE:
        quotient += 1
    return max(1, min(PROBABILITY_SCALE - 1, quotient))


def posterior_parent_weight(
    parent_weight: int,
    parent_p1: int,
    candidate_p1: int,
    truth_bit: int,
) -> int:
    if truth_bit not in (0, 1):
        raise ValueError("truth bit must be zero or one")
    parent_truth = parent_p1 if truth_bit else PROBABILITY_SCALE - parent_p1
    candidate_truth = (
        candidate_p1 if truth_bit else PROBABILITY_SCALE - candidate_p1
    )
    parent_mass = parent_weight * parent_truth
    candidate_mass = (POSTERIOR_SCALE - parent_weight) * candidate_truth
    return round_half_up(
        parent_mass, parent_mass + candidate_mass, POSTERIOR_SCALE
    )


def _normalize(weights: dict[tuple[int, str], int]) -> dict[tuple[int, str], int]:
    positive = {key: value for key, value in weights.items() if value > 0}
    if not positive:
        return {}
    total = sum(positive.values())
    rows: list[tuple[int, int, tuple[int, str]]] = []
    assigned = 0
    for key in sorted(positive, key=lambda item: (item[0], MODE_ORDER[item[1]])):
        quotient, remainder = divmod(positive[key] * ALIGNMENT_SCALE, total)
        rows.append((quotient, remainder, key))
        assigned += quotient
    missing = ALIGNMENT_SCALE - assigned
    rows.sort(key=lambda row: (-row[1], row[2][0], MODE_ORDER[row[2][1]]))
    result = {key: quotient for quotient, _, key in rows if quotient}
    for _, _, key in rows[:missing]:
        result[key] = result.get(key, 0) + 1
    if sum(result.values()) != ALIGNMENT_SCALE:
        raise AssertionError("alignment normalization drift")
    return result


def conditional_p1(histogram: tuple[int, ...], prefix: int, bit_index: int) -> int:
    if len(histogram) != 256 or not 0 <= bit_index < 8:
        raise ValueError("invalid byte distribution query")
    if not 0 <= prefix < (1 << bit_index):
        raise ValueError("invalid decoded prefix")
    width = 1 << (8 - bit_index)
    start = prefix * width
    middle = start + width // 2
    end = start + width
    denominator = sum(histogram[start:end])
    numerator = sum(histogram[middle:end])
    return round_half_up(numerator, denominator, PROBABILITY_SCALE)


def complement_histogram(histogram: tuple[int, ...]) -> tuple[int, ...]:
    if len(histogram) != 256:
        raise ValueError("invalid byte distribution")
    return tuple(histogram[value ^ 0xFF] for value in range(256))


class EditTransducer:
    """Causal fixed-band integer pair-HMM forward row over a frozen donor."""

    def __init__(self, donor: bytes):
        if not donor or len(donor) > MAX_VALUE_BYTES:
            raise ValueError("donor outside frozen value bound")
        self.donor = bytes(donor)
        self.position = 0
        self.weights = {(0, "M"): ALIGNMENT_SCALE}
        self.last_mode_mass = {mode: 0 for mode in MODES}

    @staticmethod
    def _transition_mass(weight: int, mass: int) -> int:
        quotient, remainder = divmod(weight * mass, 256)
        return quotient + (1 if remainder * 2 >= 256 else 0)

    def _closed_states(self) -> dict[tuple[int, str], int]:
        """Apply bounded silent deletions before the next target emission."""
        closed = dict(self.weights)
        for offset in range(-DRIFT, DRIFT):
            for mode in MODES:
                weight = closed.get((offset, mode), 0)
                donor_index = self.position + offset
                if weight == 0 or not 0 <= donor_index < len(self.donor):
                    continue
                deleted = self._transition_mass(weight, TRANSITIONS[mode]["D"])
                if deleted:
                    key = (offset + 1, "D")
                    closed[key] = closed.get(key, 0) + deleted
        return closed

    def _emitting_paths(self) -> list[tuple[int, str, int | None, int]]:
        paths: list[tuple[int, str, int | None, int]] = []
        for (offset, previous_mode), weight in self._closed_states().items():
            donor_index = self.position + offset
            for next_mode in ("M", "X", "I"):
                transition = self._transition_mass(
                    weight, TRANSITIONS[previous_mode][next_mode]
                )
                if transition == 0:
                    continue
                next_offset = offset + OFFSET_STEP[next_mode]
                if not -DRIFT <= next_offset <= DRIFT:
                    continue
                if next_mode == "I":
                    paths.append((next_offset, next_mode, None, transition))
                elif 0 <= donor_index < len(self.donor):
                    paths.append((
                        next_offset, next_mode, self.donor[donor_index], transition
                    ))
        return paths

    def histogram(self) -> tuple[int, ...] | None:
        baseline = 0
        adjustments = [0] * 256
        active = 0
        for _, mode, donor, weight in self._emitting_paths():
            donor_mass, other_mass = EMISSIONS[mode]
            baseline += weight * other_mass
            if donor is not None:
                adjustments[donor] += weight * (donor_mass - other_mass)
            active += weight
        if active == 0:
            return None
        histogram = tuple(baseline + adjustment for adjustment in adjustments)
        if min(histogram) <= 0:
            raise AssertionError("nonpositive edit distribution mass")
        return histogram

    def observe(self, truth: int) -> None:
        if not 0 <= truth <= 255:
            raise ValueError("truth is not a byte")
        advanced: dict[tuple[int, str], int] = {}
        for next_offset, mode, donor, weight in self._emitting_paths():
            donor_mass, other_mass = EMISSIONS[mode]
            likelihood = donor_mass if donor == truth else other_mass
            key = (next_offset, mode)
            advanced[key] = advanced.get(key, 0) + weight * likelihood
        closed = self._closed_states()
        delete_mass = sum(
            weight for (_, mode), weight in closed.items() if mode == "D"
        )
        self.position += 1
        self.weights = _normalize(advanced)
        self.last_mode_mass = {
            mode: sum(
                weight for (_, state_mode), weight in self.weights.items()
                if state_mode == mode
            )
            for mode in ("M", "X", "I")
        }
        self.last_mode_mass["D"] = delete_mass

    @property
    def awake(self) -> bool:
        return self.histogram() is not None


class LockstepTransducer:
    """Exact same-route position control with no edit tolerance."""

    def __init__(self, donor: bytes):
        if not donor or len(donor) > MAX_VALUE_BYTES:
            raise ValueError("donor outside frozen value bound")
        self.donor = bytes(donor)
        self.position = 0

    def histogram(self) -> tuple[int, ...] | None:
        if self.position >= len(self.donor):
            return None
        donor_mass, other_mass = EMISSIONS["M"]
        result = [other_mass] * 256
        result[self.donor[self.position]] = donor_mass
        return tuple(result)

    def observe(self, truth: int) -> None:
        if not 0 <= truth <= 255:
            raise ValueError("truth is not a byte")
        self.position += 1


@dataclass
class SleepingMixture:
    parent_weight: int = POSTERIOR_SCALE // 2
    awake_updates: int = 0

    def predict(self, parent_p1: int, candidate_p1: int | None) -> int:
        if not 0 < parent_p1 < PROBABILITY_SCALE:
            raise ValueError("invalid parent probability")
        return (
            parent_p1
            if candidate_p1 is None
            else mixture_p1(self.parent_weight, parent_p1, candidate_p1)
        )

    def observe(
        self, parent_p1: int, candidate_p1: int | None, truth_bit: int
    ) -> None:
        if not 0 < parent_p1 < PROBABILITY_SCALE:
            raise ValueError("invalid parent probability")
        if candidate_p1 is None:
            return
        self.parent_weight = posterior_parent_weight(
            self.parent_weight, parent_p1, candidate_p1, truth_bit
        )
        self.awake_updates += 1


@dataclass(frozen=True)
class RouteId:
    route_lo: int
    route_hi: int
    witness_lo: int
    witness_hi: int

    def seed(self) -> int:
        value = self.route_lo ^ splitmix64(self.route_hi)
        value ^= splitmix64(self.witness_lo)
        value ^= splitmix64(self.witness_hi)
        return splitmix64(value)


@dataclass
class ValueSlot:
    tag: RouteId | int
    value: bytes


class ValueBank:
    """Fixed 4,096-slot direct-mapped value bank with exact tag checks."""

    def __init__(self) -> None:
        self.slots: list[ValueSlot | None] = [None] * ROUTE_SLOTS

    def _index(self, tag: RouteId | int) -> int:
        seed = tag.seed() if isinstance(tag, RouteId) else splitmix64(tag)
        return seed & (ROUTE_SLOTS - 1)

    def get(self, tag: RouteId | int) -> bytes | None:
        slot = self.slots[self._index(tag)]
        return slot.value if slot is not None and slot.tag == tag else None

    def put(self, tag: RouteId | int, value: bytes) -> None:
        if not value or len(value) > MAX_VALUE_BYTES:
            raise ValueError("value outside frozen bound")
        self.slots[self._index(tag)] = ValueSlot(tag, bytes(value))


@dataclass
class Occurrence:
    route: RouteId
    random_bucket: int
    transducers: dict[str, EditTransducer | LockstepTransducer]
    current: bytearray = field(default_factory=bytearray)
    total_commits: int = 0
    overflow: bool = False
    closed: bool = False
    expected_commits: int | None = None


class HarmDelta:
    """Bounded route-memory and edit-state machine used by P/K/L/E/G/S/R/N."""

    ARMS = ("L", "E", "G", "S", "R", "N")
    MIXTURE_ARMS = ("L", "E", "G", "S", "R")

    def __init__(self) -> None:
        self.route_bank = ValueBank()
        self.random_bank = ValueBank()
        self.last_completed_route: RouteId | None = None
        self.occurrences: dict[tuple[int, ...], Occurrence] = {}
        self.mixtures = {arm: SleepingMixture() for arm in self.MIXTURE_ARMS}

    @staticmethod
    def random_bucket(route: RouteId, occurrence_seed: int) -> int:
        return splitmix64(route.seed() ^ splitmix64(occurrence_seed)) & (
            ROUTE_SLOTS - 1
        )

    def enter(
        self,
        occurrence_id: tuple[int, ...],
        route: RouteId,
        occurrence_seed: int,
        physical_donor: bytes | None = None,
    ) -> None:
        if (
            len(occurrence_id) != 6
            or any(not 0 <= value < 1 << 64 for value in occurrence_id)
        ):
            raise ValueError("occurrence identity is not six uint64 values")
        if occurrence_id in self.occurrences:
            raise ValueError("duplicate active occurrence")
        if len(self.occurrences) >= MAX_ACTIVE_OCCURRENCES:
            raise MemoryError("active semantic occurrence ceiling exceeded")
        same_route = self.route_bank.get(route)
        random_bucket = self.random_bucket(route, occurrence_seed)
        random_value = self.random_bank.get(random_bucket)
        shifted_value = (
            None
            if self.last_completed_route is None
            else self.route_bank.get(self.last_completed_route)
        )
        donors = {
            "L": same_route,
            "E": same_route,
            "G": physical_donor,
            "S": shifted_value,
            "R": random_value,
        }
        transducers: dict[str, EditTransducer | LockstepTransducer] = {}
        for arm, donor in donors.items():
            if donor:
                transducers[arm] = (
                    LockstepTransducer(donor)
                    if arm == "L"
                    else EditTransducer(donor)
                )
        self.occurrences[occurrence_id] = Occurrence(
            route=route,
            random_bucket=random_bucket,
            transducers=transducers,
        )

    def candidate_histograms(
        self, occurrence_id: tuple[int, ...]
    ) -> dict[str, tuple[int, ...] | None]:
        occurrence = self.occurrences[occurrence_id]
        histograms = {
            arm: (
                occurrence.transducers[arm].histogram()
                if arm in occurrence.transducers
                and not occurrence.overflow
                and occurrence.total_commits < MAX_VALUE_BYTES
                else None
            )
            for arm in ("L", "E", "G", "S", "R")
        }
        histograms["N"] = (
            None if histograms["E"] is None
            else complement_histogram(histograms["E"])
        )
        return histograms

    def score_byte(
        self,
        occurrence_id: tuple[int, ...],
        parent_p1: Iterable[int],
        truth: int,
    ) -> dict[str, tuple[int, ...]]:
        parents = tuple(parent_p1)
        if len(parents) != 8:
            raise ValueError("one parent count is required for each byte bit")
        histograms = self.candidate_histograms(occurrence_id)
        candidate_rows = {arm: [] for arm in self.ARMS}
        mixture_rows = {arm: [] for arm in self.ARMS}
        prefix = 0
        for bit_index, parent in enumerate(parents):
            if not 0 < parent < PROBABILITY_SCALE:
                raise ValueError("invalid parent probability")
            truth_bit = (truth >> (7 - bit_index)) & 1
            candidates: dict[str, int | None] = {}
            for arm in self.ARMS:
                histogram = histograms[arm]
                candidates[arm] = (
                    None if histogram is None
                    else conditional_p1(histogram, prefix, bit_index)
                )
                candidate = candidates[arm]
                candidate_rows[arm].append(parent if candidate is None else candidate)
            e_weight = self.mixtures["E"].parent_weight
            for arm in self.MIXTURE_ARMS:
                candidate = candidates[arm]
                mixture_rows[arm].append(self.mixtures[arm].predict(parent, candidate))
            n_candidate = candidates["N"]
            mixture_rows["N"].append(
                parent if n_candidate is None
                else mixture_p1(e_weight, parent, n_candidate)
            )
            for arm in self.MIXTURE_ARMS:
                self.mixtures[arm].observe(
                    parent, candidates[arm], truth_bit
                )
            prefix = (prefix << 1) | truth_bit
        return {
            "P": parents,
            "K": parents,
            **{f"candidate_{arm}": tuple(values) for arm, values in candidate_rows.items()},
            **{f"mixture_{arm}": tuple(values) for arm, values in mixture_rows.items()},
        }

    def commit_byte(self, occurrence_id: tuple[int, ...], truth: int) -> None:
        occurrence = self.occurrences[occurrence_id]
        if occurrence.total_commits < MAX_VALUE_BYTES:
            for transducer in occurrence.transducers.values():
                transducer.observe(truth)
        occurrence.total_commits += 1
        if len(occurrence.current) < MAX_VALUE_BYTES:
            occurrence.current.append(truth)
        else:
            occurrence.overflow = True
        self._maybe_finalize(occurrence_id)

    def exit(self, occurrence_id: tuple[int, ...], expected_commits: int) -> None:
        occurrence = self.occurrences[occurrence_id]
        if occurrence.closed or expected_commits < occurrence.total_commits:
            raise ValueError("invalid field exit")
        occurrence.closed = True
        occurrence.expected_commits = expected_commits
        self._maybe_finalize(occurrence_id)

    def _maybe_finalize(self, occurrence_id: tuple[int, ...]) -> None:
        occurrence = self.occurrences[occurrence_id]
        if not occurrence.closed or occurrence.expected_commits is None:
            return
        observed = occurrence.total_commits
        if observed < occurrence.expected_commits:
            return
        if observed != occurrence.expected_commits:
            raise ValueError("field commit count exceeded exit ordinal")
        if occurrence.current and not occurrence.overflow:
            value = bytes(occurrence.current)
            self.route_bank.put(occurrence.route, value)
            self.random_bank.put(occurrence.random_bucket, value)
            self.last_completed_route = occurrence.route
        del self.occurrences[occurrence_id]

    def state_digest(self) -> str:
        digest = hashlib.sha256()
        digest.update(b"HARM-DELTA-Q0-V1\0")
        for bank_name, bank in ((b"E", self.route_bank), (b"R", self.random_bank)):
            digest.update(bank_name)
            for index, slot in enumerate(bank.slots):
                if slot is None:
                    continue
                digest.update(struct.pack("<I", index))
                if isinstance(slot.tag, RouteId):
                    digest.update(b"Q")
                    digest.update(struct.pack(
                        "<4Q", slot.tag.route_lo, slot.tag.route_hi,
                        slot.tag.witness_lo, slot.tag.witness_hi
                    ))
                else:
                    digest.update(b"B")
                    digest.update(struct.pack("<Q", slot.tag))
                digest.update(struct.pack("<H", len(slot.value)))
                digest.update(slot.value)
        digest.update(b"S")
        if self.last_completed_route is not None:
            digest.update(struct.pack(
                "<4Q", self.last_completed_route.route_lo,
                self.last_completed_route.route_hi,
                self.last_completed_route.witness_lo,
                self.last_completed_route.witness_hi,
            ))
        for arm in self.MIXTURE_ARMS:
            mixture = self.mixtures[arm]
            digest.update(arm.encode("ascii"))
            digest.update(struct.pack("<QQ", mixture.parent_weight, mixture.awake_updates))
        for occurrence_id in sorted(self.occurrences):
            occurrence = self.occurrences[occurrence_id]
            digest.update(struct.pack("<I", len(occurrence_id)))
            for value in occurrence_id:
                digest.update(struct.pack("<Q", value))
            digest.update(struct.pack(
                "<4Q", occurrence.route.route_lo, occurrence.route.route_hi,
                occurrence.route.witness_lo, occurrence.route.witness_hi
            ))
            digest.update(struct.pack(
                "<QQ??Q", occurrence.random_bucket, occurrence.total_commits,
                occurrence.overflow, occurrence.closed,
                occurrence.expected_commits or 0
            ))
            digest.update(bytes(occurrence.current))
            for arm in sorted(occurrence.transducers):
                transducer = occurrence.transducers[arm]
                digest.update(arm.encode("ascii"))
                digest.update(
                    b"E" if isinstance(transducer, EditTransducer) else b"L"
                )
                digest.update(struct.pack("<H", transducer.position))
                digest.update(struct.pack("<H", len(transducer.donor)))
                digest.update(transducer.donor)
                if isinstance(transducer, EditTransducer):
                    for (offset, mode), weight in sorted(
                        transducer.weights.items(),
                        key=lambda row: (row[0][0], MODE_ORDER[row[0][1]]),
                    ):
                        digest.update(struct.pack("<bBQ", offset, MODE_ORDER[mode], weight))
        return digest.hexdigest()
