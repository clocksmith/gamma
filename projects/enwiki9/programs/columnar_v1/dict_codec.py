"""dict_codec — narrow-vocabulary dictionary coding utility.

Build a dictionary of distinct values from a list, replace each instance
with a varint index. Dict ships in its own channel; index stream uses
small varints. The dict is sorted by frequency descending so the most
common values get the shortest indices (1-byte varint for the first 128).

Used by Phase 4 to dict-code the narrowest-vocab columns:
  - template_names (~228 distinct at 10 MB)
  - template_arg_keys (~50-100 distinct: url, title, date, publisher, ...)
  - wikilink_targets (~65K distinct of 109K wikilinks; popular ones
    repeat heavily — "United States" 386x at 10 MB)

Design property: dict-coding is a pure refactor of the SERIALIZATION
of these fields, not of the canonical tuple structure. The decoder
recovers the exact same canonical bytes; the format mask is unchanged.
Roundtrip rigor preserved.
"""

from __future__ import annotations

from collections import Counter


def write_varint(buf: bytearray, n: int) -> None:
    while n >= 0x80:
        buf.append((n & 0x7F) | 0x80)
        n >>= 7
    buf.append(n)


def read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    n = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        n |= (b & 0x7F) << shift
        if not (b & 0x80):
            return n, pos
        shift += 7


def build_dict(values: list[bytes]) -> tuple[bytes, dict[bytes, int]]:
    """Returns (dict_bytes, value -> idx mapping). Sorted by frequency
    descending so popular values get small indices."""
    counter: Counter = Counter(values)
    sorted_vals = [v for v, _ in counter.most_common()]
    out = bytearray()
    write_varint(out, len(sorted_vals))
    for v in sorted_vals:
        write_varint(out, len(v))
        out.extend(v)
    val_to_idx = {v: i for i, v in enumerate(sorted_vals)}
    return bytes(out), val_to_idx


def parse_dict(buf: bytes) -> list[bytes]:
    pos = 0
    count, pos = read_varint(buf, pos)
    values: list[bytes] = []
    for _ in range(count):
        L, pos = read_varint(buf, pos)
        values.append(buf[pos : pos + L])
        pos += L
    return values
