#!/usr/bin/env python3
"""Serialized random-access binary container + single-file bit-offset seeker for BITS Rung 3.

Implements and tests an ACTUAL serialized random-access archive (kept strictly in
`rung3-archive-search-v1/` so `dcc-v5`'s unindexed CodeNet baseline table stays unchanged):
  - Header:
      * 4B magic `BIT3`
      * 2B uint16 num_entries `|D|`
      * 2B uint16 num_files `M`
      * 1B uint8 layout_tables (`1` for Design A, `2` for Design B)
      * Dictionary bytes: `|D|` entries encoded as `1B len + raw_bytes`
      * Canonical Huffman code-length table(s): `layout_tables * (|D| + 1)` bytes
      * Per-file 4-byte seek index (`M * 4` bytes):
          bit 31 = stream_id (`0` for lang1/shared, `1` for lang2)
          bits 30..0 = exact starting bit offset in that stream (`< 2^31` bits)
      * 4B uint32 payload_0 byte length (when `layout_tables == 2`)
      * Packed bitstream payload(s)
  - `decode_single_file(blob, file_index)` seeks directly to `(stream_id, bit_offset)`
    and decodes ONLY that single file until `EOF_SYMBOL` without decoding preceding files!
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path
from typing import Sequence

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
CODENET_DIR = HERE.parent / 'codenet-replication-v1'
sys.path.insert(0, str(CODENET_DIR))
import byte_encode as BE  # noqa: E402


def encode_stream_with_bit_offsets(
    doc_pieces: Sequence[Sequence[bytes]],
    codes: dict[bytes, tuple[int, int]],
) -> tuple[bytes, list[int]]:
    """Pack canonical Huffman codewords + EOF and return `(payload_bytes, start_bit_offsets)`."""
    out = bytearray()
    acc = 0
    nbits = 0
    bit_cursor = 0
    offsets: list[int] = []
    eof_code, eof_len = codes[BE.EOF_SYMBOL]

    for pieces in doc_pieces:
        offsets.append(bit_cursor)
        for piece in pieces:
            code, bit_len = codes[piece]
            acc = (acc << bit_len) | code
            nbits += bit_len
            bit_cursor += bit_len
            while nbits >= 8:
                nbits -= 8
                out.append((acc >> nbits) & 0xFF)
                acc &= (1 << nbits) - 1
        acc = (acc << eof_len) | eof_code
        nbits += eof_len
        bit_cursor += eof_len
        while nbits >= 8:
            nbits -= 8
            out.append((acc >> nbits) & 0xFF)
            acc &= (1 << nbits) - 1

    if nbits > 0:
        out.append((acc << (8 - nbits)) & 0xFF)
    return bytes(out), offsets


def decode_one_doc_from_bit_offset(payload: bytes, start_bit: int, decode_tree: dict) -> bytes:
    """Random-access decode of ONE document starting at `start_bit` until `EOF_SYMBOL`."""
    byte_idx = start_bit >> 3
    first_bit_shift = 7 - (start_bit & 7)
    node = decode_tree
    out: list[bytes] = []

    n_bytes = len(payload)
    for b_pos in range(byte_idx, n_bytes):
        byte_val = payload[b_pos]
        hi = first_bit_shift if b_pos == byte_idx else 7
        for shift in range(hi, -1, -1):
            bit = (byte_val >> shift) & 1
            node = node[bit]
            sym = node.get('sym')
            if sym is not None:
                if sym == BE.EOF_SYMBOL:
                    return b''.join(out)
                out.append(sym)
                node = decode_tree
    raise ValueError('truncated stream before EOF_SYMBOL in random-access decode')


def serialize_design_b_random_access_archive(
    entries: Sequence[bytes],
    docs_1: Sequence[bytes],
    docs_2: Sequence[bytes],
    *,
    lengths_1: dict[bytes, int] | None = None,
    lengths_2: dict[bytes, int] | None = None,
) -> bytes:
    """Serialize a complete self-contained Design B random-access archive with 4B/file index."""
    root = BE.build_trie(entries)
    if lengths_1 is not None and lengths_2 is not None:
        l1 = lengths_1
        l2 = lengths_2
        p1, _, _ = BE.segment_corpus_bits(docs_1, root, l1, max(l1.values()) + 1)
        p2, _, _ = BE.segment_corpus_bits(docs_2, root, l2, max(l2.values()) + 1)
    else:
        opt1 = BE.optimize_byte_segmentation(docs_1, root)['byte_min']
        opt2 = BE.optimize_byte_segmentation(docs_2, root)['byte_min']
        l1 = opt1['lengths']
        l2 = opt2['lengths']
        p1 = opt1['pieces']
        p2 = opt2['pieces']

    c1 = BE.assign_canonical_codes(l1)
    c2 = BE.assign_canonical_codes(l2)
    pay1, off1 = encode_stream_with_bit_offsets(p1, c1)
    pay2, off2 = encode_stream_with_bit_offsets(p2, c2)

    m_total = len(docs_1) + len(docs_2)
    buf = bytearray()
    buf.extend(b'BIT3')
    buf.extend(struct.pack('<HHB', len(entries), m_total, 2))
    for e in entries:
        buf.append(len(e))
        buf.extend(e)
    # 2 canonical Huffman code-length tables (|D| + 1 bytes each; 0 = unused)
    for tbl in (l1, l2):
        for e in entries:
            buf.append(tbl.get(e, 0))
        buf.append(tbl[BE.EOF_SYMBOL])

    # 4-byte seek index per file: bit 31 = stream_id, bits 30..0 = start bit offset
    for bit_off in off1:
        if bit_off >= (1 << 31):
            raise ValueError('stream 0 bit offset exceeds 31 bits')
        buf.extend(struct.pack('<I', bit_off))
    for bit_off in off2:
        if bit_off >= (1 << 31):
            raise ValueError('stream 1 bit offset exceeds 31 bits')
        buf.extend(struct.pack('<I', (1 << 31) | bit_off))

    buf.extend(struct.pack('<I', len(pay1)))
    buf.extend(pay1)
    buf.extend(pay2)
    return bytes(buf)


def unpack_index_and_trees(archive: bytes) -> dict[str, object]:
    if archive[:4] != b'BIT3':
        raise ValueError('bad magic')
    n_entries, n_files, n_tables = struct.unpack_from('<HHB', archive, 4)
    if n_tables != 2:
        raise ValueError('expected 2-table Design B archive')
    pos = 9
    entries: list[bytes] = []
    for _ in range(n_entries):
        ln = archive[pos]
        pos += 1
        entries.append(archive[pos:pos + ln])
        pos += ln
    trees = []
    for _ in range(2):
        lengths: dict[bytes, int] = {}
        for idx, e in enumerate(entries):
            bl = archive[pos + idx]
            if bl > 0:
                lengths[e] = bl
        eof_bl = archive[pos + n_entries]
        lengths[BE.EOF_SYMBOL] = eof_bl
        pos += n_entries + 1
        trees.append(BE.build_decode_tree(BE.assign_canonical_codes(lengths)))

    index_entries: list[tuple[int, int]] = []
    for _ in range(n_files):
        word = struct.unpack_from('<I', archive, pos)[0]
        pos += 4
        index_entries.append(((word >> 31) & 1, word & 0x7FFFFFFF))

    len_pay1 = struct.unpack_from('<I', archive, pos)[0]
    pos += 4
    pay1 = archive[pos:pos + len_pay1]
    pay2 = archive[pos + len_pay1:]
    return {
        'entries': entries,
        'trees': trees,
        'index': index_entries,
        'streams': (pay1, pay2),
    }


def decode_random_access_file(archive: bytes, file_index: int, parsed_header: dict[str, object] | None = None) -> bytes:
    hdr = parsed_header if parsed_header is not None else unpack_index_and_trees(archive)
    stream_id, bit_off = hdr['index'][file_index]
    return decode_one_doc_from_bit_offset(hdr['streams'][stream_id], bit_off, hdr['trees'][stream_id])
