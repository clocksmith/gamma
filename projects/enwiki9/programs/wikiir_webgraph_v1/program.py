"""Exact WikiIR link-target dictionary and ordered graph stream.

This discovery transform separates repeated MediaWiki link targets from their
surface positions.  A front-coded global target dictionary and a compact
ordered identifier stream describe the graph column; an escaped text skeleton
retains delimiters, labels, whitespace, malformed bytes, and every nonselected
target exactly.  The representation is deliberately reversible without an
external index or model.

The first version tests whether target-list structure creates information the
literal backend can use.  It does not reorder links: occurrence order is the
inverse-position stream, so no hidden permutation or semantic oracle exists.
"""

from __future__ import annotations

from collections import Counter
import lzma


PRESET = 9 | lzma.PRESET_EXTREME
MAGIC = b"WGL1"
MODE_LITERAL = 0
MODE_GRAPH = 1
ID_ABSOLUTE = 0
ID_DELTA = 1
ID_BLOCK_DELTA = 2
BLOCK_IDS = 64
MAX_TARGET_BYTES = 1_024
MIN_RULE_SAVING = 4
ESCAPE = 0
ESCAPED_ZERO = 0
TARGET_SLOT = 1

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


def _scan_targets(data: bytes) -> list[tuple[int, int, bytes]]:
    """Return nonoverlapping target byte ranges from bracketed wiki links."""

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
        separator = data.find(b"|", start, closing)
        end = separator if separator >= 0 else closing
        target = data[start:end]
        if (
            0 < len(target) <= MAX_TARGET_BYTES
            and b"\n" not in target
            and b"\r" not in target
        ):
            rows.append((start, end, target))
        position = closing + 2
    return rows


def _select_targets(rows: list[tuple[int, int, bytes]]) -> tuple[bytes, ...]:
    counts = Counter(target for _start, _end, target in rows)
    selected = []
    for target, count in counts.items():
        if count < 2:
            continue
        # Charge a two-byte escaped slot, a conservative two-byte ID per use,
        # dictionary framing, and a minimum margin.  Front coding and actual
        # varint selection are measured separately in the final receipt.
        estimated = count * len(target) - count * 4 - len(target) - 4
        if estimated >= MIN_RULE_SAVING:
            selected.append(target)
    return tuple(sorted(selected))


def _encode_dictionary(targets: tuple[bytes, ...]) -> bytes:
    output = bytearray()
    previous = b""
    for target in targets:
        prefix = _common_prefix(previous, target)
        suffix = target[prefix:]
        output.extend(_varint(prefix))
        output.extend(_varint(len(suffix)))
        output.extend(suffix)
        previous = target
    return bytes(output)


def _decode_dictionary(
    stream: bytes, position: int, count: int
) -> tuple[tuple[bytes, ...], int]:
    targets: list[bytes] = []
    previous = b""
    for _ in range(count):
        prefix, position = _read_varint(stream, position)
        suffix_length, position = _read_varint(stream, position)
        if prefix > len(previous):
            raise ValueError("invalid front-coded target prefix")
        end = position + suffix_length
        if end > len(stream):
            raise ValueError("truncated front-coded target")
        target = previous[:prefix] + stream[position:end]
        if not target or (targets and target <= targets[-1]):
            raise ValueError("invalid target dictionary ordering")
        targets.append(target)
        previous = target
        position = end
    return tuple(targets), position


def _encode_ids(ids: list[int]) -> tuple[int, bytes]:
    absolute = b"".join(_varint(value) for value in ids)

    delta_output = bytearray()
    previous = 0
    for value in ids:
        delta_output.extend(_varint(_zigzag(value - previous)))
        previous = value

    block_output = bytearray()
    previous = 0
    for index, value in enumerate(ids):
        if index % BLOCK_IDS == 0:
            block_output.extend(_varint(value))
        else:
            block_output.extend(_varint(_zigzag(value - previous)))
        previous = value

    choices = (
        (ID_ABSOLUTE, absolute),
        (ID_DELTA, bytes(delta_output)),
        (ID_BLOCK_DELTA, bytes(block_output)),
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
            raise ValueError("unknown link-target ID mode")
        if value < 0:
            raise ValueError("negative link-target ID")
        ids.append(value)
        previous = value
    if position != len(payload):
        raise ValueError("trailing bytes in link-target ID stream")
    return ids


def _escape_literal(data: bytes) -> bytes:
    return data.replace(b"\x00", b"\x00\x00")


def _restore_skeleton(
    skeleton: bytes, ids: list[int], targets: tuple[bytes, ...]
) -> bytes:
    output = bytearray()
    position = 0
    id_position = 0
    while position < len(skeleton):
        byte = skeleton[position]
        position += 1
        if byte != ESCAPE:
            output.append(byte)
            continue
        if position >= len(skeleton):
            raise ValueError("truncated graph skeleton escape")
        opcode = skeleton[position]
        position += 1
        if opcode == ESCAPED_ZERO:
            output.append(0)
        elif opcode == TARGET_SLOT:
            if id_position >= len(ids):
                raise ValueError("graph skeleton has too many target slots")
            target_id = ids[id_position]
            id_position += 1
            if target_id >= len(targets):
                raise ValueError("unknown graph target ID")
            output.extend(targets[target_id])
        else:
            raise ValueError("invalid graph skeleton escape")
    if id_position != len(ids):
        raise ValueError("unused link-target IDs")
    return bytes(output)


def encode_ir(data: bytes) -> tuple[bytes, dict[str, int | str]]:
    rows = _scan_targets(data)
    targets = _select_targets(rows)
    target_ids = {target: index for index, target in enumerate(targets)}

    skeleton = bytearray()
    ids: list[int] = []
    source_position = 0
    selected_source_bytes = 0
    for start, end, target in rows:
        target_id = target_ids.get(target)
        if target_id is None:
            continue
        skeleton.extend(_escape_literal(data[source_position:start]))
        skeleton.extend((ESCAPE, TARGET_SLOT))
        ids.append(target_id)
        selected_source_bytes += end - start
        source_position = end
    skeleton.extend(_escape_literal(data[source_position:]))

    dictionary = _encode_dictionary(targets)
    id_mode, id_payload = _encode_ids(ids)
    output = bytearray(MAGIC)
    output.extend(_varint(len(targets)))
    output.extend(_varint(len(dictionary)))
    output.extend(dictionary)
    output.extend(_varint(len(skeleton)))
    output.extend(skeleton)
    output.extend(_varint(len(ids)))
    output.append(id_mode)
    output.extend(_varint(len(id_payload)))
    output.extend(id_payload)
    stats: dict[str, int | str] = {
        "links_parsed": len(rows),
        "selected_target_types": len(targets),
        "selected_target_occurrences": len(ids),
        "selected_source_target_bytes": selected_source_bytes,
        "dictionary_bytes": len(dictionary),
        "skeleton_bytes": len(skeleton),
        "id_stream_mode": ("absolute", "delta", "block_delta")[id_mode],
        "id_stream_bytes": len(id_payload),
        "ir_bytes": len(output),
        "raw_ir_delta_bytes": len(data) - len(output),
    }
    return bytes(output), stats


def decode_ir(stream: bytes) -> bytes:
    if not stream.startswith(MAGIC):
        raise ValueError("invalid WikiIR WebGraph magic")
    position = len(MAGIC)
    target_count, position = _read_varint(stream, position)
    dictionary_length, position = _read_varint(stream, position)
    dictionary_end = position + dictionary_length
    if dictionary_end > len(stream):
        raise ValueError("truncated graph dictionary stream")
    targets, decoded_end = _decode_dictionary(stream, position, target_count)
    if decoded_end != dictionary_end:
        raise ValueError("graph dictionary length mismatch")
    position = dictionary_end

    skeleton_length, position = _read_varint(stream, position)
    skeleton_end = position + skeleton_length
    if skeleton_end > len(stream):
        raise ValueError("truncated graph skeleton")
    skeleton = stream[position:skeleton_end]
    position = skeleton_end

    id_count, position = _read_varint(stream, position)
    if position >= len(stream):
        raise ValueError("missing graph ID mode")
    id_mode = stream[position]
    position += 1
    id_length, position = _read_varint(stream, position)
    id_end = position + id_length
    if id_end != len(stream):
        raise ValueError("invalid graph ID stream length")
    ids = _decode_ids(id_mode, stream[position:id_end], id_count)
    return _restore_skeleton(skeleton, ids, targets)


def compress(data: bytes) -> bytes:
    global _LAST_STATS
    ir, ir_stats = encode_ir(data)
    if decode_ir(ir) != data:
        raise RuntimeError("WikiIR WebGraph internal roundtrip failed")
    literal_archive = lzma.compress(data, preset=PRESET)
    graph_archive = lzma.compress(ir, preset=PRESET)
    use_graph = len(graph_archive) < len(literal_archive)
    selected = graph_archive if use_graph else literal_archive
    _LAST_STATS = {
        **ir_stats,
        "literal_archive_bytes": len(literal_archive),
        "graph_archive_bytes": len(graph_archive),
        "graph_archive_gain_before_mode_bytes": len(literal_archive) - len(graph_archive),
        "selected_mode": "graph" if use_graph else "literal",
        "mode_byte_cost": 1,
        "selected_archive_bytes": len(selected) + 1,
        "roundtrip_checked_inside_compress": True,
    }
    return bytes([MODE_GRAPH if use_graph else MODE_LITERAL]) + selected


def decompress(archive: bytes) -> bytes:
    if not archive:
        raise ValueError("empty WikiIR WebGraph archive")
    decoded = lzma.decompress(archive[1:])
    if archive[0] == MODE_LITERAL:
        return decoded
    if archive[0] == MODE_GRAPH:
        return decode_ir(decoded)
    raise ValueError("invalid WikiIR WebGraph representation mode")


def stats() -> dict[str, int | str | bool]:
    return dict(_LAST_STATS)
