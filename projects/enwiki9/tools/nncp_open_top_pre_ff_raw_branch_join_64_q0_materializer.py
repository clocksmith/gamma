#!/usr/bin/env python3
"""Freeze the raw RMSNorm branch residual-join attribution."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_raw_branch_join_64_q0_v1"
PARENT_ID = "nncp_open_top_pre_ff_total_adjoint_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_open_top_pre_ff_raw_branch_join_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
RAW_JOIN_MATERIALIZER = PROGRAM / "materialize_raw_join.py"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T143328Z_5fb15662ea.json"
)
EXACT_RESULT = ROOT / (
    "results/nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1"
)
EXACT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T142835Z_50298bd574.json"
)
BASE_SOURCE = ROOT / (
    "programs/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/"
    "final_norm_backward.cpp"
)
STATE_MATERIALIZER = ROOT / (
    "programs/nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1/"
    "materialize_pre_ff_backward.py"
)
OUTPUT_ORDER_MATERIALIZER = ROOT / (
    "programs/nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1/"
    "materialize_output_order.py"
)
ORACLE_RESULT = ROOT / (
    "results/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2"
)
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture"
PARAMETERS = FIXTURE / "parameters_initial.coefs"
SEALED_INPUT = ORACLE_RESULT / "source-pre-ff-norm-input.bf16"
NORMALIZED_ADJOINT = ROOT / (
    "results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/"
    "source-exact-ff1-input-adjoint.bf16"
)
DIRECT_ADJOINT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
GAIN = FIXTURE / "gradients/0003_ln_g_39.bin"
BIAS = FIXTURE / "gradients/0004_ln_b_39.bin"
SEALED_BRANCH = ORACLE_RESULT / "source-pre-ff-norm-branch-adjoint.bf16"
SOURCE_TOTAL = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden-adjoint.bf16"
)
SOURCE_CEILING = 2_000_000


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
        ("exact-branch-decision", EXACT_RESULT / "decision.json"),
        ("exact-branch-reflection", EXACT_REFLECTION),
        ("base-backward-source", BASE_SOURCE),
        ("state-materializer", STATE_MATERIALIZER),
        ("output-order-materializer", OUTPUT_ORDER_MATERIALIZER),
        ("raw-join-materializer", RAW_JOIN_MATERIALIZER),
        ("initial-parameters", PARAMETERS),
        ("sealed-pre-ff-input", SEALED_INPUT),
        ("normalized-adjoint", NORMALIZED_ADJOINT),
        ("exact-direct-adjoint", DIRECT_ADJOINT),
        ("retained-gain-gradient", GAIN),
        ("retained-bias-gradient", BIAS),
        ("sealed-branch-adjoint", SEALED_BRANCH),
        ("source-total-adjoint", SOURCE_TOTAL),
        ("runner", RUNNER),
        ("materializer", MATERIALIZER),
        ("program-descriptor", DESCRIPTOR),
    )
    inputs = [base.reference(path, identifier) for identifier, path in bound]
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
                "Retaining the exact RMSNorm input-adjoint branch in F32 "
                "until the residual join reproduces both the separately "
                "rounded branch oracle and every source total-adjoint word."
            ),
            "falsification": (
                "Any branch, total, gain, or bias mismatch, dead negative "
                "control, replay difference, dependency violation, source "
                "failure, or resource failure rejects the conversion boundary."
            ),
        },
        "changedMechanism": (
            "Remove only the per-coordinate BF16 conversion immediately after "
            "the exact RMSNorm formula; preserve that conversion for the branch "
            "oracle and affine bookkeeping, but let the live residual join add "
            "the raw F32 branch to the unchanged BF16 direct residual before "
            "the existing round-to-nearest-even BF16 output conversion."
        ),
        "invariants": [
            "The exact output-order RMSNorm formula, state-wise affine reductions, inputs, parameters, direct residual, branch oracle, and source total remain hash-bound.",
            "Both complete treatment populations exist before either source comparator is read.",
            "No coordinate correction, tolerance, fitted constant, teacher execution, or gradient schedule changes.",
            "The executable has no LibNC, GGML, BLAS, OpenMP, or CUDA dependency.",
            "This zero-credit arithmetic attribution is not compression or Hutter score evidence.",
        ],
        "controls": [
            {
                "id": "raw-branch-join",
                "role": "treatment",
                "definition": "Retain the exact RMSNorm branch in F32 through the unchanged direct residual addition, then convert the total once to BF16.",
            },
            {
                "id": "separate-branch-oracle",
                "role": "comparator",
                "definition": "Round the same raw branch only at output and require exact parity with the sealed source branch probe.",
            },
            {
                "id": "source-total-oracle",
                "role": "comparator",
                "definition": "Compare the complete raw-join treatment with the sealed source pre-FF total adjoint.",
            },
            {
                "id": "negated-raw-branch",
                "role": "negative",
                "definition": "Negate the incoming adjoint before the same RMSNorm and residual-join schedule and require a non-exact total.",
            },
            {
                "id": "independent-replay",
                "role": "replay",
                "definition": "Materialize all treatment and control outputs twice and require byte identity.",
            },
        ],
        "causalBoundary": {
            "availableInformation": [
                "Sealed inputs, parameters, exact normalized adjoint, direct residual, branch oracle, source total oracle, exact RMSNorm formula, and the three-mismatch parent receipt."
            ],
            "forbiddenInformation": [
                "Coordinate-specific corrections, comparator-derived values, tolerance, teacher execution, future symbols, or objective credit."
            ],
        },
        "population": {
            "unit": "BF16 layer-19 pre-FF branch and total-adjoint words",
            "scopeBytes": 4_194_304,
            "scopeSymbols": 2_097_152,
            "selection": "Every one of 1,024 features for all 64 chronological states and 32 streams at production block 256.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "measurements": [
            base.measurement("antecedentsPass", "boolean", "All exact arithmetic antecedents remain bound."),
            base.measurement("elementCount", "BF16 elements", "Complete branch and total population size."),
            base.measurement("branchAdjointMismatchCount", "BF16 elements", "Rounded raw branch versus sealed branch mismatches."),
            base.measurement("maximumBranchAdjointAbsoluteError", "float32 value", "Maximum rounded branch error."),
            base.measurement("totalAdjointMismatchCount", "BF16 elements", "Raw-join total versus source total mismatches."),
            base.measurement("maximumTotalAdjointAbsoluteError", "float32 value", "Maximum raw-join total error."),
            base.measurement("gainGradientMismatchCount", "BF16 elements", "Gain-gradient mismatches."),
            base.measurement("biasGradientMismatchCount", "BF16 elements", "Bias-gradient mismatches."),
            base.measurement("negatedControlMismatchCount", "BF16 elements", "Negated raw-branch total mismatches."),
            base.measurement("evaluationReplayIdentical", "boolean", "Both populations reproduce byte-for-byte."),
            base.measurement("forbiddenDynamicDependencyCount", "dependencies", "Forbidden runtime dependencies."),
            base.measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed source."),
            base.measurement("guardedWorkRootPass", "boolean", "Transient work was removed."),
        ],
        "promotionPredicates": [
            base.predicate("p-antecedents", "antecedentsPass", "eq", True),
            base.predicate("p-elements", "elementCount", "eq", 2_097_152),
            base.predicate("p-branch", "branchAdjointMismatchCount", "eq", 0),
            base.predicate("p-branch-maximum", "maximumBranchAdjointAbsoluteError", "eq", 0.0),
            base.predicate("p-total", "totalAdjointMismatchCount", "eq", 0),
            base.predicate("p-total-maximum", "maximumTotalAdjointAbsoluteError", "eq", 0.0),
            base.predicate("p-gain", "gainGradientMismatchCount", "eq", 0),
            base.predicate("p-bias", "biasGradientMismatchCount", "eq", 0),
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
