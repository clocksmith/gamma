#!/usr/bin/env python3
"""Seal completed pre-FF normalization-branch captures without teacher replay."""

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
import nncp_libnc_top_ff2_input_adjoint_64_q0_v1 as comparator
import nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0 as parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v1"
PARENT_ID = "nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_v1"
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
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / (
    "tools/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v1_materializer.py"
)
COMPARATOR_SOURCE = ROOT / "tools/nncp_libnc_top_ff2_input_adjoint_64_q0_v1.py"
OPEN_BRANCH = parent.OPEN_BRANCH
SOURCE_HIDDEN = parent.SOURCE_HIDDEN
SOURCE_TOTAL = parent.SOURCE_TOTAL
FIXTURE_MANIFEST = parent.FIXTURE_MANIFEST
SOURCE_CEILING = 2_000_000


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return parent.reference(path, identifier or path.stem)


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, FREEZER)),
        PROGRAM_DESCRIPTOR.resolve(),
        COMPARATOR_SOURCE.resolve(),
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
        raise ValueError("branch-adjoint retry source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-experiment", PARENT_EXPERIMENT),
        ("parent-guard", PARENT_GUARD),
        ("parent-job", PARENT_JOB),
        ("parent-log", PARENT_LOG),
        ("parent-revision", PARENT_REVISION),
        ("parent-reflection", PARENT_REFLECTION),
        ("sealed-capture-manifests", SEALED_MANIFESTS),
        ("open-normalization-branch-adjoint", OPEN_BRANCH),
        ("source-pre-ff-hidden", SOURCE_HIDDEN),
        ("source-pre-ff-total-adjoint", SOURCE_TOTAL),
        ("fixture-manifest", FIXTURE_MANIFEST),
        ("comparator-source", COMPARATOR_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"branch-adjoint retry input drifted: {identifier}")
    job = json.loads(PARENT_JOB.read_text())
    guard = json.loads(PARENT_GUARD.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    if not (
        job["state"] == "failed"
        and job["returncode"] == 1
        and guard["status"] == "complete"
        and guard["rss_guard_exceeded"] is False
        and guard["official_decimal_memory_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and reflection["validity"]["classification"] == "implementation-failure"
        and reflection["hypothesis"]["verdict"] == "not-tested"
        and reflection["decision"]["verdict"] == "retry"
    ):
        raise ValueError("branch-adjoint retry antecedents are not satisfied")


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
        raise ValueError("branch-adjoint retry experiment identifies another candidate")
    if reference(experiment_path, "experiment") != {
        **json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]),
        "id": "experiment",
    }:
        raise ValueError("job and branch-adjoint retry experiment differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("branch-adjoint retry result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("branch-adjoint retry work root was not fresh")
    frozen = json.loads(SEALED_MANIFESTS.read_text())
    capture_base = parent.source_base.source_parent.source_capture.base
    captures = [PARENT_WORK / "capture-a", PARENT_WORK / "capture-b"]
    manifests = [capture_base.directory_manifest(path) for path in captures]
    if frozen.get("captures") != manifests:
        raise ValueError("completed source capture manifests drifted after freezing")
    fixture = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [parent.fixture_identity(row, fixture) for row in manifests]
    combined: list[dict[str, Path]] = []
    for label, directory in zip(("a", "b"), captures, strict=True):
        input_path = WORK / f"{label}-norm-input.bf16"
        adjoint_path = WORK / f"{label}-norm-branch-adjoint.bf16"
        parent.combine_probe(directory, "input", input_path)
        parent.combine_probe(directory, "adjoint", adjoint_path)
        combined.append({"input": input_path, "adjoint": adjoint_path})
    input_comparison = comparator.compare_bf16(
        combined[0]["input"], SOURCE_HIDDEN
    )
    open_comparison = comparator.compare_bf16(
        combined[0]["adjoint"], OPEN_BRANCH
    )
    total_comparison = comparator.compare_bf16(
        combined[0]["adjoint"], SOURCE_TOTAL
    )
    source_input = RESULT / "source-pre-ff-norm-input.bf16"
    source_adjoint = RESULT / "source-pre-ff-norm-branch-adjoint.bf16"
    shutil.copyfile(combined[0]["input"], source_input)
    shutil.copyfile(combined[0]["adjoint"], source_adjoint)
    repeat = (
        manifests[0]["aggregateSha256"] == manifests[1]["aggregateSha256"]
        and all(
            combined[0][name].read_bytes() == combined[1][name].read_bytes()
            for name in ("input", "adjoint")
        )
    )
    probe_exact = all(row["declaredProbePopulationExact"] for row in identities)
    non_probe_mismatches = sum(
        len(row["nonProbeMismatches"]) for row in identities
    )
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps({
        "captureManifests": manifests,
        "fixtureIdentity": identities,
        "frozenCaptureManifests": reference(
            SEALED_MANIFESTS, "sealed-capture-manifests"
        ),
        "inputComparison": list(input_comparison),
        "openBranchComparison": list(open_comparison),
        "totalAdjointComparison": list(total_comparison),
        "teacherExecuted": False,
    }, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(PARENT_WORK)
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "captureCount": len(captures),
        "sampleCount": parent.SAMPLES,
        "inputElementCount": source_input.stat().st_size // 2,
        "adjointElementCount": source_adjoint.stat().st_size // 2,
        "sourceCaptureDeterministic": repeat,
        "captureManifestsBound": True,
        "declaredProbeFileCount": sum(
            row["declaredProbeFileCount"] for row in identities
        ),
        "declaredProbePopulationExact": probe_exact,
        "nonProbeFixtureMismatchCount": non_probe_mismatches,
        "inputMismatchCount": input_comparison[0],
        "openBranchMismatchCount": open_comparison[0],
        "maximumOpenBranchAbsoluteError": open_comparison[1],
        "totalAdjointControlMismatchCount": total_comparison[0],
        "adjointComparatorLive": source_adjoint.read_bytes()
        != bytes(source_adjoint.stat().st_size),
        "teacherExecutionCount": 0,
        "incrementalSourceBytes": source_closure.stat().st_size,
        "parentWorkRootRemoved": not PARENT_WORK.exists(),
        "guardedWorkRootPass": not WORK.exists(),
    }
    evaluate = parent.source_base.source_parent.source_capture.open_parent.evaluate
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": reference(experiment_path, "experiment"),
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
            "authorize-successor" if promotion_pass
            else "retire" if kill_pass
            else "retry"
        ),
        "artifacts": [
            reference(execution_path, "execution"),
            reference(source_input, "source-pre-ff-norm-input"),
            reference(source_adjoint, "source-pre-ff-norm-branch-adjoint"),
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
