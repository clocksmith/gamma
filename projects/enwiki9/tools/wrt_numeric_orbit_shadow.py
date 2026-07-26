#!/usr/bin/env python3
"""Emit a causal exact-WRT numeric-format continuation endpoint.

The endpoint learns only from completed emission groups. While a numeric run
is causally active, it predicts the next exact encoded WRT emission from prior
groups seen in the same bounded formatting state. Everywhere else it copies
the frozen base probability exactly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wrt_wheeler_continuation_oracle import P1Trace, emission_groups, parse_store


NUMERIC_SEPARATORS = b",._:/-"


def digest(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def code_bits(value: bytes) -> tuple[int, ...]:
    return tuple((byte >> shift) & 1 for byte in value for shift in range(7, -1, -1))


class NumericState:
    def __init__(self) -> None:
        self.run = bytearray()

    def key(self) -> tuple[int, int, int, int] | None:
        if not self.run:
            return None
        last = self.run[-1]
        if not (48 <= last <= 57 or last in NUMERIC_SEPARATORS):
            return None
        digits = sum(48 <= value <= 57 for value in self.run)
        separators = 0
        for value in self.run:
            if value in NUMERIC_SEPARATORS:
                separators |= 1 << NUMERIC_SEPARATORS.index(value)
        last_class = 0 if 48 <= last <= 57 else 1 + NUMERIC_SEPARATORS.index(last)
        last_digit = next((value - 48 for value in reversed(self.run) if 48 <= value <= 57), 10)
        return min(digits, 15), last_class, separators, last_digit

    def update(self, decoded: bytes) -> None:
        for value in decoded:
            if 48 <= value <= 57:
                if not self.run:
                    self.run.append(value)
                else:
                    self.run.append(value)
            elif value in NUMERIC_SEPARATORS and self.run:
                self.run.append(value)
            else:
                self.run.clear()


class BoundedTable:
    def __init__(self, max_keys: int, codes_per_key: int) -> None:
        self.rows: OrderedDict[tuple[int, int, int, int], Counter[bytes]] = OrderedDict()
        self.max_keys = max_keys
        self.codes_per_key = codes_per_key
        self.evicted_keys = 0
        self.rejected_codes = 0

    def get(self, key: tuple[int, int, int, int]) -> Counter[bytes] | None:
        row = self.rows.get(key)
        if row is not None:
            self.rows.move_to_end(key)
        return row

    def add(self, key: tuple[int, int, int, int], code: bytes) -> None:
        row = self.rows.get(key)
        if row is None:
            if len(self.rows) >= self.max_keys:
                self.rows.popitem(last=False)
                self.evicted_keys += 1
            row = Counter()
            self.rows[key] = row
        else:
            self.rows.move_to_end(key)
        if code not in row and len(row) >= self.codes_per_key:
            self.rejected_codes += 1
            return
        row[code] += 1


def predicted_p1(
    row: Counter[bytes] | None,
    prefix: tuple[int, ...],
    minimum_support: int,
    cache: dict[bytes, tuple[int, ...]],
) -> tuple[int | None, int]:
    if not row:
        return None, 0
    zero = 0
    one = 0
    offset = len(prefix)
    for code, count in row.items():
        bits = cache.setdefault(code, code_bits(code))
        if len(bits) <= offset or bits[:offset] != prefix:
            continue
        if bits[offset]:
            one += count
        else:
            zero += count
    support = zero + one
    if support < minimum_support:
        return None, support
    probability = int(round(65536.0 * (one + 0.5) / (support + 1.0)))
    return max(1, min(65534, probability)), support


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True)
    parser.add_argument("--dictionary", required=True)
    parser.add_argument("--raw-input", required=True)
    parser.add_argument("--base-p1", required=True)
    parser.add_argument("--output-trace", required=True)
    parser.add_argument("--output-receipt", required=True)
    parser.add_argument("--max-keys", type=int, default=4096)
    parser.add_argument("--codes-per-key", type=int, default=64)
    parser.add_argument("--min-support", type=int, default=2)
    args = parser.parse_args()

    store_path = Path(args.store)
    dictionary_path = Path(args.dictionary)
    raw_path = Path(args.raw_input)
    base_path = Path(args.base_p1)
    output_path = Path(args.output_trace)
    receipt_path = Path(args.output_receipt)

    parsed = parse_store(store_path, dictionary_path)
    raw = raw_path.read_bytes()
    if parsed.decoded != raw:
        raise SystemExit("exact WRT decode does not match raw input")
    groups = emission_groups(parsed)
    trace = P1Trace(base_path)
    state = NumericState()
    table = BoundedTable(args.max_keys, args.codes_per_key)
    bit_cache: dict[bytes, tuple[int, ...]] = {}
    output_path.parent.mkdir(parents=True, exist_ok=True)

    active_groups = 0
    predicted_rows = 0
    supported_rows = 0
    maximum_support = 0
    rows_written = 0
    next_row = 0
    expected_rows = len(parsed.stream) * 8
    with output_path.open("wb") as output:
        output.write(struct.pack("<8sQ", b"CMXAUX1\0", expected_rows))
        for group in groups:
            group_start_row = group.start * 8
            while next_row < group_start_row:
                base = trace.p1(next_row)
                output.write(struct.pack("<HH", base, base))
                rows_written += 1
                next_row += 1
            key = state.key()
            row = table.get(key) if key is not None else None
            actual_bits = bit_cache.setdefault(group.encoded, code_bits(group.encoded))
            if key is not None:
                active_groups += 1
            prefix: tuple[int, ...] = ()
            for bit_index, actual_bit in enumerate(actual_bits):
                base = trace.p1(group.start * 8 + bit_index)
                auxiliary, support = predicted_p1(row, prefix, args.min_support, bit_cache)
                if key is not None:
                    predicted_rows += 1
                if auxiliary is None:
                    auxiliary = base
                else:
                    supported_rows += 1
                    maximum_support = max(maximum_support, support)
                output.write(struct.pack("<HH", base, auxiliary))
                rows_written += 1
                next_row += 1
                prefix += (actual_bit,)
            if key is not None:
                table.add(key, group.encoded)
            state.update(group.decoded)
        while next_row < expected_rows:
            base = trace.p1(next_row)
            output.write(struct.pack("<HH", base, base))
            rows_written += 1
            next_row += 1
    trace.close()

    if rows_written != expected_rows:
        raise SystemExit(f"row mismatch: wrote {rows_written}, expected {expected_rows}")

    receipt = {
        "schema": "wrt_numeric_orbit_shadow_v1",
        "evidence_level": "causal_exact_wrt_probability_trace",
        "claim_boundary": (
            "Probability trace only. Exact arithmetic replay, source cost, native integration, "
            "roundtrip, resources, transfer, and full-corpus accounting remain required."
        ),
        "identity": {
            "raw_matches_exact_wrt_decode": True,
            "base_rows_copied_outside_supported_numeric_state": True,
            "table_updates_after_completed_emission_group": True,
            "current_group_prefix_uses_prior_bits_only": True,
        },
        "inputs": {
            "store": digest(store_path),
            "dictionary": digest(dictionary_path),
            "raw_input": digest(raw_path),
            "base_p1": digest(base_path),
        },
        "scope": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(parsed.stream),
            "rows": rows_written,
            "emission_groups": len(groups),
            "numeric_active_groups": active_groups,
            "numeric_active_rows": predicted_rows,
            "supported_numeric_rows": supported_rows,
        },
        "model": {
            "table_keys": len(table.rows),
            "stored_codes": sum(len(row) for row in table.rows.values()),
            "max_keys": args.max_keys,
            "codes_per_key": args.codes_per_key,
            "minimum_support": args.min_support,
            "maximum_prefix_support": maximum_support,
            "evicted_keys": table.evicted_keys,
            "rejected_codes": table.rejected_codes,
        },
        "output": digest(output_path),
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"scope": receipt["scope"], "model": receipt["model"]}, sort_keys=True))


if __name__ == "__main__":
    main()
