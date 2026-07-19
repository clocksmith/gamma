#!/usr/bin/env python3
"""Screen exact decoder-built interning of repeated named references."""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import lzma
from pathlib import Path
import random
import re
from typing import Any

if __package__:
    from .wikiir_citation_field_columnar_probe import decode_varint, encode_varint
else:
    from wikiir_citation_field_columnar_probe import decode_varint, encode_varint


MAGIC = b"NRI1"
PLACEHOLDER = b"\x00"
REF_OPEN_RE = re.compile(br"(?:<|&lt;)ref\b", re.IGNORECASE)
NAME_RE = re.compile(
    br"\bname\s*=\s*(?:(?P<q>[\"'])(?P<quoted>.*?)(?P=q)|(?P<bare>[^\s>/]+))",
    re.IGNORECASE | re.DOTALL,
)


def named_ref_spans(data: bytes) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for match in REF_OPEN_RE.finditer(data):
        cursor = match.end()
        quote: int | None = None
        escaped = data[match.start() : match.start() + 4].lower() == b"&lt;"
        while cursor < len(data):
            byte = data[cursor]
            if quote is None and byte in (0x22, 0x27):
                quote = byte
            elif quote is not None and byte == quote:
                quote = None
            elif quote is None:
                if not escaped and byte == 0x3E:
                    break
                if escaped and data[cursor : cursor + 4].lower() == b"&gt;":
                    cursor += 3
                    break
            cursor += 1
        if cursor >= len(data):
            continue
        tag = data[match.start() : cursor + 1]
        name = NAME_RE.search(tag)
        if name is None:
            continue
        group = "quoted" if name.group("quoted") is not None else "bare"
        start, end = name.span(group)
        spans.append((match.start() + start, match.start() + end))
    return spans


def skeleton_and_values(data: bytes) -> tuple[bytes, list[bytes]]:
    output = bytearray()
    values: list[bytes] = []
    cursor = 0
    for start, end in named_ref_spans(data):
        if start < cursor:
            raise ValueError("overlapping reference names")
        output.extend(data[cursor:start])
        output.extend(PLACEHOLDER)
        values.append(data[start:end])
        cursor = end
    output.extend(data[cursor:])
    return bytes(output), values


def encode_transform(data: bytes, mode: str) -> bytes:
    skeleton, values = skeleton_and_values(data)
    output = bytearray(MAGIC)
    output.append(1 if mode == "intern" else 0)
    output.extend(encode_varint(len(skeleton)))
    output.extend(skeleton)
    output.extend(encode_varint(len(values)))
    dictionary: dict[bytes, int] = {}
    for value in values:
        prior = dictionary.get(value)
        if mode == "intern" and prior is not None:
            output.append(1)
            output.extend(encode_varint(prior))
            continue
        output.append(0)
        output.extend(encode_varint(len(value)))
        output.extend(value)
        if value not in dictionary:
            dictionary[value] = len(dictionary)
    return bytes(output)


def decode_transform(payload: bytes) -> bytes:
    if not payload.startswith(MAGIC) or len(payload) < len(MAGIC) + 1:
        raise ValueError("invalid named-reference payload")
    offset = len(MAGIC)
    mode = "intern" if payload[offset] else "literal"
    offset += 1
    skeleton_size, offset = decode_varint(payload, offset)
    skeleton = payload[offset : offset + skeleton_size]
    if len(skeleton) != skeleton_size:
        raise ValueError("truncated skeleton")
    offset += skeleton_size
    count, offset = decode_varint(payload, offset)
    values: list[bytes] = []
    dictionary: list[bytes] = []
    dictionary_index: dict[bytes, int] = {}
    for _ in range(count):
        if offset >= len(payload):
            raise ValueError("truncated reference opcode")
        opcode = payload[offset]
        offset += 1
        if opcode == 1:
            if mode != "intern":
                raise ValueError("reference opcode invalid in literal mode")
            index, offset = decode_varint(payload, offset)
            if index >= len(dictionary):
                raise ValueError("reference dictionary underflow")
            values.append(dictionary[index])
            continue
        if opcode != 0:
            raise ValueError("invalid reference opcode")
        size, offset = decode_varint(payload, offset)
        value = payload[offset : offset + size]
        if len(value) != size:
            raise ValueError("truncated reference literal")
        offset += size
        values.append(value)
        if value not in dictionary_index:
            dictionary_index[value] = len(dictionary)
            dictionary.append(value)
    if offset != len(payload):
        raise ValueError("trailing reference payload")
    spans = named_ref_spans(skeleton)
    if len(spans) != len(values):
        raise ValueError("reference occurrence count changed")
    output = bytearray()
    cursor = 0
    for (start, end), value in zip(spans, values, strict=True):
        output.extend(skeleton[cursor:start])
        output.extend(value)
        cursor = end
    output.extend(skeleton[cursor:])
    return bytes(output)


def compressed_sizes(data: bytes) -> dict[str, int]:
    return {
        "bz2": len(bz2.compress(data, compresslevel=9)),
        "lzma": len(lzma.compress(data, preset=9)),
    }


def full_corpus_census(corpus: bytes) -> dict[str, int]:
    values = skeleton_and_values(corpus)[1]
    dictionary: dict[bytes, int] = {}
    repeat_count = 0
    repeat_literal_bytes = 0
    maximum_raw_savings = 0
    for value in values:
        prior = dictionary.get(value)
        if prior is None:
            dictionary[value] = len(dictionary)
            continue
        repeat_count += 1
        repeat_literal_bytes += len(value)
        maximum_raw_savings += len(value) - (1 + len(encode_varint(prior)))
    return {
        "named_refs": len(values),
        "unique_names": len(dictionary),
        "repeat_occurrences": repeat_count,
        "repeat_literal_bytes": repeat_literal_bytes,
        "maximum_raw_intern_savings_before_container": maximum_raw_savings,
    }


def window_starts(total: int, size: int, count: int, seed: str) -> list[int]:
    rng = random.Random(int.from_bytes(hashlib.sha256(seed.encode()).digest(), "big"))
    starts: list[int] = []
    while len(starts) < count:
        start = rng.randrange(total - size + 1)
        if all(abs(start - prior) >= size for prior in starts):
            starts.append(start)
    return sorted(starts)


def run(args: argparse.Namespace) -> dict[str, Any]:
    corpus = args.data.read_bytes()
    rows: list[dict[str, Any]] = []
    for size in args.window_sizes:
        for start in window_starts(
            len(corpus), size, args.windows_per_size, f"{args.seed}:{size}"
        ):
            window = corpus[start : start + size]
            raw_sizes = compressed_sizes(window)
            values = skeleton_and_values(window)[1]
            repeats = len(values) - len(set(values))
            for mode in ("literal", "intern"):
                payload = encode_transform(window, mode)
                if decode_transform(payload) != window:
                    raise RuntimeError("named-reference roundtrip failed")
                sizes = compressed_sizes(payload)
                rows.append(
                    {
                        "scope_bytes": size,
                        "start": start,
                        "mode": mode,
                        "reference_names": len(values),
                        "repeated_reference_names": repeats,
                        "payload_bytes": len(payload),
                        "payload_delta_bytes": len(payload) - len(window),
                        "bz2_saved_vs_raw": raw_sizes["bz2"] - sizes["bz2"],
                        "lzma_saved_vs_raw": raw_sizes["lzma"] - sizes["lzma"],
                        "roundtrip_ok": True,
                    }
                )
    aggregates = []
    for size in args.window_sizes:
        group = [row for row in rows if row["scope_bytes"] == size]
        literal = [row for row in group if row["mode"] == "literal"]
        intern = [row for row in group if row["mode"] == "intern"]
        aggregates.append(
            {
                "scope_bytes": size,
                "windows": len(literal),
                "reference_names": sum(row["reference_names"] for row in intern),
                "repeated_reference_names": sum(
                    row["repeated_reference_names"] for row in intern
                ),
                "intern_bz2_saved_vs_raw": sum(
                    row["bz2_saved_vs_raw"] for row in intern
                ),
                "intern_lzma_saved_vs_raw": sum(
                    row["lzma_saved_vs_raw"] for row in intern
                ),
                "intern_bz2_saved_vs_literal_control": sum(
                    candidate["bz2_saved_vs_raw"] - control["bz2_saved_vs_raw"]
                    for candidate, control in zip(intern, literal, strict=True)
                ),
                "intern_lzma_saved_vs_literal_control": sum(
                    candidate["lzma_saved_vs_raw"] - control["lzma_saved_vs_raw"]
                    for candidate, control in zip(intern, literal, strict=True)
                ),
                "positive_lzma_windows_vs_raw": sum(
                    row["lzma_saved_vs_raw"] > 0 for row in intern
                ),
            }
        )
    return {
        "schema": "wikiir_named_ref_intern_probe_v1",
        "evidence_tier": "reversible_proxy",
        "claim_boundary": (
            "Exact reversible BZip2/LZMA random-window proxy only. It does not "
            "establish endpoint428 or official archive gain."
        ),
        "data": {
            "path": str(args.data.resolve()),
            "bytes": len(corpus),
            "sha256": hashlib.sha256(corpus).hexdigest(),
        },
        "seed": args.seed,
        "full_corpus_census": full_corpus_census(corpus),
        "rows": rows,
        "aggregates": aggregates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("projects/enwiki9/data/enwik9"))
    parser.add_argument("--window-sizes", type=int, nargs="+", default=[500_000, 1_000_000])
    parser.add_argument("--windows-per-size", type=int, default=2)
    parser.add_argument("--seed", default="named-ref-selection-v1")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["aggregates"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
