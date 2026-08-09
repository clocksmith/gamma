#!/usr/bin/env python3
"""Repeat the frozen midpoint/cache joint replay with corrected provenance."""

from __future__ import annotations

import json
import lzma
from pathlib import Path
import resource

import numpy as np

import nncp_midpoint_cache32_joint_qm0 as q0


ROOT = q0.ROOT
CANDIDATE_ID = "nncp_midpoint_cache32_joint_qm1_v1"
PARENT_ID = q0.CANDIDATE_ID
EXPECTED_PAYLOADS = {
    "faithful": (
        341_558,
        "99c7d04d174f7ba1a30ae5b4af5c5b5d248cf33225713c1de2ed28862b5ec8c6",
    ),
    "midpoint": q0.EXPECTED_PAYLOADS["midpoint"],
}


def main() -> int:
    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(
            f"refusing to replace existing output directory: {output_dir}"
        )

    parent_decision_path = ROOT / "results" / PARENT_ID / "decision.json"
    parent = json.loads(parent_decision_path.read_text())
    parent_conditions = parent.get("conditions", {})
    expected_parent_conditions = {
        key: value
        for key, value in parent_conditions.items()
        if key != "faithful_payload_reproduced"
    }
    if parent.get("verdict") != "retire_frozen_midpoint_cache32_joint":
        raise ValueError("QM0 is not the expected provenance-failure parent")
    if parent_conditions.get("faithful_payload_reproduced") is not False:
        raise ValueError("QM0 did not expose the expected faithful hash failure")
    if not all(expected_parent_conditions.values()):
        raise ValueError("QM0 has a mechanism failure beyond faithful identity")

    midpoint_dir = ROOT / "results" / q0.MIDPOINT_ID
    faithful_path = midpoint_dir / "faithful_baseline_trace.bin"
    midpoint_path = midpoint_dir / "branch_trace.bin"
    actual_sha256 = {
        "symbols": q0.sha256_file(q0.SYMBOL_PATH),
        "faithful_trace": q0.sha256_file(faithful_path),
        "midpoint_trace": q0.sha256_file(midpoint_path),
    }
    if actual_sha256 != q0.EXPECTED_SHA256:
        raise ValueError("receipt-bound symbols or teacher trace identity mismatch")

    symbols = np.asarray(
        np.memmap(
            q0.SYMBOL_PATH, mode="r", dtype=">u2"
        )[: q0.SYMBOL_COUNT],
        dtype=np.uint16,
    )
    faithful_trace = np.memmap(faithful_path, mode="r", dtype="<u2")
    midpoint_trace = np.memmap(midpoint_path, mode="r", dtype="<u2")
    replay = q0.encode_all(symbols, faithful_trace, midpoint_trace)
    payloads = replay["payloads"]
    repeat_payload = replay["repeat_payload"]
    third_payloads = replay["third_payloads"]
    decode = q0.decode_joint(payloads["joint"], midpoint_trace, symbols)

    output_dir.mkdir(parents=True)
    for arm, payload in payloads.items():
        (output_dir / f"{arm}.bin").write_bytes(payload)

    reproduced = {
        arm: (
            len(payloads[arm]) == expected_bytes
            and q0.sha256_bytes(payloads[arm]) == expected_hash
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
        ROOT / "tools/nncp_midpoint_cache32_joint_qm0.py",
        ROOT / "tools/nncp_symbol_cache32_marginal_qm0.py",
        ROOT / "tools/nncp_midpoint_phase_attribution_qm0.py",
        ROOT / "docs/nncp_midpoint_cache32_joint_qm1_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/program.py",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
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
        "incremental_gain_at_least_4000": (
            incremental_gain >= q0.GAIN_GATE_BYTES
        ),
        "all_incremental_thirds_positive": all(
            value > 0 for value in third_incremental_gains
        ),
        "control_margin_at_least_1000": (
            control_margin >= q0.CONTROL_MARGIN_BYTES
        ),
        "repeat_payload_identical": repeat_payload == payloads["joint"],
        "arithmetic_decode_exact": bool(decode["symbols_exact"]),
        "branch_population_exact": replay["branches"] == q0.EXPECTED_BRANCHES,
        "source_at_most_65536": len(source_package) <= q0.SOURCE_LIMIT_BYTES,
    }
    passed = all(conditions.values())
    decision = {
        "schema": "enwiki9_nncp_midpoint_cache32_joint_qm1_v1",
        "candidate_id": CANDIDATE_ID,
        "parent_candidate_id": PARENT_ID,
        "status": "CAUSAL_SHADOW_COMPLETE",
        "verdict": (
            "authorize_same_object_mature_joint_replay"
            if passed
            else "retire_frozen_midpoint_cache32_joint"
        ),
        "epistemic_tier": "joint_teacher_trace_exact_arithmetic_shadow_zero_score_credit",
        "score_credit_bytes": 0,
        "correction": {
            "field": "EXPECTED_PAYLOADS.faithful.sha256",
            "mechanism_changed": False,
            "parent_decision_sha256": q0.sha256_file(parent_decision_path),
        },
        "model": parent["model"],
        "population": parent["population"],
        "inputs": {
            "symbols": {
                "path": str(q0.SYMBOL_PATH),
                "sha256": actual_sha256["symbols"],
            },
            "faithful_trace": {
                "path": str(faithful_path.relative_to(ROOT)),
                "sha256": actual_sha256["faithful_trace"],
            },
            "midpoint_trace": {
                "path": str(midpoint_path.relative_to(ROOT)),
                "sha256": actual_sha256["midpoint_trace"],
            },
            "driver_sha256": q0.sha256_file(Path(__file__)),
        },
        "arithmetic": {
            "faithful_bytes": len(payloads["faithful"]),
            "faithful_sha256": q0.sha256_bytes(payloads["faithful"]),
            "midpoint_bytes": len(payloads["midpoint"]),
            "midpoint_sha256": q0.sha256_bytes(payloads["midpoint"]),
            "joint_bytes": len(payloads["joint"]),
            "joint_sha256": q0.sha256_bytes(payloads["joint"]),
            "joint_repeat_sha256": q0.sha256_bytes(repeat_payload),
            "joint_total_gain_over_faithful_bytes": (
                len(payloads["faithful"]) - len(payloads["joint"])
            ),
            "joint_incremental_gain_over_midpoint_bytes": incremental_gain,
            "cross_bytes": len(payloads["cross"]),
            "cross_sha256": q0.sha256_bytes(payloads["cross"]),
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
        "claim_boundary": parent["claim_boundary"],
        "artifacts": {
            "incremental_source_package": {
                "path": str(source_path.relative_to(ROOT)),
                "bytes": len(source_package),
                "sha256": q0.sha256_file(source_path),
                "limit_bytes": q0.SOURCE_LIMIT_BYTES,
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
