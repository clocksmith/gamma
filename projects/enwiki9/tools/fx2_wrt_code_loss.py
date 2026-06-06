#!/usr/bin/env python3
"""Join FX2_LOSS_LEDGER rows to WRT dictionary code spans."""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

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


def read_rows(path: pathlib.Path) -> dict[int, list[dict[str, str]]]:
    by_pos: dict[int, list[dict[str, str]]] = collections.defaultdict(list)
    with path.open("r", errors="replace") as f:
        for line in f:
            row = parse_row(line)
            if row is not None:
                by_pos[as_int(row, "pos")].append(row)
    return by_pos


def read_dictionary(path: pathlib.Path) -> list[str]:
    words: list[str] = []
    current: list[str] = []
    for c in path.read_bytes():
        if ord("a") <= c <= ord("z"):
            current.append(chr(c))
        elif current:
            words.append("".join(current))
            current.clear()
    if current:
        words.append("".join(current))
    return words


def wrt_code_at(data: bytes, pos: int) -> tuple[int, int] | None:
    c = data[pos]
    if c == 0x0C:
        return None
    if 0x80 <= c <= 0xCF:
        return c - 0x80, 1
    if 0xD0 <= c <= 0xEF and pos + 1 < len(data):
        c1 = data[pos + 1]
        if 0x80 <= c1 <= 0xCF:
            return 80 + (c - 0xD0) * 80 + (c1 - 0x80), 2
    if c >= 0xF0 and pos + 2 < len(data):
        c1 = data[pos + 1]
        c2 = data[pos + 2]
        if 0xD0 <= c1 <= 0xEF and 0x80 <= c2 <= 0xCF:
            return 3920 + (c - 0xF0) * 32 * 80 + (c1 - 0xD0) * 80 + (c2 - 0x80), 3
    return None


def qbits(row: dict[str, str], key: str) -> int:
    return as_int(row, key)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=pathlib.Path)
    ap.add_argument("--store", type=pathlib.Path, required=True)
    ap.add_argument("--dictionary", type=pathlib.Path, required=True)
    ap.add_argument("--output", type=pathlib.Path)
    ap.add_argument("--top", type=int, default=80)
    args = ap.parse_args()

    rows_by_pos = read_rows(args.log)
    if not rows_by_pos:
        raise SystemExit("no FX2_LOSS_LEDGER rows found")
    data = args.store.read_bytes()
    words = read_dictionary(args.dictionary)
    totals: dict[int, dict[str, object]] = {}
    length_totals: dict[int, list[int]] = collections.defaultdict(lambda: [0, 0, 0, 0])
    position_rows = 0
    token_count = 0
    pos = 0
    while pos < len(data):
        item = wrt_code_at(data, pos)
        if item is None:
            pos += 2 if data[pos] == 0x0C and pos + 1 < len(data) else 1
            continue
        code, size = item
        token_count += 1
        bucket = totals.setdefault(
            code,
            {
                "code": code,
                "word": words[code] if code < len(words) else "",
                "token_count": 0,
                "code_bytes": size,
                "ledger_rows": 0,
                "qbits": 0,
                "oracle_gap_qbits": 0,
                "positive_oracle_gap_qbits": 0,
                "first_pos": pos,
                "byte_index_counts": [0, 0, 0, 0],
                "dominant_fields": collections.Counter(),
            },
        )
        bucket["token_count"] = int(bucket["token_count"]) + 1
        for offset in range(size):
            for row in rows_by_pos.get(pos + offset, []):
                position_rows += 1
                gap = qbits(row, "oracle_gap_qbits")
                bucket["ledger_rows"] = int(bucket["ledger_rows"]) + 1
                bucket["qbits"] = int(bucket["qbits"]) + qbits(row, "qbits")
                bucket["oracle_gap_qbits"] = int(bucket["oracle_gap_qbits"]) + gap
                bucket["positive_oracle_gap_qbits"] = int(
                    bucket["positive_oracle_gap_qbits"]
                ) + max(0, gap)
                bucket["byte_index_counts"][offset] += 1  # type: ignore[index]
                bucket["dominant_fields"][row.get("field", "")] += 1  # type: ignore[index]
                lt = length_totals[size]
                lt[0] += 1
                lt[1] += qbits(row, "qbits")
                lt[2] += gap
                lt[3] += max(0, gap)
        pos += size

    ranked = []
    for bucket in totals.values():
        code = int(bucket["code"])
        word = str(bucket["word"])
        token_total = int(bucket["token_count"])
        code_bytes = int(bucket["code_bytes"])
        ledger_rows = int(bucket["ledger_rows"])
        qbit_total = int(bucket["qbits"])
        gap_total = int(bucket["oracle_gap_qbits"])
        pos_gap_total = int(bucket["positive_oracle_gap_qbits"])
        literal_savings = max(0, len(word) - code_bytes) * token_total
        fields = bucket["dominant_fields"].most_common(3)  # type: ignore[union-attr]
        ranked.append(
            {
                "code": code,
                "word": word,
                "token_count": token_total,
                "code_bytes": code_bytes,
                "ledger_rows": ledger_rows,
                "qbits": qbit_total,
                "loss_bits": qbit_total / 256.0,
                "loss_bytes": qbit_total / 2048.0,
                "oracle_gap_bits": gap_total / 256.0,
                "oracle_gap_bytes": gap_total / 2048.0,
                "positive_oracle_gap_bytes": pos_gap_total / 2048.0,
                "literal_byte_savings": literal_savings,
                "loss_per_token_bits": (qbit_total / 256.0 / token_total)
                if token_total
                else 0.0,
                "ledger_row_rate": ledger_rows / token_total if token_total else 0.0,
                "first_pos": int(bucket["first_pos"]),
                "byte_index_counts": bucket["byte_index_counts"],
                "dominant_fields": fields,
            }
        )
    ranked.sort(
        key=lambda item: (
            -float(item["positive_oracle_gap_bytes"]),
            -float(item["loss_bytes"]),
            -int(item["token_count"]),
            int(item["code"]),
        )
    )
    result = {
        "log": str(args.log),
        "store": str(args.store),
        "dictionary": str(args.dictionary),
        "store_bytes": len(data),
        "dictionary_words": len(words),
        "wrt_tokens": token_count,
        "ledger_rows_on_wrt_code_bytes": position_rows,
        "code_count_with_ledger_rows": sum(1 for item in ranked if item["ledger_rows"]),
        "by_code_length": {
            str(length): {
                "ledger_rows": values[0],
                "loss_bits": values[1] / 256.0,
                "oracle_gap_bits": values[2] / 256.0,
                "positive_oracle_gap_bytes": values[3] / 2048.0,
            }
            for length, values in sorted(length_totals.items())
        },
        "top_codes": ranked[: args.top],
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
