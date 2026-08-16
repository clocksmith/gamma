#!/usr/bin/env python3
"""Freeze the LibNC BF16 shared-gradient merge oracle."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_bf16_gradient_merge_64_q0_v1"
PARENT_ID = "nncp_open_top_pre_ff_raw_branch_join_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_bf16_gradient_merge_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
EVALUATOR = PROGRAM / "gradient_merge.c"
DESCRIPTOR = PROGRAM / "program.py"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T144129Z_cbf5902ca5.json"
)
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
BRANCH = ROOT / (
    "results/nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1/"
    "open-pre-ff-rms-output-order-adjoint.bf16"
)
DIRECT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
SOURCE_TOTAL = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden-adjoint.bf16"
)
SOURCE_CEILING = 500_000


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent_revision = ROOT / json.loads(
        (PARENT_RESULT / "decision.json").read_text()
    )["candidateRevision"]["receipt"]["path"]
    bound = (
        ("parent-decision", PARENT_RESULT / "decision.json"),
        ("parent-execution", PARENT_RESULT / "execution.json"),
        ("parent-guard", PARENT_RESULT / "guard.json"),
        ("parent-reflection", PARENT_REFLECTION),
        ("fixture-decision", FIXTURE_ROOT / "decision.json"),
        ("fixture-manifest", FIXTURE_ROOT / "fixture-manifest.json"),
        ("exact-branch-adjoint", BRANCH),
        ("exact-direct-adjoint", DIRECT),
        ("source-total-adjoint", SOURCE_TOTAL),
        ("evaluator-source", EVALUATOR),
        ("runner", RUNNER),
        ("materializer", MATERIALIZER),
        ("program-descriptor", DESCRIPTOR),
    )
    inputs = [base.reference(path, identifier) for identifier, path in bound]
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(base.reference(path, base.source_identifier(path)))
            present.add(relative)
    measurement = base.measurement
    predicate = base.predicate
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
                "A digest-bound LibNC shared-parameter graph fed the exact "
                "BF16 branch and direct adjoints reproduces the sealed source "
                "pre-FF total and identifies the graph-order merge contract."
            ),
            "falsification": (
                "Failure of either single-branch control or absence of an "
                "exact complete merge variant rejects this primitive graph "
                "as an oracle for the source residual accumulation."
            ),
        },
        "changedMechanism": (
            "Replace standalone C++ float addition with the digest-bound "
            "production LibNC autodiff engine: two coefficient-weighted paths "
            "share one BF16 parameter and deliver the exact sealed adjoints in "
            "both graph orders."
        ),
        "invariants": [
            "The branch, direct, and source-total BF16 populations remain hash-bound and unmodified.",
            "Single-path graphs must reproduce each input adjoint exactly before a two-path merge is interpreted.",
            "Both graph orders, negative control, and replay populations exist before source comparison.",
            "LibNC is a digest-bound zero-credit teacher and cannot enter the submitted codec.",
        ],
        "controls": [
            {"id": "single-branch", "role": "comparator", "definition": "A one-path graph must reproduce the exact RMSNorm branch adjoint."},
            {"id": "single-direct", "role": "comparator", "definition": "A one-path graph must reproduce the exact direct residual adjoint."},
            {"id": "branch-left", "role": "treatment", "definition": "Construct and add the branch loss before the direct loss at one shared BF16 parameter."},
            {"id": "direct-left", "role": "treatment", "definition": "Reverse construction and add order without changing either adjoint."},
            {"id": "negated-branch-left", "role": "negative", "definition": "Sign-negate the branch adjoint before the otherwise identical merge."},
            {"id": "independent-replay", "role": "replay", "definition": "Execute all five graphs twice and require byte identity."},
        ],
        "causalBoundary": {
            "availableInformation": [
                "The complete exact BF16 branch and direct adjoints, source total, production graph topology, and digest-bound LibNC implementation."
            ],
            "forbiddenInformation": [
                "Coordinate-specific repair, tolerance, comparator-derived coefficients, future symbols, or objective credit."
            ],
        },
        "population": {
            "unit": "BF16 pre-FF adjoint elements",
            "scopeBytes": 4_194_304,
            "scopeSymbols": 2_097_152,
            "selection": "Every branch and direct adjoint coordinate from all 64 states, 32 streams, and 1,024 features.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "measurements": [
            measurement("antecedentsPass", "boolean", "The localized parent and source fixture remain valid."),
            measurement("elementCount", "BF16 elements", "Complete merge population."),
            measurement("branchControlMismatchCount", "BF16 elements", "Single branch versus exact branch mismatches."),
            measurement("directControlMismatchCount", "BF16 elements", "Single direct versus exact direct mismatches."),
            measurement("branchLeftMismatchCount", "BF16 elements", "Branch-left merge versus source total mismatches."),
            measurement("directLeftMismatchCount", "BF16 elements", "Direct-left merge versus source total mismatches."),
            measurement("minimumMergeMismatchCount", "BF16 elements", "Best prospectively frozen graph-order mismatch count."),
            measurement("maximumSelectedAbsoluteError", "float32 value", "Maximum best-order error."),
            measurement("exactMergeVariantCount", "variants", "Graph orders with exact source parity."),
            measurement("negatedControlMismatchCount", "BF16 elements", "Negated merge versus source total mismatches."),
            measurement("evaluationReplayIdentical", "boolean", "Both five-graph populations reproduce byte-for-byte."),
            measurement("sourceLibraryDigestBound", "boolean", "Execution used the attributed production LibNC library."),
            measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed source."),
            measurement("guardedWorkRootPass", "boolean", "Transient work was removed."),
        ],
        "promotionPredicates": [
            predicate("p-antecedents", "antecedentsPass", "eq", True),
            predicate("p-elements", "elementCount", "eq", 2_097_152),
            predicate("p-branch", "branchControlMismatchCount", "eq", 0),
            predicate("p-direct", "directControlMismatchCount", "eq", 0),
            predicate("p-merge", "minimumMergeMismatchCount", "eq", 0),
            predicate("p-maximum", "maximumSelectedAbsoluteError", "eq", 0.0),
            predicate("p-exact", "exactMergeVariantCount", "gt", 0),
            predicate("p-control", "negatedControlMismatchCount", "gt", 0),
            predicate("p-replay", "evaluationReplayIdentical", "eq", True),
            predicate("p-library", "sourceLibraryDigestBound", "eq", True),
            predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
            predicate("p-work", "guardedWorkRootPass", "eq", True),
        ],
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-merge", "minimumMergeMismatchCount", "gt", 0),
        ],
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 0.0,
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 0.01,
            "uncertaintyRisk": 0.1,
            "interactionRisk": 0.1,
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/libnc-gradient-merge-treatment.bf16",
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
