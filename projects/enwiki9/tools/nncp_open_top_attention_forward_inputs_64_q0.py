#!/usr/bin/env python3
"""Validate exact open layer-19 probability and value forward inputs."""

from __future__ import annotations

import argparse
from array import array
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import json
import lzma
import os
from pathlib import Path
import shutil
import sys
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_open_top_w_o_input_forward_64_q0 as open_base
import nncp_libnc_top_attention_product_oracle_64_q0_v1 as source
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_attention_forward_inputs_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_concat_head_identity_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T175422Z_91aae07812.json"
)
SOURCE_ID = "nncp_libnc_top_attention_product_oracle_64_q0_retry_v2"
SOURCE_RESULT = ROOT / "results" / SOURCE_ID
SOURCE_DECISION = SOURCE_RESULT / "decision.json"
SOURCE_EXECUTION = SOURCE_RESULT / "execution.json"
SOURCE_GUARD = SOURCE_RESULT / "guard.json"
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T174722Z_8b88b4a53d.json"
)
SOURCE_PROBABILITY = SOURCE_RESULT / "source-attention-probability-input.bf16"
SOURCE_ATTENDED = SOURCE_RESULT / "source-attended-heads-input.bf16"
FORWARD_RESULT = ROOT / "results/nncp_open_profile_output_bias_gradient_64_q0_retry_v1"
FORWARD_DECISION = FORWARD_RESULT / "decision.json"
FORWARD_EXECUTION = FORWARD_RESULT / "execution.json"
FORWARD_GUARD = FORWARD_RESULT / "guard.json"
FORWARD_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T033450Z_727c49438a.json"
)
Q3_RESULT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
Q3_DECISION = Q3_RESULT / "decision.json"
Q3_MANIFEST = Q3_RESULT / "fixture-manifest.json"
Q3_GUARD = Q3_RESULT / "guard.json"
Q3_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json"
)
PARAMETERS = Q3_RESULT / "fixture/parameters_initial.coefs"
STATE = Q3_RESULT / "fixture/state_initial.params"
OPEN_SOURCE = open_base.OPEN_SOURCE
PARENT_FORWARD = open_base.PARENT_FORWARD
FORWARD_MATERIALIZER = PROGRAM / "materialize_forward.py"
CMAKE = PROGRAM / "CMakeLists.txt"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MATERIALIZER = ROOT / (
    "tools/nncp_open_top_attention_forward_inputs_64_q0_materializer.py"
)
RUNNER = Path(__file__).resolve()
STREAMS = 32
STATES = 64
LAYERS = 20
HEADS = 8
KEYS = 320
HEAD_WIDTH = 128
WIDTH = 1024
PROBABILITY_ELEMENTS = STATES * STREAMS * HEADS * KEYS
VALUE_ELEMENTS = STREAMS * HEADS * KEYS * HEAD_WIDTH
ATTENDED_ELEMENTS = STATES * STREAMS * WIDTH
SOURCE_CEILING = 2_000_000


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return source.reference(path, identifier)


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("source-decision", SOURCE_DECISION),
        ("source-execution", SOURCE_EXECUTION),
        ("source-guard", SOURCE_GUARD),
        ("source-reflection", SOURCE_REFLECTION),
        ("source-probability-input", SOURCE_PROBABILITY),
        ("source-attended-input", SOURCE_ATTENDED),
        ("forward-decision", FORWARD_DECISION),
        ("forward-execution", FORWARD_EXECUTION),
        ("forward-guard", FORWARD_GUARD),
        ("forward-reflection", FORWARD_REFLECTION),
        ("fixture-decision", Q3_DECISION),
        ("fixture-manifest", Q3_MANIFEST),
        ("fixture-guard", Q3_GUARD),
        ("fixture-reflection", Q3_REFLECTION),
        ("initial-parameters", PARAMETERS),
        ("initial-state", STATE),
        ("exact-forward-source", OPEN_SOURCE),
        ("promoted-forward-source", PARENT_FORWARD),
        ("forward-materializer", FORWARD_MATERIALIZER),
        ("cmake", CMAKE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"attention forward input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    parent_reflection = json.loads(PARENT_REFLECTION.read_text())
    source_result = json.loads(SOURCE_DECISION.read_text())
    source_reflection = json.loads(SOURCE_REFLECTION.read_text())
    forward_result = json.loads(FORWARD_DECISION.read_text())
    forward_reflection = json.loads(FORWARD_REFLECTION.read_text())
    fixture = json.loads(Q3_DECISION.read_text())
    fixture_reflection = json.loads(Q3_REFLECTION.read_text())
    if not (
        parent["promotionPass"] is True
        and parent["measurements"]["adjointMismatchCount"] == 0
        and parent_reflection["validity"]["valid"] is True
        and parent_reflection["hypothesis"]["verdict"] == "supported"
        and source_result["promotionPass"] is True
        and source_result["measurements"]["concatSourceMismatchCount"] == 0
        and source_result["measurements"]["probabilityInputElementCount"]
        == PROBABILITY_ELEMENTS
        and source_reflection["validity"]["valid"] is True
        and source_reflection["hypothesis"]["verdict"] == "supported"
        and forward_result["promotionPass"] is True
        and forward_result["measurements"]["layerInputMismatchCount"] == 0
        and forward_result["measurements"]["layerInputCheckpointCount"] == 640
        and forward_reflection["validity"]["valid"] is True
        and forward_reflection["hypothesis"]["verdict"] == "supported"
        and fixture["promotionPass"] is True
        and fixture["measurements"]["streamPopulation"] == STREAMS
        and fixture["measurements"]["segmentPopulation"] == STATES
        and fixture_reflection["validity"]["valid"] is True
    ):
        raise ValueError("attention forward antecedents are not satisfied")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        FORWARD_MATERIALIZER.resolve(),
        CMAKE.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        PARENT_FORWARD.resolve(),
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
        raise ValueError("attention forward source closure exceeds ceiling")


def to_bf16_words(path: Path, elements: int) -> array[int]:
    payload = path.read_bytes()
    if len(payload) != elements * 4:
        raise ValueError(f"open attention output geometry differs: {path}")
    words = array("I")
    words.frombytes(payload)
    if sys.byteorder != "little":
        words.byteswap()
    if any(word & 0xFFFF for word in words):
        raise ValueError(f"open attention output is not exactly BF16: {path}")
    return array("H", (word >> 16 for word in words))


def assemble_population(
    root: Path,
    probability: Path,
    probability_control: Path,
    value_state: Path,
    attended: Path,
) -> None:
    probabilities = [
        to_bf16_words(
            root / f"stream_{stream:02d}/layer_19_attention_probability.f32",
            HEADS * STATES * KEYS,
        )
        for stream in range(STREAMS)
    ]
    values = [
        to_bf16_words(
            root / f"stream_{stream:02d}/layer_19_value_state.f32",
            HEADS * KEYS * HEAD_WIDTH,
        )
        for stream in range(STREAMS)
    ]
    attended_streams = [
        to_bf16_words(
            root / f"stream_{stream:02d}/layer_19_pre_w_o_input.f32",
            STATES * WIDTH,
        )
        for stream in range(STREAMS)
    ]
    with probability.open("wb") as output:
        for state in range(STATES):
            for stream_words in probabilities:
                for head in range(HEADS):
                    begin = (head * STATES + state) * KEYS
                    output.write(stream_words[begin : begin + KEYS].tobytes())
    with probability_control.open("wb") as output:
        for stream_words in probabilities:
            output.write(stream_words.tobytes())
    with value_state.open("wb") as output:
        for stream_words in values:
            output.write(stream_words.tobytes())
    with attended.open("wb") as output:
        for state in range(STATES):
            begin = state * WIDTH
            for stream_words in attended_streams:
                output.write(stream_words[begin : begin + WIDTH].tobytes())
    expected = {
        probability: PROBABILITY_ELEMENTS,
        probability_control: PROBABILITY_ELEMENTS,
        value_state: VALUE_ELEMENTS,
        attended: ATTENDED_ELEMENTS,
    }
    for path, elements in expected.items():
        if path.stat().st_size != elements * 2:
            raise ValueError(f"assembled attention geometry differs: {path}")


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
        raise ValueError("job and attention forward bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("attention forward result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("attention forward work root is not fresh")

    source_tree = WORK / "source"
    build = WORK / "build"
    shared_parameters = WORK / "parameters"
    fixtures = WORK / "fixtures"
    open_roots = [WORK / "open-a", WORK / "open-b"]
    executions: dict[str, Any] = {
        "extract": open_base.extract(OPEN_SOURCE, source_tree)
    }
    executions["materialize"] = open_base.forward.execute(
        [
            "python3",
            str(FORWARD_MATERIALIZER),
            str(PARENT_FORWARD),
            str(source_tree / "profile_top_attention_forward_inputs.cpp"),
        ],
        ROOT,
    )
    shutil.copyfile(CMAKE, source_tree / "CMakeLists.txt")
    executions["configure"] = open_base.forward.execute(
        [
            "cmake",
            "-S",
            str(source_tree),
            "-B",
            str(build),
            "-DCMAKE_BUILD_TYPE=Release",
        ],
        ROOT,
    )
    executions["build"] = open_base.forward.execute(
        ["cmake", "--build", str(build), "--parallel", "4"], ROOT
    )
    binaries = [
        path
        for path in build.rglob("nncp_open_top_attention_forward_inputs")
        if path.is_file()
    ]
    if len(binaries) != 1:
        raise ValueError("attention forward executable is not unique")
    binary = binaries[0]
    ldd = open_base.forward.execute(["ldd", str(binary)], ROOT)
    executions["ldd"] = ldd
    forbidden = [
        line
        for line in ldd["stdout"].splitlines()
        if any(
            token in line.lower()
            for token in ("libnc", "cuda", "openmp", "gomp", "blas")
        )
    ]

    parameters = open_base.forward.Container(PARAMETERS)
    state = open_base.forward.Container(STATE)
    try:
        parameter_rows = open_base.forward.materialize_parameters(
            parameters, shared_parameters
        )
        fixtures.mkdir()
        for stream in range(STREAMS):
            open_base.forward.materialize_stream_fixture(
                state,
                shared_parameters,
                parameter_rows,
                stream,
                fixtures / f"stream_{stream:02d}",
            )
        clean_home = WORK / "home"
        clean_home.mkdir()
        environment = {
            "HOME": str(clean_home),
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
        }
        populations = []
        for replay, root in zip(("a", "b"), open_roots, strict=True):
            root.mkdir()

            def run_stream(stream: int) -> tuple[int, dict[str, Any]]:
                destination = root / f"stream_{stream:02d}"
                destination.mkdir()
                receipt = open_base.forward.execute(
                    [
                        str(binary),
                        str(fixtures / f"stream_{stream:02d}"),
                        str(destination),
                    ],
                    WORK,
                    environment,
                )
                return stream, receipt

            receipts: dict[str, Any] = {}
            with ThreadPoolExecutor(max_workers=2) as executor:
                for stream, receipt in executor.map(run_stream, range(STREAMS)):
                    receipts[f"stream-{stream:02d}"] = receipt
            checkpoints = 0
            mismatches = 0
            maximum = 0.0
            for stream in range(STREAMS):
                current = open_base.forward.compare_layer_inputs(
                    state, stream, root / f"stream_{stream:02d}"
                )
                checkpoints += current[0]
                mismatches += current[1]
                maximum = max(maximum, current[2])
            paths = {
                "probability": WORK / f"open-probability-{replay}.bf16",
                "probabilityControl": WORK
                / f"stream-major-probability-{replay}.bf16",
                "valueState": WORK / f"open-value-state-{replay}.bf16",
                "attended": WORK / f"open-attended-{replay}.bf16",
            }
            assemble_population(
                root,
                paths["probability"],
                paths["probabilityControl"],
                paths["valueState"],
                paths["attended"],
            )
            populations.append(
                {
                    "aggregate": open_base.forward.aggregate(root),
                    "checkpoints": checkpoints,
                    "maximum": maximum,
                    "mismatches": mismatches,
                    "paths": paths,
                    "receipts": receipts,
                }
            )
    finally:
        state.close()
        parameters.close()

    comparisons = {
        "probability": source.oracle.compare_bf16(
            populations[0]["paths"]["probability"], SOURCE_PROBABILITY
        ),
        "probabilityControl": source.oracle.compare_bf16(
            populations[0]["paths"]["probabilityControl"], SOURCE_PROBABILITY
        ),
        "attended": source.oracle.compare_bf16(
            populations[0]["paths"]["attended"], SOURCE_ATTENDED
        ),
    }
    replay_identical = (
        populations[0]["aggregate"] == populations[1]["aggregate"]
        and populations[0]["checkpoints"] == populations[1]["checkpoints"]
        and populations[0]["mismatches"] == populations[1]["mismatches"]
        and populations[0]["maximum"] == populations[1]["maximum"]
        and all(
            populations[0]["paths"][key].read_bytes()
            == populations[1]["paths"][key].read_bytes()
            for key in populations[0]["paths"]
        )
    )
    probability_artifact = RESULT / "open-exact-attention-probability.bf16"
    value_artifact = RESULT / "open-exact-value-state.bf16"
    shutil.copyfile(populations[0]["paths"]["probability"], probability_artifact)
    shutil.copyfile(populations[0]["paths"]["valueState"], value_artifact)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "assemblyContract": {
                    "probability": (
                        "state-major, stream-major, head-major, key-major"
                    ),
                    "valueState": (
                        "stream-major, head-major, key-major, "
                        "feature-major"
                    ),
                    "materialization": "exact high BF16 word of finite F32",
                    "staticDependency": "pinned GGML CPU source archive",
                },
                "comparisons": comparisons,
                "executions": executions,
                "forbiddenDynamicDependencies": forbidden,
                "populationReceipts": [
                    {
                        "aggregate": row["aggregate"],
                        "checkpoints": row["checkpoints"],
                        "maximum": row["maximum"],
                        "mismatches": row["mismatches"],
                        "receipts": row["receipts"],
                    }
                    for row in populations
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "streamCount": STREAMS,
        "sampleCount": STREAMS * STATES,
        "layerInputCheckpointCount": populations[0]["checkpoints"],
        "layerInputMismatchCount": sum(
            row["mismatches"] for row in populations
        ),
        "maximumLayerInputAbsoluteError": max(
            row["maximum"] for row in populations
        ),
        "probabilityElementCount": probability_artifact.stat().st_size // 2,
        "valueStateElementCount": value_artifact.stat().st_size // 2,
        "probabilitySourceMismatchCount": comparisons["probability"][
            "mismatchCount"
        ],
        "maximumProbabilityAbsoluteError": comparisons["probability"][
            "maximumAbsoluteError"
        ],
        "attendedSourceMismatchCount": comparisons["attended"][
            "mismatchCount"
        ],
        "maximumAttendedAbsoluteError": comparisons["attended"][
            "maximumAbsoluteError"
        ],
        "streamMajorControlMismatchCount": comparisons[
            "probabilityControl"
        ]["mismatchCount"],
        "valueStateLive": any(value_artifact.read_bytes()),
        "openForwardReplayIdentical": replay_identical,
        "staticGgmlSourceBound": True,
        "forbiddenDynamicDependencyCount": len(forbidden),
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
            reference(probability_artifact, "open-exact-attention-probability"),
            reference(value_artifact, "open-exact-value-state"),
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
