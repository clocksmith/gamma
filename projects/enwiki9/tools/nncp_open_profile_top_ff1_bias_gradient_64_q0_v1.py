#!/usr/bin/env python3
"""Run the open FF2-transpose and GEGLU backward projection gate."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import json
import lzma
import os
from pathlib import Path
import shutil
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_open_profile_top_ff2_gradient_64_q0_retry_v1 as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
TAIL_ID = "nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2"
TAIL_RESULT = ROOT / "results" / TAIL_ID
TAIL_DECISION = TAIL_RESULT / "decision.json"
TAIL_EXECUTION = TAIL_RESULT / "execution.json"
TAIL_GUARD = TAIL_RESULT / "guard.json"
TAIL_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T082228Z_f0bff9b6df.json"
)
PROMOTED_RESIDUAL = TAIL_RESULT / "open-final-norm-input-residual.bf16"
ACTIVATION_DECISION = ROOT / (
    "results/nncp_v33_libnc_activation_backward_parity_v1/decision.json"
)
MATERIALIZER = PROGRAM / "materialize_forward.py"
CMAKE = PROGRAM / "CMakeLists.txt"
REDUCER = PROGRAM / "top_ff1_bias_gradient.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / (
    "tools/nncp_open_profile_top_ff1_bias_gradient_64_q0_v1_materializer.py"
)
SOURCE_CEILING = 2_000_000


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("tail-decision", TAIL_DECISION),
        ("tail-execution", TAIL_EXECUTION),
        ("tail-guard", TAIL_GUARD),
        ("tail-reflection", TAIL_REFLECTION),
        ("promoted-final-rms-input-residual", PROMOTED_RESIDUAL),
        ("activation-backward-decision", ACTIVATION_DECISION),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != base.reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    tail = json.loads(TAIL_DECISION.read_text())
    reflection = json.loads(TAIL_REFLECTION.read_text())
    guard = json.loads(TAIL_GUARD.read_text())
    activation = json.loads(ACTIVATION_DECISION.read_text())
    if not (
        tail["promotionPass"] is True
        and tail["measurements"]["sourceFinalNormResidualMismatchCount"] == 0
        and tail["measurements"]["topFf2MismatchCount"] == 0
        and tail["measurements"]["openBackwardDeterministic"] is True
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "supported"
        and guard["returncode"] == 0
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and activation["status"] == "PASS"
        and activation["decision"]["promotion_authorized"] is True
        and activation["gate"]["matching_contract"]
        == "libnc_unfused_f32_tanh_formula"
    ):
        raise ValueError("top-FF1 bias antecedents are not satisfied")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, FREEZER)),
        MATERIALIZER.resolve(),
        CMAKE.resolve(),
        REDUCER.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        base.parent.OPEN_SOURCE.resolve(),
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
    compressed = lzma.compress(
        tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME
    )
    tar_path.unlink()
    if len(compressed) > SOURCE_CEILING:
        raise ValueError("top-FF1 bias source closure exceeds ceiling")
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
    if base.reference(experiment_path) != json.loads(
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
        raise ValueError("top-FF1 bias result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("candidate work root was not freshly materialized")

    used_fixture = base.parent.verify_used_fixture(
        ("parameters_initial.coefs", "state_initial.params")
    )
    source = WORK / "source"
    build = WORK / "build"
    parameters_root = WORK / "parameters"
    fixtures = WORK / "fixtures"
    open_a = WORK / "open-a"
    open_b = WORK / "open-b"
    for path in (source, fixtures, open_a, open_b):
        path.mkdir()
    executions: dict[str, Any] = {}
    executions["extractSource"] = base.execute(
        [
            "tar", "--extract", "--xz", "--no-same-owner",
            "--no-same-permissions", "--file", str(base.parent.OPEN_SOURCE),
            "--directory", str(source),
        ],
        ROOT,
    )
    executions["materializeForward"] = base.execute(
        [
            "python3", str(MATERIALIZER), str(base.parent.PARENT_FORWARD),
            str(source / "profile_top_ff1_forward.cpp"),
        ],
        ROOT,
    )
    shutil.copyfile(CMAKE, source / "CMakeLists.txt")
    shutil.copyfile(REDUCER, source / "top_ff1_bias_gradient.cpp")
    executions["configure"] = base.execute(
        ["cmake", "-S", str(source), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release"],
        ROOT,
    )
    executions["build"] = base.execute(
        ["cmake", "--build", str(build), "--parallel", "4"], ROOT
    )
    forward_binaries = [
        path for path in build.rglob("nncp_open_profile_forward") if path.is_file()
    ]
    reducer_binaries = [
        path for path in build.rglob("nncp_open_top_ff1_bias_gradient")
        if path.is_file()
    ]
    if len(forward_binaries) != 1 or len(reducer_binaries) != 1:
        raise ValueError("top-FF1 executable population differs")
    forward_binary = forward_binaries[0]
    reducer_binary = reducer_binaries[0]
    forbidden: list[str] = []
    for label, binary in (("forward", forward_binary), ("reducer", reducer_binary)):
        receipt = base.execute(["ldd", str(binary)], ROOT)
        executions[f"ldd-{label}"] = receipt
        forbidden.extend(
            line
            for line in receipt["stdout"].splitlines()
            if any(
                token in line.lower()
                for token in ("libnc", "ggml", "cuda", "openmp", "gomp", "blas")
            )
        )

    parameters = base.parent.Container(
        base.parent.Q3_FIXTURE / "parameters_initial.coefs"
    )
    state = base.parent.Container(base.parent.Q3_FIXTURE / "state_initial.params")
    try:
        parameter_rows = base.parent.materialize_parameters(
            parameters, parameters_root
        )
        for stream in range(base.parent.STREAMS):
            base.parent.materialize_stream_fixture(
                state,
                parameters_root,
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
                return stream, base.execute(
                    [
                        str(forward_binary),
                        str(fixtures / f"stream_{stream:02d}"),
                        str(destination),
                    ],
                    WORK,
                    environment,
                )

            with ThreadPoolExecutor(max_workers=2) as executor:
                for stream, receipt in executor.map(
                    run_stream, range(base.parent.STREAMS)
                ):
                    receipts[f"stream-{stream:02d}"] = receipt
            checkpoints = mismatches = 0
            maximum = 0.0
            for stream in range(base.parent.STREAMS):
                current = base.parent.compare_layer_inputs(
                    state, stream, root / f"stream_{stream:02d}"
                )
                checkpoints += current[0]
                mismatches += current[1]
                maximum = max(maximum, current[2])
            paths = {
                "ff2InputResidual": WORK / f"{label}-ff2-input-residual.bf16",
                "ff1OutputResidual": WORK / f"{label}-ff1-output-residual.bf16",
                "ff1BiasGradient": WORK / f"{label}-ff-bias1-19-gradient.bf16",
                "controlFf1BiasGradient": WORK / f"{label}-control-ff-bias1-19.bf16",
            }
            receipts["ff1BiasReducer"] = base.execute(
                [
                    str(reducer_binary),
                    str(base.parent.Q3_FIXTURE / "parameters_initial.coefs"),
                    str(root),
                    str(PROMOTED_RESIDUAL),
                    str(paths["ff2InputResidual"]),
                    str(paths["ff1OutputResidual"]),
                    str(paths["ff1BiasGradient"]),
                    str(paths["controlFf1BiasGradient"]),
                ],
                WORK,
                environment,
            )
            return {
                "receipts": receipts,
                "checkpoints": checkpoints,
                "mismatches": mismatches,
                "maximum": maximum,
                "aggregate": base.parent.aggregate(root),
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
        "open-top-ff2-input-residual": RESULT / "open-ff2-input-residual.bf16",
        "open-top-ff1-output-residual": RESULT / "open-ff1-output-residual.bf16",
        "open-top-ff1-bias-gradient": RESULT / "open-ff-bias1-19-gradient.bf16",
    }
    source_keys = {
        "open-top-ff2-input-residual": "ff2InputResidual",
        "open-top-ff1-output-residual": "ff1OutputResidual",
        "open-top-ff1-bias-gradient": "ff1BiasGradient",
    }
    for identifier, destination in artifacts.items():
        shutil.copyfile(replay_a[source_keys[identifier]], destination)
    used_fixture.update(
        base.parent.verify_used_fixture(
            ("gradients/0005_ff_bias1_19.bin", "gradients/0005_ff_bias1_19.meta")
        )
    )
    bias_comparison = base.parent.compare_bf16(
        replay_a["ff1BiasGradient"],
        base.parent.Q3_FIXTURE / "gradients/0005_ff_bias1_19.bin",
    )
    deterministic_keys = (
        "ff2InputResidual",
        "ff1OutputResidual",
        "ff1BiasGradient",
        "controlFf1BiasGradient",
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
    control_differs = (
        replay_a["controlFf1BiasGradient"].read_bytes()
        != replay_a["ff1BiasGradient"].read_bytes()
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
        "streamCount": base.parent.STREAMS,
        "sampleCount": base.parent.STREAMS * base.parent.STATES,
        "layerInputCheckpointCount": replay_a["checkpoints"],
        "layerInputMismatchCount": replay_a["mismatches"] + replay_b["mismatches"],
        "maximumLayerInputAbsoluteError": max(
            replay_a["maximum"], replay_b["maximum"]
        ),
        "ff2InputResidualElementCount": artifacts[
            "open-top-ff2-input-residual"
        ].stat().st_size
        // 2,
        "ff1OutputResidualElementCount": artifacts[
            "open-top-ff1-output-residual"
        ].stat().st_size
        // 2,
        "topFf1BiasElementCount": artifacts[
            "open-top-ff1-bias-gradient"
        ].stat().st_size
        // 2,
        "topFf1BiasMismatchCount": bias_comparison[0],
        "maximumTopFf1BiasAbsoluteError": bias_comparison[1],
        "openBackwardDeterministic": deterministic,
        "negatedTopFf1ControlDiffers": control_differs,
        "forbiddenDynamicDependencyCount": len(forbidden),
        "incrementalSourceBytes": incremental_source.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = base.evaluate(experiment["promotionPredicates"], measurements)
    kill = base.evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": base.reference(experiment_path),
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
            else "retire" if kill_pass else "retry"
        ),
        "artifacts": [
            base.reference(execution_path, "execution"),
            *(base.reference(path, identifier) for identifier, path in artifacts.items()),
            base.reference(incremental_source, "incremental-source-package"),
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
