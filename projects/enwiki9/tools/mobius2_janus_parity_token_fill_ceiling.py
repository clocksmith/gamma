#!/usr/bin/env python3
"""Exact free-model ceiling for two-pass prose-token parity filling."""

from __future__ import annotations

import argparse
from bisect import bisect_right
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

from janus_paid_residual_mdl_oracle import range_decode, range_encode
from mobius2_tessera_self_annotation_graph import ROLE_IDS, canonical_lexeme
from mobius2_tessera_typed_fiber_ceiling import (
    Page,
    artifact,
    build_pages,
    event_metadata,
    project_frequencies,
    read_p1,
    sha256_bytes,
    sha256_file,
    split_byte_masks,
)
from wrt_exact import parse_store


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "mobius2_janus_parity_token_fill_ceiling_qh0_v1"
VARIANTS = ("U0", "C1", "FL", "FB", "FR")
VARIANT_IDS = {name: index for index, name in enumerate(VARIANTS, 1)}
SPLIT_NAMES = ("development", "selection", "sealed_confirmation")
ESC = -1
BOS = -2
EOS = -3
FRAME_MAGIC = b"PARFILL\0"
FRAME = struct.Struct("<8sB7xQQQQ32s")
GROSS_GATE_BYTES = 30_000
SIDE_TOTAL = 1 << 24
STATE_BITS = 63
MAX_CODE = (1 << STATE_BITS) - 1
HALF = 1 << (STATE_BITS - 1)
QUARTER = 1 << (STATE_BITS - 2)
THREE_QUARTERS = 3 * QUARTER


class SideEncoder:
    """Classic finite 63-bit arithmetic coder for Q24 distributions."""

    def __init__(self) -> None:
        self.low = 0
        self.high = MAX_CODE
        self.pending = 0
        self.bits: list[int] = []
        self.symbols = 0

    def _emit(self, bit: int) -> None:
        self.bits.append(bit)
        self.bits.extend([1 - bit] * self.pending)
        self.pending = 0

    def encode(self, distribution: Any, symbol: int) -> None:
        index = distribution.symbol_index(symbol)
        width = self.high - self.low + 1
        lower = distribution.cdf[index]
        upper = distribution.cdf[index + 1]
        self.high = self.low + (width * upper // SIDE_TOTAL) - 1
        self.low = self.low + (width * lower // SIDE_TOTAL)
        if self.low > self.high:
            raise ValueError("Q24 arithmetic interval collapsed")
        while True:
            if self.high < HALF:
                self._emit(0)
            elif self.low >= HALF:
                self._emit(1)
                self.low -= HALF
                self.high -= HALF
            elif self.low >= QUARTER and self.high < THREE_QUARTERS:
                self.pending += 1
                self.low -= QUARTER
                self.high -= QUARTER
            else:
                break
            self.low <<= 1
            self.high = (self.high << 1) | 1
        self.symbols += 1

    def finish(self) -> bytes:
        self.pending += 1
        self._emit(0 if self.low < QUARTER else 1)
        padding = (-len(self.bits)) % 8
        values = np.asarray(self.bits + [0] * padding, dtype=np.uint8)
        return np.packbits(values, bitorder="big").tobytes()


class SideDecoder:
    """Decoder paired with SideEncoder; the symbol count is externally known."""

    def __init__(self, payload: bytes) -> None:
        if not payload:
            raise ValueError("empty parity side payload")
        self.bits = np.unpackbits(
            np.frombuffer(payload, dtype=np.uint8), bitorder="big"
        )
        self.cursor = 0
        self.low = 0
        self.high = MAX_CODE
        self.code = 0
        for _ in range(STATE_BITS):
            self.code = (self.code << 1) | self._read_bit()
        self.symbols = 0

    def _read_bit(self) -> int:
        if self.cursor >= len(self.bits):
            return 0
        value = int(self.bits[self.cursor])
        self.cursor += 1
        return value

    def decode(self, distribution: Any) -> int:
        width = self.high - self.low + 1
        scaled = ((self.code - self.low + 1) * SIDE_TOTAL - 1) // width
        index = bisect_right(distribution.cdf, scaled) - 1
        if not 0 <= index < len(distribution.symbols):
            raise ValueError("Q24 side code is outside its CDF")
        lower = distribution.cdf[index]
        upper = distribution.cdf[index + 1]
        self.high = self.low + (width * upper // SIDE_TOTAL) - 1
        self.low = self.low + (width * lower // SIDE_TOTAL)
        while True:
            if self.high < HALF:
                pass
            elif self.low >= HALF:
                self.low -= HALF
                self.high -= HALF
                self.code -= HALF
            elif self.low >= QUARTER and self.high < THREE_QUARTERS:
                self.low -= QUARTER
                self.high -= QUARTER
                self.code -= QUARTER
            else:
                break
            self.low <<= 1
            self.high = (self.high << 1) | 1
            self.code = (self.code << 1) | self._read_bit()
        self.symbols += 1
        return distribution.symbols[index]


@dataclass(frozen=True)
class TokenRecord:
    event_index: int
    lexeme_id: int
    variant_id: int


def counter_rows(
    counter: Counter[tuple[int, ...]], key_length: int
) -> list[list[int]]:
    return [
        [*(int(value) for value in key[:key_length]), int(key[key_length]), int(count)]
        for key, count in sorted(counter.items())
    ]


def grouped_counter(
    rows: Iterable[Sequence[int]], context_length: int
) -> dict[tuple[int, ...], Counter[int]]:
    result: dict[tuple[int, ...], Counter[int]] = defaultdict(Counter)
    for row in rows:
        context = tuple(int(value) for value in row[:context_length])
        result[context][int(row[context_length])] = int(row[context_length + 1])
    return dict(result)


def collect_page_events(
    parsed: Any,
    pages: Sequence[Page],
    roles: np.ndarray,
) -> tuple[list[list[int]], list[int]]:
    page_events: list[list[int]] = [[] for _ in pages]
    eligible: list[int] = []
    page_index = 0
    prose_role = int(ROLE_IDS["PROSE_WORD"])
    for event_index, event in enumerate(parsed.events):
        while page_index < len(pages) and event.start >= pages[page_index].wrt_end:
            page_index += 1
        if page_index >= len(pages):
            break
        page = pages[page_index]
        if not (page.wrt_start <= event.start and event.end <= page.wrt_end):
            continue
        if event.kind == "token" and int(roles[event_index]) == prose_role:
            page_events[page_index].append(event_index)
            eligible.append(event_index)
    return page_events, eligible


def build_model(
    parsed: Any,
    pages: Sequence[Page],
    page_events: Sequence[Sequence[int]],
) -> tuple[bytes, list[list[TokenRecord]]]:
    lexemes = sorted(
        {
            canonical_lexeme(parsed.events[index].decoded)
            for indexes in page_events
            for index in indexes
        }
    )
    lexeme_ids = {value: index for index, value in enumerate(lexemes)}
    catalog_sets: dict[int, set[str]] = defaultdict(set)
    for indexes in page_events:
        for index in indexes:
            event = parsed.events[index]
            lexeme_id = lexeme_ids[canonical_lexeme(event.decoded)]
            catalog_sets[lexeme_id].add(event.encoded.hex())
    catalogs = {
        lexeme_id: tuple(sorted(values))
        for lexeme_id, values in sorted(catalog_sets.items())
    }
    catalog_ids = {
        lexeme_id: {value: index for index, value in enumerate(values)}
        for lexeme_id, values in catalogs.items()
    }
    records: list[list[TokenRecord]] = []
    for indexes in page_events:
        page_records = []
        for index in indexes:
            event = parsed.events[index]
            lexeme_id = lexeme_ids[canonical_lexeme(event.decoded)]
            page_records.append(
                TokenRecord(
                    index,
                    lexeme_id,
                    catalog_ids[lexeme_id][event.encoded.hex()],
                )
            )
        records.append(page_records)

    base: Counter[int] = Counter()
    variants: Counter[tuple[int, int]] = Counter()
    sequential: Counter[tuple[int, int]] = Counter()
    even: Counter[tuple[int, int]] = Counter()
    odd_left: Counter[tuple[int, int]] = Counter()
    odd_pair: Counter[tuple[int, int, int]] = Counter()
    odd_rotated: Counter[tuple[int, int, int]] = Counter()
    for page, page_records in zip(pages, records, strict=True):
        if page.split != 0:
            continue
        symbols = [record.lexeme_id for record in page_records]
        previous = BOS
        for record in page_records:
            base[record.lexeme_id] += 1
            variants[(record.lexeme_id, record.variant_id)] += 1
            sequential[(previous, record.lexeme_id)] += 1
            previous = record.lexeme_id
        previous_even = BOS
        for position in range(0, len(symbols), 2):
            symbol = symbols[position]
            even[(previous_even, symbol)] += 1
            previous_even = symbol
        for position in range(1, len(symbols), 2):
            symbol = symbols[position]
            left = symbols[position - 1]
            right = symbols[position + 1] if position + 1 < len(symbols) else EOS
            rotated = symbols[position + 3] if position + 3 < len(symbols) else EOS
            odd_left[(left, symbol)] += 1
            odd_pair[(left, right, symbol)] += 1
            odd_rotated[(left, rotated, symbol)] += 1

    model = {
        "schema": "mobius2_janus_parity_token_fill_model_qh0_v1",
        "lexemes": lexemes,
        "catalogs": {str(key): list(value) for key, value in catalogs.items()},
        "base": [[int(symbol), int(count)] for symbol, count in sorted(base.items())],
        "variants": counter_rows(variants, 1),
        "sequential": counter_rows(sequential, 1),
        "even": counter_rows(even, 1),
        "odd_left": counter_rows(odd_left, 1),
        "odd_pair": counter_rows(odd_pair, 2),
        "odd_rotated": counter_rows(odd_rotated, 2),
        "development_pages": sum(page.split == 0 for page in pages),
    }
    blob = json.dumps(model, sort_keys=True, separators=(",", ":")).encode()
    return blob, records


class ParityModel:
    def __init__(self, blob: bytes) -> None:
        data = json.loads(blob)
        if data.get("schema") != "mobius2_janus_parity_token_fill_model_qh0_v1":
            raise ValueError("invalid parity token-fill model")
        self.lexemes = tuple(str(value) for value in data["lexemes"])
        self.catalogs = {
            int(key): tuple(bytes.fromhex(value) for value in values)
            for key, values in data["catalogs"].items()
        }
        self.base = Counter({int(row[0]): int(row[1]) for row in data["base"]})
        self.variants = grouped_counter(data["variants"], 1)
        self.tables = {
            "sequential": grouped_counter(data["sequential"], 1),
            "even": grouped_counter(data["even"], 1),
            "odd_left": grouped_counter(data["odd_left"], 1),
            "odd_pair": grouped_counter(data["odd_pair"], 2),
            "odd_rotated": grouped_counter(data["odd_rotated"], 2),
        }
        self.cache: dict[tuple[Any, ...], Any] = {}

    def _distribution(
        self,
        key: tuple[Any, ...],
        symbols: Sequence[int],
        counts: dict[int, int],
    ) -> Any:
        distribution = self.cache.get(key)
        if distribution is None:
            distribution = project_frequencies(symbols, counts)
            self.cache[key] = distribution
        return distribution

    def base_dist(self) -> Any:
        symbols = tuple(range(len(self.lexemes)))
        return self._distribution(
            ("base",), symbols, {symbol: int(self.base[symbol]) for symbol in symbols}
        )

    def variant_dist(self, lexeme_id: int) -> Any:
        symbols = tuple(range(len(self.catalogs[lexeme_id])))
        counts = self.variants.get((lexeme_id,), Counter())
        return self._distribution(
            ("variant", lexeme_id),
            symbols,
            {symbol: int(counts[symbol]) for symbol in symbols},
        )

    def context_dist(self, table: str, context: tuple[int, ...]) -> Any | None:
        counts = self.tables[table].get(context)
        if not counts:
            return None
        symbols = tuple(sorted((ESC, *counts.keys())))
        projected = {symbol: int(counts[symbol]) for symbol in counts}
        projected[ESC] = max(1, len(counts))
        return self._distribution((table, *context), symbols, projected)

    def encode_symbol(
        self,
        encoder: SideEncoder,
        symbol: int,
        primary: tuple[str, tuple[int, ...]] | None,
        fallback: tuple[str, tuple[int, ...]] | None = None,
    ) -> None:
        for entry in (primary, fallback):
            if entry is None:
                continue
            table, context = entry
            distribution = self.context_dist(table, context)
            if distribution is None:
                continue
            counts = self.tables[table][context]
            if symbol in counts:
                encoder.encode(distribution, symbol)
                return
            encoder.encode(distribution, ESC)
        encoder.encode(self.base_dist(), symbol)

    def decode_symbol(
        self,
        decoder: SideDecoder,
        primary: tuple[str, tuple[int, ...]] | None,
        fallback: tuple[str, tuple[int, ...]] | None = None,
    ) -> int:
        for entry in (primary, fallback):
            if entry is None:
                continue
            table, context = entry
            distribution = self.context_dist(table, context)
            if distribution is None:
                continue
            symbol = decoder.decode(distribution)
            if symbol != ESC:
                return symbol
        return decoder.decode(self.base_dist())

    def encode_record(
        self,
        encoder: SideEncoder,
        record: TokenRecord,
        primary: tuple[str, tuple[int, ...]] | None,
        fallback: tuple[str, tuple[int, ...]] | None = None,
    ) -> None:
        self.encode_symbol(encoder, record.lexeme_id, primary, fallback)
        encoder.encode(self.variant_dist(record.lexeme_id), record.variant_id)

    def decode_record(
        self,
        decoder: SideDecoder,
        primary: tuple[str, tuple[int, ...]] | None,
        fallback: tuple[str, tuple[int, ...]] | None = None,
    ) -> tuple[int, int, bytes]:
        lexeme_id = self.decode_symbol(decoder, primary, fallback)
        variant_id = decoder.decode(self.variant_dist(lexeme_id))
        return lexeme_id, variant_id, self.catalogs[lexeme_id][variant_id]


def parity_context(
    variant: str,
    symbols: Sequence[int],
    position: int,
) -> tuple[tuple[str, tuple[int, ...]], tuple[str, tuple[int, ...]] | None]:
    left = symbols[position - 1]
    if variant == "FL":
        return ("odd_left", (left,)), None
    if variant == "FB":
        right = symbols[position + 1] if position + 1 < len(symbols) else EOS
        return ("odd_pair", (left, right)), ("odd_left", (left,))
    rotated = symbols[position + 3] if position + 3 < len(symbols) else EOS
    return ("odd_rotated", (left, rotated)), ("odd_left", (left,))


def encode_side(
    model: ParityModel,
    variant: str,
    pages: Sequence[Page],
    records: Sequence[Sequence[TokenRecord]],
    allowed_splits: set[int] | None = None,
) -> tuple[bytes, int]:
    encoder = SideEncoder()
    encoded_records = 0
    for page, page_records in zip(pages, records, strict=True):
        if allowed_splits is not None and page.split not in allowed_splits:
            continue
        if variant in ("U0", "C1"):
            previous = BOS
            for record in page_records:
                primary = None if variant == "U0" else ("sequential", (previous,))
                model.encode_record(encoder, record, primary)
                previous = record.lexeme_id
                encoded_records += 1
            continue
        symbols = [record.lexeme_id for record in page_records]
        previous_even = BOS
        for position in range(0, len(page_records), 2):
            record = page_records[position]
            model.encode_record(encoder, record, ("even", (previous_even,)))
            previous_even = record.lexeme_id
            encoded_records += 1
        for position in range(1, len(page_records), 2):
            primary, fallback = parity_context(variant, symbols, position)
            model.encode_record(encoder, page_records[position], primary, fallback)
            encoded_records += 1
    return encoder.finish(), encoded_records


def decode_side(
    model: ParityModel,
    variant: str,
    payload: bytes,
    pages: Sequence[Page],
    records: Sequence[Sequence[TokenRecord]],
    parsed: Any,
    allowed_splits: set[int] | None = None,
) -> tuple[dict[int, bytes], int]:
    decoder = SideDecoder(payload)
    output: dict[int, bytes] = {}
    for page, expected in zip(pages, records, strict=True):
        if allowed_splits is not None and page.split not in allowed_splits:
            continue
        decoded: list[tuple[int, int, bytes] | None] = [None] * len(expected)
        if variant in ("U0", "C1"):
            previous = BOS
            for position in range(len(expected)):
                primary = None if variant == "U0" else ("sequential", (previous,))
                decoded[position] = model.decode_record(decoder, primary)
                previous = decoded[position][0]
        else:
            previous_even = BOS
            for position in range(0, len(expected), 2):
                decoded[position] = model.decode_record(
                    decoder, ("even", (previous_even,))
                )
                previous_even = decoded[position][0]
            symbols = [
                value[0] if value is not None else -999 for value in decoded
            ]
            for position in range(1, len(expected), 2):
                primary, fallback = parity_context(variant, symbols, position)
                decoded[position] = model.decode_record(decoder, primary, fallback)
                symbols[position] = decoded[position][0]
        for expected_record, value in zip(expected, decoded, strict=True):
            if value is None:
                raise ValueError("parity side decoder left a token unfilled")
            lexeme_id, variant_id, encoded = value
            if (
                lexeme_id != expected_record.lexeme_id
                or variant_id != expected_record.variant_id
                or encoded != parsed.events[expected_record.event_index].encoded
            ):
                raise ValueError(f"{variant} side token mismatch")
            output[expected_record.event_index] = encoded
    return output, decoder.symbols


def skip_mask(
    parsed: Any,
    records: Sequence[Sequence[TokenRecord]],
    allowed_splits: set[int] | None,
    pages: Sequence[Page],
) -> np.ndarray:
    mask = np.zeros(len(parsed.stream), dtype=np.bool_)
    for page, page_records in zip(pages, records, strict=True):
        if allowed_splits is not None and page.split not in allowed_splits:
            continue
        for record in page_records:
            event = parsed.events[record.event_index]
            mask[event.start : event.end] = True
    return mask


def make_frame(
    variant: str,
    raw_bytes: int,
    wrt_bytes: int,
    side: bytes,
    residual: bytes,
    model_sha256: str,
) -> bytes:
    return FRAME.pack(
        FRAME_MAGIC,
        VARIANT_IDS[variant],
        raw_bytes,
        wrt_bytes,
        len(side),
        len(residual),
        bytes.fromhex(model_sha256),
    ) + side + residual


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
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / CANDIDATE_ID)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    decision_path = args.output_dir / "decision.json"
    if decision_path.exists():
        raise FileExistsError("refusing to overwrite a prior parity-fill decision")

    trace_decision = json.loads(args.trace_recovery_decision.read_text())
    joint_decision = json.loads(args.joint_decision.read_text())
    if trace_decision["decision"]["verdict"] != "exact_joint_p1_trace_recovered":
        raise ValueError("joint trace is not certified")
    if sha256_file(args.joint_p1) != trace_decision["artifact"]["joint_p1"]["sha256"]:
        raise ValueError("joint P1 identity mismatch")
    expected_payload = joint_decision["payloads"]["JQ_context_quotient"]["sha256"]
    if sha256_file(args.joint_payload) != expected_payload:
        raise ValueError("joint payload identity mismatch")

    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("official WRT inverse differs from raw input")
    truth = np.unpackbits(np.frombuffer(parsed.stream, dtype=np.uint8), bitorder="big")
    p1 = read_p1(args.joint_p1, len(truth))
    parent_payload = args.joint_payload.read_bytes()
    if range_encode(p1, truth) != parent_payload:
        raise ValueError("joint parent payload replay mismatch")

    pages = build_pages(parsed)
    roles, _ = event_metadata(parsed, pages)
    page_events, eligible = collect_page_events(parsed, pages, roles)
    model_a, records_a = build_model(parsed, pages, page_events)
    model_b, records_b = build_model(parsed, pages, page_events)
    if model_a != model_b or records_a != records_b:
        raise ValueError("repeated parity model build differs")
    model_sha = sha256_bytes(model_a)
    model = ParityModel(model_a)
    compressed_model = zlib.compress(model_a, level=9)
    (args.output_dir / "model.qh0.json.zlib").write_bytes(compressed_model)

    skipped = skip_mask(parsed, records_a, None, pages)
    keep_rows = np.repeat(~skipped, 8)
    residual_p1 = np.asarray(p1[keep_rows], dtype=np.uint16)
    residual_truth = truth[keep_rows]
    residual_a = range_encode(residual_p1, residual_truth)
    residual_b = range_encode(residual_p1, residual_truth)
    if residual_a != residual_b or not np.array_equal(
        range_decode(residual_a, residual_p1), residual_truth
    ):
        raise ValueError("residual arithmetic replay failed")

    variants: dict[str, dict[str, Any]] = {}
    side_payloads: dict[str, bytes] = {}
    decoded_maps: dict[str, dict[int, bytes]] = {}
    archives: dict[str, bytes] = {}
    for variant in VARIANTS:
        side_a, token_count = encode_side(model, variant, pages, records_a)
        side_b, repeated_count = encode_side(model, variant, pages, records_a)
        if side_a != side_b or token_count != repeated_count:
            raise ValueError(f"repeated {variant} side stream differs")
        decoded, decoded_symbols = decode_side(
            model, variant, side_a, pages, records_a, parsed
        )
        if len(decoded) != len(eligible):
            raise ValueError(f"{variant} did not decode every eligible token")
        archive = make_frame(
            variant, len(raw), len(parsed.stream), side_a, residual_a, model_sha
        )
        side_payloads[variant] = side_a
        decoded_maps[variant] = decoded
        archives[variant] = archive
        variants[variant] = {
            "archive_bytes": len(archive),
            "gain_bytes": len(parent_payload) - len(archive),
            "gain_bytes_per_million": (len(parent_payload) - len(archive)) / 10.0,
            "residual_bytes": len(residual_a),
            "side_bytes": len(side_a),
            "side_symbols": decoded_symbols,
            "token_events": token_count,
            "sha256": sha256_bytes(archive),
        }

    split_masks = split_byte_masks(pages, len(parsed.stream))
    split_results: dict[str, dict[str, dict[str, int]]] = {}
    for split, split_name in enumerate(SPLIT_NAMES):
        rows = np.repeat(split_masks[split], 8)
        base_payload = range_encode(
            np.asarray(p1[rows], dtype=np.uint16), truth[rows]
        )
        split_skip = skip_mask(parsed, records_a, {split}, pages)
        candidate_rows = rows & np.repeat(~split_skip, 8)
        split_residual = range_encode(
            np.asarray(p1[candidate_rows], dtype=np.uint16), truth[candidate_rows]
        )
        split_results[split_name] = {}
        for variant in VARIANTS:
            split_side, _ = encode_side(model, variant, pages, records_a, {split})
            split_results[split_name][variant] = {
                "baseline_bytes": len(base_payload) + FRAME.size,
                "candidate_bytes": len(split_residual) + len(split_side) + FRAME.size,
                "gain_bytes": len(base_payload) - len(split_residual) - len(split_side),
            }

    chosen = "FB"
    decoded_residual_bytes = np.packbits(
        range_decode(residual_a, residual_p1), bitorder="big"
    )
    reconstructed = np.empty(len(parsed.stream), dtype=np.uint8)
    reconstructed[~skipped] = decoded_residual_bytes
    for event_index, encoded in decoded_maps[chosen].items():
        event = parsed.events[event_index]
        reconstructed[event.start : event.end] = np.frombuffer(encoded, dtype=np.uint8)
    reconstructed_bytes = reconstructed.tobytes()
    if reconstructed_bytes != parsed.stream:
        raise ValueError("complete WRT parity reconstruction failed")
    restored_store = args.output_dir / "reconstructed.store"
    restored_store.write_bytes(args.wrt_store.read_bytes()[:5] + reconstructed_bytes)
    restored = parse_store(restored_store, args.dictionary)
    raw_identity = restored.decoded == raw
    if not raw_identity:
        raise ValueError("official inverse failed after parity reconstruction")

    for variant in VARIANTS:
        rebuilt_side, _ = encode_side(model, variant, pages, records_a)
        rebuilt_archive = make_frame(
            variant, len(raw), len(parsed.stream), rebuilt_side, residual_b, model_sha
        )
        if rebuilt_archive != archives[variant]:
            raise ValueError(f"second {variant} archive differs")
        (args.output_dir / f"{variant}.archive").write_bytes(archives[variant])

    development_positive = split_results["development"][chosen]["gain_bytes"] > 0
    selection_positive = split_results["selection"][chosen]["gain_bytes"] > 0
    sealed_positive = split_results["sealed_confirmation"][chosen]["gain_bytes"] > 0
    ordering = all(
        variants[chosen]["archive_bytes"] < variants[control]["archive_bytes"]
        for control in ("U0", "C1", "FL", "FR")
    )
    gross_pass = variants[chosen]["gain_bytes"] >= GROSS_GATE_BYTES
    authorized = all(
        (development_positive, selection_positive, sealed_positive, ordering, gross_pass)
    )
    verdict = "AUTHORIZED_PAID_SCHEDULE_TABLE_GATE" if authorized else "REJECT"

    decision = {
        "schema": "gamma.mobius2_janus_parity_token_fill_ceiling_qh0.v1",
        "candidate_id": CANDIDATE_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": verdict,
        "claim_boundary": (
            "Free token-position schedule, static tables, catalogs, and source; "
            "actual side symbols, residual arithmetic, termination, and framing. "
            "Zero score and forecast credit."
        ),
        "population": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(parsed.stream),
            "complete_pages": len(pages),
            "eligible_prose_tokens": len(eligible),
            "development_pages": sum(page.split == 0 for page in pages),
            "selection_pages": sum(page.split == 1 for page in pages),
            "sealed_pages": sum(page.split == 2 for page in pages),
        },
        "parent": {
            "bytes": len(parent_payload),
            "sha256": sha256_bytes(parent_payload),
            "payload_identity": True,
        },
        "model": {
            "raw_bytes": len(model_a),
            "raw_sha256": model_sha,
            "compressed_bytes": len(compressed_model),
            "compressed_sha256": sha256_bytes(compressed_model),
            "charged_in_qh0": False,
            "lexemes": len(model.lexemes),
            "context_counts": {
                name: len(table) for name, table in model.tables.items()
            },
        },
        "variants": variants,
        "splits": split_results,
        "integrity": {
            "parent_payload_identity": True,
            "model_repeat_identity": True,
            "side_repeat_identity": True,
            "side_decode_exact": True,
            "residual_arithmetic_decode": True,
            "complete_wrt_identity": True,
            "official_raw_inverse": raw_identity,
            "second_archive_identity": True,
            "q24_probabilities_legal_nonzero": True,
            "free_position_schedule": True,
        },
        "gates": {
            "development_positive": development_positive,
            "selection_positive": selection_positive,
            "sealed_positive": sealed_positive,
            "FB_beats_all_controls": ordering,
            "gross_required_bytes": GROSS_GATE_BYTES,
            "gross_pass": gross_pass,
            "promotion_authorized": authorized,
        },
        "inputs": {
            "joint_p1": artifact(args.joint_p1),
            "joint_payload": artifact(args.joint_payload),
            "wrt_store": artifact(args.wrt_store),
            "raw_input": artifact(args.raw_input),
            "dictionary": artifact(args.dictionary),
            "trace_recovery_decision": artifact(args.trace_recovery_decision),
            "joint_decision": artifact(args.joint_decision),
            "script": artifact(Path(__file__).resolve()),
        },
        "score_credit_bytes": 0,
        "forecast_bytes": 109_389_323,
        "verified_full_1g_score_bytes": None,
    }
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "candidate_id": CANDIDATE_ID,
                "FB_gain_bytes": variants[chosen]["gain_bytes"],
                "FB_side_bytes": variants[chosen]["side_bytes"],
                "decision": verdict,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"mobius2-parity-token-fill: {error}")
        raise
