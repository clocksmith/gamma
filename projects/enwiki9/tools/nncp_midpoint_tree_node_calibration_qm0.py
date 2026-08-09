#!/usr/bin/env python3
"""Replay decoder-built midpoint tree-node calibration over exact NNCP."""

from __future__ import annotations

import hashlib
import json
import lzma
import math
from pathlib import Path
import resource

import numpy as np

import nncp_midpoint_phase_attribution_qm0 as phase
import nncp_symbol_cache32_marginal_qm0 as common


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_midpoint_tree_node_calibration_qm0_v1"
PARENT_ID = "nncp_midsegment32_update_262144_qm1_v1"
SYMBOL_PATH = common.SYMBOL_PATH
SYMBOL_COUNT = common.SYMBOL_COUNT
STREAMS = common.STREAMS
STREAM_LENGTH = common.STREAM_LENGTH
SEGMENT = common.SEGMENT
MIDPOINT = SEGMENT // 2
VOCABULARY = common.VOCABULARY
EXPECTED_BRANCHES = common.EXPECTED_BRANCHES
PROBABILITY_TOTAL = common.PROBABILITY_TOTAL
BASE_PRIOR = 16.0
EXPERT_PRIOR = 1.0
GAIN_GATE_BYTES = 7_500
CONTROL_MARGIN_BYTES = 1_000
SOURCE_LIMIT_BYTES = 65_536
EXPECTED_SHA256 = {
    "symbols": "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5",
    "faithful_trace": "8c37f952fab1242743366b99083243263cb7eb5309cd10f45a36e99188a0a706",
}
EXPECTED_BASE = (
    341_558,
    "99c7d04d174f7ba1a30ae5b4af5c5b5d248cf33225713c1de2ed28862b5ec8c6",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def node_probability(
    base_zero: int,
    counts: tuple[int, int] | None,
    base_weight: float,
    expert_weight: float,
) -> tuple[int, float, float]:
    base_p0 = base_zero / PROBABILITY_TOTAL
    if counts is None or counts[1] == 0 or expert_weight == 0.0:
        return base_zero, base_p0, 0.0
    expert_p0 = (counts[0] + 0.5) / (counts[1] + 1.0)
    mixture = (
        base_weight * base_p0 + expert_weight * expert_p0
    ) / (base_weight + expert_weight)
    frequency = min(
        max(int(round(mixture * PROBABILITY_TOTAL)), 1),
        PROBABILITY_TOTAL - 1,
    )
    return frequency, base_p0, expert_p0


def update_weights(
    bit: int,
    base_p0: float,
    expert_p0: float,
    base_weight: float,
    expert_weight: float,
) -> tuple[float, float]:
    if expert_weight == 0.0:
        return 1.0, 0.0
    base_weight *= base_p0 if bit == 0 else 1.0 - base_p0
    expert_weight *= expert_p0 if bit == 0 else 1.0 - expert_p0
    total = base_weight + expert_weight
    if total <= 0.0:
        raise ValueError("realized branch has zero mixture mass")
    return base_weight / total, expert_weight / total


def add_count(
    table: dict[object, list[int]], key: object, bit: int
) -> None:
    row = table.setdefault(key, [0, 0])
    row[0] += int(bit == 0)
    row[1] += 1


def frozen_counts(
    table: dict[object, list[int]], key: object
) -> tuple[int, int] | None:
    row = table.get(key)
    return (row[0], row[1]) if row is not None else None


def encode_all(
    symbols: np.ndarray, faithful_trace: np.ndarray
) -> dict[str, object]:
    matrix = symbols.reshape(STREAMS, STREAM_LENGTH)
    arms = ("base", "node", "depth", "prior")
    encoders = {arm: common.RangeEncoder() for arm in arms}
    repeat = common.RangeEncoder()
    thirds = {
        arm: [common.RangeEncoder() for _ in range(3)] for arm in arms
    }
    ideal_bits = {arm: 0.0 for arm in arms}
    previous_nodes: dict[object, list[int]] = {}
    branch = 0

    for segment_start in range(0, STREAM_LENGTH, SEGMENT):
        current_nodes: dict[object, list[int]] = {}
        current_depths: dict[object, list[int]] = {}
        for state in range(SEGMENT):
            absolute = segment_start + state
            collecting = state < MIDPOINT
            for stream in range(STREAMS):
                original = stream * STREAM_LENGTH + absolute
                third = common.third_for_original(original)
                symbol = int(matrix[stream, absolute])
                weights = {
                    arm: [BASE_PRIOR, EXPERT_PRIOR]
                    for arm in ("node", "depth", "prior")
                }
                start = 0
                active = VOCABULARY
                depth = 0
                for bit in phase.expected_bits(symbol):
                    base_zero = int(faithful_trace[branch])
                    if not 1 <= base_zero < PROBABILITY_TOTAL:
                        raise ValueError("illegal faithful branch frequency")
                    node = (start, active)
                    statistics = {
                        "node": frozen_counts(current_nodes, node)
                        if not collecting
                        else None,
                        "depth": frozen_counts(current_depths, depth)
                        if not collecting
                        else None,
                        "prior": frozen_counts(previous_nodes, node)
                        if not collecting
                        else None,
                    }
                    probabilities = {"base": base_zero}
                    for arm in ("node", "depth", "prior"):
                        row = statistics[arm]
                        if row is None:
                            weights[arm][1] = 0.0
                        probability, base_p0, expert_p0 = node_probability(
                            base_zero, row, weights[arm][0], weights[arm][1]
                        )
                        probabilities[arm] = probability
                        weights[arm][0], weights[arm][1] = update_weights(
                            bit,
                            base_p0,
                            expert_p0,
                            weights[arm][0],
                            weights[arm][1],
                        )
                    for arm, probability in probabilities.items():
                        encoders[arm].put_bit(probability, bit)
                        thirds[arm][third].put_bit(probability, bit)
                        realized = (
                            probability if bit == 0
                            else PROBABILITY_TOTAL - probability
                        )
                        ideal_bits[arm] -= math.log2(
                            realized / PROBABILITY_TOTAL
                        )
                    repeat.put_bit(probabilities["node"], bit)
                    if collecting:
                        add_count(current_nodes, node, bit)
                        add_count(current_depths, depth, bit)
                    left = active >> 1
                    if bit:
                        start += left
                        active -= left
                    else:
                        active = left
                    depth += 1
                    branch += 1
                if start != symbol or active != 1:
                    raise ValueError("symbol path did not terminate at truth")
        previous_nodes = current_nodes

    if branch != EXPECTED_BRANCHES:
        raise ValueError("faithful branch trace was not consumed exactly")
    return {
        "payloads": {arm: coder.finish() for arm, coder in encoders.items()},
        "repeat_payload": repeat.finish(),
        "third_payloads": {
            arm: [coder.finish() for coder in coders]
            for arm, coders in thirds.items()
        },
        "ideal_bits": ideal_bits,
        "branches": branch,
    }


def decode_node(
    payload: bytes,
    faithful_trace: np.ndarray,
    expected_symbols: np.ndarray,
) -> dict[str, object]:
    expected = expected_symbols.reshape(STREAMS, STREAM_LENGTH)
    decoded = np.zeros_like(expected)
    decoder = common.RangeDecoder(payload)
    previous_nodes: dict[object, list[int]] = {}
    branch = 0

    for segment_start in range(0, STREAM_LENGTH, SEGMENT):
        current_nodes: dict[object, list[int]] = {}
        for state in range(SEGMENT):
            absolute = segment_start + state
            collecting = state < MIDPOINT
            for stream in range(STREAMS):
                base_weight = BASE_PRIOR
                expert_weight = EXPERT_PRIOR
                start = 0
                active = VOCABULARY
                while active > 1:
                    node = (start, active)
                    counts = (
                        frozen_counts(current_nodes, node)
                        if not collecting
                        else None
                    )
                    if counts is None:
                        expert_weight = 0.0
                    base_zero = int(faithful_trace[branch])
                    probability, base_p0, expert_p0 = node_probability(
                        base_zero, counts, base_weight, expert_weight
                    )
                    bit = decoder.get_bit(probability)
                    base_weight, expert_weight = update_weights(
                        bit,
                        base_p0,
                        expert_p0,
                        base_weight,
                        expert_weight,
                    )
                    if collecting:
                        add_count(current_nodes, node, bit)
                    left = active >> 1
                    if bit:
                        start += left
                        active -= left
                    else:
                        active = left
                    branch += 1
                decoded[stream, absolute] = start
                if start != int(expected[stream, absolute]):
                    raise ValueError("node-calibrated decode differs from truth")
        previous_nodes = current_nodes

    if branch != EXPECTED_BRANCHES:
        raise ValueError("decoder consumed the wrong branch population")
    del previous_nodes
    return {
        "branches": branch,
        "decoded_sha256": common.sha256_bytes(
            decoded.astype(">u2", copy=False).tobytes()
        ),
        "symbols_exact": bool(np.array_equal(decoded, expected)),
    }


def main() -> int:
    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(
            f"refusing to replace existing output directory: {output_dir}"
        )
    parent_dir = ROOT / "results" / PARENT_ID
    trace_path = parent_dir / "faithful_baseline_trace.bin"
    decision_path = parent_dir / "decision.json"
    hashes = {
        "symbols": sha256_file(SYMBOL_PATH),
        "faithful_trace": sha256_file(trace_path),
    }
    if hashes != EXPECTED_SHA256:
        raise ValueError("receipt-bound symbols or trace changed")
    parent = json.loads(decision_path.read_text())
    if parent.get("verdict") != "authorize_native_midsegment_integration":
        raise ValueError("exact midpoint antecedent is not passed")

    symbols = np.asarray(
        np.memmap(SYMBOL_PATH, mode="r", dtype=">u2")[:SYMBOL_COUNT],
        dtype=np.uint16,
    )
    trace = np.memmap(trace_path, mode="r", dtype="<u2")
    replay = encode_all(symbols, trace)
    payloads = replay["payloads"]
    decode = decode_node(payloads["node"], trace, symbols)

    output_dir.mkdir(parents=True)
    for arm, payload in payloads.items():
        (output_dir / f"{arm}.bin").write_bytes(payload)
    base_identity = (
        len(payloads["base"]) == EXPECTED_BASE[0]
        and common.sha256_bytes(payloads["base"]) == EXPECTED_BASE[1]
    )
    gains = {
        arm: len(payloads["base"]) - len(payloads[arm])
        for arm in ("node", "depth", "prior")
    }
    margins = {
        "over_depth": len(payloads["depth"]) - len(payloads["node"]),
        "over_prior": len(payloads["prior"]) - len(payloads["node"]),
    }
    third_gains = [
        len(replay["third_payloads"]["base"][index])
        - len(replay["third_payloads"]["node"][index])
        for index in range(3)
    ]

    source_paths = (
        Path(__file__),
        ROOT / "docs/nncp_midpoint_tree_node_calibration_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/program.py",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
        ROOT
        / f"operations/adaptive/proposals/developed/000_{CANDIDATE_ID}.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes()
        for path in source_paths
    )
    source_package = lzma.compress(
        source_blob, preset=9 | lzma.PRESET_EXTREME
    )
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)

    conditions = {
        "base_payload_reproduced": base_identity,
        "node_gain_at_least_7500": gains["node"] >= GAIN_GATE_BYTES,
        "all_chronological_thirds_positive": all(
            value > 0 for value in third_gains
        ),
        "margin_over_depth_at_least_1000": (
            margins["over_depth"] >= CONTROL_MARGIN_BYTES
        ),
        "margin_over_prior_at_least_1000": (
            margins["over_prior"] >= CONTROL_MARGIN_BYTES
        ),
        "repeat_payload_identical": (
            replay["repeat_payload"] == payloads["node"]
        ),
        "arithmetic_decode_exact": bool(decode["symbols_exact"]),
        "branch_population_exact": replay["branches"] == EXPECTED_BRANCHES,
        "source_at_most_65536": len(source_package) <= SOURCE_LIMIT_BYTES,
    }
    passed = all(conditions.values())
    decision = {
        "schema": "enwiki9_nncp_midpoint_tree_node_calibration_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "CAUSAL_SHADOW_COMPLETE",
        "verdict": (
            "authorize_open_midpoint_tree_node_port"
            if passed
            else "retire_midpoint_tree_node_calibration"
        ),
        "epistemic_tier": (
            "same_symbol_domain_exact_arithmetic_shadow_zero_score_credit"
        ),
        "score_credit_bytes": 0,
        "model": {
            "base_prior_mass": BASE_PRIOR,
            "expert_prior_mass": EXPERT_PRIOR,
            "first_half_states": MIDPOINT,
            "pooling_streams": STREAMS,
            "node_law": "KT(zero,total)",
            "segment_reset": True,
            "transmitted_state": False,
        },
        "population": {
            "symbols": SYMBOL_COUNT,
            "branches": EXPECTED_BRANCHES,
            "streams": STREAMS,
            "symbols_per_stream": STREAM_LENGTH,
            "segment_symbols": SEGMENT,
            "vocabulary": VOCABULARY,
        },
        "inputs": {
            "symbols": {"path": str(SYMBOL_PATH), "sha256": hashes["symbols"]},
            "faithful_trace": {
                "path": str(trace_path.relative_to(ROOT)),
                "sha256": hashes["faithful_trace"],
            },
            "parent_decision_sha256": sha256_file(decision_path),
            "driver_sha256": sha256_file(Path(__file__)),
        },
        "arithmetic": {
            "payload_bytes": {
                arm: len(payload) for arm, payload in payloads.items()
            },
            "payload_sha256": {
                arm: common.sha256_bytes(payload)
                for arm, payload in payloads.items()
            },
            "node_repeat_sha256": common.sha256_bytes(
                replay["repeat_payload"]
            ),
            "gain_over_base_bytes": gains,
            "node_margin_bytes": margins,
            "chronological_third_gain_bytes": third_gains,
            "ideal_bits": replay["ideal_bits"],
        },
        "decode": decode,
        "conditions": conditions,
        "decision": {
            "promotion_authorized": False,
            "open_port_authorized": passed,
            "verified_full_1g_score_bytes": None,
            "forecast_bytes": 109_389_323,
        },
        "claim_boundary": (
            "The correction is causal and decoder-rebuilt given the faithful "
            "teacher trace, but this program does not rebuild NNCP. Closed "
            "LibNC remains ineligible and no score or forecast is inherited."
        ),
        "artifacts": {
            "incremental_source_package": {
                "path": str(source_path.relative_to(ROOT)),
                "bytes": len(source_package),
                "sha256": sha256_file(source_path),
                "limit_bytes": SOURCE_LIMIT_BYTES,
            }
        },
        "resource": {
            "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
    }
    (output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "gains": gains,
                "margins": margins,
                "third_gains": third_gains,
                "verdict": decision["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
