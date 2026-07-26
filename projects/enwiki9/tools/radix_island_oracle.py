#!/usr/bin/env python3
"""Screen RADIX-ISLAND headroom on an exact WRT/P1 trace."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from wrt_exact import parse_store


P1_MAGIC = b"CMX21P1\0"
P1_HEADER_BYTES = 16
QBITS = 256
FRAME_BITS = 128
SEPARATORS = frozenset(b"-:./,+TZ ")
LEFT_CONTEXT = 6
RIGHT_CONTEXT = 2
MAX_FIELDS = 8
MAX_ISLAND_SPAN = 64
MAX_SEPARATOR = 3


@dataclass(frozen=True)
class EmissionGroup:
    stream_start: int
    stream_end: int
    raw_start: int
    raw_end: int
    decoded: bytes


@dataclass(frozen=True)
class DigitRun:
    group_start: int
    group_end: int
    stream_start: int
    stream_end: int
    raw_start: int
    raw_end: int
    digits: bytes


@dataclass(frozen=True)
class NumericRecord:
    raw_start: int
    raw_end: int
    runs: tuple[DigitRun, ...]
    separators: tuple[bytes, ...]
    key: tuple[Any, ...]

    @property
    def lengths(self) -> tuple[int, ...]:
        return tuple(len(run.digits) for run in self.runs)

    @property
    def values(self) -> tuple[int, ...]:
        return tuple(int(run.digits) for run in self.runs)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def load_p1(path: Path) -> np.memmap:
    with path.open("rb") as source:
        header = source.read(P1_HEADER_BYTES)
    if len(header) != P1_HEADER_BYTES or header[:8] != P1_MAGIC:
        raise ValueError("invalid CMIX P1 trace")
    rows = int.from_bytes(header[8:16], "little")
    if rows <= 0 or rows % 8:
        raise ValueError("P1 rows must be positive and byte aligned")
    if path.stat().st_size != P1_HEADER_BYTES + rows * 2:
        raise ValueError("P1 trace size differs from row count")
    return np.memmap(
        path, mode="r", dtype="<u2", offset=P1_HEADER_BYTES, shape=(rows,)
    )


def load_truth(store: Path, rows: int) -> np.ndarray:
    if store.stat().st_size != 5 + rows // 8:
        raise ValueError("WRT store size differs from P1 rows")
    stored = np.memmap(store, mode="r", dtype="u1")
    if bytes(stored[:5]) != b"\x80\x00\x00\x00\x00":
        raise ValueError("invalid WRT outer header")
    return np.unpackbits(stored[5:], bitorder="big")


def qbit_tables() -> tuple[np.ndarray, np.ndarray]:
    probabilities = np.arange(1 << 16, dtype=np.float64) / (1 << 16)
    p1 = np.clip(probabilities, 1.0 / (1 << 16), 1.0 - 1.0 / (1 << 16))
    one = np.rint(-np.log2(p1) * QBITS).astype(np.int32)
    zero = np.rint(-np.log2(1.0 - p1) * QBITS).astype(np.int32)
    return zero, one


def emission_groups(parsed: Any) -> tuple[EmissionGroup, ...]:
    groups: list[EmissionGroup] = []
    pending_start: int | None = None
    raw_position = 0
    for event in parsed.events:
        if pending_start is None:
            pending_start = event.start
        if not event.decoded:
            continue
        group = EmissionGroup(
            stream_start=pending_start,
            stream_end=event.end,
            raw_start=raw_position,
            raw_end=raw_position + len(event.decoded),
            decoded=event.decoded,
        )
        groups.append(group)
        raw_position = group.raw_end
        pending_start = None
    if pending_start is not None:
        raise ValueError("trailing zero-output WRT controls")
    if raw_position != len(parsed.decoded):
        raise ValueError("emission groups do not cover raw output")
    return tuple(groups)


def digit_runs(groups: tuple[EmissionGroup, ...]) -> tuple[DigitRun, ...]:
    runs: list[DigitRun] = []
    index = 0
    while index < len(groups):
        group = groups[index]
        if len(group.decoded) != 1 or not group.decoded.isdigit():
            index += 1
            continue
        start = index
        digits = bytearray()
        while index < len(groups):
            current = groups[index]
            if len(current.decoded) != 1 or not current.decoded.isdigit():
                break
            digits.extend(current.decoded)
            index += 1
        last = groups[index - 1]
        runs.append(
            DigitRun(
                group_start=start,
                group_end=index,
                stream_start=groups[start].stream_start,
                stream_end=last.stream_end,
                raw_start=groups[start].raw_start,
                raw_end=last.raw_end,
                digits=bytes(digits),
            )
        )
    return tuple(runs)


def normalize_digits(raw: bytes, runs: Iterable[DigitRun]) -> bytes:
    output = bytearray(raw)
    for run in runs:
        output[run.raw_start : run.raw_end] = b"#" * len(run.digits)
    return bytes(output)


def build_key(
    normalized: bytes,
    raw_start: int,
    raw_end: int,
    runs: tuple[DigitRun, ...],
    separators: tuple[bytes, ...],
) -> tuple[Any, ...]:
    return (
        len(runs),
        tuple(len(run.digits) for run in runs),
        separators,
        normalized[max(0, raw_start - LEFT_CONTEXT) : raw_start],
        normalized[raw_end : raw_end + RIGHT_CONTEXT],
    )


def run_records(raw: bytes, runs: tuple[DigitRun, ...]) -> tuple[NumericRecord, ...]:
    normalized = normalize_digits(raw, runs)
    records = []
    for run in runs:
        run_tuple = (run,)
        records.append(
            NumericRecord(
                raw_start=run.raw_start,
                raw_end=run.raw_end,
                runs=run_tuple,
                separators=(),
                key=build_key(
                    normalized, run.raw_start, run.raw_end, run_tuple, ()
                ),
            )
        )
    return tuple(records)


def island_records(
    raw: bytes, runs: tuple[DigitRun, ...]
) -> tuple[NumericRecord, ...]:
    normalized = normalize_digits(raw, runs)
    records: list[NumericRecord] = []
    index = 0
    while index < len(runs):
        selected = [runs[index]]
        separators: list[bytes] = []
        index += 1
        while index < len(runs) and len(selected) < MAX_FIELDS:
            previous = selected[-1]
            candidate = runs[index]
            separator = raw[previous.raw_end : candidate.raw_start]
            span = candidate.raw_end - selected[0].raw_start
            if (
                len(separator) > MAX_SEPARATOR
                or any(value not in SEPARATORS for value in separator)
                or span > MAX_ISLAND_SPAN
            ):
                break
            separators.append(separator)
            selected.append(candidate)
            index += 1
        selected_tuple = tuple(selected)
        separators_tuple = tuple(separators)
        records.append(
            NumericRecord(
                raw_start=selected_tuple[0].raw_start,
                raw_end=selected_tuple[-1].raw_end,
                runs=selected_tuple,
                separators=separators_tuple,
                key=build_key(
                    normalized,
                    selected_tuple[0].raw_start,
                    selected_tuple[-1].raw_end,
                    selected_tuple,
                    separators_tuple,
                ),
            )
        )
    return tuple(records)


def truncated_binary_bits(value: int, radix: int) -> int:
    if not 0 <= value < radix:
        raise ValueError("value outside radix")
    width = radix.bit_length() - 1
    cutoff = (1 << (width + 1)) - radix
    return width if value < cutoff else width + 1


def direct_bits(record: NumericRecord) -> int:
    return sum(
        truncated_binary_bits(value, 10**length)
        for value, length in zip(record.values, record.lengths, strict=True)
    )


def rice_parameter(mean_q8: int) -> int:
    base = (mean_q8 >> 8) + 1
    return max(0, min(20, base.bit_length() - 2))


def rice_bits(delta: int, mean_q8: int) -> int:
    zigzag = 2 * delta if delta >= 0 else -2 * delta - 1
    k = rice_parameter(mean_q8)
    return (zigzag >> k) + 1 + k


def update_mean(mean_q8: int, delta: int) -> int:
    return mean_q8 + (((abs(delta) << 8) - mean_q8) >> 5)


def delta_group_bits(records: list[NumericRecord]) -> tuple[int, dict[str, int]]:
    if not records:
        return 0, {"direct_records": 0, "delta_records": 0}
    bits = direct_bits(records[0])
    direct_count = 1
    delta_count = 0
    previous = records[0].values
    means = [256] * len(previous)
    for record in records[1:]:
        values = record.values
        if len(values) != len(previous):
            raise ValueError("delta group changed field count")
        direct_option = 1 + direct_bits(record)
        delta_option = 1 + len(values)
        deltas = []
        for index, (value, prior) in enumerate(
            zip(values, previous, strict=True)
        ):
            delta = value - prior
            deltas.append(delta)
            if delta:
                delta_option += rice_bits(delta, means[index])
        if delta_option < direct_option:
            bits += delta_option
            delta_count += 1
        else:
            bits += direct_option
            direct_count += 1
        for index, delta in enumerate(deltas):
            if delta:
                means[index] = update_mean(means[index], delta)
        previous = values
    return bits, {
        "direct_records": direct_count,
        "delta_records": delta_count,
    }


def grouped_delta_bits(
    records: tuple[NumericRecord, ...], key_kind: str
) -> tuple[int, dict[str, int]]:
    groups: dict[Any, list[NumericRecord]] = defaultdict(list)
    for record in records:
        if key_kind == "length":
            key = record.lengths
        elif key_kind == "full":
            key = record.key
        else:
            raise ValueError("unknown key kind")
        groups[key].append(record)
    total_bits = 0
    counters: Counter[str] = Counter()
    for key in sorted(groups, key=repr):
        bits, counts = delta_group_bits(groups[key])
        total_bits += bits
        counters.update(counts)
    counters["groups"] = len(groups)
    return total_bits, dict(sorted(counters.items()))


def marker_length_bits(length: int, marker_bits: int) -> int:
    bits = marker_bits
    if length > 11:
        excess = length - 11
        bits += 2 * (excess.bit_length() - 1) + 1
    return bits


def candidate(
    name: str,
    parent_qbits: int,
    marker_bits: int,
    side_bits: int,
    frame_bits: int,
    raw_bytes: int,
) -> dict[str, Any]:
    total_bits = marker_bits + side_bits + frame_bits
    saved_qbits = parent_qbits - total_bits * QBITS
    saved_bytes = saved_qbits / (8 * QBITS)
    return {
        "name": name,
        "marker_bits": marker_bits,
        "side_bits": side_bits,
        "frame_bits": frame_bits,
        "total_replacement_bits": total_bits,
        "parent_digit_qbits": parent_qbits,
        "saved_qbits": saved_qbits,
        "saved_bytes": saved_bytes,
        "saved_bytes_per_1m_raw": saved_bytes * 1_000_000 / raw_bytes,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    p1 = load_p1(args.p1_trace)
    truth = load_truth(args.wrt_store, len(p1))
    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("WRT reconstruction differs from raw input")
    groups = emission_groups(parsed)
    runs = digit_runs(groups)
    if not runs:
        raise ValueError("no eligible digit runs")
    zero_cost, one_cost = qbit_tables()
    parent_qbits = 0
    original_rows = 0
    for run in runs:
        start = run.stream_start * 8
        end = run.stream_end * 8
        values = p1[start:end]
        bits = truth[start:end]
        parent_qbits += int(
            np.where(bits != 0, one_cost[values], zero_cost[values]).sum()
        )
        original_rows += end - start

    per_digit_markers = 8 * sum(len(run.digits) for run in runs)
    optimistic_run_markers = sum(
        marker_length_bits(len(run.digits), 4) for run in runs
    )
    conservative_run_markers = sum(
        marker_length_bits(len(run.digits), 16) for run in runs
    )
    direct_side = sum(
        truncated_binary_bits(int(run.digits), 10 ** len(run.digits))
        for run in runs
    )
    run_level = run_records(raw, runs)
    islands = island_records(raw, runs)
    occurrence_delta, occurrence_counts = grouped_delta_bits(
        run_level, "length"
    )
    context_delta, context_counts = grouped_delta_bits(run_level, "full")
    island_delta, island_counts = grouped_delta_bits(islands, "full")

    candidates = {
        "R1_per_digit_direct": candidate(
            "R1_per_digit_direct",
            parent_qbits,
            per_digit_markers,
            direct_side,
            FRAME_BITS,
            len(raw),
        ),
        "R2_run_direct_optimistic_marker": candidate(
            "R2_run_direct_optimistic_marker",
            parent_qbits,
            optimistic_run_markers,
            direct_side,
            FRAME_BITS,
            len(raw),
        ),
        "R2_run_direct_conservative_marker": candidate(
            "R2_run_direct_conservative_marker",
            parent_qbits,
            conservative_run_markers,
            direct_side,
            FRAME_BITS,
            len(raw),
        ),
        "R3_occurrence_delta_conservative_marker": candidate(
            "R3_occurrence_delta_conservative_marker",
            parent_qbits,
            conservative_run_markers,
            occurrence_delta,
            FRAME_BITS,
            len(raw),
        ),
        "R3_context_delta_conservative_marker": candidate(
            "R3_context_delta_conservative_marker",
            parent_qbits,
            conservative_run_markers,
            context_delta,
            FRAME_BITS,
            len(raw),
        ),
        "R4_island_delta_conservative_marker": candidate(
            "R4_island_delta_conservative_marker",
            parent_qbits,
            conservative_run_markers,
            island_delta,
            FRAME_BITS,
            len(raw),
        ),
    }
    primary = candidates["R4_island_delta_conservative_marker"]
    context_value_bits = occurrence_delta - context_delta
    island_value_bits = context_delta - island_delta
    gate_pass = (
        primary["saved_bytes_per_1m_raw"] >= args.required_rate
        and context_value_bits > 0
        and island_value_bits > 0
    )
    if gate_pass:
        verdict = "oracle_pass_requires_disjoint_replay"
        next_action = (
            "freeze rules and run the identical oracle on distant exact traces"
        )
    else:
        verdict = "retire_radix_island_insufficient_or_noncompositional_oracle"
        next_action = (
            "reject native implementation; preserve digit-regret ledger only"
        )
    return {
        "schema": "radix_island_oracle_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "truth_aware_integer_qbit_headroom_zero_credit",
        "proposal_id": "radix_island_numeric_event_v1",
        "artifacts": {
            "raw_input": artifact(args.raw_input),
            "wrt_store": artifact(args.wrt_store),
            "dictionary": artifact(args.dictionary),
            "p1_trace": artifact(args.p1_trace),
        },
        "scope": {
            "raw_bytes": len(raw),
            "trace_rows": len(p1),
            "emission_groups": len(groups),
            "eligible_digit_bytes": sum(len(run.digits) for run in runs),
            "eligible_runs": len(runs),
            "run_lengths": dict(
                sorted(Counter(len(run.digits) for run in runs).items())
            ),
            "numeric_islands": len(islands),
            "island_field_counts": dict(
                sorted(Counter(len(record.runs) for record in islands).items())
            ),
            "original_digit_event_rows": original_rows,
            "parent_mean_qbits_per_digit": (
                parent_qbits
                / sum(len(run.digits) for run in runs)
            ),
        },
        "coding": {
            "parent_digit_qbits": parent_qbits,
            "direct_side_bits": direct_side,
            "occurrence_delta_bits": occurrence_delta,
            "context_delta_bits": context_delta,
            "island_delta_bits": island_delta,
            "context_ordering_value_bits": context_value_bits,
            "island_composition_value_bits": island_value_bits,
            "occurrence_delta_counts": occurrence_counts,
            "context_delta_counts": context_counts,
            "island_delta_counts": island_counts,
            "fixed_frame_bits": FRAME_BITS,
            "conservative_marker_bits_per_short_run": 16,
        },
        "candidates": candidates,
        "gate": {
            "required_bytes_per_1m": args.required_rate,
            "primary_candidate": "R4_island_delta_conservative_marker",
            "primary_rate_bytes_per_1m": primary[
                "saved_bytes_per_1m_raw"
            ],
            "context_ordering_independently_positive": context_value_bits > 0,
            "island_composition_independently_positive": island_value_bits > 0,
            "passed": gate_pass,
            "verdict": verdict,
            "next_action": next_action,
        },
        "claim_boundary": (
            "Future-informed qbit headroom oracle only. Parent digit costs are "
            "deterministic integer qbits, not additive archive bytes. Marker and "
            "side-code lengths are explicit, but no native trajectory, source "
            "package, runtime, roundtrip, transfer, or score gain is proved."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--p1-trace", type=Path, required=True)
    parser.add_argument("--required-rate", type=float, default=3000.0)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
