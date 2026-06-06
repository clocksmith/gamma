#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from array import array
from dataclasses import dataclass, field
from typing import Iterable


PROSE_FIELDS = (
    (b'<text xml:space="preserve">', b"</text>", "text"),
    (b"<title>", b"</title>", "title"),
    (b"<comment>", b"</comment>", "comment"),
    (b"<username>", b"</username>", "username"),
    (b"<sitename>", b"</sitename>", "sitename"),
    (b"<base>", b"</base>", "base"),
)
VALUE_FIELDS = (
    (b"<timestamp>", b"</timestamp>", "timestamp"),
    (b"<id>", b"</id>", "id"),
    (b"<ip>", b"</ip>", "ip"),
)
FIELDS = tuple(sorted(PROSE_FIELDS + VALUE_FIELDS, key=lambda item: len(item[0]), reverse=True))
MASK64 = (1 << 64) - 1
FNV_OFFSET = 1469598103934665603
FNV_PRIME = 1099511628211


def splitmix64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & MASK64
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & MASK64
    return (x ^ (x >> 31)) & MASK64


def hash_bytes(data: bytes, seed: int) -> int:
    h = (FNV_OFFSET ^ seed) & MASK64
    for b in data:
        h ^= b
        h = (h * FNV_PRIME) & MASK64
    h ^= h >> 33
    h = (h * 0xFF51AFD7ED558CCD) & MASK64
    h ^= h >> 33
    return h


def is_token_byte(b: int) -> bool:
    return (48 <= b <= 57) or (65 <= b <= 90) or (97 <= b <= 122)


def lower_ascii(data: bytes) -> bytes:
    return bytes((b + 32 if 65 <= b <= 90 else b) for b in data)


def parse_widths(raw: str) -> list[int]:
    out: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        value = int(part)
        if value <= 0:
            raise argparse.ArgumentTypeError("widths must be positive")
        out.append(value)
    if not out:
        raise argparse.ArgumentTypeError("at least one width is required")
    return out


class CountMinSketch:
    def __init__(self, width: int, depth: int, seed: int) -> None:
        self.width = width
        self.depth = depth
        self.seeds = [splitmix64(seed + i * 0x9E3779B97F4A7C15) for i in range(depth)]
        self.rows = [array("I", [0]) * width for _ in range(depth)]

    def indexes(self, key: bytes) -> Iterable[tuple[array, int]]:
        for row, seed in zip(self.rows, self.seeds):
            yield row, hash_bytes(key, seed) % self.width

    def query(self, key: bytes) -> int:
        estimate = None
        for row, idx in self.indexes(key):
            value = row[idx]
            estimate = value if estimate is None else min(estimate, value)
        return int(estimate or 0)

    def add(self, key: bytes) -> None:
        for row, idx in self.indexes(key):
            if row[idx] < 0xFFFFFFFF:
                row[idx] += 1


@dataclass
class EventStats:
    events: int = 0
    token_bytes: int = 0
    actual_seen: int = 0
    predicted_seen: int = 0
    seen_tp: int = 0
    seen_fp: int = 0
    seen_fn: int = 0
    actual_heavy: int = 0
    predicted_heavy: int = 0
    heavy_tp: int = 0
    heavy_fp: int = 0
    heavy_fn: int = 0
    overestimate_events: int = 0
    overestimate_total: int = 0
    max_overestimate: int = 0
    recurring_token_bytes: int = 0
    heavy_token_bytes: int = 0

    def observe(self, exact: int, estimate: int, size: int, heavy_threshold: int) -> None:
        self.events += 1
        self.token_bytes += size

        actual_seen = exact > 0
        predicted_seen = estimate > 0
        if actual_seen:
            self.actual_seen += 1
            self.recurring_token_bytes += size
        if predicted_seen:
            self.predicted_seen += 1
        if actual_seen and predicted_seen:
            self.seen_tp += 1
        elif predicted_seen:
            self.seen_fp += 1
        elif actual_seen:
            self.seen_fn += 1

        actual_heavy = exact >= heavy_threshold
        predicted_heavy = estimate >= heavy_threshold
        if actual_heavy:
            self.actual_heavy += 1
            self.heavy_token_bytes += size
        if predicted_heavy:
            self.predicted_heavy += 1
        if actual_heavy and predicted_heavy:
            self.heavy_tp += 1
        elif predicted_heavy:
            self.heavy_fp += 1
        elif actual_heavy:
            self.heavy_fn += 1

        if estimate > exact:
            over = estimate - exact
            self.overestimate_events += 1
            self.overestimate_total += over
            self.max_overestimate = max(self.max_overestimate, over)

    @staticmethod
    def _ratio(a: int, b: int) -> float:
        return round(a / b, 6) if b else 0.0

    def as_json(self) -> dict:
        return {
            "events": self.events,
            "token_bytes": self.token_bytes,
            "actual_seen": self.actual_seen,
            "predicted_seen": self.predicted_seen,
            "seen_precision": self._ratio(self.seen_tp, self.predicted_seen),
            "seen_recall": self._ratio(self.seen_tp, self.actual_seen),
            "seen_false_positive_rate": self._ratio(self.seen_fp, self.events - self.actual_seen),
            "seen_false_negative_rate": self._ratio(self.seen_fn, self.actual_seen),
            "actual_heavy": self.actual_heavy,
            "predicted_heavy": self.predicted_heavy,
            "heavy_precision": self._ratio(self.heavy_tp, self.predicted_heavy),
            "heavy_recall": self._ratio(self.heavy_tp, self.actual_heavy),
            "heavy_false_positive_rate": self._ratio(self.heavy_fp, self.events - self.actual_heavy),
            "heavy_false_negative_rate": self._ratio(self.heavy_fn, self.actual_heavy),
            "overestimate_event_share": self._ratio(self.overestimate_events, self.events),
            "mean_overestimate_when_present": self._ratio(self.overestimate_total, self.overestimate_events),
            "max_overestimate": self.max_overestimate,
            "recurring_token_byte_share": self._ratio(self.recurring_token_bytes, self.token_bytes),
            "heavy_token_byte_share": self._ratio(self.heavy_token_bytes, self.token_bytes),
        }


@dataclass
class SketchEval:
    name: str
    width: int
    depth: int
    seed: int
    heavy_threshold: int
    cms: CountMinSketch = field(init=False)
    exact: dict[bytes, int] = field(default_factory=dict)
    total: EventStats = field(default_factory=EventStats)
    by_label: dict[str, EventStats] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.cms = CountMinSketch(self.width, self.depth, self.seed)

    def observe(self, key: bytes, label: str, token_size: int) -> None:
        exact_count = self.exact.get(key, 0)
        estimate = self.cms.query(key)
        self.total.observe(exact_count, estimate, token_size, self.heavy_threshold)
        self.by_label.setdefault(label, EventStats()).observe(
            exact_count, estimate, token_size, self.heavy_threshold
        )
        self.cms.add(key)
        self.exact[key] = exact_count + 1

    def as_json(self) -> dict:
        return {
            "name": self.name,
            "width": self.width,
            "depth": self.depth,
            "seed": self.seed,
            "unique_exact_keys": len(self.exact),
            "total": self.total.as_json(),
            "by_label": {k: v.as_json() for k, v in sorted(self.by_label.items())},
        }


def token_events(buf: bytes, min_len: int) -> Iterable[bytes]:
    i = 0
    n = len(buf)
    while i < n:
        if not is_token_byte(buf[i]):
            i += 1
            continue
        j = i + 1
        while j < n and is_token_byte(buf[j]):
            j += 1
        if j - i >= min_len:
            yield lower_ascii(buf[i:j])
        i = j


def scan_layout(data: bytes, emit_region) -> dict:
    i = 0
    n = len(data)
    syntax = bytearray()
    field_counts: dict[str, int] = {}

    def flush_syntax() -> None:
        nonlocal syntax
        if syntax:
            emit_region("syntax", bytes(syntax))
            field_counts["syntax"] = field_counts.get("syntax", 0) + len(syntax)
            syntax = bytearray()

    while i < n:
        matched = False
        for open_tag, close_tag, label in FIELDS:
            if not data.startswith(open_tag, i):
                continue
            start = i + len(open_tag)
            end = data.find(close_tag, start)
            if end < 0:
                break
            flush_syntax()
            body = data[start:end]
            emit_region(label, body)
            field_counts[label] = field_counts.get(label, 0) + len(body)
            syntax.extend(open_tag)
            syntax.extend(close_tag)
            i = end + len(close_tag)
            matched = True
            break
        if matched:
            continue
        syntax.append(data[i])
        i += 1
    flush_syntax()
    return field_counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=pathlib.Path, default=pathlib.Path("data/enwik9"))
    ap.add_argument("--limit", type=int, required=True)
    ap.add_argument("--widths", type=parse_widths, default=parse_widths("4096,16384,65536,262144"))
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--min-len", type=int, default=3)
    ap.add_argument("--heavy-threshold", type=int, default=8)
    ap.add_argument("--json-out", type=pathlib.Path)
    args = ap.parse_args()

    if args.depth <= 0:
        raise SystemExit("--depth must be positive")
    if args.min_len <= 0:
        raise SystemExit("--min-len must be positive")
    if args.heavy_threshold <= 0:
        raise SystemExit("--heavy-threshold must be positive")

    data = args.data.read_bytes()[: args.limit]
    evals: list[SketchEval] = []
    for width in args.widths:
        evals.append(SketchEval("global", width, args.depth, args.seed, args.heavy_threshold))
        evals.append(SketchEval("layout_keyed", width, args.depth, args.seed, args.heavy_threshold))

    token_count = 0

    def emit_region(label: str, region: bytes) -> None:
        nonlocal token_count
        label_b = label.encode("ascii")
        for token in token_events(region, args.min_len):
            token_count += 1
            layout_key = label_b + b"\0" + token
            for ev in evals:
                key = layout_key if ev.name == "layout_keyed" else token
                ev.observe(key, label, len(token))

    field_bytes = scan_layout(data, emit_region)
    result = {
        "data_path": str(args.data),
        "data_size": len(data),
        "seed": args.seed,
        "depth": args.depth,
        "widths": args.widths,
        "min_len": args.min_len,
        "heavy_threshold": args.heavy_threshold,
        "token_events": token_count,
        "field_bytes": dict(sorted(field_bytes.items())),
        "sketches": [ev.as_json() for ev in evals],
    }

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
