#!/usr/bin/env python3
"""Price TEXT3-style causal structural coordinates over Endpoint428 P1."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import math
from pathlib import Path

import numpy as np

import fractal4_slot_residual_quotient_qm1 as qbase
import janus_paid_residual_mdl_oracle as janus
import wrt_exact


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "text3_structural_joint_shadow_qm0_v1"
HASH_MASK = np.uint64((1 << 48) - 1)
QBITS_PER_BYTE = qbase.QBITS_PER_BIT * 8
PARENT_PRIOR = 0.99
EXPERT_PRIOR = 0.01
SHUFFLE_OFFSET = 104_729
CHUNK_ROWS = 2_000_000


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def text3_class_map() -> np.ndarray:
    """Reproduce the four broad byte classes initialized by text3.cfg."""
    table = np.full(256, 3, dtype=np.uint8)
    table[48:96] = 2
    table[96:208] = 1
    table[49:59] = 1
    table[[0, 7]] = 2
    table[[2, 6, 12]] = 1
    table[[5, 10, 11]] = 0
    return table


def prefix_state(stream: np.ndarray) -> dict[str, np.ndarray]:
    """Materialize only state available before each byte is decoded."""
    size = len(stream)
    class_history = np.empty(size, dtype=np.uint16)
    column = np.empty(size, dtype=np.uint8)
    bracket = np.empty(size, dtype=np.uint8)
    word_phase = np.empty(size, dtype=np.uint8)
    colon_word = np.empty(size, dtype=np.uint16)
    transition_state = np.empty(size, dtype=np.uint16)
    previous_byte = np.empty(size, dtype=np.uint8)

    classes = text3_class_map()
    transitions = np.zeros(256, dtype=np.uint16)
    cls = 0
    col = 0
    depth = 0
    phase = 0
    current_word = 0
    prior_word = 0
    colon = 0
    previous = 0

    for index, value in enumerate(stream):
        byte = int(value)
        class_history[index] = cls
        column[index] = col
        bracket[index] = depth
        word_phase[index] = phase
        colon_word[index] = colon
        transition_state[index] = transitions[previous]
        previous_byte[index] = previous

        transitions[previous] = ((int(transitions[previous]) << 8) | byte) & 0xFFFF
        previous = byte
        cls = ((cls << 2) | int(classes[byte])) & 0xFFFF
        if byte in (34, 39, 124):
            cls = (cls << 2) & 0xFFFF
        elif byte == 10:
            cls = ((cls << 2) | 0xFC) & 0xFFFF

        if byte == 10:
            col = 0
        else:
            col = min(63, col + 1)

        if byte in (91, 123):
            depth = min(15, depth + 1)
        elif byte in (93, 125):
            depth = max(0, depth - 1)

        folded = byte & ~32
        is_word = (65 <= folded <= 90) or byte >= 128
        if is_word:
            current_word = ((current_word * 191) + folded) & 0xFFFF
            phase = min(15, phase + 1)
        else:
            if current_word:
                prior_word = current_word
            current_word = 0
            phase = 0
            if byte == 58:
                colon = prior_word
            elif byte in (10, 46):
                colon = 0

    return {
        "class_history": class_history,
        "column": column,
        "bracket": bracket,
        "word_phase": word_phase,
        "colon_word": colon_word,
        "transition_state": transition_state,
        "previous_byte": previous_byte,
    }


def hash_context(seed: int, *coordinates: np.ndarray) -> np.ndarray:
    result = np.full(len(coordinates[0]), np.uint64(seed), dtype=np.uint64)
    constant = np.uint64(0x9E3779B97F4A7C15)
    for coordinate in coordinates:
        value = coordinate.astype(np.uint64, copy=False)
        result ^= value + constant + (result << np.uint64(6)) + (result >> np.uint64(2))
        result &= HASH_MASK
    return result


def contexts(state: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    c0 = hash_context(0xC01, state["class_history"], state["previous_byte"])
    l0 = hash_context(0xC02, state["column"], state["previous_byte"])
    joint = hash_context(
        0xC03,
        state["class_history"],
        state["column"],
        state["bracket"],
        state["word_phase"],
        state["colon_word"],
        state["transition_state"],
        state["previous_byte"],
    )
    shuffled = np.roll(joint, SHUFFLE_OFFSET)
    return {"C0": c0, "L0": l0, "S0": shuffled, "J0": joint}


def bit_node_keys(byte_context: np.ndarray, stream: np.ndarray) -> np.ndarray:
    nodes = np.empty((len(stream), 8), dtype=np.uint16)
    values = stream.astype(np.uint16, copy=False)
    for depth in range(8):
        nodes[:, depth] = (1 << depth) + (values >> (8 - depth))
    return (np.repeat(byte_context, 8) << np.uint64(9)) | nodes.reshape(-1).astype(np.uint64)


def causal_kt(keys: np.ndarray, truth: np.ndarray) -> tuple[np.ndarray, int]:
    order = np.argsort(keys, kind="stable")
    sorted_keys = keys[order]
    sorted_truth = truth[order].astype(np.int64)
    boundaries = np.flatnonzero(np.diff(sorted_keys)) + 1
    starts = np.concatenate((np.asarray([0], dtype=np.int64), boundaries))
    ends = np.concatenate((boundaries, np.asarray([len(keys)], dtype=np.int64)))
    lengths = ends - starts
    cumulative = np.cumsum(sorted_truth, dtype=np.int64)
    ones_before_group = np.zeros(len(starts), dtype=np.int64)
    nonzero = starts != 0
    ones_before_group[nonzero] = cumulative[starts[nonzero] - 1]
    base_ones = np.repeat(ones_before_group, lengths)
    base_rows = np.repeat(starts, lengths)
    ones_before = cumulative - sorted_truth - base_ones
    rows_before = np.arange(len(keys), dtype=np.int64) - base_rows
    sorted_probability = ((ones_before + 0.5) / (rows_before + 1.0)).astype(np.float32)
    probability = np.empty(len(keys), dtype=np.float32)
    probability[order] = sorted_probability
    return probability, len(starts)


def score_expert(
    expert: np.ndarray,
    parent_p1: np.ndarray,
    truth: np.ndarray,
) -> dict[str, object]:
    zero_qbits, one_qbits = qbase.qbit_tables()
    totals = {
        "parent": 0,
        "expert": 0,
        "oracle": 0,
        "bayes": 0,
    }
    splits = {name: [0, 0, 0] for name in ("expert", "oracle", "bayes")}
    log_odds = math.log(EXPERT_PRIOR / PARENT_PRIOR)
    row_count = len(truth)

    for low in range(0, row_count, CHUNK_ROWS):
        high = min(row_count, low + CHUNK_ROWS)
        bits = truth[low:high]
        parent_q16 = parent_p1[low:high]
        parent = np.clip(parent_q16.astype(np.float64) / 65536.0, 1 / 65536, 65535 / 65536)
        candidate = np.clip(expert[low:high].astype(np.float64), 1 / 65536, 65535 / 65536)

        parent_correct = np.where(bits != 0, parent, 1.0 - parent)
        candidate_correct = np.where(bits != 0, candidate, 1.0 - candidate)
        evidence = np.log(candidate_correct) - np.log(parent_correct)
        cumulative = np.cumsum(evidence)
        before = log_odds + cumulative - evidence
        weight = np.empty_like(before)
        positive = before >= 0
        weight[positive] = 1.0 / (1.0 + np.exp(-before[positive]))
        exponent = np.exp(before[~positive])
        weight[~positive] = exponent / (1.0 + exponent)
        log_odds += float(cumulative[-1])

        bayes = parent + weight * (candidate - parent)
        expert_q16 = np.clip(np.rint(candidate * 65536.0), 1, 65535).astype(np.uint16)
        bayes_q16 = np.clip(np.rint(bayes * 65536.0), 1, 65535).astype(np.uint16)
        parent_loss = np.where(bits != 0, one_qbits[parent_q16], zero_qbits[parent_q16]).astype(np.int64)
        expert_loss = np.where(bits != 0, one_qbits[expert_q16], zero_qbits[expert_q16]).astype(np.int64)
        bayes_loss = np.where(bits != 0, one_qbits[bayes_q16], zero_qbits[bayes_q16]).astype(np.int64)
        oracle_loss = np.minimum(parent_loss, expert_loss)

        totals["parent"] += int(parent_loss.sum())
        totals["expert"] += int(expert_loss.sum())
        totals["oracle"] += int(oracle_loss.sum())
        totals["bayes"] += int(bayes_loss.sum())
        positions = np.arange(low, high, dtype=np.int64)
        split_ids = np.minimum(2, positions * 3 // row_count)
        for name, loss in (("expert", expert_loss), ("oracle", oracle_loss), ("bayes", bayes_loss)):
            gain = parent_loss - loss
            values = np.bincount(split_ids, weights=gain, minlength=3).astype(np.int64)
            for index in range(3):
                splits[name][index] += int(values[index])

    receipt: dict[str, object] = {
        "rows": row_count,
        "final_expert_log_odds": log_odds,
        "loss_qbits": totals,
    }
    for name in ("expert", "oracle", "bayes"):
        gain = totals["parent"] - totals[name]
        receipt[name] = {
            "gain_qbits": gain,
            "gain_bytes": gain / QBITS_PER_BYTE,
            "chronological_gain_bytes": [value / QBITS_PER_BYTE for value in splits[name]],
        }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-input", type=Path, default=ROOT / "data/enwik9_10000000.bin")
    parser.add_argument(
        "--wrt-store",
        type=Path,
        default=ROOT / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin",
    )
    parser.add_argument(
        "--dictionary", type=Path, default=ROOT / "external/fx2-cmix/dictionary/english.dic"
    )
    parser.add_argument(
        "--parent-p1",
        type=Path,
        default=ROOT / "results/fractal2_endpoint428_trace_10m_v1/endpoint428.p1",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)

    raw = args.raw_input.read_bytes()
    parsed = wrt_exact.parse_store(args.wrt_store, args.dictionary)
    if parsed.decoded != raw:
        raise RuntimeError("canonical WRT store does not invert to the raw input")
    stream = np.frombuffer(parsed.stream, dtype=np.uint8)
    truth = np.unpackbits(stream, bitorder="big")
    magic, parent_p1 = janus.read_p1(args.parent_p1, len(truth))

    state = prefix_state(stream)
    arms_context = contexts(state)
    joint_repeat = contexts(state)["J0"]
    context_repeat_identical = bool(np.array_equal(arms_context["J0"], joint_repeat))
    del joint_repeat

    arms: dict[str, object] = {}
    for name in ("C0", "L0", "S0", "J0"):
        keys = bit_node_keys(arms_context[name], stream)
        expert, context_count = causal_kt(keys, truth)
        del keys
        scored = score_expert(expert, parent_p1, truth)
        scored["contexts"] = context_count
        arms[name] = scored
        del expert

    source_package = lzma.compress(Path(__file__).read_bytes(), preset=9 | lzma.PRESET_EXTREME)
    (args.output_dir / "shadow_source.lzma").write_bytes(source_package)
    j0 = arms["J0"]["bayes"]
    gross = float(j0["gain_bytes"])
    net = gross - len(source_package)
    controls = {
        name: gross - float(arms[name]["bayes"]["gain_bytes"])
        for name in ("C0", "L0", "S0")
    }
    thirds = [float(value) for value in j0["chronological_gain_bytes"]]
    failed: list[str] = []
    if gross < 45_000:
        failed.append("J0_bayes_gain_below_45000_bytes")
    if net < 40_000:
        failed.append("J0_net_gain_below_40000_bytes")
    if any(value <= 0 for value in thirds):
        failed.append("J0_chronological_third_nonpositive")
    for name, margin in controls.items():
        if margin < 5_000:
            failed.append(f"J0_margin_over_{name}_below_5000_bytes")
    if not context_repeat_identical:
        failed.append("joint_context_repeat_not_identical")

    decision = {
        "schema": "enwiki9_text3_structural_joint_shadow_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "causal_shadow_zero_score_credit",
        "verdict": "authorize_native_text3_structural_joint" if not failed else "retire_text3_structural_joint",
        "inputs": {
            "raw": artifact(args.raw_input),
            "wrt_store": artifact(args.wrt_store),
            "wrt_stream_bytes": len(stream),
            "wrt_stream_sha256": hashlib.sha256(parsed.stream).hexdigest(),
            "dictionary": artifact(args.dictionary),
            "parent_p1": artifact(args.parent_p1),
            "parent_p1_magic": magic,
        },
        "source_audit": {
            "text3_zip_sha256": "54491c9d5e57cd60adef1cde5b61447b5c272525b6ce68e11b6beceac87826b2",
            "text3_cfg_bytes": 5619,
            "text3_cfg_sha256": "395e5c2338fd2bcbfa6f6616e84568c357278baa044291236d65daeec0fead91",
        },
        "population": {
            "rows": len(truth),
            "parent_prior": PARENT_PRIOR,
            "expert_prior": EXPERT_PRIOR,
            "context_hash_bits": 48,
            "shuffle_offset_bytes": SHUFFLE_OFFSET,
        },
        "arms": arms,
        "accounting": {
            "gross_bayes_gain_bytes": gross,
            "compressed_shadow_source_bytes": len(source_package),
            "net_bayes_gain_bytes": net,
            "margins_over_controls_bytes": controls,
            "full_forecast_debt_bytes": 4_389_323,
            "linear_10m_leverage_bytes": gross * 100,
            "score_credit_bytes": 0,
        },
        "proof": {
            "wrt_inverse_exact": True,
            "state_is_prefix_causal": True,
            "current_byte_key_contains_only_decoded_prefix": True,
            "KT_counts_use_only_prior_same_context_bits": True,
            "bayes_mixture_has_exact_parent_expert": True,
            "joint_context_repeat_identical": context_repeat_identical,
        },
        "failed_conditions": failed,
        "claim_boundary": "Causal shadow only. Oracle rows are zero-credit ceilings; no native payload, archive, source-bound forecast, full-1G score, or runtime claim is authorized by this receipt.",
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

