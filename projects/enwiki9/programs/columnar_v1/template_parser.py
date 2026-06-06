"""template_parser — Phase 2: conservative {{...}} template extraction.

Walks the Phase-1 scaffold finding {{ }} pairs. Each candidate is
parsed into a canonical tuple plus a format mask, both serialized into
their own channels. Per-instance roundtrip validation: a candidate is
extracted only if reconstruct(canonical, mask) byte-equals the original
raw bytes — otherwise it is left in the scaffold as raw.

Per the build-order rules the user laid down:

  (1) Duplicate keys: canonical args are an ORDERED LIST of (key, value),
      not a dict. {{cite web|author=Smith|author=Jones}} becomes
      ("cite web", [("author","Smith"),("author","Jones")]).

  (2) Positional vs named: positional args use key=None. The format mask
      records whether each arg is named (so the "=" is re-emitted only
      when reconstructing a named arg).

  (3) Nesting limit: tracks {{}} and [[]] depth. Inner templates are NOT
      recursively extracted (Option B): the bytes of any nested {{...}}
      stay literal inside the outer arg's Value field. The outer arg
      separator | and key/value delimiter = are recognized only at
      top-level depth (template_depth==0, wikilink_depth==0). Templates
      with {{}} depth exceeding MAX_TEMPLATE_DEPTH are aborted entirely
      (left in scaffold). Templates exceeding MAX_TEMPLATE_BYTES are
      aborted entirely.

Canonical tuple: (name: bytes, args: list of (key_or_None: bytes|None, value: bytes))
Format mask:     list of bytes pieces, in this order:
                   masks[0]      = whitespace before name
                   masks[1]      = whitespace after name (before first |)
                   per arg:
                     positional: [arg_lead, val_trail]    (2 pieces)
                     named:      [arg_lead, key_trail, val_lead, val_trail]  (4 pieces)

Reconstruction (inverse):
  out = "{{" + masks[0] + name + masks[1]
  for arg, mask_pieces:
    out += "|" + arg_lead
    if named:
      out += key + key_trail + "=" + val_lead + value + val_trail
    else:
      out += value + val_trail
  out += "}}"

Sentinel: TEMPLATE_SENTINEL = b"\\x00\\x00\\xFE\\xFA". Each successful
extraction replaces the template's raw bytes (including {{ and }}) in the
scaffold with this sentinel. Decoder pops one record per sentinel.
"""

from __future__ import annotations

import struct

TEMPLATE_SENTINEL = b"\x00\x00\xFE\xFA"
MAX_TEMPLATE_BYTES = 16384
MAX_TEMPLATE_DEPTH = 8


def find_template_end(data: bytes, start: int) -> int | None:
    """Given start = position of '{{', find the position right after the
    matching '}}'. Returns None if not balanced within MAX_TEMPLATE_BYTES
    or depth exceeds MAX_TEMPLATE_DEPTH."""
    i = start + 2
    template_depth = 1
    wikilink_depth = 0
    n = len(data)
    end_limit = min(n, start + MAX_TEMPLATE_BYTES)
    while i < end_limit:
        if i + 1 < end_limit:
            tok = data[i : i + 2]
            if tok == b"{{":
                template_depth += 1
                if template_depth > MAX_TEMPLATE_DEPTH:
                    return None
                i += 2
                continue
            if tok == b"}}":
                template_depth -= 1
                i += 2
                if template_depth == 0:
                    return i
                continue
            if tok == b"[[":
                wikilink_depth += 1
                i += 2
                continue
            if tok == b"]]":
                if wikilink_depth > 0:
                    wikilink_depth -= 1
                i += 2
                continue
        i += 1
    return None


def split_top_level(inner: bytes, sep: int) -> list[bytes] | None:
    """Split inner bytes on `sep` byte at top level only (depth==0).
    Returns None if {{}} or [[]] is unbalanced inside inner."""
    parts: list[bytes] = []
    current = bytearray()
    i = 0
    n = len(inner)
    template_depth = 0
    wikilink_depth = 0
    while i < n:
        if i + 1 < n:
            tok = inner[i : i + 2]
            if tok == b"{{":
                template_depth += 1
                current.extend(tok)
                i += 2
                continue
            if tok == b"}}":
                if template_depth == 0:
                    return None
                template_depth -= 1
                current.extend(tok)
                i += 2
                continue
            if tok == b"[[":
                wikilink_depth += 1
                current.extend(tok)
                i += 2
                continue
            if tok == b"]]":
                if wikilink_depth == 0:
                    return None
                wikilink_depth -= 1
                current.extend(tok)
                i += 2
                continue
        if inner[i] == sep and template_depth == 0 and wikilink_depth == 0:
            parts.append(bytes(current))
            current = bytearray()
            i += 1
            continue
        current.append(inner[i])
        i += 1
    if template_depth != 0 or wikilink_depth != 0:
        return None
    parts.append(bytes(current))
    return parts


def find_top_level_byte(raw: bytes, target: int) -> int | None:
    """Return position of first occurrence of `target` byte at top
    level (template_depth==0, wikilink_depth==0), or None."""
    i = 0
    n = len(raw)
    template_depth = 0
    wikilink_depth = 0
    while i < n:
        if i + 1 < n:
            tok = raw[i : i + 2]
            if tok == b"{{":
                template_depth += 1
                i += 2
                continue
            if tok == b"}}":
                if template_depth > 0:
                    template_depth -= 1
                i += 2
                continue
            if tok == b"[[":
                wikilink_depth += 1
                i += 2
                continue
            if tok == b"]]":
                if wikilink_depth > 0:
                    wikilink_depth -= 1
                i += 2
                continue
        if raw[i] == target and template_depth == 0 and wikilink_depth == 0:
            return i
        i += 1
    return None


def _ws_split(b: bytes) -> tuple[bytes, bytes, bytes]:
    """(leading_ws, canonical, trailing_ws). Empty inputs return all-empty."""
    stripped = b.strip()
    if not stripped:
        return b"", b"", b""
    start = b.find(stripped)
    end = start + len(stripped)
    return b[:start], stripped, b[end:]


def parse_template_inner(inner: bytes):
    """Parse the bytes between {{ and }} into (name, args, masks).
    Returns None on parse failure (caller leaves raw bytes alone)."""
    parts = split_top_level(inner, ord("|"))
    if parts is None or not parts:
        return None
    name_part = parts[0]
    arg_parts = parts[1:]

    name_lead, canonical_name, name_trail = _ws_split(name_part)
    if not canonical_name:
        return None

    args: list = []
    masks: list = [name_lead, name_trail]
    for arg_raw in arg_parts:
        eq_pos = find_top_level_byte(arg_raw, ord("="))
        if eq_pos is None:
            arg_lead, canonical_val, val_trail = _ws_split(arg_raw)
            args.append((None, canonical_val))
            masks.append(arg_lead)
            masks.append(val_trail)
        else:
            key_part = arg_raw[:eq_pos]
            val_part = arg_raw[eq_pos + 1 :]
            arg_lead, canonical_key, key_trail = _ws_split(key_part)
            val_lead, canonical_val, val_trail = _ws_split(val_part)
            args.append((canonical_key, canonical_val))
            masks.append(arg_lead)
            masks.append(key_trail)
            masks.append(val_lead)
            masks.append(val_trail)
    return canonical_name, args, masks


def reconstruct_template(name: bytes, args: list, masks: list) -> bytes:
    if len(masks) < 2:
        raise ValueError("masks too short for name framing")
    out = bytearray(b"{{")
    out.extend(masks[0])
    out.extend(name)
    out.extend(masks[1])
    mask_idx = 2
    for key, value in args:
        out.extend(b"|")
        if key is None:
            out.extend(masks[mask_idx])
            out.extend(value)
            out.extend(masks[mask_idx + 1])
            mask_idx += 2
        else:
            out.extend(masks[mask_idx])
            out.extend(key)
            out.extend(masks[mask_idx + 1])
            out.extend(b"=")
            out.extend(masks[mask_idx + 2])
            out.extend(value)
            out.extend(masks[mask_idx + 3])
            mask_idx += 4
    if mask_idx != len(masks):
        raise ValueError(f"mask count mismatch: used {mask_idx} of {len(masks)}")
    out.extend(b"}}")
    return bytes(out)


def extract_templates(scaffold: bytes) -> tuple[bytes, list]:
    """Walk scaffold; for each {{...}} that parses + reconstructs
    byte-perfectly, replace its raw bytes with TEMPLATE_SENTINEL and
    record the (name, args, masks). Else leave raw bytes alone.

    Returns (new_scaffold, records).
    """
    out = bytearray()
    records: list = []
    i = 0
    n = len(scaffold)
    while i < n:
        if i + 1 < n and scaffold[i] == 0x7B and scaffold[i + 1] == 0x7B:
            end = find_template_end(scaffold, i)
            if end is not None:
                raw = scaffold[i:end]
                inner = raw[2:-2]
                parsed = parse_template_inner(inner)
                if parsed is not None:
                    name, args, masks = parsed
                    try:
                        rebuilt = reconstruct_template(name, args, masks)
                    except Exception:
                        rebuilt = None
                    if rebuilt == raw:
                        out.extend(TEMPLATE_SENTINEL)
                        records.append((name, args, masks))
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
        if i + 4 <= n and new_scaffold[i : i + 4] == TEMPLATE_SENTINEL:
            try:
                name, args, masks = next(record_iter)
            except StopIteration:
                raise ValueError("template record underflow")
            out.extend(reconstruct_template(name, args, masks))
            i += 4
        else:
            out.append(new_scaffold[i])
            i += 1
    try:
        next(record_iter)
        raise ValueError("template record overflow")
    except StopIteration:
        pass
    return bytes(out)


def serialize_records(records: list) -> tuple[bytes, bytes]:
    """Two channels: tuples_buf (canonical) and masks_buf (format)."""
    tuples = bytearray()
    masks_buf = bytearray()
    tuples.extend(struct.pack(">I", len(records)))
    masks_buf.extend(struct.pack(">I", len(records)))
    for name, args, masks in records:
        tuples.extend(struct.pack(">H", len(name)))
        tuples.extend(name)
        tuples.extend(struct.pack(">H", len(args)))
        for key, value in args:
            if key is None:
                tuples.append(0)
            else:
                tuples.append(1)
                tuples.extend(struct.pack(">H", len(key)))
                tuples.extend(key)
            tuples.extend(struct.pack(">I", len(value)))
            tuples.extend(value)
        masks_buf.extend(struct.pack(">H", len(masks)))
        for piece in masks:
            masks_buf.extend(struct.pack(">H", len(piece)))
            masks_buf.extend(piece)
    return bytes(tuples), bytes(masks_buf)


def serialize_records_dictcoded(records: list) -> tuple[bytes, bytes, bytes, bytes]:
    """Phase 4: dict-code template names AND template arg keys.

    Returns (names_dict_bytes, keys_dict_bytes, tuples_buf, masks_buf).
    tuples_buf format per record:
        varint(name_dict_idx)
        varint(arg_count)
        per arg:
            1B is_named flag
            if named: varint(key_dict_idx)
            varint(value_len) + value_bytes
    masks_buf format per record:
        varint(mask_piece_count)
        per piece: varint(piece_len) + piece_bytes
    """
    import dict_codec as DC

    all_names = [name for name, _, _ in records]
    names_dict_bytes, name_to_idx = DC.build_dict(all_names)

    all_keys: list[bytes] = []
    for _, args, _ in records:
        for k, _ in args:
            if k is not None:
                all_keys.append(k)
    keys_dict_bytes, key_to_idx = DC.build_dict(all_keys)

    tuples = bytearray()
    masks_buf = bytearray()
    DC.write_varint(tuples, len(records))
    DC.write_varint(masks_buf, len(records))

    for name, args, masks in records:
        DC.write_varint(tuples, name_to_idx[name])
        DC.write_varint(tuples, len(args))
        for key, value in args:
            if key is None:
                tuples.append(0)
            else:
                tuples.append(1)
                DC.write_varint(tuples, key_to_idx[key])
            DC.write_varint(tuples, len(value))
            tuples.extend(value)
        DC.write_varint(masks_buf, len(masks))
        for piece in masks:
            DC.write_varint(masks_buf, len(piece))
            masks_buf.extend(piece)

    return (
        names_dict_bytes,
        keys_dict_bytes,
        bytes(tuples),
        bytes(masks_buf),
    )


def parse_records_dictcoded(
    names_dict_bytes: bytes,
    keys_dict_bytes: bytes,
    tuples_buf: bytes,
    masks_buf: bytes,
) -> list:
    import dict_codec as DC

    names = DC.parse_dict(names_dict_bytes)
    keys = DC.parse_dict(keys_dict_bytes)

    pos_t = 0
    pos_m = 0
    n_t, pos_t = DC.read_varint(tuples_buf, pos_t)
    n_m, pos_m = DC.read_varint(masks_buf, pos_m)
    if n_t != n_m:
        raise ValueError(f"record count mismatch: {n_t} vs {n_m}")

    records = []
    for _ in range(n_t):
        name_idx, pos_t = DC.read_varint(tuples_buf, pos_t)
        name = names[name_idx]
        arg_count, pos_t = DC.read_varint(tuples_buf, pos_t)
        args = []
        for _ in range(arg_count):
            flag = tuples_buf[pos_t]
            pos_t += 1
            if flag == 0:
                key = None
            else:
                key_idx, pos_t = DC.read_varint(tuples_buf, pos_t)
                key = keys[key_idx]
            v_len, pos_t = DC.read_varint(tuples_buf, pos_t)
            value = tuples_buf[pos_t : pos_t + v_len]
            pos_t += v_len
            args.append((key, value))
        mask_count, pos_m = DC.read_varint(masks_buf, pos_m)
        masks = []
        for _ in range(mask_count):
            piece_len, pos_m = DC.read_varint(masks_buf, pos_m)
            masks.append(masks_buf[pos_m : pos_m + piece_len])
            pos_m += piece_len
        records.append((name, args, masks))
    return records


def parse_records(tuples_buf: bytes, masks_buf: bytes) -> list:
    pos_t = 0
    pos_m = 0
    (n_t,) = struct.unpack(">I", tuples_buf[pos_t : pos_t + 4])
    pos_t += 4
    (n_m,) = struct.unpack(">I", masks_buf[pos_m : pos_m + 4])
    pos_m += 4
    if n_t != n_m:
        raise ValueError(f"record count mismatch: tuples={n_t} masks={n_m}")
    records: list = []
    for _ in range(n_t):
        (name_len,) = struct.unpack(">H", tuples_buf[pos_t : pos_t + 2])
        pos_t += 2
        name = tuples_buf[pos_t : pos_t + name_len]
        pos_t += name_len
        (arg_count,) = struct.unpack(">H", tuples_buf[pos_t : pos_t + 2])
        pos_t += 2
        args: list = []
        for _ in range(arg_count):
            flag = tuples_buf[pos_t]
            pos_t += 1
            if flag == 0:
                key = None
            else:
                (key_len,) = struct.unpack(">H", tuples_buf[pos_t : pos_t + 2])
                pos_t += 2
                key = tuples_buf[pos_t : pos_t + key_len]
                pos_t += key_len
            (val_len,) = struct.unpack(">I", tuples_buf[pos_t : pos_t + 4])
            pos_t += 4
            value = tuples_buf[pos_t : pos_t + val_len]
            pos_t += val_len
            args.append((key, value))
        (mask_count,) = struct.unpack(">H", masks_buf[pos_m : pos_m + 2])
        pos_m += 2
        masks: list = []
        for _ in range(mask_count):
            (piece_len,) = struct.unpack(">H", masks_buf[pos_m : pos_m + 2])
            pos_m += 2
            masks.append(masks_buf[pos_m : pos_m + piece_len])
            pos_m += piece_len
        records.append((name, args, masks))
    return records
