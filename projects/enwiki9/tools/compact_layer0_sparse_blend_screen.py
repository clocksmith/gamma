#!/usr/bin/env python3
"""Fit one sparse fixed-point blend of compact layer-0 endpoints over endpoint428."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import struct
import sys
from typing import Any

import numpy as np


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from cmix_aux_logit_blend_screen import native_logit_table
from compact_layer0_blend_screen import (
    LAYER0_NAMES,
    PACKED_HEADER_BYTES,
    endpoint_name,
    read_packed_header,
    same_file,
)
from fx2_attribution_external_base_screen import (
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


DEFAULT_RIDGES = (0.01, 0.1, 1.0)
DEFAULT_SPARSITIES = (2, 4, 8, 16, 26)
LOG2_Q16_TO_NATURAL = math.log(2.0) / 65536.0


def probabilities_from_logits(logits: np.ndarray) -> np.ndarray:
    clipped = np.clip(logits, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def native_probability_from_target_logit(target: np.ndarray) -> np.ndarray:
    table = native_logit_table()
    raw_high = np.searchsorted(table[1:], target, side="left") + 1
    high = np.clip(raw_high, 1, PROBABILITY_TOTAL - 1)
    low = high - 1
    low_distance = target - table[low]
    high_distance = table[high] - target
    mixed = np.where(low_distance <= high_distance, low, high)
    mixed = np.where(raw_high <= 1, 1, mixed)
    mixed = np.where(raw_high >= PROBABILITY_TOTAL, PROBABILITY_TOTAL - 1, mixed)
    return mixed.astype(np.uint16)


def mix_sparse_native_q16(
    base: np.ndarray,
    endpoints: np.ndarray,
    coefficients_ppm: np.ndarray,
) -> np.ndarray:
    """Apply a deterministic signed multivariate correction in native logit space."""

    base_values = np.asarray(base, dtype=np.uint16)
    endpoint_values = np.asarray(endpoints, dtype=np.uint16)
    coefficients = np.asarray(coefficients_ppm, dtype=np.int64)
    if endpoint_values.ndim != 2 or endpoint_values.shape[0] != base_values.shape[0]:
        raise ValueError("endpoint matrix does not align with base probabilities")
    if coefficients.shape != (endpoint_values.shape[1],):
        raise ValueError("coefficient vector does not align with endpoints")
    if np.any(base_values == 0) or np.any(endpoint_values == 0):
        raise ValueError("probabilities must be within 1..65535")
    if np.any(np.abs(coefficients) >= PPM):
        raise ValueError("each signed coefficient must be within (-1000000, 1000000)")

    table = native_logit_table()
    base_logits = table[base_values].astype(np.int64)
    endpoint_logits = table[endpoint_values].astype(np.int64)
    correction = np.sum(
        (endpoint_logits - base_logits[:, None]) * coefficients[None, :],
        axis=1,
        dtype=np.int64,
    )
    target = base_logits + np.floor_divide(correction + PPM // 2, PPM)
    return native_probability_from_target_logit(target)


def fit_newton_coefficients(
    base: np.ndarray,
    endpoints: np.ndarray,
    truth: np.ndarray,
    *,
    ridge: float,
    iterations: int,
    chunk_rows: int,
) -> np.ndarray:
    """Fit static residual-logit coefficients using training rows only."""

    if ridge <= 0 or iterations < 1 or chunk_rows < 1:
        raise ValueError("ridge, iterations, and chunk rows must be positive")
    rows, endpoint_count = endpoints.shape
    if base.shape != (rows,) or truth.shape != (rows,):
        raise ValueError("training arrays do not align")
    table = native_logit_table()
    coefficients = np.zeros(endpoint_count, dtype=np.float64)

    for _ in range(iterations):
        gradient = ridge * coefficients
        hessian = np.eye(endpoint_count, dtype=np.float64) * ridge
        for start in range(0, rows, chunk_rows):
            end = min(rows, start + chunk_rows)
            base_logits = (
                table[np.asarray(base[start:end], dtype=np.uint16)].astype(np.float64)
                * LOG2_Q16_TO_NATURAL
            )
            endpoint_logits = (
                table[np.asarray(endpoints[start:end], dtype=np.uint16)].astype(np.float64)
                * LOG2_Q16_TO_NATURAL
            )
            features = endpoint_logits - base_logits[:, None]
            candidate_logits = base_logits + features @ coefficients
            probability = probabilities_from_logits(candidate_logits)
            local_truth = np.asarray(truth[start:end], dtype=np.float64)
            gradient += features.T @ (probability - local_truth)
            weight = probability * (1.0 - probability)
            hessian += features.T @ (features * weight[:, None])
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(hessian, gradient, rcond=1e-12)[0]
        coefficients -= step
        coefficients = np.clip(coefficients, -0.95, 0.95)
        if float(np.max(np.abs(step))) < 1e-7:
            break
    return coefficients


def quantized_sparse_candidates(
    fitted: np.ndarray,
    *,
    ridge: float,
    sparsities: tuple[int, ...],
    quantum_ppm: int,
) -> list[dict[str, Any]]:
    """Derive nested sparse candidates without consulting development rows."""

    if quantum_ppm < 1:
        raise ValueError("quantum must be positive")
    order = np.argsort(-np.abs(fitted), kind="stable")
    candidates: list[dict[str, Any]] = []
    for requested in sparsities:
        count = min(max(1, requested), fitted.shape[0])
        selected = order[:count]
        coefficients = np.zeros(fitted.shape[0], dtype=np.int64)
        coefficients[selected] = (
            np.rint(fitted[selected] * PPM / quantum_ppm).astype(np.int64)
            * quantum_ppm
        )
        coefficients = np.clip(coefficients, -PPM + 1, PPM - 1)
        nonzero = int(np.count_nonzero(coefficients))
        if nonzero == 0:
            continue
        candidates.append(
            {
                "ridge": ridge,
                "requested_sparsity": requested,
                "nonzero_count": nonzero,
                "coefficients_ppm": coefficients,
            }
        )
    return candidates


def qbit_gain(
    truth: np.ndarray,
    base: np.ndarray,
    candidate: np.ndarray,
) -> int:
    loss0, loss1 = qbit_tables()
    return int(
        (
            np.where(truth, loss1[base], loss0[base])
            - np.where(truth, loss1[candidate], loss0[candidate])
        ).sum(dtype=np.int64)
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    if not 0 < args.dev_start_ppm < args.holdout_start_ppm < PPM:
        raise ValueError("split boundaries must be ordered")
    if args.raw_scope_bytes < 1 or args.quantum_ppm < 1:
        raise ValueError("raw scope and quantum must be positive")
    ridges = tuple(sorted(set(args.ridges)))
    sparsities = tuple(sorted(set(args.sparsities)))
    if not ridges or min(ridges) <= 0 or not sparsities or min(sparsities) < 1:
        raise ValueError("ridge and sparsity grids must be nonempty and positive")

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

    trained: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for ridge in ridges:
        fitted = fit_newton_coefficients(
            base[:dev_start],
            endpoints[:dev_start],
            truth[:dev_start],
            ridge=ridge,
            iterations=args.newton_iterations,
            chunk_rows=args.chunk_rows,
        )
        trained.append(
            {
                "ridge": ridge,
                "coefficients": fitted.tolist(),
                "max_absolute_coefficient": float(np.max(np.abs(fitted))),
            }
        )
        candidates.extend(
            quantized_sparse_candidates(
                fitted,
                ridge=ridge,
                sparsities=sparsities,
                quantum_ppm=args.quantum_ppm,
            )
        )

    dev_truth = truth[dev_start:holdout_start]
    dev_base = np.asarray(base[dev_start:holdout_start], dtype=np.uint16)
    dev_endpoints = np.asarray(
        endpoints[dev_start:holdout_start], dtype=np.uint16
    )
    for candidate in candidates:
        candidate_probability = mix_sparse_native_q16(
            dev_base,
            dev_endpoints,
            candidate["coefficients_ppm"],
        )
        candidate["dev_gain_qbits"] = qbit_gain(
            dev_truth, dev_base, candidate_probability
        )
    selected = max(candidates, key=lambda item: item["dev_gain_qbits"])
    selected_coefficients = selected["coefficients_ppm"]

    full_candidate = np.empty(rows, dtype=np.uint16)
    for start in range(0, rows, args.chunk_rows):
        end = min(rows, start + args.chunk_rows)
        full_candidate[start:end] = mix_sparse_native_q16(
            np.asarray(base[start:end], dtype=np.uint16),
            np.asarray(endpoints[start:end], dtype=np.uint16),
            selected_coefficients,
        )

    split_gains: dict[str, int] = {}
    for name, start, end in (
        ("train", 0, dev_start),
        ("dev", dev_start, holdout_start),
        ("holdout", holdout_start, rows),
    ):
        split_gains[name] = qbit_gain(
            truth[start:end],
            np.asarray(base[start:end], dtype=np.uint16),
            full_candidate[start:end],
        )

    exact_full, replayed_base_payload, candidate_payload = exact_replay(
        truth, base, full_candidate
    )
    exact_holdout, _, _ = exact_replay(
        truth[holdout_start:],
        base[holdout_start:],
        full_candidate[holdout_start:],
    )
    block_audit = exact_block_audit(
        truth[holdout_start:],
        base[holdout_start:],
        full_candidate[holdout_start:],
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
    identities_ok = bool(
        archive_payload_identity
        and native_archive_identity is not False
        and pair_trace_identity is not False
    )

    if args.candidate_payload is not None:
        args.candidate_payload.parent.mkdir(parents=True, exist_ok=True)
        args.candidate_payload.write_bytes(candidate_payload)
    if args.candidate_p1 is not None:
        args.candidate_p1.parent.mkdir(parents=True, exist_ok=True)
        args.candidate_p1.write_bytes(
            b"CMX21P1\0"
            + struct.pack("<Q", rows)
            + np.asarray(full_candidate, dtype="<u2").tobytes()
        )

    full_rate = exact_full["saved_bytes"] * 1_000_000 / args.raw_scope_bytes
    holdout_raw_scope = args.raw_scope_bytes * (PPM - args.holdout_start_ppm) / PPM
    holdout_rate = exact_holdout["saved_bytes"] * 1_000_000 / holdout_raw_scope
    required_rate = (
        args.remaining_debt_bytes_per_1m + args.provisional_code_bytes / 1000
    )
    regret_ok = bool(
        block_audit["regressing_blocks"] <= args.max_regressing_blocks
        and block_audit["largest_regression_bytes"] <= args.max_largest_regression_bytes
        and block_audit["total_regression_bytes"] <= args.max_total_regression_bytes
    )
    economics_ok = full_rate >= required_rate and holdout_rate >= required_rate

    coefficient_rows = [
        {
            "endpoint_index": index,
            "endpoint_name": endpoint_name(index, endpoint_count),
            "coefficient_ppm": int(value),
        }
        for index, value in enumerate(selected_coefficients)
        if value != 0
    ]
    candidate_rows = [
        {
            "ridge": item["ridge"],
            "requested_sparsity": item["requested_sparsity"],
            "nonzero_count": item["nonzero_count"],
            "dev_gain_qbits": item["dev_gain_qbits"],
        }
        for item in sorted(
            candidates, key=lambda item: item["dev_gain_qbits"], reverse=True
        )
    ]
    verdict = (
        "compact_layer0_sparse_blend_pass_requires_native_integration"
        if identities_ok and regret_ok and economics_ok
        else "retire_static_compact_layer0_sparse_blend"
    )
    return {
        "schema": "compact_layer0_sparse_blend_screen_v1",
        "evidence_level": "train_fitted_dev_selected_exact_causal_shadow",
        "hypothesis": (
            "A sparse signed blend of already-computed compact layer-0 endpoints "
            "retains enough residual gain over endpoint428 to close its counted debt."
        ),
        "inputs": {
            "layer0_trace": artifact(args.layer0_trace),
            "base_p1": artifact(args.base_p1),
            "base_archive": artifact(args.base_archive),
            "wrt_store": artifact(args.wrt_store),
        },
        "scope": {
            "raw_bytes": args.raw_scope_bytes,
            "rows": rows,
            "endpoint_count": endpoint_count,
            "train_end_row": dev_start,
            "dev_end_row": holdout_start,
            "selection_reads_holdout": False,
        },
        "identity": {
            "base_archive_payload_identity": archive_payload_identity,
            "instrumented_archive_byte_identity": native_archive_identity,
            "instrumented_pair_trace_byte_identity": pair_trace_identity,
            "all_required_identities_pass": identities_ok,
        },
        "training": {
            "ridges": list(ridges),
            "sparsities": list(sparsities),
            "quantum_ppm": args.quantum_ppm,
            "newton_iterations": args.newton_iterations,
            "fits": trained,
        },
        "selection": {
            "selected_ridge": selected["ridge"],
            "selected_requested_sparsity": selected["requested_sparsity"],
            "selected_nonzero_count": selected["nonzero_count"],
            "selected_dev_gain_qbits": selected["dev_gain_qbits"],
            "coefficients": coefficient_rows,
            "candidate_ranking": candidate_rows,
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
    parser.add_argument("--ridges", type=float, nargs="+", default=DEFAULT_RIDGES)
    parser.add_argument(
        "--sparsities", type=int, nargs="+", default=DEFAULT_SPARSITIES
    )
    parser.add_argument("--quantum-ppm", type=int, default=1_000)
    parser.add_argument("--newton-iterations", type=int, default=6)
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
