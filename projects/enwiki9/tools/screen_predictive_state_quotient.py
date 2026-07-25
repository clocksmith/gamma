#!/usr/bin/env python3
"""Screen finite-state quotients of an endpoint428 recurrent-state trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


MAGIC = b"DPLRST2\0"
HEADER = struct.Struct("<8s5I")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_sizes(value: str) -> list[int]:
    result = [int(part) for part in value.split(",")]
    if not result or any(size < 2 for size in result):
        raise argparse.ArgumentTypeError("state counts must be at least 2")
    return result


def assign(points: np.ndarray, centers: np.ndarray, chunk: int = 4096) -> np.ndarray:
    result = np.empty(len(points), dtype=np.int32)
    center_norm = np.sum(centers * centers, axis=1)
    for start in range(0, len(points), chunk):
        part = points[start : start + chunk]
        distance = (
            np.sum(part * part, axis=1)[:, None]
            + center_norm[None, :]
            - 2.0 * part @ centers.T
        )
        result[start : start + len(part)] = np.argmin(distance, axis=1)
    return result


def train_kmeans(
    points: np.ndarray,
    states: int,
    iterations: int,
    batch_rows: int,
    rng: np.random.Generator,
) -> np.ndarray:
    centers = points[rng.choice(len(points), states, replace=False)].copy()
    counts = np.zeros(states, dtype=np.float64)
    for _ in range(iterations):
        indices = rng.integers(0, len(points), size=min(batch_rows, len(points)))
        batch = points[indices]
        labels = assign(batch, centers)
        sums = np.zeros_like(centers)
        batch_counts = np.bincount(labels, minlength=states).astype(np.float64)
        np.add.at(sums, labels, batch)
        active = batch_counts > 0
        old = counts[active]
        new = batch_counts[active]
        centers[active] = (
            centers[active] * old[:, None] + sums[active]
        ) / (old + new)[:, None]
        counts[active] += new
    return centers


def majority_map(keys: np.ndarray, targets: np.ndarray) -> tuple[dict[int, int], int]:
    order = np.lexsort((targets, keys))
    sorted_keys = keys[order]
    sorted_targets = targets[order]
    mapping: dict[int, int] = {}
    entries = 0
    start = 0
    while start < len(order):
        end = start + 1
        key = int(sorted_keys[start])
        while end < len(order) and int(sorted_keys[end]) == key:
            end += 1
        values, counts = np.unique(sorted_targets[start:end], return_counts=True)
        mapping[key] = int(values[np.argmax(counts)])
        entries += 1
        start = end
    return mapping, entries


def predict_transitions(
    codes: np.ndarray,
    events: np.ndarray,
    train_end: int,
    state_count: int,
    event_mask: int,
) -> dict[str, object]:
    source = codes[: train_end - 1].astype(np.int64)
    target = codes[1:train_end].astype(np.int64)
    state_keys = source
    event_keys = (source << 16) | (events[1:train_end].astype(np.int64) & event_mask)
    state_map, state_entries = majority_map(state_keys, target)
    event_map, event_entries = majority_map(event_keys, target)

    fallback = np.arange(state_count, dtype=np.int32)
    for key, value in state_map.items():
        fallback[key] = value

    def evaluate(start: int, end: int) -> dict[str, object]:
        actual_source = codes[start : end - 1].astype(np.int64)
        actual_target = codes[start + 1 : end].astype(np.int64)
        actual_event = events[start + 1 : end].astype(np.int64) & event_mask
        predicted = np.empty(len(actual_target), dtype=np.int32)
        hits = 0
        for index, (state, event) in enumerate(zip(actual_source, actual_event)):
            key = (int(state) << 16) | int(event)
            prediction = event_map.get(key, int(fallback[state]))
            predicted[index] = prediction
            hits += prediction == int(actual_target[index])

        rolled = int(codes[start])
        rollout_hits = 0
        first_divergence = None
        for index, event in enumerate(actual_event):
            key = (rolled << 16) | int(event)
            rolled = event_map.get(key, int(fallback[rolled]))
            expected = int(actual_target[index])
            if rolled == expected:
                rollout_hits += 1
            elif first_divergence is None:
                first_divergence = index + 1
        return {
            "transitions": len(actual_target),
            "teacher_forced_accuracy": hits / len(actual_target),
            "continuous_rollout_accuracy": rollout_hits / len(actual_target),
            "first_rollout_divergence": first_divergence,
        }

    return {
        "state_transition_entries": state_entries,
        "event_transition_entries": event_entries,
        "event_mask": event_mask,
        "development": evaluate(train_end, (train_end + len(codes)) // 2),
        "holdout": evaluate((train_end + len(codes)) // 2, len(codes)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--states", type=parse_sizes, default=[64, 256, 1024])
    parser.add_argument("--pca-dims", type=int, default=16)
    parser.add_argument("--pca-rows", type=int, default=20000)
    parser.add_argument("--iterations", type=int, default=24)
    parser.add_argument("--batch-rows", type=int, default=4096)
    parser.add_argument("--train-fraction", type=float, default=0.7)
    parser.add_argument("--event-mask", type=lambda value: int(value, 0), default=0xFF)
    parser.add_argument("--seed", type=int, default=428)
    args = parser.parse_args()

    with args.trace.open("rb") as source:
        header = source.read(HEADER.size)
    magic, version, feature_count, cells, row_bytes, flags = HEADER.unpack(header)
    header_bytes = HEADER.size
    if magic != MAGIC or version != 2 or cells != 112:
        raise ValueError("unsupported state trace")
    dtype = np.dtype(
        [
            ("event", "<u4"),
            ("x", "<f4", (feature_count,)),
            ("h0", "<f4", (cells,)),
            ("c0", "<f4", (cells,)),
            ("h1", "<f4", (cells,)),
            ("c1", "<f4", (cells,)),
        ]
    )
    if dtype.itemsize != row_bytes:
        raise ValueError("state trace row size mismatch")
    rows = (args.trace.stat().st_size - header_bytes) // row_bytes
    trace = np.memmap(
        args.trace, mode="r", dtype=dtype, offset=header_bytes, shape=(rows,)
    )
    state = np.concatenate(
        [trace["h0"], trace["c0"], trace["h1"], trace["c1"]], axis=1
    ).astype(np.float32)
    events = np.asarray(trace["event"], dtype=np.uint32)
    train_end = int(rows * args.train_fraction)
    rng = np.random.default_rng(args.seed)

    sample_indices = np.linspace(
        0, train_end - 1, min(args.pca_rows, train_end), dtype=np.int64
    )
    sample = state[sample_indices].astype(np.float64)
    mean = sample.mean(axis=0)
    centered = sample - mean
    covariance = centered.T @ centered / len(centered)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    basis = eigenvectors[:, -args.pca_dims :]
    projected = ((state - mean) @ basis).astype(np.float32)
    total_variance = float(np.var(state, axis=0).sum())
    retained_variance = float(eigenvalues[-args.pca_dims :].sum())

    screens = []
    for state_count in args.states:
        centers = train_kmeans(
            projected[:train_end],
            state_count,
            args.iterations,
            args.batch_rows,
            rng,
        )
        codes = assign(projected, centers)
        residual = projected - centers[codes]
        quotient = predict_transitions(
            codes, events, train_end, state_count, args.event_mask
        )
        quotient.update(
            {
                "states": state_count,
                "projected_quantization_rmse": float(np.sqrt(np.mean(residual**2))),
                "centroid_bytes_float16": state_count * args.pca_dims * 2,
                "estimated_transition_bytes": quotient["event_transition_entries"] * 6,
            }
        )
        screens.append(quotient)
        print(json.dumps(quotient))

    result = {
        "schema": "predictive_state_quotient_screen_v1",
        "trace": {
            "path": str(args.trace.resolve()),
            "bytes": args.trace.stat().st_size,
            "sha256": sha256_file(args.trace),
            "rows": rows,
        },
        "contract": {
            "full_recurrent_state_dimensions": 4 * cells,
            "pca_dims": args.pca_dims,
            "pca_variance_fraction": retained_variance / total_variance,
            "trace_flags": flags,
            "event_condition_is_causal_trace_event": True,
            "continuous_rollout_uses_observed_causal_events": True,
        },
        "screens": screens,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
