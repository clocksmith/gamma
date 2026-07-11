#!/usr/bin/env python3
"""Rebuild the exact WRT byte stream from an all-bit FX2 residual cache."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cache", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--receipt", type=pathlib.Path)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    positions = 0
    alignment_checks = 0
    current_pos = -1
    prefix = 0
    next_bit_pos = 0
    previous_byte: int | None = None
    digest = hashlib.sha256()

    with args.cache.open("r", newline="") as source, args.output.open("wb") as out:
        reader = csv.reader(source, delimiter="\t")
        header = next(reader)
        indexes = {name: header.index(name) for name in ("pos", "bit_pos", "bit")}
        stream_index = header.index("wrt_stream_byte")
        for values in reader:
            pos = int(values[indexes["pos"]])
            bit_pos = int(values[indexes["bit_pos"]])
            bit = int(values[indexes["bit"]])
            if pos != current_pos:
                if current_pos >= 0 and next_bit_pos != 8:
                    raise SystemExit(f"incomplete byte at position {current_pos}")
                if pos != current_pos + 1:
                    raise SystemExit(f"noncontiguous position {pos} after {current_pos}")
                if previous_byte is not None:
                    logged = int(values[stream_index]) & 0xFF
                    if logged != previous_byte:
                        raise SystemExit(
                            f"WRT alignment mismatch at {pos}: {logged} != {previous_byte}"
                        )
                    alignment_checks += 1
                current_pos = pos
                prefix = 0
                next_bit_pos = 0
            if bit_pos != next_bit_pos or bit not in (0, 1):
                raise SystemExit(
                    f"invalid bit sequence at position {pos}: {bit_pos} after {next_bit_pos}"
                )
            prefix = ((prefix << 1) | bit) & 0xFF
            next_bit_pos += 1
            rows += 1
            if next_bit_pos == 8:
                out.write(bytes((prefix,)))
                digest.update(bytes((prefix,)))
                previous_byte = prefix
                positions += 1
        if current_pos >= 0 and next_bit_pos != 8:
            raise SystemExit(f"incomplete final byte at position {current_pos}")

    payload = {
        "receipt_type": "wrt_trace_extract",
        "input": str(args.cache),
        "output": str(args.output),
        "rows": rows,
        "output_bytes": positions,
        "alignment_checks": alignment_checks,
        "alignment_ok": alignment_checks == max(0, positions - 1),
        "sha256": digest.hexdigest(),
    }
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
