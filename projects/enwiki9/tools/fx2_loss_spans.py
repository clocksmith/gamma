#!/usr/bin/env python3
"""Rank dense FX2_LOSS_LEDGER regions as candidate RDO spans."""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import string

PAIR_RE = re.compile(r"([A-Za-z_]+)=([^ ]+)")
PREFIX = "FX2_LOSS_LEDGER "
PRINTABLE = set(bytes(string.printable, "ascii")) - {0x0b, 0x0c}


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


def escaped(data: bytes) -> str:
    out: list[str] = []
    for b in data:
        if b in PRINTABLE and b not in (ord("\t"), ord("\n"), ord("\r")):
            out.append(chr(b))
        elif b == ord("\n"):
            out.append("\\n")
        elif b == ord("\r"):
            out.append("\\r")
        elif b == ord("\t"):
            out.append("\\t")
        else:
            out.append(f"\\x{b:02x}")
    return "".join(out)


def dominant(rows: list[dict[str, str]], field: str) -> str:
    counts = collections.Counter(row.get(field, "") for row in rows)
    value, count = counts.most_common(1)[0]
    return f"{value}:{count}"


def previous_match(
    data: bytes,
    pos: int,
    min_len: int,
    max_len: int,
    candidates: int,
) -> tuple[int, int]:
    if pos < min_len or pos >= len(data):
        return 0, 0
    seed = data[pos : pos + min_len]
    if len(seed) < min_len:
        return 0, 0
    best_len = 0
    best_dist = 0
    end = pos
    for _ in range(candidates):
        found = data.rfind(seed, 0, end)
        if found < 0:
            break
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
        end = found
    return best_len, best_dist


def prefix(rows: list[dict[str, str]], field: str) -> list[int]:
    out = [0]
    for row in rows:
        out.append(out[-1] + as_int(row, field))
    return out


def overlap(a: tuple[int, int], b: tuple[int, int]) -> int:
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=pathlib.Path)
    ap.add_argument("--data", type=pathlib.Path)
    ap.add_argument("--skip", type=int, default=0)
    ap.add_argument("--span", type=int, default=4096)
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--min-rows", type=int, default=4)
    ap.add_argument("--context", type=int, default=32)
    ap.add_argument("--min-match", type=int, default=12)
    ap.add_argument("--max-match", type=int, default=256)
    ap.add_argument("--candidates", type=int, default=128)
    args = ap.parse_args()

    rows = read_rows(args.log)
    if not rows:
        raise SystemExit("no FX2_LOSS_LEDGER rows found")

    qprefix = prefix(rows, "qbits")
    gprefix = prefix(rows, "oracle_gap_qbits")
    positions = [as_int(row, "pos") for row in rows]
    candidates: list[tuple[int, int, int, int, int, int]] = []
    end = 0
    for start, pos in enumerate(positions):
        while end < len(rows) and positions[end] < pos + args.span:
            end += 1
        count = end - start
        if count < args.min_rows:
            continue
        qbits = qprefix[end] - qprefix[start]
        gap = gprefix[end] - gprefix[start]
        peak = max(as_int(row, "qbits") for row in rows[start:end])
        candidates.append((qbits, gap, peak, start, end, count))

    candidates.sort(key=lambda item: (-item[0], -item[1], -item[2]))
    selected: list[tuple[int, int, int, int, int, int]] = []
    selected_ranges: list[tuple[int, int]] = []
    for cand in candidates:
        _, _, _, start, end, _ = cand
        span_range = (positions[start], positions[start] + args.span)
        if any(overlap(span_range, chosen) * 2 >= args.span for chosen in selected_ranges):
            continue
        selected.append(cand)
        selected_ranges.append(span_range)
        if len(selected) >= args.top:
            break

    data = b""
    if args.data:
        data = args.data.read_bytes()[args.skip :]

    print(
        "rank\tstart\tend\trows\tqbits\tbits\toracle_gap_bits\t"
        "recoverable_bytes\trow_density\tledger_bpb\tpeak_qbits\t"
        "field\tslot\tdepth\targ\twrt_state\toracle_group\t"
        "prev_len\tprev_dist\tleft\tright"
    )
    for rank, (qbits, gap, peak, start, end, count) in enumerate(selected):
        span_rows = rows[start:end]
        pos = positions[start]
        prev_len = prev_dist = 0
        left = right = ""
        if data:
            prev_len, prev_dist = previous_match(
                data, pos, args.min_match, args.max_match, args.candidates
            )
            left = escaped(data[max(0, pos - args.context) : pos])
            right = escaped(data[pos : min(len(data), pos + args.context)])
        print(
            f"{rank}\t{pos}\t{pos + args.span}\t{count}\t{qbits}\t"
            f"{qbits / 256.0:.3f}\t{gap / 256.0:.3f}\t"
            f"{gap / 2048.0:.3f}\t{count / args.span:.6f}\t"
            f"{qbits / 256.0 / args.span:.6f}\t{peak}\t"
            f"{dominant(span_rows, 'field')}\t"
            f"{dominant(span_rows, 'slot')}\t"
            f"{dominant(span_rows, 'template_depth')}\t"
            f"{dominant(span_rows, 'template_arg')}\t"
            f"{dominant(span_rows, 'wrt_state')}\t"
            f"{dominant(span_rows, 'oracle_group')}\t"
            f"{prev_len}\t{prev_dist}\t{left}\t{right}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
