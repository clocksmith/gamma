#!/usr/bin/env python3
"""Fit and exactly replay a paid blockwise vector correction codebook."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import struct
import tempfile
from datetime import datetime, timezone
from typing import Any

import numpy as np


MAGIC = b"AF1P1V1\0"
HEADER_BYTES = 32
ROW_BYTES = 3
TOTAL = 1 << 16
MASK32 = (1 << 32) - 1
RATIOS = ((1, 2), (3, 4), (1, 1), (4, 3), (2, 1))
IDENTITY = 2
BUCKETS = 8 * 16
QBITS = 256
NET_GATE_BPM = 2000.0
HOLDOUT_GATE_BPM = 2500.0
NULL_MARGIN_BPM = 1000.0


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: pathlib.Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def read_trace(path: pathlib.Path) -> tuple[np.memmap, np.ndarray, np.ndarray]:
    with path.open("rb") as source:
        header = source.read(HEADER_BYTES)
    if len(header) != HEADER_BYTES or header[:8] != MAGIC:
        raise ValueError("invalid AF-1 P1 trace header")
    version, header_bytes, row_bytes, total = struct.unpack_from(
        "<IIII", header, 8
    )
    rows = struct.unpack_from("<Q", header, 24)[0]
    if (
        version != 1
        or header_bytes != HEADER_BYTES
        or row_bytes != ROW_BYTES
        or total != TOTAL
        or rows == 0
    ):
        raise ValueError("unsupported AF-1 P1 trace contract")
    if path.stat().st_size != HEADER_BYTES + rows * ROW_BYTES:
        raise ValueError("AF-1 P1 trace size mismatch")
    mapped = np.memmap(
        path,
        mode="r",
        dtype=np.uint8,
        offset=HEADER_BYTES,
        shape=(rows, ROW_BYTES),
    )
    truth = np.asarray(mapped[:, 0])
    probability = (
        np.asarray(mapped[:, 1], dtype=np.uint16)
        | (np.asarray(mapped[:, 2], dtype=np.uint16) << 8)
    )
    if np.any(truth > 1) or np.any(probability == 0):
        raise ValueError("invalid AF-1 P1 trace row")
    return mapped, truth, probability


def read_archive(path: pathlib.Path) -> tuple[bytes, int, int]:
    data = path.read_bytes()
    if len(data) < 6:
        raise ValueError("archive is truncated")
    wrt_bytes = data[0] & 0x7F
    for value in data[1:5]:
        wrt_bytes = (wrt_bytes << 8) | value
    header_bytes = 5 if wrt_bytes < 10_000 else 37
    if len(data) <= header_bytes:
        raise ValueError("archive has no arithmetic payload")
    return data[header_bytes:], header_bytes, wrt_bytes


def correction_table(probability: np.ndarray) -> np.ndarray:
    p = probability.astype(np.uint64)
    output = np.empty((len(p), len(RATIOS)), dtype=np.uint16)
    for index, (a, b) in enumerate(RATIOS):
        denominator = a * p + b * (TOTAL - p)
        corrected = (TOTAL * a * p + denominator // 2) // denominator
        output[:, index] = np.clip(corrected, 1, TOTAL - 1).astype(np.uint16)
    return output


def qbit_tables() -> tuple[np.ndarray, np.ndarray]:
    p1 = np.arange(TOTAL, dtype=np.float64) / TOTAL
    p1[0] = 1.0 / TOTAL
    p0 = 1.0 - p1
    p0[0] = 1.0 - 1.0 / TOTAL
    return (
        np.rint(-np.log2(p0) * QBITS).astype(np.int32),
        np.rint(-np.log2(p1) * QBITS).astype(np.int32),
    )


def encode_payload(probability: np.ndarray, truth: np.ndarray) -> bytes:
    x1 = 0
    x2 = MASK32
    output = bytearray()
    for start in range(0, len(truth), 1 << 20):
        stop = min(len(truth), start + (1 << 20))
        probabilities = probability[start:stop].tolist()
        bits = truth[start:stop].tolist()
        for p1, bit in zip(probabilities, bits, strict=True):
            delta = x2 - x1
            midpoint = x1 + (delta >> 16) * p1
            midpoint += ((delta & 0xFFFF) * p1) >> 16
            if bit:
                x2 = midpoint
            else:
                x1 = midpoint + 1
            while ((x1 ^ x2) & 0xFF000000) == 0:
                output.append((x2 >> 24) & 0xFF)
                x1 = (x1 << 8) & MASK32
                x2 = ((x2 << 8) & MASK32) + 255
    while ((x1 ^ x2) & 0xFF000000) == 0:
        output.append((x2 >> 24) & 0xFF)
        x1 = (x1 << 8) & MASK32
        x2 = ((x2 << 8) & MASK32) + 255
    output.append((x2 >> 24) & 0xFF)
    return bytes(output)


def aggregate_costs(
    corrected: np.ndarray,
    truth: np.ndarray,
    block_index: np.ndarray,
    bucket: np.ndarray,
    block_count: int,
) -> tuple[np.ndarray, np.ndarray]:
    zero_cost, one_cost = qbit_tables()
    costs = np.zeros(
        (block_count, BUCKETS, len(RATIOS)), dtype=np.int64
    )
    observations = np.zeros((block_count, BUCKETS), dtype=np.int64)
    np.add.at(observations, (block_index, bucket), 1)
    for correction in range(len(RATIOS)):
        probability = corrected[:, correction]
        row_cost = np.where(
            truth != 0, one_cost[probability], zero_cost[probability]
        )
        np.add.at(
            costs[:, :, correction], (block_index, bucket), row_cost
        )
    return costs, observations


def independent_optimum(
    costs: np.ndarray, observations: np.ndarray
) -> np.ndarray:
    result = np.argmin(costs, axis=2).astype(np.uint8)
    result[observations == 0] = IDENTITY
    return result


def codeword_costs(costs: np.ndarray, codebook: np.ndarray) -> np.ndarray:
    block_count = costs.shape[0]
    output = np.empty((block_count, len(codebook)), dtype=np.int64)
    buckets = np.arange(BUCKETS)
    for index, codeword in enumerate(codebook):
        output[:, index] = costs[:, buckets, codeword].sum(axis=1)
    return output


def train_codebook(
    costs: np.ndarray,
    observations: np.ndarray,
    development: np.ndarray,
    size: int,
) -> np.ndarray:
    if not np.any(development):
        raise ValueError("empty development partition")
    size = min(size, int(np.count_nonzero(development)))
    dev_costs = costs[development]
    dev_observations = observations[development]
    aggregate = dev_costs.sum(axis=0, keepdims=True)
    aggregate_obs = dev_observations.sum(axis=0, keepdims=True)
    codewords = [independent_optimum(aggregate, aggregate_obs)[0]]
    per_block = independent_optimum(dev_costs, dev_observations)
    while len(codewords) < size:
        current = np.asarray(codewords, dtype=np.uint8)
        current_cost = codeword_costs(dev_costs, current).min(axis=1)
        own_cost = codeword_costs(dev_costs, per_block)
        own_diagonal = own_cost[np.arange(len(dev_costs)), np.arange(len(dev_costs))]
        regret = current_cost - own_diagonal
        order = np.argsort(-regret, kind="stable")
        chosen = None
        for candidate in order.tolist():
            word = per_block[candidate]
            if not any(np.array_equal(word, old) for old in codewords):
                chosen = word
                break
        if chosen is None:
            break
        codewords.append(chosen.copy())
    codebook = np.asarray(codewords, dtype=np.uint8)
    for _ in range(32):
        scores = codeword_costs(dev_costs, codebook)
        assignment = np.argmin(scores, axis=1)
        updated = codebook.copy()
        for index in range(len(codebook)):
            members = assignment == index
            if not np.any(members):
                continue
            group_cost = dev_costs[members].sum(axis=0, keepdims=True)
            group_obs = dev_observations[members].sum(axis=0, keepdims=True)
            updated[index] = independent_optimum(group_cost, group_obs)[0]
        if np.array_equal(updated, codebook):
            break
        codebook = updated
    return codebook


def partition_metrics(
    name: str,
    scores: np.ndarray,
    baseline: np.ndarray,
    mask: np.ndarray,
    label_bits: int,
    row_counts: np.ndarray,
    raw_bytes: int,
    total_rows: int,
) -> dict[str, Any]:
    selected = scores.min(axis=1)
    blocks = int(np.count_nonzero(mask))
    rows = int(row_counts[mask].sum())
    saved_bits = float((baseline[mask] - selected[mask]).sum()) / QBITS
    charged_bits = blocks * label_bits
    raw_equivalent = max(1.0, raw_bytes * rows / total_rows)
    return {
        "name": name,
        "blocks": blocks,
        "trace_rows": rows,
        "raw_equivalent_bytes_proportional": raw_equivalent,
        "surrogate_saved_bits": saved_bits,
        "label_bits": charged_bits,
        "net_surrogate_bits": saved_bits - charged_bits,
        "net_surrogate_bpm": (
            (saved_bits - charged_bits) / 8.0 * 1_000_000.0 / raw_equivalent
        ),
    }


def analyze(
    trace_path: pathlib.Path,
    archive_path: pathlib.Path,
    raw_bytes: int,
    block_bytes: int,
    requested_codewords: int,
    source_bytes: int,
) -> dict[str, Any]:
    mapped, truth, probability = read_trace(trace_path)
    parent_payload, archive_header_bytes, wrt_bytes = read_archive(archive_path)
    if len(truth) != wrt_bytes * 8:
        raise ValueError("trace rows do not equal coded WRT bits")
    replay = encode_payload(probability, truth)
    if replay != parent_payload:
        raise ValueError("baseline P1 replay differs from parent payload")
    rows_per_block = block_bytes * 8
    block_index = np.arange(len(truth), dtype=np.int64) // rows_per_block
    block_count = int(block_index[-1]) + 1
    row_counts = np.bincount(block_index, minlength=block_count)
    bit_position = np.arange(len(truth), dtype=np.int64) & 7
    confidence_bin = (probability.astype(np.uint32) >> 12).astype(np.int64)
    bucket = bit_position * 16 + confidence_bin
    corrected = correction_table(probability)
    costs, observations = aggregate_costs(
        corrected, truth, block_index, bucket, block_count
    )
    if block_count < 2:
        raise ValueError("at least two blocks are required for a sealed holdout")
    development_blocks = max(1, min(block_count - 1, (4 * block_count) // 5))
    development = np.arange(block_count) < development_blocks
    holdout = ~development
    codebook = train_codebook(
        costs, observations, development, requested_codewords
    )
    scores = codeword_costs(costs, codebook)
    labels = np.argmin(scores, axis=1)
    baseline = costs[:, :, IDENTITY].sum(axis=1)
    row_correction = codebook[labels[block_index], bucket]
    selected_probability = corrected[
        np.arange(len(corrected)), row_correction
    ]
    selected_payload = encode_payload(selected_probability, truth)
    rotated_labels = np.roll(labels, 1)
    rotated_correction = codebook[rotated_labels[block_index], bucket]
    rotated_probability = corrected[
        np.arange(len(corrected)), rotated_correction
    ]
    rotated_payload = encode_payload(rotated_probability, truth)
    label_bits = 0 if len(codebook) == 1 else math.ceil(math.log2(len(codebook)))
    label_bytes = math.ceil(block_count * label_bits / 8)
    codebook_bytes = math.ceil(len(codebook) * BUCKETS * 3 / 8)
    gross_saved = len(parent_payload) - len(selected_payload)
    net_saved = gross_saved - label_bytes - codebook_bytes - source_bytes
    null_saved = len(parent_payload) - len(rotated_payload)
    net_bpm = net_saved * 1_000_000.0 / raw_bytes
    null_margin_bpm = (
        (gross_saved - null_saved) * 1_000_000.0 / raw_bytes
    )
    development_metrics = partition_metrics(
        "development",
        scores,
        baseline,
        development,
        label_bits,
        row_counts,
        raw_bytes,
        len(truth),
    )
    holdout_metrics = partition_metrics(
        "holdout",
        scores,
        baseline,
        holdout,
        label_bits,
        row_counts,
        raw_bytes,
        len(truth),
    )
    exact_pass = net_bpm >= NET_GATE_BPM
    holdout_pass = (
        holdout_metrics["net_surrogate_bpm"] >= HOLDOUT_GATE_BPM
    )
    null_pass = null_margin_bpm >= NULL_MARGIN_BPM
    authorized = exact_pass and holdout_pass and null_pass
    result = {
        "schema": "paid_block_vector_codebook_decision_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "af1_paid_block_vector_codebook_v1",
        "evidence_tier": "causal_shadow",
        "claim_boundary": (
            "Labels are constructive paid information, but this screen changes "
            "no native codec and receives zero score credit until integration."
        ),
        "inputs": {
            "trace": artifact(trace_path),
            "archive": artifact(archive_path),
            "raw_bytes": raw_bytes,
            "wrt_bytes": wrt_bytes,
            "trace_rows": len(truth),
            "archive_header_bytes": archive_header_bytes,
        },
        "construction": {
            "block_bytes": block_bytes,
            "block_count": block_count,
            "bucket_count": BUCKETS,
            "ratios": [list(item) for item in RATIOS],
            "requested_codewords": requested_codewords,
            "actual_codewords": len(codebook),
            "label_bits_per_block": label_bits,
            "label_bytes": label_bytes,
            "codebook_bytes": codebook_bytes,
            "source_bytes": source_bytes,
            "development_rule": (
                "first_floor_four_fifths_blocks_with_nonempty_partition_guards"
            ),
            "holdout_rule": "remaining_final_chronological_blocks",
            "partition_rate_normalization": (
                "raw_bytes_times_partition_trace_rows_over_total_trace_rows"
            ),
            "codebook": codebook.tolist(),
            "labels_sha256": hashlib.sha256(
                labels.astype(np.uint8).tobytes()
            ).hexdigest(),
        },
        "identity": {
            "baseline_payload_bytes": len(parent_payload),
            "baseline_payload_sha256": hashlib.sha256(parent_payload).hexdigest(),
            "trace_replay_payload_bytes": len(replay),
            "trace_replay_payload_sha256": hashlib.sha256(replay).hexdigest(),
            "exact_parent_identity": True,
        },
        "exact_replay": {
            "selected_payload_bytes": len(selected_payload),
            "selected_payload_sha256": hashlib.sha256(
                selected_payload
            ).hexdigest(),
            "rotated_payload_bytes": len(rotated_payload),
            "rotated_payload_sha256": hashlib.sha256(
                rotated_payload
            ).hexdigest(),
            "gross_saved_bytes": gross_saved,
            "net_saved_bytes": net_saved,
            "net_saved_bpm": net_bpm,
            "rotated_gross_saved_bytes": null_saved,
            "real_over_rotated_bpm": null_margin_bpm,
        },
        "partitions": {
            "development": development_metrics,
            "holdout": holdout_metrics,
        },
        "gates": {
            "minimum_exact_net_bpm": NET_GATE_BPM,
            "minimum_holdout_net_surrogate_bpm": HOLDOUT_GATE_BPM,
            "minimum_real_over_rotated_bpm": NULL_MARGIN_BPM,
            "exact_net_pass": exact_pass,
            "holdout_pass": holdout_pass,
            "null_pass": null_pass,
            "authorize_native_integration": authorized,
        },
        "decision": (
            "authorize_native_paid_prompt_integration"
            if authorized
            else "retire_paid_block_vector_codebook_unchanged"
        ),
        "score_credit_bytes": 0,
    }
    del mapped
    return result


def write_synthetic_trace(
    trace: pathlib.Path, archive: pathlib.Path
) -> tuple[int, int]:
    rng = np.random.default_rng(8675309)
    block_bytes = 32
    block_count = 400
    rows = block_bytes * 8 * block_count
    index = np.arange(rows)
    block = index // (block_bytes * 8)
    bucket = (index & 7) * 16 + 8
    latent = block & 3
    actual = np.where(
        ((bucket + latent[:, None] if latent.ndim > 1 else bucket + latent) & 3)
        < 2,
        0.78,
        0.22,
    )
    truth = (rng.random(rows) < actual).astype(np.uint8)
    probability = np.full(rows, TOTAL // 2, dtype=np.uint16)
    header = bytearray(MAGIC)
    header.extend(struct.pack("<IIIIQ", 1, HEADER_BYTES, ROW_BYTES, TOTAL, rows))
    body = np.empty((rows, ROW_BYTES), dtype=np.uint8)
    body[:, 0] = truth
    body[:, 1] = probability & 0xFF
    body[:, 2] = probability >> 8
    trace.write_bytes(bytes(header) + body.tobytes())
    payload = encode_payload(probability, truth)
    wrt_bytes = rows // 8
    archive_header = bytearray(5 if wrt_bytes < 10_000 else 37)
    value = wrt_bytes
    for offset in range(4, -1, -1):
        archive_header[offset] = value & 0xFF
        value >>= 8
    archive.write_bytes(bytes(archive_header) + payload)
    return rows // 8, block_bytes


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="paid-block-codebook-") as raw:
        directory = pathlib.Path(raw)
        trace = directory / "trace.bin"
        archive = directory / "archive.bin"
        raw_bytes, block_bytes = write_synthetic_trace(trace, archive)
        result = analyze(trace, archive, raw_bytes, block_bytes, 4, 0)
        if not result["identity"]["exact_parent_identity"]:
            raise AssertionError("synthetic parent replay failed")
        if result["partitions"]["holdout"]["net_surrogate_bits"] <= 0:
            raise AssertionError("synthetic holdout control did not improve")
        return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=pathlib.Path)
    parser.add_argument("--archive", type=pathlib.Path)
    parser.add_argument("--raw-bytes", type=int)
    parser.add_argument("--block-bytes", type=int, default=4096)
    parser.add_argument("--codewords", type=int, default=16)
    parser.add_argument("--source-bytes", type=int, default=0)
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        result = self_test()
    else:
        if (
            args.trace is None
            or args.archive is None
            or args.raw_bytes is None
            or args.output is None
        ):
            raise SystemExit(
                "--trace, --archive, --raw-bytes, and --output are required"
            )
        result = analyze(
            args.trace,
            args.archive,
            args.raw_bytes,
            args.block_bytes,
            args.codewords,
            args.source_bytes,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
