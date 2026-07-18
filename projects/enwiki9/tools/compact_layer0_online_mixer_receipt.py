#!/usr/bin/env python3
"""Seal exact arithmetic evidence for a frozen compact online-mixer P1 stream."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from compact_layer0_blend_screen import same_file
from fx2_attribution_external_base_screen import (
    P1_HEADER_BYTES,
    PPM,
    artifact,
    cmix_archive_header_bytes,
    exact_block_audit,
    exact_replay,
    qbit_tables,
    read_p1_header,
)


def qbit_gain(truth: np.ndarray, base: np.ndarray, candidate: np.ndarray) -> int:
    loss0, loss1 = qbit_tables()
    return int(
        (
            np.where(truth, loss1[base], loss0[base])
            - np.where(truth, loss1[candidate], loss0[candidate])
        ).sum(dtype=np.int64)
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    screen = json.loads(args.screen_json.read_text())
    if screen.get("schema") not in {
        "compact_layer0_online_mixer_screen_v1",
        "compact_layer0_online_mixer_screen_v2",
    }:
        raise ValueError("unsupported online-mixer screen schema")
    scope = screen.get("scope", {})
    if scope.get("selection_reads_holdout") is not False:
        raise ValueError("screen does not prove holdout-blind selection")
    if screen.get("deterministic_probability_replay") is not True:
        raise ValueError("screen does not prove deterministic probability replay")

    _, base_rows = read_p1_header(args.base_p1)
    _, candidate_rows = read_p1_header(args.candidate_p1)
    rows = int(scope.get("rows", 0))
    if rows < 1 or rows != base_rows or rows != candidate_rows:
        raise ValueError("screen and P1 row counts differ")
    train_end = int(scope["train_end_row"])
    dev_end = int(scope["dev_end_row"])
    if not 0 < train_end < dev_end < rows:
        raise ValueError("invalid frozen split boundaries")
    store_bytes = args.wrt_store.read_bytes()
    if len(store_bytes) < 5 or (len(store_bytes) - 5) * 8 != rows:
        raise ValueError("WRT truth store and P1 rows differ")

    base = np.memmap(
        args.base_p1,
        mode="r",
        dtype="<u2",
        offset=P1_HEADER_BYTES,
        shape=(rows,),
    )
    candidate = np.memmap(
        args.candidate_p1,
        mode="r",
        dtype="<u2",
        offset=P1_HEADER_BYTES,
        shape=(rows,),
    )
    truth = np.unpackbits(
        np.frombuffer(store_bytes, dtype=np.uint8, offset=5), bitorder="big"
    )
    split_qbits = {
        "train_gain_qbits": qbit_gain(
            truth[:train_end], base[:train_end], candidate[:train_end]
        ),
        "dev_gain_qbits": qbit_gain(
            truth[train_end:dev_end],
            base[train_end:dev_end],
            candidate[train_end:dev_end],
        ),
        "holdout_gain_qbits": qbit_gain(
            truth[dev_end:], base[dev_end:], candidate[dev_end:]
        ),
    }
    scorer_qbits = screen.get("qbit_replay", {})
    qbit_identity = split_qbits == scorer_qbits

    exact_full, replayed_base_payload, candidate_payload = exact_replay(
        truth, base, candidate
    )
    exact_holdout, _, _ = exact_replay(
        truth[dev_end:], base[dev_end:], candidate[dev_end:]
    )
    block_audit = exact_block_audit(
        truth[dev_end:], base[dev_end:], candidate[dev_end:], args.holdout_blocks
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
        qbit_identity
        and archive_payload_identity
        and native_archive_identity is not False
        and pair_trace_identity is not False
    )
    if args.candidate_payload is not None:
        args.candidate_payload.parent.mkdir(parents=True, exist_ok=True)
        args.candidate_payload.write_bytes(candidate_payload)

    full_rate = exact_full["saved_bytes"] * 1_000_000 / args.raw_scope_bytes
    holdout_raw_scope = args.raw_scope_bytes * (rows - dev_end) / rows
    holdout_rate = exact_holdout["saved_bytes"] * 1_000_000 / holdout_raw_scope
    required_rate = (
        args.remaining_debt_bytes_per_1m + args.provisional_code_bytes / 1000
    )
    economics_ok = full_rate >= required_rate and holdout_rate >= required_rate
    regret_ok = bool(
        block_audit["regressing_blocks"] <= args.max_regressing_blocks
        and block_audit["largest_regression_bytes"] <= args.max_largest_regression_bytes
        and block_audit["total_regression_bytes"] <= args.max_total_regression_bytes
    )
    verdict = (
        "compact_layer0_online_mixer_pass_requires_native_integration"
        if identities_ok and economics_ok and regret_ok
        else "retire_frozen_compact_layer0_online_mixer"
    )
    return {
        "schema": "compact_layer0_online_mixer_receipt_v1",
        "evidence_level": "causal_dev_selected_exact_arithmetic_shadow",
        "inputs": {
            "screen_json": artifact(args.screen_json),
            "screen_source": artifact(args.screen_source),
            "screen_binary": artifact(args.screen_binary),
            "base_p1": artifact(args.base_p1),
            "candidate_p1": artifact(args.candidate_p1),
            "pair_trace": artifact(args.pair_trace)
            if args.pair_trace is not None
            else None,
            "base_archive": artifact(args.base_archive),
            "wrt_store": artifact(args.wrt_store),
        },
        "scope": {
            "raw_bytes": args.raw_scope_bytes,
            "rows": rows,
            "train_end_row": train_end,
            "dev_end_row": dev_end,
            "selection_reads_holdout": False,
        },
        "selection": screen.get("selection"),
        "causality": screen.get("causality"),
        "identity": {
            "qbit_replay_identity": qbit_identity,
            "base_archive_payload_identity": archive_payload_identity,
            "instrumented_archive_byte_identity": native_archive_identity,
            "instrumented_pair_trace_byte_identity": pair_trace_identity,
            "deterministic_probability_replay": True,
            "all_required_identities_pass": identities_ok,
        },
        "qbit_replay": split_qbits,
        "exact_replay": {
            "full": exact_full,
            "holdout": exact_holdout,
            "full_saved_bytes_per_1m_raw": full_rate,
            "holdout_saved_bytes_per_proportional_1m_raw": holdout_rate,
            "holdout_block_audit": block_audit,
            "candidate_payload_artifact": artifact(args.candidate_payload)
            if args.candidate_payload is not None
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
            "Exact arithmetic replay of a deterministic causal probability "
            "stream. Native integration, counted source delta, codec roundtrip, "
            "RSS, disjoint confirmation, and full-enwik9 proof remain required."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screen-json", type=Path, required=True)
    parser.add_argument("--screen-source", type=Path, required=True)
    parser.add_argument("--screen-binary", type=Path, required=True)
    parser.add_argument("--base-p1", type=Path, required=True)
    parser.add_argument("--candidate-p1", type=Path, required=True)
    parser.add_argument("--pair-trace", type=Path)
    parser.add_argument("--base-archive", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--raw-scope-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-payload", type=Path)
    parser.add_argument("--instrumented-archive", type=Path)
    parser.add_argument("--reference-native-archive", type=Path)
    parser.add_argument("--instrumented-pair-trace", type=Path)
    parser.add_argument("--reference-pair-trace", type=Path)
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
