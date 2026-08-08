#!/usr/bin/env python3
"""Paid trace-level FRACTAL-2 QP1 command/residual codec and controls.

The container is constructive and exactly replayed, but it consumes a frozen
Endpoint428 P1 trace.  It therefore remains zero-credit until the same bypass
and state updates are integrated into the counted native parent codec.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
import difflib
import hashlib
import json
import lzma
from pathlib import Path
import struct
from typing import Iterable

import numpy as np

import fractal2_form_echo_joint_qm1 as qm1
import fractal2_recursive_punct_forest_qm2 as qm2
import paid_block_vector_codebook as payload_codec
from janus_paid_residual_mdl_oracle import range_decode
from wrt_exact import parse_store, parse_store_bytes, read_dictionary_words


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fractal2_endpoint428_paid_mdl_qp1_v1"
TRACE_RECEIPT = ROOT / "results/fractal2_endpoint428_trace_10m_v1/decision.json"
QM3_DECISION = ROOT / "results/fractal2_endpoint428_recursive_punct_qm3_v1/decision.json"
P1_MAGIC = b"CMX21P1\0"
CONTAINER_MAGIC = b"F2QP1\0\0\0"
SIDE_MAGIC = b"F2SIDE1\0"
QBITS_PER_BYTE = 2048
FORM_INVOCATION_COST = 6
MAX_SOURCES = 8
MAX_PIECES = 4
MIN_COPY_EVENTS = 3


@dataclass(frozen=True, slots=True)
class Command:
    kind: str
    target_start: int
    target_end: int
    benefit_qbits: int
    raw_position: int
    phrase: bytes | None = None
    source_start: int | None = None
    family: str = ""

    @property
    def length(self) -> int:
        return self.target_end - self.target_start


def varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint value must be nonnegative")
    output = bytearray()
    while value >= 128:
        output.append((value & 127) | 128)
        value >>= 7
    output.append(value)
    return bytes(output)


def read_varint(data: bytes, position: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if position >= len(data) or shift > 63:
            raise ValueError("truncated or invalid varint")
        byte = data[position]
        position += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, position
        shift += 7


def vlen(value: int) -> int:
    return len(varint(value))


def span_bytes(parsed, span: qm1.Span) -> tuple[int, int, bytes]:
    start = parsed.events[span.lo].start
    end = parsed.events[span.hi - 1].end
    return start, end, parsed.stream[start:end]


def span_qbits(prefix: np.ndarray, span: qm1.Span) -> int:
    return int(prefix[span.hi] - prefix[span.lo])


def build_universe(raw: bytes, event_map: qm1.EventMap):
    pages = qm1.page_ranges(raw)
    template_parser = qm1.load_template_module()
    occurrences: list[qm1.Occurrence] = []
    for page, (start, end) in enumerate(pages):
        page_form = qm1.page_form_occurrence(raw, event_map, page, start, end)
        if page_form is not None:
            occurrences.append(page_form)
        occurrences.extend(
            qm1.local_occurrences(raw, event_map, template_parser, page, start, end)
        )
        occurrences.extend(qm2.recursive_occurrences(raw, event_map, page, start, end))
    selected, summaries = qm1.select_rules(occurrences)
    return pages, selected, summaries


def form_candidates(
    parsed,
    event_map: qm1.EventMap,
    event_prefix: np.ndarray,
    occurrences: list[qm1.Occurrence],
) -> tuple[list[Command], dict[str, object]]:
    groups: dict[bytes, dict[tuple[int, int], Command]] = defaultdict(dict)
    pages_by_phrase: dict[bytes, set[int]] = defaultdict(set)
    for occurrence in occurrences:
        for span in occurrence.structural:
            start, end, phrase = span_bytes(parsed, span)
            command = Command(
                kind="rule",
                target_start=start,
                target_end=end,
                benefit_qbits=span_qbits(event_prefix, span),
                raw_position=int(event_map.raw_starts[span.lo]),
                phrase=phrase,
                family=occurrence.family,
            )
            key = (start, end)
            old = groups[phrase].get(key)
            if old is None or command.benefit_qbits > old.benefit_qbits:
                groups[phrase][key] = command
            pages_by_phrase[phrase].add(occurrence.page)

    admitted: list[Command] = []
    admitted_phrases = 0
    rejected_phrases = 0
    for phrase in sorted(groups, key=lambda value: (len(value), value)):
        rows = sorted(groups[phrase].values(), key=lambda row: row.target_start)
        if len(pages_by_phrase[phrase]) < 3:
            rejected_phrases += 1
            continue
        benefit = sum(row.benefit_qbits for row in rows) / QBITS_PER_BYTE
        definition_cost = vlen(len(phrase)) + len(phrase)
        invocation_cost = FORM_INVOCATION_COST * len(rows)
        if benefit <= definition_cost + invocation_cost:
            rejected_phrases += 1
            continue
        admitted_phrases += 1
        admitted.extend(rows)
    return admitted, {
        "candidate_phrases": len(groups),
        "admitted_phrases": admitted_phrases,
        "rejected_phrases": rejected_phrases,
        "admitted_invocations": len(admitted),
        "frozen_universal_invocation_cost_bytes": FORM_INVOCATION_COST,
    }


def value_source_key(value: qm1.Value, mode: str, key_map: dict[str, str] | None) -> str:
    if mode == "flat":
        return f"flat:{max(1, len(value.tokens)).bit_length()}"
    if key_map is not None:
        return key_map[value.key]
    return value.key


def value_destination_key(value: qm1.Value, mode: str) -> str:
    if mode == "flat":
        return f"flat:{max(1, len(value.tokens)).bit_length()}"
    return value.key


def copy_command(
    parsed,
    event_map: qm1.EventMap,
    event_prefix: np.ndarray,
    target: qm1.Span,
    source: qm1.Span,
    family: str,
) -> Command | None:
    target_start, target_end, target_bytes = span_bytes(parsed, target)
    source_start, source_end, source_bytes = span_bytes(parsed, source)
    if target_bytes != source_bytes:
        raise ValueError("ECHO source differs from target event bytes")
    if source_end > target_start:
        raise ValueError("ECHO source is not causally complete")
    benefit = span_qbits(event_prefix, target)
    cost = 1 + vlen(target_end - target_start) + vlen(target_start - source_start) + 4
    if benefit / QBITS_PER_BYTE <= cost:
        return None
    return Command(
        kind="copy",
        target_start=target_start,
        target_end=target_end,
        benefit_qbits=benefit,
        raw_position=int(event_map.raw_starts[target.lo]),
        source_start=source_start,
        family=family,
    )


def matched_copy_commands(
    parsed,
    event_map: qm1.EventMap,
    event_prefix: np.ndarray,
    target: qm1.Value,
    sources: list[qm1.Value],
) -> list[Command]:
    for source in reversed(sources):
        if target.tokens == source.tokens:
            command = copy_command(
                parsed, event_map, event_prefix, target.span, source.span, target.family
            )
            return [command] if command is not None else []
    blocks: list[tuple[int, int, qm1.Value, int]] = []
    for source in sources:
        matcher = difflib.SequenceMatcher(None, source.tokens, target.tokens, autojunk=False)
        for block in matcher.get_matching_blocks():
            if block.size >= MIN_COPY_EVENTS:
                blocks.append((block.b, block.size, source, block.a))
    chosen: list[tuple[int, int, qm1.Value, int]] = []
    for target_at, size, source, source_at in sorted(
        blocks, key=lambda row: (-row[1], row[0], row[2].span.lo, row[3])
    ):
        target_end = target_at + size
        if any(target_at < old_at + old_size and old_at < target_end for old_at, old_size, _old_source, _old_source_at in chosen):
            continue
        chosen.append((target_at, size, source, source_at))
        if len(chosen) >= MAX_PIECES:
            break
    output: list[Command] = []
    for target_at, size, source, source_at in sorted(chosen):
        command = copy_command(
            parsed,
            event_map,
            event_prefix,
            qm1.Span(target.span.lo + target_at, target.span.lo + target_at + size),
            qm1.Span(source.span.lo + source_at, source.span.lo + source_at + size),
            target.family,
        )
        if command is not None:
            output.append(command)
    return output


def echo_candidates(
    parsed,
    event_map: qm1.EventMap,
    event_prefix: np.ndarray,
    values: list[qm1.Value],
    mode: str,
    key_map: dict[str, str] | None = None,
) -> tuple[list[Command], dict[str, int]]:
    by_page: dict[int, list[qm1.Value]] = defaultdict(list)
    for value in values:
        by_page[value.page].append(value)
    history: dict[str, deque[qm1.Value]] = defaultdict(lambda: deque(maxlen=MAX_SOURCES))
    commands: list[Command] = []
    counts: Counter[str] = Counter()
    for page in sorted(by_page):
        current = by_page[page]
        for value in current:
            source_key = value_source_key(value, mode, key_map)
            matched = matched_copy_commands(
                parsed, event_map, event_prefix, value, list(history[source_key])
            )
            commands.extend(matched)
            if matched:
                counts["SAME_or_MOSAIC_values"] += 1
                counts["copy_blocks"] += len(matched)
        for value in current:
            history[value_destination_key(value, mode)].append(value)
    counts["paying_copy_blocks"] = len(commands)
    return commands, dict(sorted(counts.items()))


def estimated_command_cost(command: Command) -> int:
    if command.kind == "rule":
        return FORM_INVOCATION_COST
    assert command.source_start is not None
    return 1 + vlen(command.length) + vlen(command.target_start - command.source_start) + 4


def select_nonoverlap(stream_bytes: int, commands: Iterable[Command]) -> list[Command]:
    occupied = np.zeros(stream_bytes, dtype=np.bool_)
    selected: list[Command] = []
    ranked = sorted(
        commands,
        key=lambda row: (
            -(row.benefit_qbits / QBITS_PER_BYTE - estimated_command_cost(row)),
            -row.length,
            row.target_start,
            row.kind,
        ),
    )
    for command in ranked:
        if np.any(occupied[command.target_start:command.target_end]):
            continue
        occupied[command.target_start:command.target_end] = True
        selected.append(command)
    return sorted(selected, key=lambda row: (row.target_start, row.target_end, row.kind))


def serialize_side(wrt_bytes: int, commands: list[Command]) -> tuple[bytes, bytes, list[bytes]]:
    phrases = sorted(
        {command.phrase for command in commands if command.kind == "rule" and command.phrase is not None},
        key=lambda value: (len(value), value),
    )
    phrase_ids = {phrase: index for index, phrase in enumerate(phrases)}
    raw = bytearray(SIDE_MAGIC)
    raw.extend(varint(wrt_bytes))
    raw.extend(varint(len(phrases)))
    for phrase in phrases:
        raw.extend(varint(len(phrase)))
        raw.extend(phrase)
    raw.extend(varint(len(commands)))
    previous_end = 0
    for command in commands:
        if command.target_start < previous_end:
            raise ValueError("overlapping paid commands")
        raw.extend(varint(command.target_start - previous_end))
        raw.extend(varint(command.length))
        if command.kind == "rule":
            raw.append(0)
            assert command.phrase is not None
            raw.extend(varint(phrase_ids[command.phrase]))
        elif command.kind == "copy":
            raw.append(1)
            assert command.source_start is not None
            raw.extend(varint(command.target_start - command.source_start))
        else:
            raise ValueError(f"unknown command kind: {command.kind}")
        previous_end = command.target_end
    raw_bytes = bytes(raw)
    compressed = lzma.compress(raw_bytes, preset=9 | lzma.PRESET_EXTREME)
    return raw_bytes, compressed, phrases


def parse_side(compressed: bytes) -> tuple[int, list[bytes], list[tuple[str, int, int, int]]]:
    data = lzma.decompress(compressed)
    if not data.startswith(SIDE_MAGIC):
        raise ValueError("invalid FRACTAL-2 side stream")
    position = len(SIDE_MAGIC)
    wrt_bytes, position = read_varint(data, position)
    rule_count, position = read_varint(data, position)
    phrases: list[bytes] = []
    for _ in range(rule_count):
        length, position = read_varint(data, position)
        end = position + length
        if end > len(data):
            raise ValueError("truncated FORM definition")
        phrases.append(data[position:end])
        position = end
    command_count, position = read_varint(data, position)
    commands: list[tuple[str, int, int, int]] = []
    previous_end = 0
    for _ in range(command_count):
        gap, position = read_varint(data, position)
        length, position = read_varint(data, position)
        if position >= len(data):
            raise ValueError("truncated command opcode")
        opcode = data[position]
        position += 1
        argument, position = read_varint(data, position)
        start = previous_end + gap
        end = start + length
        commands.append(("rule" if opcode == 0 else "copy", start, end, argument))
        previous_end = end
    if position != len(data):
        raise ValueError("trailing paid side-stream bytes")
    return wrt_bytes, phrases, commands


def command_mask(wrt_bytes: int, commands: list[Command]) -> np.ndarray:
    mask = np.zeros(wrt_bytes, dtype=np.bool_)
    for command in commands:
        mask[command.target_start:command.target_end] = True
    return mask


def encode_container(
    truth: np.ndarray,
    probabilities: np.ndarray,
    commands: list[Command],
) -> tuple[bytes, bytes, bytes]:
    wrt_bytes = len(truth) // 8
    mask = command_mask(wrt_bytes, commands)
    residual_bits = ~np.repeat(mask, 8)
    residual = payload_codec.encode_payload(probabilities[residual_bits], truth[residual_bits])
    _side_raw, side, _phrases = serialize_side(wrt_bytes, commands)
    header = CONTAINER_MAGIC + struct.pack("<QQ", len(residual), len(side))
    return header + residual + side, residual, side


def decode_container(container: bytes, probabilities: np.ndarray) -> bytes:
    if len(container) < 24 or container[:8] != CONTAINER_MAGIC:
        raise ValueError("invalid FRACTAL-2 container")
    residual_bytes, side_bytes = struct.unpack_from("<QQ", container, 8)
    if 24 + residual_bytes + side_bytes != len(container):
        raise ValueError("FRACTAL-2 container length mismatch")
    residual = container[24 : 24 + residual_bytes]
    side = container[24 + residual_bytes :]
    wrt_bytes, phrases, commands = parse_side(side)
    mask = np.zeros(wrt_bytes, dtype=np.bool_)
    for _kind, start, end, _argument in commands:
        mask[start:end] = True
    residual_bit_mask = ~np.repeat(mask, 8)
    residual_truth = range_decode(residual, probabilities[residual_bit_mask])
    residual_stream = np.packbits(residual_truth, bitorder="big").tobytes()
    residual_at = 0
    output = bytearray()
    cursor = 0
    for kind, start, end, argument in commands:
        gap = start - cursor
        output.extend(residual_stream[residual_at : residual_at + gap])
        residual_at += gap
        length = end - start
        if kind == "rule":
            if argument >= len(phrases) or len(phrases[argument]) != length:
                raise ValueError("invalid FORM replay")
            output.extend(phrases[argument])
        elif kind == "copy":
            source = start - argument
            if source < 0 or source + length > len(output):
                raise ValueError("invalid causal ECHO replay")
            output.extend(output[source : source + length])
        else:
            raise ValueError("unknown replay command")
        cursor = end
    tail = wrt_bytes - cursor
    output.extend(residual_stream[residual_at : residual_at + tail])
    residual_at += tail
    if residual_at != len(residual_stream) or len(output) != wrt_bytes:
        raise ValueError("residual replay did not consume exact stream")
    return bytes(output)


def source_package() -> tuple[bytes, list[str]]:
    paths = [
        Path(__file__).resolve(),
        ROOT / "tools/fractal2_form_echo_joint_qm1.py",
        ROOT / "tools/fractal2_recursive_punct_forest_qm2.py",
        ROOT / "tools/fractal2_endpoint428_recursive_punct_qm3.py",
        ROOT / "tools/wrt_exact.py",
        ROOT / "tools/paid_block_vector_codebook.py",
        ROOT / "tools/janus_paid_residual_mdl_oracle.py",
        ROOT / "programs/wikiir_template_grammar_v1/program.py",
    ]
    bundle = bytearray()
    names: list[str] = []
    for path in paths:
        name = str(path.relative_to(ROOT))
        data = path.read_bytes()
        names.append(name)
        encoded_name = name.encode("ascii")
        bundle.extend(varint(len(encoded_name)))
        bundle.extend(encoded_name)
        bundle.extend(varint(len(data)))
        bundle.extend(data)
    return lzma.compress(bytes(bundle), preset=9 | lzma.PRESET_EXTREME), names


def arm_metrics(
    name: str,
    parent_archive_bytes: int,
    container: bytes,
    residual: bytes,
    side: bytes,
    commands: list[Command],
    source_bytes: int,
    raw_bytes: int,
) -> dict[str, object]:
    gross_qbits = sum(command.benefit_qbits for command in commands)
    split_qbits = [0, 0, 0]
    for command in commands:
        split = min(2, command.raw_position * 3 // raw_bytes)
        split_qbits[split] += command.benefit_qbits
    archive_gain = parent_archive_bytes - len(container)
    return {
        "name": name,
        "commands": len(commands),
        "rule_commands": sum(command.kind == "rule" for command in commands),
        "copy_commands": sum(command.kind == "copy" for command in commands),
        "gross_displaced_qbits": gross_qbits,
        "gross_displaced_bytes": gross_qbits / QBITS_PER_BYTE,
        "chronological_displaced_bytes": [value / QBITS_PER_BYTE for value in split_qbits],
        "residual_payload_bytes": len(residual),
        "side_payload_bytes": len(side),
        "container_bytes": len(container),
        "archive_gain_bytes": archive_gain,
        "source_package_bytes": source_bytes,
        "net_gain_after_source_bytes": archive_gain - source_bytes,
        "side_fraction_of_displaced": len(side) / max(1.0, gross_qbits / QBITS_PER_BYTE),
        "container_sha256": hashlib.sha256(container).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-input", type=Path, default=ROOT / "data/enwik9_10000000.bin")
    parser.add_argument("--wrt-store", type=Path, default=Path("/home/x/enwiki9-nonproof/results/fx2_order_original_10m.store"))
    parser.add_argument("--dictionary", type=Path, default=ROOT / "external/fx2-cmix/dictionary/english.dic")
    parser.add_argument("--parent-p1", type=Path, default=ROOT / "results/fractal2_endpoint428_trace_10m_v1/endpoint428.p1")
    parser.add_argument("--parent-archive", type=Path, default=ROOT / "results/fractal2_endpoint428_trace_10m_v1/archive.bin")
    parser.add_argument("--output-dir", type=Path, default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()

    raw = args.raw_input.read_bytes()
    parsed = parse_store(args.wrt_store, args.dictionary)
    if parsed.decoded != raw:
        raise ValueError("WRT store does not invert to canonical raw input")
    event_map = qm1.EventMap(parsed)
    event_qbits = qm1.read_parent_qbits(parsed, args.parent_p1)
    event_prefix = np.empty(len(event_qbits) + 1, dtype=np.int64)
    event_prefix[0] = 0
    np.cumsum(event_qbits, out=event_prefix[1:])
    pages, occurrences, rule_summaries = build_universe(raw, event_map)
    values = qm1.values_for_rules(raw, event_map, occurrences)
    xml_values = qm1.ordinary_xml_values(raw, event_map, pages)

    form, form_stats = form_candidates(parsed, event_map, event_prefix, occurrences)
    joint_echo, joint_stats = echo_candidates(parsed, event_map, event_prefix, values, "slot")
    e0_echo, e0_stats = echo_candidates(parsed, event_map, event_prefix, xml_values, "slot")
    flat_echo, flat_stats = echo_candidates(parsed, event_map, event_prefix, values, "flat")
    shuffled_echo, shuffled_stats = echo_candidates(
        parsed, event_map, event_prefix, values, "slot", qm1.shuffled_keys(values)
    )
    arm_commands = {
        "F0": select_nonoverlap(len(parsed.stream), form),
        "E0": select_nonoverlap(len(parsed.stream), e0_echo),
        "C0": select_nonoverlap(len(parsed.stream), flat_echo),
        "S0": select_nonoverlap(len(parsed.stream), [*form, *shuffled_echo]),
        "J0": select_nonoverlap(len(parsed.stream), [*form, *joint_echo]),
    }

    with args.parent_p1.open("rb") as source:
        p1_header = source.read(16)
    rows = len(parsed.stream) * 8
    if len(p1_header) != 16 or p1_header[:8] != P1_MAGIC or struct.unpack_from("<Q", p1_header, 8)[0] != rows:
        raise ValueError("invalid receipt-bound Endpoint428 P1 trace")
    probabilities = np.memmap(args.parent_p1, mode="r", dtype="<u2", offset=16, shape=(rows,))
    truth = np.unpackbits(np.frombuffer(parsed.stream, dtype=np.uint8), bitorder="big")
    parent_payload, parent_header_bytes, declared_wrt = payload_codec.read_archive(args.parent_archive)
    if declared_wrt != len(parsed.stream):
        raise ValueError("parent archive WRT declaration mismatch")
    baseline_replay = payload_codec.encode_payload(probabilities, truth)
    if baseline_replay != parent_payload:
        raise ValueError("receipt-bound Endpoint428 trace does not replay parent payload")

    package, package_files = source_package()
    encoded: dict[str, tuple[bytes, bytes, bytes]] = {}
    metrics: dict[str, dict[str, object]] = {}
    for name in ("F0", "E0", "C0", "S0", "J0"):
        encoded[name] = encode_container(truth, probabilities, arm_commands[name])
        metrics[name] = arm_metrics(
            name,
            args.parent_archive.stat().st_size,
            *encoded[name],
            arm_commands[name],
            len(package),
            len(raw),
        )

    j_container, _j_residual, _j_side = encoded["J0"]
    second_container, _second_residual, _second_side = encode_container(
        truth, probabilities, arm_commands["J0"]
    )
    deterministic = second_container == j_container
    reconstructed_stream = decode_container(j_container, probabilities)
    stream_exact = reconstructed_stream == parsed.stream
    reconstructed = parse_store_bytes(
        reconstructed_stream, read_dictionary_words(args.dictionary)
    ).decoded
    raw_exact = reconstructed == raw

    failed: list[str] = []
    if metrics["J0"]["net_gain_after_source_bytes"] < 60_000:
        failed.append("J0_paid_net_below_60000_bytes")
    if metrics["J0"]["side_fraction_of_displaced"] > 0.40:
        failed.append("J0_rule_and_command_fraction_above_40_percent")
    if any(value <= 0 for value in metrics["J0"]["chronological_displaced_bytes"]):
        failed.append("J0_chronological_split_nonpositive")
    for control in ("F0", "E0", "C0", "S0"):
        if metrics["J0"]["container_bytes"] >= metrics[control]["container_bytes"]:
            failed.append(f"J0_does_not_beat_{control}_paid_container")
    if not stream_exact or not raw_exact:
        failed.append("exact_replay_failed")
    if not deterministic:
        failed.append("deterministic_second_archive_failed")

    args.output_dir.mkdir(parents=True, exist_ok=False)
    archive_path = args.output_dir / "archive.bin"
    second_path = args.output_dir / "archive_second.bin"
    package_path = args.output_dir / "source_package.lzma"
    archive_path.write_bytes(j_container)
    second_path.write_bytes(second_container)
    package_path.write_bytes(package)
    decision = {
        "schema": "fractal2_endpoint428_paid_mdl_qp1_decision_v1",
        "candidate_id": CANDIDATE_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "zero_credit_constructive_paid_external_p1_trace_codec",
        "claim_boundary": "The command container, residual arithmetic, WRT replay, raw inverse, controls, and source bundle are constructive and paid. Decoding still consumes the external 100MB Endpoint428 P1 trace and Python/numpy runtime, so this is not self-contained, native, eligible, or score-bearing.",
        "inputs": {
            "raw": qm1.artifact(args.raw_input),
            "wrt_store": qm1.artifact(args.wrt_store),
            "dictionary": qm1.artifact(args.dictionary),
            "parent_p1": qm1.artifact(args.parent_p1),
            "parent_archive": qm1.artifact(args.parent_archive),
            "trace_receipt": qm1.artifact(TRACE_RECEIPT),
            "qm3_decision": qm1.artifact(QM3_DECISION),
        },
        "population": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(parsed.stream),
            "wrt_events": len(parsed.events),
            "complete_pages": len(pages),
            "selected_free_rules": len(rule_summaries),
            "slot_values": len(values),
        },
        "selection": {
            "form": form_stats,
            "J0_ECHO": joint_stats,
            "E0_XML": e0_stats,
            "C0_FLAT": flat_stats,
            "S0_SHUFFLED": shuffled_stats,
            "minimum_copy_events": MIN_COPY_EVENTS,
            "maximum_source_candidates": MAX_SOURCES,
            "maximum_mosaic_pieces": MAX_PIECES,
            "no_post_measurement_threshold_sweep": True,
        },
        "parent_identity": {
            "archive_header_bytes": parent_header_bytes,
            "payload_bytes": len(parent_payload),
            "payload_sha256": hashlib.sha256(parent_payload).hexdigest(),
            "trace_replay_identity": True,
        },
        "source_accounting": {
            "package_bytes": len(package),
            "package_sha256": hashlib.sha256(package).hexdigest(),
            "files": package_files,
            "python_runtime_counted": False,
            "numpy_runtime_counted": False,
        },
        "arms": metrics,
        "proof": {
            "wrt_stream_exact": stream_exact,
            "raw_inverse_exact": raw_exact,
            "deterministic_second_archive": deterministic,
            "archive_sha256": hashlib.sha256(j_container).hexdigest(),
            "second_archive_sha256": hashlib.sha256(second_container).hexdigest(),
        },
        "artifacts": {
            "archive": qm1.artifact(archive_path),
            "archive_second": qm1.artifact(second_path),
            "source_package": qm1.artifact(package_path),
        },
        "decision": {
            "failed_conditions": failed,
            "verdict": "authorize_native_endpoint428_integration" if not failed else "retire_fractal2_endpoint428_paid_mdl_qp1",
            "promotion_authorized": not failed,
            "score_credit_bytes": 0,
            "next_action": "Integrate identical command replay and predictor updates into the counted Endpoint428 source." if not failed else "Preserve the paid negative and require a materially different compiled signaling mechanism or representation.",
        },
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(decision_path),
        "arms": {name: {"container_bytes": row["container_bytes"], "net_gain_after_source_bytes": row["net_gain_after_source_bytes"]} for name, row in metrics.items()},
        "proof": decision["proof"],
        "verdict": decision["decision"]["verdict"],
        "failed_conditions": failed,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
