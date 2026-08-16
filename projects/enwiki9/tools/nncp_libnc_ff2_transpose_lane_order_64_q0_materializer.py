#!/usr/bin/env python3
"""Freeze production FF2-transpose lane-order attribution."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_final_rmsnorm_reduction_scale_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_ff2_transpose_lane_order_64_q0_v1"
PARENT_ID = "nncp_libnc_top_ff2_input_adjoint_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_ff2_transpose_lane_order_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T090818Z_428a8e6c62.json"
)
OPEN_RESULT = ROOT / "results/nncp_open_profile_top_ff1_bias_gradient_64_q0_v1"
TAIL_RESULT = ROOT / (
    "results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2"
)
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T090806227557Z_6c0a99aa4fc6.json"
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
            PARENT_RESULT / "source-ff2-input-adjoint.bf16",
            "source-ff2-input-adjoint",
        ),
        reference(OPEN_RESULT / "decision.json", "open-decision"),
        reference(OPEN_RESULT / "execution.json", "open-execution"),
        reference(
            OPEN_RESULT / "open-ff2-input-residual.bf16",
            "open-ff2-input-residual",
        ),
        reference(TAIL_RESULT / "decision.json", "tail-decision"),
        reference(
            TAIL_RESULT / "open-final-norm-input-residual.bf16",
            "incoming-residual",
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
            "The valid 775-word source/open transpose boundary, exact incoming residual, parameter fixture, parent reflection, and source library digest remain bound.",
        ),
        measurement(
            "evaluationReplayIdentical",
            "boolean",
            "Two independent lane-sequential evaluations reproduce the complete output byte-for-byte.",
        ),
        measurement(
            "adjointElementCount",
            "BF16 elements",
            "Complete lane-sequential FF2-input adjoint population.",
        ),
        measurement(
            "baselineSourceMismatchCount",
            "BF16 elements",
            "Frozen horizontal-reduction baseline words differing from the source adjoint.",
        ),
        measurement(
            "laneSequentialSourceMismatchCount",
            "BF16 elements",
            "Disassembly-derived lane-sequential treatment words differing from the source adjoint.",
        ),
        measurement(
            "maximumLaneSequentialAbsoluteError",
            "float32 value",
            "Maximum absolute treatment/source BF16 value difference.",
        ),
        measurement(
            "treatmentChangesBaseline",
            "boolean",
            "The lane-sequential treatment changes at least one baseline word.",
        ),
        measurement(
            "sourceLibraryDigestBound",
            "boolean",
            "The statically attributed LibNC binary matches the frozen digest.",
        ),
        measurement(
            "parameterFixtureDigestBound",
            "boolean",
            "The initial ff2_19 container matches the digest used by the retained open population.",
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
        predicate(
            "p-baseline-source", "baselineSourceMismatchCount", "eq", 775
        ),
        predicate(
            "p-treatment-source",
            "laneSequentialSourceMismatchCount",
            "eq",
            0,
        ),
        predicate(
            "p-treatment-maximum",
            "maximumLaneSequentialAbsoluteError",
            "eq",
            0,
        ),
        predicate("p-treatment-live", "treatmentChangesBaseline", "eq", True),
        predicate("p-library", "sourceLibraryDigestBound", "eq", True),
        predicate("p-parameters", "parameterFixtureDigestBound", "eq", True),
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
            "claim": "Replacing the horizontal eight-lane reduction with the production BF16 kernel's ordered reduction-dimension FMA stream per output-feature lane reproduces every source FF2-input-adjoint word.",
            "falsification": "Any antecedent, digest, population, replay, source, or guard failure, or any nonzero treatment/source mismatch, prevents promotion.",
        },
        "changedMechanism": "Transpose the immutable ff2_19 weights into output-major lane packs, then accumulate each eight-feature output lane through all 1,024 incoming features in chronological FMA order before one BF16 output conversion; do not horizontally reduce the reduction dimension.",
        "invariants": [
            "No teacher or production executable is rerun; the complete source adjoint is a digest-bound post-completion comparator.",
            "The incoming residual, initial ff2_19 weights, sample ordering, FMA operation, and final BF16 conversion remain fixed.",
            "The only arithmetic change is mapping SIMD lanes to adjacent output features rather than partitions of the reduction dimension.",
            "The treatment is uniform over all 2,048 samples and 3,072 output features; coordinate correction and tolerance are forbidden.",
            "The LibNC disassembly and every retained source/open tensor remain zero-credit and cannot ship in a submitted codec.",
        ],
        "controls": [
            {
                "id": "retained-horizontal-baseline",
                "role": "comparator",
                "definition": "The retained open transpose must reproduce its frozen 775-word source mismatch.",
            },
            {
                "id": "independent-source-adjoint",
                "role": "comparator",
                "definition": "The target is the complete deterministic source capture frozen by the parent experiment.",
            },
            {
                "id": "independent-evaluator-replay",
                "role": "replay",
                "definition": "The complete lane-sequential treatment is evaluated twice before classification.",
            },
            {
                "id": "changed-treatment",
                "role": "treatment",
                "definition": "The treatment must differ from the retained horizontal baseline, ruling out a dead arithmetic change.",
            },
        ],
        "population": {
            "unit": "one BF16 FF2-input-adjoint word",
            "scopeBytes": None,
            "scopeSymbols": 2048,
            "selection": "All retained 64 states across 32 streams and all 3,072 layer-19 GEGLU output features.",
            "coordinate": "First retained production update over transformed-symbol coordinates [256,320) independently within each stream.",
        },
        "causalBoundary": {
            "availableInformation": [
                "Digest-bound incoming residual, initial ff2_19 parameter container, retained open residual, complete source adjoint, parent decisions/reflection, and the prospectively frozen lane-sequential treatment.",
                "Static disassembly of the digest-bound BF16 matmul kernel identifies vector lanes as adjacent output features and the reduction dimension as one ordered FMA stream per lane.",
            ],
            "forbiddenInformation": [
                "Changing lane assignment or arithmetic after comparison, coordinate-specific repair, tolerance, teacher rerun, or compression credit from the oracle.",
                "Using LibNC, its disassembly, captured tensors, hidden traces, or retained gradients in a submitted codec.",
            ],
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/lane-sequential-ff2-input-adjoint.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate(
                "k-treatment-mismatch",
                "laneSequentialSourceMismatchCount",
                "gt",
                0,
            )
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
            "interactionRisk": 0.02,
            "uncertaintyRisk": 0.02,
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
