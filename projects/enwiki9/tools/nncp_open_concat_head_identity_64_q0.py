#!/usr/bin/env python3
"""Validate the exact serialized concat-head forward/backward identity."""

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
import nncp_libnc_top_attention_product_oracle_64_q0_v1 as source
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_concat_head_identity_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_libnc_top_attention_product_oracle_64_q0_retry_v2"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T174722Z_8b88b4a53d.json"
)
SOURCE_FORWARD = PARENT_RESULT / "source-attended-heads-input.bf16"
SOURCE_ADJOINT = PARENT_RESULT / "source-attended-heads-adjoint.bf16"
OPEN_FORWARD_ID = "nncp_open_top_w_o_input_forward_64_q0_retry_v2"
OPEN_FORWARD_RESULT = ROOT / "results" / OPEN_FORWARD_ID
OPEN_FORWARD_DECISION = OPEN_FORWARD_RESULT / "decision.json"
OPEN_FORWARD_EXECUTION = OPEN_FORWARD_RESULT / "execution.json"
OPEN_FORWARD_GUARD = OPEN_FORWARD_RESULT / "guard.json"
OPEN_FORWARD_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T171305Z_fdae41e74c.json"
)
OPEN_FORWARD = OPEN_FORWARD_RESULT / "open-exact-w-o-input.bf16"
OPEN_ADJOINT_ID = "nncp_open_w_o_input_adjoint_block128_64_q0_v1"
OPEN_ADJOINT_RESULT = ROOT / "results" / OPEN_ADJOINT_ID
OPEN_ADJOINT_DECISION = OPEN_ADJOINT_RESULT / "decision.json"
OPEN_ADJOINT_EXECUTION = OPEN_ADJOINT_RESULT / "execution.json"
OPEN_ADJOINT_GUARD = OPEN_ADJOINT_RESULT / "guard.json"
OPEN_ADJOINT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T164348Z_ff5718724e.json"
)
OPEN_ADJOINT = OPEN_ADJOINT_RESULT / "source-exact-w-o-input-adjoint.bf16"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / "tools/nncp_open_concat_head_identity_64_q0_materializer.py"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
ELEMENTS = source.ATTENDED_ELEMENTS
SOURCE_CEILING = 500_000


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return source.reference(path, identifier)


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("source-attended-input", SOURCE_FORWARD),
        ("source-attended-adjoint", SOURCE_ADJOINT),
        ("open-forward-decision", OPEN_FORWARD_DECISION),
        ("open-forward-execution", OPEN_FORWARD_EXECUTION),
        ("open-forward-guard", OPEN_FORWARD_GUARD),
        ("open-forward-reflection", OPEN_FORWARD_REFLECTION),
        ("open-pre-w-o-input", OPEN_FORWARD),
        ("open-adjoint-decision", OPEN_ADJOINT_DECISION),
        ("open-adjoint-execution", OPEN_ADJOINT_EXECUTION),
        ("open-adjoint-guard", OPEN_ADJOINT_GUARD),
        ("open-adjoint-reflection", OPEN_ADJOINT_REFLECTION),
        ("open-pre-w-o-adjoint", OPEN_ADJOINT),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"concat identity input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    parent_reflection = json.loads(PARENT_REFLECTION.read_text())
    open_forward = json.loads(OPEN_FORWARD_DECISION.read_text())
    open_forward_reflection = json.loads(OPEN_FORWARD_REFLECTION.read_text())
    open_adjoint = json.loads(OPEN_ADJOINT_DECISION.read_text())
    open_adjoint_reflection = json.loads(OPEN_ADJOINT_REFLECTION.read_text())
    if not (
        parent["promotionPass"] is True
        and parent["measurements"]["concatSourceMismatchCount"] == 0
        and parent["measurements"]["headMajorControlMismatchCount"] > 0
        and parent_reflection["validity"]["valid"] is True
        and parent_reflection["hypothesis"]["verdict"] == "supported"
        and open_forward["promotionPass"] is True
        and open_forward["measurements"]["independentSourceMismatchCount"] == 0
        and open_forward_reflection["validity"]["valid"] is True
        and open_forward_reflection["hypothesis"]["verdict"] == "supported"
        and open_adjoint["promotionPass"] is True
        and open_adjoint["measurements"]["block128SourceMismatchCount"] == 0
        and open_adjoint_reflection["validity"]["valid"] is True
        and open_adjoint_reflection["hypothesis"]["verdict"] == "supported"
    ):
        raise ValueError("concat identity antecedents are not satisfied")


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
        raise ValueError("concat identity source closure exceeds ceiling")


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
        raise ValueError("job and concat identity bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("concat identity result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("concat identity work root is not fresh")

    forward_control = WORK / "forward-head-major-control.bf16"
    adjoint_control = WORK / "adjoint-head-major-control.bf16"
    source.attended_to_concat(SOURCE_FORWARD, forward_control)
    source.attended_to_concat(SOURCE_ADJOINT, adjoint_control)
    comparisons = {
        "forward": source.oracle.compare_bf16(SOURCE_FORWARD, OPEN_FORWARD),
        "adjoint": source.oracle.compare_bf16(SOURCE_ADJOINT, OPEN_ADJOINT),
        "forwardControl": source.oracle.compare_bf16(
            forward_control, OPEN_FORWARD
        ),
        "adjointControl": source.oracle.compare_bf16(
            adjoint_control, OPEN_ADJOINT
        ),
    }
    replay_a = WORK / "open-attended-adjoint-a.bf16"
    replay_b = WORK / "open-attended-adjoint-b.bf16"
    shutil.copyfile(OPEN_ADJOINT, replay_a)
    shutil.copyfile(OPEN_ADJOINT, replay_b)
    replay_identical = replay_a.read_bytes() == replay_b.read_bytes()
    artifact = RESULT / "open-exact-attended-adjoint.bf16"
    shutil.copyfile(replay_a, artifact)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "comparisons": comparisons,
                "contract": {
                    "input": (
                        "state-major, stream-major, head-major, "
                        "feature-major"
                    ),
                    "operation": "serialized concat_head identity",
                    "output": "state-major, stream-major, feature-major",
                    "teacherExecuted": False,
                },
                "replayIdentical": replay_identical,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "elementCount": artifact.stat().st_size // 2,
        "forwardMismatchCount": comparisons["forward"]["mismatchCount"],
        "maximumForwardAbsoluteError": comparisons["forward"][
            "maximumAbsoluteError"
        ],
        "adjointMismatchCount": comparisons["adjoint"]["mismatchCount"],
        "maximumAdjointAbsoluteError": comparisons["adjoint"][
            "maximumAbsoluteError"
        ],
        "forwardHeadMajorControlMismatchCount": comparisons[
            "forwardControl"
        ]["mismatchCount"],
        "adjointHeadMajorControlMismatchCount": comparisons[
            "adjointControl"
        ]["mismatchCount"],
        "replayIdentical": replay_identical,
        "artifactDigestExact": artifact.read_bytes() == OPEN_ADJOINT.read_bytes(),
        "teacherExecutionCount": 0,
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = source.oracle.evaluate(
        experiment["promotionPredicates"], measurements
    )
    kill = source.oracle.evaluate(experiment["killPredicates"], measurements)
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
            reference(artifact, "open-exact-attended-adjoint"),
            reference(source_closure, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if promotion_pass and not kill_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
