#!/usr/bin/env python3
"""Exact-shadow prototype for the Streaming Retrieval Mixer lane.

This is a lock-safe SRSTC probe. It consumes cached fx2 residual rows that
include true bits and base probabilities, builds deterministic sketch buckets
from bytes before the current position, and tests whether prior matching
contexts improve an exact binary arithmetic shadow coder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Any

from causal_state_screen import WikiState, bucket
from fx2_shadow_residual_coder import (
    TOTAL,
    BinaryArithmeticEncoder,
    as_int,
    clamp_p1,
    iter_rows,
    prob_bucket,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_OUT = ROOT / "results" / "streaming_retrieval_shadow" / "latest.json"
DEFAULT_BASELINE_SCORE = 110_181_114
DEFAULT_TARGET_SCORE = 109_000_000
DEFAULT_SCOPE_BYTES = 1_000_000_000
FNV_OFFSET = 1469598103934665603
FNV_PRIME = 1099511628211


def fnv64_bytes(data: bytes) -> int:
    h = FNV_OFFSET
    for byte in data:
        h ^= byte
        h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


def fnv64_ints(values: tuple[int, ...]) -> int:
    h = FNV_OFFSET
    for value in values:
        h ^= value & 0xFFFFFFFFFFFFFFFF
        h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


def simhash16(data: bytes, ngram: int = 3) -> int:
    if not data:
        return 0
    if len(data) < ngram:
        return fnv64_bytes(data) & 0xFFFF
    acc = [0] * 16
    for i in range(0, len(data) - ngram + 1):
        h = fnv64_bytes(data[i : i + ngram])
        for bit in range(16):
            acc[bit] += 1 if (h >> bit) & 1 else -1
    out = 0
    for bit, value in enumerate(acc):
        if value >= 0:
            out |= 1 << bit
    return out


def qbits_for(bit: int, p1: int) -> int:
    p1 = clamp_p1(p1)
    prob = p1 / TOTAL if bit else (TOTAL - p1) / TOTAL
    return int((-math.log2(prob)) * 256.0 + 0.5)


@dataclass
class BitCounts:
    zeros: int = 0
    ones: int = 0

    @property
    def total(self) -> int:
        return self.zeros + self.ones

    def update(self, bit: int) -> None:
        if bit:
            self.ones += 1
        else:
            self.zeros += 1


@dataclass
class BoundedCounterTable:
    cap_entries: int
    counters: dict[tuple[Any, ...], BitCounts] = field(default_factory=dict)
    order: deque[tuple[Any, ...]] = field(default_factory=deque)

    def get(self, key: tuple[Any, ...]) -> BitCounts | None:
        return self.counters.get(key)

    def update(self, key: tuple[Any, ...], bit: int) -> None:
        counter = self.counters.get(key)
        if counter is None:
            if self.cap_entries > 0 and len(self.counters) >= self.cap_entries:
                while self.order:
                    old = self.order.popleft()
                    if old in self.counters:
                        del self.counters[old]
                        break
            counter = BitCounts()
            self.counters[key] = counter
            self.order.append(key)
        counter.update(bit)


@dataclass
class BoundedByteTable:
    """Bounded LRU table from causal sketch keys to completed next-byte counts."""

    cap_entries: int
    counters: dict[tuple[Any, ...], Counter[int]] = field(default_factory=dict)
    order: list[tuple[Any, ...]] = field(default_factory=list)
    cursor: int = 0

    def get(self, key: tuple[Any, ...]) -> Counter[int] | None:
        return self.counters.get(key)

    def update(self, key: tuple[Any, ...], byte_value: int) -> None:
        counter = self.counters.get(key)
        if counter is None:
            if self.cap_entries > 0 and len(self.counters) >= self.cap_entries:
                while self.cursor < len(self.order):
                    old = self.order[self.cursor]
                    self.cursor += 1
                    if old in self.counters:
                        del self.counters[old]
                        break
                if self.cursor > 4096 and self.cursor * 2 > len(self.order):
                    self.order = self.order[self.cursor :]
                    self.cursor = 0
            counter = Counter()
            self.counters[key] = counter
            self.order.append(key)
        counter[byte_value & 0xFF] += 1


def wrt_regime(row: dict[str, Any]) -> int:
    modes = (
        "wrt_title_mode",
        "wrt_ref_mode",
        "wrt_url_mode",
        "wrt_table_mode",
        "wrt_list_mode",
        "wrt_template_depth",
        "wrt_section_state",
        "wrt_prose_mode",
        "wrt_page_mode",
    )
    for index, name in enumerate(modes, start=1):
        if as_int(row, name, default=0):
            return index
    return 0


@dataclass
class WrtCopyState:
    """Bounded exact WRT suffix memory rebuilt only from completed bytes."""

    min_match: int
    max_match: int
    candidates_per_key: int
    cap_entries: int
    history: bytearray = field(default_factory=bytearray)
    regimes: bytearray = field(default_factory=bytearray)
    title_flags: bytearray = field(default_factory=bytearray)
    page_start: int = 0
    positions: dict[tuple[int, bytes], deque[int]] = field(default_factory=dict)
    insertion_order: deque[tuple[int, bytes]] = field(default_factory=deque)
    cached_signature: tuple[Any, ...] | None = None
    cached_continuations: dict[str, list[tuple[int, int]]] = field(
        default_factory=dict
    )

    def prepare(self, row: dict[str, Any]) -> None:
        if as_int(row, "wrt_page_boundary", default=0) == 1:
            self.page_start = len(self.history)
            self.cached_signature = None

    def _key(self, length: int) -> tuple[int, bytes]:
        return length, bytes(self.history[-length:])

    def _match_length(self, candidate_end: int) -> int:
        current_end = len(self.history) - 1
        length = 0
        while (
            length < self.max_match
            and current_end - length >= 0
            and candidate_end - length >= 0
            and self.history[current_end - length]
            == self.history[candidate_end - length]
        ):
            length += 1
        return length

    def _continuations(self, band: str, regime: int) -> list[tuple[int, int]]:
        if len(self.history) < self.min_match:
            return []
        current_end = len(self.history) - 1
        seen: set[int] = set()
        matches: list[tuple[int, int]] = []
        for length in range(min(self.max_match, len(self.history)), self.min_match - 1, -1):
            positions = self.positions.get(self._key(length))
            if positions is None:
                continue
            for candidate_end in reversed(positions):
                if candidate_end == current_end or candidate_end in seen:
                    continue
                continuation = candidate_end + 1
                if continuation >= len(self.history):
                    continue
                match_length = self._match_length(candidate_end)
                if match_length < self.min_match:
                    continue
                if band == "copy_page" and candidate_end < self.page_start:
                    continue
                if band == "copy_typed" and self.regimes[continuation] != regime:
                    continue
                if band == "copy_title" and not self.title_flags[continuation]:
                    continue
                seen.add(candidate_end)
                matches.append((self.history[continuation], match_length))
                if len(matches) >= self.candidates_per_key:
                    return matches
            if matches:
                return matches
        return matches

    def band_candidates(
        self,
        row: dict[str, Any],
        partial_len: int,
        partial_prefix: int,
        alpha_num: int,
        bands: tuple[str, ...],
    ) -> dict[str, tuple[int, int]]:
        regime = wrt_regime(row)
        signature = (len(self.history), regime, self.page_start, bands)
        if signature != self.cached_signature:
            self.cached_continuations = {
                band: self._continuations(band, regime) for band in bands
            }
            self.cached_signature = signature
        output: dict[str, tuple[int, int]] = {}
        prefix = partial_prefix & ((1 << partial_len) - 1) if partial_len else 0
        for band in bands:
            zeros = 0
            ones = 0
            support = 0
            for byte_value, match_length in self.cached_continuations[band]:
                if partial_len and byte_value >> (8 - partial_len) != prefix:
                    continue
                weight = min(match_length, self.max_match)
                if (byte_value >> (7 - partial_len)) & 1:
                    ones += weight
                else:
                    zeros += weight
                support += weight
            if support <= 0:
                continue
            denom = 2 * support + 2 * alpha_num
            numer = (2 * ones + alpha_num) * TOTAL
            output[band] = (clamp_p1(numer // denom), support)
        return output

    def observe_byte(self, byte_value: int, row: dict[str, Any]) -> None:
        self.cached_signature = None
        self.cached_continuations.clear()
        self.history.append(byte_value & 0xFF)
        self.regimes.append(wrt_regime(row) & 0xFF)
        self.title_flags.append(int(as_int(row, "wrt_title_mode", default=0) != 0))
        for length in range(self.min_match, min(self.max_match, len(self.history)) + 1):
            key = self._key(length)
            positions = self.positions.get(key)
            if positions is None:
                while self.cap_entries > 0 and len(self.positions) >= self.cap_entries:
                    old = self.insertion_order.popleft()
                    if old in self.positions:
                        del self.positions[old]
                        break
                positions = deque(maxlen=self.candidates_per_key + 1)
                self.positions[key] = positions
                self.insertion_order.append(key)
            positions.append(len(self.history) - 1)


def _distance_since_any(data: bytes, markers: bytes) -> int:
    if not data:
        return 255
    marker_set = set(markers)
    for distance, byte in enumerate(reversed(data)):
        if byte in marker_set:
            return min(distance, 255)
    return 255


@dataclass
class RetrievalState:
    data: bytes
    suffix_len: int
    sketch_len: int
    wiki: WikiState = field(default_factory=WikiState)
    pos: int = 0
    tail: bytearray = field(default_factory=bytearray)
    sketch_trigram_hashes: deque[int] = field(default_factory=deque)
    sketch_acc: list[int] = field(default_factory=lambda: [0] * 16)
    line_distance: int = 255
    markup_distance: int = 255
    token_distance: int = 255
    cached_pos: int | None = None
    cached_features: dict[str, Any] = field(default_factory=dict)

    def _observe_distance(self, current: int, byte: int, markers: bytes) -> int:
        return 0 if byte in markers else min(255, current + 1)

    def _observe_sketch_trigram(self) -> None:
        if self.sketch_len < 3 or len(self.tail) < 3:
            return
        trigram_hash = fnv64_bytes(bytes(self.tail[-3:]))
        self.sketch_trigram_hashes.append(trigram_hash)
        for bit in range(16):
            self.sketch_acc[bit] += 1 if (trigram_hash >> bit) & 1 else -1
        max_hashes = self.sketch_len - 2
        if len(self.sketch_trigram_hashes) <= max_hashes:
            return
        expired_hash = self.sketch_trigram_hashes.popleft()
        for bit in range(16):
            self.sketch_acc[bit] -= 1 if (expired_hash >> bit) & 1 else -1

    def advance_to(self, target_pos: int) -> None:
        if target_pos < self.pos:
            raise ValueError("residual rows must be nondecreasing by pos")
        while self.pos < target_pos:
            if self.pos >= len(self.data):
                raise ValueError(f"row position {target_pos} exceeds data length {len(self.data)}")
            byte = self.data[self.pos]
            self.wiki.update(byte)
            self.tail.append(byte)
            self.line_distance = self._observe_distance(
                self.line_distance, byte, b"\n"
            )
            self.markup_distance = self._observe_distance(
                self.markup_distance, byte, b"\n|={}<>[]"
            )
            self.token_distance = self._observe_distance(
                self.token_distance, byte, b" \t\r\n|={}<>[]/\"'&;:,."
            )
            self._observe_sketch_trigram()
            keep = max(self.suffix_len, self.sketch_len, 192)
            if len(self.tail) > keep * 2:
                del self.tail[: len(self.tail) - keep]
                retained = bytes(self.tail)
                self.line_distance = _distance_since_any(retained, b"\n")
                self.markup_distance = _distance_since_any(
                    retained, b"\n|={}<>[]"
                )
                self.token_distance = _distance_since_any(
                    retained, b" \t\r\n|={}<>[]/\"'&;:,."
                )
            self.pos += 1
            self.cached_pos = None

    def features(self) -> dict[str, Any]:
        if self.cached_pos == self.pos:
            return self.cached_features
        tail = bytes(self.tail)
        suffix = tail[-self.suffix_len :]
        sketch_window = tail[-self.sketch_len :]
        wiki = self.wiki.features()
        field = int(wiki.get("field", 0))
        mode = int(wiki.get("mode", 0))
        slot = int(wiki.get("slot", 0))
        column = int(wiki.get("column_bucket", 0))
        word_sig = wiki.get("word_sig", (0, 0))
        if not isinstance(word_sig, tuple):
            word_sig = (0, 0)
        line_pos_bucket = bucket(
            self.line_distance, (0, 1, 3, 7, 15, 31, 63, 127)
        )
        markup_pos_bucket = bucket(
            self.markup_distance,
            (0, 1, 2, 4, 8, 16, 32, 64),
        )
        token_pos_bucket = bucket(
            self.token_distance,
            (0, 1, 2, 4, 8, 16, 32, 64),
        )
        if self.sketch_len >= 3 and len(sketch_window) >= 3:
            sim = sum(
                1 << bit for bit, value in enumerate(self.sketch_acc) if value >= 0
            )
        else:
            sim = simhash16(sketch_window)
        suffix_hash = fnv64_bytes(suffix) & 0xFFFF
        continuation_hash = fnv64_ints(
            (
                field,
                mode,
                slot,
                line_pos_bucket,
                markup_pos_bucket,
                token_pos_bucket,
                int(word_sig[0]),
                int(word_sig[1]),
            )
        ) & 0xFFFF
        features = {
            "field": field,
            "mode": mode,
            "slot": slot,
            "column": column,
            "word_len_bucket": int(word_sig[0]),
            "word_class": int(word_sig[1]),
            "line_pos_bucket": line_pos_bucket,
            "markup_pos_bucket": markup_pos_bucket,
            "token_pos_bucket": token_pos_bucket,
            "continuation_hash": continuation_hash,
            "suffix_hash": suffix_hash,
            "simhash16": sim,
            "sim_band0": sim & 0xFF,
            "sim_band1": (sim >> 8) & 0xFF,
            "schema_hash": fnv64_ints(
                (field, mode, slot, column, int(word_sig[0]), int(word_sig[1]))
            )
            & 0xFFFF,
        }
        self.cached_pos = self.pos
        self.cached_features = features
        return features


@dataclass
class PartialByteState:
    """Causal prefix bits already seen for the current byte position."""

    pos: int | None = None
    prefix: int = 0
    length: int = 0

    def advance_to(self, pos: int, bit_pos: int) -> tuple[int, int]:
        if self.pos != pos or bit_pos == 0 or bit_pos < self.length:
            self.pos = pos
            self.prefix = 0
            self.length = 0
        return self.length, self.prefix

    def observe(self, pos: int, bit: int) -> None:
        if self.pos != pos:
            self.pos = pos
            self.prefix = 0
            self.length = 0
        if self.length < 8:
            self.prefix = ((self.prefix << 1) | int(bit)) & 0xFF
            self.length += 1


@dataclass
class TraceAlignment:
    max_positions: int
    rows_seen: int = 0
    bits_by_pos: dict[int, dict[int, int]] = field(default_factory=dict)
    wrt_stream_byte_by_pos: dict[int, int] = field(default_factory=dict)

    def observe(
        self,
        pos: int,
        bit_pos: int,
        bit: int,
        wrt_stream_byte: int | None = None,
    ) -> None:
        if self.max_positions <= 0 or pos < 0 or pos >= self.max_positions:
            return
        if bit_pos < 0 or bit_pos > 7:
            return
        self.rows_seen += 1
        self.bits_by_pos.setdefault(pos, {})[bit_pos] = bit
        if wrt_stream_byte is not None:
            self.wrt_stream_byte_by_pos.setdefault(pos, wrt_stream_byte & 0xFF)

    def report_wrt(self) -> dict[str, Any]:
        completed: dict[int, int] = {}
        for pos, bits in self.bits_by_pos.items():
            if len(bits) < 8:
                continue
            value = 0
            for bit_pos in range(8):
                value |= (bits.get(bit_pos, 0) & 1) << (7 - bit_pos)
            completed[pos] = value
        checked = 0
        matches = 0
        examples = []
        for pos, stream_byte in sorted(self.wrt_stream_byte_by_pos.items()):
            if pos <= 0 or pos - 1 not in completed:
                continue
            checked += 1
            previous = completed[pos - 1]
            matches += int(previous == stream_byte)
            if previous != stream_byte and len(examples) < 8:
                examples.append(
                    {
                        "pos": pos,
                        "logged_prior_wrt_byte": stream_byte,
                        "reconstructed_prior_wrt_byte": previous,
                    }
                )
        match_rate = matches / checked if checked else None
        return {
            "alignment_max_positions": self.max_positions,
            "rows_seen": self.rows_seen,
            "complete_prior_bytes_checked": checked,
            "matches": matches,
            "match_rate": match_rate,
            "mismatch_examples": examples,
            "warning": "logged WRT state does not match the decoded bit prefix"
            if checked and matches * 100 < checked * 100
            else None,
        }

    def report(self, data: bytes) -> dict[str, Any]:
        counts = {
            "msb": 0,
            "lsb": 0,
            "inv_msb": 0,
            "inv_lsb": 0,
        }
        checked = 0
        incomplete = 0
        examples = []
        for pos in sorted(self.bits_by_pos):
            bits = self.bits_by_pos[pos]
            if len(bits) < 8 or pos >= len(data):
                incomplete += 1
                continue
            msb = 0
            lsb = 0
            for bit_pos in range(8):
                bit = bits.get(bit_pos, 0) & 1
                msb |= bit << (7 - bit_pos)
                lsb |= bit << bit_pos
            expected = data[pos]
            checked += 1
            candidates = {
                "msb": msb,
                "lsb": lsb,
                "inv_msb": msb ^ 0xFF,
                "inv_lsb": lsb ^ 0xFF,
            }
            matched = False
            for name, value in candidates.items():
                if value == expected:
                    counts[name] += 1
                    matched = True
            if not matched and len(examples) < 8:
                examples.append(
                    {
                        "pos": pos,
                        "data_byte": expected,
                        "trace_msb_byte": msb,
                        "trace_lsb_byte": lsb,
                    }
                )
        best_order = max(counts, key=lambda name: counts[name])
        best_matches = counts[best_order]
        best_rate = best_matches / checked if checked else None
        return {
            "alignment_max_positions": self.max_positions,
            "rows_seen": self.rows_seen,
            "complete_bytes_checked": checked,
            "incomplete_positions": incomplete,
            "match_counts": counts,
            "best_order": best_order if checked else None,
            "best_match_rate": best_rate,
            "mismatch_examples": examples,
            "warning": "trace bits do not reconstruct the supplied data bytes"
            if checked and best_matches * 100 < checked * 95
            else None,
        }


@dataclass
class SplitTotals:
    rows: int = 0
    baseline_qbits: int = 0
    candidate_qbits: int = 0

    @property
    def gain_bits(self) -> float:
        return (self.baseline_qbits - self.candidate_qbits) / 256.0

    @property
    def gain_bytes(self) -> float:
        return self.gain_bits / 8.0


def split_for(pos: int, train_bytes: int) -> str:
    if train_bytes <= 0:
        return "all"
    return "train" if pos < train_bytes else "test"


def features_from_row(row: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    field = as_int(row, "field", default=int(fallback["field"]))
    mode = as_int(row, "mode", default=int(fallback["mode"]))
    slot = as_int(row, "slot", default=int(fallback["slot"]))
    column = as_int(row, "col_bucket", "column", default=int(fallback["column"]))
    word_len = as_int(row, "word_len", default=0)
    char_class = as_int(row, "char_class", default=int(fallback["word_class"]))
    title_hash = as_int(row, "title_hash", default=0)
    template_hash = as_int(row, "template_hash", default=0)
    link_hash = as_int(row, "link_hash", default=0)
    entity_hash = as_int(row, "entity_hash", default=0)
    word_hash = as_int(row, "word_hash", default=0)
    pair_sig = as_int(row, "pair_sig", default=0)
    template_depth = as_int(row, "template_depth", default=0)
    in_tag = as_int(row, "in_tag", default=0)
    ref = as_int(row, "ref", default=0)
    url = as_int(row, "url", default=0)
    number_class = as_int(row, "number_class", default=0)
    suffix_hash = fnv64_ints((word_hash, pair_sig, link_hash, entity_hash)) & 0xFFFF
    sim = fnv64_ints((title_hash, template_hash, link_hash, entity_hash, word_hash, pair_sig)) & 0xFFFF
    schema_hash = fnv64_ints(
        (
            field,
            mode,
            slot,
            column,
            char_class,
            template_depth,
            in_tag,
            ref,
            url,
            number_class,
        )
    ) & 0xFFFF
    line_pos_bucket = as_int(
        row, "line_pos_bucket", default=int(fallback.get("line_pos_bucket", 0))
    )
    markup_pos_bucket = as_int(
        row, "markup_pos_bucket", default=int(fallback.get("markup_pos_bucket", 0))
    )
    token_pos_bucket = as_int(
        row, "token_pos_bucket", default=int(fallback.get("token_pos_bucket", 0))
    )
    continuation_hash = fnv64_ints(
        (
            field,
            mode,
            slot,
            line_pos_bucket,
            markup_pos_bucket,
            token_pos_bucket,
            bucket(word_len, (0, 1, 3, 7, 15)),
            char_class,
        )
    ) & 0xFFFF
    return {
        "field": field,
        "mode": mode,
        "slot": slot,
        "column": column,
        "word_len_bucket": bucket(word_len, (0, 1, 3, 7, 15)),
        "word_class": char_class,
        "line_pos_bucket": line_pos_bucket,
        "markup_pos_bucket": markup_pos_bucket,
        "token_pos_bucket": token_pos_bucket,
        "continuation_hash": continuation_hash,
        "suffix_hash": suffix_hash,
        "simhash16": sim,
        "sim_band0": sim & 0xFF,
        "sim_band1": (sim >> 8) & 0xFF,
        "schema_hash": schema_hash,
    }


def features_from_wrt_row(row: dict[str, Any]) -> dict[str, Any]:
    modes = (
        "wrt_title_mode",
        "wrt_ref_mode",
        "wrt_url_mode",
        "wrt_table_mode",
        "wrt_list_mode",
        "wrt_template_depth",
        "wrt_section_state",
        "wrt_prose_mode",
        "wrt_page_mode",
    )
    regime = 0
    for index, name in enumerate(modes, start=1):
        if as_int(row, name, default=0):
            regime = index
            break
    token_class = as_int(row, "wrt_token_class", default=0)
    token_id = as_int(row, "wrt_token_id", default=0)
    dictionary_hit = as_int(row, "wrt_dictionary_hit_type", default=0)
    literal_phase = as_int(row, "wrt_literal_phase", default=0)
    decoded_chars = as_int(row, "wrt_decoded_chars", default=0)
    template_depth = as_int(row, "wrt_template_depth", default=0)
    section_state = as_int(row, "wrt_section_state", default=0)
    section_level = as_int(row, "wrt_section_level", default=0)
    number_class = as_int(row, "wrt_number_class", default=0)
    stream_byte = as_int(row, "wrt_stream_byte", default=0)
    title_hash = as_int(row, "wrt_title_hash", default=0)
    template_hash = as_int(row, "wrt_template_hash", default=0)
    ref_hash = as_int(row, "wrt_ref_hash", default=0)
    section_hash = as_int(row, "wrt_section_hash", default=0)
    if as_int(row, "wrt_ref_mode", default=0):
        active_hash = ref_hash
    elif template_depth:
        active_hash = template_hash
    elif as_int(row, "wrt_title_mode", default=0):
        active_hash = title_hash
    else:
        active_hash = section_hash
    reconstructed = as_int(row, "wrt_reconstructed_bytes", default=0)
    suffix_hash = fnv64_ints((stream_byte, token_id & 0xFFFF, active_hash & 0xFF)) & 0xFFFF
    schema_hash = fnv64_ints(
        (
            regime,
            token_class,
            dictionary_hit,
            literal_phase,
            min(template_depth, 3),
            section_state,
            min(section_level, 6),
            number_class,
        )
    ) & 0xFFFF
    sim = fnv64_ints(
        (
            title_hash & 0xFF,
            template_hash & 0xFF,
            ref_hash & 0xFF,
            section_hash & 0xFF,
            token_id & 0xFF,
        )
    ) & 0xFFFF
    continuation_hash = fnv64_ints(
        (regime, schema_hash, active_hash & 0xFF, reconstructed & 0x3F)
    ) & 0xFFFF
    return {
        "field": regime,
        "mode": token_class,
        "slot": dictionary_hit * 4 + literal_phase,
        "column": min(section_level, 6),
        "word_len_bucket": min(decoded_chars, 15),
        "word_class": number_class,
        "line_pos_bucket": reconstructed & 0x0F,
        "markup_pos_bucket": min(template_depth, 3) * 4 + section_state,
        "token_pos_bucket": token_id & 0x0F,
        "continuation_hash": continuation_hash,
        "suffix_hash": suffix_hash,
        "simhash16": sim,
        "sim_band0": sim & 0xFF,
        "sim_band1": (sim >> 8) & 0xFF,
        "schema_hash": schema_hash,
    }


def make_keys(
    features: dict[str, Any],
    bit_pos: int,
    p1: int,
    p_buckets: int,
    partial_len: int,
    partial_prefix: int,
    partial_byte_family: str,
    typed_key_profile: str = "base",
) -> list[tuple[Any, ...]]:
    pbin = prob_bucket(p1, p_buckets)
    keys: list[tuple[Any, ...]] = [
        ("suffix", bit_pos, pbin, features["suffix_hash"]),
        ("sim0", bit_pos, pbin, features["sim_band0"]),
        ("sim1", bit_pos, pbin, features["sim_band1"]),
        ("schema", bit_pos, pbin, features["schema_hash"]),
        (
            "hybrid",
            bit_pos,
            pbin,
            features["field"],
            features["mode"],
            features["sim_band0"],
        ),
    ]
    if typed_key_profile in {"rich", "richpos"}:
        keys.extend(
            [
                (
                    "schema_slot",
                    bit_pos,
                    pbin,
                    features["field"],
                    features["mode"],
                    features["slot"],
                ),
                (
                    "schema_column",
                    bit_pos,
                    pbin,
                    features["field"],
                    features["mode"],
                    features["column"],
                ),
                (
                    "schema_word",
                    bit_pos,
                    pbin,
                    features["schema_hash"],
                    features["word_len_bucket"],
                    features["word_class"],
                ),
                (
                    "sim_schema",
                    bit_pos,
                    pbin,
                    features["sim_band0"],
                    features["schema_hash"],
                ),
                (
                    "suffix_schema",
                    bit_pos,
                    pbin,
                    features["suffix_hash"],
                    features["schema_hash"],
                ),
            ]
        )
    if typed_key_profile == "richpos":
        keys.extend(
            [
                (
                    "schema_pos",
                    bit_pos,
                    pbin,
                    features["field"],
                    features["mode"],
                    features["slot"],
                    features["markup_pos_bucket"],
                ),
                (
                    "line_pos",
                    bit_pos,
                    pbin,
                    features["field"],
                    features["mode"],
                    features["line_pos_bucket"],
                ),
                (
                    "token_pos",
                    bit_pos,
                    pbin,
                    features["schema_hash"],
                    features["token_pos_bucket"],
                    features["word_class"],
                ),
                (
                    "suffix_pos",
                    bit_pos,
                    pbin,
                    features["suffix_hash"],
                    features["continuation_hash"],
                ),
                (
                    "sim_pos",
                    bit_pos,
                    pbin,
                    features["sim_band0"],
                    features["continuation_hash"],
                ),
            ]
        )
    if partial_byte_family != "none" and partial_len > 0:
        partial_bucket = fnv64_ints((partial_len, partial_prefix, bit_pos)) & 0xFFFF
        if partial_byte_family in {"direct", "all"}:
            keys.extend(
                [
                    ("partial", bit_pos, partial_len, partial_prefix),
                    ("partial_pbin", bit_pos, partial_len, partial_prefix, pbin),
                    ("partial_mode", bit_pos, partial_len, partial_prefix, features["mode"]),
                    ("partial_field", bit_pos, partial_len, partial_prefix, features["field"]),
                ]
            )
        if partial_byte_family in {"sketch", "all"}:
            keys.extend(
                [
                    (
                        "partial_suffix",
                        bit_pos,
                        partial_len,
                        partial_prefix,
                        pbin,
                        features["suffix_hash"],
                    ),
                    (
                        "partial_sim0",
                        bit_pos,
                        partial_len,
                        partial_prefix,
                        pbin,
                        features["sim_band0"],
                    ),
                    (
                        "partial_schema",
                        bit_pos,
                        partial_len,
                        partial_prefix,
                        pbin,
                        features["schema_hash"],
                    ),
                    (
                        "partial_hybrid",
                        bit_pos,
                        pbin,
                        partial_bucket,
                        features["field"],
                        features["mode"],
                        features["sim_band0"],
                    ),
                ]
            )
    return keys


def make_byte_keys(features: dict[str, Any]) -> list[tuple[Any, ...]]:
    return [
        ("byte_suffix", features["suffix_hash"]),
        ("byte_sim0", features["sim_band0"]),
        ("byte_sim1", features["sim_band1"]),
        ("byte_schema", features["schema_hash"]),
        ("byte_hybrid", features["field"], features["mode"], features["sim_band0"]),
        (
            "byte_schema_word",
            features["schema_hash"],
            features["word_len_bucket"],
            features["word_class"],
        ),
    ]


def copy_residual_keys(
    candidates: dict[str, tuple[int, int]],
    bit_pos: int,
    base_p1: int,
    p_buckets: int,
    partial_len: int,
) -> list[tuple[Any, ...]]:
    base_bucket = prob_bucket(base_p1, p_buckets)
    keys: list[tuple[Any, ...]] = []
    for band, (copy_p1, support) in candidates.items():
        support_bucket = min(7, support.bit_length() - 1)
        keys.append(
            (
                f"copy_residual_{band.removeprefix('copy_')}",
                bit_pos,
                base_bucket,
                prob_bucket(copy_p1, 16),
                support_bucket,
                partial_len,
            )
        )
    return keys


def retrieval_p1(
    table: BoundedCounterTable,
    keys: list[tuple[Any, ...]],
    min_support: int,
    alpha_num: int,
) -> tuple[int | None, int, int]:
    zeros = 0
    ones = 0
    hits = 0
    for key in keys:
        counter = table.get(key)
        if counter is None:
            continue
        zeros += counter.zeros
        ones += counter.ones
        hits += counter.total
    total = zeros + ones
    if total < min_support:
        return None, hits, total
    # alpha_num is alpha scaled by 2, so default 1 means alpha=1/2.
    denom = 2 * total + 2 * alpha_num
    numer = (2 * ones + alpha_num) * TOTAL
    return clamp_p1(numer // denom), hits, total


def byte_prior_p1(
    table: BoundedByteTable,
    keys: list[tuple[Any, ...]],
    partial_len: int,
    partial_prefix: int,
    min_support: int,
    alpha_num: int,
) -> tuple[int | None, int, int]:
    zeros = 0
    ones = 0
    hits = 0
    mask_shift = 8 - partial_len
    prefix = partial_prefix & ((1 << partial_len) - 1) if partial_len else 0
    for key in keys:
        counter = table.get(key)
        if counter is None:
            continue
        for byte_value, count in counter.items():
            if partial_len and (byte_value >> mask_shift) != prefix:
                continue
            bit = (byte_value >> (7 - partial_len)) & 1
            if bit:
                ones += count
            else:
                zeros += count
            hits += count
    total = zeros + ones
    if total < min_support:
        return None, hits, total
    denom = 2 * total + 2 * alpha_num
    numer = (2 * ones + alpha_num) * TOTAL
    return clamp_p1(numer // denom), hits, total


def band_byte_prior_p1(
    table: BoundedByteTable,
    keys: list[tuple[Any, ...]],
    partial_len: int,
    partial_prefix: int,
    min_support: int,
    alpha_num: int,
) -> dict[str, tuple[int, int]]:
    mask_shift = 8 - partial_len
    prefix = partial_prefix & ((1 << partial_len) - 1) if partial_len else 0
    output: dict[str, tuple[int, int]] = {}
    for key in keys:
        counter = table.get(key)
        if counter is None:
            continue
        zeros = 0
        ones = 0
        for byte_value, count in counter.items():
            if partial_len and (byte_value >> mask_shift) != prefix:
                continue
            if (byte_value >> (7 - partial_len)) & 1:
                ones += count
            else:
                zeros += count
        total = zeros + ones
        if total < min_support:
            continue
        denom = 2 * total + 2 * alpha_num
        numer = (2 * ones + alpha_num) * TOTAL
        output[str(key[0])] = (clamp_p1(numer // denom), total)
    return output


def band_retrieval_p1(
    table: BoundedCounterTable,
    keys: list[tuple[Any, ...]],
    min_support: int,
    alpha_num: int,
) -> tuple[dict[str, tuple[int, int]], int, int]:
    grouped: dict[str, BitCounts] = {}
    hits = 0
    total_support = 0
    for key in keys:
        counter = table.get(key)
        if counter is None:
            continue
        band = str(key[0])
        bucketed = grouped.setdefault(band, BitCounts())
        bucketed.zeros += counter.zeros
        bucketed.ones += counter.ones
        hits += counter.total
        total_support += counter.total
    out: dict[str, tuple[int, int]] = {}
    for band, counter in grouped.items():
        total = counter.total
        if total < min_support:
            continue
        denom = 2 * total + 2 * alpha_num
        numer = (2 * counter.ones + alpha_num) * TOTAL
        out[band] = (clamp_p1(numer // denom), total)
    return out, hits, total_support


def blend_probability(base_p1: int, retrieval: int | None, blend_ppm: int) -> int:
    if retrieval is None:
        return base_p1
    blend_ppm = max(0, min(1_000_000, blend_ppm))
    mixed = (base_p1 * (1_000_000 - blend_ppm) + retrieval * blend_ppm) // 1_000_000
    return clamp_p1(mixed)


@dataclass
class BandRouter:
    decay_shift: int
    base_loss_qbits: int = 256
    losses_qbits: dict[str, int] = field(default_factory=dict)
    regrets_qbits: dict[str, int] = field(default_factory=dict)

    def decay(self, value: int) -> int:
        if self.decay_shift <= 0:
            return value
        return value - int(value / (1 << self.decay_shift))

    def choose(
        self,
        candidates: dict[str, tuple[int, int]],
        base_p1: int,
        blend_ppm: int,
        allow_abstain: bool,
        abstain_margin_qbits: int,
    ) -> tuple[int, str | None]:
        if not candidates:
            return base_p1, None
        chosen_band: str | None = None
        chosen_score: tuple[int, int, str] | None = None
        for band, (_prior_p1, support) in candidates.items():
            if allow_abstain:
                score = (
                    self.regrets_qbits.get(band, 0),
                    -support,
                    band,
                )
            else:
                score = (
                    self.losses_qbits.get(band, 256),
                    -support,
                    band,
                )
            if chosen_score is None or score < chosen_score:
                chosen_score = score
                chosen_band = band
        assert chosen_band is not None
        if (
            allow_abstain
            and chosen_score is not None
            and chosen_score[0] + abstain_margin_qbits >= 0
        ):
            return base_p1, "base"
        prior_p1 = candidates[chosen_band][0]
        return blend_probability(base_p1, prior_p1, blend_ppm), chosen_band

    def update(
        self,
        bit: int,
        candidates: dict[str, tuple[int, int]],
        base_p1: int,
        blend_ppm: int,
    ) -> None:
        base_loss = qbits_for(bit, base_p1)
        self.base_loss_qbits = self.decay(self.base_loss_qbits) + base_loss
        for band, (prior_p1, _support) in candidates.items():
            corrected = blend_probability(base_p1, prior_p1, blend_ppm)
            loss = qbits_for(bit, corrected)
            old = self.losses_qbits.get(band, 256)
            self.losses_qbits[band] = self.decay(old) + loss
            regret = self.regrets_qbits.get(band, 0)
            self.regrets_qbits[band] = self.decay(regret) + loss - base_loss


@dataclass
class FixedPointBlockPosterior:
    """Causal two-expert posterior reset at deterministic byte blocks.

    The ideal Bayesian version of this mixer has a per-block log-loss regret
    bound of ``-log2(prior)`` bits against either expert.  This implementation
    keeps a fixed-point posterior so encoder and decoder need only the decoded
    prefix and counted constants.  Receipts deliberately distinguish the ideal
    bound from the measured fixed-point result.
    """

    srstc_prior_ppm: int = 500_000
    weight_bits: int = 24
    scale: int = field(init=False)
    initial_srstc_weight: int = field(init=False)
    current_block_id: int | None = field(default=None, init=False)
    srstc_weight: int = field(init=False)
    reset_count: int = field(default=0, init=False)
    rows: int = field(default=0, init=False)
    base_dominant_rows: int = field(default=0, init=False)
    srstc_dominant_rows: int = field(default=0, init=False)
    tied_rows: int = field(default=0, init=False)
    floor_clamp_count: int = field(default=0, init=False)
    ceiling_clamp_count: int = field(default=0, init=False)
    srstc_weight_sum: int = field(default=0, init=False)
    min_srstc_weight: int = field(init=False)
    max_srstc_weight: int = field(init=False)

    def __post_init__(self) -> None:
        if not 0 < self.srstc_prior_ppm < 1_000_000:
            raise ValueError("srstc_prior_ppm must be in (0, 1000000)")
        if not 8 <= self.weight_bits <= 48:
            raise ValueError("weight_bits must be in [8, 48]")
        self.scale = 1 << self.weight_bits
        initial = (self.scale * self.srstc_prior_ppm + 500_000) // 1_000_000
        self.initial_srstc_weight = max(1, min(self.scale - 1, initial))
        self.srstc_weight = self.initial_srstc_weight
        self.min_srstc_weight = self.srstc_weight
        self.max_srstc_weight = self.srstc_weight

    def _start_block(self, new_block_id: int) -> None:
        self.current_block_id = new_block_id
        self.srstc_weight = self.initial_srstc_weight
        self.reset_count += 1
        self.min_srstc_weight = min(self.min_srstc_weight, self.srstc_weight)
        self.max_srstc_weight = max(self.max_srstc_weight, self.srstc_weight)

    def mix(self, block: int, base_p1: int, srstc_p1: int) -> int:
        if block != self.current_block_id:
            self._start_block(block)
        base_weight = self.scale - self.srstc_weight
        mixed = (
            base_weight * clamp_p1(base_p1)
            + self.srstc_weight * clamp_p1(srstc_p1)
            + self.scale // 2
        ) // self.scale
        self.rows += 1
        self.srstc_weight_sum += self.srstc_weight
        if self.srstc_weight < base_weight:
            self.base_dominant_rows += 1
        elif self.srstc_weight > base_weight:
            self.srstc_dominant_rows += 1
        else:
            self.tied_rows += 1
        return clamp_p1(mixed)

    def update(self, block: int, bit: int, base_p1: int, srstc_p1: int) -> None:
        if block != self.current_block_id:
            raise ValueError("mix must be called before update for each block")
        base_p1 = clamp_p1(base_p1)
        srstc_p1 = clamp_p1(srstc_p1)
        base_likelihood = base_p1 if bit else TOTAL - base_p1
        srstc_likelihood = srstc_p1 if bit else TOTAL - srstc_p1
        srstc_numerator = self.srstc_weight * srstc_likelihood
        denominator = (
            srstc_numerator
            + (self.scale - self.srstc_weight) * base_likelihood
        )
        next_weight = (
            srstc_numerator * self.scale + denominator // 2
        ) // denominator
        if next_weight <= 0:
            next_weight = 1
            self.floor_clamp_count += 1
        elif next_weight >= self.scale:
            next_weight = self.scale - 1
            self.ceiling_clamp_count += 1
        self.srstc_weight = next_weight
        self.min_srstc_weight = min(self.min_srstc_weight, next_weight)
        self.max_srstc_weight = max(self.max_srstc_weight, next_weight)

    @property
    def srstc_weight_ppm(self) -> int:
        return (self.srstc_weight * 1_000_000 + self.scale // 2) // self.scale

    def receipt(self) -> dict[str, Any]:
        base_prior = 1.0 - self.srstc_prior_ppm / 1_000_000.0
        srstc_prior = self.srstc_prior_ppm / 1_000_000.0
        return {
            "mode": "fixed_point_block_posterior",
            "weight_bits": self.weight_bits,
            "weight_scale": self.scale,
            "srstc_prior_ppm": self.srstc_prior_ppm,
            "base_prior_ppm": 1_000_000 - self.srstc_prior_ppm,
            "rows": self.rows,
            "block_resets": self.reset_count,
            "base_dominant_rows": self.base_dominant_rows,
            "srstc_dominant_rows": self.srstc_dominant_rows,
            "tied_rows": self.tied_rows,
            "mean_srstc_weight_ppm": (
                (self.srstc_weight_sum * 1_000_000) / (self.rows * self.scale)
                if self.rows
                else None
            ),
            "min_srstc_weight_ppm": (
                self.min_srstc_weight * 1_000_000 / self.scale
            ),
            "max_srstc_weight_ppm": (
                self.max_srstc_weight * 1_000_000 / self.scale
            ),
            "floor_clamp_count": self.floor_clamp_count,
            "ceiling_clamp_count": self.ceiling_clamp_count,
            "ideal_exact_bayes_regret_bound_bits_per_block_vs_base": -math.log2(
                base_prior
            ),
            "ideal_exact_bayes_regret_bound_bits_per_block_vs_srstc": -math.log2(
                srstc_prior
            ),
            "proof_boundary": (
                "ideal exact-mixture bound is motivation only; promotion uses "
                "measured fixed-point replay and counted archive bytes"
            ),
            "causality": (
                "weight resets at public byte-block boundaries and updates only "
                "from the decoded bit plus the two causal expert probabilities"
            ),
        }


def block_id(pos: int, block_bytes: int) -> int:
    return pos // block_bytes if block_bytes > 0 else 0


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.feature_source == "wrt-row":
        data = b""
    else:
        with args.data.open("rb") as handle:
            data = handle.read(args.data_limit if args.data_limit > 0 else -1)

    state = RetrievalState(data=data, suffix_len=args.suffix_len, sketch_len=args.sketch_len)
    partial_state = PartialByteState()
    alignment = TraceAlignment(max_positions=args.alignment_max_positions)
    table = BoundedCounterTable(cap_entries=args.table_cap_entries)
    byte_table = BoundedByteTable(cap_entries=args.byte_table_cap_entries)
    copy_bands = tuple(part for part in args.wrt_copy_bands.split(",") if part)
    copy_state = (
        WrtCopyState(
            min_match=args.wrt_copy_min_match,
            max_match=args.wrt_copy_max_match,
            candidates_per_key=args.wrt_copy_candidates,
            cap_entries=args.wrt_copy_index_cap_entries,
        )
        if args.wrt_copy
        else None
    )
    router = BandRouter(decay_shift=args.router_decay_shift)
    block_posterior = FixedPointBlockPosterior(
        srstc_prior_ppm=args.block_posterior_srstc_prior_ppm,
        weight_bits=args.block_posterior_weight_bits,
    )
    baseline = BinaryArithmeticEncoder()
    candidate = BinaryArithmeticEncoder()
    heldout_baseline = BinaryArithmeticEncoder()
    heldout_candidate = BinaryArithmeticEncoder()
    totals = {name: SplitTotals() for name in ("train", "test", "all")}
    band_totals: dict[str, dict[str, SplitTotals]] = {}
    block_qbits: dict[int, SplitTotals] = {}

    rows = 0
    encoded_rows = 0
    ignored_rows = 0
    retrieval_rows = 0
    retrieval_hits = 0
    byte_prior_rows = 0
    byte_prior_hits = 0
    partial_key_rows = 0
    selected_band_counts: Counter[str] = Counter()
    min_pos: int | None = None
    max_pos: int | None = None

    for row in iter_rows(args.log):
        rows += 1
        if args.max_rows > 0 and encoded_rows >= args.max_rows:
            break
        bit = as_int(row, "bit", "actual_bit", default=-1)
        if bit not in {0, 1}:
            ignored_rows += 1
            continue
        pos = as_int(row, "pos", "position", default=-1)
        bit_pos = as_int(row, "bit_pos", default=-1)
        if pos < 0 or bit_pos < 0:
            ignored_rows += 1
            continue
        alignment.observe(
            pos,
            bit_pos,
            bit,
            as_int(row, "wrt_stream_byte", default=0)
            if args.feature_source == "wrt-row"
            else None,
        )
        base_p1 = clamp_p1(as_int(row, "p1", "fx2_p1", "probability", default=32768))
        if args.feature_source == "wrt-row":
            features = features_from_wrt_row(row)
        else:
            state.advance_to(pos)
            data_features = state.features()
        if args.feature_source == "row":
            features = features_from_row(row, data_features)
        elif args.feature_source == "data":
            features = data_features
        partial_len, partial_prefix = partial_state.advance_to(pos, bit_pos)
        if copy_state is not None:
            copy_state.prepare(row)
        keys = make_keys(
            features,
            bit_pos,
            base_p1,
            args.p_buckets,
            partial_len,
            partial_prefix,
            args.partial_byte_family,
            args.typed_key_profile,
        )
        byte_keys = make_byte_keys(features)
        byte_prior, byte_hits, byte_support = byte_prior_p1(
            byte_table,
            byte_keys,
            partial_len,
            partial_prefix,
            min_support=args.byte_min_support,
            alpha_num=args.alpha2,
        )
        byte_band_candidates = (
            band_byte_prior_p1(
                byte_table,
                byte_keys,
                partial_len,
                partial_prefix,
                min_support=args.byte_min_support,
                alpha_num=args.alpha2,
            )
            if args.byte_prior_as_band
            else {}
        )
        copy_band_candidates = (
            copy_state.band_candidates(
                row,
                partial_len,
                partial_prefix,
                alpha_num=args.alpha2,
                bands=copy_bands,
            )
            if copy_state is not None
            else {}
        )
        keys.extend(
            copy_residual_keys(
                copy_band_candidates,
                bit_pos,
                base_p1,
                args.p_buckets,
                partial_len,
            )
        )
        band_candidates: dict[str, tuple[int, int]] = {}
        selected_band: str | None = None
        if args.expert_mode in {"best_band", "best_band_abstain"}:
            band_candidates, hits, support = band_retrieval_p1(
                table,
                keys,
                min_support=args.min_support,
                alpha_num=args.alpha2,
            )
            band_candidates.update(byte_band_candidates)
            if args.wrt_copy_direct:
                band_candidates.update(copy_band_candidates)
            corrected_p1, selected_band = router.choose(
                band_candidates,
                base_p1,
                args.blend_ppm,
                args.expert_mode == "best_band_abstain",
                args.router_abstain_margin_qbits,
            )
            prior_p1 = corrected_p1 if selected_band not in {None, "base"} else None
        else:
            prior_p1, hits, support = retrieval_p1(
                table,
                keys,
                min_support=args.min_support,
                alpha_num=args.alpha2,
            )
            corrected_p1 = blend_probability(base_p1, prior_p1, args.blend_ppm)

        if not args.byte_prior_as_band and args.byte_prior_blend_ppm > 0:
            corrected_p1 = blend_probability(corrected_p1, byte_prior, args.byte_prior_blend_ppm)

        current_block = block_id(pos, args.block_bytes)
        raw_srstc_p1 = corrected_p1
        if args.block_router_mode == "posterior":
            corrected_p1 = block_posterior.mix(
                current_block, base_p1, raw_srstc_p1
            )

        baseline.encode(bit, base_p1)
        candidate.encode(bit, corrected_p1)
        split = split_for(pos, args.train_bytes)
        if split == "test":
            heldout_baseline.encode(bit, base_p1)
            heldout_candidate.encode(bit, corrected_p1)
        if prior_p1 is not None:
            retrieval_rows += 1
            retrieval_hits += hits
        if byte_prior is not None:
            byte_prior_rows += 1
            byte_prior_hits += byte_hits
        if selected_band is not None:
            selected_band_counts[selected_band] += 1
        if partial_len > 0 and args.partial_byte_family != "none":
            partial_key_rows += 1

        base_qbits = qbits_for(bit, base_p1)
        candidate_qbits = qbits_for(bit, corrected_p1)
        for name in (split, "all"):
            total = totals[name]
            total.rows += 1
            total.baseline_qbits += base_qbits
            total.candidate_qbits += candidate_qbits
            if split == "all":
                break
        for band, (band_p1, _band_support) in band_candidates.items():
            corrected_band_p1 = blend_probability(base_p1, band_p1, args.blend_ppm)
            band_qbits = qbits_for(bit, corrected_band_p1)
            splits = band_totals.setdefault(
                band,
                {name: SplitTotals() for name in ("train", "test", "all")},
            )
            for name in (split, "all"):
                band_total = splits[name]
                band_total.rows += 1
                band_total.baseline_qbits += base_qbits
                band_total.candidate_qbits += band_qbits
                if split == "all":
                    break
        block = block_qbits.setdefault(current_block, SplitTotals())
        block.rows += 1
        block.baseline_qbits += base_qbits
        block.candidate_qbits += candidate_qbits

        for key in keys:
            table.update(key, bit)
        if args.expert_mode in {"best_band", "best_band_abstain"}:
            router.update(bit, band_candidates, base_p1, args.blend_ppm)
        if args.block_router_mode == "posterior":
            block_posterior.update(current_block, bit, base_p1, raw_srstc_p1)
        partial_state.observe(pos, bit)
        if partial_state.length == 8:
            for key in byte_keys:
                byte_table.update(key, partial_state.prefix)
            if copy_state is not None:
                copy_state.observe_byte(partial_state.prefix, row)

        encoded_rows += 1
        min_pos = pos if min_pos is None else min(min_pos, pos)
        max_pos = pos if max_pos is None else max(max_pos, pos)

    baseline.finish()
    candidate.finish()
    heldout_rows = totals["test"].rows
    if heldout_rows:
        heldout_baseline.finish()
        heldout_candidate.finish()

    block_rows = []
    largest_regression = 0.0
    positive_block_count = 0
    block_regression_count = 0
    positive_block_gain_bytes = 0.0
    for bid, total in sorted(block_qbits.items()):
        gain_bytes = total.gain_bytes
        if gain_bytes < 0:
            largest_regression = max(largest_regression, -gain_bytes)
            block_regression_count += 1
        elif gain_bytes > 0:
            positive_block_count += 1
            positive_block_gain_bytes += gain_bytes
        block_rows.append(
            {
                "block_id": bid,
                "rows": total.rows,
                "gain_bytes": gain_bytes,
            }
        )
    block_rows.sort(key=lambda item: item["gain_bytes"])

    heldout_saved_bytes = (
        heldout_baseline.byte_count - heldout_candidate.byte_count if heldout_rows else None
    )
    shadow_saved_bytes = baseline.byte_count - candidate.byte_count
    net_saved_bytes = (
        heldout_saved_bytes
        - args.added_code_bytes_estimate
        - args.added_static_table_bytes
        if heldout_saved_bytes is not None
        else None
    )
    if encoded_rows == 0:
        verdict = "incomplete"
    elif net_saved_bytes is not None and net_saved_bytes > 0:
        verdict = "positive_shadow_only"
    elif heldout_saved_bytes is not None and heldout_saved_bytes > 0:
        verdict = "positive_shadow_only"
    elif heldout_saved_bytes is None and shadow_saved_bytes > 0:
        verdict = "positive_shadow_only"
    elif heldout_saved_bytes is not None and heldout_saved_bytes < 0:
        verdict = "negative_shadow"
    elif heldout_saved_bytes == 0:
        verdict = "flat_shadow"
    else:
        verdict = "incomplete"

    data_hash = hashlib.sha256(data).hexdigest()
    bands = ["suffix", "sim0", "sim1", "schema", "hybrid"]
    if args.typed_key_profile in {"rich", "richpos"}:
        bands.extend(
            [
                "schema_slot",
                "schema_column",
                "schema_word",
                "sim_schema",
                "suffix_schema",
            ]
        )
    if args.typed_key_profile == "richpos":
        bands.extend(["schema_pos", "line_pos", "token_pos", "suffix_pos", "sim_pos"])
    if args.partial_byte_family in {"direct", "all"}:
        bands.extend(["partial", "partial_pbin", "partial_mode", "partial_field"])
    if args.partial_byte_family in {"sketch", "all"}:
        bands.extend(["partial_suffix", "partial_sim0", "partial_schema", "partial_hybrid"])
    if args.byte_prior_as_band:
        bands.extend(
            [
                "byte_suffix",
                "byte_sim0",
                "byte_sim1",
                "byte_schema",
                "byte_hybrid",
                "byte_schema_word",
            ]
        )
    if args.wrt_copy:
        bands.extend(
            [f"copy_residual_{band.removeprefix('copy_')}" for band in copy_bands]
        )
        if args.wrt_copy_direct:
            bands.extend(copy_bands)
    sketch_schema = {
        "suffix_len": args.suffix_len,
        "sketch_len": args.sketch_len,
        "p_buckets": args.p_buckets,
        "min_support": args.min_support,
        "blend_ppm": args.blend_ppm,
        "table_cap_entries": args.table_cap_entries,
        "feature_source": args.feature_source,
        "alignment_max_positions": args.alignment_max_positions,
        "partial_byte_family": args.partial_byte_family,
        "typed_key_profile": args.typed_key_profile,
        "partial_byte_state": args.partial_byte_family != "none",
        "byte_table_cap_entries": args.byte_table_cap_entries,
        "byte_prior_blend_ppm": args.byte_prior_blend_ppm,
        "byte_prior_as_band": args.byte_prior_as_band,
        "byte_min_support": args.byte_min_support,
        "wrt_copy": args.wrt_copy,
        "wrt_copy_bands": list(copy_bands),
        "wrt_copy_direct": args.wrt_copy_direct,
        "wrt_copy_min_match": args.wrt_copy_min_match,
        "wrt_copy_max_match": args.wrt_copy_max_match,
        "wrt_copy_candidates": args.wrt_copy_candidates,
        "wrt_copy_index_cap_entries": args.wrt_copy_index_cap_entries,
        "expert_mode": args.expert_mode,
        "router_decay_shift": args.router_decay_shift,
        "router_abstain_margin_qbits": args.router_abstain_margin_qbits,
        "block_router_mode": args.block_router_mode,
        "block_posterior_srstc_prior_ppm": args.block_posterior_srstc_prior_ppm,
        "block_posterior_weight_bits": args.block_posterior_weight_bits,
        "bands": bands,
    }
    sketch_schema_hash = hashlib.sha256(
        json.dumps(sketch_schema, sort_keys=True).encode("utf-8")
    ).hexdigest()
    alignment_report = (
        alignment.report_wrt()
        if args.feature_source == "wrt-row"
        else alignment.report(data)
    )
    checked_key = (
        "complete_prior_bytes_checked"
        if args.feature_source == "wrt-row"
        else "complete_bytes_checked"
    )
    alignment_valid_for_feature_source = not (
        args.feature_source in {"data", "wrt-row"}
        and alignment_report.get(checked_key)
        and alignment_report.get("warning")
    )
    proof_blocker = None
    if not alignment_valid_for_feature_source:
        proof_blocker = (
            "the selected feature source is not aligned with the decoded trace bits"
        )
        if verdict != "incomplete":
            verdict = "invalid_trace_alignment"

    return {
        "receipt_type": "streaming_retrieval_shadow",
        "trace_version": "fx2_shadow_trace_v1",
        "method": "streaming_retrieval_shadow_v2",
        "base_trace": str(args.log),
        "data": str(args.data),
        "data_role": (
            "unused; WRT stream and shell state are decoder-rebuilt from trace rows"
            if args.feature_source == "wrt-row"
            else "causal source bytes"
        ),
        "data_sha256": data_hash,
        "data_bytes_loaded": len(data),
        "scope_bytes": args.scope_bytes,
        "target": {
            "baseline_score": args.baseline_score,
            "target_score": args.target_score,
            "required_net_gain_bytes": args.baseline_score - args.target_score,
        },
        "position_span": {"min_pos": min_pos, "max_pos": max_pos},
        "rows": rows,
        "encoded_rows": encoded_rows,
        "ignored_rows": ignored_rows,
        "train_bytes": args.train_bytes,
        "feature_source": args.feature_source,
        "trace_data_alignment": alignment_report,
        "trace_alignment_valid_for_feature_source": alignment_valid_for_feature_source,
        "proof_blocker": proof_blocker,
        "sketch_schema": sketch_schema,
        "sketch_schema_hash": sketch_schema_hash,
        "retrieval_table_cap_entries": args.table_cap_entries,
        "retrieved_neighbors_per_bit": {
            "retrieval_rows": retrieval_rows,
            "mean_hits_when_used": retrieval_hits / retrieval_rows if retrieval_rows else 0.0,
            "partial_key_rows": partial_key_rows,
            "byte_prior_rows": byte_prior_rows,
            "mean_byte_hits_when_used": byte_prior_hits / byte_prior_rows if byte_prior_rows else 0.0,
            "selected_band_counts": dict(sorted(selected_band_counts.items())),
            "router_base_loss_qbits": router.base_loss_qbits,
            "router_loss_qbits": dict(sorted(router.losses_qbits.items())),
            "router_regret_qbits": dict(sorted(router.regrets_qbits.items())),
        },
        "causal_band_attribution": [
            {
                "band": band,
                "splits": {
                    name: {
                        "eligible_rows": total.rows,
                        "gain_bits": total.gain_bits,
                        "gain_bytes": total.gain_bytes,
                    }
                    for name, total in splits.items()
                },
            }
            for band, splits in sorted(
                band_totals.items(),
                key=lambda item: (
                    -item[1]["test"].gain_bytes,
                    -item[1]["train"].gain_bytes,
                    item[0],
                ),
            )
        ],
        "base_shadow_bytes": baseline.byte_count,
        "candidate_shadow_bytes": candidate.byte_count,
        "shadow_saved_bytes": shadow_saved_bytes,
        "heldout_shadow_bytes": heldout_candidate.byte_count if heldout_rows else None,
        "heldout_base_shadow_bytes": heldout_baseline.byte_count if heldout_rows else None,
        "heldout_shadow_saved_bytes": heldout_saved_bytes,
        "added_code_bytes_estimate": args.added_code_bytes_estimate,
        "added_static_table_bytes": args.added_static_table_bytes,
        "max_online_state_bytes": (
            args.table_cap_entries * 32
            + args.byte_table_cap_entries * 96
            + (args.wrt_copy_index_cap_entries * 40 if args.wrt_copy else 0)
            + (32 if args.block_router_mode == "posterior" else 0)
        ),
        "block_router": {
            "mode": args.block_router_mode,
            "posterior": (
                block_posterior.receipt()
                if args.block_router_mode == "posterior"
                else None
            ),
        },
        "largest_block_regression_bytes": largest_regression,
        "block_regression_count": block_regression_count,
        "positive_block_count": positive_block_count,
        "positive_block_gain_bytes": positive_block_gain_bytes,
        "positive_block_gain_share": (
            positive_block_gain_bytes / shadow_saved_bytes
            if shadow_saved_bytes > 0
            else None
        ),
        "net_saved_bytes": net_saved_bytes,
        "block_rows": block_rows,
        "split_qbit_totals": {
            name: {
                "rows": total.rows,
                "gain_bits": total.gain_bits,
                "gain_bytes": total.gain_bytes,
            }
            for name, total in totals.items()
        },
        "worst_blocks_by_qbit_loss": block_rows[:10],
        "exact_shadow_arithmetic": {
            "baseline_same_coder": {
                "encoded_bits": baseline.bit_count,
                "archive_bytes": baseline.byte_count,
            },
            "shadow_coder": {
                "encoded_bits": candidate.bit_count,
                "archive_bytes": candidate.byte_count,
            },
            "same_coder_delta": {
                "saved_bits": baseline.bit_count - candidate.bit_count,
                "saved_bytes": shadow_saved_bytes,
            },
            "heldout_same_coder_delta": {
                "saved_bits": heldout_baseline.bit_count - heldout_candidate.bit_count
                if heldout_rows
                else None,
                "saved_bytes": heldout_saved_bytes,
            },
        },
        "causality": (
            "features are computed from bytes before row.pos and bits already "
            "decoded in the current byte; retrieval counters are updated only "
            "after encoding the current bit; best-band router losses and the "
            "base abstention baseline are also updated only after the current bit; "
            "posterior weights reset at deterministic byte blocks and update only "
            "after the current bit"
        ),
        "verdict": verdict,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a lock-safe streaming retrieval shadow probe.")
    parser.add_argument("log", type=pathlib.Path)
    parser.add_argument("--data", type=pathlib.Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--data-limit", type=int, default=0)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--train-bytes", type=int, default=30_000)
    parser.add_argument("--suffix-len", type=int, default=32)
    parser.add_argument("--sketch-len", type=int, default=96)
    parser.add_argument(
        "--feature-source",
        choices=("data", "row", "wrt-row"),
        default="data",
        help="derive semantic sketch state from supplied data bytes or logged residual row fields",
    )
    parser.add_argument(
        "--alignment-max-positions",
        type=int,
        default=4096,
        help="number of byte positions to use for trace/data bit-alignment diagnostics",
    )
    parser.add_argument("--p-buckets", type=int, default=32)
    parser.add_argument("--min-support", type=int, default=4)
    parser.add_argument("--blend-ppm", type=int, default=50_000)
    parser.add_argument("--alpha2", type=int, default=1, help="alpha scaled by 2; 1 means KT alpha=1/2")
    parser.add_argument("--table-cap-entries", type=int, default=200_000)
    parser.add_argument("--byte-table-cap-entries", type=int, default=100_000)
    parser.add_argument(
        "--partial-byte-family",
        choices=("none", "sketch", "direct", "all"),
        default="sketch",
        help="causal current-byte prefix key family to add to the retrieval table",
    )
    parser.add_argument(
        "--typed-key-profile",
        choices=("base", "rich", "richpos"),
        default="base",
        help="typed retrieval key family; richpos adds causal continuation-position keys",
    )
    parser.add_argument(
        "--expert-mode",
        choices=("aggregate", "best_band", "best_band_abstain"),
        default="aggregate",
        help="combine keys, route through the best band, or let the router abstain to base",
    )
    parser.add_argument(
        "--router-decay-shift",
        type=int,
        default=6,
        help="EMA decay shift for --expert-mode best_band",
    )
    parser.add_argument(
        "--router-abstain-margin-qbits",
        type=int,
        default=0,
        help="extra qbit advantage a band must beat over base in best_band_abstain mode",
    )
    parser.add_argument("--byte-prior-blend-ppm", type=int, default=0)
    parser.add_argument(
        "--byte-prior-as-band",
        action="store_true",
        help="expose the byte-continuation prior as a routable expert band instead of a forced blend",
    )
    parser.add_argument("--byte-min-support", type=int, default=4)
    parser.add_argument("--wrt-copy", action="store_true")
    parser.add_argument("--wrt-copy-direct", action="store_true")
    parser.add_argument(
        "--wrt-copy-bands",
        default="copy_global,copy_page,copy_typed,copy_title",
    )
    parser.add_argument("--wrt-copy-min-match", type=int, default=3)
    parser.add_argument("--wrt-copy-max-match", type=int, default=16)
    parser.add_argument("--wrt-copy-candidates", type=int, default=8)
    parser.add_argument("--wrt-copy-index-cap-entries", type=int, default=200_000)
    parser.add_argument("--block-bytes", type=int, default=16_384)
    parser.add_argument(
        "--block-router-mode",
        choices=("none", "posterior"),
        default="none",
    )
    parser.add_argument("--block-posterior-srstc-prior-ppm", type=int, default=500_000)
    parser.add_argument("--block-posterior-weight-bits", type=int, default=24)
    parser.add_argument("--scope-bytes", type=int, default=DEFAULT_SCOPE_BYTES)
    parser.add_argument("--baseline-score", type=int, default=DEFAULT_BASELINE_SCORE)
    parser.add_argument("--target-score", type=int, default=DEFAULT_TARGET_SCORE)
    parser.add_argument("--added-code-bytes-estimate", type=int, default=12_288)
    parser.add_argument("--added-static-table-bytes", type=int, default=0)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if not args.log.exists():
        raise SystemExit(f"missing log: {args.log}")
    if not args.data.exists():
        raise SystemExit(f"missing data: {args.data}")
    if args.scope_bytes <= 0:
        raise SystemExit("--scope-bytes must be positive")
    if args.baseline_score < args.target_score:
        raise SystemExit("--baseline-score must be >= --target-score")
    if args.suffix_len <= 0 or args.sketch_len <= 0:
        raise SystemExit("--suffix-len and --sketch-len must be positive")
    if args.alignment_max_positions < 0:
        raise SystemExit("--alignment-max-positions must be nonnegative")
    if args.p_buckets <= 0 or args.min_support <= 0:
        raise SystemExit("--p-buckets and --min-support must be positive")
    if args.table_cap_entries <= 0:
        raise SystemExit("--table-cap-entries must be positive")
    allowed_copy_bands = {"copy_global", "copy_page", "copy_typed", "copy_title"}
    requested_copy_bands = {
        part for part in args.wrt_copy_bands.split(",") if part
    }
    if requested_copy_bands - allowed_copy_bands:
        raise SystemExit("--wrt-copy-bands contains an unknown band")
    if args.wrt_copy and args.feature_source != "wrt-row":
        raise SystemExit("--wrt-copy requires --feature-source wrt-row")
    if not 2 <= args.wrt_copy_min_match <= args.wrt_copy_max_match:
        raise SystemExit("require 2 <= --wrt-copy-min-match <= --wrt-copy-max-match")
    if args.wrt_copy_candidates <= 0 or args.wrt_copy_index_cap_entries <= 0:
        raise SystemExit("WRT copy candidates and index cap must be positive")
    if args.byte_table_cap_entries <= 0 or args.byte_min_support <= 0:
        raise SystemExit("--byte-table-cap-entries and --byte-min-support must be positive")
    if args.byte_prior_blend_ppm < 0 or args.byte_prior_blend_ppm > 1_000_000:
        raise SystemExit("--byte-prior-blend-ppm must be between 0 and 1000000")
    if args.router_decay_shift < 0:
        raise SystemExit("--router-decay-shift must be nonnegative")
    if args.router_abstain_margin_qbits < 0:
        raise SystemExit("--router-abstain-margin-qbits must be nonnegative")
    if not 0 < args.block_posterior_srstc_prior_ppm < 1_000_000:
        raise SystemExit("--block-posterior-srstc-prior-ppm must be in (0, 1000000)")
    if not 8 <= args.block_posterior_weight_bits <= 48:
        raise SystemExit("--block-posterior-weight-bits must be in [8, 48]")

    result = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.print_summary:
        print(f"encoded_rows={result['encoded_rows']}")
        print(f"shadow_saved_bytes={result['shadow_saved_bytes']}")
        print(f"heldout_shadow_saved_bytes={result['heldout_shadow_saved_bytes']}")
        print(f"net_saved_bytes={result['net_saved_bytes']}")
        print(f"verdict={result['verdict']}")
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
