#!/usr/bin/env python3
"""Replay an addressless cache-32 marginal over exact NNCP symbol branches."""

from __future__ import annotations

import hashlib
import json
import lzma
import math
from pathlib import Path
import resource

import numpy as np

import nncp_midpoint_phase_attribution_qm0 as phase


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_symbol_cache32_marginal_qm0_v1"
MIDPOINT_ID = "nncp_midsegment32_update_262144_qm1_v1"
RECURRENCE_ID = "nncp_midpoint_decoder_visible_recurrence_qm0_v1"
SYMBOL_PATH = Path(
    "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
    "preprocessed.bin"
)
SYMBOL_COUNT = 262_144
STREAMS = 32
STREAM_LENGTH = SYMBOL_COUNT // STREAMS
SEGMENT = 64
VOCABULARY = 16_392
EXPECTED_BRANCHES = 3_670_169
CACHE_WINDOW = 32
BASE_PRIOR = 16.0
CACHE_PRIOR = 1.0
CROSS_STREAM_OFFSET = 17
GAIN_GATE_BYTES = 4_000
CONTROL_MARGIN_BYTES = 1_000
SOURCE_LIMIT_BYTES = 65_536
PROBABILITY_BITS = 15
PROBABILITY_TOTAL = 1 << PROBABILITY_BITS
RANGE_MIN_BITS = 16
RANGE_MIN = (0xFF << (RANGE_MIN_BITS - 8)) + 1
RANGE_MAX = 0xFF << RANGE_MIN_BITS

EXPECTED_SHA256 = {
    "symbols": "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5",
    "baseline_trace": "8c37f952fab1242743366b99083243263cb7eb5309cd10f45a36e99188a0a706",
}


class RangeEncoder:
    def __init__(self) -> None:
        self.low = 0
        self.range = RANGE_MAX
        self.current_byte = 0xFF
        self.pending_bytes = 0
        self.output = bytearray()

    def _put_value(self, value: int) -> None:
        if value == 0xFF:
            self.pending_bytes += 1
            return
        if self.pending_bytes:
            carry = value >> 8
            self.output.append((self.current_byte + carry) & 0xFF)
            fill = (0xFF + carry) & 0xFF
            while self.pending_bytes > 1:
                self.output.append(fill)
                self.pending_bytes -= 1
        self.pending_bytes = 1
        self.current_byte = value

    def put_bit(self, probability_zero: int, bit: int) -> None:
        split = (self.range * probability_zero) >> PROBABILITY_BITS
        if not 0 < split < self.range:
            raise ValueError("invalid range split")
        if bit:
            self.low += split
            self.range -= split
        else:
            self.range = split
        while self.range < RANGE_MIN:
            self._put_value(self.low >> RANGE_MIN_BITS)
            self.low = (self.low & ((1 << RANGE_MIN_BITS) - 1)) << 8
            self.range <<= 8

    def finish(self) -> bytes:
        if self.range < (1 << RANGE_MIN_BITS):
            self._put_value(self.low >> RANGE_MIN_BITS)
            self.low = (self.low & ((1 << RANGE_MIN_BITS) - 1)) << 8
            self.range <<= 8
        width = 0
        while (1 << (width + 1)) <= self.range:
            width += 1
        value = self.low
        mask = (1 << width) - 1
        if value & mask:
            value = (value + (1 << width)) & ~mask
        if not self.low <= value < self.low + self.range:
            raise ValueError("range finalization failed")
        self._put_value(value >> RANGE_MIN_BITS)
        if self.pending_bytes:
            self._put_value(0)
        return bytes(self.output)


class RangeDecoder:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.index = 0
        self.low = 0
        self.range = 0
        for _ in range(0, RANGE_MIN_BITS + 1, 8):
            self._refill()
        self.range = RANGE_MAX

    def _refill(self) -> None:
        self.range <<= 8
        self.low <<= 8
        if self.index < len(self.payload):
            self.low += self.payload[self.index]
            self.index += 1

    def get_bit(self, probability_zero: int) -> int:
        split = (self.range * probability_zero) >> PROBABILITY_BITS
        if not 0 < split < self.range:
            raise ValueError("invalid decode split")
        bit = int(self.low >= split)
        if bit:
            self.low -= split
            self.range -= split
        else:
            self.range = split
        while self.range < RANGE_MIN:
            self._refill()
        return bit


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def source_window(
    matrix: np.ndarray,
    stream: int,
    absolute: int,
    arm: str,
) -> list[int]:
    if arm == "base":
        return []
    source_stream = stream
    if arm == "cross":
        source_stream = (stream + CROSS_STREAM_OFFSET) % STREAMS
    start = max(0, absolute - CACHE_WINDOW)
    return [int(value) for value in matrix[source_stream, start:absolute]]


def mixed_probability_zero(
    base_zero: int,
    cache_symbols: list[int],
    start: int,
    left: int,
    base_weight: float,
    cache_weight: float,
) -> tuple[int, float, float]:
    base_p0 = base_zero / PROBABILITY_TOTAL
    if cache_symbols and cache_weight > 0.0:
        boundary = start + left
        cache_zero_count = sum(symbol < boundary for symbol in cache_symbols)
        cache_p0 = cache_zero_count / len(cache_symbols)
    else:
        cache_p0 = 0.0
        cache_weight = 0.0
    denominator = base_weight + cache_weight
    if denominator <= 0.0:
        raise ValueError("symbol mixture lost all mass")
    mixture_p0 = (
        base_weight * base_p0 + cache_weight * cache_p0
    ) / denominator
    frequency = min(
        max(int(round(mixture_p0 * PROBABILITY_TOTAL)), 1),
        PROBABILITY_TOTAL - 1,
    )
    return frequency, base_p0, cache_p0


def update_symbol_mixture(
    bit: int,
    base_p0: float,
    cache_p0: float,
    base_weight: float,
    cache_weight: float,
) -> tuple[float, float]:
    base_weight *= base_p0 if bit == 0 else 1.0 - base_p0
    cache_weight *= cache_p0 if bit == 0 else 1.0 - cache_p0
    total = base_weight + cache_weight
    if total <= 0.0:
        raise ValueError("realized branch has zero mixture mass")
    return base_weight / total, cache_weight / total


def third_for_original(original: int) -> int:
    return min(2, original * 3 // SYMBOL_COUNT)


def encode_all(
    symbols: np.ndarray,
    baseline_trace: np.ndarray,
) -> dict[str, object]:
    matrix = symbols.reshape(STREAMS, STREAM_LENGTH)
    arms = ("base", "cache", "cross")
    encoders = {arm: RangeEncoder() for arm in arms}
    repeat = RangeEncoder()
    thirds = {arm: [RangeEncoder() for _ in range(3)] for arm in arms}
    ideal_bits = {arm: 0.0 for arm in arms}
    branch = 0
    for segment_start in range(0, STREAM_LENGTH, SEGMENT):
        for state in range(SEGMENT):
            absolute = segment_start + state
            for stream in range(STREAMS):
                original = stream * STREAM_LENGTH + absolute
                third = third_for_original(original)
                symbol = int(matrix[stream, absolute])
                bits = phase.expected_bits(symbol)
                arm_state: dict[str, dict[str, object]] = {}
                for arm in arms:
                    window = source_window(matrix, stream, absolute, arm)
                    arm_state[arm] = {
                        "cache": window,
                        "base_weight": BASE_PRIOR,
                        "cache_weight": CACHE_PRIOR if window else 0.0,
                    }
                start = 0
                active = VOCABULARY
                for bit in bits:
                    base_zero = int(baseline_trace[branch])
                    if not 1 <= base_zero < PROBABILITY_TOTAL:
                        raise ValueError("illegal faithful branch frequency")
                    left = active >> 1
                    boundary = start + left
                    probabilities: dict[str, int] = {}
                    for arm in arms:
                        state_row = arm_state[arm]
                        cache = state_row["cache"]
                        probability, base_p0, cache_p0 = mixed_probability_zero(
                            base_zero,
                            cache,
                            start,
                            left,
                            float(state_row["base_weight"]),
                            float(state_row["cache_weight"]),
                        )
                        probabilities[arm] = probability
                        encoders[arm].put_bit(probability, bit)
                        thirds[arm][third].put_bit(probability, bit)
                        realized = probability if bit == 0 else PROBABILITY_TOTAL - probability
                        ideal_bits[arm] -= math.log2(realized / PROBABILITY_TOTAL)
                        base_weight, cache_weight = update_symbol_mixture(
                            bit,
                            base_p0,
                            cache_p0,
                            float(state_row["base_weight"]),
                            float(state_row["cache_weight"]),
                        )
                        state_row["base_weight"] = base_weight
                        state_row["cache_weight"] = cache_weight
                        state_row["cache"] = [
                            cached
                            for cached in cache
                            if (cached < boundary) == (bit == 0)
                        ]
                    repeat.put_bit(probabilities["cache"], bit)
                    if bit:
                        start = boundary
                        active -= left
                    else:
                        active = left
                    branch += 1
                if start != symbol or active != 1:
                    raise ValueError("symbol path did not terminate at truth")
    if branch != EXPECTED_BRANCHES:
        raise ValueError("faithful branch trace was not consumed exactly")
    payloads = {arm: encoder.finish() for arm, encoder in encoders.items()}
    repeat_payload = repeat.finish()
    third_payloads = {
        arm: [encoder.finish() for encoder in coders]
        for arm, coders in thirds.items()
    }
    return {
        "payloads": payloads,
        "repeat_payload": repeat_payload,
        "third_payloads": third_payloads,
        "ideal_bits": ideal_bits,
        "branches": branch,
    }


def decode_cache(
    payload: bytes,
    baseline_trace: np.ndarray,
    expected_symbols: np.ndarray,
) -> dict[str, object]:
    expected = expected_symbols.reshape(STREAMS, STREAM_LENGTH)
    decoded = np.zeros_like(expected)
    decoder = RangeDecoder(payload)
    branch = 0
    for segment_start in range(0, STREAM_LENGTH, SEGMENT):
        for state in range(SEGMENT):
            absolute = segment_start + state
            for stream in range(STREAMS):
                window = source_window(decoded, stream, absolute, "cache")
                base_weight = BASE_PRIOR
                cache_weight = CACHE_PRIOR if window else 0.0
                start = 0
                active = VOCABULARY
                while active > 1:
                    base_zero = int(baseline_trace[branch])
                    left = active >> 1
                    boundary = start + left
                    probability, base_p0, cache_p0 = mixed_probability_zero(
                        base_zero,
                        window,
                        start,
                        left,
                        base_weight,
                        cache_weight,
                    )
                    bit = decoder.get_bit(probability)
                    base_weight, cache_weight = update_symbol_mixture(
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
                    raise ValueError("cache arithmetic decode differs from truth")
    if branch != EXPECTED_BRANCHES:
        raise ValueError("cache decoder consumed the wrong branch population")
    return {
        "symbols_exact": bool(np.array_equal(decoded, expected)),
        "decoded_sha256": sha256_bytes(decoded.astype(">u2", copy=False).tobytes()),
        "branches": branch,
    }


def main() -> int:
    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")
    midpoint_dir = ROOT / "results" / MIDPOINT_ID
    baseline_trace_path = midpoint_dir / "faithful_baseline_trace.bin"
    recurrence_decision_path = ROOT / "results" / RECURRENCE_ID / "decision.json"
    actual_sha256 = {
        "symbols": sha256_file(SYMBOL_PATH),
        "baseline_trace": sha256_file(baseline_trace_path),
    }
    if actual_sha256 != EXPECTED_SHA256:
        raise ValueError("receipt-bound symbol or faithful trace identity mismatch")
    recurrence = json.loads(recurrence_decision_path.read_text())
    if recurrence.get("verdict") != "bounded_recurrence_coordinate_supported":
        raise ValueError("recurrence antecedent does not support this gate")

    symbols = np.asarray(
        np.memmap(SYMBOL_PATH, mode="r", dtype=">u2")[:SYMBOL_COUNT],
        dtype=np.uint16,
    )
    baseline_trace = np.memmap(baseline_trace_path, mode="r", dtype="<u2")
    replay = encode_all(symbols, baseline_trace)
    payloads = replay["payloads"]
    repeat_payload = replay["repeat_payload"]
    third_payloads = replay["third_payloads"]
    decode = decode_cache(payloads["cache"], baseline_trace, symbols)

    output_dir.mkdir(parents=True)
    for arm, payload in payloads.items():
        (output_dir / f"{arm}.bin").write_bytes(payload)
    candidate_gain = len(payloads["base"]) - len(payloads["cache"])
    control_gain = len(payloads["base"]) - len(payloads["cross"])
    control_margin = candidate_gain - control_gain
    third_gains = [
        len(third_payloads["base"][index])
        - len(third_payloads["cache"][index])
        for index in range(3)
    ]

    source_paths = (
        Path(__file__),
        ROOT / "docs/nncp_symbol_cache32_marginal_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/program.py",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
        ROOT
        / f"operations/adaptive/proposals/developed/000_{CANDIDATE_ID}.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)

    conditions = {
        "candidate_gain_at_least_4000": candidate_gain >= GAIN_GATE_BYTES,
        "all_chronological_thirds_positive": all(value > 0 for value in third_gains),
        "control_margin_at_least_1000": control_margin >= CONTROL_MARGIN_BYTES,
        "repeat_payload_identical": repeat_payload == payloads["cache"],
        "arithmetic_decode_exact": bool(decode["symbols_exact"]),
        "branch_population_exact": replay["branches"] == EXPECTED_BRANCHES,
        "source_at_most_65536": len(source_package) <= SOURCE_LIMIT_BYTES,
    }
    passed = all(conditions.values())
    decision = {
        "schema": "enwiki9_nncp_symbol_cache32_marginal_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "CAUSAL_SHADOW_COMPLETE",
        "verdict": (
            "authorize_open_same_object_cache_port"
            if passed
            else "retire_frozen_symbol_cache32_marginal"
        ),
        "epistemic_tier": "same_symbol_domain_exact_arithmetic_shadow_zero_score_credit",
        "score_credit_bytes": 0,
        "model": {
            "cache_window": CACHE_WINDOW,
            "base_prior_mass": BASE_PRIOR,
            "cache_prior_mass": CACHE_PRIOR,
            "cross_stream_offset": CROSS_STREAM_OFFSET,
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
            "baseline_trace": {
                "path": str(baseline_trace_path.relative_to(ROOT)),
                "sha256": actual_sha256["baseline_trace"],
            },
            "recurrence_decision_sha256": sha256_file(recurrence_decision_path),
            "driver_sha256": sha256_file(Path(__file__)),
        },
        "arithmetic": {
            "base_bytes": len(payloads["base"]),
            "base_sha256": sha256_bytes(payloads["base"]),
            "candidate_bytes": len(payloads["cache"]),
            "candidate_sha256": sha256_bytes(payloads["cache"]),
            "candidate_repeat_sha256": sha256_bytes(repeat_payload),
            "candidate_gain_bytes": candidate_gain,
            "cross_control_bytes": len(payloads["cross"]),
            "cross_control_sha256": sha256_bytes(payloads["cross"]),
            "cross_control_gain_bytes": control_gain,
            "candidate_margin_over_control_bytes": control_margin,
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
            "The arithmetic streams are exact for a receipt-bound teacher "
            "probability trace. The trace is not decoder-rebuilt by this "
            "program, LibNC remains ineligible, and no Hutter score or "
            "full-corpus forecast is inherited."
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
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "candidate_gain_bytes": candidate_gain,
                "control_margin_bytes": control_margin,
                "third_gains": third_gains,
                "verdict": decision["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
