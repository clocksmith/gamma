#!/usr/bin/env python3
"""Freeze exact AVX2 GEGLU gate-backward attribution."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_final_rmsnorm_reduction_scale_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_geglu_gate_avx2_64_q0_v1"
PARENT_ID = "nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v2"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_geglu_gate_avx2_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T102756Z_33b5fb91aa.json"
)
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T102743270516Z_6975199679ba.json"
)
OPEN_RESULT = ROOT / (
    "results/nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2"
)
OPEN_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T095147Z_8ddedba49c.json"
)
SOURCE_CEILING = 1_000_000


sha256 = base.sha256
reference = base.reference
source_identifier = base.source_identifier
measurement = base.measurement
predicate = base.predicate


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    inputs = [
        reference(PARENT_RESULT / "decision.json", "parent-decision"),
        reference(PARENT_RESULT / "execution.json", "parent-execution"),
        reference(PARENT_RESULT / "guard.json", "parent-guard"),
        reference(PARENT_REFLECTION, "parent-reflection"),
        reference(
            PARENT_RESULT / "source-geglu-gate-input.bf16",
            "source-geglu-gate-input",
        ),
        reference(
            PARENT_RESULT / "source-geglu-gate-adjoint.bf16",
            "source-geglu-gate-adjoint",
        ),
        reference(
            PARENT_RESULT / "source-geglu-value-input.bf16",
            "source-geglu-value-input",
        ),
        reference(
            PARENT_RESULT / "source-geglu-value-adjoint.bf16",
            "source-geglu-value-adjoint",
        ),
        reference(OPEN_RESULT / "decision.json", "open-decision"),
        reference(OPEN_RESULT / "execution.json", "open-execution"),
        reference(OPEN_RESULT / "guard.json", "open-guard"),
        reference(OPEN_REFLECTION, "open-reflection"),
        reference(
            OPEN_RESULT / "open-ff2-input-residual.bf16",
            "open-ff2-input-residual",
        ),
        reference(
            OPEN_RESULT / "open-ff1-output-residual.bf16",
            "open-ff1-output-residual",
        ),
        reference(RUNNER, "runner"),
        reference(MATERIALIZER, "materializer"),
    ]
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(reference(path, source_identifier(path)))
            present.add(relative)

    measurements = [
        measurement(
            "antecedentsPass",
            "boolean",
            "The exact FF2 residual, deterministic branch capture, 114-word retained gate mismatch, exact value control, and terminal reflections remain bound.",
        ),
        measurement(
            "evaluationReplayIdentical",
            "boolean",
            "Two complete AVX2 evaluations reproduce gate and value outputs byte-for-byte.",
        ),
        measurement(
            "adjointElementCount",
            "BF16 elements",
            "Complete layer-19 GEGLU gate-adjoint population.",
        ),
        measurement(
            "retainedGateMismatchCount",
            "BF16 elements",
            "Frozen scalar-open gate words differing from source.",
        ),
        measurement(
            "maximumRetainedGateAbsoluteError",
            "float32 value",
            "Maximum retained scalar-open/source gate difference.",
        ),
        measurement(
            "avx2GateMismatchCount",
            "BF16 elements",
            "Disassembly-derived AVX2 treatment words differing from source.",
        ),
        measurement(
            "maximumAvx2GateAbsoluteError",
            "float32 value",
            "Maximum AVX2 treatment/source gate difference.",
        ),
        measurement(
            "treatmentChangesBaseline",
            "boolean",
            "The AVX2 treatment changes at least one retained scalar-open word.",
        ),
        measurement(
            "valueControlMismatchCount",
            "BF16 elements",
            "Unchanged value-branch control words differing from source.",
        ),
        measurement(
            "maximumValueControlAbsoluteError",
            "float32 value",
            "Maximum unchanged value-control/source difference.",
        ),
        measurement(
            "sourceLibraryDigestBound",
            "boolean",
            "The attributed LibNC binary matches its frozen digest.",
        ),
        measurement(
            "kernelBytesDigestBound",
            "boolean",
            "The complete eight-lane GELU-backward kernel byte range matches its frozen digest.",
        ),
        measurement(
            "incrementalSourceBytes",
            "bytes",
            "Compressed dependency-closed evaluator and orchestration source package.",
        ),
        measurement(
            "guardedWorkRootPass",
            "boolean",
            "Compiled and replay scratch was removed with the guarded work root.",
        ),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-replay", "evaluationReplayIdentical", "eq", True),
        predicate("p-elements", "adjointElementCount", "eq", 6_291_456),
        predicate("p-retained-count", "retainedGateMismatchCount", "eq", 114),
        predicate(
            "p-retained-maximum",
            "maximumRetainedGateAbsoluteError",
            "eq",
            7.450580596923828e-09,
        ),
        predicate("p-treatment-count", "avx2GateMismatchCount", "eq", 0),
        predicate(
            "p-treatment-maximum", "maximumAvx2GateAbsoluteError", "eq", 0
        ),
        predicate("p-treatment-live", "treatmentChangesBaseline", "eq", True),
        predicate("p-value-control", "valueControlMismatchCount", "eq", 0),
        predicate(
            "p-value-maximum", "maximumValueControlAbsoluteError", "eq", 0
        ),
        predicate("p-library", "sourceLibraryDigestBound", "eq", True),
        predicate("p-kernel", "kernelBytesDigestBound", "eq", True),
        predicate(
            "p-source-ceiling", "incrementalSourceBytes", "lte", SOURCE_CEILING
        ),
        predicate("p-work-root", "guardedWorkRootPass", "eq", True),
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
                "path": PARENT_REVISION.relative_to(ROOT).as_posix(),
                "sha256": f"sha256:{sha256(PARENT_REVISION)}",
            },
        },
        "hypothesis": {
            "claim": "Replacing only the scalar libm-tanh gate derivative with the digest-bound production AVX2 bounded-exp polynomial and instruction order reproduces every source GEGLU gate-adjoint word while the unchanged value branch remains exact.",
            "falsification": "Any antecedent, digest, population, replay, value-control, source, guard, or exact gate-comparison failure prevents promotion.",
        },
        "changedMechanism": "Evaluate the production eight-lane GELU-backward instruction contract: fused argument and derivative construction, bounded Cephes exp polynomial for tanh, analytic derivative, incoming-adjoint multiply, and final BF16 materialization.",
        "invariants": [
            "No teacher or production executable is rerun; all four source branch artifacts are immutable post-completion comparators.",
            "Gate input, value input, exact FF2 incoming residual, sample order, branch multiplication, BF16 conversion, and value-branch formula remain fixed.",
            "Only the gate derivative arithmetic changes from scalar libm tanh to the single disassembly-derived AVX2 contract.",
            "The treatment is uniform over all samples and features; coordinate repair, tolerance, and final-bias tuning are forbidden.",
            "LibNC, its disassembly, captured tensors, and this attribution remain zero-credit and cannot ship in a submitted codec.",
        ],
        "controls": [
            {
                "id": "retained-scalar-gate",
                "role": "comparator",
                "definition": "The retained scalar-open gate artifact must preserve exactly 114 source mismatches.",
            },
            {
                "id": "unchanged-value-branch",
                "role": "comparator",
                "definition": "The unchanged value branch must remain exact over the complete population.",
            },
            {
                "id": "independent-evaluator-replay",
                "role": "replay",
                "definition": "The complete treatment and value control are evaluated twice before classification.",
            },
            {
                "id": "avx2-gate-treatment",
                "role": "treatment",
                "definition": "The only changed arithmetic is the digest-bound eight-lane GELU derivative kernel contract.",
            },
        ],
        "population": {
            "unit": "one BF16 GEGLU branch-adjoint word",
            "scopeBytes": None,
            "scopeSymbols": 2048,
            "selection": "All retained 64 states across 32 streams and all 3,072 layer-19 gate features.",
            "coordinate": "First retained production update over transformed-symbol coordinates [256,320) independently within each stream.",
        },
        "causalBoundary": {
            "availableInformation": [
                "Digest-bound source branch inputs/adjoints, exact open FF2 residual, retained scalar branch artifacts, terminal reflections, and static disassembly of the frozen LibNC binary.",
                "The prospectively frozen treatment uses kernel bytes [0x29850,0x2999f), the eight-lane population path, and the literal constants embedded in that range.",
            ],
            "forbiddenInformation": [
                "Changing constants, operation order, BF16 boundaries, or formulas after comparison; coordinate repair; tolerance; teacher rerun; or final-bias fitting.",
                "Using LibNC, source adjoints, hidden traces, or retained gradients in a submitted codec or claiming compression credit from this oracle.",
            ],
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/avx2-geglu-gate-adjoint.bf16",
            f"results/{CANDIDATE_ID}/value-branch-control.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-treatment-mismatch", "avx2GateMismatchCount", "gt", 0)
        ],
        "outputManifestPolicy": "complete-result-artifacts-v1",
        "pythonSourceClosureEntries": ["runner", "materializer"],
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 0.01,
            "expectedMemoryRatio": 0.01,
            "interactionRisk": 0.01,
            "uncertaintyRisk": 0.01,
        },
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
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
