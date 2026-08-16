#!/usr/bin/env python3
"""Freeze corrected exact open pre-FF total-adjoint composition."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as fields
import nncp_open_top_pre_ff_total_adjoint_64_q0 as parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1"
PARENT_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
BASE_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_open_top_pre_ff_total_adjoint_64_q0_v1.json"
)
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T155008Z_4831e25438.json"
)
FAILED_TOTAL_RESULT = ROOT / "results/nncp_open_top_pre_ff_total_adjoint_64_q0_v1"
FAILED_TOTAL_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T143328Z_5fb15662ea.json"
)
BRANCH_RESULT = ROOT / "results/nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1"
BRANCH_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T142835Z_50298bd574.json"
)
DIRECT_RESULT = ROOT / (
    "results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2"
)
DIRECT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T082228Z_f0bff9b6df.json"
)
BRANCH_ADJOINT = BRANCH_RESULT / "open-pre-ff-rms-output-order-adjoint.bf16"
DIRECT_ADJOINT = DIRECT_RESULT / "open-final-norm-input-residual.bf16"
SOURCE_TOTAL = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden-adjoint.bf16"
)
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
RUNNER = ROOT / "tools/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1.py"
MATERIALIZER = Path(__file__).resolve()


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    experiment = json.loads(BASE_EXPERIMENT.read_text())
    parent_decision = json.loads((PARENT_RESULT / "decision.json").read_text())
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    experiment["parent"] = {
        "candidateId": PARENT_ID,
        "revision": parent_decision["candidateRevision"]["receipt"],
    }
    experiment["hypothesis"] = {
        "claim": (
            "BF16 addition of the exact output-order RMSNorm branch and "
            "promoted streaming-dot direct residual reproduces every source "
            "pre-FF total-adjoint word."
        ),
        "falsification": (
            "Any source-total mismatch, dead negated control, replay "
            "difference, attribution drift, dependency violation, source "
            "failure, or resource failure rejects the corrected composition."
        ),
    }
    experiment["changedMechanism"] = (
        "Keep the exact branch, one F32 addition, RNE BF16 boundary, full "
        "population, source comparator, replay, control, and limits; replace "
        "only the stale eight-word-inexact direct input with the already "
        "promoted streaming-dot residual and bind its same-run attribution."
    )
    experiment["invariants"].extend([
        "The corrected direct artifact must be promotion-backed and equal the same-run source direct in every word.",
        "The prior three-word failure and its reflection remain bound as historical evidence; they are not relabeled or edited.",
        "No captured teacher tensor is consumed by the treatment; source total remains a post-completion comparator only.",
    ])
    additions = (
        ("attribution-decision", PARENT_RESULT / "decision.json"),
        ("attribution-execution", PARENT_RESULT / "execution.json"),
        ("attribution-guard", PARENT_RESULT / "guard.json"),
        ("attribution-reflection", PARENT_REFLECTION),
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
        ("program-descriptor", DESCRIPTOR),
    )
    inputs = {
        path.relative_to(ROOT).as_posix(): parent.reference(path, identifier)
        for identifier, path in additions
    }
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in inputs:
            inputs[relative] = parent.reference(
                path, fields.source_identifier(path)
            )
    experiment["inputs"] = list(inputs.values())
    experiment["outputs"] = [
        path.replace("nncp_open_top_pre_ff_total_adjoint_64_q0_v1", CANDIDATE_ID)
        for path in experiment["outputs"]
    ]
    experiment["generatedUtc"] = (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    try:
        research_contracts.validate_artifact(OUTPUT)
    except Exception:
        OUTPUT.unlink(missing_ok=True)
        raise
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
