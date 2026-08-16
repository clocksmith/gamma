#!/usr/bin/env python3
"""Test the disassembly-derived FF2 transpose lane accumulation order."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_ff2_input_adjoint_64_q0_v1 as parent
import nncp_open_profile_top_ff2_gradient_64_q0_retry_v1 as open_base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_ff2_transpose_lane_order_64_q0_v1"
PARENT_ID = "nncp_libnc_top_ff2_input_adjoint_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T090818Z_428a8e6c62.json"
)
OPEN_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_v1"
OPEN_RESULT = ROOT / "results" / OPEN_ID
OPEN_DECISION = OPEN_RESULT / "decision.json"
OPEN_EXECUTION = OPEN_RESULT / "execution.json"
OPEN_RESIDUAL = OPEN_RESULT / "open-ff2-input-residual.bf16"
TAIL_RESULT = ROOT / (
    "results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2"
)
TAIL_DECISION = TAIL_RESULT / "decision.json"
INCOMING = TAIL_RESULT / "open-final-norm-input-residual.bf16"
SOURCE_ADJOINT = PARENT_RESULT / "source-ff2-input-adjoint.bf16"
EVALUATOR_SOURCE = PROGRAM / "ff2_transpose_lane_order.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_ff2_transpose_lane_order_64_q0_materializer.py"
)
RUNNER = Path(__file__).resolve()
LIBNC = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/libnc.so")
EXPECTED_LIBNC_SHA256 = (
    "1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e"
)
EXPECTED_PARAMETER_SHA256 = (
    "156ddbb678a9d50faeb76584f669ca182402b0ec31102fbf9d8279cac495115e"
)
ELEMENTS = 64 * 32 * 3072
SOURCE_CEILING = 1_000_000


reference = parent.capture.reference
sha256 = parent.capture.sha256
execute = parent.capture.execute


def require_inputs(experiment: dict[str, Any]) -> tuple[Path, bool, bool]:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("source-ff2-input-adjoint", SOURCE_ADJOINT),
        ("open-decision", OPEN_DECISION),
        ("open-execution", OPEN_EXECUTION),
        ("open-ff2-input-residual", OPEN_RESIDUAL),
        ("tail-decision", TAIL_DECISION),
        ("incoming-residual", INCOMING),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    decision = json.loads(PARENT_DECISION.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    guard = json.loads(PARENT_GUARD.read_text())
    open_decision = json.loads(OPEN_DECISION.read_text())
    open_execution = json.loads(OPEN_EXECUTION.read_text())
    tail = json.loads(TAIL_DECISION.read_text())
    if not (
        decision["promotionPass"] is False
        and decision["killPass"] is True
        and decision["measurements"]["openResidualMismatchCount"] == 775
        and decision["measurements"]["sourceCaptureDeterministic"] is True
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "refuted"
        and reflection["decision"]["verdict"] == "mutate"
        and guard["returncode"] == 0
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and open_decision["measurements"]["openBackwardDeterministic"] is True
        and tail["promotionPass"] is True
        and tail["measurements"]["sourceFinalNormResidualMismatchCount"] == 0
    ):
        raise ValueError("FF2 transpose lane-order antecedents are not satisfied")
    parameters = open_base.parent.Q3_FIXTURE / "parameters_initial.coefs"
    parameter_bound = (
        open_execution["usedFixtureSha256"].get("parameters_initial.coefs")
        == EXPECTED_PARAMETER_SHA256
        and sha256(parameters) == EXPECTED_PARAMETER_SHA256
    )
    library_bound = sha256(LIBNC) == EXPECTED_LIBNC_SHA256
    return parameters, parameter_bound, library_bound


def compile_evaluator() -> tuple[Path, dict[str, Any]]:
    evaluator = WORK / "ff2_transpose_lane_order"
    receipt = execute(
        [
            os.environ.get("CXX", "g++"),
            "-std=c++17",
            "-O3",
            "-mavx2",
            "-mfma",
            "-ffp-contract=off",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(EVALUATOR_SOURCE),
            "-o",
            str(evaluator),
        ],
        ROOT,
    )
    return evaluator, {"command": receipt, "evaluatorSha256": sha256(evaluator)}


def evaluate(
    evaluator: Path, parameters: Path, output: Path
) -> dict[str, Any]:
    receipt = execute(
        [str(evaluator), str(parameters), str(INCOMING), str(output)], WORK
    )
    if not output.is_file() or output.stat().st_size != ELEMENTS * 2:
        raise ValueError("lane-order evaluator output geometry differs")
    return {"receipt": receipt, "sha256": sha256(output)}


def comparison(left: Path, right: Path) -> dict[str, int | float]:
    mismatch_count, maximum_error = open_base.parent.compare_bf16(left, right)
    return {
        "mismatchCount": mismatch_count,
        "maximumAbsoluteError": maximum_error,
    }


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        EVALUATOR_SOURCE.resolve(),
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
        raise ValueError("lane-order source closure exceeds ceiling")


def evaluate_predicates(
    predicates: list[dict[str, Any]], measurements: dict[str, Any]
) -> list[dict[str, Any]]:
    return open_base.evaluate(predicates, measurements)


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
        raise ValueError("job and lane-order experiment bindings differ")
    candidate_revision = json.loads(
        os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
    )
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    parameters, parameter_bound, library_bound = require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("lane-order result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("lane-order work root was not fresh")

    evaluator, build = compile_evaluator()
    outputs = [WORK / "lane-a.bf16", WORK / "lane-b.bf16"]
    evaluations = [evaluate(evaluator, parameters, item) for item in outputs]
    replay_identical = evaluations[0]["sha256"] == evaluations[1]["sha256"]
    baseline_source = comparison(OPEN_RESIDUAL, SOURCE_ADJOINT)
    treatment_source = comparison(outputs[0], SOURCE_ADJOINT)
    treatment_baseline = comparison(outputs[0], OPEN_RESIDUAL)
    artifact = RESULT / "lane-sequential-ff2-input-adjoint.bf16"
    shutil.copyfile(outputs[0], artifact)
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "build": build,
                "sourceKernelAttribution": {
                    "librarySha256": EXPECTED_LIBNC_SHA256,
                    "matmulTypeDispatchTableOffset": "0x288d80",
                    "bf16KernelOffset": "0x7e40",
                    "accumulation": (
                        "one ordered FMA stream per output feature lane; "
                        "the reduction dimension is not horizontally folded"
                    ),
                },
                "evaluations": evaluations,
                "evaluationReplayIdentical": replay_identical,
                "baselineSourceComparison": baseline_source,
                "treatmentSourceComparison": treatment_source,
                "treatmentBaselineComparison": treatment_baseline,
                "parameterFixtureSha256": EXPECTED_PARAMETER_SHA256,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "evaluationReplayIdentical": replay_identical,
        "adjointElementCount": artifact.stat().st_size // 2,
        "baselineSourceMismatchCount": baseline_source["mismatchCount"],
        "laneSequentialSourceMismatchCount": treatment_source["mismatchCount"],
        "maximumLaneSequentialAbsoluteError": treatment_source[
            "maximumAbsoluteError"
        ],
        "treatmentChangesBaseline": treatment_baseline["mismatchCount"] > 0,
        "sourceLibraryDigestBound": library_bound,
        "parameterFixtureDigestBound": parameter_bound,
        "incrementalSourceBytes": incremental_source.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = evaluate_predicates(
        experiment["promotionPredicates"], measurements
    )
    kill = evaluate_predicates(experiment["killPredicates"], measurements)
    promotion_pass = all(item["passed"] for item in promotion)
    kill_pass = all(item["passed"] for item in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": reference(experiment_path),
        "candidateId": CANDIDATE_ID,
        "candidateRevision": candidate_revision,
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
            else "retire"
            if kill_pass
            else "retry"
        ),
        "artifacts": [
            reference(execution_path, "execution"),
            reference(artifact, "lane-sequential-ff2-input-adjoint"),
            reference(incremental_source, "incremental-source-package"),
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
