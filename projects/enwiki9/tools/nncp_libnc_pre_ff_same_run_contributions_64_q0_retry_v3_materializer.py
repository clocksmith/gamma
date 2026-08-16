#!/usr/bin/env python3
"""Freeze receipt-only finalization of staged same-run attribution."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_pre_ff_same_run_contributions_64_q0_v1 as science
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as fields
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3"
PARENT_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v2"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v2.json"
)
FAILED_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T154402Z_74511ffe59.json"
)
PARENT_RESULT = ROOT / "results" / PARENT_ID
FAILED_GUARD = PARENT_RESULT / "guard.json"
FAILED_LOG = ROOT / "run_logs/adaptive/20260816T154402Z_74511ffe59.log"
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T154402Z_74511ffe59.json"
)
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
RUNNER = ROOT / (
    "tools/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3.py"
)
MATERIALIZER = Path(__file__).resolve()
SOURCE_INPUT = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden.bf16"
)
SOURCE_TOTAL = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden-adjoint.bf16"
)
SOURCE_BRANCH = ROOT / (
    "results/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2/"
    "source-pre-ff-norm-branch-adjoint.bf16"
)
STALE_OPEN_DIRECT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
CORRECTED_OPEN_DIRECT = ROOT / (
    "results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
PARENT_ARTIFACTS = {
    "same-run-input": PARENT_RESULT / "same-run-pre-ff-input.bf16",
    "same-run-total": PARENT_RESULT / "same-run-pre-ff-total-adjoint.bf16",
    "same-run-branch": PARENT_RESULT / "same-run-pre-ff-branch-adjoint.bf16",
    "same-run-direct": PARENT_RESULT / "same-run-pre-ff-direct-adjoint.bf16",
    "same-run-composed": PARENT_RESULT / "same-run-pre-ff-composed-adjoint.bf16",
}


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    failed_job = json.loads(FAILED_JOB.read_text())
    parent = json.loads(PARENT_EXPERIMENT.read_text())
    parent["experimentId"] = CANDIDATE_ID
    parent["proposalId"] = CANDIDATE_ID
    parent["parent"] = {
        "candidateId": PARENT_ID,
        "revision": failed_job["candidate_revision"],
    }
    parent["hypothesis"] = {
        "claim": (
            "The hash-bound staged measurements and durable tensors prove "
            "that the corrected open direct and exact branch compose to every "
            "sealed source pre-FF total-adjoint word."
        ),
        "falsification": (
            "Any staged-receipt drift, execution inconsistency, durable tensor "
            "mismatch, predicate failure, replay failure, source failure, or "
            "schema failure rejects receipt-only finalization."
        ),
    }
    parent["changedMechanism"] = (
        "Bind the failed receipt-finalization job and all durable staged "
        "artifacts, remove only the forbidden experiment-reference id, "
        "independently recheck durable tensor relations, re-evaluate the "
        "frozen predicates, and publish under a new candidate revision without "
        "source capture or tensor recomputation."
    )
    parent["invariants"].extend([
        "The staged decision, execution receipt, guard, source package, and five durable tensors remain hash-bound.",
        "No staged scientific measurement may be changed; receipt-only checks may only reject inconsistent evidence.",
        "The new result must validate before it is published and must identify its own experiment and candidate revision.",
    ])
    parent["measurements"].extend([
        fields.measurement(
            "stagedDecisionBound", "boolean",
            "The staged parent result has the expected candidate, experiment, and terminal disposition.",
        ),
        fields.measurement(
            "stagedExecutionConsistent", "boolean",
            "Every staged comparison count agrees with the durable execution receipt.",
        ),
        fields.measurement(
            "durableArtifactComparisonsExact", "boolean",
            "All independently repeated durable tensor comparisons have their frozen expected outcomes.",
        ),
        fields.measurement(
            "receiptOnlyReplayIdentical", "boolean",
            "Every copied durable tensor is byte-identical to its parent artifact.",
        ),
        fields.measurement(
            "parentArtifactCount", "artifacts",
            "Durable parent tensor artifacts rebound by the receipt-only retry.",
        ),
    ])
    parent["promotionPredicates"].extend([
        fields.predicate(
            "p-staged-decision", "stagedDecisionBound", "eq", True
        ),
        fields.predicate(
            "p-staged-execution", "stagedExecutionConsistent", "eq", True
        ),
        fields.predicate(
            "p-durable-comparisons", "durableArtifactComparisonsExact",
            "eq", True,
        ),
        fields.predicate(
            "p-receipt-replay", "receiptOnlyReplayIdentical", "eq", True
        ),
        fields.predicate(
            "p-parent-artifacts", "parentArtifactCount", "eq", 5
        ),
    ])
    parent["killPredicates"].extend([
        fields.predicate(
            "k-staged-decision", "stagedDecisionBound", "eq", False
        ),
        fields.predicate(
            "k-durable-comparisons", "durableArtifactComparisonsExact",
            "eq", False,
        ),
    ])
    parent["budget"] = {
        "expectedGrossSavingsBytes": 0,
        "maximumAddedPackageBytes": 500_000,
        "expectedNetSavingsBytes": -500_000,
    }
    parent["search"]["expectedRuntimeRatio"] = 0.001
    parent["search"]["expectedMemoryRatio"] = 0.01
    parent["search"]["uncertaintyRisk"] = 0.01

    additions = (
        ("parent-experiment", PARENT_EXPERIMENT),
        ("failed-job", FAILED_JOB),
        ("failed-guard", FAILED_GUARD),
        ("failed-log", FAILED_LOG),
        ("failed-reflection", FAILED_REFLECTION),
        ("staged-decision", PARENT_RESULT / "decision.staged.json"),
        ("parent-execution", PARENT_RESULT / "execution.json"),
        ("parent-source-package", PARENT_RESULT / "incremental_source.tar.xz"),
        ("source-input", SOURCE_INPUT),
        ("source-total", SOURCE_TOTAL),
        ("source-branch", SOURCE_BRANCH),
        ("stale-open-direct", STALE_OPEN_DIRECT),
        ("corrected-open-direct", CORRECTED_OPEN_DIRECT),
        *((identifier, path) for identifier, path in PARENT_ARTIFACTS.items()),
        ("runner", RUNNER),
        ("materializer", MATERIALIZER),
        ("program-descriptor", DESCRIPTOR),
    )
    inputs = {
        path.relative_to(ROOT).as_posix(): science.reference(path, identifier)
        for identifier, path in additions
    }
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in inputs:
            inputs[relative] = science.reference(
                path, fields.source_identifier(path)
            )
    parent["inputs"] = list(inputs.values())
    parent["outputs"] = [
        path.replace(PARENT_ID, CANDIDATE_ID)
        for path in parent["outputs"]
    ]
    parent["generatedUtc"] = (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )
    OUTPUT.write_text(json.dumps(parent, indent=2, sort_keys=True) + "\n")
    try:
        research_contracts.validate_artifact(OUTPUT)
    except Exception:
        OUTPUT.unlink(missing_ok=True)
        raise
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
