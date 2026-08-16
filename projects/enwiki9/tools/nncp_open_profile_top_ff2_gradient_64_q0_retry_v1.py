#!/usr/bin/env python3
"""Retry the top-layer FF2 gradient with a BF16 affine upstream."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import time
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_open_profile_final_hidden_residual_64_q0 as parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff2_gradient_64_q0_retry_v1"
PARENT_ID = "nncp_open_profile_top_ff2_gradient_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_DECISION = ROOT / "results" / PARENT_ID / "decision.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T055603Z_52a69ff065.json"
)
FINAL_NORM_ID = "nncp_open_profile_final_norm_backward_64_q0_retry_v2"
FINAL_NORM_DECISION = ROOT / "results" / FINAL_NORM_ID / "decision.json"
FINAL_NORM_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T053159Z_b79233ecb1.json"
)
FINAL_NORM_RESIDUAL = ROOT / (
    Path("results") / FINAL_NORM_ID / "open-final-hidden-residual.bf16"
)
PARENT_RESIDUAL = ROOT / "results" / PARENT_ID / "open-final-hidden-residual.bf16"
RMS_ORDER_DECISION = ROOT / (
    "results/nncp_v33_libnc_rmsnorm_backward_order_parity_v1/decision.json"
)
MATERIALIZER = PROGRAM / "materialize_forward.py"
CMAKE = PROGRAM / "CMakeLists.txt"
NORM_REDUCER = PROGRAM / "final_norm_backward.cpp"
FF2_REDUCER = PROGRAM / "top_ff2_gradient.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
SOURCE_CEILING = 2_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"reference is not a project file: {path}")
    value = {
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }
    if identifier is not None:
        value["id"] = identifier
    return value


def execute(
    command: list[str], cwd: Path, environment: dict[str, str] | None = None
) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    receipt = {
        "command": command,
        "elapsedSeconds": time.monotonic() - started,
        "returncode": completed.returncode,
        "stdoutSha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderrSha256": hashlib.sha256(completed.stderr).hexdigest(),
        "stdout": completed.stdout.decode(errors="replace"),
        "stderr": completed.stderr.decode(errors="replace"),
    }
    if completed.returncode:
        raise RuntimeError(json.dumps(receipt, sort_keys=True))
    return receipt


def evaluate(
    predicates: list[dict[str, Any]], measurements: dict[str, bool | int | float]
) -> list[dict[str, Any]]:
    operations = {
        "eq": lambda value, threshold: value == threshold,
        "gt": lambda value, threshold: value > threshold,
        "lte": lambda value, threshold: value <= threshold,
    }
    return [
        {
            **predicate,
            "observed": measurements[predicate["measurement"]],
            "passed": bool(
                operations[predicate["operator"]](
                    measurements[predicate["measurement"]],
                    predicate["threshold"],
                )
            ),
        }
        for predicate in predicates
    ]


def require_inputs(experiment: dict[str, Any]) -> None:
    parent.require_inputs(experiment)
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("final-norm-backward-decision", FINAL_NORM_DECISION),
        ("final-norm-backward-reflection", FINAL_NORM_REFLECTION),
        ("promoted-final-norm-hidden-residual", FINAL_NORM_RESIDUAL),
        ("parent-ff2-decision", PARENT_DECISION),
        ("parent-ff2-reflection", PARENT_REFLECTION),
        ("promoted-parent-ff2-hidden-residual", PARENT_RESIDUAL),
        ("rmsnorm-output-order-decision", RMS_ORDER_DECISION),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    decision = json.loads(PARENT_DECISION.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    final_norm = json.loads(FINAL_NORM_DECISION.read_text())
    final_norm_reflection = json.loads(FINAL_NORM_REFLECTION.read_text())
    rms_order = json.loads(RMS_ORDER_DECISION.read_text())
    if not (
        decision["promotionPass"] is False
        and decision["measurements"]["topFf2MismatchCount"] == 184
        and decision["measurements"]["maximumTopFf2AbsoluteError"]
        == 9.5367431640625e-07
        and decision["measurements"]["openBackwardDeterministic"] is True
        and decision["measurements"]["finalNormGainMismatchCount"] == 0
        and decision["measurements"]["finalNormBiasMismatchCount"] == 0
        and decision["measurements"]["topFeedforwardBiasMismatchCount"] == 0
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "refuted"
        and reflection["decision"]["verdict"] == "retry"
        and final_norm["promotionPass"] is True
        and final_norm["measurements"]["openBackwardDeterministic"] is True
        and final_norm_reflection["validity"]["valid"] is True
        and final_norm_reflection["hypothesis"]["verdict"] == "supported"
        and rms_order["status"] == "PASS"
        and rms_order["decision"]["promotion_authorized"] is True
        and rms_order["gate"]["matching_contracts"]
        == ["libnc_output_order_backward"]
    ):
        raise ValueError("BF16 affine-upstream retry antecedents are not satisfied")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((Path(__file__),)),
        MATERIALIZER.resolve(),
        CMAKE.resolve(),
        NORM_REDUCER.resolve(),
        FF2_REDUCER.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        parent.REDUCER.resolve(),
        parent.OPEN_SOURCE.resolve(),
    ]
    members = sorted(set(members), key=lambda item: item.relative_to(ROOT).as_posix())
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
    compressed = lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME)
    tar_path.unlink()
    if len(compressed) > SOURCE_CEILING:
        raise ValueError("BF16 affine-upstream FF2 source closure exceeds ceiling")
    path.write_bytes(compressed)


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
        raise ValueError("job and tool experiment bindings differ")
    candidate_revision = json.loads(
        os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
    )
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("BF16 affine-upstream FF2 result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("candidate work root was not freshly materialized")

    used_fixture = parent.verify_used_fixture(
        ("parameters_initial.coefs", "state_initial.params")
    )
    source = WORK / "source"
    build = WORK / "build"
    shared_parameters = WORK / "parameters"
    fixtures = WORK / "fixtures"
    open_a = WORK / "open-a"
    open_b = WORK / "open-b"
    fixtures.mkdir()
    open_a.mkdir()
    open_b.mkdir()
    source.mkdir()
    executions: dict[str, Any] = {}
    executions["extractSource"] = execute(
        [
            "tar", "--extract", "--xz", "--no-same-owner",
            "--no-same-permissions", "--file", str(parent.OPEN_SOURCE),
            "--directory", str(source),
        ],
        ROOT,
    )
    executions["materializeForward"] = execute(
        [
            "python3", str(MATERIALIZER), str(parent.PARENT_FORWARD),
            str(source / "profile_final_norm_forward.cpp"),
        ],
        ROOT,
    )
    shutil.copyfile(CMAKE, source / "CMakeLists.txt")
    shutil.copyfile(parent.REDUCER, source / "final_hidden_residual.cpp")
    shutil.copyfile(NORM_REDUCER, source / "final_norm_backward.cpp")
    shutil.copyfile(FF2_REDUCER, source / "top_ff2_gradient.cpp")
    executions["configure"] = execute(
        ["cmake", "-S", str(source), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release"],
        ROOT,
    )
    executions["build"] = execute(
        ["cmake", "--build", str(build), "--parallel", "4"], ROOT
    )
    forward_binaries = [
        path for path in build.rglob("nncp_open_profile_forward") if path.is_file()
    ]
    hidden_binaries = [
        path for path in build.rglob("nncp_open_final_hidden_residual")
        if path.is_file()
    ]
    norm_binaries = [
        path for path in build.rglob("nncp_open_final_norm_backward")
        if path.is_file()
    ]
    ff2_binaries = [
        path for path in build.rglob("nncp_open_top_ff2_gradient")
        if path.is_file()
    ]
    if not (
        len(forward_binaries)
        == len(hidden_binaries)
        == len(norm_binaries)
        == len(ff2_binaries)
        == 1
    ):
        raise ValueError("open backward executable population differs")
    forward_binary = forward_binaries[0]
    hidden_binary = hidden_binaries[0]
    norm_binary = norm_binaries[0]
    ff2_binary = ff2_binaries[0]
    forbidden = []
    for label, binary in (
        ("forward", forward_binary),
        ("hidden", hidden_binary),
        ("norm", norm_binary),
        ("ff2", ff2_binary),
    ):
        receipt = execute(["ldd", str(binary)], ROOT)
        executions[f"ldd-{label}"] = receipt
        forbidden.extend(
            line
            for line in receipt["stdout"].splitlines()
            if any(
                token in line.lower()
                for token in ("libnc", "ggml", "cuda", "openmp", "gomp", "blas")
            )
        )

    parameters = parent.Container(parent.Q3_FIXTURE / "parameters_initial.coefs")
    state = parent.Container(parent.Q3_FIXTURE / "state_initial.params")
    try:
        parameter_rows = parent.materialize_parameters(parameters, shared_parameters)
        for stream in range(parent.STREAMS):
            parent.materialize_stream_fixture(
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

        def run_population(label: str, root: Path) -> dict[str, Any]:
            receipts: dict[str, Any] = {}

            def run_stream(stream: int) -> tuple[int, dict[str, Any]]:
                destination = root / f"stream_{stream:02d}"
                destination.mkdir()
                receipt = execute(
                    [
                        str(forward_binary),
                        str(fixtures / f"stream_{stream:02d}"),
                        str(destination),
                    ],
                    WORK,
                    environment,
                )
                return stream, receipt

            with ThreadPoolExecutor(max_workers=2) as executor:
                for stream, receipt in executor.map(
                    run_stream, range(parent.STREAMS)
                ):
                    receipts[f"stream-{stream:02d}"] = receipt
            checkpoints = 0
            mismatches = 0
            maximum = 0.0
            for stream in range(parent.STREAMS):
                current = parent.compare_layer_inputs(
                    state, stream, root / f"stream_{stream:02d}"
                )
                checkpoints += current[0]
                mismatches += current[1]
                maximum = max(maximum, current[2])
            paths = {
                "biasGradient": WORK / f"{label}-out-bias-gradient.bf16",
                "matrixGradient": WORK / f"{label}-embed-out-gradient.bf16",
                "hiddenResidual": WORK / f"{label}-final-hidden-residual.bf16",
                "parentNormBias": WORK / f"{label}-parent-ln-b-gradient.bf16",
                "shiftedNormBias": WORK / f"{label}-shifted-ln-b-gradient.bf16",
                "normGain": WORK / f"{label}-ln-g-gradient.bf16",
                "normBias": WORK / f"{label}-ln-b-gradient.bf16",
                "normInputResidual": WORK / f"{label}-norm-input-residual.bf16",
                "topFeedforwardBias": WORK / f"{label}-ff-bias2-19-gradient.bf16",
                "controlFeedforwardBias": WORK / f"{label}-control-ff-bias2-19.bf16",
                "topFf2Gradient": WORK / f"{label}-ff2-19-gradient.bf16",
                "controlTopFf2Gradient": WORK / f"{label}-control-ff2-19-gradient.bf16",
            }
            receipts["hiddenReducer"] = execute(
                [
                    str(hidden_binary),
                    str(parent.Q3_FIXTURE / "state_initial.params"),
                    str(parent.Q3_FIXTURE / "parameters_initial.coefs"),
                    str(root),
                    str(paths["biasGradient"]),
                    str(paths["matrixGradient"]),
                    str(paths["hiddenResidual"]),
                    str(paths["parentNormBias"]),
                    str(paths["shiftedNormBias"]),
                ],
                WORK,
                environment,
            )
            receipts["normReducer"] = execute(
                [
                    str(norm_binary),
                    str(parent.Q3_FIXTURE / "parameters_initial.coefs"),
                    str(root),
                    str(paths["hiddenResidual"]),
                    str(paths["normGain"]),
                    str(paths["normBias"]),
                    str(paths["normInputResidual"]),
                    str(paths["topFeedforwardBias"]),
                    str(paths["controlFeedforwardBias"]),
                ],
                WORK,
                environment,
            )
            receipts["ff2Reducer"] = execute(
                [
                    str(ff2_binary),
                    str(root),
                    str(paths["normInputResidual"]),
                    str(paths["topFf2Gradient"]),
                    str(paths["controlTopFf2Gradient"]),
                ],
                WORK,
                environment,
            )
            return {
                "receipts": receipts,
                "checkpoints": checkpoints,
                "mismatches": mismatches,
                "maximum": maximum,
                "aggregate": parent.aggregate(root),
                **paths,
            }

        replay_a = run_population("a", open_a)
        replay_b = run_population("b", open_b)
    finally:
        state.close()
        parameters.close()

    executions["openA"] = replay_a["receipts"]
    executions["openB"] = replay_b["receipts"]
    artifacts = {
        "open-final-hidden-residual": RESULT / "open-final-hidden-residual.bf16",
        "open-final-norm-gain-gradient": RESULT / "open-final-norm-gain-gradient.bf16",
        "open-final-norm-bias-gradient": RESULT / "open-final-norm-bias-gradient.bf16",
        "open-final-norm-input-residual": RESULT / "open-final-norm-input-residual.bf16",
        "open-top-feedforward-bias-gradient": RESULT / "open-ff-bias2-19-gradient.bf16",
        "open-top-ff2-gradient": RESULT / "open-ff2-19-gradient.bf16",
    }
    source_keys = {
        "open-final-hidden-residual": "hiddenResidual",
        "open-final-norm-gain-gradient": "normGain",
        "open-final-norm-bias-gradient": "normBias",
        "open-final-norm-input-residual": "normInputResidual",
        "open-top-feedforward-bias-gradient": "topFeedforwardBias",
        "open-top-ff2-gradient": "topFf2Gradient",
    }
    for identifier, destination in artifacts.items():
        shutil.copyfile(replay_a[source_keys[identifier]], destination)

    used_fixture.update(
        parent.verify_used_fixture(
            (
                "gradients/0245_out_bias.bin",
                "gradients/0245_out_bias.meta",
                "gradients/0000_embed_out.bin",
                "gradients/0000_embed_out.meta",
                "gradients/0243_ln_g_40.bin",
                "gradients/0243_ln_g_40.meta",
                "gradients/0244_ln_b_40.bin",
                "gradients/0244_ln_b_40.meta",
                "gradients/0006_ff_bias2_19.bin",
                "gradients/0006_ff_bias2_19.meta",
                "gradients/0001_ff2_19.bin",
                "gradients/0001_ff2_19.meta",
            )
        )
    )
    comparisons = {}
    for key, left, right in (
        ("outputBias", replay_a["biasGradient"], parent.Q3_FIXTURE / "gradients/0245_out_bias.bin"),
        ("outputMatrix", replay_a["matrixGradient"], parent.Q3_FIXTURE / "gradients/0000_embed_out.bin"),
        ("parentHidden", replay_a["hiddenResidual"], PARENT_RESIDUAL),
        ("normGain", replay_a["normGain"], parent.Q3_FIXTURE / "gradients/0243_ln_g_40.bin"),
        ("normBias", replay_a["normBias"], parent.Q3_FIXTURE / "gradients/0244_ln_b_40.bin"),
        ("topFeedforwardBias", replay_a["topFeedforwardBias"], parent.Q3_FIXTURE / "gradients/0006_ff_bias2_19.bin"),
        ("topFf2", replay_a["topFf2Gradient"], parent.Q3_FIXTURE / "gradients/0001_ff2_19.bin"),
    ):
        comparisons[key] = parent.compare_bf16(left, right)
    deterministic_keys = (
        "biasGradient",
        "matrixGradient",
        "hiddenResidual",
        "parentNormBias",
        "shiftedNormBias",
        "normGain",
        "normBias",
        "normInputResidual",
        "topFeedforwardBias",
        "controlFeedforwardBias",
        "topFf2Gradient",
        "controlTopFf2Gradient",
    )
    deterministic = (
        replay_a["aggregate"] == replay_b["aggregate"]
        and all(
            replay_a[key].read_bytes() == replay_b[key].read_bytes()
            for key in deterministic_keys
        )
        and replay_a["checkpoints"] == replay_b["checkpoints"]
        and replay_a["mismatches"] == replay_b["mismatches"]
        and replay_a["maximum"] == replay_b["maximum"]
    )
    shifted_differs = (
        replay_a["shiftedNormBias"].read_bytes()
        != replay_a["parentNormBias"].read_bytes()
    )
    control_differs = (
        replay_a["controlFeedforwardBias"].read_bytes()
        != replay_a["topFeedforwardBias"].read_bytes()
    )
    ff2_control_differs = (
        replay_a["controlTopFf2Gradient"].read_bytes()
        != replay_a["topFf2Gradient"].read_bytes()
    )
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "executions": executions,
                "usedFixtureSha256": used_fixture,
                "openAggregateA": replay_a["aggregate"],
                "openAggregateB": replay_b["aggregate"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)

    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "streamCount": parent.STREAMS,
        "sampleCount": parent.STREAMS * parent.STATES,
        "layerInputCheckpointCount": replay_a["checkpoints"],
        "layerInputMismatchCount": replay_a["mismatches"] + replay_b["mismatches"],
        "maximumLayerInputAbsoluteError": max(replay_a["maximum"], replay_b["maximum"]),
        "outputBiasMismatchCount": comparisons["outputBias"][0],
        "maximumOutputBiasAbsoluteError": comparisons["outputBias"][1],
        "outputMatrixMismatchCount": comparisons["outputMatrix"][0],
        "maximumOutputMatrixAbsoluteError": comparisons["outputMatrix"][1],
        "promotedHiddenResidualMismatchCount": comparisons["parentHidden"][0],
        "maximumPromotedHiddenResidualAbsoluteError": comparisons["parentHidden"][1],
        "finalNormGainElementCount": artifacts["open-final-norm-gain-gradient"].stat().st_size // 2,
        "finalNormGainMismatchCount": comparisons["normGain"][0],
        "maximumFinalNormGainAbsoluteError": comparisons["normGain"][1],
        "finalNormBiasElementCount": artifacts["open-final-norm-bias-gradient"].stat().st_size // 2,
        "finalNormBiasMismatchCount": comparisons["normBias"][0],
        "maximumFinalNormBiasAbsoluteError": comparisons["normBias"][1],
        "finalNormInputResidualElementCount": artifacts["open-final-norm-input-residual"].stat().st_size // 2,
        "topFeedforwardBiasElementCount": artifacts["open-top-feedforward-bias-gradient"].stat().st_size // 2,
        "topFeedforwardBiasMismatchCount": comparisons["topFeedforwardBias"][0],
        "maximumTopFeedforwardBiasAbsoluteError": comparisons["topFeedforwardBias"][1],
        "topFf2ElementCount": artifacts["open-top-ff2-gradient"].stat().st_size // 2,
        "topFf2MismatchCount": comparisons["topFf2"][0],
        "maximumTopFf2AbsoluteError": comparisons["topFf2"][1],
        "negatedTopFf2ControlDiffers": ff2_control_differs,
        "openBackwardDeterministic": deterministic,
        "shiftedTargetControlDiffers": shifted_differs,
        "negatedResidualControlDiffers": control_differs,
        "forbiddenDynamicDependencyCount": len(forbidden),
        "incrementalSourceBytes": incremental_source.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    decision = (
        "authorize-successor" if promotion_pass else "retire" if kill_pass else "retry"
    )
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
        "decision": decision,
        "artifacts": [
            reference(execution_path, "execution"),
            *(reference(path, identifier) for identifier, path in artifacts.items()),
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



