#!/usr/bin/env python3
"""Freeze the open layer-19 value-attention transpose contract."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_w_o_input_adjoint_64_q0_v1_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_attention_value_transpose_64_q0_v1"
PARENT_ID = "nncp_open_top_attention_forward_inputs_64_q0_v1"
PARENT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T220926Z_56872cd576.json"
)
SOURCE = ROOT / "results/nncp_libnc_top_attention_product_oracle_64_q0_retry_v2"
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T174722Z_8b88b4a53d.json"
)
CONCAT = ROOT / "results/nncp_open_concat_head_identity_64_q0_v1"
CONCAT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T175422Z_91aae07812.json"
)
PANEL = ROOT / "results/nncp_open_w_o_input_adjoint_block128_64_q0_v1"
PANEL_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T164348Z_ff5718724e.json"
)
PROGRAM = ROOT / "programs" / CANDIDATE_ID
EVALUATOR = PROGRAM / "attention_value_transpose.cpp"
DESCRIPTOR = PROGRAM / "program.py"
RUNNER = ROOT / "tools/nncp_open_top_attention_value_transpose_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
SOURCE_CEILING = 500_000
HYPOTHESIS = (
    "A LibNC-free 128-feature AVX2 FMA transpose over the exact open layer-19 "
    "value state and attended adjoint reproduces all 5,242,880 source "
    "probability-adjoint BF16 words, while stream-major and sign-negated "
    "controls differ."
)


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    suffix = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{suffix}"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent_revision = ROOT / json.loads(PARENT.joinpath("decision.json").read_text())[
        "candidateRevision"
    ]["receipt"]["path"]
    inputs = [
        base.reference(PARENT / "decision.json", "parent-decision"),
        base.reference(PARENT / "execution.json", "parent-execution"),
        base.reference(PARENT / "guard.json", "parent-guard"),
        base.reference(PARENT_REFLECTION, "parent-reflection"),
        base.reference(PARENT / "open-exact-value-state.bf16", "open-value-state"),
        base.reference(SOURCE / "decision.json", "source-decision"),
        base.reference(SOURCE / "execution.json", "source-execution"),
        base.reference(SOURCE / "guard.json", "source-guard"),
        base.reference(SOURCE_REFLECTION, "source-reflection"),
        base.reference(
            SOURCE / "source-attention-probability-adjoint.bf16",
            "source-probability-adjoint",
        ),
        base.reference(CONCAT / "decision.json", "concat-decision"),
        base.reference(CONCAT / "execution.json", "concat-execution"),
        base.reference(CONCAT / "guard.json", "concat-guard"),
        base.reference(CONCAT_REFLECTION, "concat-reflection"),
        base.reference(
            CONCAT / "open-exact-attended-adjoint.bf16",
            "open-attended-adjoint",
        ),
        base.reference(PANEL / "decision.json", "panel-decision"),
        base.reference(PANEL / "execution.json", "panel-execution"),
        base.reference(PANEL / "guard.json", "panel-guard"),
        base.reference(PANEL_REFLECTION, "panel-reflection"),
        base.reference(EVALUATOR, "evaluator-source"),
        base.reference(RUNNER, "runner"),
        base.reference(MATERIALIZER, "materializer"),
        base.reference(DESCRIPTOR, "program-descriptor"),
    ]
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(base.reference(path, source_identifier(path)))
            present.add(relative)
    measurements = [
        base.measurement("antecedentsPass", "boolean", "All exact source, forward, concat, and panel antecedents remain digest-bound."),
        base.measurement("sampleCount", "state-stream samples", "Complete 64 by 32 production population."),
        base.measurement("headCount", "heads", "Complete attention-head population."),
        base.measurement("keyCount", "keys", "Complete retained key population."),
        base.measurement("reductionWidth", "features", "Exact head-feature reduction width."),
        base.measurement("adjointElementCount", "BF16 elements", "Complete source-coordinate probability-adjoint population."),
        base.measurement("treatmentMismatchCount", "BF16 elements", "Treatment words differing from the source adjoint."),
        base.measurement("maximumTreatmentAbsoluteError", "float32 value", "Maximum treatment/source error."),
        base.measurement("streamMajorControlMismatchCount", "BF16 elements", "Wrong output-axis order mismatches."),
        base.measurement("negatedControlMismatchCount", "BF16 elements", "Sign-negated treatment mismatches."),
        base.measurement("evaluationReplayIdentical", "boolean", "Two complete evaluations reproduce byte-for-byte."),
        base.measurement("forbiddenDynamicDependencyCount", "libraries", "Dynamic LibNC, GGML, CUDA, OpenMP, or BLAS dependencies."),
        base.measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed source."),
        base.measurement("guardedWorkRootPass", "boolean", "Transient build and evaluation files were removed."),
    ]
    promotion = [
        base.predicate("p-antecedents", "antecedentsPass", "eq", True),
        base.predicate("p-samples", "sampleCount", "eq", 2048),
        base.predicate("p-heads", "headCount", "eq", 8),
        base.predicate("p-keys", "keyCount", "eq", 320),
        base.predicate("p-reduction", "reductionWidth", "eq", 128),
        base.predicate("p-elements", "adjointElementCount", "eq", 5242880),
        base.predicate("p-treatment", "treatmentMismatchCount", "eq", 0),
        base.predicate("p-maximum", "maximumTreatmentAbsoluteError", "eq", 0.0),
        base.predicate("p-layout-control", "streamMajorControlMismatchCount", "gt", 0),
        base.predicate("p-sign-control", "negatedControlMismatchCount", "gt", 0),
        base.predicate("p-replay", "evaluationReplayIdentical", "eq", True),
        base.predicate("p-dependencies", "forbiddenDynamicDependencyCount", "eq", 0),
        base.predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
        base.predicate("p-work", "guardedWorkRootPass", "eq", True),
    ]
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
            "claim": HYPOTHESIS,
            "falsification": "Any source mismatch, incomplete population, dead control, replay drift, undeclared dependency, source-closure overflow, or resource failure rejects this arithmetic boundary.",
        },
        "changedMechanism": "Implement only the layer-19 value-matrix transpose from exact open value state and exact open attended adjoint to the independently captured source probability adjoint.",
        "invariants": [
            "The parent forward, concat identity, source comparator, and all retained tensors are immutable and hash-bound.",
            "Each output key accumulates exactly 128 sequential AVX2 fused multiply-add steps from zero and rounds once to BF16.",
            "The treatment emits source coordinate order: state, head, stream, key.",
            "No teacher executable or captured source tensor may ship in a Gamma codec.",
        ],
        "controls": [
            {"id": "source-order", "role": "treatment", "definition": "Compute dProbability in state, head, stream, key order."},
            {"id": "stream-major", "role": "negative", "definition": "Serialize the same values in state, stream, head, key order and require mismatches."},
            {"id": "negated", "role": "negative", "definition": "Negate dAttended before the same transpose and require mismatches."},
            {"id": "replay", "role": "replay", "definition": "Repeat all complete treatment and control populations byte-for-byte."},
        ],
        "population": {
            "unit": "BF16 layer-19 attention-probability adjoint words",
            "scopeBytes": 10485760,
            "scopeSymbols": 5242880,
            "selection": "Every key for 64 states, 32 streams, and eight heads.",
            "coordinate": "state-major, head-major, stream-major, key-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The exact open value state, exact open attended adjoint, independent source probability-adjoint comparator, and validated 128-feature FMA schedule."
            ],
            "forbiddenInformation": [
                "LibNC execution, tolerance, fitting to mismatch coordinates, editing the source comparator, future symbols, or future experiments.",
                "Claiming softmax backward, value-state adjoints, a compact predictor, compression gain, or Hutter credit.",
            ],
        },
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 1.0,
            "uncertaintyRisk": 0.12,
            "interactionRisk": 0.08,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            base.predicate("k-antecedents", "antecedentsPass", "eq", True),
            base.predicate("k-treatment", "treatmentMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-exact-attention-probability-adjoint.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "outputManifestPolicy": "complete-result-artifacts-v1",
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(OUTPUT)
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
