#!/usr/bin/env python3
"""Freeze the top-FF1 weight-gradient schedule attribution."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_ff1_weight_slice_schedule_64_q0_v1"
PARENT_ID = "nncp_open_ff1_bias_state_reduce_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_ff1_weight_slice_schedule_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
EVALUATOR = PROGRAM / "ff1_weight_slice_schedule.c"
FORWARD_MATERIALIZER = PROGRAM / "materialize_ff1_input.py"
CMAKE = PROGRAM / "CMakeLists.txt"
DESCRIPTOR = PROGRAM / "program.py"
TOP_PARENT_RESULT = ROOT / (
    "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1"
)
TOP_PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T104952Z_2204470800.json"
)
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T112548Z_7841e2cc5b.json"
)
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
PARENT_FORWARD_MATERIALIZER = ROOT / (
    "programs/nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2/"
    "materialize_forward.py"
)
PARENT_REVISION = ROOT / json.loads((PARENT_RESULT / "decision.json").read_text())[
    "candidateRevision"
]["receipt"]["path"]
SOURCE_CEILING = 2_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"experiment input is not a project file: {path}")
    return {
        "id": identifier,
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }


def measurement(identifier: str, unit: str, definition: str) -> dict[str, str]:
    return {"id": identifier, "unit": unit, "definition": definition}


def predicate(
    identifier: str, measurement_id: str, operator: str, threshold: object
) -> dict[str, object]:
    return {
        "id": identifier,
        "measurement": measurement_id,
        "operator": operator,
        "threshold": threshold,
    }


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    suffix = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{suffix}"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    inputs = [
        reference(TOP_PARENT_RESULT / "decision.json", "top-parent-decision"),
        reference(TOP_PARENT_RESULT / "execution.json", "top-parent-execution"),
        reference(TOP_PARENT_RESULT / "guard.json", "top-parent-guard"),
        reference(TOP_PARENT_REFLECTION, "top-parent-reflection"),
        reference(
            TOP_PARENT_RESULT / "open-ff1-output-residual.bf16",
            "source-exact-ff1-output-residual",
        ),
        reference(PARENT_RESULT / "decision.json", "parent-decision"),
        reference(PARENT_RESULT / "execution.json", "parent-execution"),
        reference(PARENT_RESULT / "guard.json", "parent-guard"),
        reference(PARENT_REFLECTION, "parent-reflection"),
        reference(FIXTURE_ROOT / "decision.json", "fixture-decision"),
        reference(FIXTURE_ROOT / "fixture-manifest.json", "fixture-manifest"),
        reference(
            FIXTURE_ROOT / "fixture/gradients/0002_ff1_19.bin",
            "retained-ff1-19-gradient",
        ),
        reference(
            FIXTURE_ROOT / "fixture/gradients/0002_ff1_19.meta",
            "retained-ff1-19-gradient-meta",
        ),
        reference(
            PARENT_FORWARD_MATERIALIZER, "parent-forward-materializer"
        ),
        reference(RUNNER, "runner"),
        reference(MATERIALIZER, "materializer"),
        reference(EVALUATOR, "evaluator-source"),
        reference(FORWARD_MATERIALIZER, "ff1-input-materializer"),
        reference(CMAKE, "cmake-contract"),
        reference(DESCRIPTOR, "program-descriptor"),
    ]
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(reference(path, source_identifier(path)))
            present.add(relative)
    measurements = [
        measurement("antecedentsPass", "boolean", "The exact top-FF1 adjoint, open bias reducer, source fixture, comparator, and guards remain hash-bound."),
        measurement("streamCount", "streams", "Streams in every decoder-state matrix input."),
        measurement("stateCount", "states", "Chronological decoder states accumulated."),
        measurement("sampleCount", "samples", "Complete state-by-stream sample population."),
        measurement("inputFeatureCount", "features", "FF1 matrix input features."),
        measurement("sliceOutputFeatureCount", "features", "Prospectively selected adjacent FF1 output rows."),
        measurement("inputElementCount", "BF16 elements", "Complete open layer-19 FF1 input population."),
        measurement("residualElementCount", "BF16 elements", "Complete source-exact FF1-output adjoint population."),
        measurement("sliceElementCount", "BF16 elements", "Retained ff1_19 gradient words in the frozen slice."),
        measurement("stateMatmulCallCount", "calls", "Chronological nc_matmul_add2 state updates."),
        measurement("layerInputCheckpointCount", "checkpoints", "Inherited exact forward checkpoints in one replay."),
        measurement("layerInputMismatchCount", "float32 elements", "Inherited forward checkpoint mismatches over both replays."),
        measurement("maximumLayerInputAbsoluteError", "float32 value", "Maximum inherited forward checkpoint error."),
        measurement("treatmentMismatchCount", "BF16 elements", "Chronological treatment words differing from the retained slice."),
        measurement("maximumTreatmentAbsoluteError", "float32 value", "Maximum treatment/comparator error."),
        measurement("flatMismatchCount", "BF16 elements", "One-call flat-control words differing from the retained slice."),
        measurement("reverseMismatchCount", "BF16 elements", "Reverse-state control words differing from the retained slice."),
        measurement("negatedControlDiffers", "boolean", "Sign-negating the exact residual changes the projected slice."),
        measurement("ff1InputReplayIdentical", "boolean", "Two complete open forward populations produce the same FF1 input."),
        measurement("evaluationReplayIdentical", "boolean", "Both treatment/control populations reproduce byte-for-byte."),
        measurement("sourceLibraryDigestBound", "boolean", "Execution uses the attributed production LibNC digest."),
        measurement("forbiddenDynamicDependencyCount", "dependencies", "LibNC, GGML, BLAS, OpenMP, or CUDA dependencies in the open forward executable."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed candidate source."),
        measurement("guardedWorkRootPass", "boolean", "All transient forward, build, and oracle payloads were removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-streams", "streamCount", "eq", 32),
        predicate("p-states", "stateCount", "eq", 64),
        predicate("p-samples", "sampleCount", "eq", 2048),
        predicate("p-input-features", "inputFeatureCount", "eq", 1024),
        predicate("p-output-features", "sliceOutputFeatureCount", "eq", 128),
        predicate("p-input", "inputElementCount", "eq", 2097152),
        predicate("p-residual", "residualElementCount", "eq", 12582912),
        predicate("p-slice", "sliceElementCount", "eq", 131072),
        predicate("p-calls", "stateMatmulCallCount", "eq", 64),
        predicate("p-checkpoints", "layerInputCheckpointCount", "eq", 640),
        predicate("p-forward-mismatch", "layerInputMismatchCount", "eq", 0),
        predicate("p-forward-maximum", "maximumLayerInputAbsoluteError", "eq", 0.0),
        predicate("p-treatment", "treatmentMismatchCount", "eq", 0),
        predicate("p-treatment-maximum", "maximumTreatmentAbsoluteError", "eq", 0.0),
        predicate("p-flat-live", "flatMismatchCount", "gt", 0),
        predicate("p-reverse-live", "reverseMismatchCount", "gt", 0),
        predicate("p-negated", "negatedControlDiffers", "eq", True),
        predicate("p-input-replay", "ff1InputReplayIdentical", "eq", True),
        predicate("p-evaluation-replay", "evaluationReplayIdentical", "eq", True),
        predicate("p-library", "sourceLibraryDigestBound", "eq", True),
        predicate("p-dependencies", "forbiddenDynamicDependencyCount", "eq", 0),
        predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
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
                key: value for key, value in
                reference(PARENT_REVISION, "parent-revision").items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": "Sixty-four chronological LibNC BF16 matrix-gradient updates reproduce every retained word in the first 128 output rows of ff1_19, while a flat whole-population update and reverse state order differ.",
            "falsification": "Any treatment mismatch, exact-forward mismatch, dead control, replay failure, digest drift, or resource failure rejects this schedule as the source-exact FF1 weight-gradient boundary.",
        },
        "changedMechanism": "Expose the exact layer-19 FF1 matrix input, then replace an unspecified whole-population projection with the statically attributed backward call: nc_matmul_add2(state_residual, state_input, existing_gradient, false, true, 1, 0) for 64 chronological states.",
        "invariants": [
            "The exact FF2 and GEGLU output adjoint is consumed unchanged and the open forward changes only artifact visibility.",
            "The 128 adjacent output rows are selected before execution and no retained coordinate influences the treatment.",
            "The retained gradient is read only after both complete treatment/control populations exist; tolerance and coordinate repair are forbidden.",
            "LibNC remains a zero-credit attribution teacher and cannot ship in a submitted codec.",
        ],
        "controls": [
            {"id": "chronological-state-matmul", "role": "treatment", "definition": "Accumulate one 128-by-32 residual panel times one transposed 1,024-by-32 input panel into the existing BF16 gradient for each chronological state."},
            {"id": "flat-whole-population", "role": "comparator", "definition": "Perform one 128-by-2,048 times transposed 1,024-by-2,048 LibNC matrix update."},
            {"id": "reverse-state-order", "role": "negative", "definition": "Apply the same state updates from state 63 down to state 0."},
            {"id": "negated-residual", "role": "negative", "definition": "Invert only the sign bit of every source-exact FF1-output adjoint word."},
            {"id": "independent-replay", "role": "replay", "definition": "Regenerate the complete open forward input and all four projections twice."},
        ],
        "population": {
            "unit": "BF16 FF1 matrix-gradient operands",
            "scopeBytes": 29360128,
            "scopeSymbols": 14680064,
            "selection": "All 64 states, all 32 streams, all 1,024 FF1 inputs, the complete 6,144-feature adjoint, and a prospectively frozen adjacent 128-output gradient slice.",
            "coordinate": "state-major, stream-major, feature-major operands; input-major then output-feature-major gradient storage",
        },
        "causalBoundary": {
            "availableInformation": [
                "The complete source-exact BF16 FF1-output adjoint.",
                "A digest-derived exact open forward exposing BF16 layer-19 FF1 inputs.",
                "The statically attributed nc_backward matrix-gradient call and production LibNC digest."
            ],
            "forbiddenInformation": [
                "The retained ff1_19 slice before both replay populations complete.",
                "Coordinate-specific patches, tolerance, fitted row selection, or teacher payloads in a submitted codec."
            ],
        },
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 0.0,
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 1.0,
            "uncertaintyRisk": 0.2,
            "interactionRisk": 0.2,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-treatment", "treatmentMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/open-ff1-input.bf16",
            f"results/{CANDIDATE_ID}/libnc-treatment-slice.bf16",
            f"results/{CANDIDATE_ID}/libnc-flat-control-slice.bf16",
            f"results/{CANDIDATE_ID}/libnc-reverse-control-slice.bf16",
            f"results/{CANDIDATE_ID}/libnc-negated-control-slice.bf16",
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
