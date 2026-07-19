#!/usr/bin/env python3
"""Screen exact causal COPY/ADD deltas between prior Wikipedia references."""

from __future__ import annotations

import argparse
import bz2
from collections import defaultdict
import difflib
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


MAGIC = b"RFD1"
INLINE_MAGIC = b"RFI1"
OPEN = b"&lt;ref"
TAG_END = b"&gt;"
CLOSE = b"&lt;/ref&gt;"
PLACEHOLDER = b"\x00"


def reference_body_spans(data: bytes) -> list[tuple[int, int]]:
    lower = data.lower()
    spans: list[tuple[int, int]] = []
    cursor = 0
    while True:
        start = lower.find(OPEN, cursor)
        if start < 0:
            return spans
        tag_end = lower.find(TAG_END, start + len(OPEN))
        if tag_end < 0:
            return spans
        body_start = tag_end + len(TAG_END)
        tag = lower[start:body_start]
        cursor = body_start
        if tag.rstrip().endswith(b"/&gt;"):
            continue
        close = lower.find(CLOSE, body_start)
        if close < 0:
            continue
        spans.append((body_start, close))
        cursor = close + len(CLOSE)


def normalized_skeleton(body: bytes) -> bytes:
    value = re.sub(br"https?://[^\s|}\]]+", b"URL", body.lower())
    value = re.sub(br"=\s*[^|}\n]*", b"=", value)
    value = re.sub(br"\d+", b"#", value)
    return re.sub(br"\s+", b" ", value)


def skeleton_key(body: bytes) -> bytes:
    return hashlib.blake2b(normalized_skeleton(body), digest_size=8).digest()


def make_skeleton(data: bytes) -> tuple[bytes, list[bytes]]:
    output = bytearray()
    bodies: list[bytes] = []
    cursor = 0
    for start, end in reference_body_spans(data):
        output.extend(data[cursor:start])
        output.extend(PLACEHOLDER)
        bodies.append(data[start:end])
        cursor = end
    output.extend(data[cursor:])
    return bytes(output), bodies


def matching_blocks(prior: bytes, body: bytes) -> list[difflib.Match]:
    return [
        block
        for block in difflib.SequenceMatcher(
            None, prior, body, autojunk=False
        ).get_matching_blocks()
        if block.size >= 4
    ]


def literal_event(body: bytes) -> bytes:
    return b"\x00" + encode_varint(len(body)) + body


def delta_event(prior_id: int, prior: bytes, body: bytes) -> bytes:
    blocks = matching_blocks(prior, body)
    output = bytearray(b"\x01")
    output.extend(encode_varint(prior_id))
    output.extend(encode_varint(len(blocks)))
    cursor = 0
    for block in blocks:
        addition = body[cursor : block.b]
        output.extend(encode_varint(len(addition)))
        output.extend(addition)
        output.extend(encode_varint(block.a))
        output.extend(encode_varint(block.size))
        cursor = block.b + block.size
    tail = body[cursor:]
    output.extend(encode_varint(len(tail)))
    output.extend(tail)
    return bytes(output)


def select_events(
    bodies: list[bytes], mode: str
) -> tuple[list[bytes], dict[str, int]]:
    prior_bodies: list[bytes] = []
    buckets: dict[bytes, list[int]] = defaultdict(list)
    events: list[bytes] = []
    paying = 0
    literal_bytes = 0
    selected_bytes = 0
    for body in bodies:
        literal = literal_event(body)
        selected = literal
        if mode == "delta":
            for prior_id in buckets[skeleton_key(body)][-16:]:
                candidate = delta_event(prior_id, prior_bodies[prior_id], body)
                if len(candidate) < len(selected):
                    selected = candidate
        if len(selected) < len(literal):
            paying += 1
        events.append(selected)
        literal_bytes += len(literal)
        selected_bytes += len(selected)
        prior_id = len(prior_bodies)
        prior_bodies.append(body)
        buckets[skeleton_key(body)].append(prior_id)
    return events, {
        "reference_bodies": len(bodies),
        "paying_delta_events": paying,
        "literal_event_bytes": literal_bytes,
        "selected_event_bytes": selected_bytes,
        "raw_mdl_saved_bytes": literal_bytes - selected_bytes,
    }


def encode_events(bodies: list[bytes], mode: str) -> tuple[bytes, dict[str, int]]:
    events, metrics = select_events(bodies, mode)
    return b"".join(events), metrics


def encode_transform(data: bytes, mode: str) -> tuple[bytes, dict[str, int]]:
    skeleton, bodies = make_skeleton(data)
    events, metrics = encode_events(bodies, mode)
    output = bytearray(MAGIC)
    output.append(1 if mode == "delta" else 0)
    output.extend(encode_varint(len(skeleton)))
    output.extend(skeleton)
    output.extend(encode_varint(len(bodies)))
    output.extend(events)
    return bytes(output), metrics


def decode_transform(payload: bytes) -> bytes:
    if not payload.startswith(MAGIC) or len(payload) < len(MAGIC) + 1:
        raise ValueError("invalid reference-delta payload")
    offset = len(MAGIC)
    mode = "delta" if payload[offset] else "literal"
    offset += 1
    skeleton_size, offset = decode_varint(payload, offset)
    skeleton = payload[offset : offset + skeleton_size]
    if len(skeleton) != skeleton_size:
        raise ValueError("truncated reference skeleton")
    offset += skeleton_size
    count, offset = decode_varint(payload, offset)
    bodies: list[bytes] = []
    for _ in range(count):
        if offset >= len(payload):
            raise ValueError("truncated reference event")
        opcode = payload[offset]
        offset += 1
        if opcode == 0:
            size, offset = decode_varint(payload, offset)
            body = payload[offset : offset + size]
            if len(body) != size:
                raise ValueError("truncated reference literal")
            offset += size
        elif opcode == 1 and mode == "delta":
            prior_id, offset = decode_varint(payload, offset)
            if prior_id >= len(bodies):
                raise ValueError("future reference dependency")
            block_count, offset = decode_varint(payload, offset)
            prior = bodies[prior_id]
            output = bytearray()
            for _ in range(block_count):
                size, offset = decode_varint(payload, offset)
                addition = payload[offset : offset + size]
                if len(addition) != size:
                    raise ValueError("truncated reference addition")
                offset += size
                prior_start, offset = decode_varint(payload, offset)
                copy_size, offset = decode_varint(payload, offset)
                if prior_start + copy_size > len(prior):
                    raise ValueError("reference copy out of range")
                output.extend(addition)
                output.extend(prior[prior_start : prior_start + copy_size])
            tail_size, offset = decode_varint(payload, offset)
            tail = payload[offset : offset + tail_size]
            if len(tail) != tail_size:
                raise ValueError("truncated reference tail")
            offset += tail_size
            output.extend(tail)
            body = bytes(output)
        else:
            raise ValueError("invalid reference event opcode")
        bodies.append(body)
    if offset != len(payload):
        raise ValueError("trailing reference-delta payload")
    spans = reference_body_spans(skeleton)
    if len(spans) != len(bodies):
        raise ValueError("reference body count changed")
    output = bytearray()
    cursor = 0
    for (start, end), body in zip(spans, bodies, strict=True):
        output.extend(skeleton[cursor:start])
        output.extend(body)
        cursor = end
    output.extend(skeleton[cursor:])
    return bytes(output)


def decode_event(event: bytes, mode: str, prior_bodies: list[bytes]) -> bytes:
    if not event:
        raise ValueError("empty reference event")
    offset = 1
    if event[0] == 0:
        size, offset = decode_varint(event, offset)
        body = event[offset : offset + size]
        offset += size
    elif event[0] == 1 and mode == "delta":
        prior_id, offset = decode_varint(event, offset)
        if prior_id >= len(prior_bodies):
            raise ValueError("future inline reference dependency")
        block_count, offset = decode_varint(event, offset)
        prior = prior_bodies[prior_id]
        output = bytearray()
        for _ in range(block_count):
            size, offset = decode_varint(event, offset)
            addition = event[offset : offset + size]
            if len(addition) != size:
                raise ValueError("truncated inline addition")
            offset += size
            prior_start, offset = decode_varint(event, offset)
            copy_size, offset = decode_varint(event, offset)
            if prior_start + copy_size > len(prior):
                raise ValueError("inline reference copy out of range")
            output.extend(addition)
            output.extend(prior[prior_start : prior_start + copy_size])
        tail_size, offset = decode_varint(event, offset)
        tail = event[offset : offset + tail_size]
        if len(tail) != tail_size:
            raise ValueError("truncated inline tail")
        offset += tail_size
        output.extend(tail)
        body = bytes(output)
    else:
        raise ValueError("invalid inline reference opcode")
    if offset != len(event):
        raise ValueError("trailing inline reference event")
    return body


def encode_inline_transform(data: bytes, mode: str) -> tuple[bytes, dict[str, int]]:
    spans = reference_body_spans(data)
    bodies = [data[start:end] for start, end in spans]
    events, metrics = select_events(bodies, mode)
    output = bytearray(INLINE_MAGIC)
    output.append(1 if mode == "delta" else 0)
    cursor = 0
    for (start, end), event in zip(spans, events, strict=True):
        output.extend(data[cursor:start])
        output.extend(encode_varint(len(event)))
        output.extend(event)
        cursor = end
    output.extend(data[cursor:])
    return bytes(output), metrics


def decode_inline_transform(payload: bytes) -> bytes:
    if not payload.startswith(INLINE_MAGIC) or len(payload) < len(INLINE_MAGIC) + 1:
        raise ValueError("invalid inline reference payload")
    mode = "delta" if payload[len(INLINE_MAGIC)] else "literal"
    data = payload[len(INLINE_MAGIC) + 1 :]
    lower = data.lower()
    output = bytearray()
    bodies: list[bytes] = []
    cursor = 0
    while True:
        start = lower.find(OPEN, cursor)
        if start < 0:
            output.extend(data[cursor:])
            return bytes(output)
        output.extend(data[cursor:start])
        tag_end = lower.find(TAG_END, start + len(OPEN))
        if tag_end < 0:
            output.extend(data[start:])
            return bytes(output)
        body_start = tag_end + len(TAG_END)
        tag = data[start:body_start]
        output.extend(tag)
        if tag.lower().rstrip().endswith(b"/&gt;"):
            cursor = body_start
            continue
        event_size, event_start = decode_varint(data, body_start)
        event_end = event_start + event_size
        event = data[event_start:event_end]
        if len(event) != event_size:
            raise ValueError("truncated inline reference event")
        body = decode_event(event, mode, bodies)
        bodies.append(body)
        output.extend(body)
        if data[event_end : event_end + len(CLOSE)].lower() != CLOSE:
            raise ValueError("inline reference close tag missing")
        output.extend(data[event_end : event_end + len(CLOSE)])
        cursor = event_end + len(CLOSE)


def compressed_sizes(data: bytes) -> dict[str, int]:
    return {
        "bz2": len(bz2.compress(data, compresslevel=9)),
        "lzma": len(lzma.compress(data, preset=9)),
    }


def full_corpus_oracle(corpus: bytes) -> dict[str, int]:
    bodies = [corpus[start:end] for start, end in reference_body_spans(corpus)]
    _, metrics = encode_events(bodies, "delta")
    return metrics


def random_starts(total: int, size: int, count: int, seed: str) -> list[int]:
    rng = random.Random(int.from_bytes(hashlib.sha256(seed.encode()).digest(), "big"))
    starts: list[int] = []
    while len(starts) < count:
        start = rng.randrange(total - size + 1)
        if all(abs(start - prior) >= size for prior in starts):
            starts.append(start)
    return sorted(starts)


def dense_starts(
    corpus: bytes, size: int, count: int, rank_offset: int
) -> list[int]:
    counts: dict[int, int] = defaultdict(int)
    for start, _ in reference_body_spans(corpus):
        counts[start // size] += 1
    ranked = sorted(counts, key=lambda block: (-counts[block], block))
    selected = ranked[rank_offset : rank_offset + count]
    if len(selected) != count:
        raise ValueError("not enough reference-bearing blocks")
    return sorted(block * size for block in selected)


def run(args: argparse.Namespace) -> dict[str, Any]:
    corpus = args.data.read_bytes()
    rows: list[dict[str, Any]] = []
    for size in args.window_sizes:
        starts = (
            dense_starts(corpus, size, args.windows_per_size, args.dense_rank_offset)
            if args.sampling == "event_dense"
            else random_starts(
                len(corpus), size, args.windows_per_size, f"{args.seed}:{size}"
            )
        )
        for start in starts:
            window = corpus[start : start + size]
            raw_sizes = compressed_sizes(window)
            payloads: dict[str, bytes] = {}
            metrics: dict[str, dict[str, int]] = {}
            for mode in ("literal", "delta"):
                if args.layout == "inline":
                    payload, mode_metrics = encode_inline_transform(window, mode)
                    restored = decode_inline_transform(payload)
                else:
                    payload, mode_metrics = encode_transform(window, mode)
                    restored = decode_transform(payload)
                if restored != window:
                    raise RuntimeError("reference-delta roundtrip failed")
                payloads[mode] = payload
                metrics[mode] = mode_metrics
            literal_sizes = compressed_sizes(payloads["literal"])
            delta_sizes = compressed_sizes(payloads["delta"])
            rows.append(
                {
                    "scope_bytes": size,
                    "start": start,
                    **metrics["delta"],
                    "delta_payload_bytes": len(payloads["delta"]),
                    "literal_payload_bytes": len(payloads["literal"]),
                    "bz2_saved_vs_raw": raw_sizes["bz2"] - delta_sizes["bz2"],
                    "lzma_saved_vs_raw": raw_sizes["lzma"] - delta_sizes["lzma"],
                    "bz2_saved_vs_literal_control": literal_sizes["bz2"]
                    - delta_sizes["bz2"],
                    "lzma_saved_vs_literal_control": literal_sizes["lzma"]
                    - delta_sizes["lzma"],
                    "roundtrip_ok": True,
                }
            )
    aggregates = []
    for size in args.window_sizes:
        group = [row for row in rows if row["scope_bytes"] == size]
        aggregates.append(
            {
                "scope_bytes": size,
                "windows": len(group),
                "reference_bodies": sum(row["reference_bodies"] for row in group),
                "paying_delta_events": sum(
                    row["paying_delta_events"] for row in group
                ),
                "raw_mdl_saved_bytes": sum(row["raw_mdl_saved_bytes"] for row in group),
                "bz2_saved_vs_raw": sum(row["bz2_saved_vs_raw"] for row in group),
                "lzma_saved_vs_raw": sum(row["lzma_saved_vs_raw"] for row in group),
                "bz2_saved_vs_literal_control": sum(
                    row["bz2_saved_vs_literal_control"] for row in group
                ),
                "lzma_saved_vs_literal_control": sum(
                    row["lzma_saved_vs_literal_control"] for row in group
                ),
                "positive_lzma_windows_vs_raw": sum(
                    row["lzma_saved_vs_raw"] > 0 for row in group
                ),
            }
        )
    return {
        "schema": "wikiir_reference_delta_probe_v1",
        "evidence_tier": "reversible_proxy",
        "claim_boundary": (
            "Exact reversible BZip2/LZMA window proxy. Event-dense selection is "
            "discovery-only and does not establish corpus-wide or endpoint428 gain."
        ),
        "data": {
            "path": str(args.data.resolve()),
            "bytes": len(corpus),
            "sha256": hashlib.sha256(corpus).hexdigest(),
        },
        "sampling": args.sampling,
        "layout": args.layout,
        "seed": args.seed,
        "dense_rank_offset": args.dense_rank_offset,
        "full_corpus_causal_raw_mdl_oracle": (
            full_corpus_oracle(corpus) if args.include_full_corpus_oracle else None
        ),
        "rows": rows,
        "aggregates": aggregates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("projects/enwiki9/data/enwik9"))
    parser.add_argument("--window-sizes", type=int, nargs="+", default=[500_000, 1_000_000])
    parser.add_argument("--windows-per-size", type=int, default=2)
    parser.add_argument("--sampling", choices=("random", "event_dense"), default="event_dense")
    parser.add_argument("--layout", choices=("columnar", "inline"), default="inline")
    parser.add_argument("--seed", default="reference-delta-selection-v1")
    parser.add_argument("--dense-rank-offset", type=int, default=0)
    parser.add_argument("--include-full-corpus-oracle", action="store_true")
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
