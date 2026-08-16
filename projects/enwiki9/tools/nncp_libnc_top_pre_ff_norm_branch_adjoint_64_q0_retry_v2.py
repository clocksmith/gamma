#!/usr/bin/env python3
"""Finalize sealed branch-oracle artifacts with a schema-valid receipt."""

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
import nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v1 as parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2"
PARENT_ID = "nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_JOB = ROOT / "operations/adaptive/failed/000_20260816T141750Z_04014220dc.json"
PARENT_LOG = ROOT / "run_logs/adaptive/20260816T141750Z_04014220dc.log"
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T141735480097Z_05688e9742bd.json"
)
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T141750Z_04014220dc.json"
)
SEALED_INPUT = PARENT_RESULT / "source-pre-ff-norm-input.bf16"
SEALED_ADJOINT = PARENT_RESULT / "source-pre-ff-norm-branch-adjoint.bf16"
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / (
    "tools/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2_materializer.py"
)
SOURCE_CEILING = 2_000_000


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return parent.reference(path, identifier or path.stem)


def bare_reference(path: Path) -> dict[str, str]:
    value = reference(path, "bare-reference")
    return {key: value[key] for key in ("path", "sha256")}


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, FREEZER)),
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
        raise ValueError("receipt-only source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> dict[str, Any]:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-job", PARENT_JOB),
        ("parent-log", PARENT_LOG),
        ("parent-revision", PARENT_REVISION),
        ("parent-reflection", PARENT_REFLECTION),
        ("sealed-normalization-input", SEALED_INPUT),
        ("sealed-normalization-branch-adjoint", SEALED_ADJOINT),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"receipt-only input drifted: {identifier}")
    decision = json.loads(PARENT_DECISION.read_text())
    execution = json.loads(PARENT_EXECUTION.read_text())
    guard = json.loads(PARENT_GUARD.read_text())
    job = json.loads(PARENT_JOB.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    measurements = decision["measurements"]
    if not (
        job["state"] == "failed"
        and job["returncode"] == 1
        and guard["status"] == "complete"
        and guard["rss_guard_exceeded"] is False
        and guard["official_decimal_memory_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and "Additional properties are not allowed ('id' was unexpected)"
        in PARENT_LOG.read_text()
        and reflection["validity"]["classification"] == "implementation-failure"
        and reflection["decision"]["verdict"] == "retry"
        and execution["teacherExecuted"] is False
        and measurements["openBranchMismatchCount"] == 1_988_737
        and measurements["maximumOpenBranchAbsoluteError"]
        == 1.1920928955078125e-07
        and measurements["inputMismatchCount"] == 0
        and measurements["sourceCaptureDeterministic"] is True
        and measurements["declaredProbePopulationExact"] is True
        and measurements["nonProbeFixtureMismatchCount"] == 0
        and measurements["teacherExecutionCount"] == 0
        and decision["promotionPass"] is True
        and decision["killPass"] is False
    ):
        raise ValueError("receipt-only antecedents are not satisfied")
    return decision


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
        raise ValueError("receipt-only experiment identifies another candidate")
    if reference(experiment_path, "experiment") != {
        **json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]),
        "id": "experiment",
    }:
        raise ValueError("job and receipt-only experiment differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    parent_decision = require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("receipt-only result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("receipt-only work root was not fresh")
    source_input = RESULT / "source-pre-ff-norm-input.bf16"
    source_adjoint = RESULT / "source-pre-ff-norm-branch-adjoint.bf16"
    shutil.copyfile(SEALED_INPUT, source_input)
    shutil.copyfile(SEALED_ADJOINT, source_adjoint)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps({
        "arithmeticExecutionCount": 0,
        "parentDecision": reference(PARENT_DECISION, "parent-decision"),
        "parentExecution": reference(PARENT_EXECUTION, "parent-execution"),
        "sealedInputs": {
            "input": reference(SEALED_INPUT, "sealed-normalization-input"),
            "adjoint": reference(
                SEALED_ADJOINT, "sealed-normalization-branch-adjoint"
            ),
        },
        "teacherExecuted": False,
    }, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(WORK)
    measurements = dict(parent_decision["measurements"])
    measurements["incrementalSourceBytes"] = source_closure.stat().st_size
    measurements["guardedWorkRootPass"] = not WORK.exists()
    evaluate = parent.parent.source_base.source_parent.source_capture.open_parent.evaluate
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": bare_reference(experiment_path),
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
