#!/usr/bin/env python3
"""Replay an addressless local-successor cache over exact NNCP branches."""

from __future__ import annotations

import hashlib
import json
import lzma
import math
from pathlib import Path
import resource

import numpy as np

import nncp_midpoint_phase_attribution_qm0 as phase
import nncp_symbol_cache32_marginal_qm0 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_successor_cache32_qm0_v1"
PARENT_ID = "nncp_symbol_cache32_marginal_qm0_v1"
LAG_CONTROL = 17
GAIN_GATE_BYTES = 10_000
CONTROL_MARGIN_BYTES = 1_000
SOURCE_LIMIT_BYTES = 65_536
EXPECTED_PARENT = {
    "base": (341_558, "99c7d04d174f7ba1a30ae5b4af5c5b5d248cf33225713c1de2ed28862b5ec8c6"),
    "cache": (332_485, "2f1c3c9a340c31eca85714af3c523a04abb02795a77520e8a7242387439ac4dc"),
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def candidates(
    matrix: np.ndarray,
    stream: int,
    absolute: int,
    arm: str,
) -> list[int]:
    start = max(0, absolute - parent.CACHE_WINDOW)
    if arm == "base":
        return []
    if arm == "cache":
        return [int(value) for value in matrix[stream, start:absolute]]
    if arm == "successor":
        if absolute == 0:
            return []
        key = int(matrix[stream, absolute - 1])
    elif arm == "lag17":
        if absolute < LAG_CONTROL:
            return []
        key = int(matrix[stream, absolute - LAG_CONTROL])
    else:
        raise ValueError(f"unknown arm: {arm}")
    return [
        int(matrix[stream, source])
        for source in range(max(1, start), absolute)
        if int(matrix[stream, source - 1]) == key
    ]


def encode_all(
    symbols: np.ndarray,
    baseline_trace: np.ndarray,
) -> dict[str, object]:
    matrix = symbols.reshape(parent.STREAMS, parent.STREAM_LENGTH)
    arms = ("base", "cache", "successor", "lag17")
    encoders = {arm: parent.RangeEncoder() for arm in arms}
    repeat = parent.RangeEncoder()
    thirds = {
        arm: [parent.RangeEncoder() for _ in range(3)] for arm in arms
    }
    ideal_bits = {arm: 0.0 for arm in arms}
    activation = {arm: 0 for arm in arms}
    candidate_rows = {arm: 0 for arm in arms}
    branch = 0

    for segment_start in range(0, parent.STREAM_LENGTH, parent.SEGMENT):
        for state in range(parent.SEGMENT):
            absolute = segment_start + state
            for stream in range(parent.STREAMS):
                original = stream * parent.STREAM_LENGTH + absolute
                third = parent.third_for_original(original)
                symbol = int(matrix[stream, absolute])
                arm_state: dict[str, dict[str, object]] = {}
                for arm in arms:
                    rows = candidates(matrix, stream, absolute, arm)
                    activation[arm] += int(bool(rows))
                    candidate_rows[arm] += len(rows)
                    arm_state[arm] = {
                        "rows": rows,
                        "base_weight": parent.BASE_PRIOR,
                        "expert_weight": parent.CACHE_PRIOR if rows else 0.0,
                    }
                start = 0
                active = parent.VOCABULARY
                for bit in phase.expected_bits(symbol):
                    base_zero = int(baseline_trace[branch])
                    if not 1 <= base_zero < parent.PROBABILITY_TOTAL:
                        raise ValueError("illegal faithful branch frequency")
                    left = active >> 1
                    boundary = start + left
                    probabilities: dict[str, int] = {}
                    for arm in arms:
                        state_row = arm_state[arm]
                        rows = state_row["rows"]
                        probability, base_p0, expert_p0 = parent.mixed_probability_zero(
                            base_zero,
                            rows,
                            start,
                            left,
                            float(state_row["base_weight"]),
                            float(state_row["expert_weight"]),
                        )
                        probabilities[arm] = probability
                        encoders[arm].put_bit(probability, bit)
                        thirds[arm][third].put_bit(probability, bit)
                        realized = (
                            probability
                            if bit == 0
                            else parent.PROBABILITY_TOTAL - probability
                        )
                        ideal_bits[arm] -= math.log2(
                            realized / parent.PROBABILITY_TOTAL
                        )
                        base_weight, expert_weight = parent.update_symbol_mixture(
                            bit,
                            base_p0,
                            expert_p0,
                            float(state_row["base_weight"]),
                            float(state_row["expert_weight"]),
                        )
                        state_row["base_weight"] = base_weight
                        state_row["expert_weight"] = expert_weight
                        state_row["rows"] = [
                            value
                            for value in rows
                            if (value < boundary) == (bit == 0)
                        ]
                    repeat.put_bit(probabilities["successor"], bit)
                    if bit:
                        start = boundary
                        active -= left
                    else:
                        active = left
                    branch += 1
                if start != symbol or active != 1:
                    raise ValueError("symbol path did not terminate at truth")

    if branch != parent.EXPECTED_BRANCHES:
        raise ValueError("faithful branch trace was not consumed exactly")
    return {
        "payloads": {arm: coder.finish() for arm, coder in encoders.items()},
        "repeat_payload": repeat.finish(),
        "third_payloads": {
            arm: [coder.finish() for coder in coders]
            for arm, coders in thirds.items()
        },
        "ideal_bits": ideal_bits,
        "activation_symbols": activation,
        "candidate_rows": candidate_rows,
        "branches": branch,
    }


def decode_successor(
    payload: bytes,
    baseline_trace: np.ndarray,
    expected_symbols: np.ndarray,
) -> dict[str, object]:
    expected = expected_symbols.reshape(parent.STREAMS, parent.STREAM_LENGTH)
    decoded = np.zeros_like(expected)
    decoder = parent.RangeDecoder(payload)
    branch = 0
    for segment_start in range(0, parent.STREAM_LENGTH, parent.SEGMENT):
        for state in range(parent.SEGMENT):
            absolute = segment_start + state
            for stream in range(parent.STREAMS):
                rows = candidates(decoded, stream, absolute, "successor")
                base_weight = parent.BASE_PRIOR
                expert_weight = parent.CACHE_PRIOR if rows else 0.0
                start = 0
                active = parent.VOCABULARY
                while active > 1:
                    base_zero = int(baseline_trace[branch])
                    left = active >> 1
                    boundary = start + left
                    probability, base_p0, expert_p0 = parent.mixed_probability_zero(
                        base_zero,
                        rows,
                        start,
                        left,
                        base_weight,
                        expert_weight,
                    )
                    bit = decoder.get_bit(probability)
                    base_weight, expert_weight = parent.update_symbol_mixture(
                        bit,
                        base_p0,
                        expert_p0,
                        base_weight,
                        expert_weight,
                    )
                    rows = [
                        value
                        for value in rows
                        if (value < boundary) == (bit == 0)
                    ]
                    if bit:
                        start = boundary
                        active -= left
                    else:
                        active = left
                    branch += 1
                decoded[stream, absolute] = start
                if start != int(expected[stream, absolute]):
                    raise ValueError("successor arithmetic decode differs from truth")
    if branch != parent.EXPECTED_BRANCHES:
        raise ValueError("decoder consumed the wrong branch population")
    return {
        "symbols_exact": bool(np.array_equal(decoded, expected)),
        "decoded_sha256": sha256_bytes(
            decoded.astype(">u2", copy=False).tobytes()
        ),
        "branches": branch,
    }


def main() -> int:
    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")
    midpoint_dir = ROOT / "results" / parent.MIDPOINT_ID
    trace_path = midpoint_dir / "faithful_baseline_trace.bin"
    parent_decision_path = ROOT / "results" / PARENT_ID / "decision.json"
    parent_decision = json.loads(parent_decision_path.read_text())
    if parent_decision.get("verdict") != "authorize_open_same_object_cache_port":
        raise ValueError("unconditional-cache antecedent is not passed")
    actual_sha256 = {
        "symbols": sha256_file(parent.SYMBOL_PATH),
        "baseline_trace": sha256_file(trace_path),
    }
    if actual_sha256 != parent.EXPECTED_SHA256:
        raise ValueError("receipt-bound input identity mismatch")

    symbols = np.asarray(
        np.memmap(parent.SYMBOL_PATH, mode="r", dtype=">u2")[: parent.SYMBOL_COUNT],
        dtype=np.uint16,
    )
    baseline_trace = np.memmap(trace_path, mode="r", dtype="<u2")
    replay = encode_all(symbols, baseline_trace)
    payloads = replay["payloads"]
    repeat_payload = replay["repeat_payload"]
    thirds = replay["third_payloads"]
    decode = decode_successor(payloads["successor"], baseline_trace, symbols)

    parent_identity = {
        arm: (len(payloads[arm]), sha256_bytes(payloads[arm]))
        == EXPECTED_PARENT[arm]
        for arm in EXPECTED_PARENT
    }
    base_bytes = len(payloads["base"])
    gain = base_bytes - len(payloads["successor"])
    cache_gain = base_bytes - len(payloads["cache"])
    lag_gain = base_bytes - len(payloads["lag17"])
    cache_margin = gain - cache_gain
    lag_margin = gain - lag_gain
    third_gains = [
        len(thirds["base"][index]) - len(thirds["successor"][index])
        for index in range(3)
    ]

    output_dir.mkdir(parents=True)
    for arm, payload in payloads.items():
        (output_dir / f"{arm}.bin").write_bytes(payload)
    source_paths = (
        Path(__file__),
        ROOT / "tools/nncp_symbol_cache32_marginal_qm0.py",
        ROOT / "docs/nncp_successor_cache32_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/program.py",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
        ROOT / f"operations/adaptive/proposals/developed/000_{CANDIDATE_ID}.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)

    conditions = {
        "parent_base_identity": parent_identity["base"],
        "parent_cache_identity": parent_identity["cache"],
        "gain_at_least_10000": gain >= GAIN_GATE_BYTES,
        "margin_over_cache_at_least_1000": cache_margin >= CONTROL_MARGIN_BYTES,
        "margin_over_lag17_at_least_1000": lag_margin >= CONTROL_MARGIN_BYTES,
        "all_chronological_thirds_positive": all(value > 0 for value in third_gains),
        "repeat_payload_identical": repeat_payload == payloads["successor"],
        "arithmetic_decode_exact": bool(decode["symbols_exact"]),
        "branch_population_exact": replay["branches"] == parent.EXPECTED_BRANCHES,
        "source_at_most_65536": len(source_package) <= SOURCE_LIMIT_BYTES,
    }
    passed = all(conditions.values())
    decision = {
        "schema": "enwiki9_nncp_successor_cache32_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "CAUSAL_SHADOW_COMPLETE",
        "verdict": (
            "authorize_mature_successor_cache_replay"
            if passed
            else "retire_frozen_successor_cache32"
        ),
        "epistemic_tier": "same_symbol_domain_exact_arithmetic_shadow_zero_score_credit",
        "score_credit_bytes": 0,
        "model": {
            "window": parent.CACHE_WINDOW,
            "base_prior_mass": parent.BASE_PRIOR,
            "successor_prior_mass": parent.CACHE_PRIOR,
            "lag_control": LAG_CONTROL,
            "selector_distance_or_length_transmitted": False,
        },
        "population": {
            "symbols": parent.SYMBOL_COUNT,
            "streams": parent.STREAMS,
            "symbols_per_stream": parent.STREAM_LENGTH,
            "branches": parent.EXPECTED_BRANCHES,
            "vocabulary": parent.VOCABULARY,
            "activation_symbols": replay["activation_symbols"],
            "candidate_rows": replay["candidate_rows"],
        },
        "inputs": {
            "symbols": {"path": str(parent.SYMBOL_PATH), "sha256": actual_sha256["symbols"]},
            "baseline_trace": {"path": str(trace_path.relative_to(ROOT)), "sha256": actual_sha256["baseline_trace"]},
            "parent_decision_sha256": sha256_file(parent_decision_path),
            "driver_sha256": sha256_file(Path(__file__)),
        },
        "arithmetic": {
            "base_bytes": base_bytes,
            "base_sha256": sha256_bytes(payloads["base"]),
            "unconditional_cache_bytes": len(payloads["cache"]),
            "unconditional_cache_gain_bytes": cache_gain,
            "successor_bytes": len(payloads["successor"]),
            "successor_sha256": sha256_bytes(payloads["successor"]),
            "successor_repeat_sha256": sha256_bytes(repeat_payload),
            "successor_gain_bytes": gain,
            "lag17_bytes": len(payloads["lag17"]),
            "lag17_gain_bytes": lag_gain,
            "margin_over_unconditional_cache_bytes": cache_margin,
            "margin_over_lag17_bytes": lag_margin,
            "chronological_third_gain_bytes": third_gains,
            "ideal_bits": replay["ideal_bits"],
        },
        "decode": decode,
        "conditions": conditions,
        "decision": {
            "promotion_authorized": False,
            "mature_shadow_authorized": passed,
            "verified_full_1g_score_bytes": None,
            "forecast_bytes": 109_389_323,
        },
        "claim_boundary": (
            "Exact arithmetic over a receipt-bound teacher trace only. The "
            "trace is not decoder-rebuilt here, LibNC remains ineligible, and "
            "no score or forecast is inherited."
        ),
        "artifacts": {
            "incremental_source_package": {
                "path": str(source_path.relative_to(ROOT)),
                "bytes": len(source_package),
                "sha256": sha256_file(source_path),
                "limit_bytes": SOURCE_LIMIT_BYTES,
            }
        },
        "resource": {"max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
    }
    (output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "successor_gain_bytes": gain,
        "margin_over_unconditional_cache_bytes": cache_margin,
        "margin_over_lag17_bytes": lag_margin,
        "third_gains": third_gains,
        "verdict": decision["verdict"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
