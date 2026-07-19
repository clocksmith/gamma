#!/usr/bin/env python3
"""Screen an exact citation-field columnar transform on random enwik9 windows."""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import lzma
from pathlib import Path
import random
from typing import Any


FIELD_FAMILIES: dict[str, tuple[bytes, ...]] = {
    "dates": (b"date", b"accessdate", b"archivedate", b"year"),
    "urls": (b"url", b"archiveurl", b"doi", b"pmid", b"isbn"),
    "people": (b"author", b"first", b"last", b"authorlink"),
    "titles": (b"title", b"work", b"website", b"journal", b"publisher"),
}
FIELD_FAMILIES["all"] = tuple(
    sorted({field for fields in FIELD_FAMILIES.values() for field in fields})
)
MAGIC = b"CFC1"


def encode_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint value must be nonnegative")
    output = bytearray()
    while value >= 0x80:
        output.append((value & 0x7F) | 0x80)
        value >>= 7
    output.append(value)
    return bytes(output)


def decode_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if offset >= len(data) or shift > 63:
            raise ValueError("invalid varint")
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, offset
        shift += 7


def cite_template_ranges(data: bytes) -> list[tuple[int, int]]:
    lower = data.lower()
    ranges: list[tuple[int, int]] = []
    cursor = 0
    while True:
        start = lower.find(b"{{", cursor)
        if start < 0:
            break
        header_end = len(data)
        for delimiter in (b"|", b"}}", b"\n"):
            found = lower.find(delimiter, start + 2)
            if found >= 0:
                header_end = min(header_end, found)
        name = lower[start + 2 : header_end].strip().replace(b"_", b" ")
        if not (name.startswith(b"cite ") or name in {b"cite", b"citation"}):
            cursor = start + 2
            continue
        depth = 0
        index = start
        end = None
        while index + 1 < len(data):
            pair = data[index : index + 2]
            if pair == b"{{":
                depth += 1
                index += 2
                continue
            if pair == b"}}":
                depth -= 1
                index += 2
                if depth == 0:
                    end = index
                    break
                continue
            index += 1
        if end is None:
            cursor = start + 2
            continue
        ranges.append((start, end))
        cursor = end
    return ranges


def split_top_level_fields(data: bytes, start: int, end: int) -> list[tuple[int, int]]:
    fields: list[tuple[int, int]] = []
    brace_depth = 1
    link_depth = 0
    field_start: int | None = None
    index = start + 2
    stop = end - 2
    while index < stop:
        pair = data[index : index + 2]
        if pair == b"{{":
            brace_depth += 1
            index += 2
            continue
        if pair == b"}}":
            brace_depth -= 1
            index += 2
            continue
        if pair == b"[[":
            link_depth += 1
            index += 2
            continue
        if pair == b"]]" and link_depth:
            link_depth -= 1
            index += 2
            continue
        if data[index] == 0x7C and brace_depth == 1 and link_depth == 0:
            if field_start is not None:
                fields.append((field_start, index))
            field_start = index + 1
        index += 1
    if field_start is not None:
        fields.append((field_start, stop))
    return fields


def first_top_level_equals(data: bytes, start: int, end: int) -> int | None:
    brace_depth = 0
    link_depth = 0
    index = start
    while index < end:
        pair = data[index : index + 2]
        if pair == b"{{":
            brace_depth += 1
            index += 2
            continue
        if pair == b"}}" and brace_depth:
            brace_depth -= 1
            index += 2
            continue
        if pair == b"[[":
            link_depth += 1
            index += 2
            continue
        if pair == b"]]" and link_depth:
            link_depth -= 1
            index += 2
            continue
        if data[index] == 0x3D and brace_depth == 0 and link_depth == 0:
            return index
        index += 1
    return None


def selected_value_spans(
    data: bytes, fields: tuple[bytes, ...]
) -> list[tuple[int, int, bytes]]:
    selected = set(fields)
    spans: list[tuple[int, int, bytes]] = []
    for template_start, template_end in cite_template_ranges(data):
        for field_start, field_end in split_top_level_fields(
            data, template_start, template_end
        ):
            equals = first_top_level_equals(data, field_start, field_end)
            if equals is None:
                continue
            key = data[field_start:equals].strip().lower().replace(b"_", b"")
            if key in selected:
                spans.append((equals + 1, field_end, key))
    return spans


def make_skeleton(
    data: bytes, spans: list[tuple[int, int, bytes]]
) -> tuple[bytes, list[bytes]]:
    output = bytearray()
    values: list[bytes] = []
    cursor = 0
    for start, end, _ in spans:
        if start < cursor:
            raise ValueError("overlapping citation fields")
        output.extend(data[cursor:start])
        values.append(data[start:end])
        cursor = end
    output.extend(data[cursor:])
    return bytes(output), values


def bucket_indexes(
    spans: list[tuple[int, int, bytes]], fields: tuple[bytes, ...], mode: str
) -> list[int]:
    by_field = {field: index for index, field in enumerate(fields)}
    if mode == "semantic":
        return [by_field[key] for _, _, key in spans]
    if mode == "ordinal_control":
        return [index % len(fields) for index in range(len(spans))]
    raise ValueError(f"unknown mode: {mode}")


def encode_transform(data: bytes, family: str, mode: str) -> bytes:
    fields = FIELD_FAMILIES[family]
    spans = selected_value_spans(data, fields)
    skeleton, values = make_skeleton(data, spans)
    indexes = bucket_indexes(spans, fields, mode)
    buckets: list[list[bytes]] = [[] for _ in fields]
    for index, value in zip(indexes, values, strict=True):
        buckets[index].append(value)
    output = bytearray(MAGIC)
    output.append(sorted(FIELD_FAMILIES).index(family))
    output.append(0 if mode == "semantic" else 1)
    output.extend(encode_varint(len(skeleton)))
    output.extend(skeleton)
    for bucket in buckets:
        output.extend(encode_varint(len(bucket)))
        for value in bucket:
            output.extend(encode_varint(len(value)))
            output.extend(value)
    return bytes(output)


def decode_transform(payload: bytes) -> bytes:
    if not payload.startswith(MAGIC) or len(payload) < len(MAGIC) + 2:
        raise ValueError("invalid citation transform")
    offset = len(MAGIC)
    families = sorted(FIELD_FAMILIES)
    family = families[payload[offset]]
    offset += 1
    mode = "semantic" if payload[offset] == 0 else "ordinal_control"
    offset += 1
    skeleton_size, offset = decode_varint(payload, offset)
    skeleton = payload[offset : offset + skeleton_size]
    if len(skeleton) != skeleton_size:
        raise ValueError("truncated skeleton")
    offset += skeleton_size
    fields = FIELD_FAMILIES[family]
    buckets: list[list[bytes]] = []
    for _ in fields:
        count, offset = decode_varint(payload, offset)
        bucket = []
        for _ in range(count):
            size, offset = decode_varint(payload, offset)
            value = payload[offset : offset + size]
            if len(value) != size:
                raise ValueError("truncated citation value")
            offset += size
            bucket.append(value)
        buckets.append(bucket)
    if offset != len(payload):
        raise ValueError("trailing citation payload")
    spans = selected_value_spans(skeleton, fields)
    indexes = bucket_indexes(spans, fields, mode)
    consumed = [0] * len(fields)
    output = bytearray()
    cursor = 0
    for (start, end, _), bucket_index in zip(spans, indexes, strict=True):
        output.extend(skeleton[cursor:start])
        position = consumed[bucket_index]
        if position >= len(buckets[bucket_index]):
            raise ValueError("citation bucket underflow")
        output.extend(buckets[bucket_index][position])
        consumed[bucket_index] += 1
        cursor = end
    output.extend(skeleton[cursor:])
    if any(used != len(bucket) for used, bucket in zip(consumed, buckets, strict=True)):
        raise ValueError("citation bucket overflow")
    return bytes(output)


def compressed_sizes(data: bytes) -> dict[str, int]:
    return {
        "bz2": len(bz2.compress(data, compresslevel=9)),
        "lzma": len(lzma.compress(data, preset=9)),
    }


def window_starts(total: int, size: int, count: int, seed: str) -> list[int]:
    if size > total:
        raise ValueError("window exceeds corpus")
    rng = random.Random(int.from_bytes(hashlib.sha256(seed.encode()).digest(), "big"))
    starts: list[int] = []
    while len(starts) < count:
        start = rng.randrange(0, total - size + 1)
        if all(abs(start - prior) >= size for prior in starts):
            starts.append(start)
    return sorted(starts)


def run(args: argparse.Namespace) -> dict[str, Any]:
    corpus = args.data.read_bytes()
    rows: list[dict[str, Any]] = []
    for size in args.window_sizes:
        starts = window_starts(
            len(corpus), size, args.windows_per_size, f"{args.seed}:{size}"
        )
        for start in starts:
            window = corpus[start : start + size]
            baseline = compressed_sizes(window)
            for family in sorted(FIELD_FAMILIES):
                fields = FIELD_FAMILIES[family]
                span_count = len(selected_value_spans(window, fields))
                for mode in ("semantic", "ordinal_control"):
                    payload = encode_transform(window, family, mode)
                    restored = decode_transform(payload)
                    if restored != window:
                        raise RuntimeError("citation transform roundtrip failed")
                    sizes = compressed_sizes(payload)
                    rows.append(
                        {
                            "scope_bytes": size,
                            "start": start,
                            "family": family,
                            "mode": mode,
                            "field_occurrences": span_count,
                            "payload_bytes": len(payload),
                            "payload_delta_bytes": len(payload) - len(window),
                            "bz2_bytes": sizes["bz2"],
                            "bz2_saved_bytes": baseline["bz2"] - sizes["bz2"],
                            "lzma_bytes": sizes["lzma"],
                            "lzma_saved_bytes": baseline["lzma"] - sizes["lzma"],
                            "roundtrip_ok": True,
                        }
                    )
    aggregates: list[dict[str, Any]] = []
    keys = sorted({(row["scope_bytes"], row["family"], row["mode"]) for row in rows})
    for size, family, mode in keys:
        group = [
            row
            for row in rows
            if (row["scope_bytes"], row["family"], row["mode"])
            == (size, family, mode)
        ]
        aggregates.append(
            {
                "scope_bytes": size,
                "family": family,
                "mode": mode,
                "windows": len(group),
                "field_occurrences": sum(row["field_occurrences"] for row in group),
                "bz2_saved_bytes": sum(row["bz2_saved_bytes"] for row in group),
                "lzma_saved_bytes": sum(row["lzma_saved_bytes"] for row in group),
                "positive_bz2_windows": sum(row["bz2_saved_bytes"] > 0 for row in group),
                "positive_lzma_windows": sum(row["lzma_saved_bytes"] > 0 for row in group),
            }
        )
    return {
        "schema": "wikiir_citation_field_columnar_probe_v1",
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
        "window_sizes": args.window_sizes,
        "windows_per_size": args.windows_per_size,
        "rows": rows,
        "aggregates": aggregates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("projects/enwiki9/data/enwik9"))
    parser.add_argument("--window-sizes", type=int, nargs="+", default=[500_000, 1_000_000])
    parser.add_argument("--windows-per-size", type=int, default=2)
    parser.add_argument("--seed", default="citation-selection-v1")
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
