#!/usr/bin/env python3
"""Measure oracle concentration of one endpoint probability trace over another."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


MAGIC = b"FX2PT01\n"
DTYPE = np.dtype([("p1", "<u2"), ("bit", "u1")])
TOTAL = 1 << 16


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def open_trace(path: Path) -> np.memmap:
    with path.open("rb") as source:
        if source.read(len(MAGIC)) != MAGIC:
            raise ValueError(f"{path}: invalid FX2PT01 magic")
    payload = path.stat().st_size - len(MAGIC)
    if payload <= 0 or payload % DTYPE.itemsize:
        raise ValueError(f"{path}: invalid FX2PT01 length")
    return np.memmap(
        path,
        mode="r",
        dtype=DTYPE,
        offset=len(MAGIC),
        shape=(payload // DTYPE.itemsize,),
    )


def log2_choose(n: int, k: int) -> float:
    if k <= 0 or k >= n:
        return 0.0
    return (
        math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
    ) / math.log(2.0)


def parse_fractions(value: str) -> list[float]:
    fractions = [float(part) for part in value.split(",")]
    if not fractions or any(part <= 0.0 or part > 1.0 for part in fractions):
        raise argparse.ArgumentTypeError("fractions must be in (0,1]")
    return fractions


def parse_block_sizes(value: str) -> list[int]:
    sizes = [int(part) for part in value.split(",")]
    if not sizes or any(size <= 0 for size in sizes):
        raise argparse.ArgumentTypeError("block sizes must be positive")
    return sizes


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Rank blocks by realized teacher-versus-base coding gain while both "
            "models evolve continuously. This is an oracle output-suppression "
            "screen, not evidence that recurrent computation can yet be skipped."
        )
    )
    parser.add_argument("--teacher", required=True, type=Path)
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--teacher-archive", required=True, type=Path)
    parser.add_argument("--base-archive", required=True, type=Path)
    parser.add_argument("--teacher-seconds", required=True, type=float)
    parser.add_argument("--base-seconds", required=True, type=float)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--block-bytes",
        default=[16, 32, 64, 128, 256, 512, 1024, 4096],
        type=parse_block_sizes,
    )
    parser.add_argument(
        "--fractions",
        default=[0.01, 0.05, 0.10, 0.20, 0.50, 1.0],
        type=parse_fractions,
    )
    parser.add_argument("--chunk-rows", type=int, default=1 << 20)
    args = parser.parse_args()

    teacher = open_trace(args.teacher)
    base = open_trace(args.base)
    if len(teacher) != len(base):
        raise ValueError("teacher and base row counts differ")
    if len(teacher) % 8:
        raise ValueError("trace is not WRT-byte aligned")
    if args.chunk_rows <= 0:
        raise ValueError("chunk rows must be positive")

    rows = len(teacher)
    wrt_bytes = rows // 8
    byte_gain = np.zeros(wrt_bytes, dtype=np.float64)
    teacher_bits = 0.0
    base_bits = 0.0
    for start in range(0, rows, args.chunk_rows):
        end = min(rows, start + args.chunk_rows)
        teacher_part = teacher[start:end]
        base_part = base[start:end]
        teacher_p1 = teacher_part["p1"].astype(np.int32)
        base_p1 = base_part["p1"].astype(np.int32)
        bits = teacher_part["bit"].astype(np.int32)
        if not np.array_equal(bits, base_part["bit"]):
            raise ValueError("teacher and base truth bits differ")
        if (
            np.any(teacher_p1 <= 0)
            or np.any(teacher_p1 >= TOTAL)
            or np.any(base_p1 <= 0)
            or np.any(base_p1 >= TOTAL)
        ):
            raise ValueError("trace contains an invalid probability")
        teacher_outcome = np.where(bits == 1, teacher_p1, TOTAL - teacher_p1)
        base_outcome = np.where(bits == 1, base_p1, TOTAL - base_p1)
        teacher_loss = -np.log2(teacher_outcome / TOTAL)
        base_loss = -np.log2(base_outcome / TOTAL)
        gain = base_loss - teacher_loss
        teacher_bits += float(teacher_loss.sum())
        base_bits += float(base_loss.sum())
        first_byte = start // 8
        byte_gain[first_byte : first_byte + len(gain) // 8] = gain.reshape(-1, 8).sum(
            axis=1
        )

    total_gain = float(byte_gain.sum())
    positive_gain = float(byte_gain[byte_gain > 0.0].sum())
    curves: list[dict[str, object]] = []
    for block_bytes in args.block_bytes:
        starts = np.arange(0, wrt_bytes, block_bytes)
        block_gain = np.add.reduceat(byte_gain, starts)
        ranked = np.sort(block_gain)[::-1]
        block_count = len(block_gain)
        points: list[dict[str, object]] = []
        for fraction in args.fractions:
            selected = min(block_count, max(1, math.ceil(block_count * fraction)))
            captured = float(ranked[:selected].sum())
            mask_bits = log2_choose(block_count, selected)
            points.append(
                {
                    "coverage_fraction": fraction,
                    "selected_blocks": selected,
                    "captured_gain_bits": captured,
                    "captured_gain_bytes": captured / 8.0,
                    "fraction_of_net_teacher_gain": (
                        captured / total_gain if total_gain > 0.0 else None
                    ),
                    "fraction_of_positive_block_gain": (
                        captured / positive_gain if positive_gain > 0.0 else None
                    ),
                    "mask_lower_bound_bits": mask_bits,
                    "net_after_mask_bits": captured - mask_bits,
                    "optimistic_runtime_seconds": args.base_seconds
                    + fraction * (args.teacher_seconds - args.base_seconds),
                }
            )
        curves.append(
            {
                "block_bytes": block_bytes,
                "block_count": block_count,
                "positive_blocks": int(np.count_nonzero(block_gain > 0.0)),
                "positive_block_fraction": float(np.mean(block_gain > 0.0)),
                "positive_block_gain_bits": float(block_gain[block_gain > 0.0].sum()),
                "negative_block_gain_bits": float(block_gain[block_gain < 0.0].sum()),
                "points": points,
            }
        )

    result = {
        "schema": "endpoint_trace_gain_density_v1",
        "contract": {
            "teacher_and_base_states_evolve_on_every_symbol": True,
            "selection_is_noncausal_oracle_ranked_by_realized_block_gain": True,
            "mask_cost_is_information_theoretic_lower_bound": True,
            "runtime_is_linear_optimistic_interpolation_not_measurement": True,
            "purpose": (
                "Decide whether selective residual computation merits a causal "
                "router or transmitted-mask implementation."
            ),
        },
        "inputs": {
            "teacher_trace": artifact(args.teacher),
            "base_trace": artifact(args.base),
            "teacher_archive": artifact(args.teacher_archive),
            "base_archive": artifact(args.base_archive),
        },
        "scope": {"trace_rows": rows, "wrt_bytes": wrt_bytes},
        "measured": {
            "teacher_archive_bytes": args.teacher_archive.stat().st_size,
            "base_archive_bytes": args.base_archive.stat().st_size,
            "archive_advantage_bytes": (
                args.base_archive.stat().st_size
                - args.teacher_archive.stat().st_size
            ),
            "teacher_seconds": args.teacher_seconds,
            "base_seconds": args.base_seconds,
            "runtime_cost_seconds": args.teacher_seconds - args.base_seconds,
        },
        "ideal_log_loss": {
            "teacher_bits": teacher_bits,
            "base_bits": base_bits,
            "teacher_advantage_bits": total_gain,
            "teacher_advantage_bytes": total_gain / 8.0,
            "positive_wrt_byte_gain_bits": positive_gain,
        },
        "curves": curves,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.output.resolve()), **result["ideal_log_loss"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
