#!/usr/bin/env python3
"""Verify an archive-neutral NNCP full-distribution teacher trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import numpy as np


MAGIC = b"NNTCHD2\0"
HEADER = struct.Struct("<8sQ")
ROW = struct.Struct("<QQQQIHHI")


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


def rows(path: Path) -> Iterator[tuple[tuple[int, ...], np.ndarray]]:
    with path.open("rb") as source:
        magic, count = HEADER.unpack(source.read(HEADER.size))
        if magic != MAGIC or count <= 0:
            raise ValueError("invalid NNCP distribution trace header")
        for _ in range(count):
            fixed = ROW.unpack(source.read(ROW.size))
            n_symbols = fixed[-1]
            raw = source.read(4 * n_symbols)
            if len(raw) != 4 * n_symbols:
                raise ValueError("truncated NNCP distribution")
            yield fixed, np.frombuffer(raw, dtype="<f4")
        if source.read(1):
            raise ValueError("trailing NNCP distribution trace bytes")


def run(args: argparse.Namespace) -> dict[str, Any]:
    off = artifact(args.trace_off_archive)
    on = artifact(args.trace_on_archive)
    if any(off[key] != on[key] for key in ("bytes", "sha256")):
        raise ValueError("full-distribution observation changed the archive")
    symbols = np.memmap(args.preprocessed, mode="r", dtype=">u2")
    execution = 0
    prior_after: int | None = None
    streams: set[int] = set()
    vocabularies: set[int] = set()
    true_losses: list[float] = []
    max_normalization_error = 0.0
    with args.teacher_trace.open("rb") as source:
        magic, declared = HEADER.unpack(source.read(HEADER.size))
    if magic != MAGIC:
        raise ValueError("invalid NNCP distribution trace magic")
    for fixed, distribution in rows(args.teacher_trace):
        (
            original,
            execution_row,
            before,
            after,
            _local,
            stream,
            true_symbol,
            n_symbols,
        ) = fixed
        if execution_row != execution:
            raise ValueError("teacher execution rows are not consecutive")
        if original >= len(symbols) or int(symbols[original]) != true_symbol:
            raise ValueError("teacher symbol does not match preprocessed stream")
        if prior_after is not None and before != prior_after:
            raise ValueError("teacher coder counts are discontinuous")
        if after < before:
            raise ValueError("teacher coder count decreased")
        if (
            len(distribution) != n_symbols
            or not np.all(np.isfinite(distribution))
            or np.any(distribution <= 0)
        ):
            raise ValueError("teacher distribution is invalid")
        normalization_error = abs(float(distribution.sum(dtype=np.float64)) - 1.0)
        max_normalization_error = max(max_normalization_error, normalization_error)
        if normalization_error > args.normalization_tolerance:
            raise ValueError("teacher distribution is not normalized")
        true_losses.append(-float(np.log2(float(distribution[true_symbol]))))
        streams.add(stream)
        vocabularies.add(n_symbols)
        prior_after = after
        execution += 1
    if execution != declared:
        raise ValueError("distribution row count differs from header")
    guard = json.loads(args.rss_guard.read_text()).get(
        "rss_guard", json.loads(args.rss_guard.read_text())
    )
    if (
        guard.get("status") != "complete"
        or guard.get("returncode") != 0
        or guard.get("rss_guard_exceeded") is not False
    ):
        raise ValueError("RSS guard is not clean")
    return {
        "schema": "nncp_teacher_distribution_receipt_v2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "archive_neutral_full_distribution_teacher_zero_credit",
        "artifacts": {
            "source_tar": artifact(args.source_tar),
            "trace_patch": artifact(args.trace_patch),
            "binary": artifact(args.binary),
            "preprocessed": artifact(args.preprocessed),
            "trace_off_archive": off,
            "trace_on_archive": on,
            "teacher_trace": artifact(args.teacher_trace),
            "rss_guard": artifact(args.rss_guard),
        },
        "proof": {
            "archive_identity": True,
            "rows": execution,
            "streams": sorted(streams),
            "vocabularies": sorted(vocabularies),
            "original_positions_sequential": all(
                fixed[0] == index
                for index, (fixed, _) in enumerate(rows(args.teacher_trace))
            ),
            "distributions_positive_finite_normalized": True,
            "maximum_normalization_error": max_normalization_error,
            "mean_true_symbol_log2_loss": float(np.mean(true_losses)),
            "final_coder_bits": prior_after,
            "max_tree_rss_kib": guard["max_sampled_tree_rss_kib"],
            "elapsed_s": guard["elapsed_s"],
        },
        "claim_boundary": (
            "Bounded external full-distribution teacher observation only. "
            "It is not a student, native Gamma codec, or score improvement."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-tar", type=Path, required=True)
    parser.add_argument("--trace-patch", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--preprocessed", type=Path, required=True)
    parser.add_argument("--trace-off-archive", type=Path, required=True)
    parser.add_argument("--trace-on-archive", type=Path, required=True)
    parser.add_argument("--teacher-trace", type=Path, required=True)
    parser.add_argument("--rss-guard", type=Path, required=True)
    parser.add_argument("--normalization-tolerance", type=float, default=2e-5)
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
