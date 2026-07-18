#!/usr/bin/env python3
"""Select one compact layer-0 endpoint over endpoint428 without holdout peeking."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
from typing import Any

import numpy as np


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from cmix_aux_logit_blend_screen import (  # noqa: E402
    mix_native_q16,
    native_logit_table,
)
from fx2_attribution_external_base_screen import (  # noqa: E402
    P1_HEADER_BYTES,
    PPM,
    PROBABILITY_TOTAL,
    QBITS_PER_BYTE,
    artifact,
    cmix_archive_header_bytes,
    exact_block_audit,
    exact_replay,
    qbit_tables,
    read_p1_header,
)


PACKED_MAGIC = b"CML0P1V1"
PACKED_HEADER_BYTES = 16
DEFAULT_COEFFICIENTS = tuple(
    coefficient
    for coefficient in range(-300_000, 300_001, 25_000)
    if coefficient != 0
)
LAYER0_NAMES = (
    "byte0_ctx8_lr005",
    "byte0_ctx8_lr0005",
    "byte1_ctx8_lr005",
    "byte1_ctx8_lr0005",
    "byte2_ctx4_lr005",
    "byte3_ctx2_lr002",
    "recent_byte2_lr002",
    "recent_byte3_lr005",
    "zero_context_lr00005",
    "line_break_lr0007",
    "longest_match_lr0005",
    "wrt_context_lr002",
    "auxiliary_context_lr0005",
    "interval_ascii_thresholds_lr001",
    "interval_markup_thresholds_lr001",
    "interval_alnum_unicode_lr001",
    "bitctx_alnum_unicode_lr005",
    "interval_classmap_a_lr001",
    "interval_classmap_a15_lr001",
    "bitctx_classmap_a_lr005",
    "interval_classmap_b_lr001",
    "intervalhash_classmap_b_lr001",
    "bitctx_classmap_b_lr005",
    "bitctx_previous_byte_lr005",
    "combined_recent1_recent0_lr005",
    "combined_recent2_recent1_lr003",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_packed_header(path: Path) -> tuple[int, int]:
    with path.open("rb") as source:
        header = source.read(PACKED_HEADER_BYTES)
    if len(header) != PACKED_HEADER_BYTES or header[:8] != PACKED_MAGIC:
        raise ValueError("invalid compact layer-0 trace header")
    rows = struct.unpack_from("<Q", header, 8)[0]
    payload_bytes = path.stat().st_size - PACKED_HEADER_BYTES
    if rows < 1 or payload_bytes <= 0 or payload_bytes % (2 * rows) != 0:
        raise ValueError("compact layer-0 trace has invalid dimensions")
    endpoint_count = payload_bytes // (2 * rows)
    if endpoint_count < 1 or endpoint_count > 256:
        raise ValueError("compact layer-0 endpoint count is outside 1..256")
    return rows, endpoint_count


def endpoint_name(index: int, count: int) -> str:
    if count == len(LAYER0_NAMES):
        return LAYER0_NAMES[index]
    return f"layer0_mixer_{index}"


def mix_signed_native_q16_grid(
    base: np.ndarray,
    endpoint: np.ndarray,
    coefficients_ppm: tuple[int, ...],
) -> np.ndarray:
    """Mix in integer logit space; signed coefficients may extrapolate."""

    if not coefficients_ppm or any(abs(value) >= PPM for value in coefficients_ppm):
        raise ValueError("coefficients must be nonempty and within (-1000000, 1000000)")
    base_values = np.asarray(base, dtype=np.uint16)
    endpoint_values = np.asarray(endpoint, dtype=np.uint16)
    if base_values.shape != endpoint_values.shape:
        raise ValueError("base and endpoint shapes differ")
    if np.any(base_values == 0) or np.any(endpoint_values == 0):
        raise ValueError("probabilities must be within 1..65535")

    table = native_logit_table()
    base_logits = table[base_values].astype(np.int64)[:, None]
    endpoint_logits = table[endpoint_values].astype(np.int64)[:, None]
    coefficients = np.asarray(coefficients_ppm, dtype=np.int64)[None, :]
    numerator = (
        base_logits * PPM
        + (endpoint_logits - base_logits) * coefficients
        + PPM // 2
    )
    target = np.floor_divide(numerator, PPM)
    raw_high = np.searchsorted(table[1:], target, side="left") + 1
    high = np.clip(raw_high, 1, PROBABILITY_TOTAL - 1)
    low = high - 1
    low_distance = target - table[low]
    high_distance = table[high] - target
    mixed = np.where(low_distance <= high_distance, low, high)
    mixed = np.where(raw_high <= 1, 1, mixed)
    mixed = np.where(raw_high >= PROBABILITY_TOTAL, PROBABILITY_TOTAL - 1, mixed)
    return mixed.astype(np.uint16)


def mix_signed_native_q16(
    base: np.ndarray, endpoint: np.ndarray, coefficient_ppm: int
) -> np.ndarray:
    return mix_signed_native_q16_grid(base, endpoint, (coefficient_ppm,))[:, 0]


def same_file(left: Path | None, right: Path | None) -> bool | None:
    if left is None and right is None:
        return None
    if left is None or right is None:
        raise ValueError("identity files must be supplied as a pair")
    return left.stat().st_size == right.stat().st_size and sha256_file(left) == sha256_file(right)


def run(args: argparse.Namespace) -> dict[str, Any]:
    if not 0 < args.dev_start_ppm < args.holdout_start_ppm < PPM:
        raise ValueError("split boundaries must be ordered")
    coefficients = tuple(sorted(set(args.coefficients)))
    if not coefficients or 0 in coefficients or any(abs(value) >= PPM for value in coefficients):
        raise ValueError("nonzero coefficients must be within (-1000000, 1000000)")
    if args.raw_scope_bytes < 1 or args.chunk_rows < 1:
        raise ValueError("raw scope and chunk rows must be positive")

    rows, endpoint_count = read_packed_header(args.layer0_trace)
    _, base_rows = read_p1_header(args.base_p1)
    if rows != base_rows:
        raise ValueError("layer-0 trace and base P1 rows differ")
    store_bytes = args.wrt_store.read_bytes()
    if len(store_bytes) < 5 or (len(store_bytes) - 5) * 8 != rows:
        raise ValueError("WRT store and probability rows differ")

    base = np.memmap(
        args.base_p1,
        mode="r",
        dtype="<u2",
        offset=P1_HEADER_BYTES,
        shape=(rows,),
    )
    endpoints = np.memmap(
        args.layer0_trace,
        mode="r",
        dtype="<u2",
        offset=PACKED_HEADER_BYTES,
        shape=(rows, endpoint_count),
    )
    truth = np.unpackbits(
        np.frombuffer(store_bytes, dtype=np.uint8, offset=5), bitorder="big"
    )
    dev_start = rows * args.dev_start_ppm // PPM
    holdout_start = rows * args.holdout_start_ppm // PPM
    loss0, loss1 = qbit_tables()
    dev_gains = np.zeros((endpoint_count, len(coefficients)), dtype=np.int64)

    for start in range(dev_start, holdout_start, args.chunk_rows):
        end = min(holdout_start, start + args.chunk_rows)
        local_base = np.asarray(base[start:end], dtype=np.uint16)
        bits = truth[start:end]
        base_loss = np.where(bits, loss1[local_base], loss0[local_base])
        for endpoint_index in range(endpoint_count):
            mixed = mix_signed_native_q16_grid(
                local_base,
                np.asarray(endpoints[start:end, endpoint_index], dtype=np.uint16),
                coefficients,
            )
            candidate_loss = np.where(
                bits[:, None], loss1[mixed], loss0[mixed]
            )
            dev_gains[endpoint_index] += (
                base_loss[:, None] - candidate_loss
            ).sum(axis=0, dtype=np.int64)

    selected_flat = int(np.argmax(dev_gains))
    selected_endpoint, selected_coefficient_index = np.unravel_index(
        selected_flat, dev_gains.shape
    )
    selected_coefficient = coefficients[selected_coefficient_index]
    selected_endpoint_values = np.asarray(
        endpoints[:, selected_endpoint], dtype=np.uint16
    )
    candidate = mix_signed_native_q16(
        np.asarray(base, dtype=np.uint16),
        selected_endpoint_values,
        selected_coefficient,
    )

    split_gains: dict[str, int] = {}
    for name, start, end in (
        ("train", 0, dev_start),
        ("dev", dev_start, holdout_start),
        ("holdout", holdout_start, rows),
    ):
        bits = truth[start:end]
        split_gains[name] = int(
            (
                np.where(bits, loss1[base[start:end]], loss0[base[start:end]])
                - np.where(
                    bits,
                    loss1[candidate[start:end]],
                    loss0[candidate[start:end]],
                )
            ).sum(dtype=np.int64)
        )

    exact_full, replayed_base_payload, candidate_payload = exact_replay(
        truth, base, candidate
    )
    exact_holdout, _, _ = exact_replay(
        truth[holdout_start:], base[holdout_start:], candidate[holdout_start:]
    )
    block_audit = exact_block_audit(
        truth[holdout_start:],
        base[holdout_start:],
        candidate[holdout_start:],
        args.holdout_blocks,
    )
    archive = args.base_archive.read_bytes()
    archive_header_bytes = cmix_archive_header_bytes(archive)
    archive_payload_identity = replayed_base_payload == archive[archive_header_bytes:]
    native_archive_identity = same_file(
        args.instrumented_archive, args.reference_native_archive
    )
    pair_trace_identity = same_file(
        args.instrumented_pair_trace, args.reference_pair_trace
    )

    if args.candidate_payload is not None:
        args.candidate_payload.parent.mkdir(parents=True, exist_ok=True)
        args.candidate_payload.write_bytes(candidate_payload)
    if args.candidate_p1 is not None:
        args.candidate_p1.parent.mkdir(parents=True, exist_ok=True)
        args.candidate_p1.write_bytes(
            b"CMX21P1\0"
            + struct.pack("<Q", rows)
            + np.asarray(candidate, dtype="<u2").tobytes()
        )

    full_rate = exact_full["saved_bytes"] * 1_000_000 / args.raw_scope_bytes
    holdout_raw_scope = (
        args.raw_scope_bytes * (PPM - args.holdout_start_ppm) / PPM
    )
    holdout_rate = (
        exact_holdout["saved_bytes"] * 1_000_000 / holdout_raw_scope
    )
    required_rate = (
        args.remaining_debt_bytes_per_1m + args.provisional_code_bytes / 1000
    )
    identities_ok = bool(
        archive_payload_identity
        and native_archive_identity is not False
        and pair_trace_identity is not False
    )
    regret_ok = bool(
        block_audit["regressing_blocks"] <= args.max_regressing_blocks
        and block_audit["largest_regression_bytes"] <= args.max_largest_regression_bytes
        and block_audit["total_regression_bytes"] <= args.max_total_regression_bytes
    )
    economics_ok = full_rate >= required_rate and holdout_rate >= required_rate

    ranking: list[dict[str, Any]] = []
    for endpoint_index in range(endpoint_count):
        best_coefficient_index = int(np.argmax(dev_gains[endpoint_index]))
        gain = int(dev_gains[endpoint_index, best_coefficient_index])
        dev_raw_scope = (
            args.raw_scope_bytes
            * (args.holdout_start_ppm - args.dev_start_ppm)
            / PPM
        )
        ranking.append(
            {
                "endpoint_index": endpoint_index,
                "endpoint_name": endpoint_name(endpoint_index, endpoint_count),
                "coefficient_ppm": coefficients[best_coefficient_index],
                "dev_gain_qbits": gain,
                "dev_gain_bytes_per_proportional_1m_raw": (
                    gain / QBITS_PER_BYTE * 1_000_000 / dev_raw_scope
                ),
            }
        )
    ranking.sort(key=lambda item: item["dev_gain_qbits"], reverse=True)

    verdict = (
        "compact_layer0_endpoint_pass_requires_native_integration"
        if identities_ok and regret_ok and economics_ok
        else "retire_compact_layer0_endpoint_universe"
    )
    return {
        "schema": "compact_layer0_blend_screen_v1",
        "evidence_level": "development_selected_exact_causal_shadow",
        "hypothesis": (
            "An already-computed compact layer-0 mixer retains enough residual "
            "gain over endpoint428 to close its counted forecast debt."
        ),
        "inputs": {
            "layer0_trace": artifact(args.layer0_trace),
            "base_p1": artifact(args.base_p1),
            "base_archive": artifact(args.base_archive),
            "wrt_store": artifact(args.wrt_store),
            "instrumented_archive": artifact(args.instrumented_archive)
            if args.instrumented_archive is not None
            else None,
            "reference_native_archive": artifact(args.reference_native_archive)
            if args.reference_native_archive is not None
            else None,
            "instrumented_pair_trace": artifact(args.instrumented_pair_trace)
            if args.instrumented_pair_trace is not None
            else None,
            "reference_pair_trace": artifact(args.reference_pair_trace)
            if args.reference_pair_trace is not None
            else None,
        },
        "scope": {
            "raw_bytes": args.raw_scope_bytes,
            "rows": rows,
            "endpoint_count": endpoint_count,
            "dev_start_row": dev_start,
            "holdout_start_row": holdout_start,
            "selection_reads_holdout": False,
        },
        "identity": {
            "base_archive_payload_identity": archive_payload_identity,
            "instrumented_archive_byte_identity": native_archive_identity,
            "instrumented_pair_trace_byte_identity": pair_trace_identity,
            "all_required_identities_pass": identities_ok,
        },
        "selection": {
            "coefficients_ppm": list(coefficients),
            "selected_endpoint_index": int(selected_endpoint),
            "selected_endpoint_name": endpoint_name(selected_endpoint, endpoint_count),
            "selected_coefficient_ppm": selected_coefficient,
            "selected_dev_gain_qbits": int(
                dev_gains[selected_endpoint, selected_coefficient_index]
            ),
            "ranking": ranking,
        },
        "qbit_replay": {"split_gain_qbits": split_gains},
        "exact_replay": {
            "full": exact_full,
            "holdout": exact_holdout,
            "full_saved_bytes_per_1m_raw": full_rate,
            "holdout_saved_bytes_per_proportional_1m_raw": holdout_rate,
            "holdout_block_audit": block_audit,
            "candidate_payload_artifact": artifact(args.candidate_payload)
            if args.candidate_payload is not None
            else None,
            "candidate_p1_artifact": artifact(args.candidate_p1)
            if args.candidate_p1 is not None
            else None,
        },
        "economics": {
            "remaining_debt_bytes_per_1m": args.remaining_debt_bytes_per_1m,
            "provisional_code_bytes": args.provisional_code_bytes,
            "required_incremental_bytes_per_1m": required_rate,
            "full_and_holdout_clear_required_rate": economics_ok,
        },
        "guardrails": {
            "regret_budget_pass": regret_ok,
            "max_regressing_blocks": args.max_regressing_blocks,
            "max_largest_regression_bytes": args.max_largest_regression_bytes,
            "max_total_regression_bytes": args.max_total_regression_bytes,
        },
        "verdict": verdict,
        "claim_boundary": (
            "This is an exact arithmetic replay over an observation-only 1M "
            "trace. It is not a native integration or a full-enwik9 score."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer0-trace", type=Path, required=True)
    parser.add_argument("--base-p1", type=Path, required=True)
    parser.add_argument("--base-archive", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--raw-scope-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-payload", type=Path)
    parser.add_argument("--candidate-p1", type=Path)
    parser.add_argument("--instrumented-archive", type=Path)
    parser.add_argument("--reference-native-archive", type=Path)
    parser.add_argument("--instrumented-pair-trace", type=Path)
    parser.add_argument("--reference-pair-trace", type=Path)
    parser.add_argument("--dev-start-ppm", type=int, default=600_000)
    parser.add_argument("--holdout-start-ppm", type=int, default=800_000)
    parser.add_argument("--coefficients", type=int, nargs="+", default=DEFAULT_COEFFICIENTS)
    parser.add_argument("--chunk-rows", type=int, default=50_000)
    parser.add_argument("--holdout-blocks", type=int, default=16)
    parser.add_argument("--remaining-debt-bytes-per-1m", type=float, default=57.404)
    parser.add_argument("--provisional-code-bytes", type=int, default=12_000)
    parser.add_argument("--max-regressing-blocks", type=int, default=2)
    parser.add_argument("--max-largest-regression-bytes", type=int, default=2)
    parser.add_argument("--max-total-regression-bytes", type=int, default=3)
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
