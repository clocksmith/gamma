#!/usr/bin/env python3
"""Freeze the exact pre-FF RMSNorm output-order attribution."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1"
PARENT_ID = "nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_open_top_pre_ff_rmsnorm_output_order_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
TREATMENT_MATERIALIZER = PROGRAM / "materialize_output_order.py"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T142138Z_ac31397e1d.json"
)
STATE_ID = "nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1"
STATE_RESULT = ROOT / "results" / STATE_ID
STATE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T133105Z_4b045b57ce.json"
)
STATE_MATERIALIZER = ROOT / (
    "programs/nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1/"
    "materialize_pre_ff_backward.py"
)
BASE_BACKWARD = ROOT / (
    "programs/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/"
    "final_norm_backward.cpp"
)
FF1_RESULT = ROOT / "results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1"
DIRECT_ADJOINT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture"
RMS_ORDER = ROOT / "results/nncp_v33_libnc_rmsnorm_backward_order_parity_v1/decision.json"
SOURCE_CEILING = 2_000_000


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent_revision = ROOT / json.loads(
        (PARENT_RESULT / "decision.json").read_text()
    )["candidateRevision"]["receipt"]["path"]
    inputs = [
        base.reference(STATE_RESULT / "decision.json", "state-decision"),
        base.reference(STATE_RESULT / "execution.json", "state-execution"),
        base.reference(STATE_RESULT / "guard.json", "state-guard"),
        base.reference(STATE_REFLECTION, "state-reflection"),
        base.reference(PARENT_RESULT / "decision.json", "branch-oracle-decision"),
        base.reference(PARENT_RESULT / "execution.json", "branch-oracle-execution"),
        base.reference(PARENT_RESULT / "guard.json", "branch-oracle-guard"),
        base.reference(PARENT_REFLECTION, "branch-oracle-reflection"),
        base.reference(
            PARENT_RESULT / "source-pre-ff-norm-input.bf16",
            "sealed-pre-ff-input",
        ),
        base.reference(
            PARENT_RESULT / "source-pre-ff-norm-branch-adjoint.bf16",
            "sealed-pre-ff-branch-adjoint",
        ),
        base.reference(
            FF1_RESULT / "source-exact-ff1-input-adjoint.bf16",
            "normalized-adjoint",
        ),
        base.reference(DIRECT_ADJOINT, "direct-adjoint"),
        base.reference(FIXTURE / "parameters_initial.coefs", "initial-parameters"),
        base.reference(
            FIXTURE / "gradients/0003_ln_g_39.bin", "retained-gain-gradient"
        ),
        base.reference(
            FIXTURE / "gradients/0004_ln_b_39.bin", "retained-bias-gradient"
        ),
        base.reference(RMS_ORDER, "rms-output-order-lemma"),
        base.reference(BASE_BACKWARD, "base-backward-source"),
        base.reference(STATE_MATERIALIZER, "state-backward-materializer"),
        base.reference(TREATMENT_MATERIALIZER, "output-order-materializer"),
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
                "Removing the LayerNorm-only mean-upstream term and using "
                "LibNC's output-order RMSNorm backward reproduces every sealed "
                "branch-adjoint word."
            ),
            "falsification": (
                "Any treatment mismatch, affine-gradient regression, exact "
                "baseline or negated control, replay difference, dependency "
                "violation, source failure, or resource failure rejects this "
                "operation order."
            ),
        },
        "changedMechanism": (
            "Change only the normalization input-adjoint formula from the "
            "LayerNorm-style mean-upstream subtraction to the previously "
            "measured LibNC RMSNorm output order: inverse times upstream minus "
            "normalized output times mean upstream-output product."
        ),
        "invariants": [
            "The sealed pre-FF input, normalized adjoint, gain, exact affine state reductions, comparator population, and BF16 output conversion remain hash-bound.",
            "The treatment is generated twice before either output is compared with the source branch oracle.",
            "The current open branch artifact remains the fixed non-exact baseline and is not regenerated or altered.",
            "No LibNC, GGML, BLAS, OpenMP, CUDA, teacher executable, or captured source tensor enters the open implementation.",
            "This arithmetic attribution has zero compression, forecast, package, or Hutter score credit.",
        ],
        "controls": [
            {
                "id": "rms-output-order",
                "role": "treatment",
                "definition": "Omit mean(upstream) and compute inverse*(upstream-output*mean(upstream*output)).",
            },
            {
                "id": "layernorm-mean-upstream-baseline",
                "role": "comparator",
                "definition": "Retain the sealed mismatch count from the current mean-upstream-subtracting implementation.",
            },
            {
                "id": "retained-affine-gradients",
                "role": "shifted",
                "definition": "Require the already exact ln_g_39 and ln_b_39 gradients to remain exact.",
            },
            {
                "id": "negated-normalized-adjoint",
                "role": "negative",
                "definition": "Negate the complete normalized adjoint and require its branch output to differ from the source oracle.",
            },
            {
                "id": "independent-replay",
                "role": "replay",
                "definition": "Run the complete output-order executable twice and require every output to reproduce byte-for-byte.",
            },
        ],
        "causalBoundary": {
            "availableInformation": [
                "The sealed input, normalized adjoint, source branch oracle, current baseline mismatch, exact affine gradients, and prior direct LibNC output-order lemma."
            ],
            "forbiddenInformation": [
                "Coordinate corrections, tolerance, fitted constants, alternate epsilons, shape sweeps, teacher execution, future symbols, or objective credit."
            ],
        },
        "population": {
            "unit": "BF16 layer-19 pre-FF normalization-branch adjoint words",
            "scopeBytes": 4_194_304,
            "scopeSymbols": 2_097_152,
            "selection": "Every one of 1,024 features for all 64 chronological states and 32 streams at production block 256.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "measurements": [
            base.measurement("antecedentsPass", "boolean", "All branch-oracle, baseline, affine, and operation-order antecedents remain bound."),
            base.measurement("elementCount", "BF16 elements", "Complete branch-adjoint population."),
            base.measurement("baselineMismatchCount", "BF16 elements", "Current mean-upstream baseline mismatches."),
            base.measurement("treatmentMismatchCount", "BF16 elements", "Output-order treatment mismatches."),
            base.measurement("maximumTreatmentAbsoluteError", "float32 value", "Maximum output-order treatment error."),
            base.measurement("gainGradientMismatchCount", "BF16 elements", "Retained gain-gradient mismatches."),
            base.measurement("biasGradientMismatchCount", "BF16 elements", "Retained bias-gradient mismatches."),
            base.measurement("negatedControlMismatchCount", "BF16 elements", "Negated-adjoint control mismatches."),
            base.measurement("evaluationReplayIdentical", "boolean", "Both treatment evaluations reproduce byte-for-byte."),
            base.measurement("forbiddenDynamicDependencyCount", "dependencies", "Forbidden runtime dependencies."),
            base.measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed source."),
            base.measurement("guardedWorkRootPass", "boolean", "Transient work was removed."),
        ],
        "promotionPredicates": [
            base.predicate("p-antecedents", "antecedentsPass", "eq", True),
            base.predicate("p-elements", "elementCount", "eq", 2_097_152),
            base.predicate("p-baseline", "baselineMismatchCount", "gt", 0),
            base.predicate("p-treatment", "treatmentMismatchCount", "eq", 0),
            base.predicate("p-treatment-maximum", "maximumTreatmentAbsoluteError", "eq", 0.0),
            base.predicate("p-gain", "gainGradientMismatchCount", "eq", 0),
            base.predicate("p-bias", "biasGradientMismatchCount", "eq", 0),
            base.predicate("p-negated", "negatedControlMismatchCount", "gt", 0),
            base.predicate("p-replay", "evaluationReplayIdentical", "eq", True),
            base.predicate("p-dependencies", "forbiddenDynamicDependencyCount", "eq", 0),
            base.predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
            base.predicate("p-work", "guardedWorkRootPass", "eq", True),
        ],
        "killPredicates": [
            base.predicate("k-antecedents", "antecedentsPass", "eq", True),
            base.predicate("k-treatment", "treatmentMismatchCount", "gt", 0),
        ],
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 0.01,
            "expectedMemoryRatio": 0.1,
            "uncertaintyRisk": 0.05,
            "interactionRisk": 0.02,
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/open-pre-ff-rms-output-order-adjoint.bf16",
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
