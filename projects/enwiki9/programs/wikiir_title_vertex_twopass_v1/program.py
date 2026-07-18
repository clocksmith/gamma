"""Dictionary-free two-pass title-graph WikiIR transform.

Page titles remain literal and in their original positions.  Link-target bases
that name any page in the scoped stream become compact vertex references.  The
inverse first scans the fully decoded skeleton for literal titles, then replays
the skeleton and fills every link slot.  This permits forward references
without copying a title dictionary into the archive.
"""

from __future__ import annotations

import lzma
import struct


PRESET = 9 | lzma.PRESET_EXTREME
MODE_LITERAL = 0
MODE_VERTEX = 1
TAIL_MAGIC = b"W2TG"
TRAILER_BYTES = 12
ESCAPE = 0
ESCAPED_ZERO = 0
LINK_SLOT = 1
MAX_TARGET_BYTES = 1_024
BLOCK_IDS = 64

SURFACE_EXACT = 0
SURFACE_UNDERSCORE = 1
SURFACE_ASCII_LOWER_FIRST = 2

REF_ABSOLUTE_COMBINED = 0
REF_DELTA_COMBINED = 1
REF_BLOCK_DELTA_COMBINED = 2
REF_ABSOLUTE_SEPARATE = 3
REF_DELTA_SEPARATE = 4
REF_BLOCK_DELTA_SEPARATE = 5

_LAST_STATS: dict[str, object] = {}


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


def _zigzag(value: int) -> int:
    return 2 * value if value >= 0 else -2 * value - 1


def _unzigzag(value: int) -> int:
    return value // 2 if value % 2 == 0 else -(value // 2) - 1


def _scan_titles(data: bytes) -> list[tuple[int, int, bytes]]:
    rows: list[tuple[int, int, bytes]] = []
    position = 0
    while True:
        opening = data.find(b"<title>", position)
        if opening < 0:
            break
        start = opening + len(b"<title>")
        end = data.find(b"</title>", start)
        if end < 0:
            break
        title = data[start:end]
        if title:
            rows.append((start, end, title))
        position = end + len(b"</title>")
    return rows


def _scan_link_bases(data: bytes) -> list[tuple[int, int, bytes]]:
    rows: list[tuple[int, int, bytes]] = []
    position = 0
    while position + 3 < len(data):
        opening = data.find(b"[[", position)
        if opening < 0:
            break
        closing = data.find(b"]]", opening + 2)
        if closing < 0:
            break
        start = opening + 2
        pipe = data.find(b"|", start, closing)
        target_end = pipe if pipe >= 0 else closing
        fragment = data.find(b"#", start, target_end)
        end = fragment if fragment >= 0 else target_end
        base = data[start:end]
        if 0 < len(base) <= MAX_TARGET_BYTES and b"\n" not in base and b"\r" not in base:
            rows.append((start, end, base))
        position = closing + 2
    return rows


def _surface_bytes(title: bytes, mode: int) -> bytes:
    if mode == SURFACE_EXACT:
        return title
    if mode == SURFACE_UNDERSCORE:
        if b" " not in title:
            raise ValueError("invalid final-space underscore title reference")
        prefix, suffix = title.rsplit(b" ", 1)
        return prefix + b"_" + suffix
    if mode == SURFACE_ASCII_LOWER_FIRST:
        if not title or not 65 <= title[0] <= 90:
            raise ValueError("invalid lowercase-first title reference")
        return bytes((title[0] + 32,)) + title[1:]
    raise ValueError("unknown title surface mode")


def _title_maps(
    titles: tuple[bytes, ...],
) -> tuple[dict[bytes, int], dict[bytes, int], dict[bytes, int]]:
    exact: dict[bytes, int] = {}
    underscore: dict[bytes, int] = {}
    lower_first: dict[bytes, int] = {}
    for index, title in enumerate(titles):
        exact.setdefault(title, index)
        if b" " in title:
            prefix, suffix = title.rsplit(b" ", 1)
            underscored = prefix + b"_" + suffix
            underscore.setdefault(underscored, index)
        if title and 65 <= title[0] <= 90:
            lowered = bytes((title[0] + 32,)) + title[1:]
            lower_first.setdefault(lowered, index)
    return exact, underscore, lower_first


def _match_title(
    base: bytes,
    exact: dict[bytes, int],
    underscore: dict[bytes, int],
    lower_first: dict[bytes, int],
) -> tuple[int, int] | None:
    title_id = exact.get(base)
    if title_id is not None:
        return title_id, SURFACE_EXACT
    title_id = underscore.get(base)
    if title_id is not None:
        return title_id, SURFACE_UNDERSCORE
    title_id = lower_first.get(base)
    if title_id is not None:
        return title_id, SURFACE_ASCII_LOWER_FIRST
    return None


def _pack_surface_modes(modes: list[int]) -> bytes:
    output = bytearray((len(modes) + 3) // 4)
    for index, mode in enumerate(modes):
        if not 0 <= mode <= 3:
            raise ValueError("surface mode does not fit two bits")
        output[index // 4] |= mode << (2 * (index % 4))
    return bytes(output)


def _unpack_surface_modes(payload: bytes, count: int) -> list[int]:
    expected = (count + 3) // 4
    if len(payload) != expected:
        raise ValueError("invalid packed surface-mode length")
    return [
        (payload[index // 4] >> (2 * (index % 4))) & 3
        for index in range(count)
    ]


def _encode_id_payload(ids: list[int], mode: int) -> bytes:
    output = bytearray()
    previous = 0
    for index, value in enumerate(ids):
        if mode == REF_ABSOLUTE_SEPARATE:
            encoded = value
        elif mode == REF_DELTA_SEPARATE:
            encoded = _zigzag(value - previous)
        elif mode == REF_BLOCK_DELTA_SEPARATE:
            encoded = value if index % BLOCK_IDS == 0 else _zigzag(value - previous)
        else:
            raise ValueError("unknown separate title-reference mode")
        output.extend(_varint(encoded))
        previous = value
    return bytes(output)


def _encode_references(references: list[tuple[int, int]]) -> tuple[int, bytes]:
    combined: dict[int, bytes] = {}
    for ref_mode in (
        REF_ABSOLUTE_COMBINED,
        REF_DELTA_COMBINED,
        REF_BLOCK_DELTA_COMBINED,
    ):
        output = bytearray()
        previous = 0
        for index, (title_id, surface_mode) in enumerate(references):
            if ref_mode == REF_ABSOLUTE_COMBINED:
                encoded_id = title_id
            elif ref_mode == REF_DELTA_COMBINED:
                encoded_id = _zigzag(title_id - previous)
            else:
                encoded_id = (
                    title_id
                    if index % BLOCK_IDS == 0
                    else _zigzag(title_id - previous)
                )
            output.extend(_varint((encoded_id << 2) | surface_mode))
            previous = title_id
        combined[ref_mode] = bytes(output)

    ids = [title_id for title_id, _surface_mode in references]
    modes = _pack_surface_modes(
        [surface_mode for _title_id, surface_mode in references]
    )
    separate = {
        ref_mode: modes + _encode_id_payload(ids, ref_mode)
        for ref_mode in (
            REF_ABSOLUTE_SEPARATE,
            REF_DELTA_SEPARATE,
            REF_BLOCK_DELTA_SEPARATE,
        )
    }
    # Surface normalization is a different event family from graph distance.
    # Keep its low-entropy two-bit channel separate instead of injecting mode
    # bits into every delta varint.  When every surface is exact, retain the
    # smallest raw representation.
    if any(surface_mode != SURFACE_EXACT for _title_id, surface_mode in references):
        return REF_DELTA_SEPARATE, separate[REF_DELTA_SEPARATE]
    choices = tuple(combined.items()) + tuple(separate.items())
    return min(choices, key=lambda row: (len(row[1]), row[0]))


def _decode_references(
    mode: int, payload: bytes, count: int
) -> list[tuple[int, int]]:
    references: list[tuple[int, int]] = []
    if mode <= REF_BLOCK_DELTA_COMBINED:
        position = 0
        previous = 0
        for index in range(count):
            packed, position = _read_varint(payload, position)
            surface_mode = packed & 3
            encoded_id = packed >> 2
            if mode == REF_ABSOLUTE_COMBINED:
                title_id = encoded_id
            elif mode == REF_DELTA_COMBINED:
                title_id = previous + _unzigzag(encoded_id)
            else:
                title_id = (
                    encoded_id
                    if index % BLOCK_IDS == 0
                    else previous + _unzigzag(encoded_id)
                )
            if title_id < 0 or surface_mode > SURFACE_ASCII_LOWER_FIRST:
                raise ValueError("invalid combined title reference")
            references.append((title_id, surface_mode))
            previous = title_id
        if position != len(payload):
            raise ValueError("trailing combined title-reference bytes")
        return references

    if mode not in (
        REF_ABSOLUTE_SEPARATE,
        REF_DELTA_SEPARATE,
        REF_BLOCK_DELTA_SEPARATE,
    ):
        raise ValueError("unknown title-reference mode")
    surface_bytes = (count + 3) // 4
    if surface_bytes > len(payload):
        raise ValueError("truncated surface-mode stream")
    surface_modes = _unpack_surface_modes(payload[:surface_bytes], count)
    position = surface_bytes
    previous = 0
    for index, surface_mode in enumerate(surface_modes):
        encoded_id, position = _read_varint(payload, position)
        if mode == REF_ABSOLUTE_SEPARATE:
            title_id = encoded_id
        elif mode == REF_DELTA_SEPARATE:
            title_id = previous + _unzigzag(encoded_id)
        else:
            title_id = (
                encoded_id
                if index % BLOCK_IDS == 0
                else previous + _unzigzag(encoded_id)
            )
        if title_id < 0 or surface_mode > SURFACE_ASCII_LOWER_FIRST:
            raise ValueError("invalid separate title reference")
        references.append((title_id, surface_mode))
        previous = title_id
    if position != len(payload):
        raise ValueError("trailing separate title-reference bytes")
    return references


def _escape_literal(data: bytes) -> bytes:
    return data.replace(b"\x00", b"\x00\x00")


def _literal_title_view(skeleton: bytes) -> bytes:
    output = bytearray()
    position = 0
    while position < len(skeleton):
        byte = skeleton[position]
        position += 1
        if byte != ESCAPE:
            output.append(byte)
            continue
        if position >= len(skeleton):
            raise ValueError("truncated two-pass title escape")
        opcode = skeleton[position]
        position += 1
        if opcode == ESCAPED_ZERO:
            output.append(0)
        elif opcode == LINK_SLOT:
            # Link slots never overlap title spans.  One non-markup byte keeps
            # all title tag locations and title contents intact for pass one.
            output.append(1)
        else:
            raise ValueError("unknown two-pass title escape")
    return bytes(output)


def _restore_skeleton(
    skeleton: bytes,
    titles: tuple[bytes, ...],
    references: list[tuple[int, int]],
) -> bytes:
    output = bytearray()
    position = 0
    reference_position = 0
    while position < len(skeleton):
        byte = skeleton[position]
        position += 1
        if byte != ESCAPE:
            output.append(byte)
            continue
        if position >= len(skeleton):
            raise ValueError("truncated two-pass title escape")
        opcode = skeleton[position]
        position += 1
        if opcode == ESCAPED_ZERO:
            output.append(0)
        elif opcode == LINK_SLOT:
            if reference_position >= len(references):
                raise ValueError("too many two-pass title slots")
            title_id, surface_mode = references[reference_position]
            reference_position += 1
            if title_id >= len(titles):
                raise ValueError("unknown two-pass title ID")
            output.extend(_surface_bytes(titles[title_id], surface_mode))
        else:
            raise ValueError("unknown two-pass title escape")
    if reference_position != len(references):
        raise ValueError("unused two-pass title references")
    return bytes(output)


def _split_stream(stream: bytes) -> tuple[bytes, int, bytes]:
    if len(stream) < TRAILER_BYTES or stream[-4:] != TAIL_MAGIC:
        raise ValueError("invalid two-pass title trailer")
    metadata_length = struct.unpack_from("<Q", stream, len(stream) - TRAILER_BYTES)[0]
    if metadata_length > len(stream) - TRAILER_BYTES:
        raise ValueError("invalid two-pass title metadata length")
    metadata_start = len(stream) - TRAILER_BYTES - metadata_length
    skeleton = stream[:metadata_start]
    metadata = stream[metadata_start : len(stream) - TRAILER_BYTES]
    reference_count, position = _read_varint(metadata, 0)
    if position >= len(metadata):
        raise ValueError("missing two-pass title reference mode")
    reference_mode = metadata[position]
    return skeleton, reference_count, bytes((reference_mode,)) + metadata[position + 1 :]


def encode_ir(data: bytes) -> tuple[bytes, dict[str, object]]:
    title_rows = _scan_titles(data)
    titles = tuple(title for _start, _end, title in title_rows)
    exact, underscore, lower_first = _title_maps(titles)

    replacements: list[tuple[int, int, int, int]] = []
    match_counts = [0, 0, 0]
    matched_source_bytes = 0
    title_position = 0
    for start, end, base in _scan_link_bases(data):
        while title_position < len(title_rows) and title_rows[title_position][1] <= start:
            title_position += 1
        if (
            title_position < len(title_rows)
            and title_rows[title_position][0] < end
            and start < title_rows[title_position][1]
        ):
            continue
        match = _match_title(base, exact, underscore, lower_first)
        if match is None:
            continue
        title_id, surface_mode = match
        if _surface_bytes(titles[title_id], surface_mode) != base:
            raise RuntimeError("non-reversible title surface match")
        replacements.append((start, end, title_id, surface_mode))
        match_counts[surface_mode] += 1
        matched_source_bytes += end - start

    skeleton = bytearray()
    references: list[tuple[int, int]] = []
    source_position = 0
    for start, end, title_id, surface_mode in replacements:
        if start < source_position:
            raise RuntimeError("overlapping two-pass title replacements")
        skeleton.extend(_escape_literal(data[source_position:start]))
        skeleton.extend((ESCAPE, LINK_SLOT))
        references.append((title_id, surface_mode))
        source_position = end
    skeleton.extend(_escape_literal(data[source_position:]))

    reference_mode, reference_payload = _encode_references(references)
    metadata = _varint(len(references)) + bytes((reference_mode,)) + reference_payload
    output = bytes(skeleton) + metadata + struct.pack("<Q", len(metadata)) + TAIL_MAGIC
    mode_names = (
        "absolute_combined",
        "delta_combined",
        "block_delta_combined",
        "absolute_separate",
        "delta_separate",
        "block_delta_separate",
    )
    return output, {
        "title_count": len(titles),
        "title_source_bytes_preserved_literal": sum(len(title) for title in titles),
        "matched_link_occurrences": len(references),
        "matched_exact_occurrences": match_counts[SURFACE_EXACT],
        "matched_underscore_occurrences": match_counts[SURFACE_UNDERSCORE],
        "matched_ascii_lower_first_occurrences": match_counts[
            SURFACE_ASCII_LOWER_FIRST
        ],
        "matched_link_source_bytes": matched_source_bytes,
        "skeleton_bytes": len(skeleton),
        "reference_mode": mode_names[reference_mode],
        "reference_payload_bytes": len(reference_payload),
        "metadata_bytes": len(metadata),
        "trailer_bytes": TRAILER_BYTES,
        "ir_bytes": len(output),
        "raw_ir_delta_bytes": len(data) - len(output),
        "forward_title_references_supported": True,
        "copied_title_dictionary_bytes": 0,
    }


def decode_ir(stream: bytes) -> bytes:
    skeleton, reference_count, mode_and_payload = _split_stream(stream)
    reference_mode = mode_and_payload[0]
    references = _decode_references(
        reference_mode, mode_and_payload[1:], reference_count
    )
    title_view = _literal_title_view(skeleton)
    titles = tuple(title for _start, _end, title in _scan_titles(title_view))
    return _restore_skeleton(skeleton, titles, references)


def compress(data: bytes) -> bytes:
    global _LAST_STATS
    ir, ir_stats = encode_ir(data)
    if decode_ir(ir) != data:
        raise RuntimeError("two-pass title-graph internal roundtrip failed")
    literal_archive = lzma.compress(data, preset=PRESET)
    vertex_archive = lzma.compress(ir, preset=PRESET)
    use_vertex = len(vertex_archive) < len(literal_archive)
    selected = vertex_archive if use_vertex else literal_archive
    _LAST_STATS = {
        **ir_stats,
        "literal_archive_bytes": len(literal_archive),
        "vertex_archive_bytes": len(vertex_archive),
        "vertex_archive_gain_before_mode_bytes": len(literal_archive)
        - len(vertex_archive),
        "selected_mode": "vertex" if use_vertex else "literal",
        "mode_byte_cost": 1,
        "selected_archive_bytes": len(selected) + 1,
        "roundtrip_checked_inside_compress": True,
    }
    return bytes((MODE_VERTEX if use_vertex else MODE_LITERAL,)) + selected


def decompress(archive: bytes) -> bytes:
    if not archive:
        raise ValueError("empty two-pass title-graph archive")
    decoded = lzma.decompress(archive[1:])
    if archive[0] == MODE_LITERAL:
        return decoded
    if archive[0] == MODE_VERTEX:
        return decode_ir(decoded)
    raise ValueError("invalid two-pass title-graph representation mode")


def stats() -> dict[str, object]:
    return dict(_LAST_STATS)
