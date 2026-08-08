#!/usr/bin/env python3
"""FRACTAL-2 exact-WRT/Endpoint428 optimistic joint ceiling gate.

This is Gate -1, not a codec and not score-bearing evidence.  It supplies rule
selection and source identities for free, but every displaced byte is priced
from the frozen Endpoint428 P1 trace on the exact WRT event population.  All
references are causal across completed pages and all controls use the same
population and source-candidate cap.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
from types import ModuleType
from typing import Iterable

import numpy as np

from wrt_exact import ParsedStore, parse_store


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fractal2_form_echo_joint_qm1_v1"
P1_MAGICS = {b"CMX21P1\0", b"FX2P1V1\0"}
QBITS_PER_BYTE = 2048
MAX_VALUE_EVENTS = 512
MAX_SOURCE_CANDIDATES = 8
MAX_MOSAIC_PIECES = 4
MIN_MOSAIC_EVENTS = 3


@dataclass(frozen=True)
class Span:
    lo: int
    hi: int

    @property
    def events(self) -> int:
        return self.hi - self.lo


@dataclass(frozen=True)
class Occurrence:
    family: str
    rule_key: str
    page: int
    raw_start: int
    raw_end: int
    structural: tuple[Span, ...]
    holes: tuple[Span | None, ...]


@dataclass(frozen=True)
class Value:
    family: str
    key: str
    page: int
    span: Span
    tokens: tuple[bytes, ...]
    raw: bytes


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def load_template_module() -> ModuleType:
    path = ROOT / "programs/wikiir_template_grammar_v1/program.py"
    spec = importlib.util.spec_from_file_location("fractal2_template_parser", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load template parser: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EventMap:
    def __init__(self, parsed: ParsedStore) -> None:
        self.parsed = parsed
        count = len(parsed.events)
        self.raw_starts = np.empty(count, dtype=np.int64)
        self.raw_ends = np.empty(count, dtype=np.int64)
        cursor = 0
        for index, event in enumerate(parsed.events):
            self.raw_starts[index] = cursor
            cursor += len(event.decoded)
            self.raw_ends[index] = cursor
        if cursor != parsed.raw_length:
            raise ValueError("event/raw coordinate map does not cover decoded input")

    def span(self, start: int, end: int) -> Span | None:
        if start >= end:
            return None
        lo = int(np.searchsorted(self.raw_ends, start, side="right"))
        while lo > 0 and self.raw_starts[lo - 1] == start and self.raw_ends[lo - 1] == start:
            lo -= 1
        hi = int(np.searchsorted(self.raw_starts, end, side="left"))
        first_nonempty = lo
        while first_nonempty < hi and self.raw_starts[first_nonempty] == self.raw_ends[first_nonempty]:
            first_nonempty += 1
        last_nonempty = hi - 1
        while last_nonempty >= lo and self.raw_starts[last_nonempty] == self.raw_ends[last_nonempty]:
            last_nonempty -= 1
        if first_nonempty > last_nonempty:
            return None
        if self.raw_starts[first_nonempty] != start or self.raw_ends[last_nonempty] != end:
            return None
        return Span(lo, hi)


def page_ranges(raw: bytes) -> list[tuple[int, int]]:
    pages: list[tuple[int, int]] = []
    position = 0
    while True:
        start = raw.find(b"<page>", position)
        if start < 0:
            return pages
        end = raw.find(b"</page>", start + 6)
        if end < 0:
            return pages
        end += 7
        pages.append((start, end))
        position = end


def signature(family: str, segments: Iterable[bytes]) -> str:
    digest = hashlib.sha256()
    digest.update(family.encode("ascii") + b"\0")
    for segment in segments:
        digest.update(len(segment).to_bytes(4, "little"))
        digest.update(segment)
    return f"{family}:{digest.hexdigest()[:24]}"


def aligned(event_map: EventMap, start: int, end: int) -> Span | None:
    return event_map.span(start, end)


ATTR_VALUE = re.compile(br'(?P<quote>["\'])(?P<value>.*?)(?P=quote)')
TAG = re.compile(br"<[^>]+>")


def page_form_occurrence(
    raw: bytes, event_map: EventMap, page: int, start: int, end: int
) -> Occurrence | None:
    page_bytes = raw[start:end]
    structural: list[Span] = []
    holes: list[Span | None] = []
    shapes: list[bytes] = []
    cursor = 0
    for match in TAG.finditer(page_bytes):
        holes.append(aligned(event_map, start + cursor, start + match.start()))
        tag = match.group()
        tag_cursor = 0
        shape = bytearray()
        for attr in ATTR_VALUE.finditer(tag):
            value_start, value_end = attr.span("value")
            prefix = tag[tag_cursor:value_start]
            shape.extend(prefix)
            if prefix:
                span = aligned(
                    event_map,
                    start + match.start() + tag_cursor,
                    start + match.start() + value_start,
                )
                if span is not None:
                    structural.append(span)
            holes.append(
                aligned(
                    event_map,
                    start + match.start() + value_start,
                    start + match.start() + value_end,
                )
            )
            shape.extend(b"\0")
            tag_cursor = value_end
        suffix = tag[tag_cursor:]
        shape.extend(suffix)
        if suffix:
            span = aligned(
                event_map,
                start + match.start() + tag_cursor,
                start + match.end(),
            )
            if span is not None:
                structural.append(span)
        shapes.append(bytes(shape))
        cursor = match.end()
    holes.append(aligned(event_map, start + cursor, end))
    if not structural or len(shapes) < 4:
        return None
    return Occurrence(
        family="page_form",
        rule_key=signature("page_form", shapes),
        page=page,
        raw_start=start,
        raw_end=end,
        structural=tuple(structural),
        holes=tuple(holes),
    )


def segmented_occurrence(
    family: str,
    raw: bytes,
    event_map: EventMap,
    page: int,
    start: int,
    end: int,
    segments: tuple[bytes, ...],
) -> Occurrence | None:
    structural: list[Span] = []
    holes: list[Span | None] = []
    cursor = start
    for index, segment in enumerate(segments):
        found = raw.find(segment, cursor, end)
        if found < 0:
            return None
        if index:
            holes.append(aligned(event_map, cursor, found))
        span = aligned(event_map, found, found + len(segment))
        if span is None:
            return None
        structural.append(span)
        cursor = found + len(segment)
    if cursor != end:
        return None
    return Occurrence(
        family=family,
        rule_key=signature(family, segments),
        page=page,
        raw_start=start,
        raw_end=end,
        structural=tuple(structural),
        holes=tuple(holes),
    )


def local_occurrences(
    raw: bytes,
    event_map: EventMap,
    template_parser: ModuleType,
    page: int,
    page_start: int,
    page_end: int,
) -> list[Occurrence]:
    out: list[Occurrence] = []
    page_bytes = raw[page_start:page_end]
    for start, end, segments, _holes in template_parser._scan(page_bytes):
        row = segmented_occurrence(
            "template", raw, event_map, page, page_start + start, page_start + end, segments
        )
        if row is not None:
            out.append(row)
    for match in re.finditer(br"\[\[([^\[\]]{1,4096})\]\]", page_bytes):
        body = match.group(1)
        segments = (b"[[", b"]]") if b"|" not in body else (b"[[", b"|", b"]]")
        row = segmented_occurrence(
            "link", raw, event_map, page, page_start + match.start(), page_start + match.end(), segments
        )
        if row is not None:
            out.append(row)
    for match in re.finditer(br"(?m)^(={2,6})([^\r\n]*?)(\1)[ \t]*(?:\r?\n|$)", page_bytes):
        segments = (match.group(1), match.group(3) + match.group(0)[len(match.group(1)) + len(match.group(2)) + len(match.group(3)):])
        row = segmented_occurrence(
            "heading", raw, event_map, page, page_start + match.start(), page_start + match.end(), segments
        )
        if row is not None:
            out.append(row)
    for match in re.finditer(br"(?m)^([*#:;]+[ \t]*)([^\r\n]+)(\r?\n|$)", page_bytes):
        segments = (match.group(1), match.group(3))
        row = segmented_occurrence(
            "list_line", raw, event_map, page, page_start + match.start(), page_start + match.end(), segments
        )
        if row is not None:
            out.append(row)
    return out


def ordinary_xml_values(raw: bytes, event_map: EventMap, pages: list[tuple[int, int]]) -> list[Value]:
    pattern = re.compile(
        br"<(title|id|timestamp|username|ip|comment|text)(?:\s[^>]*)?>(.*?)</\1>",
        re.DOTALL,
    )
    values: list[Value] = []
    for page, (start, end) in enumerate(pages):
        counts: Counter[bytes] = Counter()
        for match in pattern.finditer(raw, start, end):
            tag = match.group(1)
            ordinal = counts[tag]
            counts[tag] += 1
            value_start, value_end = match.span(2)
            span = aligned(event_map, value_start, value_end)
            if span is None or span.events > MAX_VALUE_EVENTS:
                continue
            tokens = tuple(event.encoded for event in event_map.parsed.events[span.lo:span.hi])
            values.append(
                Value(
                    family="xml_path",
                    key=f"xml:{tag.decode('ascii')}:{ordinal}",
                    page=page,
                    span=span,
                    tokens=tokens,
                    raw=raw[value_start:value_end],
                )
            )
    return values


def select_rules(occurrences: list[Occurrence]) -> tuple[list[Occurrence], dict[str, dict[str, int]]]:
    grouped: dict[str, list[Occurrence]] = defaultdict(list)
    for occurrence in occurrences:
        grouped[occurrence.rule_key].append(occurrence)
    admitted: set[str] = set()
    summaries: dict[str, dict[str, int]] = {}
    for key, rows in grouped.items():
        pages = {row.page for row in rows}
        if len(rows) >= 3 and len(pages) >= 3:
            admitted.add(key)
            summaries[key] = {
                "occurrences": len(rows),
                "pages": len(pages),
                "structural_spans": sum(len(row.structural) for row in rows),
                "holes": sum(sum(span is not None for span in row.holes) for row in rows),
            }
    return [row for row in occurrences if row.rule_key in admitted], summaries


def values_for_rules(raw: bytes, event_map: EventMap, occurrences: list[Occurrence]) -> list[Value]:
    values: list[Value] = []
    for occurrence in occurrences:
        for hole_id, span in enumerate(occurrence.holes):
            if span is None or span.events < 1 or span.events > MAX_VALUE_EVENTS:
                continue
            start = int(event_map.raw_starts[span.lo])
            end = int(event_map.raw_ends[span.hi - 1])
            tokens = tuple(event.encoded for event in event_map.parsed.events[span.lo:span.hi])
            values.append(
                Value(
                    family=occurrence.family,
                    key=f"{occurrence.rule_key}:{hole_id}",
                    page=occurrence.page,
                    span=span,
                    tokens=tokens,
                    raw=raw[start:end],
                )
            )
    return values


def nonoverlap(blocks: list[tuple[int, int]]) -> list[tuple[int, int]]:
    chosen: list[tuple[int, int]] = []
    for start, size in sorted(blocks, key=lambda row: (-row[1], row[0])):
        end = start + size
        if any(start < old_end and old_start < end for old_start, old_end in chosen):
            continue
        chosen.append((start, end))
        if len(chosen) >= MAX_MOSAIC_PIECES:
            break
    return sorted(chosen)


def match_value(target: Value, sources: list[Value]) -> tuple[list[Span], str | None]:
    for source in reversed(sources):
        if target.tokens == source.tokens:
            return [target.span], "SAME"
    for source in reversed(sources):
        if (
            0 < len(target.raw) <= 32
            and len(target.raw) == len(source.raw)
            and target.raw.isdigit()
            and source.raw.isdigit()
        ):
            return [target.span], "DIGIT_DELTA"
        if (
            0 < len(target.raw) <= 1024
            and len(target.raw) == len(source.raw)
            and target.raw.lower() == source.raw.lower()
        ):
            return [target.span], "CASE_TRANSFORM"
    blocks: list[tuple[int, int]] = []
    for source in sources:
        matcher = difflib.SequenceMatcher(None, source.tokens, target.tokens, autojunk=False)
        blocks.extend(
            (block.b, block.size)
            for block in matcher.get_matching_blocks()
            if block.size >= MIN_MOSAIC_EVENTS
        )
    chosen = nonoverlap(blocks)
    if not chosen:
        return [], None
    return [Span(target.span.lo + start, target.span.lo + end) for start, end in chosen], "MOSAIC"


def shuffled_keys(values: list[Value]) -> dict[str, str]:
    counts = Counter(value.key for value in values)
    lengths: dict[str, list[int]] = defaultdict(list)
    families: dict[str, str] = {}
    for value in values:
        lengths[value.key].append(len(value.tokens))
        families[value.key] = value.family
    buckets: dict[tuple[str, int, int], list[str]] = defaultdict(list)
    for key in sorted(counts):
        median = sorted(lengths[key])[len(lengths[key]) // 2]
        buckets[(families[key], counts[key].bit_length(), max(1, median).bit_length())].append(key)
    mapping: dict[str, str] = {}
    for keys in buckets.values():
        if len(keys) == 1:
            mapping[keys[0]] = f"shuffled:none:{keys[0]}"
        else:
            for index, key in enumerate(keys):
                mapping[key] = keys[(index + 1) % len(keys)]
    return mapping


def score_values(
    values: list[Value], mode: str, key_map: dict[str, str] | None = None
) -> tuple[list[Span], dict[str, int]]:
    by_page: dict[int, list[Value]] = defaultdict(list)
    for value in values:
        by_page[value.page].append(value)
    history: dict[str, deque[Value]] = defaultdict(lambda: deque(maxlen=MAX_SOURCE_CANDIDATES))
    intervals: list[Span] = []
    commands: Counter[str] = Counter()
    for page in sorted(by_page):
        current = by_page[page]
        for value in current:
            if mode == "flat":
                source_key = f"flat:{max(1, len(value.tokens)).bit_length()}"
            elif key_map is not None:
                source_key = key_map[value.key]
            else:
                source_key = value.key
            matched, command = match_value(value, list(history[source_key]))
            intervals.extend(matched)
            if command is not None:
                commands[command] += 1
        for value in current:
            if mode == "flat":
                destination = f"flat:{max(1, len(value.tokens)).bit_length()}"
            else:
                destination = value.key
            history[destination].append(value)
    return intervals, dict(sorted(commands.items()))


def mask_for(count: int, intervals: Iterable[Span]) -> np.ndarray:
    delta = np.zeros(count + 1, dtype=np.int32)
    for span in intervals:
        if span.lo < span.hi:
            delta[span.lo] += 1
            delta[span.hi] -= 1
    return np.cumsum(delta[:-1]) > 0


def read_parent_qbits(parsed: ParsedStore, p1_path: Path) -> np.ndarray:
    rows = len(parsed.stream) * 8
    with p1_path.open("rb") as source:
        header = source.read(16)
    if len(header) != 16 or header[:8] not in P1_MAGICS:
        raise ValueError("invalid Endpoint428 P1 trace header")
    declared = struct.unpack_from("<Q", header, 8)[0]
    if declared != rows or p1_path.stat().st_size != 16 + 2 * rows:
        raise ValueError("Endpoint428 P1 trace rows differ from exact WRT stream")
    p1 = np.memmap(p1_path, mode="r", dtype="<u2", offset=16, shape=(rows,))
    truth = np.unpackbits(np.frombuffer(parsed.stream, dtype=np.uint8), bitorder="big")
    correct = np.where(truth == 1, p1.astype(np.uint32), 65_536 - p1.astype(np.uint32))
    if np.any(correct == 0):
        raise ValueError("Endpoint428 assigned zero probability to truth")
    qbits = np.rint(-np.log2(correct / 65_536.0) * 256.0).astype(np.int32)
    byte_qbits = qbits.reshape((-1, 8)).sum(axis=1, dtype=np.int64)
    prefix = np.empty(len(byte_qbits) + 1, dtype=np.int64)
    prefix[0] = 0
    np.cumsum(byte_qbits, out=prefix[1:])
    return np.fromiter(
        (prefix[event.end] - prefix[event.start] for event in parsed.events),
        dtype=np.int64,
        count=len(parsed.events),
    )


def summarize_arm(
    mask: np.ndarray,
    event_qbits: np.ndarray,
    event_map: EventMap,
    raw_bytes: int,
) -> dict[str, object]:
    boundaries = (raw_bytes // 3, 2 * raw_bytes // 3)
    split_rows = []
    for name, low, high in (
        ("development", 0, boundaries[0]),
        ("selection", boundaries[0], boundaries[1]),
        ("confirmation", boundaries[1], raw_bytes + 1),
    ):
        in_split = (event_map.raw_starts >= low) & (event_map.raw_starts < high)
        qbits = int(event_qbits[mask & in_split].sum())
        split_rows.append({"name": name, "displaced_qbits": qbits, "displaced_bytes": qbits / QBITS_PER_BYTE})
    total_qbits = int(event_qbits[mask].sum())
    return {
        "covered_events": int(mask.sum()),
        "displaced_qbits": total_qbits,
        "displaced_bytes": total_qbits / QBITS_PER_BYTE,
        "chronological_splits": split_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-input", type=Path, default=ROOT / "data/enwik9_10000000.bin")
    parser.add_argument("--wrt-store", type=Path, default=Path("/home/x/enwiki9-nonproof/results/fx2_order_original_10m.store"))
    parser.add_argument("--parent-p1", type=Path, default=Path("/home/x/enwiki9-nonproof/results/fx2_order_original_10m_p1.bin"))
    parser.add_argument("--dictionary", type=Path, default=ROOT / "external/fx2-cmix/dictionary/english.dic")
    parser.add_argument("--output", type=Path, default=ROOT / f"results/{CANDIDATE_ID}/decision.json")
    args = parser.parse_args()

    raw = args.raw_input.read_bytes()
    parsed = parse_store(args.wrt_store, args.dictionary)
    if parsed.decoded != raw:
        raise ValueError("exact WRT inverse differs from canonical raw input")
    event_map = EventMap(parsed)
    event_qbits = read_parent_qbits(parsed, args.parent_p1)
    pages = page_ranges(raw)
    template_parser = load_template_module()

    occurrences: list[Occurrence] = []
    for page, (start, end) in enumerate(pages):
        page_form = page_form_occurrence(raw, event_map, page, start, end)
        if page_form is not None:
            occurrences.append(page_form)
        occurrences.extend(local_occurrences(raw, event_map, template_parser, page, start, end))
    selected, rule_summaries = select_rules(occurrences)
    joint_values = values_for_rules(raw, event_map, selected)
    xml_values = ordinary_xml_values(raw, event_map, pages)

    form_intervals = [span for row in selected for span in row.structural]
    echo_intervals, echo_commands = score_values(joint_values, "slot")
    e0_intervals, e0_commands = score_values(xml_values, "slot")
    flat_intervals, flat_commands = score_values(joint_values, "flat")
    shuffle = shuffled_keys(joint_values)
    shuffled_intervals, shuffled_commands = score_values(joint_values, "slot", shuffle)

    event_count = len(parsed.events)
    form_mask = mask_for(event_count, form_intervals)
    echo_mask = mask_for(event_count, echo_intervals)
    e0_mask = mask_for(event_count, e0_intervals)
    flat_mask = mask_for(event_count, flat_intervals)
    shuffled_mask = mask_for(event_count, shuffled_intervals)
    masks = {
        "B0": np.zeros(event_count, dtype=np.bool_),
        "F0": form_mask,
        "E0": e0_mask,
        "C0": flat_mask,
        "S0": form_mask | shuffled_mask,
        "J0": form_mask | echo_mask,
    }
    arms = {name: summarize_arm(mask, event_qbits, event_map, len(raw)) for name, mask in masks.items()}
    controls = ("F0", "E0", "C0", "S0")
    margins = {name: arms["J0"]["displaced_bytes"] - arms[name]["displaced_bytes"] for name in controls}
    failed: list[str] = []
    if arms["J0"]["displaced_bytes"] < 100_000:
        failed.append("J0_ceiling_below_100000_bytes")
    for name, margin in margins.items():
        if margin < 20_000:
            failed.append(f"J0_margin_over_{name}_below_20000_bytes")
    if any(row["displaced_bytes"] <= 0 for row in arms["J0"]["chronological_splits"]):
        failed.append("J0_chronological_split_nonpositive")
    max_rule_pages = max((row["pages"] for row in rule_summaries.values()), default=0)
    if max_rule_pages < 3:
        failed.append("no_rule_spans_three_pages")

    top_rules = sorted(
        ({"rule_key": key, **row} for key, row in rule_summaries.items()),
        key=lambda row: (-row["occurrences"], -row["pages"], row["rule_key"]),
    )[:64]
    decision = {
        "schema": "fractal2_form_echo_joint_qm1_gate_minus1_v1",
        "candidate_id": CANDIDATE_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "zero_credit_exact_wrt_endpoint428_optimistic_candidate_universe_ceiling",
        "claim_boundary": "Rule selection and source identities are free. No commands, rule definitions, framing, decoder, or source package are serialized, so this is not a codec, archive gain, forecast, or prize result.",
        "inputs": {
            "raw": artifact(args.raw_input),
            "wrt_store": artifact(args.wrt_store),
            "parent_p1": artifact(args.parent_p1),
            "dictionary": artifact(args.dictionary),
        },
        "population": {
            "raw_bytes": len(raw),
            "wrt_stream_bytes": len(parsed.stream),
            "wrt_events": event_count,
            "complete_pages": len(pages),
            "candidate_occurrences": len(occurrences),
            "selected_occurrences": len(selected),
            "selected_rules": len(rule_summaries),
            "joint_slot_values": len(joint_values),
            "ordinary_xml_values": len(xml_values),
            "max_source_candidates": MAX_SOURCE_CANDIDATES,
            "max_mosaic_pieces": MAX_MOSAIC_PIECES,
            "max_value_events": MAX_VALUE_EVENTS,
        },
        "contracts": {
            "exact_wrt_inverse": True,
            "endpoint428_rows_match_wrt_truth": True,
            "sources_precede_completed_target_page": True,
            "event_boundary_alignment_required": True,
            "rule_minimum_distinct_pages": 3,
            "same_population_controls": True,
            "parent_prediction_update_trajectory_unchanged": True,
        },
        "commands": {
            "J0_ECHO": echo_commands,
            "E0_XML_PATH": e0_commands,
            "C0_FLAT": flat_commands,
            "S0_SHUFFLED": shuffled_commands,
        },
        "arms": arms,
        "J0_control_margins_bytes": margins,
        "top_rules": top_rules,
        "decision": {
            "failed_conditions": failed,
            "verdict": "authorize_fully_paid_10m_codec" if not failed else "retire_fractal2_qm1_realization",
            "promotion_authorized": not failed,
            "score_credit_bytes": 0,
            "next_action": "Build the counted B0/F0/E0/C0/S0/J0 codec with exact reconstruction." if not failed else "Preserve this terminal negative and mutate only through a materially different partition or source mechanism.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=False)
    temporary = args.output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(args.output)
    print(json.dumps({"output": str(args.output), "arms": {key: value["displaced_bytes"] for key, value in arms.items()}, "margins": margins, "verdict": decision["decision"]["verdict"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
