#!/usr/bin/env python3
"""Validate the exact open layer-19 pre-w_o forward value."""

from __future__ import annotations

import argparse
from array import array
from concurrent.futures import ThreadPoolExecutor
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
import nncp_open_profile_output_bias_gradient_64_q0_retry as forward
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_w_o_input_forward_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_w_o_input_adjoint_block128_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T164348Z_ff5718724e.json"
)
FORWARD_ID = "nncp_open_profile_output_bias_gradient_64_q0_retry_v1"
FORWARD_RESULT = ROOT / "results" / FORWARD_ID
FORWARD_DECISION = FORWARD_RESULT / "decision.json"
FORWARD_EXECUTION = FORWARD_RESULT / "execution.json"
FORWARD_GUARD = FORWARD_RESULT / "guard.json"
FORWARD_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T033450Z_727c49438a.json"
)
SOURCE_ID = "nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1"
SOURCE_RESULT = ROOT / "results" / SOURCE_ID
SOURCE_DECISION = SOURCE_RESULT / "decision.json"
SOURCE_EXECUTION = SOURCE_RESULT / "execution.json"
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T162351Z_97a6519638.json"
)
SOURCE_INPUT = SOURCE_RESULT / "source-w-o-input.bf16"
Q3_RESULT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
Q3_DECISION = Q3_RESULT / "decision.json"
Q3_MANIFEST = Q3_RESULT / "fixture-manifest.json"
Q3_GUARD = Q3_RESULT / "guard.json"
Q3_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json"
)
PARAMETERS = Q3_RESULT / "fixture/parameters_initial.coefs"
STATE = Q3_RESULT / "fixture/state_initial.params"
OPEN_SOURCE = ROOT / (
    "results/nncp_ggml_postupdate_forward_parity_64_q1_retry_v2/"
    "ggml_profile_forward_source_closure.tar.xz"
)
PARENT_FORWARD = ROOT / (
    "programs/nncp_ggml_postupdate_forward_parity_64_q1_retry_v1/"
    "profile_forward_parity.cpp"
)
FORWARD_MATERIALIZER = PROGRAM / "materialize_forward.py"
CMAKE = PROGRAM / "CMakeLists.txt"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MATERIALIZER = ROOT / "tools/nncp_open_top_w_o_input_forward_64_q0_materializer.py"
RUNNER = Path(__file__).resolve()
STREAMS = 32
STATES = 64
LAYERS = 20
WIDTH = 1024
ELEMENTS = STREAMS * STATES * WIDTH
SOURCE_CEILING = 2_000_000


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
        ("forward-decision", FORWARD_DECISION),
        ("forward-execution", FORWARD_EXECUTION),
        ("forward-guard", FORWARD_GUARD),
        ("forward-reflection", FORWARD_REFLECTION),
        ("source-decision", SOURCE_DECISION),
        ("source-execution", SOURCE_EXECUTION),
        ("source-reflection", SOURCE_REFLECTION),
        ("source-w-o-input", SOURCE_INPUT),
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
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    parent_reflection = json.loads(PARENT_REFLECTION.read_text())
    open_forward = json.loads(FORWARD_DECISION.read_text())
    forward_reflection = json.loads(FORWARD_REFLECTION.read_text())
    source = json.loads(SOURCE_DECISION.read_text())
    source_reflection = json.loads(SOURCE_REFLECTION.read_text())
    fixture = json.loads(Q3_DECISION.read_text())
    fixture_reflection = json.loads(Q3_REFLECTION.read_text())
    if not (
        parent["promotionPass"] is True
        and parent["measurements"]["block128SourceMismatchCount"] == 0
        and parent_reflection["validity"]["valid"] is True
        and parent_reflection["hypothesis"]["verdict"] == "supported"
        and open_forward["promotionPass"] is True
        and open_forward["measurements"]["layerInputMismatchCount"] == 0
        and open_forward["measurements"]["layerInputCheckpointCount"] == 640
        and forward_reflection["validity"]["valid"] is True
        and forward_reflection["hypothesis"]["verdict"] == "supported"
        and source["promotionPass"] is True
        and source["measurements"]["rawProbeTensorMismatchCount"] == 0
        and source_reflection["validity"]["valid"] is True
        and source_reflection["hypothesis"]["verdict"] == "supported"
        and fixture["promotionPass"] is True
        and fixture["measurements"]["streamPopulation"] == STREAMS
        and fixture["measurements"]["segmentPopulation"] == STATES
        and fixture_reflection["validity"]["valid"] is True
    ):
        raise ValueError("open pre-w_o forward antecedents are not satisfied")


def extract(archive: Path, destination: Path) -> dict[str, Any]:
    destination.mkdir()
    return forward.execute(
        [
            "tar", "--extract", "--xz", "--no-same-owner",
            "--no-same-permissions", "--file", str(archive),
            "--directory", str(destination),
        ],
        ROOT,
    )


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
        raise ValueError("open pre-w_o forward source closure exceeds ceiling")


def to_bf16_words(path: Path) -> array[int]:
    payload = path.read_bytes()
    if len(payload) != STATES * WIDTH * 4:
        raise ValueError(f"open pre-w_o output geometry differs: {path}")
    words = array("I")
    words.frombytes(payload)
    if sys.byteorder != "little":
        words.byteswap()
    if any(word & 0xFFFF for word in words):
        raise ValueError(f"open pre-w_o output is not exactly BF16: {path}")
    return array("H", (word >> 16 for word in words))


def assemble_pre_w_o(root: Path, treatment: Path, control: Path) -> None:
    streams = [
        to_bf16_words(root / f"stream_{stream:02d}/layer_19_pre_w_o_input.f32")
        for stream in range(STREAMS)
    ]
    with treatment.open("wb") as output:
        for state in range(STATES):
            begin = state * WIDTH
            end = begin + WIDTH
            for words in streams:
                output.write(words[begin:end].tobytes())
    with control.open("wb") as output:
        for words in streams:
            output.write(words.tobytes())
    expected_bytes = ELEMENTS * 2
    if treatment.stat().st_size != expected_bytes or control.stat().st_size != expected_bytes:
        raise ValueError("assembled open pre-w_o geometry differs")


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
        raise ValueError("job and open-forward bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("open pre-w_o result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("open pre-w_o work root is not fresh")

    source = WORK / "source"
    build = WORK / "build"
    shared_parameters = WORK / "parameters"
    fixtures = WORK / "fixtures"
    open_roots = [WORK / "open-a", WORK / "open-b"]
    executions: dict[str, Any] = {"extract": extract(OPEN_SOURCE, source)}
    executions["materialize"] = forward.execute(
        [
            "python3", str(FORWARD_MATERIALIZER), str(PARENT_FORWARD),
            str(source / "profile_top_w_o_input_forward.cpp"),
        ],
        ROOT,
    )
    shutil.copyfile(CMAKE, source / "CMakeLists.txt")
    executions["configure"] = forward.execute(
        ["cmake", "-S", str(source), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release"],
        ROOT,
    )
    executions["build"] = forward.execute(
        ["cmake", "--build", str(build), "--parallel", "4"], ROOT
    )
    binaries = [
        path for path in build.rglob("nncp_open_top_w_o_input_forward")
        if path.is_file()
    ]
    if len(binaries) != 1:
        raise ValueError("open pre-w_o executable is not unique")
    binary = binaries[0]
    ldd = forward.execute(["ldd", str(binary)], ROOT)
    executions["ldd"] = ldd
    forbidden = [
        line for line in ldd["stdout"].splitlines()
        if any(
            token in line.lower()
            for token in ("libnc", "cuda", "openmp", "gomp", "blas")
        )
    ]

    parameters = forward.Container(PARAMETERS)
    state = forward.Container(STATE)
    try:
        parameter_rows = forward.materialize_parameters(
            parameters, shared_parameters
        )
        for stream in range(STREAMS):
            forward.materialize_stream_fixture(
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
        for replay, root in zip(("a", "b"), open_roots):
            root.mkdir()

            def run_stream(stream: int) -> tuple[int, dict[str, Any]]:
                destination = root / f"stream_{stream:02d}"
                destination.mkdir()
                receipt = forward.execute(
                    [
                        str(binary), str(fixtures / f"stream_{stream:02d}"),
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
                current = forward.compare_layer_inputs(
                    state, stream, root / f"stream_{stream:02d}"
                )
                checkpoints += current[0]
                mismatches += current[1]
                maximum = max(maximum, current[2])
            treatment = WORK / f"open-pre-w-o-{replay}.bf16"
            control = WORK / f"stream-major-control-{replay}.bf16"
            assemble_pre_w_o(root, treatment, control)
            populations.append(
                {
                    "receipts": receipts,
                    "checkpoints": checkpoints,
                    "mismatches": mismatches,
                    "maximum": maximum,
                    "treatment": treatment,
                    "control": control,
                    "aggregate": forward.aggregate(root),
                }
            )
    finally:
        state.close()
        parameters.close()

    comparisons = {
        "treatment": oracle.compare_bf16(
            populations[0]["treatment"], SOURCE_INPUT
        ),
        "streamMajorControl": oracle.compare_bf16(
            populations[0]["control"], SOURCE_INPUT
        ),
    }
    replay_identical = (
        populations[0]["aggregate"] == populations[1]["aggregate"]
        and populations[0]["treatment"].read_bytes()
        == populations[1]["treatment"].read_bytes()
        and populations[0]["control"].read_bytes()
        == populations[1]["control"].read_bytes()
        and populations[0]["checkpoints"] == populations[1]["checkpoints"]
        and populations[0]["mismatches"] == populations[1]["mismatches"]
        and populations[0]["maximum"] == populations[1]["maximum"]
    )
    artifact = RESULT / "open-exact-w-o-input.bf16"
    shutil.copyfile(populations[0]["treatment"], artifact)
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "assemblyContract": {
                    "sourceCoordinates": "state-major, stream-major, feature-major",
                    "openCoordinates": "per-stream state-major, feature-major",
                    "materialization": "exact high BF16 word of finite F32 values",
                    "staticDependency": "pinned GGML CPU source archive",
                },
                "comparisons": comparisons,
                "executions": executions,
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
                "forbiddenDynamicDependencies": forbidden,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)
    layer_mismatches = sum(row["mismatches"] for row in populations)
    maximum_layer_error = max(row["maximum"] for row in populations)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "streamCount": STREAMS,
        "sampleCount": STREAMS * STATES,
        "layerInputCheckpointCount": populations[0]["checkpoints"],
        "layerInputMismatchCount": layer_mismatches,
        "maximumLayerInputAbsoluteError": maximum_layer_error,
        "preWOElementCount": ELEMENTS,
        "treatmentSourceMismatchCount": comparisons["treatment"]["mismatchCount"],
        "maximumTreatmentAbsoluteError": comparisons["treatment"][
            "maximumAbsoluteError"
        ],
        "streamMajorControlMismatchCount": comparisons["streamMajorControl"][
            "mismatchCount"
        ],
        "openForwardReplayIdentical": replay_identical,
        "staticGgmlSourceBound": True,
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
        "promotionPass": promotion_pass,
        "killPass": kill_pass,
        "promotionPredicates": promotion,
        "killPredicates": kill,
        "measurements": measurements,
        "decision": "authorize-attention-descent" if promotion_pass else "reject",
        "artifacts": [
            reference(execution_path, "execution"),
            reference(artifact, "open-exact-w-o-input"),
            reference(incremental_source, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    return 0 if promotion_pass and not kill_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
