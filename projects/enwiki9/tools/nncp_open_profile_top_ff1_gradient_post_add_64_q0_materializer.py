#!/usr/bin/env python3
"""Freeze the full exact open top-FF1 weight-gradient experiment."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1"
PARENT_ID = "nncp_open_ff1_weight_slice_post_add_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_open_profile_top_ff1_gradient_post_add_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
EVALUATOR = PROGRAM / "ff1_weight_gradient.cpp"
DESCRIPTOR = PROGRAM / "program.py"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T120602Z_ec1474d292.json"
)
SOURCE_RESULT = ROOT / "results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1"
RESIDUAL = ROOT / (
    "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/"
    "open-ff1-output-residual.bf16"
)
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
PARENT_REVISION = ROOT / json.loads((PARENT_RESULT / "decision.json").read_text())[
    "candidateRevision"
]["receipt"]["path"]
SOURCE_CEILING = 500_000
HYPOTHESIS = (
    "The exact post-dot prior-add schedule transfers uniformly from the frozen "
    "128-row slice to all 6,144 ff1_19 output rows and reproduces the retained "
    "6,291,456-word gradient byte-for-byte."
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
    inputs = [
        reference(PARENT_RESULT / "decision.json", "parent-decision"),
        reference(PARENT_RESULT / "execution.json", "parent-execution"),
        reference(PARENT_RESULT / "guard.json", "parent-guard"),
        reference(PARENT_REFLECTION, "parent-reflection"),
        reference(PARENT_RESULT / "open-treatment-slice.bf16", "parent-exact-slice"),
        reference(SOURCE_RESULT / "open-ff1-input.bf16", "open-ff1-input"),
        reference(RESIDUAL, "source-exact-ff1-output-residual"),
        reference(FIXTURE / "decision.json", "fixture-decision"),
        reference(
            FIXTURE / "fixture/gradients/0002_ff1_19.bin",
            "retained-ff1-19-gradient",
        ),
        reference(
            FIXTURE / "fixture/gradients/0002_ff1_19.meta",
            "retained-ff1-19-gradient-meta",
        ),
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
        measurement("antecedentsPass", "boolean", "The exact slice, operands, retained comparator, reflection, and guards remain hash-bound."),
        measurement("inputFeatureCount", "features", "Input features covered by the complete projection."),
        measurement("outputFeatureCount", "features", "FF1 output features covered by the complete projection."),
        measurement("gradientElementCount", "BF16 elements", "Words in the complete ff1_19 gradient."),
        measurement("outputBlockCount", "128-row blocks", "Prospectively partitioned output-row blocks."),
        measurement("exactOutputBlockCount", "128-row blocks", "Partitions with zero comparator mismatches."),
        measurement("treatmentMismatchCount", "BF16 elements", "Complete open-gradient words differing from the retained comparator."),
        measurement("maximumTreatmentAbsoluteError", "float32 value", "Maximum complete-gradient comparator error."),
        measurement("parentSliceMismatchCount", "BF16 elements", "First 128 full-output rows differing from the exact parent slice."),
        measurement("evaluationReplayIdentical", "boolean", "Two complete projections reproduce byte-for-byte."),
        measurement("forbiddenDynamicDependencyCount", "dependencies", "LibNC, GGML, BLAS, OpenMP, or CUDA dependencies in the open executable."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed candidate source."),
        measurement("guardedWorkRootPass", "boolean", "All transient build and evaluation payloads were removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-inputs", "inputFeatureCount", "eq", 1024),
        predicate("p-outputs", "outputFeatureCount", "eq", 6144),
        predicate("p-elements", "gradientElementCount", "eq", 6291456),
        predicate("p-blocks", "outputBlockCount", "eq", 48),
        predicate("p-exact-blocks", "exactOutputBlockCount", "eq", 48),
        predicate("p-treatment", "treatmentMismatchCount", "eq", 0),
        predicate("p-maximum", "maximumTreatmentAbsoluteError", "eq", 0.0),
        predicate("p-parent-slice", "parentSliceMismatchCount", "eq", 0),
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
                    PARENT_REVISION, "parent-revision"
                ).items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": HYPOTHESIS,
            "falsification": "Any complete-gradient or inherited-slice mismatch, inexact 128-row partition, replay failure, forbidden dependency, source failure, or resource failure rejects the uniform open boundary.",
        },
        "changedMechanism": "Expand the exact post-dot-add eight-lane kernel without arithmetic changes from 128 prospectively frozen FF1 output rows to all 6,144 rows.",
        "invariants": [
            "The exact open FF1 input, FF1-output adjoint, chronological state and stream order, BF16 conversion, and input-major output layout remain unchanged.",
            "One uniform arithmetic kernel covers all 6,291,456 coordinates; tolerance, coordinate repair, and row-specific selection are forbidden.",
            "The retained full gradient is consulted only after each complete open projection exists.",
            "The first 128 rows must independently retain the exact parent slice.",
            "No LibNC, GGML, BLAS, OpenMP, or CUDA dependency is permitted in the projection executable.",
        ],
        "controls": [
            {"id": "full-open-projection", "role": "treatment", "definition": "Apply the frozen post-dot-add kernel uniformly to all ff1_19 coordinates."},
            {"id": "retained-full-gradient", "role": "comparator", "definition": "Compare only after a complete open projection against the retained production ff1_19 gradient."},
            {"id": "parent-slice-retention", "role": "shifted", "definition": "Extract the first 128 output rows and compare them independently with the exact parent slice."},
            {"id": "partition-transfer", "role": "shifted", "definition": "Require exact parity independently in every prospectively fixed 128-row output partition."},
            {"id": "prior-and-nonfused-failures", "role": "negative", "definition": "Retain the parent's exact 43-word failure populations as the excluded arithmetic alternatives."},
            {"id": "independent-replay", "role": "replay", "definition": "Execute the complete 6,291,456-word projection twice."},
        ],
        "population": {
            "unit": "BF16 ff1_19 gradient words",
            "scopeBytes": 12582912,
            "scopeSymbols": 6291456,
            "selection": "Every coordinate in the complete 1,024-input by 6,144-output ff1_19 gradient, partitioned prospectively into 48 adjacent 128-row blocks.",
            "coordinate": "input-feature-major, then output-feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The complete exact open FF1 input and FF1-output adjoint.",
                "The exact parent slice arithmetic contract and reflection.",
                "The retained complete comparator after each projection exists.",
            ],
            "forbiddenInformation": [
                "Row-specific arithmetic, fitted corrections, tolerance, comparator-derived values, or any teacher dependency in the executable."
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
            "uncertaintyRisk": 0.1,
            "interactionRisk": 0.05,
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
            f"results/{CANDIDATE_ID}/source-exact-ff1-19-gradient.bf16",
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
