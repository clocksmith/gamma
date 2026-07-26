#!/usr/bin/env python3
"""Exact ARIADNE-0 coarse-anchor ordering experiment.

This is a constructive research harness, not an official Hutter package.  It
partitions an exact WRT store into opaque emission groups, writes independently
decodable arithmetic archives for R/O0/O1, and restores the original store
before WRT inversion.  O0 pays the same segment graph as O1 but preserves
segment order.  O1 emits anchor segments before body segments.
"""

from __future__ import annotations

import argparse
import bisect
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import lzma
import math
from pathlib import Path
import re
from typing import Iterable

from streaming_retrieval_codec import ArithmeticDecoder, ArithmeticEncoder
from fx2_shadow_residual_coder import TOTAL, clamp_p1
from wrt_exact import (
    CAPITALIZED,
    END_UPPER,
    ESCAPE,
    UPPERCASE,
    parse_store,
    wrt_byte_transform,
)


MAGIC = b"ARIADNE0\x00"
MODE_R = 0
MODE_O0 = 1
MODE_O1 = 2
MODE_NAMES = {MODE_R: "R", MODE_O0: "O0", MODE_O1: "O1"}
LABELS = {"body": 0, "title": 1, "heading": 2, "infobox": 3, "category": 4}
LABEL_NAMES = {value: key for key, value in LABELS.items()}
SPLITS = {0: "train", 1: "train", 2: "train", 3: "development", 4: "holdout"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def put_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("negative varint")
    out = bytearray()
    while value >= 128:
        out.append((value & 127) | 128)
        value >>= 7
    out.append(value)
    return bytes(out)


def get_varint(data: bytes, position: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if position >= len(data) or shift > 63:
            raise ValueError("invalid varint")
        byte = data[position]
        position += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, position
        shift += 7


@dataclass(frozen=True)
class EmissionGroup:
    encoded: bytes
    decoded: bytes
    lexical: bool


@dataclass(frozen=True)
class Segment:
    original_index: int
    label: str
    groups: tuple[EmissionGroup, ...]

    @property
    def anchor(self) -> bool:
        return self.label != "body"

    @property
    def byte_length(self) -> int:
        return sum(len(group.encoded) for group in self.groups)


@dataclass(frozen=True)
class Record:
    page_ordinal: int | None
    segments: tuple[Segment, ...]

    @property
    def groups(self) -> tuple[EmissionGroup, ...]:
        return tuple(group for segment in self.segments for group in segment.groups)

    @property
    def byte_length(self) -> int:
        return sum(segment.byte_length for segment in self.segments)


class Ppm:
    """Bounded bitwise forward PPM over completed bytes and the byte prefix."""

    def __init__(self, order: int = 4, cap: int = 250_000) -> None:
        self.order = order
        self.cap = cap
        self.tables: list[dict[tuple[bytes, int, int], list[int]]] = [
            {} for _ in range(order + 1)
        ]
        self.history = bytearray()

    def keys(self, bit_pos: int, prefix: int) -> list[tuple[bytes, int, int]]:
        return [
            (bytes(self.history[-order:]) if order else b"", bit_pos, prefix)
            for order in range(self.order + 1)
        ]

    def predict(self, bit_pos: int, prefix: int) -> tuple[int, list[tuple[bytes, int, int]]]:
        keys = self.keys(bit_pos, prefix)
        for order in range(self.order, -1, -1):
            counts = self.tables[order].get(keys[order])
            if counts is not None and counts[0] + counts[1] >= 2:
                return clamp_p1(((counts[1] + 1) * TOTAL) // (sum(counts) + 2)), keys
        return TOTAL // 2, keys

    def update(self, keys: list[tuple[bytes, int, int]], bit: int) -> None:
        for order, key in enumerate(keys):
            table = self.tables[order]
            counts = table.get(key)
            if counts is None:
                if len(table) >= max(1, self.cap // (self.order + 1)):
                    continue
                counts = [0, 0]
                table[key] = counts
            counts[bit] += 1
            if counts[0] + counts[1] >= 1024:
                counts[0] = (counts[0] + 1) >> 1
                counts[1] = (counts[1] + 1) >> 1

    def complete_byte(self, value: int) -> None:
        self.history.append(value)
        if len(self.history) > self.order:
            del self.history[: len(self.history) - self.order]


def anchor_probability(counter: Counter[bytes], prefix: int, prefix_len: int) -> int | None:
    zeros = 0
    ones = 0
    for event, multiplicity in counter.items():
        event_bits = len(event) * 8
        if event_bits <= prefix_len:
            continue
        value = int.from_bytes(event, "big")
        if prefix_len and value >> (event_bits - prefix_len) != prefix:
            continue
        next_bit = (value >> (event_bits - prefix_len - 1)) & 1
        if next_bit:
            ones += multiplicity
        else:
            zeros += multiplicity
    if not zeros and not ones:
        return None
    return clamp_p1(((ones + 1) * TOTAL) // (zeros + ones + 2))


def blended_probability(base: int, anchor: int | None, blend_ppm: int) -> int:
    if anchor is None or blend_ppm <= 0:
        return base
    return clamp_p1(((1_000_000 - blend_ppm) * base + blend_ppm * anchor) // 1_000_000)


def event_length_from_first(stored_byte: int) -> int:
    first = wrt_byte_transform(stored_byte)
    if first == ESCAPE:
        return 2
    if first <= 0xCF:
        return 1
    return 2  # The second decoded code byte determines whether a third follows.


def event_needs_third(first_stored: int, second_stored: int) -> bool:
    return wrt_byte_transform(first_stored) > 0xCF and wrt_byte_transform(second_stored) > 0xCF


def group_is_lexical(encoded: bytes) -> bool:
    """Classify the sole output-producing event after any control prefix."""
    position = 0
    while position < len(encoded):
        first = wrt_byte_transform(encoded[position])
        if first in (UPPERCASE, END_UPPER, CAPITALIZED):
            position += 1
            continue
        if first == ESCAPE:
            if position + 1 >= len(encoded):
                return False
            value = wrt_byte_transform(encoded[position + 1])
            return ord("A") <= value <= ord("Z") or ord("a") <= value <= ord("z")
        if first >= 0x80:
            return True
        return ord("A") <= first <= ord("Z") or ord("a") <= first <= ord("z")
    return False


def encode_event(
    encoder: ArithmeticEncoder,
    model: Ppm,
    event: bytes,
    anchor_counter: Counter[bytes] | None,
    use_anchor: bool,
    blend_ppm: int,
) -> float:
    loss = 0.0
    event_prefix = 0
    event_prefix_len = 0
    for value in event:
        byte_prefix = 0
        for bit_pos in range(8):
            base, keys = model.predict(bit_pos, byte_prefix)
            prior = (
                anchor_probability(anchor_counter, event_prefix, event_prefix_len)
                if use_anchor and anchor_counter
                else None
            )
            probability = blended_probability(base, prior, blend_ppm)
            bit = (value >> (7 - bit_pos)) & 1
            encoder.encode(bit, probability)
            model.update(keys, bit)
            byte_prefix = (byte_prefix << 1) | bit
            event_prefix = (event_prefix << 1) | bit
            event_prefix_len += 1
            p = probability / TOTAL if bit else (TOTAL - probability) / TOTAL
            loss -= math.log2(p)
        model.complete_byte(value)
    return loss


def encode_raw(encoder: ArithmeticEncoder, model: Ppm, data: bytes) -> float:
    return encode_event(encoder, model, data, None, False, 0)


def decode_byte(
    decoder: ArithmeticDecoder,
    model: Ppm,
    anchor_counter: Counter[bytes] | None,
    use_anchor: bool,
    blend_ppm: int,
    event_prefix: int,
    event_prefix_len: int,
) -> tuple[int, int, int]:
    value = 0
    for bit_pos in range(8):
        base, keys = model.predict(bit_pos, value)
        prior = (
            anchor_probability(anchor_counter, event_prefix, event_prefix_len)
            if use_anchor and anchor_counter
            else None
        )
        probability = blended_probability(base, prior, blend_ppm)
        bit = decoder.decode(probability)
        model.update(keys, bit)
        value = (value << 1) | bit
        event_prefix = (event_prefix << 1) | bit
        event_prefix_len += 1
    model.complete_byte(value)
    return value, event_prefix, event_prefix_len


def decode_raw(decoder: ArithmeticDecoder, model: Ppm, byte_length: int) -> bytes:
    out = bytearray()
    for _ in range(byte_length):
        value, _prefix, _length = decode_byte(decoder, model, None, False, 0, 0, 0)
        out.append(value)
    return bytes(out)


def decode_segment(
    decoder: ArithmeticDecoder,
    model: Ppm,
    group_count: int,
    byte_length: int,
    anchor: bool,
    anchor_counter: Counter[bytes],
    blend_ppm: int,
) -> bytes:
    out = bytearray()
    for _ in range(group_count):
        group = bytearray()
        group_prefix = 0
        group_prefix_len = 0
        while True:
            event = bytearray()
            first, group_prefix, group_prefix_len = decode_byte(
                decoder,
                model,
                anchor_counter,
                not anchor,
                blend_ppm,
                group_prefix,
                group_prefix_len,
            )
            event.append(first)
            needed = event_length_from_first(first)
            while len(event) < needed:
                value, group_prefix, group_prefix_len = decode_byte(
                    decoder,
                    model,
                    anchor_counter,
                    not anchor,
                    blend_ppm,
                    group_prefix,
                    group_prefix_len,
                )
                event.append(value)
                if len(event) == 2 and event_needs_third(event[0], event[1]):
                    needed = 3
            group.extend(event)
            if wrt_byte_transform(first) not in (UPPERCASE, END_UPPER, CAPITALIZED):
                break
        encoded_group = bytes(group)
        if anchor and group_is_lexical(encoded_group):
            anchor_counter[encoded_group] += 1
        out.extend(encoded_group)
    if len(out) != byte_length:
        raise ValueError("decoded segment length disagrees with descriptor")
    return bytes(out)


def infobox_span(page: bytes) -> tuple[int, int] | None:
    text_start = page.find(b"<text")
    if text_start < 0:
        return None
    text_start = page.find(b">", text_start)
    text_end = page.rfind(b"</text>")
    if text_start < 0 or text_end < 0:
        return None
    position = text_start + 1
    depth = 0
    while position + 1 < text_end:
        pair = page[position : position + 2]
        if pair == b"{{":
            if depth == 0 and re.match(rb"\{\{\s*(?:Infobox|Taxobox)\b", page[position:], re.I):
                start = position
                local_depth = 1
                cursor = position + 2
                while cursor + 1 < text_end:
                    token = page[cursor : cursor + 2]
                    if token == b"{{":
                        local_depth += 1
                        cursor += 2
                    elif token == b"}}":
                        local_depth -= 1
                        cursor += 2
                        if local_depth == 0:
                            return start, cursor
                    else:
                        cursor += 1
                return None
            depth += 1
            position += 2
        elif pair == b"}}":
            depth = max(0, depth - 1)
            position += 2
        else:
            position += 1
    return None


def anchor_spans(page: bytes) -> list[tuple[int, int, str]]:
    candidates: list[tuple[int, int, str]] = []
    title = re.search(rb"<title>.*?</title>", page, re.S)
    if title:
        candidates.append((title.start(), title.end(), "title"))
    for match in re.finditer(rb"(?m)^={2,6}[^=\r\n].*?={2,6}[ \t]*(?:\r?\n|$)", page):
        candidates.append((match.start(), match.end(), "heading"))
    infobox = infobox_span(page)
    if infobox:
        candidates.append((infobox[0], infobox[1], "infobox"))
    text_end = page.rfind(b"</text>")
    category_floor = max(0, text_end - max(4096, len(page) // 3))
    for match in re.finditer(rb"\[\[Category:[^\]\r\n]*(?:\]\])", page, re.I):
        if match.start() >= category_floor:
            candidates.append((match.start(), match.end(), "category"))
    candidates.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    selected: list[tuple[int, int, str]] = []
    cursor = -1
    for start, end, label in candidates:
        if start >= cursor:
            selected.append((start, end, label))
            cursor = end
    return selected


def page_spans(raw: bytes) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    position = 0
    while True:
        start = raw.find(b"<page>", position)
        if start < 0:
            break
        end = raw.find(b"</page>", start + 6)
        if end < 0:
            break
        end += len(b"</page>")
        spans.append((start, end))
        position = end
    return spans


def build_records(parsed) -> tuple[bytes, list[Record], dict[str, int]]:
    groups_list: list[EmissionGroup] = []
    pending = []
    for event in parsed.events:
        pending.append(event)
        if event.decoded:
            encoded = b"".join(item.encoded for item in pending)
            decoded = b"".join(item.decoded for item in pending)
            groups_list.append(EmissionGroup(encoded, decoded, group_is_lexical(encoded)))
            pending.clear()
    if pending:
        if not groups_list:
            encoded = b"".join(item.encoded for item in pending)
            groups_list.append(EmissionGroup(encoded, b"", False))
        else:
            previous = groups_list[-1]
            encoded = previous.encoded + b"".join(item.encoded for item in pending)
            groups_list[-1] = EmissionGroup(encoded, previous.decoded, previous.lexical)
    groups = tuple(groups_list)
    cumulative = [0]
    for group in groups:
        cumulative.append(cumulative[-1] + len(group.decoded))

    def boundary(offset: int) -> int | None:
        index = bisect.bisect_left(cumulative, offset)
        return index if index < len(cumulative) and cumulative[index] == offset else None

    records: list[Record] = []
    anchor_counts: Counter[str] = Counter()
    skipped_unaligned = 0
    event_cursor = 0
    for page_ordinal, (raw_start, raw_end) in enumerate(page_spans(parsed.decoded)):
        event_start = boundary(raw_start)
        event_end = boundary(raw_end)
        if event_start is None or event_end is None:
            skipped_unaligned += 1
            continue
        if event_cursor < event_start:
            records.append(
                Record(None, (Segment(0, "body", groups[event_cursor:event_start]),))
            )
        converted: list[tuple[int, int, str]] = []
        page = parsed.decoded[raw_start:raw_end]
        for start, end, label in anchor_spans(page):
            anchor_start = boundary(raw_start + start)
            anchor_end = boundary(raw_start + end)
            if (
                anchor_start is None
                or anchor_end is None
                or anchor_start < event_start
                or anchor_end > event_end
            ):
                skipped_unaligned += 1
                continue
            converted.append((anchor_start, anchor_end, label))
        segments: list[Segment] = []
        cursor = event_start
        for anchor_start, anchor_end, label in converted:
            if anchor_start < cursor:
                continue
            if cursor < anchor_start:
                segments.append(Segment(len(segments), "body", groups[cursor:anchor_start]))
            if anchor_start < anchor_end:
                segments.append(Segment(len(segments), label, groups[anchor_start:anchor_end]))
                anchor_counts[label] += 1
            cursor = anchor_end
        if cursor < event_end:
            segments.append(Segment(len(segments), "body", groups[cursor:event_end]))
        if not segments:
            segments.append(Segment(0, "body", groups[event_start:event_end]))
        records.append(Record(page_ordinal, tuple(segments)))
        event_cursor = event_end
    if event_cursor < len(groups):
        records.append(Record(None, (Segment(0, "body", groups[event_cursor:]),)))
    preamble = parsed.stored[: parsed.storage_header_bytes + 6]
    return preamble, records, {
        "pages": sum(record.page_ordinal is not None for record in records),
        "nonpage_records": sum(record.page_ordinal is None for record in records),
        "emission_groups": len(groups),
        "lexical_emission_groups": sum(group.lexical for group in groups),
        "skipped_unaligned_boundaries": skipped_unaligned,
        **{f"{label}_nodes": anchor_counts[label] for label in sorted(anchor_counts)},
    }


def ordered_segments(record: Record, mode: int) -> tuple[Segment, ...]:
    if mode != MODE_O1 or record.page_ordinal is None:
        return record.segments
    return tuple(segment for segment in record.segments if segment.anchor) + tuple(
        segment for segment in record.segments if not segment.anchor
    )


def descriptor(record: Record, mode: int, payload_length: int) -> bytes:
    out = bytearray((1 if record.page_ordinal is not None else 0,))
    if record.page_ordinal is not None:
        out.extend(put_varint(record.page_ordinal))
    out.extend(put_varint(record.byte_length))
    if mode != MODE_R and record.page_ordinal is not None:
        out.extend(put_varint(len(record.segments)))
        for segment in record.segments:
            out.append(LABELS[segment.label])
            out.extend(put_varint(len(segment.groups)))
            out.extend(put_varint(segment.byte_length))
    out.extend(put_varint(payload_length))
    return bytes(out)


def encode_record(
    record: Record, mode: int, blend_ppm: int, model: Ppm
) -> tuple[bytes, float]:
    encoder = ArithmeticEncoder()
    loss = 0.0
    if mode == MODE_R or record.page_ordinal is None:
        loss += encode_raw(encoder, model, b"".join(group.encoded for group in record.groups))
    else:
        anchors: Counter[bytes] = Counter()
        for segment in ordered_segments(record, mode):
            for group in segment.groups:
                loss += encode_event(
                    encoder,
                    model,
                    group.encoded,
                    anchors,
                    not segment.anchor,
                    blend_ppm,
                )
                if segment.anchor and group.lexical:
                    anchors[group.encoded] += 1
    return encoder.finish(), loss


def make_archive(
    preamble: bytes, records: list[Record], mode: int, blend_ppm: int
) -> tuple[bytes, dict]:
    header = MAGIC + bytes((mode,)) + blend_ppm.to_bytes(4, "big")
    header += put_varint(len(preamble)) + preamble
    if mode == MODE_R:
        encoder = ArithmeticEncoder()
        model = Ppm()
        partition_ideal_bits: Counter[str] = Counter()
        stream_length = 0
        for record in records:
            data = b"".join(group.encoded for group in record.groups)
            ideal_bits = encode_raw(encoder, model, data)
            stream_length += len(data)
            split = (
                SPLITS[record.page_ordinal % 5]
                if record.page_ordinal is not None
                else "unpartitioned"
            )
            partition_ideal_bits[split] += ideal_bits
        payload = encoder.finish()
        archive = (
            header
            + put_varint(stream_length)
            + put_varint(len(payload))
            + payload
        )
        partition_ideal_bits["unpartitioned"] += 8 * (
            len(archive) - len(payload)
        )
        return archive, {
            "archive_bytes": len(archive),
            "archive_sha256": sha256(archive),
            "partition_exact_bytes": {"unpartitioned": len(archive)},
            "partition_ideal_bits": {
                key: round(value, 3)
                for key, value in sorted(partition_ideal_bits.items())
            },
        }
    header += put_varint(len(records))
    body = bytearray()
    model = Ppm()
    partition_bytes: Counter[str] = Counter()
    partition_ideal_bits: Counter[str] = Counter()
    for record in records:
        payload, ideal_bits = encode_record(record, mode, blend_ppm, model)
        meta = descriptor(record, mode, len(payload))
        body.extend(meta)
        body.extend(payload)
        split = (
            SPLITS[record.page_ordinal % 5]
            if record.page_ordinal is not None
            else "unpartitioned"
        )
        partition_bytes[split] += len(meta) + len(payload)
        partition_ideal_bits[split] += ideal_bits + 8 * len(meta)
    archive = header + bytes(body)
    partition_bytes["unpartitioned"] += len(header)
    partition_ideal_bits["unpartitioned"] += 8 * len(header)
    return archive, {
        "archive_bytes": len(archive),
        "archive_sha256": sha256(archive),
        "partition_exact_bytes": dict(sorted(partition_bytes.items())),
        "partition_ideal_bits": {
            key: round(value, 3) for key, value in sorted(partition_ideal_bits.items())
        },
    }


def restore_archive(archive: bytes) -> bytes:
    if not archive.startswith(MAGIC):
        raise ValueError("bad ARIADNE archive magic")
    position = len(MAGIC)
    mode = archive[position]
    position += 1
    blend_ppm = int.from_bytes(archive[position : position + 4], "big")
    position += 4
    preamble_length, position = get_varint(archive, position)
    preamble = archive[position : position + preamble_length]
    position += preamble_length
    if mode == MODE_R:
        stream_length, position = get_varint(archive, position)
        payload_length, position = get_varint(archive, position)
        payload = archive[position : position + payload_length]
        position += payload_length
        if position != len(archive):
            raise ValueError("trailing bytes in ARIADNE R archive")
        decoder = ArithmeticDecoder(payload)
        model = Ppm()
        return preamble + decode_raw(decoder, model, stream_length)
    record_count, position = get_varint(archive, position)
    restored = bytearray(preamble)
    model = Ppm()
    for _ in range(record_count):
        page = archive[position] == 1
        position += 1
        if page:
            _page_ordinal, position = get_varint(archive, position)
        byte_length, position = get_varint(archive, position)
        segment_meta: list[tuple[str, int, int]] = []
        if mode != MODE_R and page:
            segment_count, position = get_varint(archive, position)
            for _segment in range(segment_count):
                label = LABEL_NAMES[archive[position]]
                position += 1
                group_count, position = get_varint(archive, position)
                segment_bytes, position = get_varint(archive, position)
                segment_meta.append((label, group_count, segment_bytes))
        payload_length, position = get_varint(archive, position)
        payload = archive[position : position + payload_length]
        position += payload_length
        decoder = ArithmeticDecoder(payload)
        if mode == MODE_R or not page:
            restored.extend(decode_raw(decoder, model, byte_length))
            continue
        order = list(range(len(segment_meta)))
        if mode == MODE_O1:
            order = [
                index for index, meta in enumerate(segment_meta) if meta[0] != "body"
            ] + [index for index, meta in enumerate(segment_meta) if meta[0] == "body"]
        decoded_segments: dict[int, bytes] = {}
        anchors: Counter[bytes] = Counter()
        for index in order:
            label, group_count, segment_bytes = segment_meta[index]
            decoded_segments[index] = decode_segment(
                decoder,
                model,
                group_count,
                segment_bytes,
                label != "body",
                anchors,
                blend_ppm,
            )
        record_data = b"".join(decoded_segments[index] for index in range(len(segment_meta)))
        if len(record_data) != byte_length:
            raise ValueError("restored record length disagrees with descriptor")
        restored.extend(record_data)
    if position != len(archive):
        raise ValueError("trailing bytes in ARIADNE archive")
    return bytes(restored)


def run(store: Path, dictionary: Path, output: Path, blends: Iterable[int]) -> dict:
    parsed = parse_store(store, dictionary)
    preamble, records, partition = build_records(parsed)
    variants: dict[str, dict] = {}
    archives: dict[str, bytes] = {}
    configurations = [(MODE_R, 0)]
    for blend in blends:
        configurations.extend(((MODE_O0, blend), (MODE_O1, blend)))
    for mode, blend in configurations:
        label = MODE_NAMES[mode] if mode == MODE_R else f"{MODE_NAMES[mode]}_p1_{blend}"
        archive, stats = make_archive(preamble, records, mode, blend)
        restored = restore_archive(archive)
        stats["roundtrip_ok"] = restored == parsed.stored
        stats["restored_sha256"] = sha256(restored)
        variants[label] = stats
        archives[label] = archive
        if not stats["roundtrip_ok"]:
            raise ValueError(f"{label} failed exact store roundtrip")

    selected: dict[str, str] = {}
    for mode_name in ("O0", "O1"):
        choices = [
            (name, row)
            for name, row in variants.items()
            if name.startswith(f"{mode_name}_")
        ]
        selected[mode_name] = min(
            choices,
            key=lambda item: item[1]["partition_ideal_bits"].get("development", math.inf),
        )[0]
    r_bytes = variants["R"]["archive_bytes"]
    o0 = variants[selected["O0"]]
    o1 = variants[selected["O1"]]
    development_order_gain = (
        o0["partition_ideal_bits"].get("development", 0)
        - o1["partition_ideal_bits"].get("development", 0)
    )
    holdout_order_gain = (
        o0["partition_ideal_bits"].get("holdout", 0)
        - o1["partition_ideal_bits"].get("holdout", 0)
    )
    development_complete_gain = (
        variants["R"]["partition_ideal_bits"].get("development", 0)
        - o1["partition_ideal_bits"].get("development", 0)
    )
    holdout_complete_gain = (
        variants["R"]["partition_ideal_bits"].get("holdout", 0)
        - o1["partition_ideal_bits"].get("holdout", 0)
    )
    source = Path(__file__).read_bytes()
    source_xz_bytes = len(lzma.compress(source, preset=9 | lzma.PRESET_EXTREME))
    gross_gain_bytes = r_bytes - o1["archive_bytes"]
    gross_gain_bytes_per_m = gross_gain_bytes * 1_000_000 / len(parsed.decoded)
    research_floor_bytes_per_m = 200.0
    safety_reserve_bytes_per_m = 50.0
    required_gain_bytes_per_m = (
        research_floor_bytes_per_m + source_xz_bytes / 1000 + safety_reserve_bytes_per_m
    )
    mechanism_positive = development_order_gain > 0 and holdout_order_gain > 0
    complete_positive = (
        gross_gain_bytes > 0
        and development_complete_gain > 0
        and holdout_complete_gain > 0
    )
    economically_positive = (
        complete_positive and gross_gain_bytes_per_m >= required_gain_bytes_per_m
    )
    if not mechanism_positive or o1["archive_bytes"] >= o0["archive_bytes"]:
        verdict = "retire_fixed_evidence_first"
    elif o1["archive_bytes"] >= r_bytes:
        verdict = "retain_ordering_primitive_reject_transform"
    elif not economically_positive:
        verdict = "positive_but_subeconomic"
    else:
        verdict = "promote_to_disjoint_native_replacement"

    output.mkdir(parents=True, exist_ok=True)
    for label, archive in archives.items():
        (output / f"{label}.ari").write_bytes(archive)
    receipt = {
        "schema": "ariadne0_coarse_anchor_order_v1",
        "evidence_level": "constructive_exact_wrt_store_codec",
        "claim_boundary": (
            "Standalone WRT-store arithmetic experiment. Source-package cost is "
            "reported separately and no full endpoint428 score credit is claimed."
        ),
        "source": str(Path(__file__).resolve()),
        "source_sha256": sha256(source),
        "source_bytes": len(source),
        "source_xz_bytes": source_xz_bytes,
        "input_store": str(store.resolve()),
        "input_store_bytes": len(parsed.stored),
        "input_store_sha256": sha256(parsed.stored),
        "dictionary": str(dictionary.resolve()),
        "dictionary_sha256": sha256(dictionary.read_bytes()),
        "decoded_raw_bytes": len(parsed.decoded),
        "decoded_raw_sha256": sha256(parsed.decoded),
        "partition": partition,
        "page_split": {
            "train": "page_index mod 5 in {0,1,2}",
            "development": "page_index mod 5 == 3",
            "holdout": "page_index mod 5 == 4",
            "chronological_updates_preserved": True,
        },
        "blends_ppm": list(blends),
        "selected_on_development": selected,
        "variants": variants,
        "decision": {
            "verdict": verdict,
            "R_archive_bytes": r_bytes,
            "selected_O0": selected["O0"],
            "selected_O0_archive_bytes": o0["archive_bytes"],
            "selected_O1": selected["O1"],
            "selected_O1_archive_bytes": o1["archive_bytes"],
            "O1_minus_O0_bytes": o1["archive_bytes"] - o0["archive_bytes"],
            "O1_minus_R_bytes": o1["archive_bytes"] - r_bytes,
            "development_order_gain_bits": round(development_order_gain, 3),
            "holdout_order_gain_bits": round(holdout_order_gain, 3),
            "development_complete_gain_bits": round(development_complete_gain, 3),
            "holdout_complete_gain_bits": round(holdout_complete_gain, 3),
            "gross_gain_bytes_per_m": round(gross_gain_bytes_per_m, 3),
            "required_gain_bytes_per_m": round(required_gain_bytes_per_m, 3),
            "research_floor_bytes_per_m": research_floor_bytes_per_m,
            "safety_reserve_bytes_per_m": safety_reserve_bytes_per_m,
            "mechanism_positive": mechanism_positive,
            "complete_positive": complete_positive,
            "score_economically_positive": economically_positive,
        },
    }
    (output / "decision.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--blend-ppm", type=int, action="append", default=[])
    args = parser.parse_args()
    blends = args.blend_ppm or [0, 125_000, 375_000]
    if any(blend < 0 or blend > 1_000_000 for blend in blends):
        raise SystemExit("blend values must be between 0 and 1000000")
    receipt = run(args.store, args.dictionary, args.output, blends)
    print(json.dumps(receipt["decision"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
