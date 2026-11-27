#!/usr/bin/env python3
"""Standalone independent byte decoder for A1AF (flat-literal) and A1AD (construction-DAG).

Written strictly from FORMAT.md using the Python standard library only.
Imports nothing from headers.py or any other module in this workspace.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from typing import Dict, List, Optional, Tuple

MAGIC_FLAT = b"A1AF"
MAGIC_DAG = b"A1AD"
MAX_ENTRY_LEN = 16


class FormatError(Exception):
    """Raised on any structural, DAG, rank, Huffman, or framing error."""


def _read_varint(buf: bytes, pos: int) -> Tuple[int, int]:
    value = 0
    shift = 0
    start = pos
    n = len(buf)
    while True:
        if pos >= n:
            raise FormatError("varint runs past end of archive")
        b = buf[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            if pos - start > 1 and b == 0:
                raise FormatError("non-canonical varint encoding")
            return value, pos
        shift += 7
        if shift > 63:
            raise FormatError("varint exceeds 64 bits")


class _BitReader:
    def __init__(self, buf: bytes, byte_pos: int) -> None:
        self.buf = buf
        self.byte_pos = byte_pos
        self.bit_offset = 0  # 0..7 within current byte
        self.total_bytes = len(buf)

    def read_bits(self, nbits: int) -> int:
        if nbits == 0:
            return 0
        out = 0
        remaining = nbits
        while remaining > 0:
            if self.byte_pos >= self.total_bytes:
                raise FormatError("bit stream runs past end of archive")
            avail = 8 - self.bit_offset
            take = remaining if remaining < avail else avail
            shift = avail - take
            mask = (1 << take) - 1
            chunk = (self.buf[self.byte_pos] >> shift) & mask
            out = (out << take) | chunk
            self.bit_offset += take
            if self.bit_offset == 8:
                self.bit_offset = 0
                self.byte_pos += 1
            remaining -= take
        return out

    def align_byte_zero_pad(self) -> int:
        if self.bit_offset != 0:
            pad_bits = 8 - self.bit_offset
            pad = self.read_bits(pad_bits)
            if pad != 0:
                raise FormatError("non-zero padding bits at section boundary")
        return self.byte_pos


def _canonical_decode_table(lengths: List[int]) -> Tuple[Dict[Tuple[int, int], int], List[int]]:
    n = len(lengths)
    if n < 2:
        raise FormatError("code table needs at least 2 symbols")
    for l in lengths:
        if not (1 <= l <= 255):
            raise FormatError(f"code length {l} outside 1..255")
    top = max(lengths)
    kraft = sum(1 << (top - l) for l in lengths)
    if kraft != (1 << top):
        raise FormatError(f"invalid prefix code Kraft sum: {kraft} != {1 << top}")

    order = sorted(range(n), key=lambda s: (lengths[s], s))
    table: Dict[Tuple[int, int], int] = {}
    code = 0
    prev_len = lengths[order[0]]
    table[(prev_len, code)] = order[0]
    for s in order[1:]:
        length = lengths[s]
        code = (code + 1) << (length - prev_len)
        prev_len = length
        if code >= (1 << length):
            raise FormatError("canonical code overflow")
        key = (length, code)
        if key in table:
            raise FormatError("duplicate canonical code")
        table[key] = s
    return table, sorted(set(lengths))


def _parse_flat_header(buf: bytes) -> Tuple[List[bytes], List[int], int, Dict[str, object]]:
    pos = 4
    n, pos = _read_varint(buf, pos)
    if n < 1:
        raise FormatError("empty dictionary")
    entries: List[bytes] = []
    seen = set()
    for _ in range(n):
        if pos >= len(buf):
            raise FormatError("flat dictionary truncated")
        ln = buf[pos]
        pos += 1
        if not (1 <= ln <= MAX_ENTRY_LEN):
            raise FormatError(f"flat entry length {ln} outside 1..{MAX_ENTRY_LEN}")
        if pos + ln > len(buf):
            raise FormatError("flat dictionary entry runs past end")
        word = bytes(buf[pos:pos + ln])
        pos += ln
        if word in seen:
            raise FormatError("duplicate entry in flat dictionary")
        seen.add(word)
        entries.append(word)
    if pos + n + 2 > len(buf):
        raise FormatError("flat code table truncated")
    lengths = list(buf[pos:pos + n + 2])
    pos += n + 2
    meta = {"format": "A1AF", "dag_nodes": n, "emitted_entries": n, "header_bytes": pos}
    return entries, lengths, pos, meta


def _parse_dag_header(buf: bytes) -> Tuple[List[bytes], List[int], int, Dict[str, object]]:
    if len(buf) < 6:
        raise FormatError("A1AD header truncated")
    flags = buf[4]
    if flags & 0xF0:
        raise FormatError(f"reserved flag bits set: 0x{flags:02x}")
    mode = flags & 0x03
    if mode not in (0, 1):
        raise FormatError(f"invalid A1AD mode: {mode}")
    has_emit_mask = bool(flags & 0x04)
    has_merge_ranks = bool(flags & 0x08)

    pos = 5
    M, pos = _read_varint(buf, pos)
    A, pos = _read_varint(buf, pos)
    if M < 1 or A < 1 or A > 256 or A > M:
        raise FormatError(f"invalid DAG counts M={M}, A={A}")
    if pos + A > len(buf):
        raise FormatError("DAG leaves truncated")

    dag: List[bytes] = []
    seen = set()
    prev_b = -1
    for _ in range(A):
        b = buf[pos]
        pos += 1
        if b <= prev_b:
            raise FormatError("DAG leaves must be strictly ascending")
        prev_b = b
        word = bytes([b])
        dag.append(word)
        seen.add(word)

    br = _BitReader(buf, pos)
    children_of: List[List[int]] = [[] for _ in range(M)]
    kind_counts = {"pair": 0, "literal": 0, "list": 0}
    for i in range(A, M):
        w_i = max(1, (i - 1).bit_length())
        if mode == 0:
            left = br.read_bits(w_i)
            right = br.read_bits(w_i)
            if left >= i or right >= i:
                raise FormatError(f"corrupted DAG edge at node {i}: ({left}, {right}) >= {i}")
            word = dag[left] + dag[right]
            children_of[i] = [left, right]
            kind_counts["pair"] += 1
        else:
            tag = br.read_bits(2)
            if tag == 0:
                left = br.read_bits(w_i)
                right = br.read_bits(w_i)
                if left >= i or right >= i:
                    raise FormatError(f"corrupted DAG pair edge at node {i}: ({left}, {right}) >= {i}")
                word = dag[left] + dag[right]
                children_of[i] = [left, right]
                kind_counts["pair"] += 1
            elif tag == 1:
                ln = br.read_bits(4) + 1
                if not (2 <= ln <= MAX_ENTRY_LEN):
                    raise FormatError(f"hybrid literal length {ln} outside 2..{MAX_ENTRY_LEN}")
                raw = bytearray(ln)
                for k in range(ln):
                    raw[k] = br.read_bits(8)
                word = bytes(raw)
                kind_counts["literal"] += 1
            elif tag == 2:
                cnt = br.read_bits(4) + 2
                if not (2 <= cnt <= MAX_ENTRY_LEN):
                    raise FormatError(f"hybrid list count {cnt} outside 2..{MAX_ENTRY_LEN}")
                parts = []
                ids = []
                for _ in range(cnt):
                    cid = br.read_bits(w_i)
                    if cid >= i:
                        raise FormatError(f"corrupted DAG list edge at node {i}: {cid} >= {i}")
                    ids.append(cid)
                    parts.append(dag[cid])
                word = b"".join(parts)
                children_of[i] = ids
                kind_counts["list"] += 1
            else:
                raise FormatError(f"reserved DAG node tag 3 at node {i}")

        if not (2 <= len(word) <= MAX_ENTRY_LEN):
            raise FormatError(f"reconstructed DAG node {i} length {len(word)} outside 2..{MAX_ENTRY_LEN}")
        if word in seen:
            raise FormatError(f"duplicate reconstructed DAG string at node {i}")
        seen.add(word)
        dag.append(word)

    pos = br.align_byte_zero_pad()

    ranks: Optional[List[int]] = None
    R = M - A
    if has_merge_ranks and R > 0:
        rbr = _BitReader(buf, pos)
        rw = max(1, (R - 1).bit_length())
        ranks = [rbr.read_bits(rw) for _ in range(R)]
        pos = rbr.align_byte_zero_pad()
        seen_ranks = [False] * R
        for idx, r in enumerate(ranks):
            if r >= R:
                raise FormatError(f"corrupted merge rank {r} >= {R} at node {A + idx}")
            if seen_ranks[r]:
                raise FormatError(f"duplicate merge rank {r} at node {A + idx}")
            seen_ranks[r] = True
        for i in range(A, M):
            ri = ranks[i - A]
            for c in children_of[i]:
                if c >= A and ranks[c - A] >= ri:
                    raise FormatError(
                        f"corrupted merge rank order: child node {c} (rank {ranks[c - A]}) "
                        f">= parent node {i} (rank {ri})"
                    )

    if has_emit_mask:
        mask_len = (M + 7) // 8
        if pos + mask_len > len(buf):
            raise FormatError("emit mask truncated")
        mask_bytes = buf[pos:pos + mask_len]
        pos += mask_len
        rem = M & 7
        if rem != 0 and (mask_bytes[-1] >> rem) != 0:
            raise FormatError("non-zero unused bits in emit mask")
        entries = [dag[i] for i in range(M) if (mask_bytes[i >> 3] >> (i & 7)) & 1]
        if not entries:
            raise FormatError("emit mask selects zero emitted entries")
    else:
        entries = dag

    n = len(entries)
    if pos + n + 2 > len(buf):
        raise FormatError("DAG code table truncated")
    lengths = list(buf[pos:pos + n + 2])
    pos += n + 2
    meta = {
        "format": "A1AD",
        "dag_mode": "pair" if mode == 0 else "hybrid",
        "dag_nodes": M,
        "leaves": A,
        "emitted_entries": n,
        "has_emit_mask": has_emit_mask,
        "has_merge_ranks": has_merge_ranks,
        "kind_counts": kind_counts,
        "header_bytes": pos,
    }
    return entries, lengths, pos, meta


def decode_archive(buf: bytes, measure_per_file_ns: bool = False) -> Dict[str, object]:
    """Decode either A1AF or A1AD archive and return decoded files + stats."""
    if len(buf) < 4:
        raise FormatError("archive too short for magic")
    magic = buf[:4]
    t0 = time.perf_counter_ns()
    if magic == MAGIC_FLAT:
        entries, lengths, pos, meta = _parse_flat_header(buf)
    elif magic == MAGIC_DAG:
        entries, lengths, pos, meta = _parse_dag_header(buf)
    else:
        raise FormatError(f"unknown magic {magic!r}")

    f, pos = _read_varint(buf, pos)
    payload_offset = pos
    table, distinct_lengths = _canonical_decode_table(lengths)
    n = len(entries)
    esc = n
    eof = n + 1

    # Build fast prefix-code lookup by length using integer bit operations.
    max_len = distinct_lengths[-1]
    min_len = distinct_lengths[0]
    payload = buf[payload_offset:]
    total_bits = len(payload) * 8

    # Direct byte-stream bit reader (avoids huge Python string allocations).
    files: List[bytes] = []
    per_file_ns: List[int] = []
    tokens = 0
    escapes = 0
    bitpos = 0
    get = table.get

    def read_one_bit() -> int:
        nonlocal bitpos
        if bitpos >= total_bits:
            raise FormatError("truncated payload bitstream")
        val = (payload[bitpos >> 3] >> (7 - (bitpos & 7))) & 1
        bitpos += 1
        return val

    def read_byte() -> int:
        nonlocal bitpos
        if bitpos + 8 > total_bits:
            raise FormatError("escaped byte runs past end of payload")
        byte_idx = bitpos >> 3
        off = bitpos & 7
        bitpos += 8
        if off == 0:
            return payload[byte_idx]
        return ((payload[byte_idx] << off) | (payload[byte_idx + 1] >> (8 - off))) & 0xFF

    # Fast table-driven decode: walk code bits 1 by 1 (short average length ~9-12 bits).
    # For speed, accumulate min_len bits at once when possible.
    header_done_ns = time.perf_counter_ns()
    for _ in range(f):
        ft0 = time.perf_counter_ns() if measure_per_file_ns else 0
        cur = bytearray()
        while True:
            code = 0
            length = 0
            sym: Optional[int] = None
            while length < max_len:
                code = (code << 1) | read_one_bit()
                length += 1
                if length >= min_len:
                    sym = get((length, code))
                    if sym is not None:
                        break
            if sym is None:
                raise FormatError(f"no Huffman code matches at payload bit {bitpos}")
            if sym < n:
                cur += entries[sym]
                tokens += 1
            elif sym == esc:
                cur.append(read_byte())
                tokens += 1
                escapes += 1
            else:
                assert sym == eof
                files.append(bytes(cur))
                break
        if measure_per_file_ns:
            per_file_ns.append(time.perf_counter_ns() - ft0)

    trailing_bits = total_bits - bitpos
    if trailing_bits >= 8:
        raise FormatError(f"excess trailing payload bits: {trailing_bits}")
    for _ in range(trailing_bits):
        if read_one_bit() != 0:
            raise FormatError("non-zero trailing padding bit in payload")

    total_ns = time.perf_counter_ns() - t0
    return {
        **meta,
        "entries": n,
        "files": files,
        "file_count": f,
        "tokens": tokens,
        "escapes": escapes,
        "payload_offset": payload_offset,
        "payload_bytes": len(payload),
        "payload_bits_used": bitpos,
        "padding_bits": trailing_bits,
        "complete_bytes": len(buf),
        "complete_bits": 8 * len(buf),
        "header_decode_ns": header_done_ns - t0,
        "total_decode_ns": total_ns,
        "per_file_decode_ns": per_file_ns,
    }


def verify_archive_against_sources(buf: bytes, sources: List[bytes]) -> Dict[str, object]:
    dec = decode_archive(buf)
    files = dec.pop("files")
    if len(files) != len(sources):
        raise FormatError(f"file count mismatch: decoded {len(files)} != {len(sources)}")
    for i, (got, want) in enumerate(zip(files, sources)):
        if got != want:
            raise FormatError(f"byte mismatch in file {i}: got {len(got)}B vs expected {len(want)}B")
    dec["all_files_equal"] = True
    dec["archive_sha256"] = hashlib.sha256(buf).hexdigest()
    return dec


def main() -> int:
    ap = argparse.ArgumentParser(description="Independent A1AF / A1AD archive decoder")
    ap.add_argument("--archive", required=True)
    ap.add_argument("--manifest", help="optional JSON manifest to verify byte-for-byte")
    ap.add_argument("--root", help="root directory for manifest paths")
    args = ap.parse_args()

    with open(args.archive, "rb") as fh:
        buf = fh.read()
    try:
        if args.manifest:
            with open(args.manifest, "rb") as fh:
                spec = json.load(fh)
            root = args.root or "."
            sources = []
            for item in spec["files"]:
                with open(f"{root}/{item['path']}", "rb") as fh:
                    sources.append(fh.read())
            res = verify_archive_against_sources(buf, sources)
        else:
            res = decode_archive(buf)
            res.pop("files")
    except FormatError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    res["ok"] = True
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
