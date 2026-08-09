#!/usr/bin/env python3
"""Localize exact NNCP midpoint gain by causal same-stream symbol recurrence."""

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
CANDIDATE_ID = "nncp_midpoint_decoder_visible_recurrence_qm0_v1"
MIDPOINT_ID = "nncp_midsegment32_update_262144_qm1_v1"
PHASE_ID = "nncp_midpoint_phase_attribution_262144_qm1_v1"
SYMBOL_PATH = Path(
    "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
    "preprocessed.bin"
)
SYMBOL_COUNT = 262_144
STREAMS = 32
STREAM_LENGTH = SYMBOL_COUNT // STREAMS
SEGMENT = 64
MIDPOINT = 32
EXPECTED_BRANCHES = 3_670_169
EXPECTED_GAIN_BYTES = 17_185.333881650356
ROTATION_SYMBOLS = 17 * SEGMENT
SOURCE_LIMIT_BYTES = 65_536
TOLERANCE_BYTES = 1e-9

EXPECTED_SHA256 = {
    "symbols": "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5",
    "baseline_trace": "8c37f952fab1242743366b99083243263cb7eb5309cd10f45a36e99188a0a706",
    "candidate_trace": "25d7b9e5566d8c0391509f92d63b488514fd42f33c4701092d01f0d2d347fa7d",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def gain_matrix(
    symbols: np.ndarray,
    baseline: np.ndarray,
    candidate: np.ndarray,
) -> np.ndarray:
    if len(baseline) != EXPECTED_BRANCHES or len(candidate) != EXPECTED_BRANCHES:
        raise ValueError("branch trace population differs from frozen receipt")
    matrix = symbols.reshape(STREAMS, STREAM_LENGTH)
    gains = np.zeros((STREAMS, STREAM_LENGTH), dtype=np.float64)
    branch = 0
    for segment_start in range(0, STREAM_LENGTH, SEGMENT):
        for state in range(SEGMENT):
            absolute = segment_start + state
            for stream in range(STREAMS):
                symbol = int(matrix[stream, absolute])
                gain_bits = 0.0
                for bit in phase.expected_bits(symbol):
                    baseline_zero = int(baseline[branch])
                    candidate_zero = int(candidate[branch])
                    baseline_mass = (
                        baseline_zero
                        if bit == 0
                        else phase.PROBABILITY_TOTAL - baseline_zero
                    )
                    candidate_mass = (
                        candidate_zero
                        if bit == 0
                        else phase.PROBABILITY_TOTAL - candidate_zero
                    )
                    if min(baseline_mass, candidate_mass) <= 0:
                        raise ValueError("illegal zero branch frequency")
                    gain_bits += math.log2(candidate_mass / baseline_mass)
                    branch += 1
                gains[stream, absolute] = gain_bits / 8.0
    if branch != EXPECTED_BRANCHES:
        raise ValueError("branch traces were not consumed exactly")
    return gains


def recurrence_features(symbols: np.ndarray) -> dict[str, np.ndarray]:
    matrix = symbols.reshape(STREAMS, STREAM_LENGTH)
    distance = np.full((STREAMS, STREAM_LENGTH), -1, dtype=np.int32)
    same_segment = np.zeros_like(distance, dtype=bool)
    first_half_support = np.zeros_like(distance, dtype=bool)
    for stream in range(STREAMS):
        last: dict[int, int] = {}
        for absolute in range(STREAM_LENGTH):
            symbol = int(matrix[stream, absolute])
            previous = last.get(symbol)
            if previous is not None:
                delta = absolute - previous
                distance[stream, absolute] = delta
                segment_start = (absolute // SEGMENT) * SEGMENT
                same_segment[stream, absolute] = previous >= segment_start
                first_half_support[stream, absolute] = (
                    absolute % SEGMENT >= MIDPOINT
                    and segment_start <= previous < segment_start + MIDPOINT
                )
            last[symbol] = absolute
    return {
        "distance": distance,
        "same_segment": same_segment,
        "first_half_support": first_half_support,
    }


def chronological_thirds(mask: np.ndarray, gains: np.ndarray) -> list[float]:
    flat_mask = mask.reshape(-1)
    flat_gain = gains.reshape(-1)
    first = (SYMBOL_COUNT + 2) // 3
    second = (2 * SYMBOL_COUNT + 2) // 3
    return [
        float(flat_gain[start:end][flat_mask[start:end]].sum())
        for start, end in (
            (0, first),
            (first, second),
            (second, SYMBOL_COUNT),
        )
    ]


def summarize_mask(
    mask: np.ndarray,
    gains: np.ndarray,
    rotated: np.ndarray,
    total_gain: float,
) -> dict[str, object]:
    genuine = float(gains[mask].sum())
    control = float(rotated[mask].sum())
    count = int(mask.sum())
    return {
        "events": count,
        "event_fraction": count / SYMBOL_COUNT,
        "genuine_gain_bytes": genuine,
        "genuine_gain_share": genuine / total_gain,
        "genuine_gain_bytes_per_1000_events": genuine * 1000.0 / count if count else None,
        "rotated_control_gain_bytes": control,
        "specificity_margin_bytes": genuine - control,
        "specificity_margin_share": (genuine - control) / total_gain,
        "chronological_third_gain_bytes": chronological_thirds(mask, gains),
    }


def main() -> int:
    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")

    midpoint_dir = ROOT / "results" / MIDPOINT_ID
    phase_decision_path = ROOT / "results" / PHASE_ID / "decision.json"
    midpoint_decision_path = midpoint_dir / "decision.json"
    baseline_trace_path = midpoint_dir / "faithful_baseline_trace.bin"
    candidate_trace_path = midpoint_dir / "branch_trace.bin"
    paths = {
        "symbols": SYMBOL_PATH,
        "baseline_trace": baseline_trace_path,
        "candidate_trace": candidate_trace_path,
    }
    actual_sha256 = {name: sha256_file(path) for name, path in paths.items()}
    if actual_sha256 != EXPECTED_SHA256:
        raise ValueError("receipt-bound symbol or trace identity mismatch")

    midpoint_decision = json.loads(midpoint_decision_path.read_text())
    phase_decision = json.loads(phase_decision_path.read_text())
    if midpoint_decision.get("status") != "AUTHORIZED_NATIVE_INTEGRATION":
        raise ValueError("midpoint trace parent is not authorized teacher evidence")
    if phase_decision.get("status") != "DIAGNOSTIC_COMPLETE":
        raise ValueError("phase attribution parent is incomplete")

    symbols = np.asarray(
        np.memmap(SYMBOL_PATH, mode="r", dtype=">u2")[:SYMBOL_COUNT],
        dtype=np.uint16,
    )
    baseline = np.memmap(baseline_trace_path, mode="r", dtype="<u2")
    candidate = np.memmap(candidate_trace_path, mode="r", dtype="<u2")
    gains = gain_matrix(symbols, baseline, candidate)
    total_gain = float(gains.sum())
    registered_thirds = midpoint_decision["maturity_comparison"]["aligned_ideal"][
        "chronological_third_gain_bytes"
    ]
    measured_thirds = chronological_thirds(np.ones_like(gains, dtype=bool), gains)
    total_identity = math.isclose(
        total_gain, EXPECTED_GAIN_BYTES, rel_tol=0.0, abs_tol=TOLERANCE_BYTES
    )
    thirds_identity = bool(
        np.allclose(
            measured_thirds,
            registered_thirds,
            rtol=0.0,
            atol=TOLERANCE_BYTES,
        )
    )
    if not total_identity or not thirds_identity:
        raise ValueError("reconstructed gain differs from registered teacher result")

    features = recurrence_features(symbols)
    distance = features["distance"]
    rotated = np.roll(gains, ROTATION_SYMBOLS, axis=1)
    masks = {
        "never_seen": distance < 0,
        "distance_1": distance == 1,
        "distance_2_8": (2 <= distance) & (distance <= 8),
        "distance_9_32": (9 <= distance) & (distance <= 32),
        "distance_33_64": (33 <= distance) & (distance <= 64),
        "distance_65_256": (65 <= distance) & (distance <= 256),
        "distance_257_plus": distance >= 257,
        "recent_32": (1 <= distance) & (distance <= 32),
        "same_segment": features["same_segment"],
        "second_half_first_half_support": features["first_half_support"],
    }
    summaries = {
        name: summarize_mask(mask, gains, rotated, total_gain)
        for name, mask in masks.items()
    }
    primary = summaries["recent_32"]
    conditions = {
        "registered_total_identity": total_identity,
        "registered_thirds_identity": thirds_identity,
        "recurrence_prefix_causal": True,
        "recent32_gain_share_at_least_0p25": primary["genuine_gain_share"] >= 0.25,
        "recent32_specificity_margin_share_at_least_0p10": (
            primary["specificity_margin_share"] >= 0.10
        ),
        "recent32_all_thirds_positive": all(
            value > 0 for value in primary["chronological_third_gain_bytes"]
        ),
    }
    supported = all(conditions.values())

    source_paths = (
        Path(__file__),
        ROOT / "docs/nncp_midpoint_decoder_visible_recurrence_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/program.py",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
        ROOT
        / f"operations/adaptive/proposals/developed/000_{CANDIDATE_ID}.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    if len(source_package) > SOURCE_LIMIT_BYTES:
        raise ValueError("diagnostic source package exceeds frozen limit")

    output_dir.mkdir(parents=True)
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)
    decision = {
        "schema": "enwiki9_nncp_midpoint_decoder_visible_recurrence_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "DIAGNOSTIC_COMPLETE",
        "verdict": (
            "bounded_recurrence_coordinate_supported"
            if supported
            else "retire_simple_bounded_symbol_recurrence_distillation"
        ),
        "epistemic_tier": "exact_trace_attribution_zero_score_credit",
        "score_credit_bytes": 0,
        "population": {
            "symbols": SYMBOL_COUNT,
            "streams": STREAMS,
            "symbols_per_stream": STREAM_LENGTH,
            "segment_symbols": SEGMENT,
            "midpoint": MIDPOINT,
            "branch_frequencies": EXPECTED_BRANCHES,
        },
        "inputs": {
            "paths": {name: str(path) for name, path in paths.items()},
            "sha256": actual_sha256,
            "midpoint_decision_sha256": sha256_file(midpoint_decision_path),
            "phase_decision_sha256": sha256_file(phase_decision_path),
            "driver_sha256": sha256_file(Path(__file__)),
        },
        "gain": {
            "total_bytes": total_gain,
            "chronological_third_bytes": measured_thirds,
            "registered_total_identity": total_identity,
            "registered_thirds_identity": thirds_identity,
        },
        "control": {
            "kind": "phase_preserving_gain_rotation_within_stream",
            "rotation_segments": 17,
            "rotation_symbols": ROTATION_SYMBOLS,
        },
        "classes": summaries,
        "conditions": conditions,
        "decision": {
            "diagnostic_support": supported,
            "promotion_authorized": False,
            "verified_full_1g_score_bytes": None,
            "forecast_bytes": 109_389_323,
        },
        "claim_boundary": (
            "This exact offline attribution changes no probability stream, "
            "earns zero score and forecast credit, does not make LibNC "
            "eligible, and cannot authorize a codec without a new open "
            "same-object arithmetic replay."
        ),
        "artifacts": {
            "incremental_source_package": {
                "path": str(source_path.relative_to(ROOT)),
                "bytes": len(source_package),
                "sha256": sha256_file(source_path),
                "limit_bytes": SOURCE_LIMIT_BYTES,
                "limit_pass": True,
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
                "recent32_gain_bytes": primary["genuine_gain_bytes"],
                "recent32_gain_share": primary["genuine_gain_share"],
                "recent32_specificity_margin_bytes": primary["specificity_margin_bytes"],
                "verdict": decision["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
