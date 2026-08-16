#!/usr/bin/env python3
"""Freeze receipt-only salvage of complete top-attention captures."""

from __future__ import annotations

import copy
import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_attention_product_oracle_64_q0_v1 as source
import nncp_libnc_top_attention_product_oracle_64_q0_v1_materializer as parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_attention_product_oracle_64_q0_retry_v2"
PARENT_ID = "nncp_libnc_top_attention_product_oracle_64_q0_retry_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_WORK = PARENT_RESULT / "work"
PARENT_EXPERIMENT = ROOT / (
    f"operations/adaptive/experiments/{PARENT_ID}.json"
)
PARENT_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T172814Z_45054e4c3f.json"
)
PARENT_LOG = ROOT / "run_logs/adaptive/20260816T172814Z_45054e4c3f.log"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T172814Z_45054e4c3f.json"
)
SEALED_MANIFESTS = PARENT_RESULT / "sealed-capture-manifests.json"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RUNNER = ROOT / (
    "tools/nncp_libnc_top_attention_product_oracle_64_q0_retry_v2.py"
)
MATERIALIZER = Path(__file__).resolve()
DESCRIPTOR = PROGRAM / "program.py"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
HYPOTHESIS = (
    "The two completed manifest-frozen attention-product captures can be "
    "re-hashed and assembled in observed stream-head byte order without "
    "teacher replay, yielding deterministic, live forward and adjoint tensors "
    "whose attended input exactly equals the promoted open pre-w_o value."
)


def freeze_capture_manifests() -> None:
    capture_base = source.capture_base.source_capture.capture.base
    captures = [
        capture_base.directory_manifest(PARENT_WORK / "capture-a"),
        capture_base.directory_manifest(PARENT_WORK / "capture-b"),
    ]
    fixture = json.loads(source.FIXTURE_MANIFEST.read_text())
    identities = [source.fixture_identity(row, fixture) for row in captures]
    if not all(
        row["declaredProbeFileCount"] == 512
        and row["declaredProbePopulationExact"] is True
        and row["nonProbeIdentical"] is True
        for row in identities
    ):
        raise ValueError("completed top-attention capture population differs")
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
        if (
            existing.get("candidateId") != PARENT_ID
            or existing.get("captures") != captures
        ):
            raise ValueError("existing top-attention manifests differ")
        return
    SEALED_MANIFESTS.write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n"
    )


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    freeze_capture_manifests()
    experiment = copy.deepcopy(json.loads(PARENT_EXPERIMENT.read_text()))
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    failed_job = json.loads(PARENT_JOB.read_text())
    parent_revision = ROOT / failed_job["candidate_revision"]["path"]
    experiment["parent"] = {
        "candidateId": PARENT_ID,
        "revision": {
            key: value
            for key, value in parent.base.reference(
                parent_revision, "parent-revision"
            ).items()
            if key != "id"
        },
    }
    experiment["hypothesis"] = {
        "claim": HYPOTHESIS,
        "falsification": (
            "Any frozen-manifest drift, incomplete population, replay "
            "difference, non-probe fixture drift, dead tensor, direct concat "
            "mismatch, dead wrong-order control, teacher execution, source "
            "failure, resource failure, or cleanup failure rejects salvage."
        ),
    }
    experiment["changedMechanism"] = (
        "Do not compile or execute the teacher. Re-hash the two completed "
        "capture trees against prospectively frozen manifests, accept observed "
        "LibNC dimensions 128,1,8,32 and 320,1,8,32, assemble their serialized "
        "stream-head order directly, validate every original scientific gate, "
        "then remove the transient source trees."
    )
    experiment["invariants"] = [
        "The failed job, guard, log, revision, reflection, capture manifests, fixture, and open pre-w_o comparator remain hash-bound.",
        "No teacher executable, model graph, optimizer, or probability path is invoked by the retry.",
        "Both current capture manifests must exactly equal their frozen per-file snapshots before tensor assembly.",
        "Observed dimension numbering is distinct from serialized order: write_axis makes stream then head the outer byte coordinates.",
        "A schema-valid pre-cleanup decision exists before either raw tree is deleted.",
        "All sealed tensors remain zero-credit teacher evidence and cannot ship in a Gamma codec.",
    ]
    experiment["controls"] = [
        {
            "id": "frozen-capture-replay",
            "role": "treatment",
            "definition": "Re-hash and combine every declared tensor from both complete capture trees without source recomputation.",
        },
        {
            "id": "direct-concat-identity",
            "role": "comparator",
            "definition": "Compare direct serialized attended input to every word of the independently exact open pre-w_o tensor.",
        },
        {
            "id": "head-major-permutation",
            "role": "negative",
            "definition": "Apply the rejected head-major interpretation and require it to differ from the open tensor.",
        },
        {
            "id": "unchanged-fixture",
            "role": "shifted",
            "definition": "Require every non-probe fixture payload to retain its bound digest.",
        },
        {
            "id": "independent-replay",
            "role": "replay",
            "definition": "Require both complete four-tensor populations and aggregate manifests to reproduce byte-for-byte.",
        },
    ]
    experiment["population"]["coordinate"] = (
        "state-major, stream-major, head-major, feature-or-key-major"
    )
    experiment["causalBoundary"] = {
        "availableInformation": [
            "The completed capture trees, their frozen manifests, failed-job receipts, retained fixture manifest, and exact open pre-w_o value.",
            "The observed LibNC metadata and write_axis serialization code needed to interpret coordinates.",
        ],
        "forbiddenInformation": [
            "Teacher execution, capture mutation, tolerance, fitted repair, future symbols, teacher probabilities outside the captured boundary, or objective credit.",
            "Shipping captured tensors or claiming open attention arithmetic before independent LibNC-free replay.",
        ],
    }
    existing_measurements = {row["id"] for row in experiment["measurements"]}
    extra_measurements = [
        parent.base.measurement("captureManifestsBound", "boolean", "Both current directory manifests exactly equal the frozen snapshots."),
        parent.base.measurement("headMajorControlMismatchCount", "BF16 elements", "Wrong head-major reinterpretation words differing from the exact open pre-w_o tensor."),
        parent.base.measurement("teacherExecutionCount", "executions", "Teacher executions performed by the salvage."),
        parent.base.measurement("resourceGuardsPass", "boolean", "The completed source run stayed within decimal memory and temporary-disk limits."),
        parent.base.measurement("sourceWorkBytesBeforeCleanup", "bytes", "Completed raw source bytes removed only after validation."),
        parent.base.measurement("sourceWorkRootRemoved", "boolean", "The manifest-verified source work root was removed."),
    ]
    experiment["measurements"].extend(
        row for row in extra_measurements if row["id"] not in existing_measurements
    )
    experiment["promotionPredicates"].extend(
        [
            parent.base.predicate("p-manifests", "captureManifestsBound", "eq", True),
            parent.base.predicate("p-order-control", "headMajorControlMismatchCount", "gt", 0),
            parent.base.predicate("p-no-teacher", "teacherExecutionCount", "eq", 0),
            parent.base.predicate("p-resources", "resourceGuardsPass", "eq", True),
            parent.base.predicate("p-source-work", "sourceWorkRootRemoved", "eq", True),
        ]
    )
    experiment["killPredicates"] = [
        parent.base.predicate("k-antecedents", "antecedentsPass", "eq", True),
        parent.base.predicate("k-concat", "concatSourceMismatchCount", "gt", 0),
    ]
    excluded = {"runner", "materializer", "program-descriptor"}
    inputs = [
        item
        for item in experiment["inputs"]
        if item["id"] not in excluded
        and not item["id"].startswith("runtime-source-")
    ]
    inputs.extend(
        (
            parent.base.reference(PARENT_EXPERIMENT, "source-experiment"),
            parent.base.reference(PARENT_JOB, "source-failed-job"),
            parent.base.reference(PARENT_LOG, "source-log"),
            parent.base.reference(PARENT_GUARD, "source-guard"),
            parent.base.reference(PARENT_REFLECTION, "source-reflection"),
            parent.base.reference(
                SEALED_MANIFESTS, "sealed-capture-manifests"
            ),
            parent.base.reference(RUNNER, "runner"),
            parent.base.reference(MATERIALIZER, "materializer"),
            parent.base.reference(DESCRIPTOR, "program-descriptor"),
        )
    )
    deduplicated: dict[str, dict[str, str]] = {}
    for item in inputs:
        deduplicated[item["id"]] = item
    inputs = list(deduplicated.values())
    present = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(
                parent.base.reference(path, parent.source_identifier(path))
            )
            present.add(relative)
    experiment["inputs"] = inputs
    experiment["outputs"] = [
        f"results/{CANDIDATE_ID}/decision.json",
        f"results/{CANDIDATE_ID}/execution.json",
        f"results/{CANDIDATE_ID}/source-attended-heads-input.bf16",
        f"results/{CANDIDATE_ID}/source-attended-heads-adjoint.bf16",
        f"results/{CANDIDATE_ID}/source-attention-probability-input.bf16",
        f"results/{CANDIDATE_ID}/source-attention-probability-adjoint.bf16",
        f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
    ]
    experiment["generatedUtc"] = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
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
