#!/usr/bin/env python3
"""Verify the native HORIZON exact-arithmetic fixture with Python integers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


WEIGHT_TOTAL = 1 << 63
PROBABILITY_SCALE = 65_536
REDUCED_PROBABILITY_SCALE = 16
SCHEMA = "gamma.enwiki9.horizon-exact-arithmetic-verification.v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def round_half_up_ratio(numerator: int, denominator: int, total: int) -> int:
    quotient, remainder = divmod(numerator * total, denominator)
    if 2 * remainder >= denominator:
        quotient += 1
    return max(1, min(total - 1, quotient))


def mix_count(total: int, probability_scale: int, weight: int,
              parent_count: int, candidate_count: int) -> int:
    numerator = weight * parent_count + (total - weight) * candidate_count
    quotient, remainder = divmod(numerator, total)
    if 2 * remainder >= total:
        quotient += 1
    return max(1, min(probability_scale - 1, quotient))


def parse_wide(value: str) -> int:
    high, low = (int(part) for part in value.split(":"))
    if not (0 <= high < 1 << 64 and 0 <= low < 1 << 64):
        raise ValueError("wide integer limb is outside uint64")
    return (high << 64) | low


def expected_boundaries() -> dict[str, int]:
    return {
        "D:half_at_zero": 1,
        "D:one_and_half": 2,
        "D:half_below_total": WEIGHT_TOTAL - 1,
        "D:minimum_ratio": 1,
        "D:maximum_ratio": WEIGHT_TOTAL - 1,
        "P:equal_low": WEIGHT_TOTAL // 2,
        "P:equal_high": WEIGHT_TOTAL // 2,
        "P:candidate_wins": WEIGHT_TOTAL // 65_536,
        "P:parent_wins": WEIGHT_TOTAL - WEIGHT_TOTAL // 65_536,
        "P:low_clamp": 1,
        "P:high_clamp": WEIGHT_TOTAL - 1,
        "M:parent_low": 1,
        "M:candidate_low": 1,
        "M:equal_counts": 32_768,
        "M:half_up": 2,
    }


def verify(native: Path) -> dict[str, Any]:
    boundaries = expected_boundaries()
    seen_boundaries: set[str] = set()
    reduced_rows = 0
    expected_reduced_rows = 0
    for bits in range(2, 9):
        expected_reduced_rows += ((1 << bits) - 1) * 15 * 15 * 2

    with native.open("r", encoding="ascii", newline="") as stream:
        header = stream.readline()
        if header != "H horizon-exact-arithmetic-fixture-v1\n":
            raise ValueError("native fixture header mismatch")
        for line_number, raw in enumerate(stream, 2):
            if not raw.endswith("\n"):
                raise ValueError(f"line {line_number}: unterminated row")
            row = raw.split()
            if not row:
                raise ValueError(f"line {line_number}: empty row")
            kind = row[0]
            if kind == "D" and len(row) == 5:
                key = f"D:{row[1]}"
                numerator = parse_wide(row[2])
                denominator = parse_wide(row[3])
                observed = int(row[4])
                expected = round_half_up_ratio(
                    numerator, denominator, WEIGHT_TOTAL
                )
            elif kind == "P" and len(row) == 6:
                key = f"P:{row[1]}"
                weight, parent_truth, candidate_truth, observed = (
                    int(value) for value in row[2:]
                )
                parent_mass = weight * parent_truth
                denominator = (
                    parent_mass + (WEIGHT_TOTAL - weight) * candidate_truth
                )
                expected = round_half_up_ratio(
                    parent_mass, denominator, WEIGHT_TOTAL
                )
            elif kind == "M" and len(row) == 6:
                key = f"M:{row[1]}"
                weight, parent_count, candidate_count, observed = (
                    int(value) for value in row[2:]
                )
                expected = mix_count(
                    WEIGHT_TOTAL, PROBABILITY_SCALE, weight,
                    parent_count, candidate_count
                )
            elif kind == "R" and len(row) == 8:
                (
                    bits,
                    weight,
                    parent_count,
                    candidate_count,
                    truth,
                    observed_mix,
                    observed_posterior,
                ) = (int(value) for value in row[1:])
                total = 1 << bits
                expected_mix = mix_count(
                    total, REDUCED_PROBABILITY_SCALE, weight,
                    parent_count, candidate_count
                )
                parent_truth = (
                    parent_count if truth else
                    REDUCED_PROBABILITY_SCALE - parent_count
                )
                candidate_truth = (
                    candidate_count if truth else
                    REDUCED_PROBABILITY_SCALE - candidate_count
                )
                parent_mass = weight * parent_truth
                expected_posterior = round_half_up_ratio(
                    parent_mass,
                    parent_mass + (total - weight) * candidate_truth,
                    total,
                )
                if (observed_mix, observed_posterior) != (
                    expected_mix, expected_posterior
                ):
                    raise ValueError(f"line {line_number}: reduced row mismatch")
                reduced_rows += 1
                continue
            else:
                raise ValueError(f"line {line_number}: malformed row")

            if key not in boundaries or key in seen_boundaries:
                raise ValueError(f"line {line_number}: unexpected boundary {key}")
            if observed != expected or observed != boundaries[key]:
                raise ValueError(f"line {line_number}: boundary mismatch {key}")
            seen_boundaries.add(key)

    terminal_pass = (
        seen_boundaries == set(boundaries)
        and reduced_rows == expected_reduced_rows
    )
    return {
        "schema": SCHEMA,
        "candidate_id": "endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3",
        "native_fixture": {
            "path": str(native.resolve()),
            "bytes": native.stat().st_size,
            "sha256": sha256(native),
        },
        "weight_total": WEIGHT_TOTAL,
        "initial_parent_weight": WEIGHT_TOTAL // 2,
        "rounding": "nearest_exact_halves_upward",
        "full_scale_boundary_count": len(seen_boundaries),
        "exhaustive_reduced_row_count": reduced_rows,
        "expected_exhaustive_reduced_row_count": expected_reduced_rows,
        "arbitrary_precision_identity_pass": terminal_pass,
        "terminal_pass": terminal_pass,
        "archive_authority": False,
        "score_credit_bytes": 0,
    }


def write_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite {path}")
    payload = json.dumps(value, indent=2, sort_keys=True).encode("ascii") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        cursor = 0
        while cursor < len(payload):
            written = os.write(descriptor, payload[cursor:])
            if written <= 0:
                raise OSError("short write")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    receipt = verify(Path(args.native))
    write_new(Path(args.receipt), receipt)
    return 0 if receipt["terminal_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
