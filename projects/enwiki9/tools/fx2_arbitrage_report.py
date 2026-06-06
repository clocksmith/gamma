#!/usr/bin/env python3
"""Rank FX2 loss-ledger families against a concrete score gap."""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
from typing import Iterable

PAIR_RE = re.compile(r"([A-Za-z_]+)=([^ ]+)")
PREFIX = "FX2_LOSS_LEDGER "

DEFAULT_FAMILIES = {
    "oracle_group": ["oracle_group"],
    "byte_class": ["byte_class"],
    "struct_byte": ["field", "slot", "template_depth", "template_arg", "byte_class"],
    "wrt_prefix": [
        "field",
        "template_depth",
        "wrt_state",
        "wrt_first",
        "wrt_second",
        "byte_class",
    ],
    "xml_numeric": ["xml_depth", "in_tag", "numeric_class", "byte_class"],
    "template_hash": ["template_hash", "template_arg", "byte_class"],
    "oracle_struct": ["oracle_group", "field", "template_depth", "byte_class"],
}


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


def qbits(row: dict[str, str], key: str) -> int:
    value = as_int(row, key)
    if key == "oracle_gap_qbits":
        return max(0, value)
    return value


def row_stride(row: dict[str, str], fallback: int) -> int:
    return max(1, as_int(row, "ledger_stride", fallback))


def read_rows(path: pathlib.Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", errors="replace") as f:
        for line in f:
            row = parse_row(line)
            if row is not None:
                rows.append(row)
    rows.sort(key=lambda row: as_int(row, "pos"))
    return rows


def key_dict(fields: list[str], key: tuple[str, ...]) -> dict[str, str]:
    return {field: value for field, value in zip(fields, key)}


def hint_for(fields: list[str], key: tuple[str, ...]) -> str:
    values = key_dict(fields, key)
    byte_class = values.get("byte_class", "")
    if any(field.startswith("wrt_") for field in fields) or byte_class == "14":
        return "wrt_byte_prediction"
    if values.get("numeric_class", "0") not in ("", "0"):
        return "numeric_context"
    if values.get("template_hash", "0") not in ("", "0"):
        return "template_local_context"
    if values.get("in_tag", "0") == "1" or values.get("xml_depth", "0") not in ("", "0"):
        return "xml_boundary_context"
    if values.get("oracle_group") in ("match", "indirect_ns", "fxcm"):
        return "model_selection_context"
    return "generic_predictor_context"


def hint_for_row(row: dict[str, str]) -> str:
    byte_class = row.get("byte_class", "")
    if row.get("wrt_state", "0") != "0" or byte_class == "14":
        return "wrt_byte_prediction"
    if row.get("numeric_class", "0") not in ("", "0"):
        return "numeric_context"
    if row.get("template_hash", "0") not in ("", "0"):
        return "template_local_context"
    if row.get("in_tag", "0") == "1" or row.get("xml_depth", "0") not in ("", "0"):
        return "xml_boundary_context"
    if row.get("oracle_group") in ("match", "indirect_ns", "fxcm"):
        return "model_selection_context"
    return "generic_predictor_context"


def group_rows(
    rows: Iterable[dict[str, str]],
    fields: list[str],
    fallback_stride: int,
    required_bytes: float,
    scope_scale: float,
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
    for key, (count, loss_qbits, gap_qbits, est_gap_qbits) in totals.items():
        estimated_gap_bytes = est_gap_qbits / 2048.0
        extrapolated_gap_bytes = estimated_gap_bytes * scope_scale
        ranked.append(
            {
                "key": key_dict(fields, key),
                "rows": count,
                "observed_loss_bits": loss_qbits / 256.0,
                "observed_oracle_gap_bytes": gap_qbits / 2048.0,
                "estimated_oracle_gap_bytes": estimated_gap_bytes,
                "extrapolated_oracle_gap_bytes": extrapolated_gap_bytes,
                "required_gap_fraction": (
                    extrapolated_gap_bytes / required_bytes if required_bytes else 0.0
                ),
                "hint": hint_for(fields, key),
            }
        )
    ranked.sort(
        key=lambda item: (
            -float(item["extrapolated_oracle_gap_bytes"]),
            -float(item["estimated_oracle_gap_bytes"]),
            -float(item["observed_loss_bits"]),
        )
    )
    return ranked[:limit]


def concentration(items: list[dict[str, object]], total_gap: float) -> list[dict[str, object]]:
    if not total_gap:
        return items
    out = []
    for item in items:
        clone = dict(item)
        clone["share_of_total_gap"] = (
            float(item["extrapolated_oracle_gap_bytes"]) / total_gap
        )
        out.append(clone)
    return out


def parse_family(spec: str) -> tuple[str, list[str]]:
    if ":" in spec:
        name, fields = spec.split(":", 1)
        parsed = [field for field in fields.split(",") if field]
        if not name or not parsed:
            raise SystemExit(f"invalid family spec: {spec}")
        return name, parsed
    if spec not in DEFAULT_FAMILIES:
        raise SystemExit(f"unknown family: {spec}")
    return spec, DEFAULT_FAMILIES[spec]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=pathlib.Path)
    ap.add_argument("--output", type=pathlib.Path)
    ap.add_argument("--sample-stride", type=int, default=1)
    ap.add_argument("--scope-bytes", type=int, default=0)
    ap.add_argument("--required-bytes", type=float, default=0.0)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument(
        "--family",
        action="append",
        default=[],
        help=(
            "family name or name:field,field. Defaults to oracle, structural, "
            "WRT, XML, and template-hash groupings."
        ),
    )
    args = ap.parse_args()

    rows = read_rows(args.log)
    if not rows:
        raise SystemExit("no FX2_LOSS_LEDGER rows found")

    fallback_stride = max(1, args.sample_stride)
    first_pos = as_int(rows[0], "pos")
    last_pos = as_int(rows[-1], "pos")
    covered_span = max(1, last_pos - first_pos + 1)
    scope_bytes = args.scope_bytes if args.scope_bytes > 0 else covered_span
    scope_scale = scope_bytes / covered_span

    observed_loss_qbits = sum(qbits(row, "qbits") for row in rows)
    observed_gap_qbits = sum(qbits(row, "oracle_gap_qbits") for row in rows)
    estimated_gap_qbits = sum(
        qbits(row, "oracle_gap_qbits") * row_stride(row, fallback_stride)
        for row in rows
    )
    estimated_gap_bytes = estimated_gap_qbits / 2048.0
    extrapolated_gap_bytes = estimated_gap_bytes * scope_scale

    families = [parse_family(spec) for spec in args.family]
    if not families:
        families = list(DEFAULT_FAMILIES.items())

    grouped = {
        name: concentration(
            group_rows(
                rows,
                fields,
                fallback_stride,
                args.required_bytes,
                scope_scale,
                args.top,
            ),
            extrapolated_gap_bytes,
        )
        for name, fields in families
    }

    hint_totals: dict[str, float] = collections.defaultdict(float)
    for row in rows:
        hint_totals[hint_for_row(row)] += (
            qbits(row, "oracle_gap_qbits")
            * row_stride(row, fallback_stride)
            / 2048.0
            * scope_scale
        )
    hint_rank = [
        {
            "hint": hint,
            "extrapolated_oracle_gap_bytes": gap,
            "required_gap_fraction": gap / args.required_bytes
            if args.required_bytes
            else 0.0,
        }
        for hint, gap in sorted(hint_totals.items(), key=lambda item: -item[1])
    ]

    result = {
        "log": str(args.log),
        "rows": len(rows),
        "first_pos": first_pos,
        "last_pos": last_pos,
        "covered_span_bytes": covered_span,
        "scope_bytes": scope_bytes,
        "coverage_fraction": min(1.0, covered_span / scope_bytes)
        if scope_bytes
        else 1.0,
        "sample_stride_fallback": fallback_stride,
        "observed_loss_bits": observed_loss_qbits / 256.0,
        "observed_positive_oracle_gap_bytes": observed_gap_qbits / 2048.0,
        "estimated_positive_oracle_gap_bytes": estimated_gap_bytes,
        "extrapolated_positive_oracle_gap_bytes": extrapolated_gap_bytes,
        "required_bytes": args.required_bytes,
        "required_gap_fraction": extrapolated_gap_bytes / args.required_bytes
        if args.required_bytes
        else 0.0,
        "coverage_warning": (
            "Log rows cover a prefix smaller than the requested scope; "
            "extrapolated values are directional attribution, not score proof."
            if covered_span < scope_bytes
            else ""
        ),
        "hint_rank": hint_rank,
        "families": grouped,
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
