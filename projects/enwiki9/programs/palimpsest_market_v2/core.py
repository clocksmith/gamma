#!/usr/bin/env python3
"""Exact source-only core for the dormant PALIMPSEST-MARKET-v2 shadow.

The model consumes decoder-visible route callbacks and immutable parent
probabilities.  It does not parse a corpus, write parent state, or authorize a
native codec.  Population binding and resource/accounting receipts remain a
separate dependency-gated replay.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re
import struct
from typing import Iterable, Sequence


PROBABILITY_SCALE = 1 << 16
POSTERIOR_SCALE = 1 << 63
ALIGNMENT_SCALE = 1 << 30
MAX_VALUE_BYTES = 512
RESERVOIR_DEPTH = 8
TABLE_SLOTS = 4096
CONTROL_POOL_RECORDS = 4096
MAX_ACTIVE_OCCURRENCES = 16
DRIFT = 8
MASK64 = (1 << 64) - 1

ARMS = ("A", "M", "H", "T", "X", "C", "G")
CODED_ARMS = ("P", "K") + ARMS
CONTENT_TYPES = ("numeric", "delimited", "token", "atomic")
TYPED_KERNELS = (
    "numeric_affine",
    "delimiter_substitution",
    "token_alignment",
    "prefix_suffix_grafting",
)
LEVEL_PRIORS = {"exact": 8, "shape": 5, "type": 3, "physical": 8}
AGE_RANK_PRIORS = (128, 64, 32, 16, 8, 4, 2, 1)
KERNEL_PRIORS = {"generic_edit": 3, "typed": 1}
DELIMITERS = frozenset(b":/|,;=_-.")

MODES = ("M", "X", "I", "D")
MODE_ORDER = {mode: ordinal for ordinal, mode in enumerate(MODES)}
OFFSET_STEP = {"M": 0, "X": 0, "I": -1, "D": 1}
TRANSITIONS = {
    "M": {"M": 224, "X": 16, "I": 8, "D": 8},
    "X": {"M": 128, "X": 96, "I": 16, "D": 16},
    "I": {"M": 96, "X": 16, "I": 136, "D": 8},
    "D": {"M": 96, "X": 16, "I": 8, "D": 136},
}
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


def _round_ratio(numerator: int, denominator: int, scale: int) -> int:
    if numerator <= 0 or denominator <= 0 or numerator >= denominator:
        raise ValueError("invalid probability ratio")
    quotient, remainder = divmod(numerator * scale, denominator)
    if remainder * 2 >= denominator:
        quotient += 1
    return max(1, min(scale - 1, quotient))


def _weighted_probability(weighted_counts: int, total_weight: int) -> int:
    return _round_ratio(
        weighted_counts,
        total_weight * PROBABILITY_SCALE,
        PROBABILITY_SCALE,
    )


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
    return _round_ratio(
        parent_mass,
        parent_mass + candidate_mass,
        POSTERIOR_SCALE,
    )


def _normalize_vector(values: Sequence[int], scale: int) -> list[int]:
    if not values or any(value < 0 for value in values) or not any(values):
        raise ValueError("invalid weight vector")
    total = sum(values)
    rows: list[list[int]] = []
    assigned = 0
    for index, value in enumerate(values):
        quotient, remainder = divmod(value * scale, total)
        rows.append([quotient, remainder, index])
        assigned += quotient
    missing = scale - assigned
    rows.sort(key=lambda row: (-row[1], row[2]))
    result = [0] * len(values)
    for quotient, _, index in rows:
        result[index] = quotient
    for _, _, index in rows[:missing]:
        result[index] += 1
    if sum(result) != scale:
        raise AssertionError("weight normalization drift")
    return result


def _normalize_alignment(
    weights: dict[tuple[int, str], int],
) -> dict[tuple[int, str], int]:
    positive = {key: value for key, value in weights.items() if value > 0}
    if not positive:
        return {}
    keys = sorted(positive, key=lambda item: (item[0], MODE_ORDER[item[1]]))
    normalized = _normalize_vector([positive[key] for key in keys], ALIGNMENT_SCALE)
    return {key: value for key, value in zip(keys, normalized) if value}


def conditional_p1(histogram: tuple[int, ...], prefix: int, bit_index: int) -> int:
    if len(histogram) != 256 or not 0 <= bit_index < 8:
        raise ValueError("invalid byte distribution query")
    if not 0 <= prefix < (1 << bit_index):
        raise ValueError("invalid decoded prefix")
    width = 1 << (8 - bit_index)
    start = prefix * width
    middle = start + width // 2
    end = start + width
    return _round_ratio(
        sum(histogram[middle:end]),
        sum(histogram[start:end]),
        PROBABILITY_SCALE,
    )


def _point_histogram(value: int) -> tuple[int, ...]:
    donor_mass, other_mass = EMISSIONS["M"]
    result = [other_mass] * 256
    result[value] = donor_mass
    return tuple(result)


class EditTransducer:
    """The frozen HARM-Delta generic integer pair-HMM."""

    kernel_name = "generic_edit"

    def __init__(self, donor: bytes):
        if not donor or len(donor) > MAX_VALUE_BYTES:
            raise ValueError("donor outside frozen value bound")
        self.donor = bytes(donor)
        self.position = 0
        self.weights = {(0, "M"): ALIGNMENT_SCALE}

    @staticmethod
    def _transition_mass(weight: int, mass: int) -> int:
        quotient, remainder = divmod(weight * mass, 256)
        return quotient + (1 if remainder * 2 >= 256 else 0)

    def _closed_states(self) -> dict[tuple[int, str], int]:
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
                    paths.append(
                        (next_offset, next_mode, self.donor[donor_index], transition)
                    )
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
        advanced: dict[tuple[int, str], int] = {}
        for next_offset, mode, donor, weight in self._emitting_paths():
            donor_mass, other_mass = EMISSIONS[mode]
            likelihood = donor_mass if donor == truth else other_mass
            key = (next_offset, mode)
            advanced[key] = advanced.get(key, 0) + weight * likelihood
        self.position += 1
        self.weights = _normalize_alignment(advanced)

    def digest_bytes(self) -> bytes:
        result = bytearray(struct.pack("<H", self.position))
        for (offset, mode), weight in sorted(
            self.weights.items(), key=lambda row: (row[0][0], MODE_ORDER[row[0][1]])
        ):
            result.extend(struct.pack("<bBQ", offset, MODE_ORDER[mode], weight))
        return bytes(result)


class _VariantKernel:
    kernel_name = "variant"

    def __init__(self, donor: bytes, variants: Sequence[bytes]):
        unique: list[bytes] = []
        for value in variants:
            if value and value not in unique:
                unique.append(bytes(value))
        if not unique:
            unique = [bytes(donor)]
        self.donor = bytes(donor)
        self.variants = tuple(unique)
        self.weights = _normalize_vector([1] * len(unique), ALIGNMENT_SCALE)
        self.position = 0

    def histogram(self) -> tuple[int, ...] | None:
        active = [
            index
            for index, value in enumerate(self.variants)
            if self.position < len(value) and self.weights[index]
        ]
        if not active:
            return None
        baseline = sum(self.weights[index] for index in active) * EMISSIONS["M"][1]
        adjustments = [0] * 256
        delta = EMISSIONS["M"][0] - EMISSIONS["M"][1]
        for index in active:
            adjustments[self.variants[index][self.position]] += self.weights[index] * delta
        return tuple(baseline + adjustment for adjustment in adjustments)

    def observe(self, truth: int) -> None:
        histogram = self.histogram()
        if histogram is not None:
            market_truth = _round_ratio(
                histogram[truth], sum(histogram), PROBABILITY_SCALE
            )
            raw = []
            for weight, value in zip(self.weights, self.variants):
                likelihood = (
                    EMISSIONS["M"][0]
                    if self.position < len(value) and value[self.position] == truth
                    else EMISSIONS["M"][1]
                    if self.position < len(value)
                    else market_truth
                )
                raw.append(weight * likelihood)
            self.weights = _normalize_vector(raw, ALIGNMENT_SCALE)
        self.position += 1

    def digest_bytes(self) -> bytes:
        return struct.pack("<H", self.position) + b"".join(
            struct.pack("<Q", weight) for weight in self.weights
        )


class NumericAffineKernel(_VariantKernel):
    kernel_name = "numeric_affine"

    def __init__(self, donor: bytes):
        if re.fullmatch(rb"[+-]?[0-9]+", donor) is None:
            raise ValueError("numeric affine donor is not a signed integer")
        value = int(donor.decode("ascii"))
        transforms = [(1, delta) for delta in (-1000, -100, -10, -1, 0, 1, 10, 100, 1000)]
        transforms.extend(((-1, 0), (2, 0)))
        variants = [str(scale * value + delta).encode("ascii") for scale, delta in transforms]
        super().__init__(donor, variants)


class DelimiterSubstitutionKernel:
    kernel_name = "delimiter_substitution"

    def __init__(self, donor: bytes):
        self.donor = bytes(donor)
        self.position = 0

    def histogram(self) -> tuple[int, ...] | None:
        if self.position >= len(self.donor):
            return None
        value = self.donor[self.position]
        if value in DELIMITERS:
            return _point_histogram(value)
        result = [1] * 256
        for candidate in range(256):
            if chr(candidate).isascii() and chr(candidate).isalnum():
                result[candidate] += 1024
        return tuple(result)

    def observe(self, truth: int) -> None:
        self.position += 1

    def digest_bytes(self) -> bytes:
        return struct.pack("<H", self.position)


class TokenAlignmentKernel:
    kernel_name = "token_alignment"

    def __init__(self, donor: bytes):
        self.donor = bytes(donor)
        self.tokens = tuple(match.group(0) for match in re.finditer(rb"[A-Za-z0-9]+", donor))
        if not self.tokens:
            raise ValueError("token alignment donor has no tokens")
        self.token_ordinal = 0
        self.token_offset = 0
        self.in_token = False

    def histogram(self) -> tuple[int, ...] | None:
        result = [128] * 256
        active = False
        for drift, mass in ((-2, 1), (-1, 2), (0, 4), (1, 2), (2, 1)):
            token_index = self.token_ordinal + drift
            if not 0 <= token_index < len(self.tokens):
                continue
            token = self.tokens[token_index]
            offset = self.token_offset if self.in_token else 0
            if offset < len(token):
                result[token[offset]] += mass * 4096
                active = True
        return tuple(result) if active else None

    def observe(self, truth: int) -> None:
        alphanumeric = chr(truth).isascii() and chr(truth).isalnum()
        if alphanumeric:
            if self.in_token:
                self.token_offset += 1
            else:
                self.in_token = True
                self.token_offset = 1
        elif self.in_token:
            self.token_ordinal += 1
            self.token_offset = 0
            self.in_token = False

    def digest_bytes(self) -> bytes:
        return struct.pack(
            "<HH?", self.token_ordinal, self.token_offset, self.in_token
        )


class PrefixSuffixGraftingKernel(_VariantKernel):
    kernel_name = "prefix_suffix_grafting"

    def __init__(self, donor: bytes):
        boundaries = [0]
        for index in range(1, len(donor)):
            if donor[index - 1] in DELIMITERS or chr(donor[index]).isspace():
                boundaries.append(index)
        suffixes = [donor[index:] for index in boundaries[-4:]]
        super().__init__(donor, [donor, *suffixes])


def classify_value(value: bytes) -> str:
    if re.fullmatch(rb"[+-]?[0-9]+", value):
        return "numeric"
    if sum(byte in DELIMITERS for byte in value) >= 2:
        return "delimited"
    if len(re.findall(rb"[A-Za-z0-9]+", value)) >= 2 or any(
        chr(byte).isspace() for byte in value
    ):
        return "token"
    return "atomic"


def infer_prefix_type(prefix: bytes) -> str | None:
    if not prefix:
        return None
    if re.fullmatch(rb"[+-]?[0-9]+", prefix):
        return "numeric"
    if sum(byte in DELIMITERS for byte in prefix) >= 2:
        return "delimited"
    if len(re.findall(rb"[A-Za-z0-9]+", prefix)) >= 2 or any(
        chr(byte).isspace() for byte in prefix
    ):
        return "token"
    return "atomic" if len(prefix) >= 8 else None


def typed_kernel_name(content_type: str) -> str:
    return {
        "numeric": "numeric_affine",
        "delimited": "delimiter_substitution",
        "token": "token_alignment",
        "atomic": "prefix_suffix_grafting",
    }[content_type]


def _make_kernel(name: str, donor: bytes):
    constructors = {
        "generic_edit": EditTransducer,
        "numeric_affine": NumericAffineKernel,
        "delimiter_substitution": DelimiterSubstitutionKernel,
        "token_alignment": TokenAlignmentKernel,
        "prefix_suffix_grafting": PrefixSuffixGraftingKernel,
    }
    return constructors[name](donor)


@dataclass(frozen=True)
class RouteId:
    route_lo: int
    route_hi: int
    witness_lo: int
    witness_hi: int

    def __post_init__(self) -> None:
        if any(
            not 0 <= value <= MASK64
            for value in (self.route_lo, self.route_hi, self.witness_lo, self.witness_hi)
        ):
            raise ValueError("route identity is not four uint64 values")

    def seed(self) -> int:
        value = self.route_lo ^ splitmix64(self.route_hi)
        value ^= splitmix64(self.witness_lo)
        value ^= splitmix64(self.witness_hi)
        return splitmix64(value)


@dataclass(frozen=True)
class MarketRoute:
    exact: RouteId
    shape_id: int

    def __post_init__(self) -> None:
        if not 0 <= self.shape_id <= MASK64:
            raise ValueError("route shape is not uint64")


@dataclass(frozen=True)
class DonorRecord:
    serial: int
    completion_coordinate: int
    route: RouteId
    shape_id: int
    content_type: str
    value: bytes


@dataclass
class _ReservoirSlot:
    tag: RouteId | int | str
    records: list[DonorRecord]


def _tag_seed(tag: RouteId | int | str) -> int:
    if isinstance(tag, RouteId):
        return tag.seed()
    if isinstance(tag, int):
        return splitmix64(tag)
    value = 0
    for byte in tag.encode("ascii"):
        value = splitmix64(value ^ byte)
    return value


class ReservoirTable:
    def __init__(self) -> None:
        self.slots: list[_ReservoirSlot | None] = [None] * TABLE_SLOTS

    def _index(self, tag: RouteId | int | str) -> int:
        return _tag_seed(tag) & (TABLE_SLOTS - 1)

    def get(self, tag: RouteId | int | str) -> tuple[DonorRecord, ...]:
        slot = self.slots[self._index(tag)]
        return tuple(slot.records) if slot is not None and slot.tag == tag else ()

    def put(self, tag: RouteId | int | str, record: DonorRecord) -> None:
        index = self._index(tag)
        slot = self.slots[index]
        records = [] if slot is None or slot.tag != tag else list(slot.records)
        records.insert(0, record)
        self.slots[index] = _ReservoirSlot(tag, records[:RESERVOIR_DEPTH])


def _length_bucket(length: int) -> int:
    if length <= 0:
        raise ValueError("empty donor has no length bucket")
    return (length - 1).bit_length()


def _age_bucket(age: int) -> int:
    if age <= 0:
        raise ValueError("noncausal donor age")
    return age.bit_length() - 1


@dataclass(frozen=True)
class DonorChoice:
    level: str
    rank: int
    age: int
    record: DonorRecord


@dataclass(frozen=True)
class PhysicalDonor:
    value: bytes
    age: int


@dataclass
class MarketLeaf:
    level: str
    rank: int
    record: DonorRecord
    kernel_name: str
    kernel: object

    def eligible(self, current_type: str | None) -> bool:
        return self.level != "type" or current_type == self.record.content_type


class BayesianMarket:
    """Per-occurrence hierarchical sleeping market over donor kernels."""

    def __init__(self, leaves: Sequence[MarketLeaf]):
        self.leaves = list(leaves)
        raw_priors = []
        for leaf in self.leaves:
            level_prior = LEVEL_PRIORS[leaf.level]
            age_prior = AGE_RANK_PRIORS[min(leaf.rank, RESERVOIR_DEPTH - 1)]
            kernel_prior = KERNEL_PRIORS[
                "generic_edit" if leaf.kernel_name == "generic_edit" else "typed"
            ]
            raw_priors.append(level_prior * age_prior * kernel_prior)
        self.weights = (
            _normalize_vector(raw_priors, POSTERIOR_SCALE) if raw_priors else []
        )

    def predict(
        self, prefix: bytes, bit_prefix: int, bit_index: int
    ) -> tuple[int | None, dict[int, int]]:
        current_type = infer_prefix_type(prefix)
        probabilities: dict[int, int] = {}
        weighted = 0
        total_weight = 0
        for index, (leaf, weight) in enumerate(zip(self.leaves, self.weights)):
            if not weight or not leaf.eligible(current_type):
                continue
            histogram = leaf.kernel.histogram()
            if histogram is None:
                continue
            probability = conditional_p1(histogram, bit_prefix, bit_index)
            probabilities[index] = probability
            weighted += weight * probability
            total_weight += weight
        if not probabilities:
            return None, {}
        return _weighted_probability(weighted, total_weight), probabilities

    def observe_bit(
        self,
        candidate_p1: int | None,
        probabilities: dict[int, int],
        truth_bit: int,
    ) -> None:
        if candidate_p1 is None:
            return
        market_truth = (
            candidate_p1 if truth_bit else PROBABILITY_SCALE - candidate_p1
        )
        raw = []
        for index, weight in enumerate(self.weights):
            probability = probabilities.get(index)
            likelihood = (
                market_truth
                if probability is None
                else probability if truth_bit else PROBABILITY_SCALE - probability
            )
            raw.append(weight * likelihood)
        self.weights = _normalize_vector(raw, POSTERIOR_SCALE)

    def observe_byte(self, truth: int) -> None:
        for leaf in self.leaves:
            leaf.kernel.observe(truth)

    def digest_bytes(self) -> bytes:
        result = bytearray(struct.pack("<H", len(self.leaves)))
        for leaf, weight in zip(self.leaves, self.weights):
            result.extend(leaf.level.encode("ascii") + b"\0")
            result.extend(leaf.kernel_name.encode("ascii") + b"\0")
            result.extend(struct.pack("<BqQ", leaf.rank, leaf.record.serial, weight))
            result.extend(leaf.kernel.digest_bytes())
        return bytes(result)


@dataclass
class SleepingParentMixture:
    parent_weight: int = POSTERIOR_SCALE // 2
    awake_updates: int = 0

    def predict(self, parent_p1: int, candidate_p1: int | None) -> int:
        return (
            parent_p1
            if candidate_p1 is None
            else mixture_p1(self.parent_weight, parent_p1, candidate_p1)
        )

    def observe(
        self, parent_p1: int, candidate_p1: int | None, truth_bit: int
    ) -> None:
        if candidate_p1 is None:
            return
        self.parent_weight = posterior_parent_weight(
            self.parent_weight, parent_p1, candidate_p1, truth_bit
        )
        self.awake_updates += 1


@dataclass
class Occurrence:
    route: MarketRoute
    entry_coordinate: int
    markets: dict[str, BayesianMarket]
    controls_admissible: dict[str, bool]
    current: bytearray = field(default_factory=bytearray)
    total_commits: int = 0
    overflow: bool = False
    closed: bool = False
    expected_commits: int | None = None
    completion_coordinate: int | None = None


class PalimpsestMarket:
    def __init__(self) -> None:
        self.exact_bank = ReservoirTable()
        self.shape_bank = ReservoirTable()
        self.type_bank = ReservoirTable()
        self.control_pool: list[DonorRecord] = []
        self.completed_serial = 0
        self.occurrences: dict[tuple[int, ...], Occurrence] = {}
        self.outer = {arm: SleepingParentMixture() for arm in ARMS}

    def _choices(
        self, route: MarketRoute, coordinate: int
    ) -> tuple[list[DonorChoice], list[DonorChoice], list[DonorChoice]]:
        seen: set[int] = set()

        def add(level: str, records: Sequence[DonorRecord]) -> list[DonorChoice]:
            selected = []
            for rank, record in enumerate(records[:RESERVOIR_DEPTH]):
                if record.serial in seen:
                    continue
                age = coordinate - record.completion_coordinate
                if age <= 0:
                    raise ValueError("reservoir exposed a noncausal donor")
                seen.add(record.serial)
                selected.append(DonorChoice(level, rank, age, record))
            return selected

        exact = add("exact", self.exact_bank.get(route.exact))
        shape = add("shape", self.shape_bank.get(route.shape_id))
        typed: list[DonorChoice] = []
        for content_type in CONTENT_TYPES:
            typed.extend(add("type", self.type_bank.get(content_type)))
        return exact, shape, typed

    @staticmethod
    def _random_wrong_kernels(correct: str, seed: int) -> list[str]:
        alternatives = [name for name in TYPED_KERNELS if name != correct]
        rotation = splitmix64(seed) % len(alternatives)
        return alternatives[rotation:] + alternatives[:rotation]

    def _leaves(
        self,
        choices: Sequence[DonorChoice],
        *,
        typed: bool,
        randomized_kernels: bool = False,
    ) -> list[MarketLeaf]:
        leaves: list[MarketLeaf] = []
        for choice in choices:
            donor = choice.record.value
            leaves.append(
                MarketLeaf(
                    choice.level,
                    choice.rank,
                    choice.record,
                    "generic_edit",
                    EditTransducer(donor),
                )
            )
            if typed:
                name = typed_kernel_name(choice.record.content_type)
                if randomized_kernels:
                    names = self._random_wrong_kernels(
                        name,
                        choice.record.route.seed()
                        ^ splitmix64(choice.record.serial)
                        ^ splitmix64(choice.rank),
                    )
                    for name in names:
                        try:
                            kernel = _make_kernel(name, donor)
                            break
                        except ValueError:
                            continue
                    else:
                        raise AssertionError("no valid randomized typed kernel")
                else:
                    kernel = _make_kernel(name, donor)
                leaves.append(
                    MarketLeaf(
                        choice.level,
                        choice.rank,
                        choice.record,
                        name,
                        kernel,
                    )
                )
        return leaves

    def _permuted_choices(
        self,
        route: MarketRoute,
        coordinate: int,
        targets: Sequence[DonorChoice],
    ) -> tuple[list[DonorChoice], bool]:
        selected: list[DonorChoice] = []
        for ordinal, target in enumerate(targets):
            candidates = [
                record
                for record in self.control_pool
                if record.route != route.exact
                and record.serial != target.record.serial
                and _age_bucket(coordinate - record.completion_coordinate)
                == _age_bucket(target.age)
                and _length_bucket(len(record.value))
                == _length_bucket(len(target.record.value))
            ]
            if not candidates:
                return selected, False
            record = min(
                candidates,
                key=lambda value: splitmix64(
                    route.exact.seed()
                    ^ splitmix64(target.record.serial)
                    ^ splitmix64(value.serial)
                    ^ ordinal
                ),
            )
            selected.append(
                DonorChoice(
                    target.level,
                    target.rank,
                    coordinate - record.completion_coordinate,
                    record,
                )
            )
        return selected, len(selected) == len(targets)

    @staticmethod
    def _physical_choices(
        route: MarketRoute,
        coordinate: int,
        targets: Sequence[DonorChoice],
        physical: Sequence[PhysicalDonor] | None,
    ) -> tuple[list[DonorChoice], bool]:
        if physical is None or len(physical) != len(targets):
            return [], False
        choices = []
        for ordinal, (target, donor) in enumerate(zip(targets, physical)):
            if (
                donor.age != target.age
                or donor.age <= 0
                or not donor.value
                or len(donor.value) > MAX_VALUE_BYTES
                or _length_bucket(len(donor.value))
                != _length_bucket(len(target.record.value))
                or classify_value(donor.value) != target.record.content_type
            ):
                return [], False
            record = DonorRecord(
                serial=-(ordinal + 1),
                completion_coordinate=coordinate - donor.age,
                route=RouteId(
                    splitmix64(route.exact.seed() ^ ordinal),
                    splitmix64(route.shape_id ^ ordinal),
                    splitmix64(ordinal),
                    splitmix64(ordinal + 1),
                ),
                shape_id=route.shape_id,
                content_type=target.record.content_type,
                value=bytes(donor.value),
            )
            choices.append(
                DonorChoice(target.level, target.rank, donor.age, record)
            )
        return choices, True

    def preview_h_choices(
        self, route: MarketRoute, coordinate: int
    ) -> tuple[DonorChoice, ...]:
        exact, shape, typed = self._choices(route, coordinate)
        return tuple([*exact, *shape, *typed])

    def enter(
        self,
        occurrence_id: tuple[int, ...],
        route: MarketRoute,
        coordinate: int,
        physical_donors: Sequence[PhysicalDonor] | None = None,
    ) -> None:
        if occurrence_id in self.occurrences:
            raise ValueError("duplicate active occurrence")
        if len(self.occurrences) >= MAX_ACTIVE_OCCURRENCES:
            raise MemoryError("active occurrence ceiling exceeded")
        if coordinate < 0:
            raise ValueError("negative entry coordinate")
        exact, shape, typed = self._choices(route, coordinate)
        h_choices = [*exact, *shape, *typed]
        x_choices, x_admissible = self._permuted_choices(
            route, coordinate, h_choices
        )
        g_choices, g_admissible = self._physical_choices(
            route, coordinate, h_choices, physical_donors
        )
        markets = {
            "A": BayesianMarket(self._leaves(exact[:1], typed=False)),
            "M": BayesianMarket(self._leaves(exact, typed=False)),
            "H": BayesianMarket(self._leaves(h_choices, typed=False)),
            "T": BayesianMarket(self._leaves(h_choices, typed=True)),
            "X": BayesianMarket(
                self._leaves(x_choices, typed=True) if x_admissible else []
            ),
            "C": BayesianMarket(
                self._leaves(h_choices, typed=True, randomized_kernels=True)
            ),
            "G": BayesianMarket(
                self._leaves(g_choices, typed=True) if g_admissible else []
            ),
        }
        self.occurrences[occurrence_id] = Occurrence(
            route=route,
            entry_coordinate=coordinate,
            markets=markets,
            controls_admissible={"X": x_admissible, "G": g_admissible},
        )

    def score_byte(
        self,
        occurrence_id: tuple[int, ...],
        parent_p1: Iterable[int],
        truth: int,
    ) -> dict[str, tuple[int, ...]]:
        parents = tuple(parent_p1)
        if len(parents) != 8 or any(
            not 0 < probability < PROBABILITY_SCALE for probability in parents
        ):
            raise ValueError("eight valid parent probabilities are required")
        if not 0 <= truth <= 255:
            raise ValueError("truth is not a byte")
        occurrence = self.occurrences[occurrence_id]
        candidate_rows = {arm: [] for arm in ARMS}
        mixture_rows = {arm: [] for arm in ARMS}
        bit_prefix = 0
        byte_prefix = bytes(occurrence.current)
        for bit_index, parent in enumerate(parents):
            truth_bit = (truth >> (7 - bit_index)) & 1
            predictions: dict[str, tuple[int | None, dict[int, int]]] = {}
            for arm in ARMS:
                prediction = occurrence.markets[arm].predict(
                    byte_prefix, bit_prefix, bit_index
                )
                predictions[arm] = prediction
                candidate = prediction[0]
                candidate_rows[arm].append(parent if candidate is None else candidate)
                mixture_rows[arm].append(self.outer[arm].predict(parent, candidate))
            for arm in ARMS:
                candidate, leaf_probabilities = predictions[arm]
                occurrence.markets[arm].observe_bit(
                    candidate, leaf_probabilities, truth_bit
                )
                self.outer[arm].observe(parent, candidate, truth_bit)
            bit_prefix = (bit_prefix << 1) | truth_bit
        return {
            "P": parents,
            "K": parents,
            **{
                f"candidate_{arm}": tuple(values)
                for arm, values in candidate_rows.items()
            },
            **{
                f"mixture_{arm}": tuple(values)
                for arm, values in mixture_rows.items()
            },
        }

    def commit_byte(self, occurrence_id: tuple[int, ...], truth: int) -> None:
        occurrence = self.occurrences[occurrence_id]
        if occurrence.total_commits < MAX_VALUE_BYTES:
            for market in occurrence.markets.values():
                market.observe_byte(truth)
            occurrence.current.append(truth)
        else:
            occurrence.overflow = True
        occurrence.total_commits += 1
        self._maybe_finalize(occurrence_id)

    def exit(
        self,
        occurrence_id: tuple[int, ...],
        expected_commits: int,
        completion_coordinate: int,
    ) -> None:
        occurrence = self.occurrences[occurrence_id]
        if (
            occurrence.closed
            or expected_commits < occurrence.total_commits
            or completion_coordinate <= occurrence.entry_coordinate
        ):
            raise ValueError("invalid field exit")
        occurrence.closed = True
        occurrence.expected_commits = expected_commits
        occurrence.completion_coordinate = completion_coordinate
        self._maybe_finalize(occurrence_id)

    def _maybe_finalize(self, occurrence_id: tuple[int, ...]) -> None:
        occurrence = self.occurrences[occurrence_id]
        if not occurrence.closed or occurrence.expected_commits is None:
            return
        if occurrence.total_commits < occurrence.expected_commits:
            return
        if occurrence.total_commits != occurrence.expected_commits:
            raise ValueError("field commit count exceeded exit ordinal")
        if occurrence.current and not occurrence.overflow:
            assert occurrence.completion_coordinate is not None
            record = DonorRecord(
                serial=self.completed_serial,
                completion_coordinate=occurrence.completion_coordinate,
                route=occurrence.route.exact,
                shape_id=occurrence.route.shape_id,
                content_type=classify_value(bytes(occurrence.current)),
                value=bytes(occurrence.current),
            )
            self.completed_serial += 1
            self.exact_bank.put(record.route, record)
            self.shape_bank.put(record.shape_id, record)
            self.type_bank.put(record.content_type, record)
            self.control_pool.insert(0, record)
            del self.control_pool[CONTROL_POOL_RECORDS:]
        del self.occurrences[occurrence_id]

    def state_digest(self) -> str:
        digest = hashlib.sha256(b"PALIMPSEST-MARKET-V2\0")
        digest.update(struct.pack("<Q", self.completed_serial))
        for name, table in (
            (b"E", self.exact_bank),
            (b"H", self.shape_bank),
            (b"T", self.type_bank),
        ):
            digest.update(name)
            for index, slot in enumerate(table.slots):
                if slot is None:
                    continue
                digest.update(struct.pack("<I", index))
                for record in slot.records:
                    digest.update(struct.pack(
                        "<qQQH", record.serial, record.completion_coordinate,
                        record.shape_id, len(record.value)
                    ))
                    digest.update(record.value)
        for arm in ARMS:
            mixture = self.outer[arm]
            digest.update(arm.encode("ascii"))
            digest.update(struct.pack(
                "<QQ", mixture.parent_weight, mixture.awake_updates
            ))
        for occurrence_id in sorted(self.occurrences):
            occurrence = self.occurrences[occurrence_id]
            digest.update(struct.pack("<H", len(occurrence_id)))
            for value in occurrence_id:
                digest.update(struct.pack("<Q", value))
            digest.update(bytes(occurrence.current))
            for arm in ARMS:
                digest.update(arm.encode("ascii"))
                digest.update(occurrence.markets[arm].digest_bytes())
        return digest.hexdigest()
