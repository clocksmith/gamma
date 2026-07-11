#!/usr/bin/env python3
"""Build a compact TSV cache from FX2_RESIDUAL_ROW logs.

The residual probe logs are useful but noisy: they mix progress output with
per-bit rows. This tool extracts just the numeric causal fields needed by
offline shadow tools. The emitted TSV is accepted by fx2_shadow_residual_coder's
row parser and can be reused by I-SSA/MWCC searches without rescanning stderr.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
from collections import Counter
from typing import Any

from fx2_shadow_residual_coder import TOTAL, as_int, iter_rows


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_FIELDS = (
    "pos",
    "bit_pos",
    "bit",
    "p1",
    "baseline_qbits",
    "field",
    "mode",
    "slot",
    "page_kind",
    "char_class",
    "template_depth",
    "in_tag",
    "ref",
    "url",
    "number_class",
    "word_len",
    "col_bucket",
    "page_bucket",
    "category_state",
    "template_arg",
    "link_recency",
    "title_hash",
    "template_hash",
    "link_hash",
    "entity_hash",
    "word_hash",
    "pair_sig",
    "wrt_stream_byte",
    "wrt_token_class",
    "wrt_token_id",
    "wrt_dictionary_hit_type",
    "wrt_literal_phase",
    "wrt_decoded_chars",
    "wrt_page_boundary",
    "wrt_page_mode",
    "wrt_title_mode",
    "wrt_prose_mode",
    "wrt_ref_mode",
    "wrt_url_mode",
    "wrt_table_mode",
    "wrt_list_mode",
    "wrt_template_depth",
    "wrt_number_class",
    "wrt_section_state",
    "wrt_section_level",
    "wrt_title_hash",
    "wrt_template_hash",
    "wrt_ref_hash",
    "wrt_section_hash",
    "wrt_reconstructed_bytes",
)


def value_for(row: dict[str, Any], field: str) -> int:
    return as_int(row, field, default=0)


def build_cache(args: argparse.Namespace) -> dict[str, Any]:
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output)
    fields = tuple(args.fields.split(",")) if args.fields else DEFAULT_FIELDS
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = 0
    skipped = 0
    bit_counts: Counter[int] = Counter()
    field_counts: Counter[int] = Counter()
    mode_counts: Counter[int] = Counter()
    min_pos: int | None = None
    max_pos: int | None = None

    with output_path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(fields)
        for row in iter_rows(input_path):
            bit = as_int(row, "bit", default=-1)
            p1 = as_int(row, "p1", default=0)
            if bit not in (0, 1) or not (0 < p1 < TOTAL):
                skipped += 1
                continue
            pos = as_int(row, "pos", default=0)
            min_pos = pos if min_pos is None else min(min_pos, pos)
            max_pos = pos if max_pos is None else max(max_pos, pos)
            bit_counts[bit] += 1
            field_counts[as_int(row, "field", default=0)] += 1
            mode_counts[as_int(row, "mode", default=0)] += 1
            writer.writerow([value_for(row, field) for field in fields])
            rows += 1
            if args.max_rows > 0 and rows >= args.max_rows:
                break

    summary = {
        "input": str(input_path),
        "output": str(output_path),
        "rows": rows,
        "skipped": skipped,
        "fields": list(fields),
        "min_pos": min_pos,
        "max_pos": max_pos,
        "bit_counts": {str(key): value for key, value in sorted(bit_counts.items())},
        "top_fields": field_counts.most_common(16),
        "top_modes": mode_counts.most_common(16),
    }
    if args.summary:
        pathlib.Path(args.summary).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract compact TSV residual rows.")
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary")
    parser.add_argument("--fields", help="comma-separated output field list")
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if args.max_rows < 0:
        raise SystemExit("--max-rows must be non-negative")

    summary = build_cache(args)
    if args.print_summary:
        print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
