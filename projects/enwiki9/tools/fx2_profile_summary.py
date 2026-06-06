#!/usr/bin/env python3
"""Summarize FX2_LOSS_PROFILE stderr output."""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

PAIR_RE = re.compile(r"([A-Za-z_]+)=([^ ]+)")
PREFIX = "FX2_LOSS_PROFILE "


def parse_pairs(payload: str) -> dict[str, str]:
    return {key: value for key, value in PAIR_RE.findall(payload)}


def as_float(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "0"))
    except ValueError:
        return 0.0


def as_int(row: dict[str, str], key: str) -> int:
    try:
        return int(float(row.get(key, "0")))
    except ValueError:
        return 0


def read_profile(path: pathlib.Path) -> tuple[dict[str, str] | None, list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    total: dict[str, str] | None = None
    buckets: list[dict[str, str]] = []
    models: list[dict[str, str]] = []
    hotspots: list[dict[str, str]] = []
    with path.open("r", errors="replace") as f:
        for line in f:
            if PREFIX not in line:
                continue
            payload = line.split(PREFIX, 1)[1].strip()
            row = parse_pairs(payload)
            if not row:
                continue
            if payload.startswith("total "):
                total = row
            elif "model_group" in row:
                models.append(row)
            elif "rank" in row and "pos" in row:
                hotspots.append(row)
            else:
                buckets.append(row)
    return total, buckets, models, hotspots


def bucket_name(row: dict[str, str]) -> tuple[str, str]:
    for key in row:
        if key not in {"bytes", "bits", "bpb"}:
            return key, row[key]
    return "", ""


def print_total(total: dict[str, str] | None) -> None:
    if total is None:
        return
    print(
        "total\tbytes\tbits\tbpb\toracle_bits\toracle_bpb\toracle_gap\tcoded_bits"
    )
    print(
        "total\t{bytes}\t{bits}\t{bpb}\t{oracle_bits}\t{oracle_bpb}\t"
        "{oracle_gap}\t{coded_bits}".format(**total)
    )


def print_buckets(buckets: list[dict[str, str]], top: int, oracle_only: bool) -> None:
    rows = []
    for row in buckets:
        name, idx = bucket_name(row)
        if oracle_only and not name.startswith("oracle_gap_"):
            continue
        if not oracle_only and name.startswith("oracle_gap_"):
            continue
        rows.append((as_float(row, "bits"), name, idx, row))
    rows.sort(key=lambda item: (-item[0], item[1], item[2]))
    title = "oracle_bucket" if oracle_only else "bucket"
    print(f"{title}\tname\tidx\tbytes\tbits\tbpb")
    for _bits, name, idx, row in rows[:top]:
        print(
            f"{title}\t{name}\t{idx}\t{row.get('bytes', '')}\t"
            f"{row.get('bits', '')}\t{row.get('bpb', '')}"
        )


def print_models(models: list[dict[str, str]], top: int) -> None:
    rows = sorted(
        models,
        key=lambda row: (-as_int(row, "wins"), as_float(row, "bits")),
    )
    print("model\tgroup\tcoded_bits\tbits\tbyte_equiv_bpb\tbit_avg\twins")
    for row in rows[:top]:
        print(
            f"model\t{row.get('model_group', '')}\t{row.get('coded_bits', '')}\t"
            f"{row.get('bits', '')}\t{row.get('byte_equiv_bpb', '')}\t"
            f"{row.get('bit_avg', '')}\t{row.get('wins', '')}"
        )


def print_hotspots(hotspots: list[dict[str, str]], top: int) -> None:
    rows = sorted(hotspots, key=lambda row: (-as_float(row, "bits"), as_int(row, "pos")))
    print(
        "hotspot\trank\tpos\tbyte\tbits\toracle_gap\tfield\tslot\tdepth\t"
        "arg\tclass\twrt_state\toracle_group\tdominant_model"
    )
    for row in rows[:top]:
        print(
            f"hotspot\t{row.get('rank', '')}\t{row.get('pos', '')}\t"
            f"{row.get('byte', '')}\t{row.get('bits', '')}\t"
            f"{row.get('oracle_gap', '')}\t{row.get('field', '')}\t"
            f"{row.get('slot', '')}\t{row.get('template_depth', '')}\t"
            f"{row.get('template_arg', '')}\t{row.get('byte_class', '')}\t"
            f"{row.get('wrt_state', '')}\t{row.get('oracle_group', '')}\t"
            f"{row.get('dominant_model', '')}"
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=pathlib.Path)
    ap.add_argument("--top", type=int, default=30)
    args = ap.parse_args()

    total, buckets, models, hotspots = read_profile(args.log)
    if total is None and not buckets and not models and not hotspots:
        print("no FX2_LOSS_PROFILE rows found", file=sys.stderr)
        return 1
    print_total(total)
    print_buckets(buckets, args.top, oracle_only=False)
    print_buckets(buckets, args.top, oracle_only=True)
    print_models(models, args.top)
    print_hotspots(hotspots, args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
