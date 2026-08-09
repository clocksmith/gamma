#!/usr/bin/env python3
"""Replay a cache weighted by earlier decoder-visible NNCP branch errors."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import lzma
import math
from pathlib import Path
import resource

import numpy as np

import nncp_midpoint_phase_attribution_qm0 as phase
import nncp_symbol_cache32_marginal_qm0 as cache_q0


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_branch_residual_cache32_qm0_v1"
BASELINE_ID = "nncp_midsegment32_update_262144_qm1_v1"
JOINT_ID = "nncp_midpoint_cache32_joint_qm1_v1"
SYMBOL_PATH = cache_q0.SYMBOL_PATH
SYMBOL_COUNT = cache_q0.SYMBOL_COUNT
STREAMS = cache_q0.STREAMS
STREAM_LENGTH = cache_q0.STREAM_LENGTH
SEGMENT = cache_q0.SEGMENT
VOCABULARY = cache_q0.VOCABULARY
EXPECTED_BRANCHES = cache_q0.EXPECTED_BRANCHES
GAIN_GATE_BYTES = 10_000
MARGIN_GATE_BYTES = 1_000
SOURCE_LIMIT_BYTES = 65_536

EXPECTED_SHA256 = {
    "symbols": "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5",
    "faithful_trace": "8c37f952fab1242743366b99083243263cb7eb5309cd10f45a36e99188a0a706",
}
EXPECTED_BASE = (
    341_558,
    "99c7d04d174f7ba1a30ae5b4af5c5b5d248cf33225713c1de2ed28862b5ec8c6",
)


@dataclass(frozen=True)
class CacheRecord:
    symbol: int
    residual: int


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def arm_records(
    history: list[CacheRecord],
    arm: str,
) -> list[tuple[int, int]]:
    if arm == "base" or not history:
        return []
    if arm == "uniform":
        return [(record.symbol, 1) for record in history]
    if arm == "weighted":
        return [(record.symbol, record.residual) for record in history]
    if arm == "rotated":
        rotated = history[1:] + history[:1]
        return [
            (record.symbol, donor.residual)
            for record, donor in zip(history, rotated, strict=True)
        ]
    raise ValueError(f"unknown arm: {arm}")


def mixed_probability_zero(
    base_zero: int,
    records: list[tuple[int, int]],
    boundary: int,
    base_weight: float,
    cache_weight: float,
) -> tuple[int, float, float]:
    base_p0 = base_zero / cache_q0.PROBABILITY_TOTAL
    total_weight = sum(weight for _, weight in records)
    if records and total_weight > 0 and cache_weight > 0.0:
        zero_weight = sum(
            weight for symbol, weight in records if symbol < boundary
        )
        cache_p0 = zero_weight / total_weight
    else:
        cache_p0 = 0.0
        cache_weight = 0.0
    denominator = base_weight + cache_weight
    if denominator <= 0.0:
        raise ValueError("branch mixture lost all mass")
    mixture = (
        base_weight * base_p0 + cache_weight * cache_p0
    ) / denominator
    frequency = min(
        max(int(round(mixture * cache_q0.PROBABILITY_TOTAL)), 1),
        cache_q0.PROBABILITY_TOTAL - 1,
    )
    return frequency, base_p0, cache_p0


def encode_all(
    symbols: np.ndarray,
    faithful_trace: np.ndarray,
) -> dict[str, object]:
    matrix = symbols.reshape(STREAMS, STREAM_LENGTH)
    arms = ("base", "uniform", "weighted", "rotated")
    encoders = {arm: cache_q0.RangeEncoder() for arm in arms}
    repeat = cache_q0.RangeEncoder()
    thirds = {
        arm: [cache_q0.RangeEncoder() for _ in range(3)] for arm in arms
    }
    ideal_bits = {arm: 0.0 for arm in arms}
    histories: list[list[CacheRecord]] = [[] for _ in range(STREAMS)]
    branch = 0

    for segment_start in range(0, STREAM_LENGTH, SEGMENT):
        for state in range(SEGMENT):
            absolute = segment_start + state
            for stream in range(STREAMS):
                original = stream * STREAM_LENGTH + absolute
                third = cache_q0.third_for_original(original)
                symbol = int(matrix[stream, absolute])
                records = {
                    arm: arm_records(histories[stream], arm) for arm in arms
                }
                weights = {
                    arm: [
                        cache_q0.BASE_PRIOR,
                        cache_q0.CACHE_PRIOR if records[arm] else 0.0,
                    ]
                    for arm in arms
                }
                start = 0
                active = VOCABULARY
                residual = 0

                for bit in phase.expected_bits(symbol):
                    base_zero = int(faithful_trace[branch])
                    if not 1 <= base_zero < cache_q0.PROBABILITY_TOTAL:
                        raise ValueError("illegal faithful branch frequency")
                    realized_base = (
                        base_zero
                        if bit == 0
                        else cache_q0.PROBABILITY_TOTAL - base_zero
                    )
                    residual += cache_q0.PROBABILITY_TOTAL - realized_base
                    left = active >> 1
                    boundary = start + left
                    probabilities: dict[str, int] = {}

                    for arm in arms:
                        probability, base_p0, cache_p0 = mixed_probability_zero(
                            base_zero,
                            records[arm],
                            boundary,
                            weights[arm][0],
                            weights[arm][1],
                        )
                        probabilities[arm] = probability
                        encoders[arm].put_bit(probability, bit)
                        thirds[arm][third].put_bit(probability, bit)
                        realized = (
                            probability
                            if bit == 0
                            else cache_q0.PROBABILITY_TOTAL - probability
                        )
                        ideal_bits[arm] -= math.log2(
                            realized / cache_q0.PROBABILITY_TOTAL
                        )
                        weights[arm][0], weights[arm][1] = (
                            cache_q0.update_symbol_mixture(
                                bit,
                                base_p0,
                                cache_p0,
                                weights[arm][0],
                                weights[arm][1],
                            )
                        )
                        records[arm] = [
                            row
                            for row in records[arm]
                            if (row[0] < boundary) == (bit == 0)
                        ]
                    repeat.put_bit(probabilities["weighted"], bit)

                    if bit:
                        start = boundary
                        active -= left
                    else:
                        active = left
                    branch += 1

                if start != symbol or active != 1:
                    raise ValueError("symbol path did not terminate at truth")
                histories[stream].append(CacheRecord(symbol, residual))
                if len(histories[stream]) > cache_q0.CACHE_WINDOW:
                    del histories[stream][0]

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


def decode_weighted(
    payload: bytes,
    faithful_trace: np.ndarray,
    expected_symbols: np.ndarray,
) -> dict[str, object]:
    expected = expected_symbols.reshape(STREAMS, STREAM_LENGTH)
    decoded = np.zeros_like(expected)
    histories: list[list[CacheRecord]] = [[] for _ in range(STREAMS)]
    decoder = cache_q0.RangeDecoder(payload)
    branch = 0

    for segment_start in range(0, STREAM_LENGTH, SEGMENT):
        for state in range(SEGMENT):
            absolute = segment_start + state
            for stream in range(STREAMS):
                records = arm_records(histories[stream], "weighted")
                base_weight = cache_q0.BASE_PRIOR
                cache_weight = cache_q0.CACHE_PRIOR if records else 0.0
                start = 0
                active = VOCABULARY
                residual = 0
                while active > 1:
                    base_zero = int(faithful_trace[branch])
                    left = active >> 1
                    boundary = start + left
                    probability, base_p0, cache_p0 = mixed_probability_zero(
                        base_zero,
                        records,
                        boundary,
                        base_weight,
                        cache_weight,
                    )
                    bit = decoder.get_bit(probability)
                    realized_base = (
                        base_zero
                        if bit == 0
                        else cache_q0.PROBABILITY_TOTAL - base_zero
                    )
                    residual += cache_q0.PROBABILITY_TOTAL - realized_base
                    base_weight, cache_weight = cache_q0.update_symbol_mixture(
                        bit,
                        base_p0,
                        cache_p0,
                        base_weight,
                        cache_weight,
                    )
                    records = [
                        row
                        for row in records
                        if (row[0] < boundary) == (bit == 0)
                    ]
                    if bit:
                        start = boundary
                        active -= left
                    else:
                        active = left
                    branch += 1
                decoded[stream, absolute] = start
                if start != int(expected[stream, absolute]):
                    raise ValueError("weighted arithmetic decode differs from truth")
                histories[stream].append(CacheRecord(start, residual))
                if len(histories[stream]) > cache_q0.CACHE_WINDOW:
                    del histories[stream][0]

    if branch != EXPECTED_BRANCHES:
        raise ValueError("weighted decoder consumed the wrong branch population")
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
        raise SystemExit(
            f"refusing to replace existing output directory: {output_dir}"
        )

    baseline_dir = ROOT / "results" / BASELINE_ID
    faithful_path = baseline_dir / "faithful_baseline_trace.bin"
    joint_decision_path = ROOT / "results" / JOINT_ID / "decision.json"
    joint = json.loads(joint_decision_path.read_text())
    if joint.get("verdict") != "authorize_same_object_mature_joint_replay":
        raise ValueError("joint midpoint/cache antecedent is not passed")
    actual_sha256 = {
        "symbols": sha256_file(SYMBOL_PATH),
        "faithful_trace": sha256_file(faithful_path),
    }
    if actual_sha256 != EXPECTED_SHA256:
        raise ValueError("receipt-bound symbols or faithful trace mismatch")

    symbols = np.asarray(
        np.memmap(SYMBOL_PATH, mode="r", dtype=">u2")[:SYMBOL_COUNT],
        dtype=np.uint16,
    )
    faithful_trace = np.memmap(faithful_path, mode="r", dtype="<u2")
    replay = encode_all(symbols, faithful_trace)
    payloads = replay["payloads"]
    repeat_payload = replay["repeat_payload"]
    third_payloads = replay["third_payloads"]
    decode = decode_weighted(payloads["weighted"], faithful_trace, symbols)

    output_dir.mkdir(parents=True)
    for arm, payload in payloads.items():
        (output_dir / f"{arm}.bin").write_bytes(payload)

    base_reproduced = (
        len(payloads["base"]) == EXPECTED_BASE[0]
        and sha256_bytes(payloads["base"]) == EXPECTED_BASE[1]
    )
    gains = {
        arm: len(payloads["base"]) - len(payloads[arm])
        for arm in ("uniform", "weighted", "rotated")
    }
    margins = {
        "over_uniform": len(payloads["uniform"]) - len(payloads["weighted"]),
        "over_rotated": len(payloads["rotated"]) - len(payloads["weighted"]),
    }
    third_incremental_gains = [
        len(third_payloads["uniform"][index])
        - len(third_payloads["weighted"][index])
        for index in range(3)
    ]

    source_paths = (
        Path(__file__),
        ROOT / "tools/nncp_symbol_cache32_marginal_qm0.py",
        ROOT / "tools/nncp_midpoint_phase_attribution_qm0.py",
        ROOT / "docs/nncp_branch_residual_cache32_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/program.py",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
        ROOT / f"operations/adaptive/proposals/developed/000_{CANDIDATE_ID}.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(
        source_blob, preset=9 | lzma.PRESET_EXTREME
    )
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)

    conditions = {
        "base_payload_reproduced": base_reproduced,
        "weighted_gain_at_least_10000": gains["weighted"] >= GAIN_GATE_BYTES,
        "margin_over_uniform_at_least_1000": (
            margins["over_uniform"] >= MARGIN_GATE_BYTES
        ),
        "margin_over_rotated_at_least_1000": (
            margins["over_rotated"] >= MARGIN_GATE_BYTES
        ),
        "all_incremental_thirds_positive": all(
            value > 0 for value in third_incremental_gains
        ),
        "repeat_payload_identical": repeat_payload == payloads["weighted"],
        "arithmetic_decode_exact": bool(decode["symbols_exact"]),
        "branch_population_exact": replay["branches"] == EXPECTED_BRANCHES,
        "source_at_most_65536": len(source_package) <= SOURCE_LIMIT_BYTES,
    }
    passed = all(conditions.values())
    decision = {
        "schema": "enwiki9_nncp_branch_residual_cache32_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "CAUSAL_SHADOW_COMPLETE",
        "verdict": (
            "authorize_mature_branch_residual_cache"
            if passed
            else "retire_branch_residual_cache32"
        ),
        "epistemic_tier": "teacher_trace_exact_arithmetic_shadow_zero_score_credit",
        "score_credit_bytes": 0,
        "model": {
            "cache_window": cache_q0.CACHE_WINDOW,
            "base_prior_mass": cache_q0.BASE_PRIOR,
            "cache_prior_mass": cache_q0.CACHE_PRIOR,
            "residual": "sum(32768-realized_faithful_branch_mass)",
            "rotated_control": "next cache occurrence weight cyclically",
            "transmitted_state": False,
        },
        "population": {
            "symbols": SYMBOL_COUNT,
            "streams": STREAMS,
            "symbols_per_stream": STREAM_LENGTH,
            "branches": EXPECTED_BRANCHES,
            "vocabulary": VOCABULARY,
        },
        "inputs": {
            "symbols": {
                "path": str(SYMBOL_PATH),
                "sha256": actual_sha256["symbols"],
            },
            "faithful_trace": {
                "path": str(faithful_path.relative_to(ROOT)),
                "sha256": actual_sha256["faithful_trace"],
            },
            "joint_antecedent_sha256": sha256_file(joint_decision_path),
            "driver_sha256": sha256_file(Path(__file__)),
        },
        "arithmetic": {
            "payload_bytes": {
                arm: len(payload) for arm, payload in payloads.items()
            },
            "payload_sha256": {
                arm: sha256_bytes(payload) for arm, payload in payloads.items()
            },
            "weighted_repeat_sha256": sha256_bytes(repeat_payload),
            "gain_over_base_bytes": gains,
            "weighted_margin_bytes": margins,
            "weighted_minus_uniform_chronological_third_bytes": (
                third_incremental_gains
            ),
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
            "The residual weights are causal and decoder-visible given the "
            "teacher trace, but this program does not rebuild the faithful "
            "model and closed LibNC receives no score eligibility."
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
    decision_path = output_dir / "decision.json"
    decision_path.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "weighted_gain_bytes": gains["weighted"],
                "margin_over_uniform_bytes": margins["over_uniform"],
                "margin_over_rotated_bytes": margins["over_rotated"],
                "third_incremental_bytes": third_incremental_gains,
                "verdict": decision["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
