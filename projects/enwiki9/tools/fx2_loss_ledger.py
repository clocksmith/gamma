#!/usr/bin/env python3
"""Aggregate FX2_LOSS_LEDGER rows from an fx2-cmix stderr log."""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

PAIR_RE = re.compile(r"([A-Za-z_]+)=([^ ]+)")
PREFIX = "FX2_LOSS_LEDGER "


def parse_row(line: str) -> dict[str, str] | None:
    if PREFIX not in line:
        return None
    payload = line.split(PREFIX, 1)[1].strip()
    row = {key: value for key, value in PAIR_RE.findall(payload)}
    return row or None


def as_int(row: dict[str, str], key: str) -> int:
    try:
        return int(row.get(key, "0"))
    except ValueError:
        return 0


def aggregate(
    rows: list[dict[str, str]],
    group_fields: list[str],
) -> list[tuple[tuple[str, ...], int, int, int, int]]:
    totals: dict[tuple[str, ...], list[int]] = collections.defaultdict(
        lambda: [0, 0, 0, 0]
    )
    for row in rows:
        key = tuple(row.get(field, "") for field in group_fields)
        bucket = totals[key]
        qbits = as_int(row, "qbits")
        oracle_gap = as_int(row, "oracle_gap_qbits")
        bucket[0] += 1
        bucket[1] += qbits
        bucket[2] += oracle_gap
        bucket[3] = max(bucket[3], qbits)
    ranked = [(key, *values) for key, values in totals.items()]
    ranked.sort(key=lambda item: (-item[2], -item[3], item[0]))
    return ranked


def read_rows(path: pathlib.Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", errors="replace") as f:
        for line in f:
            row = parse_row(line)
            if row is not None:
                rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=pathlib.Path)
    ap.add_argument(
        "--group",
        default="field,template_depth,template_hash,template_arg,byte_class",
        help="comma-separated FX2_LOSS_LEDGER fields to group by",
    )
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

    rows = read_rows(args.log)
    group_fields = [field for field in args.group.split(",") if field]
    if not rows:
        print("no FX2_LOSS_LEDGER rows found", file=sys.stderr)
        return 1

    print(
        "group_fields\trows\tqbits\tbits\toracle_gap_qbits\t"
        "oracle_gap_bits\tpeak_qbits\tkey"
    )
    for key, count, qbits, oracle_gap, peak in aggregate(rows, group_fields)[
        : args.top
    ]:
        print(
            f"{','.join(group_fields)}\t{count}\t{qbits}\t{qbits / 256:.3f}\t"
            f"{oracle_gap}\t{oracle_gap / 256:.3f}\t{peak}\t"
            f"{','.join(key)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
