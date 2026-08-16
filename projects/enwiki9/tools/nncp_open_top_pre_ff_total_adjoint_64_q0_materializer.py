#!/usr/bin/env python3
"""Freeze exact pre-FF total-adjoint composition."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_total_adjoint_64_q0_v1"
PARENT_ID = "nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_open_top_pre_ff_total_adjoint_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
MERGER = PROGRAM / "merge_bf16.cpp"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T142835Z_50298bd574.json"
)
DIRECT_ADJOINT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
SOURCE_TOTAL = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden-adjoint.bf16"
)
SOURCE_CEILING = 1_000_000


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent_revision = ROOT / json.loads(
        (PARENT_RESULT / "decision.json").read_text()
    )["candidateRevision"]["receipt"]["path"]
    inputs = [
        base.reference(PARENT_RESULT / "decision.json", "parent-decision"),
        base.reference(PARENT_RESULT / "execution.json", "parent-execution"),
        base.reference(PARENT_RESULT / "guard.json", "parent-guard"),
        base.reference(PARENT_REFLECTION, "parent-reflection"),
        base.reference(
            PARENT_RESULT / "open-pre-ff-rms-output-order-adjoint.bf16",
            "exact-branch-adjoint",
        ),
        base.reference(DIRECT_ADJOINT, "exact-direct-adjoint"),
        base.reference(SOURCE_TOTAL, "source-total-adjoint"),
        base.reference(MERGER, "merger-source"),
        base.reference(RUNNER, "runner"),
        base.reference(MATERIALIZER, "materializer"),
        base.reference(DESCRIPTOR, "program-descriptor"),
    ]
    present_paths = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            inputs.append(base.reference(path, base.source_identifier(path)))
            present_paths.add(relative)
    experiment = {
        "schema": "gamma.enwiki9.adaptive-experiment-contract.v1",
        "objective": research_contracts.objective_binding(),
        "experimentId": CANDIDATE_ID,
        "proposalId": CANDIDATE_ID,
        "status": "frozen",
        "registrationTiming": "prospective",
        "evidenceClass": "oracle",
        "objectiveCreditBytes": 0,
        "parent": {
            "candidateId": PARENT_ID,
            "revision": {
                key: value
                for key, value in base.reference(
                    parent_revision, "parent-revision"
                ).items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": (
                "BF16 addition of the exact open RMSNorm branch adjoint and "
                "exact direct residual reproduces every source pre-FF total-"
                "adjoint word."
            ),
            "falsification": (
                "Any total-adjoint mismatch, dead negated control, replay "
                "difference, dependency violation, source failure, or resource "
                "failure rejects the residual composition."
            ),
        },
        "changedMechanism": (
            "Compose the two already exact BF16 branch populations with one "
            "F32 addition followed by round-to-nearest-even BF16, matching the "
            "production residual-add boundary."
        ),
        "invariants": [
            "The exact open RMSNorm branch, exact direct residual, source total oracle, geometry, and BF16 conversion remain hash-bound.",
            "Both complete compositions exist before comparison with the source total oracle.",
            "No normalization, gradient reduction, coordinate correction, tolerance, fitted constant, or teacher path is changed.",
            "The executable has no LibNC, GGML, BLAS, OpenMP, or CUDA dependency.",
            "This zero-credit composition is a regression boundary, not compression or Hutter score evidence.",
        ],
        "controls": [
            {
                "id": "exact-branch-addition",
                "role": "treatment",
                "definition": "Add exact RMSNorm branch and direct residual values, then round the sum once to BF16.",
            },
            {
                "id": "source-total-oracle",
                "role": "comparator",
                "definition": "Compare the complete materialized total with the sealed source pre-FF total adjoint.",
            },
            {
                "id": "negated-branch",
                "role": "negative",
                "definition": "Subtract the exact RMSNorm branch from the same direct residual and require a non-exact result.",
            },
            {
                "id": "independent-replay",
                "role": "replay",
                "definition": "Materialize treatment and control twice and require byte identity.",
            },
        ],
        "causalBoundary": {
            "availableInformation": [
                "The sealed exact branch and direct adjoints, source total oracle, and prior conversion-order rejection."
            ],
            "forbiddenInformation": [
                "Unrounded branch intermediates, tolerance, coordinate fitting, teacher execution, future symbols, or objective credit."
            ],
        },
        "population": {
            "unit": "BF16 layer-19 pre-FF total-adjoint words",
            "scopeBytes": 4_194_304,
            "scopeSymbols": 2_097_152,
            "selection": "Every one of 1,024 features for all 64 chronological states and 32 streams at production block 256.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "measurements": [
            base.measurement("antecedentsPass", "boolean", "All exact branch and composition antecedents remain bound."),
            base.measurement("elementCount", "BF16 elements", "Complete pre-FF total-adjoint population."),
            base.measurement("totalAdjointMismatchCount", "BF16 elements", "Treatment versus source total mismatches."),
            base.measurement("maximumTotalAdjointAbsoluteError", "float32 value", "Maximum treatment error."),
            base.measurement("negatedControlMismatchCount", "BF16 elements", "Negated-branch control mismatches."),
            base.measurement("evaluationReplayIdentical", "boolean", "Both compositions reproduce byte-for-byte."),
            base.measurement("forbiddenDynamicDependencyCount", "dependencies", "Forbidden runtime dependencies."),
            base.measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed source."),
            base.measurement("guardedWorkRootPass", "boolean", "Transient work was removed."),
        ],
        "promotionPredicates": [
            base.predicate("p-antecedents", "antecedentsPass", "eq", True),
            base.predicate("p-elements", "elementCount", "eq", 2_097_152),
            base.predicate("p-total", "totalAdjointMismatchCount", "eq", 0),
            base.predicate("p-maximum", "maximumTotalAdjointAbsoluteError", "eq", 0.0),
            base.predicate("p-control", "negatedControlMismatchCount", "gt", 0),
            base.predicate("p-replay", "evaluationReplayIdentical", "eq", True),
            base.predicate("p-dependencies", "forbiddenDynamicDependencyCount", "eq", 0),
            base.predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
            base.predicate("p-work", "guardedWorkRootPass", "eq", True),
        ],
        "killPredicates": [
            base.predicate("k-antecedents", "antecedentsPass", "eq", True),
            base.predicate("k-total", "totalAdjointMismatchCount", "gt", 0),
        ],
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 0.001,
            "expectedMemoryRatio": 0.01,
            "uncertaintyRisk": 0.01,
            "interactionRisk": 0.01,
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-exact-pre-ff-total-adjoint.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "outputManifestPolicy": "complete-result-artifacts-v1",
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
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
