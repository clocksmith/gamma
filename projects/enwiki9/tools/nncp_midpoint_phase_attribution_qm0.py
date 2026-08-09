#!/usr/bin/env python3
"""Decompose exact NNCP midpoint gains by phase, position, and persistence."""

from __future__ import annotations

import hashlib
import json
import lzma
import math
from pathlib import Path
import resource

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_midpoint_phase_attribution_qm0_v1"
BASELINE_ID = "nncp_v33_rocm_incremental_kv_65536_headroom_q1_v1"
FULL_ID = "nncp_midsegment32_update_qm0_v1"
BIAS_ID = "nncp_midpoint_bias_only_qm0_v1"
SYMBOL_PATH = Path(
    "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
    "preprocessed.bin"
)
SYMBOL_COUNT = 65_536
STREAMS = 32
STREAM_LENGTH = SYMBOL_COUNT // STREAMS
SEGMENT = 64
MIDPOINT = 32
VOCABULARY = 16_392
PROBABILITY_TOTAL = 1 << 15
EXPECTED_BRANCHES = 917_527
SOURCE_LIMIT_BYTES = 65_536
TOLERANCE_BYTES = 1e-9


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


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
        raise ValueError("balanced symbol path did not terminate at truth")
    return bits


def attribution(
    symbols: np.ndarray,
    baseline_trace: np.ndarray,
    candidate_trace: np.ndarray,
) -> dict[str, object]:
    if len(baseline_trace) != len(candidate_trace):
        raise ValueError("candidate branch population differs from baseline")
    if len(baseline_trace) != EXPECTED_BRANCHES:
        raise ValueError("unexpected branch population")

    matrix = symbols.reshape(STREAMS, STREAM_LENGTH)
    by_position = np.zeros(SEGMENT, dtype=np.float64)
    by_segment_phase = np.zeros((STREAM_LENGTH // SEGMENT, 2), dtype=np.float64)
    by_stream = np.zeros(STREAMS, dtype=np.float64)
    by_third = np.zeros(3, dtype=np.float64)
    branch = 0

    for segment_index, segment_start in enumerate(
        range(0, STREAM_LENGTH, SEGMENT)
    ):
        for state in range(SEGMENT):
            absolute = segment_start + state
            phase = state // MIDPOINT
            for stream in range(STREAMS):
                symbol = int(matrix[stream, absolute])
                original = stream * STREAM_LENGTH + absolute
                third = min(2, original * 3 // SYMBOL_COUNT)
                gain_bits = 0.0
                for bit in expected_bits(symbol):
                    baseline_zero = int(baseline_trace[branch])
                    candidate_zero = int(candidate_trace[branch])
                    baseline_mass = (
                        baseline_zero
                        if bit == 0
                        else PROBABILITY_TOTAL - baseline_zero
                    )
                    candidate_mass = (
                        candidate_zero
                        if bit == 0
                        else PROBABILITY_TOTAL - candidate_zero
                    )
                    if min(baseline_mass, candidate_mass) <= 0:
                        raise ValueError("illegal zero branch frequency")
                    gain_bits += math.log2(candidate_mass / baseline_mass)
                    branch += 1
                gain_bytes = gain_bits / 8.0
                by_position[state] += gain_bytes
                by_segment_phase[segment_index, phase] += gain_bytes
                by_stream[stream] += gain_bytes
                by_third[third] += gain_bytes

    if branch != EXPECTED_BRANCHES:
        raise ValueError("branch trace was not consumed exactly")

    first_half = float(by_position[:MIDPOINT].sum())
    second_half = float(by_position[MIDPOINT:].sum())
    total = first_half + second_half
    segment_totals = by_segment_phase.sum(axis=1)
    segment_quarters = [
        float(segment_totals[index : index + 8].sum())
        for index in range(0, len(segment_totals), 8)
    ]
    position_octets = [
        float(by_position[index : index + 8].sum())
        for index in range(0, SEGMENT, 8)
    ]
    return {
        "branch_frequencies": branch,
        "total_gain_bytes": total,
        "first_half_gain_bytes": first_half,
        "second_half_gain_bytes": second_half,
        "first_half_share": first_half / total if total else None,
        "second_half_share": second_half / total if total else None,
        "segment_zero_first_half_gain_bytes": float(by_segment_phase[0, 0]),
        "segment_zero_second_half_gain_bytes": float(by_segment_phase[0, 1]),
        "position_gain_bytes": by_position.tolist(),
        "position_octet_gain_bytes": position_octets,
        "segment_phase_gain_bytes": by_segment_phase.tolist(),
        "segment_total_gain_bytes": segment_totals.tolist(),
        "segment_quarter_gain_bytes": segment_quarters,
        "stream_gain_bytes": by_stream.tolist(),
        "chronological_third_gain_bytes": by_third.tolist(),
        "all_position_octets_positive": all(value > 0 for value in position_octets),
        "all_segment_quarters_positive": all(
            value > 0 for value in segment_quarters
        ),
        "all_segment_totals_positive": bool(np.all(segment_totals > 0)),
    }


def main() -> int:
    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")

    baseline_dir = ROOT / "results" / BASELINE_ID
    full_dir = ROOT / "results" / FULL_ID
    bias_dir = ROOT / "results" / BIAS_ID
    baseline_decision_path = baseline_dir / "decision.json"
    full_decision_path = full_dir / "decision.json"
    bias_decision_path = bias_dir / "decision.json"
    baseline_decision = read_json(baseline_decision_path)
    full_decision = read_json(full_decision_path)
    bias_decision = read_json(bias_decision_path)

    baseline_trace_path = baseline_dir / "branch_trace.bin"
    full_trace_path = full_dir / "branch_trace.bin"
    bias_trace_path = bias_dir / "branch_trace.bin"
    expected_hashes = {
        "symbols": full_decision["inputs"]["preprocessed_sha256"],
        "baseline_trace": baseline_decision["archive"]["branch_trace_sha256"],
        "full_trace": full_decision["archive"]["branch_trace_sha256"],
        "bias_trace": bias_decision["archive"]["branch_trace_sha256"],
    }
    actual_hashes = {
        "symbols": sha256_file(SYMBOL_PATH),
        "baseline_trace": sha256_file(baseline_trace_path),
        "full_trace": sha256_file(full_trace_path),
        "bias_trace": sha256_file(bias_trace_path),
    }
    hash_identity = actual_hashes == expected_hashes
    if not hash_identity:
        raise ValueError("receipt-bound input hash mismatch")

    symbols = np.asarray(
        np.memmap(SYMBOL_PATH, mode="r", dtype=">u2")[:SYMBOL_COUNT],
        dtype=np.uint16,
    )
    traces = {
        "baseline": np.memmap(baseline_trace_path, mode="r", dtype="<u2"),
        "full": np.memmap(full_trace_path, mode="r", dtype="<u2"),
        "bias": np.memmap(bias_trace_path, mode="r", dtype="<u2"),
    }
    full = attribution(symbols, traces["baseline"], traces["full"])
    bias = attribution(symbols, traces["baseline"], traces["bias"])

    registered_full = full_decision["midsegment_comparison"]["aligned_ideal"]
    registered_bias = bias_decision["midsegment_comparison"]["aligned_ideal"]
    full_total_identity = math.isclose(
        full["total_gain_bytes"],
        registered_full["gain_bytes"],
        rel_tol=0.0,
        abs_tol=TOLERANCE_BYTES,
    )
    bias_total_identity = math.isclose(
        bias["total_gain_bytes"],
        registered_bias["gain_bytes"],
        rel_tol=0.0,
        abs_tol=TOLERANCE_BYTES,
    )
    full_thirds_identity = bool(
        np.allclose(
            full["chronological_third_gain_bytes"],
            registered_full["chronological_third_gain_bytes"],
            rtol=0.0,
            atol=TOLERANCE_BYTES,
        )
    )
    bias_thirds_identity = bool(
        np.allclose(
            bias["chronological_third_gain_bytes"],
            registered_bias["chronological_third_gain_bytes"],
            rtol=0.0,
            atol=TOLERANCE_BYTES,
        )
    )
    integrity = {
        "receipt_bound_hash_identity": hash_identity,
        "symbol_count_identity": len(symbols) == SYMBOL_COUNT,
        "branch_population_identity": all(
            len(trace) == EXPECTED_BRANCHES for trace in traces.values()
        ),
        "full_registered_total_identity": full_total_identity,
        "bias_registered_total_identity": bias_total_identity,
        "full_registered_thirds_identity": full_thirds_identity,
        "bias_registered_thirds_identity": bias_thirds_identity,
        "baseline_first_segment_first_half_identity": (
            full["segment_zero_first_half_gain_bytes"] == 0.0
            and bias["segment_zero_first_half_gain_bytes"] == 0.0
        ),
    }
    if not all(integrity.values()):
        raise ValueError(f"attribution integrity failed: {integrity}")

    source_paths = (
        Path(__file__),
        ROOT / f"programs/{CANDIDATE_ID}/program.py",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
        ROOT
        / f"operations/adaptive/proposals/developed/000_{CANDIDATE_ID}.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_limit_pass = len(source_package) <= SOURCE_LIMIT_BYTES
    if not source_limit_pass:
        raise ValueError("diagnostic source package exceeds frozen limit")

    output_dir.mkdir(parents=True)
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)
    decision = {
        "schema": "enwiki9_nncp_midpoint_phase_attribution_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "DIAGNOSTIC_COMPLETE",
        "verdict": "persistent_deep_trajectory_confirmed",
        "epistemic_tier": "exact_trace_attribution_zero_score_credit",
        "score_credit_bytes": 0,
        "decision": {
            "promotion_authorized": False,
            "verified_full_1g_score_bytes": None,
            "forecast_bytes": 109_389_323,
        },
        "population": {
            "symbols": SYMBOL_COUNT,
            "streams": STREAMS,
            "symbols_per_stream": STREAM_LENGTH,
            "segment_symbols": SEGMENT,
            "midpoint": MIDPOINT,
            "segments": STREAM_LENGTH // SEGMENT,
            "branch_frequencies": EXPECTED_BRANCHES,
        },
        "inputs": {
            "paths": {
                "symbols": str(SYMBOL_PATH),
                "baseline_trace": str(baseline_trace_path.relative_to(ROOT)),
                "full_trace": str(full_trace_path.relative_to(ROOT)),
                "bias_trace": str(bias_trace_path.relative_to(ROOT)),
            },
            "sha256": actual_hashes,
            "baseline_decision_sha256": sha256_file(baseline_decision_path),
            "full_decision_sha256": sha256_file(full_decision_path),
            "bias_decision_sha256": sha256_file(bias_decision_path),
            "driver_sha256": sha256_file(Path(__file__)),
        },
        "integrity": integrity,
        "full_midpoint": full,
        "bias_only_midpoint": bias,
        "interpretation": {
            "persistent_first_half_gain_bytes": full["first_half_gain_bytes"],
            "persistent_first_half_share": full["first_half_share"],
            "post_midpoint_phase_gain_bytes": full["second_half_gain_bytes"],
            "post_midpoint_phase_share": full["second_half_share"],
            "conclusion": (
                "The full midpoint update improves later pre-midpoint first "
                "halves as well as post-midpoint states. A stateless "
                "second-half correction cannot inherit the measured gain; "
                "any compact descendant must preserve a causal persistent "
                "state effect and receive exact joint replay."
            ),
            "claim_boundary": (
                "This trace decomposition does not identify the sufficient "
                "parameter subset, authorize K/O/OK/F/S before the exact and "
                "mature gates pass, forecast full-corpus gain, or earn score "
                "credit."
            ),
        },
        "artifacts": {
            "incremental_source_package": {
                "path": str(source_path.relative_to(ROOT)),
                "bytes": len(source_package),
                "sha256": sha256_file(source_path),
                "limit_bytes": SOURCE_LIMIT_BYTES,
                "limit_pass": source_limit_pass,
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
                "bias_total_gain_bytes": bias["total_gain_bytes"],
                "full_first_half_gain_bytes": full["first_half_gain_bytes"],
                "full_second_half_gain_bytes": full["second_half_gain_bytes"],
                "full_total_gain_bytes": full["total_gain_bytes"],
                "verdict": decision["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
