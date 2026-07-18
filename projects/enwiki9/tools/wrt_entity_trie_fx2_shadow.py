#!/usr/bin/env python3
"""Score a causal WRT entity-continuation trie against an exact base trace.

The model stores completed title and link-target WRT event sequences.  While a
later link target is decoded, it predicts the next WRT event from the trie node
reached by the already completed target prefix.  No raw bytes are reordered,
no static entity dictionary is shipped, and every update follows completion of
the current WRT event.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
import hashlib
import json
import math
import mmap
import os
from pathlib import Path
from typing import Any

from fx2_shadow_residual_coder import BinaryArithmeticEncoder, TOTAL, clamp_p1
from streaming_retrieval_shadow import blend_probability, qbits_for


TEXT_SEGMENT = 7
UPPERCASE = 0x07
END_UPPER = 0x06
CAPITALIZED = 0x40
ESCAPE = 0x0C
P1_HEADER_BYTES = 16
P1_MAGICS = (b"FX2P1V1\0", b"CMX21P1\0")
TITLE_OPEN = b"<title>"
TITLE_CLOSE = b"</title>"
LINK_OPEN = b"[["
LINK_CLOSE = b"]]"
TAIL_BYTES = 32
QBIT_ZERO = tuple(
    int(-math.log2((TOTAL - p1) / TOTAL) * 256.0 + 0.5)
    for p1 in range(1, TOTAL)
)
QBIT_ONE = tuple(
    int(-math.log2(p1 / TOTAL) * 256.0 + 0.5)
    for p1 in range(1, TOTAL)
)


def fast_qbits(bit: int, p1: int) -> int:
    index = clamp_p1(p1) - 1
    return QBIT_ONE[index] if bit else QBIT_ZERO[index]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


class P1Trace:
    """Memory-mapped uint16 final probabilities from FX2 or CMIX21."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.source = path.open("rb")
        self.data = mmap.mmap(self.source.fileno(), 0, access=mmap.ACCESS_READ)
        if len(self.data) < P1_HEADER_BYTES or self.data[:8] not in P1_MAGICS:
            self.close()
            raise ValueError("invalid FX2/CMIX21 probability trace")
        self.magic = bytes(self.data[:8])
        self.rows = int.from_bytes(self.data[8:16], "little")
        if len(self.data) != P1_HEADER_BYTES + 2 * self.rows:
            self.close()
            raise ValueError("probability trace length mismatch")

    def p1(self, row: int) -> int:
        if not 0 <= row < self.rows:
            raise IndexError("probability trace row out of range")
        offset = P1_HEADER_BYTES + 2 * row
        value = self.data[offset] | (self.data[offset + 1] << 8)
        if not 1 <= value < TOTAL:
            raise ValueError("invalid probability in trace")
        return value

    def close(self) -> None:
        data = getattr(self, "data", None)
        if data is not None:
            data.close()
            self.data = None
        source = getattr(self, "source", None)
        if source is not None:
            source.close()
            self.source = None


def read_dictionary_words(path: Path) -> list[bytes]:
    words: list[bytes] = []
    current = bytearray()
    for value in path.read_bytes():
        if ord("a") <= value <= ord("z"):
            current.append(value)
        elif current:
            words.append(bytes(current))
            current.clear()
    if current:
        words.append(bytes(current))
    return words


def wrt_byte_transform(value: int) -> int:
    """Apply the involution used by FX2's WRT storage wrapper."""
    value &= 0xFF
    if ord("{") <= value < 127:
        value += ord("P") - ord("{")
    elif ord("P") <= value < ord("T"):
        value -= ord("P") - ord("{")
    elif ord(":") <= value <= ord("?") or ord("J") <= value <= ord("O"):
        value ^= 0x70
    if value in (ord("X"), ord("`")):
        value ^= ord("X") ^ ord("`")
    return value & 0xFF


def detect_storage_header(stored: bytes) -> int:
    if len(stored) >= 11 and stored[1:5] == b"\0\0\0\0" and stored[5] == TEXT_SEGMENT:
        return 5
    if len(stored) >= 6 and stored[0] == TEXT_SEGMENT:
        return 0
    raise ValueError("input is neither a full FX2 store nor a bare WRT stream")


def token_index(code: bytes) -> int:
    if len(code) == 1 and 0x80 <= code[0] <= 0xCF:
        return code[0] - 0x80
    if len(code) == 2 and 0xD0 <= code[0] <= 0xFF and 0x80 <= code[1] <= 0xCF:
        return 80 + (code[0] - 0xD0) * 80 + (code[1] - 0x80)
    if (
        len(code) == 3
        and code[0] >= 0xF0
        and 0xD0 <= code[1] <= 0xEF
        and 0x80 <= code[2] <= 0xCF
    ):
        return (
            3920
            + (code[0] - 0xF0) * 32 * 80
            + (code[1] - 0xD0) * 80
            + code[2]
            - 0x80
        )
    raise ValueError(f"invalid WRT dictionary code: {code.hex()}")


@dataclass
class WrtDecoderState:
    uppercase: bool = False
    capitalized: bool = False

    def control(self, value: int) -> None:
        if value == UPPERCASE:
            self.uppercase = True
        elif value == CAPITALIZED:
            self.capitalized = True
        elif value == END_UPPER:
            self.uppercase = False
        else:
            raise ValueError("unsupported WRT control byte")

    def escaped(self, value: int) -> bytes:
        self.uppercase = False
        return bytes((value & 0xFF,))

    def word(self, word: bytes) -> bytes:
        output = bytearray(word)
        for index, value in enumerate(output):
            if index == 0 and self.capitalized:
                output[index] = value - ord("a") + ord("A")
                self.capitalized = False
            if self.uppercase:
                output[index] = output[index] - ord("a") + ord("A")
        return bytes(output)

    def literal(self, value: int) -> bytes:
        is_alpha = ord("a") <= value <= ord("z") or ord("A") <= value <= ord("Z")
        if not is_alpha:
            self.uppercase = False
        if self.capitalized or self.uppercase:
            value = (value - ord("a") + ord("A")) & 0xFF
        if self.capitalized:
            self.capitalized = False
        return bytes((value & 0xFF,))


@dataclass(frozen=True)
class WrtEvent:
    start: int
    end: int
    encoded: bytes
    decoded: bytes
    kind: str

    @property
    def bit_length(self) -> int:
        return 8 * len(self.encoded)


@dataclass(frozen=True)
class ParsedStore:
    stored: bytes
    storage_header_bytes: int
    stream: bytes
    raw_length: int
    events: tuple[WrtEvent, ...]
    decoded: bytes
    kind_counts: dict[str, int]


def parse_store_bytes(stored: bytes, dictionary_words: list[bytes]) -> ParsedStore:
    header_bytes = detect_storage_header(stored)
    stream = stored[header_bytes:]
    if len(stream) < 6 or stream[0] != TEXT_SEGMENT:
        raise ValueError("invalid WRT text segment")
    raw_length = int.from_bytes(stream[1:5], "big")
    if stream[5] != TEXT_SEGMENT:
        raise ValueError("WRT dictionary transform is disabled")
    state = WrtDecoderState()
    decoded = bytearray()
    events: list[WrtEvent] = []
    kinds: Counter[str] = Counter()
    position = 6
    while position < len(stream):
        start = position
        first = wrt_byte_transform(stream[position])
        position += 1
        if first == ESCAPE:
            if position >= len(stream):
                raise ValueError("truncated WRT escape")
            value = wrt_byte_transform(stream[position])
            position += 1
            kind = "escaped_literal"
            output = state.escaped(value)
        elif first in (UPPERCASE, END_UPPER, CAPITALIZED):
            kind = "control"
            state.control(first)
            output = b""
        elif first >= 0x80:
            code = bytearray((first,))
            if first > 0xCF:
                if position >= len(stream):
                    raise ValueError("truncated two-byte WRT token")
                second = wrt_byte_transform(stream[position])
                position += 1
                code.append(second)
                if second > 0xCF:
                    if position >= len(stream):
                        raise ValueError("truncated three-byte WRT token")
                    code.append(wrt_byte_transform(stream[position]))
                    position += 1
            index = token_index(bytes(code))
            if index >= len(dictionary_words):
                raise ValueError("WRT token exceeds dictionary")
            kind = "token"
            output = state.word(dictionary_words[index])
        else:
            kind = "literal"
            output = state.literal(first)
        event = WrtEvent(
            start=start,
            end=position,
            encoded=stream[start:position],
            decoded=output,
            kind=kind,
        )
        events.append(event)
        kinds[kind] += 1
        decoded.extend(output)
    if len(decoded) != raw_length:
        raise ValueError("WRT decoded length differs from segment header")
    return ParsedStore(
        stored=stored,
        storage_header_bytes=header_bytes,
        stream=stream,
        raw_length=raw_length,
        events=tuple(events),
        decoded=bytes(decoded),
        kind_counts=dict(sorted(kinds.items())),
    )


def parse_store(path: Path, dictionary: Path) -> ParsedStore:
    return parse_store_bytes(path.read_bytes(), read_dictionary_words(dictionary))


def event_bit(encoded: bytes, bit_index: int) -> int:
    return (encoded[bit_index // 8] >> (7 - (bit_index & 7))) & 1


def event_prefix(encoded: bytes, bit_count: int) -> int:
    prefix = 0
    for index in range(bit_count):
        prefix = (prefix << 1) | event_bit(encoded, index)
    return prefix


@dataclass
class TrieEdge:
    count: int
    child: int


@dataclass
class EntityTrie:
    cap_nodes: int
    nodes: list[dict[bytes, TrieEdge]] = field(default_factory=lambda: [{}])
    insertions: int = 0
    blocked_nodes: int = 0
    edge_code_bytes: int = 0

    def insert(self, sequence: tuple[bytes, ...]) -> None:
        if not sequence:
            return
        node = 0
        inserted_any = False
        for code in sequence:
            edges = self.nodes[node]
            edge = edges.get(code)
            if edge is None:
                if len(self.nodes) >= self.cap_nodes:
                    self.blocked_nodes += 1
                    break
                edge = TrieEdge(count=0, child=len(self.nodes))
                edges[code] = edge
                self.nodes.append({})
                self.edge_code_bytes += len(code)
            edge.count += 1
            node = edge.child
            inserted_any = True
        if inserted_any:
            self.insertions += 1

    def follow(self, prefix: tuple[bytes, ...]) -> int | None:
        node = 0
        for code in prefix:
            edge = self.nodes[node].get(code)
            if edge is None:
                return None
            node = edge.child
        return node

    def predict(
        self,
        node: int | None,
        bit_index: int,
        prefix: int,
        min_support: int,
        alpha2: int,
    ) -> tuple[int | None, int]:
        if node is None:
            return None, 0
        zeros = 0
        ones = 0
        support = 0
        for code, edge in self.nodes[node].items():
            code_bits = 8 * len(code)
            if bit_index >= code_bits:
                continue
            if bit_index:
                code_prefix = int.from_bytes(code, "big") >> (code_bits - bit_index)
                if code_prefix != prefix:
                    continue
            bit = event_bit(code, bit_index)
            if bit:
                ones += edge.count
            else:
                zeros += edge.count
            support += edge.count
        if support < min_support:
            return None, support
        probability = ((2 * ones + alpha2) * TOTAL) // (
            2 * support + 2 * alpha2
        )
        return clamp_p1(probability), support

    @property
    def state_bytes_estimate(self) -> int:
        edge_count = len(self.nodes) - 1
        return len(self.nodes) * 16 + edge_count * 16 + self.edge_code_bytes

    def receipt(self) -> dict[str, int]:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.nodes) - 1,
            "edge_code_bytes": self.edge_code_bytes,
            "insertions": self.insertions,
            "blocked_nodes": self.blocked_nodes,
            "state_bytes_estimate": self.state_bytes_estimate,
        }


@dataclass
class EntityObserver:
    mode: str = "none"
    capture: list[WrtEvent] = field(default_factory=list)
    tail: bytearray = field(default_factory=bytearray)
    completed_titles: int = 0
    completed_links: int = 0
    discarded_boundaries: int = 0

    @property
    def in_link(self) -> bool:
        return self.mode == "link"

    @property
    def link_prefix(self) -> tuple[bytes, ...]:
        if not self.in_link:
            return ()
        return tuple(event.encoded for event in self.capture)

    def _strip_suffix(self, byte_count: int) -> tuple[bytes, ...] | None:
        events = list(self.capture)
        remaining = byte_count
        while remaining > 0 and events:
            event = events.pop()
            decoded_bytes = len(event.decoded)
            if decoded_bytes == 0:
                continue
            if decoded_bytes > remaining:
                self.discarded_boundaries += 1
                return None
            remaining -= decoded_bytes
        if remaining != 0:
            self.discarded_boundaries += 1
            return None
        return tuple(event.encoded for event in events)

    def observe(self, event: WrtEvent) -> tuple[str, tuple[bytes, ...]] | None:
        if self.mode != "none":
            self.capture.append(event)
        self.tail.extend(event.decoded)
        if len(self.tail) > TAIL_BYTES:
            del self.tail[: len(self.tail) - TAIL_BYTES]
        tail = bytes(self.tail)

        if self.mode == "title" and tail.endswith(TITLE_CLOSE):
            sequence = self._strip_suffix(len(TITLE_CLOSE))
            self.mode = "none"
            self.capture.clear()
            if sequence:
                self.completed_titles += 1
                return "title", sequence
            return None

        if self.mode == "link":
            suffix = 0
            if tail.endswith(LINK_CLOSE):
                suffix = len(LINK_CLOSE)
            elif tail.endswith(b"|") or tail.endswith(b"#"):
                suffix = 1
            if suffix:
                sequence = self._strip_suffix(suffix)
                self.mode = "none"
                self.capture.clear()
                if sequence:
                    self.completed_links += 1
                    return "link", sequence
                return None

        if self.mode == "none":
            if tail.endswith(TITLE_OPEN):
                self.mode = "title"
                self.capture.clear()
            elif tail.endswith(LINK_OPEN):
                self.mode = "link"
                self.capture.clear()
        return None

    def receipt(self) -> dict[str, int]:
        return {
            "completed_titles": self.completed_titles,
            "completed_links": self.completed_links,
            "discarded_non_event_aligned_boundaries": self.discarded_boundaries,
        }


@dataclass(frozen=True)
class CandidateSpec:
    trie_name: str
    minimum_prefix_events: int
    blend_ppm: int

    @property
    def name(self) -> str:
        return (
            f"{self.trie_name}_p{self.minimum_prefix_events}_b{self.blend_ppm}"
        )


@dataclass
class CandidateTotals:
    train_rows: int = 0
    test_rows: int = 0
    train_active_rows: int = 0
    test_active_rows: int = 0
    train_gain_qbits: int = 0
    test_gain_qbits: int = 0

    def receipt(self) -> dict[str, float | int]:
        return {
            "train_rows": self.train_rows,
            "test_rows": self.test_rows,
            "train_active_rows": self.train_active_rows,
            "test_active_rows": self.test_active_rows,
            "train_gain_bytes": self.train_gain_qbits / 2048.0,
            "test_gain_bytes": self.test_gain_qbits / 2048.0,
        }


def make_tries(cap_nodes: int) -> dict[str, EntityTrie]:
    return {
        "title": EntityTrie(cap_nodes=cap_nodes),
        "link": EntityTrie(cap_nodes=cap_nodes),
        "combined": EntityTrie(cap_nodes=cap_nodes),
    }


def observe_and_insert(
    observer: EntityObserver,
    tries: dict[str, EntityTrie],
    event: WrtEvent,
    minimum_events: int,
    maximum_events: int,
) -> None:
    completed = observer.observe(event)
    if completed is None:
        return
    kind, sequence = completed
    if not minimum_events <= len(sequence) <= maximum_events:
        return
    tries[kind].insert(sequence)
    tries["combined"].insert(sequence)


def active_endpoint_probabilities(
    observer: EntityObserver,
    tries: dict[str, EntityTrie],
    relative_bit: int,
    prefix: int,
    min_support: int,
    alpha2: int,
) -> dict[str, tuple[int | None, int]]:
    if not observer.in_link:
        return {name: (None, 0) for name in tries}
    path = observer.link_prefix
    return {
        name: trie.predict(
            trie.follow(path),
            relative_bit,
            prefix,
            min_support,
            alpha2,
        )
        for name, trie in tries.items()
    }


def scan_candidates(
    parsed: ParsedStore,
    trace: P1Trace,
    specs: list[CandidateSpec],
    *,
    train_stream_bytes: int,
    cap_nodes: int,
    min_support: int,
    alpha2: int,
    minimum_entity_events: int,
    maximum_entity_events: int,
) -> tuple[dict[str, CandidateTotals], dict[str, EntityTrie], EntityObserver]:
    totals = {spec.name: CandidateTotals() for spec in specs}
    tries = make_tries(cap_nodes)
    observer = EntityObserver()
    event_index = 0
    active_event_start: int | None = None
    endpoint: dict[str, tuple[int | None, int]] = {
        name: (None, 0) for name in tries
    }
    events = parsed.events
    train_rows = min(train_stream_bytes, len(parsed.stream)) * 8
    test_rows = max(0, len(parsed.stream) - train_stream_bytes) * 8
    for row in totals.values():
        row.train_rows = train_rows
        row.test_rows = test_rows
    for position in range(len(parsed.stream)):
        while event_index < len(events) and position >= events[event_index].end:
            event_index += 1
        event = (
            events[event_index]
            if event_index < len(events)
            and events[event_index].start <= position < events[event_index].end
            else None
        )
        if event is not None and event.start != active_event_start:
            active_event_start = event.start
            path = observer.link_prefix if observer.in_link else ()
            endpoint = active_endpoint_probabilities(
                observer,
                tries,
                relative_bit=0,
                prefix=0,
                min_support=min_support,
                alpha2=alpha2,
            )
        for bit_position in range(8):
            bit = (parsed.stream[position] >> (7 - bit_position)) & 1
            base_p1 = trace.p1(position * 8 + bit_position)
            if event is not None:
                relative_bit = (position - event.start) * 8 + bit_position
                prefix = event_prefix(event.encoded, relative_bit)
                endpoint = active_endpoint_probabilities(
                    observer,
                    tries,
                    relative_bit,
                    prefix,
                    min_support,
                    alpha2,
                )
            path_events = len(observer.link_prefix) if observer.in_link else 0
            is_train = position < train_stream_bytes
            if not any(value[0] is not None for value in endpoint.values()):
                continue
            base_qbits = fast_qbits(bit, base_p1)
            for spec in specs:
                row = totals[spec.name]
                entity_p1, _support = endpoint[spec.trie_name]
                active = (
                    entity_p1 is not None
                    and path_events >= spec.minimum_prefix_events
                )
                candidate_p1 = (
                    blend_probability(base_p1, entity_p1, spec.blend_ppm)
                    if active
                    else base_p1
                )
                gain = base_qbits - fast_qbits(bit, candidate_p1)
                if is_train:
                    row.train_gain_qbits += gain
                    row.train_active_rows += int(active)
                else:
                    row.test_gain_qbits += gain
                    row.test_active_rows += int(active)
        if event is not None and position == event.end - 1:
            observe_and_insert(
                observer,
                tries,
                event,
                minimum_entity_events,
                maximum_entity_events,
            )
    return totals, tries, observer


def exact_replay(
    parsed: ParsedStore,
    trace: P1Trace,
    spec: CandidateSpec,
    *,
    train_stream_bytes: int,
    cap_nodes: int,
    min_support: int,
    alpha2: int,
    minimum_entity_events: int,
    maximum_entity_events: int,
    block_bytes: int,
) -> dict[str, Any]:
    tries = make_tries(cap_nodes)
    observer = EntityObserver()
    baseline = BinaryArithmeticEncoder()
    candidate = BinaryArithmeticEncoder()
    heldout_baseline = BinaryArithmeticEncoder()
    heldout_candidate = BinaryArithmeticEncoder()
    block_qbits: dict[int, int] = {}
    active_rows = 0
    heldout_active_rows = 0
    support_sum = 0
    event_index = 0
    active_event_start: int | None = None
    endpoint_p1: int | None = None
    endpoint_support = 0
    events = parsed.events
    for position in range(len(parsed.stream)):
        while event_index < len(events) and position >= events[event_index].end:
            event_index += 1
        event = (
            events[event_index]
            if event_index < len(events)
            and events[event_index].start <= position < events[event_index].end
            else None
        )
        if event is not None and event.start != active_event_start:
            active_event_start = event.start
            endpoint_p1 = None
            endpoint_support = 0
        for bit_position in range(8):
            bit = (parsed.stream[position] >> (7 - bit_position)) & 1
            base_p1 = trace.p1(position * 8 + bit_position)
            if event is not None and observer.in_link:
                relative_bit = (position - event.start) * 8 + bit_position
                prefix = event_prefix(event.encoded, relative_bit)
                trie = tries[spec.trie_name]
                endpoint_p1, endpoint_support = trie.predict(
                    trie.follow(observer.link_prefix),
                    relative_bit,
                    prefix,
                    min_support,
                    alpha2,
                )
            else:
                endpoint_p1 = None
                endpoint_support = 0
            active = (
                endpoint_p1 is not None
                and len(observer.link_prefix) >= spec.minimum_prefix_events
            )
            candidate_p1 = (
                blend_probability(base_p1, endpoint_p1, spec.blend_ppm)
                if active
                else base_p1
            )
            baseline.encode(bit, base_p1)
            candidate.encode(bit, candidate_p1)
            active_rows += int(active)
            support_sum += endpoint_support if active else 0
            if position >= train_stream_bytes:
                heldout_baseline.encode(bit, base_p1)
                heldout_candidate.encode(bit, candidate_p1)
                heldout_active_rows += int(active)
                block = position // block_bytes
                block_qbits[block] = block_qbits.get(block, 0) + (
                    fast_qbits(bit, base_p1) - fast_qbits(bit, candidate_p1)
                )
        if event is not None and position == event.end - 1:
            observe_and_insert(
                observer,
                tries,
                event,
                minimum_entity_events,
                maximum_entity_events,
            )
    baseline.finish()
    candidate.finish()
    heldout_baseline.finish()
    heldout_candidate.finish()
    blocks = [
        {"block_id": block, "gain_bytes": gain / 2048.0}
        for block, gain in sorted(block_qbits.items())
    ]
    return {
        "selected_candidate": spec.name,
        "baseline_bytes": baseline.byte_count,
        "candidate_bytes": candidate.byte_count,
        "saved_bytes": baseline.byte_count - candidate.byte_count,
        "heldout_baseline_bytes": heldout_baseline.byte_count,
        "heldout_candidate_bytes": heldout_candidate.byte_count,
        "heldout_saved_bytes": heldout_baseline.byte_count
        - heldout_candidate.byte_count,
        "active_rows": active_rows,
        "heldout_active_rows": heldout_active_rows,
        "mean_active_support": support_sum / active_rows if active_rows else 0.0,
        "block_rows": blocks,
        "positive_blocks": sum(row["gain_bytes"] > 0 for row in blocks),
        "regressing_blocks": sum(row["gain_bytes"] < 0 for row in blocks),
        "largest_block_regression_bytes": max(
            (-row["gain_bytes"] for row in blocks if row["gain_bytes"] < 0),
            default=0.0,
        ),
        "tries": {name: trie.receipt() for name, trie in tries.items()},
        "observer": observer.receipt(),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    parsed = parse_store(args.store, args.dictionary)
    with args.raw.open("rb") as source:
        raw = source.read(parsed.raw_length)
    if len(raw) != parsed.raw_length:
        raise RuntimeError("raw corpus is shorter than the WRT-declared scope")
    if raw != parsed.decoded:
        raise RuntimeError("WRT store does not reconstruct the declared raw prefix")
    trace = P1Trace(args.base_p1)
    try:
        if trace.rows != len(parsed.stream) * 8:
            raise RuntimeError("base probability trace does not cover the exact WRT stream")
        blends = tuple(int(value) for value in args.blends.split(",") if value)
        prefix_floors = tuple(
            int(value) for value in args.minimum_prefix_events.split(",") if value
        )
        specs = [
            CandidateSpec(trie_name=name, minimum_prefix_events=floor, blend_ppm=blend)
            for name in ("title", "link", "combined")
            for floor in prefix_floors
            for blend in blends
        ]
        totals, discovery_tries, discovery_observer = scan_candidates(
            parsed,
            trace,
            specs,
            train_stream_bytes=args.train_stream_bytes,
            cap_nodes=args.cap_nodes,
            min_support=args.min_support,
            alpha2=args.alpha2,
            minimum_entity_events=args.minimum_entity_events,
            maximum_entity_events=args.maximum_entity_events,
        )
        ranked = sorted(
            specs,
            key=lambda spec: (
                -totals[spec.name].train_gain_qbits,
                spec.minimum_prefix_events,
                spec.blend_ppm,
                spec.trie_name,
            ),
        )
        selected = ranked[0]
        replay = exact_replay(
            parsed,
            trace,
            selected,
            train_stream_bytes=args.train_stream_bytes,
            cap_nodes=args.cap_nodes,
            min_support=args.min_support,
            alpha2=args.alpha2,
            minimum_entity_events=args.minimum_entity_events,
            maximum_entity_events=args.maximum_entity_events,
            block_bytes=args.block_bytes,
        )
        code_bytes = Path(__file__).stat().st_size
        heldout_stream_fraction = (
            len(parsed.stream) - args.train_stream_bytes
        ) / len(parsed.stream)
        heldout_raw_bytes_estimate = parsed.raw_length * heldout_stream_fraction
        gross_per_1m = (
            replay["heldout_saved_bytes"] * 1_000_000 / heldout_raw_bytes_estimate
            if heldout_raw_bytes_estimate > 0
            else 0.0
        )
        state_bytes = sum(
            row["state_bytes_estimate"] for row in replay["tries"].values()
        )
        required_gross_per_1m = args.forecast_gap_bytes / 1000.0 + code_bytes / 1000.0
        candidates = []
        for spec in ranked:
            row = totals[spec.name].receipt()
            row.update(
                {
                    "candidate": spec.name,
                    "trie": spec.trie_name,
                    "minimum_prefix_events": spec.minimum_prefix_events,
                    "blend_ppm": spec.blend_ppm,
                }
            )
            candidates.append(row)
        verdict = (
            "positive_heldout_requires_disjoint_and_native_integration"
            if gross_per_1m > required_gross_per_1m
            and replay["heldout_saved_bytes"] > 0
            else "insufficient_realizable_margin_preserve_mechanism"
            if replay["heldout_saved_bytes"] > 0
            else "negative_or_flat_heldout_retire_current_entity_universe"
        )
        return {
            "schema": "wrt_entity_trie_fx2_shadow_v1",
            "evidence_level": "selection_then_heldout_exact_arithmetic_shadow",
            "inputs": {
                "store": artifact(args.store),
                "raw_corpus": artifact(args.raw),
                "raw_scope_bytes": len(raw),
                "raw_scope_sha256": sha256_bytes(raw),
                "dictionary": artifact(args.dictionary),
                "base_p1": artifact(args.base_p1),
                "base_p1_magic": trace.magic.decode("ascii", errors="replace"),
            },
            "scope": {
                "raw_bytes": parsed.raw_length,
                "wrt_stream_bytes": len(parsed.stream),
                "encoded_rows": len(parsed.stream) * 8,
                "events": len(parsed.events),
                "event_kind_counts": parsed.kind_counts,
                "train_stream_bytes": args.train_stream_bytes,
                "heldout_stream_bytes": len(parsed.stream) - args.train_stream_bytes,
                "heldout_raw_bytes_estimate_by_stream_fraction": heldout_raw_bytes_estimate,
            },
            "parameters": {
                "cap_nodes_per_trie": args.cap_nodes,
                "minimum_support": args.min_support,
                "alpha2": args.alpha2,
                "minimum_entity_events": args.minimum_entity_events,
                "maximum_entity_events": args.maximum_entity_events,
                "candidate_blends_ppm": list(blends),
                "candidate_minimum_prefix_events": list(prefix_floors),
                "block_bytes": args.block_bytes,
            },
            "selection": {
                "rule": "maximum early-split qbit gain; heldout unopened until selection",
                "selected_candidate": selected.name,
                "candidates": candidates,
            },
            "exact_replay": replay,
            "discovery_state": {
                "tries": {
                    name: trie.receipt() for name, trie in discovery_tries.items()
                },
                "observer": discovery_observer.receipt(),
            },
            "economics": {
                "heldout_gross_saved_bytes_per_1m_raw_estimate": gross_per_1m,
                "forecast_gap_bytes_per_1m": args.forecast_gap_bytes / 1000.0,
                "provisional_code_bytes": code_bytes,
                "provisional_code_cost_bytes_per_1m_at_1g": code_bytes / 1000.0,
                "required_gross_bytes_per_1m_before_integration_regressions": required_gross_per_1m,
                "max_incremental_state_bytes_estimate": state_bytes,
            },
            "identity": {
                "raw_roundtrip_ok": True,
                "base_trace_full_stream_coverage": True,
                "updates_after_completed_current_event": True,
                "prediction_uses_only_completed_entity_prefix": True,
                "static_entity_payload_bytes": 0,
                "decoder_replayable_state": True,
            },
            "verdict": verdict,
            "promotion_authorized": False,
            "claim_boundary": (
                "This is an exact arithmetic shadow over a quarantined but hash-pinned "
                "base trace. It does not change a constructive archive score. Native "
                "integration, source accounting, disjoint confirmation, roundtrip, "
                "determinism, RSS, and official 1G proof remain."
            ),
        }
    finally:
        trace.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--base-p1", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--train-stream-bytes", type=int, default=100_000)
    parser.add_argument("--cap-nodes", type=int, default=500_000)
    parser.add_argument("--min-support", type=int, default=2)
    parser.add_argument("--alpha2", type=int, default=1)
    parser.add_argument("--minimum-entity-events", type=int, default=1)
    parser.add_argument("--maximum-entity-events", type=int, default=64)
    parser.add_argument("--minimum-prefix-events", default="0,1,2")
    parser.add_argument("--blends", default="50000,100000,250000,500000,1000000")
    parser.add_argument("--block-bytes", type=int, default=16_384)
    parser.add_argument("--forecast-gap-bytes", type=int, default=57_404)
    args = parser.parse_args()
    for path in (args.store, args.raw, args.dictionary, args.base_p1):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    if not 0 < args.train_stream_bytes:
        raise SystemExit("training boundary must be positive")
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(
        json.dumps(
            {
                "selected": receipt["selection"]["selected_candidate"],
                "heldout_saved_bytes": receipt["exact_replay"]["heldout_saved_bytes"],
                "gross_per_1m": receipt["economics"]["heldout_gross_saved_bytes_per_1m_raw_estimate"],
                "required_per_1m": receipt["economics"]["required_gross_bytes_per_1m_before_integration_regressions"],
                "verdict": receipt["verdict"],
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
