#!/usr/bin/env python3
"""Attribute the production top-FF1 matrix-gradient accumulation schedule."""

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
import sys
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_ff1_bias_state_reduce_64_q0 as oracle
import nncp_open_profile_top_ff1_bias_gradient_64_q0_v1 as profile
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_ff1_weight_slice_schedule_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
TOP_PARENT_ID = "nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1"
TOP_PARENT_RESULT = ROOT / "results" / TOP_PARENT_ID
TOP_PARENT_DECISION = TOP_PARENT_RESULT / "decision.json"
TOP_PARENT_EXECUTION = TOP_PARENT_RESULT / "execution.json"
TOP_PARENT_GUARD = TOP_PARENT_RESULT / "guard.json"
TOP_PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T104952Z_2204470800.json"
)
EXACT_RESIDUAL = TOP_PARENT_RESULT / "open-ff1-output-residual.bf16"
PARENT_ID = "nncp_open_ff1_bias_state_reduce_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T112548Z_7841e2cc5b.json"
)
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_DECISION = FIXTURE_ROOT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture-manifest.json"
COMPARATOR = FIXTURE_ROOT / "fixture/gradients/0002_ff1_19.bin"
COMPARATOR_META = FIXTURE_ROOT / "fixture/gradients/0002_ff1_19.meta"
LIBNC = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/libnc.so")
LIBNC_INCLUDE = LIBNC.parent
EXPECTED_LIBNC_SHA256 = (
    "1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e"
)
PARENT_FORWARD_MATERIALIZER = ROOT / (
    "programs/nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2/"
    "materialize_forward.py"
)
FORWARD_MATERIALIZER = PROGRAM / "materialize_ff1_input.py"
CMAKE = PROGRAM / "CMakeLists.txt"
EVALUATOR_SOURCE = PROGRAM / "ff1_weight_slice_schedule.c"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / "tools/nncp_libnc_ff1_weight_slice_schedule_64_q0_materializer.py"
STREAMS = 32
STATES = 64
SAMPLES = STREAMS * STATES
INPUTS = 1024
FULL_OUTPUTS = 6144
SLICE_OUTPUTS = 128
SLICE_ELEMENTS = SLICE_OUTPUTS * INPUTS
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
        ("top-parent-decision", TOP_PARENT_DECISION),
        ("top-parent-execution", TOP_PARENT_EXECUTION),
        ("top-parent-guard", TOP_PARENT_GUARD),
        ("top-parent-reflection", TOP_PARENT_REFLECTION),
        ("source-exact-ff1-output-residual", EXACT_RESIDUAL),
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("fixture-decision", FIXTURE_DECISION),
        ("fixture-manifest", FIXTURE_MANIFEST),
        ("retained-ff1-19-gradient", COMPARATOR),
        ("retained-ff1-19-gradient-meta", COMPARATOR_META),
        ("parent-forward-materializer", PARENT_FORWARD_MATERIALIZER),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    top = json.loads(TOP_PARENT_DECISION.read_text())
    top_guard = json.loads(TOP_PARENT_GUARD.read_text())
    top_reflection = json.loads(TOP_PARENT_REFLECTION.read_text())
    parent = json.loads(PARENT_DECISION.read_text())
    parent_guard = json.loads(PARENT_GUARD.read_text())
    parent_reflection = json.loads(PARENT_REFLECTION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    if not (
        top["measurements"]["sourceFf2InputResidualMismatchCount"] == 0
        and top["measurements"]["sourceGateAdjointMismatchCount"] == 0
        and top["measurements"]["sourceValueAdjointMismatchCount"] == 0
        and top["measurements"]["openBackwardDeterministic"] is True
        and top_guard["returncode"] == 0
        and top_guard["rss_guard_exceeded"] is False
        and top_guard["temporary_disk_guard_exceeded"] is False
        and top_reflection["validity"]["valid"] is True
        and parent["promotionPass"] is True
        and parent["measurements"]["treatmentMismatchCount"] == 0
        and parent["measurements"]["forbiddenDynamicDependencyCount"] == 0
        and parent_guard["returncode"] == 0
        and parent_guard["rss_guard_exceeded"] is False
        and parent_guard["temporary_disk_guard_exceeded"] is False
        and parent_reflection["validity"]["valid"] is True
        and parent_reflection["hypothesis"]["verdict"] == "supported"
        and fixture["measurements"]["fixtureComplete"] is True
    ):
        raise ValueError("top-FF1 weight-slice antecedents are not satisfied")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, FREEZER)),
        PARENT_FORWARD_MATERIALIZER.resolve(),
        FORWARD_MATERIALIZER.resolve(),
        CMAKE.resolve(),
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
        raise ValueError("FF1 weight-slice source closure exceeds ceiling")


def aggregate_ff1_input(root: Path, output: Path) -> None:
    if sys.byteorder != "little":
        raise ValueError("FF1 input aggregation requires little-endian host")
    streams: list[bytes] = []
    expected = STATES * INPUTS * 4
    for stream in range(STREAMS):
        path = root / f"stream_{stream:02d}/layer_19_ff1_input.f32"
        payload = path.read_bytes()
        if len(payload) != expected:
            raise ValueError(f"layer-19 FF1 input geometry differs: {path}")
        streams.append(payload)
    combined = bytearray(SAMPLES * INPUTS * 2)
    cursor = 0
    row_bytes = INPUTS * 4
    for state in range(STATES):
        for stream in range(STREAMS):
            row = memoryview(streams[stream])[
                state * row_bytes : (state + 1) * row_bytes
            ]
            for offset in range(0, row_bytes, 4):
                if row[offset] != 0 or row[offset + 1] != 0:
                    raise ValueError("layer-19 FF1 input is not BF16-exact")
                combined[cursor : cursor + 2] = row[offset + 2 : offset + 4]
                cursor += 2
    if cursor != len(combined):
        raise ValueError("FF1 input aggregation did not cover the population")
    output.write_bytes(combined)


def retained_slice(path: Path) -> bytes:
    payload = path.read_bytes()
    if len(payload) != FULL_OUTPUTS * INPUTS * 2:
        raise ValueError("retained ff1_19 gradient geometry differs")
    result = bytearray(SLICE_ELEMENTS * 2)
    cursor = 0
    for input_feature in range(INPUTS):
        start = input_feature * FULL_OUTPUTS * 2
        block = payload[start : start + SLICE_OUTPUTS * 2]
        result[cursor : cursor + len(block)] = block
        cursor += len(block)
    return bytes(result)


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
        raise ValueError("job and FF1 weight-slice bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("FF1 weight-slice result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("FF1 weight-slice work root was not freshly materialized")
    if sha256(LIBNC) != EXPECTED_LIBNC_SHA256:
        raise ValueError("LibNC digest differs from attributed production library")

    source = WORK / "source"
    build = WORK / "build"
    fixtures = WORK / "fixtures"
    parameters_root = WORK / "parameters"
    open_a = WORK / "open-a"
    open_b = WORK / "open-b"
    for path in (source, fixtures, open_a, open_b):
        path.mkdir()
    executions: dict[str, Any] = {}
    executions["extractSource"] = profile.base.execute(
        [
            "tar", "--extract", "--xz", "--no-same-owner",
            "--no-same-permissions", "--file",
            str(profile.base.parent.OPEN_SOURCE), "--directory", str(source),
        ],
        ROOT,
    )
    parent_forward = source / "profile_top_ff1_parent.cpp"
    executions["materializeParentForward"] = profile.base.execute(
        [
            "python3", str(PARENT_FORWARD_MATERIALIZER),
            str(profile.base.parent.PARENT_FORWARD), str(parent_forward),
        ],
        ROOT,
    )
    executions["materializeFf1Input"] = profile.base.execute(
        [
            "python3", str(FORWARD_MATERIALIZER), str(parent_forward),
            str(source / "profile_ff1_input.cpp"),
        ],
        ROOT,
    )
    shutil.copyfile(CMAKE, source / "CMakeLists.txt")
    executions["configure"] = profile.base.execute(
        ["cmake", "-S", str(source), "-B", str(build),
         "-DCMAKE_BUILD_TYPE=Release"],
        ROOT,
    )
    executions["buildForward"] = profile.base.execute(
        ["cmake", "--build", str(build), "--parallel", "4"], ROOT
    )
    forward_binaries = [
        path for path in build.rglob("nncp_open_profile_ff1_input")
        if path.is_file()
    ]
    if len(forward_binaries) != 1:
        raise ValueError("FF1 input forward executable population differs")
    forward_binary = forward_binaries[0]
    forward_ldd = profile.base.execute(["ldd", str(forward_binary)], ROOT)
    executions["lddForward"] = forward_ldd
    forbidden = [
        line for line in forward_ldd["stdout"].splitlines()
        if any(
            token in line.lower()
            for token in ("libnc", "ggml", "cuda", "openmp", "gomp", "blas")
        )
    ]

    evaluator = build / "ff1_weight_slice_schedule"
    executions["buildEvaluator"] = profile.base.execute(
        [
            os.environ.get("CC", "cc"), "-std=gnu11", "-O2", "-Wall",
            "-Wextra", "-Werror", "-Wno-unused-parameter",
            f"-I{LIBNC_INCLUDE}", str(EVALUATOR_SOURCE), str(LIBNC),
            f"-Wl,-rpath,{LIBNC_INCLUDE}", "-lm", "-lpthread", "-o",
            str(evaluator),
        ],
        ROOT,
    )
    evaluator_ldd = profile.base.execute(["ldd", str(evaluator)], ROOT)
    executions["lddEvaluator"] = evaluator_ldd
    if str(LIBNC) not in evaluator_ldd["stdout"]:
        raise ValueError("evaluator did not resolve the attributed LibNC")

    used_fixture = profile.base.parent.verify_used_fixture(
        ("parameters_initial.coefs", "state_initial.params")
    )
    parameters = profile.base.parent.Container(
        profile.base.parent.Q3_FIXTURE / "parameters_initial.coefs"
    )
    state = profile.base.parent.Container(
        profile.base.parent.Q3_FIXTURE / "state_initial.params"
    )
    try:
        parameter_rows = profile.base.parent.materialize_parameters(
            parameters, parameters_root
        )
        for stream in range(STREAMS):
            profile.base.parent.materialize_stream_fixture(
                state, parameters_root, parameter_rows, stream,
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
                return stream, profile.base.execute(
                    [
                        str(forward_binary),
                        str(fixtures / f"stream_{stream:02d}"),
                        str(destination),
                    ],
                    WORK,
                    environment,
                )

            with ThreadPoolExecutor(max_workers=2) as executor:
                for stream, receipt in executor.map(run_stream, range(STREAMS)):
                    receipts[f"stream-{stream:02d}"] = receipt
            checkpoints = mismatches = 0
            maximum = 0.0
            for stream in range(STREAMS):
                comparison = profile.base.parent.compare_layer_inputs(
                    state, stream, root / f"stream_{stream:02d}"
                )
                checkpoints += comparison[0]
                mismatches += comparison[1]
                maximum = max(maximum, comparison[2])
            aggregate_input = WORK / f"{label}-ff1-input.bf16"
            aggregate_ff1_input(root, aggregate_input)
            outputs = {
                name: WORK / f"{label}-{name}.bf16"
                for name in ("treatment", "flat", "reverse", "negated")
            }
            receipts["weightSliceEvaluator"] = profile.base.execute(
                [
                    str(evaluator), str(aggregate_input), str(EXACT_RESIDUAL),
                    *(str(outputs[name]) for name in
                      ("treatment", "flat", "reverse", "negated")),
                ],
                WORK,
                environment,
            )
            if any(path.stat().st_size != SLICE_ELEMENTS * 2
                   for path in outputs.values()):
                raise ValueError("FF1 weight-slice output geometry differs")
            return {
                "receipts": receipts,
                "checkpoints": checkpoints,
                "mismatches": mismatches,
                "maximum": maximum,
                "aggregate": profile.base.parent.aggregate(root),
                "input": aggregate_input,
                **outputs,
            }

        replay_a = run_population("a", open_a)
        replay_b = run_population("b", open_b)
    finally:
        state.close()
        parameters.close()

    executions["populationA"] = replay_a["receipts"]
    executions["populationB"] = replay_b["receipts"]
    deterministic_keys = ("input", "treatment", "flat", "reverse", "negated")
    evaluation_replay_identical = all(
        replay_a[key].read_bytes() == replay_b[key].read_bytes()
        for key in deterministic_keys
    )
    input_replay_identical = (
        replay_a["input"].read_bytes() == replay_b["input"].read_bytes()
        and replay_a["aggregate"] == replay_b["aggregate"]
        and replay_a["checkpoints"] == replay_b["checkpoints"]
        and replay_a["mismatches"] == replay_b["mismatches"]
        and replay_a["maximum"] == replay_b["maximum"]
    )

    comparator_slice = WORK / "retained-slice.bf16"
    comparator_slice.write_bytes(retained_slice(COMPARATOR))
    comparisons = {
        name: oracle.compare_bf16(replay_a[name], comparator_slice)
        for name in ("treatment", "flat", "reverse", "negated")
    }
    artifacts = {
        "open-ff1-input": RESULT / "open-ff1-input.bf16",
        "libnc-treatment-slice": RESULT / "libnc-treatment-slice.bf16",
        "libnc-flat-control-slice": RESULT / "libnc-flat-control-slice.bf16",
        "libnc-reverse-control-slice": RESULT / "libnc-reverse-control-slice.bf16",
        "libnc-negated-control-slice": RESULT / "libnc-negated-control-slice.bf16",
    }
    artifact_sources = {
        "open-ff1-input": replay_a["input"],
        "libnc-treatment-slice": replay_a["treatment"],
        "libnc-flat-control-slice": replay_a["flat"],
        "libnc-reverse-control-slice": replay_a["reverse"],
        "libnc-negated-control-slice": replay_a["negated"],
    }
    for identifier, destination in artifacts.items():
        shutil.copyfile(artifact_sources[identifier], destination)
    used_fixture.update(
        profile.base.parent.verify_used_fixture(
            ("gradients/0002_ff1_19.bin", "gradients/0002_ff1_19.meta")
        )
    )
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "arithmeticContract": {
                    "matrix": "FF1 output adjoint multiplied by transposed FF1 input",
                    "stateOrder": "0..63 chronological",
                    "stateShape": [SLICE_OUTPUTS, STREAMS, INPUTS],
                    "accumulation": "nc_matmul_add2(residual, input, existing, false, true, 1, 0)",
                },
                "attributedLibrary": {
                    "path": str(LIBNC),
                    "sha256": EXPECTED_LIBNC_SHA256,
                },
                "comparisons": comparisons,
                "executions": executions,
                "forbiddenForwardDependencies": forbidden,
                "inputSha256": sha256(artifacts["open-ff1-input"]),
                "outputSha256": {
                    identifier: sha256(path)
                    for identifier, path in artifacts.items()
                    if identifier != "open-ff1-input"
                },
                "openAggregateA": replay_a["aggregate"],
                "openAggregateB": replay_b["aggregate"],
                "usedFixtureSha256": used_fixture,
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
        "stateCount": STATES,
        "sampleCount": SAMPLES,
        "inputFeatureCount": INPUTS,
        "sliceOutputFeatureCount": SLICE_OUTPUTS,
        "inputElementCount": SAMPLES * INPUTS,
        "residualElementCount": SAMPLES * FULL_OUTPUTS,
        "sliceElementCount": SLICE_ELEMENTS,
        "stateMatmulCallCount": STATES,
        "layerInputCheckpointCount": replay_a["checkpoints"],
        "layerInputMismatchCount": replay_a["mismatches"] + replay_b["mismatches"],
        "maximumLayerInputAbsoluteError": max(
            replay_a["maximum"], replay_b["maximum"]
        ),
        "treatmentMismatchCount": comparisons["treatment"]["mismatchCount"],
        "maximumTreatmentAbsoluteError": comparisons["treatment"]["maximumAbsoluteError"],
        "flatMismatchCount": comparisons["flat"]["mismatchCount"],
        "reverseMismatchCount": comparisons["reverse"]["mismatchCount"],
        "negatedControlDiffers": comparisons["negated"]["mismatchCount"] > 0,
        "ff1InputReplayIdentical": input_replay_identical,
        "evaluationReplayIdentical": evaluation_replay_identical,
        "sourceLibraryDigestBound": sha256(LIBNC) == EXPECTED_LIBNC_SHA256,
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
            "authorize-successor" if promotion_pass
            else "retire" if kill_pass else "retry"
        ),
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

