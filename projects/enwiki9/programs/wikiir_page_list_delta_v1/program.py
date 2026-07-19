"""Exact causal prior-page link-list delta transform for WikiIR-MDL.

Each completed XML page may cite an already decoded page.  The current page's
ordered MediaWiki link targets are then emitted as COPY ranges and literal ADD
runs, while an escaped byte skeleton retains every byte outside those target
spans.  The reference distance and inverse program are explicit; no page
ordering, external index, or future text is used by the decoder.

This is deliberately a representation probe.  It falls back page-by-page to
literal bytes whenever the complete delta event is not smaller before backend
compression, so every claimed raw-IR saving includes skeleton and command
costs rather than only target-list overlap.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import difflib
import lzma


PRESET = 9 | lzma.PRESET_EXTREME
MAGIC = b"WPL1"
MODE_LITERAL = 0
MODE_DELTA = 1
OP_COPY = 0
OP_ADD = 1
ESCAPE = 0
ESCAPED_ZERO = 0
TARGET_SLOT = 1
MAX_TARGET_BYTES = 1_024
MAX_CANDIDATES = 16

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


def _scan_targets(data: bytes) -> tuple[tuple[int, int, bytes], ...]:
    """Return nonoverlapping, exact link-target byte spans in occurrence order."""

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
            target
            and len(target) <= MAX_TARGET_BYTES
            and b"\n" not in target
            and b"\r" not in target
        ):
            rows.append((start, end, target))
        position = closing + 2
    return tuple(rows)


def _escape_literal(data: bytes) -> bytes:
    return data.replace(b"\x00", b"\x00\x00")


def _skeleton(page: bytes, rows: tuple[tuple[int, int, bytes], ...]) -> bytes:
    output = bytearray()
    position = 0
    for start, end, _target in rows:
        output.extend(_escape_literal(page[position:start]))
        output.extend((ESCAPE, TARGET_SLOT))
        position = end
    output.extend(_escape_literal(page[position:]))
    return bytes(output)


def _matching_blocks(
    prior: tuple[bytes, ...], current: tuple[bytes, ...]
) -> tuple[tuple[int, int, int], ...]:
    matcher = difflib.SequenceMatcher(a=prior, b=current, autojunk=False)
    return tuple(
        (block.a, block.b, block.size)
        for block in matcher.get_matching_blocks()
        if block.size
    )


def _operations(
    prior: tuple[bytes, ...], current: tuple[bytes, ...]
) -> tuple[tuple[int, int, int] | tuple[int, tuple[bytes, ...]], ...]:
    """Emit monotone COPY and ADD operations covering every current target."""

    output: list[tuple[int, int, int] | tuple[int, tuple[bytes, ...]]] = []
    position = 0
    for source, destination, length in _matching_blocks(prior, current):
        if destination < position or source + length > len(prior):
            raise ValueError("invalid sequence matcher block")
        if position < destination:
            output.append((OP_ADD, current[position:destination]))
        output.append((OP_COPY, source, length))
        position = destination + length
    if position < len(current):
        output.append((OP_ADD, current[position:]))
    return tuple(output)


def _encode_delta_event(
    reference_distance: int,
    page: bytes,
    rows: tuple[tuple[int, int, bytes], ...],
    prior_targets: tuple[bytes, ...],
) -> bytes:
    if reference_distance < 1:
        raise ValueError("reference distance must be positive")
    current_targets = tuple(target for _start, _end, target in rows)
    skeleton = _skeleton(page, rows)
    operations = _operations(prior_targets, current_targets)
    output = bytearray((MODE_DELTA,))
    output.extend(_varint(reference_distance))
    output.extend(_varint(len(skeleton)))
    output.extend(skeleton)
    output.extend(_varint(len(operations)))
    for operation in operations:
        output.append(operation[0])
        if operation[0] == OP_COPY:
            _mode, source, length = operation
            output.extend(_varint(source))
            output.extend(_varint(length))
        else:
            _mode, values = operation
            output.extend(_varint(len(values)))
            for value in values:
                output.extend(_varint(len(value)))
                output.extend(value)
    return bytes(output)


def _literal_event(page: bytes) -> bytes:
    return bytes((MODE_LITERAL,)) + _varint(len(page)) + page


def _candidate_prior_ids(
    targets: tuple[bytes, ...], postings: dict[bytes, list[int]]
) -> tuple[int, ...]:
    overlap: Counter[int] = Counter()
    for target in set(targets):
        overlap.update(postings.get(target, ()))
    return tuple(
        ordinal
        for ordinal, _count in sorted(
            overlap.items(), key=lambda item: (-item[1], -item[0])
        )[:MAX_CANDIDATES]
    )


def _split_pages(raw: bytes) -> tuple[bytes, tuple[tuple[bytes, bytes], ...], bytes]:
    """Return prefix, complete page/gap pairs, and suffix without dropping bytes."""

    pages: list[tuple[bytes, bytes]] = []
    first = raw.find(b"<page>")
    if first < 0:
        return raw, (), b""
    prefix = raw[:first]
    position = first
    while raw.startswith(b"<page>", position):
        close = raw.find(b"</page>", position + len(b"<page>"))
        if close < 0:
            break
        end = close + len(b"</page>")
        next_page = raw.find(b"<page>", end)
        if next_page < 0:
            pages.append((raw[position:end], b""))
            return prefix, tuple(pages), raw[end:]
        pages.append((raw[position:end], raw[end:next_page]))
        position = next_page
    return prefix, tuple(pages), raw[position:]


def encode_ir(data: bytes) -> tuple[bytes, dict[str, int | str]]:
    prefix, pages, suffix = _split_pages(data)
    output = bytearray(MAGIC)
    output.extend(_varint(len(prefix)))
    output.extend(prefix)
    output.extend(_varint(len(pages)))
    postings: dict[bytes, list[int]] = defaultdict(list)
    prior_targets: list[tuple[bytes, ...]] = []
    literal_pages = 0
    delta_pages = 0
    candidate_pages = 0
    delta_event_savings = 0
    copied_targets = 0
    copy_operations = 0

    for ordinal, (page, gap) in enumerate(pages):
        rows = _scan_targets(page)
        targets = tuple(target for _start, _end, target in rows)
        literal = _literal_event(page)
        selected = literal
        candidates = _candidate_prior_ids(targets, postings)
        if candidates:
            candidate_pages += 1
            choices = []
            for prior in candidates:
                candidate = _encode_delta_event(
                    ordinal - prior, page, rows, prior_targets[prior]
                )
                choices.append((len(candidate), -prior, candidate, prior))
            _length, _inverse_prior, candidate, prior = min(choices)
            if len(candidate) < len(literal):
                selected = candidate
                delta_pages += 1
                delta_event_savings += len(literal) - len(candidate)
                for operation in _operations(prior_targets[prior], targets):
                    if operation[0] == OP_COPY:
                        _mode, source, length = operation
                        copied_targets += length
                        copy_operations += 1
        if selected is literal:
            literal_pages += 1
        output.extend(selected)
        output.extend(_varint(len(gap)))
        output.extend(gap)
        prior_targets.append(targets)
        for target in set(targets):
            postings[target].append(ordinal)

    output.extend(_varint(len(suffix)))
    output.extend(suffix)
    stats: dict[str, int | str] = {
        "pages": len(pages),
        "pages_with_reference_candidates": candidate_pages,
        "literal_pages": literal_pages,
        "delta_pages": delta_pages,
        "delta_event_savings_bytes": delta_event_savings,
        "copied_target_occurrences": copied_targets,
        "copy_operations": copy_operations,
        "ir_bytes": len(output),
        "raw_ir_delta_bytes": len(data) - len(output),
        "candidate_limit": MAX_CANDIDATES,
    }
    return bytes(output), stats


def _restore_skeleton(skeleton: bytes, targets: tuple[bytes, ...]) -> bytes:
    output = bytearray()
    position = 0
    target_position = 0
    while position < len(skeleton):
        byte = skeleton[position]
        position += 1
        if byte != ESCAPE:
            output.append(byte)
            continue
        if position >= len(skeleton):
            raise ValueError("truncated page-list skeleton escape")
        opcode = skeleton[position]
        position += 1
        if opcode == ESCAPED_ZERO:
            output.append(ESCAPE)
        elif opcode == TARGET_SLOT:
            if target_position >= len(targets):
                raise ValueError("too many page-list skeleton target slots")
            output.extend(targets[target_position])
            target_position += 1
        else:
            raise ValueError("invalid page-list skeleton escape")
    if target_position != len(targets):
        raise ValueError("unused page-list targets")
    return bytes(output)


def _decode_delta_event(
    stream: bytes, position: int, previous: list[tuple[bytes, tuple[bytes, ...]]]
) -> tuple[bytes, int]:
    distance, position = _read_varint(stream, position)
    if distance < 1 or distance > len(previous):
        raise ValueError("invalid prior-page reference distance")
    skeleton_length, position = _read_varint(stream, position)
    skeleton_end = position + skeleton_length
    if skeleton_end > len(stream):
        raise ValueError("truncated page-list skeleton")
    skeleton = stream[position:skeleton_end]
    position = skeleton_end
    operation_count, position = _read_varint(stream, position)
    prior_targets = previous[-distance][1]
    targets: list[bytes] = []
    for _ in range(operation_count):
        if position >= len(stream):
            raise ValueError("truncated page-list operation")
        opcode = stream[position]
        position += 1
        if opcode == OP_COPY:
            source, position = _read_varint(stream, position)
            length, position = _read_varint(stream, position)
            if length < 1 or source + length > len(prior_targets):
                raise ValueError("invalid page-list COPY range")
            targets.extend(prior_targets[source : source + length])
        elif opcode == OP_ADD:
            count, position = _read_varint(stream, position)
            if count < 1:
                raise ValueError("empty page-list ADD run")
            for _ in range(count):
                length, position = _read_varint(stream, position)
                if length < 1 or length > MAX_TARGET_BYTES:
                    raise ValueError("invalid page-list ADD target length")
                end = position + length
                if end > len(stream):
                    raise ValueError("truncated page-list ADD target")
                targets.append(stream[position:end])
                position = end
        else:
            raise ValueError("unknown page-list operation")
    page = _restore_skeleton(skeleton, tuple(targets))
    if tuple(target for _start, _end, target in _scan_targets(page)) != tuple(targets):
        raise ValueError("page-list decoded targets do not match skeleton")
    return page, position


def decode_ir(stream: bytes) -> bytes:
    if not stream.startswith(MAGIC):
        raise ValueError("invalid WikiIR page-list magic")
    position = len(MAGIC)
    prefix_length, position = _read_varint(stream, position)
    prefix_end = position + prefix_length
    if prefix_end > len(stream):
        raise ValueError("truncated page-list prefix")
    output = bytearray(stream[position:prefix_end])
    position = prefix_end
    page_count, position = _read_varint(stream, position)
    previous: list[tuple[bytes, tuple[bytes, ...]]] = []
    for _ in range(page_count):
        if position >= len(stream):
            raise ValueError("truncated page-list event mode")
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
            page, position = _decode_delta_event(stream, position, previous)
        else:
            raise ValueError("unknown page-list event mode")
        targets = tuple(target for _start, _end, target in _scan_targets(page))
        previous.append((page, targets))
        output.extend(page)
        gap_length, position = _read_varint(stream, position)
        gap_end = position + gap_length
        if gap_end > len(stream):
            raise ValueError("truncated page-list inter-page gap")
        output.extend(stream[position:gap_end])
        position = gap_end
    suffix_length, position = _read_varint(stream, position)
    suffix_end = position + suffix_length
    if suffix_end != len(stream):
        raise ValueError("invalid page-list suffix length")
    output.extend(stream[position:suffix_end])
    return bytes(output)


def compress(data: bytes) -> bytes:
    global _LAST_STATS
    ir, ir_stats = encode_ir(data)
    if decode_ir(ir) != data:
        raise RuntimeError("WikiIR page-list internal roundtrip failed")
    literal_archive = lzma.compress(data, preset=PRESET)
    delta_archive = lzma.compress(ir, preset=PRESET)
    use_delta = len(delta_archive) < len(literal_archive)
    selected = delta_archive if use_delta else literal_archive
    _LAST_STATS = {
        **ir_stats,
        "literal_archive_bytes": len(literal_archive),
        "delta_archive_bytes": len(delta_archive),
        "delta_archive_gain_before_mode_bytes": len(literal_archive) - len(delta_archive),
        "selected_mode": "delta" if use_delta else "literal",
        "mode_byte_cost": 1,
        "selected_archive_bytes": len(selected) + 1,
        "roundtrip_checked_inside_compress": True,
    }
    return bytes((MODE_DELTA if use_delta else MODE_LITERAL,)) + selected


def decompress(archive: bytes) -> bytes:
    if not archive:
        raise ValueError("empty WikiIR page-list archive")
    decoded = lzma.decompress(archive[1:])
    if archive[0] == MODE_LITERAL:
        return decoded
    if archive[0] == MODE_DELTA:
        return decode_ir(decoded)
    raise ValueError("invalid WikiIR page-list representation mode")


def stats() -> dict[str, int | str | bool]:
    return dict(_LAST_STATS)
