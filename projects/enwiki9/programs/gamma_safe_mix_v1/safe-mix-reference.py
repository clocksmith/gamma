#!/usr/bin/env python3
"""Exact integer oracle for gamma_safe_mix_v1; never grants archive authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterator, TextIO


SCHEMA = "gamma.enwiki9.safe-mix-integer-reference-receipt.v1"
WEIGHT_TOTAL = 9_223_372_036_854_775_807
INITIAL_PARENT_WEIGHT = 4_611_686_018_427_387_903
MAX_EVENTS = 65_536


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def exact_int(value: Any, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def round_ties_to_even(numerator: int, denominator: int) -> int:
    if numerator < 0 or denominator <= 0:
        raise ValueError("rounding operands are outside the nonnegative contract")
    quotient, remainder = divmod(numerator, denominator)
    twice = remainder * 2
    if twice > denominator or (twice == denominator and quotient & 1):
        quotient += 1
    return quotient


def q63_mix_count(parent_weight: int, parent_count: int, treatment_count: int, scale: int) -> int:
    numerator = parent_weight * parent_count + (WEIGHT_TOTAL - parent_weight) * treatment_count
    mixed = round_ties_to_even(numerator, WEIGHT_TOTAL)
    return min(scale - 1, max(1, mixed))


def q63_update(parent_weight: int, parent_truth: int, treatment_truth: int) -> int:
    parent_mass = parent_weight * parent_truth
    treatment_mass = (WEIGHT_TOTAL - parent_weight) * treatment_truth
    updated = round_ties_to_even(
        WEIGHT_TOTAL * parent_mass,
        parent_mass + treatment_mass,
    )
    return min(WEIGHT_TOTAL - 1, max(1, updated))


def rows(stream: TextIO, label: str) -> Iterator[tuple[int, dict[str, Any]]]:
    for line_number, raw in enumerate(stream, 1):
        if not raw.strip():
            raise ValueError(f"{label}:{line_number}: blank rows are forbidden")
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError(f"{label}:{line_number}: row must be an object")
        yield line_number, value


def write_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=False)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(canonical(value))
    os.replace(temporary, path)


def evaluate(input_path: Path, native_path: Path | None) -> dict[str, Any]:
    input_digest = hashlib.sha256()
    trace_digest = hashlib.sha256()
    parent_weight = INITIAL_PARENT_WEIGHT
    parent_sequence_numerator = 1
    treatment_sequence_numerator = 1
    common_scale_power = 1
    scale: int | None = None
    event_count = 0
    bookkeeping_neutrality = True
    native_identity: bool | None = None if native_path is None else True

    native_stream = native_path.open("r", encoding="ascii") if native_path is not None else None
    native_iterator = rows(native_stream, str(native_path)) if native_stream is not None else None
    try:
        with input_path.open("r", encoding="ascii") as stream:
            for line_number, value in rows(stream, str(input_path)):
                raw = canonical(value)
                input_digest.update(raw)
                event_scale = exact_int(value.get("scale"), f"input:{line_number}.scale", 3)
                parent_count = exact_int(value.get("parent_count"), f"input:{line_number}.parent_count", 1)
                treatment_count = exact_int(value.get("treatment_count"), f"input:{line_number}.treatment_count", 1)
                truth = value.get("truth")
                if not isinstance(truth, bool):
                    raise ValueError(f"input:{line_number}.truth must be boolean")
                if parent_count >= event_scale or treatment_count >= event_scale:
                    raise ValueError(f"input:{line_number}: counts must be in [1,C-1]")
                if scale is None:
                    scale = event_scale
                elif event_scale != scale:
                    raise ValueError("probability scale changed after stream initialization")
                event_count += 1
                if event_count > MAX_EVENTS:
                    raise ValueError(f"reference population exceeds {MAX_EVENTS} events")

                mixed_count = q63_mix_count(
                    parent_weight, parent_count, treatment_count, event_scale
                )
                parent_truth = parent_count if truth else event_scale - parent_count
                treatment_truth = treatment_count if truth else event_scale - treatment_count
                parent_sequence_numerator *= parent_truth
                treatment_sequence_numerator *= treatment_truth
                common_scale_power *= event_scale
                parent_weight = q63_update(
                    parent_weight, parent_truth, treatment_truth
                )

                bookkeeping_mixed = q63_mix_count(
                    INITIAL_PARENT_WEIGHT, parent_count, parent_count, event_scale
                )
                bookkeeping_weight = q63_update(
                    INITIAL_PARENT_WEIGHT, parent_truth, parent_truth
                )
                bookkeeping_neutrality = bookkeeping_neutrality and (
                    bookkeeping_mixed == parent_count
                    and bookkeeping_weight == INITIAL_PARENT_WEIGHT
                )

                trace_row = {
                    "event": event_count - 1,
                    "mixed_count": mixed_count,
                    "parent_weight_after": parent_weight,
                }
                trace_digest.update(canonical(trace_row))
                if native_iterator is not None:
                    try:
                        native_line, native = next(native_iterator)
                    except StopIteration as error:
                        raise ValueError("native trace ended before reference population") from error
                    native_mixed = exact_int(
                        native.get("mixed_count"),
                        f"native:{native_line}.mixed_count",
                    )
                    native_weight = exact_int(
                        native.get("parent_weight_after"),
                        f"native:{native_line}.parent_weight_after",
                    )
                    native_identity = native_identity and (
                        native_mixed == mixed_count
                        and native_weight == parent_weight
                    )
        if event_count == 0 or scale is None:
            raise ValueError("reference population is empty")
        if native_iterator is not None:
            try:
                next(native_iterator)
            except StopIteration:
                pass
            else:
                raise ValueError("native trace contains rows beyond reference population")
    finally:
        if native_stream is not None:
            native_stream.close()

    mixture_sequence_numerator = parent_sequence_numerator + treatment_sequence_numerator
    ideal_bound_pass = (
        mixture_sequence_numerator >= parent_sequence_numerator
        and mixture_sequence_numerator >= treatment_sequence_numerator
    )
    return {
        "schema": SCHEMA,
        "candidate_id": "gamma_safe_mix_v1",
        "mode": "integer_reference",
        "authority": "diagnostic_only",
        "input": {
            "path": str(input_path.resolve()),
            "bytes": input_path.stat().st_size,
            "sha256": sha256(input_path),
            "canonical_rows_sha256": input_digest.hexdigest(),
        },
        "native_trace": None if native_path is None else {
            "path": str(native_path.resolve()),
            "bytes": native_path.stat().st_size,
            "sha256": sha256(native_path),
        },
        "population": {
            "event_count": event_count,
            "probability_scale": scale,
            "complete_population_pass": True,
        },
        "q63": {
            "weight_total": WEIGHT_TOTAL,
            "initial_parent_weight": INITIAL_PARENT_WEIGHT,
            "final_parent_weight": parent_weight,
            "trace_sha256": trace_digest.hexdigest(),
            "bookkeeping_neutrality_pass": bookkeeping_neutrality,
            "native_trace_identity_pass": native_identity,
        },
        "ideal_sequence": {
            "common_denominator_is_two_times_scale_power": True,
            "scale_power_bit_length": common_scale_power.bit_length(),
            "parent_numerator_bit_length": parent_sequence_numerator.bit_length(),
            "treatment_numerator_bit_length": treatment_sequence_numerator.bit_length(),
            "mixture_numerator_bit_length": mixture_sequence_numerator.bit_length(),
            "equal_prior_one_bit_bound_exact_pass": ideal_bound_pass,
        },
        "terminal_pass": bool(
            ideal_bound_pass
            and bookkeeping_neutrality
            and native_identity is not False
        ),
        "archive_promotion_authority": False,
        "compression_credit_bytes": 0,
        "score_credit_bytes": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--native-trace")
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    receipt = evaluate(
        Path(args.input),
        None if args.native_trace is None else Path(args.native_trace),
    )
    write_new(Path(args.receipt), receipt)
    return 0 if receipt["terminal_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
