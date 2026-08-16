#!/usr/bin/env python3
"""Freeze the ordered-panel open top-FF1 input-adjoint experiment."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_ff1_input_adjoint_block128_64_q0_v1"
PARENT_ID = "nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_open_top_ff1_input_adjoint_block128_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
EVALUATOR = PROGRAM / "ff1_transpose_block128.cpp"
DESCRIPTOR = PROGRAM / "program.py"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T123446Z_5cbfc56c6d.json"
)
INCOMING = ROOT / (
    "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/"
    "open-ff1-output-residual.bf16"
)
FF2_RESULT = ROOT / "results/nncp_libnc_ff2_transpose_block128_64_q0_v1"
FF2_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T093907Z_7f51e2d346.json"
)
SOURCE_CEILING = 1_000_000
HYPOTHESIS = (
    "The source-attributed ordered 128-feature matmul panels transfer from FF2 "
    "to the 6,144-feature FF1 reduction and reproduce all 2,097,152 production "
    "FF1 input-adjoint words exactly, while one unbroken reduction remains "
    "distinguishable."
)


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
    parent_revision = ROOT / json.loads(
        (PARENT_RESULT / "decision.json").read_text()
    )["candidateRevision"]["receipt"]["path"]
    inputs = [
        reference(PARENT_RESULT / "decision.json", "parent-decision"),
        reference(PARENT_RESULT / "execution.json", "parent-execution"),
        reference(PARENT_RESULT / "guard.json", "parent-guard"),
        reference(PARENT_REFLECTION, "parent-reflection"),
        reference(
            PARENT_RESULT / "source-ff1-input-adjoint.bf16",
            "source-ff1-input-adjoint",
        ),
        reference(
            PARENT_RESULT / "source-initial-ff1-19.bf16",
            "source-initial-ff1-19",
        ),
        reference(INCOMING, "open-ff1-output-adjoint"),
        reference(FF2_RESULT / "decision.json", "ff2-panel-decision"),
        reference(FF2_RESULT / "execution.json", "ff2-panel-execution"),
        reference(FF2_REFLECTION, "ff2-panel-reflection"),
        reference(RUNNER, "runner"),
        reference(MATERIALIZER, "materializer"),
        reference(EVALUATOR, "evaluator-source"),
        reference(DESCRIPTOR, "program-descriptor"),
    ]
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(reference(path, source_identifier(path)))
            present.add(relative)
    measurements = [
        measurement("antecedentsPass", "boolean", "The deterministic source oracle, exact operands, initial matrix, and prior FF2 panel attribution remain hash-bound."),
        measurement("adjointElementCount", "BF16 elements", "Words in each complete FF1 input-adjoint cell."),
        measurement("reductionPanelCount", "128-feature panels", "Ordered panels covering the 6,144-feature reduction."),
        measurement("block128SourceMismatchCount", "BF16 elements", "Ordered-panel words differing from the source adjoint."),
        measurement("maximumBlock128AbsoluteError", "float32 value", "Maximum ordered-panel/source error."),
        measurement("unblockedSourceMismatchCount", "BF16 elements", "One-unbroken-reduction words differing from the source adjoint."),
        measurement("arithmeticCellsDiffer", "boolean", "Ordered-panel and unblocked complete populations differ byte-for-byte."),
        measurement("evaluationReplayIdentical", "boolean", "Two complete two-cell evaluations reproduce byte-for-byte."),
        measurement("forbiddenDynamicDependencyCount", "dependencies", "LibNC, GGML, BLAS, OpenMP, or CUDA dependencies in the open executable."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed candidate source."),
        measurement("guardedWorkRootPass", "boolean", "All transient build and evaluation payloads were removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-elements", "adjointElementCount", "eq", 2097152),
        predicate("p-panels", "reductionPanelCount", "eq", 48),
        predicate("p-treatment", "block128SourceMismatchCount", "eq", 0),
        predicate("p-maximum", "maximumBlock128AbsoluteError", "eq", 0.0),
        predicate("p-unblocked-live", "unblockedSourceMismatchCount", "gt", 0),
        predicate("p-cells-differ", "arithmeticCellsDiffer", "eq", True),
        predicate("p-replay", "evaluationReplayIdentical", "eq", True),
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
                key: value
                for key, value in reference(
                    parent_revision, "parent-revision"
                ).items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": HYPOTHESIS,
            "falsification": "Any ordered-panel/source mismatch, indistinguishable unblocked control, replay failure, forbidden dependency, source failure, or resource failure rejects the transferred driver contract.",
        },
        "changedMechanism": "Apply the previously source-attributed matmul driver schedule to FF1: eight adjacent destination lanes, 48 ordered 128-feature reduction panels, sequential fused accumulation within panels, and explicit panel combination before one BF16 output conversion.",
        "invariants": [
            "The captured source adjoint, initial ff1_19 matrix, exact incoming FF1 output adjoint, sample order, coordinate layout, and BF16 conversion remain unchanged.",
            "One uniform kernel covers all 2,097,152 coordinates; tolerance, coordinate repair, and comparator-derived values are forbidden.",
            "Both complete arithmetic cells are generated before consulting the source comparator.",
            "The executable has no LibNC, GGML, BLAS, OpenMP, or CUDA dependency.",
        ],
        "controls": [
            {"id": "ordered-128-panels", "role": "treatment", "definition": "Reduce 6,144 features as 48 ordered 128-feature panels and combine completed panels sequentially."},
            {"id": "source-input-adjoint", "role": "comparator", "definition": "Compare only after both complete open cells exist against the deterministic source oracle."},
            {"id": "one-unbroken-reduction", "role": "negative", "definition": "Use the same lanes, weights, input, FMA, and BF16 conversion but remove all intermediate panel boundaries."},
            {"id": "ff2-driver-transfer", "role": "shifted", "definition": "Bind the independent exact FF2 transpose receipt that first attributed the ordered-panel driver."},
            {"id": "independent-replay", "role": "replay", "definition": "Execute both complete arithmetic cells twice."},
        ],
        "population": {
            "unit": "BF16 top-FF1 input-adjoint words",
            "scopeBytes": 4194304,
            "scopeSymbols": 2097152,
            "selection": "Every one of 1,024 destination features for all 64 chronological states and 32 streams.",
            "coordinate": "state-major, stream-major, destination-feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The exact incoming FF1 output adjoint and initial BF16 ff1_19 matrix.",
                "The prior independently attributed ordered-panel LibNC matmul-driver contract.",
                "The source adjoint only after complete open populations exist.",
            ],
            "forbiddenInformation": [
                "Coordinate-specific arithmetic, fitted corrections, tolerance, or any source-oracle dependency in the executable."
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
            "uncertaintyRisk": 0.15,
            "interactionRisk": 0.05,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-treatment", "block128SourceMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-exact-ff1-input-adjoint.bf16",
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
