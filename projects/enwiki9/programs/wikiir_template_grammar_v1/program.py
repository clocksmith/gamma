"""WikiIR ordered-template grammar with an exact MDL fallback.

This discovery candidate parses outer MediaWiki templates into ordered literal
segments and value holes.  Repeated skeletons become explicit grammar rules:

    {{cite web|url=URL|title=TITLE}}
      -> ({{cite web|url=, |title=, }}) + (URL, TITLE)

Unlike the retired template-name macro, named argument keys and punctuation
belong to the reusable rule while only values remain literal.  Rule metadata,
references, hole lengths, literal framing, and a one-byte representation mode
are all present in the archive.  The decoder needs no external table.

The current backend is deliberately the same stdlib LZMA control used by the
older grammar probes.  This program establishes whether the new reversible
representation creates backend-visible bytes; it is not an FX2 integration.
"""

from __future__ import annotations

import lzma


PRESET = 9 | lzma.PRESET_EXTREME
MODE_LITERAL = 0
MODE_GRAMMAR = 1
OP_LITERAL = 0
OP_DEFINE = 1
OP_REFERENCE = 2
MIN_OCCURRENCES = 3
MIN_ESTIMATED_SAVING = 32
MAX_RULES = 65_536

_LAST_STATS: dict[str, int | str | bool] = {}


def _varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint value must be nonnegative")
    encoded = bytearray()
    while value >= 0x80:
        encoded.append((value & 0x7F) | 0x80)
        value >>= 7
    encoded.append(value)
    return bytes(encoded)


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


def _template_end(data: bytes, start: int) -> int | None:
    if data[start : start + 2] != b"{{":
        return None
    depth = 1
    position = start + 2
    while position + 1 < len(data):
        pair = data[position : position + 2]
        if pair == b"{{":
            depth += 1
            position += 2
        elif pair == b"}}":
            depth -= 1
            position += 2
            if depth == 0:
                return position
        else:
            position += 1
    return None


def _top_level_separator_positions(data: bytes, separator: int) -> list[int]:
    positions: list[int] = []
    template_depth = 0
    link_depth = 0
    position = 0
    while position < len(data):
        pair = data[position : position + 2]
        if pair == b"{{":
            template_depth += 1
            position += 2
            continue
        if pair == b"}}" and template_depth:
            template_depth -= 1
            position += 2
            continue
        if pair == b"[[":
            link_depth += 1
            position += 2
            continue
        if pair == b"]]" and link_depth:
            link_depth -= 1
            position += 2
            continue
        if (
            data[position] == separator
            and template_depth == 0
            and link_depth == 0
        ):
            positions.append(position)
        position += 1
    return positions


def _split_top_level(data: bytes, separator: int) -> list[bytes]:
    positions = _top_level_separator_positions(data, separator)
    if not positions:
        return [data]
    parts: list[bytes] = []
    start = 0
    for position in positions:
        parts.append(data[start:position])
        start = position + 1
    parts.append(data[start:])
    return parts


def _first_top_level_equals(argument: bytes) -> int | None:
    positions = _top_level_separator_positions(argument, ord("="))
    return positions[0] if positions else None


def _template_ir(template: bytes) -> tuple[tuple[bytes, ...], tuple[bytes, ...]] | None:
    if len(template) < 4 or not template.startswith(b"{{") or not template.endswith(b"}}"):
        return None
    fields = _split_top_level(template[2:-2], ord("|"))
    if not fields or not fields[0] or len(fields) > 65:
        return None
    segments = [b"{{" + fields[0]]
    holes: list[bytes] = []
    for argument in fields[1:]:
        equals = _first_top_level_equals(argument)
        if equals is None:
            segments.append(b"|")
            holes.append(argument)
        else:
            segments.append(b"|" + argument[: equals + 1])
            holes.append(argument[equals + 1 :])
    segments.append(b"}}")
    return tuple(segments), tuple(holes)


def _event_hole_cost(holes: tuple[bytes, ...]) -> int:
    return sum(len(_varint(len(hole))) + len(hole) for hole in holes)


def _definition_cost(segments: tuple[bytes, ...], holes: tuple[bytes, ...]) -> int:
    return (
        1
        + len(_varint(len(segments)))
        + sum(len(_varint(len(segment))) + len(segment) for segment in segments)
        + _event_hole_cost(holes)
    )


def _reference_cost(rule_id: int, holes: tuple[bytes, ...]) -> int:
    return 1 + len(_varint(rule_id)) + _event_hole_cost(holes)


def _scan(data: bytes) -> list[tuple[int, int, tuple[bytes, ...], tuple[bytes, ...]]]:
    occurrences = []
    position = 0
    while position + 1 < len(data):
        start = data.find(b"{{", position)
        if start < 0:
            break
        end = _template_end(data, start)
        if end is None:
            position = start + 2
            continue
        parsed = _template_ir(data[start:end])
        if parsed is not None:
            segments, holes = parsed
            occurrences.append((start, end, segments, holes))
        position = end
    return occurrences


def _select_rules(
    occurrences: list[tuple[int, int, tuple[bytes, ...], tuple[bytes, ...]]]
) -> dict[tuple[bytes, ...], int]:
    grouped: dict[tuple[bytes, ...], list[tuple[int, int, tuple[bytes, ...]]]] = {}
    first_position: dict[tuple[bytes, ...], int] = {}
    for start, end, segments, holes in occurrences:
        grouped.setdefault(segments, []).append((start, end, holes))
        first_position.setdefault(segments, start)

    candidates: list[tuple[int, tuple[bytes, ...]]] = []
    provisional_id = 0
    for segments in sorted(grouped, key=first_position.__getitem__):
        rows = grouped[segments]
        if len(rows) < MIN_OCCURRENCES:
            continue
        literal_bytes = sum(end - start for start, end, _holes in rows)
        encoded_bytes = _definition_cost(segments, rows[0][2])
        encoded_bytes += sum(
            _reference_cost(provisional_id, holes)
            for _start, _end, holes in rows[1:]
        )
        # Charge one conservative literal-run boundary byte at each side of
        # every occurrence in addition to the explicit event costs.
        estimated_saving = literal_bytes - encoded_bytes - 2 * len(rows)
        if estimated_saving >= MIN_ESTIMATED_SAVING:
            candidates.append((first_position[segments], segments))
            provisional_id += 1
        if len(candidates) >= MAX_RULES:
            break
    candidates.sort()
    return {segments: rule_id for rule_id, (_position, segments) in enumerate(candidates)}


def _emit_literal(output: bytearray, literal: bytes) -> None:
    if not literal:
        return
    output.append(OP_LITERAL)
    output.extend(_varint(len(literal)))
    output.extend(literal)


def encode_ir(data: bytes) -> tuple[bytes, dict[str, int]]:
    occurrences = _scan(data)
    rules = _select_rules(occurrences)
    defined: set[int] = set()
    output = bytearray()
    literal_start = 0
    references = 0
    captured_bytes = 0

    for start, end, segments, holes in occurrences:
        rule_id = rules.get(segments)
        if rule_id is None:
            continue
        _emit_literal(output, data[literal_start:start])
        captured_bytes += end - start
        if rule_id not in defined:
            output.append(OP_DEFINE)
            output.extend(_varint(len(segments)))
            for segment in segments:
                output.extend(_varint(len(segment)))
                output.extend(segment)
            defined.add(rule_id)
        else:
            output.append(OP_REFERENCE)
            output.extend(_varint(rule_id))
            references += 1
        for hole in holes:
            output.extend(_varint(len(hole)))
            output.extend(hole)
        literal_start = end

    _emit_literal(output, data[literal_start:])
    return bytes(output), {
        "templates_parsed": len(occurrences),
        "rules_admitted": len(rules),
        "rule_definitions": len(defined),
        "rule_references": references,
        "captured_source_bytes": captured_bytes,
        "ir_bytes": len(output),
        "raw_ir_delta_bytes": len(data) - len(output),
    }


def decode_ir(stream: bytes) -> bytes:
    output = bytearray()
    rules: list[tuple[bytes, ...]] = []
    position = 0
    while position < len(stream):
        opcode = stream[position]
        position += 1
        if opcode == OP_LITERAL:
            length, position = _read_varint(stream, position)
            end = position + length
            if end > len(stream):
                raise ValueError("truncated WikiIR literal")
            output.extend(stream[position:end])
            position = end
            continue
        if opcode == OP_DEFINE:
            segment_count, position = _read_varint(stream, position)
            if segment_count < 1 or segment_count > 66:
                raise ValueError("invalid WikiIR segment count")
            segments = []
            for _ in range(segment_count):
                length, position = _read_varint(stream, position)
                end = position + length
                if end > len(stream):
                    raise ValueError("truncated WikiIR rule segment")
                segments.append(stream[position:end])
                position = end
            rules.append(tuple(segments))
            rule = rules[-1]
        elif opcode == OP_REFERENCE:
            rule_id, position = _read_varint(stream, position)
            if rule_id >= len(rules):
                raise ValueError("unknown WikiIR rule reference")
            rule = rules[rule_id]
        else:
            raise ValueError(f"unknown WikiIR opcode {opcode}")

        if len(rule) < 2:
            raise ValueError("WikiIR rule lacks a terminal segment")
        output.extend(rule[0])
        for segment in rule[1:-1]:
            output.extend(segment)
            length, position = _read_varint(stream, position)
            end = position + length
            if end > len(stream):
                raise ValueError("truncated WikiIR hole")
            output.extend(stream[position:end])
            position = end
        output.extend(rule[-1])
    return bytes(output)


def compress(data: bytes) -> bytes:
    global _LAST_STATS
    ir, ir_stats = encode_ir(data)
    literal_archive = lzma.compress(data, preset=PRESET)
    grammar_archive = lzma.compress(ir, preset=PRESET)
    use_grammar = len(grammar_archive) < len(literal_archive)
    selected = grammar_archive if use_grammar else literal_archive
    _LAST_STATS = {
        **ir_stats,
        "literal_archive_bytes": len(literal_archive),
        "grammar_archive_bytes": len(grammar_archive),
        "grammar_archive_gain_before_mode_bytes": (
            len(literal_archive) - len(grammar_archive)
        ),
        "selected_mode": "grammar" if use_grammar else "literal",
        "mode_byte_cost": 1,
        "selected_archive_bytes": len(selected) + 1,
        "roundtrip_checked_inside_compress": decode_ir(ir) == data,
    }
    return bytes([MODE_GRAMMAR if use_grammar else MODE_LITERAL]) + selected


def decompress(archive: bytes) -> bytes:
    if not archive:
        raise ValueError("empty WikiIR archive")
    decoded = lzma.decompress(archive[1:])
    if archive[0] == MODE_LITERAL:
        return decoded
    if archive[0] == MODE_GRAMMAR:
        return decode_ir(decoded)
    raise ValueError("unknown WikiIR representation mode")


def stats() -> dict[str, int | str | bool]:
    return dict(_LAST_STATS)
