#!/usr/bin/env python3
"""Freeze the layer-19 pre-FF residual conversion-order attribution."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_residual_conversion_order_64_q0_v1"
PARENT_ID = "nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1"
PARENT_EXPERIMENT = ROOT / (
    f"operations/adaptive/experiments/{PARENT_ID}.json"
)
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T133105Z_4b045b57ce.json"
)
RUNNER = ROOT / "tools/nncp_open_top_pre_ff_residual_conversion_order_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
CONVERSION_MATERIALIZER = PROGRAM / "materialize_conversion_probe.py"
DESCRIPTOR = PROGRAM / "program.py"
STATE_MATERIALIZER = ROOT / (
    "programs/nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1/"
    "materialize_pre_ff_backward.py"
)
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    experiment = json.loads(PARENT_EXPERIMENT.read_text())
    parent_decision = json.loads((PARENT_RESULT / "decision.json").read_text())
    parent_revision = ROOT / parent_decision["candidateRevision"]["receipt"][
        "path"
    ]
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    experiment["parent"] = {
        "candidateId": PARENT_ID,
        "revision": {
            "path": parent_revision.relative_to(ROOT).as_posix(),
            "sha256": f"sha256:{base.sha256(parent_revision)}",
        },
    }
    experiment["hypothesis"] = {
        "claim": (
            "Keeping the normalization input residual in F32 through the "
            "residual add and converting the merged result once reproduces "
            "every source total-adjoint word while the preconverted control "
            "does not."
        ),
        "falsification": (
            "Any fused-total mismatch, exact preconverted control, affine-"
            "gradient regression, dead control, replay failure, dependency "
            "violation, or resource failure rejects the conversion boundary."
        ),
    }
    experiment["changedMechanism"] = (
        "Change only the normalization-input residual conversion point: retain "
        "the exact F32 centered result until it is added to the BF16 direct "
        "branch, then convert the merged value once."
    )
    experiment["invariants"] = [
        "The hidden input, normalized adjoint, direct residual, parameters, state-wise affine reduction, and source comparators remain hash-bound.",
        "Both conversion variants are generated twice before either is compared with the source total adjoint.",
        "The treatment changes no coordinate, threshold, fitted constant, or retained affine-gradient arithmetic.",
        "The executable has no LibNC, GGML, BLAS, OpenMP, or CUDA dynamic dependency.",
        "The source oracle is zero-credit validation and cannot ship in a Gamma codec.",
    ]
    experiment["controls"] = [
        {"id": "post-merge-conversion", "role": "treatment", "definition": "Add the raw F32 normalization input residual to the BF16 direct branch, then convert once."},
        {"id": "pre-merge-conversion", "role": "comparator", "definition": "Convert the normalization input residual to BF16 before the same residual add."},
        {"id": "retained-affine-gradients", "role": "shifted", "definition": "Require the already exact ln_g_39 and ln_b_39 gradients to remain exact."},
        {"id": "direct-only", "role": "negative", "definition": "Remove the normalized branch."},
        {"id": "negated-normalized-branch", "role": "negative", "definition": "Negate the normalized branch before the post-merge conversion."},
        {"id": "independent-replay", "role": "replay", "definition": "Materialize every variant twice before source comparison."},
    ]
    experiment["causalBoundary"]["availableInformation"] = [
        "The exact source hidden input, normalized adjoint, corrected direct residual, and initial parameters.",
        "The prior exact affine-gradient state-reduction contract and one-ulp total-adjoint mismatch receipt.",
        "The source total-adjoint comparator only after both conversion-variant populations exist.",
    ]
    experiment["budget"] = {
        "expectedGrossSavingsBytes": 0,
        "maximumAddedPackageBytes": 1_000_000,
        "expectedNetSavingsBytes": -1_000_000,
    }
    experiment["search"] = {
        "expectedTransferRetention": 1.0,
        "expectedRuntimeRatio": 0.1,
        "expectedMemoryRatio": 0.2,
        "uncertaintyRisk": 0.05,
        "interactionRisk": 0.05,
    }
    replacements = {
        "pre-ff-backward-materializer": base.reference(
            STATE_MATERIALIZER, "state-backward-materializer"
        ),
        "runner": base.reference(RUNNER, "runner"),
        "materializer": base.reference(MATERIALIZER, "materializer"),
        "program-descriptor": base.reference(DESCRIPTOR, "program-descriptor"),
    }
    inputs = [replacements.get(item["id"], item) for item in experiment["inputs"]]
    additions = [
        base.reference(PARENT_RESULT / "decision.json", "conversion-parent-decision"),
        base.reference(PARENT_RESULT / "execution.json", "conversion-parent-execution"),
        base.reference(PARENT_RESULT / "guard.json", "conversion-parent-guard"),
        base.reference(PARENT_REFLECTION, "conversion-parent-reflection"),
        base.reference(CONVERSION_MATERIALIZER, "conversion-probe-materializer"),
    ]
    existing_ids = {item["id"] for item in inputs}
    inputs.extend(item for item in additions if item["id"] not in existing_ids)
    present_paths = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            inputs.append(base.reference(path, base.source_identifier(path)))
            present_paths.add(relative)
    experiment["inputs"] = inputs
    experiment["measurements"] = [
        base.measurement("antecedentsPass", "boolean", "All parent receipts and arithmetic inputs remain hash-bound."),
        base.measurement("elementCount", "BF16 elements", "Complete total-adjoint population."),
        base.measurement("gainGradientMismatchCount", "BF16 elements", "State-reduced gain-gradient mismatches."),
        base.measurement("biasGradientMismatchCount", "BF16 elements", "State-reduced bias-gradient mismatches."),
        base.measurement("fusedTotalMismatchCount", "BF16 elements", "Post-merge conversion mismatches."),
        base.measurement("maximumFusedTotalAbsoluteError", "float32 value", "Maximum post-merge conversion error."),
        base.measurement("preconvertedTotalMismatchCount", "BF16 elements", "Pre-merge conversion control mismatches."),
        base.measurement("directOnlyControlMismatchCount", "BF16 elements", "Direct-only control mismatches."),
        base.measurement("negatedControlMismatchCount", "BF16 elements", "Negated-branch control mismatches."),
        base.measurement("evaluationReplayIdentical", "boolean", "Both variant evaluations reproduce byte-for-byte."),
        base.measurement("forbiddenDynamicDependencyCount", "dependencies", "Forbidden dynamic dependencies."),
        base.measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed source."),
        base.measurement("guardedWorkRootPass", "boolean", "Transient evaluation work was removed."),
    ]
    experiment["promotionPredicates"] = [
        base.predicate("p-antecedents", "antecedentsPass", "eq", True),
        base.predicate("p-elements", "elementCount", "eq", 2_097_152),
        base.predicate("p-gain", "gainGradientMismatchCount", "eq", 0),
        base.predicate("p-bias", "biasGradientMismatchCount", "eq", 0),
        base.predicate("p-fused", "fusedTotalMismatchCount", "eq", 0),
        base.predicate("p-fused-maximum", "maximumFusedTotalAbsoluteError", "eq", 0.0),
        base.predicate("p-preconverted", "preconvertedTotalMismatchCount", "gt", 0),
        base.predicate("p-direct", "directOnlyControlMismatchCount", "gt", 0),
        base.predicate("p-negated", "negatedControlMismatchCount", "gt", 0),
        base.predicate("p-replay", "evaluationReplayIdentical", "eq", True),
        base.predicate("p-dependencies", "forbiddenDynamicDependencyCount", "eq", 0),
        base.predicate("p-source", "incrementalSourceBytes", "lte", 1_000_000),
        base.predicate("p-work", "guardedWorkRootPass", "eq", True),
    ]
    experiment["killPredicates"] = [
        base.predicate("k-antecedents", "antecedentsPass", "eq", True),
        base.predicate("k-fused", "fusedTotalMismatchCount", "gt", 0),
    ]
    experiment["outputs"] = [
        f"results/{CANDIDATE_ID}/decision.json",
        f"results/{CANDIDATE_ID}/execution.json",
        f"results/{CANDIDATE_ID}/source-exact-pre-ff-total-adjoint.bf16",
        f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
    ]
    experiment["generatedUtc"] = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
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
