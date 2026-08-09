#!/usr/bin/env python3
"""Test one fixed 64-summary/192-exact NNCP hidden-memory representation."""

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

import torch

import nncp_evicted_ema_memory_qm0 as harness


CANDIDATE_ID = "nncp_hierarchical_448_memory_qm0_v1"
SUMMARY_SLOTS = 64
SUMMARY_WIDTH = 4
EXACT_SLOTS = 192
SOURCE_LIMIT_BYTES = 65_536


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def install_hierarchical_memory() -> None:
    block_type = harness.parent.core.RelativeBlock
    faithful_forward = block_type.forward

    def hierarchical_forward(
        self: object,
        value: torch.Tensor,
        memory: torch.Tensor,
        shared_relative_bias: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        output, faithful_next = faithful_forward(
            self, value, memory, shared_relative_bias
        )
        if memory.shape[1] != 256 or faithful_next.shape[1] != 256:
            raise ValueError("hierarchical child requires frozen 256-slot memory")
        retained_summaries = memory[:, 16:SUMMARY_SLOTS, :]
        newly_evicted = memory[:, SUMMARY_SLOTS:128, :]
        new_summaries = newly_evicted.reshape(
            memory.shape[0], 16, SUMMARY_WIDTH, memory.shape[2]
        ).float().mean(dim=2).to(memory.dtype)
        recent_exact = faithful_next[:, -EXACT_SLOTS:, :]
        next_memory = torch.cat(
            (retained_summaries, new_summaries, recent_exact), dim=1
        )
        if next_memory.shape != memory.shape:
            raise ValueError("hierarchical memory shape changed")
        return output, next_memory

    block_type.forward = hierarchical_forward


def main() -> int:
    harness.CANDIDATE_ID = CANDIDATE_ID
    harness.install_ema_memory = install_hierarchical_memory
    status = harness.main()

    output_dir = ROOT / "results" / CANDIDATE_ID
    if "--output-dir" in sys.argv:
        output_dir = Path(sys.argv[sys.argv.index("--output-dir") + 1]).resolve()
    decision_path = output_dir / "decision.json"
    decision = json.loads(decision_path.read_text())
    comparison = decision.pop("ema_comparison")
    decision.pop("ema_memory")

    source_paths = (
        Path(__file__),
        ROOT / "tools/nncp_evicted_ema_memory_qm0.py",
        ROOT / "docs/nncp_hierarchical_448_memory_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)
    comparison["incremental_source_package_bytes"] = len(source_package)

    failed = [
        condition
        for condition in decision["failed_conditions"]
        if condition != "incremental_source_exceeds_65536"
    ]
    if len(source_package) > SOURCE_LIMIT_BYTES:
        failed.append("incremental_source_exceeds_65536")
    promotion = not failed
    decision.update(
        {
            "schema": "enwiki9_nncp_hierarchical_448_memory_qm0_v1",
            "candidate_id": CANDIDATE_ID,
            "status": "AUTHORIZED_MATURE_HIERARCHY" if promotion else "REJECT",
            "verdict": (
                "authorize_mature_hierarchical_memory"
                if promotion
                else "retire_hierarchical_448_memory"
            ),
            "hierarchical_memory": {
                "summary_slots_per_layer_stream": SUMMARY_SLOTS,
                "states_per_summary": SUMMARY_WIDTH,
                "exact_recent_slots_per_layer_stream": EXACT_SLOTS,
                "nominal_causal_positions_covered": (
                    SUMMARY_SLOTS * SUMMARY_WIDTH + EXACT_SLOTS
                ),
                "summary_update": (
                    "retain newest 48 summaries; append sixteen means of the "
                    "64 exact states leaving the 192-state recent window"
                ),
                "parameter_delta": 0,
                "resident_memory_shape_delta": 0,
            },
            "hierarchical_comparison": comparison,
            "failed_conditions": failed,
            "claim_boundary": (
                "Exact fixed 64x4-summary plus 192-exact hierarchical hidden "
                "memory child at 65,536 symbols. No summary-count, pooling-width, "
                "horizon, published-score, package-forecast, or full-corpus "
                "inheritance."
            ),
        }
    )
    decision["decision"]["promotion_authorized"] = promotion
    decision["inputs"]["hierarchical_driver_script_sha256"] = sha256_file(
        Path(__file__)
    )
    decision["artifacts"] = {
        "incremental_source_package": {
            "path": str(source_path.relative_to(ROOT)),
            "bytes": len(source_package),
            "sha256": sha256_file(source_path),
        }
    }
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "actual_gain_bytes": comparison["actual_gain_bytes"],
                "candidate_archive_bytes": comparison["candidate_archive_bytes"],
                "failed_conditions": failed,
                "ideal_third_gain_bytes": comparison["aligned_ideal"][
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
        print(f"nncp-hierarchical-448-memory-qm0: {error}", file=sys.stderr)
        raise
