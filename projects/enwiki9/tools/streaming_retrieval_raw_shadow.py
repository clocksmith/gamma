#!/usr/bin/env python3
"""Raw byte-aligned SRSTC shadow probe.

This lock-safe probe tests the streaming retrieval idea on the actual raw
`enwik9` bitstream instead of cached residual rows. It is not a submission
compressor: the baseline is a small adaptive bit context model, and the
candidate adds SRSTC-style retrieval priors on top of that same baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import sys
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from fx2_shadow_residual_coder import TOTAL, BinaryArithmeticEncoder, clamp_p1, prob_bucket
from streaming_retrieval_shadow import (
    BandRouter,
    BitCounts,
    BoundedCounterTable,
    PartialByteState,
    RetrievalState,
    SplitTotals,
    band_retrieval_p1,
    blend_probability,
    block_id,
    make_keys,
    qbits_for,
    retrieval_p1,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_OUT = ROOT / "results" / "streaming_retrieval_shadow" / "raw_latest.json"
DEFAULT_BASELINE_SCORE = 110_181_114
DEFAULT_TARGET_SCORE = 109_500_000
DEFAULT_SCOPE_BYTES = 1_000_000_000
LOGIT_SCALE = 4096
LOGIT_CLIP = 12 * LOGIT_SCALE
COPY_WEIGHT_SCALE = 4096
COPY_ENTRY_RESIDENT_BYTES = 64


@dataclass
class RawContextModel:
    cap_entries: int
    p_buckets: int
    order: int
    table: BoundedCounterTable = field(init=False)

    def __post_init__(self) -> None:
        self.table = BoundedCounterTable(cap_entries=self.cap_entries)

    def key(self, history: bytes, bit_pos: int, partial_len: int, partial_prefix: int) -> tuple[Any, ...]:
        if self.order <= 0:
            suffix: tuple[int, ...] = ()
        else:
            suffix = tuple(history[-self.order:])
        return ("raw_base", bit_pos, partial_len, partial_prefix, suffix)

    def predict(
        self,
        history: bytes,
        bit_pos: int,
        partial_len: int,
        partial_prefix: int,
        alpha2: int,
    ) -> int:
        counter = self.table.get(self.key(history, bit_pos, partial_len, partial_prefix))
        if counter is None:
            return TOTAL // 2
        total = counter.total
        denom = 2 * total + 2 * alpha2
        numer = (2 * counter.ones + alpha2) * TOTAL
        return clamp_p1(numer // denom)

    def update(self, history: bytes, bit_pos: int, partial_len: int, partial_prefix: int, bit: int) -> None:
        self.table.update(self.key(history, bit_pos, partial_len, partial_prefix), bit)


@dataclass
class BoundedByteTable:
    """Bounded LRU table from causal sketch keys to observed next-byte counts."""

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


@lru_cache(maxsize=131_072)
def logit_q12(p1: int) -> int:
    p1 = max(1, min(TOTAL - 1, int(p1)))
    return int(round(math.log(p1 / (TOTAL - p1)) * LOGIT_SCALE))


def p1_from_logit_q12(value: int) -> int:
    value = max(-LOGIT_CLIP, min(LOGIT_CLIP, value))
    p = 1.0 / (1.0 + math.exp(-(value / LOGIT_SCALE)))
    return clamp_p1(int(round(p * TOTAL)))


def log_odds_mix_probability(
    base_p1: int,
    weighted_priors: list[tuple[int | None, int]],
) -> int:
    value = logit_q12(base_p1)
    active = False
    for prior_p1, weight_ppm in weighted_priors:
        if prior_p1 is None or weight_ppm <= 0:
            continue
        active = True
        weight_ppm = max(0, min(1_000_000, int(weight_ppm)))
        value += (logit_q12(prior_p1) * weight_ppm) // 1_000_000
    if not active:
        return base_p1
    return p1_from_logit_q12(value)


def copy_type_for(features: dict[str, Any]) -> str:
    field = int(features.get("field", 0))
    mode = int(features.get("mode", 0))
    slot = int(features.get("slot", 0))
    word_class = int(features.get("word_class", 0))
    word_len_bucket = int(features.get("word_len_bucket", 0))
    if field == 1:
        return "title"
    if slot == 7:
        return "url"
    if slot in {5, 6, 9}:
        return "ref"
    if slot == 4:
        return "infobox"
    if mode == 4:
        return "table"
    if mode == 2:
        return "template"
    if slot == 1 or mode == 1:
        return "category_link"
    if field == 6 and word_class in {1, 2} and word_len_bucket >= 2:
        return "entity"
    return "prose"


def make_copy_keys(features: dict[str, Any], type_name: str) -> list[tuple[Any, ...]]:
    return [
        ("copy_suffix", type_name, features["suffix_hash"]),
        ("copy_sim0", type_name, features["sim_band0"]),
        ("copy_sim1", type_name, features["sim_band1"]),
        ("copy_schema", type_name, features["schema_hash"]),
        ("copy_schema_suffix", type_name, features["schema_hash"], features["suffix_hash"]),
        (
            "copy_schema_word",
            type_name,
            features["schema_hash"],
            features["word_len_bucket"],
            features["word_class"],
        ),
        (
            "copy_slot",
            type_name,
            features["field"],
            features["mode"],
            features["slot"],
        ),
        (
            "copy_hybrid",
            type_name,
            features["field"],
            features["mode"],
            features["sim_band0"],
        ),
    ]


def parse_copy_offsets(value: str) -> tuple[int, ...]:
    offsets: list[int] = []
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        offsets.append(int(raw))
    if not offsets:
        raise ValueError("copy offsets must include at least one offset")
    return tuple(dict.fromkeys(offsets))


def parse_copy_type_blends(value: str) -> dict[str, int]:
    blends: dict[str, int] = {}
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        if "=" not in raw:
            raise ValueError(
                "--copy-channel-type-blends entries must look like prose=320000"
            )
        raw_key, raw_blend = raw.split("=", 1)
        key = raw_key.strip()
        if key.startswith("copy_"):
            key = key[len("copy_") :]
        if not key:
            raise ValueError("--copy-channel-type-blends contains an empty copy type")
        blend = int(raw_blend.strip())
        if blend < 0 or blend > 1_000_000:
            raise ValueError("copy type blends must be between 0 and 1000000")
        blends[key] = blend
    return blends


@dataclass
class CopyEntry:
    entry_id: int
    pos: int
    type_name: str
    simhash16: int
    suffix_hash: int
    schema_hash: int
    field: int
    mode: int
    slot: int
    column: int
    word_len_bucket: int
    word_class: int
    gain_qbits: int = 0
    heldout_gain_qbits: int = 0
    uses: int = 0


@dataclass
class CopyTypeStats:
    entries: int = 0
    resident_bytes: int = 0
    evictions: int = 0
    uses: int = 0
    gain_qbits: int = 0
    heldout_gain_qbits: int = 0

    def receipt(self) -> dict[str, Any]:
        return {
            "entries": self.entries,
            "resident_bytes": self.resident_bytes,
            "evictions": self.evictions,
            "uses": self.uses,
            "gain_bytes": self.gain_qbits / 2048.0,
            "heldout_gain_bytes": self.heldout_gain_qbits / 2048.0,
            "mdl_value_qbits_per_resident_byte": (
                self.heldout_gain_qbits / self.resident_bytes
                if self.resident_bytes
                else 0.0
            ),
        }


@dataclass
class CopyPrior:
    p1: int
    hits: int
    support_weight: int
    type_name: str
    entry_ids: tuple[int, ...]
    candidates_scanned: int = 0
    best_sketch_distance: int | None = None
    mean_sketch_distance: float | None = None
    mean_abs_offset: float | None = None
    mean_age_bucket: float | None = None
    mean_edit_distance: float | None = None


@dataclass
class AttributionStats:
    rows: int = 0
    heldout_rows: int = 0
    selected_rows: int = 0
    selected_heldout_rows: int = 0
    positive_rows: int = 0
    negative_rows: int = 0
    heldout_positive_rows: int = 0
    heldout_negative_rows: int = 0
    direct_gain_qbits_vs_base: int = 0
    heldout_direct_gain_qbits_vs_base: int = 0
    selected_gain_qbits_vs_base: int = 0
    heldout_selected_gain_qbits_vs_base: int = 0
    direct_gain_qbits_vs_typed: int = 0
    direct_gain_qbits_vs_byte: int = 0
    direct_gain_qbits_vs_copy: int = 0
    heldout_direct_gain_qbits_vs_typed: int = 0
    heldout_direct_gain_qbits_vs_byte: int = 0
    heldout_direct_gain_qbits_vs_copy: int = 0
    hits: int = 0
    support: int = 0
    copy_candidates_scanned: int = 0
    copy_best_sketch_distance_sum: int = 0
    copy_best_sketch_distance_rows: int = 0
    copy_mean_sketch_distance_sum: float = 0.0
    copy_mean_abs_offset_sum: float = 0.0
    copy_mean_age_bucket_sum: float = 0.0
    copy_mean_edit_distance_sum: float = 0.0
    copy_quality_rows: int = 0

    def record(
        self,
        *,
        bit: int,
        prior_p1: int,
        base_qbits: int,
        split: str,
        selected: bool,
        typed_p1: int | None = None,
        byte_p1: int | None = None,
        copy_p1: int | None = None,
        hits: int = 0,
        support: int = 0,
        copy_prior: CopyPrior | None = None,
    ) -> None:
        self.rows += 1
        if split == "test":
            self.heldout_rows += 1
        if selected:
            self.selected_rows += 1
            if split == "test":
                self.selected_heldout_rows += 1

        prior_qbits = qbits_for(bit, prior_p1)
        gain_vs_base = base_qbits - prior_qbits
        self.direct_gain_qbits_vs_base += gain_vs_base
        if gain_vs_base > 0:
            self.positive_rows += 1
            if split == "test":
                self.heldout_positive_rows += 1
        elif gain_vs_base < 0:
            self.negative_rows += 1
            if split == "test":
                self.heldout_negative_rows += 1
        if split == "test":
            self.heldout_direct_gain_qbits_vs_base += gain_vs_base
        if selected:
            self.selected_gain_qbits_vs_base += gain_vs_base
            if split == "test":
                self.heldout_selected_gain_qbits_vs_base += gain_vs_base

        if typed_p1 is not None:
            gain_vs_typed = qbits_for(bit, typed_p1) - prior_qbits
            self.direct_gain_qbits_vs_typed += gain_vs_typed
            if split == "test":
                self.heldout_direct_gain_qbits_vs_typed += gain_vs_typed
        if byte_p1 is not None:
            gain_vs_byte = qbits_for(bit, byte_p1) - prior_qbits
            self.direct_gain_qbits_vs_byte += gain_vs_byte
            if split == "test":
                self.heldout_direct_gain_qbits_vs_byte += gain_vs_byte
        if copy_p1 is not None:
            gain_vs_copy = qbits_for(bit, copy_p1) - prior_qbits
            self.direct_gain_qbits_vs_copy += gain_vs_copy
            if split == "test":
                self.heldout_direct_gain_qbits_vs_copy += gain_vs_copy

        self.hits += hits
        self.support += support
        if copy_prior is not None:
            self.copy_candidates_scanned += copy_prior.candidates_scanned
            if copy_prior.best_sketch_distance is not None:
                self.copy_best_sketch_distance_sum += copy_prior.best_sketch_distance
                self.copy_best_sketch_distance_rows += 1
            if (
                copy_prior.mean_sketch_distance is not None
                and copy_prior.mean_abs_offset is not None
                and copy_prior.mean_age_bucket is not None
                and copy_prior.mean_edit_distance is not None
            ):
                self.copy_mean_sketch_distance_sum += copy_prior.mean_sketch_distance
                self.copy_mean_abs_offset_sum += copy_prior.mean_abs_offset
                self.copy_mean_age_bucket_sum += copy_prior.mean_age_bucket
                self.copy_mean_edit_distance_sum += copy_prior.mean_edit_distance
                self.copy_quality_rows += 1

    def receipt(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "heldout_rows": self.heldout_rows,
            "selected_rows": self.selected_rows,
            "selected_heldout_rows": self.selected_heldout_rows,
            "positive_rows": self.positive_rows,
            "negative_rows": self.negative_rows,
            "heldout_positive_rows": self.heldout_positive_rows,
            "heldout_negative_rows": self.heldout_negative_rows,
            "direct_gain_bytes_vs_base": self.direct_gain_qbits_vs_base / 2048.0,
            "heldout_direct_gain_bytes_vs_base": (
                self.heldout_direct_gain_qbits_vs_base / 2048.0
            ),
            "selected_gain_bytes_vs_base": self.selected_gain_qbits_vs_base / 2048.0,
            "heldout_selected_gain_bytes_vs_base": (
                self.heldout_selected_gain_qbits_vs_base / 2048.0
            ),
            "direct_gain_bytes_vs_typed": self.direct_gain_qbits_vs_typed / 2048.0,
            "direct_gain_bytes_vs_byte_prior": self.direct_gain_qbits_vs_byte / 2048.0,
            "direct_gain_bytes_vs_copy": self.direct_gain_qbits_vs_copy / 2048.0,
            "heldout_direct_gain_bytes_vs_typed": (
                self.heldout_direct_gain_qbits_vs_typed / 2048.0
            ),
            "heldout_direct_gain_bytes_vs_byte_prior": (
                self.heldout_direct_gain_qbits_vs_byte / 2048.0
            ),
            "heldout_direct_gain_bytes_vs_copy": (
                self.heldout_direct_gain_qbits_vs_copy / 2048.0
            ),
            "mean_hits": self.hits / self.rows if self.rows else 0.0,
            "mean_support": self.support / self.rows if self.rows else 0.0,
            "mean_copy_candidates_scanned": (
                self.copy_candidates_scanned / self.rows if self.rows else 0.0
            ),
            "mean_copy_best_sketch_distance": (
                self.copy_best_sketch_distance_sum / self.copy_best_sketch_distance_rows
                if self.copy_best_sketch_distance_rows
                else None
            ),
            "mean_copy_sketch_distance": (
                self.copy_mean_sketch_distance_sum / self.copy_quality_rows
                if self.copy_quality_rows
                else None
            ),
            "mean_copy_abs_offset": (
                self.copy_mean_abs_offset_sum / self.copy_quality_rows
                if self.copy_quality_rows
                else None
            ),
            "mean_copy_age_bucket": (
                self.copy_mean_age_bucket_sum / self.copy_quality_rows
                if self.copy_quality_rows
                else None
            ),
            "mean_copy_edit_distance": (
                self.copy_mean_edit_distance_sum / self.copy_quality_rows
                if self.copy_quality_rows
                else None
            ),
        }


@dataclass
class TypedCopyChannel:
    cap_entries: int
    top_k: int
    max_key_scan: int
    offsets: tuple[int, ...]
    age_shift: int
    sketch_penalty: int
    type_penalty: int
    slot_penalty: int
    word_penalty: int
    column_penalty: int
    offset_penalty: int
    age_penalty: int
    edit_penalty: int
    edit_distance: int
    escape_ppm: int
    entries: dict[int, CopyEntry] = field(default_factory=dict)
    key_index: dict[tuple[Any, ...], list[int]] = field(default_factory=dict)
    order: list[int] = field(default_factory=list)
    cursor: int = 0
    next_entry_id: int = 1
    type_stats: dict[str, CopyTypeStats] = field(default_factory=dict)
    retrieval_rows: int = 0
    retrieval_hits: int = 0
    retrieval_support_weight: int = 0

    def _stats(self, type_name: str) -> CopyTypeStats:
        return self.type_stats.setdefault(type_name, CopyTypeStats())

    def _entry_value(self, entry: CopyEntry) -> tuple[float, int, int, int]:
        heldout_value = entry.heldout_gain_qbits / COPY_ENTRY_RESIDENT_BYTES
        return (heldout_value, entry.gain_qbits, entry.uses, entry.pos)

    def _evict_one(self) -> None:
        best_id: int | None = None
        best_score: tuple[int, int, int] | None = None
        scanned = 0
        while self.cursor < len(self.order) and scanned < 256:
            entry_id = self.order[self.cursor]
            self.cursor += 1
            entry = self.entries.get(entry_id)
            if entry is None:
                continue
            scanned += 1
            score = self._entry_value(entry)
            if best_score is None or score < best_score:
                best_id = entry_id
                best_score = score
        if best_id is None:
            for entry_id in self.order:
                if entry_id in self.entries:
                    best_id = entry_id
                    break
        if best_id is None:
            return
        entry = self.entries.pop(best_id)
        stats = self._stats(entry.type_name)
        stats.entries = max(0, stats.entries - 1)
        stats.resident_bytes = max(0, stats.resident_bytes - COPY_ENTRY_RESIDENT_BYTES)
        stats.evictions += 1
        if self.cursor > 4096 and self.cursor * 2 > len(self.order):
            self.order = [entry_id for entry_id in self.order[self.cursor :] if entry_id in self.entries]
            self.cursor = 0

    def insert(self, pos: int, features: dict[str, Any]) -> None:
        if self.cap_entries <= 0:
            return
        while len(self.entries) >= self.cap_entries:
            before = len(self.entries)
            self._evict_one()
            if len(self.entries) >= before:
                break
        type_name = copy_type_for(features)
        entry_id = self.next_entry_id
        self.next_entry_id += 1
        entry = CopyEntry(
            entry_id=entry_id,
            pos=pos,
            type_name=type_name,
            simhash16=int(features["simhash16"]),
            suffix_hash=int(features["suffix_hash"]),
            schema_hash=int(features["schema_hash"]),
            field=int(features["field"]),
            mode=int(features["mode"]),
            slot=int(features["slot"]),
            column=int(features["column"]),
            word_len_bucket=int(features["word_len_bucket"]),
            word_class=int(features["word_class"]),
        )
        self.entries[entry_id] = entry
        self.order.append(entry_id)
        stats = self._stats(type_name)
        stats.entries += 1
        stats.resident_bytes += COPY_ENTRY_RESIDENT_BYTES
        for key in make_copy_keys(features, type_name):
            bucket = self.key_index.setdefault(key, [])
            bucket.append(entry_id)
            if len(bucket) > self.max_key_scan * 4:
                del bucket[: len(bucket) - self.max_key_scan * 2]

    def _candidate_entries(self, features: dict[str, Any], type_name: str) -> list[CopyEntry]:
        seen: set[int] = set()
        scored: list[tuple[int, int, CopyEntry]] = []
        cur_sim = int(features["simhash16"])
        cur_schema = int(features["schema_hash"])
        cur_suffix = int(features["suffix_hash"])
        cur_field = int(features["field"])
        cur_mode = int(features["mode"])
        cur_slot = int(features["slot"])
        cur_column = int(features["column"])
        cur_word_len = int(features["word_len_bucket"])
        cur_word_class = int(features["word_class"])
        for key in make_copy_keys(features, type_name):
            bucket = self.key_index.get(key)
            if not bucket:
                continue
            for entry_id in reversed(bucket[-self.max_key_scan :]):
                if entry_id in seen:
                    continue
                seen.add(entry_id)
                entry = self.entries.get(entry_id)
                if entry is None:
                    continue
                sketch_distance = (cur_sim ^ entry.simhash16).bit_count()
                schema_penalty = 0 if cur_schema == entry.schema_hash else 2
                suffix_penalty = 0 if cur_suffix == entry.suffix_hash else 1
                type_penalty = (
                    (0 if cur_field == entry.field else self.type_penalty)
                    + (0 if cur_mode == entry.mode else self.type_penalty)
                    + (0 if cur_slot == entry.slot else self.slot_penalty)
                    + (0 if cur_column == entry.column else self.column_penalty)
                    + (0 if cur_word_len == entry.word_len_bucket else self.word_penalty)
                    + (0 if cur_word_class == entry.word_class else self.word_penalty)
                )
                score = (
                    sketch_distance * self.sketch_penalty
                    + schema_penalty
                    + suffix_penalty
                    + type_penalty
                )
                scored.append((score, -entry.pos, entry))
        scored.sort(key=lambda item: (item[0], item[1]))
        return [entry for _score, _neg_pos, entry in scored[: self.top_k]]

    def prior_p1(
        self,
        data: bytes,
        pos: int,
        features: dict[str, Any],
        partial_len: int,
        partial_prefix: int,
        min_support: int,
        alpha_num: int,
    ) -> CopyPrior | None:
        if self.cap_entries <= 0 or self.top_k <= 0:
            return None
        type_name = copy_type_for(features)
        candidates = self._candidate_entries(features, type_name)
        if not candidates:
            return None
        zeros = 0
        ones = 0
        hits = 0
        support_weight = 0
        used_entries: set[int] = set()
        best_sketch_distance = min(
            (int(features["simhash16"]) ^ entry.simhash16).bit_count()
            for entry in candidates
        )
        weighted_sketch_distance = 0
        weighted_abs_offset = 0
        weighted_age_bucket = 0
        weighted_edit_distance = 0
        prefix = partial_prefix & ((1 << partial_len) - 1) if partial_len else 0
        mask_shift = 8 - partial_len
        for entry in candidates:
            sketch_distance = (int(features["simhash16"]) ^ entry.simhash16).bit_count()
            age_bucket = max(0, (pos - entry.pos) >> self.age_shift) if self.age_shift >= 0 else 0
            for offset in self.offsets:
                source_pos = entry.pos + offset
                if source_pos < 0 or source_pos >= pos or source_pos >= len(data):
                    continue
                byte_value = data[source_pos]
                edit_distance = 0
                if partial_len:
                    candidate_prefix = byte_value >> mask_shift
                    edit_distance = (candidate_prefix ^ prefix).bit_count()
                    if edit_distance > self.edit_distance:
                        continue
                penalty = (
                    sketch_distance * self.sketch_penalty
                    + abs(offset) * self.offset_penalty
                    + min(age_bucket, 31) * self.age_penalty
                    + edit_distance * self.edit_penalty
                )
                shift = max(0, min(20, penalty))
                weight = max(1, COPY_WEIGHT_SCALE >> min(12, shift))
                bit = (byte_value >> (7 - partial_len)) & 1
                if bit:
                    ones += weight
                else:
                    zeros += weight
                support_weight += weight
                hits += 1
                used_entries.add(entry.entry_id)
                weighted_sketch_distance += sketch_distance * weight
                weighted_abs_offset += abs(offset) * weight
                weighted_age_bucket += age_bucket * weight
                weighted_edit_distance += edit_distance * weight
        if support_weight < min_support * COPY_WEIGHT_SCALE:
            return None
        alpha_weight = alpha_num * COPY_WEIGHT_SCALE
        denom = 2 * support_weight + 2 * alpha_weight
        numer = (2 * ones + alpha_weight) * TOTAL
        p1 = clamp_p1(numer // denom)
        floor = max(1, min(TOTAL // 2 - 1, (TOTAL * self.escape_ppm) // 1_000_000))
        p1 = max(floor, min(TOTAL - floor, p1))
        self.retrieval_rows += 1
        self.retrieval_hits += hits
        self.retrieval_support_weight += support_weight
        return CopyPrior(
            p1=p1,
            hits=hits,
            support_weight=support_weight,
            type_name=type_name,
            entry_ids=tuple(sorted(used_entries)),
            candidates_scanned=len(candidates),
            best_sketch_distance=best_sketch_distance,
            mean_sketch_distance=weighted_sketch_distance / support_weight,
            mean_abs_offset=weighted_abs_offset / support_weight,
            mean_age_bucket=weighted_age_bucket / support_weight,
            mean_edit_distance=weighted_edit_distance / support_weight,
        )

    def credit(self, prior: CopyPrior | None, gain_qbits: int, split: str) -> None:
        if prior is None or not prior.entry_ids:
            return
        share = int(gain_qbits / len(prior.entry_ids))
        for entry_id in prior.entry_ids:
            entry = self.entries.get(entry_id)
            if entry is None:
                continue
            entry.gain_qbits += share
            entry.uses += 1
            stats = self._stats(entry.type_name)
            stats.uses += 1
            stats.gain_qbits += share
            if split == "test":
                entry.heldout_gain_qbits += share
                stats.heldout_gain_qbits += share

    def receipt(self) -> dict[str, Any]:
        return {
            "enabled": self.cap_entries > 0,
            "cap_entries": self.cap_entries,
            "resident_bytes_per_entry": COPY_ENTRY_RESIDENT_BYTES,
            "entry_count": len(self.entries),
            "top_k": self.top_k,
            "max_key_scan": self.max_key_scan,
            "offsets": list(self.offsets),
            "escape_ppm": self.escape_ppm,
            "type_penalty": self.type_penalty,
            "slot_penalty": self.slot_penalty,
            "word_penalty": self.word_penalty,
            "column_penalty": self.column_penalty,
            "retrieval_rows": self.retrieval_rows,
            "mean_hits_when_used": (
                self.retrieval_hits / self.retrieval_rows if self.retrieval_rows else 0.0
            ),
            "mean_support_weight_when_used": (
                self.retrieval_support_weight / self.retrieval_rows
                if self.retrieval_rows
                else 0.0
            ),
            "type_tables": {
                name: stats.receipt() for name, stats in sorted(self.type_stats.items())
            },
            "eviction_policy": (
                "bounded typed tables evict the lowest sampled "
                "heldout_logloss_gain_per_resident_byte proxy"
            ),
        }


@dataclass
class BlockFallbackStats:
    proposed_baseline_qbits: int = 0
    proposed_candidate_qbits: int = 0
    disabled: bool = False


def selected_router_probability(
    base_p1: int,
    band_candidates: dict[str, tuple[int, int]],
    selected_band: str | None,
    blend_ppm: int,
    use_log_odds: bool,
    fallback_p1: int,
) -> int:
    if selected_band in {None, "base"}:
        return base_p1 if selected_band == "base" else fallback_p1
    prior = band_candidates.get(selected_band)
    if prior is None:
        return fallback_p1
    prior_p1 = prior[0]
    if use_log_odds:
        return log_odds_mix_probability(base_p1, [(prior_p1, blend_ppm)])
    return blend_probability(base_p1, prior_p1, blend_ppm)


def blend_for_band(
    band: str,
    default_blend_ppm: int,
    copy_blend_ppm: int,
    copy_type_blends: dict[str, int] | None = None,
) -> int:
    if band.startswith("copy_"):
        copy_type = band[len("copy_") :]
        if copy_type_blends and copy_type in copy_type_blends:
            return copy_type_blends[copy_type]
        if copy_blend_ppm > 0:
            return copy_blend_ppm
    return default_blend_ppm


def selected_router_probability_by_band(
    base_p1: int,
    band_candidates: dict[str, tuple[int, int]],
    selected_band: str | None,
    blend_ppm: int,
    copy_blend_ppm: int,
    copy_type_blends: dict[str, int],
    use_log_odds: bool,
    fallback_p1: int,
) -> int:
    selected_blend = (
        blend_for_band(selected_band, blend_ppm, copy_blend_ppm, copy_type_blends)
        if selected_band is not None
        else blend_ppm
    )
    return selected_router_probability(
        base_p1,
        band_candidates,
        selected_band,
        selected_blend,
        use_log_odds,
        fallback_p1,
    )


def update_router_losses(
    router: BandRouter,
    bit: int,
    band_candidates: dict[str, tuple[int, int]],
    base_p1: int,
    blend_ppm: int,
    copy_blend_ppm: int,
    copy_type_blends: dict[str, int],
    use_log_odds: bool,
) -> None:
    if not use_log_odds:
        base_loss = qbits_for(bit, base_p1)
        router.base_loss_qbits = router.decay(router.base_loss_qbits) + base_loss
        for band, (prior_p1, _support) in band_candidates.items():
            corrected = blend_probability(
                base_p1,
                prior_p1,
                blend_for_band(band, blend_ppm, copy_blend_ppm, copy_type_blends),
            )
            loss = qbits_for(bit, corrected)
            old = router.losses_qbits.get(band, 256)
            router.losses_qbits[band] = router.decay(old) + loss
            regret = router.regrets_qbits.get(band, 0)
            router.regrets_qbits[band] = router.decay(regret) + loss - base_loss
        return
    base_loss = qbits_for(bit, base_p1)
    router.base_loss_qbits = router.decay(router.base_loss_qbits) + base_loss
    for band, (prior_p1, _support) in band_candidates.items():
        corrected = log_odds_mix_probability(
            base_p1,
            [(prior_p1, blend_for_band(band, blend_ppm, copy_blend_ppm, copy_type_blends))],
        )
        loss = qbits_for(bit, corrected)
        old = router.losses_qbits.get(band, 256)
        router.losses_qbits[band] = router.decay(old) + loss
        regret = router.regrets_qbits.get(band, 0)
        router.regrets_qbits[band] = router.decay(regret) + loss - base_loss


def router_trace_snapshot(
    router: BandRouter,
    band_candidates: dict[str, tuple[int, int]],
    allow_abstain: bool,
    scale_qbits: int,
) -> tuple[dict[str, int], dict[str, int]]:
    scores: dict[str, int] = {}
    for band in band_candidates:
        if allow_abstain:
            scores[band] = router.regrets_qbits.get(band, 0)
        else:
            scores[band] = router.losses_qbits.get(band, 256)
    if allow_abstain:
        scores["base"] = 0
    if not scores:
        return {}, {}
    best = min(scores.values())
    scale = max(1, scale_qbits)
    raw_weights = {
        band: math.exp(-min(60.0, max(0.0, (score - best) / scale)))
        for band, score in scores.items()
    }
    total = sum(raw_weights.values())
    if total <= 0:
        return scores, {}
    weights = {
        band: int(round((weight / total) * 1_000_000))
        for band, weight in raw_weights.items()
    }
    drift = 1_000_000 - sum(weights.values())
    if weights and drift:
        best_band = max(weights, key=weights.get)
        weights[best_band] += drift
    return scores, weights


def iter_raw_bits(data: bytes, limit_bytes: int) -> tuple[int, int, int]:
    end = len(data) if limit_bytes <= 0 else min(len(data), limit_bytes)
    for pos in range(end):
        byte = data[pos]
        for bit_pos in range(8):
            yield pos, bit_pos, (byte >> (7 - bit_pos)) & 1


def split_for(pos: int, train_bytes: int) -> str:
    if train_bytes <= 0:
        return "all"
    return "train" if pos < train_bytes else "test"


def run(args: argparse.Namespace) -> dict[str, Any]:
    with args.data.open("rb") as f:
        data = f.read(args.limit_bytes)

    state = RetrievalState(data=data, suffix_len=args.suffix_len, sketch_len=args.sketch_len)
    partial_state = PartialByteState()
    base_model = RawContextModel(
        cap_entries=args.base_table_cap_entries,
        p_buckets=args.p_buckets,
        order=args.base_order,
    )
    retrieval_table = BoundedCounterTable(cap_entries=args.retrieval_table_cap_entries)
    byte_table = BoundedByteTable(cap_entries=args.byte_table_cap_entries)
    router = BandRouter(decay_shift=args.router_decay_shift)
    copy_channel = TypedCopyChannel(
        cap_entries=args.copy_channel_cap_entries if args.copy_channel_enabled else 0,
        top_k=args.copy_channel_top_k,
        max_key_scan=args.copy_channel_max_key_scan,
        offsets=args.copy_channel_offsets,
        age_shift=args.copy_channel_age_shift,
        sketch_penalty=args.copy_channel_sketch_penalty,
        type_penalty=args.copy_channel_type_penalty,
        slot_penalty=args.copy_channel_slot_penalty,
        word_penalty=args.copy_channel_word_penalty,
        column_penalty=args.copy_channel_column_penalty,
        offset_penalty=args.copy_channel_offset_penalty,
        age_penalty=args.copy_channel_age_penalty,
        edit_penalty=args.copy_channel_edit_penalty,
        edit_distance=args.copy_channel_edit_distance,
        escape_ppm=args.copy_channel_escape_ppm,
    )

    baseline = BinaryArithmeticEncoder()
    candidate = BinaryArithmeticEncoder()
    heldout_baseline = BinaryArithmeticEncoder()
    heldout_candidate = BinaryArithmeticEncoder()

    totals = {name: SplitTotals() for name in ("train", "test", "all")}
    block_qbits: dict[int, SplitTotals] = {}
    proposed_block_qbits: dict[int, SplitTotals] = {}
    block_fallback_state: dict[int, BlockFallbackStats] = {}
    selected_band_counts: Counter[str] = Counter()
    copy_type_counts: Counter[str] = Counter()

    encoded_rows = 0
    retrieval_rows = 0
    retrieval_hits = 0
    byte_prior_rows = 0
    byte_prior_hits = 0
    partial_key_rows = 0
    copy_prior_rows = 0
    copy_prior_hits = 0
    attribution: dict[str, AttributionStats] = {}
    block_fallback_rows = 0
    block_fallback_trigger_count = 0
    trace_rows = 0
    trace_file = None
    if args.trace_jsonl is not None:
        args.trace_jsonl.parent.mkdir(parents=True, exist_ok=True)
        trace_file = args.trace_jsonl.open("w", encoding="utf-8")

    def attr(name: str) -> AttributionStats:
        return attribution.setdefault(name, AttributionStats())

    for pos, bit_pos, bit in iter_raw_bits(data, args.limit_bytes):
        if args.max_rows > 0 and encoded_rows >= args.max_rows:
            break
        state.advance_to(pos)
        features = state.features()
        partial_len, partial_prefix = partial_state.advance_to(pos, bit_pos)
        history = bytes(state.tail)
        base_p1 = base_model.predict(
            history,
            bit_pos,
            partial_len,
            partial_prefix,
            args.alpha2,
        )
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
        copy_prior = copy_channel.prior_p1(
            data,
            pos,
            features,
            partial_len,
            partial_prefix,
            min_support=args.copy_channel_min_support,
            alpha_num=args.alpha2,
        )
        if copy_prior is not None:
            copy_prior_rows += 1
            copy_prior_hits += copy_prior.hits
            copy_type_counts[copy_prior.type_name] += 1

        selected_band: str | None = None
        band_candidates: dict[str, tuple[int, int]] = {}
        typed_prior_p1: int | None = None
        hits = 0
        typed_hits = 0
        typed_support = 0
        if args.expert_mode in {"best_band", "best_band_abstain"}:
            band_candidates, hits, _support = band_retrieval_p1(
                retrieval_table,
                keys,
                min_support=args.min_support,
                alpha_num=args.alpha2,
            )
            if args.copy_channel_as_band and copy_prior is not None:
                band_candidates[f"copy_{copy_prior.type_name}"] = (
                    copy_prior.p1,
                    max(1, copy_prior.support_weight // COPY_WEIGHT_SCALE),
                )
            corrected_p1, selected_band = router.choose(
                band_candidates,
                base_p1,
                args.blend_ppm,
                args.expert_mode == "best_band_abstain",
                args.router_abstain_margin_qbits,
            )
            corrected_p1 = selected_router_probability_by_band(
                base_p1,
                band_candidates,
                selected_band,
                args.blend_ppm,
                args.copy_channel_blend_ppm,
                args.copy_channel_type_blends,
                args.log_odds_mix,
                corrected_p1,
            )
            prior_used = selected_band not in {None, "base"}
        else:
            prior_p1, hits, _support = retrieval_p1(
                retrieval_table,
                keys,
                min_support=args.min_support,
                alpha_num=args.alpha2,
            )
            typed_prior_p1 = prior_p1
            typed_hits = hits
            typed_support = _support
            if args.expert_mode in {"no_regret", "no_regret_abstain"}:
                expert_candidates: dict[str, tuple[int, int]] = {}
                if prior_p1 is not None:
                    expert_candidates["typed_retrieval"] = (prior_p1, max(1, _support))
                if copy_prior is not None:
                    expert_candidates[f"copy_{copy_prior.type_name}"] = (
                        copy_prior.p1,
                        max(1, copy_prior.support_weight // COPY_WEIGHT_SCALE),
                    )
                corrected_p1, selected_band = router.choose(
                    expert_candidates,
                    base_p1,
                    args.blend_ppm,
                    args.expert_mode == "no_regret_abstain",
                    args.router_abstain_margin_qbits,
                )
                corrected_p1 = selected_router_probability_by_band(
                    base_p1,
                    expert_candidates,
                    selected_band,
                    args.blend_ppm,
                    args.copy_channel_blend_ppm,
                    args.copy_channel_type_blends,
                    args.log_odds_mix,
                    corrected_p1,
                )
                prior_used = selected_band not in {None, "base"}
                band_candidates = expert_candidates
            elif args.log_odds_mix:
                corrected_p1 = log_odds_mix_probability(
                    base_p1,
                    [
                        (prior_p1, args.blend_ppm),
                        (
                            copy_prior.p1 if copy_prior is not None else None,
                            args.copy_channel_blend_ppm,
                        ),
                    ],
                )
                prior_used = prior_p1 is not None or copy_prior is not None
            else:
                corrected_p1 = blend_probability(base_p1, prior_p1, args.blend_ppm)
                if copy_prior is not None and args.copy_channel_blend_ppm > 0:
                    corrected_p1 = blend_probability(
                        corrected_p1, copy_prior.p1, args.copy_channel_blend_ppm
                    )
                prior_used = prior_p1 is not None or (
                    copy_prior is not None and args.copy_channel_blend_ppm > 0
                )

        byte_prior, byte_hits, _byte_support = byte_prior_p1(
            byte_table,
            byte_keys,
            partial_len,
            partial_prefix,
            min_support=args.byte_min_support,
            alpha_num=args.alpha2,
        )
        if args.expert_mode in {"no_regret", "no_regret_abstain"} and byte_prior is not None:
            band_candidates["byte_prior"] = (byte_prior, max(1, _byte_support))
            corrected_p1, selected_band = router.choose(
                band_candidates,
                base_p1,
                args.blend_ppm,
                args.expert_mode == "no_regret_abstain",
                args.router_abstain_margin_qbits,
            )
            corrected_p1 = selected_router_probability_by_band(
                base_p1,
                band_candidates,
                selected_band,
                args.blend_ppm,
                args.copy_channel_blend_ppm,
                args.copy_channel_type_blends,
                args.log_odds_mix,
                corrected_p1,
            )
            prior_used = selected_band not in {None, "base"}
        elif args.log_odds_mix:
            corrected_p1 = log_odds_mix_probability(
                corrected_p1,
                [(byte_prior, args.byte_prior_blend_ppm)],
            )
        elif args.byte_prior_blend_ppm > 0:
            corrected_p1 = blend_probability(corrected_p1, byte_prior, args.byte_prior_blend_ppm)

        proposed_p1 = corrected_p1
        block = block_id(pos, args.block_bytes)
        block_state = block_fallback_state.setdefault(block, BlockFallbackStats())
        if args.block_fallback_qbits > 0 and block_state.disabled:
            corrected_p1 = base_p1
            block_fallback_rows += 1

        baseline.encode(bit, base_p1)
        candidate.encode(bit, corrected_p1)
        split = split_for(pos, args.train_bytes)
        if split == "test":
            heldout_baseline.encode(bit, base_p1)
            heldout_candidate.encode(bit, corrected_p1)

        if prior_used:
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
        proposed_candidate_qbits = qbits_for(bit, proposed_p1)
        copy_p1 = copy_prior.p1 if copy_prior is not None else None
        if typed_prior_p1 is not None:
            attr("typed_retrieval").record(
                bit=bit,
                prior_p1=typed_prior_p1,
                base_qbits=base_qbits,
                split=split,
                selected=selected_band == "typed_retrieval",
                byte_p1=byte_prior,
                copy_p1=copy_p1,
                hits=typed_hits,
                support=typed_support,
            )
        if byte_prior is not None:
            attr("byte_prior").record(
                bit=bit,
                prior_p1=byte_prior,
                base_qbits=base_qbits,
                split=split,
                selected=selected_band == "byte_prior",
                typed_p1=typed_prior_p1,
                copy_p1=copy_p1,
                hits=byte_hits,
                support=_byte_support,
            )
        if copy_prior is not None:
            copy_band = f"copy_{copy_prior.type_name}"
            copy_selected = selected_band == copy_band
            for name in ("copy_available", copy_band):
                attr(name).record(
                    bit=bit,
                    prior_p1=copy_prior.p1,
                    base_qbits=base_qbits,
                    split=split,
                    selected=copy_selected,
                    typed_p1=typed_prior_p1,
                    byte_p1=byte_prior,
                    hits=copy_prior.hits,
                    support=max(1, copy_prior.support_weight // COPY_WEIGHT_SCALE),
                    copy_prior=copy_prior,
                )
        if copy_prior is not None:
            copy_channel.credit(
                copy_prior,
                base_qbits - qbits_for(bit, copy_prior.p1),
                split,
            )
        for name in (split, "all"):
            total = totals[name]
            total.rows += 1
            total.baseline_qbits += base_qbits
            total.candidate_qbits += candidate_qbits
            if split == "all":
                break
        block_total = block_qbits.setdefault(block, SplitTotals())
        block_total.rows += 1
        block_total.baseline_qbits += base_qbits
        block_total.candidate_qbits += candidate_qbits
        proposed_block = proposed_block_qbits.setdefault(block, SplitTotals())
        proposed_block.rows += 1
        proposed_block.baseline_qbits += base_qbits
        proposed_block.candidate_qbits += proposed_candidate_qbits
        block_state.proposed_baseline_qbits += base_qbits
        block_state.proposed_candidate_qbits += proposed_candidate_qbits
        if (
            args.block_fallback_qbits > 0
            and not block_state.disabled
            and block_state.proposed_candidate_qbits
            - block_state.proposed_baseline_qbits
            > args.block_fallback_qbits
        ):
            block_state.disabled = True
            block_fallback_trigger_count += 1

        if trace_file is not None and (
            args.trace_stride <= 1 or encoded_rows % args.trace_stride == 0
        ):
            allow_abstain = args.expert_mode in {"best_band_abstain", "no_regret_abstain"}
            expert_scores, expert_weights = router_trace_snapshot(
                router,
                band_candidates,
                allow_abstain,
                max(1, args.router_abstain_margin_qbits),
            )
            trace_row = {
                "row": encoded_rows,
                "pos": pos,
                "bit_pos": bit_pos,
                "bit": bit,
                "split": split,
                "block": block,
                "span_type": copy_type_for(features),
                "features": {
                    "field": features["field"],
                    "mode": features["mode"],
                    "slot": features["slot"],
                    "column": features["column"],
                    "word_len_bucket": features["word_len_bucket"],
                    "word_class": features["word_class"],
                    "schema_hash": features["schema_hash"],
                    "suffix_hash": features["suffix_hash"],
                    "simhash16": features["simhash16"],
                },
                "p1": {
                    "base": base_p1,
                    "typed_retrieval": typed_prior_p1,
                    "copy": copy_prior.p1 if copy_prior is not None else None,
                    "byte_prior": byte_prior,
                    "proposed": proposed_p1,
                    "final": corrected_p1,
                },
                "hits": {
                    "typed_retrieval": hits,
                    "byte_prior": byte_hits,
                    "copy": copy_prior.hits if copy_prior is not None else 0,
                    "copy_support_weight": (
                        copy_prior.support_weight if copy_prior is not None else 0
                    ),
                },
                "expert": {
                    "selected": selected_band,
                    "candidates": {
                        name: {"p1": p1, "support": support}
                        for name, (p1, support) in sorted(band_candidates.items())
                    },
                    "scores_qbits": expert_scores,
                    "weights_ppm": expert_weights,
                },
                "qbits": {
                    "base": base_qbits,
                    "candidate": candidate_qbits,
                    "proposed_candidate": proposed_candidate_qbits,
                    "gain": base_qbits - candidate_qbits,
                    "proposed_gain": base_qbits - proposed_candidate_qbits,
                    "typed_retrieval_gain_vs_base": (
                        base_qbits - qbits_for(bit, typed_prior_p1)
                        if typed_prior_p1 is not None
                        else None
                    ),
                    "byte_prior_gain_vs_base": (
                        base_qbits - qbits_for(bit, byte_prior)
                        if byte_prior is not None
                        else None
                    ),
                    "copy_gain_vs_base": (
                        base_qbits - qbits_for(bit, copy_prior.p1)
                        if copy_prior is not None
                        else None
                    ),
                    "copy_gain_vs_typed": (
                        qbits_for(bit, typed_prior_p1) - qbits_for(bit, copy_prior.p1)
                        if copy_prior is not None and typed_prior_p1 is not None
                        else None
                    ),
                    "copy_gain_vs_byte_prior": (
                        qbits_for(bit, byte_prior) - qbits_for(bit, copy_prior.p1)
                        if copy_prior is not None and byte_prior is not None
                        else None
                    ),
                },
                "block_delta": {
                    "candidate_gain_qbits": (
                        block_total.baseline_qbits - block_total.candidate_qbits
                    ),
                    "proposed_gain_qbits": (
                        proposed_block.baseline_qbits - proposed_block.candidate_qbits
                    ),
                    "fallback_disabled": block_state.disabled,
                },
            }
            trace_file.write(json.dumps(trace_row, sort_keys=True) + "\n")
            trace_rows += 1

        base_model.update(history, bit_pos, partial_len, partial_prefix, bit)
        for key in keys:
            retrieval_table.update(key, bit)
        if args.expert_mode in {"best_band", "best_band_abstain", "no_regret", "no_regret_abstain"}:
            update_router_losses(
                router,
                bit,
                band_candidates,
                base_p1,
                args.blend_ppm,
                args.copy_channel_blend_ppm,
                args.copy_channel_type_blends,
                args.log_odds_mix,
            )
        partial_state.observe(pos, bit)
        if partial_state.length == 8:
            for key in byte_keys:
                byte_table.update(key, partial_state.prefix)
            copy_channel.insert(pos, features)
        encoded_rows += 1
        if (
            args.progress_interval_bytes > 0
            and bit_pos == 7
            and (pos + 1) % args.progress_interval_bytes == 0
        ):
            print(
                json.dumps(
                    {
                        "event": "progress",
                        "bytes": pos + 1,
                        "encoded_rows": encoded_rows,
                        "base_shadow_bytes": baseline.byte_count,
                        "candidate_shadow_bytes": candidate.byte_count,
                        "shadow_saved_bytes": baseline.byte_count - candidate.byte_count,
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
                flush=True,
            )

    if trace_file is not None:
        trace_file.close()

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
        block_rows.append({"block_id": bid, "rows": total.rows, "gain_bytes": gain_bytes})
    block_rows.sort(key=lambda item: item["gain_bytes"])
    proposed_block_rows = [
        {"block_id": bid, "rows": total.rows, "gain_bytes": total.gain_bytes}
        for bid, total in sorted(proposed_block_qbits.items())
    ]
    proposed_block_rows.sort(key=lambda item: item["gain_bytes"])
    proposed_gain_qbits = sum(
        total.baseline_qbits - total.candidate_qbits for total in proposed_block_qbits.values()
    )

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
    if args.copy_channel_enabled:
        bands.extend(
            [
                "copy_prose",
                "copy_title",
                "copy_template",
                "copy_ref",
                "copy_url",
                "copy_table",
                "copy_infobox",
                "copy_category_link",
                "copy_entity",
            ]
        )

    sketch_schema = {
        "feature_source": "raw_data",
        "suffix_len": args.suffix_len,
        "sketch_len": args.sketch_len,
        "p_buckets": args.p_buckets,
        "min_support": args.min_support,
        "blend_ppm": args.blend_ppm,
        "base_order": args.base_order,
        "base_table_cap_entries": args.base_table_cap_entries,
        "retrieval_table_cap_entries": args.retrieval_table_cap_entries,
        "byte_table_cap_entries": args.byte_table_cap_entries,
        "partial_byte_family": args.partial_byte_family,
        "typed_key_profile": args.typed_key_profile,
        "byte_prior_blend_ppm": args.byte_prior_blend_ppm,
        "byte_min_support": args.byte_min_support,
        "expert_mode": args.expert_mode,
        "log_odds_mix": args.log_odds_mix,
        "router_decay_shift": args.router_decay_shift,
        "router_abstain_margin_qbits": args.router_abstain_margin_qbits,
        "block_fallback_qbits": args.block_fallback_qbits,
        "copy_channel": {
            "enabled": args.copy_channel_enabled,
            "as_band": args.copy_channel_as_band,
            "blend_ppm": args.copy_channel_blend_ppm,
            "type_blends": args.copy_channel_type_blends,
            "cap_entries": args.copy_channel_cap_entries,
            "top_k": args.copy_channel_top_k,
            "max_key_scan": args.copy_channel_max_key_scan,
            "min_support": args.copy_channel_min_support,
            "offsets": list(args.copy_channel_offsets),
            "age_shift": args.copy_channel_age_shift,
            "sketch_penalty": args.copy_channel_sketch_penalty,
            "type_penalty": args.copy_channel_type_penalty,
            "slot_penalty": args.copy_channel_slot_penalty,
            "word_penalty": args.copy_channel_word_penalty,
            "column_penalty": args.copy_channel_column_penalty,
            "offset_penalty": args.copy_channel_offset_penalty,
            "age_penalty": args.copy_channel_age_penalty,
            "edit_penalty": args.copy_channel_edit_penalty,
            "edit_distance": args.copy_channel_edit_distance,
            "escape_ppm": args.copy_channel_escape_ppm,
        },
        "bands": bands,
    }
    sketch_schema_hash = hashlib.sha256(
        json.dumps(sketch_schema, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return {
        "receipt_type": "streaming_retrieval_shadow",
        "trace_version": "raw_enwik9_bits_msb_v1",
        "method": "streaming_retrieval_raw_shadow_v1",
        "base_trace": "raw_enwik9_bits_msb",
        "data": str(args.data),
        "data_sha256": hashlib.sha256(data).hexdigest(),
        "data_bytes_loaded": len(data),
        "scope_bytes": args.scope_bytes,
        "target": {
            "baseline_score": args.baseline_score,
            "target_score": args.target_score,
            "required_net_gain_bytes": args.baseline_score - args.target_score,
        },
        "position_span": {"min_pos": 0 if encoded_rows else None, "max_pos": (encoded_rows - 1) // 8 if encoded_rows else None},
        "rows": encoded_rows,
        "encoded_rows": encoded_rows,
        "ignored_rows": 0,
        "train_bytes": args.train_bytes,
        "feature_source": "raw_data",
        "trace_data_alignment": {
            "complete_bytes_checked": min(len(data), args.limit_bytes if args.limit_bytes > 0 else len(data)),
            "best_order": "msb",
            "best_match_rate": 1.0,
            "warning": None,
        },
        "sketch_schema": sketch_schema,
        "sketch_schema_hash": sketch_schema_hash,
        "retrieval_table_cap_entries": args.retrieval_table_cap_entries,
        "retrieved_neighbors_per_bit": {
            "retrieval_rows": retrieval_rows,
            "mean_hits_when_used": retrieval_hits / retrieval_rows if retrieval_rows else 0.0,
            "partial_key_rows": partial_key_rows,
            "byte_prior_rows": byte_prior_rows,
            "mean_byte_hits_when_used": byte_prior_hits / byte_prior_rows if byte_prior_rows else 0.0,
            "copy_prior_rows": copy_prior_rows,
            "mean_copy_hits_when_used": copy_prior_hits / copy_prior_rows if copy_prior_rows else 0.0,
            "copy_type_counts": dict(sorted(copy_type_counts.items())),
            "selected_band_counts": dict(sorted(selected_band_counts.items())),
            "router_base_loss_qbits": router.base_loss_qbits,
            "router_loss_qbits": dict(sorted(router.losses_qbits.items())),
            "router_regret_qbits": dict(sorted(router.regrets_qbits.items())),
        },
        "conditional_attribution": {
            "schema": "conditional_copy_attribution_v1",
            "interpretation": (
                "Rows count prior availability; selected_rows count router selection. "
                "Positive direct_gain_bytes_vs_X means this prior beat X on the same bits."
            ),
            "buckets": {
                name: stats.receipt() for name, stats in sorted(attribution.items())
            },
        },
        "correction_trace": {
            "jsonl": str(args.trace_jsonl) if args.trace_jsonl is not None else None,
            "rows": trace_rows,
            "stride": args.trace_stride,
            "fields": [
                "bit",
                "base_p1",
                "typed_retrieval_p1",
                "copy_p1",
                "byte_prior_p1",
                "selected_expert",
                "expert_scores_qbits",
                "expert_weights_ppm",
                "qbit_gain",
                "typed_retrieval_gain_vs_base",
                "copy_gain_vs_base",
                "copy_gain_vs_typed",
                "copy_gain_vs_byte_prior",
                "block_delta",
            ],
        },
        "typed_copy_channel": copy_channel.receipt(),
        "base_shadow_bytes": baseline.byte_count,
        "candidate_shadow_bytes": candidate.byte_count,
        "shadow_saved_bytes": shadow_saved_bytes,
        "heldout_shadow_bytes": heldout_candidate.byte_count if heldout_rows else None,
        "heldout_base_shadow_bytes": heldout_baseline.byte_count if heldout_rows else None,
        "heldout_shadow_saved_bytes": heldout_saved_bytes,
        "added_code_bytes_estimate": args.added_code_bytes_estimate,
        "added_static_table_bytes": args.added_static_table_bytes,
        "max_online_state_bytes": (
            args.base_table_cap_entries * 32
            + args.retrieval_table_cap_entries * 32
            + args.byte_table_cap_entries * 96
            + (args.copy_channel_cap_entries * COPY_ENTRY_RESIDENT_BYTES if args.copy_channel_enabled else 0)
        ),
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
        "block_fallback": {
            "threshold_qbits": args.block_fallback_qbits,
            "triggered_blocks": block_fallback_trigger_count,
            "fallback_rows": block_fallback_rows,
            "disabled_block_ids": sorted(
                bid for bid, state in block_fallback_state.items() if state.disabled
            )[:64],
            "proposed_gain_bytes_before_fallback": proposed_gain_qbits / 2048.0,
        },
        "block_rows": block_rows,
        "proposed_block_rows_before_fallback": proposed_block_rows[:64],
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
            "raw bits are emitted MSB-first from data bytes; all base and retrieval "
            "counters are updated only after encoding the current bit"
        ),
        "verdict": verdict,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a raw byte-aligned SRSTC shadow probe.")
    parser.add_argument("--data", type=pathlib.Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--limit-bytes", type=int, default=64_000)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--train-bytes", type=int, default=8_000)
    parser.add_argument("--suffix-len", type=int, default=32)
    parser.add_argument("--sketch-len", type=int, default=96)
    parser.add_argument("--base-order", type=int, default=2)
    parser.add_argument("--p-buckets", type=int, default=32)
    parser.add_argument("--min-support", type=int, default=8)
    parser.add_argument("--blend-ppm", type=int, default=10_000)
    parser.add_argument("--alpha2", type=int, default=1)
    parser.add_argument("--base-table-cap-entries", type=int, default=200_000)
    parser.add_argument("--retrieval-table-cap-entries", type=int, default=200_000)
    parser.add_argument("--byte-table-cap-entries", type=int, default=100_000)
    parser.add_argument(
        "--partial-byte-family",
        choices=("none", "sketch", "direct", "all"),
        default="sketch",
    )
    parser.add_argument(
        "--typed-key-profile",
        choices=("base", "rich", "richpos"),
        default="base",
        help="typed retrieval key family; richpos adds causal continuation-position keys",
    )
    parser.add_argument(
        "--expert-mode",
        choices=("aggregate", "best_band", "best_band_abstain", "no_regret", "no_regret_abstain"),
        default="best_band_abstain",
    )
    parser.add_argument("--log-odds-mix", action="store_true")
    parser.add_argument("--byte-prior-blend-ppm", type=int, default=0)
    parser.add_argument("--byte-min-support", type=int, default=4)
    parser.add_argument("--router-decay-shift", type=int, default=6)
    parser.add_argument("--router-abstain-margin-qbits", type=int, default=128)
    parser.add_argument("--block-bytes", type=int, default=16_384)
    parser.add_argument("--block-fallback-qbits", type=int, default=0)
    parser.add_argument("--copy-channel-enabled", action="store_true")
    parser.add_argument("--copy-channel-as-band", action="store_true")
    parser.add_argument("--copy-channel-blend-ppm", type=int, default=0)
    parser.add_argument(
        "--copy-channel-type-blends",
        default="",
        help=(
            "optional comma-separated per-copy-type blend overrides, "
            "for example prose=160000,ref=320000"
        ),
    )
    parser.add_argument("--copy-channel-cap-entries", type=int, default=100_000)
    parser.add_argument("--copy-channel-top-k", type=int, default=8)
    parser.add_argument("--copy-channel-max-key-scan", type=int, default=32)
    parser.add_argument("--copy-channel-min-support", type=int, default=4)
    parser.add_argument("--copy-channel-offsets", default="0,-1,1")
    parser.add_argument("--copy-channel-age-shift", type=int, default=14)
    parser.add_argument("--copy-channel-sketch-penalty", type=int, default=1)
    parser.add_argument("--copy-channel-type-penalty", type=int, default=2)
    parser.add_argument("--copy-channel-slot-penalty", type=int, default=2)
    parser.add_argument("--copy-channel-word-penalty", type=int, default=1)
    parser.add_argument("--copy-channel-column-penalty", type=int, default=1)
    parser.add_argument("--copy-channel-offset-penalty", type=int, default=2)
    parser.add_argument("--copy-channel-age-penalty", type=int, default=1)
    parser.add_argument("--copy-channel-edit-penalty", type=int, default=4)
    parser.add_argument("--copy-channel-edit-distance", type=int, default=1)
    parser.add_argument("--copy-channel-escape-ppm", type=int, default=512)
    parser.add_argument("--scope-bytes", type=int, default=DEFAULT_SCOPE_BYTES)
    parser.add_argument("--baseline-score", type=int, default=DEFAULT_BASELINE_SCORE)
    parser.add_argument("--target-score", type=int, default=DEFAULT_TARGET_SCORE)
    parser.add_argument("--added-code-bytes-estimate", type=int, default=12_288)
    parser.add_argument("--added-static-table-bytes", type=int, default=0)
    parser.add_argument(
        "--trace-jsonl",
        type=pathlib.Path,
        default=None,
        help="optional JSONL row trace for exact SRSTC correction accounting",
    )
    parser.add_argument(
        "--trace-stride",
        type=int,
        default=0,
        help="write every Nth row to --trace-jsonl; 0 or 1 writes every row",
    )
    parser.add_argument(
        "--progress-interval-bytes",
        type=int,
        default=0,
        help="print deterministic progress JSON to stderr every N completed bytes",
    )
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if not args.data.exists():
        raise SystemExit(f"missing data: {args.data}")
    if args.limit_bytes <= 0:
        raise SystemExit("--limit-bytes must be positive")
    if args.train_bytes < 0:
        raise SystemExit("--train-bytes must be nonnegative")
    if args.base_order < 0:
        raise SystemExit("--base-order must be nonnegative")
    if args.p_buckets <= 0 or args.min_support <= 0:
        raise SystemExit("--p-buckets and --min-support must be positive")
    if args.base_table_cap_entries <= 0 or args.retrieval_table_cap_entries <= 0:
        raise SystemExit("table caps must be positive")
    if args.byte_table_cap_entries <= 0 or args.byte_min_support <= 0:
        raise SystemExit("byte table cap and byte min support must be positive")
    if args.byte_prior_blend_ppm < 0 or args.byte_prior_blend_ppm > 1_000_000:
        raise SystemExit("--byte-prior-blend-ppm must be between 0 and 1000000")
    if args.router_decay_shift < 0 or args.router_abstain_margin_qbits < 0:
        raise SystemExit("router settings must be nonnegative")
    if args.block_fallback_qbits < 0:
        raise SystemExit("--block-fallback-qbits must be nonnegative")
    if args.copy_channel_blend_ppm < 0 or args.copy_channel_blend_ppm > 1_000_000:
        raise SystemExit("--copy-channel-blend-ppm must be between 0 and 1000000")
    if (
        args.copy_channel_cap_entries < 0
        or args.copy_channel_top_k < 0
        or args.copy_channel_max_key_scan <= 0
        or args.copy_channel_min_support <= 0
    ):
        raise SystemExit("copy channel caps, top-k, scan, and support settings are invalid")
    if (
        args.copy_channel_age_shift < 0
        or args.copy_channel_sketch_penalty < 0
        or args.copy_channel_type_penalty < 0
        or args.copy_channel_slot_penalty < 0
        or args.copy_channel_word_penalty < 0
        or args.copy_channel_column_penalty < 0
        or args.copy_channel_offset_penalty < 0
        or args.copy_channel_age_penalty < 0
        or args.copy_channel_edit_penalty < 0
        or args.copy_channel_edit_distance < 0
    ):
        raise SystemExit("copy channel penalties must be nonnegative")
    if args.copy_channel_escape_ppm < 0 or args.copy_channel_escape_ppm >= 500_000:
        raise SystemExit("--copy-channel-escape-ppm must be in [0, 500000)")
    if args.trace_stride < 0:
        raise SystemExit("--trace-stride must be nonnegative")
    if args.progress_interval_bytes < 0:
        raise SystemExit("--progress-interval-bytes must be nonnegative")
    try:
        args.copy_channel_offsets = parse_copy_offsets(args.copy_channel_offsets)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    try:
        args.copy_channel_type_blends = parse_copy_type_blends(args.copy_channel_type_blends)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

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
