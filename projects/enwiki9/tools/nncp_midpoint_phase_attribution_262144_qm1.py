#!/usr/bin/env python3
"""Replicate NNCP midpoint phase persistence at 262,144 symbols."""

from __future__ import annotations

import hashlib
import json
import lzma
import math
from pathlib import Path
import resource

import numpy as np

import nncp_midpoint_phase_attribution_qm0 as phase_qm0


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_midpoint_phase_attribution_262144_qm1_v1"
PARENT_ID = "nncp_midpoint_phase_attribution_qm0_v1"
MIDPOINT_ID = "nncp_midsegment32_update_262144_qm1_v1"
SYMBOL_PATH = Path(
    "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
    "preprocessed.bin"
)
SYMBOL_COUNT = 262_144
STREAM_LENGTH = SYMBOL_COUNT // phase_qm0.STREAMS
EXPECTED_BRANCHES = 3_670_169
SOURCE_LIMIT_BYTES = 65_536
TOLERANCE_BYTES = 1e-9


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")

    midpoint_dir = ROOT / "results" / MIDPOINT_ID
    midpoint_decision_path = midpoint_dir / "decision.json"
    parent_decision_path = ROOT / "results" / PARENT_ID / "decision.json"
    midpoint_decision = json.loads(midpoint_decision_path.read_text())
    parent_decision = json.loads(parent_decision_path.read_text())
    if midpoint_decision.get("status") != "AUTHORIZED_NATIVE_INTEGRATION":
        raise ValueError("262144-symbol midpoint parent is not authorized")
    if parent_decision.get("status") != "DIAGNOSTIC_COMPLETE":
        raise ValueError("phase attribution parent is not complete")

    baseline_trace_path = midpoint_dir / "faithful_baseline_trace.bin"
    candidate_trace_path = midpoint_dir / "branch_trace.bin"
    expected_hashes = {
        "symbols": midpoint_decision["inputs"]["preprocessed_sha256"],
        "baseline_trace": midpoint_decision["faithful_baseline"][
            "branch_trace_sha256"
        ],
        "candidate_trace": midpoint_decision["archive"]["branch_trace_sha256"],
    }
    actual_hashes = {
        "symbols": sha256_file(SYMBOL_PATH),
        "baseline_trace": sha256_file(baseline_trace_path),
        "candidate_trace": sha256_file(candidate_trace_path),
    }
    if actual_hashes != expected_hashes:
        raise ValueError("receipt-bound 262144 input hash mismatch")

    symbols = np.asarray(
        np.memmap(SYMBOL_PATH, mode="r", dtype=">u2")[:SYMBOL_COUNT],
        dtype=np.uint16,
    )
    baseline_trace = np.memmap(baseline_trace_path, mode="r", dtype="<u2")
    candidate_trace = np.memmap(candidate_trace_path, mode="r", dtype="<u2")
    phase_qm0.SYMBOL_COUNT = SYMBOL_COUNT
    phase_qm0.STREAM_LENGTH = STREAM_LENGTH
    phase_qm0.EXPECTED_BRANCHES = EXPECTED_BRANCHES
    attribution = phase_qm0.attribution(
        symbols, baseline_trace, candidate_trace
    )

    registered = midpoint_decision["maturity_comparison"]["aligned_ideal"]
    total_identity = math.isclose(
        attribution["total_gain_bytes"],
        registered["gain_bytes"],
        rel_tol=0.0,
        abs_tol=TOLERANCE_BYTES,
    )
    thirds_identity = bool(
        np.allclose(
            attribution["chronological_third_gain_bytes"],
            registered["chronological_third_gain_bytes"],
            rtol=0.0,
            atol=TOLERANCE_BYTES,
        )
    )
    segment_phase = np.asarray(
        attribution["segment_phase_gain_bytes"], dtype=np.float64
    )
    segment_totals = segment_phase.sum(axis=1)
    tail_segment_count = 32
    tail = segment_phase[-tail_segment_count:]
    tail_summary = {
        "segments": tail_segment_count,
        "total_gain_bytes": float(tail.sum()),
        "first_half_gain_bytes": float(tail[:, 0].sum()),
        "second_half_gain_bytes": float(tail[:, 1].sum()),
        "all_segment_totals_positive": bool(np.all(tail.sum(axis=1) > 0)),
    }
    parent_first_share = parent_decision["full_midpoint"]["first_half_share"]
    share_delta = attribution["first_half_share"] - parent_first_share
    integrity = {
        "receipt_bound_hash_identity": actual_hashes == expected_hashes,
        "symbol_count_identity": len(symbols) == SYMBOL_COUNT,
        "branch_population_identity": (
            len(baseline_trace) == EXPECTED_BRANCHES
            and len(candidate_trace) == EXPECTED_BRANCHES
        ),
        "registered_total_identity": total_identity,
        "registered_thirds_identity": thirds_identity,
        "baseline_first_segment_first_half_identity": (
            attribution["segment_zero_first_half_gain_bytes"] == 0.0
        ),
        "persistent_share_replication": (
            attribution["first_half_gain_bytes"] > 0
            and abs(share_delta) <= 0.02
        ),
        "tail_first_half_positive": tail_summary["first_half_gain_bytes"] > 0,
    }
    if not all(integrity.values()):
        raise ValueError(f"262144 attribution integrity failed: {integrity}")

    source_paths = (
        Path(__file__),
        ROOT / "tools/nncp_midpoint_phase_attribution_qm0.py",
        ROOT / f"programs/{CANDIDATE_ID}/program.py",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
        ROOT
        / (
            "operations/adaptive/proposals/developed/000_"
            f"{CANDIDATE_ID}.json"
        ),
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
        "schema": "enwiki9_nncp_midpoint_phase_attribution_262144_qm1_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "DIAGNOSTIC_COMPLETE",
        "verdict": "persistent_deep_trajectory_replicated_at_262144",
        "epistemic_tier": "exact_trace_attribution_zero_score_credit",
        "score_credit_bytes": 0,
        "decision": {
            "promotion_authorized": False,
            "verified_full_1g_score_bytes": None,
            "forecast_bytes": 109_389_323,
        },
        "population": {
            "symbols": SYMBOL_COUNT,
            "streams": phase_qm0.STREAMS,
            "symbols_per_stream": STREAM_LENGTH,
            "segment_symbols": phase_qm0.SEGMENT,
            "midpoint": phase_qm0.MIDPOINT,
            "segments": STREAM_LENGTH // phase_qm0.SEGMENT,
            "branch_frequencies": EXPECTED_BRANCHES,
        },
        "inputs": {
            "paths": {
                "symbols": str(SYMBOL_PATH),
                "baseline_trace": str(baseline_trace_path.relative_to(ROOT)),
                "candidate_trace": str(candidate_trace_path.relative_to(ROOT)),
            },
            "sha256": actual_hashes,
            "midpoint_decision_sha256": sha256_file(midpoint_decision_path),
            "parent_decision_sha256": sha256_file(parent_decision_path),
            "driver_sha256": sha256_file(Path(__file__)),
        },
        "integrity": integrity,
        "full_midpoint": attribution,
        "replication": {
            "parent_65536_first_half_share": parent_first_share,
            "current_262144_first_half_share": attribution["first_half_share"],
            "first_half_share_delta": share_delta,
            "nonpositive_segment_count": int(np.sum(segment_totals <= 0)),
            "nonpositive_first_half_count": int(np.sum(segment_phase[:, 0] <= 0)),
            "nonpositive_second_half_count": int(np.sum(segment_phase[:, 1] <= 0)),
            "minimum_segment_gain_bytes": float(segment_totals.min()),
            "minimum_segment_index": int(segment_totals.argmin()),
            "tail": tail_summary,
        },
        "interpretation": {
            "conclusion": (
                "The persistent pre-midpoint share remains approximately "
                "44 percent at four times the exact population and remains "
                "positive in the final 32 segments. Compact attribution must "
                "preserve a persistent decoder-visible state trajectory."
            ),
            "claim_boundary": (
                "This oracle neither identifies a sufficient parameter subset "
                "nor authorizes a midpoint descendant before the exact-native "
                "and mature source-native gates both pass."
            ),
        },
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
                "first_half_gain_bytes": attribution["first_half_gain_bytes"],
                "first_half_share": attribution["first_half_share"],
                "second_half_gain_bytes": attribution["second_half_gain_bytes"],
                "tail_first_half_gain_bytes": tail_summary["first_half_gain_bytes"],
                "total_gain_bytes": attribution["total_gain_bytes"],
                "verdict": decision["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
