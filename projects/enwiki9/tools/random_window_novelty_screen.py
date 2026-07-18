#!/usr/bin/env python3
"""Screen reversible Wikipedia transforms on deterministic random windows.

This is a bounded representation-discovery probe.  It deliberately uses two
unrelated standard-library backends so a transform that only exploits one
coder's quirks is visible.  A positive result is proxy evidence only: it earns
an exact target-substrate trace, never a Hutter score claim.

Every candidate is decoder-rebuildable and carries no learned table payload:

* wiki_graph_mtf: move-to-front references for link targets, template names,
  parameter keys, URL hosts, and named references;
* rolling_phrase: phrases mined deterministically from the preceding block;
* title_echo: page-title phrases rebuilt from the title already decoded;
* xml_id_delta: per-page ID streams encoded as signed deltas;
* casefold_mask/casefold_positions: ASCII case residuals split from text.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import lzma
import random
import re
import struct
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_OUT = ROOT / "results" / "random_window_novelty_v1"
TARGET_GROSS_GAIN_PER_MILLION = 700.0
MARKER = 0


def uvarint(value: int) -> bytes:
    if value < 0:
        raise ValueError("uvarint requires a non-negative value")
    out = bytearray()
    while value >= 128:
        out.append((value & 127) | 128)
        value >>= 7
    out.append(value)
    return bytes(out)


def read_uvarint(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if pos >= len(data):
            raise ValueError("truncated varint")
        byte = data[pos]
        pos += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, pos
        shift += 7
        if shift > 63:
            raise ValueError("oversized varint")


def zigzag_encode(value: int) -> int:
    return value * 2 if value >= 0 else (-value * 2) - 1


def zigzag_decode(value: int) -> int:
    return value // 2 if value % 2 == 0 else -((value + 1) // 2)


def escape_literals(data: bytes) -> bytes:
    return data.replace(b"\0", b"\0\0")


def literal_or_reference_decode(
    data: bytes,
    pos: int,
    delimiters: frozenset[int],
    table: list[bytes],
) -> tuple[bytes, int, int]:
    """Decode one MTF field and return target, delimiter position, new pos."""

    if pos < len(data) and data[pos] == MARKER:
        if pos + 1 >= len(data):
            raise ValueError("truncated MTF marker")
        if data[pos + 1] == MARKER:
            end = pos + 2
            while end < len(data) and data[end] not in delimiters:
                end += 1
            if end >= len(data):
                raise ValueError("unterminated escaped MTF literal")
            return b"\0" + data[pos + 2 : end], end, end
        index_plus_one, end = read_uvarint(data, pos + 1)
        index = index_plus_one - 1
        if index < 0 or index >= len(table):
            raise ValueError(f"invalid MTF index {index}")
        if end >= len(data) or data[end] not in delimiters:
            raise ValueError("MTF reference not followed by a delimiter")
        return table[index], end, end

    end = pos
    while end < len(data) and data[end] not in delimiters:
        end += 1
    if end >= len(data):
        raise ValueError("unterminated MTF literal")
    return data[pos:end], end, end


def mtf_update(table: list[bytes], value: bytes, limit: int) -> None:
    try:
        table.remove(value)
    except ValueError:
        pass
    table.insert(0, value)
    if len(table) > limit:
        del table[limit:]


@dataclass(frozen=True)
class AnchorSpec:
    name: str
    anchor: bytes
    delimiters: bytes
    required_delimiters: bytes = b""

    @property
    def delimiter_set(self) -> frozenset[int]:
        return frozenset(self.delimiters)

    @property
    def required_set(self) -> frozenset[int]:
        return frozenset(self.required_delimiters)


GRAPH_SPECS = (
    AnchorSpec("link_target", b"[[", b"|]#\r\n"),
    AnchorSpec("template_name", b"{{", b"|}\r\n"),
    AnchorSpec("url_host", b"://", b"/ \t\r\n]|}\"'"),
    AnchorSpec("ref_name", b'<ref name="', b'"\r\n'),
    AnchorSpec("parameter_key", b"|", b"=|}\r\n", b"="),
)


def mtf_encode_pass(data: bytes, spec: AnchorSpec, limit: int) -> bytes:
    out = bytearray()
    table: list[bytes] = []
    pos = 0
    delimiters = spec.delimiter_set
    while True:
        anchor_pos = data.find(spec.anchor, pos)
        if anchor_pos < 0:
            out.extend(data[pos:])
            break
        target_pos = anchor_pos + len(spec.anchor)
        out.extend(data[pos:target_pos])
        end = target_pos
        while end < len(data) and data[end] not in delimiters:
            end += 1
        if end >= len(data):
            out.extend(data[target_pos:])
            break
        target = data[target_pos:end]
        delimiter = data[end]
        eligible = not spec.required_set or delimiter in spec.required_set
        if eligible and target:
            try:
                index = table.index(target)
            except ValueError:
                index = -1
            reference = b""
            if index >= 0:
                reference = bytes((MARKER,)) + uvarint(index + 1)
            if reference and len(reference) < len(target):
                out.extend(reference)
            elif target[0] == MARKER:
                out.extend((MARKER, MARKER))
                out.extend(target[1:])
            else:
                out.extend(target)
            mtf_update(table, target, limit)
        else:
            out.extend(target)
        pos = end
    return bytes(out)


def mtf_decode_pass(data: bytes, spec: AnchorSpec, limit: int) -> bytes:
    out = bytearray()
    table: list[bytes] = []
    pos = 0
    delimiters = spec.delimiter_set
    while True:
        anchor_pos = data.find(spec.anchor, pos)
        if anchor_pos < 0:
            out.extend(data[pos:])
            break
        target_pos = anchor_pos + len(spec.anchor)
        out.extend(data[pos:target_pos])
        try:
            target, delimiter_pos, _ = literal_or_reference_decode(
                data, target_pos, delimiters, table
            )
        except ValueError:
            out.extend(data[target_pos:])
            break
        delimiter = data[delimiter_pos]
        eligible = not spec.required_set or delimiter in spec.required_set
        out.extend(target)
        if eligible and target:
            mtf_update(table, target, limit)
        pos = delimiter_pos
    return bytes(out)


def wiki_graph_mtf_encode(data: bytes, limit: int) -> bytes:
    transformed = data
    for spec in GRAPH_SPECS:
        transformed = mtf_encode_pass(transformed, spec, limit)
    return transformed


def wiki_graph_mtf_decode(data: bytes, limit: int) -> bytes:
    transformed = data
    for spec in reversed(GRAPH_SPECS):
        transformed = mtf_decode_pass(transformed, spec, limit)
    return transformed


ATOM_RE = re.compile(rb"[A-Za-z][A-Za-z0-9_:/.-]{3,31}")
STRUCT_RE = re.compile(
    rb"(?:</?[A-Za-z][A-Za-z0-9:_-]{1,24}>|"
    rb"(?:\{\{|\[\[|\|)[A-Za-z][A-Za-z0-9 _:/.-]{2,31}=?)"
)


def derive_phrases(data: bytes, max_phrases: int = 127) -> tuple[bytes, ...]:
    counts: Counter[bytes] = Counter()
    atoms = list(ATOM_RE.finditer(data))
    for match in atoms:
        counts[match.group()] += 1
    for match in STRUCT_RE.finditer(data):
        counts[match.group()] += 1
    for index, first in enumerate(atoms):
        for width in (2, 3):
            last_index = index + width - 1
            if last_index >= len(atoms):
                continue
            last = atoms[last_index]
            span = data[first.start() : last.end()]
            if len(span) <= 64 and last.end() - first.end() <= 48:
                counts[span] += 1
    ranked = []
    for phrase, count in counts.items():
        if count < 2 or not (4 <= len(phrase) <= 64) or MARKER in phrase:
            continue
        score = (len(phrase) - 2) * (count - 1)
        ranked.append((score, len(phrase), count, phrase))
    ranked.sort(key=lambda row: (-row[0], -row[1], -row[2], row[3]))
    return tuple(row[3] for row in ranked[:max_phrases])


def phrase_buckets(
    phrases: Sequence[bytes],
    *,
    data: bytes | None = None,
    min_occurrences: int = 1,
    min_phrase_length: int = 1,
) -> dict[int, list[tuple[int, bytes]]]:
    buckets: dict[int, list[tuple[int, bytes]]] = defaultdict(list)
    for index, phrase in enumerate(phrases, 1):
        if len(phrase) < min_phrase_length:
            continue
        if data is not None and min_occurrences > 1:
            if data.count(phrase) < min_occurrences:
                continue
        buckets[phrase[0]].append((index, phrase))
    for rows in buckets.values():
        rows.sort(key=lambda row: (-len(row[1]), row[0]))
    return buckets


def phrase_encode_block(
    data: bytes,
    phrases: Sequence[bytes],
    *,
    min_occurrences: int = 1,
    min_phrase_length: int = 1,
) -> bytes:
    buckets = phrase_buckets(
        phrases,
        data=data,
        min_occurrences=min_occurrences,
        min_phrase_length=min_phrase_length,
    )
    out = bytearray()
    pos = 0
    while pos < len(data):
        match: tuple[int, bytes] | None = None
        for row in buckets.get(data[pos], ()):
            if data.startswith(row[1], pos):
                match = row
                break
        if match is not None:
            out.extend((MARKER, match[0]))
            pos += len(match[1])
        elif data[pos] == MARKER:
            out.extend((MARKER, MARKER))
            pos += 1
        else:
            out.append(data[pos])
            pos += 1
    return bytes(out)


def phrase_decode_block(
    data: bytes,
    pos: int,
    phrases: Sequence[bytes],
    decoded_size: int,
) -> tuple[bytes, int]:
    out = bytearray()
    while pos < len(data) and len(out) < decoded_size:
        byte = data[pos]
        pos += 1
        if byte != MARKER:
            out.append(byte)
            continue
        if pos >= len(data):
            raise ValueError("truncated phrase marker")
        code = data[pos]
        pos += 1
        if code == MARKER:
            out.append(MARKER)
        elif code <= len(phrases):
            phrase = phrases[code - 1]
            if len(out) + len(phrase) > decoded_size:
                raise ValueError("phrase crosses a block boundary")
            out.extend(phrase)
        else:
            raise ValueError(f"invalid phrase code {code}")
    return bytes(out), pos


def rolling_phrase_encode(data: bytes, block_size: int) -> bytes:
    out = bytearray()
    previous = b""
    for start in range(0, len(data), block_size):
        block = data[start : start + block_size]
        phrases = derive_phrases(previous) if previous else ()
        out.extend(phrase_encode_block(block, phrases))
        previous = block
    return bytes(out)


def rolling_phrase_decode(data: bytes, block_size: int) -> bytes:
    out = bytearray()
    pos = 0
    previous = b""
    while pos < len(data):
        phrases = derive_phrases(previous) if previous else ()
        block, pos = phrase_decode_block(data, pos, phrases, block_size)
        if not block:
            raise ValueError("empty rolling phrase block")
        out.extend(block)
        previous = block
        if len(block) < block_size and pos != len(data):
            raise ValueError("short rolling phrase block before end of stream")
    return bytes(out)


TITLE_WORD_RE = re.compile(rb"[A-Za-z0-9][A-Za-z0-9_'-]{3,31}")


def title_alias_roots(title: bytes) -> set[bytes]:
    roots = {title}
    without_parenthetical = re.sub(rb"\s*\([^()]*\)\s*$", b"", title).strip()
    if without_parenthetical:
        roots.add(without_parenthetical)
    if b"," in title:
        roots.add(title.split(b",", 1)[0].strip())
    if b":" in title:
        roots.add(title.split(b":", 1)[1].strip())
    return {root for root in roots if root}


def phrase_case_variants(phrase: bytes) -> set[bytes]:
    variants = {phrase, phrase.replace(b"_", b" ")}
    for value in tuple(variants):
        variants.add(value.lower())
        variants.add(value.upper())
        if value:
            variants.add(value[:1].lower() + value[1:])
            variants.add(value[:1].upper() + value[1:])
    return variants


def title_phrases(title: bytes, mode: str = "exact") -> tuple[bytes, ...]:
    phrases: set[bytes] = set()
    roots = title_alias_roots(title) if mode == "aliases" else {title}
    for root in roots:
        if 4 <= len(root) <= 127 and MARKER not in root:
            phrases.add(root)
        words = list(TITLE_WORD_RE.finditer(root))
        if mode != "multiword":
            for match in words:
                phrases.add(match.group())
        for index, first in enumerate(words):
            for width in (2, 3):
                last_index = index + width - 1
                if last_index < len(words):
                    phrase = root[first.start() : words[last_index].end()]
                    if len(phrase) <= 127 and MARKER not in phrase:
                        phrases.add(phrase)
    if mode == "aliases":
        expanded: set[bytes] = set()
        for phrase in phrases:
            expanded.update(phrase_case_variants(phrase))
        phrases = expanded
    phrases = {
        phrase
        for phrase in phrases
        if 4 <= len(phrase) <= 127 and MARKER not in phrase
    }
    return tuple(sorted(phrases, key=lambda value: (-len(value), value))[:127])


def title_echo_encode(
    data: bytes,
    *,
    mode: str = "exact",
    min_occurrences: int = 1,
    min_phrase_length: int = 1,
    title_source: str = "current",
) -> bytes:
    out = bytearray()
    pos = 0
    previous_title = b""
    while True:
        page_start = data.find(b"<page>", pos)
        if page_start < 0:
            out.extend(data[pos:])
            break
        page_end = data.find(b"</page>", page_start)
        if page_end < 0:
            out.extend(data[pos:])
            break
        title_start = data.find(b"<title>", page_start, page_end)
        title_end = data.find(b"</title>", title_start, page_end) if title_start >= 0 else -1
        if title_start < 0 or title_end < 0:
            out.extend(data[pos : page_end + len(b"</page>")])
            pos = page_end + len(b"</page>")
            continue
        body_start = title_end + len(b"</title>")
        title = data[title_start + len(b"<title>") : title_end]
        phrase_title = title if title_source == "current" else previous_title
        phrases = title_phrases(phrase_title, mode) if phrase_title else ()
        out.extend(data[pos:body_start])
        out.extend(
            phrase_encode_block(
                data[body_start:page_end],
                phrases,
                min_occurrences=min_occurrences,
                min_phrase_length=min_phrase_length,
            )
        )
        out.extend(b"</page>")
        previous_title = title
        pos = page_end + len(b"</page>")
    return bytes(out)


def title_echo_decode(
    data: bytes,
    *,
    mode: str = "exact",
    title_source: str = "current",
) -> bytes:
    out = bytearray()
    pos = 0
    previous_title = b""
    while True:
        page_start = data.find(b"<page>", pos)
        if page_start < 0:
            out.extend(data[pos:])
            break
        page_end = data.find(b"</page>", page_start)
        if page_end < 0:
            out.extend(data[pos:])
            break
        title_start = data.find(b"<title>", page_start, page_end)
        title_end = data.find(b"</title>", title_start, page_end) if title_start >= 0 else -1
        if title_start < 0 or title_end < 0:
            out.extend(data[pos : page_end + len(b"</page>")])
            pos = page_end + len(b"</page>")
            continue
        body_start = title_end + len(b"</title>")
        title = data[title_start + len(b"<title>") : title_end]
        phrase_title = title if title_source == "current" else previous_title
        phrases = title_phrases(phrase_title, mode) if phrase_title else ()
        encoded_body = data[body_start:page_end]
        body, consumed = phrase_decode_block(encoded_body, 0, phrases, 1 << 62)
        if consumed != len(encoded_body):
            raise ValueError("title echo page body was not fully consumed")
        out.extend(data[pos:body_start])
        out.extend(body)
        out.extend(b"</page>")
        previous_title = title
        pos = page_end + len(b"</page>")
    return bytes(out)


def xml_id_delta_encode(data: bytes) -> bytes:
    out = bytearray()
    previous: dict[int, int] = {}
    slot = 0
    pos = 0
    while pos < len(data):
        page_pos = data.find(b"<page>", pos)
        id_pos = data.find(b"<id>", pos)
        choices = [value for value in (page_pos, id_pos) if value >= 0]
        if not choices:
            out.extend(data[pos:])
            break
        event = min(choices)
        out.extend(data[pos:event])
        if event == page_pos:
            out.extend(b"<page>")
            previous.clear()
            slot = 0
            pos = event + len(b"<page>")
            continue
        close = data.find(b"</id>", event + len(b"<id>"))
        if close < 0:
            out.extend(data[event:])
            break
        body_start = event + len(b"<id>")
        body = data[body_start:close]
        out.extend(b"<id>")
        canonical = body.isdigit() and (body == b"0" or not body.startswith(b"0"))
        if canonical:
            value = int(body)
            delta = value - previous.get(slot, 0)
            out.append(MARKER)
            out.extend(uvarint(zigzag_encode(delta) + 1))
            previous[slot] = value
        elif body.startswith(b"\0"):
            out.extend(b"\0\0")
            out.extend(body[1:])
        else:
            out.extend(body)
        out.extend(b"</id>")
        slot += 1
        pos = close + len(b"</id>")
    return bytes(out)


def xml_id_delta_decode(data: bytes) -> bytes:
    out = bytearray()
    previous: dict[int, int] = {}
    slot = 0
    pos = 0
    while pos < len(data):
        page_pos = data.find(b"<page>", pos)
        id_pos = data.find(b"<id>", pos)
        choices = [value for value in (page_pos, id_pos) if value >= 0]
        if not choices:
            out.extend(data[pos:])
            break
        event = min(choices)
        out.extend(data[pos:event])
        if event == page_pos:
            out.extend(b"<page>")
            previous.clear()
            slot = 0
            pos = event + len(b"<page>")
            continue
        body_start = event + len(b"<id>")
        close = data.find(b"</id>", body_start)
        if close < 0:
            out.extend(data[event:])
            break
        out.extend(b"<id>")
        if body_start < len(data) and data[body_start] == MARKER:
            if body_start + 1 < len(data) and data[body_start + 1] == MARKER:
                out.append(MARKER)
                out.extend(data[body_start + 2 : close])
            else:
                encoded, end = read_uvarint(data, body_start + 1)
                if end != close or encoded == 0:
                    raise ValueError("invalid XML ID delta")
                value = previous.get(slot, 0) + zigzag_decode(encoded - 1)
                if value < 0:
                    raise ValueError("negative reconstructed XML ID")
                out.extend(str(value).encode("ascii"))
                previous[slot] = value
        else:
            out.extend(data[body_start:close])
            if data[body_start:close].isdigit():
                previous[slot] = int(data[body_start:close])
        out.extend(b"</id>")
        slot += 1
        pos = close + len(b"</id>")
    return bytes(out)


CASE_MASK_HEADER = struct.Struct("<4sQ")
CASE_POSITION_HEADER = struct.Struct("<4sQ")


def casefold_mask_encode(data: bytes) -> bytes:
    lower = bytearray(data)
    letter_index = 0
    mask = bytearray()
    for index, byte in enumerate(data):
        is_letter = 65 <= byte <= 90 or 97 <= byte <= 122
        if not is_letter:
            continue
        if letter_index % 8 == 0:
            mask.append(0)
        if 65 <= byte <= 90:
            mask[letter_index >> 3] |= 1 << (letter_index & 7)
            lower[index] = byte + 32
        letter_index += 1
    return CASE_MASK_HEADER.pack(b"CFM1", len(mask)) + bytes(mask) + bytes(lower)


def casefold_mask_decode(data: bytes) -> bytes:
    if len(data) < CASE_MASK_HEADER.size:
        raise ValueError("truncated casefold mask header")
    magic, mask_len = CASE_MASK_HEADER.unpack(data[: CASE_MASK_HEADER.size])
    if magic != b"CFM1":
        raise ValueError("bad casefold mask magic")
    mask = data[CASE_MASK_HEADER.size : CASE_MASK_HEADER.size + mask_len]
    lower = bytearray(data[CASE_MASK_HEADER.size + mask_len :])
    letter_index = 0
    for index, byte in enumerate(lower):
        if 97 <= byte <= 122:
            if letter_index >> 3 >= len(mask):
                raise ValueError("truncated casefold mask")
            if mask[letter_index >> 3] & (1 << (letter_index & 7)):
                lower[index] = byte - 32
            letter_index += 1
        elif 65 <= byte <= 90:
            raise ValueError("uppercase byte in casefold lowercase plane")
    if (letter_index + 7) // 8 != len(mask):
        raise ValueError("unused casefold mask bytes")
    return bytes(lower)


def casefold_positions_encode(data: bytes) -> bytes:
    lower = bytearray(data)
    positions = bytearray()
    previous = -1
    count = 0
    for index, byte in enumerate(data):
        if 65 <= byte <= 90:
            positions.extend(uvarint(index - previous))
            previous = index
            lower[index] = byte + 32
            count += 1
    return (
        CASE_POSITION_HEADER.pack(b"CFP1", len(positions))
        + bytes(positions)
        + bytes(lower)
    )


def casefold_positions_decode(data: bytes) -> bytes:
    if len(data) < CASE_POSITION_HEADER.size:
        raise ValueError("truncated casefold position header")
    magic, positions_len = CASE_POSITION_HEADER.unpack(
        data[: CASE_POSITION_HEADER.size]
    )
    if magic != b"CFP1":
        raise ValueError("bad casefold position magic")
    positions = data[
        CASE_POSITION_HEADER.size : CASE_POSITION_HEADER.size + positions_len
    ]
    lower = bytearray(data[CASE_POSITION_HEADER.size + positions_len :])
    pos = 0
    previous = -1
    while pos < len(positions):
        delta, pos = read_uvarint(positions, pos)
        index = previous + delta
        if index < 0 or index >= len(lower) or not 97 <= lower[index] <= 122:
            raise ValueError("invalid casefold uppercase position")
        lower[index] -= 32
        previous = index
    return bytes(lower)


@dataclass(frozen=True)
class Transform:
    name: str
    family: str
    encode: Callable[[bytes], bytes]
    decode: Callable[[bytes], bytes]
    decoder_payload: str
    role: str = "candidate"


def transform_registry() -> dict[str, Transform]:
    transforms = [
        Transform(
            "identity",
            "control",
            lambda data: data,
            lambda data: data,
            "none",
            "control",
        ),
        Transform(
            "wiki_graph_mtf64",
            "wiki_graph_mtf",
            lambda data: wiki_graph_mtf_encode(data, 64),
            lambda data: wiki_graph_mtf_decode(data, 64),
            "zero table bytes; 64-entry decoder-built tables",
        ),
        Transform(
            "wiki_graph_mtf256",
            "wiki_graph_mtf",
            lambda data: wiki_graph_mtf_encode(data, 256),
            lambda data: wiki_graph_mtf_decode(data, 256),
            "zero table bytes; 256-entry decoder-built tables",
        ),
        Transform(
            "wiki_graph_mtf1024",
            "wiki_graph_mtf",
            lambda data: wiki_graph_mtf_encode(data, 1024),
            lambda data: wiki_graph_mtf_decode(data, 1024),
            "zero table bytes; 1024-entry decoder-built tables",
        ),
        Transform(
            "rolling_phrase32k",
            "rolling_phrase",
            lambda data: rolling_phrase_encode(data, 32_768),
            lambda data: rolling_phrase_decode(data, 32_768),
            "zero table bytes; phrases rebuilt from preceding 32KiB",
        ),
        Transform(
            "rolling_phrase64k",
            "rolling_phrase",
            lambda data: rolling_phrase_encode(data, 65_536),
            lambda data: rolling_phrase_decode(data, 65_536),
            "zero table bytes; phrases rebuilt from preceding 64KiB",
        ),
        Transform(
            "rolling_phrase128k",
            "rolling_phrase",
            lambda data: rolling_phrase_encode(data, 131_072),
            lambda data: rolling_phrase_decode(data, 131_072),
            "zero table bytes; phrases rebuilt from preceding 128KiB",
        ),
        Transform(
            "title_echo",
            "title_echo",
            title_echo_encode,
            title_echo_decode,
            "zero table bytes; phrase table rebuilt from each decoded title",
        ),
        Transform(
            "title_echo_previous_control",
            "title_echo_control",
            lambda data: title_echo_encode(data, title_source="previous"),
            lambda data: title_echo_decode(data, title_source="previous"),
            "matched mechanics; phrase table rebuilt from the previous page title",
            "matched_control",
        ),
        Transform(
            "title_echo_multiword",
            "title_echo",
            lambda data: title_echo_encode(data, mode="multiword"),
            lambda data: title_echo_decode(data, mode="multiword"),
            "zero table bytes; full-title and multiword phrases only",
        ),
        Transform(
            "title_echo_selective",
            "title_echo",
            lambda data: title_echo_encode(
                data, min_occurrences=2, min_phrase_length=6
            ),
            title_echo_decode,
            "zero table bytes; exact title phrases used only after two page-local hits",
        ),
        Transform(
            "title_echo_aliases",
            "title_echo",
            lambda data: title_echo_encode(data, mode="aliases"),
            lambda data: title_echo_decode(data, mode="aliases"),
            "zero table bytes; title-derived aliases and ASCII case variants",
        ),
        Transform(
            "title_echo_aliases_selective",
            "title_echo",
            lambda data: title_echo_encode(
                data,
                mode="aliases",
                min_occurrences=2,
                min_phrase_length=6,
            ),
            lambda data: title_echo_decode(data, mode="aliases"),
            "zero table bytes; repeated title aliases and case variants only",
        ),
        Transform(
            "xml_id_delta",
            "xml_id_delta",
            xml_id_delta_encode,
            xml_id_delta_decode,
            "zero table bytes; prior IDs rebuilt per page and ordinal",
        ),
        Transform(
            "casefold_mask",
            "casefold",
            casefold_mask_encode,
            casefold_mask_decode,
            "zero table bytes; one compressed case bit per ASCII letter",
        ),
        Transform(
            "casefold_positions",
            "casefold",
            casefold_positions_encode,
            casefold_positions_decode,
            "zero table bytes; delta-coded uppercase positions",
        ),
    ]
    return {transform.name: transform for transform in transforms}


@dataclass(frozen=True)
class Backend:
    name: str
    compress: Callable[[bytes], bytes]
    decompress: Callable[[bytes], bytes]


def backends() -> tuple[Backend, ...]:
    return (
        Backend(
            "bz2_9",
            lambda data: bz2.compress(data, compresslevel=9),
            bz2.decompress,
        ),
        Backend(
            "lzma_6",
            lambda data: lzma.compress(data, preset=6),
            lzma.decompress,
        ),
    )


def stable_seed(seed: int, phase: str, window_size: int) -> int:
    digest = hashlib.sha256(f"{seed}\0{phase}\0{window_size}".encode()).digest()
    return int.from_bytes(digest[:8], "little")


def sample_offsets(
    corpus_size: int,
    window_size: int,
    count: int,
    seed: int,
    phase: str,
) -> list[int]:
    if window_size <= 0 or window_size > corpus_size:
        raise ValueError("window size must be within the corpus")
    if count <= 0:
        raise ValueError("window count must be positive")
    rng = random.Random(stable_seed(seed, phase, window_size))
    available = corpus_size - window_size
    offsets = []
    for index in range(count):
        lo = (available * index) // count
        hi = (available * (index + 1)) // count
        offsets.append(rng.randint(lo, max(lo, hi)))
    return offsets


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate(
    raw: bytes,
    transform: Transform,
    backend: Backend,
) -> dict[str, object]:
    t0 = time.perf_counter()
    encoded = transform.encode(raw)
    transform_time = time.perf_counter() - t0
    roundtrip = transform.decode(encoded)
    transform_roundtrip_ok = roundtrip == raw
    encoded_second = transform.encode(raw)
    transform_deterministic = encoded_second == encoded

    t1 = time.perf_counter()
    archive = backend.compress(encoded)
    compress_time = time.perf_counter() - t1
    encoded_restored = backend.decompress(archive)
    full_roundtrip_ok = transform.decode(encoded_restored) == raw
    archive_second = backend.compress(encoded_second)
    archive_deterministic = archive_second == archive
    return {
        "transformed_bytes": len(encoded),
        "transformed_delta_bytes": len(encoded) - len(raw),
        "archive_bytes": len(archive),
        "archive_sha256": hashlib.sha256(archive).hexdigest(),
        "transform_roundtrip_ok": transform_roundtrip_ok,
        "full_roundtrip_ok": full_roundtrip_ok,
        "transform_deterministic": transform_deterministic,
        "archive_deterministic": archive_deterministic,
        "transform_time_s": round(transform_time, 6),
        "compress_time_s": round(compress_time, 6),
    }


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, int], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        if row["algorithm"] == "identity":
            continue
        grouped[(str(row["algorithm"]), str(row["backend"]), int(row["window_size"]))].append(row)

    summaries = []
    for (algorithm, backend, window_size), group in sorted(grouped.items()):
        total_input = sum(int(row["window_size"]) for row in group)
        total_delta = sum(int(row["archive_delta_vs_identity"]) for row in group)
        gross_gain_per_million = -total_delta * 1_000_000 / total_input
        deltas = [int(row["archive_delta_vs_identity"]) for row in group]
        summaries.append(
            {
                "algorithm": algorithm,
                "family": group[0]["family"],
                "role": group[0]["role"],
                "backend": backend,
                "window_size": window_size,
                "windows": len(group),
                "total_input_bytes": total_input,
                "total_archive_delta_vs_identity": total_delta,
                "gross_gain_bytes_per_million": round(gross_gain_per_million, 6),
                "wins": sum(delta < 0 for delta in deltas),
                "ties": sum(delta == 0 for delta in deltas),
                "regressions": sum(delta > 0 for delta in deltas),
                "best_window_delta": min(deltas),
                "worst_window_delta": max(deltas),
                "all_roundtrip_ok": all(bool(row["full_roundtrip_ok"]) for row in group),
                "all_deterministic": all(bool(row["archive_deterministic"]) for row in group),
            }
        )
    return summaries


def family_decisions(
    summaries: list[dict[str, object]], phase: str
) -> list[dict[str, object]]:
    by_algorithm: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in summaries:
        by_algorithm[str(row["algorithm"])].append(row)
    decisions = []
    for algorithm, rows in sorted(by_algorithm.items()):
        gains = [float(row["gross_gain_bytes_per_million"]) for row in rows]
        role = str(rows[0]["role"])
        eligible = (
            role == "candidate"
            and
            min(gains) >= TARGET_GROSS_GAIN_PER_MILLION
            and all(bool(row["all_roundtrip_ok"]) for row in rows)
            and all(bool(row["all_deterministic"]) for row in rows)
        )
        if role != "candidate":
            verdict = "control_only"
        elif eligible and phase == "selection":
            verdict = "confirmation_earned"
        elif eligible:
            verdict = "exact_fx2_trace_earned"
        else:
            verdict = "proxy_only_or_retire"
        decisions.append(
            {
                "algorithm": algorithm,
                "family": rows[0]["family"],
                "role": role,
                "minimum_backend_scope_gain_bytes_per_million": round(min(gains), 6),
                "mean_backend_scope_gain_bytes_per_million": round(sum(gains) / len(gains), 6),
                "proxy_fx2_trace_eligible": eligible,
                "verdict": verdict,
            }
        )
    decisions.sort(
        key=lambda row: (
            -float(row["minimum_backend_scope_gain_bytes_per_million"]),
            str(row["algorithm"]),
        )
    )
    return decisions


def render_markdown(receipt: dict[str, object]) -> str:
    lines = [
        "# Random-Window Novelty Screen",
        "",
        f"- Phase: `{receipt['phase']}`",
        f"- Corpus bytes: `{receipt['corpus_bytes']}`",
        f"- Corpus SHA-256: `{receipt['corpus_sha256']}`",
        f"- Window sizes: `{', '.join(str(v) for v in receipt['window_sizes'])}`",
        f"- Windows per size: `{receipt['windows_per_size']}`",
        f"- Evidence: `{receipt['evidence_level']}`",
        "- Claim boundary: proxy gains do not change the enwik9 score forecast or prove 10.95%.",
        "- Promotion boundary: a qualifying row earns an exact FX2 residual/component trace with counted code; it does not earn a native gate.",
        "",
        "## Ranked Decisions",
        "",
        "| Algorithm | Role | Family | Minimum gain B/1M | Mean gain B/1M | Decision |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in receipt["decisions"]:
        lines.append(
            f"| `{row['algorithm']}` | `{row['role']}` | `{row['family']}` | "
            f"{row['minimum_backend_scope_gain_bytes_per_million']:.3f} | "
            f"{row['mean_backend_scope_gain_bytes_per_million']:.3f} | "
            f"`{row['verdict']}` |"
        )
    lines.extend(
        [
            "",
            "## Scope Summaries",
            "",
            "| Algorithm | Backend | Scope | Windows | Delta bytes | Gain B/1M | W/T/R | Worst regression |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in receipt["summaries"]:
        lines.append(
            f"| `{row['algorithm']}` | `{row['backend']}` | {row['window_size']:,} | "
            f"{row['windows']} | {row['total_archive_delta_vs_identity']:+d} | "
            f"{row['gross_gain_bytes_per_million']:.3f} | "
            f"{row['wins']}/{row['ties']}/{row['regressions']} | "
            f"{row['worst_window_delta']:+d} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Negative archive deltas and positive gain rates are improvements over raw input under the same backend. The algorithm source/package cost is not counted in this proxy receipt. Backend disagreement, window regressions, or failure to clear 700 gross bytes per million at every tested scope prevents promotion.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_csv_ints(value: str) -> list[int]:
    result = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not result or any(item <= 0 for item in result):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return result


def parse_names(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def run(args: argparse.Namespace) -> dict[str, object]:
    registry = transform_registry()
    requested = args.algorithms or list(registry)
    unknown = sorted(set(requested) - set(registry))
    if unknown:
        raise SystemExit(f"unknown algorithms: {', '.join(unknown)}")
    if "identity" not in requested:
        requested.insert(0, "identity")

    corpus_size = args.data.stat().st_size
    rows: list[dict[str, object]] = []
    windows: list[dict[str, object]] = []
    with args.data.open("rb") as corpus:
        for window_size in args.window_sizes:
            offsets = sample_offsets(
                corpus_size,
                window_size,
                args.windows_per_size,
                args.seed,
                args.phase,
            )
            for window_index, offset in enumerate(offsets):
                corpus.seek(offset)
                raw = corpus.read(window_size)
                if len(raw) != window_size:
                    raise SystemExit("short corpus read")
                window_id = f"{args.phase}-{window_size}-{window_index}"
                windows.append(
                    {
                        "window_id": window_id,
                        "window_size": window_size,
                        "offset": offset,
                        "sha256": hashlib.sha256(raw).hexdigest(),
                    }
                )
                baseline_by_backend: dict[str, int] = {}
                for name in requested:
                    transform = registry[name]
                    for backend in backends():
                        result = evaluate(raw, transform, backend)
                        if name == "identity":
                            baseline_by_backend[backend.name] = int(result["archive_bytes"])
                        baseline = baseline_by_backend.get(backend.name)
                        if baseline is None:
                            raise AssertionError("identity must run before candidates")
                        result.update(
                            {
                                "window_id": window_id,
                                "window_size": window_size,
                                "offset": offset,
                                "algorithm": name,
                                "family": transform.family,
                                "role": transform.role,
                                "backend": backend.name,
                                "decoder_payload": transform.decoder_payload,
                                "identity_archive_bytes": baseline,
                                "archive_delta_vs_identity": int(result["archive_bytes"]) - baseline,
                            }
                        )
                        rows.append(result)

    summaries = summarize(rows)
    receipt: dict[str, object] = {
        "schema_version": 1,
        "mode": "random_window_novel_algorithm_proxy",
        "phase": args.phase,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "evidence_level": "level_1_proxy_reversible_transform",
        "claim_boundary": "No proxy row changes the forecast or proves 10.95%.",
        "promotion_boundary": "A robust proxy row only earns an exact FX2 residual/component trace with complete code and state accounting.",
        "target_gross_gain_bytes_per_million": TARGET_GROSS_GAIN_PER_MILLION,
        "algorithm_source_cost_counted": False,
        "data_path": str(args.data),
        "corpus_bytes": corpus_size,
        "corpus_sha256": hash_file(args.data),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seed": args.seed,
        "window_sizes": args.window_sizes,
        "windows_per_size": args.windows_per_size,
        "algorithms": requested,
        "backends": [backend.name for backend in backends()],
        "windows": windows,
        "rows": rows,
        "summaries": summaries,
        "decisions": family_decisions(summaries, args.phase),
    }
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--phase", choices=("selection", "confirmation"), required=True)
    parser.add_argument("--window-sizes", type=parse_csv_ints, default=[500_000, 1_000_000])
    parser.add_argument("--windows-per-size", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0xE9_500_1000)
    parser.add_argument("--algorithms", type=parse_names)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args(argv)
    if args.windows_per_size <= 0:
        raise SystemExit("--windows-per-size must be positive")
    if not args.data.exists():
        raise SystemExit(f"missing corpus: {args.data}")
    out_dir = DEFAULT_OUT
    json_out = args.json_out or out_dir / f"{args.phase}.json"
    md_out = args.md_out or out_dir / f"{args.phase}.md"
    receipt = run(args)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    md_out.write_text(render_markdown(receipt))
    print(f"wrote {json_out}")
    print(f"wrote {md_out}")
    for row in receipt["decisions"]:
        print(
            f"{row['algorithm']} min_gain_B_per_1M="
            f"{row['minimum_backend_scope_gain_bytes_per_million']:.3f} "
            f"verdict={row['verdict']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
