#!/usr/bin/env python3
"""Finalize the sealed top pre-FF oracle with typed BF16 comparisons."""

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
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T130215Z_9a50367a99.json"
)
PARENT_LOG = ROOT / "run_logs/adaptive/20260816T130215Z_9a50367a99.log"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v1/"
    "20260816T130158991978Z_0472db71dab5.json"
)
SOURCE_HIDDEN = PARENT_RESULT / "source-pre-ff-hidden.bf16"
SOURCE_ADJOINT = PARENT_RESULT / "source-pre-ff-hidden-adjoint.bf16"
NORMALIZED_INPUT = ROOT / (
    "results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/"
    "open-ff1-input.bf16"
)
NORMALIZED_ADJOINT = ROOT / (
    "results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/"
    "source-exact-ff1-input-adjoint.bf16"
)
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2_materializer.py"
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
        raise ValueError("final pre-FF sealing source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-job", PARENT_JOB),
        ("parent-log", PARENT_LOG),
        ("parent-revision", PARENT_REVISION),
        ("sealed-pre-ff-hidden", SOURCE_HIDDEN),
        ("sealed-pre-ff-hidden-adjoint", SOURCE_ADJOINT),
        ("normalized-ff1-input", NORMALIZED_INPUT),
        ("normalized-ff1-input-adjoint", NORMALIZED_ADJOINT),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    guard = json.loads(PARENT_GUARD.read_text())
    job = json.loads(PARENT_JOB.read_text())
    execution = json.loads(PARENT_EXECUTION.read_text())
    manifests = execution["captureManifests"]
    identities = execution["fixtureIdentity"]
    if not (
        guard["returncode"] == 1
        and guard["status"] == "complete"
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and job["state"] == "failed"
        and job["returncode"] == 1
        and "not supported between instances of 'str' and 'int'"
        in PARENT_LOG.read_text()
        and len(manifests) == 2
        and manifests[0]["aggregateSha256"]
        == manifests[1]["aggregateSha256"]
        and len(identities) == 2
        and all(row["declaredProbePopulationExact"] for row in identities)
        and all(row["nonProbeIdentical"] for row in identities)
        and all(not row["nonProbeMismatches"] for row in identities)
    ):
        raise ValueError("final pre-FF sealing antecedents are not satisfied")


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
        raise ValueError("job and final pre-FF sealing bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("final pre-FF sealing result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("final pre-FF sealing work root is not fresh")

    parent_execution = json.loads(PARENT_EXECUTION.read_text())
    manifests = parent_execution["captureManifests"]
    identities = parent_execution["fixtureIdentity"]
    hidden_comparison = oracle.compare_bf16(SOURCE_HIDDEN, NORMALIZED_INPUT)
    adjoint_comparison = oracle.compare_bf16(SOURCE_ADJOINT, NORMALIZED_ADJOINT)
    hidden = RESULT / "source-pre-ff-hidden.bf16"
    adjoint = RESULT / "source-pre-ff-hidden-adjoint.bf16"
    shutil.copyfile(SOURCE_HIDDEN, hidden)
    shutil.copyfile(SOURCE_ADJOINT, adjoint)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "captureAggregateSha256": [
                    row["aggregateSha256"] for row in manifests
                ],
                "fixtureIdentity": identities,
                "hiddenComparison": hidden_comparison,
                "adjointComparison": adjoint_comparison,
                "sealedInputs": {
                    "hidden": reference(SOURCE_HIDDEN, "sealed-pre-ff-hidden"),
                    "adjoint": reference(
                        SOURCE_ADJOINT, "sealed-pre-ff-hidden-adjoint"
                    ),
                    "parentExecution": reference(
                        PARENT_EXECUTION, "parent-execution"
                    ),
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "captureCount": len(manifests),
        "sampleCount": 2048,
        "hiddenElementCount": hidden.stat().st_size // 2,
        "adjointElementCount": adjoint.stat().st_size // 2,
        "sourceCaptureDeterministic": (
            manifests[0]["aggregateSha256"] == manifests[1]["aggregateSha256"]
        ),
        "declaredProbeFileCount": sum(
            row["declaredProbeFileCount"] for row in identities
        ),
        "declaredProbePopulationExact": all(
            row["declaredProbePopulationExact"] for row in identities
        ),
        "nonProbeFixtureMismatchCount": sum(
            len(row["nonProbeMismatches"]) for row in identities
        ),
        "fixturePayloadIdentical": all(
            row["nonProbeIdentical"] for row in identities
        ),
        "hiddenComparatorLive": hidden.read_bytes() != bytes(hidden.stat().st_size),
        "adjointComparatorLive": adjoint.read_bytes() != bytes(adjoint.stat().st_size),
        "preVsPostNormInputMismatchCount": hidden_comparison["mismatchCount"],
        "totalVsNormBranchAdjointMismatchCount": adjoint_comparison[
            "mismatchCount"
        ],
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
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
