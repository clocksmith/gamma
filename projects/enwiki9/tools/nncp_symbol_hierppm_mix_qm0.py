#!/usr/bin/env python3
"""Screen a decoder-built hierarchical symbol PPM against mature NNCP."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import math
from pathlib import Path
import struct

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_symbol_hierppm_mix_qm0_v1"
TRACE_MAGIC = b"NNNTR4\0\0"
TRACE_HEADER = struct.Struct("<8sQQQQ")
TRACE_ROW = struct.Struct("<QQQQQQQQHHBBB")
TRACE_BRANCH = struct.Struct("<HB")
ROWS = 1_998_848
BLOCK_SYMBOLS = 499_712
STREAMS = 32
STREAM_STRIDE = 15_616
SEGMENT = 64
VOCABULARY = 16_392
SELECTION_START = 1_499_136
SELECTION_END = 1_998_848
ORDER1_CONCENTRATION = 16.0
ORDER2_CONCENTRATION = 8.0
TARGET_GAIN_BYTES = 7_000.0
CONTROL_MARGIN_BYTES = 1_000.0
SOURCE_LIMIT_BYTES = 65_536
EXPECTED = {
    "teacher_trace": (
        225_871_253,
        "230eb8823665cfe1724fee7de55103ed4d78fc31a0c3d7a2881754d78507acc9",
    ),
    "preprocessed": (
        401_217_922,
        "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5",
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(label: str, path: Path) -> dict[str, object]:
    expected_bytes, expected_sha = EXPECTED[label]
    result = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if result["bytes"] != expected_bytes or result["sha256"] != expected_sha:
        raise ValueError(f"{label} differs from frozen artifact")
    return result


def expected_bits(symbol: int) -> list[int]:
    start = 0
    active = VOCABULARY
    bits: list[int] = []
    while active > 1:
        left = active >> 1
        bit = int(symbol >= start + left)
        bits.append(bit)
        if bit:
            start += left
            active -= left
        else:
            active = left
    if start != symbol:
        raise ValueError("symbol tree path is invalid")
    return bits


def update_switch(weights: list[float], base: float, expert: float) -> float:
    mixture = weights[0] * base + weights[1] * expert
    if not 0.0 < mixture <= 1.0:
        raise ValueError("mixture probability is invalid")
    weights[0] = weights[0] * base / mixture
    weights[1] = weights[1] * expert / mixture
    return mixture


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--teacher-trace",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/teacher_native_trace.bin",
    )
    parser.add_argument(
        "--preprocessed",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/preprocessed.bin"
        ),
    )
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / f"results/{CANDIDATE_ID}"
    )
    args = parser.parse_args()
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=False)

    inputs = {
        "teacher_trace": artifact("teacher_trace", args.teacher_trace),
        "preprocessed": artifact("preprocessed", args.preprocessed),
    }
    symbols = np.memmap(args.preprocessed, mode="r", dtype=">u2")
    if len(symbols) * 2 != EXPECTED["preprocessed"][0]:
        raise ValueError("preprocessed symbol count changed")

    count0 = np.zeros(VOCABULARY, dtype=np.uint32)
    total0 = 0
    stream_count1: dict[int, int] = {}
    stream_total1 = np.zeros(VOCABULARY, dtype=np.uint32)
    stream_count2: dict[int, int] = {}
    stream_total2: dict[int, int] = {}
    global_count1: dict[int, int] = {}
    global_total1 = np.zeros(VOCABULARY, dtype=np.uint32)
    histories: list[list[int]] = [[] for _ in range(STREAMS)]
    global_previous: int | None = None
    arms = ("order0", "stream_order1", "stream_order2", "execution_order1")
    weights = {arm: [[0.5, 0.5] for _ in range(STREAMS)] for arm in arms}
    losses = {
        arm: {"mixture_bits": 0.0, "expert_bits": 0.0, "split_mixture_bits": [0.0] * 3}
        for arm in arms
    }
    baseline_bits = 0.0
    split_baseline_bits = [0.0] * 3
    seen = bytearray(ROWS)
    observed_branches = 0

    with args.teacher_trace.open("rb") as source:
        header = source.read(TRACE_HEADER.size)
        if len(header) != TRACE_HEADER.size:
            raise ValueError("truncated trace header")
        magic, rows, declared_branches, trees, checkpoints = TRACE_HEADER.unpack(header)
        if magic != TRACE_MAGIC or rows != ROWS or trees or checkpoints:
            raise ValueError("trace header differs from frozen contract")
        active_block = -1
        for execution in range(rows):
            raw_row = source.read(TRACE_ROW.size)
            if len(raw_row) != TRACE_ROW.size:
                raise ValueError("truncated trace row")
            (
                original,
                observed_execution,
                _before_bits,
                _after_bits,
                _before_bytes,
                _after_bytes,
                exact_bits,
                exact_bytes,
                symbol,
                vocabulary,
                branch_count,
                has_tree,
                checkpoint,
            ) = TRACE_ROW.unpack(raw_row)
            if observed_execution != execution or original >= ROWS or seen[original]:
                raise ValueError("trace execution/original permutation is invalid")
            seen[original] = 1
            if (
                vocabulary != VOCABULARY
                or symbol != int(symbols[original])
                or has_tree
                or checkpoint
                or exact_bits
                or exact_bytes
            ):
                raise ValueError("trace symbol or flags differ from frozen contract")
            block = original // BLOCK_SYMBOLS
            within = original - block * BLOCK_SYMBOLS
            stream = within // STREAM_STRIDE
            local = within - stream * STREAM_STRIDE
            if not 0 <= stream < STREAMS:
                raise ValueError("derived stream is invalid")
            expected_execution = block * BLOCK_SYMBOLS + local * STREAMS + stream
            if execution != expected_execution:
                raise ValueError("trace order differs from native state-major schedule")
            if block != active_block:
                if block != active_block + 1 or local != 0 or stream != 0:
                    raise ValueError("native block transition is invalid")
                histories = [[] for _ in range(STREAMS)]
                global_previous = None
                active_block = block

            bits = expected_bits(symbol)
            if len(bits) != branch_count:
                raise ValueError("trace branch count differs from symbol path")
            log_base = 0.0
            for expected_bit in bits:
                raw_branch = source.read(TRACE_BRANCH.size)
                if len(raw_branch) != TRACE_BRANCH.size:
                    raise ValueError("truncated branch row")
                probability0, bit = TRACE_BRANCH.unpack(raw_branch)
                if bit != expected_bit or not 1 <= probability0 < 32_768:
                    raise ValueError("trace branch truth/probability is invalid")
                mass = probability0 if bit == 0 else 32_768 - probability0
                log_base += math.log(mass / 32_768.0)
            observed_branches += branch_count
            base_probability = math.exp(log_base)

            p0 = (float(count0[symbol]) + 0.5) / (
                total0 + 0.5 * VOCABULARY
            )
            history = histories[stream]
            if history:
                previous = history[-1]
                key1 = previous * VOCABULARY + symbol
                p1 = (
                    stream_count1.get(key1, 0) + ORDER1_CONCENTRATION * p0
                ) / (float(stream_total1[previous]) + ORDER1_CONCENTRATION)
            else:
                p1 = p0
            if len(history) >= 2:
                context2 = history[-2] * VOCABULARY + history[-1]
                key2 = context2 * VOCABULARY + symbol
                p2 = (
                    stream_count2.get(key2, 0) + ORDER2_CONCENTRATION * p1
                ) / (stream_total2.get(context2, 0) + ORDER2_CONCENTRATION)
            else:
                p2 = p1
            if global_previous is not None:
                global_key = global_previous * VOCABULARY + symbol
                pg1 = (
                    global_count1.get(global_key, 0) + ORDER1_CONCENTRATION * p0
                ) / (
                    float(global_total1[global_previous]) + ORDER1_CONCENTRATION
                )
            else:
                pg1 = p0
            expert_probabilities = {
                "order0": p0,
                "stream_order1": p1,
                "stream_order2": p2,
                "execution_order1": pg1,
            }

            if local % SEGMENT == 0:
                for arm in arms:
                    weights[arm][stream] = [0.5, 0.5]
            selected = SELECTION_START <= execution < SELECTION_END
            split = min(2, (execution - SELECTION_START) * 3 // (SELECTION_END - SELECTION_START)) if selected else 0
            if selected:
                base_loss = -math.log2(base_probability)
                baseline_bits += base_loss
                split_baseline_bits[split] += base_loss
            for arm, expert_probability in expert_probabilities.items():
                mixture = update_switch(
                    weights[arm][stream], base_probability, expert_probability
                )
                if selected:
                    mixture_loss = -math.log2(mixture)
                    losses[arm]["mixture_bits"] += mixture_loss
                    losses[arm]["expert_bits"] += -math.log2(expert_probability)
                    losses[arm]["split_mixture_bits"][split] += mixture_loss

            if history:
                previous = history[-1]
                key1 = previous * VOCABULARY + symbol
                stream_count1[key1] = stream_count1.get(key1, 0) + 1
                stream_total1[previous] += 1
            if len(history) >= 2:
                context2 = history[-2] * VOCABULARY + history[-1]
                key2 = context2 * VOCABULARY + symbol
                stream_count2[key2] = stream_count2.get(key2, 0) + 1
                stream_total2[context2] = stream_total2.get(context2, 0) + 1
            if global_previous is not None:
                global_key = global_previous * VOCABULARY + symbol
                global_count1[global_key] = global_count1.get(global_key, 0) + 1
                global_total1[global_previous] += 1
            count0[symbol] += 1
            total0 += 1
            history.append(symbol)
            if len(history) > 2:
                del history[0]
            global_previous = symbol
        if source.read(1):
            raise ValueError("trace has trailing bytes")

    if observed_branches != declared_branches or not all(seen):
        raise ValueError("trace totals/permutation differ from header")
    evaluations: dict[str, dict[str, object]] = {}
    for arm in arms:
        gain = (baseline_bits - float(losses[arm]["mixture_bits"])) / 8.0
        split_gain = [
            (split_baseline_bits[index] - float(losses[arm]["split_mixture_bits"][index])) / 8.0
            for index in range(3)
        ]
        evaluations[arm] = {
            **losses[arm],
            "mixture_gain_bytes_vs_nncp": gain,
            "split_mixture_gain_bytes_vs_nncp": split_gain,
        }

    source_paths = [
        Path(__file__),
        ROOT / "docs/nncp_symbol_hierppm_mix_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    ]
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = args.output_dir / "diagnostic_source_package.lzma"
    source_path.write_bytes(source_package)

    main_gain = float(evaluations["stream_order2"]["mixture_gain_bytes_vs_nncp"])
    split_gain = [
        float(value)
        for value in evaluations["stream_order2"]["split_mixture_gain_bytes_vs_nncp"]
    ]
    margin_order1 = main_gain - float(
        evaluations["stream_order1"]["mixture_gain_bytes_vs_nncp"]
    )
    margin_execution = main_gain - float(
        evaluations["execution_order1"]["mixture_gain_bytes_vs_nncp"]
    )
    failed: list[str] = []
    if main_gain < TARGET_GAIN_BYTES:
        failed.append("stream_order2_gain_below_7000")
    if any(value <= 0 for value in split_gain):
        failed.append("stream_order2_chronological_third_nonpositive")
    if margin_order1 < CONTROL_MARGIN_BYTES:
        failed.append("margin_over_stream_order1_below_1000")
    if margin_execution < CONTROL_MARGIN_BYTES:
        failed.append("margin_over_execution_order1_below_1000")
    if len(source_package) > SOURCE_LIMIT_BYTES:
        failed.append("diagnostic_source_exceeds_65536")

    decision = {
        "schema": "enwiki9_nncp_symbol_hierppm_mix_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "mature_same_symbol_domain_causal_logloss_shadow_zero_credit",
        "verdict": "authorize_finite_symbol_mixture" if not failed else "retire_nncp_symbol_hierppm_mix",
        "inputs": inputs,
        "population": {
            "execution_rows": ROWS,
            "selection_start": SELECTION_START,
            "selection_end": SELECTION_END,
            "selected_symbols": SELECTION_END - SELECTION_START,
            "native_streams": STREAMS,
            "native_segment_symbols": SEGMENT,
            "vocabulary": VOCABULARY,
        },
        "model": {
            "order0_alpha_per_symbol": 0.5,
            "order1_concentration": ORDER1_CONCENTRATION,
            "order2_concentration": ORDER2_CONCENTRATION,
            "switch_prior": [0.5, 0.5],
            "switch_reset": "each existing 64-symbol native stream segment",
            "stream_order1_pairs": len(stream_count1),
            "stream_order2_triples": len(stream_count2),
            "execution_order1_pairs": len(global_count1),
        },
        "accounting": {
            "nncp_baseline_ideal_bits": baseline_bits,
            "evaluations": evaluations,
            "stream_order2_margin_over_stream_order1_bytes": margin_order1,
            "stream_order2_margin_over_execution_order1_bytes": margin_execution,
            "diagnostic_source_package_bytes": len(source_package),
            "target_gain_bytes": TARGET_GAIN_BYTES,
            "control_margin_bytes": CONTROL_MARGIN_BYTES,
            "score_credit_bytes": 0,
        },
        "proof": {
            "trace_original_ordinal_permutation_complete": True,
            "trace_execution_order_exact": True,
            "preprocessed_symbol_identity_exact": True,
            "same_normalized_symbol_alphabet": True,
            "expert_updates_after_truth": True,
            "switch_updates_after_truth": True,
        },
        "artifacts": {
            "diagnostic_source_package": {
                "path": str(source_path.relative_to(ROOT)),
                "bytes": source_path.stat().st_size,
                "sha256": sha256_file(source_path),
            }
        },
        "failed_conditions": failed,
        "claim_boundary": "Causal ideal-codelength shadow over the exact mature NNCP branch trace. No independently terminated mixture stream, native decoder, package forecast, published-score inheritance, or Hutter score exists.",
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "verdict": decision["verdict"],
                "stream_order2_gain_bytes": main_gain,
                "split_gain_bytes": split_gain,
                "margin_over_stream_order1_bytes": margin_order1,
                "margin_over_execution_order1_bytes": margin_execution,
                "failed_conditions": failed,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
