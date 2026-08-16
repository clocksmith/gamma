#!/usr/bin/env python3
"""Seal completed top pre-FF captures after comparator dispatch failed."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import lzma
import os
from pathlib import Path
import shutil
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_ff1_bias_state_reduce_64_q0 as oracle
import nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1 as source
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_WORK = PARENT_RESULT / "work"
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1.json"
)
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T124600Z_7c726d2560.json"
)
PARENT_LOG = ROOT / "run_logs/adaptive/20260816T124600Z_7c726d2560.log"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_v1/"
    "20260816T124540281418Z_85e687c692c5.json"
)
NORMALIZED_INPUT = source.NORMALIZED_INPUT
NORMALIZED_ADJOINT = source.NORMALIZED_ADJOINT
FIXTURE_MANIFEST = source.FIXTURE_MANIFEST
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v1_materializer.py"
)
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
SOURCE_CEILING = 2_000_000


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return oracle.reference(path, identifier)


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        PROGRAM_DESCRIPTOR.resolve(),
    ]
    members = sorted(
        set(members), key=lambda item: item.relative_to(ROOT).as_posix()
    )
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(
                str(member), arcname=member.relative_to(ROOT).as_posix()
            )
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    path.write_bytes(
        lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME)
    )
    tar_path.unlink()
    if path.stat().st_size > SOURCE_CEILING:
        raise ValueError("top pre-FF sealing source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-experiment", PARENT_EXPERIMENT),
        ("parent-guard", PARENT_GUARD),
        ("parent-job", PARENT_JOB),
        ("parent-log", PARENT_LOG),
        ("parent-revision", PARENT_REVISION),
        ("normalized-ff1-input", NORMALIZED_INPUT),
        ("normalized-ff1-input-adjoint", NORMALIZED_ADJOINT),
        ("production-fixture-manifest", FIXTURE_MANIFEST),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    guard = json.loads(PARENT_GUARD.read_text())
    job = json.loads(PARENT_JOB.read_text())
    if not (
        guard["returncode"] == 1
        and guard["status"] == "complete"
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and guard["sample_count"] > 0
        and job["state"] == "failed"
        and job["returncode"] == 1
        and job["candidate_revision"]["path"]
        == PARENT_REVISION.relative_to(ROOT).as_posix()
        and "has no attribute 'compare_bf16'" in PARENT_LOG.read_text()
    ):
        raise ValueError("top pre-FF sealing antecedents are not satisfied")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    experiment_path = args.experiment.resolve()
    output = args.output.resolve()
    research_contracts.validate_artifact(experiment_path)
    experiment = json.loads(experiment_path.read_text())
    if experiment["proposalId"] != CANDIDATE_ID:
        raise ValueError("experiment identifies another candidate")
    if reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and top pre-FF sealing bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("top pre-FF sealing result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("top pre-FF sealing work root is not fresh")
    captures = [PARENT_WORK / "capture-a", PARENT_WORK / "capture-b"]
    if not all(path.is_dir() for path in captures):
        raise ValueError("completed top pre-FF capture directories are absent")

    manifests = [
        source.source_parent.source_capture.base.directory_manifest(path)
        for path in captures
    ]
    parent_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [
        source.fixture_identity(manifest, parent_manifest)
        for manifest in manifests
    ]
    combined: list[dict[str, Path]] = []
    for label, directory in zip(("a", "b"), captures, strict=True):
        hidden = WORK / f"{label}-pre-ff-hidden.bf16"
        adjoint = WORK / f"{label}-pre-ff-hidden-adjoint.bf16"
        source.combine_probe(directory, "input", hidden)
        source.combine_probe(directory, "adjoint", adjoint)
        combined.append({"hidden": hidden, "adjoint": adjoint})
    hidden_difference, hidden_maximum = oracle.compare_bf16(
        combined[0]["hidden"], NORMALIZED_INPUT
    )
    adjoint_difference, adjoint_maximum = oracle.compare_bf16(
        combined[0]["adjoint"], NORMALIZED_ADJOINT
    )
    hidden = RESULT / "source-pre-ff-hidden.bf16"
    adjoint = RESULT / "source-pre-ff-hidden-adjoint.bf16"
    shutil.copyfile(combined[0]["hidden"], hidden)
    shutil.copyfile(combined[0]["adjoint"], adjoint)
    repeat_identical = (
        manifests[0]["aggregateSha256"] == manifests[1]["aggregateSha256"]
        and combined[0]["hidden"].read_bytes()
        == combined[1]["hidden"].read_bytes()
        and combined[0]["adjoint"].read_bytes()
        == combined[1]["adjoint"].read_bytes()
    )
    probe_exact = all(row["declaredProbePopulationExact"] for row in identities)
    non_probe_mismatches = sum(
        len(row["nonProbeMismatches"]) for row in identities
    )
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "captureManifests": manifests,
                "fixtureIdentity": identities,
                "parentFailure": {
                    "guard": reference(PARENT_GUARD, "parent-guard"),
                    "job": reference(PARENT_JOB, "parent-job"),
                    "log": reference(PARENT_LOG, "parent-log"),
                    "failure": "post-capture comparator attribute lookup",
                },
                "normalizedInputDifference": {
                    "mismatchCount": hidden_difference,
                    "maximumAbsoluteError": hidden_maximum,
                },
                "normalizedAdjointDifference": {
                    "mismatchCount": adjoint_difference,
                    "maximumAbsoluteError": adjoint_maximum,
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(PARENT_WORK)
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "captureCount": len(captures),
        "sampleCount": source.SAMPLES,
        "hiddenElementCount": hidden.stat().st_size // 2,
        "adjointElementCount": adjoint.stat().st_size // 2,
        "sourceCaptureDeterministic": repeat_identical,
        "declaredProbeFileCount": sum(
            row["declaredProbeFileCount"] for row in identities
        ),
        "declaredProbePopulationExact": probe_exact,
        "nonProbeFixtureMismatchCount": non_probe_mismatches,
        "fixturePayloadIdentical": non_probe_mismatches == 0,
        "hiddenComparatorLive": hidden.read_bytes() != bytes(hidden.stat().st_size),
        "adjointComparatorLive": adjoint.read_bytes() != bytes(adjoint.stat().st_size),
        "preVsPostNormInputMismatchCount": hidden_difference,
        "totalVsNormBranchAdjointMismatchCount": adjoint_difference,
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists() and not PARENT_WORK.exists(),
    }
    promotion = oracle.evaluate(experiment["promotionPredicates"], measurements)
    kill = oracle.evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": reference(experiment_path),
        "candidateId": CANDIDATE_ID,
        "candidateRevision": revision,
        "evidenceClass": experiment["evidenceClass"],
        "objectiveCreditBytes": 0,
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": kill,
        "promotionPass": promotion_pass,
        "killPass": kill_pass,
        "decision": (
            "authorize-successor"
            if promotion_pass
            else "retire" if kill_pass else "retry"
        ),
        "artifacts": [
            reference(execution_path, "execution"),
            reference(hidden, "source-pre-ff-hidden"),
            reference(adjoint, "source-pre-ff-hidden-adjoint"),
            reference(source_closure, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
