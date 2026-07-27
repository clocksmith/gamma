#!/usr/bin/env python3
"""Exact replay screen for a bounded label-free block expert mixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import tempfile
from datetime import datetime, timezone
from typing import Any

import numpy as np

import paid_block_vector_codebook as pbvc


TOTAL = 65536
POSTERIOR_SCALE = 1 << 24
RENORMALIZE_BITS = 8
NET_GATE_BPM = 2000.0
HOLDOUT_GATE_BPM = 2500.0


def artifact(path: pathlib.Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": str(path),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def prior_weights(count: int, scale: int) -> list[int]:
    if count < 1 or scale < count:
        raise ValueError("posterior scale must support every expert")
    base, extra = divmod(scale, count)
    return [base + (1 if index < extra else 0) for index in range(count)]


def project_weights(values: list[int], scale: int) -> list[int]:
    """Hamilton projection with one unit reserved for every expert."""
    count = len(values)
    if count < 1 or scale < count or any(value <= 0 for value in values):
        raise ValueError("invalid posterior projection input")
    value_sum = sum(values)
    distributable = scale - count
    projected: list[int] = []
    remainders: list[int] = []
    for value in values:
        quotient, remainder = divmod(distributable * value, value_sum)
        projected.append(1 + quotient)
        remainders.append(remainder)
    missing = scale - sum(projected)
    order = sorted(range(count), key=lambda index: (-remainders[index], index))
    for index in order[:missing]:
        projected[index] += 1
    if sum(projected) != scale or any(value < 1 for value in projected):
        raise AssertionError("posterior projection violated its simplex")
    return projected


def mixture_probabilities(
    baseline_probability: np.ndarray,
    truth: np.ndarray,
    codebook: np.ndarray,
    block_bytes: int,
    posterior_scale: int = POSTERIOR_SCALE,
) -> np.ndarray:
    if len(baseline_probability) != len(truth):
        raise ValueError("probability and truth lengths differ")
    if codebook.ndim != 2 or codebook.shape[1] != pbvc.BUCKETS:
        raise ValueError("invalid correction codebook shape")
    corrected = pbvc.correction_table(baseline_probability)
    result = np.empty(len(truth), dtype=np.uint16)
    rows_per_block = block_bytes * 8
    weights = prior_weights(len(codebook), posterior_scale)
    for row in range(len(truth)):
        within_block = row % rows_per_block
        if within_block == 0:
            weights = prior_weights(len(codebook), posterior_scale)
        bucket = (row & 7) * 16 + (int(baseline_probability[row]) >> 12)
        frequencies = [
            int(corrected[row, int(codebook[index, bucket])])
            for index in range(len(codebook))
        ]
        weight_sum = sum(weights)
        numerator = sum(
            weights[index] * frequencies[index]
            for index in range(len(codebook))
        )
        frequency_one = (numerator + weight_sum // 2) // weight_sum
        frequency_one = max(1, min(TOTAL - 1, frequency_one))
        result[row] = frequency_one
        observed = int(truth[row])
        weights = [
            weights[index]
            * (
                frequencies[index]
                if observed
                else TOTAL - frequencies[index]
            )
            for index in range(len(codebook))
        ]
        if (within_block + 1) % RENORMALIZE_BITS == 0:
            weights = project_weights(weights, posterior_scale)
    return result


def partition_loss_metrics(
    name: str,
    baseline: np.ndarray,
    mixture: np.ndarray,
    truth: np.ndarray,
    mask: np.ndarray,
    raw_bytes: int,
) -> dict[str, Any]:
    selected_truth = truth[mask].astype(np.float64)
    baseline_selected = baseline[mask].astype(np.float64)
    mixture_selected = mixture[mask].astype(np.float64)
    baseline_true = np.where(
        selected_truth > 0.5,
        baseline_selected,
        TOTAL - baseline_selected,
    )
    mixture_true = np.where(
        selected_truth > 0.5,
        mixture_selected,
        TOTAL - mixture_selected,
    )
    saved_bits = float(
        np.log2(mixture_true / baseline_true, dtype=np.float64).sum()
    )
    rows = int(np.count_nonzero(mask))
    raw_equivalent = max(1.0, raw_bytes * rows / len(truth))
    return {
        "name": name,
        "trace_rows": rows,
        "raw_equivalent_bytes_proportional": raw_equivalent,
        "surrogate_saved_bits": saved_bits,
        "surrogate_saved_bpm": saved_bits / 8.0 * 1_000_000.0 / raw_equivalent,
    }


def analyze(
    trace_path: pathlib.Path,
    archive_path: pathlib.Path,
    pbvc_decision_path: pathlib.Path,
    raw_bytes: int,
    source_bytes: int,
) -> dict[str, Any]:
    pbvc_decision = json.loads(pbvc_decision_path.read_text())
    if not pbvc_decision["gates"]["authorize_native_integration"]:
        raise ValueError("PBVC did not authorize its frozen expert family")
    block_bytes = int(pbvc_decision["construction"]["block_bytes"])
    codebook = np.asarray(
        pbvc_decision["construction"]["codebook"], dtype=np.uint8
    )
    mapped, truth, baseline_probability = pbvc.read_trace(trace_path)
    parent_payload, archive_header_bytes, wrt_bytes = pbvc.read_archive(archive_path)
    if len(truth) != wrt_bytes * 8:
        raise ValueError("trace rows do not equal coded WRT bits")
    replay = pbvc.encode_payload(baseline_probability, truth)
    if replay != parent_payload:
        raise ValueError("baseline replay differs from parent payload")
    mixture = mixture_probabilities(
        baseline_probability, truth, codebook, block_bytes
    )
    mixture_payload = pbvc.encode_payload(mixture, truth)
    codebook_bytes = math.ceil(len(codebook) * pbvc.BUCKETS * 3 / 8)
    gross_saved = len(parent_payload) - len(mixture_payload)
    net_saved = gross_saved - codebook_bytes - source_bytes
    net_bpm = net_saved * 1_000_000.0 / raw_bytes
    split = max(1, min(len(truth) - 1, (4 * len(truth)) // 5))
    development_mask = np.arange(len(truth)) < split
    holdout_mask = ~development_mask
    development = partition_loss_metrics(
        "development",
        baseline_probability,
        mixture,
        truth,
        development_mask,
        raw_bytes,
    )
    holdout = partition_loss_metrics(
        "holdout",
        baseline_probability,
        mixture,
        truth,
        holdout_mask,
        raw_bytes,
    )
    exact_pass = net_bpm >= NET_GATE_BPM
    holdout_pass = holdout["surrogate_saved_bpm"] >= HOLDOUT_GATE_BPM
    authorized = exact_pass and holdout_pass
    del mapped
    return {
        "schema": "causal_block_expert_mixture_decision_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "af1_causal_block_expert_mixture_v1",
        "evidence_tier": "causal_shadow",
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Bounded label-free posterior replay over a frozen PBVC codebook; "
            "no native or full-corpus score credit."
        ),
        "inputs": {
            "trace": artifact(trace_path),
            "archive": artifact(archive_path),
            "pbvc_decision": artifact(pbvc_decision_path),
            "raw_bytes": raw_bytes,
            "wrt_bytes": wrt_bytes,
            "trace_rows": len(truth),
            "archive_header_bytes": archive_header_bytes,
        },
        "construction": {
            "block_bytes": block_bytes,
            "expert_count": len(codebook),
            "posterior_scale": POSTERIOR_SCALE,
            "renormalize_bits": RENORMALIZE_BITS,
            "projection": "positive_hamilton_remainder_then_expert_id",
            "probability_rounding": "nearest_half_up_clamped_1_to_65535",
            "transmitted_label_bytes": 0,
            "codebook_bytes": codebook_bytes,
            "source_bytes": source_bytes,
        },
        "identity": {
            "baseline_payload_bytes": len(parent_payload),
            "baseline_payload_sha256": hashlib.sha256(parent_payload).hexdigest(),
            "trace_replay_payload_bytes": len(replay),
            "trace_replay_payload_sha256": hashlib.sha256(replay).hexdigest(),
            "exact_parent_identity": True,
        },
        "exact_replay": {
            "mixture_payload_bytes": len(mixture_payload),
            "mixture_payload_sha256": hashlib.sha256(
                mixture_payload
            ).hexdigest(),
            "gross_saved_bytes": gross_saved,
            "net_saved_bytes": net_saved,
            "net_saved_bpm": net_bpm,
        },
        "partitions": {
            "development": development,
            "holdout": holdout,
            "holdout_rule": "final_chronological_fifth_of_trace_rows",
        },
        "gates": {
            "minimum_exact_net_bpm": NET_GATE_BPM,
            "minimum_holdout_surrogate_bpm": HOLDOUT_GATE_BPM,
            "exact_net_pass": exact_pass,
            "holdout_pass": holdout_pass,
            "authorize_native_integration": authorized,
        },
        "decision": (
            "authorize_bounded_native_mixture_integration"
            if authorized
            else "retire_bounded_block_mixture"
        ),
    }


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="cbm-self-test-") as directory:
        root = pathlib.Path(directory)
        trace = root / "trace.bin"
        archive = root / "archive.bin"
        raw_bytes, block_bytes = pbvc.write_synthetic_trace(trace, archive)
        pbvc_result = pbvc.analyze(trace, archive, raw_bytes, block_bytes, 4, 0)
        pbvc_decision = root / "pbvc.json"
        pbvc_decision.write_text(
            json.dumps(pbvc_result, indent=2, sort_keys=True) + "\n"
        )
        result = analyze(trace, archive, pbvc_decision, raw_bytes, 0)
        if not result["identity"]["exact_parent_identity"]:
            raise AssertionError("synthetic parent replay failed")
        if result["construction"]["transmitted_label_bytes"] != 0:
            raise AssertionError("label-free construction transmitted labels")
        print(json.dumps(result, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=pathlib.Path)
    parser.add_argument("--archive", type=pathlib.Path)
    parser.add_argument("--pbvc-decision", type=pathlib.Path)
    parser.add_argument("--raw-bytes", type=int)
    parser.add_argument("--source-bytes", type=int, default=0)
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    required = (
        args.trace,
        args.archive,
        args.pbvc_decision,
        args.raw_bytes,
        args.output,
    )
    if any(item is None for item in required):
        parser.error("trace, archive, PBVC decision, raw bytes, and output required")
    result = analyze(
        args.trace,
        args.archive,
        args.pbvc_decision,
        args.raw_bytes,
        args.source_bytes,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
