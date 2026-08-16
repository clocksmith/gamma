#!/usr/bin/env python3
"""Run the state-reduced layer-19 pre-FF backward replay."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import nncp_open_top_pre_ff_rmsnorm_backward_64_q0 as implementation


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / (
    "tools/nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_materializer.py"
)
FAILED_ID = "nncp_open_top_pre_ff_rmsnorm_backward_64_q0_v1"
FAILED_RESULT = ROOT / "results" / FAILED_ID
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T130752Z_2641246e8c.json"
)
DIRECT_ADJOINT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
BACKWARD_MATERIALIZER = PROGRAM / "materialize_pre_ff_backward.py"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"


parent_require_inputs = implementation.require_inputs


def require_inputs(experiment: dict[str, Any]) -> None:
    parent_require_inputs(experiment)
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("failed-decision", FAILED_RESULT / "decision.json"),
        ("failed-execution", FAILED_RESULT / "execution.json"),
        ("failed-guard", FAILED_RESULT / "guard.json"),
        ("failed-reflection", FAILED_REFLECTION),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != implementation.reference(path, identifier):
            raise ValueError(f"state-reduced experiment input drifted: {identifier}")
    failed = json.loads((FAILED_RESULT / "decision.json").read_text())
    reflection = json.loads(FAILED_REFLECTION.read_text())
    if not (
        failed["promotionPass"] is False
        and failed["killPass"] is True
        and failed["measurements"]["hiddenSourceMismatchCount"] == 0
        and failed["measurements"]["normalizedInputMismatchCount"] == 0
        and failed["measurements"]["totalAdjointMismatchCount"] > 0
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "refuted"
        and reflection["decision"]["verdict"] == "mutate"
    ):
        raise ValueError("state-reduced retry antecedents are not satisfied")


implementation.CANDIDATE_ID = CANDIDATE_ID
implementation.PROGRAM = PROGRAM
implementation.RESULT = RESULT
implementation.WORK = RESULT / "work"
implementation.RUNNER = RUNNER
implementation.FREEZER = FREEZER
implementation.DIRECT_ADJOINT = DIRECT_ADJOINT
implementation.BACKWARD_MATERIALIZER = BACKWARD_MATERIALIZER
implementation.PROGRAM_DESCRIPTOR = PROGRAM_DESCRIPTOR
implementation.require_inputs = require_inputs


if __name__ == "__main__":
    raise SystemExit(implementation.main())
