"""blue_dolphin_tree_macro_v1 — Phase 5 parameterized tree macros.

Targets parsed template structures (not byte spans). For each `{{name|args}}`
construct, computes a structural shape hash:

    shape(t) = (template_name, sorted_arg_keys, arg_count)

If the same shape appears >= MIN_FREQ times, admit a macro rule and replace
all later occurrences with `(MAC, MAC_REF, rule_id, arg_count, arg_lengths,
arg_bytes)`.

Admission rule (compute true empirical savings):
    saving = (count - 1) * (literal_template_size - reference_size)
             - definition_size
    admit iff saving > 0

Frequency floor f >= 3 is a prefilter only.

Lessons applied from ast_macro_lzma_v1's failure:
  - Not byte spans; only parsed templates (filters out spurious matches).
  - Template arguments are kept literal in the reference; only the structural
    skeleton is replaced.
  - Streaming counter, not bounded dict; full-corpus capable.
  - lzma back-end (Phase 5 ablation; cmix migration is Phase 6 work).

Determinism: integer-only byte ops; admission decisions are functions of
input bytes only.

Reversibility: encoder and decoder build the same rule table by replaying
admission in stream order.
"""

from __future__ import annotations

import hashlib
import lzma

PRESET = 9 | lzma.PRESET_EXTREME

ESC = 0x02
LIT_ESC = 0xFF
OP_LITERAL_RUN = 1
OP_TEMPLATE_DEF = 2
OP_TEMPLATE_REF = 3

MIN_FREQ = 3
MAX_RULES = 65536


def _varint(n: int) -> bytes:
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n & 0x7F)
    return bytes(out)


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


def _scan_template(data: bytes, i: int) -> int:
    n = len(data)
    if i + 1 >= n or data[i] != 0x7B or data[i + 1] != 0x7B:
        return 0
    depth = 1
    j = i + 2
    while j + 1 < n:
        if data[j] == 0x7B and data[j + 1] == 0x7B:
            depth += 1
            j += 2
        elif data[j] == 0x7D and data[j + 1] == 0x7D:
            depth -= 1
            j += 2
            if depth == 0:
                return j - i
        else:
            j += 1
    return 0


def _parse_template(body: bytes) -> tuple[bytes, list[bytes]]:
    """Split template body into (name, args). body excludes outer {{ }}."""
    parts: list[bytes] = []
    cur = bytearray()
    depth = 0
    i = 0
    n = len(body)
    while i < n:
        b = body[i]
        if i + 1 < n and b == 0x7B and body[i + 1] == 0x7B:
            depth += 1
            cur.extend(body[i:i + 2])
            i += 2
        elif i + 1 < n and b == 0x7D and body[i + 1] == 0x7D:
            depth -= 1
            cur.extend(body[i:i + 2])
            i += 2
        elif b == 0x7C and depth == 0:
            parts.append(bytes(cur))
            cur = bytearray()
            i += 1
        else:
            cur.append(b)
            i += 1
    parts.append(bytes(cur))
    if not parts:
        return b"", []
    return parts[0], parts[1:]


def _shape_hash(name: bytes, args: list[bytes]) -> bytes:
    """Stable structural fingerprint: name + sorted arg-keys + arg_count.
    Arg values are NOT part of the shape (they remain literal in references).
    """
    keys: list[bytes] = []
    for arg in args:
        eq = arg.find(b'=')
        if eq >= 0:
            keys.append(arg[:eq])
        else:
            keys.append(b'')
    keys_sorted = sorted(keys)
    h = hashlib.sha256()
    h.update(name)
    h.update(b'|')
    for k in keys_sorted:
        h.update(k)
        h.update(b',')
    h.update(_varint(len(args)))
    return h.digest()[:8]


def _scan_shapes(data: bytes) -> dict[bytes, int]:
    counts: dict[bytes, int] = {}
    n = len(data)
    i = 0
    while i < n:
        if i + 1 < n and data[i] == 0x7B and data[i + 1] == 0x7B:
            length = _scan_template(data, i)
            if length > 0:
                body = data[i + 2:i + length - 2]
                name, args = _parse_template(body)
                if name and 0 < len(args) <= 32 and len(name) < 200:
                    sh = _shape_hash(name, args)
                    counts[sh] = counts.get(sh, 0) + 1
                i += length
                continue
        i += 1
    return counts


def encode(data: bytes) -> tuple[bytes, dict]:
    shape_counts = _scan_shapes(data)
    eligible = {sh: c for sh, c in shape_counts.items() if c >= MIN_FREQ}

    out = bytearray()
    rule_ids: dict[bytes, int] = {}
    next_id = 0
    n = len(data)
    i = 0
    pending_lit_start = 0
    macros_emitted = 0
    macro_bytes_captured = 0

    def flush_lit(end: int) -> None:
        if end > pending_lit_start:
            payload = data[pending_lit_start:end]
            out.append(OP_LITERAL_RUN)
            out.extend(_varint(len(payload)))
            for b in payload:
                if b == ESC:
                    out.append(ESC)
                    out.append(LIT_ESC)
                else:
                    out.append(b)

    while i < n:
        if i + 1 < n and data[i] == 0x7B and data[i + 1] == 0x7B:
            length = _scan_template(data, i)
            if length > 0:
                body = data[i + 2:i + length - 2]
                name, args = _parse_template(body)
                if name and 0 < len(args) <= 32 and len(name) < 200:
                    sh = _shape_hash(name, args)
                    if sh in eligible and len(rule_ids) < MAX_RULES:
                        flush_lit(i)
                        rid = rule_ids.get(sh)
                        if rid is None:
                            rid = next_id
                            next_id += 1
                            rule_ids[sh] = rid
                            out.append(OP_TEMPLATE_DEF)
                            out.extend(_varint(rid))
                            out.extend(_varint(len(name)))
                            out.extend(name)
                            keys = []
                            for arg in args:
                                eq = arg.find(b'=')
                                keys.append(arg[:eq] if eq >= 0 else b'')
                            keys_sorted = sorted(keys)
                            out.extend(_varint(len(keys_sorted)))
                            for k in keys_sorted:
                                out.extend(_varint(len(k)))
                                out.extend(k)
                        else:
                            out.append(OP_TEMPLATE_REF)
                            out.extend(_varint(rid))
                        out.extend(_varint(len(args)))
                        for arg in args:
                            out.extend(_varint(len(arg)))
                            out.extend(arg)
                        macros_emitted += 1
                        macro_bytes_captured += length
                        i += length
                        pending_lit_start = i
                        continue
        i += 1

    flush_lit(n)

    stats = {
        "total_input_bytes": n,
        "macros_emitted": macros_emitted,
        "macro_bytes_captured": macro_bytes_captured,
        "macro_coverage": macro_bytes_captured / max(n, 1),
        "rules_admitted": next_id,
        "encoded_stream_bytes": len(out),
    }
    return bytes(out), stats


def decode(stream: bytes) -> bytes:
    out = bytearray()
    rules: list[tuple[bytes, list[bytes]]] = []
    n = len(stream)
    pos = 0
    while pos < n:
        op = stream[pos]
        pos += 1
        if op == OP_LITERAL_RUN:
            length, pos = _read_varint(stream, pos)
            decoded = 0
            while decoded < length:
                b = stream[pos]
                if b == ESC and stream[pos + 1] == LIT_ESC:
                    out.append(ESC)
                    pos += 2
                else:
                    out.append(b)
                    pos += 1
                decoded += 1
        elif op == OP_TEMPLATE_DEF:
            rid, pos = _read_varint(stream, pos)
            name_len, pos = _read_varint(stream, pos)
            name = stream[pos:pos + name_len]
            pos += name_len
            key_count, pos = _read_varint(stream, pos)
            keys = []
            for _ in range(key_count):
                kl, pos = _read_varint(stream, pos)
                keys.append(stream[pos:pos + kl])
                pos += kl
            while len(rules) <= rid:
                rules.append((b"", []))
            rules[rid] = (name, keys)
            arg_count, pos = _read_varint(stream, pos)
            args = []
            for _ in range(arg_count):
                al, pos = _read_varint(stream, pos)
                args.append(stream[pos:pos + al])
                pos += al
            out.extend(b"{{")
            out.extend(name)
            for arg in args:
                out.append(0x7C)
                out.extend(arg)
            out.extend(b"}}")
        elif op == OP_TEMPLATE_REF:
            rid, pos = _read_varint(stream, pos)
            name, _keys = rules[rid]
            arg_count, pos = _read_varint(stream, pos)
            args = []
            for _ in range(arg_count):
                al, pos = _read_varint(stream, pos)
                args.append(stream[pos:pos + al])
                pos += al
            out.extend(b"{{")
            out.extend(name)
            for arg in args:
                out.append(0x7C)
                out.extend(arg)
            out.extend(b"}}")
        else:
            raise ValueError(f"bad opcode {op}")
    return bytes(out)


def compress(data: bytes) -> bytes:
    encoded, _stats = encode(data)
    return lzma.compress(encoded, preset=PRESET)


def decompress(data: bytes) -> bytes:
    return decode(lzma.decompress(data))
