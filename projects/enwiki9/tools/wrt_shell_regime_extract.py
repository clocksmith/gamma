#!/usr/bin/env python3
"""Extract one causal structural-regime byte per exact WRT probability row."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


FIELDS = (
    "pos",
    "bit_pos",
    "wrt_page_mode",
    "wrt_title_mode",
    "wrt_prose_mode",
    "wrt_ref_mode",
    "wrt_url_mode",
    "wrt_table_mode",
    "wrt_list_mode",
    "wrt_template_depth",
    "wrt_section_state",
)

def classify(values: list[str], indexes: dict[str, int]) -> int:
    def active(name: str) -> bool:
        return int(values[indexes[name]]) != 0

    fields = (
        "wrt_page_mode",
        "wrt_title_mode",
        "wrt_prose_mode",
        "wrt_ref_mode",
        "wrt_url_mode",
        "wrt_table_mode",
        "wrt_list_mode",
        "wrt_template_depth",
    )
    mask = 0
    for bit, name in enumerate(fields):
        mask |= int(active(name)) << bit
    return mask


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    counts: Counter[int] = Counter()
    rows = 0
    previous_pos = -1
    previous_bit_pos = 7
    with args.cache.open("r", encoding="utf-8", newline="") as source:
        header = source.readline().rstrip("\n").split("\t")
        indexes = {name: header.index(name) for name in FIELDS}
        with args.output.open("wb") as output:
            for line in source:
                values = line.rstrip("\n").split("\t")
                pos = int(values[indexes["pos"]])
                bit_pos = int(values[indexes["bit_pos"]])
                if bit_pos != (previous_bit_pos + 1) % 8:
                    raise ValueError(f"noncausal bit order at row {rows}")
                if bit_pos == 0 and pos != previous_pos + 1:
                    raise ValueError(f"noncontiguous WRT position at row {rows}")
                if bit_pos != 0 and pos != previous_pos:
                    raise ValueError(f"position changed within byte at row {rows}")
                regime = classify(values, indexes)
                payload = bytes((regime,))
                output.write(payload)
                digest.update(payload)
                counts[regime] += 1
                rows += 1
                previous_pos = pos
                previous_bit_pos = bit_pos

    receipt = {
        "schema_version": 1,
        "receipt_type": "wrt_shell_regime_extract",
        "claim_boundary": (
            "Causal state extraction from an observation trace. The sidecar is a "
            "research alignment artifact, not submission payload or score evidence."
        ),
        "input": str(args.cache),
        "output": str(args.output),
        "rows": rows,
        "bytes": args.output.stat().st_size,
        "sha256": digest.hexdigest(),
        "mask_bits": [
            "page",
            "title",
            "prose",
            "reference",
            "url",
            "table",
            "list",
            "template",
        ],
        "regime_counts": {
            f"0x{index:02x}": counts[index] for index in sorted(counts)
        },
    }
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
