"""WikiIR prior-page prototype delta with explicit ADD/COPY/RUN events.

Each complete ``<page>...</page>`` record may reference one earlier decoded
page.  Candidate discovery uses template/category signatures and a bounded
recent-page set; the chosen reference distance and complete edit program are
stored in the archive.  Decoder and encoder therefore share no hidden index.

This is a discovery implementation.  Its exact MDL choices and global
one-byte fallback prevent an unprofitable representation from being mistaken
for compression gain.  A production version would replace the Python byte
index with bounded minimizers and integrate ahead of the target backend.
"""

from __future__ import annotations

import lzma
import re


PRESET = 9 | lzma.PRESET_EXTREME
MAGIC = b"WPD1"
MODE_LITERAL = 0
MODE_DELTA = 1
OP_ADD = 0
OP_COPY = 1
OP_RUN = 2
ANCHOR_BYTES = 8
MIN_COPY = 12
MIN_RUN = 8
RECENT_CANDIDATES = 8
MAX_CANDIDATES = 40
MAX_ANCHOR_POSITIONS = 6
MIN_PAGE_SAVING = 8

_TEMPLATE_RE = re.compile(rb"\{\{\s*([^|{}\r\n]{1,80})")
_CATEGORY_RE = re.compile(rb"\[\[Category:([^|\]\r\n]{1,96})", re.IGNORECASE)
_LAST_STATS: dict[str, int | str | bool] = {}


def _varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint value must be nonnegative")
    output = bytearray()
    while value >= 0x80:
        output.append((value & 0x7F) | 0x80)
        value >>= 7
    output.append(value)
    return bytes(output)


def _read_varint(data: bytes, position: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if position >= len(data) or shift > 63:
            raise ValueError("invalid or truncated varint")
        byte = data[position]
        position += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, position
        shift += 7


def _split_pages(data: bytes) -> tuple[bytes, list[bytes], bytes]:
    pages: list[bytes] = []
    first = data.find(b"<page>")
    if first < 0:
        return data, pages, b""
    prefix = data[:first]
    position = first
    while True:
        start = data.find(b"<page>", position)
        if start < 0:
            return prefix, pages, data[position:]
        if start != position:
            # Preserve unexpected inter-page bytes with the following page.
            start = position
        close = data.find(b"</page>", position)
        if close < 0:
            return prefix, pages, data[position:]
        end = close + len(b"</page>")
        if data[end : end + 1] == b"\n":
            end += 1
        pages.append(data[start:end])
        position = end


def _features(page: bytes) -> tuple[bytes, ...]:
    features = {b"t:" + match.strip().lower() for match in _TEMPLATE_RE.findall(page)}
    features.update(
        b"c:" + match.strip().lower() for match in _CATEGORY_RE.findall(page)
    )
    if b"<redirect" in page.lower():
        features.add(b"m:redirect")
    if b"{|" in page:
        features.add(b"m:table")
    if b"<ref" in page.lower():
        features.add(b"m:ref")
    return tuple(sorted(features))


def _build_anchor_index(reference: bytes) -> dict[bytes, tuple[int, ...]]:
    mutable: dict[bytes, list[int]] = {}
    end = len(reference) - ANCHOR_BYTES + 1
    for position in range(max(0, end)):
        anchor = reference[position : position + ANCHOR_BYTES]
        positions = mutable.setdefault(anchor, [])
        if len(positions) < MAX_ANCHOR_POSITIONS:
            positions.append(position)
    return {anchor: tuple(positions) for anchor, positions in mutable.items()}


def _longest_match(
    reference: bytes,
    target: bytes,
    target_position: int,
    index: dict[bytes, tuple[int, ...]],
) -> tuple[int, int]:
    anchor = target[target_position : target_position + ANCHOR_BYTES]
    candidates = index.get(anchor, ())
    best_position = 0
    best_length = 0
    for reference_position in candidates:
        length = ANCHOR_BYTES
        maximum = min(
            len(reference) - reference_position,
            len(target) - target_position,
        )
        while length < maximum and (
            reference[reference_position + length]
            == target[target_position + length]
        ):
            length += 1
        if length > best_length:
            best_position = reference_position
            best_length = length
    return best_position, best_length


def _flush_add(output: bytearray, pending: bytearray) -> None:
    if pending:
        output.append(OP_ADD)
        output.extend(_varint(len(pending)))
        output.extend(pending)
        pending.clear()


def _delta_encode(
    reference: bytes,
    target: bytes,
    index: dict[bytes, tuple[int, ...]] | None = None,
) -> tuple[bytes, dict[str, int]]:
    if index is None:
        index = _build_anchor_index(reference)
    output = bytearray()
    pending = bytearray()
    position = 0
    copies = 0
    copied_bytes = 0
    runs = 0
    run_bytes = 0
    while position < len(target):
        run_length = 1
        while (
            position + run_length < len(target)
            and target[position + run_length] == target[position]
        ):
            run_length += 1
        if run_length >= MIN_RUN:
            _flush_add(output, pending)
            output.append(OP_RUN)
            output.append(target[position])
            output.extend(_varint(run_length))
            position += run_length
            runs += 1
            run_bytes += run_length
            continue

        reference_position, match_length = _longest_match(
            reference, target, position, index
        )
        copy_cost = (
            1 + len(_varint(reference_position)) + len(_varint(match_length))
        )
        if match_length >= MIN_COPY and match_length > copy_cost + 2:
            _flush_add(output, pending)
            output.append(OP_COPY)
            output.extend(_varint(reference_position))
            output.extend(_varint(match_length))
            position += match_length
            copies += 1
            copied_bytes += match_length
            continue
        pending.append(target[position])
        position += 1
    _flush_add(output, pending)
    return bytes(output), {
        "copy_commands": copies,
        "copied_bytes": copied_bytes,
        "run_commands": runs,
        "run_bytes": run_bytes,
    }


def _delta_decode(reference: bytes, stream: bytes) -> bytes:
    output = bytearray()
    position = 0
    while position < len(stream):
        opcode = stream[position]
        position += 1
        if opcode == OP_ADD:
            length, position = _read_varint(stream, position)
            end = position + length
            if end > len(stream):
                raise ValueError("truncated prior-page ADD")
            output.extend(stream[position:end])
            position = end
        elif opcode == OP_COPY:
            source, position = _read_varint(stream, position)
            length, position = _read_varint(stream, position)
            end = source + length
            if end > len(reference):
                raise ValueError("prior-page COPY exceeds reference")
            output.extend(reference[source:end])
        elif opcode == OP_RUN:
            if position >= len(stream):
                raise ValueError("truncated prior-page RUN")
            byte = stream[position]
            position += 1
            length, position = _read_varint(stream, position)
            output.extend(bytes([byte]) * length)
        else:
            raise ValueError(f"unknown prior-page delta opcode {opcode}")
    return bytes(output)


def _candidate_ids(
    page_id: int,
    page_features: tuple[bytes, ...],
    postings: dict[bytes, list[int]],
) -> list[int]:
    overlap: dict[int, int] = {}
    for feature in page_features:
        for candidate in postings.get(feature, ())[-64:]:
            overlap[candidate] = overlap.get(candidate, 0) + 1
    ranked = sorted(overlap, key=lambda candidate: (-overlap[candidate], page_id - candidate))
    recent = list(range(max(0, page_id - RECENT_CANDIDATES), page_id))
    selected: list[int] = []
    for candidate in ranked + list(reversed(recent)):
        if candidate not in selected:
            selected.append(candidate)
        if len(selected) >= MAX_CANDIDATES:
            break
    return selected


def encode_ir(data: bytes) -> tuple[bytes, dict[str, int]]:
    prefix, pages, suffix = _split_pages(data)
    output = bytearray(MAGIC)
    output.extend(_varint(len(prefix)))
    output.extend(prefix)
    output.extend(_varint(len(pages)))
    postings: dict[bytes, list[int]] = {}
    indexes: dict[int, dict[bytes, tuple[int, ...]]] = {}
    delta_pages = 0
    delta_payload_bytes = 0
    literal_payload_bytes = 0
    copied_bytes = 0
    copy_commands = 0
    references_considered = 0

    for page_id, page in enumerate(pages):
        features = _features(page)
        literal_event = bytes([MODE_LITERAL]) + _varint(len(page)) + page
        best_event = literal_event
        best_stats: dict[str, int] | None = None
        for candidate_id in _candidate_ids(page_id, features, postings):
            index = indexes.get(candidate_id)
            if index is None:
                index = _build_anchor_index(pages[candidate_id])
                indexes[candidate_id] = index
            delta, delta_stats = _delta_encode(pages[candidate_id], page, index)
            distance = page_id - candidate_id
            event = (
                bytes([MODE_DELTA])
                + _varint(distance)
                + _varint(len(delta))
                + delta
            )
            references_considered += 1
            if len(event) < len(best_event):
                best_event = event
                best_stats = delta_stats
        if (
            best_stats is not None
            and len(literal_event) - len(best_event) >= MIN_PAGE_SAVING
        ):
            output.extend(best_event)
            delta_pages += 1
            delta_payload_bytes += len(best_event)
            copied_bytes += best_stats["copied_bytes"]
            copy_commands += best_stats["copy_commands"]
        else:
            output.extend(literal_event)
            literal_payload_bytes += len(literal_event)
        for feature in features:
            postings.setdefault(feature, []).append(page_id)

    output.extend(_varint(len(suffix)))
    output.extend(suffix)
    return bytes(output), {
        "complete_pages": len(pages),
        "delta_pages": delta_pages,
        "literal_pages": len(pages) - delta_pages,
        "references_considered": references_considered,
        "copy_commands": copy_commands,
        "copied_bytes": copied_bytes,
        "delta_event_bytes": delta_payload_bytes,
        "literal_event_bytes": literal_payload_bytes,
        "ir_bytes": len(output),
        "raw_ir_delta_bytes": len(data) - len(output),
    }


def decode_ir(stream: bytes) -> bytes:
    if not stream.startswith(MAGIC):
        raise ValueError("invalid prior-page WikiIR magic")
    position = len(MAGIC)
    prefix_length, position = _read_varint(stream, position)
    prefix_end = position + prefix_length
    if prefix_end > len(stream):
        raise ValueError("truncated prior-page prefix")
    output = bytearray(stream[position:prefix_end])
    position = prefix_end
    page_count, position = _read_varint(stream, position)
    pages: list[bytes] = []
    for page_id in range(page_count):
        if position >= len(stream):
            raise ValueError("truncated prior-page event")
        mode = stream[position]
        position += 1
        if mode == MODE_LITERAL:
            length, position = _read_varint(stream, position)
            end = position + length
            if end > len(stream):
                raise ValueError("truncated literal page")
            page = stream[position:end]
            position = end
        elif mode == MODE_DELTA:
            distance, position = _read_varint(stream, position)
            if distance < 1 or distance > page_id:
                raise ValueError("invalid prior-page reference distance")
            delta_length, position = _read_varint(stream, position)
            end = position + delta_length
            if end > len(stream):
                raise ValueError("truncated page delta")
            page = _delta_decode(pages[page_id - distance], stream[position:end])
            position = end
        else:
            raise ValueError("invalid prior-page representation mode")
        pages.append(page)
        output.extend(page)
    suffix_length, position = _read_varint(stream, position)
    suffix_end = position + suffix_length
    if suffix_end != len(stream):
        raise ValueError("invalid prior-page suffix length")
    output.extend(stream[position:suffix_end])
    return bytes(output)


def compress(data: bytes) -> bytes:
    global _LAST_STATS
    ir, ir_stats = encode_ir(data)
    if decode_ir(ir) != data:
        raise RuntimeError("prior-page WikiIR internal roundtrip failed")
    literal_archive = lzma.compress(data, preset=PRESET)
    delta_archive = lzma.compress(ir, preset=PRESET)
    use_delta = len(delta_archive) < len(literal_archive)
    selected = delta_archive if use_delta else literal_archive
    _LAST_STATS = {
        **ir_stats,
        "literal_archive_bytes": len(literal_archive),
        "delta_archive_bytes": len(delta_archive),
        "delta_archive_gain_before_mode_bytes": (
            len(literal_archive) - len(delta_archive)
        ),
        "selected_mode": "delta" if use_delta else "literal",
        "mode_byte_cost": 1,
        "selected_archive_bytes": len(selected) + 1,
        "roundtrip_checked_inside_compress": True,
    }
    return bytes([MODE_DELTA if use_delta else MODE_LITERAL]) + selected


def decompress(archive: bytes) -> bytes:
    if not archive:
        raise ValueError("empty prior-page WikiIR archive")
    decoded = lzma.decompress(archive[1:])
    if archive[0] == MODE_LITERAL:
        return decoded
    if archive[0] == MODE_DELTA:
        return decode_ir(decoded)
    raise ValueError("invalid prior-page archive mode")


def stats() -> dict[str, int | str | bool]:
    return dict(_LAST_STATS)
