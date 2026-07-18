#!/usr/bin/env python3
"""Score a causal WRT title-token endpoint against compact FX2 probabilities.

The compact trace contains only FX2's pre-bit probability and the true bit.
This tool reconstructs the exact WRT byte stream, tokenizes it with the same
dictionary code contract, rebuilds current and previous page titles, and
scores title-token predictions without rewriting the stream.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Iterable, Iterator, Sequence


TRACE_MAGIC = b"FX2PT01\n"
TRACE_RECORD = struct.Struct("<HB")
TOTAL = 1 << 16
MAX_CODE = (1 << 32) - 1
TITLE_CONTEXTS = (1, 2, 3, 4, 6, 8)
BLENDS_PPM = (10_000, 25_000, 50_000, 100_000, 200_000)
EXPERT_ONE = 63_488
EXPERT_ZERO = TOTAL - EXPERT_ONE
BLOCK_BYTES = 65_536


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def char_swap(value: int) -> int:
    if ord("{") <= value < 127:
        value += ord("P") - ord("{")
    elif ord("P") <= value < ord("T"):
        value -= ord("P") - ord("{")
    elif ord(":") <= value <= ord("?") or ord("J") <= value <= ord("O"):
        value ^= 0x70
    if value in (ord("X"), ord("`")):
        value ^= ord("X") ^ ord("`")
    return value


def load_dictionary(path: Path) -> list[bytes]:
    words: list[bytes] = []
    word = bytearray()
    for value in path.read_bytes():
        if ord("a") <= value <= ord("z"):
            word.append(value)
        elif word:
            words.append(bytes(word))
            word.clear()
    if word:
        words.append(bytes(word))
    return words


@dataclass(frozen=True)
class TraceByte:
    value: int
    probabilities: tuple[int, ...]
    bits: tuple[int, ...]


def iter_trace_bytes(path: Path) -> Iterator[TraceByte]:
    with path.open("rb") as handle:
        if handle.read(len(TRACE_MAGIC)) != TRACE_MAGIC:
            raise ValueError("invalid compact FX2 trace header")
        while True:
            chunk = handle.read(8 * TRACE_RECORD.size)
            if not chunk:
                break
            if len(chunk) != 8 * TRACE_RECORD.size:
                raise ValueError("compact trace ends inside a WRT byte")
            probabilities: list[int] = []
            bits: list[int] = []
            value = 0
            for p1, bit in TRACE_RECORD.iter_unpack(chunk):
                if not 1 <= p1 < TOTAL or bit not in (0, 1):
                    raise ValueError("invalid compact trace record")
                probabilities.append(p1)
                bits.append(bit)
                value = (value << 1) | bit
            yield TraceByte(value, tuple(probabilities), tuple(bits))


@dataclass(frozen=True)
class WrtUnit:
    signature: int
    encoded: bytes
    decoded: bytes


class WrtTokenizer:
    def __init__(self, dictionary: list[bytes]) -> None:
        self.dictionary = dictionary
        self.escape = False
        self.upper = False
        self.capital = False
        self.pending_encoded = bytearray()
        self.pending_logical = bytearray()

    @staticmethod
    def token_id(values: bytes) -> int:
        if len(values) == 1:
            return values[0] - 0x80
        if len(values) == 2:
            return 80 + (values[0] - 0xD0) * 80 + (values[1] - 0x80)
        return 3920 + (values[0] - 0xF0) * 32 * 80 + (values[1] - 0xD0) * 80 + (values[2] - 0x80)

    def _apply_case(self, data: bytes) -> bytes:
        output = bytearray(data)
        for index, value in enumerate(output):
            if (index == 0 and self.capital) or self.upper:
                if ord("a") <= value <= ord("z"):
                    output[index] = value - 32
        self.capital = False
        return bytes(output)

    def feed(self, encoded: int) -> WrtUnit | None:
        logical = char_swap(encoded)
        if self.escape:
            self.escape = False
            self.upper = False
            raw = bytes(self.pending_encoded) + bytes((encoded,))
            self.pending_encoded.clear()
            return WrtUnit(0x30000 + logical, raw, bytes((logical,)))

        if self.pending_logical:
            self.pending_encoded.append(encoded)
            self.pending_logical.append(logical)
            first = self.pending_logical[0]
            expected = 1 if first <= 0xCF else (2 if first <= 0xEF else 3)
            if len(self.pending_logical) < expected:
                return None
            token_bytes = bytes(self.pending_logical)
            token_id = self.token_id(token_bytes)
            word = self.dictionary[token_id] if token_id < len(self.dictionary) else b""
            unit = WrtUnit(token_id, bytes(self.pending_encoded), self._apply_case(word))
            self.pending_encoded.clear()
            self.pending_logical.clear()
            return unit

        if logical == 0x0C:
            self.escape = True
            self.pending_encoded.append(encoded)
            return None
        if logical == 0x07:
            self.upper = True
            return WrtUnit(0x20000 + logical, bytes((encoded,)), b"")
        if logical == 0x40:
            self.capital = True
            return WrtUnit(0x20000 + logical, bytes((encoded,)), b"")
        if logical == 0x06:
            self.upper = False
            return WrtUnit(0x20000 + logical, bytes((encoded,)), b"")
        if logical >= 0x80:
            self.pending_encoded.append(encoded)
            self.pending_logical.append(logical)
            first = self.pending_logical[0]
            expected = 1 if first <= 0xCF else (2 if first <= 0xEF else 3)
            if expected > 1:
                return None
            token_id = self.token_id(bytes(self.pending_logical))
            word = self.dictionary[token_id] if token_id < len(self.dictionary) else b""
            unit = WrtUnit(token_id, bytes(self.pending_encoded), self._apply_case(word))
            self.pending_encoded.clear()
            self.pending_logical.clear()
            return unit

        literal = logical
        if (self.capital or self.upper) and ord("a") <= literal <= ord("z"):
            literal -= 32
        if not (ord("a") <= literal <= ord("z") or ord("A") <= literal <= ord("Z")):
            self.upper = False
        self.capital = False
        return WrtUnit(0x10000 + logical, bytes((encoded,)), bytes((literal,)))


class WikiState:
    def __init__(self) -> None:
        self.in_tag = False
        self.tag_closing = False
        self.tag_name_done = False
        self.tag = bytearray()
        self.previous = 0
        self.page_mode = False
        self.title_mode = False
        self.prose_mode = False
        self.page_boundary = 0

    def _finish_tag(self, self_closing: bool) -> None:
        tag = bytes(self.tag).lower()
        closing = self.tag_closing
        if tag == b"page":
            self.page_boundary = 2 if closing else 1
            self.page_mode = not closing
        elif tag == b"title":
            self.title_mode = not closing
        elif tag == b"text":
            self.prose_mode = not closing
        self.tag.clear()
        self.tag_closing = False
        self.tag_name_done = False

    def feed(self, data: bytes) -> None:
        self.page_boundary = 0
        for value in data:
            if value == ord("<"):
                self.in_tag = True
                self.tag.clear()
                self.tag_closing = False
                self.tag_name_done = False
            elif self.in_tag:
                if not self.tag and not self.tag_name_done and value == ord("/"):
                    self.tag_closing = True
                elif not self.tag_name_done and (
                    ord("A") <= value <= ord("Z")
                    or ord("a") <= value <= ord("z")
                    or ord("0") <= value <= ord("9")
                ):
                    if len(self.tag) < 24:
                        self.tag.append(value)
                elif self.tag and value != ord("/"):
                    self.tag_name_done = True
                if value == ord(">"):
                    self._finish_tag(self.previous == ord("/"))
                    self.in_tag = False
            self.previous = value


@dataclass(frozen=True)
class Rule:
    encoded: bytes
    best_count: int
    total: int


@dataclass(frozen=True)
class Endpoint:
    expected_byte: int
    match_tokens: int
    best_count: int
    total: int


class TitleTokenModel:
    def __init__(self, max_context: int = max(TITLE_CONTEXTS)) -> None:
        self.max_context = max_context
        self.rules: dict[tuple[int, ...], Rule] = {}
        self.recent: list[int] = []
        self.expected = b""
        self.expected_index = 0
        self.expected_rule: Rule | None = None
        self.expected_match = 0

    def build(self, units: Sequence[WrtUnit]) -> None:
        histograms: dict[tuple[int, ...], Counter[bytes]] = {}
        signatures = [unit.signature for unit in units]
        for next_index in range(1, len(units)):
            for length in range(1, min(self.max_context, next_index) + 1):
                context = tuple(signatures[next_index - length : next_index])
                histograms.setdefault(context, Counter())[units[next_index].encoded] += 1
        self.rules.clear()
        for context, counts in histograms.items():
            encoded, best_count = min(
                counts.items(), key=lambda item: (-item[1], item[0])
            )
            self.rules[context] = Rule(encoded, best_count, sum(counts.values()))
        self.reset_recent()

    def reset_recent(self) -> None:
        self.recent.clear()
        self.expected = b""
        self.expected_index = 0
        self.expected_rule = None
        self.expected_match = 0

    def endpoint(self) -> Endpoint | None:
        if self.expected_rule is None or self.expected_index >= len(self.expected):
            return None
        return Endpoint(
            self.expected[self.expected_index],
            self.expected_match,
            self.expected_rule.best_count,
            self.expected_rule.total,
        )

    def observe_stream_byte(self, value: int) -> None:
        if self.expected_rule is None or self.expected_index >= len(self.expected):
            return
        if value != self.expected[self.expected_index]:
            self.expected = b""
            self.expected_index = 0
            self.expected_rule = None
            self.expected_match = 0
            return
        self.expected_index += 1

    def observe_unit(self, signature: int) -> None:
        self.recent.append(signature)
        if len(self.recent) > self.max_context:
            del self.recent[0]
        self.expected = b""
        self.expected_index = 0
        self.expected_rule = None
        self.expected_match = 0
        for length in range(min(self.max_context, len(self.recent)), 0, -1):
            rule = self.rules.get(tuple(self.recent[-length:]))
            if rule is not None:
                self.expected = rule.encoded
                self.expected_rule = rule
                self.expected_match = length
                return


class TitleEndpointState:
    def __init__(self, dictionary: list[bytes]) -> None:
        self.tokenizer = WrtTokenizer(dictionary)
        self.wiki = WikiState()
        self.current_units: list[WrtUnit] = []
        self.current = TitleTokenModel()
        self.previous = TitleTokenModel()
        self.pages = 0
        self.titles = 0
        self.title_units = 0
        self.decoded_sha256 = hashlib.sha256()
        self.decoded_bytes = 0

    def endpoints(self) -> tuple[Endpoint | None, Endpoint | None]:
        return self.current.endpoint(), self.previous.endpoint()

    def feed(self, encoded: int) -> None:
        self.current.observe_stream_byte(encoded)
        self.previous.observe_stream_byte(encoded)
        unit = self.tokenizer.feed(encoded)
        if unit is None:
            return
        title_before = self.wiki.title_mode
        prose_before = self.wiki.prose_mode
        in_tag_before = self.wiki.in_tag
        self.decoded_sha256.update(unit.decoded)
        self.decoded_bytes += len(unit.decoded)
        self.wiki.feed(unit.decoded)

        if self.wiki.page_boundary == 1:
            self.previous.build(self.current_units)
            self.current_units = []
            self.current.build(())
            self.pages += 1

        begins_tag = unit.decoded.startswith(b"<")
        if title_before and not in_tag_before and not begins_tag:
            self.current_units.append(unit)
            self.title_units += 1
        if title_before and not self.wiki.title_mode:
            self.current.build(self.current_units)
            self.titles += 1

        body_unit = prose_before and not in_tag_before and not begins_tag
        if body_unit:
            self.current.observe_unit(unit.signature)
            self.previous.observe_unit(unit.signature)
        else:
            self.current.reset_recent()
            self.previous.reset_recent()


LOSS_QBITS = tuple(
    0 if probability == 0 else int(round(-math.log2(probability / TOTAL) * 256))
    for probability in range(TOTAL + 1)
)


def loss_qbits(bit: int, p1: int) -> int:
    return LOSS_QBITS[p1 if bit else TOTAL - p1]


def blend_probability(base_p1: int, expert_p1: int, blend_ppm: int) -> int:
    mixed = (base_p1 * (1_000_000 - blend_ppm) + expert_p1 * blend_ppm + 500_000) // 1_000_000
    return max(1, min(TOTAL - 1, mixed))


def decay_toward_zero(value: int, shift: int = 12) -> int:
    amount = abs(value) >> shift
    return value - amount if value > 0 else value + amount


@dataclass(frozen=True)
class VariantSpec:
    source: str
    min_context: int
    blend_ppm: int
    strict: bool
    router: str

    @property
    def variant_id(self) -> str:
        strict = "strict" if self.strict else "majority"
        return f"{self.source}_m{self.min_context}_b{self.blend_ppm}_{strict}_{self.router}"


@dataclass
class VariantStats:
    spec: VariantSpec
    eligible_bits: int = 0
    applied_bits: int = 0
    qbits_saved: int = 0
    counterfactual_qbits: int = 0
    regret_qbits: int = 0
    block_qbits: dict[int, int] = field(default_factory=dict)

    def probability(self, endpoint: Endpoint, bit_pos: int, prefix: int, base_p1: int) -> tuple[int, int] | None:
        if endpoint.match_tokens < self.spec.min_context:
            return None
        if self.spec.strict and endpoint.best_count != endpoint.total:
            return None
        if bit_pos and endpoint.expected_byte >> (8 - bit_pos) != prefix:
            return None
        expected_bit = (endpoint.expected_byte >> (7 - bit_pos)) & 1
        expert_p1 = EXPERT_ONE if expected_bit else EXPERT_ZERO
        return blend_probability(base_p1, expert_p1, self.spec.blend_ppm), expected_bit


def all_specs() -> list[VariantSpec]:
    return [
        VariantSpec(source, context, blend, strict, router)
        for source in ("current", "previous")
        for context in TITLE_CONTEXTS
        for blend in BLENDS_PPM
        for strict in (True, False)
        for router in ("always", "regret12")
    ]


class Fx2RangeCounter:
    def __init__(self) -> None:
        self.x1 = 0
        self.x2 = MAX_CODE
        self.bytes = 0

    def encode(self, bit: int, p1: int) -> None:
        delta = self.x2 - self.x1
        midpoint = self.x1 + (delta >> 16) * p1 + ((delta & 0xFFFF) * p1 >> 16)
        if bit:
            self.x2 = midpoint
        else:
            self.x1 = midpoint + 1
        while ((self.x1 ^ self.x2) & 0xFF000000) == 0:
            self.bytes += 1
            self.x1 = (self.x1 << 8) & MAX_CODE
            self.x2 = ((self.x2 << 8) & MAX_CODE) + 255

    def finish(self) -> None:
        while ((self.x1 ^ self.x2) & 0xFF000000) == 0:
            self.bytes += 1
            self.x1 = (self.x1 << 8) & MAX_CODE
            self.x2 = ((self.x2 << 8) & MAX_CODE) + 255
        self.bytes += 1


def score_trace(
    trace: Path,
    dictionary: list[bytes],
    specs: Sequence[VariantSpec],
    exact_ids: set[str] | None = None,
) -> tuple[dict[str, VariantStats], dict[str, object]]:
    states = {spec.variant_id: VariantStats(spec) for spec in specs}
    endpoint_state = TitleEndpointState(dictionary)
    exact_ids = exact_ids or set()
    exact = {variant_id: Fx2RangeCounter() for variant_id in exact_ids}
    baseline = Fx2RangeCounter() if exact_ids else None
    wrt_digest = hashlib.sha256()
    wrt_bytes = 0

    for byte_pos, trace_byte in enumerate(iter_trace_bytes(trace)):
        current, previous = endpoint_state.endpoints()
        endpoints = {"current": current, "previous": previous}
        prefix = 0
        wrt_digest.update(bytes((trace_byte.value,)))
        wrt_bytes += 1
        for bit_pos, (p1, bit) in enumerate(zip(trace_byte.probabilities, trace_byte.bits)):
            if baseline is not None:
                baseline.encode(bit, p1)
            for variant_id, state in states.items():
                endpoint = endpoints[state.spec.source]
                candidate: tuple[int, int] | None = None
                if endpoint is not None:
                    candidate = state.probability(endpoint, bit_pos, prefix, p1)
                chosen = p1
                if candidate is not None:
                    candidate_p1, _ = candidate
                    delta = loss_qbits(bit, p1) - loss_qbits(bit, candidate_p1)
                    state.eligible_bits += 1
                    state.counterfactual_qbits += delta
                    apply = state.spec.router == "always" or state.regret_qbits > 0
                    if apply:
                        chosen = candidate_p1
                        state.applied_bits += 1
                        state.qbits_saved += delta
                        block = byte_pos // BLOCK_BYTES
                        state.block_qbits[block] = state.block_qbits.get(block, 0) + delta
                    if state.spec.router == "regret12":
                        state.regret_qbits = max(
                            -(1 << 24),
                            min(1 << 24, decay_toward_zero(state.regret_qbits) + delta),
                        )
                if variant_id in exact:
                    exact[variant_id].encode(bit, chosen)
            prefix = (prefix << 1) | bit
        endpoint_state.feed(trace_byte.value)

    exact_rows: dict[str, object] = {}
    if baseline is not None:
        baseline.finish()
        for variant_id, coder in exact.items():
            coder.finish()
            exact_rows[variant_id] = {
                "baseline_payload_bytes": baseline.bytes,
                "candidate_payload_bytes": coder.bytes,
                "saved_bytes": baseline.bytes - coder.bytes,
            }
    diagnostics = {
        "wrt_bytes": wrt_bytes,
        "wrt_sha256": wrt_digest.hexdigest(),
        "decoded_bytes": endpoint_state.decoded_bytes,
        "decoded_sha256": endpoint_state.decoded_sha256.hexdigest(),
        "pages": endpoint_state.pages,
        "titles": endpoint_state.titles,
        "title_units": endpoint_state.title_units,
        "exact": exact_rows,
    }
    return states, diagnostics


def row_for(stats: VariantStats, scope_bytes: int) -> dict[str, object]:
    blocks = list(stats.block_qbits.values())
    return {
        "variant_id": stats.spec.variant_id,
        "source": stats.spec.source,
        "min_context_tokens": stats.spec.min_context,
        "blend_ppm": stats.spec.blend_ppm,
        "strict_next_token": stats.spec.strict,
        "router": stats.spec.router,
        "eligible_bits": stats.eligible_bits,
        "applied_bits": stats.applied_bits,
        "qbits_saved": stats.qbits_saved,
        "qbit_saved_bytes": stats.qbits_saved / 2048.0,
        "qbit_gain_bytes_per_million": stats.qbits_saved / 2048.0 * 1_000_000 / scope_bytes,
        "counterfactual_qbits": stats.counterfactual_qbits,
        "positive_blocks": sum(value > 0 for value in blocks),
        "regressing_blocks": sum(value < 0 for value in blocks),
        "flat_blocks": sum(value == 0 for value in blocks),
        "worst_block_qbit_bytes": min(blocks, default=0) / 2048.0,
    }


def archive_payload_bytes(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(5)
    if len(header) != 5:
        raise ValueError("truncated FX2 archive")
    wrt_bytes = header[0] & 0x7F
    for value in header[1:]:
        wrt_bytes = (wrt_bytes << 8) | value
    header_bytes = 5 if wrt_bytes < 10_000 else 37
    return path.stat().st_size - header_bytes, wrt_bytes


def parse_variant_id(value: str, specs: Sequence[VariantSpec]) -> VariantSpec:
    matches = [spec for spec in specs if spec.variant_id == value]
    if len(matches) != 1:
        raise ValueError(f"unknown variant id: {value}")
    return matches[0]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--wrt-store", type=Path)
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--phase", choices=("selection", "confirmation"), required=True)
    parser.add_argument("--variant-id")
    parser.add_argument("--exact-top", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.scope_bytes <= 0 or args.exact_top <= 0:
        raise SystemExit("scope and exact-top must be positive")
    for path in (args.trace, args.dictionary):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")

    specs = all_specs()
    if args.variant_id:
        selected = parse_variant_id(args.variant_id, specs)
        first_specs = [selected]
    else:
        first_specs = specs
    dictionary = load_dictionary(args.dictionary)
    first, diagnostics = score_trace(args.trace, dictionary, first_specs)
    rows = [row_for(stats, args.scope_bytes) for stats in first.values()]
    rows.sort(
        key=lambda row: (
            -float(row["qbit_gain_bytes_per_million"]),
            int(row["regressing_blocks"]),
            str(row["variant_id"]),
        )
    )
    candidate_rows = [row for row in rows if row["source"] == "current"]
    control_rows = [row for row in rows if row["source"] == "previous"]
    exact_ids = {
        str(row["variant_id"])
        for row in candidate_rows[: args.exact_top]
        + control_rows[: min(4, args.exact_top)]
    }
    exact_specs = [parse_variant_id(value, specs) for value in exact_ids]
    _, exact_diagnostics = score_trace(args.trace, dictionary, exact_specs, exact_ids)
    exact = exact_diagnostics["exact"]
    for row in rows:
        row["exact"] = exact.get(str(row["variant_id"]))

    validations: dict[str, object] = {}
    if args.archive:
        payload_bytes, archive_wrt_bytes = archive_payload_bytes(args.archive)
        baseline_values = {
            int(value["baseline_payload_bytes"])
            for value in exact.values()
        }
        validations["archive"] = {
            "path": str(args.archive),
            "sha256": sha256_file(args.archive),
            "payload_bytes": payload_bytes,
            "wrt_bytes": archive_wrt_bytes,
            "trace_wrt_bytes_match": archive_wrt_bytes == diagnostics["wrt_bytes"],
            "baseline_range_match": baseline_values == {payload_bytes},
        }
    if args.wrt_store:
        stored = args.wrt_store.read_bytes()
        traced = b"".join(bytes((row.value,)) for row in iter_trace_bytes(args.trace))
        candidates = (stored, stored[5:] if len(stored) >= 5 else b"")
        validations["wrt_store"] = {
            "path": str(args.wrt_store),
            "sha256": sha256_file(args.wrt_store),
            "trace_matches_store": traced in candidates,
            "trace_sha256": hashlib.sha256(traced).hexdigest(),
        }

    tool = Path(__file__).resolve()
    payload = {
        "schema_version": 1,
        "receipt_type": "wrt_title_token_automaton_shadow",
        "evidence_level": "compact_exact_fx2_probability_trace_shadow",
        "claim_boundary": (
            "This is a causal shadow replay on an arbitrary random window. "
            "It is not integrated source, a native candidate archive, a prefix score, "
            "or a 10.95% proof."
        ),
        "window_id": args.window_id,
        "phase": args.phase,
        "scope_bytes": args.scope_bytes,
        "trace": {
            "path": str(args.trace),
            "bytes": args.trace.stat().st_size,
            "sha256": sha256_file(args.trace),
            "record_format": "8-byte FX2PT01 header then little-endian uint16 p1 and uint8 truth bit",
        },
        "dictionary": {
            "path": str(args.dictionary),
            "bytes": args.dictionary.stat().st_size,
            "sha256": sha256_file(args.dictionary),
            "words": len(dictionary),
        },
        "tool": {"path": str(tool), "sha256": sha256_file(tool)},
        "contract": {
            "sources": ["current", "previous"],
            "title_context_tokens": list(TITLE_CONTEXTS),
            "blend_ppm": list(BLENDS_PPM),
            "strict_modes": [True, False],
            "routers": ["always", "regret12"],
            "expert_probability_one": EXPERT_ONE,
            "block_bytes": BLOCK_BYTES,
            "target_gross_bytes_per_million": 700,
        },
        "diagnostics": diagnostics,
        "validations": validations,
        "rows": rows,
        "best": candidate_rows[0] if candidate_rows else None,
        "best_control": control_rows[0] if control_rows else None,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["best"], indent=2, sort_keys=True))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
