#!/usr/bin/env python3
"""Freeze manifest-only salvage of the completed same-run captures."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_pre_ff_same_run_contributions_64_q0_v1 as science
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer as fields
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v2"
PARENT_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v1"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v1.json"
)
FAILED_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T152537Z_f7e75c364c.json"
)
FAILED_GUARD = ROOT / "results" / PARENT_ID / "guard.json"
FAILED_LOG = ROOT / "run_logs/adaptive/20260816T152537Z_f7e75c364c.log"
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T152537Z_f7e75c364c.json"
)
SOURCE_WORK = ROOT / "results" / PARENT_ID / "work"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
SALVAGE_MANIFEST = PROGRAM / "salvage-source-manifest.json"
DESCRIPTOR = PROGRAM / "program.py"
RUNNER = ROOT / (
    "tools/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v2.py"
)
MATERIALIZER = Path(__file__).resolve()
COMPOSER_SOURCE = ROOT / (
    "programs/nncp_libnc_pre_ff_same_run_contributions_64_q0_v1/"
    "compose_bf16.cpp"
)
PROBE_SOURCE = ROOT / (
    "programs/nncp_libnc_pre_ff_same_run_contributions_64_q0_v1/"
    "same_run_probe.c"
)
SOURCE_INPUT = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden.bf16"
)
SOURCE_TOTAL = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden-adjoint.bf16"
)
SOURCE_BRANCH = ROOT / (
    "results/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2/"
    "source-pre-ff-norm-branch-adjoint.bf16"
)
STALE_OPEN_DIRECT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
CORRECTED_OPEN_RESULT = ROOT / (
    "results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2"
)
CORRECTED_OPEN_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T082228Z_f0bff9b6df.json"
)
FIXTURE_MANIFEST = ROOT / (
    "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture-manifest.json"
)


def write_salvage_manifest() -> None:
    if not SOURCE_WORK.is_dir():
        raise ValueError("completed same-run source work is unavailable")
    directory_manifest = (
        science.total_parent.source_parent.source_capture.base
        .directory_manifest
    )
    manifest = {
        "schema": "gamma.enwiki9.same-run-salvage-source.v1",
        "sourceCandidateId": PARENT_ID,
        "sourceFailedJob": science.reference(FAILED_JOB, "failed-job"),
        "captures": [
            directory_manifest(SOURCE_WORK / label)
            for label in ("capture-a", "capture-b")
        ],
        "combined": {
            f"{label}-{kind}": science.reference(
                SOURCE_WORK / f"{label}-{kind}.bf16", f"{label}-{kind}"
            )
            for label in ("a", "b")
            for kind in science.KINDS
        },
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0).isoformat(),
    }
    SALVAGE_MANIFEST.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    write_salvage_manifest()
    parent_job = json.loads(FAILED_JOB.read_text())
    experiment = json.loads(PARENT_EXPERIMENT.read_text())
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    experiment["parent"] = {
        "candidateId": PARENT_ID,
        "revision": parent_job["candidate_revision"],
    }
    experiment["hypothesis"] = {
        "claim": (
            "The completed same-run source direct equals the already promoted "
            "streaming-dot final-RMSNorm residual, differs from the stale "
            "artifact in exactly eight words, and composes with the exact "
            "RMSNorm branch to every sealed source total-adjoint word."
        ),
        "falsification": (
            "Any capture-manifest drift, fixture drift, replay difference, "
            "source input/total/branch drift, corrected-direct mismatch, "
            "non-exact composition, dead control, or resource failure rejects "
            "the salvage attribution."
        ),
    }
    experiment["changedMechanism"] = (
        "Do not rerun the completed teacher captures. Hash-bind their full "
        "manifests, re-parse and reassemble every probe, replace the broken "
        "comparator import, add the already promoted streaming-dot direct "
        "residual comparator, and remove the source scratch only after durable "
        "artifacts and receipts are staged."
    )
    experiment["invariants"].extend([
        "The failed job, resource guard, log, reflection, complete capture manifests, and combined tensors remain hash-bound.",
        "The corrected open direct must be independently promotion-backed and source-exact; the same-run capture cannot become a submitted codec input.",
        "The source scratch is removed only after both captures are re-parsed, replay is proved, outputs are retained, and execution evidence is durable.",
    ])
    experiment["controls"].append({
        "id": "corrected-open-direct",
        "role": "treatment",
        "definition": (
            "Require the same-run direct to equal the promoted streaming-dot "
            "final-RMSNorm residual in every word."
        ),
    })
    experiment["measurements"].extend([
        fields.measurement(
            "sourceInputMismatchCount", "BF16 elements",
            "Same-run input words differing from the sealed source pre-FF input.",
        ),
        fields.measurement(
            "correctedOpenDirectMismatchCount", "BF16 elements",
            "Same-run direct words differing from the corrected open residual.",
        ),
        fields.measurement(
            "maximumCorrectedOpenDirectAbsoluteError", "absolute value",
            "Largest corrected-open-direct difference.",
        ),
        fields.measurement(
            "capturedEvidenceManifestPass", "boolean",
            "Recomputed capture and combined-file manifests equal the frozen salvage manifest.",
        ),
        fields.measurement(
            "capturedCombinedExact", "boolean",
            "Freshly reassembled tensors equal every failed-job combined tensor.",
        ),
        fields.measurement(
            "sourceResourceGuardPass", "boolean",
            "The source capture stayed inside decimal memory and temporary-disk limits.",
        ),
        fields.measurement(
            "sourceWorkRootRemoved", "boolean",
            "The superseded completed-capture scratch was removed after salvage.",
        ),
    ])
    experiment["promotionPredicates"] = [
        fields.predicate("p-antecedents", "antecedentsPass", "eq", True),
        fields.predicate("p-captures", "captureCount", "eq", 2),
        fields.predicate("p-elements", "elementCount", "eq", 2_097_152),
        fields.predicate(
            "p-probe-files", "declaredProbeFileCount", "eq", 1024
        ),
        fields.predicate(
            "p-probe-population", "declaredProbePopulationExact", "eq", True
        ),
        fields.predicate(
            "p-fixture", "nonProbeFixtureMismatchCount", "eq", 0
        ),
        fields.predicate("p-source-input", "sourceInputMismatchCount", "eq", 0),
        fields.predicate("p-total", "sealedTotalMismatchCount", "eq", 0),
        fields.predicate("p-branch", "sealedBranchMismatchCount", "eq", 0),
        fields.predicate(
            "p-stale-direct", "openDirectMismatchCount", "eq", 8
        ),
        fields.predicate(
            "p-corrected-direct", "correctedOpenDirectMismatchCount", "eq", 0
        ),
        fields.predicate(
            "p-corrected-maximum", "maximumCorrectedOpenDirectAbsoluteError",
            "eq", 0.0,
        ),
        fields.predicate(
            "p-composition", "composedTotalMismatchCount", "eq", 0
        ),
        fields.predicate(
            "p-composition-maximum", "maximumComposedTotalAbsoluteError",
            "eq", 0.0,
        ),
        fields.predicate(
            "p-control", "negatedControlMismatchCount", "gt", 0
        ),
        fields.predicate(
            "p-replay", "sourceCaptureDeterministic", "eq", True
        ),
        fields.predicate(
            "p-manifest", "capturedEvidenceManifestPass", "eq", True
        ),
        fields.predicate(
            "p-combined", "capturedCombinedExact", "eq", True
        ),
        fields.predicate(
            "p-source-guard", "sourceResourceGuardPass", "eq", True
        ),
        fields.predicate(
            "p-source-cleanup", "sourceWorkRootRemoved", "eq", True
        ),
        fields.predicate(
            "p-source", "incrementalSourceBytes", "lte", 2_000_000
        ),
        fields.predicate("p-work", "guardedWorkRootPass", "eq", True),
    ]
    experiment["killPredicates"] = [
        fields.predicate("k-antecedents", "antecedentsPass", "eq", True),
        fields.predicate(
            "k-corrected-direct", "correctedOpenDirectMismatchCount", "gt", 0
        ),
        fields.predicate(
            "k-composition", "composedTotalMismatchCount", "gt", 0
        ),
    ]
    experiment["search"]["expectedRuntimeRatio"] = 0.02
    experiment["search"]["expectedMemoryRatio"] = 0.05
    experiment["search"]["uncertaintyRisk"] = 0.02

    discarded_ids = {"runner", "materializer", "program-descriptor"}
    inputs = [
        item for item in experiment["inputs"]
        if item["id"] not in discarded_ids
    ]
    additions = (
        ("failed-job", FAILED_JOB),
        ("failed-guard", FAILED_GUARD),
        ("failed-log", FAILED_LOG),
        ("failed-reflection", FAILED_REFLECTION),
        ("salvage-source-manifest", SALVAGE_MANIFEST),
        ("source-input", SOURCE_INPUT),
        ("sealed-source-total", SOURCE_TOTAL),
        ("sealed-source-branch", SOURCE_BRANCH),
        ("stale-open-direct", STALE_OPEN_DIRECT),
        ("corrected-open-decision", CORRECTED_OPEN_RESULT / "decision.json"),
        ("corrected-open-execution", CORRECTED_OPEN_RESULT / "execution.json"),
        ("corrected-open-guard", CORRECTED_OPEN_RESULT / "guard.json"),
        ("corrected-open-reflection", CORRECTED_OPEN_REFLECTION),
        (
            "corrected-open-direct",
            CORRECTED_OPEN_RESULT / "open-final-norm-input-residual.bf16",
        ),
        ("fixture-manifest", FIXTURE_MANIFEST),
        ("composer-source", COMPOSER_SOURCE),
        ("probe-source", PROBE_SOURCE),
        ("runner", RUNNER),
        ("materializer", MATERIALIZER),
        ("program-descriptor", DESCRIPTOR),
    )
    closure = local_source_closure((RUNNER, MATERIALIZER))
    closure_by_path = {
        path.relative_to(ROOT).as_posix(): path for path in closure
    }
    inputs = [
        science.reference(closure_by_path[item["path"]], item["id"])
        if item["path"] in closure_by_path else item
        for item in inputs
    ]
    by_id = {item["id"]: item for item in inputs}
    for identifier, path in additions:
        by_id[identifier] = science.reference(path, identifier)
    present_paths = {item["path"] for item in by_id.values()}
    for path in closure:
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            identifier = fields.source_identifier(path)
            by_id[identifier] = science.reference(path, identifier)
            present_paths.add(relative)
    by_path = {item["path"]: item for item in by_id.values()}
    experiment["inputs"] = list(by_path.values())
    experiment["outputs"] = [
        path.replace(PARENT_ID, CANDIDATE_ID)
        for path in experiment["outputs"]
    ]
    experiment["generatedUtc"] = (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )
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
