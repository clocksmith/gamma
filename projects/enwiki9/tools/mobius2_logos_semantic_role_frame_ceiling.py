#!/usr/bin/env python3
"""Run the frozen opening-1M LOGOS semantic-role frame ceiling."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass, field
import gzip
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from typing import Any, Iterable, Sequence

import numpy as np

import paid_block_vector_codebook as range_codec
from radix_island_oracle import EmissionGroup, emission_groups
from wrt_exact import parse_store


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "mobius2_logos_semantic_role_frame_ceiling_q0_v1"
PROPOSAL_ID = "mobius2_logos_semantic_role_frame_ceiling_v1"
PLAN = ROOT / "docs/mobius2_logos_semantic_role_frame_ceiling_plan.md"
SCHEMA = ROOT / "docs/mobius2_logos_semantic_role_frame_ceiling_decision.schema.json"
P1_MAGIC = b"CMX21P1\0"
PAGE_MAP_MAGIC = b"SIBMAP1\0"
PAGE_MAP_RECORD = struct.Struct("<QQQQ")
PAGE_MAP_SHA256 = "3122936977eb65650601c15cd0fa42bacbbd60ad3713e18c1e99fae1e5033425"
BACKEND_BYTES = 1_899_840
BACKEND_SHA256 = "d1066630f0d58894e69bd84519ec7d0f608b9e2fce67ab9ebedde65c58eca194"
MIN_GROUPS = 6
MAX_GROUPS = 128
MIN_RAW_BYTES = 24
MAX_RAW_BYTES = 512
MIN_ASCII_LETTERS = 12
MIN_SLOTS = 2
MIN_CLASSIFIED_WORDS = 3
MIN_RELATIONS = 1
GROSS_GATE_BPM = 3_000.0
TOTAL = 1 << 16

SLOT_LABELS = ("TITLE", "LINK", "ENTITY", "DATE", "NUMBER", "QUANTITY", "URL", "CONTENT")
SLOT_INDEX = {name: index for index, name in enumerate(SLOT_LABELS)}

MONTHS = frozenset(
    b"january february march april may june july august september october november december "
    b"jan feb mar apr jun jul aug sep sept oct nov dec".split()
)
UNITS = frozenset(
    b"km m cm mm kg g mg lb lbs ft feet mile miles metre metres meter meters percent percentage "
    b"hz khz mhz ghz byte bytes kb mb gb tb celsius fahrenheit kelvin litre litres liter liters".split()
)


def words(source: bytes) -> tuple[bytes, ...]:
    return tuple(source.split())


WORD_GROUPS: dict[str, tuple[bytes, ...]] = {
    "DET": words(b"a an the this that these those another any either neither"),
    "COPULA": words(b"am is are was were be been being become becomes became remain remains remained"),
    "AUX": words(b"can could may might must shall should will would do does did done"),
    "HAVE": words(b"has have had having"),
    "CONJ": words(b"and or but nor yet while although though however whereas"),
    "RELATIVE": words(b"who whom whose which where when"),
    "PREP_LOC": words(b"in on at near within from into across through between among around under over outside inside"),
    "PREP_TIME": words(b"before after during since until upon throughout"),
    "PREP": words(b"of for with by as to about against without via per"),
    "QUANTIFIER": words(b"one two three many several each every all some most more less few numerous various"),
    "NEG": words(b"not no never neither"),
    "BIRTH": words(b"born birth birthplace native"),
    "DEATH": words(b"died death killed"),
    "CREATE": words(b"founded established created built opened formed developed published released invented"),
    "SERVE": words(b"served held elected appointed joined represented worked played won"),
    "LOCATE": words(b"located situated lies lie based headquartered borders covers occupies"),
    "NAME": words(b"known called named titled nicknamed referred"),
    "INCLUDE": words(b"include includes included contain contains contained comprise comprises consisting consists feature features"),
    "TYPE": words(b"type kind species genus family class form category member example"),
    "MEMBER": words(b"part belongs belonging affiliated division subsidiary component branch"),
    "MEASURE": words(b"measures measured weighs spans reaches covers totals"),
    "CHANGE": words(b"began started ended ceased continued changed moved merged renamed replaced"),
}
WORD_CLASS = {
    word: group
    for group, group_words in WORD_GROUPS.items()
    for word in group_words
}
RELATION_CLASSES = frozenset(
    {
        "COPULA",
        "BIRTH",
        "DEATH",
        "CREATE",
        "SERVE",
        "LOCATE",
        "NAME",
        "INCLUDE",
        "TYPE",
        "MEMBER",
        "MEASURE",
        "CHANGE",
    }
)
PROHIBITED = (
    b"{{",
    b"}}",
    b"{|",
    b"|}",
    b"<ref",
    b"</ref",
    b"<gallery",
    b"</gallery",
    b"[[category:",
    b"[[file:",
    b"[[image:",
    b"<table",
)


@dataclass(frozen=True)
class Page:
    index: int
    raw_start: int
    raw_end: int
    wrt_start: int
    wrt_end: int
    split: str


@dataclass(frozen=True)
class TextPopulation:
    page: Page
    raw_start: int
    raw_end: int
    group_start: int
    group_end: int
    title: bytes


@dataclass(frozen=True)
class Clause:
    page_index: int
    clause_index: int
    split: str
    semantic_key: tuple[tuple[str, Any], ...]
    surface_key: tuple[tuple[str, Any], ...]
    rotated_key: tuple[tuple[str, Any], ...]
    slot_surfaces: tuple[bytes, ...]
    realization: tuple[bytes, ...]
    fixed_intervals: tuple[tuple[int, int], ...]


@dataclass
class RuleStats:
    pages: set[int] = field(default_factory=set)
    slots: set[tuple[bytes, ...]] = field(default_factory=set)
    realizations: set[tuple[bytes, ...]] = field(default_factory=set)

    def observe(self, clause: Clause) -> None:
        self.pages.add(clause.page_index)
        self.slots.add(clause.slot_surfaces)
        self.realizations.add(clause.realization)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def require_identity(observed: dict[str, Any], expected: dict[str, Any], label: str) -> None:
    if (observed["bytes"], observed["sha256"]) != (expected["bytes"], expected["sha256"]):
        raise ValueError(f"{label} differs from the certified parent trace")


def read_p1(path: Path, rows: int) -> np.ndarray:
    raw = path.read_bytes()
    if len(raw) < 16 or raw[:8] != P1_MAGIC:
        raise ValueError("invalid endpoint428 P1 trace")
    declared = struct.unpack_from("<Q", raw, 8)[0]
    values = np.frombuffer(raw, dtype="<u2", offset=16).copy()
    if declared != rows or len(values) != rows or np.any(values == 0):
        raise ValueError("endpoint428 P1 trace does not match WRT truth")
    return values


def read_pages(path: Path, wrt_bytes: int) -> list[Page]:
    if sha256_file(path) != PAGE_MAP_SHA256:
        raise ValueError("page map differs from the frozen population")
    data = path.read_bytes()
    if len(data) < 16 or data[:8] != PAGE_MAP_MAGIC:
        raise ValueError("invalid page map")
    count = struct.unpack_from("<Q", data, 8)[0]
    if len(data) != 16 + count * PAGE_MAP_RECORD.size:
        raise ValueError("page-map record count mismatch")
    development_end = count * 3 // 5
    selection_end = count * 4 // 5
    output: list[Page] = []
    for index in range(count):
        raw_start, raw_end, row_start, row_end = PAGE_MAP_RECORD.unpack_from(
            data, 16 + index * PAGE_MAP_RECORD.size
        )
        if row_start % 8 or row_end % 8:
            raise ValueError("page map is not WRT-byte aligned")
        split = "development" if index < development_end else "selection" if index < selection_end else "sealed_confirmation"
        page = Page(index, raw_start, raw_end, row_start // 8, row_end // 8, split)
        if not 0 <= page.wrt_start < page.wrt_end <= wrt_bytes:
            raise ValueError("page map exceeds WRT stream")
        output.append(page)
    return output


def text_populations(raw: bytes, pages: Sequence[Page], groups: Sequence[EmissionGroup]) -> tuple[list[TextPopulation], dict[str, int]]:
    starts = [group.raw_start for group in groups]
    populations: list[TextPopulation] = []
    missing = 0
    for page in pages:
        title_open = raw.find(b"<title>", page.raw_start, page.raw_end)
        title_close = raw.find(b"</title>", title_open + 7, page.raw_end) if title_open >= 0 else -1
        title = raw[title_open + 7 : title_close] if title_open >= 0 and title_close >= 0 else b""
        opening = raw.find(b"<text", page.raw_start, page.raw_end)
        content_start = raw.find(b">", opening, page.raw_end) if opening >= 0 else -1
        if content_start < 0:
            missing += 1
            continue
        content_start += 1
        content_end = raw.find(b"</text>", content_start, page.raw_end)
        if content_end < 0:
            missing += 1
            continue
        group_start = int(np.searchsorted(starts, content_start, side="left"))
        group_end = int(np.searchsorted(starts, content_end, side="left"))
        while group_start < len(groups) and groups[group_start].raw_start < content_start:
            group_start += 1
        while group_end > group_start and groups[group_end - 1].raw_end > content_end:
            group_end -= 1
        if group_start >= group_end:
            missing += 1
            continue
        populations.append(TextPopulation(page, content_start, content_end, group_start, group_end, title))
    return populations, {"pages_with_text": len(populations), "pages_without_eligible_text": missing}


def mark_semantic_spans(raw: bytes, population: TextPopulation) -> bytearray:
    mask = bytearray(population.raw_end - population.raw_start)

    def mark(start: int, end: int, value: int) -> None:
        lo = max(start, population.raw_start) - population.raw_start
        hi = min(end, population.raw_end) - population.raw_start
        if lo < hi:
            mask[lo:hi] = bytes((value,)) * (hi - lo)

    title = population.title.strip()
    if len(title) >= 4 and sum(chr(value).isalpha() for value in title) >= 3:
        cursor = population.raw_start
        while True:
            found = raw.find(title, cursor, population.raw_end)
            if found < 0:
                break
            mark(found, found + len(title), 1)
            cursor = found + len(title)

    cursor = population.raw_start
    while True:
        opening = raw.find(b"[[", cursor, population.raw_end)
        if opening < 0:
            break
        closing = raw.find(b"]]", opening + 2, population.raw_end)
        if closing < 0:
            break
        target_end = closing
        for separator in (b"|", b"#"):
            position = raw.find(separator, opening + 2, closing)
            if position >= 0:
                target_end = min(target_end, position)
        mark(opening + 2, target_end, 2)
        cursor = closing + 2
    return mask


def punctuation_class(decoded: bytes) -> str | None:
    if decoded.isspace():
        return "WS"
    if decoded in (b".", b"!", b"?"):
        return "END"
    if decoded in (b",", b";", b":"):
        return "PAUSE"
    if decoded in (b"(", b")", b"[", b"]"):
        return "BRACKET"
    if decoded in (b'"', b"'", b"``", b"''"):
        return "QUOTE"
    if decoded in (b"-", b"--", b"\xe2\x80\x93", b"\xe2\x80\x94"):
        return "DASH"
    return None


def group_slot(group: EmissionGroup, mask: bytearray, population: TextPopulation) -> str | None:
    local_start = group.raw_start - population.raw_start
    local_end = group.raw_end - population.raw_start
    if 0 <= local_start < local_end <= len(mask):
        values = mask[local_start:local_end]
        if values and all(value == 1 for value in values):
            return "TITLE"
        if values and all(value == 2 for value in values):
            return "LINK"
    decoded = group.decoded
    lower = decoded.lower()
    if any(ord("0") <= value <= ord("9") for value in decoded):
        return "NUMBER"
    if lower in MONTHS:
        return "DATE"
    if lower in UNITS:
        return "QUANTITY"
    if lower in (b"http", b"https", b"www"):
        return "URL"
    if lower in WORD_CLASS:
        return None
    if decoded.isalpha():
        return "ENTITY" if decoded[:1].isupper() else "CONTENT"
    return None


def fixed_semantic_atom(group: EmissionGroup, wrt: bytes) -> tuple[str, Any]:
    lower = group.decoded.lower()
    word_class = WORD_CLASS.get(lower)
    if word_class is not None:
        return ("W", word_class)
    punct = punctuation_class(group.decoded)
    if punct is not None:
        return ("P", punct)
    return ("X", wrt[group.stream_start : group.stream_end])


def rotate_slot(label: str, page_index: int, clause_index: int, slot_index: int) -> str:
    index = SLOT_INDEX[label]
    shift = 1 + ((page_index * 131 + clause_index * 17 + slot_index * 7) % (len(SLOT_LABELS) - 1))
    return SLOT_LABELS[(index + shift) % len(SLOT_LABELS)]


def merge_intervals(intervals: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    ordered = sorted(intervals)
    merged: list[list[int]] = []
    for start, end in ordered:
        if not 0 <= start < end:
            raise ValueError("invalid generated interval")
        if merged and start < merged[-1][1]:
            raise ValueError("overlapping generated intervals")
        if merged and start == merged[-1][1]:
            merged[-1][1] = end
        else:
            merged.append([start, end])
    return tuple((start, end) for start, end in merged)


def make_clause(
    raw: bytes,
    wrt: bytes,
    groups: Sequence[EmissionGroup],
    population: TextPopulation,
    mask: bytearray,
    start: int,
    end: int,
    clause_index: int,
) -> Clause | None:
    while start < end and groups[start].decoded.isspace():
        start += 1
    while end > start and groups[end - 1].decoded.isspace():
        end -= 1
    if not MIN_GROUPS <= end - start <= MAX_GROUPS:
        return None
    raw_start = groups[start].raw_start
    raw_end = groups[end - 1].raw_end
    surface = raw[raw_start:raw_end]
    lower = surface.lower()
    if not MIN_RAW_BYTES <= len(surface) <= MAX_RAW_BYTES:
        return None
    if sum((ord("a") <= value <= ord("z")) or (ord("A") <= value <= ord("Z")) for value in surface) < MIN_ASCII_LETTERS:
        return None
    if b"<" in surface or any(token in lower for token in PROHIBITED):
        return None

    selected = groups[start:end]
    labels = [group_slot(group, mask, population) for group in selected]
    for index in range(1, len(selected) - 1):
        if selected[index].decoded.isspace() and labels[index - 1] is not None and labels[index - 1] == labels[index + 1]:
            labels[index] = labels[index - 1]

    semantic_atoms: list[tuple[str, Any]] = []
    surface_atoms: list[tuple[str, Any]] = []
    slot_surfaces: list[bytes] = []
    realization: list[bytes] = []
    fixed_intervals: list[tuple[int, int]] = []
    classified_words = 0
    relations = 0
    slot_index = 0
    index = 0
    while index < len(selected):
        group = selected[index]
        label = labels[index]
        if label is not None:
            stop = index + 1
            while stop < len(selected) and labels[stop] == label:
                stop += 1
            slot_bytes = wrt[group.stream_start : selected[stop - 1].stream_end]
            semantic_atoms.append(("S", label))
            surface_atoms.append(("S", label))
            slot_surfaces.append(slot_bytes)
            slot_index += 1
            index = stop
            continue

        encoded = wrt[group.stream_start : group.stream_end]
        atom = fixed_semantic_atom(group, wrt)
        semantic_atoms.append(atom)
        surface_atoms.append(("F", encoded))
        realization.append(encoded)
        fixed_intervals.append((group.stream_start, group.stream_end))
        if atom[0] == "W":
            classified_words += 1
            if atom[1] in RELATION_CLASSES:
                relations += 1
        index += 1

    if len(slot_surfaces) < MIN_SLOTS or classified_words < MIN_CLASSIFIED_WORDS or relations < MIN_RELATIONS:
        return None
    rotated_atoms: list[tuple[str, Any]] = []
    rotated_index = 0
    for atom in semantic_atoms:
        if atom[0] == "S":
            rotated_atoms.append(("S", rotate_slot(str(atom[1]), population.page.index, clause_index, rotated_index)))
            rotated_index += 1
        else:
            rotated_atoms.append(atom)
    return Clause(
        population.page.index,
        clause_index,
        population.page.split,
        tuple(semantic_atoms),
        tuple(surface_atoms),
        tuple(rotated_atoms),
        tuple(slot_surfaces),
        tuple(realization),
        merge_intervals(fixed_intervals),
    )


def discover_clauses(raw: bytes, wrt: bytes, groups: Sequence[EmissionGroup], populations: Sequence[TextPopulation]) -> tuple[list[Clause], dict[str, int]]:
    clauses: list[Clause] = []
    scanned = 0
    for population in populations:
        mask = mark_semantic_spans(raw, population)
        start = population.group_start
        clause_index = 0
        for index in range(population.group_start, population.group_end):
            decoded = groups[index].decoded
            boundary = any(value in decoded for value in b".!?;\n")
            if not boundary:
                continue
            scanned += 1
            clause = make_clause(raw, wrt, groups, population, mask, start, index + 1, clause_index)
            if clause is not None:
                clauses.append(clause)
            clause_index += 1
            start = index + 1
        if start < population.group_end:
            scanned += 1
            clause = make_clause(raw, wrt, groups, population, mask, start, population.group_end, clause_index)
            if clause is not None:
                clauses.append(clause)
    return clauses, {"clause_segments_scanned": scanned, "eligible_semantic_clauses": len(clauses)}


def qualified_keys(clauses: Sequence[Clause]) -> tuple[set[Any], set[Any], set[Any], dict[str, Any]]:
    semantic: dict[Any, RuleStats] = defaultdict(RuleStats)
    surface: dict[Any, RuleStats] = defaultdict(RuleStats)
    rotated: dict[Any, RuleStats] = defaultdict(RuleStats)
    for clause in clauses:
        if clause.split != "development":
            continue
        semantic[clause.semantic_key].observe(clause)
        surface[clause.surface_key].observe(clause)
        rotated[clause.rotated_key].observe(clause)

    semantic_keys = {key for key, stats in semantic.items() if len(stats.pages) >= 2 and len(stats.slots) >= 2 and len(stats.realizations) >= 2}
    surface_keys = {key for key, stats in surface.items() if len(stats.pages) >= 2 and len(stats.slots) >= 2}
    rotated_keys = {key for key, stats in rotated.items() if len(stats.pages) >= 2 and len(stats.slots) >= 2 and len(stats.realizations) >= 2}
    return semantic_keys, surface_keys, rotated_keys, {
        "development_semantic_keys": len(semantic),
        "development_surface_keys": len(surface),
        "development_rotated_keys": len(rotated),
        "qualified_semantic_keys": len(semantic_keys),
        "qualified_surface_keys": len(surface_keys),
        "qualified_rotated_keys": len(rotated_keys),
    }


def decode_payload(payload: bytes, probabilities: np.ndarray) -> np.ndarray:
    if len(payload) < 1:
        raise ValueError("empty arithmetic payload")
    low = 0
    high = 0xFFFFFFFF
    code = int.from_bytes(payload[:4].ljust(4, b"\0"), "big")
    cursor = 4
    truth = np.empty(len(probabilities), dtype=np.uint8)
    for row, p1_value in enumerate(probabilities):
        p1 = int(p1_value)
        delta = high - low
        midpoint = low + (delta >> 16) * p1 + (((delta & 0xFFFF) * p1) >> 16)
        if code <= midpoint:
            truth[row] = 1
            high = midpoint
        else:
            truth[row] = 0
            low = midpoint + 1
        while ((low ^ high) & 0xFF000000) == 0:
            low = (low << 8) & 0xFFFFFFFF
            high = ((high << 8) & 0xFFFFFFFF) + 255
            next_byte = payload[cursor] if cursor < len(payload) else 0
            cursor += 1
            code = ((code << 8) & 0xFFFFFFFF) + next_byte
    return truth


def build_control(name: str, clauses: Sequence[Clause], key_name: str, probabilities: np.ndarray, truth: np.ndarray, wrt: bytes, parent_payload_bytes: int) -> tuple[dict[str, Any], bytes, bytes]:
    intervals = merge_intervals(
        interval
        for clause in clauses
        for interval in clause.fixed_intervals
    )
    literal_mask = np.ones(len(truth), dtype=bool)
    for start, end in intervals:
        literal_mask[start * 8 : end * 8] = False
    literal_p1 = probabilities[literal_mask]
    literal_truth = truth[literal_mask]
    payload = range_codec.encode_payload(literal_p1, literal_truth)
    decoded_literal = decode_payload(payload, literal_p1)
    reconstructed = np.zeros(len(truth), dtype=np.uint8)
    reconstructed[literal_mask] = decoded_literal
    for start, end in intervals:
        reconstructed[start * 8 : end * 8] = truth[start * 8 : end * 8]
    reconstructed_wrt = np.packbits(reconstructed, bitorder="big").tobytes()
    second = range_codec.encode_payload(literal_p1, literal_truth)
    receipt = {
        "name": name,
        "key": key_name,
        "qualified_rules_used": len({getattr(clause, key_name) for clause in clauses}) if clauses else 0,
        "selected_clauses": len(clauses),
        "generated_intervals": len(intervals),
        "generated_wrt_bytes": sum(end - start for start, end in intervals),
        "literal_bits": int(literal_mask.sum()),
        "payload_bytes": len(payload),
        "payload_sha256": sha256_bytes(payload),
        "gain_vs_parent_payload_bytes": parent_payload_bytes - len(payload),
        "arithmetic_decode_ok": np.array_equal(decoded_literal, literal_truth),
        "wrt_reconstruction_ok": reconstructed_wrt == wrt,
        "second_payload_identity": second == payload,
        "split_clauses": {
            split: sum(clause.split == split for clause in clauses)
            for split in ("development", "selection", "sealed_confirmation")
        },
    }
    if not receipt["arithmetic_decode_ok"] or not receipt["wrt_reconstruction_ok"] or not receipt["second_payload_identity"]:
        raise ValueError(f"{name} exact residual replay failed")
    return receipt, payload, reconstructed_wrt


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
    if args.output_dir.exists():
        raise ValueError("output directory already exists")
    args.output_dir.mkdir(parents=True)

    trace_decision = json.loads(args.parent_trace_decision.read_text())
    if trace_decision.get("schema") != "endpoint428_exact_parent_p1_trace_gate_v1" or not trace_decision["decision"]["typed_event_shadow_authorized"]:
        raise ValueError("parent trace certificate is not authorized")
    observed = {
        "p1": artifact(args.p1),
        "wrt_store": artifact(args.wrt_store),
        "raw_input": artifact(args.raw_input),
        "parent_archive": artifact(args.parent_archive),
        "dictionary": artifact(args.dictionary),
    }
    expected = {
        "p1": trace_decision["artifacts"]["p1_a"],
        "wrt_store": trace_decision["inputs"]["wrt_store"],
        "raw_input": trace_decision["inputs"]["raw_input"],
        "parent_archive": trace_decision["inputs"]["reference_archive"],
        "dictionary": trace_decision["inputs"]["dictionary"],
    }
    for label in observed:
        require_identity(observed[label], expected[label], label)
    backend_artifact = artifact(args.backend)
    if (backend_artifact["bytes"], backend_artifact["sha256"]) != (BACKEND_BYTES, BACKEND_SHA256):
        raise ValueError("backend differs from the recovered exact inverse")

    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    wrt = parsed.stream
    if parsed.decoded != raw:
        raise ValueError("exact WRT inverse differs from canonical raw")
    truth = np.unpackbits(np.frombuffer(wrt, dtype=np.uint8), bitorder="big")
    probabilities = read_p1(args.p1, len(truth))
    parent_payload, header_bytes, declared_wrt = range_codec.read_archive(args.parent_archive)
    if declared_wrt != len(wrt):
        raise ValueError("parent archive WRT length mismatch")
    replay_parent = range_codec.encode_payload(probabilities, truth)
    if replay_parent != parent_payload:
        raise ValueError("frontier P1 does not replay parent payload")

    pages = read_pages(args.page_map, len(wrt))
    groups = emission_groups(parsed)
    populations, text_stats = text_populations(raw, pages, groups)
    print("phase=semantic_clause_discovery", flush=True)
    clauses, clause_stats = discover_clauses(raw, wrt, groups, populations)
    semantic_keys, surface_keys, rotated_keys, discovery_stats = qualified_keys(clauses)
    selected = {
        "S1": [clause for clause in clauses if clause.surface_key in surface_keys],
        "S2": [clause for clause in clauses if clause.semantic_key in semantic_keys],
        "SR": [clause for clause in clauses if clause.rotated_key in rotated_keys],
    }
    print(
        f"phase=exact_residuals semantic_rules={len(semantic_keys)} semantic_clauses={len(selected['S2'])}",
        flush=True,
    )

    controls: dict[str, dict[str, Any]] = {
        "B0": {
            "payload_bytes": len(parent_payload),
            "payload_sha256": sha256_bytes(parent_payload),
            "parent_payload_identity": replay_parent == parent_payload,
        },
        "SL": {
            "payload_bytes": len(parent_payload),
            "payload_sha256": sha256_bytes(parent_payload),
            "gain_vs_parent_payload_bytes": 0,
        },
    }
    payloads: dict[str, bytes] = {}
    reconstructed_controls: dict[str, bytes] = {}
    for name, key_name in (("S1", "surface_key"), ("S2", "semantic_key"), ("SR", "rotated_key")):
        controls[name], payloads[name], reconstructed_controls[name] = build_control(
            name,
            selected[name],
            key_name,
            probabilities,
            truth,
            wrt,
            len(parent_payload),
        )

    split_controls: dict[str, dict[str, Any]] = {}
    for split in ("development", "selection", "sealed_confirmation"):
        rows = [clause for clause in selected["S2"] if clause.split == split]
        split_controls[split], _payload, _reconstructed = build_control(
            f"S2_{split}",
            rows,
            "semantic_key",
            probabilities,
            truth,
            wrt,
            len(parent_payload),
        )

    reconstructed_store = (
        parsed.stored[: parsed.storage_header_bytes] + reconstructed_controls["S2"]
    )
    wrt_path = args.output_dir / "s2.wrt_store.bin"
    wrt_path.write_bytes(reconstructed_store)
    raw_path = args.output_dir / "s2.restored.raw"
    with (args.output_dir / "s2_inverse.stdout.log").open("wb") as stdout, (args.output_dir / "s2_inverse.stderr.log").open("wb") as stderr:
        inverse = subprocess.run(
            [str(args.backend), "-d", str(args.dictionary), str(wrt_path), str(raw_path)],
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    raw_roundtrip = inverse.returncode == 0 and raw_path.is_file() and raw_path.read_bytes() == raw
    if not raw_roundtrip:
        raise ValueError("official S2 WRT inverse failed")

    for name, payload in payloads.items():
        (args.output_dir / f"{name.lower()}.payload").write_bytes(payload)
    gross_bpm = controls["S2"]["gain_vs_parent_payload_bytes"] * 1_000_000.0 / len(raw)
    conditions = {
        "S2_exact_gross_at_least_3000_BPM": gross_bpm >= GROSS_GATE_BPM,
        "development_gain_positive": split_controls["development"]["gain_vs_parent_payload_bytes"] > 0,
        "selection_gain_positive": split_controls["selection"]["gain_vs_parent_payload_bytes"] > 0,
        "sealed_gain_positive": split_controls["sealed_confirmation"]["gain_vs_parent_payload_bytes"] > 0,
        "S2_beats_surface_S1": controls["S2"]["payload_bytes"] < controls["S1"]["payload_bytes"],
        "S2_beats_rotated_SR": controls["S2"]["payload_bytes"] < controls["SR"]["payload_bytes"],
        "parent_payload_identity": replay_parent == parent_payload,
        "all_arithmetic_decodes": all(controls[name]["arithmetic_decode_ok"] for name in ("S1", "S2", "SR")) and all(row["arithmetic_decode_ok"] for row in split_controls.values()),
        "all_WRT_reconstructions": all(controls[name]["wrt_reconstruction_ok"] for name in ("S1", "S2", "SR")) and all(row["wrt_reconstruction_ok"] for row in split_controls.values()),
        "all_second_payloads_identical": all(controls[name]["second_payload_identity"] for name in ("S1", "S2", "SR")) and all(row["second_payload_identity"] for row in split_controls.values()),
        "official_raw_inverse": raw_roundtrip,
    }
    failed = [name for name, passed in conditions.items() if not passed]
    authorized = not failed
    verdict = "authorize_paid_semantic_role_grammar_q1" if authorized else "retire_frozen_semantic_role_frame_ceiling"
    source_compressed = gzip.compress(Path(__file__).read_bytes(), compresslevel=9, mtime=0)
    decision = {
        "schema": "mobius2_logos_semantic_role_frame_ceiling_q0_v1",
        "candidate_id": CANDIDATE_ID,
        "proposal_id": PROPOSAL_ID,
        "evidence_level": "zero_credit_exact_semantic_role_frame_ceiling",
        "claim_boundary": "Exact opening-1M out-of-band semantic-role generation ceiling only. Rule, realization, slot, invocation, framing, and source bytes are uncharged. No native state hash, forecast credit, larger replay, or full-1G claim.",
        "inputs": {
            **observed,
            "backend": backend_artifact,
            "page_map": artifact(args.page_map),
            "parent_trace_decision": artifact(args.parent_trace_decision),
            "plan": artifact(PLAN),
            "decision_schema": artifact(SCHEMA),
            "oracle_tool": artifact(Path(__file__)),
        },
        "population": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(wrt),
            "trace_rows": len(truth),
            "emission_groups": len(groups),
            "complete_pages": len(pages),
            "page_splits": {split: sum(page.split == split for page in pages) for split in ("development", "selection", "sealed_confirmation")},
            **text_stats,
            **clause_stats,
        },
        "construction": {
            "minimum_groups": MIN_GROUPS,
            "maximum_groups": MAX_GROUPS,
            "minimum_raw_bytes": MIN_RAW_BYTES,
            "maximum_raw_bytes": MAX_RAW_BYTES,
            "minimum_ascii_letters": MIN_ASCII_LETTERS,
            "minimum_slots": MIN_SLOTS,
            "minimum_classified_words": MIN_CLASSIFIED_WORDS,
            "minimum_relations": MIN_RELATIONS,
            "slot_labels": SLOT_LABELS,
            "word_classes": {name: [word.decode("ascii") for word in group] for name, group in WORD_GROUPS.items()},
            "rule_minimum_development_pages": 2,
            "rule_minimum_slot_surfaces": 2,
            "semantic_rule_minimum_realizations": 2,
            "out_of_band_description_bytes_charged": 0,
            "compressed_oracle_source_bytes_uncharged": len(source_compressed),
        },
        "discovery": {
            **discovery_stats,
            "matched_clauses": {name: len(selected[name]) for name in ("S1", "S2", "SR")},
        },
        "controls": controls,
        "split_controls": split_controls,
        "economics": {
            "S2_zero_cost_exact_gain_bytes_per_million": gross_bpm,
            "forecast_bytes_unchanged": 109_389_323,
            "remaining_design_target_debt_bytes": 1_389_323,
            "score_credit_bytes": 0,
        },
        "proof": {
            "input_bindings_exact": True,
            "parent_payload_identity": replay_parent == parent_payload,
            "archive_header_bytes": header_bytes,
            "S2_reconstructed_store_equals_parent": reconstructed_store == parsed.stored,
            "official_inverse_returncode": inverse.returncode,
            "raw_roundtrip": raw_roundtrip,
            "conditions": conditions,
            "failed_conditions": failed,
            "native_predictor_state_hash_proved": False,
        },
        "decision": {
            "verdict": verdict,
            "paid_q1_authorized": authorized,
            "distant_replay_authorized": False,
            "native_integration_authorized": False,
            "full_1g_authorized": False,
            "next_action": "Freeze one paid semantic-role grammar Q1." if authorized else "Retire this exact ontology and frame contract without parameter rescue sweeps.",
        },
        "score_credit_bytes": 0,
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision_path": str(decision_path), "S2_gain_BPM": gross_bpm, "failed_conditions": failed, "verdict": verdict}, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
