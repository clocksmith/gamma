#!/usr/bin/env python3
"""Kill-gate causal context selection over matched 96x2 endpoint blends.

The endpoint blend weights are frozen by an earlier matched-trace receipt.
This probe learns only a context-to-action map on the training prefix, then
scores development and holdout rows without reading their truth during map
construction.  Every context is reconstructible from pre-bit probabilities
and the already-decoded prefix of the current WRT byte.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import struct
from typing import Any

import numpy as np


TRACE_MAGIC = b"CMNEST1\0"
TRACE_HEADER = struct.Struct("<8sIIIIIQ")
TRACE_VERSION = 1
TRACE_HEADER_BYTES = TRACE_HEADER.size
PROBABILITY_TOTAL = 1 << 16
QBITS_PER_BYTE = 256 * 8
PPM = 1_000_000


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_trace(path: pathlib.Path) -> tuple[np.memmap, dict[str, int]]:
    with path.open("rb") as source:
        header = source.read(TRACE_HEADER_BYTES)
    if len(header) != TRACE_HEADER_BYTES:
        raise ValueError("matched trace header is truncated")
    magic, version, header_bytes, row_bytes, endpoints, layer0, rows = (
        TRACE_HEADER.unpack(header)
    )
    if magic != TRACE_MAGIC or version != TRACE_VERSION:
        raise ValueError("unsupported matched trace magic/version")
    if header_bytes != TRACE_HEADER_BYTES or row_bytes != 1 + 2 * endpoints:
        raise ValueError("matched trace row contract mismatch")
    if endpoints != 5 + layer0 or rows <= 0:
        raise ValueError("matched trace endpoint contract mismatch")
    if path.stat().st_size != header_bytes + rows * row_bytes:
        raise ValueError("matched trace size does not match its row count")
    dtype = np.dtype([("bit", "u1"), ("p", "<u2", (endpoints,))])
    trace = np.memmap(path, mode="r", dtype=dtype, offset=header_bytes, shape=(rows,))
    return trace, {
        "rows": rows,
        "row_bytes": row_bytes,
        "endpoint_count": endpoints,
        "layer0_count": layer0,
    }


def load_store(path: pathlib.Path, rows: int, truth: np.ndarray) -> np.memmap:
    if rows % 8:
        raise ValueError("matched trace does not contain complete WRT bytes")
    if path.stat().st_size != 5 + rows // 8:
        raise ValueError("WRT store size does not match trace rows")
    stream = np.memmap(path, mode="r", dtype="u1", offset=5, shape=(rows // 8,))
    reconstructed = np.packbits(np.asarray(truth, dtype=np.uint8), bitorder="big")
    if not np.array_equal(reconstructed, stream):
        raise ValueError("matched trace truth differs from WRT store")
    return stream


def loss_tables() -> tuple[np.ndarray, np.ndarray]:
    loss1 = np.zeros(PROBABILITY_TOTAL, dtype=np.int32)
    loss0 = np.zeros(PROBABILITY_TOTAL, dtype=np.int32)
    one_values = np.arange(1, PROBABILITY_TOTAL, dtype=np.float64)
    zero_values = np.arange(0, PROBABILITY_TOTAL - 1, dtype=np.float64)
    loss1[1:] = np.floor(
        -np.log2(one_values / PROBABILITY_TOTAL) * 256.0 + 0.5
    ).astype(np.int32)
    loss0[:-1] = np.floor(
        -np.log2((PROBABILITY_TOTAL - zero_values) / PROBABILITY_TOTAL)
        * 256.0
        + 0.5
    ).astype(np.int32)
    return loss0, loss1


def load_actions(receipt_path: pathlib.Path, endpoint_count: int) -> list[dict[str, Any]]:
    receipt = json.loads(receipt_path.read_text())
    actions: list[dict[str, Any]] = [
        {"endpoint": 0, "weight_ppm": 0, "endpoint_name": "base_post_sse_96x2"}
    ]
    for item in receipt.get("fixed_blend_dev_ranking", []):
        endpoint = int(item["endpoint"])
        weight = int(item["weight_ppm"])
        if not weight:
            continue
        if not 0 < endpoint < endpoint_count or not 0 < weight <= PPM:
            raise ValueError("frozen endpoint action is outside the trace contract")
        actions.append(
            {
                "endpoint": endpoint,
                "weight_ppm": weight,
                "endpoint_name": str(item["endpoint_name"]),
            }
        )
    if len(actions) == 1:
        raise ValueError("endpoint receipt has no non-base fixed blend actions")
    return actions


def context_keys(
    start: int,
    stop: int,
    probabilities: np.ndarray,
    stream: np.ndarray,
) -> dict[str, np.ndarray]:
    indexes = np.arange(start, stop, dtype=np.int64)
    bit_position = indexes & 7
    pbin = (probabilities[:, 0].astype(np.uint32) >> 12).astype(np.int64)
    stored_byte = np.asarray(stream[indexes >> 3], dtype=np.uint16)
    prefix = stored_byte >> (8 - bit_position)
    prefix_state = ((1 << bit_position) - 1) + prefix
    peers = probabilities[:, 5:].astype(np.int32)
    base = probabilities[:, 0].astype(np.int32)
    vote = np.minimum(
        7, (np.count_nonzero(peers > base[:, None], axis=1) * 8) // peers.shape[1]
    )
    spread = np.minimum(
        7, (np.max(peers, axis=1) - np.min(peers, axis=1)) >> 13
    )
    return {
        "bit": bit_position,
        "bit_p16": bit_position * 16 + pbin,
        "prefix": prefix_state,
        "prefix_p16": prefix_state * 16 + pbin,
        "bit_p16_vote8_spread8": (((bit_position * 16 + pbin) * 8 + vote) * 8 + spread),
    }


def mixed_probability(
    probabilities: np.ndarray, action: dict[str, Any]
) -> np.ndarray:
    base = probabilities[:, 0].astype(np.int64)
    endpoint = int(action["endpoint"])
    if endpoint == 0:
        return base.astype(np.uint16)
    weight = int(action["weight_ppm"])
    mixed = (
        base * (PPM - weight)
        + probabilities[:, endpoint].astype(np.int64) * weight
    ) // PPM
    return np.clip(mixed, 1, PROBABILITY_TOTAL - 1).astype(np.uint16)


def qbits(
    truth: np.ndarray,
    probability: np.ndarray,
    loss0: np.ndarray,
    loss1: np.ndarray,
) -> np.ndarray:
    return np.where(truth != 0, loss1[probability], loss0[probability])


def run(args: argparse.Namespace) -> dict[str, Any]:
    trace, trace_meta = load_trace(args.trace)
    rows = trace_meta["rows"]
    truth = trace["bit"]
    stream = load_store(args.store, rows, truth)
    actions = load_actions(args.endpoint_receipt, trace_meta["endpoint_count"])
    loss0, loss1 = loss_tables()
    profiles = {
        "bit": 8,
        "bit_p16": 128,
        "prefix": 255,
        "prefix_p16": 4080,
        "bit_p16_vote8_spread8": 8192,
    }
    train_end = rows * args.train_end_ppm // PPM
    dev_end = rows * args.dev_end_ppm // PPM
    action_losses = {
        name: np.zeros((contexts, len(actions)), dtype=np.int64)
        for name, contexts in profiles.items()
    }
    context_counts = {
        name: np.zeros(contexts, dtype=np.int64)
        for name, contexts in profiles.items()
    }
    for start in range(0, train_end, args.chunk_rows):
        stop = min(train_end, start + args.chunk_rows)
        probabilities = np.asarray(trace["p"][start:stop])
        row_truth = np.asarray(truth[start:stop], dtype=np.uint8)
        keys = context_keys(start, stop, probabilities, stream)
        for name, key in keys.items():
            context_counts[name] += np.bincount(key, minlength=profiles[name])
        for action_index, action in enumerate(actions):
            row_qbits = qbits(
                row_truth,
                mixed_probability(probabilities, action),
                loss0,
                loss1,
            )
            for name, key in keys.items():
                action_losses[name][:, action_index] += np.bincount(
                    key, weights=row_qbits, minlength=profiles[name]
                ).astype(np.int64)
    selected: dict[str, np.ndarray] = {}
    for name in profiles:
        selected[name] = np.argmin(action_losses[name], axis=1)
        selected[name][context_counts[name] < args.minimum_train_rows] = 0

    def evaluate(start: int, stop: int) -> tuple[dict[str, int], dict[str, list[int]]]:
        gains = {name: 0 for name in profiles}
        block_gains = {name: [0] * args.holdout_blocks for name in profiles}
        span = max(1, stop - start)
        for left in range(start, stop, args.chunk_rows):
            right = min(stop, left + args.chunk_rows)
            probabilities = np.asarray(trace["p"][left:right])
            row_truth = np.asarray(truth[left:right], dtype=np.uint8)
            keys = context_keys(left, right, probabilities, stream)
            base_qbits = qbits(
                row_truth, probabilities[:, 0], loss0, loss1
            ).astype(np.int64)
            row_indexes = np.arange(left, right, dtype=np.int64)
            blocks = np.minimum(
                args.holdout_blocks - 1,
                ((row_indexes - start) * args.holdout_blocks) // span,
            )
            for name, mapping in selected.items():
                choices = mapping[keys[name]]
                candidate = np.empty(len(choices), dtype=np.uint16)
                for action_index, action in enumerate(actions):
                    mask = choices == action_index
                    if np.any(mask):
                        candidate[mask] = mixed_probability(
                            probabilities[mask], action
                        )
                differences = base_qbits - qbits(
                    row_truth, candidate, loss0, loss1
                ).astype(np.int64)
                gains[name] += int(differences.sum())
                block_gains[name] = [
                    old + int(value)
                    for old, value in zip(
                        block_gains[name],
                        np.bincount(
                            blocks,
                            weights=differences,
                            minlength=args.holdout_blocks,
                        ).astype(np.int64),
                    )
                ]
        return gains, block_gains

    dev_gains, _ = evaluate(train_end, dev_end)
    holdout_gains, holdout_blocks = evaluate(dev_end, rows)
    dev_raw = args.raw_scope_bytes * (dev_end - train_end) / rows
    holdout_raw = args.raw_scope_bytes * (rows - dev_end) / rows
    results = []
    for name, contexts in profiles.items():
        nonbase = int(np.count_nonzero(selected[name]))
        map_bits = nonbase * math.log2(len(actions))
        dev_bytes = dev_gains[name] / QBITS_PER_BYTE
        holdout_bytes = holdout_gains[name] / QBITS_PER_BYTE
        blocks = holdout_blocks[name]
        results.append(
            {
                "profile": name,
                "contexts": contexts,
                "trained_contexts": int(np.count_nonzero(context_counts[name])),
                "nonbase_contexts": nonbase,
                "provisional_raw_map_bytes": math.ceil(map_bits / 8),
                "dev_gain_bytes": dev_bytes,
                "dev_gain_bytes_per_1m_raw": dev_bytes * 1_000_000 / dev_raw,
                "holdout_gain_bytes": holdout_bytes,
                "holdout_gain_bytes_per_1m_raw": (
                    holdout_bytes * 1_000_000 / holdout_raw
                ),
                "holdout_block_regressions": sum(value < 0 for value in blocks),
                "largest_holdout_block_regression_bytes": (
                    max((-value for value in blocks if value < 0), default=0)
                    / QBITS_PER_BYTE
                ),
            }
        )
    best = max(results, key=lambda item: item["dev_gain_bytes_per_1m_raw"])
    verdict = (
        "contextual_endpoint_screen_pass_requires_exact_online_replay"
        if best["holdout_gain_bytes_per_1m_raw"] >= args.required_rate
        else "retire_measured_contextual_endpoint_universe_insufficient_margin"
    )
    return {
        "schema": "fx2_cmix21_contextual_endpoint_screen_v1",
        "evidence_level": "matched_trace_train_fitted_qbit_shadow_nonproof",
        "inputs": {
            "trace": {**trace_meta, "path": str(args.trace), "sha256": sha256_file(args.trace)},
            "store": {"path": str(args.store), "sha256": sha256_file(args.store), "truth_identity": True},
            "endpoint_receipt": {"path": str(args.endpoint_receipt), "sha256": sha256_file(args.endpoint_receipt)},
        },
        "scope": {
            "raw_bytes": args.raw_scope_bytes,
            "train_end_row": train_end,
            "dev_end_row": dev_end,
            "rows": rows,
            "holdout_blocks": args.holdout_blocks,
        },
        "selection_contract": {
            "context_map_uses_training_truth_only": True,
            "minimum_train_rows": args.minimum_train_rows,
            "action_weights_frozen_by_endpoint_receipt_dev": True,
            "holdout_truth_unused_until_final_scoring": True,
        },
        "actions": actions,
        "results": results,
        "selected_on_dev": best,
        "economics": {
            "required_holdout_bytes_per_1m_raw": args.required_rate,
            "payload_is_provisional": True,
        },
        "causality": (
            "contexts use only pre-bit endpoint probabilities, bit position, "
            "already-decoded current-byte prefix, and pre-bit endpoint vote/spread"
        ),
        "verdict": verdict,
        "promotion_authorized": False,
        "claim_boundary": (
            "Matched qbit shadow kill-gate only; not an online mixer, exact range "
            "archive, native integration, roundtrip, full-corpus score, or 10.95 percent claim."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=pathlib.Path, required=True)
    parser.add_argument("--store", type=pathlib.Path, required=True)
    parser.add_argument("--endpoint-receipt", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--raw-scope-bytes", type=int, required=True)
    parser.add_argument("--train-end-ppm", type=int, default=600_000)
    parser.add_argument("--dev-end-ppm", type=int, default=800_000)
    parser.add_argument("--minimum-train-rows", type=int, default=256)
    parser.add_argument("--required-rate", type=float, default=500.0)
    parser.add_argument("--holdout-blocks", type=int, default=16)
    parser.add_argument("--chunk-rows", type=int, default=131_072)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not 0 < args.train_end_ppm < args.dev_end_ppm < PPM:
        raise SystemExit("split PPM values must be ordered inside (0, 1000000)")
    if min(
        args.raw_scope_bytes,
        args.minimum_train_rows,
        args.holdout_blocks,
        args.chunk_rows,
    ) <= 0:
        raise SystemExit("scope, row, and block parameters must be positive")
    for path in (args.trace, args.store, args.endpoint_receipt):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    result = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "selected_profile": result["selected_on_dev"]["profile"],
                "holdout_gain_bytes_per_1m_raw": result["selected_on_dev"][
                    "holdout_gain_bytes_per_1m_raw"
                ],
                "verdict": result["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
