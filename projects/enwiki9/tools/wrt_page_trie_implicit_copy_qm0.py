#!/usr/bin/env python3
"""Paid-qbit gate for decoder-derived typed WRT event-run copies."""

from __future__ import annotations

import argparse
from array import array
from collections import deque
from dataclasses import dataclass, field
import hashlib
import json
import lzma
import math
from pathlib import Path
import struct
from typing import Iterable

import numpy as np

import wrt_exact


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "wrt_page_trie_implicit_copy_qm0_v1"
SUFFIX_LENGTHS = (8, 4, 2)
COPY_LENGTHS = (1, 2, 4, 8, 16, 32)
MAX_POSITIONS_PER_KEY = 8
INDEX_KEY_CAP = 250_000
MASK64 = (1 << 64) - 1
HASH_BASE = 0x9E3779B185EBCA87
P1_MAGIC = b"CMX21P1\0"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def fnv64(data: bytes) -> int:
    value = 1469598103934665603
    for byte in data:
        value ^= byte
        value = value * 1099511628211 & MASK64
    return value


def mix64(value: int) -> int:
    value ^= value >> 30
    value = value * 0xBF58476D1CE4E5B9 & MASK64
    value ^= value >> 27
    value = value * 0x94D049BB133111EB & MASK64
    return value ^ (value >> 31)


def qbits(bit: int, p1: int) -> int:
    correct = p1 if bit else 65_536 - p1
    return round(-math.log2(correct / 65_536.0) * 256.0)


@dataclass
class WikiState:
    field_id: int = 0
    link_depth: int = 0
    template_depth: int = 0
    ref_depth: int = 0
    url_mode: bool = False
    page: int = -1
    page_start_event: int = 0
    tail: bytearray = field(default_factory=bytearray)

    def observe(self, decoded: bytes, event_index: int) -> None:
        for byte in decoded:
            self.tail.append(byte)
            if len(self.tail) > 192:
                del self.tail[:64]
            lower = bytes(self.tail).lower()
            if lower.endswith(b"<page>"):
                self.page += 1
                self.page_start_event = event_index
            elif lower.endswith(b"<title>"):
                self.field_id = 1
            elif lower.endswith(b"</title>"):
                self.field_id = 0
            elif lower.endswith(b"<timestamp>"):
                self.field_id = 2
            elif lower.endswith(b"</timestamp>"):
                self.field_id = 0
            elif lower.endswith(b'<text xml:space="preserve">'):
                self.field_id = 3
            elif lower.endswith(b"</text>"):
                self.field_id = 0
                self.link_depth = 0
                self.template_depth = 0
                self.ref_depth = 0
                self.url_mode = False
            if lower.endswith(b"[["):
                self.link_depth = min(7, self.link_depth + 1)
            elif lower.endswith(b"]]"):
                self.link_depth = max(0, self.link_depth - 1)
            elif lower.endswith(b"{{"):
                self.template_depth = min(7, self.template_depth + 1)
            elif lower.endswith(b"}}"):
                self.template_depth = max(0, self.template_depth - 1)
            elif lower.endswith(b"<ref"):
                self.ref_depth = min(3, self.ref_depth + 1)
            elif lower.endswith(b"</ref>"):
                self.ref_depth = max(0, self.ref_depth - 1)
            if lower.endswith(b"http://") or lower.endswith(b"https://"):
                self.url_mode = True
            elif self.url_mode and byte in (9, 10, 13, 32, 34, 39, 60, 62, 93, 125):
                self.url_mode = False

    def regime(self) -> int:
        if self.field_id == 1:
            return 1
        if self.ref_depth:
            return 2
        if self.url_mode:
            return 3
        if self.template_depth:
            return 4
        if self.link_depth:
            return 5
        if self.field_id == 2:
            return 6
        if self.field_id == 3:
            return 7
        return 0


@dataclass
class BitCounts:
    zero: int
    one: int

    def probability(self) -> int:
        return max(1, min(65_535, self.one * 65_536 // (self.zero + self.one)))

    def observe(self, bit: int) -> None:
        if bit:
            self.one += 1
        else:
            self.zero += 1
        if self.zero + self.one >= 32_768:
            self.zero = max(1, (self.zero + 1) // 2)
            self.one = max(1, (self.one + 1) // 2)


@dataclass
class AdaptiveSymbols:
    selector: dict[tuple[int, int, int], BitCounts] = field(default_factory=dict)
    length: dict[tuple[int, int, int, int, int], BitCounts] = field(default_factory=dict)

    def selector_cost(self, context: tuple[int, int, int], take: bool) -> int:
        counts = self.selector.setdefault(context, BitCounts(15, 1))
        bit = int(take)
        cost = qbits(bit, counts.probability())
        counts.observe(bit)
        return cost

    def length_cost(self, context: tuple[int, int, int], length_index: int) -> int:
        cost = 0
        prefix = 0
        for position in range(3):
            bit = (length_index >> (2 - position)) & 1
            key = (*context, position, prefix)
            counts = self.length.setdefault(key, BitCounts(1, 1))
            cost += qbits(bit, counts.probability())
            counts.observe(bit)
            prefix = (prefix << 1) | bit
        return cost


class SuffixIndex:
    def __init__(self) -> None:
        self.positions: dict[tuple[int, int, int], deque[int]] = {}
        self.order: deque[tuple[int, int, int]] = deque()

    def add(self, key: tuple[int, int, int], end: int) -> None:
        positions = self.positions.get(key)
        if positions is None:
            while len(self.positions) >= INDEX_KEY_CAP:
                old = self.order.popleft()
                if old in self.positions:
                    del self.positions[old]
                    break
            positions = deque(maxlen=MAX_POSITIONS_PER_KEY)
            self.positions[key] = positions
            self.order.append(key)
        positions.append(end)


@dataclass
class Arm:
    name: str
    index: SuffixIndex = field(default_factory=SuffixIndex)
    adaptive: AdaptiveSymbols = field(default_factory=AdaptiveSymbols)
    next_schedule: int = 1
    opportunities: int = 0
    takes: int = 0
    copied_events: int = 0
    copied_stream_bytes: int = 0
    displaced_qbits: int = 0
    selector_qbits: int = 0
    length_qbits: int = 0
    gain_qbits: int = 0
    thirds: list[int] = field(default_factory=lambda: [0, 0, 0])
    suffix_opportunities: dict[int, int] = field(default_factory=dict)


def load_parent_qbits(parsed: wrt_exact.ParsedStore, path: Path) -> np.ndarray:
    rows = len(parsed.stream) * 8
    with path.open("rb") as source:
        header = source.read(16)
    if len(header) != 16 or header[:8] != P1_MAGIC:
        raise ValueError("invalid parent P1 trace")
    if struct.unpack_from("<Q", header, 8)[0] != rows:
        raise ValueError("parent P1 row count differs from WRT stream")
    if path.stat().st_size != 16 + 2 * rows:
        raise ValueError("parent P1 trace length differs from declared rows")
    p1 = np.memmap(path, mode="r", dtype="<u2", offset=16, shape=(rows,))
    truth = np.unpackbits(np.frombuffer(parsed.stream, dtype=np.uint8), bitorder="big")
    correct = np.where(truth == 1, p1.astype(np.uint32), 65_536 - p1.astype(np.uint32))
    if np.any(correct == 0):
        raise ValueError("parent assigns zero probability to truth")
    bit_qbits = np.rint(-np.log2(correct / 65_536.0) * 256.0).astype(np.int32)
    byte_qbits = bit_qbits.reshape((-1, 8)).sum(axis=1, dtype=np.int64)
    prefix = np.empty(len(byte_qbits) + 1, dtype=np.int64)
    prefix[0] = 0
    np.cumsum(byte_qbits, out=prefix[1:])
    return np.fromiter(
        (prefix[event.end] - prefix[event.start] for event in parsed.events),
        dtype=np.int64,
        count=len(parsed.events),
    )


def boundaries(parsed: wrt_exact.ParsedStore) -> tuple[bytearray, array, array, array]:
    regimes = bytearray()
    pages = array("I")
    page_starts = array("I")
    symbols = array("Q")
    wiki = WikiState()
    for index, event in enumerate(parsed.events):
        wiki.observe(event.decoded, index)
        regimes.append(wiki.regime())
        pages.append(max(0, wiki.page))
        page_starts.append(wiki.page_start_event)
        symbols.append(fnv64(event.encoded))
    return regimes, pages, page_starts, symbols


def prefix_hashes(symbols: array) -> tuple[array, dict[int, int]]:
    prefix = array("Q", [0])
    value = 0
    for symbol in symbols:
        value = (value * HASH_BASE + int(symbol) + 1) & MASK64
        prefix.append(value)
    powers = {0: 1}
    for length in range(1, max(SUFFIX_LENGTHS) + 1):
        powers[length] = powers[length - 1] * HASH_BASE & MASK64
    return prefix, powers


def suffix_hash(prefix: array, powers: dict[int, int], end: int, length: int) -> int:
    start = end + 1 - length
    return (int(prefix[end + 1]) - int(prefix[start]) * powers[length]) & MASK64


def exact_suffix(events: tuple[wrt_exact.WrtEvent, ...], a: int, b: int, length: int) -> bool:
    for offset in range(length):
        if events[a - offset].encoded != events[b - offset].encoded:
            return False
    return True


def arm_label(name: str, boundary: int, regime: int, page: int) -> int:
    if name == "C0":
        return 0
    if name == "T0":
        return regime
    return mix64((boundary + 1) ^ ((page + 1) * HASH_BASE)) & 7


def opportunity(
    arm: Arm,
    events: tuple[wrt_exact.WrtEvent, ...],
    prefix: array,
    powers: dict[int, int],
    regimes: bytearray,
    pages: array,
    page_starts: array,
    target: int,
) -> tuple[int, int, int, int] | None:
    end = target - 1
    label = arm_label(arm.name, end, regimes[end], pages[end])
    available_suffix = end - int(page_starts[end]) + 1
    for length in SUFFIX_LENGTHS:
        if length > available_suffix:
            continue
        key = (label, length, suffix_hash(prefix, powers, end, length))
        positions = arm.index.positions.get(key)
        if not positions:
            continue
        matches: list[int] = []
        next_symbol: bytes | None = None
        collision = False
        for source_end in reversed(positions):
            if source_end >= end or source_end + 1 > end:
                continue
            if not exact_suffix(events, end, source_end, length):
                continue
            symbol = events[source_end + 1].encoded
            if next_symbol is None:
                next_symbol = symbol
            elif symbol != next_symbol:
                collision = True
                break
            matches.append(source_end)
        if collision or not matches:
            continue
        return matches[0] + 1, length, len(matches), label
    return None


def available_match(
    events: tuple[wrt_exact.WrtEvent, ...], target: int, source: int
) -> int:
    limit = min(32, len(events) - target, target - source)
    length = 0
    while length < limit and events[target + length].encoded == events[source + length].encoded:
        length += 1
    return length


def add_boundary(
    arm: Arm,
    prefix: array,
    powers: dict[int, int],
    regimes: bytearray,
    pages: array,
    page_starts: array,
    end: int,
) -> None:
    label = arm_label(arm.name, end, regimes[end], pages[end])
    available = end - int(page_starts[end]) + 1
    for length in SUFFIX_LENGTHS:
        if length <= available:
            arm.index.add(
                (label, length, suffix_hash(prefix, powers, end, length)), end
            )


def scan_arm_event(
    arm: Arm,
    events: tuple[wrt_exact.WrtEvent, ...],
    event_qbits: np.ndarray,
    raw_starts: array,
    raw_bytes: int,
    prefix: array,
    powers: dict[int, int],
    regimes: bytearray,
    pages: array,
    page_starts: array,
    target: int,
) -> None:
    if target < arm.next_schedule or target == 0:
        return
    found = opportunity(
        arm, events, prefix, powers, regimes, pages, page_starts, target
    )
    if found is None:
        return
    source, suffix_length, support, label = found
    arm.opportunities += 1
    arm.suffix_opportunities[suffix_length] = arm.suffix_opportunities.get(suffix_length, 0) + 1
    match = available_match(events, target, source)
    take_length = max((length for length in COPY_LENGTHS if length <= match), default=0)
    context = (label, suffix_length, min(7, support.bit_length() - 1))
    selector_cost = arm.adaptive.selector_cost(context, take_length > 0)
    arm.selector_qbits += selector_cost
    delta = -selector_cost
    third = min(2, int(raw_starts[target]) * 3 // raw_bytes)
    arm.thirds[third] -= selector_cost
    if take_length:
        length_index = COPY_LENGTHS.index(take_length)
        length_cost = arm.adaptive.length_cost(context, length_index)
        displaced = int(event_qbits[target : target + take_length].sum())
        arm.length_qbits += length_cost
        arm.displaced_qbits += displaced
        arm.takes += 1
        arm.copied_events += take_length
        arm.copied_stream_bytes += sum(
            len(event.encoded) for event in events[target : target + take_length]
        )
        delta += displaced - length_cost
        arm.thirds[third] += displaced - length_cost
        arm.next_schedule = target + take_length
    else:
        arm.next_schedule = target + 1
    arm.gain_qbits += delta


def arm_receipt(arm: Arm, source_bytes: int) -> dict[str, object]:
    gross = arm.gain_qbits / 2048.0
    return {
        "opportunities": arm.opportunities,
        "takes": arm.takes,
        "copied_events": arm.copied_events,
        "copied_stream_bytes": arm.copied_stream_bytes,
        "displaced_bytes": arm.displaced_qbits / 2048.0,
        "selector_bytes": arm.selector_qbits / 2048.0,
        "length_bytes": arm.length_qbits / 2048.0,
        "gross_gain_bytes": gross,
        "net_after_common_source_bytes": gross - source_bytes,
        "chronological_gain_bytes": [value / 2048.0 for value in arm.thirds],
        "suffix_opportunities": {
            str(key): value for key, value in sorted(arm.suffix_opportunities.items())
        },
        "index_keys_final": len(arm.index.positions),
        "selector_contexts": len(arm.adaptive.selector),
        "length_contexts": len(arm.adaptive.length),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT / "data/enwik9_10000000.bin")
    parser.add_argument(
        "--store", type=Path,
        default=Path("/home/x/enwiki9-nonproof/results/fx2_order_original_10m.store"),
    )
    parser.add_argument(
        "--dictionary", type=Path,
        default=ROOT / "external/fx2-cmix/dictionary/english.dic",
    )
    parser.add_argument(
        "--parent-p1", type=Path,
        default=ROOT / "results/fractal2_endpoint428_trace_10m_v1/endpoint428.p1",
    )
    parser.add_argument(
        "--parent-archive", type=Path,
        default=ROOT / "results/fractal2_endpoint428_trace_10m_v1/archive.bin",
    )
    parser.add_argument(
        "--parent-receipt", type=Path,
        default=ROOT / "results/fractal2_endpoint428_trace_10m_v1/decision.json",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=ROOT / f"results/{CANDIDATE_ID}",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if (args.output_dir / "decision.json").exists():
        raise FileExistsError(f"measured decision already exists: {args.output_dir}")
    parsed = wrt_exact.parse_store(args.store, args.dictionary)
    raw = args.raw.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("WRT store does not reconstruct canonical raw input")
    parent_receipt = json.loads(args.parent_receipt.read_text())
    if not parent_receipt["proof"]["archive_matches_endpoint428_10m_receipt"]:
        raise ValueError("parent archive receipt is not identity-bound")
    if sha256_file(args.parent_archive) != parent_receipt["artifacts"]["archive"]["sha256"]:
        raise ValueError("parent archive differs from receipt")
    if sha256_file(args.parent_p1) != parent_receipt["artifacts"]["p1_trace"]["sha256"]:
        raise ValueError("parent P1 differs from receipt")

    event_qbits = load_parent_qbits(parsed, args.parent_p1)
    regimes, pages, page_starts, symbols = boundaries(parsed)
    prefix, powers = prefix_hashes(symbols)
    raw_starts = array("I")
    raw_cursor = 0
    for event in parsed.events:
        raw_starts.append(raw_cursor)
        raw_cursor += len(event.decoded)
    if raw_cursor != len(raw):
        raise ValueError("event/raw coordinates do not cover input")

    source_paths = [Path(__file__), Path(wrt_exact.__file__)]
    source_blob = b"".join(
        path.name.encode("ascii") + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    (args.output_dir / "source_package.lzma").write_bytes(source_package)

    arms = {name: Arm(name) for name in ("C0", "S0", "T0")}
    for target in range(len(parsed.events)):
        for arm in arms.values():
            scan_arm_event(
                arm, parsed.events, event_qbits, raw_starts, len(raw), prefix,
                powers, regimes, pages, page_starts, target,
            )
        for arm in arms.values():
            add_boundary(arm, prefix, powers, regimes, pages, page_starts, target)

    rows = {name: arm_receipt(arm, len(source_package)) for name, arm in arms.items()}
    t0_net = float(rows["T0"]["net_after_common_source_bytes"])
    margins = {
        name: float(rows["T0"]["gross_gain_bytes"]) - float(rows[name]["gross_gain_bytes"])
        for name in ("C0", "S0")
    }
    failed: list[str] = []
    if t0_net < 50_000:
        failed.append("T0_net_below_50000_bytes")
    if any(value <= 0 for value in rows["T0"]["chronological_gain_bytes"]):
        failed.append("T0_chronological_third_nonpositive")
    for name, value in margins.items():
        if value < 10_000:
            failed.append(f"T0_margin_over_{name}_below_10000_bytes")
    if len(source_package) > 20_000:
        failed.append("source_package_above_20000_bytes")

    decision = {
        "schema": "enwiki9_wrt_page_trie_implicit_copy_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "paid_trace_qbit_screen_zero_credit",
        "inputs": {
            "raw": artifact(args.raw),
            "wrt_store": artifact(args.store),
            "dictionary": artifact(args.dictionary),
            "parent_p1": artifact(args.parent_p1),
            "parent_archive": artifact(args.parent_archive),
            "parent_receipt": artifact(args.parent_receipt),
        },
        "contract": {
            "suffix_lengths": list(SUFFIX_LENGTHS),
            "copy_lengths": list(COPY_LENGTHS),
            "positions_per_key": MAX_POSITIONS_PER_KEY,
            "index_key_cap_per_arm": INDEX_KEY_CAP,
            "source_rule": "unique next exact WRT event across bounded exact suffix matches; most recent source tie break",
            "selector_rule": "adaptive paid take bit with 15:1 literal prior",
            "length_rule": "three adaptive paid bits for power-of-two copy length",
            "source_identity_transmitted": False,
            "opportunity_position_transmitted": False,
        },
        "population": {
            "raw_bytes": len(raw),
            "wrt_stream_bytes": len(parsed.stream),
            "wrt_events": len(parsed.events),
            "pages": max(pages) + 1 if pages else 0,
            "regime_counts": {
                str(regime): regimes.count(regime) for regime in sorted(set(regimes))
            },
        },
        "arms": rows,
        "T0_control_margins_bytes": margins,
        "accounting": {
            "source_package_bytes": len(source_package),
            "source_package_sha256": hashlib.sha256(source_package).hexdigest(),
            "all_selector_and_length_symbols_charged": True,
            "score_credit_bytes": 0,
        },
        "proof": {
            "wrt_store_inverse_exact": True,
            "raw_inverse_exact": True,
            "parent_archive_and_p1_receipt_bound": True,
            "only_completed_events_enter_source_index": True,
            "source_and_schedule_decoder_derived": True,
            "hash_matches_verified_by_exact_event_sequences": True,
        },
        "failed_conditions": failed,
        "verdict": (
            "authorize_exact_mixed_arithmetic_replay" if not failed
            else "retire_page_trie_implicit_copy_realization"
        ),
        "claim_boundary": (
            "All macro symbols and the compressed research implementation are paid, "
            "but this receipt uses parent-qbit accounting rather than an exact mixed "
            "arithmetic payload. It earns zero score credit. Only a gate pass may "
            "authorize exact deterministic payload/decode work."
        ),
    }
    output = args.output_dir / "decision.json"
    output.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "candidate_id": CANDIDATE_ID,
        "T0": rows["T0"],
        "margins_bytes": margins,
        "failed_conditions": failed,
        "verdict": decision["verdict"],
        "output": str(output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
