#!/usr/bin/env python3
"""Freeze the LibNC-free FF1 weight-slice arithmetic grid."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_ff1_weight_slice_kernel_grid_64_q0_v1"
PARENT_ID = "nncp_libnc_ff1_weight_slice_schedule_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_open_ff1_weight_slice_kernel_grid_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
EVALUATOR = PROGRAM / "ff1_weight_slice_kernel_grid.cpp"
DESCRIPTOR = PROGRAM / "program.py"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T114029Z_4b8fd50e01.json"
)
RESIDUAL = ROOT / (
    "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/"
    "open-ff1-output-residual.bf16"
)
PARENT_REVISION = ROOT / json.loads((PARENT_RESULT / "decision.json").read_text())[
    "candidateRevision"
]["receipt"]["path"]
SOURCE_CEILING = 500_000


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
        reference(PARENT_RESULT / "open-ff1-input.bf16", "open-ff1-input"),
        reference(RESIDUAL, "source-exact-ff1-output-residual"),
        reference(
            PARENT_RESULT / "libnc-treatment-slice.bf16",
            "libnc-treatment-slice",
        ),
        reference(
            PARENT_RESULT / "libnc-reverse-control-slice.bf16",
            "libnc-reverse-control-slice",
        ),
        reference(
            PARENT_RESULT / "libnc-negated-control-slice.bf16",
            "libnc-negated-control-slice",
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
        measurement("antecedentsPass", "boolean", "The exact state-scheduled LibNC slice, open operands, controls, reflection, and guards remain hash-bound."),
        measurement("sliceElementCount", "BF16 elements", "Words in every complete 128-by-1,024 arithmetic cell."),
        measurement("priorFmaMismatchCount", "BF16 elements", "Prior-initialized sequential-FMA words differing from the LibNC treatment oracle."),
        measurement("maximumPriorFmaAbsoluteError", "float32 value", "Maximum prior-FMA/oracle error."),
        measurement("postAddMismatchCount", "BF16 elements", "Post-dot prior-add words differing from the treatment oracle."),
        measurement("nonfusedMismatchCount", "BF16 elements", "Separate multiply/add words differing from the treatment oracle."),
        measurement("reverseOracleMismatchCount", "BF16 elements", "Open reverse-state words differing from the LibNC reverse oracle."),
        measurement("negatedOracleMismatchCount", "BF16 elements", "Open sign-negated words differing from the LibNC sign-negated oracle."),
        measurement("evaluationReplayIdentical", "boolean", "Two complete five-cell populations reproduce byte-for-byte."),
        measurement("forbiddenDynamicDependencyCount", "dependencies", "LibNC, GGML, BLAS, OpenMP, or CUDA dependencies in the open evaluator."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed candidate source."),
        measurement("guardedWorkRootPass", "boolean", "All transient build and evaluation payloads were removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-slice", "sliceElementCount", "eq", 131072),
        predicate("p-prior-fma", "priorFmaMismatchCount", "eq", 0),
        predicate("p-prior-fma-maximum", "maximumPriorFmaAbsoluteError", "eq", 0.0),
        predicate("p-post-live", "postAddMismatchCount", "gt", 0),
        predicate("p-nonfused-live", "nonfusedMismatchCount", "gt", 0),
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
                key: value for key, value in
                reference(PARENT_REVISION, "parent-revision").items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": "Initializing eight adjacent output-feature lanes from the prior BF16 gradient and applying 32 sequential AVX2 FMAs before one BF16 state-boundary conversion reproduces the exact LibNC ff1_19 slice and its reverse/sign controls.",
            "falsification": "Any prior-FMA, reverse-oracle, or negated-oracle mismatch, a non-distinct post-add or nonfused cell, replay failure, forbidden dependency, source failure, or resource failure rejects this open contract.",
        },
        "changedMechanism": "Replace the digest-bound LibNC matrix update with an explicit open eight-lane kernel and cross prior-initialized fused accumulation against post-dot prior addition and nonfused multiply/add arithmetic while preserving all 64 state boundaries.",
        "invariants": [
            "The exact open FF1 input, exact FF1-output adjoint, state order, stream order, row selection, and BF16 state-boundary materialization remain unchanged.",
            "All cells use uniform arithmetic over all 131,072 slice coordinates; tolerance and coordinate repair are forbidden.",
            "The independent LibNC treatment and reverse/sign controls are consulted only after both complete open populations exist.",
            "No LibNC, GGML, BLAS, OpenMP, or CUDA dependency is permitted in the treatment executable.",
        ],
        "controls": [
            {"id": "prior-initialized-fma", "role": "treatment", "definition": "Decode eight prior BF16 gradient words, apply streams 0 through 31 as sequential AVX2 FMAs, then materialize BF16 once."},
            {"id": "libnc-slice", "role": "comparator", "definition": "Compare only after two complete open populations against the exact chronological LibNC slice."},
            {"id": "post-dot-prior-add", "role": "negative", "definition": "Accumulate the 32 products from zero and add the decoded prior gradient only after the dot."},
            {"id": "nonfused-multiply-add", "role": "negative", "definition": "Start from the prior gradient but use separate AVX2 multiply and add instructions."},
            {"id": "reverse-and-negated", "role": "negative", "definition": "Apply the treatment kernel to reverse-state and sign-negated populations and compare with their independent LibNC controls."},
            {"id": "independent-replay", "role": "replay", "definition": "Execute all five complete cells twice."},
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
                "The exact independent LibNC treatment and reverse/sign control slices after population completion."
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
            "expectedTransferRetention": 0.0,
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 1.0,
            "uncertaintyRisk": 0.2,
            "interactionRisk": 0.1,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-prior-fma", "priorFmaMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/open-prior-fma-slice.bf16",
            f"results/{CANDIDATE_ID}/open-post-add-slice.bf16",
            f"results/{CANDIDATE_ID}/open-nonfused-slice.bf16",
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
