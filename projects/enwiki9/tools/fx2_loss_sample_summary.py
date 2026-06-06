#!/usr/bin/env python3
"""Summarize deterministically sampled FX2_LOSS_LEDGER rows."""

from __future__ import annotations

import argparse
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


def as_int(row: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(row.get(key, str(default)))
    except ValueError:
        return default


def read_rows(path: pathlib.Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", errors="replace") as f:
        for line in f:
            row = parse_row(line)
            if row is not None:
                rows.append(row)
    rows.sort(key=lambda row: as_int(row, "pos"))
    return rows


def row_stride(row: dict[str, str], fallback: int) -> int:
    return max(1, as_int(row, "ledger_stride", fallback))


def qbits(row: dict[str, str], key: str) -> int:
    if key == "oracle_gap_qbits":
        return max(0, as_int(row, key))
    return as_int(row, key)


def group_rows(
    rows: list[dict[str, str]],
    fields: list[str],
    fallback_stride: int,
    limit: int,
) -> list[dict[str, object]]:
    totals: dict[tuple[str, ...], list[int]] = collections.defaultdict(
        lambda: [0, 0, 0, 0]
    )
    for row in rows:
        key = tuple(row.get(field, "") for field in fields)
        stride = row_stride(row, fallback_stride)
        bucket = totals[key]
        bucket[0] += 1
        bucket[1] += qbits(row, "qbits")
        bucket[2] += qbits(row, "oracle_gap_qbits")
        bucket[3] += qbits(row, "oracle_gap_qbits") * stride
    ranked = []
    for key, (count, loss_qbits, gap_qbits, estimated_gap_qbits) in totals.items():
        ranked.append(
            {
                "key": dict(zip(fields, key)),
                "rows": count,
                "observed_loss_bits": loss_qbits / 256.0,
                "observed_oracle_gap_bits": gap_qbits / 256.0,
                "estimated_oracle_gap_bytes": estimated_gap_qbits / 2048.0,
            }
        )
    ranked.sort(
        key=lambda item: (
            -float(item["estimated_oracle_gap_bytes"]),
            -float(item["observed_loss_bits"]),
        )
    )
    return ranked[:limit]


def top_windows(
    rows: list[dict[str, str]],
    fallback_stride: int,
    span: int,
    limit: int,
) -> list[dict[str, object]]:
    if not rows:
        return []
    positions = [as_int(row, "pos") for row in rows]
    selected: list[dict[str, object]] = []
    end = 0
    candidates: list[tuple[int, int, int, int, int]] = []
    for start, pos in enumerate(positions):
        while end < len(rows) and positions[end] < pos + span:
            end += 1
        window = rows[start:end]
        if not window:
            continue
        observed_gap = sum(qbits(row, "oracle_gap_qbits") for row in window)
        estimated_gap = sum(
            qbits(row, "oracle_gap_qbits") * row_stride(row, fallback_stride)
            for row in window
        )
        candidates.append((estimated_gap, observed_gap, len(window), start, end))
    candidates.sort(key=lambda item: (-item[0], -item[1], -item[2]))
    used: list[tuple[int, int]] = []
    for estimated_gap, observed_gap, count, start, end in candidates:
        begin = positions[start]
        interval = (begin, begin + span)
        if any(max(interval[0], old[0]) < min(interval[1], old[1]) for old in used):
            continue
        window = rows[start:end]
        groups = collections.Counter(row.get("oracle_group", "") for row in window)
        byte_classes = collections.Counter(row.get("byte_class", "") for row in window)
        selected.append(
            {
                "start": begin,
                "end": begin + span,
                "rows": count,
                "observed_oracle_gap_bits": observed_gap / 256.0,
                "estimated_oracle_gap_bytes": estimated_gap / 2048.0,
                "dominant_oracle_group": groups.most_common(1)[0][0],
                "dominant_byte_class": byte_classes.most_common(1)[0][0],
            }
        )
        used.append(interval)
        if len(selected) >= limit:
            break
    return selected


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=pathlib.Path)
    ap.add_argument("--output", type=pathlib.Path)
    ap.add_argument("--sample-stride", type=int, default=1)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--window-span", type=int, default=4096)
    ap.add_argument("--top-windows", type=int, default=12)
    args = ap.parse_args()

    rows = read_rows(args.log)
    if not rows:
        raise SystemExit("no FX2_LOSS_LEDGER rows found")
    fallback_stride = max(1, args.sample_stride)
    loss_qbits = sum(qbits(row, "qbits") for row in rows)
    gap_qbits = sum(qbits(row, "oracle_gap_qbits") for row in rows)
    estimated_loss_qbits = sum(
        qbits(row, "qbits") * row_stride(row, fallback_stride) for row in rows
    )
    estimated_gap_qbits = sum(
        qbits(row, "oracle_gap_qbits") * row_stride(row, fallback_stride)
        for row in rows
    )
    result = {
        "log": str(args.log),
        "rows": len(rows),
        "first_pos": as_int(rows[0], "pos"),
        "last_pos": as_int(rows[-1], "pos"),
        "observed_loss_bits": loss_qbits / 256.0,
        "observed_oracle_gap_bits": gap_qbits / 256.0,
        "observed_oracle_gap_bytes": gap_qbits / 2048.0,
        "estimated_loss_bits": estimated_loss_qbits / 256.0,
        "estimated_oracle_gap_bits": estimated_gap_qbits / 256.0,
        "estimated_oracle_gap_bytes": estimated_gap_qbits / 2048.0,
        "estimator_note": (
            "Rows are a deterministic position-stride sample after threshold and "
            "gap filters; scaled values are attribution estimates, not exact scores."
        ),
        "top_by_byte_class": group_rows(
            rows, ["byte_class"], fallback_stride, args.top
        ),
        "top_by_oracle_group": group_rows(
            rows, ["oracle_group"], fallback_stride, args.top
        ),
        "top_by_struct": group_rows(
            rows,
            ["field", "slot", "template_depth", "template_arg", "byte_class"],
            fallback_stride,
            args.top,
        ),
        "top_by_wrt": group_rows(
            rows,
            ["wrt_state", "wrt_first", "wrt_second", "byte_class"],
            fallback_stride,
            args.top,
        ),
        "top_windows": top_windows(
            rows, fallback_stride, args.window_span, args.top_windows
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
