#!/usr/bin/env python3
"""Freeze the exact production BF16 final-RMSNorm operation-order gate."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_final_rmsnorm_order_64_q0_v1"
PARENT_ID = "nncp_libnc_top_ff2_adjoint_64_q0_retry_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_final_rmsnorm_order_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T065021151451Z_f614bd733469.json"
)
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T065037Z_1d8853ab41.json"
)
OPEN_ID = "nncp_open_profile_top_ff2_gradient_64_q0_retry_v1"
OPEN_RESULT = ROOT / "results" / OPEN_ID
OPEN_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T061837Z_1dfa2ae8f8.json"
)
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_HOOK = ROOT / "tools/nncp_profile_update_fixture_hook_q3.c"
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
        reference(PARENT_RESULT / "decision.json", "parent-source-decision"),
        reference(PARENT_REFLECTION, "parent-source-reflection"),
        reference(
            PARENT_RESULT / "source-top-ff2-adjoint.bf16",
            "parent-source-adjoint",
        ),
        reference(OPEN_RESULT / "decision.json", "open-tail-decision"),
        reference(OPEN_REFLECTION, "open-tail-reflection"),
        reference(
            OPEN_RESULT / "open-final-hidden-residual.bf16",
            "open-incoming-residual",
        ),
        reference(
            OPEN_RESULT / "open-final-norm-input-residual.bf16",
            "open-input-adjoint",
        ),
        reference(FIXTURE_ROOT / "decision.json", "production-fixture-decision"),
        reference(
            FIXTURE_ROOT / "fixture-manifest.json",
            "production-fixture-manifest",
        ),
        reference(FIXTURE_ROOT / "guard.json", "production-fixture-guard"),
        reference(PROGRAM / "final_rmsnorm_probe.inc.c", "probe-source"),
        reference(PROGRAM / "final_rmsnorm_order.cpp", "evaluator-source"),
        reference(PROGRAM / "program.py", "program-descriptor"),
        reference(FIXTURE_HOOK, "production-fixture-hook"),
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
            "The exact production fixture, source FF2 adjoint, open incoming residual, and failed open RMSNorm residual remain valid and digest-bound.",
        ),
        measurement(
            "sourceCaptureRepeatIdentical",
            "boolean",
            "Two complete read-only production captures have identical directory aggregates.",
        ),
        measurement(
            "combinedReplayIdentical",
            "boolean",
            "Both captures combine to identical complete input and output BF16 populations.",
        ),
        measurement(
            "evaluationReplayIdentical",
            "boolean",
            "The forward reconstruction, six frozen orders, and negative control are byte-identical across both captures.",
        ),
        measurement(
            "parentFixtureIdentity",
            "boolean",
            "Every non-probe production artifact remains byte-identical to the retained q3 fixture in both captures.",
        ),
        measurement(
            "capturedStateCount",
            "states",
            "Sequential final-RMSNorm production states captured at the first retained update.",
        ),
        measurement(
            "sourceInputElementCount",
            "BF16 activation elements",
            "Complete production final-RMSNorm input population.",
        ),
        measurement(
            "sourceOutputElementCount",
            "BF16 activation elements",
            "Complete production final-RMSNorm affine-output population, equal to the normalized output under the digest-bound all-one gain and zero bias.",
        ),
        measurement(
            "forwardMismatchCount",
            "BF16 activation elements",
            "Captured output words differing from the frozen width-1024 forward reduction and rounding contract.",
        ),
        measurement(
            "maximumForwardAbsoluteError",
            "float32 value",
            "Maximum captured-output versus reconstructed-output absolute difference.",
        ),
        measurement(
            "openInputAdjointMismatchCount",
            "BF16 gradient elements",
            "Already localized source-adjoint words differing from the current open centered-FMA order.",
        ),
        measurement(
            "currentVariantMismatchCount",
            "BF16 gradient elements",
            "Source-adjoint words differing from an independently regenerated current pre-centered FMA order.",
        ),
        measurement(
            "exactVariantCount",
            "operation orders",
            "Frozen arithmetic-order variants reproducing every source-adjoint word exactly.",
        ),
        measurement(
            "negatedControlDiffers",
            "boolean",
            "Negating the incoming residual changes the complete reconstructed adjoint.",
        ),
        measurement(
            "incrementalSourceBytes",
            "bytes",
            "Compressed dependency-closed instrumentation, evaluator, and orchestration source package.",
        ),
        measurement(
            "guardedWorkRootPass",
            "boolean",
            "Generated builds and complete source captures remained under and were removed with the guarded work root.",
        ),
    ]
    expected = {
        "antecedentsPass": True,
        "sourceCaptureRepeatIdentical": True,
        "combinedReplayIdentical": True,
        "evaluationReplayIdentical": True,
        "parentFixtureIdentity": True,
        "capturedStateCount": 64,
        "sourceInputElementCount": 2_097_152,
        "sourceOutputElementCount": 2_097_152,
        "forwardMismatchCount": 0,
        "maximumForwardAbsoluteError": 0,
        "exactVariantCount": 1,
        "negatedControlDiffers": True,
        "guardedWorkRootPass": True,
    }
    promotion = [
        predicate(f"p-{name.lower()}", name, "eq", threshold)
        for name, threshold in expected.items()
    ]
    promotion.extend(
        [
            predicate(
                "p-open-adjoint-mismatch",
                "openInputAdjointMismatchCount",
                "gt",
                0,
            ),
            predicate(
                "p-current-order-refuted",
                "currentVariantMismatchCount",
                "gt",
                0,
            ),
            predicate(
                "p-incremental-source-bytes",
                "incrementalSourceBytes",
                "lte",
                SOURCE_CEILING,
            ),
        ]
    )
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
            "claim": "Exactly one member of the frozen six-order BF16 family reproduces all 2,097,152 production final-RMSNorm input-adjoint words, while the current pre-centered FMA order retains a nonzero mismatch.",
            "falsification": "Any antecedent drift, fixture mutation, capture or evaluator replay difference, forward mismatch, dead control, geometry or guard failure, exact current-order match, or zero/nonunique alternative match prevents operation-order promotion.",
        },
        "changedMechanism": "Read-only capture of the production final-RMSNorm input and affine output at update block 256, followed by exact replay of six frozen centered or standard FMA/split subtraction orders against the independently retained source input adjoint.",
        "invariants": [
            "Instrumentation only copies the existing final-RMSNorm input and output; it inserts no node, parameter, value, branch, or altered production operation.",
            "Both complete production runs and all six reconstruction payloads finish before any order is classified as exact.",
            "The forward inverse and mean reductions reuse the frozen width-1024 AVX reduction tree; only the per-element centered subtraction/FMA order varies.",
            "The first retained update has digest-bound all-one ln_g_40 and zero ln_b_40, so the captured affine output is the BF16 normalized output and the promoted incoming residual is the RMSNorm upstream.",
            "The teacher, LibNC executable, captured tensors, source adjoint, open residuals, and operation-order oracle receive zero objective credit and may not ship in a submitted codec.",
            "This gate identifies one arithmetic boundary; it proves no broader transformer backward, recursive adaptation, archive saving, package, transfer, or Hutter result.",
        ],
        "controls": [
            {
                "id": "read-only-production-capture",
                "role": "treatment",
                "definition": "Final-RMSNorm input and output are copied without changing the graph or values.",
            },
            {
                "id": "retained-complete-fixture",
                "role": "comparator",
                "definition": "Every non-probe artifact must match the retained production fixture in both captures.",
            },
            {
                "id": "independent-source-adjoint",
                "role": "comparator",
                "definition": "The expected input adjoint comes from the separately completed zero-add source capture that exactly reconstructs ff2_19.",
            },
            {
                "id": "independent-source-replay",
                "role": "replay",
                "definition": "The complete production capture and every arithmetic-order evaluation execute twice and reproduce identical bytes.",
            },
            {
                "id": "negated-incoming-residual",
                "role": "negative",
                "definition": "Sign-negating the complete incoming residual must change the reconstructed input adjoint.",
            },
        ],
        "population": {
            "unit": "one production state or BF16 activation/gradient word",
            "scopeBytes": None,
            "scopeSymbols": 2048,
            "selection": "All 64 sequential states across all 32 streams at update block 256, comprising 2,097,152 input, 2,097,152 normalized-output, 2,097,152 incoming-residual, and 2,097,152 source-adjoint words.",
            "coordinate": "First retained production update over original transformed-symbol coordinates [256,320) independently within each of 32 contiguous streams.",
        },
        "causalBoundary": {
            "availableInformation": [
                "Digest-bound production source, model, vocabulary, corpus, complete q3 fixture, exact source input adjoint, exact open incoming residual, and the prospectively frozen finite order family.",
                "Captured final-RMSNorm inputs and outputs only as zero-credit teacher attribution evidence after both source executions finish.",
            ],
            "forbiddenInformation": [
                "Using any source-captured tensor, teacher executable, LibNC dependency, hidden trace, or uncounted probability in a submitted codec.",
                "Adding a comparator-derived coordinate correction, changing the six-order family after observation, tolerating BF16 differences, or claiming compression benefit from this attribution gate.",
            ],
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-final-rms-input.bf16",
            f"results/{CANDIDATE_ID}/source-final-rms-output.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate(
                "k-nonunique-order", "exactVariantCount", "gt", 1
            ),
            predicate(
                "k-current-order-exact", "currentVariantMismatchCount", "eq", 0
            ),
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
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 1.0,
            "interactionRisk": 0.1,
            "uncertaintyRisk": 0.2,
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
