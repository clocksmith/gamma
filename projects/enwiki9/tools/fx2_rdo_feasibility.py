#!/usr/bin/env python3
"""Estimate copy-style RDO headroom from FX2_LOSS_LEDGER rows."""

from __future__ import annotations

import argparse
import bisect
import collections
import json
import pathlib
import re

PAIR_RE = re.compile(r"([A-Za-z_]+)=([^ ]+)")
PREFIX = "FX2_LOSS_LEDGER "


def parse_row(line: str) -> dict[str, str] | None:
    if PREFIX not in line:
        return None
    row = {key: value for key, value in PAIR_RE.findall(line.split(PREFIX, 1)[1])}
    return row or None


def as_int(row: dict[str, str], key: str) -> int:
    try:
        return int(row.get(key, "0"))
    except ValueError:
        return 0


def read_rows(path: pathlib.Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", errors="replace") as f:
        for line in f:
            row = parse_row(line)
            if row is not None:
                rows.append(row)
    rows.sort(key=lambda row: as_int(row, "pos"))
    return rows


def build_seed_index(data: bytes, seed_len: int, cap: int) -> dict[bytes, list[int]]:
    index: dict[bytes, list[int]] = collections.defaultdict(list)
    if seed_len <= 0 or len(data) < seed_len:
        return index
    for pos in range(0, len(data) - seed_len + 1):
        bucket = index[data[pos : pos + seed_len]]
        if len(bucket) >= cap:
            del bucket[0]
        bucket.append(pos)
    return index


def previous_match_indexed(
    data: bytes,
    index: dict[bytes, list[int]],
    pos: int,
    min_len: int,
    max_len: int,
) -> tuple[int, int]:
    if pos < min_len or pos >= len(data):
        return 0, 0
    seed = data[pos : pos + min_len]
    if len(seed) < min_len:
        return 0, 0
    best_len = 0
    best_dist = 0
    for found in reversed(index.get(seed, [])):
        if found >= pos:
            continue
        length = min_len
        while (
            length < max_len
            and pos + length < len(data)
            and found + length < pos
            and data[found + length] == data[pos + length]
        ):
            length += 1
        if length > best_len:
            best_len = length
            best_dist = pos - found
    return best_len, best_dist


def prefix(values: list[int]) -> list[int]:
    out = [0]
    for value in values:
        out.append(out[-1] + max(0, value))
    return out


def range_sum(positions: list[int], values_prefix: list[int], start: int, end: int) -> int:
    left = bisect.bisect_left(positions, start)
    right = bisect.bisect_left(positions, end)
    return values_prefix[right] - values_prefix[left]


def overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return max(a[0], b[0]) < min(a[1], b[1])


def group_rows(rows: list[dict[str, str]], fields: list[str], limit: int) -> list[dict[str, object]]:
    buckets: dict[tuple[str, ...], list[int]] = collections.defaultdict(lambda: [0, 0, 0])
    for row in rows:
        key = tuple(row.get(field, "") for field in fields)
        bucket = buckets[key]
        bucket[0] += 1
        bucket[1] += as_int(row, "qbits")
        bucket[2] += max(0, as_int(row, "oracle_gap_qbits"))
    ranked = []
    for key, (count, qbits, gap_qbits) in buckets.items():
        ranked.append(
            {
                "key": dict(zip(fields, key)),
                "rows": count,
                "qbits": qbits,
                "bits": qbits / 256.0,
                "oracle_gap_bits": gap_qbits / 256.0,
                "oracle_gap_bytes": gap_qbits / 2048.0,
            }
        )
    ranked.sort(key=lambda item: (-item["oracle_gap_bits"], -item["bits"]))
    return ranked[:limit]


def build_copy_candidates(
    rows: list[dict[str, str]],
    data: bytes,
    min_match: int,
    max_match: int,
    candidates: int,
    copy_cost_bits: float,
) -> list[dict[str, object]]:
    positions = [as_int(row, "pos") for row in rows]
    gap_values = [max(0, as_int(row, "oracle_gap_qbits")) for row in rows]
    gap_prefix = prefix(gap_values)
    out: list[dict[str, object]] = []
    cost_qbits = int(copy_cost_bits * 256.0 + 0.5)
    index = build_seed_index(data, min_match, candidates)
    seen: set[tuple[int, int]] = set()
    for pos in positions:
        length, dist = previous_match_indexed(data, index, pos, min_match, max_match)
        if length < min_match:
            continue
        key = (pos, length)
        if key in seen:
            continue
        seen.add(key)
        gross_qbits = range_sum(positions, gap_prefix, pos, pos + length)
        net_qbits = gross_qbits - cost_qbits
        if net_qbits <= 0:
            continue
        out.append(
            {
                "start": pos,
                "end": pos + length,
                "length": length,
                "distance": dist,
                "gross_bits": gross_qbits / 256.0,
                "net_bits": net_qbits / 256.0,
                "net_bytes": net_qbits / 2048.0,
            }
        )
    out.sort(key=lambda item: (-item["net_bits"], -item["length"], item["start"]))
    return out


def select_non_overlapping(
    candidates: list[dict[str, object]], limit: int
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    ranges: list[tuple[int, int]] = []
    for item in candidates:
        span = (int(item["start"]), int(item["end"]))
        if any(overlaps(span, old) for old in ranges):
            continue
        selected.append(item)
        ranges.append(span)
        if len(selected) >= limit:
            break
    return selected


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=pathlib.Path)
    ap.add_argument("--data", type=pathlib.Path, required=True)
    ap.add_argument("--output", type=pathlib.Path)
    ap.add_argument("--min-match", type=int, default=8)
    ap.add_argument("--max-match", type=int, default=512)
    ap.add_argument("--candidates", type=int, default=128)
    ap.add_argument("--copy-cost-bits", type=float, default=32.0)
    ap.add_argument("--top-groups", type=int, default=20)
    ap.add_argument("--top-copies", type=int, default=200)
    args = ap.parse_args()

    rows = read_rows(args.log)
    if not rows:
        raise SystemExit("no FX2_LOSS_LEDGER rows found")
    data = args.data.read_bytes()
    candidates = build_copy_candidates(
        rows,
        data,
        args.min_match,
        args.max_match,
        args.candidates,
        args.copy_cost_bits,
    )
    selected = select_non_overlapping(candidates, args.top_copies)
    total_qbits = sum(as_int(row, "qbits") for row in rows)
    gap_qbits = sum(max(0, as_int(row, "oracle_gap_qbits")) for row in rows)
    net_bits = sum(float(item["net_bits"]) for item in selected)
    result = {
        "log": str(args.log),
        "data": str(args.data),
        "rows": len(rows),
        "first_pos": as_int(rows[0], "pos"),
        "last_pos": as_int(rows[-1], "pos"),
        "sampled_loss_bits": total_qbits / 256.0,
        "sampled_oracle_gap_bits": gap_qbits / 256.0,
        "sampled_oracle_gap_bytes": gap_qbits / 2048.0,
        "copy_cost_bits": args.copy_cost_bits,
        "min_match": args.min_match,
        "max_match": args.max_match,
        "copy_candidate_count": len(candidates),
        "selected_copy_count": len(selected),
        "selected_copy_net_bits": net_bits,
        "selected_copy_net_bytes": net_bits / 8.0,
        "selected_copy_gap_fraction": net_bits / (gap_qbits / 256.0)
        if gap_qbits
        else 0.0,
        "top_copy_spans": selected[:20],
        "top_by_oracle_group": group_rows(rows, ["oracle_group"], args.top_groups),
        "top_by_byte_class": group_rows(rows, ["byte_class"], args.top_groups),
        "top_by_wrt_pair": group_rows(
            rows,
            ["field", "template_depth", "wrt_state", "wrt_first", "wrt_second"],
            args.top_groups,
        ),
    }
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
