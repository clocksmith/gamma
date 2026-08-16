#!/usr/bin/env python3
"""Resolve final-RMSNorm backward reduction and scalar placement exactly."""

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
import nncp_libnc_final_rmsnorm_affine_order_64_q0 as parent
import nncp_open_profile_top_ff2_gradient_64_q0_retry_v1 as open_parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1"
PARENT_ID = "nncp_libnc_final_rmsnorm_affine_order_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T074218Z_9b38a51094.json"
)
CAPTURE_RESULT = ROOT / "results/nncp_libnc_final_rmsnorm_order_64_q0_retry_v1"
SOURCE_INPUT = CAPTURE_RESULT / "source-final-rms-input.bf16"
NORMALIZED = PARENT_RESULT / "open-final-rms-normalized.bf16"
SOURCE_RESULT = ROOT / "results/nncp_libnc_top_ff2_adjoint_64_q0_retry_v1"
SOURCE_ADJOINT = SOURCE_RESULT / "source-top-ff2-adjoint.bf16"
OPEN_RESULT = ROOT / "results/nncp_open_profile_top_ff2_gradient_64_q0_retry_v1"
INCOMING = OPEN_RESULT / "open-final-hidden-residual.bf16"
OPEN_ADJOINT = OPEN_RESULT / "open-final-norm-input-residual.bf16"
CAPTURE_EXECUTION = CAPTURE_RESULT / "execution.json"
EVALUATOR_SOURCE = PROGRAM / "final_rmsnorm_order.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_final_rmsnorm_reduction_scale_64_q0_materializer.py"
)
RUNNER = Path(__file__).resolve()
SOURCE_CEILING = 1_000_000
ELEMENTS = 64 * 32 * 1024
EXPECTED_LIBNC_SHA256 = (
    "1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e"
)
VARIANTS = (
    "generic_dot_mean_scaled",
    "stream_dot_mean_scaled",
    "generic_dot_width_scaled",
    "stream_dot_width_scaled",
)


sha256 = parent.sha256
reference = parent.reference
execute = parent.execute


def compile_evaluator(scratch: Path) -> tuple[Path, dict[str, Any]]:
    evaluator = scratch / "final_rmsnorm_reduction_scale"
    command = [
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
    ]
    receipt = execute(command, ROOT)
    return evaluator, {"command": receipt, "evaluatorSha256": sha256(evaluator)}


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
        raise ValueError("reduction-scale source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> bool:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-reflection", PARENT_REFLECTION),
        ("source-final-rms-input", SOURCE_INPUT),
        ("open-final-rms-normalized", NORMALIZED),
        ("source-final-rms-input-adjoint", SOURCE_ADJOINT),
        ("open-incoming-residual", INCOMING),
        ("open-input-adjoint", OPEN_ADJOINT),
        ("source-capture-execution", CAPTURE_EXECUTION),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    decision = json.loads(PARENT_DECISION.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    capture = json.loads(CAPTURE_EXECUTION.read_text())
    library_digest = capture["externalInputSha256"].get(
        "/home/x/enwiki9-nonproof/external/nncp-2024-06-05/libnc.so"
    )
    if not (
        decision["promotionPass"] is False
        and decision["measurements"]["affineMismatchCount"] == 0
        and decision["measurements"]["currentOpenMismatchCount"] == 0
        and decision["measurements"]["currentSourceMismatchCount"] == 8
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "refuted"
        and reflection["decision"]["verdict"] == "mutate"
    ):
        raise ValueError("reduction-scale antecedents are not satisfied")
    return library_digest == EXPECTED_LIBNC_SHA256


def evaluate_run(evaluator: Path, directory: Path) -> dict[str, Any]:
    directory.mkdir()
    receipt = execute(
        [
            str(evaluator),
            str(SOURCE_INPUT),
            str(NORMALIZED),
            str(INCOMING),
            str(directory),
        ],
        WORK,
    )
    files = {
        name: directory / f"{name}.bf16"
        for name in (*VARIANTS, "negated_control")
    }
    expected_bytes = ELEMENTS * 2
    if any(
        not path.is_file() or path.stat().st_size != expected_bytes
        for path in files.values()
    ):
        raise ValueError("reduction-scale evaluator output geometry differs")
    return {
        "receipt": receipt,
        "files": files,
        "sha256": {name: sha256(path) for name, path in files.items()},
    }


def comparison(left: Path, right: Path) -> dict[str, int | float]:
    mismatch_count, maximum_error = open_parent.parent.compare_bf16(left, right)
    return {
        "mismatchCount": mismatch_count,
        "maximumAbsoluteError": maximum_error,
    }


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
        raise ValueError("job and reduction-scale experiment bindings differ")
    candidate_revision = json.loads(
        os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
    )
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    library_bound = require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("reduction-scale result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("reduction-scale work root was not fresh")

    scratch = WORK / "build"
    scratch.mkdir()
    evaluator, build = compile_evaluator(scratch)
    evaluations = [
        evaluate_run(evaluator, WORK / "evaluation-a"),
        evaluate_run(evaluator, WORK / "evaluation-b"),
    ]
    replay_identical = evaluations[0]["sha256"] == evaluations[1]["sha256"]
    source_comparisons = {
        name: comparison(evaluations[0]["files"][name], SOURCE_ADJOINT)
        for name in VARIANTS
    }
    baseline_open = comparison(
        evaluations[0]["files"]["generic_dot_mean_scaled"], OPEN_ADJOINT
    )
    control = comparison(
        evaluations[0]["files"]["negated_control"], SOURCE_ADJOINT
    )
    exact_variants = [
        name
        for name in VARIANTS
        if source_comparisons[name]["mismatchCount"] == 0
    ]
    treatment = "stream_dot_width_scaled"
    treatment_artifact = RESULT / "source-exact-final-rms-adjoint.bf16"
    shutil.copyfile(evaluations[0]["files"][treatment], treatment_artifact)
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "build": build,
                "sourceKernelAttribution": {
                    "librarySha256": EXPECTED_LIBNC_SHA256,
                    "layerNormBackwardDispatchOffset": "0x43090",
                    "bf16DotHelperOffset": "0xa4b0",
                    "sumHelper": "vec_sum_bf16",
                    "factorialVariants": list(VARIANTS),
                },
                "evaluations": [
                    {"receipt": item["receipt"], "sha256": item["sha256"]}
                    for item in evaluations
                ],
                "evaluationReplayIdentical": replay_identical,
                "sourceComparisons": source_comparisons,
                "baselineOpenComparison": baseline_open,
                "negatedControlComparison": control,
                "exactVariants": exact_variants,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)

    baseline_source = source_comparisons["generic_dot_mean_scaled"]
    treatment_source = source_comparisons[treatment]
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "evaluationReplayIdentical": replay_identical,
        "baselineOpenMismatchCount": baseline_open["mismatchCount"],
        "baselineSourceMismatchCount": baseline_source["mismatchCount"],
        "streamDotWidthScaledMismatchCount": treatment_source[
            "mismatchCount"
        ],
        "exactVariantCount": len(exact_variants),
        "alternativeExactCount": len(
            [name for name in exact_variants if name != treatment]
        ),
        "negatedControlDiffers": control["mismatchCount"] > 0,
        "sourceLibraryDigestBound": library_bound,
        "incrementalSourceBytes": incremental_source.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = open_parent.evaluate(
        experiment["promotionPredicates"], measurements
    )
    kill = open_parent.evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
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
            reference(treatment_artifact, "source-exact-final-rms-adjoint"),
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
