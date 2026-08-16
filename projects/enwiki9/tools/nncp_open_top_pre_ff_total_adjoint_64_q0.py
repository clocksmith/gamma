#!/usr/bin/env python3
"""Compose the exact open pre-FF branch and direct residual adjoints."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_ff2_input_adjoint_64_q0_v1 as comparator
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0 as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_total_adjoint_64_q0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MERGER_SOURCE = PROGRAM / "merge_bf16.cpp"
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / "tools/nncp_open_top_pre_ff_total_adjoint_64_q0_materializer.py"
PARENT_ID = "nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T142835Z_50298bd574.json"
)
BRANCH_ADJOINT = PARENT_RESULT / "open-pre-ff-rms-output-order-adjoint.bf16"
DIRECT_ADJOINT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
SOURCE_TOTAL = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden-adjoint.bf16"
)
SOURCE_CEILING = 1_000_000


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return base.reference(path, identifier)


def execute(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command, cwd=ROOT, capture_output=True, check=False
    )
    receipt = {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.decode(errors="replace"),
        "stderr": completed.stderr.decode(errors="replace"),
    }
    if completed.returncode:
        raise RuntimeError(json.dumps(receipt, sort_keys=True))
    return receipt


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, FREEZER)),
        MERGER_SOURCE.resolve(),
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
        raise ValueError("pre-FF total-adjoint source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("exact-branch-adjoint", BRANCH_ADJOINT),
        ("exact-direct-adjoint", DIRECT_ADJOINT),
        ("source-total-adjoint", SOURCE_TOTAL),
        ("merger-source", MERGER_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"pre-FF total input drifted: {identifier}")
    decision = json.loads(PARENT_DECISION.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    if not (
        decision["promotionPass"] is True
        and decision["measurements"]["treatmentMismatchCount"] == 0
        and decision["measurements"]["gainGradientMismatchCount"] == 0
        and decision["measurements"]["biasGradientMismatchCount"] == 0
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "supported"
        and reflection["decision"]["verdict"] == "mutate"
    ):
        raise ValueError("pre-FF total-adjoint antecedents are not satisfied")


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
        raise ValueError("pre-FF total experiment identifies another candidate")
    if reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and pre-FF total experiment differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("pre-FF total result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("pre-FF total work root was not fresh")
    binary = WORK / "merge-bf16"
    executions: dict[str, Any] = {}
    executions["compile"] = execute([
        os.environ.get("CXX", "c++"), "-std=c++20", "-O3", "-Wall", "-Wextra",
        str(MERGER_SOURCE), "-o", str(binary)
    ])
    executions["ldd"] = execute(["ldd", str(binary)])
    forbidden = [
        line for line in executions["ldd"]["stdout"].splitlines()
        if any(token in line.lower() for token in (
            "libnc", "ggml", "cuda", "openmp", "gomp", "blas"
        ))
    ]

    def run(label: str) -> tuple[Path, Path]:
        total = WORK / f"{label}-total.bf16"
        negated = WORK / f"{label}-negated.bf16"
        executions[f"merge-{label}"] = execute([
            str(binary), str(BRANCH_ADJOINT), str(DIRECT_ADJOINT),
            str(total), str(negated)
        ])
        return total, negated

    populations = [run("a"), run("b")]
    treatment = comparator.compare_bf16(populations[0][0], SOURCE_TOTAL)
    negated = comparator.compare_bf16(populations[0][1], SOURCE_TOTAL)
    replay = all(
        populations[0][index].read_bytes() == populations[1][index].read_bytes()
        for index in range(2)
    )
    retained = RESULT / "source-exact-pre-ff-total-adjoint.bf16"
    shutil.copyfile(populations[0][0], retained)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps({
        "comparisons": {
            "negated": list(negated),
            "treatment": list(treatment),
        },
        "executions": executions,
        "forbiddenDynamicDependencies": forbidden,
    }, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "elementCount": retained.stat().st_size // 2,
        "totalAdjointMismatchCount": treatment[0],
        "maximumTotalAdjointAbsoluteError": treatment[1],
        "negatedControlMismatchCount": negated[0],
        "evaluationReplayIdentical": replay,
        "forbiddenDynamicDependencyCount": len(forbidden),
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = base.oracle.evaluate(experiment["promotionPredicates"], measurements)
    kill = base.oracle.evaluate(experiment["killPredicates"], measurements)
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
            "authorize-successor" if promotion_pass
            else "retire" if kill_pass
            else "retry"
        ),
        "artifacts": [
            reference(execution_path, "execution"),
            reference(retained, "source-exact-pre-ff-total-adjoint"),
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
