#!/usr/bin/env python3
"""Run the invocation-corrected exact-FF2 top-FF1 projection gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import nncp_open_profile_top_ff1_bias_gradient_64_q0_v1 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
BLOCK_RESULT = ROOT / "results/nncp_libnc_ff2_transpose_block128_64_q0_v1"
BLOCK_DECISION = BLOCK_RESULT / "decision.json"
BLOCK_EXECUTION = BLOCK_RESULT / "execution.json"
BLOCK_GUARD = BLOCK_RESULT / "guard.json"
BLOCK_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T093907Z_7f51e2d346.json"
)
BLOCK_ADJOINT = BLOCK_RESULT / "block128-ff2-input-adjoint.bf16"
SOURCE_RESULT = ROOT / "results/nncp_libnc_top_ff2_input_adjoint_64_q0_v1"
SOURCE_DECISION = SOURCE_RESULT / "decision.json"
SOURCE_ADJOINT = SOURCE_RESULT / "source-ff2-input-adjoint.bf16"
INVOCATION_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T094657Z_e9fe7b3dcc.json"
)


original_require_inputs = parent.require_inputs
original_evaluate = parent.base.evaluate


def require_inputs(experiment: dict[str, Any]) -> None:
    original_require_inputs(experiment)
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("block128-decision", BLOCK_DECISION),
        ("block128-execution", BLOCK_EXECUTION),
        ("block128-guard", BLOCK_GUARD),
        ("block128-reflection", BLOCK_REFLECTION),
        ("block128-ff2-input-adjoint", BLOCK_ADJOINT),
        ("source-ff2-input-adjoint-decision", SOURCE_DECISION),
        ("source-ff2-input-adjoint", SOURCE_ADJOINT),
        ("invocation-failure-reflection", INVOCATION_REFLECTION),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != parent.base.reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    decision = json.loads(BLOCK_DECISION.read_text())
    reflection = json.loads(BLOCK_REFLECTION.read_text())
    guard = json.loads(BLOCK_GUARD.read_text())
    source = json.loads(SOURCE_DECISION.read_text())
    invocation = json.loads(INVOCATION_REFLECTION.read_text())
    if not (
        decision["promotionPass"] is True
        and decision["measurements"]["block128SourceMismatchCount"] == 0
        and decision["measurements"]["maximumBlock128AbsoluteError"] == 0
        and decision["measurements"]["evaluationReplayIdentical"] is True
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "supported"
        and reflection["decision"]["verdict"] == "mutate"
        and guard["returncode"] == 0
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and source["measurements"]["sourceCaptureDeterministic"] is True
        and BLOCK_ADJOINT.read_bytes() == SOURCE_ADJOINT.read_bytes()
        and invocation["validity"]["classification"] == "implementation-failure"
        and invocation["hypothesis"]["verdict"] == "not-tested"
        and invocation["decision"]["verdict"] == "retry"
    ):
        raise ValueError("exact FF2 retry antecedents are not satisfied")


def evaluate(
    predicates: list[dict[str, Any]],
    measurements: dict[str, bool | int | float],
) -> list[dict[str, Any]]:
    if "sourceFf2InputResidualMismatchCount" not in measurements:
        comparison = parent.base.parent.compare_bf16(
            RESULT / "open-ff2-input-residual.bf16", SOURCE_ADJOINT
        )
        measurements["sourceFf2InputResidualMismatchCount"] = comparison[0]
        measurements["maximumSourceFf2InputResidualAbsoluteError"] = comparison[1]
    return original_evaluate(predicates, measurements)


def main() -> int:
    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.PROGRAM = PROGRAM
    parent.RESULT = RESULT
    parent.WORK = RESULT / "work"
    parent.MATERIALIZER = PROGRAM / "materialize_forward.py"
    parent.CMAKE = PROGRAM / "CMakeLists.txt"
    parent.REDUCER = PROGRAM / "top_ff1_bias_gradient.cpp"
    parent.PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
    parent.RUNNER = Path(__file__).resolve()
    parent.FREEZER = ROOT / (
        "tools/nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2_materializer.py"
    )
    parent.require_inputs = require_inputs
    parent.base.evaluate = evaluate
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
