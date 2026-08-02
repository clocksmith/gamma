#!/usr/bin/env python3
"""Run the frozen MOBIUS-2 TESSERA typed lexical side-stream QH0 gate."""

from __future__ import annotations

import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
from typing import Any, Iterable, Sequence
import zlib

import numpy as np

from causal_state_screen import WikiState
from janus_paid_residual_mdl_oracle import range_decode, range_encode
from mobius2_tessera_self_annotation_graph import (
    ROLE_IDS,
    ROLE_NAMES,
    build_self_annotation_signatures,
    canonical_lexeme,
    morphology_class,
    relation_histogram,
    role_id,
    surface_class,
)
from sibyl_page_prompt_oracle import archive_payload, page_intervals, write_page_map
from wrt_exact import (
    CAPITALIZED,
    END_UPPER,
    ESCAPE,
    TEXT_SEGMENT,
    UPPERCASE,
    ParsedStore,
    WrtDecoderState,
    parse_store,
    read_dictionary_words,
    token_index,
    wrt_byte_transform,
)


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "mobius2_tessera_typed_fiber_ceiling_qh0_v1"
P1_MAGIC = b"CMX21P1\0"
SIDE_TOTAL = 1 << 24
SIDE_MASK = SIDE_TOTAL - 1
FRAME_MAGIC = b"TESSQH1\0"
FRAME_STRUCT = struct.Struct("<8sBBIQQQQ32s")
VARIANTS = ("F1", "F2", "F3", "FR")
VARIANT_IDS = {name: index + 1 for index, name in enumerate(VARIANTS)}
SPLIT_NAMES = ("development", "selection", "sealed_confirmation")
GROSS_GATE_BYTES = 30_000
MODEL_TYPE_RECORD_BYTES = 8
QBITS = 256


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def read_p1(path: Path, rows: int) -> np.memmap:
    with path.open("rb") as handle:
        header = handle.read(16)
    if len(header) != 16 or header[:8] != P1_MAGIC:
        raise ValueError(f"invalid P1 trace: {path}")
    declared = struct.unpack_from("<Q", header, 8)[0]
    if declared != rows or path.stat().st_size != 16 + rows * 2:
        raise ValueError(f"P1 row binding failed: {path}")
    values = np.memmap(path, mode="r", dtype="<u2", offset=16, shape=(rows,))
    if np.any(values == 0):
        raise ValueError(f"P1 contains an illegal zero probability: {path}")
    return values


def qbit_tables() -> tuple[np.ndarray, np.ndarray]:
    values = np.arange(65536, dtype=np.float64)
    values[0] = 1.0
    p1 = values / 65536.0
    p0 = 1.0 - p1
    return (
        np.rint(-np.log2(p0) * QBITS).astype(np.int32),
        np.rint(-np.log2(p1) * QBITS).astype(np.int32),
    )


def byte_qbits(
    p1: np.ndarray, truth: np.ndarray, zero: np.ndarray, one: np.ndarray
) -> np.ndarray:
    if len(p1) != len(truth) or len(p1) % 8:
        raise ValueError("P1/truth rows are not byte aligned")
    output = np.empty(len(p1) // 8, dtype=np.int64)
    chunk_bytes = 1 << 17
    for byte_start in range(0, len(output), chunk_bytes):
        byte_end = min(len(output), byte_start + chunk_bytes)
        row_start = byte_start * 8
        row_end = byte_end * 8
        probabilities = np.asarray(p1[row_start:row_end], dtype=np.uint16)
        bits = truth[row_start:row_end]
        costs = np.where(bits != 0, one[probabilities], zero[probabilities])
        output[byte_start:byte_end] = costs.reshape(-1, 8).sum(axis=1)
    return output


@dataclass(frozen=True)
class Page:
    raw_start: int
    raw_end: int
    wrt_start: int
    wrt_end: int
    split: int


def build_pages(parsed: ParsedStore) -> list[Page]:
    intervals = page_intervals(parsed)
    development_end = len(intervals) * 3 // 5
    selection_end = len(intervals) * 4 // 5
    result = []
    for index, (raw_start, raw_end, row_start, row_end) in enumerate(intervals):
        split = 0 if index < development_end else 1 if index < selection_end else 2
        result.append(Page(raw_start, raw_end, row_start // 8, row_end // 8, split))
    return result


def event_metadata(parsed: ParsedStore, pages: Sequence[Page]) -> tuple[np.ndarray, np.ndarray]:
    roles = np.empty(len(parsed.events), dtype=np.uint8)
    splits = np.full(len(parsed.events), -1, dtype=np.int8)
    state = WikiState()
    page_index = 0
    for index, event in enumerate(parsed.events):
        while page_index < len(pages) and event.start >= pages[page_index].wrt_end:
            page_index += 1
        roles[index] = role_id(state)
        if page_index < len(pages):
            page = pages[page_index]
            if page.wrt_start <= event.start and event.end <= page.wrt_end:
                splits[index] = page.split
        for byte in event.decoded:
            state.update(byte)
    return roles, splits


def project_frequencies(symbols: Sequence[int], counts: dict[int, int]) -> "Distribution":
    ordered = tuple(sorted(int(symbol) for symbol in symbols))
    if not ordered or len(ordered) > SIDE_TOTAL:
        raise ValueError("invalid Q24 side alphabet")
    weights = [int(counts.get(symbol, 0)) + 1 for symbol in ordered]
    total_weight = sum(weights)
    distributable = SIDE_TOTAL - len(ordered)
    frequencies = []
    remainders = []
    for weight in weights:
        quotient, remainder = divmod(distributable * weight, total_weight)
        frequencies.append(1 + quotient)
        remainders.append(remainder)
    missing = SIDE_TOTAL - sum(frequencies)
    order = sorted(range(len(ordered)), key=lambda i: (-remainders[i], ordered[i]))
    for index in order[:missing]:
        frequencies[index] += 1
    cdf = [0]
    for frequency in frequencies:
        cdf.append(cdf[-1] + frequency)
    if cdf[-1] != SIDE_TOTAL or any(frequency <= 0 for frequency in frequencies):
        raise ValueError("invalid projected Q24 distribution")
    return Distribution(ordered, tuple(frequencies), tuple(cdf))


@dataclass(frozen=True)
class Distribution:
    symbols: tuple[int, ...]
    frequencies: tuple[int, ...]
    cdf: tuple[int, ...]

    def symbol_index(self, symbol: int) -> int:
        index = bisect_left(self.symbols, int(symbol))
        if index >= len(self.symbols) or self.symbols[index] != int(symbol):
            raise ValueError(f"side symbol {symbol} is outside its alphabet")
        return index

    def qbits(self, symbol: int) -> int:
        frequency = self.frequencies[self.symbol_index(symbol)]
        return int(round(-math.log2(frequency / SIDE_TOTAL) * QBITS))


class SideEncoder:
    def __init__(self) -> None:
        self.low = 0
        self.high = 0xFFFFFFFF
        self.output = bytearray()
        self.symbols = 0

    def _bound(self, cumulative: int) -> int:
        delta = self.high - self.low
        return self.low + (delta >> 24) * cumulative + (
            ((delta & SIDE_MASK) * cumulative) >> 24
        )

    def encode(self, distribution: Distribution, symbol: int) -> None:
        index = distribution.symbol_index(symbol)
        lower = distribution.cdf[index]
        upper = distribution.cdf[index + 1]
        new_low = self.low if lower == 0 else self._bound(lower) + 1
        new_high = self.high if upper == SIDE_TOTAL else self._bound(upper)
        if new_low > new_high:
            raise ValueError("Q24 range collapsed during side encode")
        self.low, self.high = new_low, new_high
        while ((self.low ^ self.high) & 0xFF000000) == 0:
            self.output.append((self.high >> 24) & 0xFF)
            self.low = (self.low << 8) & 0xFFFFFFFF
            self.high = ((self.high << 8) & 0xFFFFFFFF) + 255
        self.symbols += 1

    def finish(self) -> bytes:
        while ((self.low ^ self.high) & 0xFF000000) == 0:
            self.output.append((self.high >> 24) & 0xFF)
            self.low = (self.low << 8) & 0xFFFFFFFF
            self.high = ((self.high << 8) & 0xFFFFFFFF) + 255
        self.output.append((self.high >> 24) & 0xFF)
        return bytes(self.output)


class SideDecoder:
    def __init__(self, payload: bytes) -> None:
        if not payload:
            raise ValueError("empty TESSERA side payload")
        self.payload = payload
        self.cursor = 4
        self.code = int.from_bytes(payload[:4].ljust(4, b"\0"), "big")
        self.low = 0
        self.high = 0xFFFFFFFF
        self.symbols = 0

    def _bound(self, cumulative: int) -> int:
        delta = self.high - self.low
        return self.low + (delta >> 24) * cumulative + (
            ((delta & SIDE_MASK) * cumulative) >> 24
        )

    def decode(self, distribution: Distribution) -> int:
        left = 0
        right = len(distribution.symbols)
        while left < right:
            middle = (left + right) // 2
            if self.code <= self._bound(distribution.cdf[middle + 1]):
                right = middle
            else:
                left = middle + 1
        if left >= len(distribution.symbols):
            raise ValueError("Q24 side code falls outside its CDF")
        lower = distribution.cdf[left]
        upper = distribution.cdf[left + 1]
        new_low = self.low if lower == 0 else self._bound(lower) + 1
        new_high = self.high if upper == SIDE_TOTAL else self._bound(upper)
        if not new_low <= self.code <= new_high:
            raise ValueError("Q24 side decoder interval mismatch")
        self.low, self.high = new_low, new_high
        while ((self.low ^ self.high) & 0xFF000000) == 0:
            self.low = (self.low << 8) & 0xFFFFFFFF
            self.high = ((self.high << 8) & 0xFFFFFFFF) + 255
            next_byte = self.payload[self.cursor] if self.cursor < len(self.payload) else 0
            self.cursor += 1
            self.code = ((self.code << 8) & 0xFFFFFFFF) + next_byte
        self.symbols += 1
        return distribution.symbols[left]


def laplace_cost(total: int, alphabet: int, sum_terms: float) -> float:
    if total <= 0:
        return 0.0
    return total * math.log2(total + alphabet) - sum_terms


def mdl_types(
    signatures: dict[str, int],
    lexemes: Sequence[str],
    role_lex_counts: np.ndarray,
) -> tuple[list[int], dict[str, object]]:
    signature_groups: dict[int, list[int]] = defaultdict(list)
    for lexeme_id, lexeme in enumerate(lexemes):
        signature_groups[int(signatures.get(lexeme, 0))].append(lexeme_id)
    groups: dict[int, dict[str, Any]] = {}
    for group_id, signature in enumerate(sorted(signature_groups)):
        members = set(signature_groups[signature])
        totals = role_lex_counts[:, list(members)].sum(axis=1).astype(np.int64)
        sum_terms = np.zeros(len(ROLE_NAMES), dtype=np.float64)
        for role in range(len(ROLE_NAMES)):
            values = role_lex_counts[role, list(members)]
            positive = values[values > 0].astype(np.float64)
            sum_terms[role] = float(np.sum(positive * np.log2(positive + 1.0)))
        groups[group_id] = {
            "members": members,
            "totals": totals,
            "sum_terms": sum_terms,
            "signatures": [signature],
        }

    initial_count = len(groups)
    merges = []
    while True:
        ids = sorted(groups)
        type_count = len(ids)
        if type_count <= 1:
            break
        role_totals = sum((groups[group_id]["totals"] for group_id in ids))
        best: tuple[int, int, int] | None = None
        for left_index, left_id in enumerate(ids):
            left = groups[left_id]
            left_support = left["totals"] > 0
            for right_id in ids[left_index + 1 :]:
                right = groups[right_id]
                if not np.any(left_support & (right["totals"] > 0)):
                    continue
                type_delta = 0.0
                lex_delta = 0.0
                for role in range(len(ROLE_NAMES)):
                    total = int(role_totals[role])
                    a = int(left["totals"][role])
                    b = int(right["totals"][role])
                    if total:
                        old = total * math.log2(total + type_count)
                        old -= (a * math.log2(a + 1.0) if a else 0.0)
                        old -= (b * math.log2(b + 1.0) if b else 0.0)
                        merged = a + b
                        new = total * math.log2(total + type_count - 1)
                        new -= merged * math.log2(merged + 1.0) if merged else 0.0
                        type_delta += new - old
                    old_lex = laplace_cost(
                        a, len(left["members"]), float(left["sum_terms"][role])
                    ) + laplace_cost(
                        b, len(right["members"]), float(right["sum_terms"][role])
                    )
                    lex_delta += laplace_cost(
                        a + b,
                        len(left["members"]) + len(right["members"]),
                        float(left["sum_terms"][role] + right["sum_terms"][role]),
                    ) - old_lex
                saving_qbits = int(
                    round((-type_delta - lex_delta) * QBITS)
                    + MODEL_TYPE_RECORD_BYTES * 8 * QBITS
                )
                candidate = (saving_qbits, -left_id, -right_id)
                if best is None or candidate > best:
                    best = candidate
        if best is None or best[0] <= 0:
            break
        saving, negative_left, negative_right = best
        left_id = -negative_left
        right_id = -negative_right
        left = groups[left_id]
        right = groups.pop(right_id)
        left["members"].update(right["members"])
        left["totals"] = left["totals"] + right["totals"]
        left["sum_terms"] = left["sum_terms"] + right["sum_terms"]
        left["signatures"].extend(right["signatures"])
        left["signatures"].sort()
        merges.append((left_id, right_id, saving))

    mapping = [0] * len(lexemes)
    surviving = sorted(groups)
    dense = {group_id: index for index, group_id in enumerate(surviving)}
    for group_id in surviving:
        for lexeme_id in groups[group_id]["members"]:
            mapping[lexeme_id] = dense[group_id]
    receipt = {
        "initial_types": initial_count,
        "final_types": len(surviving),
        "merges": len(merges),
        "total_merge_saving_qbits": sum(row[2] for row in merges),
        "merge_digest": sha256_bytes(
            json.dumps(merges, separators=(",", ":")).encode("utf-8")
        ),
        "first_merges": [list(row) for row in merges[:32]],
    }
    return mapping, receipt


def shuffled_types(
    type_map: Sequence[int],
    lexemes: Sequence[str],
    global_counts: np.ndarray,
    role_lex_counts: np.ndarray,
    morphologies: Sequence[int],
    typical_lengths: Sequence[int],
    typical_surfaces: Sequence[int],
) -> list[int]:
    bins: dict[tuple[int, ...], list[int]] = defaultdict(list)
    for lexeme_id in range(len(lexemes)):
        frequency = int(global_counts[lexeme_id])
        frequency_bucket = frequency.bit_length() - 1 if frequency else 0
        support = int(np.count_nonzero(role_lex_counts[:, lexeme_id]))
        key = (
            frequency_bucket,
            int(typical_lengths[lexeme_id]),
            int(morphologies[lexeme_id]),
            int(typical_surfaces[lexeme_id]),
            support,
            1,
        )
        bins[key].append(lexeme_id)
    output = list(type_map)
    for key in sorted(bins):
        ids = sorted(bins[key])
        if len(ids) > 1:
            values = [type_map[index] for index in ids]
            values = values[1:] + values[:1]
            for index, value in zip(ids, values, strict=True):
                output[index] = int(value)
    return output


def sparse_counts(counter: Counter[tuple[int, ...]]) -> list[list[int]]:
    return [list(key) + [int(value)] for key, value in sorted(counter.items())]


def build_model(
    parsed: ParsedStore,
    pages: Sequence[Page],
    roles: np.ndarray,
    splits: np.ndarray,
) -> tuple[bytes, dict[str, object]]:
    development_pages = [
        parsed.decoded[page.raw_start : page.raw_end] for page in pages if page.split == 0
    ]
    signatures = build_self_annotation_signatures(development_pages)
    lexeme_set = {
        canonical_lexeme(event.decoded)
        for index, event in enumerate(parsed.events)
        if splits[index] == 0 and event.kind == "token"
    }
    lexemes = sorted(lexeme_set)
    lexeme_ids = {lexeme: index for index, lexeme in enumerate(lexemes)}
    morphologies = [morphology_class(lexeme) for lexeme in lexemes]
    role_lex_counts = np.zeros((len(ROLE_NAMES), len(lexemes)), dtype=np.int64)
    global_counts = np.zeros(len(lexemes), dtype=np.int64)
    tag_counts = np.zeros((len(ROLE_NAMES), 2), dtype=np.int64)
    surface_counts: Counter[tuple[int, ...]] = Counter()
    global_surface_counts: Counter[tuple[int, ...]] = Counter()
    variant_counts: Counter[tuple[int, ...]] = Counter()
    global_variant_counts: Counter[tuple[int, ...]] = Counter()
    catalog_sets: dict[tuple[int, int], set[str]] = defaultdict(set)
    surface_hist: list[Counter[int]] = [Counter() for _ in lexemes]
    length_hist: list[Counter[int]] = [Counter() for _ in lexemes]

    for index, event in enumerate(parsed.events):
        if splits[index] != 0:
            continue
        role = int(roles[index])
        if event.kind != "token":
            tag_counts[role, 0] += 1
            continue
        lexeme_id = lexeme_ids[canonical_lexeme(event.decoded)]
        surface = surface_class(event.decoded)
        encoded_hex = event.encoded.hex()
        catalog_sets[(lexeme_id, surface)].add(encoded_hex)
        role_lex_counts[role, lexeme_id] += 1
        global_counts[lexeme_id] += 1
        tag_counts[role, 1] += 1
        surface_counts[(role, lexeme_id, surface)] += 1
        global_surface_counts[(lexeme_id, surface)] += 1
        surface_hist[lexeme_id][surface] += 1
        length_hist[lexeme_id][len(event.encoded)] += 1

    catalogs: dict[str, list[str]] = {}
    catalog_indexes: dict[tuple[int, int], dict[str, int]] = {}
    for key in sorted(catalog_sets):
        values = sorted(catalog_sets[key])
        catalogs[f"{key[0]}:{key[1]}"] = values
        catalog_indexes[key] = {value: index for index, value in enumerate(values)}

    for index, event in enumerate(parsed.events):
        if splits[index] != 0 or event.kind != "token":
            continue
        role = int(roles[index])
        lexeme_id = lexeme_ids[canonical_lexeme(event.decoded)]
        surface = surface_class(event.decoded)
        variant = catalog_indexes[(lexeme_id, surface)][event.encoded.hex()]
        variant_counts[(role, lexeme_id, surface, variant)] += 1
        global_variant_counts[(lexeme_id, surface, variant)] += 1

    type_map, merge_receipt = mdl_types(signatures, lexemes, role_lex_counts)
    typical_lengths = [
        min((-count, value) for value, count in histogram.items())[1]
        for histogram in length_hist
    ]
    typical_surfaces = [
        min((-count, value) for value, count in histogram.items())[1]
        for histogram in surface_hist
    ]
    rotated = shuffled_types(
        type_map,
        lexemes,
        global_counts,
        role_lex_counts,
        morphologies,
        typical_lengths,
        typical_surfaces,
    )
    model = {
        "schema": "mobius2_tessera_model_tsf0_v1",
        "roles": list(ROLE_NAMES),
        "lexemes": lexemes,
        "morphologies": morphologies,
        "type_map": type_map,
        "shuffled_type_map": rotated,
        "global_lex_counts": global_counts.astype(int).tolist(),
        "role_lex_counts": role_lex_counts.astype(int).tolist(),
        "tag_counts": tag_counts.astype(int).tolist(),
        "surface_counts": sparse_counts(surface_counts),
        "global_surface_counts": sparse_counts(global_surface_counts),
        "variant_counts": sparse_counts(variant_counts),
        "global_variant_counts": sparse_counts(global_variant_counts),
        "catalogs": catalogs,
        "merge": merge_receipt,
        "self_annotation": {
            "lexemes": len(signatures),
            "signature_sha256": sha256_bytes(
                json.dumps(signatures, sort_keys=True, separators=(",", ":")).encode()
            ),
            "relation_histogram": relation_histogram(signatures),
        },
    }
    blob = json.dumps(model, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return blob, model


def counter_from_rows(rows: Iterable[Sequence[int]], key_length: int) -> Counter[tuple[int, ...]]:
    counter: Counter[tuple[int, ...]] = Counter()
    for row in rows:
        counter[tuple(int(value) for value in row[:key_length])] = int(row[key_length])
    return counter


class TesseraModel:
    def __init__(self, raw: bytes) -> None:
        data = json.loads(raw)
        if data.get("schema") != "mobius2_tessera_model_tsf0_v1":
            raise ValueError("invalid TESSERA model schema")
        self.lexemes = tuple(str(value) for value in data["lexemes"])
        self.lexeme_ids = {value: index for index, value in enumerate(self.lexemes)}
        self.morphologies = tuple(int(value) for value in data["morphologies"])
        self.type_maps = {
            "F3": tuple(int(value) for value in data["type_map"]),
            "FR": tuple(int(value) for value in data["shuffled_type_map"]),
        }
        self.global_lex = np.asarray(data["global_lex_counts"], dtype=np.int64)
        self.role_lex = np.asarray(data["role_lex_counts"], dtype=np.int64)
        self.tag = np.asarray(data["tag_counts"], dtype=np.int64)
        self.surface = counter_from_rows(data["surface_counts"], 3)
        self.global_surface = counter_from_rows(data["global_surface_counts"], 2)
        self.variant = counter_from_rows(data["variant_counts"], 4)
        self.global_variant = counter_from_rows(data["global_variant_counts"], 3)
        self.catalogs = {
            tuple(int(part) for part in key.split(":")): tuple(values)
            for key, values in data["catalogs"].items()
        }
        self.catalog_indexes = {
            key: {value: index for index, value in enumerate(values)}
            for key, values in self.catalogs.items()
        }
        self.cache: dict[tuple[Any, ...], Distribution] = {}
        self.type_members: dict[str, dict[int, tuple[int, ...]]] = {}
        self.type_counts: dict[str, np.ndarray] = {}
        for variant in ("F3", "FR"):
            mapping = self.type_maps[variant]
            members: dict[int, list[int]] = defaultdict(list)
            for lexeme_id, type_id in enumerate(mapping):
                members[type_id].append(lexeme_id)
            self.type_members[variant] = {
                type_id: tuple(values) for type_id, values in sorted(members.items())
            }
            counts = np.zeros((len(ROLE_NAMES), len(members)), dtype=np.int64)
            for lexeme_id, type_id in enumerate(mapping):
                counts[:, type_id] += self.role_lex[:, lexeme_id]
            self.type_counts[variant] = counts

    def _cached(
        self, key: tuple[Any, ...], symbols: Sequence[int], counts: dict[int, int]
    ) -> Distribution:
        distribution = self.cache.get(key)
        if distribution is None:
            distribution = project_frequencies(symbols, counts)
            self.cache[key] = distribution
        return distribution

    def tag_dist(self, role: int) -> Distribution:
        return self._cached(
            ("tag", role), (0, 1), {0: int(self.tag[role, 0]), 1: int(self.tag[role, 1])}
        )

    def type_dist(self, variant: str, role: int) -> Distribution:
        if variant in ("F1", "F2"):
            return self._cached((variant, "type"), (0,), {0: 1})
        counts = self.type_counts[variant][role]
        symbols = tuple(range(len(counts)))
        return self._cached(
            (variant, "type", role),
            symbols,
            {symbol: int(counts[symbol]) for symbol in symbols},
        )

    def lexeme_dist(self, variant: str, role: int, type_id: int) -> Distribution:
        if variant == "F1":
            symbols = tuple(range(len(self.lexemes)))
            counts = {symbol: int(self.global_lex[symbol]) for symbol in symbols}
            return self._cached((variant, "lexeme"), symbols, counts)
        if variant == "F2":
            symbols = tuple(range(len(self.lexemes)))
            counts = {symbol: int(self.role_lex[role, symbol]) for symbol in symbols}
            return self._cached((variant, "lexeme", role), symbols, counts)
        symbols = self.type_members[variant][type_id]
        counts = {symbol: int(self.role_lex[role, symbol]) for symbol in symbols}
        return self._cached((variant, "lexeme", role, type_id), symbols, counts)

    def morph_dist(self, variant: str, role: int, lexeme_id: int) -> Distribution:
        morph = self.morphologies[lexeme_id]
        key = (variant == "F1", role if variant != "F1" else -1, lexeme_id)
        return self._cached(("morph",) + key, tuple(range(8)), {morph: int(self.global_lex[lexeme_id])})

    def surface_dist(self, variant: str, role: int, lexeme_id: int) -> Distribution:
        counts = {}
        for surface in range(6):
            key = (lexeme_id, surface) if variant == "F1" else (role, lexeme_id, surface)
            counts[surface] = int(
                self.global_surface.get(key, 0) if variant == "F1" else self.surface.get(key, 0)
            )
        cache_role = -1 if variant == "F1" else role
        return self._cached(("surface", variant, cache_role, lexeme_id), tuple(range(6)), counts)

    def variant_dist(
        self, variant: str, role: int, lexeme_id: int, surface: int
    ) -> Distribution:
        catalog = self.catalogs[(lexeme_id, surface)]
        counts = {}
        for variant_id in range(len(catalog)):
            key = (
                (lexeme_id, surface, variant_id)
                if variant == "F1"
                else (role, lexeme_id, surface, variant_id)
            )
            counts[variant_id] = int(
                self.global_variant.get(key, 0)
                if variant == "F1"
                else self.variant.get(key, 0)
            )
        cache_role = -1 if variant == "F1" else role
        return self._cached(
            ("variant", variant, cache_role, lexeme_id, surface),
            tuple(range(len(catalog))),
            counts,
        )

    def event_values(self, event: Any) -> tuple[int, int, int] | None:
        if event.kind != "token":
            return None
        lexeme_id = self.lexeme_ids.get(canonical_lexeme(event.decoded))
        if lexeme_id is None:
            return None
        surface = surface_class(event.decoded)
        indexes = self.catalog_indexes.get((lexeme_id, surface))
        if indexes is None or event.encoded.hex() not in indexes:
            return None
        return lexeme_id, surface, indexes[event.encoded.hex()]

    def factors(
        self,
        variant: str,
        role: int,
        lexeme_id: int,
        surface: int,
        event_variant: int,
    ) -> list[tuple[Distribution, int]]:
        type_id = 0 if variant in ("F1", "F2") else self.type_maps[variant][lexeme_id]
        return [
            (self.type_dist(variant, role), type_id),
            (self.lexeme_dist(variant, role, type_id), lexeme_id),
            (self.morph_dist(variant, role, lexeme_id), self.morphologies[lexeme_id]),
            (self.surface_dist(variant, role, lexeme_id), surface),
            (self.variant_dist(variant, role, lexeme_id, surface), event_variant),
        ]

    def decoded_event(self, variant: str, role: int, decoder: SideDecoder) -> bytes:
        type_id = decoder.decode(self.type_dist(variant, role))
        lexeme_id = decoder.decode(self.lexeme_dist(variant, role, type_id))
        morph = decoder.decode(self.morph_dist(variant, role, lexeme_id))
        if morph != self.morphologies[lexeme_id]:
            raise ValueError("decoded TESSERA morphology disagrees with lexeme")
        surface = decoder.decode(self.surface_dist(variant, role, lexeme_id))
        event_variant = decoder.decode(self.variant_dist(variant, role, lexeme_id, surface))
        return bytes.fromhex(self.catalogs[(lexeme_id, surface)][event_variant])


def side_encode(
    model: TesseraModel,
    variant: str,
    parsed: ParsedStore,
    roles: np.ndarray,
    active_roles: set[int],
    event_indexes: Iterable[int],
) -> tuple[bytes, np.ndarray, dict[str, int]]:
    encoder = SideEncoder()
    skip_bytes = np.zeros(len(parsed.stream), dtype=np.bool_)
    opportunities = typed = escapes = 0
    for index in event_indexes:
        role = int(roles[index])
        if role not in active_roles:
            continue
        opportunities += 1
        event = parsed.events[index]
        values = model.event_values(event)
        tag = int(values is not None)
        encoder.encode(model.tag_dist(role), tag)
        if values is None:
            escapes += 1
            continue
        typed += 1
        for distribution, symbol in model.factors(variant, role, *values):
            encoder.encode(distribution, symbol)
        skip_bytes[event.start : event.end] = True
    return encoder.finish(), skip_bytes, {
        "opportunities": opportunities,
        "typed": typed,
        "escapes": escapes,
        "symbols": encoder.symbols,
    }


def side_verify(
    model: TesseraModel,
    variant: str,
    payload: bytes,
    parsed: ParsedStore,
    roles: np.ndarray,
    active_roles: set[int],
    event_indexes: Iterable[int],
) -> bool:
    decoder = SideDecoder(payload)
    expected_symbols = 0
    for index in event_indexes:
        role = int(roles[index])
        if role not in active_roles:
            continue
        event = parsed.events[index]
        values = model.event_values(event)
        tag = decoder.decode(model.tag_dist(role))
        expected_symbols += 1
        if tag != int(values is not None):
            return False
        if tag:
            reconstructed = model.decoded_event(variant, role, decoder)
            expected_symbols += 5
            if reconstructed != event.encoded:
                return False
    return decoder.symbols == expected_symbols


def side_event_qbits(
    model: TesseraModel, variant: str, role: int, event: Any
) -> tuple[int, bool]:
    values = model.event_values(event)
    tag = int(values is not None)
    total = model.tag_dist(role).qbits(tag)
    if values is not None:
        total += sum(
            distribution.qbits(symbol)
            for distribution, symbol in model.factors(variant, role, *values)
        )
    return total, values is not None


def select_active_roles(
    model: TesseraModel,
    parsed: ParsedStore,
    roles: np.ndarray,
    splits: np.ndarray,
    joint_byte_cost: np.ndarray,
) -> tuple[set[int], list[dict[str, object]]]:
    side_costs = np.zeros(len(ROLE_NAMES), dtype=np.int64)
    displaced = np.zeros(len(ROLE_NAMES), dtype=np.int64)
    opportunities = np.zeros(len(ROLE_NAMES), dtype=np.int64)
    typed = np.zeros(len(ROLE_NAMES), dtype=np.int64)
    for index, event in enumerate(parsed.events):
        if splits[index] != 1:
            continue
        role = int(roles[index])
        cost, is_typed = side_event_qbits(model, "F3", role, event)
        side_costs[role] += cost
        opportunities[role] += 1
        if is_typed:
            displaced[role] += int(joint_byte_cost[event.start : event.end].sum())
            typed[role] += 1
    rows = []
    active = set()
    for role in range(len(ROLE_NAMES)):
        gain = int(displaced[role] - side_costs[role])
        if gain > 0 and opportunities[role] > 0:
            active.add(role)
        rows.append(
            {
                "role_id": role,
                "role": ROLE_NAMES[role],
                "opportunities": int(opportunities[role]),
                "typed": int(typed[role]),
                "displaced_joint_qbits": int(displaced[role]),
                "side_qbits": int(side_costs[role]),
                "selection_gain_qbits": gain,
                "active": role in active,
            }
        )
    return active, rows


def byte_mask_to_rows(mask: np.ndarray) -> np.ndarray:
    return np.repeat(mask, 8)


def frame_archive(
    variant: str,
    active_roles: set[int],
    raw_bytes: int,
    wrt_bytes: int,
    side: bytes,
    residual: bytes,
    model_sha256: str,
) -> bytes:
    mask = sum(1 << role for role in active_roles)
    frame = FRAME_STRUCT.pack(
        FRAME_MAGIC,
        1,
        VARIANT_IDS[variant],
        mask,
        raw_bytes,
        wrt_bytes,
        len(side),
        len(residual),
        bytes.fromhex(model_sha256),
    )
    return frame + side + residual


def decode_event_bytes(
    encoded: bytes, state: WrtDecoderState, dictionary_words: Sequence[bytes]
) -> bytes:
    if not encoded:
        raise ValueError("empty WRT event")
    first = wrt_byte_transform(encoded[0])
    if first == ESCAPE:
        if len(encoded) != 2:
            raise ValueError("invalid escaped WRT event")
        return state.escaped(wrt_byte_transform(encoded[1]))
    if first in (UPPERCASE, END_UPPER, CAPITALIZED):
        if len(encoded) != 1:
            raise ValueError("invalid WRT control event")
        state.control(first)
        return b""
    if first >= 0x80:
        code = bytes(wrt_byte_transform(value) for value in encoded)
        index = token_index(code)
        if index >= len(dictionary_words):
            raise ValueError("TESSERA token exceeds dictionary")
        return state.word(dictionary_words[index])
    if len(encoded) != 1:
        raise ValueError("invalid WRT literal event")
    return state.literal(first)


class ResidualCursor:
    def __init__(self, bits: np.ndarray) -> None:
        self.bits = bits
        self.cursor = 0

    def byte(self) -> int:
        if self.cursor + 8 > len(self.bits):
            raise ValueError("TESSERA residual bitstream ended inside an event")
        value = 0
        for bit in self.bits[self.cursor : self.cursor + 8]:
            value = (value << 1) | int(bit)
        self.cursor += 8
        return value

    def event(self) -> bytes:
        output = bytearray((self.byte(),))
        first = wrt_byte_transform(output[0])
        if first == ESCAPE:
            output.append(self.byte())
        elif first > 0xCF:
            output.append(self.byte())
            if wrt_byte_transform(output[1]) > 0xCF:
                output.append(self.byte())
        return bytes(output)


def reconstruct_full(
    archive: bytes,
    model: TesseraModel,
    variant: str,
    p1: np.ndarray,
    keep_rows: np.ndarray,
    dictionary_words: Sequence[bytes],
) -> tuple[bytes, bytes, dict[str, int]]:
    if len(archive) < FRAME_STRUCT.size:
        raise ValueError("TESSERA archive is truncated")
    values = FRAME_STRUCT.unpack_from(archive)
    magic, version, variant_id, active_mask, raw_bytes, wrt_bytes, side_len, residual_len, _ = values
    if magic != FRAME_MAGIC or version != 1 or variant_id != VARIANT_IDS[variant]:
        raise ValueError("TESSERA frame identity failed")
    if len(archive) != FRAME_STRUCT.size + side_len + residual_len:
        raise ValueError("TESSERA frame lengths do not sum to archive size")
    side = archive[FRAME_STRUCT.size : FRAME_STRUCT.size + side_len]
    residual = archive[-residual_len:]
    filtered_p1 = np.asarray(p1[keep_rows], dtype=np.uint16)
    residual_bits = range_decode(residual, filtered_p1)
    cursor = ResidualCursor(residual_bits)
    side_decoder = SideDecoder(side)
    active_roles = {role for role in range(len(ROLE_NAMES)) if active_mask & (1 << role)}
    stream = bytearray(cursor.byte() for _ in range(6))
    if stream[0] != TEXT_SEGMENT or stream[5] != TEXT_SEGMENT:
        raise ValueError("TESSERA reconstructed WRT segment header is invalid")
    wrt_state = WrtDecoderState()
    wiki = WikiState()
    raw = bytearray()
    typed = escapes = events = 0
    while len(stream) < wrt_bytes:
        role = role_id(wiki)
        if role in active_roles:
            tag = side_decoder.decode(model.tag_dist(role))
            if tag:
                encoded = model.decoded_event(variant, role, side_decoder)
                typed += 1
            else:
                encoded = cursor.event()
                escapes += 1
        else:
            encoded = cursor.event()
        stream.extend(encoded)
        if len(stream) > wrt_bytes:
            raise ValueError("TESSERA event exceeds declared WRT length")
        decoded = decode_event_bytes(encoded, wrt_state, dictionary_words)
        raw.extend(decoded)
        for byte in decoded:
            wiki.update(byte)
        events += 1
    if cursor.cursor != len(residual_bits):
        raise ValueError("TESSERA residual decoder left truth bits unused")
    if len(raw) != raw_bytes:
        raise ValueError("TESSERA reconstructed raw length mismatch")
    return bytes(stream), bytes(raw), {
        "events": events,
        "typed": typed,
        "escapes": escapes,
        "side_symbols": side_decoder.symbols,
        "residual_bits": cursor.cursor,
    }


def split_byte_masks(pages: Sequence[Page], wrt_bytes: int) -> list[np.ndarray]:
    masks = [np.zeros(wrt_bytes, dtype=np.bool_) for _ in SPLIT_NAMES]
    for page in pages:
        masks[page.split][page.wrt_start : page.wrt_end] = True
    return masks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--joint-p1",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1",
    )
    parser.add_argument(
        "--joint-payload",
        type=Path,
        default=ROOT / "results/janus_recurrent_quotient_joint_10m_v1/joint/candidate.payload",
    )
    parser.add_argument(
        "--endpoint-p1",
        type=Path,
        default=ROOT / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/native.p1",
    )
    parser.add_argument(
        "--endpoint-archive",
        type=Path,
        default=ROOT / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/archive.bin",
    )
    parser.add_argument(
        "--wrt-store",
        type=Path,
        default=ROOT / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin",
    )
    parser.add_argument("--raw-input", type=Path, default=ROOT / "data/enwik9_10000000.bin")
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/"
            "clean-build-b/build/english.dic"
        ),
    )
    parser.add_argument(
        "--trace-recovery-decision",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/decision.json",
    )
    parser.add_argument(
        "--joint-decision",
        type=Path,
        default=ROOT / "results/janus_recurrent_quotient_joint_10m_v1/joint/decision.json",
    )
    parser.add_argument(
        "--inverse-receipt",
        type=Path,
        default=ROOT / "results/endpoint428_wrt_store_inverse_10m_v1/decision.json",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    decision_path = output_dir / "decision.json"
    if decision_path.exists():
        raise FileExistsError("refusing to overwrite a prior TESSERA decision")

    trace_decision = json.loads(args.trace_recovery_decision.read_text())
    joint_decision = json.loads(args.joint_decision.read_text())
    if trace_decision["decision"]["verdict"] != "exact_joint_p1_trace_recovered":
        raise ValueError("joint P1 trace recovery is not certified")
    if sha256_file(args.joint_p1) != trace_decision["artifact"]["joint_p1"]["sha256"]:
        raise ValueError("joint P1 differs from trace recovery receipt")
    if sha256_file(args.joint_payload) != joint_decision["payloads"]["JQ_context_quotient"]["sha256"]:
        raise ValueError("joint payload differs from terminal joint receipt")
    if sha256_file(args.wrt_store) not in args.inverse_receipt.read_text():
        raise ValueError("official inverse receipt does not bind the WRT store")

    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("official WRT inverse differs from canonical raw input")
    truth = np.unpackbits(np.frombuffer(parsed.stream, dtype=np.uint8), bitorder="big")
    rows = len(truth)
    joint_p1 = read_p1(args.joint_p1, rows)
    endpoint_p1 = read_p1(args.endpoint_p1, rows)
    joint_payload = args.joint_payload.read_bytes()
    endpoint_payload_bytes, endpoint_header_bytes, endpoint_wrt_bytes = archive_payload(
        args.endpoint_archive
    )
    endpoint_archive = args.endpoint_archive.read_bytes()
    endpoint_payload = endpoint_archive[endpoint_header_bytes:]
    if endpoint_wrt_bytes != len(parsed.stream) or len(endpoint_payload) != endpoint_payload_bytes:
        raise ValueError("endpoint archive WRT/payload framing mismatch")
    replay_joint = range_encode(joint_p1, truth)
    replay_endpoint = range_encode(endpoint_p1, truth)
    if replay_joint != joint_payload or replay_endpoint != endpoint_payload:
        raise ValueError("F0 or endpoint parent payload identity failed")

    canonical_intervals = page_intervals(parsed)
    page_map_path = output_dir / "page_map.bin"
    write_page_map(page_map_path, canonical_intervals)
    pages = build_pages(parsed)
    roles, splits = event_metadata(parsed, pages)
    model_a, model_receipt_a = build_model(parsed, pages, roles, splits)
    model_b, model_receipt_b = build_model(parsed, pages, roles, splits)
    if model_a != model_b or model_receipt_a != model_receipt_b:
        raise ValueError("repeated TESSERA model builds differ")
    model_sha = sha256_bytes(model_a)
    model = TesseraModel(model_a)
    compressed_model = zlib.compress(model_a, level=9)
    (output_dir / "model.tsf0.json").write_bytes(model_a)
    (output_dir / "model.tsf0.json.zlib").write_bytes(compressed_model)

    zero, one = qbit_tables()
    joint_cost = byte_qbits(joint_p1, truth, zero, one)
    active_roles, fiber_rows = select_active_roles(
        model, parsed, roles, splits, joint_cost
    )

    all_indexes = range(len(parsed.events))
    side_a: dict[str, bytes] = {}
    side_b: dict[str, bytes] = {}
    stats: dict[str, dict[str, int]] = {}
    skip_reference: np.ndarray | None = None
    side_roundtrip: dict[str, bool] = {}
    for variant in VARIANTS:
        payload_a, skip_a, row_stats = side_encode(
            model, variant, parsed, roles, active_roles, all_indexes
        )
        payload_b, skip_b, _ = side_encode(
            model, variant, parsed, roles, active_roles, all_indexes
        )
        if payload_a != payload_b or not np.array_equal(skip_a, skip_b):
            raise ValueError(f"repeated {variant} side build differs")
        if skip_reference is None:
            skip_reference = skip_a
        elif not np.array_equal(skip_reference, skip_a):
            raise ValueError("TESSERA controls do not use identical event boundaries")
        side_a[variant] = payload_a
        side_b[variant] = payload_b
        stats[variant] = row_stats
        side_roundtrip[variant] = side_verify(
            model, variant, payload_a, parsed, roles, active_roles, range(len(parsed.events))
        )
    assert skip_reference is not None
    keep_rows = byte_mask_to_rows(~skip_reference)
    filtered_joint = np.asarray(joint_p1[keep_rows], dtype=np.uint16)
    filtered_truth = truth[keep_rows]
    residual_a = range_encode(filtered_joint, filtered_truth)
    residual_b = range_encode(filtered_joint, filtered_truth)
    if residual_a != residual_b:
        raise ValueError("repeated TESSERA residual payloads differ")
    decoded_residual = range_decode(residual_a, filtered_joint)
    if not np.array_equal(decoded_residual, filtered_truth):
        raise ValueError("TESSERA residual arithmetic decode failed")

    archives = {
        variant: frame_archive(
            variant,
            active_roles,
            len(raw),
            len(parsed.stream),
            side_a[variant],
            residual_a,
            model_sha,
        )
        for variant in VARIANTS
    }
    for variant, archive in archives.items():
        (output_dir / f"{variant.lower()}.archive").write_bytes(archive)
    reconstructed_wrt, reconstructed_raw, reconstruction_stats = reconstruct_full(
        archives["F3"], model, "F3", joint_p1, keep_rows, read_dictionary_words(args.dictionary)
    )
    wrt_exact = reconstructed_wrt == parsed.stream
    raw_exact = reconstructed_raw == raw
    if not wrt_exact or not raw_exact:
        raise ValueError("TESSERA full reconstruction identity failed")

    endpoint_filtered = np.asarray(endpoint_p1[keep_rows], dtype=np.uint16)
    endpoint_residual = range_encode(endpoint_filtered, filtered_truth)
    if not np.array_equal(range_decode(endpoint_residual, endpoint_filtered), filtered_truth):
        raise ValueError("TESSERA endpoint diagnostic residual decode failed")
    endpoint_archive_f3 = frame_archive(
        "F3",
        active_roles,
        len(raw),
        len(parsed.stream),
        side_a["F3"],
        endpoint_residual,
        model_sha,
    )

    controls = {}
    for variant in VARIANTS:
        total = len(archives[variant])
        controls[variant] = {
            "total_bytes": total,
            "side_bytes": len(side_a[variant]),
            "residual_bytes": len(residual_a),
            "frame_bytes": FRAME_STRUCT.size,
            "gain_over_joint_bytes": len(joint_payload) - total,
            "archive_sha256": sha256_bytes(archives[variant]),
            "side_sha256": sha256_bytes(side_a[variant]),
            **stats[variant],
        }
    controls["F0"] = {
        "total_bytes": len(joint_payload),
        "sha256": sha256_bytes(joint_payload),
    }
    endpoint_gain = len(endpoint_payload) - len(endpoint_archive_f3)
    joint_gain = controls["F3"]["gain_over_joint_bytes"]
    eta = None if endpoint_gain == 0 else joint_gain / endpoint_gain
    controls["endpoint_diagnostic"] = {
        "parent_payload_bytes": len(endpoint_payload),
        "candidate_total_bytes": len(endpoint_archive_f3),
        "gain_bytes": endpoint_gain,
        "eta_orthogonal": eta,
    }

    split_masks = split_byte_masks(pages, len(parsed.stream))
    split_receipts: dict[str, object] = {}
    for split_id, split_name in enumerate(SPLIT_NAMES):
        scope_bytes = split_masks[split_id]
        scope_rows = byte_mask_to_rows(scope_bytes)
        candidate_rows = byte_mask_to_rows(scope_bytes & ~skip_reference)
        parent_split = range_encode(
            np.asarray(joint_p1[scope_rows], dtype=np.uint16), truth[scope_rows]
        )
        residual_split = range_encode(
            np.asarray(joint_p1[candidate_rows], dtype=np.uint16), truth[candidate_rows]
        )
        indexes = np.flatnonzero(splits == split_id).tolist()
        side_split, _, split_stats = side_encode(
            model, "F3", parsed, roles, active_roles, indexes
        )
        raw_split = sum(
            page.raw_end - page.raw_start for page in pages if page.split == split_id
        )
        wrt_split = int(np.count_nonzero(scope_bytes))
        candidate_total = len(
            frame_archive(
                "F3",
                active_roles,
                raw_split,
                wrt_split,
                side_split,
                residual_split,
                model_sha,
            )
        )
        split_receipts[split_name] = {
            "pages": sum(page.split == split_id for page in pages),
            "raw_bytes": raw_split,
            "wrt_bytes": wrt_split,
            "parent_payload_bytes": len(parent_split),
            "candidate_total_bytes": candidate_total,
            "gain_bytes": len(parent_split) - candidate_total,
            "side_bytes": len(side_split),
            "residual_bytes": len(residual_split),
            **split_stats,
        }

    split_positive = all(split_receipts[name]["gain_bytes"] > 0 for name in SPLIT_NAMES)
    ordering = all(
        controls["F3"]["total_bytes"] < controls[name]["total_bytes"]
        for name in ("F1", "F2", "FR")
    )
    exactness = {
        "joint_parent_payload_identity": replay_joint == joint_payload,
        "endpoint_parent_payload_identity": replay_endpoint == endpoint_payload,
        "repeated_model_identity": model_a == model_b,
        "repeated_side_identity": all(side_a[name] == side_b[name] for name in VARIANTS),
        "repeated_residual_identity": residual_a == residual_b,
        "side_roundtrip": side_roundtrip,
        "residual_arithmetic_decode": True,
        "endpoint_residual_arithmetic_decode": True,
        "complete_wrt_reconstruction": wrt_exact,
        "official_raw_inverse": raw_exact,
        "all_probabilities_legal_nonzero": True,
        "all_q24_cdfs_legal_nonzero": all(
            distribution.cdf[-1] == SIDE_TOTAL
            and all(value > 0 for value in distribution.frequencies)
            for distribution in model.cache.values()
        ),
        "identical_control_event_boundaries": True,
    }
    gates = {
        "gross_required_bytes": GROSS_GATE_BYTES,
        "gross_pass": joint_gain >= GROSS_GATE_BYTES,
        "development_selection_sealed_positive": split_positive,
        "control_ordering_pass": ordering,
        "exactness_pass": all(
            value if isinstance(value, bool) else all(value.values())
            for value in exactness.values()
        ),
    }
    authorized = all(
        (
            gates["gross_pass"],
            gates["development_selection_sealed_positive"],
            gates["control_ordering_pass"],
            gates["exactness_pass"],
        )
    )
    decision_name = "AUTHORIZED_PAID_TSF1" if authorized else "REJECT"
    decision = {
        "schema": "mobius2_tessera_typed_fiber_ceiling_decision_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "decision": decision_name,
        "inputs": {
            "joint_p1": artifact(args.joint_p1),
            "joint_payload": artifact(args.joint_payload),
            "endpoint_p1": artifact(args.endpoint_p1),
            "endpoint_archive": artifact(args.endpoint_archive),
            "wrt_store": artifact(args.wrt_store),
            "raw_input": artifact(args.raw_input),
            "dictionary": artifact(args.dictionary),
            "trace_recovery_decision": artifact(args.trace_recovery_decision),
            "joint_decision": artifact(args.joint_decision),
            "inverse_receipt": artifact(args.inverse_receipt),
        },
        "scope": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(parsed.stream),
            "p1_rows": rows,
            "events": len(parsed.events),
            "complete_pages": len(pages),
            "event_kind_counts": parsed.kind_counts,
            "page_map": artifact(page_map_path),
        },
        "model": {
            "raw_bytes": len(model_a),
            "raw_sha256": model_sha,
            "compressed_bytes": len(compressed_model),
            "compressed_sha256": sha256_bytes(compressed_model),
            "charged_in_qh0": False,
            "lexemes": len(model.lexemes),
            "types": len(set(model.type_maps["F3"])),
            "shuffled_types": len(set(model.type_maps["FR"])),
            "merge": model_receipt_a["merge"],
            "self_annotation": model_receipt_a["self_annotation"],
            "active_roles": [ROLE_NAMES[role] for role in sorted(active_roles)],
            "active_role_mask": sum(1 << role for role in active_roles),
            "selection_fibers": fiber_rows,
        },
        "controls": controls,
        "splits": split_receipts,
        "reconstruction": reconstruction_stats,
        "exactness": exactness,
        "gates": gates,
        "economics": {
            "incremental_gain_over_joint_bytes": joint_gain,
            "incremental_gain_over_joint_bytes_per_million": joint_gain / 10.0,
            "endpoint_diagnostic_gain_bytes": endpoint_gain,
            "eta_orthogonal": eta,
            "forecast_score_bytes_unchanged": 109_389_323,
            "forecast_debt_bytes": 1_389_323,
            "score_credit_bytes": 0,
        },
        "claim_boundary": (
            "Zero-credit model-free 10M typed event side-stream ceiling over a "
            "retired joint trace. Model/source bytes are reported but free; no "
            "native codec, forecast change, full-1G score, or prize claim exists."
        ),
    }
    temporary = decision_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(decision_path)
    print(
        json.dumps(
            {
                "decision": decision_name,
                "decision_path": str(decision_path),
                "f3_gain_bytes": joint_gain,
                "f3_total_bytes": controls["F3"]["total_bytes"],
                "active_roles": [ROLE_NAMES[role] for role in sorted(active_roles)],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
