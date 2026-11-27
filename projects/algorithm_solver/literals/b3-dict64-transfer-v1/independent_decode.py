"""Independent zero-shared-code decoder for B3 binary packages (B3H1, B3P1, B3B1).

Reconstructs every program SOLELY from frozen package bytes with zero external
state, zero hidden helpers, and zero imports from package_codec.py / rewriter.py.

Strict failure guarantees (exercised by dev_gate negative controls):
- Rejects bad magic, invalid widths/modes, dictionary size > 64 (B3H1) or > 2^width (B3P1).
- Rejects duplicate/empty entries, invalid UTF-8, invalid Huffman Kraft sum.
- Rejects ANY invalid dictionary ID (>= entry_count) in B3P1 or invalid prefix/ID in B3H1.
- Rejects non-zero trailing padding bits or trailing garbage bytes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


class DecodeError(ValueError):
    """Raised whenever a B3 package violates any binary or dictionary invariant."""


def _read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if pos >= len(buf):
            raise DecodeError("truncated varint")
        byte = buf[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return value, pos
        shift += 7
        if shift > 35:
            raise DecodeError("varint overflow")


def _unpack_fixed(buf: bytes, pos: int, count: int, width: int, vocab_len: int) -> tuple[list[int], int]:
    byte_len = (count * width + 7) // 8
    if pos + byte_len > len(buf):
        raise DecodeError("truncated fixed-width token stream")
    mask = (1 << width) - 1
    acc = 0
    bits = 0
    ids: list[int] = []
    for byte in buf[pos : pos + byte_len]:
        acc = (acc << 8) | byte
        bits += 8
        while bits >= width and len(ids) < count:
            bits -= width
            tok = (acc >> bits) & mask
            acc &= (1 << bits) - 1
            if tok >= vocab_len:
                raise DecodeError(f"invalid dictionary ID {tok} (vocab_len={vocab_len})")
            ids.append(tok)
    if len(ids) != count:
        raise DecodeError(f"decoded {len(ids)} tokens, expected {count}")
    if acc != 0:
        raise DecodeError("non-zero padding bits in fixed-width stream")
    return ids, pos + byte_len


def _read_dictionary(buf: bytes, pos: int, max_entries: int) -> tuple[list[bytes], int]:
    count, pos = _read_varint(buf, pos)
    if count < 1 or count > max_entries:
        raise DecodeError(f"dictionary size {count} outside [1, {max_entries}]")
    entries: list[bytes] = []
    seen: set[bytes] = set()
    for _ in range(count):
        ln, pos = _read_varint(buf, pos)
        if ln < 1 or pos + ln > len(buf):
            raise DecodeError("invalid or truncated dictionary entry")
        raw = buf[pos : pos + ln]
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DecodeError(f"invalid UTF-8 in dictionary entry: {exc}") from exc
        if raw in seen:
            raise DecodeError("duplicate dictionary entry")
        seen.add(raw)
        entries.append(raw)
        pos += ln
    return entries, pos


def _canonical_huffman_table(lengths: list[int]) -> dict[tuple[int, int], int]:
    if not lengths or min(lengths) < 1 or max(lengths) > 32:
        raise DecodeError("invalid Huffman code lengths")
    top = max(lengths)
    if sum(1 << (top - ln) for ln in lengths) != (1 << top):
        raise DecodeError("Huffman Kraft sum mismatch")
    order = sorted(range(len(lengths)), key=lambda s: (lengths[s], s))
    table: dict[tuple[int, int], int] = {}
    code = 0
    prev = lengths[order[0]]
    for sym in order:
        code <<= lengths[sym] - prev
        prev = lengths[sym]
        table[(lengths[sym], code)] = sym
        code += 1
    return table


def decode_b3h1(buf: bytes) -> dict[str, Any]:
    if len(buf) < 7 or buf[:4] != b"B3H1":
        raise DecodeError("bad B3H1 magic")
    fb_mode = buf[4]
    if fb_mode not in (0, 1, 2):
        raise DecodeError(f"invalid B3H1 fallback mode {fb_mode}")
    entries, pos = _read_dictionary(buf, 5, 64)
    n = len(entries)
    if pos + n + 1 > len(buf):
        raise DecodeError("truncated B3H1 Huffman table")
    lengths = list(buf[pos : pos + n + 1])
    pos += n + 1
    table = _canonical_huffman_table(lengths)

    fb_vocab: list[bytes] | None = None
    if fb_mode == 2:
        n_base, pos = _read_varint(buf, pos)
        if pos + n_base > len(buf):
            raise DecodeError("truncated B3H1 fallback base alphabet")
        fb_vocab = [bytes([buf[pos + i]]) for i in range(n_base)]
        pos += n_base
        n_merges, pos = _read_varint(buf, pos)
        if pos + 2 * n_merges > len(buf):
            raise DecodeError("truncated B3H1 fallback merges")
        for _ in range(n_merges):
            a, b = buf[pos], buf[pos + 1]
            pos += 2
            if a >= len(fb_vocab) or b >= len(fb_vocab):
                raise DecodeError("invalid B3H1 fallback merge")
            fb_vocab.append(fb_vocab[a] + fb_vocab[b])

    n_programs, pos = _read_varint(buf, pos)
    modes = [0] * n_programs
    if fb_mode != 0:
        sel_bytes = (n_programs + 7) // 8
        if pos + sel_bytes > len(buf):
            raise DecodeError("truncated B3H1 selector bitmap")
        sel_raw = buf[pos : pos + sel_bytes]
        pos += sel_bytes
        for k in range(n_programs, sel_bytes * 8):
            if (sel_raw[k >> 3] >> (7 - (k & 7))) & 1:
                raise DecodeError("non-zero padding bit in B3H1 selector bitmap")
        modes = [(sel_raw[k >> 3] >> (7 - (k & 7))) & 1 for k in range(n_programs)]

    programs: list[str] = []
    token_counts: list[int] = []
    used_ids: set[int] = set()
    bitpos = pos * 8
    total_bits = len(buf) * 8

    for m in modes:
        if m == 0:
            cur = bytearray()
            code = 0
            ln = 0
            nt = 0
            while True:
                if bitpos >= total_bits:
                    raise DecodeError("truncated B3H1 Huffman stream")
                bit = (buf[bitpos >> 3] >> (7 - (bitpos & 7))) & 1
                bitpos += 1
                code = (code << 1) | bit
                ln += 1
                if ln > 32:
                    raise DecodeError("invalid Huffman code prefix")
                sym = table.get((ln, code))
                if sym is None:
                    continue
                code = 0
                ln = 0
                if sym == n:
                    break
                if sym < 0 or sym >= n:
                    raise DecodeError(f"invalid dictionary ID {sym} >= {n}")
                used_ids.add(sym)
                cur.extend(entries[sym])
                nt += 1
            programs.append(cur.decode("utf-8"))
            token_counts.append(nt)
        else:
            if bitpos & 7:
                rem = 8 - (bitpos & 7)
                if buf[bitpos >> 3] & ((1 << rem) - 1):
                    raise DecodeError("non-zero alignment padding before fallback record")
                bitpos += rem
            pos = bitpos >> 3
            if fb_mode == 1:
                ln, pos = _read_varint(buf, pos)
                if pos + ln > len(buf):
                    raise DecodeError("truncated B3H1 raw fallback record")
                programs.append(buf[pos : pos + ln].decode("utf-8"))
                pos += ln
                token_counts.append(0)
            else:
                assert fb_vocab is not None
                nt, pos = _read_varint(buf, pos)
                esc = len(fb_vocab)
                cur = bytearray()
                for _ in range(nt):
                    if pos >= len(buf):
                        raise DecodeError("truncated B3H1 BPE fallback record")
                    sym = buf[pos]
                    pos += 1
                    if sym == esc:
                        if pos >= len(buf):
                            raise DecodeError("truncated B3H1 BPE fallback escape")
                        cur.append(buf[pos])
                        pos += 1
                    elif sym < esc:
                        cur.extend(fb_vocab[sym])
                    else:
                        raise DecodeError(f"invalid B3H1 fallback ID {sym} >= {esc}")
                programs.append(cur.decode("utf-8"))
                token_counts.append(nt)
            bitpos = pos * 8

    rem_bits = total_bits - bitpos
    if rem_bits >= 8:
        raise DecodeError(f"trailing bytes after B3H1 stream: {rem_bits} bits")
    while bitpos < total_bits:
        if (buf[bitpos >> 3] >> (7 - (bitpos & 7))) & 1:
            raise DecodeError("non-zero padding bit at end of B3H1 stream")
        bitpos += 1

    return {
        "format": "B3H1",
        "fallback_mode": fb_mode,
        "dictionary": [e.decode("utf-8") for e in entries],
        "programs": programs,
        "modes": modes,
        "token_counts": token_counts,
        "used_entries": len(used_ids),
        "covered_count": sum(m == 0 for m in modes),
        "fallback_count": sum(m == 1 for m in modes),
        "package_bytes": len(buf),
        "package_sha256": hashlib.sha256(buf).hexdigest(),
    }


def decode_b3p1(buf: bytes, max_width: int = 8) -> dict[str, Any]:
    if len(buf) < 6 or buf[:4] != b"B3P1":
        raise DecodeError("bad B3P1 magic")
    width = buf[4]
    if width < 1 or width > max_width:
        raise DecodeError(f"invalid B3P1 width {width}")
    entries, pos = _read_dictionary(buf, 5, 1 << width)
    n_programs, pos = _read_varint(buf, pos)
    programs: list[str] = []
    token_counts: list[int] = []
    used_ids: set[int] = set()
    for _ in range(n_programs):
        n_tok, pos = _read_varint(buf, pos)
        ids, pos = _unpack_fixed(buf, pos, n_tok, width, len(entries))
        used_ids.update(ids)
        raw = b"".join(entries[i] for i in ids)
        programs.append(raw.decode("utf-8"))
        token_counts.append(n_tok)
    if pos != len(buf):
        raise DecodeError(f"trailing bytes after B3P1 stream: {len(buf) - pos}")
    return {
        "format": "B3P1",
        "width": width,
        "dictionary": [e.decode("utf-8") for e in entries],
        "programs": programs,
        "token_counts": token_counts,
        "used_entries": len(used_ids),
        "package_bytes": len(buf),
        "package_sha256": hashlib.sha256(buf).hexdigest(),
    }


def decode_b3b1(buf: bytes) -> dict[str, Any]:
    if len(buf) < 8 or buf[:4] != b"B3B1":
        raise DecodeError("bad B3B1 magic")
    coding = buf[4]
    allow_escape = buf[5]
    if coding not in (0, 1) or allow_escape not in (0, 1):
        raise DecodeError("invalid B3B1 flags")
    pos = 6
    n_base, pos = _read_varint(buf, pos)
    if pos + n_base > len(buf):
        raise DecodeError("truncated B3B1 base alphabet")
    vocab = [bytes([buf[pos + i]]) for i in range(n_base)]
    pos += n_base
    n_merges, pos = _read_varint(buf, pos)
    if pos + 2 * n_merges > len(buf):
        raise DecodeError("truncated B3B1 merges")
    for _ in range(n_merges):
        a, b = buf[pos], buf[pos + 1]
        pos += 2
        if a >= len(vocab) or b >= len(vocab):
            raise DecodeError(f"invalid B3B1 merge ({a}, {b})")
        vocab.append(vocab[a] + vocab[b])

    esc_sym = len(vocab)
    programs: list[bytes] = []
    total_tokens = 0
    total_escapes = 0

    if coding == 0:
        n_programs, pos = _read_varint(buf, pos)
        for _ in range(n_programs):
            n_tok, pos = _read_varint(buf, pos)
            out = bytearray()
            for _ in range(n_tok):
                if pos >= len(buf):
                    raise DecodeError("truncated B3B1 fixed8 stream")
                sym = buf[pos]
                pos += 1
                total_tokens += 1
                if allow_escape and sym == esc_sym:
                    if pos >= len(buf):
                        raise DecodeError("truncated B3B1 escape")
                    out.append(buf[pos])
                    pos += 1
                    total_escapes += 1
                elif sym < len(vocab):
                    out.extend(vocab[sym])
                else:
                    raise DecodeError(f"invalid B3B1 symbol {sym} >= {len(vocab)}")
            programs.append(bytes(out))
        if pos != len(buf):
            raise DecodeError(f"trailing bytes after B3B1 fixed8 stream: {len(buf) - pos}")
    else:
        n_syms = len(vocab) + (1 if allow_escape else 0) + 1
        eof_sym = n_syms - 1
        if pos + n_syms > len(buf):
            raise DecodeError("truncated B3B1 Huffman table")
        lengths = list(buf[pos : pos + n_syms])
        pos += n_syms
        table = _canonical_huffman_table(lengths)
        n_programs, pos = _read_varint(buf, pos)
        bitpos = pos * 8
        total_bits = len(buf) * 8

        def next_bit() -> int:
            nonlocal bitpos
            if bitpos >= total_bits:
                raise DecodeError("truncated B3B1 Huffman bitstream")
            bit = (buf[bitpos >> 3] >> (7 - (bitpos & 7))) & 1
            bitpos += 1
            return bit

        cur = bytearray()
        code = 0
        ln = 0
        while len(programs) < n_programs:
            code = (code << 1) | next_bit()
            ln += 1
            if ln > 32:
                raise DecodeError("invalid Huffman prefix")
            sym = table.get((ln, code))
            if sym is None:
                continue
            code = 0
            ln = 0
            if sym == eof_sym:
                programs.append(bytes(cur))
                cur = bytearray()
            elif allow_escape and sym == esc_sym:
                v = 0
                for _ in range(8):
                    v = (v << 1) | next_bit()
                cur.append(v)
                total_tokens += 1
                total_escapes += 1
            else:
                cur.extend(vocab[sym])
                total_tokens += 1
        rem_bits = total_bits - bitpos
        if rem_bits >= 8:
            raise DecodeError(f"trailing bytes after B3B1 Huffman stream: {rem_bits} bits")
        for _ in range(rem_bits):
            if next_bit() != 0:
                raise DecodeError("non-zero padding bit in B3B1 Huffman stream")

    return {
        "format": "B3B1-fixed8" if coding == 0 else "B3B1-huffman",
        "vocab_size": len(vocab),
        "programs": [p.decode("utf-8") for p in programs],
        "total_tokens": total_tokens,
        "total_escapes": total_escapes,
        "package_bytes": len(buf),
        "package_sha256": hashlib.sha256(buf).hexdigest(),
    }


def decode_package(buf: bytes) -> dict[str, Any]:
    if len(buf) < 4:
        raise DecodeError("package shorter than 4-byte magic")
    magic = buf[:4]
    if magic == b"B3H1":
        return decode_b3h1(buf)
    if magic == b"B3P1":
        return decode_b3p1(buf)
    if magic == b"B3B1":
        return decode_b3b1(buf)
    raise DecodeError(f"unknown package magic {magic!r}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python independent_decode.py <package.bin>")
    raw = Path(sys.argv[1]).read_bytes()
    decoded = decode_package(raw)
    print(json.dumps({k: v for k, v in decoded.items() if k != "programs"}, indent=2))
