#!/usr/bin/env python3
"""Promote the frozen NNCP 32/32 update schedule to 262,144 symbols."""

from __future__ import annotations

import hashlib
import json
import lzma
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
ROCM_PYTHON = Path("/home/x/deco/gamma/.venv_rocm/bin/python")
os.environ.setdefault("AMD_SERIALIZE_KERNEL", "3")
os.environ.setdefault("HSA_OVERRIDE_GFX_VERSION", "11.0.0")
if Path(sys.executable) != ROCM_PYTHON:
    if not ROCM_PYTHON.is_file():
        raise SystemExit(f"missing receipt-bound ROCm interpreter: {ROCM_PYTHON}")
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        os.environ.copy(),
    )

import numpy as np
import torch

import nncp_midsegment32_update_qm0 as q0


parent = q0.parent
headroom = parent.headroom_q1
comparison_harness = q0.comparison_harness
core = q0.core
CANDIDATE_ID = "nncp_midsegment32_update_262144_qm1_v1"
SYMBOL_COUNT = 262_144
STREAM_LENGTH = SYMBOL_COUNT // core.Config.streams
GAIN_GATE_BYTES = 8_000
SOURCE_LIMIT_BYTES = 65_536
Q0_DECISION = ROOT / "results/nncp_midsegment32_update_qm0_v1/decision.json"
Q0_DECISION_SHA256 = "7245450832f5e31240b861e62461b736ad25e5965f6af53b90b77427d5fd76a7"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    if sha256(Q0_DECISION) != Q0_DECISION_SHA256:
        raise ValueError("authorized Qm0 decision identity mismatch")
    q0_decision = json.loads(Q0_DECISION.read_text())
    if q0_decision.get("status") != "AUTHORIZED_MATURE_MIDSEGMENT32":
        raise ValueError("Qm0 does not authorize the maturity gate")

    output_dir = ROOT / "results" / CANDIDATE_ID
    if "--output-dir" not in sys.argv:
        sys.argv.extend(("--output-dir", str(output_dir)))
    else:
        output_dir = Path(sys.argv[sys.argv.index("--output-dir") + 1]).resolve()
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")

    preprocessed_path = Path(
        "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
        "preprocessed.bin"
    )
    symbols = np.asarray(
        np.memmap(preprocessed_path, mode="r", dtype=">u2")[:SYMBOL_COUNT],
        dtype=np.uint16,
    )
    config = core.Config()
    if len(symbols) != SYMBOL_COUNT or int(symbols.max()) >= config.vocabulary:
        raise ValueError("frozen 262,144-symbol population is invalid")
    if not torch.cuda.is_available() or torch.version.hip is None:
        raise SystemExit("PyTorch ROCm is required")
    torch.use_deterministic_algorithms(True)
    device = torch.device("cuda")

    headroom.SYMBOL_COUNT = SYMBOL_COUNT
    headroom.STREAM_LENGTH = STREAM_LENGTH
    q0.STREAM_LENGTH = STREAM_LENGTH
    comparison_harness.SYMBOL_COUNT = SYMBOL_COUNT
    comparison_harness.STREAM_LENGTH = STREAM_LENGTH

    faithful_run_once = parent.run_once
    print(json.dumps({"event": "fresh_faithful_baseline_start"}), flush=True)
    baseline = faithful_run_once(
        symbols, config, device, "encode_first"
    )
    baseline_archive = baseline["archive"]
    baseline_trace_bytes = core.trace_bytes(baseline["branch_trace"])
    print(
        json.dumps(
            {
                "archive_bytes": len(baseline_archive),
                "event": "fresh_faithful_baseline_complete",
            },
            sort_keys=True,
        ),
        flush=True,
    )

    parent.run_once = q0.run_once
    parent.CANDIDATE_ID = CANDIDATE_ID
    status = parent.main()

    decision_path = output_dir / "decision.json"
    decision = json.loads(decision_path.read_text())
    candidate_archive_path = output_dir / "archive.bin"
    candidate_trace_path = output_dir / "branch_trace.bin"
    baseline_archive_path = output_dir / "faithful_baseline.bin"
    baseline_trace_path = output_dir / "faithful_baseline_trace.bin"
    baseline_archive_path.write_bytes(baseline_archive)
    baseline_trace_path.write_bytes(baseline_trace_bytes)

    baseline_trace = np.frombuffer(baseline_trace_bytes, dtype="<u2")
    candidate_trace = np.memmap(candidate_trace_path, mode="r", dtype="<u2")
    ideal = comparison_harness.aligned_ideal_gain(
        symbols, baseline_trace, candidate_trace
    )
    candidate_bytes = candidate_archive_path.stat().st_size
    actual_gain = len(baseline_archive) - candidate_bytes

    source_paths = (
        Path(__file__),
        ROOT / "tools/nncp_midsegment32_update_qm0.py",
        ROOT / "docs/nncp_midsegment32_update_262144_qm1_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)

    failed: list[str] = []
    if not all(bool(value) for value in decision["integrity"].values()):
        failed.append("candidate_exact_identity_failed")
    if actual_gain < GAIN_GATE_BYTES:
        failed.append("actual_gain_below_8000")
    if any(value <= 0 for value in ideal["chronological_third_gain_bytes"]):
        failed.append("aligned_ideal_chronological_third_nonpositive")
    candidate_resource = decision["resource"]
    baseline_memory_pass = (
        baseline["peak_allocated_bytes"] < 10_000_000_000
        and baseline["peak_reserved_bytes"] < 10_000_000_000
    )
    if not (
        candidate_resource["decimal_10gb_allocated_pass"]
        and candidate_resource["decimal_10gb_reserved_pass"]
        and baseline_memory_pass
    ):
        failed.append("decimal_10gb_memory_failed")
    if len(source_package) > SOURCE_LIMIT_BYTES:
        failed.append("incremental_source_exceeds_65536")
    promotion = not failed

    decision.update(
        {
            "schema": "enwiki9_nncp_midsegment32_update_262144_qm1_v1",
            "candidate_id": CANDIDATE_ID,
            "status": "AUTHORIZED_NATIVE_INTEGRATION" if promotion else "REJECT",
            "verdict": (
                "authorize_native_midsegment_integration"
                if promotion
                else "retain_qm0_opening_only"
            ),
            "score_credit_bytes": 0,
            "epistemic_tier": "exact_262144_symbol_constructive_child_zero_credit",
            "faithful_baseline": {
                "archive_bytes": len(baseline_archive),
                "archive_sha256": hashlib.sha256(baseline_archive).hexdigest(),
                "branch_trace_sha256": hashlib.sha256(
                    baseline_trace_bytes
                ).hexdigest(),
                "complete_state_sha256": baseline["complete_state_sha256"],
                "peak_allocated_bytes": baseline["peak_allocated_bytes"],
                "peak_reserved_bytes": baseline["peak_reserved_bytes"],
                "decimal_10gb_memory_pass": baseline_memory_pass,
            },
            "maturity_comparison": {
                "candidate_archive_bytes": candidate_bytes,
                "candidate_archive_sha256": sha256(candidate_archive_path),
                "actual_gain_bytes": actual_gain,
                "required_actual_gain_bytes": GAIN_GATE_BYTES,
                "aligned_ideal": ideal,
                "incremental_source_package_bytes": len(source_package),
                "incremental_source_limit_bytes": SOURCE_LIMIT_BYTES,
            },
            "failed_conditions": failed,
            "claim_boundary": (
                "Exact fresh-parent 262,144-symbol maturity comparison for the "
                "frozen 32/32 schedule. No published NNCP, package forecast, "
                "full-corpus score, or Endpoint428 composability inheritance."
            ),
        }
    )
    decision["decision"]["promotion_authorized"] = promotion
    decision["inputs"]["qm0_decision_sha256"] = Q0_DECISION_SHA256
    decision["inputs"]["maturity_driver_script_sha256"] = sha256(Path(__file__))
    decision["artifacts"] = {
        "incremental_source_package": {
            "path": str(source_path.relative_to(ROOT)),
            "bytes": len(source_package),
            "sha256": sha256(source_path),
        }
    }
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "actual_gain_bytes": actual_gain,
                "candidate_archive_bytes": candidate_bytes,
                "failed_conditions": failed,
                "faithful_archive_bytes": len(baseline_archive),
                "ideal_third_gain_bytes": ideal[
                    "chronological_third_gain_bytes"
                ],
                "verdict": decision["verdict"],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return status


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"nncp-midsegment32-update-262144-qm1: {error}", file=sys.stderr)
        raise
