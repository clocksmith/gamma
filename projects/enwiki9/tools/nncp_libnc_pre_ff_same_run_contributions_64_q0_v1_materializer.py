#!/usr/bin/env python3
"""Freeze the same-run pre-FF contribution attribution oracle."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_v1"
PARENT_ID = "nncp_libnc_bf16_gradient_merge_64_q0_retry_v5"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RUNNER = ROOT / "tools/nncp_libnc_pre_ff_same_run_contributions_64_q0_v1.py"
MATERIALIZER = Path(__file__).resolve()
PROBE = PROGRAM / "same_run_probe.c"
COMPOSER = PROGRAM / "compose_bf16.cpp"
DESCRIPTOR = PROGRAM / "program.py"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T151453Z_cbf1bff98d.json"
)
TOTAL_RESULT = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2"
)
BRANCH_RESULT = ROOT / (
    "results/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2"
)
OPEN_DIRECT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
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
        raise ValueError(f"same-run input is not a project file: {path}")
    return {
        "id": identifier,
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    suffix = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{suffix}"


def measurement(identifier: str, unit: str, definition: str) -> dict[str, str]:
    return {"id": identifier, "unit": unit, "definition": definition}


def predicate(
    identifier: str, field: str, operator: str, threshold: object
) -> dict[str, object]:
    return {
        "id": identifier,
        "measurement": field,
        "operator": operator,
        "threshold": threshold,
    }


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    parent_decision = json.loads((PARENT_RESULT / "decision.json").read_text())
    parent_revision = ROOT / parent_decision["candidateRevision"]["receipt"]["path"]
    inputs = [
        reference(PARENT_RESULT / "decision.json", "parent-decision"),
        reference(PARENT_RESULT / "execution.json", "parent-execution"),
        reference(PARENT_RESULT / "guard.json", "parent-guard"),
        reference(PARENT_REFLECTION, "parent-reflection"),
        reference(
            TOTAL_RESULT / "source-pre-ff-hidden-adjoint.bf16",
            "sealed-source-total",
        ),
        reference(TOTAL_RESULT / "decision.json", "sealed-total-decision"),
        reference(
            BRANCH_RESULT / "source-pre-ff-norm-branch-adjoint.bf16",
            "sealed-source-branch",
        ),
        reference(BRANCH_RESULT / "decision.json", "sealed-branch-decision"),
        reference(OPEN_DIRECT, "open-direct-adjoint"),
        reference(FIXTURE / "decision.json", "fixture-decision"),
        reference(FIXTURE / "fixture-manifest.json", "fixture-manifest"),
        reference(FIXTURE / "guard.json", "fixture-guard"),
        reference(PROBE, "probe-source"),
        reference(COMPOSER, "composer-source"),
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
        measurement("antecedentsPass", "boolean", "The failed synthetic merge, sealed source total and branch, open direct, production fixture, source tree, and experiment remain bound."),
        measurement("captureCount", "captures", "Independent complete source graph executions."),
        measurement("elementCount", "BF16 elements per tensor", "Complete state-stream-feature population in every combined tensor."),
        measurement("declaredProbeFileCount", "files", "Exact input, total, branch, and direct bin/meta paths across both captures."),
        measurement("declaredProbePopulationExact", "boolean", "Each capture manifest contains exactly the declared same-run probe path set."),
        measurement("nonProbeFixtureMismatchCount", "files", "Non-probe files differing from the retained production fixture."),
        measurement("sealedTotalMismatchCount", "BF16 elements", "Same-run total words differing from the prior sealed source total."),
        measurement("sealedBranchMismatchCount", "BF16 elements", "Same-run branch words differing from the prior sealed source branch."),
        measurement("openDirectMismatchCount", "BF16 elements", "Same-run source direct words differing from the open direct calculation."),
        measurement("maximumOpenDirectAbsoluteError", "absolute value", "Largest source-direct versus open-direct difference."),
        measurement("composedTotalMismatchCount", "BF16 elements", "RNE sum of same-run branch and direct differing from the same-run source total."),
        measurement("maximumComposedTotalAbsoluteError", "absolute value", "Largest composed versus source-total difference."),
        measurement("negatedControlMismatchCount", "BF16 elements", "Sign-negated branch composition differing from the source total."),
        measurement("sourceCaptureDeterministic", "boolean", "Both complete capture and composition populations replay byte-identically."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed oracle source."),
        measurement("guardedWorkRootPass", "boolean", "All transient source, build, and capture data was removed."),
    ]
    promotion = [
        predicate("p-antecedents", "antecedentsPass", "eq", True),
        predicate("p-captures", "captureCount", "eq", 2),
        predicate("p-elements", "elementCount", "eq", 2_097_152),
        predicate("p-probe-files", "declaredProbeFileCount", "eq", 1024),
        predicate("p-probe-population", "declaredProbePopulationExact", "eq", True),
        predicate("p-fixture", "nonProbeFixtureMismatchCount", "eq", 0),
        predicate("p-total", "sealedTotalMismatchCount", "eq", 0),
        predicate("p-branch", "sealedBranchMismatchCount", "eq", 0),
        predicate("p-direct-localization", "openDirectMismatchCount", "gt", 0),
        predicate("p-composition", "composedTotalMismatchCount", "eq", 0),
        predicate("p-composition-maximum", "maximumComposedTotalAbsoluteError", "eq", 0.0),
        predicate("p-control", "negatedControlMismatchCount", "gt", 0),
        predicate("p-replay", "sourceCaptureDeterministic", "eq", True),
        predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
        predicate("p-work", "guardedWorkRootPass", "eq", True),
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
                key: value for key, value in reference(
                    parent_revision, "parent-revision"
                ).items() if key != "id"
            },
        },
        "hypothesis": {
            "claim": "The direct pre-FF residual adjoint captured in the same source graph differs from the open direct calculation at the exceptional coordinates and, with the same-run exact RMSNorm branch, reconstructs every sealed source total word.",
            "falsification": "Any sealed-total or sealed-branch drift, no direct difference, non-exact same-run composition, incomplete or nondeterministic capture, fixture drift, source failure, or resource failure rejects this attribution.",
        },
        "changedMechanism": "Replace synthetic coefficient injection with one production NNCP graph carrying zero-valued marked parameters before the layer-19 pre-FF split, before its RMSNorm branch, and before final RMSNorm, thereby capturing total, branch, and direct adjoints under one traversal.",
        "invariants": [
            "The model, source base, LibNC, parameters, state, optimizer, probabilities, update, block, and non-probe fixture outputs remain unchanged.",
            "Every marked parameter is zero-valued and shape-identical to its source tensor.",
            "The same-run total and branch must remain bit-identical to their independently sealed source captures before the new direct tensor is interpreted.",
            "No coordinate correction, tolerance, fitted value, future symbol, or objective credit is permitted.",
            "Teacher capture tensors are attribution evidence and cannot ship in a Gamma codec.",
        ],
        "controls": [
            {"id": "sealed-total", "role": "comparator", "definition": "Require the same-run total to equal the prior complete source total."},
            {"id": "sealed-branch", "role": "comparator", "definition": "Require the same-run RMSNorm branch to equal the prior complete source branch."},
            {"id": "open-direct", "role": "treatment", "definition": "Compare every new source direct word with the open final-RMSNorm input residual."},
            {"id": "same-run-composition", "role": "treatment", "definition": "RNE-compose the same-run branch and direct and require the exact same-run total."},
            {"id": "negated-branch", "role": "negative", "definition": "Negate the branch before composition and require a live mismatch."},
            {"id": "independent-replay", "role": "replay", "definition": "Repeat the complete source capture and all compositions byte-for-byte."},
        ],
        "population": {
            "unit": "BF16 layer-19 state-stream-feature adjoint words",
            "scopeBytes": 4_194_304,
            "scopeSymbols": 2_097_152,
            "selection": "Every feature for all 64 chronological states and 32 streams at production block 256.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "causalBoundary": {
            "availableInformation": [
                "The bound production graph, sealed total and branch, open direct, exact probe namespace, and retained fixture manifest."
            ],
            "forbiddenInformation": [
                "Coordinate-specific repairs, tolerance, fitted coefficients, future symbols, or use of captured tensors in a submitted codec."
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
            "uncertaintyRisk": 0.1,
            "interactionRisk": 0.1,
        },
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": [
            predicate("k-antecedents", "antecedentsPass", "eq", True),
            predicate("k-composition", "composedTotalMismatchCount", "gt", 0),
        ],
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/same-run-pre-ff-input.bf16",
            f"results/{CANDIDATE_ID}/same-run-pre-ff-total-adjoint.bf16",
            f"results/{CANDIDATE_ID}/same-run-pre-ff-branch-adjoint.bf16",
            f"results/{CANDIDATE_ID}/same-run-pre-ff-direct-adjoint.bf16",
            f"results/{CANDIDATE_ID}/same-run-pre-ff-composed-adjoint.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "outputManifestPolicy": "complete-result-artifacts-v1",
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(
            microsecond=0
        ).isoformat(),
    }
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(OUTPUT)
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
