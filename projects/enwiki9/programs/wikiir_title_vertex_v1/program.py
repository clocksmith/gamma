"""Exact title-as-vertex WikiIR transform.

Page titles are moved, not copied, into one front-coded table in source order.
Every exact link-target prefix that names a table title becomes a compact page
identifier while labels, fragments, delimiters, malformed markup, and all
unselected bytes remain in an escaped surface skeleton.  The decoder therefore
reconstructs the original bytes without a semantic model or external index.
"""

from __future__ import annotations

import lzma


PRESET = 9 | lzma.PRESET_EXTREME
MAGIC = b"WTV1"
MODE_LITERAL = 0
MODE_VERTEX = 1
ID_ABSOLUTE = 0
ID_DELTA = 1
ID_BLOCK_DELTA = 2
BLOCK_IDS = 64
ESCAPE = 0
ESCAPED_ZERO = 0
TITLE_SLOT = 1
LINK_SLOT = 2
MAX_TARGET_BYTES = 1_024

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


def _zigzag(value: int) -> int:
    return 2 * value if value >= 0 else -2 * value - 1


def _unzigzag(value: int) -> int:
    return value // 2 if value % 2 == 0 else -(value // 2) - 1


def _common_prefix(left: bytes, right: bytes) -> int:
    limit = min(len(left), len(right))
    position = 0
    while position < limit and left[position] == right[position]:
        position += 1
    return position


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


def _encode_dictionary(titles: tuple[bytes, ...]) -> bytes:
    output = bytearray()
    previous = b""
    for title in titles:
        prefix = _common_prefix(previous, title)
        suffix = title[prefix:]
        output.extend(_varint(prefix))
        output.extend(_varint(len(suffix)))
        output.extend(suffix)
        previous = title
    return bytes(output)


def _decode_dictionary(
    stream: bytes, position: int, count: int
) -> tuple[tuple[bytes, ...], int]:
    titles: list[bytes] = []
    previous = b""
    for _ in range(count):
        prefix, position = _read_varint(stream, position)
        suffix_length, position = _read_varint(stream, position)
        if prefix > len(previous):
            raise ValueError("invalid front-coded title prefix")
        end = position + suffix_length
        if end > len(stream):
            raise ValueError("truncated front-coded title")
        title = previous[:prefix] + stream[position:end]
        if not title:
            raise ValueError("empty title in vertex table")
        titles.append(title)
        previous = title
        position = end
    return tuple(titles), position


def _encode_ids(ids: list[int]) -> tuple[int, bytes]:
    absolute = b"".join(_varint(value) for value in ids)
    delta = bytearray()
    block = bytearray()
    previous = 0
    for index, value in enumerate(ids):
        delta.extend(_varint(_zigzag(value - previous)))
        if index % BLOCK_IDS == 0:
            block.extend(_varint(value))
        else:
            block.extend(_varint(_zigzag(value - previous)))
        previous = value
    choices = (
        (ID_ABSOLUTE, absolute),
        (ID_DELTA, bytes(delta)),
        (ID_BLOCK_DELTA, bytes(block)),
    )
    return min(choices, key=lambda row: (len(row[1]), row[0]))


def _decode_ids(mode: int, payload: bytes, count: int) -> list[int]:
    ids: list[int] = []
    position = 0
    previous = 0
    for index in range(count):
        encoded, position = _read_varint(payload, position)
        if mode == ID_ABSOLUTE:
            value = encoded
        elif mode == ID_DELTA:
            value = previous + _unzigzag(encoded)
        elif mode == ID_BLOCK_DELTA:
            value = encoded if index % BLOCK_IDS == 0 else previous + _unzigzag(encoded)
        else:
            raise ValueError("unknown title-vertex ID mode")
        if value < 0:
            raise ValueError("negative title-vertex ID")
        ids.append(value)
        previous = value
    if position != len(payload):
        raise ValueError("trailing title-vertex ID bytes")
    return ids


def _escape_literal(data: bytes) -> bytes:
    return data.replace(b"\x00", b"\x00\x00")


def _restore_skeleton(
    skeleton: bytes, titles: tuple[bytes, ...], link_ids: list[int]
) -> bytes:
    output = bytearray()
    position = 0
    title_position = 0
    link_position = 0
    while position < len(skeleton):
        byte = skeleton[position]
        position += 1
        if byte != ESCAPE:
            output.append(byte)
            continue
        if position >= len(skeleton):
            raise ValueError("truncated title-vertex escape")
        opcode = skeleton[position]
        position += 1
        if opcode == ESCAPED_ZERO:
            output.append(0)
        elif opcode == TITLE_SLOT:
            if title_position >= len(titles):
                raise ValueError("too many title slots")
            output.extend(titles[title_position])
            title_position += 1
        elif opcode == LINK_SLOT:
            if link_position >= len(link_ids):
                raise ValueError("too many link slots")
            title_id = link_ids[link_position]
            link_position += 1
            if title_id >= len(titles):
                raise ValueError("unknown title-vertex link ID")
            output.extend(titles[title_id])
        else:
            raise ValueError("invalid title-vertex escape")
    if title_position != len(titles) or link_position != len(link_ids):
        raise ValueError("unused title or link entries")
    return bytes(output)


def encode_ir(data: bytes) -> tuple[bytes, dict[str, int | str]]:
    title_rows = _scan_titles(data)
    titles = tuple(title for _start, _end, title in title_rows)
    title_ids: dict[bytes, int] = {}
    for index, title in enumerate(titles):
        title_ids.setdefault(title, index)

    replacements: list[tuple[int, int, int, int | None]] = [
        (start, end, TITLE_SLOT, None)
        for start, end, _title in title_rows
    ]
    matched_link_bytes = 0
    for start, end, base in _scan_link_bases(data):
        title_id = title_ids.get(base)
        if title_id is not None:
            replacements.append((start, end, LINK_SLOT, title_id))
            matched_link_bytes += end - start
    replacements.sort()

    skeleton = bytearray()
    link_ids: list[int] = []
    source_position = 0
    for start, end, opcode, value in replacements:
        if start < source_position:
            raise RuntimeError("overlapping title-vertex replacements")
        skeleton.extend(_escape_literal(data[source_position:start]))
        skeleton.extend((ESCAPE, opcode))
        if opcode == LINK_SLOT:
            assert value is not None
            link_ids.append(value)
        source_position = end
    skeleton.extend(_escape_literal(data[source_position:]))

    dictionary = _encode_dictionary(titles)
    id_mode, id_payload = _encode_ids(link_ids)
    output = bytearray(MAGIC)
    output.extend(_varint(len(titles)))
    output.extend(_varint(len(dictionary)))
    output.extend(dictionary)
    output.extend(_varint(len(skeleton)))
    output.extend(skeleton)
    output.extend(_varint(len(link_ids)))
    output.append(id_mode)
    output.extend(_varint(len(id_payload)))
    output.extend(id_payload)
    return bytes(output), {
        "title_count": len(titles),
        "title_source_bytes": sum(len(title) for title in titles),
        "title_dictionary_bytes": len(dictionary),
        "matched_link_occurrences": len(link_ids),
        "matched_link_source_bytes": matched_link_bytes,
        "skeleton_bytes": len(skeleton),
        "id_stream_mode": ("absolute", "delta", "block_delta")[id_mode],
        "id_stream_bytes": len(id_payload),
        "ir_bytes": len(output),
        "raw_ir_delta_bytes": len(data) - len(output),
    }


def decode_ir(stream: bytes) -> bytes:
    if not stream.startswith(MAGIC):
        raise ValueError("invalid title-vertex WikiIR magic")
    position = len(MAGIC)
    title_count, position = _read_varint(stream, position)
    dictionary_length, position = _read_varint(stream, position)
    dictionary_end = position + dictionary_length
    if dictionary_end > len(stream):
        raise ValueError("truncated title-vertex dictionary")
    titles, decoded_end = _decode_dictionary(stream, position, title_count)
    if decoded_end != dictionary_end:
        raise ValueError("title-vertex dictionary length mismatch")
    position = dictionary_end
    skeleton_length, position = _read_varint(stream, position)
    skeleton_end = position + skeleton_length
    if skeleton_end > len(stream):
        raise ValueError("truncated title-vertex skeleton")
    skeleton = stream[position:skeleton_end]
    position = skeleton_end
    link_count, position = _read_varint(stream, position)
    if position >= len(stream):
        raise ValueError("missing title-vertex ID mode")
    id_mode = stream[position]
    position += 1
    id_length, position = _read_varint(stream, position)
    id_end = position + id_length
    if id_end != len(stream):
        raise ValueError("invalid title-vertex ID stream length")
    link_ids = _decode_ids(id_mode, stream[position:id_end], link_count)
    return _restore_skeleton(skeleton, titles, link_ids)


def compress(data: bytes) -> bytes:
    global _LAST_STATS
    ir, ir_stats = encode_ir(data)
    if decode_ir(ir) != data:
        raise RuntimeError("title-vertex WikiIR internal roundtrip failed")
    literal_archive = lzma.compress(data, preset=PRESET)
    vertex_archive = lzma.compress(ir, preset=PRESET)
    use_vertex = len(vertex_archive) < len(literal_archive)
    selected = vertex_archive if use_vertex else literal_archive
    _LAST_STATS = {
        **ir_stats,
        "literal_archive_bytes": len(literal_archive),
        "vertex_archive_bytes": len(vertex_archive),
        "vertex_archive_gain_before_mode_bytes": len(literal_archive) - len(vertex_archive),
        "selected_mode": "vertex" if use_vertex else "literal",
        "mode_byte_cost": 1,
        "selected_archive_bytes": len(selected) + 1,
        "roundtrip_checked_inside_compress": True,
    }
    return bytes([MODE_VERTEX if use_vertex else MODE_LITERAL]) + selected


def decompress(archive: bytes) -> bytes:
    if not archive:
        raise ValueError("empty title-vertex WikiIR archive")
    decoded = lzma.decompress(archive[1:])
    if archive[0] == MODE_LITERAL:
        return decoded
    if archive[0] == MODE_VERTEX:
        return decode_ir(decoded)
    raise ValueError("invalid title-vertex representation mode")


def stats() -> dict[str, int | str | bool]:
    return dict(_LAST_STATS)
