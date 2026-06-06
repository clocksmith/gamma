"""wikilink_parser — Phase 2A: conservative [[wikilink]] extraction.

Walks the post-XML scaffold finding [[ ]] pairs. Strict
conservative-abort discipline:
  - aborts on nested [[ ]] (one level only)
  - aborts if inner contains {{ or }} (template residue)
  - aborts on multi-piped (3+ parts split on |): [[Image:X|caption|param]]
  - aborts if target is empty after trim
  - per-instance reconstruction must byte-equal the original

Extraction order in program.py: wikilinks FIRST, templates SECOND. This
way wikilinks inside template parameter values (e.g. {{cite|url=[[X]]}})
are extracted as wikilinks — they would otherwise be locked inside the
template's canonical value bytes if templates were extracted first.

For accepted wikilinks, emits a record (target, display_or_None, masks):
  simple [[X]]:   target=X, display=None, masks=[lead, trail]              (2)
  piped  [[X|Y]]: target=X, display=Y,    masks=[t_lead, t_trail,
                                                  d_lead, d_trail]          (4)

Both [[X]] (article links) and [[Category:X]] (category links) flow
through this single extractor. Phase 3 columnar transposition can split
by target prefix later.

Sentinel: WIKILINK_SENTINEL = b"\\x00\\x00\\xFE\\xFB". Each successful
extraction replaces the wikilink's raw bytes with this sentinel.
"""

from __future__ import annotations

import struct

WIKILINK_SENTINEL = b"\x00\x00\xFE\xFB"
MAX_WIKILINK_BYTES = 4096


def find_wikilink_end(data: bytes, start: int) -> int | None:
    """Find position right after matching ]] for [[ at start.
    Returns None if a nested [[ is encountered or no balanced match
    within MAX_WIKILINK_BYTES."""
    i = start + 2
    n = len(data)
    end_limit = min(n, start + MAX_WIKILINK_BYTES)
    while i < end_limit:
        if i + 1 < end_limit:
            tok = data[i : i + 2]
            if tok == b"[[":
                return None  # conservative-abort: nested wikilink
            if tok == b"]]":
                return i + 2
        i += 1
    return None


def _ws_split(b: bytes) -> tuple[bytes, bytes, bytes]:
    stripped = b.strip()
    if not stripped:
        return b"", b"", b""
    start = b.find(stripped)
    end = start + len(stripped)
    return b[:start], stripped, b[end:]


def parse_wikilink_inner(inner: bytes):
    """Parse the bytes between [[ and ]]. Returns (target, display, masks)
    or None on conservative abort."""
    if b"{{" in inner or b"}}" in inner:
        return None  # template residue inside wikilink
    parts = inner.split(b"|", 2)
    if len(parts) > 2:
        return None  # multi-piped — abort

    target_raw = parts[0]
    target_lead, canonical_target, target_trail = _ws_split(target_raw)
    if not canonical_target:
        return None

    if len(parts) == 1:
        return canonical_target, None, [target_lead, target_trail]

    display_raw = parts[1]
    display_lead, canonical_display, display_trail = _ws_split(display_raw)
    return (
        canonical_target,
        canonical_display,
        [target_lead, target_trail, display_lead, display_trail],
    )


def reconstruct_wikilink(target: bytes, display, masks: list) -> bytes:
    out = bytearray(b"[[")
    out.extend(masks[0])
    out.extend(target)
    out.extend(masks[1])
    if display is not None:
        out.extend(b"|")
        out.extend(masks[2])
        out.extend(display)
        out.extend(masks[3])
    out.extend(b"]]")
    return bytes(out)


def extract_wikilinks(scaffold: bytes) -> tuple[bytes, list]:
    """Walk scaffold; for each [[...]] that parses + reconstructs
    byte-perfectly, replace with WIKILINK_SENTINEL and record
    (target, display, masks). Else leave bytes alone.

    Returns (new_scaffold, records).
    """
    out = bytearray()
    records: list = []
    i = 0
    n = len(scaffold)
    while i < n:
        if i + 1 < n and scaffold[i] == 0x5B and scaffold[i + 1] == 0x5B:
            end = find_wikilink_end(scaffold, i)
            if end is not None:
                raw = scaffold[i:end]
                inner = raw[2:-2]
                parsed = parse_wikilink_inner(inner)
                if parsed is not None:
                    target, display, masks = parsed
                    try:
                        rebuilt = reconstruct_wikilink(target, display, masks)
                    except Exception:
                        rebuilt = None
                    if rebuilt == raw:
                        out.extend(WIKILINK_SENTINEL)
                        records.append((target, display, masks))
                        i = end
                        continue
            out.append(scaffold[i])
            i += 1
        else:
            out.append(scaffold[i])
            i += 1
    return bytes(out), records


def reconstruct_scaffold(new_scaffold: bytes, records: list) -> bytes:
    out = bytearray()
    record_iter = iter(records)
    i = 0
    n = len(new_scaffold)
    while i < n:
        if i + 4 <= n and new_scaffold[i : i + 4] == WIKILINK_SENTINEL:
            try:
                target, display, masks = next(record_iter)
            except StopIteration:
                raise ValueError("wikilink record underflow")
            out.extend(reconstruct_wikilink(target, display, masks))
            i += 4
        else:
            out.append(new_scaffold[i])
            i += 1
    try:
        next(record_iter)
        raise ValueError("wikilink record overflow")
    except StopIteration:
        pass
    return bytes(out)


def serialize_records(records: list) -> tuple[bytes, bytes]:
    tuples = bytearray(struct.pack(">I", len(records)))
    masks_buf = bytearray(struct.pack(">I", len(records)))
    for target, display, masks in records:
        tuples.extend(struct.pack(">H", len(target)))
        tuples.extend(target)
        if display is None:
            tuples.append(0)
        else:
            tuples.append(1)
            tuples.extend(struct.pack(">H", len(display)))
            tuples.extend(display)
        masks_buf.extend(struct.pack(">H", len(masks)))
        for piece in masks:
            masks_buf.extend(struct.pack(">H", len(piece)))
            masks_buf.extend(piece)
    return bytes(tuples), bytes(masks_buf)


def serialize_records_dictcoded(records: list) -> tuple[bytes, bytes, bytes]:
    """Phase 4: dict-code wikilink targets.

    Returns (targets_dict_bytes, tuples_buf, masks_buf). tuples_buf:
        varint(record_count)
        per record:
            varint(target_dict_idx)
            1B has_display
            if display: varint(display_len) + display_bytes
    masks_buf:
        varint(record_count)
        per record:
            varint(mask_piece_count)
            per piece: varint(piece_len) + piece_bytes
    """
    import dict_codec as DC

    all_targets = [target for target, _, _ in records]
    targets_dict_bytes, target_to_idx = DC.build_dict(all_targets)

    tuples = bytearray()
    masks_buf = bytearray()
    DC.write_varint(tuples, len(records))
    DC.write_varint(masks_buf, len(records))

    for target, display, masks in records:
        DC.write_varint(tuples, target_to_idx[target])
        if display is None:
            tuples.append(0)
        else:
            tuples.append(1)
            DC.write_varint(tuples, len(display))
            tuples.extend(display)
        DC.write_varint(masks_buf, len(masks))
        for piece in masks:
            DC.write_varint(masks_buf, len(piece))
            masks_buf.extend(piece)

    return targets_dict_bytes, bytes(tuples), bytes(masks_buf)


def parse_records_dictcoded(
    targets_dict_bytes: bytes,
    tuples_buf: bytes,
    masks_buf: bytes,
) -> list:
    import dict_codec as DC

    targets = DC.parse_dict(targets_dict_bytes)

    pos_t = 0
    pos_m = 0
    n_t, pos_t = DC.read_varint(tuples_buf, pos_t)
    n_m, pos_m = DC.read_varint(masks_buf, pos_m)
    if n_t != n_m:
        raise ValueError(f"record count mismatch: {n_t} vs {n_m}")

    records = []
    for _ in range(n_t):
        target_idx, pos_t = DC.read_varint(tuples_buf, pos_t)
        target = targets[target_idx]
        flag = tuples_buf[pos_t]
        pos_t += 1
        if flag == 0:
            display = None
        else:
            d_len, pos_t = DC.read_varint(tuples_buf, pos_t)
            display = tuples_buf[pos_t : pos_t + d_len]
            pos_t += d_len
        mask_count, pos_m = DC.read_varint(masks_buf, pos_m)
        masks = []
        for _ in range(mask_count):
            piece_len, pos_m = DC.read_varint(masks_buf, pos_m)
            masks.append(masks_buf[pos_m : pos_m + piece_len])
            pos_m += piece_len
        records.append((target, display, masks))
    return records


def parse_records(tuples_buf: bytes, masks_buf: bytes) -> list:
    pos_t = 0
    pos_m = 0
    (n_t,) = struct.unpack(">I", tuples_buf[pos_t : pos_t + 4])
    pos_t += 4
    (n_m,) = struct.unpack(">I", masks_buf[pos_m : pos_m + 4])
    pos_m += 4
    if n_t != n_m:
        raise ValueError(
            f"wikilink record count mismatch: tuples={n_t} masks={n_m}"
        )
    records: list = []
    for _ in range(n_t):
        (target_len,) = struct.unpack(">H", tuples_buf[pos_t : pos_t + 2])
        pos_t += 2
        target = tuples_buf[pos_t : pos_t + target_len]
        pos_t += target_len
        flag = tuples_buf[pos_t]
        pos_t += 1
        if flag == 0:
            display = None
        else:
            (display_len,) = struct.unpack(">H", tuples_buf[pos_t : pos_t + 2])
            pos_t += 2
            display = tuples_buf[pos_t : pos_t + display_len]
            pos_t += display_len
        (mask_count,) = struct.unpack(">H", masks_buf[pos_m : pos_m + 2])
        pos_m += 2
        masks: list = []
        for _ in range(mask_count):
            (piece_len,) = struct.unpack(">H", masks_buf[pos_m : pos_m + 2])
            pos_m += 2
            masks.append(masks_buf[pos_m : pos_m + piece_len])
            pos_m += piece_len
        records.append((target, display, masks))
    return records
