#!/usr/bin/env python3
"""Verify rational box containment in quantizer polyhedra."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def rational(value: object) -> Fraction:
    if not isinstance(value, (str, int)):
        raise ValueError(f"invalid rational: {value!r}")
    return Fraction(value)


def maximum_linear(coefficients: list[Fraction], box: list[tuple[Fraction, Fraction]]) -> Fraction:
    if len(coefficients) != len(box):
        raise ValueError("coefficient and box dimensions differ")
    total = Fraction(0)
    for coefficient, (lower, upper) in zip(coefficients, box, strict=True):
        if lower > upper:
            raise ValueError("box lower endpoint exceeds upper endpoint")
        total += coefficient * (upper if coefficient >= 0 else lower)
    return total


def verify_row(row: dict[str, object]) -> dict[str, object]:
    raw_box = row.get("box")
    raw_constraints = row.get("constraints")
    if not isinstance(raw_box, list) or not isinstance(raw_constraints, list):
        raise ValueError("row requires box and constraints arrays")
    box: list[tuple[Fraction, Fraction]] = []
    for interval in raw_box:
        if not isinstance(interval, list) or len(interval) != 2:
            raise ValueError("box interval must contain two rationals")
        box.append((rational(interval[0]), rational(interval[1])))

    faces: list[dict[str, object]] = []
    passed = True
    for constraint in raw_constraints:
        if not isinstance(constraint, dict):
            raise ValueError("constraint must be an object")
        raw_coefficients = constraint.get("coefficients")
        if not isinstance(raw_coefficients, list):
            raise ValueError("constraint coefficients must be an array")
        coefficients = [rational(value) for value in raw_coefficients]
        bound = rational(constraint.get("bound"))
        strict = bool(constraint.get("strict", False))
        maximum = maximum_linear(coefficients, box)
        face_passed = maximum < bound if strict else maximum <= bound
        passed = passed and face_passed
        faces.append(
            {
                "bound": str(bound),
                "maximum": str(maximum),
                "passed": face_passed,
                "strict": strict,
            }
        )
    return {
        "cell_id": row.get("cell_id"),
        "faces": faces,
        "passed": passed,
    }


def self_test() -> None:
    passing = {
        "cell_id": "middle",
        "box": [["49/100", "51/100"], ["1/5", "1/4"]],
        "constraints": [
            {"coefficients": ["1", "0"], "bound": "3/5", "strict": True},
            {"coefficients": ["-1", "0"], "bound": "-2/5"},
            {"coefficients": ["0", "1"], "bound": "1/4"},
        ],
    }
    failing = {
        "cell_id": "strict-boundary",
        "box": [["1/2", "3/5"]],
        "constraints": [
            {"coefficients": ["1"], "bound": "3/5", "strict": True}
        ],
    }
    assert verify_row(passing)["passed"] is True
    assert verify_row(failing)["passed"] is False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print('{"self_test":"pass"}')
        return 0
    if args.input is None or args.receipt is None:
        parser.error("--input and --receipt are required without --self-test")

    source = args.input.read_bytes()
    document = json.loads(source)
    rows = document.get("rows")
    if not isinstance(rows, list):
        raise ValueError("input requires a rows array")
    results = [verify_row(row) for row in rows]
    passed = all(bool(result["passed"]) for result in results)
    receipt = {
        "input_sha256": hashlib.sha256(source).hexdigest(),
        "passed": passed,
        "row_count": len(results),
        "rows": results,
        "schema": "polyhedral_probability_cell_certificate_v1",
        "score_credit_bytes": 0,
    }
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
