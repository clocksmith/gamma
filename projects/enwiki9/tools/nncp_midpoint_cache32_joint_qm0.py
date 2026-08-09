#!/usr/bin/env python3
"""Jointly replay full-midpoint NNCP probabilities and cache-32 marginal."""

from __future__ import annotations

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
CANDIDATE_ID = "nncp_midpoint_cache32_joint_qm0_v1"
MIDPOINT_ID = "nncp_midsegment32_update_262144_qm1_v1"
SYMBOL_PATH = cache_q0.SYMBOL_PATH
SYMBOL_COUNT = cache_q0.SYMBOL_COUNT
STREAMS = cache_q0.STREAMS
STREAM_LENGTH = cache_q0.STREAM_LENGTH
SEGMENT = cache_q0.SEGMENT
VOCABULARY = cache_q0.VOCABULARY
EXPECTED_BRANCHES = cache_q0.EXPECTED_BRANCHES
GAIN_GATE_BYTES = 4_000
CONTROL_MARGIN_BYTES = 1_000
SOURCE_LIMIT_BYTES = 65_536

EXPECTED_SHA256 = {
    "symbols": "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5",
    "faithful_trace": "8c37f952fab1242743366b99083243263cb7eb5309cd10f45a36e99188a0a706",
    "midpoint_trace": "25d7b9e5566d8c0391509f92d63b488514fd42f33c4701092d01f0d2d347fa7d",
}
EXPECTED_PAYLOADS = {
    "faithful": (341_558, "99c7d04da7bc4912a1e1a8dd750b7b100864c4a6db1c301f639be6b467ec8c6"),
    "midpoint": (324_373, "52072f2607d9094575948ef1c77c5796afd5e1eeb5e24a119ce20db5c0f2db6e"),
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def encode_all(
    symbols: np.ndarray,
    faithful_trace: np.ndarray,
    midpoint_trace: np.ndarray,
) -> dict[str, object]:
    matrix = symbols.reshape(STREAMS, STREAM_LENGTH)
    arms = ("faithful", "midpoint", "joint", "cross")
    encoders = {arm: cache_q0.RangeEncoder() for arm in arms}
    repeat = cache_q0.RangeEncoder()
    thirds = {
        arm: [cache_q0.RangeEncoder() for _ in range(3)] for arm in arms
    }
    ideal_bits = {arm: 0.0 for arm in arms}
    branch = 0

    for segment_start in range(0, STREAM_LENGTH, SEGMENT):
        for state in range(SEGMENT):
            absolute = segment_start + state
            for stream in range(STREAMS):
                original = stream * STREAM_LENGTH + absolute
                third = cache_q0.third_for_original(original)
                symbol = int(matrix[stream, absolute])
                windows = {
                    "joint": cache_q0.source_window(
                        matrix, stream, absolute, "cache"
                    ),
                    "cross": cache_q0.source_window(
                        matrix, stream, absolute, "cross"
                    ),
                }
                weights = {
                    arm: [
                        cache_q0.BASE_PRIOR,
                        cache_q0.CACHE_PRIOR if windows[arm] else 0.0,
                    ]
                    for arm in ("joint", "cross")
                }
                start = 0
                active = VOCABULARY

                for bit in phase.expected_bits(symbol):
                    faithful_zero = int(faithful_trace[branch])
                    midpoint_zero = int(midpoint_trace[branch])
                    if not (
                        1 <= faithful_zero < cache_q0.PROBABILITY_TOTAL
                        and 1 <= midpoint_zero < cache_q0.PROBABILITY_TOTAL
                    ):
                        raise ValueError("illegal teacher branch frequency")

                    left = active >> 1
                    boundary = start + left
                    probabilities = {
                        "faithful": faithful_zero,
                        "midpoint": midpoint_zero,
                    }
                    mixture_rows: dict[str, tuple[float, float]] = {}
                    for arm in ("joint", "cross"):
                        probability, base_p0, cache_p0 = (
                            cache_q0.mixed_probability_zero(
                                midpoint_zero,
                                windows[arm],
                                start,
                                left,
                                weights[arm][0],
                                weights[arm][1],
                            )
                        )
                        probabilities[arm] = probability
                        mixture_rows[arm] = (base_p0, cache_p0)

                    for arm in arms:
                        probability = probabilities[arm]
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
                    repeat.put_bit(probabilities["joint"], bit)

                    for arm in ("joint", "cross"):
                        base_p0, cache_p0 = mixture_rows[arm]
                        weights[arm][0], weights[arm][1] = (
                            cache_q0.update_symbol_mixture(
                                bit,
                                base_p0,
                                cache_p0,
                                weights[arm][0],
                                weights[arm][1],
                            )
                        )
                        windows[arm] = [
                            cached
                            for cached in windows[arm]
                            if (cached < boundary) == (bit == 0)
                        ]

                    if bit:
                        start = boundary
                        active -= left
                    else:
                        active = left
                    branch += 1

                if start != symbol or active != 1:
                    raise ValueError("symbol path did not terminate at truth")

    if branch != EXPECTED_BRANCHES:
        raise ValueError("teacher traces were not consumed exactly")
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


def decode_joint(
    payload: bytes,
    midpoint_trace: np.ndarray,
    expected_symbols: np.ndarray,
) -> dict[str, object]:
    expected = expected_symbols.reshape(STREAMS, STREAM_LENGTH)
    decoded = np.zeros_like(expected)
    decoder = cache_q0.RangeDecoder(payload)
    branch = 0

    for segment_start in range(0, STREAM_LENGTH, SEGMENT):
        for state in range(SEGMENT):
            absolute = segment_start + state
            for stream in range(STREAMS):
                window = cache_q0.source_window(
                    decoded, stream, absolute, "cache"
                )
                base_weight = cache_q0.BASE_PRIOR
                cache_weight = cache_q0.CACHE_PRIOR if window else 0.0
                start = 0
                active = VOCABULARY
                while active > 1:
                    midpoint_zero = int(midpoint_trace[branch])
                    left = active >> 1
                    boundary = start + left
                    probability, base_p0, cache_p0 = (
                        cache_q0.mixed_probability_zero(
                            midpoint_zero,
                            window,
                            start,
                            left,
                            base_weight,
                            cache_weight,
                        )
                    )
                    bit = decoder.get_bit(probability)
                    base_weight, cache_weight = cache_q0.update_symbol_mixture(
                        bit,
                        base_p0,
                        cache_p0,
                        base_weight,
                        cache_weight,
                    )
                    window = [
                        cached
                        for cached in window
                        if (cached < boundary) == (bit == 0)
                    ]
                    if bit:
                        start = boundary
                        active -= left
                    else:
                        active = left
                    branch += 1
                decoded[stream, absolute] = start
                if start != int(expected[stream, absolute]):
                    raise ValueError("joint arithmetic decode differs from truth")

    if branch != EXPECTED_BRANCHES:
        raise ValueError("joint decoder consumed the wrong branch population")
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

    midpoint_dir = ROOT / "results" / MIDPOINT_ID
    faithful_path = midpoint_dir / "faithful_baseline_trace.bin"
    midpoint_path = midpoint_dir / "branch_trace.bin"
    actual_sha256 = {
        "symbols": sha256_file(SYMBOL_PATH),
        "faithful_trace": sha256_file(faithful_path),
        "midpoint_trace": sha256_file(midpoint_path),
    }
    if actual_sha256 != EXPECTED_SHA256:
        raise ValueError("receipt-bound symbols or teacher trace identity mismatch")

    symbols = np.asarray(
        np.memmap(SYMBOL_PATH, mode="r", dtype=">u2")[:SYMBOL_COUNT],
        dtype=np.uint16,
    )
    faithful_trace = np.memmap(faithful_path, mode="r", dtype="<u2")
    midpoint_trace = np.memmap(midpoint_path, mode="r", dtype="<u2")
    if len(faithful_trace) != EXPECTED_BRANCHES or len(midpoint_trace) != EXPECTED_BRANCHES:
        raise ValueError("teacher trace branch population mismatch")

    replay = encode_all(symbols, faithful_trace, midpoint_trace)
    payloads = replay["payloads"]
    repeat_payload = replay["repeat_payload"]
    third_payloads = replay["third_payloads"]
    decode = decode_joint(payloads["joint"], midpoint_trace, symbols)

    output_dir.mkdir(parents=True)
    for arm, payload in payloads.items():
        (output_dir / f"{arm}.bin").write_bytes(payload)

    reproduced = {
        arm: (
            len(payloads[arm]) == expected_bytes
            and sha256_bytes(payloads[arm]) == expected_hash
        )
        for arm, (expected_bytes, expected_hash) in EXPECTED_PAYLOADS.items()
    }
    incremental_gain = len(payloads["midpoint"]) - len(payloads["joint"])
    cross_incremental_gain = (
        len(payloads["midpoint"]) - len(payloads["cross"])
    )
    control_margin = incremental_gain - cross_incremental_gain
    third_incremental_gains = [
        len(third_payloads["midpoint"][index])
        - len(third_payloads["joint"][index])
        for index in range(3)
    ]

    source_paths = (
        Path(__file__),
        ROOT / "tools/nncp_symbol_cache32_marginal_qm0.py",
        ROOT / "tools/nncp_midpoint_phase_attribution_qm0.py",
        ROOT / "docs/nncp_midpoint_cache32_joint_qm0_plan.md",
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
        "faithful_payload_reproduced": reproduced["faithful"],
        "midpoint_payload_reproduced": reproduced["midpoint"],
        "incremental_gain_at_least_4000": incremental_gain >= GAIN_GATE_BYTES,
        "all_incremental_thirds_positive": all(
            value > 0 for value in third_incremental_gains
        ),
        "control_margin_at_least_1000": control_margin >= CONTROL_MARGIN_BYTES,
        "repeat_payload_identical": repeat_payload == payloads["joint"],
        "arithmetic_decode_exact": bool(decode["symbols_exact"]),
        "branch_population_exact": replay["branches"] == EXPECTED_BRANCHES,
        "source_at_most_65536": len(source_package) <= SOURCE_LIMIT_BYTES,
    }
    passed = all(conditions.values())
    decision = {
        "schema": "enwiki9_nncp_midpoint_cache32_joint_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "CAUSAL_SHADOW_COMPLETE",
        "verdict": (
            "authorize_same_object_mature_joint_replay"
            if passed
            else "retire_frozen_midpoint_cache32_joint"
        ),
        "epistemic_tier": "joint_teacher_trace_exact_arithmetic_shadow_zero_score_credit",
        "score_credit_bytes": 0,
        "model": {
            "cache_window": cache_q0.CACHE_WINDOW,
            "midpoint_prior_mass": cache_q0.BASE_PRIOR,
            "cache_prior_mass": cache_q0.CACHE_PRIOR,
            "cross_stream_offset": cache_q0.CROSS_STREAM_OFFSET,
            "source_selector_transmitted": False,
            "distance_or_length_transmitted": False,
        },
        "population": {
            "symbols": SYMBOL_COUNT,
            "streams": STREAMS,
            "symbols_per_stream": STREAM_LENGTH,
            "branches": EXPECTED_BRANCHES,
            "vocabulary": VOCABULARY,
        },
        "inputs": {
            "symbols": {"path": str(SYMBOL_PATH), "sha256": actual_sha256["symbols"]},
            "faithful_trace": {
                "path": str(faithful_path.relative_to(ROOT)),
                "sha256": actual_sha256["faithful_trace"],
            },
            "midpoint_trace": {
                "path": str(midpoint_path.relative_to(ROOT)),
                "sha256": actual_sha256["midpoint_trace"],
            },
            "driver_sha256": sha256_file(Path(__file__)),
        },
        "arithmetic": {
            "faithful_bytes": len(payloads["faithful"]),
            "faithful_sha256": sha256_bytes(payloads["faithful"]),
            "midpoint_bytes": len(payloads["midpoint"]),
            "midpoint_sha256": sha256_bytes(payloads["midpoint"]),
            "joint_bytes": len(payloads["joint"]),
            "joint_sha256": sha256_bytes(payloads["joint"]),
            "joint_repeat_sha256": sha256_bytes(repeat_payload),
            "joint_total_gain_over_faithful_bytes": (
                len(payloads["faithful"]) - len(payloads["joint"])
            ),
            "joint_incremental_gain_over_midpoint_bytes": incremental_gain,
            "cross_bytes": len(payloads["cross"]),
            "cross_sha256": sha256_bytes(payloads["cross"]),
            "cross_incremental_gain_over_midpoint_bytes": cross_incremental_gain,
            "joint_margin_over_cross_bytes": control_margin,
            "incremental_chronological_third_gain_bytes": third_incremental_gains,
            "ideal_bits": replay["ideal_bits"],
        },
        "decode": decode,
        "conditions": conditions,
        "decision": {
            "promotion_authorized": False,
            "mature_joint_replay_authorized": passed,
            "verified_full_1g_score_bytes": None,
            "forecast_bytes": 109_389_323,
        },
        "claim_boundary": (
            "This exact joint replay prevents additive gain accounting, but "
            "both probability traces remain teacher artifacts and closed "
            "LibNC remains outside an eligible submission boundary."
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
                "incremental_gain_bytes": incremental_gain,
                "control_margin_bytes": control_margin,
                "third_incremental_gains": third_incremental_gains,
                "verdict": decision["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
