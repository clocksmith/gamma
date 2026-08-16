#!/usr/bin/env python3
"""Open the layer-19 pre-FF RMSNorm backward and residual merge."""

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
import nncp_libnc_ff1_weight_slice_schedule_64_q0 as forward_parent
import nncp_libnc_top_ff2_input_adjoint_64_q0_v1 as bf16_comparator
import nncp_libnc_top_ff1_input_adjoint_64_q0_v1 as comparator
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_rmsnorm_backward_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T130603Z_423b21f22f.json"
)
SOURCE_HIDDEN = PARENT_RESULT / "source-pre-ff-hidden.bf16"
SOURCE_TOTAL_ADJOINT = PARENT_RESULT / "source-pre-ff-hidden-adjoint.bf16"
FF1_ID = "nncp_open_top_ff1_input_adjoint_block128_64_q0_v1"
FF1_RESULT = ROOT / "results" / FF1_ID
FF1_DECISION = FF1_RESULT / "decision.json"
FF1_EXECUTION = FF1_RESULT / "execution.json"
FF1_GUARD = FF1_RESULT / "guard.json"
FF1_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T123635Z_f1f6615808.json"
)
NORMALIZED_ADJOINT = FF1_RESULT / "source-exact-ff1-input-adjoint.bf16"
NORMALIZED_INPUT = ROOT / (
    "results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/"
    "open-ff1-input.bf16"
)
FINAL_ID = "nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2"
FINAL_RESULT = ROOT / "results" / FINAL_ID
FINAL_DECISION = FINAL_RESULT / "decision.json"
FINAL_EXECUTION = FINAL_RESULT / "execution.json"
FINAL_GUARD = FINAL_RESULT / "guard.json"
FINAL_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T082228Z_f0bff9b6df.json"
)
FINAL_BACKWARD = ROOT / (
    "programs/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/"
    "final_norm_backward.cpp"
)
DIRECT_ADJOINT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-hidden-residual.bf16"
)
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_DECISION = FIXTURE_ROOT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture-manifest.json"
PARAMETERS = FIXTURE_ROOT / "fixture/parameters_initial.coefs"
GAIN_COMPARATOR = FIXTURE_ROOT / "fixture/gradients/0003_ln_g_39.bin"
GAIN_META = FIXTURE_ROOT / "fixture/gradients/0003_ln_g_39.meta"
BIAS_COMPARATOR = FIXTURE_ROOT / "fixture/gradients/0004_ln_b_39.bin"
BIAS_META = FIXTURE_ROOT / "fixture/gradients/0004_ln_b_39.meta"
PARENT_FORWARD_MATERIALIZER = ROOT / (
    "programs/nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2/"
    "materialize_forward.py"
)
FF1_INPUT_MATERIALIZER = ROOT / (
    "programs/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/"
    "materialize_ff1_input.py"
)
FORWARD_MATERIALIZER = PROGRAM / "materialize_pre_ff_forward.py"
BACKWARD_MATERIALIZER = PROGRAM / "materialize_pre_ff_backward.py"
CMAKE = PROGRAM / "CMakeLists.txt"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / (
    "tools/nncp_open_top_pre_ff_rmsnorm_backward_64_q0_materializer.py"
)
STREAMS = 32
STATES = 64
WIDTH = 1024
SAMPLES = STREAMS * STATES
SOURCE_CEILING = 2_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return oracle.reference(path, identifier)


def aggregate_bf16_exact(
    root: Path, filename: str, output: Path
) -> None:
    if sys.byteorder != "little":
        raise ValueError("pre-FF aggregation requires a little-endian host")
    streams: list[bytes] = []
    expected = STATES * WIDTH * 4
    for stream in range(STREAMS):
        path = root / f"stream_{stream:02d}" / filename
        payload = path.read_bytes()
        if len(payload) != expected:
            raise ValueError(f"pre-FF forward geometry differs: {path}")
        streams.append(payload)
    result = bytearray(SAMPLES * WIDTH * 2)
    cursor = 0
    row_bytes = WIDTH * 4
    for state in range(STATES):
        for stream in range(STREAMS):
            row = memoryview(streams[stream])[
                state * row_bytes : (state + 1) * row_bytes
            ]
            for offset in range(0, row_bytes, 4):
                if row[offset] != 0 or row[offset + 1] != 0:
                    raise ValueError(f"{filename} is not BF16-exact")
                result[cursor : cursor + 2] = row[offset + 2 : offset + 4]
                cursor += 2
    if cursor != len(result):
        raise ValueError("pre-FF aggregation did not cover the population")
    output.write_bytes(result)


def require_gradient_meta(path: Path, name: str, index: int) -> None:
    expected = {
        "index": str(index),
        "name": name,
        "item_type": "1",
        "item_size": "2",
        "dims": str(WIDTH),
        "byte_order": "little",
        "column_index": "none",
    }
    if comparator.source_capture.parse_meta(path) != expected:
        raise ValueError(f"retained {name} gradient metadata differs")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("source-pre-ff-hidden", SOURCE_HIDDEN),
        ("source-pre-ff-hidden-adjoint", SOURCE_TOTAL_ADJOINT),
        ("ff1-decision", FF1_DECISION),
        ("ff1-execution", FF1_EXECUTION),
        ("ff1-guard", FF1_GUARD),
        ("ff1-reflection", FF1_REFLECTION),
        ("normalized-ff1-input", NORMALIZED_INPUT),
        ("normalized-ff1-input-adjoint", NORMALIZED_ADJOINT),
        ("final-decision", FINAL_DECISION),
        ("final-execution", FINAL_EXECUTION),
        ("final-guard", FINAL_GUARD),
        ("final-reflection", FINAL_REFLECTION),
        ("exact-final-backward-source", FINAL_BACKWARD),
        ("direct-residual-adjoint", DIRECT_ADJOINT),
        ("fixture-decision", FIXTURE_DECISION),
        ("fixture-manifest", FIXTURE_MANIFEST),
        ("initial-parameters", PARAMETERS),
        ("retained-ln-g-39-gradient", GAIN_COMPARATOR),
        ("retained-ln-g-39-meta", GAIN_META),
        ("retained-ln-b-39-gradient", BIAS_COMPARATOR),
        ("retained-ln-b-39-meta", BIAS_META),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    parent_reflection = json.loads(PARENT_REFLECTION.read_text())
    ff1 = json.loads(FF1_DECISION.read_text())
    final = json.loads(FINAL_DECISION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    if not (
        parent["promotionPass"] is True
        and parent["measurements"]["sourceCaptureDeterministic"] is True
        and parent["measurements"]["nonProbeFixtureMismatchCount"] == 0
        and parent_reflection["validity"]["valid"] is True
        and parent_reflection["hypothesis"]["verdict"] == "supported"
        and parent_reflection["decision"]["verdict"] == "mutate"
        and ff1["promotionPass"] is True
        and ff1["measurements"]["block128SourceMismatchCount"] == 0
        and final["promotionPass"] is True
        and final["measurements"]["sourceFinalNormResidualMismatchCount"] == 0
        and final["measurements"]["finalNormGainMismatchCount"] == 0
        and final["measurements"]["finalNormBiasMismatchCount"] == 0
        and fixture["promotionPass"] is True
    ):
        raise ValueError("open pre-FF backward antecedents are not satisfied")
    require_gradient_meta(GAIN_META, "ln_g_39", 3)
    require_gradient_meta(BIAS_META, "ln_b_39", 4)


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, FREEZER)),
        PARENT_FORWARD_MATERIALIZER.resolve(),
        FF1_INPUT_MATERIALIZER.resolve(),
        FORWARD_MATERIALIZER.resolve(),
        BACKWARD_MATERIALIZER.resolve(),
        FINAL_BACKWARD.resolve(),
        CMAKE.resolve(),
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
        raise ValueError("open pre-FF source closure exceeds ceiling")


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
        raise ValueError("job and open pre-FF experiment bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("open pre-FF result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("open pre-FF work root was not freshly materialized")

    source = WORK / "source"
    build = WORK / "build"
    fixtures = WORK / "fixtures"
    parameters_root = WORK / "parameters"
    open_roots = [WORK / "open-a", WORK / "open-b"]
    for path in (source, fixtures, *open_roots):
        path.mkdir()
    executions: dict[str, Any] = {}
    profile = forward_parent.profile
    executions["extractSource"] = profile.base.execute(
        [
            "tar", "--extract", "--xz", "--no-same-owner",
            "--no-same-permissions", "--file",
            str(profile.base.parent.OPEN_SOURCE), "--directory", str(source),
        ],
        ROOT,
    )
    parent_forward = source / "profile_top_ff1_parent.cpp"
    ff1_forward = source / "profile_ff1_input.cpp"
    executions["materializeParentForward"] = profile.base.execute(
        [
            "python3", str(PARENT_FORWARD_MATERIALIZER),
            str(profile.base.parent.PARENT_FORWARD), str(parent_forward),
        ],
        ROOT,
    )
    executions["materializeFf1Input"] = profile.base.execute(
        [
            "python3", str(FF1_INPUT_MATERIALIZER), str(parent_forward),
            str(ff1_forward),
        ],
        ROOT,
    )
    executions["materializePreFfForward"] = profile.base.execute(
        [
            "python3", str(FORWARD_MATERIALIZER), str(ff1_forward),
            str(source / "profile_pre_ff_forward.cpp"),
        ],
        ROOT,
    )
    executions["materializePreFfBackward"] = profile.base.execute(
        [
            "python3", str(BACKWARD_MATERIALIZER), str(FINAL_BACKWARD),
            str(source / "pre_ff_backward.cpp"),
        ],
        ROOT,
    )
    shutil.copyfile(CMAKE, source / "CMakeLists.txt")
    executions["configure"] = profile.base.execute(
        [
            "cmake", "-S", str(source), "-B", str(build),
            "-DCMAKE_BUILD_TYPE=Release",
        ],
        ROOT,
    )
    executions["build"] = profile.base.execute(
        ["cmake", "--build", str(build), "--parallel", "4"], ROOT
    )
    forward_binaries = [
        path for path in build.rglob("nncp_open_pre_ff_forward")
        if path.is_file()
    ]
    backward_binaries = [
        path for path in build.rglob("nncp_open_pre_ff_backward")
        if path.is_file()
    ]
    if len(forward_binaries) != 1 or len(backward_binaries) != 1:
        raise ValueError("open pre-FF executable population differs")
    forward_binary = forward_binaries[0]
    backward_binary = backward_binaries[0]
    forbidden: list[str] = []
    for label, binary in (
        ("forward", forward_binary), ("backward", backward_binary)
    ):
        receipt = profile.base.execute(["ldd", str(binary)], ROOT)
        executions[f"ldd-{label}"] = receipt
        forbidden.extend(
            line
            for line in receipt["stdout"].splitlines()
            if any(
                token in line.lower()
                for token in (
                    "libnc", "ggml", "cuda", "openmp", "gomp", "blas"
                )
            )
        )

    used_fixture = profile.base.parent.verify_used_fixture(
        ("parameters_initial.coefs", "state_initial.params")
    )
    parameters = profile.base.parent.Container(PARAMETERS)
    state = profile.base.parent.Container(
        FIXTURE_ROOT / "fixture/state_initial.params"
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
            hidden = WORK / f"{label}-pre-ff-hidden.bf16"
            normalized = WORK / f"{label}-normalized-ff1-input.bf16"
            aggregate_bf16_exact(
                root, "layer_19_pre_ff_hidden.f32", hidden
            )
            aggregate_bf16_exact(root, "layer_19_ff1_input.f32", normalized)
            outputs = {
                name: WORK / f"{label}-{name}.bf16"
                for name in (
                    "gain", "bias", "norm-input-adjoint", "total-adjoint",
                    "direct-only", "negated-total",
                )
            }
            receipts["backward"] = profile.base.execute(
                [
                    str(backward_binary), str(PARAMETERS), str(root),
                    str(NORMALIZED_ADJOINT), str(DIRECT_ADJOINT),
                    *(str(outputs[name]) for name in (
                        "gain", "bias", "norm-input-adjoint", "total-adjoint",
                        "direct-only", "negated-total",
                    )),
                ],
                WORK,
                environment,
            )
            return {
                "receipts": receipts,
                "checkpoints": checkpoints,
                "mismatches": mismatches,
                "maximum": maximum,
                "hidden": hidden,
                "normalized": normalized,
                "outputs": outputs,
            }

        populations = [
            run_population(label, root)
            for label, root in zip(("a", "b"), open_roots, strict=True)
        ]
    finally:
        state.close()
        parameters.close()

    executions["populations"] = [row["receipts"] for row in populations]
    hidden_mismatches, hidden_maximum = bf16_comparator.compare_bf16(
        populations[0]["hidden"], SOURCE_HIDDEN
    )
    normalized_mismatches, normalized_maximum = bf16_comparator.compare_bf16(
        populations[0]["normalized"], NORMALIZED_INPUT
    )
    gain_mismatches, gain_maximum = bf16_comparator.compare_bf16(
        populations[0]["outputs"]["gain"], GAIN_COMPARATOR
    )
    bias_mismatches, bias_maximum = bf16_comparator.compare_bf16(
        populations[0]["outputs"]["bias"], BIAS_COMPARATOR
    )
    total_mismatches, total_maximum = bf16_comparator.compare_bf16(
        populations[0]["outputs"]["total-adjoint"], SOURCE_TOTAL_ADJOINT
    )
    direct_mismatches, _ = bf16_comparator.compare_bf16(
        populations[0]["outputs"]["direct-only"], SOURCE_TOTAL_ADJOINT
    )
    negated_mismatches, _ = bf16_comparator.compare_bf16(
        populations[0]["outputs"]["negated-total"], SOURCE_TOTAL_ADJOINT
    )
    replay_identical = all(
        populations[0][key].read_bytes() == populations[1][key].read_bytes()
        for key in ("hidden", "normalized")
    ) and all(
        populations[0]["outputs"][name].read_bytes()
        == populations[1]["outputs"][name].read_bytes()
        for name in populations[0]["outputs"]
    )

    retained = {
        "open-pre-ff-hidden": populations[0]["hidden"],
        "open-ln-g-39-gradient": populations[0]["outputs"]["gain"],
        "open-ln-b-39-gradient": populations[0]["outputs"]["bias"],
        "open-pre-ff-norm-input-adjoint": populations[0]["outputs"][
            "norm-input-adjoint"
        ],
        "source-exact-pre-ff-total-adjoint": populations[0]["outputs"][
            "total-adjoint"
        ],
    }
    artifacts: dict[str, Path] = {}
    for identifier, source_path in retained.items():
        destination = RESULT / f"{identifier}.bf16"
        shutil.copyfile(source_path, destination)
        artifacts[identifier] = destination
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "executions": executions,
                "usedFixture": used_fixture,
                "forbiddenDynamicDependencies": forbidden,
                "comparisons": {
                    "hidden": [hidden_mismatches, hidden_maximum],
                    "normalized": [normalized_mismatches, normalized_maximum],
                    "gain": [gain_mismatches, gain_maximum],
                    "bias": [bias_mismatches, bias_maximum],
                    "totalAdjoint": [total_mismatches, total_maximum],
                    "directOnly": [direct_mismatches, None],
                    "negatedTotal": [negated_mismatches, None],
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "sampleCount": SAMPLES,
        "layerInputCheckpointCount": sum(
            row["checkpoints"] for row in populations
        ),
        "layerInputMismatchCount": sum(row["mismatches"] for row in populations),
        "maximumLayerInputAbsoluteError": max(
            row["maximum"] for row in populations
        ),
        "hiddenElementCount": artifacts["open-pre-ff-hidden"].stat().st_size // 2,
        "hiddenSourceMismatchCount": hidden_mismatches,
        "maximumHiddenSourceAbsoluteError": hidden_maximum,
        "normalizedInputMismatchCount": normalized_mismatches,
        "maximumNormalizedInputAbsoluteError": normalized_maximum,
        "gainGradientElementCount": GAIN_COMPARATOR.stat().st_size // 2,
        "gainGradientMismatchCount": gain_mismatches,
        "maximumGainGradientAbsoluteError": gain_maximum,
        "biasGradientElementCount": BIAS_COMPARATOR.stat().st_size // 2,
        "biasGradientMismatchCount": bias_mismatches,
        "maximumBiasGradientAbsoluteError": bias_maximum,
        "totalAdjointElementCount": SOURCE_TOTAL_ADJOINT.stat().st_size // 2,
        "totalAdjointMismatchCount": total_mismatches,
        "maximumTotalAdjointAbsoluteError": total_maximum,
        "directOnlyControlMismatchCount": direct_mismatches,
        "negatedBranchControlMismatchCount": negated_mismatches,
        "openReplayIdentical": replay_identical,
        "forbiddenDynamicDependencyCount": len(forbidden),
        "incrementalSourceBytes": source_closure.stat().st_size,
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
            *(reference(path, identifier) for identifier, path in artifacts.items()),
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
