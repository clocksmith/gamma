"""Deterministic AST tokenizer for enwik9 — Phase A of Track B.

Emits a single opcode stream:

    OP_LITERAL  (0x01)   varint length   raw bytes
    OP_XML      (0x02)   varint length   raw bytes (full <...> span)
    OP_WLINK    (0x03)   varint length   raw bytes (full [[...]] span)
    OP_TMPL     (0x04)   varint length   raw bytes (full {{...}} span)

Reversibility: decode(encode(x)) == x byte-exact, by construction —
every input byte appears in exactly one opcode payload.

Determinism: pure integer byte-level scanning. No regex, no locale,
no float, no Python str. Two hosts running this on the same input
produce byte-identical output.

Patch tracking: when the parser sees a structural prefix (`<`, `[[`,
`{{`) but cannot parse a valid span, the prefix bytes fall through
into literal output and are counted as patch bytes for the ledger.
"""

from __future__ import annotations

OP_LITERAL = 1
OP_XML = 2
OP_WLINK = 3
OP_TMPL = 4

# Cap structural-span lookahead. Anything longer is treated as malformed
# and falls through to literal. 1 MB is generous for any real Wikipedia
# tag, link, or template; protects against a single missing `>` running
# parsing to end-of-corpus.
MAX_STRUCTURAL_LEN = 1 << 20


def varint_encode(n: int) -> bytes:
    if n < 0:
        raise ValueError("varint negative")
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n & 0x7F)
    return bytes(out)


def varint_decode(buf: bytes, pos: int) -> tuple[int, int]:
    n = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        n |= (b & 0x7F) << shift
        if not (b & 0x80):
            return n, pos
        shift += 7


def _parse_xml(data: bytes, i: int) -> int:
    n = len(data)
    end_cap = min(n, i + MAX_STRUCTURAL_LEN)
    j = i + 1
    while j < end_cap:
        b = data[j]
        if b == 0x3E:  # '>'
            return j - i + 1
        if b == 0x3C:  # nested '<' = malformed for Phase A
            return 0
        j += 1
    return 0


def _parse_pair(data: bytes, i: int, open_a: int, open_b: int,
                close_a: int, close_b: int) -> int:
    n = len(data)
    end_cap = min(n, i + MAX_STRUCTURAL_LEN)
    depth = 1
    j = i + 2
    while j + 1 < end_cap:
        if data[j] == open_a and data[j + 1] == open_b:
            depth += 1
            j += 2
        elif data[j] == close_a and data[j + 1] == close_b:
            depth -= 1
            j += 2
            if depth == 0:
                return j - i
        else:
            j += 1
    return 0


def encode(data: bytes) -> tuple[bytes, dict]:
    n = len(data)
    out = bytearray()

    structural_bytes = 0
    literal_bytes = 0
    patch_bytes = 0
    structural_attempts = 0
    structural_fails = 0
    pending_lit_start = 0
    i = 0

    def flush_literal(end: int) -> None:
        nonlocal literal_bytes
        if end > pending_lit_start:
            payload = data[pending_lit_start:end]
            out.append(OP_LITERAL)
            out.extend(varint_encode(len(payload)))
            out.extend(payload)
            literal_bytes += len(payload)

    while i < n:
        b = data[i]
        op = 0
        length = 0
        is_struct_prefix = False

        if b == 0x3C:
            is_struct_prefix = True
            structural_attempts += 1
            length = _parse_xml(data, i)
            if length:
                op = OP_XML
        elif b == 0x5B and i + 1 < n and data[i + 1] == 0x5B:
            is_struct_prefix = True
            structural_attempts += 1
            length = _parse_pair(data, i, 0x5B, 0x5B, 0x5D, 0x5D)
            if length:
                op = OP_WLINK
        elif b == 0x7B and i + 1 < n and data[i + 1] == 0x7B:
            is_struct_prefix = True
            structural_attempts += 1
            length = _parse_pair(data, i, 0x7B, 0x7B, 0x7D, 0x7D)
            if length:
                op = OP_TMPL

        if op:
            flush_literal(i)
            out.append(op)
            out.extend(varint_encode(length))
            out.extend(data[i:i + length])
            structural_bytes += length
            i += length
            pending_lit_start = i
        else:
            if is_struct_prefix:
                structural_fails += 1
                patch_bytes += 1
            i += 1

    flush_literal(n)

    stats = {
        "total_input_bytes": n,
        "structural_bytes": structural_bytes,
        "literal_bytes": literal_bytes,
        "patch_bytes": patch_bytes,
        "patch_fraction": patch_bytes / max(n, 1),
        "structural_attempts": structural_attempts,
        "structural_fails": structural_fails,
        "structural_fail_rate": (
            structural_fails / structural_attempts if structural_attempts else 0.0
        ),
        "encoded_stream_bytes": len(out),
    }
    return bytes(out), stats


def decode(stream: bytes) -> bytes:
    out = bytearray()
    pos = 0
    n = len(stream)
    while pos < n:
        _op = stream[pos]
        pos += 1
        length, pos = varint_decode(stream, pos)
        out.extend(stream[pos:pos + length])
        pos += length
    return bytes(out)
