#!/usr/bin/env python3
"""Gate-minus-one oracle for SRSTC residual-program retrieval.

The candidate universe is causal: every correction program comes from a
complete prior 16-byte block and is read only from the preceding 64KiB WRT
epoch snapshot.  The oracle may inspect the current block to choose B0 or one
of at most eight available programs, but it pays a four-bit transmitted index.
That choice is noncausal evidence and earns no score credit.
"""

from __future__ import annotations

import argparse
from collections import OrderedDict, deque
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
from typing import Any, Iterable

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
sys.path.insert(0, str(TOOLS))

from causal_state_screen import WikiState  # noqa: E402
from streaming_retrieval_shadow import fnv64_bytes, simhash16  # noqa: E402
from wrt_exact import ParsedStore, WrtEvent, parse_store  # noqa: E402


CANDIDATE_ID = "srstc_residual_program_retrieval_qm1_v1"
PROPOSAL_ID = "srstc_residual_program_retrieval_q0_v1"
P1_MAGIC = b"CMX21P1\0"
PAGE_MAP_MAGIC = b"SIBMAP1\0"
PAGE_RECORD = struct.Struct("<QQQQ")
TOTAL = 1 << 16
BLOCK_BYTES = 16
PROGRAM_BITS = 128
PROGRAM_BYTES = 48
RECENT_PROGRAMS = 8
EPOCH_BYTES = 65_536
MAX_KEYS = 65_536
REFS_PER_KEY = 4
MIN_PROGRAMS = 3
MAX_CANDIDATES = 8
INDEX_BITS = 4
PROMOTION_BPM = 3_000.0
PROGRAM_ROTATION = 37

DEFAULT_STORE = Path("/home/x/enwiki9-nonproof/results/fx2_wrt_store_1m.bin")
DEFAULT_DICTIONARY = Path(
    "/home/x/enwiki9-nonproof/results/"
    "endpoint428_pair_layer0_gate_dot_fuse_output_update_loop_lzma_source_package_v1/"
    "clean-build-a/build/english.dic"
)
DEFAULT_P1 = PROJECT / "results/typed_event_sleeping_bayes_parent_trace_q0_v1/native_a.p1"
DEFAULT_ARCHIVE = PROJECT / "results/typed_event_sleeping_bayes_parent_trace_q0_v1/archive_a.bin"
DEFAULT_RAW = PROJECT / "data/enwik9_1000000.bin"
DEFAULT_PAGE_MAP = PROJECT / "results/endpoint_final_trace_1m_v1/page_map.bin"
DEFAULT_OUTPUT = PROJECT / f"results/{CANDIDATE_ID}/decision.json"

EXPECTED = {
    "store": (600_747, "1e209c7d19a22af5ce6a1de3bab1fc636669f40686aebd88bbe9dc8e5411e583"),
    "dictionary": (411_996, "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a"),
    "p1": (9_611_888, "02a263445e753604653c3cc8f7b05b783c379b0a84f576a62dd0f77438ab6715"),
    "archive": (173_902, "6d32bddb912b14d318f2770ae2624f59d76ab402ab0fb53a13a76d4f70d6da04"),
    "raw": (1_000_000, "369b688978f649681136198fb96db14c1616756260c55fb4b65e9bc049552cad"),
    "page_map": (5_488, "3122936977eb65650601c15cd0fa42bacbbd60ad3713e18c1e99fae1e5033425"),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def bind(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    result = artifact(path)
    expected_bytes, expected_sha = EXPECTED[label]
    if result["bytes"] != expected_bytes or result["sha256"] != expected_sha:
        raise ValueError(f"{label} differs from its frozen identity")
    return result


def load_p1(path: Path, expected_rows: int) -> np.ndarray:
    with path.open("rb") as source:
        header = source.read(16)
    if len(header) != 16 or header[:8] != P1_MAGIC:
        raise ValueError("invalid endpoint428 P1 header")
    rows = struct.unpack_from("<Q", header, 8)[0]
    if rows != expected_rows or path.stat().st_size != 16 + 2 * rows:
        raise ValueError("endpoint428 P1 rows differ from WRT truth")
    values = np.memmap(path, mode="r", dtype="<u2", offset=16, shape=(rows,))
    if np.any(values == 0):
        raise ValueError("endpoint428 P1 contains zero")
    return values


def truth_bits(stream: bytes) -> np.ndarray:
    return np.unpackbits(np.frombuffer(stream, dtype=np.uint8), bitorder="big")


def range_encode(probabilities: np.ndarray, truth: np.ndarray) -> bytes:
    output = bytearray()
    x1 = 0
    x2 = 0xFFFFFFFF
    for probability, actual in zip(probabilities, truth, strict=True):
        p1 = int(probability)
        delta = x2 - x1
        midpoint = x1 + (delta >> 16) * p1 + ((delta & 0xFFFF) * p1 >> 16)
        if int(actual):
            x2 = midpoint
        else:
            x1 = midpoint + 1
        while ((x1 ^ x2) & 0xFF000000) == 0:
            output.append((x2 >> 24) & 0xFF)
            x1 = (x1 << 8) & 0xFFFFFFFF
            x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
    while ((x1 ^ x2) & 0xFF000000) == 0:
        output.append((x2 >> 24) & 0xFF)
        x1 = (x1 << 8) & 0xFFFFFFFF
        x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
    output.append((x2 >> 24) & 0xFF)
    return bytes(output)


def range_decode_equal(payload: bytes, probabilities: np.ndarray, truth: np.ndarray) -> bool:
    if len(payload) < 4:
        return False
    cursor = 4
    code = int.from_bytes(payload[:4], "big")
    x1 = 0
    x2 = 0xFFFFFFFF
    for probability, expected in zip(probabilities, truth, strict=True):
        p1 = int(probability)
        delta = x2 - x1
        midpoint = x1 + (delta >> 16) * p1 + ((delta & 0xFFFF) * p1 >> 16)
        if code <= midpoint:
            actual = 1
            x2 = midpoint
        else:
            actual = 0
            x1 = midpoint + 1
        if actual != int(expected):
            return False
        while ((x1 ^ x2) & 0xFF000000) == 0:
            x1 = (x1 << 8) & 0xFFFFFFFF
            x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
            next_byte = payload[cursor] if cursor < len(payload) else 0
            cursor += 1
            code = ((code << 8) & 0xFFFFFFFF) + next_byte
    return True


def pack_q(q: np.ndarray) -> bytes:
    if q.shape != (PROGRAM_BITS,):
        raise ValueError("residual program has the wrong shape")
    output = bytearray()
    accumulator = 0
    used = 0
    for value in q:
        symbol = int(value) + 3
        if not 0 <= symbol <= 6:
            raise ValueError("residual symbol outside [-3, 3]")
        accumulator = (accumulator << 3) | symbol
        used += 3
        if used >= 8:
            used -= 8
            output.append((accumulator >> used) & 0xFF)
            accumulator &= (1 << used) - 1
    if used or len(output) != PROGRAM_BYTES:
        raise ValueError("residual program packing is not exact")
    return bytes(output)


def residual_program(p1: np.ndarray, bits: np.ndarray) -> tuple[np.ndarray, bytes]:
    target = np.where(bits != 0, TOTAL, 0).astype(np.int64)
    error = target - p1.astype(np.int64)
    magnitude = np.minimum(3, (np.abs(error) + 4_096) // 8_192)
    q = (np.sign(error) * magnitude).astype(np.int8)
    return q, pack_q(q)


def adjust_p1(parent: np.ndarray, q: np.ndarray) -> np.ndarray:
    result = parent.astype(np.uint64, copy=True)
    for residual in range(-3, 4):
        mask = q == residual
        if not np.any(mask) or residual == 0:
            continue
        if residual > 0:
            numerator = 5**residual
            denominator = 4**residual
        else:
            numerator = 4 ** (-residual)
            denominator = 5 ** (-residual)
        p = parent[mask].astype(np.uint64)
        divisor = numerator * p + denominator * (TOTAL - p)
        scaled = TOTAL * numerator * p
        result[mask] = (2 * scaled + divisor) // (2 * divisor)
    return np.clip(result, 1, TOTAL - 1).astype(np.uint16)


def qbit_cost(probabilities: np.ndarray, truth: np.ndarray) -> int:
    p = probabilities.astype(np.float64) / TOTAL
    likelihood = np.where(truth != 0, p, 1.0 - p)
    return int(np.rint(-np.log2(likelihood) * 256.0).astype(np.int64).sum())


def fnv64_codes(codes: Iterable[bytes]) -> int:
    value = 0xCBF29CE484222325
    for code in codes:
        value ^= len(code)
        value = (value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
        for byte in code:
            value ^= byte
            value = (value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return value


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
    if len(data) != 16 + count * PAGE_RECORD.size:
        raise ValueError("page map length mismatch")
    development_end = count * 3 // 5
    selection_end = count * 4 // 5
    pages: list[Page] = []
    for index in range(count):
        raw_start, raw_end, row_start, row_end = PAGE_RECORD.unpack_from(
            data, 16 + index * PAGE_RECORD.size
        )
        if row_start % 8 or row_end % 8:
            raise ValueError("page map is not WRT-byte aligned")
        split = (
            "development"
            if index < development_end
            else "selection"
            if index < selection_end
            else "sealed_confirmation"
        )
        page = Page(index, raw_start, raw_end, row_start // 8, row_end // 8, split)
        if not 0 <= page.wrt_start < page.wrt_end <= wrt_bytes:
            raise ValueError("page map exceeds WRT stream")
        pages.append(page)
    return pages


@dataclass(frozen=True)
class Program:
    ordinal: int
    q: np.ndarray
    packed: bytes
    completed_at: int


class ProgramTable:
    def __init__(self) -> None:
        self.live: OrderedDict[tuple[int, ...], deque[int]] = OrderedDict()
        self.snapshot: dict[tuple[int, ...], tuple[int, ...]] = {}
        self.programs: dict[int, Program] = {}
        self.snapshot_epoch = 0
        self.evicted_keys = 0

    def open_epoch(self, epoch: int) -> None:
        if epoch < self.snapshot_epoch:
            raise ValueError("epoch moved backward")
        while self.snapshot_epoch < epoch:
            self.snapshot = {key: tuple(refs) for key, refs in self.live.items()}
            self.snapshot_epoch += 1

    def candidates(self, keys: tuple[tuple[int, ...], ...], epoch_start: int) -> list[Program]:
        newest: dict[bytes, Program] = {}
        for key in keys:
            for ordinal in self.snapshot.get(key, ()):
                program = self.programs[ordinal]
                if program.completed_at > epoch_start:
                    raise ValueError("snapshot exposed a current-epoch program")
                previous = newest.get(program.packed)
                if previous is None or program.ordinal > previous.ordinal:
                    newest[program.packed] = program
        ordered = sorted(newest.values(), key=lambda item: (-item.ordinal, item.packed))
        return ordered[:MAX_CANDIDATES]

    def insert(self, keys: tuple[tuple[int, ...], ...], program: Program) -> None:
        self.programs[program.ordinal] = program
        for key in keys:
            refs = self.live.get(key)
            if refs is None:
                if len(self.live) >= MAX_KEYS:
                    self.live.popitem(last=False)
                    self.evicted_keys += 1
                refs = deque(maxlen=REFS_PER_KEY)
                self.live[key] = refs
            refs.append(program.ordinal)


@dataclass(frozen=True)
class Opportunity:
    start: int
    split: str | None
    candidates: int
    chosen: int
    parent_qbits: int
    chosen_qbits: int


@dataclass
class BuildResult:
    probabilities: np.ndarray
    indices: bytes
    opportunities: list[Opportunity]
    table_keys: int
    evicted_keys: int
    programs: int
    blocks: int
    snapshot_epochs: int
    candidate_histogram: dict[str, int]


def block_split(pages: list[Page], start: int, end: int, page_cursor: int) -> tuple[str | None, int]:
    while page_cursor < len(pages) and pages[page_cursor].wrt_end <= start:
        page_cursor += 1
    if page_cursor < len(pages):
        page = pages[page_cursor]
        if page.wrt_start <= start and end <= page.wrt_end:
            return page.split, page_cursor
    return None, page_cursor


def pack_indices(values: list[int]) -> bytes:
    output = bytearray()
    for offset in range(0, len(values), 2):
        high = values[offset]
        low = values[offset + 1] if offset + 1 < len(values) else 0
        if not 0 <= high < 16 or not 0 <= low < 16:
            raise ValueError("oracle index exceeds four bits")
        output.append((high << 4) | low)
    return bytes(output)


def make_keys(
    recent: deque[bytes],
    wiki: WikiState,
    current_prefix: bytes,
    event_chain: deque[bytes],
    first_p1: int,
) -> tuple[tuple[int, ...], ...]:
    signature = simhash16(b"".join(recent))
    prefix_hash = fnv64_bytes(current_prefix) & 0xFF
    chain_hash = fnv64_codes(event_chain) & 0xFFFF
    return (
        (0, signature, wiki.field_id, wiki.mode),
        (1, signature & 0xFF, wiki.slot, min(len(current_prefix), 7), prefix_hash),
        (2, (signature >> 8) & 0xFF, chain_hash, first_p1 >> 12),
    )


def build_oracle(
    parsed: ParsedStore,
    parent: np.ndarray,
    truth: np.ndarray,
    pages: list[Page],
) -> BuildResult:
    probabilities = np.array(parent, dtype=np.uint16, copy=True)
    table = ProgramTable()
    recent: deque[bytes] = deque(maxlen=RECENT_PROGRAMS)
    event_chain: deque[bytes] = deque(maxlen=4)
    wiki = WikiState()
    events = parsed.events
    event_cursor = 0
    page_cursor = 0
    opportunities: list[Opportunity] = []
    chosen_indices: list[int] = []
    histogram: dict[str, int] = {}
    blocks = 0
    ordinal = 0

    for start in range(6, len(parsed.stream) - BLOCK_BYTES + 1, BLOCK_BYTES):
        end = start + BLOCK_BYTES
        blocks += 1
        while event_cursor < len(events) and events[event_cursor].end <= start:
            event = events[event_cursor]
            for byte in event.decoded:
                wiki.update(byte)
            event_chain.append(event.encoded)
            event_cursor += 1

        current_prefix = b""
        if event_cursor < len(events):
            event = events[event_cursor]
            if event.start <= start < event.end:
                current_prefix = parsed.stream[event.start:start]

        relative_start = start - 6
        epoch = relative_start // EPOCH_BYTES
        table.open_epoch(epoch)
        epoch_start = 6 + epoch * EPOCH_BYTES
        row_start = start * 8
        row_end = end * 8
        block_parent = np.asarray(parent[row_start:row_end])
        block_truth = truth[row_start:row_end]
        keys = make_keys(recent, wiki, current_prefix, event_chain, int(block_parent[0]))
        candidates = table.candidates(keys, epoch_start)
        histogram[str(len(candidates))] = histogram.get(str(len(candidates)), 0) + 1
        split, page_cursor = block_split(pages, start, end, page_cursor)

        chosen = 0
        parent_cost = qbit_cost(block_parent, block_truth)
        chosen_cost = parent_cost
        chosen_probabilities = block_parent
        if len(candidates) >= MIN_PROGRAMS:
            for index, candidate in enumerate(candidates, start=1):
                adjusted = adjust_p1(block_parent, candidate.q)
                cost = qbit_cost(adjusted, block_truth)
                if cost < chosen_cost:
                    chosen = index
                    chosen_cost = cost
                    chosen_probabilities = adjusted
            probabilities[row_start:row_end] = chosen_probabilities
            chosen_indices.append(chosen)
            opportunities.append(
                Opportunity(start, split, len(candidates), chosen, parent_cost, chosen_cost)
            )

        q, packed = residual_program(block_parent, block_truth)
        ordinal += 1
        program = Program(ordinal, q, packed, end)
        table.insert(keys, program)
        recent.append(packed)

    return BuildResult(
        probabilities=probabilities,
        indices=pack_indices(chosen_indices),
        opportunities=opportunities,
        table_keys=len(table.live),
        evicted_keys=table.evicted_keys,
        programs=len(table.programs),
        blocks=blocks,
        snapshot_epochs=table.snapshot_epoch + 1,
        candidate_histogram=dict(sorted(histogram.items(), key=lambda item: int(item[0]))),
    )


def split_arrays(
    pages: list[Page],
    split: str,
    probabilities: np.ndarray,
    truth: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, int, int]:
    selected = [page for page in pages if page.split == split]
    p = np.concatenate([probabilities[page.wrt_start * 8 : page.wrt_end * 8] for page in selected])
    y = np.concatenate([truth[page.wrt_start * 8 : page.wrt_end * 8] for page in selected])
    raw_bytes = sum(page.raw_end - page.raw_start for page in selected)
    return p, y, raw_bytes, len(selected)


def side_bytes(opportunities: list[Opportunity], split: str | None = None) -> int:
    count = sum(1 for item in opportunities if split is None or item.split == split)
    return (count * INDEX_BITS + 7) // 8


def build_receipt(args: argparse.Namespace) -> dict[str, Any]:
    inputs = {
        "store": bind(args.store, "store"),
        "dictionary": bind(args.dictionary, "dictionary"),
        "p1": bind(args.p1, "p1"),
        "archive": bind(args.parent_archive, "archive"),
        "raw": bind(args.raw, "raw"),
        "page_map": bind(args.page_map, "page_map"),
    }
    parsed = parse_store(args.store, args.dictionary)
    raw = args.raw.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("official WRT inverse differs from canonical raw input")
    truth = truth_bits(parsed.stream)
    parent = load_p1(args.p1, len(truth))
    pages = read_pages(args.page_map, len(parsed.stream))

    parent_payload = range_encode(parent, truth)
    archive = args.parent_archive.read_bytes()
    if archive[37:] != parent_payload:
        raise ValueError("endpoint428 parent payload is not byte-identical")
    if not range_decode_equal(parent_payload, parent, truth):
        raise ValueError("endpoint428 parent arithmetic decode failed")

    first = build_oracle(parsed, parent, truth, pages)
    second = build_oracle(parsed, parent, truth, pages)
    deterministic = (
        np.array_equal(first.probabilities, second.probabilities)
        and first.indices == second.indices
        and first.opportunities == second.opportunities
        and first.candidate_histogram == second.candidate_histogram
    )
    if not deterministic:
        raise ValueError("oracle candidate universe is nondeterministic")
    if np.any(first.probabilities == 0):
        raise ValueError("oracle emitted an illegal probability")

    oracle_payload = range_encode(first.probabilities, truth)
    oracle_decode = range_decode_equal(oracle_payload, first.probabilities, truth)
    if not oracle_decode:
        raise ValueError("oracle residual arithmetic decode failed")
    reconstructed = np.packbits(truth, bitorder="big").tobytes()
    if reconstructed != parsed.stream:
        raise ValueError("truth bits do not reconstruct the complete WRT stream")

    split_rows: dict[str, Any] = {}
    all_split_pass = True
    for split in ("development", "selection", "sealed_confirmation"):
        parent_split, split_truth, raw_bytes, page_count = split_arrays(
            pages, split, parent, truth
        )
        oracle_split, _, _, _ = split_arrays(pages, split, first.probabilities, truth)
        parent_bytes = len(range_encode(parent_split, split_truth))
        residual_bytes = len(range_encode(oracle_split, split_truth))
        index_bytes = side_bytes(first.opportunities, split)
        total_bytes = residual_bytes + index_bytes
        gain = parent_bytes - total_bytes
        gain_bpm = gain * 1_000_000.0 / raw_bytes
        passed = gain_bpm >= PROMOTION_BPM
        all_split_pass = all_split_pass and passed
        split_rows[split] = {
            "pages": page_count,
            "raw_bytes": raw_bytes,
            "parent_payload_bytes": parent_bytes,
            "oracle_residual_payload_bytes": residual_bytes,
            "oracle_index_bytes": index_bytes,
            "oracle_total_bytes": total_bytes,
            "gain_bytes": gain,
            "gain_bytes_per_million": gain_bpm,
            "gate_3000_bpm": passed,
            "opportunities": sum(1 for item in first.opportunities if item.split == split),
            "chosen_nonparent": sum(
                1 for item in first.opportunities if item.split == split and item.chosen != 0
            ),
        }

    full_index_bytes = side_bytes(first.opportunities)
    full_total = len(oracle_payload) + full_index_bytes
    full_gain = len(parent_payload) - full_total
    verdict = "AUTHORIZED_CAUSAL_Q0" if all_split_pass else "REJECT"
    return {
        "schema": "srstc_residual_program_candidate_universe_ceiling_v1",
        "candidate_id": CANDIDATE_ID,
        "proposal_id": PROPOSAL_ID,
        "evidence_level": "zero_credit_noncausal_candidate_universe_ceiling",
        "inputs": inputs,
        "population": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(parsed.stream),
            "truth_rows": len(truth),
            "complete_pages": len(pages),
            "blocks": first.blocks,
        },
        "architecture": {
            "block_bytes": BLOCK_BYTES,
            "program_bits": PROGRAM_BITS,
            "residual_symbols": [-3, -2, -1, 0, 1, 2, 3],
            "residual_step": 8_192,
            "recent_programs": RECENT_PROGRAMS,
            "program_packing": "q_plus_3_msb_first_three_bits",
            "simhash": "three_byte_ngram_fnv_simhash16",
            "epoch_bytes": EPOCH_BYTES,
            "max_keys": MAX_KEYS,
            "references_per_key": REFS_PER_KEY,
            "minimum_distinct_programs": MIN_PROGRAMS,
            "maximum_candidates": MAX_CANDIDATES,
            "oracle_index_bits": INDEX_BITS,
            "odds_ladder": "(5/4)^q integer nearest ties upward",
            "q0_shuffled_control_rotation": PROGRAM_ROTATION,
        },
        "candidate_universe": {
            "snapshot_epochs": first.snapshot_epochs,
            "programs": first.programs,
            "live_keys_final": first.table_keys,
            "evicted_keys": first.evicted_keys,
            "candidate_count_histogram": first.candidate_histogram,
            "eligible_opportunities": len(first.opportunities),
            "chosen_nonparent": sum(item.chosen != 0 for item in first.opportunities),
            "indices_bytes": len(first.indices),
            "indices_sha256": sha256_bytes(first.indices),
            "mean_qbit_gain_before_index": (
                sum(item.parent_qbits - item.chosen_qbits for item in first.opportunities)
                / max(1, len(first.opportunities))
            ),
        },
        "economics": {
            "full_parent_payload_bytes": len(parent_payload),
            "full_oracle_residual_payload_bytes": len(oracle_payload),
            "full_oracle_index_bytes": full_index_bytes,
            "full_oracle_total_bytes": full_total,
            "full_gain_bytes": full_gain,
            "full_gain_bytes_per_million": full_gain,
            "splits": split_rows,
            "promotion_threshold_bytes_per_million": PROMOTION_BPM,
        },
        "proof": {
            "all_input_identities_exact": True,
            "parent_payload_byte_identity": True,
            "parent_arithmetic_decode": True,
            "candidate_programs_preceding_epoch_only": True,
            "oracle_arithmetic_decode": oracle_decode,
            "complete_wrt_reconstruction": reconstructed == parsed.stream,
            "official_raw_inverse": parsed.decoded == raw,
            "all_probabilities_legal_nonzero": True,
            "second_candidate_universe_identical": deterministic,
            "second_index_stream_identical": first.indices == second.indices,
            "valid_reject_exits_zero": True,
        },
        "decision": {
            "verdict": verdict,
            "causal_q0_authorized": all_split_pass,
            "score_credit_bytes": 0,
            "forecast_bytes": 109_389_323,
            "verified_full_1g_score": None,
            "next_action": (
                "materialize frozen B0/F0/R0/RB/RS causal Q0"
                if all_split_pass
                else "retire the frozen residual-program candidate universe without rescue sweeps"
            ),
        },
        "claim_boundary": (
            "The oracle index is chosen after reading each current block and therefore earns zero "
            "score credit. A pass authorizes only the frozen causal matched-control Q0."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--p1", type=Path, default=DEFAULT_P1)
    parser.add_argument("--parent-archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--page-map", type=Path, default=DEFAULT_PAGE_MAP)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    receipt = build_receipt(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    args.output.write_text(encoded)
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
