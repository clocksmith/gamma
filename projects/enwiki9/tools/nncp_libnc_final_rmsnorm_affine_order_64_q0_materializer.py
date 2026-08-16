#!/usr/bin/env python3
"""Freeze bias-aware production BF16 final-RMSNorm order attribution."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_final_rmsnorm_affine_order_64_q0_v1"
PARENT_ID = "nncp_libnc_final_rmsnorm_order_64_q0_retry_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / "tools/nncp_libnc_final_rmsnorm_affine_order_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T072334216369Z_8c6e24f42831.json"
)
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T072401Z_436d248c4d.json"
)
SOURCE_ADJOINT_RESULT = ROOT / (
    "results/nncp_libnc_top_ff2_adjoint_64_q0_retry_v1"
)
OPEN_RESULT = ROOT / "results/nncp_open_profile_top_ff2_gradient_64_q0_retry_v1"
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
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
        reference(PARENT_RESULT / "decision.json", "parent-invalid-decision"),
        reference(PARENT_RESULT / "execution.json", "parent-invalid-execution"),
        reference(PARENT_REFLECTION, "parent-invalid-reflection"),
        reference(
            PARENT_RESULT / "source-final-rms-input.bf16",
            "source-final-rms-input",
        ),
        reference(
            PARENT_RESULT / "source-final-rms-output.bf16",
            "source-final-rms-affine-output",
        ),
        reference(
            SOURCE_ADJOINT_RESULT / "decision.json",
            "source-adjoint-decision",
        ),
        reference(
            SOURCE_ADJOINT_RESULT / "source-top-ff2-adjoint.bf16",
            "source-final-rms-input-adjoint",
        ),
        reference(OPEN_RESULT / "decision.json", "open-tail-decision"),
        reference(
            OPEN_RESULT / "open-final-hidden-residual.bf16",
            "open-incoming-residual",
        ),
        reference(
            OPEN_RESULT / "open-final-norm-input-residual.bf16",
            "open-input-adjoint",
        ),
        reference(
            FIXTURE_ROOT / "fixture/parameters_initial.coefs",
            "production-initial-parameters",
        ),
        reference(PROGRAM / "final_rmsnorm_order.cpp", "evaluator-source"),
        reference(PROGRAM / "program.py", "program-descriptor"),
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
            "The repeated source input/affine output, exact source adjoint, open incoming and input residuals, invalid-parent reflection, and production parameters remain valid and digest-bound.",
        ),
        measurement(
            "evaluationReplayIdentical",
            "boolean",
            "Two independent evaluator executions reproduce normalized, affine, six-order, and control payloads byte-for-byte.",
        ),
        measurement(
            "gainAllOne",
            "boolean",
            "Every digest-bound ln_g_40 BF16 word is exactly one.",
        ),
        measurement(
            "biasDistinctWordCount",
            "BF16 words",
            "Distinct digest-bound ln_b_40 words proving the affine bias is not a zero scalar.",
        ),
        measurement(
            "biasNonzeroWordCount",
            "BF16 elements",
            "Nonzero digest-bound ln_b_40 elements.",
        ),
        measurement(
            "affineMismatchCount",
            "BF16 activation elements",
            "Captured source affine-output words differing from reconstructed normalized plus ln_b_40 output.",
        ),
        measurement(
            "maximumAffineAbsoluteError",
            "float32 value",
            "Maximum source versus reconstructed affine-output absolute difference.",
        ),
        measurement(
            "currentOpenMismatchCount",
            "BF16 gradient elements",
            "Current pre-centered FMA replay words differing from the retained open input residual.",
        ),
        measurement(
            "maximumCurrentOpenAbsoluteError",
            "float32 value",
            "Maximum current-order replay versus retained open residual absolute difference.",
        ),
        measurement(
            "currentSourceMismatchCount",
            "BF16 gradient elements",
            "Current pre-centered FMA replay words differing from the independent source input adjoint.",
        ),
        measurement(
            "openSourceMismatchCount",
            "BF16 gradient elements",
            "Retained open input-residual words differing from the independent source input adjoint.",
        ),
        measurement(
            "exactVariantCount",
            "operation orders",
            "Frozen arithmetic orders reproducing every independent source-adjoint word exactly.",
        ),
        measurement(
            "negatedControlDiffers",
            "boolean",
            "Negating the incoming residual changes the complete reconstructed adjoint.",
        ),
        measurement(
            "incrementalSourceBytes",
            "bytes",
            "Compressed dependency-closed evaluator and orchestration source package.",
        ),
        measurement(
            "guardedWorkRootPass",
            "boolean",
            "The compiled evaluator and all replay payloads remained under and were removed with the guarded work root.",
        ),
    ]
    expected = {
        "antecedentsPass": True,
        "evaluationReplayIdentical": True,
        "gainAllOne": True,
        "affineMismatchCount": 0,
        "maximumAffineAbsoluteError": 0,
        "currentOpenMismatchCount": 0,
        "maximumCurrentOpenAbsoluteError": 0,
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
            predicate("p-bias-distinct", "biasDistinctWordCount", "gt", 1),
            predicate("p-bias-live", "biasNonzeroWordCount", "gt", 0),
            predicate(
                "p-current-source-differs",
                "currentSourceMismatchCount",
                "gt",
                0,
            ),
            predicate(
                "p-open-source-differs", "openSourceMismatchCount", "gt", 0
            ),
            predicate(
                "p-source-ceiling",
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
            "claim": "The digest-bound ln_b_40 affine replay validates the reconstructed raw normalized output, the current pre-centered FMA order exactly reproduces the retained open residual but differs from source, and exactly one unchanged alternative order reproduces every source-adjoint word.",
            "falsification": "Any antecedent or replay drift, non-one gain, dead bias or control, affine mismatch, current-versus-open mismatch, exact current-versus-source match, zero/nonunique alternative match, source overflow, or guard failure prevents promotion.",
        },
        "changedMechanism": "Replace the false zero-bias assumption with digest-bound ln_g_40/ln_b_40 extraction, validate the reconstructed normalized output by exact affine replay against the retained production output, then apply the unchanged six-order family to the retained production input and independent source adjoint.",
        "invariants": [
            "The retained production input and affine output are consumed exactly as captured; no teacher or production executable is rerun.",
            "The raw normalized output is accepted only if adding the digest-bound ln_b_40 under all-one ln_g_40 reproduces every captured affine-output BF16 word.",
            "The current pre-centered FMA evaluator must reproduce every retained open input-residual word before alternative orders are interpreted.",
            "The six backward orders, width-1024 AVX reductions, incoming residual, source adjoint, coordinates, and exact no-tolerance comparators are unchanged from the invalid parent.",
            "Both evaluator runs finish before the source adjoint classifies any order as exact.",
            "All source, teacher, LibNC, open-shadow, and retained tensor evidence remains zero-credit and may not ship in a submitted codec.",
        ],
        "controls": [
            {
                "id": "source-affine-replay",
                "role": "treatment",
                "definition": "Reconstructed raw normalization plus digest-bound bias must reproduce the retained source affine output exactly.",
            },
            {
                "id": "current-open-replay",
                "role": "comparator",
                "definition": "The frozen current order must reproduce the retained open residual exactly before source comparison.",
            },
            {
                "id": "independent-source-adjoint",
                "role": "comparator",
                "definition": "The expected adjoint comes from the separate source capture that exactly reconstructs ff2_19.",
            },
            {
                "id": "independent-evaluator-replay",
                "role": "replay",
                "definition": "Every normalized, affine, order, and negative-control payload is generated twice and must be byte-identical.",
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
            "selection": "All retained 64 states across 32 streams: 2,097,152 input, affine-output, incoming-residual, open-adjoint, and source-adjoint words plus 1,024 gain and bias words.",
            "coordinate": "First retained production update over transformed-symbol coordinates [256,320) independently within each of 32 streams.",
        },
        "causalBoundary": {
            "availableInformation": [
                "Digest-bound repeated production input/affine output, initial affine parameters, exact source adjoint, open incoming/input residuals, invalid-parent reflection, and the prospectively unchanged finite order family.",
                "The parent result establishes only that its read-only source capture is repeatable and that its output semantic was mislabeled; it supplies no operation-order verdict.",
            ],
            "forbiddenInformation": [
                "Using any retained tensor, teacher executable, LibNC dependency, hidden trace, or uncounted probability in a submitted codec.",
                "Changing the six-order family after comparison, applying coordinate-specific corrections, tolerating BF16 differences, or claiming compression benefit from this oracle.",
            ],
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/open-final-rms-normalized.bf16",
            f"results/{CANDIDATE_ID}/ln-b-40.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-nonunique-order", "exactVariantCount", "gt", 1),
            predicate(
                "k-current-source-exact", "currentSourceMismatchCount", "eq", 0
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
            "expectedRuntimeRatio": 0.01,
            "expectedMemoryRatio": 0.01,
            "interactionRisk": 0.1,
            "uncertaintyRisk": 0.1,
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
