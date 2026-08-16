#!/usr/bin/env python3
"""Freeze exact final-RMSNorm backward reduction/scale attribution."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1"
PARENT_ID = "nncp_libnc_final_rmsnorm_affine_order_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_final_rmsnorm_reduction_scale_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T074218Z_9b38a51094.json"
)
CAPTURE_RESULT = ROOT / "results/nncp_libnc_final_rmsnorm_order_64_q0_retry_v1"
SOURCE_RESULT = ROOT / "results/nncp_libnc_top_ff2_adjoint_64_q0_retry_v1"
OPEN_RESULT = ROOT / "results/nncp_open_profile_top_ff2_gradient_64_q0_retry_v1"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T074151586602Z_9d29603e7a8c.json"
)
SOURCE_CEILING = 1_000_000


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


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    digest = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{digest}"


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


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    inputs = [
        reference(PARENT_RESULT / "decision.json", "parent-decision"),
        reference(PARENT_RESULT / "execution.json", "parent-execution"),
        reference(PARENT_REFLECTION, "parent-reflection"),
        reference(
            CAPTURE_RESULT / "source-final-rms-input.bf16",
            "source-final-rms-input",
        ),
        reference(
            PARENT_RESULT / "open-final-rms-normalized.bf16",
            "open-final-rms-normalized",
        ),
        reference(
            SOURCE_RESULT / "source-top-ff2-adjoint.bf16",
            "source-final-rms-input-adjoint",
        ),
        reference(
            OPEN_RESULT / "open-final-hidden-residual.bf16",
            "open-incoming-residual",
        ),
        reference(
            OPEN_RESULT / "open-final-norm-input-residual.bf16",
            "open-input-adjoint",
        ),
        reference(CAPTURE_RESULT / "execution.json", "source-capture-execution"),
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
            "The exact affine replay, eight-word source/open boundary, retained tensors, reflection, and source-library digest remain bound.",
        ),
        measurement(
            "evaluationReplayIdentical",
            "boolean",
            "Two independent executions reproduce all four factorial variants and the negative control byte-for-byte.",
        ),
        measurement(
            "baselineOpenMismatchCount",
            "BF16 gradient elements",
            "Generic-dot mean-scaled baseline words differing from the retained open adjoint.",
        ),
        measurement(
            "baselineSourceMismatchCount",
            "BF16 gradient elements",
            "Generic-dot mean-scaled baseline words differing from the independent source adjoint.",
        ),
        measurement(
            "streamDotWidthScaledMismatchCount",
            "BF16 gradient elements",
            "Disassembly-derived streaming-dot, width-scaled replay words differing from the independent source adjoint.",
        ),
        measurement(
            "exactVariantCount",
            "reduction/scale variants",
            "Prospectively frozen factorial variants reproducing every independent source-adjoint word.",
        ),
        measurement(
            "alternativeExactCount",
            "reduction/scale variants",
            "Source-exact variants other than the streaming-dot, width-scaled treatment.",
        ),
        measurement(
            "negatedControlDiffers",
            "boolean",
            "Negating the incoming residual changes the complete treatment adjoint.",
        ),
        measurement(
            "sourceLibraryDigestBound",
            "boolean",
            "The captured production execution identifies the expected LibNC SHA-256 used for static kernel attribution.",
        ),
        measurement(
            "incrementalSourceBytes",
            "bytes",
            "Compressed dependency-closed evaluator and orchestration source package.",
        ),
        measurement(
            "guardedWorkRootPass",
            "boolean",
            "The compiled evaluator and replay payloads were removed with the guarded work root.",
        ),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-replay", "evaluationReplayIdentical", "eq", True),
        predicate("p-baseline-open", "baselineOpenMismatchCount", "eq", 0),
        predicate("p-baseline-source", "baselineSourceMismatchCount", "eq", 8),
        predicate(
            "p-treatment-source",
            "streamDotWidthScaledMismatchCount",
            "eq",
            0,
        ),
        predicate("p-unique", "exactVariantCount", "eq", 1),
        predicate("p-no-alternative", "alternativeExactCount", "eq", 0),
        predicate("p-negative", "negatedControlDiffers", "eq", True),
        predicate("p-library", "sourceLibraryDigestBound", "eq", True),
        predicate(
            "p-source-ceiling", "incrementalSourceBytes", "lte", SOURCE_CEILING
        ),
        predicate("p-guard", "guardedWorkRootPass", "eq", True),
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
            "claim": "Exactly the disassembly-derived combination of a streaming eight-lane BF16 dot reduction and width-scaled fused backward expression reproduces every retained source final-RMSNorm input-adjoint word; the other three factorial combinations do not.",
            "falsification": "Any antecedent, baseline, replay, digest, control, source, or guard failure, or a zero/nonunique source-exact treatment, prevents promotion.",
        },
        "changedMechanism": "Hold the exact forward normalization, generic BF16 sum, incoming residual, and final BF16 rounding fixed while crossing generic versus streaming dot reduction with mean-scaled versus width-scaled fused backward evaluation.",
        "invariants": [
            "No teacher or production executable is rerun; every tensor is a digest-bound retained artifact.",
            "The generic-dot mean-scaled cell must reproduce the retained open adjoint exactly before source attribution.",
            "The four cells form a frozen two-by-two factorial: only dot reduction and backward scalar placement vary.",
            "The streaming dot uses one AVX2 accumulator across 128 ordered eight-lane BF16 product FMAs followed by the source horizontal tree.",
            "The width-scaled expression computes width*g-sum(g)-normalized*dot and multiplies once by inverse/width before BF16 rounding.",
            "All source, disassembly, LibNC, open-shadow, and retained-tensor evidence remains zero-credit and cannot ship in a submitted codec.",
        ],
        "controls": [
            {
                "id": "open-baseline",
                "role": "comparator",
                "definition": "The unchanged generic-dot mean-scaled cell reproduces the retained open adjoint.",
            },
            {
                "id": "factorial-isolation",
                "role": "treatment",
                "definition": "Four cells isolate streaming dot reduction, width scaling, and their interaction.",
            },
            {
                "id": "independent-source-adjoint",
                "role": "comparator",
                "definition": "The target adjoint comes from the separate source capture that exactly reconstructs ff2_19.",
            },
            {
                "id": "independent-evaluator-replay",
                "role": "replay",
                "definition": "All output payloads are generated twice before source classification.",
            },
            {
                "id": "negated-incoming-residual",
                "role": "negative",
                "definition": "Negating the incoming residual must change the treatment output.",
            },
        ],
        "population": {
            "unit": "one production state or BF16 gradient word",
            "scopeBytes": None,
            "scopeSymbols": 2048,
            "selection": "All retained 64 states across 32 streams and all 1,024 final-normalization features.",
            "coordinate": "First retained production update over transformed-symbol coordinates [256,320) independently within each stream.",
        },
        "causalBoundary": {
            "availableInformation": [
                "Digest-bound source input, normalized output, incoming residual, open adjoint, source adjoint, parent decision/reflection, source execution digest, and the prospectively frozen four-cell family.",
                "Static source-kernel attribution identifies an eight-lane streaming dot and width-scaled fused expression, but no replay result was consulted before freezing this contract.",
            ],
            "forbiddenInformation": [
                "Changing the four-cell family after comparison, coordinate-specific correction, tolerance, teacher rerun, or compression credit from the oracle.",
                "Using LibNC, its disassembly, retained tensors, or hidden traces in a submitted codec.",
            ],
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-exact-final-rms-adjoint.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-nonunique", "exactVariantCount", "gt", 1)
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
            "interactionRisk": 0.05,
            "uncertaintyRisk": 0.05,
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
