#!/usr/bin/env python3
"""Resolve production BF16 final-RMSNorm order through exact affine replay."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import lzma
import os
from pathlib import Path
import shutil
import struct
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_final_rmsnorm_order_64_q0 as order_parent
import nncp_open_profile_top_ff2_gradient_64_q0_retry_v1 as open_parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_final_rmsnorm_affine_order_64_q0_v1"
PARENT_ID = "nncp_libnc_final_rmsnorm_order_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T072401Z_436d248c4d.json"
)
SOURCE_INPUT = PARENT_RESULT / "source-final-rms-input.bf16"
SOURCE_AFFINE_OUTPUT = PARENT_RESULT / "source-final-rms-output.bf16"
SOURCE_ADJOINT_ID = "nncp_libnc_top_ff2_adjoint_64_q0_retry_v1"
SOURCE_ADJOINT_RESULT = ROOT / "results" / SOURCE_ADJOINT_ID
SOURCE_ADJOINT_DECISION = SOURCE_ADJOINT_RESULT / "decision.json"
SOURCE_ADJOINT = SOURCE_ADJOINT_RESULT / "source-top-ff2-adjoint.bf16"
OPEN_ID = "nncp_open_profile_top_ff2_gradient_64_q0_retry_v1"
OPEN_RESULT = ROOT / "results" / OPEN_ID
OPEN_DECISION = OPEN_RESULT / "decision.json"
INCOMING_RESIDUAL = OPEN_RESULT / "open-final-hidden-residual.bf16"
OPEN_INPUT_ADJOINT = OPEN_RESULT / "open-final-norm-input-residual.bf16"
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
PARAMETERS = FIXTURE_ROOT / "fixture/parameters_initial.coefs"
EVALUATOR_SOURCE = PROGRAM / "final_rmsnorm_order.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_final_rmsnorm_affine_order_64_q0_materializer.py"
)
RUNNER = Path(__file__).resolve()
SOURCE_CEILING = 1_000_000
STATES = 64
STREAMS = 32
WIDTH = 1024
ELEMENTS = STATES * STREAMS * WIDTH
VARIANTS = order_parent.VARIANTS
COEFFICIENT_MAGIC = 0x23F4AEFB
TENSOR_MAGIC = 0x23F4AEFA
TYPE_SIZES = (4, 2, 2, 1, 2, 4, 1, 2, 4)


sha256 = order_parent.sha256
reference = order_parent.reference
execute = order_parent.execute


def read_u32(stream) -> int:
    payload = stream.read(4)
    if len(payload) != 4:
        raise ValueError("truncated coefficient u32")
    return struct.unpack("<I", payload)[0]


def extract_affine_parameters(path: Path, bias_output: Path) -> dict[str, Any]:
    found: dict[str, bytes] = {}
    with path.open("rb") as stream:
        if read_u32(stream) != COEFFICIENT_MAGIC:
            raise ValueError("invalid coefficient container")
        stream.seek(read_u32(stream), os.SEEK_CUR)
        while stream.tell() < path.stat().st_size:
            marker = stream.read(4)
            if not marker:
                break
            if len(marker) != 4 or struct.unpack("<I", marker)[0] != TENSOR_MAGIC:
                raise ValueError("invalid coefficient tensor marker")
            item_type = read_u32(stream)
            rank = read_u32(stream)
            name_size = read_u32(stream)
            dimensions = tuple(read_u32(stream) for _ in range(rank))
            name = stream.read(name_size).decode()
            count = 1
            for dimension in dimensions:
                count *= dimension
            if item_type >= len(TYPE_SIZES):
                raise ValueError("unsupported coefficient item type")
            byte_count = count * TYPE_SIZES[item_type]
            if name in {"ln_g_40", "ln_b_40"}:
                payload = stream.read(byte_count)
                if len(payload) != byte_count:
                    raise ValueError("truncated final-normalization parameter")
                if item_type != 1 or dimensions != (WIDTH,):
                    raise ValueError("final-normalization parameter geometry differs")
                found[name] = payload
            else:
                stream.seek(byte_count, os.SEEK_CUR)
    if set(found) != {"ln_g_40", "ln_b_40"}:
        raise ValueError("missing final-normalization affine parameter")
    gain_words = struct.unpack(f"<{WIDTH}H", found["ln_g_40"])
    bias_words = struct.unpack(f"<{WIDTH}H", found["ln_b_40"])
    one_word = struct.unpack("<H", struct.pack("<f", 1.0)[2:])[0]
    bias_output.write_bytes(found["ln_b_40"])
    return {
        "gainAllOne": all(word == one_word for word in gain_words),
        "biasDistinctWordCount": len(set(bias_words)),
        "biasNonzeroWordCount": sum(word not in {0, 0x8000} for word in bias_words),
        "gainSha256": __import__("hashlib").sha256(found["ln_g_40"]).hexdigest(),
        "biasSha256": __import__("hashlib").sha256(found["ln_b_40"]).hexdigest(),
    }


def compile_evaluator(scratch: Path) -> tuple[Path, dict[str, Any]]:
    evaluator = scratch / "final_rmsnorm_affine_order"
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
    return evaluator, {
        "command": receipt,
        "evaluatorSha256": sha256(evaluator),
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
        raise ValueError("affine-order source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-invalid-decision", PARENT_DECISION),
        ("parent-invalid-execution", PARENT_EXECUTION),
        ("parent-invalid-reflection", PARENT_REFLECTION),
        ("source-final-rms-input", SOURCE_INPUT),
        ("source-final-rms-affine-output", SOURCE_AFFINE_OUTPUT),
        ("source-adjoint-decision", SOURCE_ADJOINT_DECISION),
        ("source-final-rms-input-adjoint", SOURCE_ADJOINT),
        ("open-tail-decision", OPEN_DECISION),
        ("open-incoming-residual", INCOMING_RESIDUAL),
        ("open-input-adjoint", OPEN_INPUT_ADJOINT),
        ("production-initial-parameters", PARAMETERS),
        ("evaluator-source", EVALUATOR_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    source = json.loads(SOURCE_ADJOINT_DECISION.read_text())
    open_decision = json.loads(OPEN_DECISION.read_text())
    if not (
        parent["promotionPass"] is False
        and parent["killPass"] is False
        and parent["measurements"]["sourceCaptureRepeatIdentical"] is True
        and parent["measurements"]["parentFixtureIdentity"] is True
        and reflection["validity"]["classification"] == "invalid-experiment"
        and reflection["hypothesis"]["verdict"] == "not-tested"
        and reflection["decision"]["verdict"] == "retry"
        and source["promotionPass"] is True
        and source["measurements"]["sourceFf2MismatchCount"] == 0
        and source["measurements"]["openAdjointMismatchCount"] == 8
        and open_decision["measurements"]["openBackwardDeterministic"] is True
        and open_decision["measurements"]["topFf2MismatchCount"] == 184
    ):
        raise ValueError("affine-order antecedents are not satisfied")


def evaluate_run(
    evaluator: Path, bias: Path, directory: Path
) -> dict[str, Any]:
    directory.mkdir()
    receipt = execute(
        [
            str(evaluator),
            str(SOURCE_INPUT),
            str(INCOMING_RESIDUAL),
            str(bias),
            str(directory),
        ],
        WORK,
    )
    files = {
        name: directory / f"{name}.bf16"
        for name in ("forward", "affine", *VARIANTS, "negated_control")
    }
    expected_bytes = ELEMENTS * 2
    if any(
        not path.is_file() or path.stat().st_size != expected_bytes
        for path in files.values()
    ):
        raise ValueError("affine-order evaluator output geometry differs")
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
        raise ValueError("job and affine-order experiment bindings differ")
    candidate_revision = json.loads(
        os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
    )
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("affine-order result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("affine-order work root was not fresh")

    scratch = WORK / "build"
    scratch.mkdir()
    evaluator, build = compile_evaluator(scratch)
    bias = WORK / "ln-b-40.bf16"
    affine_parameters = extract_affine_parameters(PARAMETERS, bias)
    evaluations = [
        evaluate_run(evaluator, bias, WORK / "evaluation-a"),
        evaluate_run(evaluator, bias, WORK / "evaluation-b"),
    ]
    replay_identical = evaluations[0]["sha256"] == evaluations[1]["sha256"]
    affine_comparison = comparison(
        evaluations[0]["files"]["affine"], SOURCE_AFFINE_OUTPUT
    )
    variant_source_comparisons = {
        name: comparison(evaluations[0]["files"][name], SOURCE_ADJOINT)
        for name in VARIANTS
    }
    current_open_comparison = comparison(
        evaluations[0]["files"]["centered_fma_precenter"],
        OPEN_INPUT_ADJOINT,
    )
    open_source_comparison = comparison(OPEN_INPUT_ADJOINT, SOURCE_ADJOINT)
    exact_variants = [
        name
        for name in VARIANTS
        if variant_source_comparisons[name]["mismatchCount"] == 0
    ]
    control_comparison = comparison(
        evaluations[0]["files"]["negated_control"], SOURCE_ADJOINT
    )

    normalized_artifact = RESULT / "open-final-rms-normalized.bf16"
    bias_artifact = RESULT / "ln-b-40.bf16"
    shutil.copyfile(evaluations[0]["files"]["forward"], normalized_artifact)
    shutil.copyfile(bias, bias_artifact)
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "build": build,
                "affineParameters": affine_parameters,
                "evaluations": [
                    {"receipt": item["receipt"], "sha256": item["sha256"]}
                    for item in evaluations
                ],
                "evaluationReplayIdentical": replay_identical,
                "affineComparison": affine_comparison,
                "variantSourceComparisons": variant_source_comparisons,
                "currentOpenComparison": current_open_comparison,
                "openSourceComparison": open_source_comparison,
                "negatedControlComparison": control_comparison,
                "exactVariants": exact_variants,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)

    current_source = variant_source_comparisons["centered_fma_precenter"]
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "evaluationReplayIdentical": replay_identical,
        "gainAllOne": affine_parameters["gainAllOne"],
        "biasDistinctWordCount": affine_parameters["biasDistinctWordCount"],
        "biasNonzeroWordCount": affine_parameters["biasNonzeroWordCount"],
        "affineMismatchCount": affine_comparison["mismatchCount"],
        "maximumAffineAbsoluteError": affine_comparison[
            "maximumAbsoluteError"
        ],
        "currentOpenMismatchCount": current_open_comparison["mismatchCount"],
        "maximumCurrentOpenAbsoluteError": current_open_comparison[
            "maximumAbsoluteError"
        ],
        "currentSourceMismatchCount": current_source["mismatchCount"],
        "openSourceMismatchCount": open_source_comparison["mismatchCount"],
        "exactVariantCount": len(exact_variants),
        "negatedControlDiffers": control_comparison["mismatchCount"] > 0,
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
            reference(normalized_artifact, "open-final-rms-normalized"),
            reference(bias_artifact, "final-rms-bias"),
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
