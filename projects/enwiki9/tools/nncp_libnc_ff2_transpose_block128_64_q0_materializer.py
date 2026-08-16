#!/usr/bin/env python3
"""Freeze production FF2-transpose 128-feature panel attribution."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_final_rmsnorm_reduction_scale_64_q0_materializer as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_ff2_transpose_block128_64_q0_v1"
PARENT_ID = "nncp_libnc_ff2_transpose_lane_order_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_ff2_transpose_block128_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T093214Z_c6950a77d0.json"
)
SOURCE_RESULT = ROOT / "results/nncp_libnc_top_ff2_input_adjoint_64_q0_v1"
OPEN_RESULT = ROOT / "results/nncp_open_profile_top_ff1_bias_gradient_64_q0_v1"
TAIL_RESULT = ROOT / (
    "results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2"
)
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T093154904697Z_3942ac06fd66.json"
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
            PARENT_RESULT / "lane-sequential-ff2-input-adjoint.bf16",
            "lane-sequential-residual",
        ),
        reference(SOURCE_RESULT / "decision.json", "source-decision"),
        reference(
            SOURCE_RESULT / "source-ff2-input-adjoint.bf16",
            "source-ff2-input-adjoint",
        ),
        reference(OPEN_RESULT / "execution.json", "open-execution"),
        reference(
            OPEN_RESULT / "open-ff2-input-residual.bf16",
            "open-ff2-input-residual",
        ),
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
            "The valid horizontal and unblocked-lane refutations, exact source/input artifacts, parameter fixture, and source library digest remain bound.",
        ),
        measurement(
            "evaluationReplayIdentical",
            "boolean",
            "Two independent 128-panel evaluations reproduce the complete output byte-for-byte.",
        ),
        measurement(
            "adjointElementCount",
            "BF16 elements",
            "Complete 128-panel FF2-input-adjoint population.",
        ),
        measurement(
            "baselineSourceMismatchCount",
            "BF16 elements",
            "Frozen horizontal-reduction baseline words differing from source.",
        ),
        measurement(
            "laneSourceMismatchCount",
            "BF16 elements",
            "Frozen unblocked lane-sequential words differing from source.",
        ),
        measurement(
            "block128SourceMismatchCount",
            "BF16 elements",
            "128-panel treatment words differing from source.",
        ),
        measurement(
            "maximumBlock128AbsoluteError",
            "float32 value",
            "Maximum absolute treatment/source BF16 value difference.",
        ),
        measurement(
            "treatmentChangesBaseline",
            "boolean",
            "The treatment differs from the horizontal baseline.",
        ),
        measurement(
            "treatmentChangesLane",
            "boolean",
            "The panel reset changes the unblocked lane treatment.",
        ),
        measurement(
            "sourceLibraryDigestBound",
            "boolean",
            "The statically attributed LibNC binary matches the frozen digest.",
        ),
        measurement(
            "parameterFixtureDigestBound",
            "boolean",
            "The initial ff2_19 container matches the retained population digest.",
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
        predicate("p-lane-source", "laneSourceMismatchCount", "eq", 929),
        predicate(
            "p-treatment-source", "block128SourceMismatchCount", "eq", 0
        ),
        predicate(
            "p-treatment-maximum",
            "maximumBlock128AbsoluteError",
            "eq",
            0,
        ),
        predicate("p-baseline-live", "treatmentChangesBaseline", "eq", True),
        predicate("p-panel-live", "treatmentChangesLane", "eq", True),
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
            "claim": "Resetting lane-sequential FF2 transpose accumulation at each ordered 128-feature reduction panel and adding each panel to the prior output reproduces every source FF2-input-adjoint word.",
            "falsification": "Any antecedent, digest, population, replay, source, or guard failure, or any nonzero treatment/source mismatch, prevents promotion.",
        },
        "changedMechanism": "Preserve adjacent output-feature SIMD lanes, but reset their accumulators for each ordered 128-feature reduction panel and add the completed panel to the prior output before processing the next panel.",
        "invariants": [
            "No teacher or production executable is rerun; the complete source adjoint is a digest-bound post-completion comparator.",
            "The incoming residual, initial ff2_19 weights, sample order, FMA operation, adjacent-feature lanes, and final BF16 conversion remain fixed.",
            "Only the disassembly-derived 128-feature reset-and-combine boundary differs from the refuted unblocked lane treatment.",
            "The treatment is uniform over all samples and features; coordinate repair and tolerance are forbidden.",
            "LibNC disassembly and all retained source/open tensors remain zero-credit and cannot ship in a submitted codec.",
        ],
        "controls": [
            {
                "id": "retained-horizontal-baseline",
                "role": "comparator",
                "definition": "The horizontal baseline must retain its 775-word source mismatch.",
            },
            {
                "id": "retained-unblocked-lane",
                "role": "comparator",
                "definition": "The unblocked lane treatment must retain its 929-word source mismatch.",
            },
            {
                "id": "block128-treatment",
                "role": "treatment",
                "definition": "The only changed arithmetic is the ordered 128-feature panel reset and combination.",
            },
            {
                "id": "independent-evaluator-replay",
                "role": "replay",
                "definition": "The complete treatment is evaluated twice before classification.",
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
                "Digest-bound incoming residual, initial ff2_19 weights, horizontal and unblocked-lane outputs, source adjoint, parent decisions/reflections, and the prospectively frozen 128-panel treatment.",
                "Static disassembly identifies a 128-feature driver panel and a 32-output lane kernel; no 128-panel output was computed before this contract was frozen.",
            ],
            "forbiddenInformation": [
                "Changing panel width or arithmetic after comparison, coordinate-specific repair, tolerance, teacher rerun, or compression credit from the oracle.",
                "Using LibNC, its disassembly, captured tensors, hidden traces, or retained gradients in a submitted codec.",
            ],
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/block128-ff2-input-adjoint.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate(
                "k-treatment-mismatch", "block128SourceMismatchCount", "gt", 0
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
