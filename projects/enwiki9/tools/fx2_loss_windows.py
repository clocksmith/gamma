#!/usr/bin/env python3
"""Annotate FX2_LOSS_LEDGER rows with local preprocessed bytes."""

from __future__ import annotations

import argparse
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


def read_rows(path: pathlib.Path) -> list[dict[str, str]]:
    rows = []
    with path.open("r", errors="replace") as f:
        for line in f:
            row = parse_row(line)
            if row is not None:
                rows.append(row)
    rows.sort(key=lambda row: (-as_int(row, "qbits"), as_int(row, "pos")))
    return rows


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=pathlib.Path)
    ap.add_argument("preprocessed", type=pathlib.Path)
    ap.add_argument("--skip", type=int, default=0)
    ap.add_argument("--top", type=int, default=80)
    ap.add_argument("--context", type=int, default=24)
    ap.add_argument("--min-match", type=int, default=8)
    ap.add_argument("--max-match", type=int, default=96)
    ap.add_argument("--candidates", type=int, default=64)
    args = ap.parse_args()

    data = args.preprocessed.read_bytes()[args.skip :]
    rows = read_rows(args.log)
    print(
        "rank\tpos\tqbits\tbits\tbyte\tfield\tslot\tdepth\targ\tclass\t"
        "oracle_group\toracle_gap_bits\tprev_len\tprev_dist\tleft\tright"
    )
    for rank, row in enumerate(rows[: args.top]):
        pos = as_int(row, "pos")
        qbits = as_int(row, "qbits")
        oracle_gap = as_int(row, "oracle_gap_qbits") / 256.0
        prev_len, prev_dist = previous_match(
            data, pos, args.min_match, args.max_match, args.candidates
        )
        left = escaped(data[max(0, pos - args.context) : pos])
        right = escaped(data[pos : min(len(data), pos + args.context)])
        print(
            f"{rank}\t{pos}\t{qbits}\t{qbits / 256.0:.3f}\t"
            f"{row.get('byte', '')}\t{row.get('field', '')}\t"
            f"{row.get('slot', '')}\t{row.get('template_depth', '')}\t"
            f"{row.get('template_arg', '')}\t{row.get('byte_class', '')}\t"
            f"{row.get('oracle_group', '')}\t{oracle_gap:.3f}\t"
            f"{prev_len}\t{prev_dist}\t{left}\t{right}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
