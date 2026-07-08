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
DEFAULT_TARGET_SCORE = 109_500_000
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
    cached_pos: int | None = None
    cached_features: dict[str, Any] = field(default_factory=dict)

    def advance_to(self, target_pos: int) -> None:
        if target_pos < self.pos:
            raise ValueError("residual rows must be nondecreasing by pos")
        while self.pos < target_pos:
            if self.pos >= len(self.data):
                raise ValueError(f"row position {target_pos} exceeds data length {len(self.data)}")
            byte = self.data[self.pos]
            self.wiki.update(byte)
            self.tail.append(byte)
            keep = max(self.suffix_len, self.sketch_len, 192)
            if len(self.tail) > keep * 2:
                del self.tail[: len(self.tail) - keep]
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
        line_pos_bucket = bucket(_distance_since_any(tail, b"\n"), (0, 1, 3, 7, 15, 31, 63, 127))
        markup_pos_bucket = bucket(
            _distance_since_any(tail, b"\n|={}<>[]"),
            (0, 1, 2, 4, 8, 16, 32, 64),
        )
        token_pos_bucket = bucket(
            _distance_since_any(tail, b" \t\r\n|={}<>[]/\"'&;:,."),
            (0, 1, 2, 4, 8, 16, 32, 64),
        )
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

    def observe(self, pos: int, bit_pos: int, bit: int) -> None:
        if self.max_positions <= 0 or pos < 0 or pos >= self.max_positions:
            return
        if bit_pos < 0 or bit_pos > 7:
            return
        self.rows_seen += 1
        self.bits_by_pos.setdefault(pos, {})[bit_pos] = bit

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


def block_id(pos: int, block_bytes: int) -> int:
    return pos // block_bytes if block_bytes > 0 else 0


def run(args: argparse.Namespace) -> dict[str, Any]:
    data = args.data.read_bytes()
    if args.data_limit > 0:
        data = data[: args.data_limit]

    state = RetrievalState(data=data, suffix_len=args.suffix_len, sketch_len=args.sketch_len)
    partial_state = PartialByteState()
    alignment = TraceAlignment(max_positions=args.alignment_max_positions)
    table = BoundedCounterTable(cap_entries=args.table_cap_entries)
    byte_table = BoundedByteTable(cap_entries=args.byte_table_cap_entries)
    router = BandRouter(decay_shift=args.router_decay_shift)
    baseline = BinaryArithmeticEncoder()
    candidate = BinaryArithmeticEncoder()
    heldout_baseline = BinaryArithmeticEncoder()
    heldout_candidate = BinaryArithmeticEncoder()
    totals = {name: SplitTotals() for name in ("train", "test", "all")}
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
        alignment.observe(pos, bit_pos, bit)
        state.advance_to(pos)
        base_p1 = clamp_p1(as_int(row, "p1", "fx2_p1", "probability", default=32768))
        data_features = state.features()
        if args.feature_source == "row":
            features = features_from_row(row, data_features)
        else:
            features = data_features
        partial_len, partial_prefix = partial_state.advance_to(pos, bit_pos)
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
        band_candidates: dict[str, tuple[int, int]] = {}
        selected_band: str | None = None
        if args.expert_mode in {"best_band", "best_band_abstain"}:
            band_candidates, hits, support = band_retrieval_p1(
                table,
                keys,
                min_support=args.min_support,
                alpha_num=args.alpha2,
            )
            if args.byte_prior_as_band and byte_prior is not None:
                band_candidates["byte_prior"] = (byte_prior, byte_support)
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
        block = block_qbits.setdefault(block_id(pos, args.block_bytes), SplitTotals())
        block.rows += 1
        block.baseline_qbits += base_qbits
        block.candidate_qbits += candidate_qbits

        for key in keys:
            table.update(key, bit)
        if args.expert_mode in {"best_band", "best_band_abstain"}:
            router.update(bit, band_candidates, base_p1, args.blend_ppm)
        partial_state.observe(pos, bit)
        if partial_state.length == 8:
            for key in byte_keys:
                byte_table.update(key, partial_state.prefix)

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
        "expert_mode": args.expert_mode,
        "router_decay_shift": args.router_decay_shift,
        "router_abstain_margin_qbits": args.router_abstain_margin_qbits,
        "bands": bands,
    }
    sketch_schema_hash = hashlib.sha256(
        json.dumps(sketch_schema, sort_keys=True).encode("utf-8")
    ).hexdigest()
    alignment_report = alignment.report(data)
    alignment_valid_for_feature_source = not (
        args.feature_source == "data"
        and alignment_report.get("complete_bytes_checked")
        and alignment_report.get("warning")
    )
    proof_blocker = None
    if not alignment_valid_for_feature_source:
        proof_blocker = (
            "feature_source=data requires trace bits to reconstruct the supplied "
            "data bytes; use feature_source=row or a byte-aligned trace"
        )
        if verdict != "incomplete":
            verdict = "invalid_trace_alignment"

    return {
        "receipt_type": "streaming_retrieval_shadow",
        "trace_version": "fx2_shadow_trace_v1",
        "method": "streaming_retrieval_shadow_v2",
        "base_trace": str(args.log),
        "data": str(args.data),
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
        "base_shadow_bytes": baseline.byte_count,
        "candidate_shadow_bytes": candidate.byte_count,
        "shadow_saved_bytes": shadow_saved_bytes,
        "heldout_shadow_bytes": heldout_candidate.byte_count if heldout_rows else None,
        "heldout_base_shadow_bytes": heldout_baseline.byte_count if heldout_rows else None,
        "heldout_shadow_saved_bytes": heldout_saved_bytes,
        "added_code_bytes_estimate": args.added_code_bytes_estimate,
        "added_static_table_bytes": args.added_static_table_bytes,
        "max_online_state_bytes": args.table_cap_entries * 32 + args.byte_table_cap_entries * 96,
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
            "base abstention baseline are also updated only after the current bit"
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
        choices=("data", "row"),
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
    parser.add_argument("--block-bytes", type=int, default=16_384)
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
    if args.byte_table_cap_entries <= 0 or args.byte_min_support <= 0:
        raise SystemExit("--byte-table-cap-entries and --byte-min-support must be positive")
    if args.byte_prior_blend_ppm < 0 or args.byte_prior_blend_ppm > 1_000_000:
        raise SystemExit("--byte-prior-blend-ppm must be between 0 and 1000000")
    if args.router_decay_shift < 0:
        raise SystemExit("--router-decay-shift must be nonnegative")
    if args.router_abstain_margin_qbits < 0:
        raise SystemExit("--router-abstain-margin-qbits must be nonnegative")

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
