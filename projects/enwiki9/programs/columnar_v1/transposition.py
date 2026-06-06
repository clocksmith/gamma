"""transposition — Phase 3: columnar transposition of canonical tuples.

Per-record interleaved serialization (Phase 2A) loses to lzma+raw because
the per-instance framing (length prefixes, flags, mask piece counts)
fragments the columns lzma's matcher would otherwise feast on.

This module re-packs template_records and wikilink_records into per-field
COLUMNS so each homogeneous data type has its own contiguous channel.
The single-stream xz over the concatenated columns then sees:

  [name][name][name]... | [arg_count][arg_count]... | [flag][flag]... |
  [key_bytes][key_bytes]... | [value_bytes][value_bytes]... |
  [mask_piece][mask_piece]...

Every column is internally homogeneous: names are template names,
key_bytes are wikitext arg keys (url, title, date, publisher, ...), the
flags column is mostly 0/1 bytes, the lens are mostly small varints.
lzma's match finder, working over these contiguous streams, finds the
heavy duplication that was previously hidden behind framing.

Length tables use varint to keep the lens column compact for the typical
case (most lengths < 128 fit in one byte).

A 4B record_count is stored at the head of T_arg_counts (templates) and
W_targets_lens (wikilinks) so the decoder knows how many records to walk.
"""

from __future__ import annotations

import struct


# ─── varint helpers ───

def _write_varint(buf: bytearray, n: int) -> None:
    while n >= 0x80:
        buf.append((n & 0x7F) | 0x80)
        n >>= 7
    buf.append(n)


def _read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    n = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        n |= (b & 0x7F) << shift
        if not (b & 0x80):
            return n, pos
        shift += 7


# ─── templates ───

T_COLUMNS = [
    "T_name_content",
    "T_name_lens",
    "T_arg_counts",
    "T_arg_flags",
    "T_keys_content",
    "T_key_lens",
    "T_values_content",
    "T_value_lens",
    "T_mask_content",
    "T_mask_lens",
]


def transpose_templates(records: list) -> dict[str, bytes]:
    name_content = bytearray()
    name_lens = bytearray()
    arg_counts = bytearray(struct.pack(">I", len(records)))
    arg_flags = bytearray()
    keys_content = bytearray()
    key_lens = bytearray()
    values_content = bytearray()
    value_lens = bytearray()
    mask_content = bytearray()
    mask_lens = bytearray()

    for name, args, masks in records:
        name_content.extend(name)
        _write_varint(name_lens, len(name))
        _write_varint(arg_counts, len(args))
        for key, value in args:
            if key is None:
                arg_flags.append(0)
            else:
                arg_flags.append(1)
                keys_content.extend(key)
                _write_varint(key_lens, len(key))
            values_content.extend(value)
            _write_varint(value_lens, len(value))
        for piece in masks:
            mask_content.extend(piece)
            _write_varint(mask_lens, len(piece))

    return {
        "T_name_content": bytes(name_content),
        "T_name_lens": bytes(name_lens),
        "T_arg_counts": bytes(arg_counts),
        "T_arg_flags": bytes(arg_flags),
        "T_keys_content": bytes(keys_content),
        "T_key_lens": bytes(key_lens),
        "T_values_content": bytes(values_content),
        "T_value_lens": bytes(value_lens),
        "T_mask_content": bytes(mask_content),
        "T_mask_lens": bytes(mask_lens),
    }


def untranspose_templates(cols: dict[str, bytes]) -> list:
    arg_counts = cols["T_arg_counts"]
    record_count = struct.unpack(">I", arg_counts[:4])[0]
    pos_arg_counts = 4
    pos_name_content = 0
    pos_name_lens = 0
    pos_arg_flags = 0
    pos_keys_content = 0
    pos_key_lens = 0
    pos_values_content = 0
    pos_value_lens = 0
    pos_mask_content = 0
    pos_mask_lens = 0

    name_content = cols["T_name_content"]
    name_lens = cols["T_name_lens"]
    arg_flags = cols["T_arg_flags"]
    keys_content = cols["T_keys_content"]
    key_lens = cols["T_key_lens"]
    values_content = cols["T_values_content"]
    value_lens = cols["T_value_lens"]
    mask_content = cols["T_mask_content"]
    mask_lens = cols["T_mask_lens"]

    records = []
    for _ in range(record_count):
        name_len, pos_name_lens = _read_varint(name_lens, pos_name_lens)
        name = name_content[pos_name_content : pos_name_content + name_len]
        pos_name_content += name_len

        arg_count, pos_arg_counts = _read_varint(arg_counts, pos_arg_counts)
        args = []
        n_named = 0
        n_positional = 0
        for _ in range(arg_count):
            flag = arg_flags[pos_arg_flags]
            pos_arg_flags += 1
            if flag == 0:
                key = None
                n_positional += 1
            else:
                key_len, pos_key_lens = _read_varint(key_lens, pos_key_lens)
                key = keys_content[pos_keys_content : pos_keys_content + key_len]
                pos_keys_content += key_len
                n_named += 1
            v_len, pos_value_lens = _read_varint(value_lens, pos_value_lens)
            value = values_content[pos_values_content : pos_values_content + v_len]
            pos_values_content += v_len
            args.append((key, value))

        mask_piece_count = 2 + 2 * n_positional + 4 * n_named
        masks = []
        for _ in range(mask_piece_count):
            piece_len, pos_mask_lens = _read_varint(mask_lens, pos_mask_lens)
            piece = mask_content[pos_mask_content : pos_mask_content + piece_len]
            pos_mask_content += piece_len
            masks.append(piece)
        records.append((name, args, masks))
    return records


# ─── wikilinks ───

W_COLUMNS = [
    "W_target_content",
    "W_target_lens",
    "W_has_display",
    "W_display_content",
    "W_display_lens",
    "W_mask_content",
    "W_mask_lens",
]


def transpose_wikilinks(records: list) -> dict[str, bytes]:
    target_content = bytearray()
    target_lens = bytearray(struct.pack(">I", len(records)))
    has_display = bytearray()
    display_content = bytearray()
    display_lens = bytearray()
    mask_content = bytearray()
    mask_lens = bytearray()

    for target, display, masks in records:
        target_content.extend(target)
        _write_varint(target_lens, len(target))
        if display is None:
            has_display.append(0)
        else:
            has_display.append(1)
            display_content.extend(display)
            _write_varint(display_lens, len(display))
        for piece in masks:
            mask_content.extend(piece)
            _write_varint(mask_lens, len(piece))

    return {
        "W_target_content": bytes(target_content),
        "W_target_lens": bytes(target_lens),
        "W_has_display": bytes(has_display),
        "W_display_content": bytes(display_content),
        "W_display_lens": bytes(display_lens),
        "W_mask_content": bytes(mask_content),
        "W_mask_lens": bytes(mask_lens),
    }


def untranspose_wikilinks(cols: dict[str, bytes]) -> list:
    target_lens = cols["W_target_lens"]
    record_count = struct.unpack(">I", target_lens[:4])[0]
    pos_target_lens = 4
    pos_target_content = 0
    pos_has_display = 0
    pos_display_lens = 0
    pos_display_content = 0
    pos_mask_content = 0
    pos_mask_lens = 0

    target_content = cols["W_target_content"]
    has_display = cols["W_has_display"]
    display_content = cols["W_display_content"]
    display_lens = cols["W_display_lens"]
    mask_content = cols["W_mask_content"]
    mask_lens = cols["W_mask_lens"]

    records = []
    for _ in range(record_count):
        target_len, pos_target_lens = _read_varint(target_lens, pos_target_lens)
        target = target_content[pos_target_content : pos_target_content + target_len]
        pos_target_content += target_len

        flag = has_display[pos_has_display]
        pos_has_display += 1
        if flag == 0:
            display = None
            mask_piece_count = 2
        else:
            d_len, pos_display_lens = _read_varint(display_lens, pos_display_lens)
            display = display_content[
                pos_display_content : pos_display_content + d_len
            ]
            pos_display_content += d_len
            mask_piece_count = 4

        masks = []
        for _ in range(mask_piece_count):
            piece_len, pos_mask_lens = _read_varint(mask_lens, pos_mask_lens)
            piece = mask_content[pos_mask_content : pos_mask_content + piece_len]
            pos_mask_content += piece_len
            masks.append(piece)
        records.append((target, display, masks))
    return records
