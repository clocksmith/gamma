#!/usr/bin/env python3
"""Capture the production source top-layer FF2 adjoint and reconstruct ff2_19."""

from __future__ import annotations

import argparse
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
import nncp_libnc_profile_update_fixture_64_q3 as fixture_parent
import nncp_open_profile_top_ff2_gradient_64_q0_retry_v1 as open_parent
import research_contracts


base = fixture_parent.base
ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_ff2_adjoint_64_q0_v1"
PARENT_ID = "nncp_open_profile_top_ff2_gradient_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_DECISION = ROOT / "results" / PARENT_ID / "decision.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T061837Z_1dfa2ae8f8.json"
)
PARENT_RESIDUAL = ROOT / "results" / PARENT_ID / "open-final-norm-input-residual.bf16"
FIXTURE_ID = "nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_ROOT = ROOT / "results" / FIXTURE_ID
FIXTURE_DECISION = FIXTURE_ROOT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture-manifest.json"
FIXTURE_GUARD = FIXTURE_ROOT / "guard.json"
RETAINED_FF2 = FIXTURE_ROOT / "fixture/gradients/0001_ff2_19.bin"
RETAINED_FF2_META = FIXTURE_ROOT / "fixture/gradients/0001_ff2_19.meta"
PROBE_SOURCE = PROGRAM / "top_ff2_probe.inc.c"
REDUCER_SOURCE = PROGRAM / "source_ff2_gradient.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
FIXTURE_HOOK = ROOT / "tools/nncp_profile_update_fixture_hook_q3.c"
MATERIALIZER = ROOT / "tools/nncp_libnc_top_ff2_adjoint_64_q0_materializer.py"
SOURCE_CEILING = 2_000_000
STATES = 64
STREAMS = 32
WIDTH = 1024
INNER = 3072


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
    result = {
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }
    if identifier is not None:
        result["id"] = identifier
    return result


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


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"source probe boundary is not unique: {old!r}")
    return source.replace(old, new, 1)


def patch_teacher(source: str) -> str:
    source = base.patch_teacher(source)
    probe = PROBE_SOURCE.read_text()
    source = replace_once(
        source,
        "static FILE *teacher_trace_file;\n",
        probe + "\nstatic FILE *teacher_trace_file;\n",
    )
    source = replace_once(
        source,
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n",
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n"
        "        gamma_top_ff2_probe_set_block(block_idx);\n",
    )
    source = replace_once(
        source,
        "        t0 = nc_matmul(nc_dup_tensor(tl->ff2), t0);",
        "        gamma_top_ff2_input_dump(t0, layer_idx, output_index);\n"
        "        t0 = nc_matmul(nc_dup_tensor(tl->ff2), t0);",
    )
    bias = (
        "        if (tl->ff_bias2)\n"
        "            t0 = nc_add(t0, nc_dup_tensor(tl->ff_bias2));"
    )
    source = replace_once(
        source,
        bias,
        bias + "\n        t0 = gamma_top_ff2_probe_attach(\n"
        "            t0, layer_idx, output_index);",
    )
    source = replace_once(
        source,
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
        "    if (gamma_top_ff2_probe_capture(opaque, yg, get_col_index))\n"
        "        return;\n"
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
    )
    return source


def compile_tools(scratch: Path) -> tuple[Path, Path, Path, dict[str, Any]]:
    compiler = os.environ.get("CC", "cc")
    cxx = os.environ.get("CXX", "g++")
    patched = scratch / "nncp_top_ff2_adjoint.c"
    patched.write_text(patch_teacher((base.LIBNC_ROOT / "nncp.c").read_text()))
    nncp_object = scratch / "nncp_top_ff2_adjoint.o"
    executable = scratch / "nncp_top_ff2_adjoint"
    hook = scratch / "nncp_profile_update_fixture_hook_q3.so"
    reducer = scratch / "source_ff2_gradient"
    commands = [
        [
            compiler,
            "-O3",
            "-Wall",
            "-Wpointer-arith",
            "-g",
            "-fno-math-errno",
            "-fno-trapping-math",
            '-DCONFIG_VERSION="2024-06-05"',
            "-DLIBNC_CONFIG_FULL",
            f"-I{base.LIBNC_ROOT}",
            "-c",
            str(patched),
            "-o",
            str(nncp_object),
        ],
        [
            compiler,
            f"-Wl,-rpath,{base.LIBNC_ROOT}",
            "-o",
            str(executable),
            str(nncp_object),
            *[
                str(base.LIBNC_ROOT / name)
                for name in (
                    "cmdopt.o",
                    "cp_utils.o",
                    "arith.o",
                    "preprocess.o",
                    "cutils.o",
                )
            ],
            str(base.LIBNC_ROOT / "libnc.so"),
            "-lz",
            "-lm",
            "-lpthread",
        ],
        [
            compiler,
            "-std=gnu11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Wno-unused-parameter",
            "-shared",
            "-fPIC",
            f"-I{base.LIBNC_ROOT}",
            str(FIXTURE_HOOK),
            f"-L{base.LIBNC_ROOT}",
            f"-Wl,-rpath,{base.LIBNC_ROOT}",
            "-lnc",
            "-ldl",
            "-o",
            str(hook),
        ],
        [
            cxx,
            "-std=c++17",
            "-O3",
            "-mavx2",
            "-mfma",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(REDUCER_SOURCE),
            "-o",
            str(reducer),
        ],
    ]
    receipts = [execute(command, ROOT) for command in commands]
    return executable, hook, reducer, {
        "commands": receipts,
        "patchedSourceSha256": sha256(patched),
        "executableSha256": sha256(executable),
        "hookSha256": sha256(hook),
        "reducerSha256": sha256(reducer),
    }


def parse_meta(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines())


def combine_probe(directory: Path, kind: str, width: int, output: Path) -> None:
    with output.open("wb") as destination:
        for state in range(STATES):
            stem = f"top_ff2_{kind}_s{state:03d}"
            payload = directory / f"{stem}.bin"
            metadata = directory / f"{stem}.meta"
            expected_bytes = width * STREAMS * 2
            expected_meta = {
                "kind": kind,
                "state": str(state),
                "item_type": "1",
                "item_size": "2",
                "dims": f"{width},{STREAMS}",
                "byte_order": "little",
            }
            if (
                not payload.is_file()
                or payload.stat().st_size != expected_bytes
                or not metadata.is_file()
                or parse_meta(metadata) != expected_meta
            ):
                raise ValueError(f"source top FF2 {kind} state differs: {state}")
            with payload.open("rb") as source:
                shutil.copyfileobj(source, destination, 8 * 1024 * 1024)
    if output.stat().st_size != STATES * STREAMS * width * 2:
        raise ValueError(f"combined source top FF2 {kind} geometry differs")


def fixture_identity(
    observed: dict[str, Any], parent_manifest: dict[str, Any]
) -> tuple[bool, list[str]]:
    parent_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in parent_manifest["fixture"]["files"]
    }
    observed_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in observed["files"]
        if not row["path"].startswith("top_ff2_")
    }
    paths = sorted(set(parent_rows) | set(observed_rows))
    mismatches = [path for path in paths if parent_rows.get(path) != observed_rows.get(path)]
    return not mismatches, mismatches


def mismatch_features(left: Path, right: Path) -> int:
    left_bytes = left.read_bytes()
    right_bytes = right.read_bytes()
    if len(left_bytes) != len(right_bytes) or len(left_bytes) % 2:
        raise ValueError("adjoint mismatch-feature geometry differs")
    features = set()
    for index in range(0, len(left_bytes), 2):
        if left_bytes[index : index + 2] != right_bytes[index : index + 2]:
            features.add((index // 2) % WIDTH)
    return len(features)


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((Path(__file__), MATERIALIZER)),
        PROBE_SOURCE.resolve(),
        REDUCER_SOURCE.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        FIXTURE_HOOK.resolve(),
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
    path.write_bytes(lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME))
    tar_path.unlink()
    if path.stat().st_size > SOURCE_CEILING:
        raise ValueError("source top FF2 adjoint closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-open-decision", PARENT_DECISION),
        ("parent-open-reflection", PARENT_REFLECTION),
        ("parent-open-residual", PARENT_RESIDUAL),
        ("production-fixture-decision", FIXTURE_DECISION),
        ("production-fixture-manifest", FIXTURE_MANIFEST),
        ("production-fixture-guard", FIXTURE_GUARD),
        ("retained-ff2-gradient", RETAINED_FF2),
        ("retained-ff2-gradient-meta", RETAINED_FF2_META),
        ("probe-source", PROBE_SOURCE),
        ("reducer-source", REDUCER_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    if not (
        parent["promotionPass"] is False
        and parent["measurements"]["topFf2MismatchCount"] == 184
        and parent["measurements"]["openBackwardDeterministic"] is True
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "refuted"
        and reflection["decision"]["verdict"] == "retry"
        and fixture["promotionPass"] is True
        and fixture["measurements"]["fixtureRepeatByteIdentical"] is True
        and fixture["measurements"]["parameterPopulation"] == 246
        and fixture["measurements"]["targetBlockBefore"] == 256
    ):
        raise ValueError("source top FF2 adjoint antecedents are not satisfied")
    for path, expected in base.EXPECTED.items():
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"frozen source input identity differs: {path}")


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
        raise ValueError("job and source-adjoint experiment bindings differ")
    candidate_revision = json.loads(
        os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
    )
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("source top FF2 adjoint result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("source top FF2 work root was not freshly materialized")

    scratch = WORK / "build"
    scratch.mkdir()
    executable, hook, reducer, build = compile_tools(scratch)
    captures = [WORK / "capture-a", WORK / "capture-b"]
    executions = [base.capture(executable, hook, directory) for directory in captures]
    manifests = [base.directory_manifest(directory) for directory in captures]
    parent_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [fixture_identity(manifest, parent_manifest) for manifest in manifests]

    combined = []
    for label, directory in zip(("a", "b"), captures, strict=True):
        input_path = WORK / f"{label}-source-top-ff2-input.bf16"
        adjoint_path = WORK / f"{label}-source-top-ff2-adjoint.bf16"
        gradient_path = WORK / f"{label}-source-ff2-19-gradient.bf16"
        control_path = WORK / f"{label}-control-source-ff2-19-gradient.bf16"
        combine_probe(directory, "input", INNER, input_path)
        combine_probe(directory, "adjoint", WIDTH, adjoint_path)
        reduction = execute(
            [
                str(reducer),
                str(input_path),
                str(adjoint_path),
                str(gradient_path),
                str(control_path),
            ],
            WORK,
        )
        combined.append(
            {
                "input": input_path,
                "adjoint": adjoint_path,
                "gradient": gradient_path,
                "control": control_path,
                "reduction": reduction,
            }
        )

    capture_repeat = manifests[0]["aggregateSha256"] == manifests[1]["aggregateSha256"]
    combined_repeat = all(
        combined[0][key].read_bytes() == combined[1][key].read_bytes()
        for key in ("input", "adjoint", "gradient", "control")
    )
    parent_fixture_identity = all(identity[0] for identity in identities)
    open_comparison = open_parent.parent.compare_bf16(
        combined[0]["adjoint"], PARENT_RESIDUAL
    )
    source_gradient_comparison = open_parent.parent.compare_bf16(
        combined[0]["gradient"], RETAINED_FF2
    )
    feature_count = mismatch_features(combined[0]["adjoint"], PARENT_RESIDUAL)
    control_differs = (
        combined[0]["control"].read_bytes()
        != combined[0]["gradient"].read_bytes()
    )

    artifacts = {
        "source-top-ff2-input": RESULT / "source-top-ff2-input.bf16",
        "source-top-ff2-adjoint": RESULT / "source-top-ff2-adjoint.bf16",
        "source-top-ff2-gradient": RESULT / "source-ff2-19-gradient.bf16",
    }
    shutil.copyfile(combined[0]["input"], artifacts["source-top-ff2-input"])
    shutil.copyfile(combined[0]["adjoint"], artifacts["source-top-ff2-adjoint"])
    shutil.copyfile(combined[0]["gradient"], artifacts["source-top-ff2-gradient"])
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "build": build,
                "captures": executions,
                "captureAggregateSha256": [
                    manifest["aggregateSha256"] for manifest in manifests
                ],
                "captureFileCount": [manifest["fileCount"] for manifest in manifests],
                "captureTotalBytes": [manifest["totalBytes"] for manifest in manifests],
                "parentFixtureIdentity": [identity[0] for identity in identities],
                "parentFixtureMismatches": [identity[1] for identity in identities],
                "reductions": [item["reduction"] for item in combined],
                "combinedSha256": [
                    {key: sha256(item[key]) for key in ("input", "adjoint", "gradient", "control")}
                    for item in combined
                ],
                "externalInputSha256": {
                    str(path): sha256(path) for path in base.EXPECTED
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
        "sourceCaptureRepeatIdentical": capture_repeat,
        "combinedReplayIdentical": combined_repeat,
        "parentFixtureIdentity": parent_fixture_identity,
        "capturedStateCount": STATES,
        "sourceAdjointElementCount": artifacts["source-top-ff2-adjoint"].stat().st_size // 2,
        "sourceInputElementCount": artifacts["source-top-ff2-input"].stat().st_size // 2,
        "sourceFf2ElementCount": artifacts["source-top-ff2-gradient"].stat().st_size // 2,
        "openAdjointMismatchCount": open_comparison[0],
        "maximumOpenAdjointAbsoluteError": open_comparison[1],
        "openAdjointMismatchFeatureCount": feature_count,
        "sourceFf2MismatchCount": source_gradient_comparison[0],
        "maximumSourceFf2AbsoluteError": source_gradient_comparison[1],
        "negatedSourceAdjointControlDiffers": control_differs,
        "incrementalSourceBytes": incremental_source.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = open_parent.evaluate(experiment["promotionPredicates"], measurements)
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
            "authorize-successor" if promotion_pass else "retire" if kill_pass else "retry"
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
