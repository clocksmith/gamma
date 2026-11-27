"""Frozen binary package codecs and exact bit accounting for B3.

Formats:
- B3H1: Primary B3 <=64-entry Canonical Huffman package (mode 0 = zero-escape witness;
  mode 1 = transfer with 1-bit selector + raw UTF-8 fallback; mode 2 = transfer with
  1-bit selector + frozen matched80 BPE-255+escape fallback).
- B3P1: Fixed-width (6-bit for <=64 entries; 7/8-bit for Arm 1 flat-tiling controls)
  dictionary + bit-packed token stream (zero escapes).
- B3B1: Frozen 256-entry raw-code BPE package (base byte table + merge-pair table +
  fixed-8 or canonical Huffman coded stream; optional escape for transfer).

Every single bit is explicitly accounted in `complete_bits`, including header,
dictionary/code/merge tables, selector flags, coded payload, padding, helper bytes,
and charged standalone reference decoder bytes (`b3_ref_decoder.py`).
"""
from __future__ import annotations

import hashlib
import heapq
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REF_DECODER_PATH = HERE / "b3_ref_decoder.py"
WITNESS_DECODER_PATH = HERE / "b3_witness_decoder.py"


def decoder_machinery_bytes(witness_only: bool = False) -> int:
    path = WITNESS_DECODER_PATH if witness_only else REF_DECODER_PATH
    return path.stat().st_size


def decoder_machinery_bits(witness_only: bool = False) -> int:
    return decoder_machinery_bytes(witness_only=witness_only) * 8


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encode_varint(n: int) -> bytes:
    if n < 0:
        raise ValueError("varint must be non-negative")
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def pack_fixed_ids(ids: list[int], width: int) -> bytes:
    if not (1 <= width <= 8):
        raise ValueError(f"unsupported width {width}")
    mask = (1 << width) - 1
    out = bytearray()
    acc = 0
    nbits = 0
    for idx in ids:
        if idx < 0 or idx > mask:
            raise ValueError(f"token id {idx} out of range for width {width}")
        acc = (acc << width) | idx
        nbits += width
        while nbits >= 8:
            nbits -= 8
            out.append((acc >> nbits) & 0xFF)
            acc &= (1 << nbits) - 1
    if nbits:
        out.append((acc << (8 - nbits)) & 0xFF)
    return bytes(out)


def huffman_lengths(counts: list[int]) -> list[int]:
    n = len(counts)
    if n <= 1:
        return [1] * n
    heap = [(max(1, c), i) for i, c in enumerate(counts)]
    heapq.heapify(heap)
    parent = [-1] * (2 * n - 1)
    nxt = n
    while len(heap) > 1:
        c1, a = heapq.heappop(heap)
        c2, b = heapq.heappop(heap)
        parent[a] = nxt
        parent[b] = nxt
        heapq.heappush(heap, (c1 + c2, nxt))
        nxt += 1
    depth = [0] * (2 * n - 1)
    for node in range(2 * n - 3, -1, -1):
        depth[node] = depth[parent[node]] + 1
    return depth[:n]


def canonical_codes(lengths: list[int]) -> list[int]:
    order = sorted(range(len(lengths)), key=lambda s: (lengths[s], s))
    codes = [0] * len(lengths)
    code = 0
    prev = lengths[order[0]]
    for s in order:
        code <<= lengths[s] - prev
        prev = lengths[s]
        codes[s] = code
        code += 1
    return codes


def encode_b3p1(vocab: list[str], sequences: list[list[int]], width: int = 6) -> tuple[bytes, dict[str, Any]]:
    """Encode fixed-width literal package B3P1 (zero escapes)."""
    if len(vocab) == 0 or len(vocab) > (1 << width):
        raise ValueError(f"vocab size {len(vocab)} exceeds width {width} capacity {1 << width}")
    if len(set(vocab)) != len(vocab):
        raise ValueError("duplicate dictionary entries")

    header = bytearray(b"B3P1")
    header.append(width)
    header.extend(encode_varint(len(vocab)))
    dict_entry_bytes = 0
    for entry in vocab:
        raw = entry.encode("utf-8")
        if not raw:
            raise ValueError("empty dictionary entry")
        header.extend(encode_varint(len(raw)))
        header.extend(raw)
        dict_entry_bytes += len(raw)

    stream = bytearray()
    stream.extend(encode_varint(len(sequences)))
    total_tokens = 0
    framing_bytes = len(encode_varint(len(sequences)))
    padding_bits = 0

    for seq in sequences:
        for tok in seq:
            if tok < 0 or tok >= len(vocab):
                raise ValueError(f"invalid token id {tok}")
        cnt_var = encode_varint(len(seq))
        framing_bytes += len(cnt_var)
        stream.extend(cnt_var)
        packed = pack_fixed_ids(seq, width)
        stream.extend(packed)
        total_tokens += len(seq)
        padding_bits += len(packed) * 8 - len(seq) * width

    package = bytes(header) + bytes(stream)
    dec_bits = decoder_machinery_bits()
    breakdown = {
        "format": "B3P1",
        "width_bits": width,
        "entries": len(vocab),
        "programs": len(sequences),
        "total_tokens": total_tokens,
        "header_bits": len(header) * 8,
        "dictionary_utf8_bytes": dict_entry_bytes,
        "framing_bits": framing_bytes * 8,
        "token_payload_bits": total_tokens * width,
        "padding_bits": padding_bits,
        "coded_stream_bits": len(stream) * 8,
        "package_bytes_excluding_decoder": len(package),
        "package_bits_excluding_decoder": len(package) * 8,
        "decoder_machinery_bytes": decoder_machinery_bytes(),
        "decoder_machinery_bits": dec_bits,
        "complete_bits": len(package) * 8 + dec_bits,
        "package_sha256": sha256_bytes(package),
    }
    return package, breakdown


def encode_b3h1(
    vocab: list[str],
    records: list[dict[str, Any]],
    lengths: list[int] | None = None,
    fallback_bpe: dict[str, Any] | None = None,
    transfer_mode: bool = False,
) -> tuple[bytes, dict[str, Any]]:
    """Encode B3H1 Canonical Huffman <=64-entry package (witness or transfer).

    `records`: list of dicts:
      - `covered`: bool
      - `token_ids`: list[int] (when covered=True)
      - `raw_bytes`: bytes (when covered=False)
      - `fallback_bpe_seq`: list[tuple[int, int | None]] (when covered=False & fallback_bpe given)
    `lengths`: optional frozen Huffman length table of size len(vocab)+1 (required for transfer
      so code lengths are strictly frozen from fit set!).
    """
    n = len(vocab)
    if not (1 <= n <= 64):
        raise ValueError(f"B3H1 requires 1..64 entries, got {n}")
    if len(set(vocab)) != n:
        raise ValueError("duplicate dictionary entries")

    refused_count = sum(1 for r in records if not r["covered"])
    if not transfer_mode:
        if refused_count > 0:
            raise ValueError("witness mode B3H1 forbids refusals/escapes")
        fb_mode = 0
    elif fallback_bpe is not None and refused_count > 0:
        fb_mode = 2
    else:
        fb_mode = 1

    if lengths is None:
        counts = [0] * (n + 1)
        for rec in records:
            if rec["covered"]:
                for tok in rec["token_ids"]:
                    counts[tok] += 1
                counts[n] += 1
        lengths = huffman_lengths(counts)
    if len(lengths) != n + 1:
        raise ValueError(f"expected {n + 1} code lengths, got {len(lengths)}")
    codes = canonical_codes(lengths)

    header = bytearray(b"B3H1")
    header.append(fb_mode)
    header.extend(encode_varint(n))
    dict_utf8_bytes = 0
    for entry in vocab:
        raw = entry.encode("utf-8")
        if not raw:
            raise ValueError("empty entry")
        header.extend(encode_varint(len(raw)))
        header.extend(raw)
        dict_utf8_bytes += len(raw)
    header.extend(bytes(lengths))
    primary_header_bits = len(header) * 8

    fb_table_start = len(header)
    if fb_mode == 2:
        assert fallback_bpe is not None
        base_alpha = fallback_bpe["base_alphabet"]
        merges = fallback_bpe["merges"]
        header.extend(encode_varint(len(base_alpha)))
        header.extend(bytes(base_alpha))
        header.extend(encode_varint(len(merges)))
        for a, b in merges:
            header.append(a)
            header.append(b)
    fallback_table_bits = (len(header) - fb_table_start) * 8

    stream = bytearray()
    stream.extend(encode_varint(len(records)))
    selector_bits = 0
    if fb_mode != 0:
        sel = bytearray((len(records) + 7) // 8)
        for k, rec in enumerate(records):
            if not rec["covered"]:
                sel[k >> 3] |= 1 << (7 - (k & 7))
        stream.extend(sel)
        selector_bits = len(sel) * 8

    acc = 0
    nbits = 0
    covered_tokens = 0
    covered_raw_bits = 0
    fallback_bytes = 0
    fallback_tokens = 0
    pad_bits_total = 0

    def put_bits(code: int, ln: int) -> None:
        nonlocal acc, nbits, covered_raw_bits
        acc = (acc << ln) | code
        nbits += ln
        covered_raw_bits += ln
        while nbits >= 8:
            nbits -= 8
            stream.append((acc >> nbits) & 0xFF)
            acc &= (1 << nbits) - 1

    def flush_byte() -> None:
        nonlocal acc, nbits, pad_bits_total
        if nbits:
            pad = 8 - nbits
            stream.append((acc << pad) & 0xFF)
            pad_bits_total += pad
            acc = 0
            nbits = 0

    for rec in records:
        if rec["covered"]:
            for tok in rec["token_ids"]:
                if tok < 0 or tok >= n:
                    raise ValueError(f"invalid token id {tok}")
                put_bits(codes[tok], lengths[tok])
                covered_tokens += 1
            put_bits(codes[n], lengths[n])  # EOF
        else:
            flush_byte()
            if fb_mode == 1:
                raw = rec["raw_bytes"]
                chunk = encode_varint(len(raw)) + raw
                stream.extend(chunk)
                fallback_bytes += len(chunk)
            else:
                assert fallback_bpe is not None
                seq = rec["fallback_bpe_seq"]
                esc = len(fallback_bpe["base_alphabet"]) + len(fallback_bpe["merges"])
                chunk = bytearray(encode_varint(len(seq)))
                for sym, raw_b in seq:
                    chunk.append(sym)
                    if sym == esc:
                        assert raw_b is not None
                        chunk.append(raw_b)
                stream.extend(chunk)
                fallback_bytes += len(chunk)
                fallback_tokens += len(seq)
    flush_byte()

    package = bytes(header) + bytes(stream)
    witness_only = fb_mode == 0
    dec_bytes = decoder_machinery_bytes(witness_only=witness_only)
    dec_bits = dec_bytes * 8
    full_dec_bits = decoder_machinery_bits(witness_only=False)
    breakdown = {
        "format": "B3H1",
        "fallback_mode": ["none_witness", "raw_utf8", "frozen_matched80_bpe255_escape"][fb_mode],
        "entries": n,
        "programs": len(records),
        "covered_programs": len(records) - refused_count,
        "refused_programs": refused_count,
        "dictionary_utf8_bytes": dict_utf8_bytes,
        "code_table_bits": (n + 1) * 8,
        "primary_header_bits": primary_header_bits,
        "fallback_table_bits": fallback_table_bits,
        "selector_bits": selector_bits,
        "covered_tokens": covered_tokens,
        "covered_payload_bits": covered_raw_bits,
        "padding_bits": pad_bits_total,
        "fallback_stream_bits": fallback_bytes * 8,
        "fallback_tokens": fallback_tokens,
        "fallback_total_bits": fallback_table_bits + selector_bits + fallback_bytes * 8,
        "header_bits": len(header) * 8,
        "coded_stream_bits": len(stream) * 8,
        "package_bytes_excluding_decoder": len(package),
        "package_bits_excluding_decoder": len(package) * 8,
        "decoder_machinery_file": WITNESS_DECODER_PATH.name if witness_only else REF_DECODER_PATH.name,
        "decoder_machinery_bytes": dec_bytes,
        "decoder_machinery_bits": dec_bits,
        "full_transfer_decoder_bits": full_dec_bits,
        "complete_bits": len(package) * 8 + dec_bits,
        "complete_bits_with_full_transfer_decoder": len(package) * 8 + full_dec_bits,
        "huffman_lengths": list(lengths),
        "package_sha256": sha256_bytes(package),
    }
    return package, breakdown


def encode_b3b1_bpe(
    base_alphabet: list[int],
    merges: list[tuple[int, int]],
    sequences: list[list[tuple[int, int | None]]],
    coding: str = "fixed8",
    allow_escape: bool = False,
) -> tuple[bytes, dict[str, Any]]:
    """Encode Arm 4 frozen 256-entry raw-code BPE package (B3B1)."""
    vocab_size = len(base_alphabet) + len(merges)
    max_syms = 255 if allow_escape else 256
    if vocab_size > max_syms:
        raise ValueError(f"BPE vocab {vocab_size} exceeds {max_syms}")

    header = bytearray(b"B3B1")
    header.append(0 if coding == "fixed8" else 1)
    header.append(1 if allow_escape else 0)
    header.extend(encode_varint(len(base_alphabet)))
    header.extend(bytes(base_alphabet))
    header.extend(encode_varint(len(merges)))
    for a, b in merges:
        header.append(a)
        header.append(b)

    total_tokens = sum(len(s) for s in sequences)
    total_escapes = sum(1 for s in sequences for sym, _ in s if sym == vocab_size)

    if coding == "fixed8":
        stream = bytearray()
        stream.extend(encode_varint(len(sequences)))
        for seq in sequences:
            stream.extend(encode_varint(len(seq)))
            for sym, raw_b in seq:
                stream.append(sym)
                if sym == vocab_size:
                    assert raw_b is not None
                    stream.append(raw_b)
        package = bytes(header) + bytes(stream)
        return package, {
            "format": "B3B1-fixed8",
            "coding": "fixed8",
            "allow_escape": allow_escape,
            "base_alphabet": len(base_alphabet),
            "merges": len(merges),
            "entries": vocab_size + (1 if allow_escape else 0),
            "programs": len(sequences),
            "total_tokens": total_tokens,
            "total_escapes": total_escapes,
            "header_bits": len(header) * 8,
            "coded_stream_bits": len(stream) * 8,
            "package_bytes_excluding_decoder": len(package),
            "package_bits_excluding_decoder": len(package) * 8,
            "complete_bits": len(package) * 8,
            "package_sha256": sha256_bytes(package),
        }

    n_syms = vocab_size + (1 if allow_escape else 0) + 1
    eof_sym = n_syms - 1
    counts = [0] * n_syms
    for seq in sequences:
        for sym, _ in seq:
            counts[sym] += 1
    counts[eof_sym] = len(sequences)
    lengths = huffman_lengths(counts)
    codes = canonical_codes(lengths)
    header.extend(bytes(lengths))

    stream = bytearray()
    stream.extend(encode_varint(len(sequences)))
    acc = 0
    nbits = 0
    raw_payload_bits = 0

    def put(code: int, ln: int) -> None:
        nonlocal acc, nbits, raw_payload_bits
        acc = (acc << ln) | code
        nbits += ln
        raw_payload_bits += ln
        while nbits >= 8:
            nbits -= 8
            stream.append((acc >> nbits) & 0xFF)
            acc &= (1 << nbits) - 1

    for seq in sequences:
        for sym, raw_b in seq:
            put(codes[sym], lengths[sym])
            if allow_escape and sym == vocab_size:
                assert raw_b is not None
                put(raw_b, 8)
        put(codes[eof_sym], lengths[eof_sym])
    pad_bits = (-nbits) % 8
    if nbits:
        stream.append((acc << pad_bits) & 0xFF)

    package = bytes(header) + bytes(stream)
    return package, {
        "format": "B3B1-huffman",
        "coding": "huffman",
        "allow_escape": allow_escape,
        "base_alphabet": len(base_alphabet),
        "merges": len(merges),
        "entries": vocab_size + (1 if allow_escape else 0),
        "programs": len(sequences),
        "total_tokens": total_tokens,
        "total_escapes": total_escapes,
        "header_bits": len(header) * 8,
        "raw_payload_bits": raw_payload_bits,
        "padding_bits": pad_bits,
        "coded_stream_bits": len(stream) * 8,
        "package_bytes_excluding_decoder": len(package),
        "package_bits_excluding_decoder": len(package) * 8,
        "complete_bits": len(package) * 8,
        "package_sha256": sha256_bytes(package),
    }
