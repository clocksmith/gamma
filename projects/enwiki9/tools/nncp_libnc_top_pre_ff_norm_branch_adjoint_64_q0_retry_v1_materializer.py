#!/usr/bin/env python3
"""Freeze sealing of the completed pre-FF branch-adjoint captures."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as base
import nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0 as parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v1"
PARENT_ID = "nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
RUNNER = ROOT / (
    "tools/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v1.py"
)
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
DESCRIPTOR = PROGRAM / "program.py"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_WORK = PARENT_RESULT / "work"
PARENT_EXPERIMENT = ROOT / "operations/adaptive/experiments" / f"{PARENT_ID}.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_JOB = ROOT / "operations/adaptive/failed/000_20260816T135852Z_0445009531.json"
PARENT_LOG = ROOT / "run_logs/adaptive/20260816T135852Z_0445009531.log"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T135835969917Z_51519aaa3638.json"
)
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T135852Z_0445009531.json"
)
SEALED_MANIFESTS = PARENT_RESULT / "sealed-capture-manifests.json"
COMPARATOR_SOURCE = ROOT / "tools/nncp_libnc_top_ff2_input_adjoint_64_q0_v1.py"
SOURCE_CEILING = 2_000_000


def freeze_capture_manifests() -> None:
    capture_base = parent.source_base.source_parent.source_capture.base
    captures = [
        capture_base.directory_manifest(PARENT_WORK / "capture-a"),
        capture_base.directory_manifest(PARENT_WORK / "capture-b"),
    ]
    fixture = json.loads(parent.FIXTURE_MANIFEST.read_text())
    identities = [parent.fixture_identity(row, fixture) for row in captures]
    if not all(
        row["declaredProbeFileCount"] == 256
        and row["declaredProbePopulationExact"] is True
        and row["nonProbeIdentical"] is True
        for row in identities
    ):
        raise ValueError("completed branch-adjoint capture population differs")
    frozen = {
        "schema": "gamma.enwiki9.sealed-source-capture-manifests.v1",
        "candidateId": PARENT_ID,
        "captures": captures,
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    if SEALED_MANIFESTS.exists():
        existing = json.loads(SEALED_MANIFESTS.read_text())
        if existing.get("candidateId") != PARENT_ID or existing.get("captures") != captures:
            raise ValueError("existing sealed capture manifests differ")
        return
    SEALED_MANIFESTS.write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n"
    )


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    freeze_capture_manifests()
    inputs = [
        base.reference(PARENT_EXPERIMENT, "parent-experiment"),
        base.reference(PARENT_GUARD, "parent-guard"),
        base.reference(PARENT_JOB, "parent-job"),
        base.reference(PARENT_LOG, "parent-log"),
        base.reference(PARENT_REVISION, "parent-revision"),
        base.reference(PARENT_REFLECTION, "parent-reflection"),
        base.reference(SEALED_MANIFESTS, "sealed-capture-manifests"),
        base.reference(
            parent.OPEN_BRANCH, "open-normalization-branch-adjoint"
        ),
        base.reference(parent.SOURCE_HIDDEN, "source-pre-ff-hidden"),
        base.reference(parent.SOURCE_TOTAL, "source-pre-ff-total-adjoint"),
        base.reference(parent.FIXTURE_MANIFEST, "fixture-manifest"),
        base.reference(COMPARATOR_SOURCE, "comparator-source"),
        base.reference(RUNNER, "runner"),
        base.reference(MATERIALIZER, "materializer"),
        base.reference(DESCRIPTOR, "program-descriptor"),
    ]
    present_paths = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            inputs.append(base.reference(path, base.source_identifier(path)))
            present_paths.add(relative)
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
                for key, value in base.reference(
                    PARENT_REVISION, "parent-revision"
                ).items()
                if key != "id"
            },
        },
        "hypothesis": {
            "claim": (
                "The two completed, manifest-frozen source populations are "
                "exact and can be sealed with the explicit typed BF16 "
                "comparator without rerunning the teacher, yielding the "
                "branch-arithmetic versus residual-join attribution."
            ),
            "falsification": (
                "Any manifest drift, incomplete probe population, non-probe "
                "fixture drift, replay difference, wrong input, dead control, "
                "teacher execution, source failure, or resource failure "
                "rejects finalization."
            ),
        },
        "changedMechanism": (
            "Do not compile or execute the teacher. Re-read only the two "
            "manifest-frozen completed capture directories, combine the exact "
            "declared populations, invoke the explicit tuple comparator, seal "
            "the artifacts, and remove the transient parent work tree."
        ),
        "invariants": [
            "The failed job, guard, log, revision, reflection, complete directory manifests, fixture, and comparator source remain hash-bound.",
            "No teacher executable, model, graph, optimizer, or probability path is invoked by the retry.",
            "Both exact capture manifests must match their prospectively frozen directory snapshots before any comparison.",
            "The open comparator is evaluated only after both source populations already exist and cannot modify them.",
            "The sealed tensors remain zero-credit oracle evidence and cannot ship in a Gamma codec.",
        ],
        "controls": [
            {
                "id": "sealed-capture-populations",
                "role": "treatment",
                "definition": "Combine every declared state from both completed capture directories without source recomputation.",
            },
            {
                "id": "frozen-directory-manifests",
                "role": "comparator",
                "definition": "Require every file size and digest to match the pre-comparison sealed snapshots.",
            },
            {
                "id": "independent-source-replay",
                "role": "replay",
                "definition": "Require both completed source inputs, branch adjoints, and aggregate manifests to reproduce byte-for-byte.",
            },
            {
                "id": "input-and-total-boundaries",
                "role": "negative",
                "definition": "Require exact pre-FF input identity and a branch-only adjoint distinct from the total adjoint.",
            },
            {
                "id": "explicit-typed-comparator",
                "role": "shifted",
                "definition": "Bind and invoke nncp_libnc_top_ff2_input_adjoint_64_q0_v1.compare_bf16 directly.",
            },
        ],
        "causalBoundary": {
            "availableInformation": [
                "The two completed capture directories, their frozen manifests, failed-job receipts, sealed comparator artifacts, and explicit comparator source."
            ],
            "forbiddenInformation": [
                "Teacher execution, capture mutation, tolerance, coordinate fitting, future symbols, teacher probabilities, or objective credit."
            ],
        },
        "population": {
            "unit": "BF16 layer-19 pre-FF normalization-branch adjoint words",
            "scopeBytes": 4_194_304,
            "scopeSymbols": 2_097_152,
            "selection": "Every one of 1,024 features for all 64 chronological states and 32 streams at production block 256.",
            "coordinate": "state-major, stream-major, feature-major",
        },
        "measurements": [
            base.measurement("antecedentsPass", "boolean", "All failure, capture, fixture, comparator, and source antecedents remain hash-bound."),
            base.measurement("captureCount", "captures", "Completed source capture populations."),
            base.measurement("sampleCount", "state-stream samples", "Chronological layer-19 pre-FF samples."),
            base.measurement("inputElementCount", "BF16 elements", "Words in the sealed normalization input."),
            base.measurement("adjointElementCount", "BF16 elements", "Words in the sealed normalization-branch adjoint."),
            base.measurement("sourceCaptureDeterministic", "boolean", "Both completed source populations reproduce byte-for-byte."),
            base.measurement("captureManifestsBound", "boolean", "Both current directory manifests exactly match the frozen snapshots."),
            base.measurement("declaredProbeFileCount", "files", "Exact input/adjoint, state, bin/meta files across both captures."),
            base.measurement("declaredProbePopulationExact", "boolean", "Each manifest contains exactly the enumerated probe path set."),
            base.measurement("nonProbeFixtureMismatchCount", "files", "Non-probe files differing from the retained fixture."),
            base.measurement("inputMismatchCount", "BF16 elements", "Source branch-input words differing from the sealed pre-FF hidden input."),
            base.measurement("openBranchMismatchCount", "BF16 elements", "Source branch-adjoint words differing from the open formula."),
            base.measurement("maximumOpenBranchAbsoluteError", "float32 value", "Maximum source/open branch-adjoint error."),
            base.measurement("totalAdjointControlMismatchCount", "BF16 elements", "Branch-only words differing from the sealed total adjoint."),
            base.measurement("adjointComparatorLive", "boolean", "The sealed branch adjoint is not all zero."),
            base.measurement("teacherExecutionCount", "executions", "Teacher executions performed by the retry."),
            base.measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed retry source."),
            base.measurement("parentWorkRootRemoved", "boolean", "The sealed parent capture tree was removed."),
            base.measurement("guardedWorkRootPass", "boolean", "The retry work root was removed."),
        ],
        "promotionPredicates": [
            base.predicate("p-antecedents", "antecedentsPass", "eq", True),
            base.predicate("p-captures", "captureCount", "eq", 2),
            base.predicate("p-samples", "sampleCount", "eq", 2_048),
            base.predicate("p-input-elements", "inputElementCount", "eq", 2_097_152),
            base.predicate("p-adjoint-elements", "adjointElementCount", "eq", 2_097_152),
            base.predicate("p-replay", "sourceCaptureDeterministic", "eq", True),
            base.predicate("p-manifests", "captureManifestsBound", "eq", True),
            base.predicate("p-probe-files", "declaredProbeFileCount", "eq", 512),
            base.predicate("p-probe-population", "declaredProbePopulationExact", "eq", True),
            base.predicate("p-fixture", "nonProbeFixtureMismatchCount", "eq", 0),
            base.predicate("p-input", "inputMismatchCount", "eq", 0),
            base.predicate("p-total-separation", "totalAdjointControlMismatchCount", "gt", 0),
            base.predicate("p-live", "adjointComparatorLive", "eq", True),
            base.predicate("p-no-teacher", "teacherExecutionCount", "eq", 0),
            base.predicate("p-source", "incrementalSourceBytes", "lte", SOURCE_CEILING),
            base.predicate("p-parent-work", "parentWorkRootRemoved", "eq", True),
            base.predicate("p-work", "guardedWorkRootPass", "eq", True),
        ],
        "killPredicates": [
            base.predicate("k-antecedents", "antecedentsPass", "eq", True),
            base.predicate("k-input", "inputMismatchCount", "gt", 0),
        ],
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": SOURCE_CEILING,
            "expectedNetSavingsBytes": -SOURCE_CEILING,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 0.01,
            "expectedMemoryRatio": 0.01,
            "uncertaintyRisk": 0.02,
            "interactionRisk": 0.01,
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/source-pre-ff-norm-input.bf16",
            f"results/{CANDIDATE_ID}/source-pre-ff-norm-branch-adjoint.bf16",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "outputManifestPolicy": "complete-result-artifacts-v1",
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
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
