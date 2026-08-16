#!/usr/bin/env python3
"""Verify the full exact open top-FF1 matrix gradient."""

from __future__ import annotations

import argparse
from array import array
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import sys
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_ff1_bias_state_reduce_64_q0 as oracle
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_ff1_weight_slice_post_add_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_SLICE = PARENT_RESULT / "open-treatment-slice.bf16"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T120602Z_ec1474d292.json"
)
SOURCE_RESULT = ROOT / "results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1"
OPEN_INPUT = SOURCE_RESULT / "open-ff1-input.bf16"
RESIDUAL = ROOT / (
    "results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/"
    "open-ff1-output-residual.bf16"
)
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_DECISION = FIXTURE / "decision.json"
COMPARATOR = FIXTURE / "fixture/gradients/0002_ff1_19.bin"
COMPARATOR_META = FIXTURE / "fixture/gradients/0002_ff1_19.meta"
EVALUATOR_SOURCE = PROGRAM / "ff1_weight_gradient.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_open_profile_top_ff1_gradient_post_add_64_q0_materializer.py"
)
INPUTS = 1024
OUTPUTS = 6144
SLICE_OUTPUTS = 128
ELEMENTS = INPUTS * OUTPUTS
BLOCK_COUNT = OUTPUTS // SLICE_OUTPUTS
SOURCE_CEILING = 500_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return oracle.reference(path, identifier)


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("parent-exact-slice", PARENT_SLICE),
        ("open-ff1-input", OPEN_INPUT),
        ("source-exact-ff1-output-residual", RESIDUAL),
        ("fixture-decision", FIXTURE_DECISION),
        ("retained-ff1-19-gradient", COMPARATOR),
        ("retained-ff1-19-gradient-meta", COMPARATOR_META),
        ("evaluator-source", EVALUATOR_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    guard = json.loads(PARENT_GUARD.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    if not (
        parent["promotionPass"] is True
        and parent["killPass"] is False
        and parent["measurements"]["treatmentMismatchCount"] == 0
        and parent["measurements"]["reverseOracleMismatchCount"] == 0
        and parent["measurements"]["negatedOracleMismatchCount"] == 0
        and parent["measurements"]["priorControlMismatchCount"] == 43
        and parent["measurements"]["nonfusedControlMismatchCount"] == 43
        and guard["returncode"] == 0
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "supported"
        and reflection["decision"]["verdict"] == "mutate"
        and fixture["measurements"]["fixtureComplete"] is True
    ):
        raise ValueError("full open FF1-gradient antecedents are not satisfied")


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
        raise ValueError("full open FF1-gradient source closure exceeds ceiling")


def read_words(path: Path) -> array:
    words = array("H")
    words.frombytes(path.read_bytes())
    if sys.byteorder != "little":
        words.byteswap()
    if len(words) != ELEMENTS:
        raise ValueError("full FF1-gradient comparison geometry differs")
    return words


def partition_comparison(left: Path, right: Path) -> dict[str, Any]:
    left_words = read_words(left)
    right_words = read_words(right)
    mismatches = [0] * BLOCK_COUNT
    for input_feature in range(INPUTS):
        base = input_feature * OUTPUTS
        for output_feature in range(OUTPUTS):
            if left_words[base + output_feature] != right_words[
                base + output_feature
            ]:
                mismatches[output_feature // SLICE_OUTPUTS] += 1
    return {
        "blockOutputWidth": SLICE_OUTPUTS,
        "blockMismatchCounts": mismatches,
        "exactBlockCount": sum(count == 0 for count in mismatches),
    }


def first_slice(source: Path, destination: Path) -> None:
    payload = source.read_bytes()
    if len(payload) != ELEMENTS * 2:
        raise ValueError("full FF1-gradient output geometry differs")
    sliced = bytearray(INPUTS * SLICE_OUTPUTS * 2)
    cursor = 0
    for input_feature in range(INPUTS):
        start = input_feature * OUTPUTS * 2
        block = payload[start : start + SLICE_OUTPUTS * 2]
        sliced[cursor : cursor + len(block)] = block
        cursor += len(block)
    destination.write_bytes(sliced)


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
        raise ValueError("job and full FF1-gradient experiment bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("full FF1-gradient result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("full FF1-gradient work root was not freshly materialized")

    build = WORK / "build"
    build.mkdir()
    evaluator = build / "ff1_weight_gradient"
    build_receipt = oracle.execute(
        [
            os.environ.get("CXX", "g++"), "-std=c++17", "-O3", "-mavx2",
            "-mfma", "-ffp-contract=off", "-Wall", "-Wextra", "-Werror",
            str(EVALUATOR_SOURCE), "-o", str(evaluator),
        ],
        ROOT,
    )
    ldd_receipt = oracle.execute(["ldd", str(evaluator)], ROOT)
    forbidden = [
        line
        for line in ldd_receipt["stdout"].splitlines()
        if any(
            token in line.lower()
            for token in ("libnc", "ggml", "cuda", "openmp", "gomp", "blas")
        )
    ]
    evaluations: list[dict[str, Any]] = []
    replay_paths: list[Path] = []
    for replay in ("a", "b"):
        replay_path = WORK / f"gradient-{replay}.bf16"
        receipt = oracle.execute(
            [str(evaluator), str(OPEN_INPUT), str(RESIDUAL), str(replay_path)],
            WORK,
        )
        if replay_path.stat().st_size != ELEMENTS * 2:
            raise ValueError("full FF1-gradient output geometry differs")
        evaluations.append({"receipt": receipt, "sha256": sha256(replay_path)})
        replay_paths.append(replay_path)
    replay_identical = replay_paths[0].read_bytes() == replay_paths[1].read_bytes()
    comparison = oracle.compare_bf16(replay_paths[0], COMPARATOR)
    partitions = partition_comparison(replay_paths[0], COMPARATOR)
    extracted_slice = WORK / "first-slice.bf16"
    first_slice(replay_paths[0], extracted_slice)
    slice_comparison = oracle.compare_bf16(extracted_slice, PARENT_SLICE)

    gradient = RESULT / "source-exact-ff1-19-gradient.bf16"
    shutil.copyfile(replay_paths[0], gradient)
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "arithmeticContract": {
                    "stateOrder": "chronological 0..63",
                    "streamOrder": "0..31 within every state",
                    "dot": "32 sequential AVX2 FMAs from zero",
                    "prior": "add decoded prior BF16 gradient after each dot",
                    "materialization": "round-to-nearest-even BF16 after every state",
                    "laneMapping": "eight adjacent FF1 output features",
                    "outputMapping": "input feature major, output feature minor",
                },
                "build": build_receipt,
                "comparison": comparison,
                "evaluations": evaluations,
                "forbiddenDynamicDependencies": forbidden,
                "ldd": ldd_receipt,
                "parentSliceComparison": slice_comparison,
                "partitionComparison": partitions,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "inputFeatureCount": INPUTS,
        "outputFeatureCount": OUTPUTS,
        "gradientElementCount": ELEMENTS,
        "outputBlockCount": BLOCK_COUNT,
        "exactOutputBlockCount": partitions["exactBlockCount"],
        "treatmentMismatchCount": comparison["mismatchCount"],
        "maximumTreatmentAbsoluteError": comparison["maximumAbsoluteError"],
        "parentSliceMismatchCount": slice_comparison["mismatchCount"],
        "evaluationReplayIdentical": replay_identical,
        "forbiddenDynamicDependencyCount": len(forbidden),
        "incrementalSourceBytes": incremental_source.stat().st_size,
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
            reference(gradient, "source-exact-ff1-19-gradient"),
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
