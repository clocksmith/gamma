#!/usr/bin/env python3
"""Compose exact pre-FF total adjoint with the corrected direct residual."""

from __future__ import annotations

import json
import os
from pathlib import Path

import nncp_open_top_pre_ff_total_adjoint_64_q0 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1"
ATTRIBUTION_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3"
ATTRIBUTION_RESULT = ROOT / "results" / ATTRIBUTION_ID
ATTRIBUTION_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T155008Z_4831e25438.json"
)
FAILED_TOTAL_ID = "nncp_open_top_pre_ff_total_adjoint_64_q0_v1"
FAILED_TOTAL_RESULT = ROOT / "results" / FAILED_TOTAL_ID
FAILED_TOTAL_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T143328Z_5fb15662ea.json"
)
BRANCH_ID = "nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1"
BRANCH_RESULT = ROOT / "results" / BRANCH_ID
BRANCH_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T142835Z_50298bd574.json"
)
DIRECT_ID = "nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2"
DIRECT_RESULT = ROOT / "results" / DIRECT_ID
DIRECT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T082228Z_f0bff9b6df.json"
)
BRANCH_ADJOINT = BRANCH_RESULT / "open-pre-ff-rms-output-order-adjoint.bf16"
DIRECT_ADJOINT = DIRECT_RESULT / "open-final-norm-input-residual.bf16"
SOURCE_TOTAL = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden-adjoint.bf16"
)
RESULT = ROOT / "results" / CANDIDATE_ID
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1_materializer.py"
)


def require_inputs(experiment: dict[str, object]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("attribution-decision", ATTRIBUTION_RESULT / "decision.json"),
        ("attribution-execution", ATTRIBUTION_RESULT / "execution.json"),
        ("attribution-guard", ATTRIBUTION_RESULT / "guard.json"),
        ("attribution-reflection", ATTRIBUTION_REFLECTION),
        ("failed-total-decision", FAILED_TOTAL_RESULT / "decision.json"),
        ("failed-total-execution", FAILED_TOTAL_RESULT / "execution.json"),
        ("failed-total-guard", FAILED_TOTAL_RESULT / "guard.json"),
        ("failed-total-reflection", FAILED_TOTAL_REFLECTION),
        ("branch-decision", BRANCH_RESULT / "decision.json"),
        ("branch-execution", BRANCH_RESULT / "execution.json"),
        ("branch-guard", BRANCH_RESULT / "guard.json"),
        ("branch-reflection", BRANCH_REFLECTION),
        ("exact-branch-adjoint", BRANCH_ADJOINT),
        ("direct-decision", DIRECT_RESULT / "decision.json"),
        ("direct-execution", DIRECT_RESULT / "execution.json"),
        ("direct-guard", DIRECT_RESULT / "guard.json"),
        ("direct-reflection", DIRECT_REFLECTION),
        ("exact-direct-adjoint", DIRECT_ADJOINT),
        ("source-total-adjoint", SOURCE_TOTAL),
        ("merger-source", parent.MERGER_SOURCE),
        ("runner", RUNNER),
        ("materializer", MATERIALIZER),
        ("program-descriptor", PROGRAM / "program.py"),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != parent.reference(path, identifier):
            raise ValueError(f"corrected total input drifted: {identifier}")
    attribution = json.loads(
        (ATTRIBUTION_RESULT / "decision.json").read_text()
    )
    attribution_reflection = json.loads(ATTRIBUTION_REFLECTION.read_text())
    failed = json.loads((FAILED_TOTAL_RESULT / "decision.json").read_text())
    failed_reflection = json.loads(FAILED_TOTAL_REFLECTION.read_text())
    branch = json.loads((BRANCH_RESULT / "decision.json").read_text())
    branch_reflection = json.loads(BRANCH_REFLECTION.read_text())
    direct = json.loads((DIRECT_RESULT / "decision.json").read_text())
    direct_reflection = json.loads(DIRECT_REFLECTION.read_text())
    if not (
        attribution["promotionPass"] is True
        and attribution["measurements"]["openDirectMismatchCount"] == 8
        and attribution["measurements"][
            "correctedOpenDirectMismatchCount"
        ] == 0
        and attribution["measurements"]["composedTotalMismatchCount"] == 0
        and attribution_reflection["validity"]["valid"] is True
        and attribution_reflection["hypothesis"]["verdict"] == "supported"
        and attribution_reflection["decision"]["verdict"] == "mutate"
        and failed["promotionPass"] is False
        and failed["measurements"]["totalAdjointMismatchCount"] == 3
        and failed_reflection["validity"]["valid"] is True
        and failed_reflection["hypothesis"]["verdict"] == "refuted"
        and branch["promotionPass"] is True
        and branch["measurements"]["treatmentMismatchCount"] == 0
        and branch_reflection["validity"]["valid"] is True
        and direct["promotionPass"] is True
        and direct["measurements"][
            "sourceFinalNormResidualMismatchCount"
        ] == 0
        and direct_reflection["validity"]["valid"] is True
    ):
        raise ValueError("corrected total antecedents are not satisfied")


def main() -> int:
    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.PARENT_ID = ATTRIBUTION_ID
    parent.RESULT = RESULT
    parent.WORK = RESULT / "work"
    parent.PROGRAM = PROGRAM
    parent.PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
    parent.RUNNER = RUNNER
    parent.FREEZER = MATERIALIZER
    parent.PARENT_RESULT = ATTRIBUTION_RESULT
    parent.PARENT_DECISION = ATTRIBUTION_RESULT / "decision.json"
    parent.PARENT_EXECUTION = ATTRIBUTION_RESULT / "execution.json"
    parent.PARENT_GUARD = ATTRIBUTION_RESULT / "guard.json"
    parent.PARENT_REFLECTION = ATTRIBUTION_REFLECTION
    parent.BRANCH_ADJOINT = BRANCH_ADJOINT
    parent.DIRECT_ADJOINT = DIRECT_ADJOINT
    parent.SOURCE_TOTAL = SOURCE_TOTAL
    parent.require_inputs = require_inputs
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
