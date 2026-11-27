#!/usr/bin/env python3
"""Independent decoder and verifier for B1RA archives.

Written strictly from FORMAT.md using the Python standard library only.
Imports nothing from archive_grid.py, bits_oh.py, or any other project module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

MAGIC = b"B1RA"


class FormatError(Exception):
    """Raised when a B1RA archive violates FORMAT.md."""


def read_varint(buf: bytes | memoryview, pos: int) -> tuple[int, int]:
    """Read a canonical unsigned LEB128 varint."""
    value = 0
    shift = 0
    start = pos
    while True:
        if pos >= len(buf):
            raise FormatError("varint runs past end of archive")
        b = buf[pos]
        pos += 1
        if shift > 63:
            raise FormatError("varint exceeds 64-bit bound")
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            if pos > start + 1 and b == 0:
                raise FormatError("non-canonical overlong varint")
            return value, pos
        shift += 7


def canonical_codes(lengths: list[int]) -> list[tuple[int, int]]:
    """Return [(code_int, length), ...] and verify exact Kraft equality."""
    m = len(lengths)
    if m < 2:
        raise FormatError(f"need at least 2 symbols (ESC, EOF), got {m}")
    for idx, ln in enumerate(lengths):
        if not (1 <= ln <= 255):
            raise FormatError(f"symbol {idx} has invalid code length {ln}")
    max_len = max(lengths)
    kraft_lhs = 0
    for ln in lengths:
        kraft_lhs += 1 << (max_len - ln)
    kraft_rhs = 1 << max_len
    if kraft_lhs != kraft_rhs:
        raise FormatError(
            f"code table fails exact Kraft equality: {kraft_lhs} != {kraft_rhs}"
        )

    order = sorted(range(m), key=lambda s: (lengths[s], s))
    codes: list[tuple[int, int]] = [(0, 0)] * m
    code = 0
    prev_len = lengths[order[0]]
    codes[order[0]] = (0, prev_len)
    for s in order[1:]:
        ln = lengths[s]
        code = (code + 1) << (ln - prev_len)
        prev_len = ln
        if code >> ln:
            raise FormatError("canonical code overflow")
        codes[s] = (code, ln)
    return codes


def _build_decode_trie(
    codes: list[tuple[int, int]],
) -> tuple[dict[tuple[int, int], int], list[int]]:
    """Build (length, code) -> symbol lookup table and sorted distinct lengths."""
    table: dict[tuple[int, int], int] = {}
    distinct: set[int] = set()
    for sym, (code, ln) in enumerate(codes):
        key = (ln, code)
        if key in table:
            raise FormatError(f"duplicate canonical code for symbol {sym}")
        table[key] = sym
        distinct.add(ln)
    return table, sorted(distinct)


def parse_archive_structure(buf: bytes) -> dict[str, Any]:
    """Parse header and random-access framing index without decoding payloads."""
    if len(buf) < 4 or buf[:4] != MAGIC:
        raise FormatError("bad magic (expected B1RA)")
    pos = 4
    n, pos = read_varint(buf, pos)
    entries: list[bytes] = []
    seen_entries: set[bytes] = set()
    dict_bytes = 0
    for i in range(n):
        if pos >= len(buf):
            raise FormatError(f"dictionary truncated at entry {i}")
        ln = buf[pos]
        pos += 1
        if not (1 <= ln <= 16):
            raise FormatError(f"entry {i} length {ln} outside 1..16")
        if pos + ln > len(buf):
            raise FormatError(f"dictionary truncated inside entry {i}")
        entry = bytes(buf[pos : pos + ln])
        pos += ln
        if entry in seen_entries:
            raise FormatError(f"duplicate dictionary entry at index {i}")
        seen_entries.add(entry)
        entries.append(entry)
        dict_bytes += 1 + ln

    table_len = n + 2
    if pos + table_len > len(buf):
        raise FormatError("code table truncated")
    lengths = list(buf[pos : pos + table_len])
    pos += table_len
    header_bytes = pos

    # Validate canonical prefix code & exact Kraft equality immediately.
    codes = canonical_codes(lengths)

    f_count, pos = read_varint(buf, pos)
    record_lengths: list[int] = []
    for j in range(f_count):
        p_j, pos = read_varint(buf, pos)
        if p_j < 1:
            raise FormatError(f"record {j} has invalid payload byte length {p_j}")
        record_lengths.append(p_j)

    payload_start = pos
    framing_bytes = payload_start - header_bytes
    payload_bytes = sum(record_lengths)
    if payload_start + payload_bytes != len(buf):
        raise FormatError(
            f"archive length mismatch: header({header_bytes}) + framing({framing_bytes}) "
            f"+ payload({payload_bytes}) = {payload_start + payload_bytes} != {len(buf)}"
        )

    return {
        "n": n,
        "entries": entries,
        "lengths": lengths,
        "codes": codes,
        "dict_bytes": dict_bytes,
        "code_table_bytes": table_len,
        "header_bytes": header_bytes,
        "record_count": f_count,
        "record_lengths": record_lengths,
        "framing_bytes": framing_bytes,
        "payload_start": payload_start,
        "payload_bytes": payload_bytes,
        "body_bytes": framing_bytes + payload_bytes,
        "complete_bytes": len(buf),
    }


def _decode_record_slice(
    rec_buf: bytes | memoryview,
    entries: list[bytes],
    table: dict[tuple[int, int], int],
    max_len: int,
) -> tuple[bytes, int, int, int, int]:
    """Decode one byte-aligned record slice.

    Returns (raw_bytes, tokens, escapes, bits_used, padding_bits).
    """
    n = len(entries)
    esc = n
    eof = n + 1
    total_bits = len(rec_buf) * 8
    bit_pos = 0

    out = bytearray()
    tokens = 0
    escapes = 0
    code = 0
    clen = 0
    get_sym = table.get

    found_eof = False
    while bit_pos < total_bits:
        b = (rec_buf[bit_pos >> 3] >> (7 - (bit_pos & 7))) & 1
        bit_pos += 1
        code = (code << 1) | b
        clen += 1
        if clen > max_len:
            raise FormatError(f"no valid prefix code matched within {max_len} bits")
        sym = get_sym((clen, code))
        if sym is None:
            continue
        code = 0
        clen = 0
        if sym < n:
            out += entries[sym]
            tokens += 1
        elif sym == esc:
            if bit_pos + 8 > total_bits:
                raise FormatError("escaped byte truncated before 8 bits")
            val = 0
            for _ in range(8):
                val = (val << 1) | ((rec_buf[bit_pos >> 3] >> (7 - (bit_pos & 7))) & 1)
                bit_pos += 1
            out.append(val)
            tokens += 1
            escapes += 1
        elif sym == eof:
            found_eof = True
            break
        else:
            raise FormatError(f"invalid symbol id {sym}")

    if not found_eof:
        raise FormatError("record ended without EOF code")

    padding_bits = total_bits - bit_pos
    if padding_bits >= 8:
        raise FormatError(f"excess trailing padding bits in record: {padding_bits}")
    for p in range(bit_pos, total_bits):
        if (rec_buf[p >> 3] >> (7 - (p & 7))) & 1:
            raise FormatError("non-zero padding bit after EOF")

    return bytes(out), tokens, escapes, bit_pos, padding_bits


def decode_archive(buf: bytes) -> dict[str, Any]:
    """Decode every record in a B1RA archive and verify all invariants."""
    meta = parse_archive_structure(buf)
    entries = meta["entries"]
    table, distinct_lengths = _build_decode_trie(meta["codes"])
    max_len = distinct_lengths[-1]

    view = memoryview(buf)
    offset = meta["payload_start"]
    records: list[bytes] = []
    total_tokens = 0
    total_escapes = 0
    total_bits_used = 0
    total_padding_bits = 0
    per_record_tokens: list[int] = []

    for j, p_j in enumerate(meta["record_lengths"]):
        rec_slice = view[offset : offset + p_j]
        offset += p_j
        try:
            raw, toks, escs, bits_used, pad_bits = _decode_record_slice(
                rec_slice, entries, table, max_len
            )
        except FormatError as exc:
            raise FormatError(f"record {j}: {exc}") from exc
        records.append(raw)
        total_tokens += toks
        total_escapes += escs
        total_bits_used += bits_used
        total_padding_bits += pad_bits
        per_record_tokens.append(toks)

    assert offset == len(buf)
    return {
        "entries_count": meta["n"],
        "header_bytes": meta["header_bytes"],
        "dict_bytes": meta["dict_bytes"],
        "code_table_bytes": meta["code_table_bytes"],
        "framing_bytes": meta["framing_bytes"],
        "payload_bytes": meta["payload_bytes"],
        "body_bytes": meta["body_bytes"],
        "complete_bytes": meta["complete_bytes"],
        "record_count": meta["record_count"],
        "tokens": total_tokens,
        "escapes": total_escapes,
        "payload_bits_used": total_bits_used,
        "padding_bits": total_padding_bits,
        "per_record_tokens": per_record_tokens,
        "records": records,
    }


def decode_single_record(buf: bytes, record_idx: int) -> bytes:
    """Random-access decode of a single record by index using the framing table."""
    meta = parse_archive_structure(buf)
    if not (0 <= record_idx < meta["record_count"]):
        raise IndexError(f"record_idx {record_idx} out of range 0..{meta['record_count'] - 1}")
    table, distinct_lengths = _build_decode_trie(meta["codes"])
    max_len = distinct_lengths[-1]
    offset = meta["payload_start"] + sum(meta["record_lengths"][:record_idx])
    p_j = meta["record_lengths"][record_idx]
    raw, _, _, _, _ = _decode_record_slice(
        memoryview(buf)[offset : offset + p_j], meta["entries"], table, max_len
    )
    return raw


def verify_archive_against_sources(
    archive_bytes: bytes,
    sources: list[bytes],
    expected_header_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Independently decode an archive and verify 100% byte fidelity against sources."""
    dec = decode_archive(archive_bytes)
    header_prefix_ok = True
    if expected_header_bytes is not None:
        header_prefix_ok = (
            archive_bytes[: len(expected_header_bytes)] == expected_header_bytes
            and dec["header_bytes"] == len(expected_header_bytes)
        )
    records = dec.pop("records")
    count_ok = len(records) == len(sources)
    mismatches = []
    for idx in range(min(len(records), len(sources))):
        if records[idx] != sources[idx]:
            mismatches.append(idx)

    # Also verify random-access single-record decode on first, middle, and last record.
    ra_ok = True
    if sources and count_ok and not mismatches:
        probe_indices = sorted({0, len(sources) // 2, len(sources) - 1})
        for idx in probe_indices:
            if decode_single_record(archive_bytes, idx) != sources[idx]:
                ra_ok = False
                break

    all_ok = header_prefix_ok and count_ok and (not mismatches) and ra_ok
    dec["header_prefix_ok"] = header_prefix_ok
    dec["record_count_ok"] = count_ok
    dec["mismatched_records"] = mismatches[:10]
    dec["mismatched_count"] = len(mismatches)
    dec["random_access_spot_check_ok"] = ra_ok
    dec["archive_sha256"] = hashlib.sha256(archive_bytes).hexdigest()
    dec["fidelity"] = 1.0 if all_ok else (
        (len(sources) - len(mismatches)) / max(1, len(sources))
    )
    dec["all_ok"] = all_ok
    return dec


def main() -> int:
    ap = argparse.ArgumentParser(description="Independent B1RA archive decoder/verifier.")
    ap.add_argument("--archive", required=True, help="Path to .b1ra archive file")
    ap.add_argument("--sources-manifest", help="Optional JSON manifest with source paths or inline texts")
    ap.add_argument("--root", default=".", help="Root directory for manifest paths")
    args = ap.parse_args()

    buf = Path(args.archive).read_bytes()
    if args.sources_manifest:
        spec = json.loads(Path(args.sources_manifest).read_text())
        root = Path(args.root)
        sources = []
        for item in spec["files"]:
            if "text" in item:
                sources.append(item["text"].encode("utf-8"))
            else:
                sources.append((root / item["path"]).read_bytes())
        res = verify_archive_against_sources(buf, sources)
        res.pop("per_record_tokens", None)
        print(json.dumps(res, indent=2))
        return 0 if res["all_ok"] else 1

    dec = decode_archive(buf)
    dec.pop("records")
    dec.pop("per_record_tokens")
    print(json.dumps(dec, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
