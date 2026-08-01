#!/usr/bin/env python3
"""Run the frozen opening-1M Typed Event Sleeping Bayes Q0 gate."""

from __future__ import annotations

import argparse
from collections import Counter, deque
from dataclasses import dataclass, field
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
from typing import Any, Iterable

import numpy as np

from causal_state_screen import WikiState
import paid_block_vector_codebook as parent_codec
from wrt_entity_trie_fx2_shadow import EntityObserver
from wrt_exact import (
    CAPITALIZED,
    END_UPPER,
    ESCAPE,
    TEXT_SEGMENT,
    UPPERCASE,
    WrtDecoderState,
    WrtEvent,
    parse_store,
    read_dictionary_words,
    token_index,
    wrt_byte_transform,
)


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "typed_event_sleeping_bayes_envelope_q0_v1"
CONTRACT = ROOT / "docs/typed_event_sleeping_bayes_q0_contract.md"
P1_MAGIC = b"CMX21P1\0"
PAGE_MAP_MAGIC = b"SIBMAP1\0"
PAGE_MAP_RECORD = struct.Struct("<QQQQ")
TOTAL = 1 << 16
POSTERIOR_SCALE = 1 << 24
MAX_KEYS = 50_000
CODES_PER_KEY = 32
MIN_SUPPORT = 4
MAX_CANDIDATES = 16
LITERAL_PRIOR = 65_536
SUFFIX_BYTES = 32
ENTITY_PREFIX_EVENTS = 8
PACKAGE_ALLOWANCE_BYTES = 98_304
GROSS_GATE_BPM = 3_000.0
NET_GATE_BPM = 2_100.0
ATTRIBUTION_GATE_BPM = 256.0
S1_BLOCK_BYTES = 65_536
VARIANTS = ("C0", "E0", "E1", "E2", "E3", "M0", "M1")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
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
        "sha256": sha256_file(resolved),
    }


def fnv32(data: bytes) -> int:
    value = 0x811C9DC5
    for byte in data:
        value ^= byte
        value = (value * 0x01000193) & 0xFFFFFFFF
    return value


def fnv64_codes(codes: Iterable[bytes]) -> int:
    value = 0xCBF29CE484222325
    for code in codes:
        value ^= len(code)
        value = (value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
        for byte in code:
            value ^= byte
            value = (value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return value


def fnv16_ints(values: Iterable[int]) -> int:
    raw = bytearray()
    for value in values:
        raw.extend(int(value).to_bytes(4, "little", signed=False))
    return fnv32(bytes(raw)) & 0xFFFF


def clamp_probability(value: int) -> int:
    return max(1, min(TOTAL - 1, int(value)))


def round_ratio(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("nonpositive probability denominator")
    return (numerator + denominator // 2) // denominator


def project_positive(weights: list[int], scale: int) -> list[int]:
    if not weights or any(weight <= 0 for weight in weights) or scale < len(weights):
        raise ValueError("invalid posterior projection")
    total = sum(weights)
    distributable = scale - len(weights)
    projected: list[int] = []
    remainders: list[int] = []
    for weight in weights:
        quotient, remainder = divmod(distributable * weight, total)
        projected.append(1 + quotient)
        remainders.append(remainder)
    missing = scale - sum(projected)
    order = sorted(range(len(weights)), key=lambda index: (-remainders[index], index))
    for index in order[:missing]:
        projected[index] += 1
    return projected


@dataclass(frozen=True)
class Page:
    index: int
    raw_start: int
    raw_end: int
    wrt_start: int
    wrt_end: int
    split: str


def read_pages(path: Path, wrt_bytes: int) -> list[Page]:
    data = path.read_bytes()
    if len(data) < 16 or data[:8] != PAGE_MAP_MAGIC:
        raise ValueError("invalid page map")
    count = struct.unpack_from("<Q", data, 8)[0]
    if len(data) != 16 + count * PAGE_MAP_RECORD.size:
        raise ValueError("page-map length mismatch")
    development_end = count * 3 // 5
    selection_end = count * 4 // 5
    pages: list[Page] = []
    previous_raw_end = 0
    previous_wrt_end = 0
    for index in range(count):
        raw_start, raw_end, row_start, row_end = PAGE_MAP_RECORD.unpack_from(
            data, 16 + index * PAGE_MAP_RECORD.size
        )
        if row_start % 8 or row_end % 8:
            raise ValueError("page map is not byte aligned")
        split = (
            "development"
            if index < development_end
            else "selection"
            if index < selection_end
            else "sealed_confirmation"
        )
        page = Page(index, raw_start, raw_end, row_start // 8, row_end // 8, split)
        if not 0 <= previous_raw_end <= raw_start < raw_end:
            raise ValueError("raw pages are not chronological")
        if not 0 <= previous_wrt_end <= page.wrt_start < page.wrt_end <= wrt_bytes:
            raise ValueError("WRT pages are not chronological")
        pages.append(page)
        previous_raw_end = raw_end
        previous_wrt_end = page.wrt_end
    return pages


def read_p1(path: Path, expected_rows: int) -> np.ndarray:
    raw = path.read_bytes()
    if len(raw) < 16 or raw[:8] != P1_MAGIC:
        raise ValueError("invalid endpoint428 P1 trace")
    rows = struct.unpack_from("<Q", raw, 8)[0]
    probabilities = np.frombuffer(raw, dtype="<u2", offset=16).copy()
    if rows != expected_rows or len(probabilities) != expected_rows:
        raise ValueError("P1 rows differ from WRT truth")
    if np.any(probabilities == 0):
        raise ValueError("P1 contains an illegal zero probability")
    return probabilities


@dataclass
class BoundedEventTable:
    counts: dict[tuple[Any, ...], Counter[bytes]] = field(default_factory=dict)
    order: deque[tuple[Any, ...]] = field(default_factory=deque)
    evicted_keys: int = 0
    rejected_codes: int = 0

    def update(self, keys: Iterable[tuple[Any, ...]], code: bytes) -> None:
        for key in keys:
            counter = self.counts.get(key)
            if counter is None:
                if len(self.counts) >= MAX_KEYS:
                    old = self.order.popleft()
                    del self.counts[old]
                    self.evicted_keys += 1
                counter = Counter()
                self.counts[key] = counter
                self.order.append(key)
            if code not in counter and len(counter) >= CODES_PER_KEY:
                self.rejected_codes += 1
                continue
            counter[code] += 1

    def candidates(self, keys: Iterable[tuple[Any, ...]]) -> dict[bytes, int]:
        aggregate: Counter[bytes] = Counter()
        for key in keys:
            counter = self.counts.get(key)
            if counter is not None:
                aggregate.update(counter)
        if sum(aggregate.values()) < MIN_SUPPORT:
            return {}
        ranked = sorted(aggregate.items(), key=lambda row: (-row[1], row[0]))
        return dict(ranked[:MAX_CANDIDATES])

    def receipt(self) -> dict[str, int]:
        code_bytes = 0
        code_entries = 0
        for counter in self.counts.values():
            for code in counter:
                code_entries += 1
                code_bytes += len(code)
        return {
            "keys": len(self.counts),
            "code_entries": code_entries,
            "code_bytes": code_bytes,
            "evicted_keys": self.evicted_keys,
            "rejected_codes": self.rejected_codes,
            "state_bytes_estimate": len(self.counts) * 32 + code_entries * 16 + code_bytes,
        }

    def digest(self) -> str:
        digest = hashlib.sha256()
        for key in sorted(self.counts, key=repr):
            digest.update(repr(key).encode("utf-8"))
            for code, count in sorted(self.counts[key].items()):
                digest.update(len(code).to_bytes(2, "little"))
                digest.update(code)
                digest.update(count.to_bytes(8, "little"))
        return digest.hexdigest()


@dataclass
class EventMixture:
    candidates: dict[bytes, int]
    literal_numerator: int = LITERAL_PRIOR
    literal_denominator: int = 1
    bit_index: int = 0

    def predict(self, base_p1: int) -> int:
        if not self.candidates:
            return base_p1
        total_weight = 0
        one_weight = 0
        for code, weight in self.candidates.items():
            if self.bit_index >= len(code) * 8:
                continue
            total_weight += weight
            bit = (code[self.bit_index // 8] >> (7 - (self.bit_index & 7))) & 1
            one_weight += weight * bit
        if total_weight == 0:
            return base_p1
        numerator = (
            self.literal_numerator * base_p1
            + one_weight * self.literal_denominator * TOTAL
        )
        denominator = self.literal_numerator + total_weight * self.literal_denominator
        return clamp_probability(round_ratio(numerator, denominator))

    def observe(self, bit: int, base_p1: int) -> None:
        likelihood = base_p1 if bit else TOTAL - base_p1
        self.literal_numerator *= likelihood
        self.literal_denominator *= TOTAL
        kept: dict[bytes, int] = {}
        for code, weight in self.candidates.items():
            if self.bit_index >= len(code) * 8:
                continue
            candidate_bit = (
                code[self.bit_index // 8] >> (7 - (self.bit_index & 7))
            ) & 1
            if candidate_bit == bit:
                kept[code] = weight
        self.candidates = kept
        self.bit_index += 1


@dataclass
class OuterBayes:
    ideal: bool
    bit_count: int = 0
    float_weights: list[float] = field(
        default_factory=lambda: [65535.0 / 65536.0, 1.0 / 65536.0]
    )
    fixed_weights: list[int] = field(
        default_factory=lambda: [POSTERIOR_SCALE - 256, 256]
    )

    def predict(self, base_p1: int, event_p1: int) -> int:
        if self.ideal:
            value = self.float_weights[0] * base_p1 + self.float_weights[1] * event_p1
            return clamp_probability(int(math.floor(value + 0.5)))
        numerator = self.fixed_weights[0] * base_p1 + self.fixed_weights[1] * event_p1
        return clamp_probability(round_ratio(numerator, sum(self.fixed_weights)))

    def observe(self, bit: int, base_p1: int, event_p1: int) -> None:
        likelihoods = (
            base_p1 if bit else TOTAL - base_p1,
            event_p1 if bit else TOTAL - event_p1,
        )
        if self.ideal:
            values = [
                self.float_weights[index] * likelihoods[index]
                for index in range(2)
            ]
            total = values[0] + values[1]
            self.float_weights = [values[0] / total, values[1] / total]
        else:
            self.fixed_weights = [
                self.fixed_weights[index] * likelihoods[index]
                for index in range(2)
            ]
            if (self.bit_count + 1) % 8 == 0:
                self.fixed_weights = project_positive(
                    self.fixed_weights, POSTERIOR_SCALE
                )
        self.bit_count += 1


@dataclass
class SemanticState:
    wiki: WikiState = field(default_factory=WikiState)
    raw_tail: bytearray = field(default_factory=bytearray)
    entity: EntityObserver = field(default_factory=EntityObserver)
    history: deque[bytes] = field(default_factory=lambda: deque(maxlen=4))

    def key_levels(self) -> tuple[list[tuple[Any, ...]], ...]:
        suffix = ("suffix32", fnv32(bytes(self.raw_tail[-SUFFIX_BYTES:])))
        features = self.wiki.features()
        schema = fnv16_ints(
            (
                int(features["field"]),
                int(features["mode"]),
                int(features["slot"]),
                int(features["column_bucket"]),
                int(features["prev_class"]),
            )
        )
        wiki = (
            "wiki",
            int(features["field"]),
            int(features["mode"]),
            int(features["slot"]),
            schema,
        )
        e0 = [suffix]
        e1 = [suffix, wiki]
        e2 = list(e1)
        if self.entity.mode in ("title", "link") and self.entity.capture:
            prefix = self.entity.link_prefix if self.entity.in_link else tuple(
                event.encoded for event in self.entity.capture
            )
            prefix = prefix[-ENTITY_PREFIX_EVENTS:]
            e2.append(("entity", self.entity.mode, fnv64_codes(prefix), len(prefix)))
        e3 = list(e2)
        history = tuple(self.history)
        if len(history) >= 2:
            e3.append(("chain2", int(features["field"]), int(features["mode"]), fnv64_codes(history[-2:])))
        if len(history) >= 4:
            e3.append(("chain4", int(features["field"]), int(features["mode"]), fnv64_codes(history[-4:])))
        return e0, e1, e2, e3

    def observe(self, event: WrtEvent) -> None:
        for byte in event.decoded:
            self.wiki.update(byte)
            self.raw_tail.append(byte)
        if len(self.raw_tail) > SUFFIX_BYTES:
            del self.raw_tail[: len(self.raw_tail) - SUFFIX_BYTES]
        self.entity.observe(event)
        self.history.append(event.encoded)


class StreamingTypedEventModel:
    def __init__(self, dictionary_words: list[bytes]) -> None:
        self.dictionary_words = dictionary_words
        self.table = BoundedEventTable()
        self.semantic = SemanticState()
        self.wrt_state = WrtDecoderState()
        self.stream = bytearray()
        self.raw = bytearray()
        self.current_byte = 0
        self.current_bit = 0
        self.current_code: bytearray | None = None
        self.current_start = 0
        self.current_keys: tuple[list[tuple[Any, ...]], ...] | None = None
        self.mixtures: dict[str, EventMixture] = {}
        self.outer_ideal = OuterBayes(ideal=True)
        self.outer_fixed = OuterBayes(ideal=False)
        self.reservoir: list[bytes] = []
        self.reservoir_set: set[bytes] = set()
        self.event_index = 0
        self.active_opportunities = Counter()
        self.outside_equality_checks = 0
        self.outside_equality_violations = 0

    def state_blind(self, aligned: dict[bytes, int]) -> dict[bytes, int]:
        if not aligned or not self.reservoir:
            return {}
        weights = [weight for _code, weight in sorted(aligned.items(), key=lambda row: (-row[1], row[0]))]
        selected: dict[bytes, int] = {}
        size = len(self.reservoir)
        for rank, weight in enumerate(weights):
            start = (self.event_index * 17 + rank * 7919) % size
            for offset in range(size):
                code = self.reservoir[(start + offset) % size]
                if code not in selected:
                    selected[code] = weight
                    break
        return selected

    def start_event(self) -> None:
        if self.current_code is not None or len(self.stream) < 6:
            return
        self.current_code = bytearray()
        self.current_start = len(self.stream)
        levels = self.semantic.key_levels()
        candidates = [self.table.candidates(keys) for keys in levels]
        blind = self.state_blind(candidates[3])
        self.current_keys = levels
        self.mixtures = {
            "C0": EventMixture(blind),
            "E0": EventMixture(candidates[0]),
            "E1": EventMixture(candidates[1]),
            "E2": EventMixture(candidates[2]),
            "E3": EventMixture(candidates[3]),
        }
        for name, mixture in self.mixtures.items():
            if mixture.candidates:
                self.active_opportunities[name] += 1

    def predict(self, base_p1: int) -> dict[str, int]:
        self.start_event()
        event_predictions = {
            name: mixture.predict(base_p1)
            for name, mixture in self.mixtures.items()
        }
        if not event_predictions:
            event_predictions = {name: base_p1 for name in ("C0", "E0", "E1", "E2", "E3")}
        e3 = event_predictions["E3"]
        e3_active = bool(self.mixtures.get("E3") and self.mixtures["E3"].candidates)
        if not e3_active:
            self.outside_equality_checks += 1
            if e3 != base_p1:
                self.outside_equality_violations += 1
        return {
            **event_predictions,
            "M0": self.outer_ideal.predict(base_p1, e3),
            "M1": self.outer_fixed.predict(base_p1, e3),
        }

    def event_complete(self) -> bool:
        assert self.current_code is not None and self.current_code
        transformed = [wrt_byte_transform(value) for value in self.current_code]
        first = transformed[0]
        if first == ESCAPE:
            return len(transformed) == 2
        if first in (UPPERCASE, END_UPPER, CAPITALIZED) or first < 0x80 or first <= 0xCF:
            return len(transformed) == 1
        if len(transformed) == 1:
            return False
        if transformed[1] <= 0xCF:
            return len(transformed) == 2
        return len(transformed) == 3

    def decode_event(self, encoded: bytes) -> tuple[bytes, str]:
        transformed = bytes(wrt_byte_transform(value) for value in encoded)
        first = transformed[0]
        if first == ESCAPE:
            if len(transformed) != 2:
                raise ValueError("invalid WRT escape event")
            return self.wrt_state.escaped(transformed[1]), "escaped_literal"
        if first in (UPPERCASE, END_UPPER, CAPITALIZED):
            if len(transformed) != 1:
                raise ValueError("invalid WRT control event")
            self.wrt_state.control(first)
            return b"", "control"
        if first >= 0x80:
            index = token_index(transformed)
            if index >= len(self.dictionary_words):
                raise ValueError("WRT token exceeds dictionary")
            return self.wrt_state.word(self.dictionary_words[index]), "token"
        if len(transformed) != 1:
            raise ValueError("invalid WRT literal event")
        return self.wrt_state.literal(first), "literal"

    def finish_event(self) -> None:
        assert self.current_code is not None and self.current_keys is not None
        encoded = bytes(self.current_code)
        decoded, kind = self.decode_event(encoded)
        event = WrtEvent(self.current_start, len(self.stream), encoded, decoded, kind)
        all_keys = self.current_keys[3]
        self.table.update(all_keys, encoded)
        self.semantic.observe(event)
        self.raw.extend(decoded)
        if encoded not in self.reservoir_set:
            self.reservoir_set.add(encoded)
            self.reservoir.append(encoded)
        self.event_index += 1
        self.current_code = None
        self.current_keys = None
        self.mixtures = {}

    def observe(self, bit: int, base_p1: int, predictions: dict[str, int]) -> None:
        e3 = predictions["E3"]
        self.outer_ideal.observe(bit, base_p1, e3)
        self.outer_fixed.observe(bit, base_p1, e3)
        for mixture in self.mixtures.values():
            mixture.observe(bit, base_p1)
        self.current_byte = (self.current_byte << 1) | bit
        self.current_bit += 1
        if self.current_bit != 8:
            return
        value = self.current_byte
        self.stream.append(value)
        if self.current_code is not None:
            self.current_code.append(value)
            if self.event_complete():
                self.finish_event()
        self.current_byte = 0
        self.current_bit = 0

    def validate_complete(self, expected_stream: bytes, expected_raw: bytes) -> None:
        if self.current_bit or self.current_code is not None:
            raise ValueError("typed-event replay ended inside a byte or event")
        if bytes(self.stream) != expected_stream:
            raise ValueError("typed-event replay WRT stream mismatch")
        if len(self.stream) < 6 or self.stream[0] != TEXT_SEGMENT or self.stream[5] != TEXT_SEGMENT:
            raise ValueError("typed-event replay has an invalid WRT header")
        if int.from_bytes(self.stream[1:5], "big") != len(expected_raw):
            raise ValueError("typed-event replay WRT raw length mismatch")
        if bytes(self.raw) != expected_raw:
            raise ValueError("typed-event replay raw reconstruction mismatch")

    def digest(self) -> str:
        digest = hashlib.sha256()
        digest.update(self.table.digest().encode("ascii"))
        digest.update(bytes(self.semantic.raw_tail))
        digest.update(self.event_index.to_bytes(8, "little"))
        for code in self.reservoir:
            digest.update(len(code).to_bytes(2, "little"))
            digest.update(code)
        return digest.hexdigest()


def generate_probabilities(
    base: np.ndarray,
    truth: np.ndarray,
    dictionary_words: list[bytes],
    expected_stream: bytes,
    expected_raw: bytes,
    store: bool,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    model = StreamingTypedEventModel(dictionary_words)
    arrays = {
        name: np.empty(len(truth), dtype=np.uint16)
        for name in VARIANTS
    } if store else {"M1": np.empty(len(truth), dtype=np.uint16)}
    hashers = {name: hashlib.sha256() for name in VARIANTS}
    for row in range(len(truth)):
        base_p1 = int(base[row])
        predictions = model.predict(base_p1)
        for name in VARIANTS:
            value = predictions[name]
            hashers[name].update(struct.pack("<H", value))
            if name in arrays:
                arrays[name][row] = value
        model.observe(int(truth[row]), base_p1, predictions)
    model.validate_complete(expected_stream, expected_raw)
    return arrays, {
        "p1_sha256": {name: hasher.hexdigest() for name, hasher in hashers.items()},
        "state_sha256": model.digest(),
        "event_count": model.event_index,
        "active_opportunities": dict(sorted(model.active_opportunities.items())),
        "outside_equality_checks": model.outside_equality_checks,
        "outside_equality_violations": model.outside_equality_violations,
        "table": model.table.receipt(),
        "entity": model.semantic.entity.receipt(),
        "reservoir_codes": len(model.reservoir),
    }


def causal_decode(
    payload: bytes,
    base: np.ndarray,
    dictionary_words: list[bytes],
    expected_stream: bytes,
    expected_raw: bytes,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    if len(payload) < 4:
        raise ValueError("candidate payload is too short")
    model = StreamingTypedEventModel(dictionary_words)
    low = 0
    high = 0xFFFFFFFF
    code = int.from_bytes(payload[:4], "big")
    cursor = 4
    truth = np.empty(len(base), dtype=np.uint8)
    m1 = np.empty(len(base), dtype=np.uint16)
    for row in range(len(base)):
        base_p1 = int(base[row])
        predictions = model.predict(base_p1)
        p1 = predictions["M1"]
        m1[row] = p1
        delta = high - low
        midpoint = low + (delta >> 16) * p1 + (((delta & 0xFFFF) * p1) >> 16)
        if code <= midpoint:
            bit = 1
            high = midpoint
        else:
            bit = 0
            low = midpoint + 1
        truth[row] = bit
        model.observe(bit, base_p1, predictions)
        while ((low ^ high) & 0xFF000000) == 0:
            low = (low << 8) & 0xFFFFFFFF
            high = ((high << 8) & 0xFFFFFFFF) + 255
            next_byte = payload[cursor] if cursor < len(payload) else 0
            cursor += 1
            code = ((code << 8) & 0xFFFFFFFF) + next_byte
    model.validate_complete(expected_stream, expected_raw)
    return truth, m1, {
        "state_sha256": model.digest(),
        "event_count": model.event_index,
        "table": model.table.receipt(),
    }


def concatenate_pages(
    values: np.ndarray, pages: list[Page]
) -> np.ndarray:
    chunks = [values[page.wrt_start * 8 : page.wrt_end * 8] for page in pages]
    return np.concatenate(chunks) if chunks else np.empty(0, dtype=values.dtype)


def split_metrics(
    base: np.ndarray,
    candidates: dict[str, np.ndarray],
    truth: np.ndarray,
    pages: list[Page],
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for split in ("development", "selection", "sealed_confirmation"):
        selected = [page for page in pages if page.split == split]
        selected_truth = concatenate_pages(truth, selected)
        selected_base = concatenate_pages(base, selected)
        base_payload = parent_codec.encode_payload(selected_base, selected_truth)
        raw_bytes = sum(page.raw_end - page.raw_start for page in selected)
        rows: dict[str, Any] = {}
        for name in VARIANTS:
            selected_p1 = concatenate_pages(candidates[name], selected)
            payload = parent_codec.encode_payload(selected_p1, selected_truth)
            gain = len(base_payload) - len(payload)
            rows[name] = {
                "payload_bytes": len(payload),
                "gain_bytes": gain,
                "gain_bytes_per_million_raw": gain * 1_000_000.0 / raw_bytes,
            }
        output[split] = {
            "pages": len(selected),
            "raw_bytes": raw_bytes,
            "wrt_rows": len(selected_truth),
            "base_payload_bytes": len(base_payload),
            "variants": rows,
        }
    return output


def sealed_quartiles(
    base: np.ndarray, m1: np.ndarray, truth: np.ndarray, pages: list[Page]
) -> list[dict[str, Any]]:
    sealed = [page for page in pages if page.split == "sealed_confirmation"]
    rows: list[dict[str, Any]] = []
    for quartile in range(4):
        start = len(sealed) * quartile // 4
        stop = len(sealed) * (quartile + 1) // 4
        group = sealed[start:stop]
        group_truth = concatenate_pages(truth, group)
        base_payload = parent_codec.encode_payload(concatenate_pages(base, group), group_truth)
        m1_payload = parent_codec.encode_payload(concatenate_pages(m1, group), group_truth)
        rows.append({
            "quartile": quartile,
            "pages": len(group),
            "raw_bytes": sum(page.raw_end - page.raw_start for page in group),
            "base_payload_bytes": len(base_payload),
            "m1_payload_bytes": len(m1_payload),
            "gain_bytes": len(base_payload) - len(m1_payload),
        })
    return rows


def adaptive_mode_payload(modes: list[int]) -> bytes:
    probabilities = np.empty(len(modes), dtype=np.uint16)
    count0 = 1
    count1 = 1
    for index, mode in enumerate(modes):
        probabilities[index] = clamp_probability(
            round_ratio(count1 * TOTAL, count0 + count1)
        )
        if mode:
            count1 += 1
        else:
            count0 += 1
    return parent_codec.encode_payload(probabilities, np.asarray(modes, dtype=np.uint8))


def selector_receipts(base: np.ndarray, e3: np.ndarray, truth: np.ndarray) -> dict[str, Any]:
    base_payload = parent_codec.encode_payload(base, truth)
    e3_payload = parent_codec.encode_payload(e3, truth)
    global_mode = int(len(e3_payload) < len(base_payload))
    selected = e3_payload if global_mode else base_payload
    mode_payload = adaptive_mode_payload([global_mode])
    s0 = b"TESG1\0" + struct.pack("<I", len(mode_payload)) + mode_payload
    s0 += struct.pack("<I", len(selected)) + selected

    rows_per_block = S1_BLOCK_BYTES * 8
    modes: list[int] = []
    block_payloads: list[bytes] = []
    for start in range(0, len(truth), rows_per_block):
        stop = min(len(truth), start + rows_per_block)
        base_block = parent_codec.encode_payload(base[start:stop], truth[start:stop])
        e3_block = parent_codec.encode_payload(e3[start:stop], truth[start:stop])
        mode = int(len(e3_block) < len(base_block))
        modes.append(mode)
        block_payloads.append(e3_block if mode else base_block)
    s1_modes = adaptive_mode_payload(modes)
    s1 = bytearray(b"TESB1\0")
    s1.extend(struct.pack("<II", len(block_payloads), len(s1_modes)))
    s1.extend(s1_modes)
    for payload in block_payloads:
        s1.extend(struct.pack("<I", len(payload)))
        s1.extend(payload)
    return {
        "S0": {
            "mode": global_mode,
            "mode_payload_bytes": len(mode_payload),
            "total_bytes": len(s0),
            "sha256": sha256_bytes(s0),
            "gain_vs_parent_payload_bytes": len(base_payload) - len(s0),
        },
        "S1": {
            "block_bytes": S1_BLOCK_BYTES,
            "blocks": len(block_payloads),
            "event_modes": sum(modes),
            "mode_payload_bytes": len(s1_modes),
            "total_bytes": len(s1),
            "sha256": sha256_bytes(bytes(s1)),
            "gain_vs_parent_payload_bytes": len(base_payload) - len(s1),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p1", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--parent-archive", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--page-map", type=Path, required=True)
    parser.add_argument("--parent-trace-decision", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    trace_decision = json.loads(args.parent_trace_decision.read_text())
    if trace_decision.get("schema") != "endpoint428_exact_parent_p1_trace_gate_v1":
        raise ValueError("unexpected parent trace decision schema")
    if not trace_decision["proof"]["trace_replay_payload_identity"]:
        raise ValueError("parent trace decision is not authorized")
    if not trace_decision["decision"]["typed_event_shadow_authorized"]:
        raise ValueError("parent trace decision did not authorize typed-event Q0")

    bound_inputs = {
        "p1": artifact(args.p1),
        "wrt_store": artifact(args.wrt_store),
        "raw_input": artifact(args.raw_input),
        "parent_archive": artifact(args.parent_archive),
        "dictionary": artifact(args.dictionary),
    }
    trace_bindings = {
        "p1": trace_decision["artifacts"]["p1_a"],
        "wrt_store": trace_decision["inputs"]["wrt_store"],
        "raw_input": trace_decision["inputs"]["raw_input"],
        "parent_archive": trace_decision["inputs"]["reference_archive"],
        "dictionary": trace_decision["inputs"]["dictionary"],
    }
    for name, observed in bound_inputs.items():
        expected = trace_bindings[name]
        if (observed["bytes"], observed["sha256"]) != (
            expected["bytes"],
            expected["sha256"],
        ):
            raise ValueError(f"{name} differs from the certified parent trace input")

    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("WRT inverse differs from canonical raw")
    truth = np.unpackbits(np.frombuffer(parsed.stream, dtype=np.uint8), bitorder="big")
    base = read_p1(args.p1, len(truth))
    parent_payload, header_bytes, declared_wrt = parent_codec.read_archive(args.parent_archive)
    if declared_wrt != len(parsed.stream):
        raise ValueError("parent archive WRT length mismatch")
    replay_parent = parent_codec.encode_payload(base, truth)
    if replay_parent != parent_payload:
        raise ValueError("frontier P1 does not replay the parent payload")

    dictionary_words = read_dictionary_words(args.dictionary)
    first, first_receipt = generate_probabilities(
        base, truth, dictionary_words, parsed.stream, raw, True
    )
    second, second_receipt = generate_probabilities(
        base, truth, dictionary_words, parsed.stream, raw, False
    )
    if first_receipt["p1_sha256"]["M1"] != second_receipt["p1_sha256"]["M1"]:
        raise ValueError("second causal M1 P1 replay differs")
    if first_receipt["state_sha256"] != second_receipt["state_sha256"]:
        raise ValueError("second causal state replay differs")
    if not np.array_equal(first["M1"], second["M1"]):
        raise ValueError("second stored M1 P1 differs")

    full_payloads = {"B0": parent_payload}
    for name in VARIANTS:
        full_payloads[name] = parent_codec.encode_payload(first[name], truth)
    decoded_truth, decoded_m1, decode_receipt = causal_decode(
        full_payloads["M1"], base, dictionary_words, parsed.stream, raw
    )
    if not np.array_equal(decoded_truth, truth):
        raise ValueError("causal M1 arithmetic decode differs from truth")
    if not np.array_equal(decoded_m1, first["M1"]):
        raise ValueError("causal M1 decoder regenerated different probabilities")
    second_payload = parent_codec.encode_payload(decoded_m1, decoded_truth)
    if second_payload != full_payloads["M1"]:
        raise ValueError("second M1 archive differs")

    reconstructed_wrt = np.packbits(decoded_truth, bitorder="big").tobytes()
    reconstructed_store = parsed.stored[: parsed.storage_header_bytes] + reconstructed_wrt
    wrt_path = args.output_dir / "m1.wrt_store.bin"
    wrt_path.write_bytes(reconstructed_store)
    restored_path = args.output_dir / "m1.restored.raw"
    with (args.output_dir / "m1_inverse.stdout.log").open("wb") as stdout, (
        args.output_dir / "m1_inverse.stderr.log"
    ).open("wb") as stderr:
        inverse = subprocess.run(
            [str(args.backend), "-d", str(args.dictionary), str(wrt_path), str(restored_path)],
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    official_inverse_ok = (
        inverse.returncode == 0
        and restored_path.is_file()
        and restored_path.read_bytes() == raw
    )
    if not official_inverse_ok:
        raise ValueError("official WRT inverse failed")

    pages = read_pages(args.page_map, len(parsed.stream))
    splits = split_metrics(base, first, truth, pages)
    quartiles = sealed_quartiles(base, first["M1"], truth, pages)
    selectors = selector_receipts(base, first["E3"], truth)
    sealed = splits["sealed_confirmation"]
    sealed_m1 = sealed["variants"]["M1"]
    sealed_m0 = sealed["variants"]["M0"]
    sealed_e3 = sealed["variants"]["E3"]
    sealed_c0 = sealed["variants"]["C0"]
    gross_bpm = sealed_m1["gain_bytes_per_million_raw"]
    net_bpm = gross_bpm - PACKAGE_ALLOWANCE_BYTES / 1000.0
    attribution_bpm = (
        sealed_e3["gain_bytes_per_million_raw"]
        - sealed_c0["gain_bytes_per_million_raw"]
    )
    ideal_gain = sealed_m0["gain_bytes"]
    fixed_gain = sealed_m1["gain_bytes"]
    fixed_loss_fraction = (
        (ideal_gain - fixed_gain) / ideal_gain if ideal_gain > 0 else None
    )
    positive_quartiles = sum(row["gain_bytes"] > 0 for row in quartiles)
    positive_total = sum(max(0, row["gain_bytes"]) for row in quartiles)
    largest_positive_share = (
        max((max(0, row["gain_bytes"]) for row in quartiles), default=0)
        / positive_total
        if positive_total
        else 1.0
    )

    conditions = {
        "parent_payload_identity": replay_parent == parent_payload,
        "independent_frontier_P1_identity": trace_decision["proof"]["independent_p1_identity"],
        "M1_arithmetic_decode": np.array_equal(decoded_truth, truth),
        "WRT_reconstruction": reconstructed_wrt == parsed.stream,
        "official_raw_inverse": official_inverse_ok,
        "second_M1_P1_identity": np.array_equal(decoded_m1, first["M1"]),
        "second_M1_payload_identity": second_payload == full_payloads["M1"],
        "E_star_equals_B_outside_opportunities": (
            first_receipt["outside_equality_violations"] == 0
            and second_receipt["outside_equality_violations"] == 0
        ),
        "development_M1_gain_positive": splits["development"]["variants"]["M1"]["gain_bytes"] > 0,
        "selection_M1_gain_positive": splits["selection"]["variants"]["M1"]["gain_bytes"] > 0,
        "sealed_M1_gross_at_least_3000_BPM": gross_bpm >= GROSS_GATE_BPM,
        "sealed_M1_net_at_least_2100_BPM": net_bpm >= NET_GATE_BPM,
        "sealed_E3_beats_C0_by_256_BPM": attribution_bpm >= ATTRIBUTION_GATE_BPM,
        "fixed_point_loss_below_5_percent": fixed_loss_fraction is not None and fixed_loss_fraction < 0.05,
        "positive_sealed_quartiles_at_least_3": positive_quartiles >= 3,
        "largest_positive_quartile_share_at_most_60_percent": largest_positive_share <= 0.60,
        "all_probabilities_legal_nonzero": all(
            not np.any(values == 0) for values in first.values()
        ),
    }
    failed = [name for name, passed in conditions.items() if not passed]
    authorized = not failed
    verdict = "authorize_frozen_distant_1m_replay" if authorized else "retire_frozen_typed_event_sleeping_bayes_q0"

    for name, payload in full_payloads.items():
        (args.output_dir / f"{name.lower()}.payload").write_bytes(payload)
    (args.output_dir / "m1.p1").write_bytes(
        P1_MAGIC + struct.pack("<Q", len(first["M1"])) + first["M1"].astype("<u2").tobytes()
    )
    source_compressed = gzip.compress(Path(__file__).read_bytes(), compresslevel=9, mtime=0)
    decision = {
        "schema": "typed_event_sleeping_bayes_envelope_q0_v1",
        "candidate_id": CANDIDATE_ID,
        "evidence_level": "zero_credit_exact_same_stream_typed_event_oracle",
        "claim_boundary": "Exact opening-1M same-stream typed-event evidence only. No native integration, forecast credit, distant transfer, runtime qualification, or full-1G claim.",
        "inputs": {
            **bound_inputs,
            "backend": artifact(args.backend),
            "page_map": artifact(args.page_map),
            "parent_trace_decision": artifact(args.parent_trace_decision),
            "contract": artifact(CONTRACT),
        },
        "scope": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(parsed.stream),
            "trace_rows": len(truth),
            "complete_pages": len(pages),
            "archive_header_bytes": header_bytes,
        },
        "frozen_construction": {
            "suffix_bytes": SUFFIX_BYTES,
            "max_keys": MAX_KEYS,
            "codes_per_key": CODES_PER_KEY,
            "minimum_support": MIN_SUPPORT,
            "maximum_candidates": MAX_CANDIDATES,
            "literal_prior": LITERAL_PRIOR,
            "posterior_scale": POSTERIOR_SCALE,
            "s1_block_bytes": S1_BLOCK_BYTES,
            "package_allowance_bytes": PACKAGE_ALLOWANCE_BYTES,
            "compressed_oracle_source_bytes": len(source_compressed),
        },
        "causal_replays": {
            "first": first_receipt,
            "second": second_receipt,
            "decode": decode_receipt,
        },
        "full_payloads": {
            name: {
                "bytes": len(payload),
                "sha256": sha256_bytes(payload),
                "gain_vs_parent_payload_bytes": len(parent_payload) - len(payload),
            }
            for name, payload in full_payloads.items()
        },
        "splits": splits,
        "sealed_quartiles": quartiles,
        "selectors": selectors,
        "economics": {
            "sealed_M1_gross_bytes_per_million": gross_bpm,
            "sealed_M1_projected_net_bytes_per_million": net_bpm,
            "sealed_E3_minus_C0_bytes_per_million": attribution_bpm,
            "sealed_M0_gain_bytes": ideal_gain,
            "sealed_M1_gain_bytes": fixed_gain,
            "fixed_point_loss_fraction_of_ideal_gain": fixed_loss_fraction,
            "positive_sealed_quartiles": positive_quartiles,
            "largest_positive_quartile_share": largest_positive_share,
            "forecast_bytes": 109_389_323,
            "remaining_design_target_debt_bytes": 1_389_323,
            "score_credit_bytes": 0,
        },
        "proof": {
            "event_length_from_completed_bytes_only": True,
            "memory_update_after_event_completion": True,
            "E_star_equals_B_outside_opportunities": first_receipt["outside_equality_violations"] == 0,
            "both_experts_update_every_bit": True,
            "state_blind_control_uses_completed_reservoir_only": True,
            "official_inverse_returncode": inverse.returncode,
            "conditions": conditions,
            "failed_conditions": failed,
        },
        "decision": {
            "verdict": verdict,
            "distant_1m_authorized": authorized,
            "native_10m_authorized": False,
            "full_1g_authorized": False,
            "next_action": "Run the frozen distant 1M." if authorized else "Retire this exact typed-event realization without parameter rescue sweeps.",
        },
    }
    decision_path = args.output_dir / "decision.json"
    temporary = decision_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(decision_path)
    print(json.dumps({"decision_path": str(decision_path), "verdict": verdict, "failed_conditions": failed}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
