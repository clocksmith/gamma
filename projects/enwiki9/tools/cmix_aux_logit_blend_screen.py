#!/usr/bin/env python3
"""Screen a same-execution CMIX auxiliary endpoint in logit space.

The trace records the unchanged archive-producing probability and one causal
auxiliary endpoint before the current bit is learned. Weight selection reads
development rows only. Exact holdout and full range-coder replay occur after
the weight is frozen.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
import json
import os
import struct
import sys
from pathlib import Path
from typing import Any

import numpy as np


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from fx2_attribution_external_base_screen import (  # noqa: E402
    P1_HEADER_BYTES,
    PPM,
    QBITS_PER_BYTE,
    PROBABILITY_TOTAL,
    artifact,
    cmix_archive_header_bytes,
    exact_block_audit,
    exact_replay,
    qbit_tables,
    read_p1_header,
)


PAIR_MAGIC = b"CMXAUX1\0"
PAIR_HEADER_BYTES = 16
ENDPOINT_MAGIC = b"FX2L428\0"
ENDPOINT_HEADER_BYTES = 16
DEFAULT_WEIGHTS = tuple(range(100_000, 350_001, 5_000))
MIX_MODES = ("native_q16", "float64_logit")


def read_pair_header(path: Path) -> int:
    with path.open("rb") as source:
        header = source.read(PAIR_HEADER_BYTES)
    if len(header) != PAIR_HEADER_BYTES or header[:8] != PAIR_MAGIC:
        raise ValueError("invalid CMIX auxiliary-pair trace header")
    rows = struct.unpack_from("<Q", header, 8)[0]
    if rows < 1 or path.stat().st_size != PAIR_HEADER_BYTES + 4 * rows:
        raise ValueError("CMIX auxiliary-pair trace length mismatch")
    return rows


def read_endpoint_header(path: Path) -> int:
    with path.open("rb") as source:
        header = source.read(ENDPOINT_HEADER_BYTES)
    if len(header) != ENDPOINT_HEADER_BYTES or header[:8] != ENDPOINT_MAGIC:
        raise ValueError("invalid standalone endpoint trace header")
    rows = struct.unpack_from("<Q", header, 8)[0]
    if rows < 1 or path.stat().st_size != ENDPOINT_HEADER_BYTES + 2 * rows:
        raise ValueError("standalone endpoint trace length mismatch")
    return rows


def probability_logit(probability: np.ndarray) -> np.ndarray:
    scaled = np.clip(
        probability.astype(np.float64) / PROBABILITY_TOTAL,
        1 / PROBABILITY_TOTAL,
        (PROBABILITY_TOTAL - 1) / PROBABILITY_TOTAL,
    )
    return np.log(scaled) - np.log1p(-scaled)


def log2_q16(value: int) -> int:
    """Match FixedLogitBlend::Log2Q16 exactly."""

    if value <= 0:
        raise ValueError("log2_q16 requires a positive integer")
    integer = value.bit_length() - 1
    normalized = value << (31 - integer)
    fraction = 0
    for bit in range(15, -1, -1):
        squared = (normalized * normalized) >> 31
        if squared >= 1 << 32:
            squared >>= 1
            fraction |= 1 << bit
        normalized = squared
    return (integer << 16) | fraction


@lru_cache(maxsize=1)
def native_logit_table() -> np.ndarray:
    table = np.empty(PROBABILITY_TOTAL, dtype=np.int32)
    for probability in range(1, PROBABILITY_TOTAL):
        table[probability] = log2_q16(probability) - log2_q16(
            PROBABILITY_TOTAL - probability
        )
    table[0] = table[1]
    table.setflags(write=False)
    return table


def mix_native_q16_grid(
    base: np.ndarray,
    endpoint: np.ndarray,
    weights_ppm: tuple[int, ...],
) -> np.ndarray:
    """Reproduce the native integer-logit mixer for one or more weights."""

    if not weights_ppm or any(weight <= 0 or weight >= PPM for weight in weights_ppm):
        raise ValueError("native Q16 weights must be within 1..999999")
    table = native_logit_table()
    base_values = np.asarray(base, dtype=np.uint16)
    endpoint_values = np.asarray(endpoint, dtype=np.uint16)
    if base_values.shape != endpoint_values.shape:
        raise ValueError("base and endpoint probability shapes differ")
    if np.any(base_values == 0) or np.any(endpoint_values == 0):
        raise ValueError("native Q16 probabilities must be within 1..65535")

    weights = np.asarray(weights_ppm, dtype=np.int64)[None, :]
    base_logits = table[base_values].astype(np.int64)[:, None]
    endpoint_logits = table[endpoint_values].astype(np.int64)[:, None]
    numerator = (
        base_logits * (PPM - weights)
        + endpoint_logits * weights
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


def mix_native_q16(
    base: np.ndarray, endpoint: np.ndarray, weight_ppm: int
) -> np.ndarray:
    return mix_native_q16_grid(base, endpoint, (weight_ppm,))[:, 0]


def mix_logit(
    base: np.ndarray, endpoint: np.ndarray, weight_ppm: int
) -> np.ndarray:
    base_logit = probability_logit(base)
    endpoint_logit = probability_logit(endpoint)
    mixed_logit = (
        base_logit * (PPM - weight_ppm) + endpoint_logit * weight_ppm
    ) / PPM
    mixed_probability = 1.0 / (1.0 + np.exp(-np.clip(mixed_logit, -40, 40)))
    return np.clip(
        np.floor(mixed_probability * PROBABILITY_TOTAL + 0.5),
        1,
        PROBABILITY_TOTAL - 1,
    ).astype(np.uint16)


def run(args: argparse.Namespace) -> dict[str, Any]:
    if not 0 < args.dev_start_ppm < args.holdout_start_ppm < PPM:
        raise ValueError("split PPM boundaries must be ordered")
    weights = tuple(sorted(set(args.weights)))
    if not weights or any(weight <= 0 or weight >= PPM for weight in weights):
        raise ValueError("weights must be within 1..999999")

    if (args.pair_trace is None) == (args.endpoint_p1 is None):
        raise ValueError("exactly one of pair_trace or endpoint_p1 is required")
    rows = (
        read_pair_header(args.pair_trace)
        if args.pair_trace is not None
        else read_endpoint_header(args.endpoint_p1)
    )
    _, base_rows = read_p1_header(args.base_p1)
    if rows != base_rows:
        raise ValueError("pair trace and frozen base P1 rows differ")
    store_bytes = args.wrt_store.read_bytes()
    if len(store_bytes) < 5 or (len(store_bytes) - 5) * 8 != rows:
        raise ValueError("WRT store and pair-trace rows do not align")

    frozen_base = np.memmap(
        args.base_p1,
        dtype="<u2",
        mode="r",
        offset=P1_HEADER_BYTES,
        shape=(rows,),
    )
    if args.pair_trace is not None:
        pair = np.memmap(
            args.pair_trace,
            dtype="<u2",
            mode="r",
            offset=PAIR_HEADER_BYTES,
            shape=(rows, 2),
        )
        base = np.asarray(pair[:, 0], dtype=np.uint16)
        endpoint = np.asarray(pair[:, 1], dtype=np.uint16)
        base_p1_identity = bool(np.array_equal(base, frozen_base))
        trace_kind = "same_execution_pair"
    else:
        base = np.asarray(frozen_base, dtype=np.uint16)
        endpoint = np.memmap(
            args.endpoint_p1,
            dtype="<u2",
            mode="r",
            offset=ENDPOINT_HEADER_BYTES,
            shape=(rows,),
        )
        base_p1_identity = True
        trace_kind = "independent_causal_endpoint"
    truth = np.unpackbits(
        np.frombuffer(store_bytes, dtype=np.uint8, offset=5), bitorder="big"
    )
    dev_start = rows * args.dev_start_ppm // PPM
    holdout_start = rows * args.holdout_start_ppm // PPM
    loss0, loss1 = qbit_tables()

    weight_array = np.asarray(weights, dtype=np.float64)
    dev_base_loss = 0
    dev_candidate_losses = np.zeros(len(weights), dtype=np.int64)
    for start in range(dev_start, holdout_start, args.chunk_rows):
        end = min(holdout_start, start + args.chunk_rows)
        local_base = base[start:end]
        local_endpoint = endpoint[start:end]
        bits = truth[start:end]
        base_loss = np.where(bits, loss1[local_base], loss0[local_base])
        dev_base_loss += int(base_loss.sum(dtype=np.int64))
        if args.mix_mode == "native_q16":
            mixed = mix_native_q16_grid(local_base, local_endpoint, weights)
        else:
            base_logit = probability_logit(local_base)[:, None]
            endpoint_logit = probability_logit(local_endpoint)[:, None]
            mixed_logit = (
                base_logit * (PPM - weight_array) + endpoint_logit * weight_array
            ) / PPM
            mixed = np.clip(
                np.floor(
                    (1.0 / (1.0 + np.exp(-np.clip(mixed_logit, -40, 40))))
                    * PROBABILITY_TOTAL
                    + 0.5
                ),
                1,
                PROBABILITY_TOTAL - 1,
            ).astype(np.uint16)
        dev_candidate_losses += np.where(
            bits[:, None], loss1[mixed], loss0[mixed]
        ).sum(axis=0, dtype=np.int64)

    dev_gains = dev_base_loss - dev_candidate_losses
    selected_index = int(np.argmax(dev_gains))
    selected_weight = weights[selected_index]
    selected_dev_gain = int(dev_gains[selected_index])
    candidate = (
        mix_native_q16(base, endpoint, selected_weight)
        if args.mix_mode == "native_q16"
        else mix_logit(base, endpoint, selected_weight)
    )

    split_bounds = (
        ("train", 0, dev_start),
        ("dev", dev_start, holdout_start),
        ("holdout", holdout_start, rows),
    )
    split_qbits: dict[str, int] = {}
    for name, start, end in split_bounds:
        bits = truth[start:end]
        split_qbits[name] = int(
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
    archive_payload = archive[archive_header_bytes:]
    archive_payload_identity = replayed_base_payload == archive_payload
    candidate_reference_identity = None
    candidate_reference_header_bytes = None
    if args.candidate_reference_archive is not None:
        candidate_reference = args.candidate_reference_archive.read_bytes()
        candidate_reference_header_bytes = cmix_archive_header_bytes(
            candidate_reference
        )
        candidate_reference_identity = bool(
            candidate_payload
            == candidate_reference[candidate_reference_header_bytes:]
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
    holdout_scope = (
        args.raw_scope_bytes * (PPM - args.holdout_start_ppm) / PPM
    )
    holdout_rate = exact_holdout["saved_bytes"] * 1_000_000 / holdout_scope
    regret_ok = bool(
        block_audit["regressing_blocks"] <= args.max_regressing_blocks
        and block_audit["largest_regression_bytes"]
        <= args.max_largest_regression_bytes
        and block_audit["total_regression_bytes"]
        <= args.max_total_regression_bytes
    )
    identities_ok = bool(
        base_p1_identity
        and archive_payload_identity
        and candidate_reference_identity is not False
    )
    economics_ok = bool(
        full_rate >= args.required_incremental_bytes_per_1m
        and holdout_rate >= args.required_incremental_bytes_per_1m
    )
    return {
        "schema": "cmix_aux_logit_blend_screen_v3",
        "evidence_level": (
            "development_selected_exact_same_execution_shadow"
            if args.pair_trace is not None
            else "development_selected_exact_independent_endpoint_shadow"
        ),
        "inputs": {
            "pair_trace": (
                artifact(args.pair_trace) if args.pair_trace is not None else None
            ),
            "endpoint_p1": (
                artifact(args.endpoint_p1)
                if args.endpoint_p1 is not None
                else None
            ),
            "base_p1": artifact(args.base_p1),
            "base_archive": artifact(args.base_archive),
            "candidate_reference_archive": (
                artifact(args.candidate_reference_archive)
                if args.candidate_reference_archive is not None
                else None
            ),
            "wrt_store": artifact(args.wrt_store),
        },
        "scope": {
            "raw_bytes": args.raw_scope_bytes,
            "rows": rows,
            "dev_start_row": dev_start,
            "holdout_start_row": holdout_start,
            "selection_reads_holdout": False,
        },
        "identity": {
            "trace_kind": trace_kind,
            "pair_base_equals_frozen_base_p1": base_p1_identity,
            "archive_header_bytes": archive_header_bytes,
            "archive_payload_identity": archive_payload_identity,
            "candidate_reference_archive_header_bytes": (
                candidate_reference_header_bytes
            ),
            "candidate_payload_equals_native_reference": (
                candidate_reference_identity
            ),
        },
        "selection": {
            "mix_mode": args.mix_mode,
            "weight_denominator_ppm": PPM,
            "weights_ppm": list(weights),
            "selected_weight_ppm": selected_weight,
            "selected_dev_gain_qbits": selected_dev_gain,
            "selected_dev_gain_bytes_per_proportional_1m_raw": (
                selected_dev_gain
                / QBITS_PER_BYTE
                * 1_000_000
                / (
                    args.raw_scope_bytes
                    * (args.holdout_start_ppm - args.dev_start_ppm)
                    / PPM
                )
            ),
        },
        "qbit_replay": {"split_gain_qbits": split_qbits},
        "exact_replay": {
            "full": exact_full,
            "holdout": exact_holdout,
            "full_saved_bytes_per_1m_raw": full_rate,
            "holdout_saved_bytes_per_proportional_1m_raw": holdout_rate,
            "holdout_block_audit": block_audit,
            "candidate_payload_path": (
                str(args.candidate_payload.resolve())
                if args.candidate_payload is not None
                else None
            ),
            "candidate_payload_artifact": (
                artifact(args.candidate_payload)
                if args.candidate_payload is not None
                else None
            ),
            "candidate_p1_artifact": (
                artifact(args.candidate_p1)
                if args.candidate_p1 is not None
                else None
            ),
        },
        "guardrails": {
            "max_regressing_blocks": args.max_regressing_blocks,
            "max_largest_regression_bytes": args.max_largest_regression_bytes,
            "max_total_regression_bytes": args.max_total_regression_bytes,
            "regret_budget_pass": regret_ok,
        },
        "economics": {
            "required_incremental_bytes_per_1m": (
                args.required_incremental_bytes_per_1m
            ),
            "full_and_holdout_clear_required_incremental": economics_ok,
        },
        "verdict": (
            "causal_endpoint_pass_requires_native_fixed_point_integration"
            if identities_ok and economics_ok and regret_ok
            else "retire_same_state_auxiliary_endpoint"
        ),
        "promotion_authorized": False,
        "claim_boundary": (
            "Causal trace shadow with development-only weight selection. "
            "Native fixed-point integration, archive roundtrip, determinism, "
            "counted source, resources, disjoint confirmation, and full-corpus "
            "official accounting remain required."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    trace_group = parser.add_mutually_exclusive_group(required=True)
    trace_group.add_argument("--pair-trace", type=Path)
    trace_group.add_argument("--endpoint-p1", type=Path)
    parser.add_argument("--base-p1", type=Path, required=True)
    parser.add_argument("--base-archive", type=Path, required=True)
    parser.add_argument("--candidate-reference-archive", type=Path)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--raw-scope-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-payload", type=Path)
    parser.add_argument("--candidate-p1", type=Path)
    parser.add_argument("--dev-start-ppm", type=int, default=600_000)
    parser.add_argument("--holdout-start-ppm", type=int, default=800_000)
    parser.add_argument("--weights", type=int, nargs="+", default=DEFAULT_WEIGHTS)
    parser.add_argument("--mix-mode", choices=MIX_MODES, default="native_q16")
    parser.add_argument("--chunk-rows", type=int, default=65_536)
    parser.add_argument("--holdout-blocks", type=int, default=16)
    parser.add_argument("--max-regressing-blocks", type=int, default=2)
    parser.add_argument("--max-largest-regression-bytes", type=int, default=32)
    parser.add_argument("--max-total-regression-bytes", type=int, default=64)
    parser.add_argument(
        "--required-incremental-bytes-per-1m", type=float, default=154.324
    )
    args = parser.parse_args()
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(receipt["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
