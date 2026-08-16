#!/usr/bin/env python3
"""Freeze the exact post-dot-add open FF1 weight-slice kernel."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_ff1_weight_slice_post_add_64_q0_v1"
PARENT_ID = "nncp_open_ff1_weight_slice_kernel_grid_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_open_ff1_weight_slice_post_add_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
PARENT_SOURCE = ROOT / (
    "programs/nncp_open_ff1_weight_slice_kernel_grid_64_q0_v1/"
    "ff1_weight_slice_kernel_grid.cpp"
)
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T115801Z_99a2e7695e.json"
)
SOURCE_RESULT = ROOT / "results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1"
RESIDUAL = ROOT / (
    "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/"
    "open-ff1-output-residual.bf16"
)
PARENT_REVISION = ROOT / json.loads((PARENT_RESULT / "decision.json").read_text())[
    "candidateRevision"
]["receipt"]["path"]
SOURCE_CEILING = 500_000
HYPOTHESIS = (
    "The post-dot prior-add AVX2 cell reproduces the complete LibNC treatment, "
    "reverse-state, and sign-negated FF1 weight slices exactly while retaining "
    "the frozen prior-initialized and nonfused mismatch populations."
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
        reference(PARENT_SOURCE, "parent-evaluator-source"),
        reference(SOURCE_RESULT / "open-ff1-input.bf16", "open-ff1-input"),
        reference(RESIDUAL, "source-exact-ff1-output-residual"),
        reference(
            SOURCE_RESULT / "libnc-treatment-slice.bf16",
            "libnc-treatment-slice",
        ),
        reference(
            SOURCE_RESULT / "libnc-reverse-control-slice.bf16",
            "libnc-reverse-control-slice",
        ),
        reference(
            SOURCE_RESULT / "libnc-negated-control-slice.bf16",
            "libnc-negated-control-slice",
        ),
        reference(RUNNER, "runner"),
        reference(MATERIALIZER, "materializer"),
        reference(DESCRIPTOR, "program-descriptor"),
    ]
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(reference(path, source_identifier(path)))
            present.add(relative)
    measurements = [
        measurement("antecedentsPass", "boolean", "The refuted grid, exact operands, independent oracles, reflection, and guards remain hash-bound."),
        measurement("sliceElementCount", "BF16 elements", "Words in every complete 128-by-1,024 arithmetic population."),
        measurement("treatmentMismatchCount", "BF16 elements", "Post-dot prior-add treatment words differing from the LibNC oracle."),
        measurement("maximumTreatmentAbsoluteError", "float32 value", "Maximum treatment/oracle absolute error."),
        measurement("priorControlMismatchCount", "BF16 elements", "Frozen prior-initialized FMA control words differing from the oracle."),
        measurement("nonfusedControlMismatchCount", "BF16 elements", "Frozen nonfused control words differing from the oracle."),
        measurement("reverseOracleMismatchCount", "BF16 elements", "Post-dot reverse-state words differing from the LibNC reverse oracle."),
        measurement("negatedOracleMismatchCount", "BF16 elements", "Post-dot sign-negated words differing from the LibNC negated oracle."),
        measurement("evaluationReplayIdentical", "boolean", "Two complete five-population evaluations reproduce byte-for-byte."),
        measurement("forbiddenDynamicDependencyCount", "dependencies", "LibNC, GGML, BLAS, OpenMP, or CUDA dependencies in the open executable."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed candidate source."),
        measurement("guardedWorkRootPass", "boolean", "All transient build and evaluation payloads were removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-slice", "sliceElementCount", "eq", 131072),
        predicate("p-treatment", "treatmentMismatchCount", "eq", 0),
        predicate("p-treatment-maximum", "maximumTreatmentAbsoluteError", "eq", 0.0),
        predicate("p-prior-control", "priorControlMismatchCount", "eq", 43),
        predicate("p-nonfused-control", "nonfusedControlMismatchCount", "eq", 43),
        predicate("p-reverse", "reverseOracleMismatchCount", "eq", 0),
        predicate("p-negated", "negatedOracleMismatchCount", "eq", 0),
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
            "falsification": "Any treatment, reverse, or negated mismatch; changed control population; replay failure; forbidden dependency; source failure; or resource failure rejects the exact open kernel.",
        },
        "changedMechanism": "Promote only the prospectively frozen post-dot prior-add cell: accumulate each 32-stream dot from zero with sequential AVX2 FMAs, add the decoded prior BF16 gradient, then materialize BF16 once per state.",
        "invariants": [
            "The exact open FF1 input, FF1-output adjoint, prior gradient, state order, stream order, row selection, and BF16 state boundaries remain unchanged.",
            "One uniform post-dot-add kernel covers all slice coordinates; tolerance and coordinate repair are forbidden.",
            "The independent LibNC treatment and reverse/sign controls are consulted only after both complete open populations exist.",
            "The prior-initialized FMA and nonfused mismatch populations remain frozen controls rather than search inputs.",
            "No LibNC, GGML, BLAS, OpenMP, or CUDA dependency is permitted in the treatment executable.",
        ],
        "controls": [
            {"id": "post-dot-prior-add", "role": "treatment", "definition": "Accumulate 32 products from zero with sequential AVX2 FMAs, add the decoded prior BF16 gradient, then materialize BF16 once."},
            {"id": "libnc-slice", "role": "comparator", "definition": "Compare only after two complete populations against the exact chronological LibNC treatment slice."},
            {"id": "prior-initialized-fma", "role": "negative", "definition": "Retain the frozen 43-word mismatch population from initializing the accumulator with the prior gradient."},
            {"id": "nonfused-multiply-add", "role": "negative", "definition": "Retain the frozen 43-word mismatch population from separate multiply/add arithmetic."},
            {"id": "reverse-and-negated", "role": "shifted", "definition": "Apply the post-dot kernel to reverse-state and sign-negated populations and compare with independent LibNC controls."},
            {"id": "independent-replay", "role": "replay", "definition": "Execute all five complete populations twice."},
        ],
        "population": {
            "unit": "BF16 ff1_19 gradient words",
            "scopeBytes": 262144,
            "scopeSymbols": 131072,
            "selection": "Every coordinate in the prospectively frozen 128-adjacent-output by 1,024-input slice across all 64 states and 32 streams.",
            "coordinate": "input-major, then adjacent-output-feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The complete exact open FF1 input and FF1-output adjoint.",
                "The attributed state, stream, and eight-lane output-feature mapping.",
                "The refuted grid's prospectively measured post-dot-add cell.",
                "The exact independent LibNC oracles after population completion.",
            ],
            "forbiddenInformation": [
                "Coordinate-specific arithmetic choices, fitted corrections, tolerance, or any teacher dependency in the executable."
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
            "uncertaintyRisk": 0.05,
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
            f"results/{CANDIDATE_ID}/open-treatment-slice.bf16",
            f"results/{CANDIDATE_ID}/open-prior-control-slice.bf16",
            f"results/{CANDIDATE_ID}/open-nonfused-control-slice.bf16",
            f"results/{CANDIDATE_ID}/open-reverse-slice.bf16",
            f"results/{CANDIDATE_ID}/open-negated-slice.bf16",
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
