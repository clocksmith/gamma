#!/usr/bin/env python3
"""Causally train and freeze a compact calibration table for an aux trace.

The table chooses a fixed integer-logit blend from decoder-available base and
auxiliary probability buckets plus bit position.  It accumulates losses only
over the initial training prefix, freezes once, and is then exact-replayed on
development and sealed holdout rows.  It is a bounded endpoint calibration,
not an oracle or a block selector.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from typing import Any

import numpy as np

from cmix_aux_logit_blend_screen import (
    PAIR_HEADER_BYTES,
    PAIR_MAGIC,
    P1_HEADER_BYTES,
    PPM,
    exact_block_audit,
    exact_replay,
    mix_native_q16_grid,
    qbit_tables,
)
from fx2_attribution_external_base_screen import artifact, read_p1_header


def read_pair_rows(path: Path) -> int:
    with path.open("rb") as stream:
        header = stream.read(PAIR_HEADER_BYTES)
    if len(header) != PAIR_HEADER_BYTES or header[:8] != PAIR_MAGIC:
        raise ValueError("invalid auxiliary pair trace")
    rows = struct.unpack_from("<Q", header, 8)[0]
    if rows < 1 or path.stat().st_size != PAIR_HEADER_BYTES + 4 * rows:
        raise ValueError("auxiliary pair trace length mismatch")
    return rows


def probability_bucket(values: np.ndarray, buckets: int) -> np.ndarray:
    return np.minimum(buckets - 1, values.astype(np.uint32) * buckets // 65536)


def context_ids(
    base: np.ndarray, endpoint: np.ndarray, start_row: int, base_buckets: int,
    endpoint_buckets: int,
) -> np.ndarray:
    base_id = probability_bucket(base, base_buckets)
    endpoint_id = probability_bucket(endpoint, endpoint_buckets)
    bit_position = np.arange(start_row, start_row + len(base), dtype=np.uint32) & 7
    return ((base_id * endpoint_buckets + endpoint_id) * 8 + bit_position).astype(np.int64)


def mixed_grid(
    base: np.ndarray, endpoint: np.ndarray, weights: tuple[int, ...]
) -> np.ndarray:
    nonzero = tuple(weight for weight in weights if weight)
    output = np.empty((len(base), len(weights)), dtype=np.uint16)
    for index, weight in enumerate(weights):
        if weight == 0:
            output[:, index] = base
    if nonzero:
        grid = mix_native_q16_grid(base, endpoint, nonzero)
        for grid_index, weight in enumerate(nonzero):
            output[:, weights.index(weight)] = grid[:, grid_index]
    return output


def choose_weights(
    losses: np.ndarray, support: np.ndarray, min_support: int,
    min_advantage_qbits: int,
) -> np.ndarray:
    selected = np.zeros(len(support), dtype=np.int16)
    for context in range(len(support)):
        if support[context] < min_support:
            continue
        row = losses[context]
        choice = int(np.argmin(row))
        if choice and row[0] - row[choice] >= min_advantage_qbits:
            selected[context] = choice
    return selected


def write_p1(path: Path, values: np.ndarray) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        stream.write(b"CMX21P1\0")
        stream.write(struct.pack("<Q", len(values)))
        stream.write(np.asarray(values, dtype="<u2").tobytes())
    return artifact(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(args: argparse.Namespace) -> dict[str, Any]:
    if not 0 < args.train_end_ppm < args.holdout_start_ppm < PPM:
        raise ValueError("train and holdout boundaries must be ordered")
    weights = tuple(sorted(set(args.weights)))
    if not weights or weights[0] != 0 or any(weight < 0 or weight >= PPM for weight in weights):
        raise ValueError("weights must include zero and remain within 0..999999")
    rows = read_pair_rows(args.pair_trace)
    _, p1_rows = read_p1_header(args.base_p1)
    if rows != p1_rows:
        raise ValueError("pair trace and base P1 rows differ")
    store = args.wrt_store.read_bytes()
    if len(store) < 5 or (len(store) - 5) * 8 != rows:
        raise ValueError("WRT store and pair trace do not align")
    truth = np.unpackbits(np.frombuffer(store, dtype=np.uint8, offset=5), bitorder="big")
    pair = np.memmap(
        args.pair_trace, dtype="<u2", mode="r", offset=PAIR_HEADER_BYTES,
        shape=(rows, 2),
    )
    frozen_base = np.memmap(
        args.base_p1, dtype="<u2", mode="r", offset=P1_HEADER_BYTES, shape=(rows,)
    )
    base = np.asarray(pair[:, 0], dtype=np.uint16)
    endpoint = np.asarray(pair[:, 1], dtype=np.uint16)
    if not np.array_equal(base, frozen_base):
        raise ValueError("pair base column differs from frozen base P1")
    train_end = rows * args.train_end_ppm // PPM
    holdout_start = rows * args.holdout_start_ppm // PPM
    context_count = args.base_buckets * args.endpoint_buckets * 8
    losses = np.zeros((context_count, len(weights)), dtype=np.int64)
    support = np.zeros(context_count, dtype=np.uint32)
    loss0, loss1 = qbit_tables()
    for start in range(0, train_end, args.chunk_rows):
        end = min(train_end, start + args.chunk_rows)
        local_base = base[start:end]
        local_endpoint = endpoint[start:end]
        ids = context_ids(
            local_base, local_endpoint, start, args.base_buckets, args.endpoint_buckets
        )
        support += np.bincount(ids, minlength=context_count).astype(np.uint32)
        mixed = mixed_grid(local_base, local_endpoint, weights)
        bits = truth[start:end]
        for index in range(len(weights)):
            qbits = np.where(bits, loss1[mixed[:, index]], loss0[mixed[:, index]])
            np.add.at(losses[:, index], ids, qbits.astype(np.int64))
    selected = choose_weights(
        losses, support, args.min_support, args.min_advantage_qbits
    )
    candidate = np.asarray(base, dtype=np.uint16).copy()
    for start in range(train_end, rows, args.chunk_rows):
        end = min(rows, start + args.chunk_rows)
        local_base = base[start:end]
        local_endpoint = endpoint[start:end]
        ids = context_ids(
            local_base, local_endpoint, start, args.base_buckets, args.endpoint_buckets
        )
        choices = selected[ids]
        mixed = mixed_grid(local_base, local_endpoint, weights)
        candidate[start:end] = mixed[np.arange(end - start), choices]
    full, _base_payload, candidate_payload = exact_replay(truth, base, candidate)
    development, _, _ = exact_replay(
        truth[train_end:holdout_start],
        base[train_end:holdout_start],
        candidate[train_end:holdout_start],
    )
    heldout, _, _ = exact_replay(
        truth[holdout_start:], base[holdout_start:], candidate[holdout_start:]
    )
    block_audit = exact_block_audit(
        truth[holdout_start:], base[holdout_start:], candidate[holdout_start:],
        args.holdout_blocks,
    )
    args.candidate_payload.parent.mkdir(parents=True, exist_ok=True)
    args.candidate_payload.write_bytes(candidate_payload)
    chosen_weights = {
        str(weights[index]): int(np.count_nonzero(selected == index))
        for index in range(len(weights))
    }
    full_rate = full["saved_bytes"] * 1_000_000 / args.raw_scope_bytes
    holdout_raw_bytes = (rows - holdout_start) / 8
    holdout_rate = (
        heldout["saved_bytes"] * 1_000_000 / holdout_raw_bytes
        if holdout_raw_bytes else 0.0
    )
    payload = {
        "schema": "cmix_aux_bucket_calibration_v1",
        "evidence_level": "causal_prefix_trained_auxiliary_replay",
        "claim_boundary": (
            "Frozen-prefix calibration over a paired trace. Native integration, "
            "incremental source accounting, roundtrip, resources, disjoint "
            "confirmation, and full-corpus official accounting remain required."
        ),
        "promotion_authorized": False,
        "inputs": {
            "pair_trace": artifact(args.pair_trace),
            "base_p1": artifact(args.base_p1),
            "base_archive": artifact(args.base_archive),
            "wrt_store": artifact(args.wrt_store),
        },
        "identity": {
            "base_column_matches_frozen_p1": True,
            "table_updates_only_before_freeze": True,
            "route_is_fixed_after_train_prefix": True,
            "route_uses_decoder_available_probabilities_and_bit_position": True,
        },
        "scope": {
            "raw_bytes": args.raw_scope_bytes,
            "rows": rows,
            "train_end_row": train_end,
            "holdout_start_row": holdout_start,
        },
        "router": {
            "base_buckets": args.base_buckets,
            "endpoint_buckets": args.endpoint_buckets,
            "contexts": context_count,
            "contexts_with_training_support": int(np.count_nonzero(support)),
            "contexts_with_nonbase_choice": int(np.count_nonzero(selected)),
            "minimum_training_support": args.min_support,
            "minimum_training_advantage_qbits": args.min_advantage_qbits,
            "weights_ppm": list(weights),
            "selected_context_counts_by_weight": chosen_weights,
            "estimated_dynamic_state_bytes": int(losses.nbytes + support.nbytes + selected.nbytes),
        },
        "exact_replay": {
            "full": full,
            "development": development,
            "holdout": heldout,
            "holdout_block_audit": block_audit,
            "full_saved_bytes_per_1m_raw": full_rate,
            "holdout_saved_bytes_per_1m_raw": holdout_rate,
            "candidate_payload": artifact(args.candidate_payload),
            "candidate_p1": write_p1(args.candidate_p1, candidate),
        },
        "economics": {
            "required_incremental_bytes_per_1m": args.required_incremental_bytes_per_1m,
            "full_and_holdout_clear_required_incremental": (
                full_rate >= args.required_incremental_bytes_per_1m
                and holdout_rate >= args.required_incremental_bytes_per_1m
            ),
        },
        "verdict": (
            "candidate_for_native_integration"
            if full_rate >= args.required_incremental_bytes_per_1m
            and holdout_rate >= args.required_incremental_bytes_per_1m
            else "insufficient_calibrated_auxiliary_margin"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Train/freeze a compact paired-endpoint calibration table."
    )
    parser.add_argument("--pair-trace", type=Path, required=True)
    parser.add_argument("--base-p1", type=Path, required=True)
    parser.add_argument("--base-archive", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--raw-scope-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-payload", type=Path, required=True)
    parser.add_argument("--candidate-p1", type=Path, required=True)
    parser.add_argument("--train-end-ppm", type=int, default=200_000)
    parser.add_argument("--holdout-start-ppm", type=int, default=800_000)
    parser.add_argument("--base-buckets", type=int, default=8)
    parser.add_argument("--endpoint-buckets", type=int, default=8)
    parser.add_argument("--min-support", type=int, default=128)
    parser.add_argument("--min-advantage-qbits", type=int, default=512)
    parser.add_argument(
        "--weights", type=int, nargs="+", default=[0, 10_000, 20_000, 40_000, 60_000, 80_000, 100_000]
    )
    parser.add_argument("--chunk-rows", type=int, default=262_144)
    parser.add_argument("--holdout-blocks", type=int, default=16)
    parser.add_argument("--required-incremental-bytes-per-1m", type=float, default=69.404)
    args = parser.parse_args()
    payload = run(args)
    print(payload["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
