#!/usr/bin/env python3
"""Verify an observation-only NNCP true-symbol probability trace."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


MAGIC = b"NNTCHR1\0"
HEADER_BYTES = 16
ROW_DTYPE = np.dtype(
    [
        ("original_symbol_index", "<u8"),
        ("execution_row", "<u8"),
        ("coder_bits_before", "<u8"),
        ("coder_bits_after", "<u8"),
        ("local_position", "<u4"),
        ("stream_index", "<u2"),
        ("true_symbol", "<u2"),
        ("true_probability_bits", "<u4"),
        ("n_symbols", "<u4"),
    ]
)


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


def load_guard(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    guard = value.get("rss_guard", value)
    if (
        guard.get("status") != "complete"
        or guard.get("returncode") != 0
        or guard.get("rss_guard_exceeded") is not False
        or guard.get("official_decimal_over_limit_kib") != 0
    ):
        raise ValueError("teacher trace RSS guard is not clean")
    return guard


def run(args: argparse.Namespace) -> dict[str, Any]:
    trace_off = artifact(args.trace_off_archive)
    trace_on = artifact(args.trace_on_archive)
    if any(trace_off[key] != trace_on[key] for key in ("bytes", "sha256")):
        raise ValueError("teacher observation changed the NNCP archive")

    with args.teacher_trace.open("rb") as source:
        header = source.read(HEADER_BYTES)
    if len(header) != HEADER_BYTES or header[:8] != MAGIC:
        raise ValueError("invalid NNCP teacher trace header")
    rows = int.from_bytes(header[8:16], "little")
    if rows <= 0:
        raise ValueError("teacher trace has no rows")
    if args.teacher_trace.stat().st_size != HEADER_BYTES + rows * ROW_DTYPE.itemsize:
        raise ValueError("teacher trace size differs from its row count")
    trace = np.memmap(
        args.teacher_trace,
        mode="r",
        dtype=ROW_DTYPE,
        offset=HEADER_BYTES,
        shape=(rows,),
    )
    preprocessed_rows = args.preprocessed.stat().st_size // 2
    if args.preprocessed.stat().st_size % 2:
        raise ValueError("preprocessed stream is not 16-bit aligned")
    positions = trace["original_symbol_index"]
    if int(positions.max()) >= preprocessed_rows:
        raise ValueError("teacher trace position exceeds preprocessed stream")
    if len(np.unique(positions)) != rows:
        raise ValueError("teacher trace repeats an original symbol position")
    if not np.array_equal(trace["execution_row"], np.arange(rows, dtype=np.uint64)):
        raise ValueError("teacher execution rows are not consecutive")
    source_symbols = np.memmap(
        args.preprocessed, mode="r", dtype=">u2", shape=(preprocessed_rows,)
    )
    if not np.array_equal(trace["true_symbol"], source_symbols[positions]):
        raise ValueError("teacher true symbols differ from mapped input symbols")
    if rows > 1 and not np.array_equal(
        trace["coder_bits_before"][1:], trace["coder_bits_after"][:-1]
    ):
        raise ValueError("teacher coder counts are not continuous")
    if np.any(trace["coder_bits_after"] < trace["coder_bits_before"]):
        raise ValueError("teacher coder count decreases")
    probabilities = trace["true_probability_bits"].view("<f4")
    if (
        not np.all(np.isfinite(probabilities))
        or np.any(probabilities <= 0.0)
        or np.any(probabilities > 1.0)
    ):
        raise ValueError("teacher true probability is outside (0, 1]")
    if np.any(trace["true_symbol"] >= trace["n_symbols"]):
        raise ValueError("teacher symbol exceeds its vocabulary")
    guard = load_guard(args.rss_guard)
    sequential = np.arange(rows, dtype=np.uint64)
    displacement = np.abs(
        positions.astype(np.int64) - sequential.astype(np.int64)
    )
    return {
        "schema": "nncp_teacher_trace_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "adjacent_archive_identity_true_symbol_teacher_trace",
        "artifacts": {
            "official_source_tar": artifact(args.source_tar),
            "symbol_map_patch": artifact(args.symbol_map_patch),
            "teacher_trace_patch": artifact(args.teacher_trace_patch),
            "instrumented_binary": artifact(args.binary),
            "preprocessed_symbols": artifact(args.preprocessed),
            "trace_off_archive": trace_off,
            "trace_on_archive": trace_on,
            "teacher_trace": artifact(args.teacher_trace),
            "rss_guard": artifact(args.rss_guard),
        },
        "proof": {
            "archive_identity_with_and_without_trace": True,
            "trace_rows": rows,
            "trace_row_bytes": ROW_DTYPE.itemsize,
            "unique_original_symbol_positions": True,
            "execution_rows_consecutive": True,
            "true_symbols_match_preprocessed_stream": True,
            "coder_counts_continuous": True,
            "true_probabilities_finite_and_bounded": True,
            "vocabulary_sizes": sorted(map(int, np.unique(trace["n_symbols"]))),
            "streams": int(trace["stream_index"].max()) + 1,
            "execution_order_differs_from_original_order_rows": int(
                np.count_nonzero(positions != sequential)
            ),
            "maximum_execution_displacement_symbols": int(displacement.max()),
            "final_observed_coder_bits": int(trace["coder_bits_after"][-1]),
            "mean_true_symbol_log2_loss": float(
                np.mean(-np.log2(probabilities.astype(np.float64)))
            ),
            "rss_guard_clean": True,
            "max_sampled_tree_rss_kib": guard["max_sampled_tree_rss_kib"],
            "guard_elapsed_s": guard["elapsed_s"],
        },
        "claim_boundary": (
            "This is an archive-neutral external teacher trace on a bounded "
            "scope. It records only true-symbol probabilities, is not a Gamma "
            "student or codec, and receives zero score credit."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-tar", type=Path, required=True)
    parser.add_argument("--symbol-map-patch", type=Path, required=True)
    parser.add_argument("--teacher-trace-patch", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--preprocessed", type=Path, required=True)
    parser.add_argument("--trace-off-archive", type=Path, required=True)
    parser.add_argument("--trace-on-archive", type=Path, required=True)
    parser.add_argument("--teacher-trace", type=Path, required=True)
    parser.add_argument("--rss-guard", type=Path, required=True)
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
