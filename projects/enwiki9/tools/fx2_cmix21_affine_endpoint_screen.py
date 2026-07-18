#!/usr/bin/env python3
"""Fit a tiny affine-logit mixer on one matched causal endpoint trace.

This closes the gap between the fixed probability blend used by the matched
96x2 endpoint screen and the three-coefficient logistic construction used by
the earlier CMIX21 family probe.  Coefficients are fitted on the training
prefix only; development and holdout truth are used only for scoring.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
from typing import Any

import numpy as np


TRACE_MAGIC = b"CMNEST1\0"
TRACE_HEADER = struct.Struct("<8sIIIIIQ")
TRACE_VERSION = 1
P1_MAGIC = b"CMX21P1\0"
P1_HEADER_BYTES = 16
PROBABILITY_TOTAL = 65536.0
QBITS_PER_BYTE = 2048


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def load_matched_trace(
    path: pathlib.Path,
) -> tuple[np.memmap, dict[str, int]]:
    with path.open("rb") as source:
        header = source.read(TRACE_HEADER.size)
    if len(header) != TRACE_HEADER.size:
        raise ValueError("matched trace header is truncated")
    magic, version, header_bytes, row_bytes, endpoints, layer0, rows = (
        TRACE_HEADER.unpack(header)
    )
    if magic != TRACE_MAGIC or version != TRACE_VERSION:
        raise ValueError("unsupported matched trace magic/version")
    if header_bytes != TRACE_HEADER.size or row_bytes != 1 + 2 * endpoints:
        raise ValueError("matched trace row contract mismatch")
    if endpoints != 5 + layer0 or rows <= 0:
        raise ValueError("matched trace endpoint contract mismatch")
    if path.stat().st_size != header_bytes + rows * row_bytes:
        raise ValueError("matched trace size does not match its row count")
    dtype = np.dtype([("bit", "u1"), ("p", "<u2", (endpoints,))])
    trace = np.memmap(
        path, mode="r", dtype=dtype, offset=header_bytes, shape=(rows,)
    )
    return trace, {
        "rows": rows,
        "row_bytes": row_bytes,
        "endpoint_count": endpoints,
        "layer0_count": layer0,
    }


def load_external_endpoint(path: pathlib.Path, rows: int) -> np.memmap:
    with path.open("rb") as source:
        header = source.read(P1_HEADER_BYTES)
    if len(header) != P1_HEADER_BYTES or header[:8] != P1_MAGIC:
        raise ValueError("external endpoint header is invalid")
    declared_rows = int.from_bytes(header[8:16], "little")
    if declared_rows != rows or path.stat().st_size != P1_HEADER_BYTES + 2 * rows:
        raise ValueError("external endpoint row contract mismatch")
    return np.memmap(
        path, mode="r", dtype="<u2", offset=P1_HEADER_BYTES, shape=(rows,)
    )


def validate_truth(
    store_path: pathlib.Path, rows: int, trace_truth: np.ndarray
) -> None:
    if rows % 8 or store_path.stat().st_size != 5 + rows // 8:
        raise ValueError("WRT store length does not match trace rows")
    with store_path.open("rb") as source:
        if source.read(5) != b"\x80\x00\x00\x00\x00":
            raise ValueError("WRT store header is invalid")
    stream = np.memmap(
        store_path, mode="r", dtype="u1", offset=5, shape=(rows // 8,)
    )
    packed = np.packbits(np.asarray(trace_truth, dtype=np.uint8), bitorder="big")
    if not np.array_equal(packed, stream):
        raise ValueError("matched trace truth differs from WRT store")


def logit_probabilities(values: np.ndarray) -> np.ndarray:
    probabilities = values.astype(np.float64) / PROBABILITY_TOTAL
    np.clip(
        probabilities,
        1.0 / PROBABILITY_TOTAL,
        1.0 - 1.0 / PROBABILITY_TOTAL,
        out=probabilities,
    )
    return np.log(probabilities) - np.log1p(-probabilities)


def sigmoid(values: np.ndarray) -> np.ndarray:
    output = np.empty_like(values)
    positive = values >= 0
    output[positive] = 1.0 / (1.0 + np.exp(-values[positive]))
    negative_exp = np.exp(values[~positive])
    output[~positive] = negative_exp / (1.0 + negative_exp)
    return output


def fit_affine(
    base: np.ndarray,
    endpoint: np.ndarray | None,
    truth: np.ndarray,
    train_end: int,
    chunk_rows: int,
    iterations: int,
    l2: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    feature_count = 1 + int(endpoint is not None)
    total = np.zeros(feature_count, dtype=np.float64)
    total_sq = np.zeros(feature_count, dtype=np.float64)
    for start in range(0, train_end, chunk_rows):
        stop = min(train_end, start + chunk_rows)
        columns = [logit_probabilities(base[start:stop])]
        if endpoint is not None:
            columns.append(logit_probabilities(endpoint[start:stop]))
        matrix = np.column_stack(columns)
        total += matrix.sum(axis=0)
        total_sq += np.square(matrix).sum(axis=0)
    means = total / train_end
    variance = np.maximum(total_sq / train_end - np.square(means), 1e-12)
    scales = np.sqrt(variance)

    weights = np.zeros(feature_count + 1, dtype=np.float64)
    weights[0] = means[0]
    weights[1] = scales[0]
    regularizer = np.eye(feature_count + 1, dtype=np.float64)
    regularizer[0, 0] = 0.0
    for _ in range(iterations):
        gradient = l2 * (regularizer @ weights)
        hessian = l2 * regularizer
        for start in range(0, train_end, chunk_rows):
            stop = min(train_end, start + chunk_rows)
            design = np.empty((stop - start, feature_count + 1))
            design[:, 0] = 1.0
            design[:, 1] = (
                logit_probabilities(base[start:stop]) - means[0]
            ) / scales[0]
            if endpoint is not None:
                design[:, 2] = (
                    logit_probabilities(endpoint[start:stop]) - means[1]
                ) / scales[1]
            probability = sigmoid(design @ weights)
            residual = probability - truth[start:stop]
            gradient += design.T @ residual / train_end
            curvature = probability * (1.0 - probability)
            hessian += (design.T * curvature) @ design / train_end
        step = np.linalg.solve(
            hessian + np.eye(feature_count + 1) * 1e-12, gradient
        )
        weights -= step
        if float(np.max(np.abs(step))) < 1e-8:
            break
    return weights, means, scales


def rounded_qbits(probability: np.ndarray, truth: np.ndarray) -> int:
    selected = np.where(truth != 0, probability, 1.0 - probability)
    np.clip(
        selected,
        1.0 / PROBABILITY_TOTAL,
        1.0 - 1.0 / PROBABILITY_TOTAL,
        out=selected,
    )
    return int(np.rint(-np.log2(selected) * 256.0).astype(np.int64).sum())


def evaluate(
    base: np.ndarray,
    endpoint: np.ndarray | None,
    truth: np.ndarray,
    start: int,
    stop: int,
    weights: np.ndarray,
    means: np.ndarray,
    scales: np.ndarray,
    chunk_rows: int,
    block_rows: int,
    raw_scope_bytes: int,
    total_rows: int,
) -> dict[str, Any]:
    base_qbits = 0
    candidate_qbits = 0
    block_gains: list[int] = []
    block_base = 0
    block_candidate = 0
    block_position = 0
    for left in range(start, stop, chunk_rows):
        right = min(stop, left + chunk_rows)
        design = np.empty((right - left, len(weights)))
        design[:, 0] = 1.0
        design[:, 1] = (
            logit_probabilities(base[left:right]) - means[0]
        ) / scales[0]
        if endpoint is not None:
            design[:, 2] = (
                logit_probabilities(endpoint[left:right]) - means[1]
            ) / scales[1]
        candidate = sigmoid(design @ weights)
        base_probability = base[left:right].astype(np.float64) / PROBABILITY_TOTAL
        labels = truth[left:right]
        cursor = 0
        while cursor < right - left:
            take = min(block_rows - block_position, right - left - cursor)
            end = cursor + take
            base_part = rounded_qbits(base_probability[cursor:end], labels[cursor:end])
            candidate_part = rounded_qbits(candidate[cursor:end], labels[cursor:end])
            base_qbits += base_part
            candidate_qbits += candidate_part
            block_base += base_part
            block_candidate += candidate_part
            block_position += take
            cursor = end
            if block_position == block_rows:
                block_gains.append(block_base - block_candidate)
                block_base = block_candidate = block_position = 0
    if block_position:
        block_gains.append(block_base - block_candidate)
    gain_qbits = base_qbits - candidate_qbits
    proportional_raw_bytes = raw_scope_bytes * (stop - start) / total_rows
    gain_bytes = gain_qbits / QBITS_PER_BYTE
    return {
        "rows": stop - start,
        "proportional_raw_bytes": proportional_raw_bytes,
        "base_qbits": base_qbits,
        "candidate_qbits": candidate_qbits,
        "gain_qbits": gain_qbits,
        "gain_bytes": gain_bytes,
        "gain_bytes_per_1m_raw": gain_bytes * 1_000_000 / proportional_raw_bytes,
        "block_count": len(block_gains),
        "improving_blocks": sum(value > 0 for value in block_gains),
        "regressing_blocks": sum(value < 0 for value in block_gains),
        "largest_block_regression_bytes": (
            min(0, min(block_gains, default=0)) / QBITS_PER_BYTE
        ),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    trace, trace_meta = load_matched_trace(args.trace)
    rows = trace_meta["rows"]
    if not 0 < args.train_end_row < args.dev_end_row < rows:
        raise ValueError("split rows must be ordered within the trace")
    endpoint = load_external_endpoint(args.external_endpoint, rows)
    truth = np.asarray(trace["bit"], dtype=np.float64)
    validate_truth(args.store, rows, trace["bit"])
    base = trace["p"][:, args.base_endpoint]
    models: dict[str, dict[str, Any]] = {}
    for name, candidate_endpoint in (
        ("base_calibration_control", None),
        ("affine_base_plus_external", endpoint),
    ):
        weights, means, scales = fit_affine(
            base,
            candidate_endpoint,
            truth,
            args.train_end_row,
            args.chunk_rows,
            args.iterations,
            args.l2,
        )
        splits = {}
        for split, start, stop in (
            ("train", 0, args.train_end_row),
            ("dev", args.train_end_row, args.dev_end_row),
            ("holdout", args.dev_end_row, rows),
        ):
            splits[split] = evaluate(
                base,
                candidate_endpoint,
                truth,
                start,
                stop,
                weights,
                means,
                scales,
                args.chunk_rows,
                args.block_rows,
                args.raw_scope_bytes,
                rows,
            )
        models[name] = {
            "coefficient_count": len(weights),
            "weights_standardized": weights.tolist(),
            "feature_means": means.tolist(),
            "feature_scales": scales.tolist(),
            "splits": splits,
        }
    affine_rate = models["affine_base_plus_external"]["splits"]["holdout"][
        "gain_bytes_per_1m_raw"
    ]
    return {
        "schema": "fx2_cmix21_affine_endpoint_screen_v1",
        "evidence_level": "matched_trace_train_fitted_affine_qbit_shadow_nonproof",
        "inputs": {
            "trace": {
                **trace_meta,
                "path": str(args.trace),
                "sha256": sha256_file(args.trace),
            },
            "external_endpoint": {
                "path": str(args.external_endpoint),
                "sha256": sha256_file(args.external_endpoint),
            },
            "store": {
                "path": str(args.store),
                "sha256": sha256_file(args.store),
                "truth_identity": True,
            },
        },
        "scope": {
            "raw_bytes": args.raw_scope_bytes,
            "rows": rows,
            "train_end_row": args.train_end_row,
            "dev_end_row": args.dev_end_row,
            "block_rows": args.block_rows,
        },
        "fit": {
            "method": "deterministic_chunked_newton_affine_logit",
            "training_truth_only": True,
            "iterations": args.iterations,
            "l2": args.l2,
            "chunk_rows": args.chunk_rows,
        },
        "models": models,
        "required_holdout_bytes_per_1m_raw": args.required_rate,
        "verdict": (
            "affine_endpoint_clears_shadow_screen_requires_fixed_point_replay"
            if affine_rate >= args.required_rate
            else "retire_affine_matched_endpoint_insufficient_margin"
        ),
        "promotion_authorized": False,
        "claim_boundary": (
            "Train-fitted matched-trace qbit shadow only. Fixed-point coefficients, "
            "exact range-coder replay, integration bytes, native runtime, roundtrip, "
            "disjoint scope, and an official score remain unproven."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=pathlib.Path, required=True)
    parser.add_argument("--external-endpoint", type=pathlib.Path, required=True)
    parser.add_argument("--store", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--raw-scope-bytes", type=int, default=1_000_000)
    parser.add_argument("--base-endpoint", type=int, default=0)
    parser.add_argument("--train-end-row", type=int, default=2_883_561)
    parser.add_argument("--dev-end-row", type=int, default=3_844_748)
    parser.add_argument("--chunk-rows", type=int, default=131_072)
    parser.add_argument("--block-rows", type=int, default=131_072)
    parser.add_argument("--iterations", type=int, default=12)
    parser.add_argument("--l2", type=float, default=1e-5)
    parser.add_argument("--required-rate", type=float, default=500.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.output), "verdict": result["verdict"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
