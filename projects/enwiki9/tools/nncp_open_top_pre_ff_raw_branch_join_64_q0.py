#!/usr/bin/env python3
"""Evaluate the exact RMSNorm branch at its live pre-FF residual join."""

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
import nncp_open_top_pre_ff_rmsnorm_output_order_64_q0 as exact_branch
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_raw_branch_join_64_q0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RAW_JOIN_MATERIALIZER = PROGRAM / "materialize_raw_join.py"
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / "tools/nncp_open_top_pre_ff_raw_branch_join_64_q0_materializer.py"
PARENT_ID = "nncp_open_top_pre_ff_total_adjoint_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T143328Z_5fb15662ea.json"
)
EXACT_ID = "nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1"
EXACT_RESULT = ROOT / "results" / EXACT_ID
EXACT_DECISION = EXACT_RESULT / "decision.json"
EXACT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T142835Z_50298bd574.json"
)
BASE_SOURCE = exact_branch.BASE_BACKWARD
STATE_MATERIALIZER = exact_branch.STATE_MATERIALIZER
OUTPUT_ORDER_MATERIALIZER = exact_branch.TREATMENT_MATERIALIZER
PARAMETERS = exact_branch.PARAMETERS
SEALED_INPUT = exact_branch.SEALED_INPUT
NORMALIZED_ADJOINT = exact_branch.NORMALIZED_ADJOINT
DIRECT_ADJOINT = exact_branch.DIRECT_ADJOINT
GAIN_COMPARATOR = exact_branch.GAIN_COMPARATOR
BIAS_COMPARATOR = exact_branch.BIAS_COMPARATOR
SEALED_BRANCH = exact_branch.SEALED_BRANCH
SOURCE_TOTAL = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden-adjoint.bf16"
)
SOURCE_CEILING = 2_000_000


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return exact_branch.reference(path, identifier)


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, FREEZER)),
        PROGRAM_DESCRIPTOR.resolve(),
        RAW_JOIN_MATERIALIZER.resolve(),
        OUTPUT_ORDER_MATERIALIZER.resolve(),
        STATE_MATERIALIZER.resolve(),
        BASE_SOURCE.resolve(),
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
        raise ValueError("raw-branch join source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("exact-branch-decision", EXACT_DECISION),
        ("exact-branch-reflection", EXACT_REFLECTION),
        ("base-backward-source", BASE_SOURCE),
        ("state-materializer", STATE_MATERIALIZER),
        ("output-order-materializer", OUTPUT_ORDER_MATERIALIZER),
        ("raw-join-materializer", RAW_JOIN_MATERIALIZER),
        ("initial-parameters", PARAMETERS),
        ("sealed-pre-ff-input", SEALED_INPUT),
        ("normalized-adjoint", NORMALIZED_ADJOINT),
        ("exact-direct-adjoint", DIRECT_ADJOINT),
        ("retained-gain-gradient", GAIN_COMPARATOR),
        ("retained-bias-gradient", BIAS_COMPARATOR),
        ("sealed-branch-adjoint", SEALED_BRANCH),
        ("source-total-adjoint", SOURCE_TOTAL),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"raw-branch join input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    parent_reflection = json.loads(PARENT_REFLECTION.read_text())
    exact = json.loads(EXACT_DECISION.read_text())
    exact_reflection = json.loads(EXACT_REFLECTION.read_text())
    if not (
        parent["promotionPass"] is False
        and parent["measurements"]["totalAdjointMismatchCount"] == 3
        and parent_reflection["validity"]["valid"] is True
        and parent_reflection["hypothesis"]["verdict"] == "refuted"
        and parent_reflection["decision"]["verdict"] == "mutate"
        and exact["promotionPass"] is True
        and exact["measurements"]["treatmentMismatchCount"] == 0
        and exact["measurements"]["gainGradientMismatchCount"] == 0
        and exact["measurements"]["biasGradientMismatchCount"] == 0
        and exact_reflection["validity"]["valid"] is True
        and exact_reflection["hypothesis"]["verdict"] == "supported"
    ):
        raise ValueError("raw-branch join antecedents are not satisfied")


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
        raise ValueError("raw-branch experiment identifies another candidate")
    if reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and raw-branch experiment differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("raw-branch result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("raw-branch work root was not fresh")
    state_source = WORK / "state-reduced.cpp"
    output_order_source = WORK / "output-order.cpp"
    treatment_source = WORK / "raw-branch-join.cpp"
    binary = WORK / "raw-branch-join"
    executions: dict[str, Any] = {}
    executions["materializeState"] = exact_branch.execute([
        "python3", str(STATE_MATERIALIZER), str(BASE_SOURCE), str(state_source)
    ])
    executions["materializeOutputOrder"] = exact_branch.execute([
        "python3", str(OUTPUT_ORDER_MATERIALIZER), str(state_source),
        str(output_order_source)
    ])
    executions["materializeRawJoin"] = exact_branch.execute([
        "python3", str(RAW_JOIN_MATERIALIZER), str(output_order_source),
        str(treatment_source)
    ])
    executions["compile"] = exact_branch.execute([
        os.environ.get("CXX", "c++"), "-std=c++20", "-O3", "-mavx2",
        "-mfma", "-Wall", "-Wextra", str(treatment_source), "-o", str(binary)
    ])
    executions["ldd"] = exact_branch.execute(["ldd", str(binary)])
    forbidden = [
        line for line in executions["ldd"]["stdout"].splitlines()
        if any(token in line.lower() for token in (
            "libnc", "ggml", "cuda", "openmp", "gomp", "blas"
        ))
    ]

    def run(label: str) -> dict[str, Path]:
        outputs = {
            name: WORK / f"{label}-{name}.bf16"
            for name in (
                "gain", "bias", "branch", "total", "direct",
                "negated-total"
            )
        }
        executions[f"treatment-{label}"] = exact_branch.execute([
            str(binary), str(PARAMETERS), str(SEALED_INPUT),
            str(NORMALIZED_ADJOINT), str(DIRECT_ADJOINT),
            *(str(outputs[name]) for name in (
                "gain", "bias", "branch", "total", "direct",
                "negated-total"
            )),
        ])
        return outputs

    populations = [run("a"), run("b")]
    branch = comparator.compare_bf16(populations[0]["branch"], SEALED_BRANCH)
    total = comparator.compare_bf16(populations[0]["total"], SOURCE_TOTAL)
    gain = comparator.compare_bf16(populations[0]["gain"], GAIN_COMPARATOR)
    bias = comparator.compare_bf16(populations[0]["bias"], BIAS_COMPARATOR)
    negated = comparator.compare_bf16(
        populations[0]["negated-total"], SOURCE_TOTAL
    )
    replay = all(
        populations[0][name].read_bytes() == populations[1][name].read_bytes()
        for name in populations[0]
    )
    retained = RESULT / "source-exact-pre-ff-total-adjoint.bf16"
    shutil.copyfile(populations[0]["total"], retained)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps({
        "comparisons": {
            "bias": list(bias),
            "branch": list(branch),
            "gain": list(gain),
            "negatedTotal": list(negated),
            "total": list(total),
        },
        "executions": executions,
        "forbiddenDynamicDependencies": forbidden,
    }, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "elementCount": retained.stat().st_size // 2,
        "branchAdjointMismatchCount": branch[0],
        "maximumBranchAdjointAbsoluteError": branch[1],
        "totalAdjointMismatchCount": total[0],
        "maximumTotalAdjointAbsoluteError": total[1],
        "gainGradientMismatchCount": gain[0],
        "biasGradientMismatchCount": bias[0],
        "negatedControlMismatchCount": negated[0],
        "evaluationReplayIdentical": replay,
        "forbiddenDynamicDependencyCount": len(forbidden),
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = exact_branch.base.oracle.evaluate(
        experiment["promotionPredicates"], measurements
    )
    kill = exact_branch.base.oracle.evaluate(
        experiment["killPredicates"], measurements
    )
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
